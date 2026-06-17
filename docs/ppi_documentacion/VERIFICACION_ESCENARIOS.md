# Verificación de Escenarios — Flujos de Decisión del Motor

**Sistema:** Detección temprana de comportamientos anómalos mediante Isolation Forest  
**Universidad:** Universidad Peruana Unión — PPI Ingeniería de Sistemas  
**Validado:** 2026-06-17 | Motor activo con τ1=−0.4459, τ2=−0.6027

---

## 1. Arquitectura de Decisión del Motor

El motor (`motor_decision.py`) sigue este pipeline por cada evento `flow`:

```
eve.json (Suricata)
    │
    ▼
seguir_eve()  ── tail -f, detecta rotación
    │
    ├── ¿event_type == 'flow'?    NO → skip
    ├── ¿src_ip in WHITELIST?     SÍ → skip (nunca bloquear IPs conocidas)
    ├── ¿pkts_toserver == 0?      SÍ → skip
    │
    ▼
extract_features(evento)
    │  14 features: pkts_toserver, pkts_toclient, bytes_toserver,
    │               bytes_toclient, duration, pkt_rate, byte_rate,
    │               pkt_ratio, byte_ratio, avg_pkt_size,
    │               is_tcp, is_udp, is_icmp, dest_port
    │
    ▼
scaler.transform(X)   ← StandardScaler ajustado SOLO a datos normales (80%)
    │
    ▼
clf.score_samples(X)  ← IsolationForest(n=300, contamination=0.05)
    │                    rango: [-1, 0]  |  más negativo = más anómalo
    │
    ├── [HEURÍSTICO 1] detectar_http_abuse()
    │       ventana: 30s  |  ≥50 req/30s → LIMIT  |  ≥100 req/30s → BLOCK
    │       aplica SOLO a TCP/80
    │
    ├── [HEURÍSTICO 2] detectar_brute_force()
    │       ventana: 60s  |  ≥5 intentos/60s → LIMIT  |  ≥15 → BLOCK
    │       aplica SOLO a TCP/22
    │
    └── decidir(score):
            score > τ1 (-0.4459)         → PERMIT
            τ2 (-0.6027) < score ≤ τ1   → LIMIT   (hashlimit 100 pkt/s)
            score ≤ τ2 (-0.6027)         → BLOCK   (DROP total)

[Si BLOCK o LIMIT]:
    bloquear_ip() / limitar_ip()
      └── SSH → Servidor.120 → ipset add ppi_blocked/ppi_limited timeout 300s
    log.warning(...)
    telegram_alerta() → relay Desktop:8889 → api.telegram.org
    [SSE push] → dashboard_web.py → navegador en tiempo real
```

**Whitelist hardcoded (motor_decision.py línea 53):**
`192.168.0.1`, `192.168.0.20`, `192.168.0.110`, `192.168.0.120`, `192.168.0.130`, `192.168.0.140`, `127.0.0.1`

---

## 2. Escenarios Grupo A — Tráfico Normal (sin alertas)

> Desktop (192.168.0.20) está en WHITELIST → motor omite procesamiento completo.
> Todos los flows de Desktop son PERMIT implícito — no pasan por IF ni heurísticos.

### A1 — HTTP Normal

```bash
while true; do
    curl -s -o /dev/null http://192.168.0.120/
    sleep 3
done
```

**Features típicas por flow:**

| Feature | Valor típico | Por qué |
|---|---|---|
| pkts_toserver | 3–6 | GET + ACKs |
| pkts_toclient | 4–8 | respuesta HTTP + ACKs |
| bytes_toserver | 150–400 | headers HTTP |
| bytes_toclient | 800–5000 | respuesta nginx |
| duration | 0.01–0.5s | conexión TCP corta |
| pkt_rate | 5–50 pkt/s | bajo |
| byte_ratio | 0.1–0.5 | más bytes en respuesta |

**Decisión:** `src_ip = 192.168.0.20` → **IN WHITELIST → `continue` (sin scoring)**  
**Resultado:** 0 alertas, 0 entradas en ipset, 0 mensajes Telegram

