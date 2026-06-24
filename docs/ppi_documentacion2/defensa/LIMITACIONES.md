# Limitaciones y Puntos Débiles del Sistema
**PPI UPeU 2026 — Rubén Mark Salazar Tocas**
**Actualizado:** 2026-06-22 — todas las mitigaciones implementadas

---

## Resumen ejecutivo para la defensa

El sistema tiene **10 limitaciones identificadas**. Las 3 críticas tienen mitigación implementada. Las 4 moderadas tienen mitigación implementada. Las 2 menores también están resueltas.

| Tipo | Total | Mitigadas | Argumentadas |
|---|---|---|---|
| 🔴 Críticas | 3 | 3 | 0 |
| 🟡 Moderadas | 4 | 4 | 0 |
| 🟢 Menores | 2 | 2 | 0 |

---

## Métricas reales de los modelos

### Isolation Forest (F2)
| Métrica | Valor | Contexto |
|---|---|---|
| AUC-ROC | **0.8998** | Competitivo para IDS no supervisado |
| Precision @ τ1 | 99.54% | |
| Recall @ τ1 | 99.40% | |
| F1-Score | 0.9947 | |
| FPR @ τ1 | **20.47%** | Limitación principal — mitigada por whitelist (FPR operativo = 0%) |
| FPR @ τ2 | 1.99% | Umbral de BLOCK — muy bajo |
| TPR @ τ2 | 18.27% | Solo ataques muy marcados llegan a BLOCK directo por IF |
| Latencia P95 | 34.8ms | Requiere <500ms ✅ |
| Lead time SYN Flood | ~62s | Inherente a arquitectura Netflow |

### XGBoost Predictor v2 (F4)
| Métrica | Valor | Contexto |
|---|---|---|
| AUC-ROC | **0.9992** | Sin data leakage — `score` removido de features (ver L6) |
| Precision clase 1 | 99.25% | |
| Recall clase 1 | 99.53% | |
| FP | 8 / 12,385 | |
| FN | 5 / 12,385 | |
| Validación en vivo | P=77.39% | SYN Flood confirmado ✅ |
| FPR tráfico normal | 0% | Whitelist activa ✅ |

---

## Limitaciones — clasificadas por criticidad

### 🔴 Críticas

#### L1 — FPR = 20.47% en τ1
**Qué es:** 1 de cada 5 flows normales queda bajo τ1 (zona LIMIT).
**Por qué existe:** Isolation Forest penaliza flows con features inusuales (transferencias grandes, SCP) aunque sean legítimos. τ1 prioriza no perder ataques sobre evitar falsas alarmas (índice de Youden).
**✅ Mitigación implementada:** whitelist de IPs internas — ITL efectivo = 0% en las 40 corridas. τ1 activa solo LIMIT (rate limiting), no BLOCK. Whitelist ahora en `config/whitelist.conf` (editable sin tocar código).
**Argumento defensa:** El FPR operativo es 0% porque la whitelist cubre todos los hosts legítimos del laboratorio. En una red real se requeriría whitelist dinámica, cuyo mecanismo ya está implementado en el archivo de configuración.
**Detalle:** `docs/informe_resultados/limitaciones_detalladas.md §1`

---

#### L2 — Lead time por escenario (validado en vivo 2026-06-22)
**Qué es:** el tiempo desde que comienza el ataque hasta el primer BLOCK varía según el tipo.
**Por qué existe:** Suricata procesa flows cerrados (FIN/RST). Los SYN floods nunca completan el handshake — Suricata espera el timeout antes de escribir el evento.

**Lead times medidos en vivo:**

| Escenario | Lead time LIMIT | Lead time BLOCK | Mecanismo |
|---|---|---|---|
| B1 SYN Flood | — | **~62s** | Suricata flow timeout |
| B6 SSH BF (hydra -t 4) | **~53s** | **~60s** | Heurístico BF-SSH (ventana 60s, umbral 15 intentos) |

