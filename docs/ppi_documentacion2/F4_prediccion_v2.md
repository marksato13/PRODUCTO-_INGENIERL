# F4 — Predicción Inteligente (XGBoost v2)
**Estado: 🔄 EN IMPLEMENTACIÓN**

---

## Objetivo

Predecir si un evento del IF (LIMIT o BLOCK) corresponde a un ataque sostenido o a una anomalía puntual, usando los outputs del propio IF como señal. Notificar al operador con anticipación gradual.

---

## ¿Por qué complementa al IF?

El IF clasifica flujo por flujo — no tiene memoria temporal. No distingue entre:
- Una anomalía puntual (falso positivo o evento aislado → puede ignorarse)
- El inicio de un ataque sostenido que continuará → requiere atención

El XGBoost analiza el patrón temporal de eventos del IF para predecir persistencia.

---

## Señal de entrada — LIMIT + BLOCK combinados

Lee ambas líneas de `motor_decision.log`:

| Línea del log | Tipo | Ataque típico |
|---|---|---|
| `SOSPECHOSO ... \| LIMIT` | Gradual | HTTP Abuse, Brute Force SSH |
| `ANOMALÍA ... \| BLOCK` | Volumétrico | SYN Flood, UDP/ICMP Flood, Port Scan |

---

## Features del modelo (12)

```python
score            # IF decision_function — intensidad de la anomalía
pkt_rate         # velocidad de paquetes del flujo
byte_ratio       # ratio bytes (0=SYN flood puro, alto=descarga)
dest_port        # puerto objetivo (80=HTTP, 22=SSH, etc.)
proto_tcp        # booleano
proto_udp        # booleano
proto_icmp       # booleano
grado_alta       # ALTA vs BAJA anomalía según grado IF
hora_sin         # componente temporal sin(hora/24 * 2π)
hora_cos         # componente temporal cos(hora/24 * 2π)
limit_count_15s  # cuántos LIMITs de esta IP en los últimos 15s
block_count_60s  # cuántos BLOCKs de esta IP en los últimos 60s
```

---

## Label automático (sin etiquetado manual)

```python
label = 1  # hay otro BLOCK de la misma IP en los próximos 60s → ataque sostenido
label = 0  # no hay más eventos en 60s → anomalía puntual o falso positivo
```

El log se etiqueta solo — sin trabajo manual.

---

## Comportamiento por escenario

| Escenario | Señal dominante | ¿Antes o después del BLOCK? | Valor |
|---|---|---|---|
| B1 SYN Flood | BLOCK (score=-0.74) | Después (~T+10s) | ¿Es sostenido? |
| B2 Port Scan | BLOCK mixto | Después | ¿Va a escalar? |
| B3 UDP Flood | BLOCK directo | Después | ¿Es sostenido? |
| B4 ICMP Flood | BLOCK directo | Después | ¿Es sostenido? |
| B5 HTTP Abuse | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana |
| B6 Brute Force SSH | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana |

---

## Niveles de alerta — 2 tipos

```
P < 0.40         → SILENCIO
                   Tráfico normal o anomalía puntual. No se registra.

0.40 ≤ P < 0.70  → AVISO (amarillo en dashboard)
                   "Actividad sospechosa detectada, monitoreando."
                   Log INFO. Visible en panel del dashboard.
                   No envía Telegram. El sistema sigue observando.
                   Si el ataque escala → próximo ciclo sube a ALERTA.
                   Si se normaliza   → vuelve a silencio solo.

P ≥ 0.70         → ALERTA-PREDICTIVA (rojo en dashboard)
                   "Ataque en curso / inminente — actuar."
                   Log WARNING. Panel rojo en dashboard.
                   Envía Telegram al operador.
                   Dedup: una alerta por IP cada 5 min.
```

El operador recibe Telegram solo cuando hay alta confianza. Los avisos intermedios son visibles en el dashboard sin interrumpir.

---

## Telegram (F4)

- Mismo relay que F3: `http://192.168.0.20:8889/telegram`
- Envía solo con P ≥ 0.70 (ALERTA-PREDICTIVA)
- Mensaje: `[PREDICTOR] Ataque sostenido probable | IP: X.X.X.X | P=87% | tipo=ANOMALIA_GENERICA`
- Dedup 5 min por IP para evitar spam

---

## Datos de entrenamiento disponibles

```
/home/m4rk/ppi-surikata-producto/results/motor_decision.log
  - 50,134 eventos LIMIT (SOSPECHOSO)
  - 11,977 eventos BLOCK (ANOMALÍA)
  - Período: 2026-06-02 al 2026-06-21
  - Label generado automáticamente
```

---

## Scripts — convenio de nombres

Los nuevos scripts de F4 usan prefijo `f4_` para distinguirlos de los scripts legacy:

| Archivo | Estado |
|---|---|
| `scripts/f4_entrenar_predictor_v2.py` | ⬜ PENDIENTE — extrae features, entrena XGBoost |
| `scripts/predictor.py` | ⬜ MODIFICAR — nueva señal LIMIT+BLOCK, ciclo 10s |
| `models/predictor_modelo_v2.pkl` | ⬜ PENDIENTE — se genera al entrenar |
| `models/features_predictor_v2.txt` | ⬜ PENDIENTE — lista de 12 features |
| `results/metricas_predictor_v2.txt` | ⬜ PENDIENTE — AUC, F1, τ, lead time |
| `config/systemd/ppi-predictor.service` | ✅ YA EXISTE |

---

## Criterios de aceptación

| ID | Criterio | Estado |
|---|---|---|
| CA-F4-01 | AUC-ROC > 0.70 | ⬜ pendiente |
| CA-F4-02 | B5/B6: AVISO o ALERTA antes del primer BLOCK | ⬜ pendiente |
| CA-F4-03 | B1/B3/B4: ALERTA en ≤ 15s del primer BLOCK | ⬜ pendiente |
| CA-F4-04 | Corridas normales: FPR < 10% | ⬜ pendiente |
| CA-F4-05 | Inferencia < 50ms por ciclo | ⬜ pendiente |
| CA-F4-06 | AVISO visible en dashboard sin Telegram | ⬜ pendiente |
| CA-F4-07 | ALERTA envía Telegram con dedup 5min | ⬜ pendiente |

---

## Argumento de defensa

> "El IF detecta anomalías flujo por flujo pero no distingue una anomalía puntual de un ataque sostenido. El XGBoost usa los outputs del IF como features para predecir la persistencia. El sistema responde con dos niveles: un aviso de vigilancia activa, y una alerta de alta confianza con notificación al operador."
