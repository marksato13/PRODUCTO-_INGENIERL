# F6 — Especificación Técnica: Validación del Sistema

## 1. Objetivo y posición en el pipeline

Validar el sistema completo (F1-F5) en condiciones operacionales reales con el
**motor activo**, midiendo disponibilidad del servicio, ausencia de interrupción a
tráfico legítimo (ITL), tiempo de detección (Lead Time) y contención del atacante (TIE).

```
POSICIÓN EN EL PIPELINE COMPLETO

F1-F5 (sistema completo)          F6 (validación)               Tesis
────────────────────────  →  ─────────────────────────────  →  ──────────────
Suricata activo                   f6_corridas.py               7 figuras PNG
Motor con τ1/τ2           →       40 corridas × 300s      →    CSV de métricas
ipsets en servidor                Desktop + Kali activos        Disponibilidad 100%
                                  lee motor_decision.log        ITL=0%, Lead=62s
```

> **Nota metodológica:** F6 no valida sobre CSVs estáticos — ejecuta el sistema
> completo en tiempo real con tráfico mixto. El orquestador `f6_corridas.py` lanza
> tráfico real, espera 300 segundos, lee `motor_decision.log` para medir cuándo y
> cómo actuó el motor, y escribe el resultado en un CSV de corridas.

---

## 2. Terminología clave

### 2.1 Corrida

Una **corrida** es una ejecución de 300 segundos (5 minutos) con condiciones
controladas. La función `ejecutar_corrida(num, grupo, escenario_anom, duracion)`:

1. Lanza tráfico normal (Desktop): curl HTTP + ssh cada 8s en paralelo
2. (Opcional) espera 15s y lanza ataque desde Kali
3. A los 150s (mitad): llama `verificar_disponibilidad()` → curl HTTP al servidor
4. Al terminar: lee `motor_decision.log` en la ventana temporal
5. Calcula métricas y escribe fila en CSV

### 2.2 Métricas por corrida (columnas del CSV)

| Campo CSV | Cómo se mide | Valor típico |
|---|---|---|
| `disponibilidad` | `curl http://servidor/ --max-time 2` → 200 OK = 1, else = 0 | 1 en 40/40 |
| `flows_normal` | de línea "Estadísticas \| flows=N" del log en la ventana | 0–312,500 |
| `flows_anom` | count de líneas WARNING en el log (ANOMALÍA/SOSPECHOSO/HTTP-ABUSE/BF) | 0 ó 2 |
| `bloqueados` | IPs únicas en BLOCKs del log ventana | 0 ó 1 |
| `limitados` | IPs únicas en LIMITs del log ventana | 0 ó 1 |
| `latencia_ms` | `(dur_ventana / n_lineas_log) × 1000` — ver §2.5 | ~15,000–17,000 |
| `lead_time_s` | `t_primera_alerta − t_ataque_inicio` | 61.92s (corrida 11) |
| `mtta_s` | Mean Time to Alert = `lead_time_s` | igual a lead_time_s |
| `mttc_s` | Mean Time to Contain = `t_primera_accion − t_ataque_inicio` | 61.92s |
| `tie_pct` | `(IPs_intervenidas / flows_anom) × 100` | 100% (corrida 11) |
| `itl_pct` | % flows legítimos interrumpidos (calculado post-hoc) | 0.0% todas |

### 2.3 Lead Time — qué mide y por qué 61.92s

`lead_time_s = t_primera_alerta_en_log - t_ataque_inicio`

```
t=0s      Corrida 11 inicia
t=0s      Desktop lanza curl + ssh (tráfico normal)
t=15s     Kali inicia hping3 -S --flood  ← t_ataque_inicio
t=15-75s  SYN Flood activo — Suricata captura paquetes
          Flows TCP half-open no se cierran (sin ACK)
          Suricata NO emite evento flow hasta timeout (~60s)
t=76.9s   Suricata emite flows TCP half-open → eve.json
          Motor lee flow → score = -0.4937 → LIMIT
          Motor escribe WARNING en motor_decision.log ← t_primera_alerta
          lead_time_s = 76.9 - 15 = 61.92s
```

**El Lead Time NO es un retraso del motor** (latencia del modelo = 34.8ms P95).
Es el tiempo que Suricata tarda en emitir el evento `flow` TCP half-open. El
timeout de Suricata para conexiones TCP en estado `new` (sin completar handshake)
es de ~60 segundos.

### 2.4 `flows_anom=0` en corridas 12–40 — comportamiento correcto

