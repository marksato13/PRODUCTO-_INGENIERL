# F6 — Especificación Técnica: Validación del Sistema

## Objetivo
Validar el sistema completo mediante 40 corridas organizadas en 4 grupos, midiendo disponibilidad del servicio, ausencia de interrupción a tráfico legítimo, tiempo de detección y contención del ataque.

## Scripts involucrados

| Script | Entrada | Proceso | Salida |
|---|---|---|---|
| `scripts/f6_corridas.py` | Motor activo + Kali accesible | Orquesta 40 corridas, mide métricas | `results/resultados_f6_completo.csv`, CSVs por grupo |
| `scripts/generar_graficas_f6.py` | `resultados_f6_completo.csv` | Genera 7 figuras matplotlib 300 DPI | `results/graficas_f6/f6_0[1-7]_*.png` |
| `scripts/auc_por_escenario.py` | scores + labels de test.csv | AUC por escenario B1-B6, C1-C3 | `results/reports/auc_por_escenario.txt` |

## Diseño de las 40 corridas

| Grupo | Corridas | Descripción | Criterio de éxito |
|---|---|---|---|
| Normal | 1–10 | Solo tráfico Desktop normal | `flows_anom=0`, `disp=1`, `itl=0` |
| Mixto | 11–20 | Normal + ataques alternados | Corrida 11 detecta ataque; 12–20 IP contenida |
| Reeval | 21–30 | Re-evaluación con IP bloqueada | `disp=1` en todas, motor retiene bloqueo |
| Final | 31–40 | Confirmación de contención | `disp=1`, `itl=0` en todas |

Duración por corrida: **300 s** (5 min) + 60 s de pausa entre corridas.
Duración total F6: ~4 horas.

## Métricas medidas por corrida (columnas del CSV)

| Campo | Descripción |
|---|---|
| `disponibilidad` | 1 si servicio nginx accesible durante el ataque |
| `flows_anom` | Flows con WARNING en motor log (ANOMALÍA/SOSPECHOSO/HTTP-ABUSE/BRUTE-FORCE) |
| `bloqueados` | IPs únicas en ipset ppi_blocked |
| `limitados` | IPs únicas en ipset ppi_limited |
| `lead_time_s` | Segundos desde inicio de ataque hasta primera alerta |
| `mttc_s` | Mean Time To Contain (= lead_time en este diseño) |
| `tie_pct` | Time In Exposure (%) — fracción de corrida con ataque activo sin contener |
| `itl_pct` | Interrupción Tráfico Legítimo (%) — siempre 0% en las 40 corridas |

> **Nota sobre `flows_normal`:** campo acumulativo total desde inicio de F6, no por corrida.
> **Nota sobre `latencia_ms`:** latencia acumulada de la ventana de análisis completa (~316 s), no por flow individual. La latencia por flow individual es P95=34.8 ms (ver `results/latencia_pipeline.txt`).

## Resultados finales validados (2026-06-16)

| Métrica | Valor | Requisito |
|---|---|---|
| Disponibilidad | **100%** (40/40) | > 99% ✓ |
| ITL global | **0%** | = 0% ✓ |
| Lead Time detección | **61.92 s** (corrida 11) | < 120 s ✓ |
| Flows procesados totales | 312,500 | — |
| Latencia P95 | 34.8 ms | < 500 ms ✓ |
| AUC-ROC | 0.8998 | > 0.85 ✓ |

## Figuras generadas

| Archivo | Contenido |
|---|---|
| `f6_01_disponibilidad.png` | Disponibilidad 100% en 40 barras verdes |
| `f6_02_flows_anomalos.png` | Corrida 11 destacada — única con detección |
| `f6_03_timeline_deteccion.png` | Timeline SYN Flood → LIMIT → BLOCK a t=62s |
| `f6_04_itl.png` | ITL=0% en todas las corridas |
| `f6_05_flujos_acumulados.png` | 0 → 312,500 flows procesados |
| `f6_06_latencia_pipeline.png` | Distribución 34–39 ms vs umbral 500 ms |
| `f6_07_panel_resumen.png` | Panel ejecutivo 2×3 con todas las métricas |

## Secuencia de ejecución F6
```bash
# En sensor — motor debe estar activo
sudo systemctl start ppi-motor.service

# Lanzar validación (tarda ~4 horas)
cd /home/m4rk/ppi-surikata-producto
nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/f6_corridas.py > /tmp/f6_log.txt 2>&1 &

# Monitorear
tail -f /tmp/f6_log.txt

# Generar gráficas al terminar
/home/m4rk/ppi-sensor/venv/bin/python3 scripts/generar_graficas_f6.py
```
