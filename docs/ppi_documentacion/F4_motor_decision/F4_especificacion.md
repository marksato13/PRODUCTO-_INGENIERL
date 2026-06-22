# F4 — Especificación Técnica: Motor de Decisión en Tiempo Real

## Estado: ✅ COMPLETA — criterios validados en F6


## 1. Objetivo y posición en el pipeline

Procesar flujos de Suricata **en tiempo real** (tail -f sobre eve.json), puntuar cada
flow con Isolation Forest y aplicar la acción de red correspondiente (PERMIT / LIMIT / BLOCK)
en el servidor vía ipset/iptables. Los umbrales τ1/τ2 se leen de `metricas_offline.txt`
al arrancar — sin edición manual tras re-entrenamientos de F3.

```
POSICIÓN EN EL PIPELINE COMPLETO

F3 (modelado offline)          F4 (motor tiempo real)         F5 / F6
────────────────────  →  ─────────────────────────────  →  ─────────────────
models/*.pkl                   motor_decision.py              dashboard.py
metricas_offline.txt      →    tail eve.json en vivo    →    dashboard_web.py
                               score IF + heurísticos         f6_corridas.py
                               enforce.sh → ipset             motor_decision.log
```

---

## 2. Terminología clave

### 2.1 ipset y iptables — cómo funciona el enforcement

**ipset** es una extensión del kernel Linux para gestionar conjuntos de IPs de forma
eficiente en memoria hash. Permite aplicar reglas de iptables a millones de IPs con
tiempo de lookup O(1):

```bash
# Estructura en servidor 192.168.0.120
ipset ppi_blocked  (hash:ip, timeout=300s)   ← IPs con DROP total
ipset ppi_limited  (hash:ip, timeout=300s)   ← IPs con rate limit 100 pkt/s

# Reglas iptables correspondientes (añadidas al arrancar el motor)
iptables -I INPUT 1 -m set --match-set ppi_blocked src -j DROP
iptables -I INPUT 2 -m set --match-set ppi_limited src \
  -m hashlimit --hashlimit-upto 100/sec --hashlimit-burst 200 \
  --hashlimit-mode srcip --hashlimit-name ppi_limit -j ACCEPT
```

Las IPs en `ppi_blocked` expiran automáticamente después de **300 segundos** (ipset
timeout). El motor no necesita limpiarlas manualmente.

### 2.2 hashlimit — rate limiting por IP

`hashlimit` limita paquetes por unidad de tiempo **por IP de origen**. Con `--hashlimit-upto 100/sec`:
- Los primeros 100 paquetes/segundo de la IP pasan (`-j ACCEPT`)
- El exceso se descarta sin alcanzar las reglas siguientes
- El servidor sigue respondiendo, pero a velocidad degradada

Esto es más suave que DROP y adecuado para la zona gris (τ2 < score ≤ τ1): la IP
puede ser un falso positivo, así que se limita sin cortarla.

### 2.3 seguir_eve() — tail con detección de rotación

El motor lee `eve.json` secuencialmente como `tail -f`, pero con detección de truncado:

```python
def seguir_eve(path):
    with open(path) as f:
        f.seek(0, 2)          # posicionarse al final (no leer histórico)
        while True:
            line = f.readline()
            if line:
                yield line    # nueva línea disponible → procesarla
            else:
                new_size = os.path.getsize(path)
                if new_size < f.tell():
                    f.seek(0) # truncado detectado → volver al inicio
                else:
                    time.sleep(0.1)  # polling cada 100ms
```

**Por qué polling (0.1s) y no inotify:** `inotify` requiere dependencias extra
(`pyinotify`). El polling de 100ms añade ≤100ms de latencia adicional, dejando el
pipeline total muy por debajo del requisito de 500ms.

**Detección de truncado:** cuando `exportar_eve_por_escenario.sh` ejecuta
`truncate -s 0 eve.json`, el tamaño del archivo baja a 0 pero el fd abierto del
motor sigue apuntando al final (posición > 0). En el siguiente poll, `getsize() < tell()`
→ el motor hace `seek(0)` y lee desde el principio del archivo vacío.

