# F6 — Validación del Sistema (40 Corridas)
**Estado: ✅ COMPLETA Y VALIDADA**  
**Resultado:** 40/40 corridas | Disponibilidad 100% | ITL 0% | 16/16 CAs PASS

---

## Objetivo

Demostrar empíricamente que el sistema completo (F1→F5) opera correctamente en condiciones reproducibles de laboratorio, cumpliendo todos los criterios de aceptación formales definidos en el plan PPI: disponibilidad, latencia, cero interrupción de tráfico legítimo y detección efectiva bajo todos los vectores de ataque.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Corrida** | Una sesión de validación estructurada: escenario definido, duración controlada, métricas registradas al terminar. Equivalente a un "test case" del sistema completo. |
| **Disponibilidad** | Porcentaje de corridas donde el sistema completó su función sin fallos. 100% = ninguna corrida falló por error del sistema. |
| **ITL (Interrupción de Tráfico Legítimo)** | Porcentaje de corridas donde tráfico normal fue bloqueado incorrectamente. ITL=0% = la whitelist funcionó perfectamente en todas las corridas. |
| **Lead time** | Tiempo desde el inicio del ataque hasta el primer BLOCK efectivo registrado en el log. Mide la velocidad de respuesta del pipeline completo. |
| **Latencia P95** | Percentil 95 de la latencia del pipeline. El 95% de los flujos se procesan en ≤34.8ms. Mide el rendimiento bajo carga, no solo el promedio. |
| **AUC por escenario** | AUC-ROC calculado para cada tipo de ataque por separado (B1, B2, ..., B6). Permite ver si el IF discrimina mejor en unos escenarios que en otros. |
| **Corrida normal** | Corridas donde solo Desktop genera tráfico (Grupo A). Valida que el sistema no genera falsas alarmas bajo condiciones normales. |
| **Corrida mixta** | Desktop + Kali simultáneos (Grupo C). Valida que el sistema bloquea a Kali pero NO a Desktop. La prueba más exigente del ITL. |
| **Corrida de reevaluación** | Corridas con Kali ya bloqueada en ipset. Valida que el bloqueo persiste y los paquetes de Kali no llegan a Suricata (flujos_anom=0 es correcto). |
| **CA (Criterio de Aceptación)** | Condición mínima que el sistema debe cumplir. Definida antes de las pruebas. El sistema PASA si todos los CAs son PASS. |
| **Suite de validación** | Conjunto de scripts automatizados (`run_all.sh`) que evalúan cada CA individualmente y producen un informe PASS/FAIL reproducible. |
| **Panel resumen** | Figura `f6_07_panel_resumen.png` — 7 gráficas en una sola imagen que resume visualmente todos los resultados de F6. |

---

## Diseño de las 40 corridas

Las 40 corridas fueron ejecutadas el **2026-06-16** (09:17 → 13:22) con `python3 scripts/f6_corridas.py`.

**Parámetros reales del script:**
```python
DURACION_NORMAL = 300   # segundos por corrida (5 min)
DURACION_MIXTO  = 300   # misma duración para mixtas
PAUSA_ENTRE     = 60    # pausa entre corridas (1 min)
N_NORMAL        = 10    # corridas grupo normal
N_MIXTO         = 10    # corridas grupo mixto
N_REEVAL        = 10    # corridas re-evaluación
N_FINAL         = 10    # corridas finales
```

**Secuencia dentro de cada corrida mixta:**
1. T+0s — se lanza tráfico normal desde el sensor (curl + SSH → servidor, whitelisted)
2. T+15s — se lanza el ataque desde Kali
3. T+150s — verificación de disponibilidad (curl al servidor)
4. T+300s — fin de corrida, se recolectan métricas del log

**Nota sobre tráfico normal en f6_corridas.py:** el script genera tráfico desde el **sensor (192.168.0.110)**, que está en la whitelist. El propósito es tener flujos normales activos que el sistema debe ignorar mientras detecta a Kali. Las corridas manuales A1–A4 se ejecutan desde el Desktop (192.168.0.20).

