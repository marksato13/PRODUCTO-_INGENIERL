# F4 — Secuencia exacta de ejecución: cómo funciona el motor de decisión

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Script principal:** `scripts/motor_decision.py` (547 líneas)

---

## Punto de partida: lo que llega de F3

Al arrancar F4 deben existir estos artefactos producidos por F3 y `auc_roc_umbrales.py`:

```
/home/m4rk/ppi-surikata-producto/
├── models/
│   ├── isolation_forest.pkl   ← modelo IF entrenado (n=300, corridas 01 normales)
│   ├── scaler.pkl             ← StandardScaler con μ/σ de 684 flows normales
│   └── features.csv           ← lista de 14 features en orden exacto
├── results/
│   └── umbrales_finales.txt   ← τ1=−0.4973, τ2=−0.6873, AUC=0.9440
```

Y en el sensor, corriendo continuamente:
```
/var/log/suricata/eve.json     ← Suricata escribe aquí en tiempo real (append)
```

---

## Cómo se inicia el motor

```bash
# Vía systemd (producción)
sudo systemctl start ppi-motor.service

# Manual (debug/desarrollo)
python3 /home/m4rk/ppi-surikata-producto/scripts/motor_decision.py
```

El servicio systemd apunta a `motor_decision.py` y lo reinicia automáticamente si falla.

---

## Secuencia de arranque — función `main()`

### Arranque [A] — Carga del modelo

```python
clf, scaler = load_model()
```

**Lo que hace `load_model()`:**
```python
clf    = joblib.load("models/isolation_forest.pkl")   # carga el IF
scaler = joblib.load("models/scaler.pkl")             # carga el scaler
# Imprime en log:
# "Modelo cargado | umbral_base=−0.5481 | τ1=−0.4973 | τ2=−0.6873"
```

Los umbrales τ1 y τ2 **no se leen del archivo** — están hardcodeados en las constantes del script (derivados manualmente de `umbrales_finales.txt` durante la recalibración de F3):

```python
TAU1 = -0.4973   # PERMIT / LIMIT  (Youden, TPR=91%, FPR=9.5%)
TAU2 = -0.6873   # LIMIT  / BLOCK  (FPR≤2%, TPR=40.6%)
```

**Salida en log:**
```
Motor de decisión PPI — iniciando
Modelo cargado | umbral_base=−0.5481 | τ1=−0.4973 | τ2=−0.6873
```

---

### Arranque [B] — Inicialización del servidor (F5)

```python
inicializar_servidor()
```

Esta función conecta por SSH al servidor (`192.168.0.120`) y crea las estructuras de control si no existen:

```bash
# ipset BLOCK (DROP total)
sudo ipset create ppi_blocked hash:ip timeout 300
sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP

# ipset LIMIT (hashlimit 100 pkt/s, burst 150)
sudo ipset create ppi_limited hash:ip timeout 300
sudo iptables -I INPUT 2 -m set --match-set ppi_limited src \
  -m hashlimit --hashlimit-above 100/sec --hashlimit-burst 150 \
  --hashlimit-mode srcip --hashlimit-name ppi_limit -j DROP
```

Si las reglas ya existen (reinicio del motor), los comandos con `-exist` y `|| true` no fallan.

**Salida en log:**
```
Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=−0.4973 τ2=−0.6873
```

---

### Arranque [C] — Inicialización de estructuras en memoria

```python
bloqueados    = set()             # IPs ya en ppi_blocked (evita SSH redundante)
limitados     = set()             # IPs ya en ppi_limited
ssh_intentos  = defaultdict(list) # ip → [timestamps] para detector SSH
http_requests = defaultdict(list) # ip → [timestamps] para detector HTTP
total_flows   = 0
total_anom    = 0
latencias_ms  = []
```

Estas estructuras viven en RAM. Se reinician si el motor se reinicia (pero ipset en el servidor persiste independientemente).

---

## Bucle principal — por cada flow de `eve.json`

