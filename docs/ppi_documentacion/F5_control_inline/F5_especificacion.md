# F5 — Especificación Técnica: Control Inline y Monitoreo

## Estado: ✅ COMPLETA — criterios validados en F6


## 1. Objetivo y posición en el pipeline

F5 agrupa los tres mecanismos de acción y observabilidad del sistema:

1. **Enforcement:** aplicar las decisiones del motor (BLOCK/LIMIT) sobre el tráfico real
   mediante ipset/iptables en el servidor, sin interrumpir el flujo de paquetes legítimos.
2. **Monitoreo:** visualizar el estado del sistema en tiempo real vía dashboard terminal
   (ANSI) y dashboard web (Flask + SSE).
3. **Notificación:** alertar al operador por Telegram en menos de 5 segundos desde la detección.

```
POSICIÓN EN EL PIPELINE COMPLETO

F4 (motor)                F5 (control + monitoreo)         F6 (validación)
──────────────  →   ──────────────────────────────────  →  ─────────────────
motor_decision.py   enforce.sh  → ipset/iptables .120       f6_corridas.py
BLOCK/LIMIT     →   dashboard.py → terminal ANSI        →   lee motor_decision.log
motor_decision.log  dashboard_web.py → Flask:8080            durante 40 corridas
                    telegram_relay.py → bot Telegram
```

---

## 2. Terminología clave

### 2.1 ipset hash:ip — estructura real en el servidor

`ipset` gestiona conjuntos de IPs en una hash table del kernel con tiempo de lookup O(1).
El estado real en el servidor (192.168.0.120):

```
Name: ppi_blocked
Header: family inet hashsize 1024 maxelem 65536 timeout 300
        bucketsize 12 initval 0xa4c9efb6
Members:   ← IPs bloqueadas (vacío cuando no hay ataques activos)

Name: ppi_limited
Header: family inet hashsize 1024 maxelem 65536 timeout 300
        bucketsize 12 initval 0x1cd390c0
Members:   ← IPs limitadas (vacío cuando no hay ataques activos)
```

El campo `timeout 300` es el **timeout por defecto** al crear el set. Cada IP añadida
hereda este timeout y desaparece automáticamente del set 300 segundos después de
`ipset add`, sin intervención del motor.

### 2.2 Reglas iptables reales (estado verificado en servidor)

```bash
# sudo iptables -L INPUT -n --line-numbers   (salida real del servidor)
Chain INPUT (policy ACCEPT)
num  target  prot  opt  source      destination
1    DROP    all   --   0.0.0.0/0   0.0.0.0/0   match-set ppi_blocked src
2    DROP    all   --   0.0.0.0/0   0.0.0.0/0   match-set ppi_limited src
                                                  limit: above 100/sec burst 150 mode srcip
```

**Regla 1 (BLOCK):** si el paquete proviene de una IP en `ppi_blocked` → DROP incondicional.

**Regla 2 (LIMIT):** si el paquete proviene de una IP en `ppi_limited` Y la tasa
**supera** 100 paquetes/segundo (burst de hasta 150) → DROP. Los paquetes que no
superan la tasa salen de la regla 2 sin coincidir y llegan al resto de la cadena
(`policy ACCEPT`).

**Parámetros de hashlimit:**
- `above 100/sec`: descarta si la tasa del último segundo supera 100 pkt/s
- `burst 150`: permite ráfagas de hasta 150 paquetes antes de comenzar a descartar
- `mode srcip`: el contador es por IP de origen (no global)

### 2.3 SSE (Server-Sent Events)

SSE es un protocolo HTTP unidireccional donde el servidor envía eventos al navegador
sin que éste los solicite. En `dashboard_web.py`:

```
Navegador GET /api/stream  (conexión HTTP persistente)
       ↑
       │  data: {"accion":"BLOCK","src":"192.168.0.100",...}\n\n
       │  (cada vez que log_reader detecta un evento nuevo)
       │
dashboard_web.py: push_sse(ev) → pone en cada sse_clients[i] (queue por cliente)
                  generate() → yield "data: {json}\n\n" (streaming)
```

Ventaja sobre polling: el navegador recibe el evento en milisegundos sin enviar
una petición GET cada N segundos.

### 2.4 Estado clase — dashboard.py