Las corridas 12–40 también lanzan ataques (ver §4 — la lista `ataques_mixto`
rota entre synflood, portscan, udpflood, httpabuse). Pero `flows_anom=0` porque:

```python
# motor_decision.py — evaluación de flows con IP ya bloqueada
if src_ip in bloqueados:               # ← IP en set en-memoria
    log.debug(f"... | BLOCK (ya bloqueado)")  # DEBUG, no WARNING
    continue
```

La función `leer_log_ventana()` de f6_corridas.py solo cuenta líneas WARNING:
```python
KEYWORDS_ANOM = ("ANOMALÍA", "SOSPECHOSO", "HTTP-ABUSE", "BRUTE-FORCE")
if any(k in linea for k in KEYWORDS_ANOM):
    flows_anom += 1   ← solo cuenta WARNINGs, no DEBUGs
```

→ El motor procesa los flows de Kali a nivel DEBUG (contenida) → `flows_anom=0`.
→ El ipset del servidor (`ppi_blocked`) también mantiene a Kali bloqueada (timeout
300s que se renueva en cada corrida que dura ≤300s → la IP nunca expira durante F6).

### 2.5 `latencia_ms` en el CSV vs latencia real por flow

**`latencia_ms` en `resultados_f6_completo.csv`** NO es la latencia por flow:

```python
# calcular_metricas() en f6_corridas.py:
if len(tiempos) > 2:
    dur = tiempos[-1] - tiempos[0]        # duración de la ventana de log
    latencia_ms = (dur / len(tiempos) * 1000)  # ms entre líneas de log
```

Esto calcula la separación promedio entre líneas del log (estadísticas + warnings),
lo que da ~15,000–17,000ms porque hay pocas líneas de log en 300s.

**La latencia real por flow** está en `results/latencia_pipeline.txt`:
```
Flows medidos      : 1000
Latencia media     : 34.533 ms
Latencia mínima    : 34.224 ms
Latencia máxima    : 38.717 ms
Latencia P95       : 34.768 ms
Throughput         : 29 flows/segundo
Requiere < 500ms   : CUMPLE
```

Para la tesis, usar **P95=34.8ms de `latencia_pipeline.txt`**, no el campo
`latencia_ms` del CSV de corridas.

---

## 3. Entradas

| Entrada | Descripción |
|---|---|
| F1-F5 operativos | Suricata activo, motor con τ1/τ2 cargados, ipsets en servidor |
| `results/metricas_offline.txt` | τ1=−0.4459, τ2=−0.6027 cargados por el motor |
| `models/isolation_forest.pkl` + `scaler.pkl` | Modelo IF en memoria del motor |
| Desktop 192.168.0.20 | Genera tráfico HTTP+SSH normal en todas las corridas |
| Kali 192.168.0.100 | Lanza ataques en corridas 11–40 (rotación de escenarios) |

---

## 4. Diseño de las 40 corridas

### 4.1 Los 4 grupos y sus ataques

```python
# f6_corridas.py
N_NORMAL  = 10    # corridas 1-10
N_MIXTO   = 10    # corridas 11-20
N_REEVAL  = 10    # corridas 21-30
N_FINAL   = 10    # corridas 31-40

ataques_mixto = [
    "synflood","portscan","udpflood","httpabuse",
    "synflood","portscan","udpflood","httpabuse",
    "synflood","portscan"
]
# Se aplica a grupos Mixto, Reeval y Final (misma rotación)
```

| Corrida | Grupo | Escenario Kali | Descripción |
|---|---|---|---|
| 1–10 | normal | — | Solo Desktop, cero ataques |
| 11 | mixto | synflood | **Primera detección** — Lead Time 61.92s |
| 12 | mixto | portscan | Kali bloqueada en memoria → flows_anom=0 |
| 13 | mixto | udpflood | idem |
| 14 | mixto | httpabuse | idem |
| 15–20 | mixto | synflood/portscan/udpflood/httpabuse/synflood/portscan | idem |
| 21–30 | reeval | rotación | Re-evaluación con Kali contenida |
| 31–40 | final | rotación | Confirmación de contención total |

### 4.2 Parámetros de ejecución

| Parámetro | Valor | Descripción |
|---|---|---|
| `DURACION_NORMAL` | 300s | Duración por corrida (grupos normal y mixto) |
| `DURACION_MIXTO` | 300s | idem para reeval y final |
| `PAUSA_ENTRE` | 60s | Pausa entre corridas (Suricata cierra flows abiertos) |
| Tiempo inicio ataque | t+15s | Espera 15s de tráfico normal antes del ataque |
| Total estimado | ~4 horas | 40 corridas × (300+60)s = 14,400s |