```bash
# Verificación
grep '192.168.0.20' results/motor_decision.log | grep WARNING  # → vacío
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 192.168.0.20"  # → vacío
```

### A2 — SSH Legítimo

```bash
ssh -o BatchMode=yes m4rk@192.168.0.120 "uptime; df -h"
```

| Feature | Valor | Por qué |
|---|---|---|
| is_tcp | 1 | SSH es TCP |
| dest_port | 22 | SSH estándar |
| pkts_toserver | 20–100 | intercambio SSH |
| duration | 2–30s | sesión interactiva |

**Score IF hipotético (sin whitelist):** ~−0.39 → PERMIT (sobre τ1)

### A3 — Transferencia Legítima

```bash
scp /tmp/archivo.txt m4rk@192.168.0.120:/tmp/
wget -q -O /dev/null http://192.168.0.120/
```

| Feature | Valor | Por qué |
|---|---|---|
| bytes_toserver | 10,000–1,000,000 | archivo completo |
| byte_rate | 1,000–100,000 B/s | tasa normal |
| byte_ratio | 2–500 | más datos hacia servidor |

### A4 — Tráfico Sostenido Mixto

Combinación A1+A2+A3 durante 15 minutos. Alto volumen pero patterns normales.

> **FPR teórico:** 20.47% de flows → score ∈ (−0.6027, −0.4459] → serían LIMIT si no hubiera whitelist.
> La whitelist elimina estos falsos positivos para IPs del laboratorio conocidas.

---

## 3. Escenarios Grupo B — Ataques Puros (BLOCK esperado)

> Kali (192.168.0.100) **NO** está en whitelist → todos sus flows son evaluados por IF y heurísticos.

### B1 — SYN Flood

```bash
# Kali
sudo hping3 -S -p 80 --flood 192.168.0.120
```

**Pipeline completo paso a paso:**

1. Kali envía millones de paquetes SYN a `.120:80` sin completar handshake TCP (`--flood`)
2. Suricata acumula el flow durante **~60s** (timeout TCP half-open de Suricata 7.0.3)
3. Suricata emite evento `flow` en `eve.json` con todos los paquetes acumulados
4. Motor extrae features:

| Feature | Valor | Por qué |
|---|---|---|
| pkts_toserver | 50,000–1,000,000 | --flood masivo |
| pkts_toclient | 0 | sin handshake completo |
| bytes_toserver | 3,000,000+ | headers TCP SYN ~60B cada uno |
| bytes_toclient | 0 | |
| duration | ~60s | timeout Suricata |
| pkt_rate | 833–16,000 pkt/s | extremo |
| byte_ratio | 3,000,000/(0+1) | asimétrico extremo |
| pkt_ratio | 50,000/(0+1) | asimétrico extremo |
| is_tcp | 1 | |
| dest_port | 80 | |

5. `scaler.transform()` → valores outliers vs distribución normal del entrenamiento
6. `clf.score_samples()` → **score ≈ −0.49 a −0.71** (zona gris — AUC B1=0.8302, el más bajo)
7. `decidir(score)`:
   - Si score ≤ τ2 (−0.6027) → **BLOCK directo por IF**
   - Si τ2 < score ≤ τ1 (−0.4459) → **LIMIT por IF** + heurístico HTTP-ABUSE puede escalar a BLOCK
8. **Heurístico HTTP-ABUSE** (opera en paralelo): si el flood genera ≥100 flows TCP/80 en 30s → **BLOCK**
   - En el test 2026-06-17: score=−0.4937 → LIMIT por IF; HTTP-ABUSE con 100/30s → BLOCK a los 11s
9. `bloquear_ip(192.168.0.100)`:
   ```
   SSH → Servidor.120 → sudo ipset add ppi_blocked 192.168.0.100 timeout 300
   ```
10. **Log observado (test real 2026-06-17 02:21):**
    ```
    WARNING | SOSPECHOSO   | src=192.168.0.100 dst=:80 proto=TCP score=-0.4937 | LIMIT
    WARNING | HTTP-ABUSE   | src=192.168.0.100 dst=:80 proto=TCP requests=100/30s | BLOCK
    ```