El dashboard terminal usa una clase `Estado` para acumular eventos en memoria:

```python
class Estado:
    eventos    = deque(maxlen=300)  # últimos 300 eventos (ts_epoch, dict)
    vent_min   = deque()            # timestamps de los últimos 60s (para F/min)
    flows_total  = 0                # de la línea "Estadísticas" del log
    anom_total   = 0
    bf_total     = 0
    http_total   = 0
    bloq_total   = 0
    lim_total    = 0
    latencia     = 0.0              # latencia media del último batch 500 flows
    motor_inicio = "—"              # hora de inicio del motor
```

`deque(maxlen=300)` descarta automáticamente el evento más antiguo cuando llega el
evento 301, manteniendo el uso de memoria acotado.

### 2.5 NOPASSWD sudoers — por qué es necesario

El motor y los dashboards ejecutan `sudo ipset`/`sudo iptables` de forma no interactiva
(sin terminal ni contraseña). La configuración en el servidor:

```
# /etc/sudoers.d/ppi  (en 192.168.0.120)
m4rk ALL=(ALL) NOPASSWD: /usr/sbin/ipset, /usr/sbin/iptables
```

Sin esto, `ssh m4rk@192.168.0.120 "sudo ipset add ..."` fallaría con
`sudo: a terminal is required to read the password`.

---

## 3. Componentes de F5

| Componente | Ruta | Líneas | Rol |
|---|---|---|---|
| `enforce.sh` | `scripts/enforce.sh` | 38 | Control manual BLOCK/LIMIT/UNBLOCK vía CLI |
| `dashboard.py` | `scripts/dashboard.py` | 343 | Dashboard terminal ANSI — refresh cada 3s |
| `dashboard_web.py` | `scripts/dashboard_web.py` | 1,477 | Dashboard web Flask+SSE en puerto :8080 |
| `telegram_relay.py` | `/home/m4rk/Descargas/` (Desktop .20) | ~50 | Relay HTTP:8889 → api.telegram.org |

---

## 4. enforce.sh — control manual de bloqueos

Script de 38 líneas para aplicar BLOCK/LIMIT/UNBLOCK manualmente, sin necesidad
de que el motor esté corriendo.

```bash
#!/usr/bin/env bash
# scripts/enforce.sh — Control inline PPI
# Aplica accion de bloqueo/limite sobre una IP en el SERVIDOR (192.168.0.120)
# Uso: enforce.sh <ip> <accion> [timeout_seg]

set -euo pipefail

IP="$1"
ACCION="${2:-BLOCK}"
TIMEOUT="${3:-300}"

SET_BLOCK="ppi_blocked"
SET_LIMIT="ppi_limited"
SERVIDOR="192.168.0.120"
SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

_srv() { ssh $SSH_OPTS m4rk@$SERVIDOR "$1"; }

case "$ACCION" in
  BLOCK)
    _srv "sudo ipset add $SET_BLOCK $IP timeout $TIMEOUT -exist"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | BLOCK | $IP | timeout=${TIMEOUT}s"
    ;;
  LIMIT)
    _srv "sudo ipset add $SET_LIMIT $IP timeout $TIMEOUT -exist"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | LIMIT | $IP | 100pkt/s | timeout=${TIMEOUT}s"
    ;;
  UNBLOCK)
    _srv "sudo ipset del $SET_BLOCK $IP 2>/dev/null || true"
    _srv "sudo ipset del $SET_LIMIT $IP 2>/dev/null || true"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | UNBLOCK | $IP"
    ;;
esac
```

**Idempotencia:** el flag `-exist` en `ipset add` evita error si la IP ya está en el
set (actualiza el timeout). `2>/dev/null || true` en UNBLOCK evita error si la IP
no estaba en el set.

**Casos de uso:**

```bash
# Desde sensor (192.168.0.110) o Desktop (192.168.0.20)
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 300
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 LIMIT 60
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK

# Verificar resultado en servidor
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
ssh m4rk@192.168.0.120 "sudo ipset list ppi_limited"
```

---

## 5. Flujo de un paquete de red en el servidor

Este es el recorrido de cada paquete desde que entra al servidor hasta que se acepta
o descarta. Refleja el estado real de iptables verificado en 192.168.0.120:

```
PAQUETE ENTRANTE (src=192.168.0.100, dst=192.168.0.120:80)
       │
       ▼
iptables INPUT chain (kernel)
       │
       ├── Regla 1: ¿src_ip ∈ ppi_blocked?
       │         SÍ → DROP  ← paquete descartado, sin respuesta
       │         NO ↓
       │
       ├── Regla 2: ¿src_ip ∈ ppi_limited?
       │         NO → (pasa a policy ACCEPT → llega a nginx/SSH)
       │         SÍ ↓
       │           ¿tasa > 100 pkt/s (burst 150)?
       │             SÍ → DROP  ← paquete de exceso descartado
       │             NO → (pasa a policy ACCEPT → llega a nginx/SSH)
       │
       └── Policy ACCEPT → nginx:80 o SSH:22

EJEMPLOS CONCRETOS:

Desktop .20 (curl legítimo):
  → No está en ningún ipset → ACCEPT → nginx responde 200 OK

Kali .100 (BLOQUEADA):
  → Está en ppi_blocked → Regla 1 → DROP
  → nginx nunca ve el paquete
  → Suricata SÍ lo captura (está antes del firewall) → motor sigue viendo los flows

Kali .100 (LIMITADA):
  → Está en ppi_limited → Regla 2
  → Si manda 50 pkt/s: bajo el límite → ACCEPT → llega a nginx (degradado)
  → Si manda 200 pkt/s: sobre el límite → 100 pkt/s pasan, 100 pkt/s → DROP
```

**Nota importante:** Suricata captura tráfico en la interfaz de red del sensor
(ens35), **antes** del firewall del servidor. Esto significa que aunque Kali esté
bloqueada, Suricata sigue registrando sus flows en eve.json y el motor los sigue
procesando (solo hace `log.debug("ya bloqueado")` sin re-enforcement).

---

## 6. dashboard.py — terminal ANSI

Script de 343 líneas que muestra el estado del sistema en la terminal con caracteres
ANSI en caja, refrescándose cada 3 segundos.

### 6.1 Arquitectura

```
Arranque:
  estado = Estado()                        ← instancia de acumulador
  leer_log_completo(log_path, estado)      ← carga historial completo del log
  Thread(seguir_log, daemon=True).start()  ← tail continuo en hilo separado

Bucle principal (hilo main):
  while True:
    print("\033[2J\033[H")                 ← limpia pantalla (ANSI clear)
    print(render(estado))                   ← dibuja la caja completa
    sleep(3)                                ← pausa configurable (--interval N)
```

### 6.2 Parseo del log (regex)

El dashboard parsea tres tipos de líneas del log del motor:

```python
# Tipo 1: eventos (ANOMALÍA, SOSPECHOSO, BRUTE-FORCE, HTTP-ABUSE)
RE_EVENTO = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"          # timestamp
    r".*?\| (ANOMALÍA|SOSPECHOSO|BRUTE-FORCE|HTTP-ABUSE)"
    r".*?src=([\d.]+)"                                   # src_ip
    r".*?dst=([\d.]+):(\d+)"                             # dst_ip:puerto
    r".*?proto=(\w+)"
    r".*?score=([-\d.]+)"
    r"(?:.*?grado=(\w+))?"                               # opcional
    r"(?:.*?tipo=(\w+))?"                                # opcional
    r".*?\| (BLOCK|LIMIT)"                               # accion final
)

# Tipo 2: estadísticas del motor (cada 500 flows)
RE_STATS = re.compile(
    r"flows=(\d+).*anomalías=(\d+).*bf=(\d+).*http_abuse=(\d+)"
    r".*bloqueados=(\d+).*limitados=(\d+).*latencia_media=([\d.]+)"
)

# Tipo 3: arranque del motor
RE_INICIO = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Motor de decisión PPI — iniciando"
)
```

### 6.3 Lo que muestra el dashboard