### 2.4 Estados en memoria del motor

El motor mantiene estado en RAM durante toda su ejecución (se pierde al reiniciar):

```python
bloqueados    = set()              # IPs actualmente en ipset ppi_blocked
limitados     = set()              # IPs actualmente en ipset ppi_limited
ssh_intentos  = defaultdict(list)  # ip → [t1, t2, ...] timestamps intentos SSH/60s
http_requests = defaultdict(list)  # ip → [t1, t2, ...] timestamps requests HTTP/30s
total_flows   = 0                  # flows procesados (contador global)
total_anom    = 0                  # flows con decisión LIMIT o BLOCK
total_bf      = 0                  # veces que disparó BruteForce detector
total_http_ab = 0                  # veces que disparó HTTP-Abuse detector
latencias_ms  = []                 # latencias del último batch de 500 flows
```

**`defaultdict(list)`:** cada clave (IP) tiene una lista de timestamps que crece al
llegar flows. Antes de cada evaluación, la lista se filtra para mantener solo los
timestamps dentro de la ventana activa (`ahora - ventana_seg`).

### 2.5 Clasificación de grado y tipo

**Grado** (calidad de la anomalía, basado en score IF):

```python
def clasificar_grado(score: float) -> str:
    if score > TAU1:     return "NORMAL"   # score > -0.4459
    elif score > TAU2:   return "BAJA"     # -0.6027 < score ≤ -0.4459
    elif score > -0.82:  return "ALTA"     # -0.82 < score ≤ -0.6027
    else:                return "CRITICA"  # score ≤ -0.82
```

| Grado | Score range | Ejemplo | Acción IF |
|---|---|---|---|
| NORMAL | > −0.4459 | curl normal, ssh legítimo | PERMIT |
| BAJA | −0.6027 a −0.4459 | SYN Flood gradual, HTTP Abuse | LIMIT |
| ALTA | −0.82 a −0.6027 | Port Scan, UDP/ICMP Flood | BLOCK |
| CRITICA | ≤ −0.82 | Ataque extremamente denso | BLOCK |

**Tipo** (nombre del ataque, basado en features + heurísticos):

```python
def clasificar_tipo(e, score, decision, ssh_intentos, http_requests) -> str:
    # Orden de prioridad (primero heurísticos, luego features IF)
    if dest_port == 22 and hay_intentos_ssh_recientes:  return "BRUTE_FORCE"
    if dest_port == 80 and hay_requests_http_recientes: return "HTTP_ABUSE"
    if proto == "ICMP" and pkt_rate > 300:              return "ICMP_FLOOD"
    if proto == "UDP"  and pkt_rate > 500:              return "UDP_FLOOD"
    if proto == "TCP"  and pkt_rate > 2000 and dur < 2.0 and bytes_toclient < 100:
                                                         return "SYN_FLOOD"
    if dest_port == 80 and proto == "TCP" and pkt_rate > 200:
                                                         return "HTTP_ABUSE"
    return "ANOMALIA"
```

### 2.6 Thread Telegram (arquitectura asíncrona)

El envío de alertas **no bloquea** el bucle principal:

```python
_tg_queue = Queue(maxsize=100)            # buffer de mensajes pendientes

# Hilo daemon iniciado al arrancar el motor:
threading.Thread(target=_tg_worker, daemon=True, name="tg-sender").start()

def _tg_worker():
    while True:
        msg = _tg_queue.get()             # bloquea hasta que haya mensaje
        POST http://192.168.0.20:8889/telegram  {"text": msg}
        _tg_queue.task_done()

def telegram_alerta(mensaje: str):
    _tg_queue.put_nowait(mensaje)         # no bloquea; descarta si queue llena
```

`daemon=True` garantiza que el hilo muera cuando el proceso principal termine
(sin necesidad de join() explícito). Si la queue se llena (>100 mensajes pendientes),
`put_nowait()` descarta la alerta sin interrumpir el motor.