11. **Telegram:** `🚨 PPI ALERTA — SYN_FLOOD` (via relay Desktop:8889)
12. **Dashboard:** SSE push → alerta en `http://192.168.0.110:8080`

**Lead Time observado:** ~11s en test 2026-06-17 (HTTP-ABUSE disparó antes que el timeout TCP de Suricata)
El Lead Time canónico de ~62s del informe F6 corresponde al escenario donde IF detecta el flow
tras el timeout TCP half-open de Suricata (~60s). La latencia del motor sigue siendo 34.8ms (P95).

```bash
# Verificación
grep '192.168.0.100' results/motor_decision.log | grep BLOCK
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
curl -s http://192.168.0.110:8080/api/alerts | python3 -m json.tool
```

---

### B2 — Port Scan

```bash
# Kali
sudo nmap -sS -p 1-1024 --min-rate 1000 -T5 192.168.0.120
```

**Features por flow** (uno por puerto escaneado):

| Feature | Valor | Por qué |
|---|---|---|
| pkts_toserver | 1 | SYN único |
| pkts_toclient | 0 o 1 | RST o SYN-ACK |
| bytes_toserver | 40–60 | solo header TCP |
| duration | <0.01s | sin handshake |
| pkt_rate | ~1000 pkt/s | instantáneo |
| dest_port | varía 1–1024 | rasgo distintivo |

**Decisión:** score ≈ −0.72 → BLOCK en primer flow anómalo detectado  
Flows subsiguientes: "ya bloqueado" (log DEBUG, no WARNING)

---

### B3 — UDP Flood

```bash
# Kali
sudo hping3 --udp --flood -p 53 192.168.0.120
```

| Feature | Valor | Por qué |
|---|---|---|
| is_udp | 1 | proto=UDP |
| pkts_toserver | masivo | --flood |
| pkts_toclient | 0 | UDP no bidireccional |
| dest_port | 53 | DNS |
| pkt_rate | extremo | |

**Mecanismo:** SOLO Isolation Forest (heurísticos no cubren UDP/53)

> **Hallazgo real (test 2026-06-17):** Suricata genera múltiples flows UDP cortos
> en lugar de uno acumulado. El IF clasifica los flows individuales como PERMIT (score > τ1).
> Resultado: IP recibe **LIMIT** por flows TCP residuales (100 pkt/s), no BLOCK por UDP.
> Es una limitación del modelo con los umbrales actuales para UDP.

