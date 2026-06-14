# FASE 6 — Validación y Experimentación

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fecha de ejecución:** 2–4 de junio 2026  

---

## Objetivo de la fase

Validar el sistema completo mediante 40 corridas de experimentación controlada, midiendo las métricas de rendimiento definidas en el plan: disponibilidad, impacto en tráfico legítimo (ITL), tasa de intervención efectiva (TIE), Lead Time, MTTC y latencia de decisión.

---

## 1. Diseño experimental — 40 corridas

Se ejecutaron 40 corridas organizadas en 4 grupos de 10, con duración de 5 minutos cada una:

| Grupo | Corridas | Descripción | Escenarios |
|---|---|---|---|
| **Normal** | 1–10 | Solo tráfico legítimo | A1-A4 desde Desktop |
| **Mixto** | 11–20 | Tráfico legítimo + ataque | A + B simultáneos |
| **Re-evaluación** | 21–30 | Re-validación con τ1/τ2 | A + B simultáneos |
| **Final** | 31–40 | Corridas finales definitivas | A + B simultáneos |

**Script de automatización:** `scripts/f6_corridas.py` y `scripts/f6_corridas_mixtas.py`

**Pausa entre corridas:** 60 segundos.

---

## 2. Métricas medidas por grupo

**Archivos de resultados:**
- `results/resultados_normal.csv`
- `results/resultados_mixto.csv`
- `results/resultados_reeval.csv`
- `results/resultados_final.csv`
- `results/resultados_f6_completo.csv` (40 corridas consolidadas)

| Grupo | Corridas | Disponibilidad | Lead Time | MTTC | TIE | ITL |
|---|---|---|---|---|---|---|
| **Normal (1-10)** | 10 | **100%** | N/A | N/A | N/A | **0%** |
| **Mixto (11-20)** | 10 | **100%** | **26.0s** | **28.0s** | **100%** | **0%** |
| **Reeval (21-30)** | 10 | **100%** | **26.0s** | **28.0s** | **100%** | **0%** |
| **Final (31-40)** | 10 | **100%** | **26.0s** | **28.0s** | **100%** | **0%** |

### Definición de métricas

| Métrica | Definición | Valor obtenido |
|---|---|---|
| **Disponibilidad** | % de corridas donde el servidor respondió (HTTP 200) | 100% |
| **ITL** | % de flows legítimos afectados por el sistema | 0% |
| **TIE** | % de anomalías detectadas que recibieron acción | 100% |
| **Lead Time** | Segundos desde inicio ataque hasta primera detección | 26s |
| **MTTC** | Segundos desde inicio ataque hasta primera acción aplicada | 28s |
| **Latencia** | Tiempo de procesamiento por flow en el motor | 34.8ms P95 |

> **Nota metodológica:** El Lead Time de 26s incluye el **timeout de flow de Suricata** (~15-20s), que es el tiempo que Suricata espera antes de registrar un flow cerrado en eve.json, más el tiempo de procesamiento del motor (<1s). El valor fue validado en la sesión de validación en vivo del 2026-06-02 19:47 con el escenario A2+B2.

---

## 3. Corridas de tráfico normal (1-10)

**Objetivo:** Verificar que el sistema no impacta el tráfico legítimo.

**Tráfico generado:** curl HTTP, wget, SSH legítimo desde Desktop (192.168.0.20).

| Resultado | Valor |
|---|---|
| Disponibilidad del servidor | 100% (10/10 corridas) |
| Impacto en tráfico legítimo (ITL) | **0%** |
| Falsas alarmas en SSH | **0%** |
| Falsas alarmas en transferencia | **0%** |
| Latencia media del motor | 6.6 ms |

Los flows del Desktop fueron clasificados como PERMIT en todos los casos. El motor no aplicó ninguna acción de bloqueo o limitación durante las corridas normales.

---

## 4. Corridas mixtas (11-40)

**Objetivo:** Verificar detección y respuesta con tráfico normal y anómalo coexistiendo.

**Ataques ejecutados por corrida (rotación):** synflood, portscan, udpflood, httpabuse, synflood, portscan, udpflood, httpabuse, synflood, portscan.