---

## 3. Entradas

| Entrada | Ruta | Descripción |
|---|---|---|
| Flujos en tiempo real | `/var/log/suricata/eve.json` | tail -f — un JSON por línea, polling 100ms |
| Modelo IF | `models/isolation_forest.pkl` | Generado por `fase3_entrenar.py`, cargado al arrancar |
| Scaler | `models/scaler.pkl` | StandardScaler ajustado en 80% de datos normales |
| Features | `models/features.csv` | 14 nombres en orden exacto — valida el orden de columnas |
| Umbrales | `results/metricas_offline.txt` | τ1/τ2 — leídos al arrancar; valores por defecto si no existe |

---

## 4. Salidas

| Salida | Ruta / Destino | Descripción |
|---|---|---|
| Log del motor | `results/motor_decision.log` | Decisiones WARNING (LIMIT/BLOCK), INFO (stats cada 500), DEBUG (PERMIT) |
| Bloqueos activos | ipset `ppi_blocked` en servidor .120 | IPs con iptables DROP — timeout 300s |
| Limitaciones activas | ipset `ppi_limited` en servidor .120 | IPs con hashlimit 100 pkt/s — timeout 300s |
| Alertas Telegram | relay `http://192.168.0.20:8889` | Push al operador para LIMIT y BLOCK |

---

## 5. Arranque del motor (secuencia de inicialización)

```
ppi-motor.service arranca motor_decision.py
       │
t=0s   load_model():
         clf   = joblib.load('models/isolation_forest.pkl')
         scaler = joblib.load('models/scaler.pkl')
         log.info(f"Modelo cargado | τ1={TAU1} | τ2={TAU2}")
       │
t=0s   Leer metricas_offline.txt:
         TAU1, TAU2 = -0.4459, -0.6027  (hardcoded por defecto)
         Si existe el archivo → parsear tau1/tau2 y sobreescribir
         regex r'\s*tau1\s*:\s*[-\d]' previene parsear 'tau1_fpr' por error
       │
t=1s   inicializar_servidor() — SSH a 192.168.0.120:
         sudo ipset create ppi_blocked hash:ip timeout 300 2>/dev/null || true
         sudo iptables -C INPUT -m set --match-set ppi_blocked src -j DROP 2>/dev/null
           || sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP
         sudo ipset create ppi_limited hash:ip timeout 300 2>/dev/null || true
         sudo iptables -I INPUT 2 -m set --match-set ppi_limited src \
           -m hashlimit --hashlimit-upto 100/sec ... -j ACCEPT
         (idempotente: 2>/dev/null || true maneja re-ejecuciones)
       │
t=2s   Thread tg-sender iniciado (daemon=True)
       │
t=2s   Inicializar contadores en memoria:
         bloqueados = set(), limitados = set()
         ssh_intentos = defaultdict(list), http_requests = defaultdict(list)
         total_flows = 0, latencias_ms = []
       │
t=2s   log.info("Monitoreando /var/log/suricata/eve.json ...")
       │
t=2s   seguir_eve() → seek(0, 2) → posición al FINAL del eve.json actual
       │
       BUCLE PRINCIPAL (ver §6)
```

---

## 6. Flujo de procesamiento de un flow (paso a paso)

Ejemplo real: **Port Scan desde Kali** (primera detección)