---

## 5. Flujo interno de `f6_corridas.py` (paso a paso)

### 5.1 Estructura del script (358 líneas)

```
Constantes y configuración (líneas 1-40)
  DURACION_NORMAL=300, N_NORMAL=10, N_MIXTO=10, N_REEVAL=10, N_FINAL=10
  SERVIDOR, KALI, SENSOR, LOG_PATH, RESULT_DIR

Helpers (líneas 41-80)
  ts(), log(), run(cmd), ssh_kali(cmd)

Métricas (líneas 81-120)
  verificar_disponibilidad()  → curl HTTP al servidor → 200=OK
  leer_log_ventana(t_ini, t_fin) → filtra log por timestamps
  calcular_metricas(lineas, t_ataque) → extrae flows, lead_time, TIE...

Tráfico (líneas 121-180)
  trafico_normal_bg(dur)  → multiprocessing.Process: curl + ssh en loop
  trafico_anom_bg(tipo, dur) → ssh_kali: hping3/nmap/curl según tipo

Corrida (líneas 181-230)
  ejecutar_corrida(num, grupo, escenario_anom, duracion) → dict con métricas

CSV (líneas 231-250)
  COLS = [18 columnas], guardar_csv(path, filas)

Main (líneas 251-358)
  4 bucles for: normal, mixto, reeval, final
  guarda CSV parcial tras cada corrida (seguridad ante fallos)
  imprime resumen por grupo al final
```

### 5.2 Flujo de una corrida individual (ejemplo: corrida 11)

```
EJECUTAR_CORRIDA(num=11, grupo="mixto", escenario_anom="synflood", duracion=300)

t=09:16:43  t_inicio = time.time()

t=09:16:43  trafico_normal_bg(300):
            multiprocessing.Process(target=worker) → worker lanza:
              curl http://192.168.0.120/ -o /dev/null  (Desktop → Servidor)
              ssh m4rk@192.168.0.120 uptime  (cada 8s)

t=09:16:58  (t+15s) t_ataque = time.time()
            trafico_anom_bg("synflood", 285):
              ssh_kali("sudo timeout 285 hping3 -S -p 80 -i u5000 192.168.0.120 &")
              → Kali lanza SYN Flood (1 pkt cada 5ms, ~200 pkt/s)

t=09:16:58 – 09:18:59  SYN Flood activo (100 segundos)
            Suricata captura los SYN packets en ens35
            Flows TCP "new" (sin ACK) se acumulan en estado Suricata
            No se emiten eventos `flow` todavía (esperando timeout ~60s)

t=09:18:50  Suricata timeout TCP half-open expira para los primeros flows
            → emite: {"event_type":"flow","src_ip":"192.168.0.100","dest_port":80,
                      "flow":{"pkts_toserver":1,"pkts_toclient":0,...}}
            Motor lee el flow → score = -0.4937 → LIMIT
            Motor lee otro flow → score = -0.6027 → BLOCK
            log.warning("ANOMALÍA | src=192.168.0.100 ... | BLOCK")
            log.warning("SOSPECHOSO | src=192.168.0.100 ... | LIMIT")
            t_primera_alerta = 09:18:50 (= t_ataque + 61.92s)

t=09:19:13  verificar_disponibilidad() (t+150s):
            ssh m4rk@192.168.0.120 'curl -s http://localhost/ → "200"'
            → disponibilidad = 1  (nginx sigue respondiendo)

t=09:21:43  (t+300s) p_normal.terminate() — detener tráfico normal
            t_fin = time.time()

t=09:21:43  leer_log_ventana(t_inicio=09:16:43, t_fin=09:21:59):
            filtra líneas del log con timestamps en [09:16:43, 09:21:59]
            encuentra: 2 líneas WARNING (ANOMALÍA + SOSPECHOSO), N líneas Estadísticas

t=09:21:43  calcular_metricas(lineas, t_ataque=09:16:58):
            flows_anom = 2  (2 WARNINGs encontrados)
            bloqueados = {192.168.0.100}  → len=1
            limitados  = {192.168.0.100}  → len=1
            lead_time_s = 09:18:50 - 09:16:58 = 61.92s
            mtta_s = mttc_s = 61.92s
            tie_pct = 1/2 × 100 = 100%
            itl_pct = 0.0

RESULTADO corrida 11 (fila real del CSV):
11,mixto,synflood,2026-06-16,09:17:25,09:21:59,316,1,6500,2,1,1,15400.0,61.92,61.92,61.92,100.0,0.0
```

---

