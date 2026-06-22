# Sistema de Detección Temprana de Anomalías en Redes
## PPI — Universidad Peruana Unión | Rubén Mark Salazar Tocas

> Índice principal. Cada fase tiene su propio archivo de especificación y validación.
> Estado actualizado al 2026-06-21.

---

## Visión del sistema

```
Red de datos
    │
    ▼
[F1] CAPTURA Y PREPARACIÓN
    Suricata 7.0.3 → eve.json → dataset estructurado (14 features)
    │
    ▼
[F2] DETECCIÓN DE ANOMALÍAS — Isolation Forest
    Modelo offline n=300 → τ1=-0.4459 / τ2=-0.6027
    AUC=0.8998 | Precision=99.54% | Recall=99.40%
    │
    ▼
[F3] CONTROL EN TIEMPO REAL — Motor + ipset
    score → PERMIT / LIMIT (100pkt/s) / BLOCK (DROP)
    Latencia P95=34.8ms | ITL=0% | Disponibilidad=100%
    │
    ▼
[F4] PREDICCIÓN INTELIGENTE — XGBoost v2
    señal LIMIT+BLOCK → P(ataque sostenido)
    Ataques graduales: alerta ANTES del BLOCK
    Ataques volumétricos: predice persistencia
    │
    ▼
[F5] APRENDIZAJE CONTINUO — Reentrenamiento automático
    IF: semanal con tráfico PERMIT → umbrales se adaptan
    XGBoost: noche con log 24h → mejora predicciones
    Hot-reload sin reiniciar servicios
```

---

## Estado de fases

| Fase | Nombre | Estado | Archivo |
|---|---|---|---|
| F1 | Captura y Preparación de Datos | ✅ COMPLETA | [F1_captura_datos.md](F1_captura_datos.md) |
| F2 | Detección de Anomalías (IF) | ✅ COMPLETA | [F2_deteccion_if.md](F2_deteccion_if.md) |
| F3 | Control en Tiempo Real | ✅ COMPLETA | [F3_control_motor.md](F3_control_motor.md) |
| F4 | Predicción XGBoost v2 | 🔄 EN IMPLEMENTACIÓN | [F4_prediccion_v2.md](F4_prediccion_v2.md) |
| F5 | Aprendizaje Continuo | 📋 PLANIFICADA | [F5_aprendizaje.md](F5_aprendizaje.md) |

---

## Flujo de componentes — orden correcto

```
Ataque gradual (HTTP Abuse, BF SSH):
  T=0s   Kali empieza tráfico anómalo lento
  T=5s   Motor: primeros flujos → LIMIT (score entre τ2 y τ1)
  T=10s  XGBoost: limit_count_15s sube → P=0.82 → ALERTA-PREDICTIVA ✅
  T=30s  Motor: flujos escalan → BLOCK → ipset DROP

Ataque volumétrico (SYN Flood, UDP, ICMP):
  T=0s   Kali empieza flood masivo
  T=5s   Motor: 500 flujos → score=-0.74 → BLOCK → ipset DROP
  T=10s  XGBoost: ve BLOCK con pkt_rate=10K → P=0.87 → ALERTA (sostenido)

Tráfico normal:
  T=∞    Motor: score > τ1 → PERMIT
         XGBoost: P < 0.40 → silencio
```

---

## Argumentos de defensa — resumen

**"¿Por qué Isolation Forest?"**
No requiere etiquetas manuales. Aprende el comportamiento normal y detecta cualquier desviación. Ideal para redes donde los ataques son desconocidos a priori.

**"¿Por qué XGBoost?"**
Complementa al IF: el IF detecta por flujo individual, el XGBoost analiza patrones temporales para predecir si el ataque va a escalar o persistir.

**"¿Por qué predice después en SYN Flood?"**
No existe señal antes del primer paquete anómalo — es físicamente imposible. El IF bloquea en 5s (suficiente). El XGBoost agrega contexto sobre la gravedad y persistencia.

**"¿El sistema aprende solo?"**
Sí. En F5: el IF se reajusta al tráfico normal reciente, el XGBoost se actualiza con el historial de ataques reales. Sin intervención manual.

---

## Topología del laboratorio

| IP | VM | Rol |
|---|---|---|
| 192.168.0.10 | Win11 | Cliente |
| 192.168.0.20 | Ubuntu Desktop | Admin / origen tráfico normal |
| 192.168.0.100 | Kali Linux | Origen tráfico anómalo |
| 192.168.0.110 | Ubuntu Suricata | Sensor — motor + predictor |
| 192.168.0.120 | Ubuntu Server | Servicio nginx:80, SSH:22 |
