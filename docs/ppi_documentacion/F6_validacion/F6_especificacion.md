# F6 — Especificación Técnica: Validación del Sistema

## 1. Objetivo

Validar el sistema completo (F1-F5) en condiciones operacionales reales con el
**motor activo**, midiendo disponibilidad del servicio, ausencia de interrupción a
tráfico legítimo (ITL), tiempo de detección y contención del atacante.

> **Nota metodológica:** F6 no valida sobre CSVs estáticos — ejecuta el sistema completo
> en tiempo real con tráfico mixto. `f6_corridas.py` orquesta escenarios y lee el
> `motor_decision.log` para medir cuándo y cómo actuó el motor.

---

## 2. Entradas

| Entrada | Descripción |
|---|---|
| Sistema F1-F5 operativo | Suricata activo, motor iniciado, ipsets en servidor |
| `results/metricas_offline.txt` | τ1/τ2 cargados por el motor al arrancar |
| `models/isolation_forest.pkl` + `scaler.pkl` | Modelo en memoria del motor |
| Desktop 192.168.0.20 | Genera tráfico normal durante todas las corridas |
| Kali 192.168.0.100 | Lanza ataques en corrida 11 (SYN Flood) |

---

## 3. Salidas

| Salida | Ruta | Descripción |
|---|---|---|
| Resultados de 40 corridas | `results/resultados_f6_completo.csv` | Métricas por corrida: disponibilidad, ITL, lead time, etc. |
| 7 figuras PNG | `results/graficas_f6/f6_0[1-7]_*.png` | Visualizaciones 300 DPI para el informe |
| Log del motor | `results/motor_decision.log` | Registro completo de decisiones durante F6 |
| Bitácora | `docs/bitacora/bitacora_escenarios.txt` | Registro de cada corrida ejecutada |

---

## 4. Diseño de las 40 corridas

| Grupo | Corridas | Condición | Criterio de éxito |
|---|---|---|---|
| Normal | 1–10 | Solo tráfico Desktop legítimo | `flows_anom=0`, `disp=1`, `itl=0` |
| Mixto | 11–20 | Normal + SYN Flood (corrida 11) | Corrida 11 detecta y bloquea; 12-20 IP contenida |
| Reeval | 21–30 | Re-evaluación — Kali bloqueada en memoria | `disp=1` en todas, motor retiene bloqueo sin reinicio |
| Final | 31–40 | Confirmación de contención total | `disp=1`, `itl=0` en todas |

- Duración por corrida: **300 s** (5 min)
- Pausa entre corridas: **60 s**
- Duración total F6: **~4 horas**

---

## 5. Scripts involucrados

| Script | Entrada | Proceso | Salida |
|---|---|---|---|
| `scripts/f6_corridas.py` | Motor activo + tráfico real | Orquesta 40 corridas, lee `motor_decision.log` | `results/resultados_f6_completo.csv` |
| `scripts/generar_graficas_f6.py` | `resultados_f6_completo.csv` | Genera 7 figuras matplotlib 300 DPI | `results/graficas_f6/f6_0[1-7]_*.png` |
| `scripts/auc_por_escenario.py` | `data/raw/*_anom_*.gz` + `*_mixto_*.gz` | AUC individual B1-B6 y C1-C3 | `results/reports/auc_por_escenario.txt` |

> `auc_por_escenario.py` lee los archivos `.gz` de Grupo B y C directamente
> (no lee `test.csv` — ese archivo fue eliminado).

---

## 6. Métricas medidas por corrida

| Campo CSV | Descripción |
|---|---|
| `disponibilidad` | 1 si nginx responde durante la corrida, 0 si no |
| `flows_anom` | Flows con WARNING en log del motor (acumulativo desde corrida 11) |
| `bloqueados` | IPs únicas en `ipset ppi_blocked` al final de la corrida |
| `limitados` | IPs únicas en `ipset ppi_limited` al final de la corrida |
| `lead_time_s` | Segundos desde inicio del ataque hasta primera alerta del motor |
| `itl_pct` | % de tráfico legítimo interrumpido (0% en todas las corridas) |

