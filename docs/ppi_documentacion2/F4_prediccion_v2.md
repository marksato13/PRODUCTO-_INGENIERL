# F4 — Predicción Inteligente (XGBoost v2)
**Estado: 🔄 EN IMPLEMENTACIÓN**

---

## Objetivo

Predecir si un evento detectado por el IF (LIMIT o BLOCK) corresponde a un ataque sostenido o a una anomalía puntual, usando los propios outputs del IF como señal de entrada.

---

## ¿Por qué XGBoost complementa al IF?

El IF detecta flujo por flujo — no tiene memoria temporal. No distingue entre:
- Una anomalía puntual (falso positivo o evento aislado)
- El inicio de un ataque sostenido que va a continuar

El XGBoost analiza el patrón temporal de los eventos del IF para predecir la persistencia del ataque.

---

## Señal de entrada — LIMIT + BLOCK combinados

El predictor lee AMBAS líneas del `motor_decision.log`:

| Línea del log | Tipo | Ataque típico |
|---|---|---|
| `SOSPECHOSO ... \| LIMIT` | Ataque gradual | HTTP Abuse, Brute Force SSH |
| `ANOMALÍA ... \| BLOCK` | Ataque volumétrico | SYN Flood, UDP/ICMP Flood |

---

## Features del modelo (12)

```python
score            # IF decision_function — qué tan anómalo es el flujo
pkt_rate         # velocidad de paquetes
byte_ratio       # ratio bytes (0=SYN flood puro, alto=descarga)
dest_port        # puerto objetivo (80=HTTP, 22=SSH, etc.)
proto_tcp        # booleano
proto_udp        # booleano
proto_icmp       # booleano
grado_alta       # ALTA vs BAJA anomalía
hora_sin         # componente temporal sin(hora/24 * 2π)
hora_cos         # componente temporal cos(hora/24 * 2π)
limit_count_15s  # LIMITs de esta IP en los últimos 15s
block_count_60s  # BLOCKs de esta IP en los últimos 60s
```

---

## Label automático (sin etiquetado manual)

```python
label = 1  # hay otro BLOCK de la misma IP en los próximos 60s → ataque sostenido
label = 0  # no hay más eventos en 60s → puntual o falso positivo
```

---

## Comportamiento por escenario

| Escenario | Señal dominante | ¿Predice antes o después? | Valor |
|---|---|---|---|
| B1 SYN Flood | BLOCK (score=-0.74) | Después (~T+10s) | ¿Es sostenido? |
| B2 Port Scan | BLOCK mixto | Después | ¿Va a escalar? |
| B3 UDP Flood | BLOCK (score bajo) | Después | ¿Es sostenido? |
| B4 ICMP Flood | BLOCK (score bajo) | Después | ¿Es sostenido? |
| B5 HTTP Abuse | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana |
| B6 Brute Force SSH | LIMITs acumulados → BLOCK | **Antes** ✅ | Alerta temprana |

---

## Umbrales de alerta

| Probabilidad | Acción |
|---|---|
| P < 0.40 | Silencio — flujo normal o puntual |
| 0.40 ≤ P < 0.70 | RIESGO-MEDIO — log INFO, visible en dashboard |
| P ≥ 0.70 | ALERTA-PREDICTIVA — WARNING, dashboard rojo |

---

## Datos de entrenamiento disponibles

```
Fuente: /home/m4rk/ppi-surikata-producto/results/motor_decision.log
  - 50,134 eventos LIMIT (SOSPECHOSO)
  - 11,977 eventos BLOCK (ANOMALÍA)
  - Período: 2026-06-02 al 2026-06-21
  - Label generado automáticamente — sin trabajo manual
```

---

## Archivos a crear

| Archivo | Estado |
|---|---|
| `scripts/entrenar_predictor_v2.py` | ⬜ PENDIENTE |
| `scripts/predictor.py` | ⬜ MODIFICAR (nueva señal) |
| `models/predictor_modelo_v2.pkl` | ⬜ PENDIENTE (se genera al entrenar) |
| `models/features_predictor_v2.txt` | ⬜ PENDIENTE |
| `results/metricas_predictor_v2.txt` | ⬜ PENDIENTE |
| `config/systemd/ppi-predictor.service` | ✅ YA EXISTE (ajustar si necesario) |

---

## Criterios de aceptación

| ID | Criterio | Estado |
|---|---|---|
| CA-F4-01 | AUC-ROC > 0.70 | ⬜ pendiente |
| CA-F4-02 | Para B5/B6: alerta ANTES del primer BLOCK | ⬜ pendiente |
| CA-F4-03 | Para B1/B3/B4: alerta en ≤ 15s del BLOCK | ⬜ pendiente |
| CA-F4-04 | Corridas normales: FPR < 10% | ⬜ pendiente |
| CA-F4-05 | Inferencia < 50ms | ⬜ pendiente |
| CA-F4-06 | Ciclo del predictor: 10s | ⬜ pendiente |

---

## Argumento de defensa

> "El IF detecta anomalías flujo por flujo pero no distingue una anomalía puntual de un ataque sostenido. El XGBoost usa los outputs del IF (score, tipo, tasa) como features para predecir si el evento actual va a persistir. Para ataques graduales logra alerta antes del primer BLOCK. Para ataques volumétricos, el IF ya bloqueó en 5s y el XGBoost agrega contexto sobre la gravedad."

> "Para SYN Flood: no existe señal antes del primer paquete anómalo. Es físicamente imposible anticipar sin información previa. El IF responde en 5s, que es suficiente para proteger la red."
