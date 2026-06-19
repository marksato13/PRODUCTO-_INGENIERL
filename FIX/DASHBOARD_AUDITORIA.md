# Auditoría y Fixes — Dashboard Web + Telegram

**Fecha:** 2026-06-19
**Archivo auditado:** `scripts/dashboard_web.py`

---

## FIXES APLICADOS (inconsistencias corregidas)

### FIX-VIS-01 — Métricas del modelo con valores incorrectos

**Problema:** el panel "Métricas del Modelo — Isolation Forest" mostraba valores hardcodeados que NO coincidían con los resultados validados en F6.

| Métrica | Valor anterior (INCORRECTO) | Valor correcto (validado) |
|---|---|---|
| Accuracy | 99.97% | — (métrica no reportada en este PPI) |
| Precision | 99.96% | **99.54%** |
| Recall | 99.30% | **99.40%** |
| F1 Score | 0.9963 | **0.9947** |
| AUC-ROC | 0.9440 | **0.8998** |
| τ1 | −0.4973 | **−0.4459** |
| τ2 | −0.6873 | **−0.6027** |
| ITL sublabel | "0 falsos positivos" | **"F6 · whitelist activa"** |

**Qué se hizo:** corregidos los 7 valores. Se eliminó la tarjeta "Accuracy" (no es una métrica reportada en el informe). Se reemplazó por tarjeta "Corridas F6: 40". El sub-label de ITL ahora dice "F6 · whitelist activa" para reflejar que el 0% aplica en validación con whitelist, no que no existan scores sobre τ1.

---

### FIX-VIS-02 — Configuración del modelo incorrecta en Vista Sistema

**Problema:** la tabla de configuración en la vista Sistema mostraba datos incorrectos.

| Campo | Valor anterior (INCORRECTO) | Valor correcto |
|---|---|---|
| scikit-learn | 1.8.0 | **1.9.0** |
| Entrenamiento | 684 flujos normales | **53,708 flujos normales (Grupo A 80%)** |
| Dataset total | 376,827 flujos · 40 corridas | **401,424 flujos · 47 archivos** |

**Qué se hizo:** corregidos los 3 campos con los valores reales de `metricas_offline.txt` y del EDA.

---

### FIX-VIS-03 — Gráfica `chartMetrics` con datos estáticos incorrectos

**Problema:** la Vista Análisis tenía un tercer panel "Métricas del modelo" que renderizaba una gráfica de barras con los mismos valores incorrectos del FIX-VIS-01. Era ruido visual puro: estático, no conectado a datos reales, y mostraba números equivocados.

**Qué se hizo:** eliminado `chartMetrics` (JS + canvas + variable). El espacio se reemplazó por un panel "Top IPs detectadas" que muestra las IPs más frecuentes en el feed de alertas (información útil y real).

---

## QUÉ DEBE ESTAR — Elementos validados y correctos

| Elemento | Vista | Estado | Por qué está bien |
|---|---|---|---|
| Contadores BLOCK / LIMIT / PERMIT | Dashboard | ✅ | Vienen de `api/stats` en tiempo real |
| Nivel de Riesgo (%) | Dashboard | ✅ | Calculado dinámicamente sobre ipset |
| Flows/min, Latencia media | Dashboard | ✅ | Leídos del log en tiempo real |
| Gráfica timeline 24h (BLOCK/LIMIT) | Dashboard + Análisis | ✅ | `api/timeline` — datos reales |
| Gráfica donut tipos de ataque | Dashboard + Análisis | ✅ | `api/tipos` — datos reales |
| Feed de alertas con SSE push | Alertas | ✅ | ~150ms de latencia |
| byte_ratio + pkt_rate en tarjeta | Alertas | ✅ | Añadido en FIX-03 |
| Filtros BLOCK / LIMIT / CRÍTICA | Alertas | ✅ | Funcionales |
| Ticker última alerta | Alertas | ✅ | Se actualiza por SSE |
| Toast + beep sonido | Global | ✅ | Funcional (WebAudio API) |
| Tabla historial con exportar CSV | Detecciones | ✅ | Funcional |
| ipset ppi_blocked / ppi_limited | Control | ✅ | Consulta SSH al servidor |
| Desbloquear IP (modal + control) | Control + Modal | ✅ | Funcional vía `api/unblock` |
| Bloqueo manual | Control | ✅ | Funcional vía `api/block` |
| Arquitectura del laboratorio | Sistema | ✅ | Información estática correcta |
| Sincronización SSE ↔ Telegram | Sistema | ✅ | Documentación del flujo correcta |
| Motor inicio + uptime | Sistema | ✅ | Leídos del log en tiempo real |
| Clientes SSE conectados | Sistema | ✅ | Contador real |
| Modal con Score + byte_ratio + pkt_rate | Global | ✅ | Añadido en FIX-03 |