```python
for line in seguir_eve(EVE_PATH):
    ...
```

**`seguir_eve()`** funciona como `tail -f`: abre `eve.json`, se posiciona al final (`seek(0, 2)`) y espera nuevas líneas. Si detecta que el archivo fue truncado (rotación al exportar corrida), lo reabre automáticamente.

Cada iteración del bucle procesa **una línea** = **un evento** de Suricata.

---

### Filtro [1] — Solo eventos tipo `flow`

```python
if e.get('event_type') != 'flow':
    continue
```

Suricata escribe muchos tipos de eventos en `eve.json` (dns, http, alert, stats, etc.). El motor solo procesa los de tipo `flow` — un resumen estadístico de cada conexión de red cerrada.

---

### Filtro [2] — Validar IP origen

```python
src_ip = e.get('src_ip', '')
if not src_ip or ':' in src_ip or src_ip in WHITELIST:
    continue
```

Descarta:
- Eventos sin `src_ip`
- IPv6 (contienen `:`)
- IPs en la whitelist (nunca se bloquean):

```python
WHITELIST = {
    "192.168.0.1",    # gateway
    "192.168.0.20",   # Desktop (Admin — aquí corre Claude Code)
    "192.168.0.110",  # Sensor (el propio sensor)
    "192.168.0.120",  # Servidor nginx/SSH
    "127.0.0.1",      # loopback
    "192.168.0.130",  # reservado
    "192.168.0.140",  # reservado
}
```

---

### Filtro [3] — IP bloqueable

```python
if not es_ip_bloqueable(src_ip):
    continue
```

`es_ip_bloqueable()` verifica que sea una IPv4 de rango privado válido (usa `ipaddress.ip_address()`). Filtra IPs malformadas o rangos especiales (multicast, link-local, etc.).

---

### Filtro [4] — Flow con paquetes al servidor

```python
if (e.get('flow', {}).get('pkts_toserver', 0) or 0) == 0:
    continue
```

Descarta flows donde no hubo paquetes hacia el servidor (ruido de gestión interna). Sin este filtro, `pkt_rate` y `byte_rate` dividirían entre 0.

---

### Pipeline IF [5] — Extracción de features y score

```python
t_proc_ini = time.time()
X     = scaler.transform(extract_features(e))
score = clf.score_samples(X)[0]
latencia_ms = (time.time() - t_proc_ini) * 1000
```

**Paso a paso:**

**5a. `extract_features(e)`** — arma el vector de 14 features desde el JSON:

```python
return np.array([[
    pkts_toserver, pkts_toclient,
    bytes_toserver, bytes_toclient,
    duration,
    (pkts_toserver + pkts_toclient) / duration,       # pkt_rate
    (bytes_toserver + bytes_toclient) / duration,      # byte_rate
    pkts_toserver / (pkts_toclient + 1),               # pkt_ratio
    bytes_toserver / (bytes_toclient + 1),             # byte_ratio
    (bytes_toserver + bytes_toclient) / (pkts + 1),   # avg_pkt_size
    int(proto == 'TCP'),
    int(proto == 'UDP'),
    int(proto in ('ICMP', 'IPV6-ICMP')),
    dest_port,
]], dtype=float)
```

Devuelve array shape `(1, 14)`.

**5b. `scaler.transform(X)`** — aplica el mismo StandardScaler de F3:
- Usa los μ y σ aprendidos de los 684 flows normales
- Transforma: `z = (x − μ) / σ`
- Un SYN flood con `pkt_rate=50,000/s` → `z ≈ +45` (muy alejado de la media normal de ~12/s)

**5c. `clf.score_samples(X)`** — el Isolation Forest devuelve el score continuo:
- Rango: `(−1, 0)` donde más negativo = más anómalo
- Los 300 árboles votan cuántas particiones necesitó para aislar el punto
- Devuelve `score` como float (ej: `−0.71` para un SYN flood)

**Latencia medida:** P95 = 34.8ms (requisito < 500ms: CUMPLE)

---