```
t=0ms   seguir_eve() → readline() de eve.json:
        {"event_type":"flow","src_ip":"192.168.0.100","dest_ip":"192.168.0.120",
         "dest_port":80,"proto":"TCP",
         "flow":{"pkts_toserver":1,"pkts_toclient":0,
                 "bytes_toserver":60,"bytes_toclient":0,
                 "start":"2026-06-15T21:44:57.100Z","end":"2026-06-15T21:44:57.120Z"}}

t=0.1ms  json.loads() → dict e
         e.get('event_type') == 'flow'?         → SÍ, continuar
         src_ip = '192.168.0.100'
         ':' in src_ip?                          → NO (no IPv6)
         src_ip in WHITELIST?                    → NO (Kali no está en whitelist)
         es_ip_bloqueable('192.168.0.100')?      → SÍ (IP privada .100)
         flow.pkts_toserver = 1 > 0?             → SÍ
         total_flows += 1

t=0.5ms  t_proc_ini = time.time()

         extract_features(e):
           pkts_toserver = 1,  pkts_toclient = 0
           bytes_toserver = 60, bytes_toclient = 0
           duration = (end - start).total_seconds() = 0.020s
           pkt_rate = (1+0) / max(0.020, 0.001) = 50.0 pkt/s
           byte_rate = (60+0) / 0.020 = 3000.0 B/s
           pkt_ratio = 1 / (0+1) = 1.0
           byte_ratio = 60 / (0+1) = 60.0
           avg_pkt_size = (60+0) / max(1+0,1) = 60.0 B
           is_tcp=1, is_udp=0, is_icmp=0
           dest_port=80
           → X_raw = [1, 0, 60, 0, 0.020, 50.0, 3000.0, 1.0, 60.0, 60.0, 1, 0, 0, 80]

t=1ms    X_scaled = scaler.transform([X_raw])   ← aplica mean/std de F3
         score = clf.score_samples(X_scaled)[0]  = -0.7333
         latencia_ms = ~0.5ms (solo el modelo; SSH viene después)

t=1.5ms  dest_port=80, proto='TCP', ts_flow=1750024697.1

         ─── HTTP Abuse detector ───
         detectar_http_abuse('192.168.0.100', 80, ts_flow, http_requests)
         http_requests['192.168.0.100'].append(ts_flow)  → [ts_flow]   n=1
         1 < HTTP_UMBRAL_LIMIT(50) → resultado: None

         ─── BF-SSH detector ───
         detectar_brute_force('192.168.0.100', 80, ts_flow, ssh_intentos)
         dest_port(80) != SSH_PORT(22) → return None inmediatamente

         ─── Decisión IF ───
         accion = decidir(-0.7333):  -0.7333 ≤ TAU2(-0.6027) → 'BLOCK'
         grado  = clasificar_grado(-0.7333):  -0.82 < -0.7333 ≤ -0.6027 → 'ALTA'
         tipo   = clasificar_tipo(...):  pkt_rate=50 (no SYN_FLOOD nivel),
                  pkts_toclient=0, duration=0.020 → 'ANOMALIA' o 'PORT_SCAN'

t=2ms    '192.168.0.100' in bloqueados? → NO (primera vez)
         bloqueados.add('192.168.0.100')

         bloquear_ip('192.168.0.100'):
           _ssh('sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist')
           → subprocess.run(['ssh','-o','BatchMode=yes','m4rk@192.168.0.120', '...'])

t=~100ms SSH al servidor completo
         ipset ppi_blocked en .120: {192.168.0.100 (TTL=300s)}
         iptables ya tenía: -I INPUT 1 --match-set ppi_blocked src -j DROP
         → TODOS los paquetes futuros de 192.168.0.100 son DROPeados en servidor

t=100ms  log.warning(
           "ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 "
           "proto=TCP score=-0.7333 grado=ALTA tipo=ANOMALIA | BLOCK"
         )

t=100ms  telegram_alerta("🚨 PPI ALERTA — ANOMALIA\n...")
         _tg_queue.put_nowait(msg)   ← no bloqueante

t=101ms  bucle → siguiente readline() de eve.json

─── PARALELO: hilo tg-sender ───────────────────────────────────
t~102ms  _tg_queue.get() → obtiene el mensaje
         POST http://192.168.0.20:8889/telegram  {"text": "🚨 PPI ALERTA..."}
t~1.5s   relay → HTTPS api.telegram.org → operador recibe notificación

─── t=300s: AUTO-EXPIRACIÓN ────────────────────────────────────
         ipset timeout agota en servidor → 192.168.0.100 sale de ppi_blocked
         Motor no es notificado → 192.168.0.100 sigue en bloqueados (set en RAM)
         Si el motor se reinicia → bloqueados se vacía → re-detección normal
```