| Resultado | Valor |
|---|---|
| Disponibilidad del servidor | 100% (30/30 corridas) |
| Flows anómalos detectados | ~680–702 por corrida |
| TIE (anomalías con acción aplicada) | **100%** |
| Lead Time | **26.0 segundos** |
| MTTC | **28.0 segundos** |
| ITL | **0%** |

---

## 5. Validación en vivo — Escenario A2 + B2

**Fecha:** 2026-06-02 · 19:41–19:50  
**Fuente:** `results/motor_decision.log`

Se ejecutaron simultáneamente:
- **A2:** SSH legítimo desde Desktop (192.168.0.20) hacia servidor
- **B2:** Port scan nmap -sS desde Kali (192.168.0.100)

| Flujo | Clasificación | Acción | Score |
|---|---|---|---|
| Desktop → Server:22 (SSH normal) | PERMIT | Sin acción | -0.434 |
| Kali → Server:* (port scan) | ANOMALÍA | **BLOCK** | -0.655 |

**Resultados:**
- SSH legítimo: **0 falsas alarmas** ✓
- Port scan: **1,705/1,705 flows detectados** (100%) ✓
- Bloqueo automático en el **1er flow** anómalo ✓
- Separación de scores: **0.221 unidades** (normal -0.434 vs. anómalo -0.655)

---

## 6. Validación de detectores temporales

### Brute Force SSH
**Fecha:** 2026-06-03 18:50 · **Fuente:** `results/motor_decision.log`

```
2026-06-03 18:50:03 | WARNING | BRUTE-FORCE | src=192.168.0.100
dst=192.168.0.120:22 proto=TCP intentos=15/60s | BLOCK → BLOCKED 192.168.0.100
```

- **Ataque:** 25 intentos SSH simultáneos desde Kali
- **Detección:** 15 intentos en 60 segundos → BLOCK automático
- **Alerta Telegram:** Enviada y recibida ✓

### HTTP Abuse
**Fecha:** 2026-06-04 15:10 · **Fuente:** `results/motor_decision.log`

```
2026-06-04 15:10:28 | WARNING | HTTP-ABUSE | src=192.168.0.100
dst=192.168.0.120:80 proto=TCP requests=100/30s | BLOCK → BLOCKED 192.168.0.100
```

- **Ataque:** curl en bucle continuo desde Kali
- **Detección:** 100 requests en 30 segundos → BLOCK automático
- **Alerta Telegram:** Enviada y recibida ✓

### Validación LIMIT
```
2026-06-03 23:28:58 | WARNING | SOSPECHOSO | src=192.168.0.100
dst=192.168.0.120:80 proto=TCP score=-0.4985 | LIMIT → LIMITED 192.168.0.100
```

- HTTP abuse lento con score entre τ2 y τ1 → acción LIMIT (no BLOCK)
- Tráfico de la IP limitado a **100 paquetes/segundo** ✓

---

## 7. Escenarios mixtos Grupo C

| Escenario | Tráfico normal | Tráfico anómalo | Resultado |
|---|---|---|---|
| C1 | HTTP curl (Desktop) | SYN Flood hping3 (Kali) | Flood LIMIT/BLOCK · HTTP sin impacto ✓ |
| C2 | SSH legítimo (Desktop) | Port scan nmap (Kali) | Scan BLOCK · SSH PERMIT ✓ |
| C3 | Wget descargas (Desktop) | UDP Flood hping3 (Kali) | UDP BLOCK · descargas sin impacto ✓ |

---

## 8. Métricas globales finales del modelo

**Archivo:** `results/reports/reporte_validacion_fase6.txt`  
**Archivo:** `results/reporte_validacion_final.pdf`

| Métrica | Valor |
|---|---|
| **Recall (Detección)** | **87.6%** |
| **Precisión** | **99.96%** |
| **F1-Score** | **0.9338** |
| AUC-ROC global | 0.9440 |
| Tasa Falsos Positivos | 5.1% |
| FP en SSH legítimo | **0%** |
| FP en transferencia | **0%** |
| Latencia pipeline P95 | **34.8 ms** (< 500ms requerido ✓) |
| Disponibilidad (40 corridas) | **100%** |
| ITL (impacto tráfico legítimo) | **0%** |
| TIE (tasa intervención efectiva) | **100%** |
| Lead Time | **26 segundos** |
| MTTC | **28 segundos** |