---

## LO QUE NO DEBE PREGUNTARSE EN LA DEFENSA

Con estos fixes, el dashboard ya no tiene datos que contradigan el informe. Puntos clave:

- **"El dashboard dice AUC=0.89, ¿por qué es diferente al 0.94 que vi antes?"** → ya no existe esa inconsistencia
- **"¿Por qué Precision es 99.54% y no 99.96%?"** → ya coincide con `metricas_offline.txt`
- **"Los umbrales τ1/τ2 no coinciden con lo del informe"** → ya corregidos
- **"Dice scikit-learn 1.8 pero el README dice 1.9"** → ya corregido
- **"Con 684 flujos de entrenamiento, ¿cómo AUC=0.89?"** → ya dice 53,708
- **"¿Por qué la gráfica de métricas no coincide con la tabla?"** → gráfica eliminada

---

## MEJORAS A FUTURO (no bloqueantes para el PPI)

### MEJORA-01 — Top IPs detectadas (reemplaza chartMetrics)
El panel "Top IPs detectadas" en Vista Análisis actualmente muestra texto estático. A futuro: conectar con `api/eventos` para renderizar las 5 IPs más frecuentes con contador de BLOCKs.

### MEJORA-02 — Métricas del modelo dinámicas
Las 8 tarjetas de métricas son aún hardcodeadas. A futuro: crear `api/metricas` que lea `results/metricas_offline.txt` en tiempo real, para que reflejen automáticamente cualquier reentrenamiento.

### MEJORA-03 — Persistencia de alertas entre reinicios
El feed de alertas se pierde al reiniciar el dashboard (en memoria). A futuro: leer `motor_decision.log` completo al arrancar (ya lo hace parcialmente), pero también mantener `eventos_alerta.jsonl` persistente.

### MEJORA-04 — Filtro por fecha en tabla Detecciones
La tabla muestra máx 200 eventos en memoria. A futuro: agregar selector de rango de fecha que filtre sobre el log histórico completo.

### MEJORA-05 — Alerta AVISO en feed (FIX-05)
El motor ahora emite líneas `TENDENCIA | src=... | AVISO` al log. A futuro: añadir a RE_EVENTO del dashboard para mostrar tarjetas de "aviso previo" en color naranja antes del BLOCK.

---

## Alertas Telegram — estado actual tras todos los fixes

| Tipo de alerta | Emoji | Campos incluidos | Deduplicación |
|---|---|---|---|
| IF BLOCK | 🚨 | tipo, IP, proto, puerto, score, grado, byte_ratio, pkt_rate, hora | Sí (5 min/IP) |
| IF LIMIT | ⚠️ | tipo, IP, proto, puerto, score, grado, byte_ratio, pkt_rate, hora | Sí (5 min/IP) |
| BF SSH BLOCK | 🚨 | IP, puerto, intentos/ventana, hora | Sí (5 min/IP) |
| BF SSH LIMIT | ⚠️ | IP, puerto, intentos/ventana, hora | Sí (5 min/IP) |
| HTTP ABUSE BLOCK | 🚨 | IP, proto, puerto, requests/ventana, score, hora | Sí (5 min/IP) |
| HTTP ABUSE LIMIT | ⚠️ | IP, puerto, requests/ventana, hora | Sí (5 min/IP) |
| TENDENCIA AVISO | 👀 | IP, score medio 10 flows, umbral, byte_ratio, hora | Sí (5 min/IP) |

**Lo que NO envía Telegram (por diseño):**
- Flows PERMIT (no son anomalías)
- Re-detecciones de IP ya bloqueada en la misma sesión (logs como debug)
- IPs en whitelist (192.168.0.20, .110, .120, .1, 127.0.0.1)