---

## 7. Lógica de decisión completa

```
Para cada flow que pasa los filtros (no whitelist, no IPv6, pkts_toserver > 0):

PASO 1 — Heurístico HTTP Abuse (port 80, TCP)
  http_requests[ip].filtrar_ventana(30s)
  Si n ≥ 100 → BLOCK (override sobre score IF)
  Si n ≥  50 → LIMIT (override sobre score IF)

PASO 2 — Heurístico BF-SSH (port 22)
  ssh_intentos[ip].filtrar_ventana(60s)
  Si n ≥ 15 → BLOCK (override sobre score IF)
  Si n ≥  5 → LIMIT (override sobre score IF)

PASO 3 — Score Isolation Forest
  X_scaled = scaler.transform(extract_features(flow))
  score    = clf.score_samples(X_scaled)[0]          # [-1, 0]

  Si score ≤ TAU2 (-0.6027): accion = BLOCK
  Si score ≤ TAU1 (-0.4459): accion = LIMIT
  Else:                       accion = PERMIT

NOTA: Los heurísticos (PASO 1 y 2) se evalúan ANTES del score IF.
Si disparan, aplican su acción INDEPENDIENTEMENTE del score.
El score IF sigue evaluándose para clasificación y log.
Un flow puede recibir BLOCK por heurístico aunque IF diga PERMIT.
```

---

## 8. Detectores heurísticos (ventanas deslizantes)

### 8.1 BF-SSH — Brute Force SSH

```python
BF_PORT         = 22
BF_VENTANA_SEG  = 60    # ventana deslizante de observación
BF_UMBRAL_LIMIT = 5     # intentos en ventana → LIMIT (hashlimit)
BF_UMBRAL_BLOCK = 15    # intentos en ventana → BLOCK (DROP)

def detectar_brute_force(ip, dest_port, ts_flow, ssh_intentos):
    if dest_port != BF_PORT: return None
    ahora = ts_flow
    ventana_inicio = ahora - BF_VENTANA_SEG
    ssh_intentos[ip].append(ahora)
    # Mantener solo timestamps en la ventana activa
    ssh_intentos[ip] = [t for t in ssh_intentos[ip] if t >= ventana_inicio]
    n = len(ssh_intentos[ip])
    if n >= BF_UMBRAL_BLOCK:  return ('BLOCK', n)
    if n >= BF_UMBRAL_LIMIT:  return ('LIMIT', n)
    return None
```

Ejemplo: hydra envía 30 intentos/60s → al 5° intento → LIMIT → al 15° → BLOCK

### 8.2 HTTP-Abuse

```python
HTTP_PORT          = 80
HTTP_VENTANA_SEG   = 30   # ventana deslizante de observación
HTTP_UMBRAL_LIMIT  = 50   # requests en ventana → LIMIT
HTTP_UMBRAL_BLOCK  = 100  # requests en ventana → BLOCK

def detectar_http_abuse(ip, dest_port, ts_flow, http_requests):
    if dest_port != HTTP_PORT: return None
    ahora = ts_flow
    ventana_inicio = ahora - HTTP_VENTANA_SEG
    http_requests[ip].append(ahora)
    http_requests[ip] = [t for t in http_requests[ip] if t >= ventana_inicio]
    n = len(http_requests[ip])
    if n >= HTTP_UMBRAL_BLOCK: return ('BLOCK', n)
    if n >= HTTP_UMBRAL_LIMIT: return ('LIMIT', n)
    return None
```

Ejemplo: curl en bucle agresivo → 100 requests en 30s → BLOCK en ~10 segundos

---

## 9. Ciclo de vida de un bloqueo

