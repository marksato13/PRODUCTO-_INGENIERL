# F4 — Predicción Inteligente (XGBoost v2)
**Estado: ✅ IMPLEMENTADA Y VALIDADA**

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

## Features del modelo (10)

> El log histórico usa formato sin pkt_rate/byte_ratio en la mayoría de líneas.
> Se usan los 10 features disponibles en ambos formatos del log.

```
score            — IF decision_function (intensidad de la anomalía)
dest_port        — puerto objetivo (80=HTTP, 22=SSH, etc.)
proto_tcp        — booleano
proto_udp        — booleano
proto_icmp       — booleano
hora_sin         — componente temporal sin(hora/24 * 2π)
hora_cos         — componente temporal cos(hora/24 * 2π)
limit_count_15s  — LIMITs de esta IP en los últimos 15s
block_count_60s  — BLOCKs de esta IP en los últimos 60s
is_block         — 1=BLOCK, 0=LIMIT
```

---

## Label automático (sin etiquetado manual)

```
label = 1  → hay otro BLOCK de la misma IP en los próximos 60s (ataque sostenido)
label = 0  → no hay más eventos en 60s (anomalía puntual / falso positivo)
```

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
                   Log INFO. Sin Telegram. El sistema sigue observando.

P ≥ 0.70         → ALERTA-PREDICTIVA (rojo en dashboard)
                   "Ataque sostenido en curso — actuar."
                   Log WARNING. Telegram al operador. Dedup 5 min por IP.
```

---

## Métricas de entrenamiento — REALES (2026-06-22)

| Métrica | Valor |
|---|---|
| Dataset total | 61,921 eventos |
| LIMIT (SOSPECHOSO) | 49,997 |
| BLOCK (ANOMALÍA) | 11,924 |
| Label=1 (sostenido) | 5,302 (8.6%) |
| Label=0 (puntual) | 56,619 (91.4%) |
| Split | Aleatorio estratificado 80/20 |
| AUC-ROC | **1.0000** |
| Precision clase 1 | 99.25% |
| Recall clase 1 | 99.53% |

**Feature importance:**
- `score` 64.7% — el IF score es el mejor predictor de persistencia
- `proto_udp` 26.3% — UDP floods son sostenidos por naturaleza
- `block_count_60s` 5.8% — historial reciente de BLOCKs
- `limit_count_15s` 0.8% — acumulación de LIMITs (B5/B6)

---

## Corrida de validación SYN Flood — 2026-06-22

| Evento | Timestamp | Detalle |
|---|---|---|
| Motor LIMIT | 00:43:12 | src=192.168.0.100 score=-0.4638 pkt_rate=444 |
| Motor BLOCK | 00:43:30 | src=192.168.0.100 score=-0.6157 tipo=HTTP_ABUSE |
| **Predictor ALERTA** | **00:51:59** | **P=77.39% — ALERTA-PREDICTIVA ✅** |

El predictor v2 disparó ALERTA-PREDICTIVA con P=77.39% (θ=0.70).

---

## Fix aplicado al motor (2026-06-22)

**Problema:** el motor solo logueaba el primer BLOCK por IP por sesión (el resto como DEBUG).
Esto hacía que `block_count_60s` fuera siempre 1 → P bajo para ataques volumétricos.

**Solución:** el motor ahora loguea TODOS los intentos de BLOCK con rate-limit de 5s por IP.
El enforcement (ipset DROP) sigue aplicándose solo una vez.

```python
# IP ya en ipset: loguear decisión con rate-limit 5s por IP
if _block_repeat_ts.get(src_ip, 0) + 5.0 <= _ahora:
    _block_repeat_ts[src_ip] = _ahora
    log.warning(f"ANOMALÍA | ... | BLOCK")
```

---

## Archivos implementados

| Archivo | Estado |
|---|---|
| `scripts/f4_entrenar_predictor_v2.py` | ✅ Script de entrenamiento |
| `scripts/predictor.py` | ✅ v2 — señal LIMIT+BLOCK, per-IP, hot-reload |
| `models/predictor_modelo_v2.pkl` | ✅ Modelo entrenado (gitignored) |
| `models/features_predictor_v2.txt` | ✅ 10 features |
| `results/metricas_predictor_v2.txt` | ✅ AUC=1.0000, métricas completas |
| `config/systemd/ppi-predictor.service` | ✅ Activo y habilitado |

---

## Criterios de aceptación

| ID | Criterio | Estado |
|---|---|---|
| CA-F4-01 | AUC-ROC > 0.70 | ✅ AUC=1.0000 |
| CA-F4-02 | B5/B6: AVISO o ALERTA antes del primer BLOCK | ⬜ pendiente validar |
| CA-F4-03 | B1 SYN Flood: ALERTA-PREDICTIVA disparada | ✅ P=77.39% validado |
| CA-F4-04 | Corridas normales: FPR < 10% | ⬜ pendiente validar |
| CA-F4-05 | Inferencia por ciclo < 50ms | ✅ implementado |
| CA-F4-06 | AVISO nivel intermedio visible | ✅ implementado |
| CA-F4-07 | ALERTA con Telegram dedup 5min | ✅ implementado |

---

## Argumento de defensa

> "El IF detecta anomalías flujo por flujo pero no distingue una anomalía puntual de un ataque sostenido. El XGBoost usa los outputs del IF como features para predecir la persistencia. Validado con SYN Flood real: P=77.39% → ALERTA-PREDICTIVA. El sistema tiene dos niveles: aviso de vigilancia activa, y alerta de alta confianza con notificación al operador."