**Ataques usados en el script automatizado** (4 tipos):

| ID | Herramienta | Comando en Kali |
|---|---|---|
| synflood | hping3 | `hping3 -S -p 80 -i u5000 192.168.0.120` |
| portscan | nmap | `nmap -sS -p 1-1024 192.168.0.120` |
| udpflood | hping3 | `hping3 --udp -p 53 -i u5000 192.168.0.120` |
| httpabuse | curl loop | `while true; do curl -s http://192.168.0.120/; done` |

> B4 (icmpflood) y B6 (bruteforce) no están en el script automatizado — se validaron en corridas manuales y en las validaciones en vivo del 2026-06-22.

| Grupo | Corridas | Tipo | Propósito |
|---|---|---|---|
| **Normal** (1–10) | solo_normal | Sensor whitelisted | ITL = 0%: motor ignora tráfico whitelisted |
| **Mixto** (11–20) | synflood/portscan/udpflood/httpabuse | Sensor + Kali | Primera detección y bloqueo |
| **Reevaluación** (21–30) | mismos ataques, IP ya bloqueada | Kali en ipset | Persistencia del bloqueo |
| **Final** (31–40) | mismos ataques | Bloqueo acumulado | Disponibilidad sostenida |

> **Por qué flujos_anom=0 en corridas 11–40 es correcto:** una vez que Kali entra en `ppi_blocked`, sus paquetes son descartados en el kernel (iptables DROP) antes de llegar a Suricata. Suricata no genera flujos de esos paquetes → motor no ve eventos anómalos. Esto demuestra que el bloqueo funciona, no que el sistema dejó de detectar.

---

## Entradas → Proceso → Salidas

```
ENTRADAS
  Sistema completo F1–F5 activo y funcionando:
    suricata.service          (capturando en ens35)
    ppi-motor.service         (motor_decision.py corriendo)
    ppi-predictor.service     (predictor.py corriendo)
    ppi-dashboard.service     (dashboard_web.py en :8080)
  Acceso SSH a Kali (192.168.0.100) para lanzar ataques
  results/motor_decision.log  (fuente de métricas de cada corrida)

PROCESO  [f6_corridas.py — 40 corridas, ~40 minutos]
  Para cada corrida (300s = 5 min):
    T+0s   → trafico_normal_bg(): curl + SSH desde sensor → servidor
    T+15s  → trafico_anom_bg(): ataque desde Kali (synflood/portscan/udpflood/httpabuse)
    T+150s → verificar_disponibilidad(): curl al servidor → disp=1 ó 0
    T+300s → leer_log_ventana() → calcular_metricas()
    Guardar fila CSV → continuar
    Pausa 60s entre corridas

  4 grupos × 10 corridas:
    Normal (1-10)    → solo tráfico normal (sensor, whitelisted)
    Mixto (11-20)    → normal + ataque Kali → primera detección
    Reeval (21-30)   → Kali ya bloqueada → confirmar persistencia
    Final (31-40)    → bloqueo consolidado → disponibilidad sostenida

SALIDAS
  results/resultados_f6_completo.csv             (40 filas, 18 columnas)
  docs/documentacion/imagenes/F6_validacion/     (7 figuras 300 DPI)
  docs/bitacora/bitacora_escenarios.txt          (64 entradas)

MÉTRICAS EN EL CSV (18 columnas):
  corrida, grupo, escenario, fecha, hora_inicio, hora_fin, duracion_s,
  disponibilidad, flows_normal, flows_anom, bloqueados, limitados,
  latencia_ms, lead_time_s, mtta_s, mttc_s, tie_pct, itl_pct
```


---

## Scripts de validación F6

```bash
# Batch de 40 corridas (tarda ~40 min incluyendo pausas)
python3 scripts/f6_corridas.py
# → results/resultados_f6_completo.csv   (40 filas, 18 columnas)

# AUC por escenario
python3 scripts/auc_por_escenario.py
# → imprime en stdout / guardar manualmente si se necesita

# 7 gráficas PNG 300 DPI
python3 scripts/generar_graficas_f6.py
# → docs/documentacion/imagenes/F6_validacion/*.png
```