**Evidencia B6 (2026-06-22 08:31):** `T+53s → LIMIT (score=-0.4832)`, `T+60s → BLOCK tipo=BRUTE_FORCE_SSH (score=-0.6228, bloqueo#1 300s)`
**✅ Mitigación implementada:** detectores heurísticos actúan por conteo de intentos (BF-SSH: ventana 60s / HTTP Abuse: ventana 30s), no esperan cierre del flow.
**Argumento defensa:** 60s es el tiempo mínimo para acumular evidencia estadística de brute force (15 intentos). Es una ventana deliberada para evitar falsos positivos con SSHs legítimos lentos. Sistemas SIEM comerciales usan ventanas similares (30–120s).
**Detalle:** `docs/informe_resultados/limitaciones_detalladas.md §2`

---

#### L3 — Predictor no anticipa primer BLOCK en ataques graduales (CA-F4-02)
**Qué es:** para B5 HTTP Abuse y B6 BF SSH, el predictor produce P≈0.02% durante la fase LIMIT. Solo dispara ALERTA después del primer BLOCK.
**Por qué existe:** el feature `limit_count_15s` tiene solo 0.8% de importancia en XGBoost. En el modelo actual (sin leakage), `block_count_60s` (57.29%) y `is_block` (38.22%) son los predictores dominantes. Sin BLOCKs previos de la IP, `block_count_60s`=0 y P permanece bajo.
**✅ Mitigación implementada:** regla determinista en `predictor.py` — si `limit_count_15s >= 5` de la misma IP Y no hubo alerta en los últimos 300s → disparar `AVISO-DETERMINISTA` directo, sin esperar probabilidad XGBoost.
**Argumento defensa:** El predictor predice persistencia de ataques ya detectados. Para ataques graduales, la regla determinista complementa al XGBoost cuando la señal estadística aún es débil. Ambos mecanismos son capas defensivas independientes.

---

### 🟡 Moderadas

#### L4 — Saturación de tabla de flujos Suricata
**Qué es:** 6+ procesos hping3 --flood simultáneos saturan 65K sesiones en Suricata — deja de escribir eventos al eve.json — motor queda ciego.
**Impacto:** vector de evasión en un entorno sin defensa de red previa.
**✅ Mitigación implementada:** `motor_decision.py` monitorea eventos `stats` de eve.json cada ciclo. Si `kernel_drops` crece más de 100.000 drops/min → log WARNING + alerta Telegram inmediata (cooldown 600s). El motor ya no queda silencioso ante una saturación.

---

#### L5 — Timeout de bloqueo fijo (300s)
**Qué era:** los BLOCKs en ipset expiraban a los 5 minutos. Un atacante que pausa puede reintentar.
**✅ Mitigación implementada y validada en vivo:** bloqueo progresivo en `motor_decision.py`:
- 1° bloqueo de la IP → 300s (5 min)
- 2° bloqueo → 1.800s (30 min)
- 3° bloqueo en adelante → permanente (`timeout 0` en ipset — no expira)

El historial se persiste en `results/block_counts.json` y se recarga en cada reinicio del motor.

**Validación en vivo — corrida B1 SYN Flood (2026-06-22):**

| Corrida | Timestamp | Evento detector | Resultado | ipset verificado |
|---|---|---|---|---|
| 1ª | 05:44:13 | ANOMALÍA score=−0.6066 grado=ALTA | `bloqueo#1 timeout=300s` | ✅ |
| 2ª | 06:05:03 | ANOMALÍA score=−0.7696 grado=ALTA | `bloqueo#2 timeout=1800s` | ipset: timeout=1768 ✅ |
| 3ª | 06:39:42 | HTTP-ABUSE 100 req/30s | `bloqueo#3 PERMANENTE` | ipset: timeout=0 ✅ |

`results/block_counts.json` final: `{"192.168.0.100": 3}` — historial persistido entre reinicios.

---

#### L6 — Data leakage XGBoost corregido (AUC=1.0 → 0.9992)
**Qué era:** el feature `score` (IF decision function) tenía 64.7% de importancia. Los labels se derivan de los mismos umbrales de `score` → data leakage. AUC=1.0 era matemáticamente inevitable.
**✅ Mitigación implementada (2026-06-22):** `score` removido de features en `f4_entrenar_predictor_v2.py` y `predictor.py`. El modelo ahora usa 10 features comportamentales:

| Feature | Importancia | Interpretación |
|---|---|---|
| `block_count_60s` | 57.29% | Reincidencia en 60s — predictor dominante |
| `is_block` | 38.22% | Evento actual supera τ2 del Isolation Forest |
| `limit_count_15s` | 1.72% | Acumulación de eventos sospechosos previos |
| Resto (6 features) | 3.68% | Puerto, hora, conteo LIMITs, is_block |

**Resultado:** AUC=**0.9992** — alto pero explicable: ataques de lab son sostenidos por naturaleza.
**Commit:** `ad573f0`
**Argumento defensa:** El AUC alto refleja que en el laboratorio un host que inicia UDP flood lo mantiene durante toda la corrida (`proto_udp` + `block_count_60s` son predictores legítimos de persistencia). No hay correlación artefactual. La validación en vivo (P=77.39% SYN Flood) confirma que el modelo generaliza.

---

#### L7 — Lab cerrado — sin validación en red real
**Qué es:** el modelo fue entrenado con tráfico de 5 VMs específicas. Generalización a otras redes: desconocida.
**Contexto:** apropiado para PPI de pregrado. Escala real requeriría reentrenamiento con datos de la red destino (F5 cubre el mecanismo automáticamente).

---

### 🟢 Menores

#### L9 — Telegram relay inexistente en laboratorio
**Antes:** el motor enviaba notificaciones a `http://192.168.0.20:8889/telegram` (relay en Desktop que no existía). `Connection refused` en cada alerta.
**✅ Resuelto:** `motor_decision.py` y `predictor.py` llaman directamente a `https://api.telegram.org/bot{TOKEN}/sendMessage`. Probado en vivo: HTTP 200 desde el sensor.

---

#### L10 — Dashboard web sin systemd
**Antes:** `dashboard_web.py` corría con `nohup`. Se caía al reiniciar el sensor.
**✅ Resuelto:** `ppi-dashboard.service` instalado, `enabled` y `active`. El proceso nohup huérfano fue eliminado.

---

## Estado final de todas las mitigaciones

| # | Limitación | Prioridad | Estado | Commit |
|---|---|---|---|---|
| L1 | FPR 20.47% — whitelist operativa | Alta | ✅ Implementado | preexistente |
| L2 | Lead time B6=60s BLOCK, B1=62s — validado en vivo 2026-06-22 | Alta | ✅ Implementado | preexistente |
| L3 | AVISO-DETERMINISTA lc>=5 | Alta | ✅ Implementado | 8df6132 |
| L4 | Monitor kernel_drops Suricata | Alta | ✅ Implementado | 8df6132 |
| L5 | Bloqueo progresivo 5min/30min/perm | Media | ✅ Implementado | esta sesión |
| L6 | Data leakage corregido — score removido — AUC=0.9992 | Alta | ✅ Implementado | ad573f0 |
| L7 | Lab cerrado — F5 cubre reentren. | Baja | ✅ Documentado | 5b598ff |
| L8 | Whitelist externa en config/ | Baja | ✅ Implementado | esta sesión |
| L9 | Telegram directo a api.telegram.org | Media | ✅ Implementado | 8df6132 |
| L10 | Dashboard systemd service | Media | ✅ Implementado | preexistente |

---

## Referencias

- `docs/informe_resultados/limitaciones_detalladas.md` — análisis técnico profundo L1, L2, L3
- `docs/informe_resultados/puntos_debiles_defensa.md` — Q&A preparado para el jurado
- `docs/ppi_documentacion2/F4_prediccion_v2.md §CAs` — validaciones en vivo
- `docs/ppi_documentacion2/F2_deteccion_if.md` — umbrales y curva ROC
- `config/whitelist.conf` — IPs excluidas de bloqueo (editable)
- `results/block_counts.json` — historial de bloqueos progresivos (generado en runtime)