```
DETECCIÓN
  score ≤ τ2 (o heurístico BLOCK)
  src_ip NOT in bloqueados  ← evita doble enforcement
  bloqueados.add(src_ip)
       │
       ▼
ENFORCEMENT (SSH desde sensor .110 → servidor .120, ~100ms)
  sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist
  iptables INPUT DROP (regla pre-existente)
  → Paquetes de .100 DROPeados ANTES de llegar a nginx/SSH
       │
       ▼
ESTADO ACTIVO (0–300s)
  Flows siguientes de .100 en eve.json:
    Suricata sigue capturando (está en el switch, antes del DROP)
    Motor evalúa → score < τ2 → "BLOCK (ya bloqueado)" → log.debug, sin SSH
    Contadores ssh_intentos / http_requests siguen actualizándose
       │
  t = 300s: ipset timeout automático (sin acción del motor)
       │
       ▼
AUTO-EXPIRACIÓN
  IP sale de ppi_blocked en el servidor → tráfico vuelve a pasar
  Motor: IP sigue en bloqueados set (en RAM) hasta reinicio del servicio
  → Si ataca de nuevo: motor detecta "ya en bloqueados" → solo log.debug
  → Para re-bloquear sin reiniciar: bash enforce.sh 192.168.0.100 BLOCK 300
  → Para limpiar estado en RAM:     sudo systemctl restart ppi-motor.service
```

---

## 10. Enforcement en servidor (192.168.0.120)

`enforce.sh` es llamado por `bloquear_ip()` / `limitar_ip()` internamente, pero
también puede usarse manualmente:

```bash
# scripts/enforce.sh
SERVIDOR="192.168.0.120"
_srv() { ssh -o BatchMode=yes -o ConnectTimeout=5 m4rk@$SERVIDOR "$1"; }

case "$ACCION" in
  BLOCK)   _srv "sudo ipset add ppi_blocked $IP timeout $TIMEOUT -exist" ;;
  LIMIT)   _srv "sudo ipset add ppi_limited $IP timeout $TIMEOUT -exist" ;;
  UNBLOCK) _srv "sudo ipset del ppi_blocked $IP 2>/dev/null || true"
           _srv "sudo ipset del ppi_limited $IP 2>/dev/null || true" ;;
esac
```

| Acción | Mecanismo en servidor | Timeout | Efecto en tráfico |
|---|---|---|---|
| BLOCK | `ipset add ppi_blocked` → iptables `-j DROP` | 300s | DROP total de paquetes |
| LIMIT | `ipset add ppi_limited` → hashlimit 100pkt/s | 300s | Degrada a 100 pkt/s máximo |
| UNBLOCK | `ipset del` de ambos sets | inmediato | Tráfico normal restaurado |

Los ipsets están en el **servidor (.120)**, no en el sensor (.110). El sensor solo
monitorea — no filtra paquetes. El enforcement es en el destino del tráfico.

---

## 11. Alertas Telegram

El sensor (.110) no tiene acceso a internet → relay en Desktop (.20):

```
motor_decision.py (sensor .110)
    │ LIMIT/BLOCK detectado
    │ telegram_alerta(msg)
    │   └── _tg_queue.put_nowait(msg)    ← no bloquea el bucle principal
    │
    │ Thread "tg-sender" (daemon):
    │   msg = _tg_queue.get()
    │   POST http://192.168.0.20:8889/telegram  {text: msg}
    ▼
telegram_relay.py (Desktop .20, puerto 8889)
    │ Recibe POST JSON
    │ Reenvía a api.telegram.org/bot.../sendMessage
    ▼
Bot Telegram → notificación al operador
```

**Constantes reales en motor_decision.py:**
```python
TG_TOKEN   = "8677152686:AAEUKDJm0gbkc7Vu3NwRcNaxqx3iqQwaa7g"
TG_CHAT_ID = "8512353253"
TG_RELAY   = "http://192.168.0.20:8889/telegram"
```

**Mensajes enviados por evento:**