```
╔════════════════════════════════════════════════════════════════════════════╗
║  PPI-SURIKATA  Sistema de Detección de Anomalías en Red                   ║
║  2026-06-16 19:41:23   UPeU 2026   Motor activo desde: 17:38:01           ║
╠════════════════════════════════════════════════════════════════════════════╣
║  ● Suricata  ● Motor  ● Telegram  │  Uptime: 2h 03m 22s  │  F/min: 142  ║
╠════════════════════════════════════════════════════════════════════════════╣
║  BLOCK:    12 (80.0%)   LIMIT:    3 (20.0%)   Total: 15   Lat: 34.5ms   ║
║  BruteForce SSH: 2   HTTP Abuse: 1   flows procesados: 71,500            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  ÚLTIMAS DECISIONES                                                        ║
║  Hora      Origen           Puerto  Score     Grado     Tipo         Dec  ║
║  ──────────────────────────────────────────────────────────────────────   ║
║  19:41:02  ● 192.168.0.100  :22     -0.5200   BAJA      BRUTE_FORCE  BLOCK║
║  19:40:15  ● 192.168.0.100  :80     -0.4937   BAJA      SYN_FLOOD    LIMIT║
║  ...                                                                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║  MÉTRICAS DEL MODELO          IPSET ACTIVO                                 ║
║  Precision:  99.54%  ████████  BLOQUEADAS: 1                               ║
║  Recall:     99.40%  ████████    192.168.0.100                             ║
║  AUC-ROC:    0.8998  ███████   LIMITADAS: 0                                ║
║  ...                                                                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║  TIPOS DE ATAQUE (sesión)                                                  ║
║  SYN_FLOOD     ████████████   75%  (9)                                     ║
║  BRUTE_FORCE   ████           25%  (3)                                     ║
╠────────────────────────────────────────────────────────────────────────────╣
║  τ1=-0.4459 (PERMIT/LIMIT)  τ2=-0.6027 (LIMIT/BLOCK)  │  Ctrl+C para salir║
╚════════════════════════════════════════════════════════════════════════════╝
```

**Ipset en vivo:** el dashboard llama `sudo ipset list ppi_blocked` y
`sudo ipset list ppi_limited` en cada render (cada 3s) para mostrar las IPs
bloqueadas actuales directamente desde el kernel del sensor.

### 6.4 Uso

```bash
# En sensor — hilo separado del motor
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py

# Con intervalo personalizado
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py --interval 5

# Con log alternativo
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py \
  --log /ruta/alternativa/motor.log
```

---

## 7. dashboard_web.py — Flask + SSE

Script de 1,477 líneas que expone un dashboard web en tiempo real con interfaz
HTML/CSS/JS completa, actualización vía Server-Sent Events y control manual de IPs.

### 7.1 Arquitectura

```
PROCESO dashboard_web.py (puerto :8080)
│
├── Thread "log-reader" (daemon):
│     Carga historial del log al arrancar (sin push SSE)
│     Tail continuo del log:
│       → parsear cada línea nueva
│       → actualizar state{} (dict compartido con Lock)
│       → push_sse(ev) → poner evento en cada cola de cliente SSE
│
├── Flask main thread:
│     GET /              → HTML completo (render_template_string)
│     GET /api/stats     → JSON con métricas actuales
│     GET /api/stream    → SSE: genera eventos para un cliente conectado
│     GET /api/events    → últimos N eventos (JSON)
│     GET /api/alerts    → últimas 50 alertas BLOCK/LIMIT (JSON)
│     GET /api/timeline  → datos para gráfica temporal (últimos 60 minutos)
│     GET /api/tipos     → distribución por tipo de ataque (JSON)
│     POST /api/block    → bloquear IP manualmente {"ip":"x.x.x.x"}
│     POST /api/unblock  → desbloquear IP {"ip":"x.x.x.x"}
│     POST /api/clear    → limpiar contadores de sesión
│
└── Por cada cliente SSE conectado:
      generate() generator: espera en sse_clients[i].get()
                             yield "data: {json}\n\n"
```

### 7.2 SSE — cómo funciona /api/stream

```python
sse_clients = []  # lista de queues, una por cliente conectado

def push_sse(ev: dict):
    # Envia un evento a todos los clientes SSE conectados.
    for q in list(sse_clients):
        try:
            q.put_nowait(ev)   # no bloquea
        except Exception:
            pass

@app.route("/api/stream")
def api_stream():
    q = Queue(maxsize=200)
    sse_clients.append(q)
    def generate():
        try:
            while True:
                ev = q.get(timeout=30)    # espera hasta 30s o nuevo evento
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception:
            pass
        finally:
            sse_clients.remove(q)
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})
```