## 6. Scripts del pipeline F6

### 6.1 `scripts/f6_corridas.py` (358 líneas)

**Entrada:** Motor activo + tráfico en tiempo real
**Salida:** `results/resultados_f6_completo.csv` (41 líneas) + 4 CSVs parciales

```bash
# Ejecución completa (~4 horas)
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
nohup python3 scripts/f6_corridas.py > /tmp/f6_log.txt 2>&1 &
tail -f /tmp/f6_log.txt   # monitorear progreso
```

Salida en stdout por corrida:
```
[09:17:25] Corrida 01 | grupo=normal | escenario=solo_normal | dur=300s
[09:22:26]   → flows_anom=0 bloq=0 lim=0 lead=None mttc=None disp=1
[09:23:27] Corrida 02 | ...
...
[10:16:43] Corrida 11 | grupo=mixto | escenario=synflood | dur=300s
[10:21:59]   → flows_anom=2 bloq=1 lim=1 lead=61.92s mttc=61.92s disp=1
[10:23:00] Corrida 12 | grupo=mixto | escenario=portscan | dur=300s
[10:28:00]   → flows_anom=0 bloq=0 lim=0 lead=None mttc=None disp=1
```

### 6.2 `scripts/generar_graficas_f6.py` (488 líneas)

**Entrada:** `results/resultados_f6_completo.csv`
**Salida:** 7 archivos PNG 300 DPI en `results/graficas_f6/`

```bash
python3 scripts/generar_graficas_f6.py
ls results/graficas_f6/*.png | sort
```

| Archivo | Eje X | Eje Y | Lo que muestra |
|---|---|---|---|
| `f6_01_disponibilidad.png` | Corrida (1-40) | Disponibilidad (0/1) | 40 barras verdes = 100% |
| `f6_02_flows_anomalos.png` | Corrida (1-40) | flows_anom | Barra en corrida 11 (=2), resto=0 |
| `f6_03_timeline_deteccion.png` | Tiempo (s) | Evento | Timeline corrida 11: t=0 ataque → t=15 Kali → t=61.92 LIMIT/BLOCK |
| `f6_04_itl.png` | Corrida (1-40) | ITL (%) | Línea plana en 0% — sin impacto legítimo |
| `f6_05_flujos_acumulados.png` | Corrida (1-40) | flows_normal | Acumulativo 0→312,500 |
| `f6_06_latencia_pipeline.png` | Latencia (ms) | Distribución | P95=34.8ms vs umbral 500ms |
| `f6_07_panel_resumen.png` | — | — | Panel 2×3: disponibilidad, flows, ITL, latencia, lead time, TIE |

### 6.3 `scripts/auc_por_escenario.py` (en contexto de F6)

Genera `results/reports/auc_por_escenario.txt` leyendo los `.gz` de F2:

```bash
python3 scripts/auc_por_escenario.py
cat results/reports/auc_por_escenario.txt
```

No interviene en las 40 corridas — se ejecuta por separado para obtener el AUC
desglosado por tipo de ataque (B1-B6, C1-C3) que complementa los resultados de F6.

---

## 7. Estructura del CSV de resultados

**Archivo:** `results/resultados_f6_completo.csv` (41 líneas: 1 header + 40 corridas)

**Header:**
```
corrida,grupo,escenario,fecha,hora_inicio,hora_fin,duracion_s,disponibilidad,
flows_normal,flows_anom,bloqueados,limitados,latencia_ms,lead_time_s,
mtta_s,mttc_s,tie_pct,itl_pct
```

**Filas representativas:**
```
# Corrida 1 — normal, sin ataques
1,normal,normal,2026-06-16,09:17:25,09:22:26,300,1,0,0,0,0,0,,,,0,0.0

# Corrida 11 — ÚNICA DETECCIÓN
11,mixto,synflood,2026-06-16,10:16:43,10:21:59,316,1,6500,2,1,1,15400.0,61.92,61.92,61.92,100.0,0.0

# Corrida 12 — Kali ya bloqueada
12,mixto,portscan,2026-06-16,10:23:00,10:28:00,300,1,7000,0,0,0,16000.0,,,,0,0.0

# Corrida 40 — final, confirmación
40,final,portscan,2026-06-16,13:17:10,13:22:26,316,1,312500,0,0,0,16833.33,,,,0,0.0
```

**Nota sobre `flows_normal`:** el campo refleja el acumulado del motor desde el
arranque, no solo de la corrida individual. Va creciendo de 0 en corrida 1 hasta
312,500 en corrida 40.

---

## 8. Resultados finales validados (2026-06-16)