**Log observado:**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=:113 proto=TCP score=-0.4461 | LIMIT
(flows UDP/53 → PERMIT por IF, no aparecen en WARNING)
```
**Estado:** IP en `ppi_limited` — rate-limitada 100 pkt/s (mitigación parcial)

---

### B4 — ICMP Flood

```bash
# Kali
sudo hping3 -1 --flood 192.168.0.120
```

| Feature | Valor | Por qué |
|---|---|---|
| is_icmp | 1 | proto=ICMP |
| dest_port | 0 | ICMP no tiene puerto |
| pkts_toserver | masivo | --flood |
| pkt_rate | extremo | miles/s |

**Mecanismo:** SOLO Isolation Forest (teórico) — **brecha real en esta topología**

> **Hallazgo (análisis offline 2026-06-16):** `auc_por_escenario.py` procesó
> `20260615_anom_icmpflood_01_eve.json.gz` (26.8M flows) y obtuvo
> **AUC=0.8961, Det%=100%** — el modelo sí detecta ICMP Flood desde los archivos `.gz`.
>
> **Hallazgo (test en tiempo real 2026-06-17):** En el test con motor activo y
> `hping3 -1 --flood`, Suricata 7.0.3 no emitió eventos `flow` para ICMP IPv4 en
> esa corrida específica. Solo emitió flows ICMP en IPv6 (src con `:`), filtrados
> en línea 389 (`if ':' in src_ip: continue`). Resultado en tiempo real: **0 detecciones**.
>
> **Conclusión:** el modelo tiene capacidad de detección ICMP (AUC=0.8961 offline),
> pero la cobertura en tiempo real depende de que Suricata genere eventos `flow` para
> ICMP IPv4, lo cual no ocurrió de forma consistente en todas las corridas del laboratorio.
> Comportamiento clasificado como **cobertura variable** según la sesión de captura.

**Mitigación posible:** añadir heurístico ICMP por conteo de paquetes en ventana temporal,
o verificar configuración de Suricata (`flow-timeouts` para ICMP) para asegurar emisión
consistente de eventos `flow` IPv4.

---

### B5 — HTTP Abuse ✅ VALIDADO 2026-06-17 01:53

```bash
# Kali — curl sin pausa
while true; do curl -s -o /dev/null http://192.168.0.120/; done
```

**Pipeline heurístico:**

1. Kali → GET requests a `:80` sin pausa (~3–10 req/s)
2. Cada request = flow TCP/80 en Suricata
3. Motor → `detectar_http_abuse()`:
   ```python
   http_requests[192.168.0.100].append(ts_flow)
   # elimina timestamps > 30s de la deque
   count = len(http_requests[192.168.0.100])
   if count >= 50:  → LIMIT
   if count >= 100: → BLOCK
   ```
4. Con `curl` sin pausa: LIMIT a los ~15s, BLOCK a los ~30s
5. IF score complementario: ~−0.46 (LIMIT por IF también)
6. **Heurístico dispara PRIMERO** en el código (antes del scoring IF)

**Log observado (test real 2026-06-17):**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.4805 | LIMIT
WARNING | ANOMALÍA   | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.6060 | BLOCK
→ 192.168.0.100 en ppi_blocked timeout=264s
```

---

### B6 — Brute Force SSH ✅ VALIDADO 2026-06-17 01:54

```bash
# Kali
hydra -l root -P /tmp/bf_wordlist.txt -t 8 ssh://192.168.0.120
```

**Pipeline heurístico:**

1. hydra abre 8 conexiones SSH paralelas (`-t 8`)
2. Cada intento fallido = flow TCP/22 corto en Suricata
3. Motor → `detectar_brute_force()`:
   ```python
   ssh_intentos[192.168.0.100].append(ts_flow)
   # elimina timestamps > 60s
   count = len(ssh_intentos[192.168.0.100])
   if count >= 5:  → LIMIT
   if count >= 15: → BLOCK
   ```
4. Con `hydra -t 8`: LIMIT en <5s, BLOCK en ~10s
5. **Desktop SSH (`.20` en whitelist):** NO cuenta en el detector BF

**Log esperado (aislado):**
```
WARNING | BRUTE-FORCE | src=192.168.0.100 dst=192.168.0.120:22 intentos=5/60s  | LIMIT
WARNING | BRUTE-FORCE | src=192.168.0.100 dst=192.168.0.120:22 intentos=15/60s | BLOCK
```

> **Nota:** Si se ejecuta después de B5 sin limpiar, Kali puede estar ya bloqueada.
> Usar `reset_motor` (reinicia motor + limpia ipsets) para test aislado.

---

## 4. Escenarios Grupo C — Tráfico Mixto (detección selectiva)

> **Clave:** Motor procesa TODOS los flows de Suricata.
> Desktop → skip (whitelist) → servicio disponible.
> Kali → evalúa → BLOCK.
> **Resultado: ITL = 0%**

### C1 — HTTP Normal + SYN Flood

```bash
# Desktop (paralelo):
while true; do curl -s -o /dev/null http://192.168.0.120/; sleep 3; done

# Kali (paralelo):
sudo hping3 -S -p 80 --flood 192.168.0.120
```

**Flujo en el motor (flows intercalados en eve.json):**
```
flow: src=192.168.0.20,  dst=:80, pkts=5     → WHITELIST → skip
flow: src=192.168.0.100, dst=:80, pkts=50000 → score=-0.71 → BLOCK
flow: src=192.168.0.20,  dst=:80, pkts=4     → WHITELIST → skip
...
```