Cuando `log_reader` detecta un nuevo BLOCK/LIMIT en el log, llama `push_sse(ev)`,
que pone el evento en la queue de cada cliente conectado. El `generate()` de cada
cliente lo obtiene y hace `yield` — el navegador lo recibe instantáneamente sin
necesidad de polling.

### 7.3 Endpoints y respuestas

| Endpoint | Método | Respuesta real |
|---|---|---|
| `/` | GET | HTML completo con sidebar, tabla de alertas, gráfica timeline |
| `/api/stats` | GET | `{"block":12,"limit":3,"permit":71485,"flows_total":71500,"latencia_media":34.5,"ipset_blocked":["192.168.0.100"],"ipset_limited":[],"block_counter":12,"sse_clients":1,...}` |
| `/api/stream` | GET | SSE: `data: {"accion":"BLOCK","src":"192.168.0.100","port":"80","score":"-0.7333","grado":"ALTA","tipo":"ANOMALIA"}\n\n` |
| `/api/alerts` | GET | `[{"ts":"19:41:02","src":"192.168.0.100","accion":"BLOCK",...}, ...]` (últimas 50) |
| `/api/timeline` | GET | `{"labels":["19:00","19:01"...],"block":[0,0,2...],"limit":[0,1,0...]}` |
| `/api/tipos` | GET | `[["SYN_FLOOD",9],["BRUTE_FORCE",3]]` (top 5) |
| `/api/block` | POST | `{"ok":true}` — añade IP a ppi_blocked via `ssh_run("sudo ipset add...")` |
| `/api/unblock` | POST | `{"ok":true}` — elimina IP de ambos ipsets |
| `/api/clear` | POST | Limpia contadores de sesión en `state{}` |

### 7.4 Uso

```bash
# En sensor (background)
cd /home/m4rk/ppi-surikata-producto
nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py \
  > /tmp/dashweb.log 2>&1 &

# Verificar que está corriendo
ss -tlnp | grep 8080   # → *:8080

# Acceder desde Desktop en navegador
# http://192.168.0.110:8080

# Controlar IPs desde el dashboard web (POST)
curl -s -X POST http://192.168.0.110:8080/api/block \
  -H "Content-Type: application/json" -d '{"ip":"192.168.0.100"}'
curl -s -X POST http://192.168.0.110:8080/api/unblock \
  -H "Content-Type: application/json" -d '{"ip":"192.168.0.100"}'
```

---

## 8. Telegram Relay

El sensor (192.168.0.110) no tiene salida a internet. El relay en Desktop actúa
como puente HTTP entre la LAN del laboratorio y api.telegram.org.

### 8.1 Flujo de una alerta

```
motor_decision.py (sensor .110)
  │  BLOCK/LIMIT detectado
  │  telegram_alerta(msg)
  │    └── _tg_queue.put_nowait(msg)  [Thread tg-sender, daemon]
  │         └── POST http://192.168.0.20:8889/telegram
  │               Content-Type: application/json
  │               {"text": "🚨 PPI ALERTA — SYN_FLOOD\nAccion: BLOCK\nIP: 192.168.0.100\n..."}
  ▼
telegram_relay.py (Desktop .20:8889)
  │  Flask app: @app.route("/telegram", methods=["POST"])
  │  Recibe {"text": "..."}
  │  requests.post(
  │    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
  │    json={"chat_id": CHAT_ID, "text": body["text"]}
  │  )
  ▼
api.telegram.org → Bot → Operador recibe notificación en < 5s
```

### 8.2 Iniciar y verificar

```bash
# En Desktop (192.168.0.20) — ANTES de iniciar el motor
python3 /home/m4rk/Descargas/telegram_relay.py &

# Verificar
ss -tlnp | grep 8889   # → 0.0.0.0:8889

# Test de envío
curl -s -X POST http://localhost:8889/telegram \
     -H "Content-Type: application/json" \
     -d '{"text": "✅ Relay activo — PPI OK"}' && echo OK

# Desde sensor (para verificar conectividad LAN)
curl -s -X POST http://192.168.0.20:8889/telegram \
     -H "Content-Type: application/json" \
     -d '{"text": "Test desde sensor"}' && echo OK
```

### 8.3 Resiliencia

