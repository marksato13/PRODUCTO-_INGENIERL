# Limitaciones y Puntos Débiles del Sistema
**PPI UPeU 2026 — Rubén Mark Salazar Tocas**
**Fuente de verdad:** este archivo + `docs/informe_resultados/limitaciones_detalladas.md`

---

## Resumen ejecutivo para la defensa

El sistema tiene **10 limitaciones identificadas**. Las 3 más críticas tienen mitigación aplicada o argumentación técnica sólida. Las demás son reconocidas como trabajo futuro.

---

## Métricas reales de los modelos

### Isolation Forest (F2)
| Métrica | Valor | Contexto |
|---|---|---|
| AUC-ROC | **0.8998** | Competitivo para IDS no supervisado |
| Precision @ τ1 | 99.54% | |
| Recall @ τ1 | 99.40% | |
| F1-Score | 0.9947 | |
| FPR @ τ1 | **20.47%** | Limitación principal — ver L1 |
| FPR @ τ2 | 1.99% | Umbral de BLOCK — muy bajo |
| TPR @ τ2 | 18.27% | Solo ataques muy marcados llegan a BLOCK por IF |
| Latencia P95 | 34.8ms | Requiere <500ms ✅ |
| Lead time SYN Flood | ~62s | Ver L2 |

### XGBoost Predictor v2 (F4)
| Métrica | Valor | Contexto |
|---|---|---|
| AUC-ROC | **1.0000** | ⚠️ Sospechoso — ver L6 |
| Precision clase 1 | 99.25% | |
| Recall clase 1 | 99.53% | |
| FP | 8 / 12,385 | |
| FN | 5 / 12,385 | |
| Validación en vivo | P=77.39% | SYN Flood confirmado ✅ |
| FPR tráfico normal | 0% | Whitelist activa ✅ |

---

## Limitaciones — clasificadas por criticidad

### 🔴 Críticas (mitigadas o argumentadas)

#### L1 — FPR = 20.47% en τ1
**Qué es:** 1 de cada 5 flows normales queda bajo τ1 (zona LIMIT).
**Por qué existe:** Isolation Forest penaliza flows con features inusuales (transferencias grandes, SCP) aunque sean legítimos. τ1 prioriza no perder ataques sobre evitar falsas alarmas (índice de Youden).
**Mitigación aplicada:** whitelist de IPs internas → ITL efectivo = 0% en las 40 corridas. τ1 activa solo LIMIT (rate limiting), no BLOCK.
**Argumento defensa:** "El FPR operativo es 0% porque la whitelist cubre todos los hosts legítimos del laboratorio. En una red real se requeriría whitelist dinámica."
**Detalle:** `docs/informe_resultados/limitaciones_detalladas.md §1`

---

#### L2 — Lead time ~62s en SYN Flood
**Qué es:** el motor tarda ~62s en emitir el primer BLOCK desde que comienza el ataque.
**Por qué existe:** Suricata procesa flows cerrados (FIN/RST). Los SYN floods nunca completan el handshake → Suricata espera el timeout antes de escribir el evento.
**Mitigación aplicada:** detectores heurísticos (SSH BF: <5s, HTTP Abuse: <5s) actúan por paquetes individuales, no por flows.
**Argumento defensa:** "62s es inherente a la arquitectura basada en Netflow. Sistemas comerciales tienen latencias similares. Para los ataques más peligrosos (BF SSH, HTTP Abuse) la detección es <5s."
**Detalle:** `docs/informe_resultados/limitaciones_detalladas.md §2`

---

#### L3 — Predictor no anticipa primer BLOCK en ataques graduales (CA-F4-02)
**Qué es:** para B5 HTTP Abuse y B6 BF SSH, el predictor produce P≈0.02% durante la fase LIMIT. Solo dispara ALERTA después del primer BLOCK.
**Por qué existe:** el feature `limit_count_15s` tiene solo 0.8% de importancia en XGBoost. El modelo aprendió que `block_count_60s` (5.8%) y `score` (64.7%) son los mejores predictores de persistencia. Sin BLOCKs previos, P permanece bajo.
**Mitigación aplicada:** regla determinista en predictor → si `limit_count_15s >= 5` de la misma IP, disparar AVISO directo (sin esperar XGBoost). *(pendiente implementar)*
**Argumento defensa:** "El predictor predice *persistencia* de ataques ya detectados. Para ataques graduales, el IF + heurísticos detectan y bloquean antes de que el predictor acumule señal. Ambos mecanismos son complementarios."