**Estado ipset tras detección:**
```
ppi_blocked: 192.168.0.100 timeout 300s
              (192.168.0.20 NO aparece)

iptables en .120:
  src=192.168.0.100 → DROP    (ppi_blocked match)
  src=192.168.0.20  → ACCEPT  (sin match → pasa)
```

**Verificación:**
```bash
curl -s http://192.168.0.120/               # → 200 OK (Desktop no interrumpida)
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep .100"  # → presente
# ITL = 0%
```

### C2 — SSH Legítimo + Port Scan

| Origen | Tráfico | Decisión motor |
|---|---|---|
| Kali .100 | `nmap -sS -p 1-1024` | IF score ≤ τ2 → BLOCK |
| Desktop .20 | `ssh m4rk@servidor` | WHITELIST → skip → funciona |

### C3 — Transferencia Legítima + UDP Flood

| Origen | Tráfico | Decisión motor |
|---|---|---|
| Kali .100 | `hping3 --udp --flood -p 53` | is_udp=1, pkt_rate masivo → IF BLOCK |

> **Resultado real:** igual que B3 — UDP Flood no detectado por IF en esta topología.
> Desktop sin interrupciones (OK=60 FAIL=0), Kali sin bloquear.
| Desktop .20 | `scp/wget` | WHITELIST → skip → transferencia completa |

---

## 5. Análisis de Falsos Positivos

### 5.1 FPR del modelo en τ1 = −0.4459

| Umbral | Métrica | Valor |
|---|---|---|
| τ1 = −0.4459 | TPR (Recall) | 99.40% |
| τ1 = −0.4459 | FPR (Falsos Pos.) | 20.47% |
| τ2 = −0.6027 | TPR | 18.27% |
| τ2 = −0.6027 | FPR | 2.00% |

**Interpretación:** 20.47% de flows normales → score ∈ (−0.6027, −0.4459] → LIMIT (hashlimit 100 pkt/s), NO bloqueados.

**Por qué es aceptable:**
1. **Whitelist mitiga:** IPs conocidas excluidas ANTES del scoring IF
2. **LIMIT ≠ BLOCK:** hashlimit 100 pkt/s >> necesario para HTTP normal (~10 pkt/s)
3. **Alternativa peor:** τ1=−0.5547 → FPR=5%, pero SYN Flood (score≈−0.49) escaparía

**Distribución de scores (resultado final):**
```
Score medio normal  : −0.3965 ± 0.0753
Score medio anómalo : −0.5420 ± 0.0900
Separación (delta)  : 0.1454
AUC-ROC             : 0.8998
```

### 5.2 AUC por escenario de ataque

| Escenario | AUC | Dificultad |
|---|---|---|
| B1 SYN Flood | **0.8342** | Mayor dificultad (score ≈ −0.48, zona gris entre τ1 y τ2) |
| B2 Port Scan | **0.9722** | Menor dificultad (flujos de 1 pkt muy distintos al normal) |
| B3 UDP Flood | **0.9537** | Alto (is_udp=1 + byte_rate extremo discriminan bien) |
| B4 ICMP Flood | **0.8961** | Medio-alto (is_icmp=1, dest_port=0 — det. offline 100%) |
| B5 HTTP Abuse | **0.9670** | Alto (heurístico HTTP-ABUSE + score IF complementan) |
| B6 BruteForce | **0.8658** | Medio-alto (heurístico BF-SSH + score IF complementan) |

> Fuente: `results/reports/auc_por_escenario.txt` — generado 2026-06-16 con τ1=−0.4459.
> Escenarios mixtos: C1=0.8206, C2=0.8596, C3=0.9327.

---

## 6. Sincronización Motor → Dashboard → Telegram