### Detectores heurísticos [6] — Override temporal

Los detectores se ejecutan **antes** de la decisión IF para capturar ataques que el score puede tardar en detectar (ventanas temporales):

**Detector HTTP Abuse** (`detectar_http_abuse()`):

```
Ventana: 30 segundos
≥ 50 requests/30s  → LIMIT
≥ 100 requests/30s → BLOCK directo (override: no espera al score IF)
```

Si dispara BLOCK/LIMIT, ejecuta la acción inmediatamente (SSH al servidor) y escribe en log + Telegram. Luego **continúa** al análisis IF (no hace `continue`).

**Detector Brute Force SSH** (`detectar_brute_force()`):

```
Puerto: 22
Ventana: 60 segundos
≥ 5 intentos/60s   → LIMIT
≥ 15 intentos/60s  → BLOCK directo
```

Mismo mecanismo: acción inmediata + log + Telegram + continúa al IF.

---

### Decisión IF [7] — Triple umbral τ1/τ2

```python
accion = decidir(score)
grado  = clasificar_grado(score)
tipo   = clasificar_tipo(e, score, accion, ssh_intentos, http_requests)
```

**`decidir(score)`:**
```python
if score > TAU1:      return 'PERMIT'   # > −0.4973
elif score > TAU2:    return 'LIMIT'    # entre −0.6873 y −0.4973
else:                 return 'BLOCK'    # ≤ −0.6873
```

**`clasificar_grado(score)`:**
```
score > −0.4973          → NORMAL
−0.6873 < score ≤ −0.4973 → BAJA
−0.82   < score ≤ −0.6873 → ALTA
score ≤ −0.82            → CRÍTICA
```

**`clasificar_tipo()`:** determina etiqueta descriptiva (SYN_FLOOD, PORT_SCAN, BRUTE_FORCE_SSH, HTTP_ABUSE, ANOMALIA_DESCONOCIDA, etc.) en base al protocolo, puerto y contadores de los detectores.

---

### Acción [8] — Ejecutar decisión en el servidor

**Si BLOCK:**
```python
if src_ip not in bloqueados:
    bloqueados.add(src_ip)          # marca en RAM (no repite SSH)
    limitar.discard(src_ip)         # si estaba limitado, se remueve
    bloquear_ip(src_ip)             # SSH → ipset add ppi_blocked <ip> timeout 300
    log.warning("ANOMALÍA | ...")
    telegram_alerta("🚨 PPI ALERTA ...")
```

**Si LIMIT:**
```python
if src_ip not in limitados and src_ip not in bloqueados:
    limitados.add(src_ip)
    limitar_ip(src_ip)              # SSH → ipset add ppi_limited <ip> timeout 300
    log.warning("SOSPECHOSO | ...")
    telegram_alerta("⚠️ PPI ALERTA ...")
```

**Si PERMIT:**
```python
log.debug("normal | src=... score=... | PERMIT")
# Sin acción en servidor
```

La función `bloquear_ip()` y `limitar_ip()` usan `_ssh()` para ejecutar el comando en el servidor por SSH:

```python
def _ssh(cmd):
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5',
         'm4rk@192.168.0.120', cmd],
        capture_output=True, text=True, timeout=8
    )
```

---

### Notificaciones [9] — Telegram

Las alertas se envían en un **hilo separado** (no bloquean el bucle):

```python
tg_queue = _queue.Queue()

def _tg_worker():       # corre en hilo daemon
    while True:
        msg = tg_queue.get()
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        urllib.request.urlopen(...)

threading.Thread(target=_tg_worker, daemon=True).start()

def telegram_alerta(mensaje):
    tg_queue.put(mensaje)   # no bloquea — encola y sigue
```

El hilo Telegram arranca junto con el motor. Si no hay internet, los mensajes quedan en cola y el motor sigue procesando flows.

---

### Estadísticas periódicas [10]

Cada 500 flows procesados:

```python
if total_flows % 500 == 0:
    lat_med = sum(latencias_ms) / len(latencias_ms)
    log.info(
        f"Estadísticas | flows={total_flows} anomalías={total_anom} "
        f"bf={total_bf} http_abuse={total_http_ab} "
        f"bloqueados={len(bloqueados)} limitados={len(limitados)} "
        f"latencia_media={lat_med:.2f}ms"
    )
```

Este log es el que lee `dashboard.py` y `dashboard_web.py` para mostrar estadísticas en tiempo real.

---

## Resumen del flujo completo por flow

```
Suricata escribe línea en eve.json
         │
         ▼
seguir_eve() → yield line
         │
         ▼
¿event_type == 'flow'?   NO → descarta
         │ SÍ
         ▼
¿src_ip válida y no en WHITELIST?   NO → descarta
         │ SÍ
         ▼
¿pkts_toserver > 0?   NO → descarta
         │ SÍ
         ▼
extract_features(e) → vector [1×14]
         │
scaler.transform()  → vector normalizado [1×14]
         │
clf.score_samples() → score ∈ (−1, 0)
         │
  ┌──────┴──────────────────┐
  │                         │
detectar_http_abuse()  detectar_brute_force()
  │                         │
  ▼ (si dispara)            ▼ (si dispara)
SSH → ipset (inmediato)   SSH → ipset (inmediato)
  │                         │
  └──────────┬──────────────┘
             │ (siempre continúa)
             ▼
         decidir(score)
         ┌───────────────────────┐
         │ score > −0.4973       │→ PERMIT  → log.debug
         │ score > −0.6873       │→ LIMIT   → SSH ipset ppi_limited + Telegram
         │ score ≤ −0.6873       │→ BLOCK   → SSH ipset ppi_blocked + Telegram
         └───────────────────────┘
             │
             ▼
      log motor_decision.log
      latencias_ms.append()
      cada 500 flows → log estadísticas
```

---

## Qué produce F4 para las fases siguientes

| Output | Ruta | Usado en |
|---|---|---|
| `motor_decision.log` | `results/` | F6 `f6_corridas.py` — métricas; `dashboard.py`/`dashboard_web.py` — live |
| `ppi_blocked` en ipset | Servidor 192.168.0.120 | F5 `enforce.sh` — control manual; iptables DROP |
| `ppi_limited` en ipset | Servidor 192.168.0.120 | F5 `enforce.sh` — control manual; iptables hashlimit |
| Alertas Telegram | Chat bot | Monitoreo en tiempo real |

---

## Pregunta frecuente de defensa

**¿Por qué el motor usa SSH para bloquear en vez de actuar directamente?**

El motor corre en el **sensor** (192.168.0.110, con Suricata). Las reglas de firewall deben estar en el **servidor** (192.168.0.120, con nginx y SSH). El motor no puede tocar iptables del servidor directamente — debe conectarse por SSH para ejecutar los comandos `ipset`. Esta es la arquitectura distribuida del sistema: sensor detecta, servidor aplica.

**¿Qué pasa si el SSH al servidor falla?**

`_ssh()` tiene timeout de 8 segundos. Si falla, la excepción se captura silenciosamente y el motor sigue procesando el siguiente flow. El bloqueo no se aplica pero el log registra el intento.

**¿Qué pasa si un flow llega de una IP ya bloqueada?**

Los sets `bloqueados` y `limitados` en RAM evitan que el motor envíe SSH repetidamente para la misma IP. Una IP ya en `bloqueados` solo genera `log.debug` sin acción adicional. El timeout de 300 segundos en ipset expira automáticamente.

**¿Por qué los detectores heurísticos se ejecutan antes que el score IF?**

El Isolation Forest analiza **un flow a la vez** en el momento que se cierra la conexión. Un brute force SSH de 15 intentos puede tener flows individuales con score cercano a PERMIT (cada intento SSH fallido tiene pocas bytes). La ventana temporal de 60 segundos del detector acumula los intentos y detecta el patrón antes de que el score por flow lo haga.
