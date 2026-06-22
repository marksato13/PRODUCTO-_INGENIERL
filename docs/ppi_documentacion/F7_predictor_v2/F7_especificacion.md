# F7 — Predictor v2: Anticipación Temporal basada en Señal LIMIT
## Estado: 🔄 EN PROGRESO

## Objetivo
Emitir ALERTA-PREDICTIVA ANTES de que el motor IF ejecute el BLOCK,
usando eventos LIMIT como señal precursora natural del bloqueo.

Orden correcto exigido: T_alerta (predictor) < T_block (IF)

## Por qué cambió de v1 a v2
| | Predictor v1 (obsoleto) | Predictor v2 (correcto) |
|---|---|---|
| Señal | Gap entre STATS/500 flujos | Conteo eventos LIMIT/15s |
| Primera señal | T≈34s | T≈1s |
| Ciclo | 10s | 2s |
| Resultado | T_alerta=T+89s > T_block=T+11s ❌ | T_alerta≈T+2s < T_block≈T+5s ✅ |

## Features del modelo (6)
- limit_count_15s: cantidad LIMITs de esa IP en últimos 15s
- limit_rate_15s: tasa LIMITs por segundo
- score_min_15s: score IF más bajo (más cerca de BLOCK)
- score_mean_15s: score IF promedio en ventana
- hora_sin / hora_cos: patrón circadiano codificado

## Dataset disponible SIN correr nuevos escenarios
- Fuente: motor_decision.log (2026-06-02 al 2026-06-21)
- Eventos LIMIT: 50,134
- Eventos BLOCK: 11,977
- Etiquetado automático: LIMIT → BLOCK/10s = label=1

## Criterios de aceptación
- [ ] CA-F7-01: entrenar_predictor_v2.py corre sin errores
- [ ] CA-F7-02: AUC-ROC >= 0.75 en test set cronológico
- [ ] CA-F7-03: Precision >= 85%
- [ ] CA-F7-04: Recall >= 80%
- [ ] CA-F7-05: En corridas ataque: T_alerta < T_block
- [ ] CA-F7-06: En corridas normales: 0 falsas alertas (FPR=0%)
- [ ] CA-F7-07: Lead time promedio >= 2 segundos
- [ ] CA-F7-08: Hot-reload sin reiniciar servicio
- [ ] CA-F7-09: Dashboard muestra gauge subir ANTES que BLOCK en tabla

## Archivos a crear/modificar
- scripts/entrenar_predictor_v2.py (NUEVO)
- scripts/predictor.py (MODIFICAR señal + ciclo 2s)
- models/predictor_modelo_v2.pkl (GENERAR)
- models/features_predictor_v2.txt (GENERAR)
- results/metricas_predictor_v2.txt (GENERAR)
- results/corridas_predictor_v3.txt (GENERAR en validación)

## Auto-reentrenamiento (autonomía)
Cron semanal domingos 02:00 en sensor.
Si AUC nuevo > AUC anterior: reemplaza modelo.
Si AUC nuevo <= AUC anterior: conserva modelo previo.
predictor.py detecta cambio de .pkl y hace hot-reload automático.