```
motor_decision.py
    │
    ├── log.warning("ANOMALÍA...")  → motor_decision.log
    │
    ├── telegram_alerta(msg)
    │       _tg_queue.put(msg)        ← no bloqueante, Queue(maxsize=100)
    │       _tg_worker() thread:
    │         POST http://192.168.0.20:8889/telegram  ← relay Desktop
    │         relay → POST https://api.telegram.org/bot.../sendMessage
    │         Latencia estimada: <500ms para entrega
    │
    └── motor_decision.log actualizado
            │
            dashboard_web.py (thread log_reader)
              tail del log cada 0.2s
              detecta nueva línea WARNING → push_sse(evento)
              actualiza: alerts[], stats{}, timeline{}
              │
              Navegador (SSE EventSource /api/stream)
                recibe evento → actualiza UI sin polling
                Latencia detección → dashboard: <1s
                Latencia detección → Telegram: <3s
```

**Endpoints del dashboard (`http://192.168.0.110:8080`):**

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/stats` | GET | Estadísticas globales (JSON) |
| `/api/events` | GET | Últimos N flows procesados |
| `/api/alerts` | GET | Últimas alertas WARNING |
| `/api/timeline` | GET | Distribución temporal |
| `/api/tipos` | GET | Conteo por tipo de anomalía |
| `/api/stream` | GET (SSE) | Stream en tiempo real |
| `/api/block` | POST | Bloqueo manual desde web |
| `/api/unblock` | POST | Desbloqueo manual desde web |
| `/api/clear` | POST | Limpiar historial alertas |

---

## 7. Comandos de Verificación Rápida

```bash
# ── DESDE DESKTOP (192.168.0.20) ─────────────────────────────────────────────

# Ver alertas en tiempo real
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# Dashboard web
# http://192.168.0.110:8080

# Ver ipsets en servidor
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
ssh m4rk@192.168.0.120 "sudo ipset list ppi_limited"

# ── CONTROL MANUAL ────────────────────────────────────────────────────────────

# Bloquear IP manualmente
ssh m4rk@192.168.0.110 \
  "bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 300"

# Desbloquear
ssh m4rk@192.168.0.110 \
  "bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK"

# Reiniciar motor (limpia in-memory + recarga τ de metricas_offline.txt)
ssh m4rk@192.168.0.110 \
  "echo cisco123 | sudo -S systemctl restart ppi-motor.service"

# ── EJECUTAR SUITE DE VERIFICACIÓN ────────────────────────────────────────────

# NOTA: scripts de verificación automatizada pendientes de creación
# Los tests se ejecutaron manualmente (ver resultados en §9)
# Referencia de comandos individuales — ver §7 para verificación manual
bash /home/m4rk/Descargas/verificacion/RUN_VERIFICACION_COMPLETA.sh RAPIDO   # pendiente
bash /home/m4rk/Descargas/verificacion/RUN_VERIFICACION_COMPLETA.sh TODOS    # pendiente
bash /home/m4rk/Descargas/verificacion/RUN_VERIFICACION_COMPLETA.sh B5       # pendiente
bash /home/m4rk/Descargas/verificacion/RUN_VERIFICACION_COMPLETA.sh B1       # pendiente

# ── DEMO RÁPIDA DE DETECCIÓN (manual, 30s) ────────────────────────────────────

# Test B5 rápido: BLOCK en ~30s
ssh -o BatchMode=yes -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "nohup bash -c 'while true; do curl -s -o /dev/null http://192.168.0.120/; done' > /dev/null 2>&1 &"
sleep 35
ssh m4rk@192.168.0.110 \
  "tail -3 /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```

---

## 8. Criterios de Éxito por Escenario

| Escenario | Condición de éxito | Verificación |
|---|---|---|
| A1–A4 | 0 WARNINGs para .20 | `grep 192.168.0.20 motor_decision.log \| grep WARNING` → vacío |
| B1 SYN | `.100` en `ppi_blocked` | `ipset list ppi_blocked \| grep .100` |
| B2 Scan | `.100` en `ppi_blocked` | ídem |
| B3 UDP | `.100` en `ppi_blocked` | ídem |
| B4 ICMP | `.100` en `ppi_blocked` | ídem |
| B5 HTTP | Log `HTTP-ABUSE` + BLOCK | `grep HTTP-ABUSE motor_decision.log` |
| B6 BF | Log `BRUTE-FORCE` + BLOCK | `grep BRUTE-FORCE motor_decision.log` |
| C1–C3 | `.100` blocked + `.20` accesible | `curl http://.120/` → 200 + ipset check |
| Telegram | Alerta recibida en bot | Revisar chat Telegram |
| Dashboard | Alerta en UI | `http://192.168.0.110:8080` → tab Alertas |