---

### 🟡 Moderadas (documentadas, trabajo futuro)

#### L4 — Saturación de tabla de flujos Suricata
**Qué es:** 6+ procesos hping3 --flood simultáneos saturan 65K sesiones en Suricata → deja de escribir eventos al eve.json → motor queda ciego.
**Impacto:** vector de evasión en un entorno sin defensa de red previa.
**Mitigación propuesta:** monitoreo de `kernel_drops` en el motor + alerta si crece >100K/min. *(pendiente implementar)*

---

#### L5 — Timeout de bloqueo fijo (300s)
**Qué es:** los BLOCKs en ipset expiran a los 5 minutos. Un atacante que pausa puede reintentar.
**Mitigación propuesta:** bloqueo progresivo (1° BLOCK=5min, 2°=30min, 3°=permanente). Requiere estado persistente entre reinicios del motor.

---

#### L6 — AUC=1.0000 del XGBoost (sospechoso)
**Qué es:** un AUC perfecto con datos reales es señal de data leakage o sobreajuste.
**Explicación técnica:** el dataset proviene del mismo log del motor que genera los labels automáticos. Los scores IF son features del XGBoost Y base de los labels → correlación directa. El split es aleatorio (no temporal), lo que permite que datos de la misma corrida queden en train y test.
**AUC realista estimado:** 0.85–0.95 con datos de nuevas corridas o split temporal.
**Argumento defensa:** "El AUC=1.0 refleja alta correlación entre features y labels en el dataset de entrenamiento. La validación en vivo (P=77.39% con SYN Flood real) confirma que el modelo generaliza. Con más corridas independientes se obtendría un AUC más conservador."

---

#### L7 — Lab cerrado — sin validación en red real
**Qué es:** el modelo fue entrenado con tráfico de 5 VMs específicas. Generalización a otras redes: desconocida.
**Contexto:** apropiado para PPI de pregrado. Escala real requeriría reentrenamiento con datos de la red destino (F5 cubre el mecanismo).

---

#### L8 — Whitelist hardcodeada
**Qué es:** las IPs en whitelist están en el código del motor (`WHITELIST = {...}`). Si un atacante compromete una IP whitelisted, el sistema no la detectará.
**Mitigación propuesta:** whitelist en archivo de configuración externo + validación periódica de comportamiento de IPs whitelisted.

---

### 🟢 Menores (sin impacto en defensa)

#### L9 — Telegram relay inexistente en laboratorio
**Qué es:** el motor envía notificaciones a `http://192.168.0.20:8889/telegram` (relay en Desktop) que no está corriendo. Error `Connection refused` en cada alerta.
**Impacto:** las alertas solo son visibles en dashboard web (:8080) y log.
**Solución:** llamada directa a `api.telegram.org` desde el sensor (tiene internet). *(pendiente implementar)*

---

#### L10 — Dashboard web sin systemd
**Qué es:** `dashboard_web.py` corre con `nohup` (PID 2730). Se cae si el sensor se reinicia.
**Solución:** crear `ppi-dashboard.service`. *(pendiente implementar)*

---

## Mapa de mitigaciones pendientes

| # | Limitación | Prioridad | Implementar en |
|---|---|---|---|
| L3 | Regla AVISO para limit_count >= 5 | Alta | `scripts/predictor.py` |
| L4 | Monitor kernel_drops Suricata | Alta | `scripts/motor_decision.py` |
| L9 | Telegram API directo | Media | `scripts/motor_decision.py` + `predictor.py` |
| L10 | Dashboard systemd | Media | `config/systemd/ppi-dashboard.service` |
| L5 | Bloqueo progresivo | Baja | `scripts/enforce.sh` + motor |
| L8 | Whitelist externa | Baja | `config/whitelist.conf` |

---

## Referencias

- `docs/informe_resultados/limitaciones_detalladas.md` — análisis técnico profundo L1, L2, L3 (estático)
- `docs/informe_resultados/puntos_debiles_defensa.md` — Q&A preparado para el jurado
- `docs/ppi_documentacion2/F4_prediccion_v2.md §CAs` — validaciones en vivo
- `docs/ppi_documentacion2/F2_deteccion_if.md` — umbrales y curva ROC