Si el relay no está activo:
- El motor registra `Telegram ERROR: Connection refused` en el log
- El enforcement (ipset/iptables) **continúa operando** sin interrupción
- `put_nowait()` descarta el mensaje si la queue está llena (>100 mensajes)
- La disponibilidad del sistema NO depende del relay

---

## 9. Verificación del estado del sistema

```bash
# ── DESDE SENSOR (.110) ─────────────────────────────────────────────────
# Motor activo
systemctl is-active ppi-motor.service

# τ cargados correctamente
grep "τ1=" results/motor_decision.log | head -1

# Últimos eventos
tail -20 results/motor_decision.log

# Dashboard terminal (interactivo)
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py

# ── DESDE SERVIDOR (.120) ────────────────────────────────────────────────
# IPs actualmente bloqueadas
sudo ipset list ppi_blocked

# IPs actualmente limitadas
sudo ipset list ppi_limited

# Reglas iptables activas
sudo iptables -L INPUT -n --line-numbers

# Verificar que iptables recibe tráfico de Kali bloqueada
sudo iptables -L INPUT -n -v | grep ppi_blocked  # columna pkts aumenta con cada intento

# ── DESDE DESKTOP (.20) ──────────────────────────────────────────────────
# Dashboard web
# http://192.168.0.110:8080

# Relay Telegram
ss -tlnp | grep 8889
```

---

## 10. Pruebas de integración (T3–T5)

| Prueba | Procedimiento | Resultado verificado |
|---|---|---|
| T3.1 enforce.sh BLOCK | `bash enforce.sh 192.168.0.100 BLOCK 60` | IP en ppi_blocked (verificado en servidor) |
| T3.2 enforce.sh LIMIT | `bash enforce.sh 192.168.0.100 LIMIT 60` | IP en ppi_limited con hashlimit activo |
| T3.3 enforce.sh UNBLOCK | `bash enforce.sh 192.168.0.100 UNBLOCK` | IP removida de ambos sets |
| T3.4 Auto-expiry | Añadir con timeout=5s, esperar 6s | IP desaparece del set automáticamente |
| T4.1 Dashboard web HTTP | GET http://192.168.0.110:8080 | HTTP 200, 17ms tiempo de respuesta |
| T4.2 SSE stream | GET /api/stream + trigger BLOCK | Evento recibido en < 1s en el navegador |
| T4.3 API block/unblock | POST /api/block y /api/unblock | `{"ok":true}` + cambio en ipset |
| T5.1 Relay Telegram :8889 | POST a relay + verificar bot | HTTP 200 + alerta recibida en bot |
| T5.2 Alerta BLOCK real | Motor detecta Port Scan | Alerta recibida en Telegram en < 3s |
| T5.3 Resiliencia relay | Motor activo + relay detenido | Motor continúa, log registra error Telegram |

---

## 11. Criterios de éxito (salida de F5)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| BLOCK activo | `sudo ipset list ppi_blocked` en .120 | Set creado, timeout=300 |
| LIMIT activo | `sudo ipset list ppi_limited` en .120 | Set creado, timeout=300 |
| iptables Regla 1 | `sudo iptables -L INPUT -n` en .120 | Línea 1: DROP match-set ppi_blocked src |
| iptables Regla 2 | idem | Línea 2: DROP match-set ppi_limited hashlimit above 100/sec |
| Dashboard terminal | `python3 scripts/dashboard.py` | Caja ANSI con métricas en tiempo real |
| Dashboard web | GET http://192.168.0.110:8080 | HTTP 200, SSE activo |
| API block | POST /api/block `{"ip":"192.168.0.100"}` | IP en ppi_blocked, `{"ok":true}` |
| Relay activo | `ss -tlnp \| grep 8889` en Desktop | Puerto 8889 escuchando |
| Alerta Telegram | Detectar ataque real | Mensaje en bot en < 5s |
| ITL=0% | curl normal desde Desktop durante bloqueo Kali | Sin interrupciones en Desktop |

**F5 se considera ACTIVO** cuando los ipsets existen con las reglas iptables correctas,
los dashboards muestran datos en tiempo real y una prueba de BLOCK manual envía alerta
al bot Telegram en menos de 5 segundos.

---

**Siguiente fase:** `F6_especificacion.md` — validación formal del sistema completo
con 40 corridas de tráfico, usando F4 (motor) y F5 (enforcement) operativos simultáneamente.