| Evento | Emoji | Campos en el mensaje |
|---|---|---|
| BLOCK por IF | 🚨 | tipo, accion, IP, proto, puerto, score, grado, hora |
| LIMIT por IF | ⚠️ | tipo, accion, IP, proto, puerto, score, grado, hora |
| HTTP-ABUSE BLOCK | ⚠️ | accion=BLOCK, IP, puerto, requests/30s, hora |
| HTTP-ABUSE LIMIT | ⚠️ | accion=LIMIT, IP, puerto, requests/30s, hora |
| BF-SSH BLOCK | 🚨 | accion=BLOCK, IP, puerto, intentos/60s, hora |
| BF-SSH LIMIT | ⚠️ | accion=LIMIT, IP, puerto, intentos/60s, hora |

---

## 12. Formato del log (`results/motor_decision.log`)

```
# ARRANQUE
2026-06-16 17:38:01,123 INFO  Motor de decisión PPI — iniciando
2026-06-16 17:38:02,456 INFO  Modelo cargado | umbral_base=-0.0000 | τ1=-0.4459 | τ2=-0.6027
2026-06-16 17:38:03,789 INFO  Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=-0.4459 τ2=-0.6027
2026-06-16 17:38:03,790 INFO  Monitoreando /var/log/suricata/eve.json ...

# FLOW NORMAL (DEBUG — no aparece en log estándar)
2026-06-16 19:38:00,001 DEBUG normal | src=192.168.0.20 dst=192.168.0.120:80 proto=TCP score=-0.3821 | PERMIT

# FLOW SOSPECHOSO (LIMIT)
2026-06-16 19:38:01,234 WARNING SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.4937 grado=BAJA tipo=SYN_FLOOD | LIMIT

# FLOW ANÓMALO (BLOCK)
2026-06-16 19:38:42,567 WARNING ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.7333 grado=ALTA tipo=ANOMALIA | BLOCK

# HEURÍSTICO HTTP-ABUSE
2026-06-16 19:40:15,890 WARNING HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP requests=100/30s | BLOCK

# HEURÍSTICO BF-SSH
2026-06-16 19:41:02,123 WARNING BRUTE-FORCE | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP intentos=15/60s | BLOCK

# ESTADÍSTICAS CADA 500 FLOWS
2026-06-16 19:39:06,456 INFO  Estadísticas | flows=500 anomalías=2 bf=0 http_abuse=0 bloqueados=1 limitados=0 latencia_media=34.51ms

# FLOW YA BLOQUEADO (DEBUG — sin re-enforce)
2026-06-16 19:38:45,678 DEBUG ANOMALÍA | src=192.168.0.100 ... score=-0.7100 | BLOCK (ya bloqueado)
```

---

## 13. Métricas de rendimiento validadas (F6)

| Métrica | Valor | Requisito | Estado |
|---|---|---|---|
| Latencia media pipeline | **34.51 ms** | < 500 ms | ✅ CUMPLE |
| Latencia P95 | **34.8 ms** | < 500 ms | ✅ CUMPLE |
| Lead Time SYN Flood | **~62 s** | < 120 s | ✅ CUMPLE |
| ITL (interrupción tráfico legítimo) | **0%** | = 0% | ✅ CUMPLE |
| Disponibilidad servicio | **100%** | > 99% | ✅ CUMPLE |
| Alertas Telegram entregadas | **100%** | — | ✅ |

**¿Por qué Lead Time ≈62s en SYN Flood?**
Suricata emite el evento `flow` TCP solo cuando la conexión **se cierra** o **expira**.
Los SYN Floods sin completar el handshake (sin ACK del servidor) mantienen los flows
en estado `new` hasta que el timeout de Suricata para TCP half-open (~60s) los cierra.
El motor no puede actuar antes de recibir el evento `flow` de Suricata. Los ataques
con flows que se cierran rápidamente (Port Scan, UDP Flood) tienen Lead Time < 5s.

**¿Por qué ITL=0%?**
El Desktop (192.168.0.20), Sensor (.110) y Servidor (.120) están en WHITELIST.
Son los únicos hosts que generan tráfico legítimo en el laboratorio. Nunca son
evaluados por el motor → nunca pueden recibir LIMIT/BLOCK erróneo.

---