---

## 9. Resultados de Verificación (2026-06-17)

| Test | Resultado | Evidencia |
|---|---|---|
| Setup | PASS | Motor τ1=−0.4459, relay:8889, dashboard:8080 activos |
| A1-A4 Tráfico Normal | PASS | 0 alertas, 0 entradas ipset — Desktop.20 en WHITELIST (35 ciclos, 120s) |
| Whitelist test | PASS | .20 y .110 NO bloqueadas; enforce.sh manual→BLOCK/UNBLOCK OK |
| B1 SYN Flood  | PASS    | LIMIT(score=-0.4937) + HTTP-ABUSE BLOCK en 11s |
| B2 Port Scan  | PASS    | IF score=-0.7352 → BLOCK en <1s |
| B3 UDP Flood  | PARCIAL | IP rate-limitada (LIMIT), flows UDP → PERMIT por IF |
| B4 ICMP Flood | VARIABLE | Offline AUC=0.8961 Det%=100%; real-time: 0 det. (ver §B4) |
| C1 HTTP+SYNFlood | PASS    | Kali BLOCK(HTTP-ABUSE 10s) Desktop OK=60 FAIL=0 ITL=0% |
| C2 SSH+PortScan  | PASS    | Kali BLOCK(IF score=-0.7333) Desktop OK=53 FAIL=0 ITL=0% |
| C3 SCP+UDPFlood  | PARCIAL | Kali no bloqueada (gap UDP), Desktop OK=60 FAIL=0 |
| B5 HTTP Abuse | PASS | BLOCK a los 63s, `.100` en `ppi_blocked` |
| B6 BruteForce | PASS | BLOCK detectado, `.100` en `ppi_blocked` |
| Telegram relay | PASS | relay Desktop:8889 → `api.telegram.org` OK |
| Dashboard | PASS | `/api/stats`, `/api/alerts` con datos reales |

---

## 10. Scripts de Verificación (`/home/m4rk/Descargas/verificacion/`)

> **Estado:** Estos scripts están documentados como referencia de la suite de verificación planeada. **No están creados en el repositorio actual** — el directorio `/home/m4rk/Descargas/verificacion/` no existe en el sensor. Los tests de verificación se ejecutaron manualmente durante el desarrollo (resultados en §9). La creación automatizada de estos scripts queda como trabajo futuro.

| Script | Descripción | Duración |
|---|---|---|
| `00_setup_verificacion.sh` | Pre-requisitos, conectividad, motor | 2 min |
| `01_test_A_normal_FP.sh` | Grupo A normal + análisis FP | 5 min |
| `02_test_B1_synflood.sh` | B1 SYN Flood (IF score) | 5 min |
| `03_test_B2_portscan.sh` | B2 Port Scan (IF score) | 4 min |
| `04_test_B3_udpflood.sh` | B3 UDP Flood (IF score) | 4 min |
| `05_test_B4_icmpflood.sh` | B4 ICMP Flood (IF score) | 4 min |
| `06_test_B5_httpabuse.sh` | B5 HTTP Abuse (heurístico HTTP) | 3 min |
| `07_test_B6_bruteforce.sh` | B6 BruteForce SSH (heurístico BF) | 3 min |
| `08_test_C_mixto.sh` | C1+C2+C3 mixtos selectivos | 15 min |
| `09_test_whitelist.sh` | Whitelist anti-falsos-positivos | 3 min |
| `10_reporte_final.sh` | Reporte consolidado | 1 min |
| `RUN_VERIFICACION_COMPLETA.sh` | Orquestador (TODOS/RAPIDO/B1/B5...) | 49 min |
