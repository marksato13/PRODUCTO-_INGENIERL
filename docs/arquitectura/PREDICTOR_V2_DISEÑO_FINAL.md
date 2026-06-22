# Predictor XGBoost v2 — Diseño Final

> Decisiones tomadas en sesiones 2026-06-21. Este archivo es la fuente de verdad para implementar v2.

---

## Problema del v1 (descartado)

El predictor v1 usaba el tiempo entre líneas `STATS` del motor (cada 500 flujos) como señal de aceleración de tráfico.

**Por qué falló:**
- Necesita mínimo 2 líneas STATS = 34s para calcular un gap
- El IF ya bloqueó el SYN flood a T=5s
- Resultado medido: lead time = **-78s** (predice 78s DESPUÉS del bloqueo)
- En ataques inactivos/reinicio: predictor entra en estado "inactivo" (gap>600s)

---

## Diseño correcto — señal combinada LIMIT + BLOCK

### ¿Qué usa el XGBoost para aprender?

**Ambas líneas del log: SOSPECHOSO (LIMIT) y ANOMALÍA (BLOCK)**

| Señal | Línea del log | Ataque típico |
|---|---|---|
| LIMIT | `SOSPECHOSO ... \| LIMIT` | HTTP Abuse, Brute Force SSH |
| BLOCK | `ANOMALÍA ... \| BLOCK` | SYN Flood, UDP Flood, ICMP Flood, Port Scan |

### Features por evento de entrenamiento

```python
features = {
    'score':            float,   # IF decision_function (τ1=-0.4459, τ2=-0.6027)
    'pkt_rate':         float,   # velocidad de paquetes
    'byte_ratio':       float,   # 0=SYN flood puro, alto=descarga
    'dest_port':        int,     # 80=HTTP, 22=SSH, etc.
    'proto_tcp':        bool,
    'proto_udp':        bool,
    'proto_icmp':       bool,
    'grado_alta':       bool,    # ALTA vs BAJA anomalía
    'hora_sin':         float,   # ciclo temporal (sin(hora/24*2π))
    'hora_cos':         float,
    'limit_count_15s':  int,     # LIMITs de esta IP en últimos 15s
    'block_count_60s':  int,     # BLOCKs de esta IP en últimos 60s
}
```

### Label automático desde el log

```python
# Sin etiquetado manual — el log se etiqueta solo
label = 1  # si hay otro BLOCK de la misma IP en los próximos 60s (ataque sostenido)
label = 0  # si no hay más eventos (anomalía puntual / falso positivo)
```

---

## Comportamiento por escenario (los 6 del lab)

| Escenario | Señal dominante | ¿Predice antes o después del BLOCK? | Valor |
|---|---|---|---|
| B1 SYN Flood | BLOCK directo (score=-0.74) | **Después** (~T+10s) | Predice si el ataque es sostenido |
| B2 Port Scan | BLOCK mixto | Después | Predice persistencia |
| B3 UDP Flood | BLOCK directo | Después | Predice persistencia |
| B4 ICMP Flood | BLOCK directo | Después | Predice persistencia |
| B5 HTTP Abuse | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana real |
| B6 Brute Force SSH | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana real |

**Regla general:**
- Ataque gradual (B5, B6): LIMIT acumulados → XGBoost predice escalación → ANTES del BLOCK
- Ataque volumétrico (B1-B4): BLOCK directo → XGBoost predice si es sostenido → DESPUÉS del BLOCK

---

## Argumentos de defensa para el jurado

### "¿Qué predice realmente?"
> El IF detecta anomalías flujo por flujo pero no distingue una anomalía puntual de un ataque sostenido. El XGBoost predice si el evento actual va a continuar o escalar, usando como features los outputs del propio IF (score, tipo, tasa). Para ataques graduales logra alerta antes del primer BLOCK. Para floods, el IF bloquea en 5s (suficiente) y el XGBoost agrega inteligencia operacional sobre la gravedad.

### "¿No debería predecir antes en SYN Flood?"
> No existe señal antes del primer paquete anómalo — es físicamente imposible anticipar un ataque sin información previa. Para SYN Flood, el IF responde en 5s que es suficiente. El XGBoost no compite con el IF: el IF es el sensor, el XGBoost es el analista que interpreta el patrón.

### "¿Es necesario?"
> Sin XGBoost: el sistema bloquea pero no sabe si el atacante va a seguir. Con XGBoost: el operador sabe si debe mantener el bloqueo o si fue una anomalía puntual. Reduce falsas alarmas y da contexto para tomar decisiones.

---

## Visión v2 — aprendizaje continuo

### IF en v2
- Reentrenar **semanalmente con tráfico NORMAL (PERMIT únicamente)**
- Los umbrales τ1/τ2 se ajustan al baseline real de la red
- **NO entrenar con ataques** — normalizaría el comportamiento malicioso

### XGBoost en v2
- Reentrenar **cada noche** con las últimas 24h del log
- Soporta entrenamiento incremental: `xgb_model=modelo_anterior`
- Aprende de TODO (normal + ataque) porque es supervisado — sabe la diferencia

### Son complementarios, no reemplazables
El XGBoost depende del IF (sus outputs son las features). Esta dependencia es correcta:
- Si el IF mejora → XGBoost recibe mejores señales automáticamente
- Si el IF reajusta umbrales → XGBoost aprende los nuevos patrones

**Riesgo de aprendizaje puro en tiempo real:** envenenamiento — un atacante puede disfrazar tráfico malicioso como normal para "educar" al modelo. Por eso: reentrenamiento periódico con validación de AUC, no aprendizaje online puro.

---

## Datos de entrenamiento disponibles (ya existen)

```
Fuente: motor_decision.log (sensor 192.168.0.110)
  /home/m4rk/ppi-surikata-producto/results/motor_decision.log

Volumen:
  - 50,134 eventos LIMIT (SOSPECHOSO)
  - 11,977 eventos BLOCK (ANOMALÍA)
  - Período: 2026-06-02 al 2026-06-21
  - Sin etiquetado manual requerido
```

---

## Archivos a crear/modificar para implementar v2

| Archivo (en sensor) | Acción |
|---|---|
| `scripts/entrenar_predictor_v2.py` | CREAR — extrae features de LIMIT+BLOCK, entrena XGBoost |
| `scripts/predictor.py` | MODIFICAR — nueva señal combinada, ciclo 10s |
| `models/predictor_modelo_v2.pkl` | GENERAR — nuevo modelo entrenado |
| `models/features_predictor_v2.txt` | GENERAR — lista de 12 features |
| `results/metricas_predictor_v2.txt` | GENERAR — AUC, F1, τ, lead time por escenario |
| `docs/arquitectura/PREDICTOR_V2_DISEÑO_FINAL.md` | ESTE ARCHIVO (copiar al sensor) |

---

## Lo que NO cambia

- Motor IF (`motor_decision.py`) — no se toca
- Umbrales τ1/τ2 — no cambian
- ipset/iptables enforcement — no cambia
- Fases F1-F6 — completas y validadas
- AUC-ROC del IF: 0.8998