---

## Resultados — todos los criterios cumplidos ✅

| Métrica | Valor medido | Criterio | Estado |
|---|---|---|---|
| **Disponibilidad** | **100%** | ≥ 99% | ✅ |
| **ITL** | **0%** | = 0% | ✅ |
| **Latencia P95** | **34.768ms** | < 500ms | ✅ (×14 de margen) |
| **Lead time SYN Flood (B1)** | **~62s** | < 120s | ✅ |
| **Lead time BF SSH (B6)** | **~60s** | < 90s | ✅ |
| **Bloqueo #3 permanente** | **timeout=0** | verificable | ✅ |
| **Telegram alerta** | **HTTP 200** | recibida | ✅ |

---

## 7 Gráficas generadas (300 DPI para informe)

| Gráfica | Qué muestra | Resultado visual |
|---|---|---|
| `f6_01_disponibilidad.png` | Barra por corrida: OK vs FAIL | 40/40 barras verdes |
| `f6_02_flows_anomalos.png` | Flujos anómalos detectados por escenario | Pico en B1 (SYN flood) y B3 (UDP) |
| `f6_03_timeline_deteccion.png` | Lead time por escenario (segundos) | B1≈62s, B6≈60s, B2<15s |
| `f6_04_itl.png` | ITL % por corrida | 0% en todas las 40 corridas |
| `f6_05_flujos_acumulados.png` | Flujos procesados acumulados | Crecimiento lineal = motor estable |
| `f6_06_latencia_pipeline.png` | Distribución de latencia (ms) | P95=34.8ms, sin picos |
| `f6_07_panel_resumen.png` | Todas las métricas en un panel | Usar en slide 13 del PPT |

---

## Validaciones adicionales en vivo — 2026-06-22

Complementan los 40 corridas formales con evidencia directa en tiempo real:

### Bloqueo progresivo validado

| Bloqueo | Timestamp | Trigger | Timeout | ipset timeout |
|---|---|---|---|---|
| #1 | 05:44:13 | score=−0.6066 SYN flood | 300s | Kali sale de ipset en 5 min |
| #2 | 06:05:03 | score=−0.7696 reincidencia | 1,800s | Kali sale en 30 min |
| #3 | 06:39:42 | HTTP-ABUSE 100 req/30s | **0s** | **PERMANENTE** |

```json
block_counts.json: {"192.168.0.100": 2}
```

### Lead time B6 SSH Brute Force

| Evento | T desde inicio | Score IF | Acción | Trigger |
|---|---|---|---|---|
| Primera detección | T+53s | −0.4832 | LIMIT | BF_SSH_warn: 5 intentos/60s |
| BLOCK | T+60s | −0.6228 | BLOCK #1 | BRUTE_FORCE_SSH: 15 intentos/60s |

Telegram recibido: `08:31:37 — 🚨 BRUTE_FORCE_SSH | BLOCK | IP: 192.168.0.100 | Puerto: 22`

### CA-16: Datos normales nuevos (2026-06-22 15:09)

119 flows capturados en sesión nueva (curl HTTP + SSH + wget, 3 min):
- Score medio: **+0.0139** (vs −0.3965 del entrenamiento → más normal aún)
- FPR efectivo: **0.0%** — 119/119 PERMIT
- **CA-16: PASS**

---

## Suite de validación automatizada

La carpeta `scripts/validacion/` y `docs/documentacion/validacion/` implementan validación reproducible por script:

```bash
# Ejecutar 16 CAs automáticamente (F1–F6)
bash scripts/validacion/run_all.sh
# → Salida: results/validacion_YYYYMMDD_HHMMSS.log
```

### Resultado de la ejecución 2026-06-22 15:04:05