> **`flows_normal`:** acumulativo total desde inicio de F6, no por corrida individual.
> **`latencia_ms`:** latencia acumulada de toda la ventana (~316 s), no por flow.
> La latencia por flow individual (P95=34.8 ms) está en `results/latencia_pipeline.txt`.

> **`flows_anom=0` en corridas 12-40:** comportamiento CORRECTO. Tras la detección
> en corrida 11, el motor retiene `192.168.0.100` en el set in-memory `bloqueados`.
> Los flows subsiguientes se procesan a nivel DEBUG (no WARNING) porque la IP ya está
> contenida. El atacante sigue bloqueado en ipset → disponibilidad = 100%.

---

## 7. Resultados finales validados (2026-06-16)

| Métrica | Valor | Requisito |
|---|---|---|
| Disponibilidad | **100%** (40/40 corridas) | ≥ 99% ✓ |
| ITL global | **0%** | = 0% ✓ |
| Lead Time detección | **61.92 s** (corrida 11, SYN Flood) | < 120 s ✓ |
| Latencia P95 por flow | **34.8 ms** | < 500 ms ✓ |
| AUC-ROC | **0.8998** | ≥ 0.85 ✓ |
| Corridas exitosas | **40/40** | 40/40 ✓ |

**Lead Time de 61.92 s** se explica por el timeout de Suricata para flows TCP
half-open (~60 s) — Suricata no emite el evento `flow` hasta que la conexión
cierra o expira. No es un retraso del motor (latencia=34.8 ms) sino una limitación
del sensor IDS.

---

## 8. Figuras generadas (`results/graficas_f6/`)

| Archivo | Contenido |
|---|---|
| `f6_01_disponibilidad.png` | 40 barras verdes — Disponibilidad 100% en cada corrida |
| `f6_02_flows_anomalos.png` | Corrida 11 destacada — única con detección activa |
| `f6_03_timeline_deteccion.png` | Timeline SYN Flood: t=0s inicio → t=61.9s LIMIT → BLOCK |
| `f6_04_itl.png` | ITL=0% en todas las corridas — sin interrupción legítima |
| `f6_05_flujos_acumulados.png` | Flujos normales acumulados: 0 → 312,500 |
| `f6_06_latencia_pipeline.png` | Distribución 34-39 ms (xlim ajustado) vs umbral 500 ms |
| `f6_07_panel_resumen.png` | Panel ejecutivo 2×3 con todas las métricas clave |

---

## 9. Secuencia técnica de ejecución F6

```bash
# En sensor — motor DEBE estar activo con el modelo correcto
sudo systemctl start ppi-motor.service

# Verificar que cargó τ correctamente
grep "τ1=" results/motor_decision.log | tail -1
# Esperado: τ1=-0.4459 τ2=-0.6027

# Lanzar F6 en background (~4 horas)
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
nohup python3 scripts/f6_corridas.py > /tmp/f6_log.txt 2>&1 &

# Monitorear progreso
tail -f /tmp/f6_log.txt

# Al terminar: generar gráficas
python3 scripts/generar_graficas_f6.py
```

---

## 10. Criterios de éxito (salida de F6)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| CSV de resultados | `wc -l results/resultados_f6_completo.csv` | 41 líneas (header + 40 corridas) |
| Disponibilidad 100% | `awk -F, 'NR>1{print $disp}' results/resultados_f6_completo.csv` | Todos `1` |
| ITL = 0% | `grep -c ",0.0," results/resultados_f6_completo.csv` | 40 |
| Lead Time corrida 11 | columna `lead_time_s` en fila 12 | ~62 s |
| 7 figuras generadas | `ls results/graficas_f6/*.png \| wc -l` | 7 |

**F6 se considera COMPLETADA** cuando `resultados_f6_completo.csv` tiene 40 corridas
con Disponibilidad=100%, ITL=0% y Lead Time < 120 s en la corrida de detección.