## 14. Concurrencia del motor

```
PROCESO PRINCIPAL (motor_decision.py)
│
├── Thread MAIN:
│     seguir_eve() → parse → filtros → extract_features()
│     → scaler.transform() → IF.score_samples()
│     → heurísticos → decidir() → enforce.sh (SSH síncrono ~100ms)
│     → log → telegram_alerta() [solo encola, no espera]
│     → estadísticas cada 500 flows
│
└── Thread "tg-sender" (daemon):
      while True:
        msg = _tg_queue.get()         ← bloquea esperando mensajes
        POST relay:8889               ← puede tardar 1-5s (red)
        _tg_queue.task_done()
      (muere automáticamente cuando el proceso principal termina)
```

El único punto de sincronización es `_tg_queue` (thread-safe por diseño en Python).
No hay locks, no hay condiciones de carrera porque solo el hilo main escribe en
`bloqueados`, `limitados`, `ssh_intentos`, `http_requests`.

---

## 15. Conexión F4 → F5 (dashboards)

```
results/motor_decision.log
       │
       ├── dashboard.py     ← lee el log cada 3s, muestra stats en terminal
       │                       parsea líneas "Estadísticas | flows=..." y "WARNING"
       │
       └── dashboard_web.py ← Flask + SSE en :8080
                               tail -f del log → Server-Sent Events al navegador
                               Acceso: http://192.168.0.110:8080
```

---

## 16. Secuencia de operación F4

```bash
# 0. PRE-REQUISITO: relay Telegram activo en Desktop
python3 /home/m4rk/Descargas/telegram_relay.py &
ss -tlnp | grep 8889   # verificar puerto 8889

# 1. Iniciar motor en sensor
sudo systemctl start ppi-motor.service

# 2. Verificar que leyó τ correctamente
sleep 3
grep "τ1=" results/motor_decision.log | tail -1
# → 2026-06-16 17:38:02 INFO  Modelo cargado | τ1=-0.4459 | τ2=-0.6027

# 3. Monitorear en tiempo real
tail -f results/motor_decision.log

# 4. Dashboard web (opcional)
nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &
# Acceder desde Desktop: http://192.168.0.110:8080

# 5. Control manual de bloqueos
bash scripts/enforce.sh 192.168.0.100 BLOCK 300
bash scripts/enforce.sh 192.168.0.100 UNBLOCK

# 6. Ver estado de ipsets en servidor
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
ssh m4rk@192.168.0.120 "sudo ipset list ppi_limited"

# 7. Reiniciar motor (limpia contadores en RAM, ipsets persisten en servidor)
sudo systemctl restart ppi-motor.service
```

---

## 17. Criterios de éxito (salida de F4)

| Criterio | Comando de verificación | Resultado esperado |
|---|---|---|
| Motor activo | `systemctl is-active ppi-motor.service` | `active` |
| τ leídos del archivo | `grep "τ1=" results/motor_decision.log \| head -1` | `τ1=-0.4459` |
| Flow procesado | `tail -5 results/motor_decision.log` | Líneas de eventos o stats |
| BLOCK funciona | `bash enforce.sh 192.168.0.100 BLOCK 10` | IP en `ipset list ppi_blocked` en .120 |
| BLOCK expira solo | (esperar 10s) `ipset list ppi_blocked` en .120 | IP desaparece |
| Latencia OK | stats en log cada 500 flows | `latencia_media < 500ms` |
| Relay Telegram activo | `ss -tlnp \| grep 8889` en Desktop | Puerto 8889 escuchando |
| Alerta Telegram OK | `bash enforce.sh 192.168.0.100 BLOCK 5` + revisar bot | Mensaje en <5s |
| ITL=0% con whitelist | curl normal desde Desktop durante ataque Kali | Sin interrupciones |

**F4 se considera ACTIVO** cuando el log muestra τ1/τ2 correctos al arranque,
el servidor tiene los ipsets creados, y un flow anómalo de prueba genera alerta
Telegram en menos de 5 segundos.