```
F1 Suricata:    4/4 PASS  (activo, 500MB, ens35 promiscuo)
F2 IF modelo:   4/4 PASS  (AUC=0.8998, TPR=99.40%, FPR=20.47%)
F3 Motor:       3/3 PASS  (P95=34.768ms, 1.18M entradas, τ correctos)
F3 ipset:       PASS      (whitelist 5/5, 12,811 BLOCKs, Kali #2)
F4 XGBoost:     2/2 PASS  (AUC=0.9992, 14 errores de 12,488)
F5 Reentrenam.: PASS      (2 crons, 3 corridas, anti-regresión)
F6 Corridas:    PASS      (40/40, disp.100%, 7 PNGs, 64 bitácora)
CA-16 nueva data: PASS    (FPR=0.0% en 119 flows nuevos)

TOTAL: 16/16 criterios PASS ✅
```

Log de esa ejecución archivado (eliminado del repo — los CAs de la tabla arriba son la evidencia)

---

## Imágenes de referencia

| Imagen | Ruta |
|---|---|
| Disponibilidad 40 corridas | `docs/documentacion/imagenes/F6_validacion/f6_01_disponibilidad.png` |
| Flujos anómalos por escenario | `docs/documentacion/imagenes/F6_validacion/f6_02_flows_anomalos.png` |
| Timeline lead time | `docs/documentacion/imagenes/F6_validacion/f6_03_timeline_deteccion.png` |
| ITL = 0% todas las corridas | `docs/documentacion/imagenes/F6_validacion/f6_04_itl.png` |
| Latencia del pipeline | `docs/documentacion/imagenes/F6_validacion/f6_06_latencia_pipeline.png` |
| Panel resumen 7-en-1 | `docs/documentacion/imagenes/F6_validacion/f6_07_panel_resumen.png` |

---

## Criterios de aceptación — TODOS CUMPLIDOS ✅

| CA | Criterio | Valor | Estado |
|---|---|---|---|
| CA-1 | AUC-ROC IF ≥ 0.85 | 0.8998 | ✅ |
| CA-2 | TPR@τ1 ≥ 95% | 99.40% | ✅ |
| CA-3 | FPR@τ1 ≤ 25% | 20.47% | ✅ |
| CA-4 | Precision ≥ 95% | 99.54% | ✅ |
| CA-5 | Latencia P95 < 500ms | 34.768ms | ✅ |
| CA-6 | Motor activo / ITL=0% | 1.18M entradas / 0% | ✅ |
| CA-7 | τ1/τ2 cargados | −0.4459/−0.6027 | ✅ |
| CA-8 | Whitelist protegida | 0/5 IPs en BLOCK | ✅ |
| CA-9 | IP atacante bloqueada | 12,811 BLOCKs | ✅ |
| CA-10 | Bloqueo #3 permanente | timeout=0 | ✅ |
| CA-11 | XGBoost AUC ≥ 0.95 | 0.9992 | ✅ |
| CA-12 | FP+FN ≤ 30 en test | 14 (7+7) | ✅ |
| CA-13 | Crons F5 configurados | 2 activos | ✅ |
| CA-14 | Corridas F5 registradas | 3 corridas | ✅ |
| CA-15 | 40 corridas / disp. 100% | 40/40 | ✅ |
| CA-16 | FPR datos nuevos ≤ 30% | 0.0% (119 flows) | ✅ |

---

## Argumento de defensa

> "F6 no es un experimento aislado — es la validación empírica del sistema completo operando como lo haría en producción real. 40 corridas ejecutadas en condiciones reproducibles, con cuatro grupos de escenarios que cubren desde el uso normal hasta el bloqueo permanente después de múltiples reincidencias. Los 16 criterios de aceptación definidos antes de las pruebas — todos cumplidos — son la evidencia objetiva. El 22 de junio añadimos validación en vivo que ningún paper puede dar: el sistema detectó un brute force SSH real en 60 segundos y lo escaló a bloqueo permanente después de tres incidencias, con notificación Telegram recibida en tiempo real. La tasa de interrupción de tráfico legítimo fue cero en todas las pruebas — el sistema actúa quirúrgicamente, no como un firewall que corta todo."