---

## 9. Limitaciones documentadas

**Archivo:** `results/reports/reporte_validacion_fase6.txt` (sección 6)

### a) Brute Force SSH — solución implementada

- **Modelo base:** detección ~1% (flows SSH individuales similares al tráfico normal)
- **Solución:** Detector temporal en F4 (ventana 60s, 15 intentos → BLOCK)
- **Resultado:** Detección elevada a **~90%** en validación en vivo

### b) HTTP Abuse lento — solución implementada

- **Modelo base:** detección 31% (curl lento imita HTTP normal)
- **Solución:** Detector temporal en F4 (ventana 30s, 100 requests → BLOCK)
- **Resultado:** Detección elevada a **~80%** en validación en vivo

### c) Balance de datos de entrenamiento

Durante la fase se descubrió que Isolation Forest es sensible al balance del dato de entrenamiento: agregar más datos normales de SSH cambió la distribución de features y redujo la separación normal/anomalía. El modelo final usa **684 flows normales filtrados** que maximizan esta separación (0.229 unidades).

---

## 10. Archivos entregables generados

| Entregable | Archivo | Descripción |
|---|---|---|
| Resultados corridas normales | `results/resultados_normal.csv` | 10 corridas, ITL=0% |
| Resultados corridas mixtas | `results/resultados_mixto.csv` | 10 corridas, TIE=100% |
| Resultados re-evaluación | `results/resultados_reeval.csv` | 10 corridas |
| Resultados finales | `results/resultados_final.csv` | 10 corridas |
| Consolidado F6 | `results/resultados_f6_completo.csv` | **40 corridas** |
| Umbrales finales | `results/umbrales_finales.txt` | τ1, τ2 y detectores |
| Reporte validación | `results/reports/reporte_validacion_fase6.txt` | Reporte formal |
| **PDF final** | `results/reporte_validacion_final.pdf` | **Entregable principal** |
| **MVP** | `results/MVP_funcional.zip` | **ZIP completo del sistema** |

---

## 11. Criterios de cierre de F6

| Criterio | Estado |
|---|---|
| 10 corridas tráfico normal · disponibilidad ≥ 99% | ✅ 100% |
| 10 corridas mixtas · Lead Time medido | ✅ 26s |
| 10 corridas re-evaluación τ1/τ2 | ✅ |
| 10 corridas finales | ✅ |
| ITL ≤ 2% verificado | ✅ 0% |
| TIE medido | ✅ 100% |
| Latencia pipeline < 500ms | ✅ 34.8ms |
| Disponibilidad 100% en las 40 corridas | ✅ |
| Escenarios mixtos C1-C3 completados | ✅ |
| Validación en vivo A2+B2 exitosa | ✅ |
| Detectores temporales validados en vivo | ✅ |
| Telegram validado (brute force + HTTP abuse) | ✅ |
| `reporte_validacion_final.pdf` generado | ✅ |
| `MVP_funcional.zip` generado (25 MB, 40 archivos) | ✅ |

**F6 CERRADA ✅ — 4 de junio 2026**

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| `f6_corridas.py` | `scripts/` | Automatización 40 corridas (sensor) |
| `f6_corridas_mixtas.py` | `scripts/` | Corridas mixtas desde Desktop |
| `resultados_*.csv` | `results/` | Resultados por grupo |
| `resultados_f6_completo.csv` | `results/` | **40 corridas consolidadas** |
| `umbrales_finales.txt` | `results/` | Umbrales τ1/τ2 y detectores |
| `reporte_validacion_fase6.txt` | `results/reports/` | Reporte formal F6 |
| `reporte_validacion_final.pdf` | `results/` | **PDF entregable final** |
| `MVP_funcional.zip` | `results/` | **ZIP del sistema completo** |
| `guia_demo_defensa.txt` | `~/Descargas/` | Guía para demo en vivo |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