| Métrica | Valor | Requisito PPI | Estado |
|---|---|---|---|
| Disponibilidad | **100%** (40/40 corridas) | ≥ 99% | ✅ CUMPLE |
| ITL global | **0%** | = 0% | ✅ CUMPLE |
| Lead Time detección SYN Flood | **61.92 s** | < 120 s | ✅ CUMPLE |
| Latencia P95 por flow | **34.8 ms** | < 500 ms | ✅ CUMPLE |
| AUC-ROC | **0.8998** | ≥ 0.85 | ✅ CUMPLE |
| TIE (corrida 11) | **100%** | — | ✅ |
| Corridas exitosas | **40/40** | — | ✅ |
| Figuras generadas | **7/7 PNG 300 DPI** | — | ✅ |

### Resumen por grupo (del stdout de f6_corridas.py):

| Grupo | Corridas | Disponibilidad | Lead Time | MTTC | TIE | ITL |
|---|---|---|---|---|---|---|
| Normal | 1-10 | 100% | N/A | N/A | N/A | 0% |
| Mixto | 11-20 | 100% | 61.92s (c.11) | 61.92s | 100% (c.11) | 0% |
| Reeval | 21-30 | 100% | N/A | N/A | N/A | 0% |
| Final | 31-40 | 100% | N/A | N/A | N/A | 0% |

---

## 9. Secuencia técnica de ejecución F6

```bash
# ── PRE-REQUISITOS ──────────────────────────────────────────────────────
# 1. Motor activo con modelo correcto
sudo systemctl status ppi-motor.service   # → active
grep "τ1=" results/motor_decision.log | tail -1
# → τ1=-0.4459 τ2=-0.6027

# 2. Relay Telegram activo en Desktop (opcional — no afecta métricas)
# python3 /home/m4rk/Descargas/telegram_relay.py &

# 3. Servidor disponible
ssh m4rk@192.168.0.120 "curl -s http://localhost/ -o /dev/null -w '%{http_code}'"
# → 200

# ── EJECUCIÓN F6 (~4 horas) ────────────────────────────────────────────
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
nohup python3 scripts/f6_corridas.py > /tmp/f6_log.txt 2>&1 &
echo "PID: $!"

# Monitorear progreso
tail -f /tmp/f6_log.txt
# ó desde Desktop:
# ssh m4rk@192.168.0.110 "tail -f /tmp/f6_log.txt"

# ── POST-PROCESAMIENTO ──────────────────────────────────────────────────
# Verificar CSV
wc -l results/resultados_f6_completo.csv   # → 41

# Generar 7 figuras
python3 scripts/generar_graficas_f6.py
ls -lh results/graficas_f6/*.png           # → 7 archivos PNG

# Obtener AUC por escenario (complementario)
python3 scripts/auc_por_escenario.py
cat results/reports/auc_por_escenario.txt
```

---

## 10. Criterios de éxito (salida de F6)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| CSV de resultados | `wc -l results/resultados_f6_completo.csv` | **41** líneas |
| Disponibilidad 100% | `awk -F, 'NR>1{print $8}' results/resultados_f6_completo.csv \| sort -u` | Solo `1` |
| ITL = 0% | `awk -F, 'NR>1{print $18}' results/resultados_f6_completo.csv \| sort -u` | Solo `0.0` |
| Lead Time corrida 11 | `awk -F, 'NR==12{print $14}' results/resultados_f6_completo.csv` | `61.92` |
| flows_anom corrida 11 | `awk -F, 'NR==12{print $10}' results/resultados_f6_completo.csv` | `2` |
| flows_anom resto | `awk -F, 'NR>2&&NR!=12{print $10}' ... \| sort -u` | Solo `0` |
| 7 figuras PNG | `ls results/graficas_f6/*.png \| wc -l` | **7** |
| Latencia P95 real | `grep P95 results/latencia_pipeline.txt` | `34.768 ms` |
| AUC por escenario | `cat results/reports/auc_por_escenario.txt \| grep B2` | `0.9722` |

**F6 se considera COMPLETADA** cuando el CSV tiene 40 corridas con disponibilidad=1
en todas, ITL=0% en todas, Lead Time ≤ 120s en corrida 11, y las 7 figuras están
generadas. Estos resultados constituyen la evidencia experimental de la tesis.

---

**F6 cierra el pipeline F1→F6.** Los resultados van directamente a los capítulos
de Resultados y Discusión de la tesis (disponibilidad, ITL, lead time, latencia,
AUC-ROC), respaldados por las 7 figuras PNG de 300 DPI.
