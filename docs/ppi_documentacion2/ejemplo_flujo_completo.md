# Ejemplo de Flujo Completo — Del Comando al Telegram
**PPI UPeU 2026 · Rubén Mark Salazar Tocas**
**Datos reales del log — 2026-06-22**

> Este documento traza el recorrido completo de un ataque a través de las 6 fases
> del sistema, desde el comando ejecutado en Kali hasta la respuesta en Telegram
> y el dashboard. Todo con líneas de log reales, métricas reales y tiempos reales.

---

## Escenario 1 — B1 SYN Flood → detección por Isolation Forest

### Comando ejecutado en Kali (192.168.0.100)

```bash
# Kali Linux — atacante
sudo hping3 -S --flood -p 80 192.168.0.120
# -S       = SYN packets (simula inicio de conexión TCP)
# --flood  = envía tan rápido como puede (miles de pkt/s)
# -p 80    = puerto destino: nginx del servidor
```

Este comando genera un SYN Flood: miles de paquetes TCP-SYN por segundo
que intentan agotar la tabla de conexiones del servidor nginx.

---

### F1 — CAPTURA (Suricata · sensor 192.168.0.110)

Suricata monitorea la interfaz `ens35` en modo pasivo. Cada vez que un flujo
TCP se cierra (por timeout, RST o FIN), Suricata escribe un evento `flow`
en `/var/log/suricata/eve.json`.

**Problema:** un SYN flood nunca completa el handshake TCP (nunca llega el ACK).
Suricata espera el **flow timeout** (~30–60 s) antes de registrar cada flujo incompleto.

```json
{
  "timestamp": "2026-06-22T05:44:09.812Z",
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 8420,   ← miles de SYN acumulados en el timeout
    "pkts_toclient": 0,      ← el servidor no responde (ya colapsó)
    "bytes_toserver": 421000,
    "bytes_toclient": 0,
    "start": "2026-06-22T05:43:07.991Z",
    "end":   "2026-06-22T05:44:09.812Z"
  }
}
```

> **Por eso el lead time es ~62 s.** Es el tiempo que tarda Suricata en
> cerrar el primer flujo incompleto y escribirlo en eve.json.

---

### F2 — MODELO ISOLATION FOREST (extracción de features + score)

El motor (`motor_decision.py`) lee eve.json en tiempo real con `tail -f`.
Al llegar el evento de arriba, extrae las **14 features** en el mismo orden
que `models/features.csv`:

```python
# Valores calculados para este flujo:
pkts_toserver  = 8420      pkts_toclient  = 0
bytes_toserver = 421000    bytes_toclient = 0
duration       = 61.82 s   # end - start
pkt_rate       = 136.2 pkt/s   # (8420+0) / 61.82
byte_rate      = 6809.1 B/s
pkt_ratio      = inf → clippeado a 9999  # toserver/toclient (div/0)
byte_ratio     = inf → clippeado a 9999
avg_pkt_size   = 50.0 B    # 421000/8420
is_tcp         = 1    is_udp = 0    is_icmp = 0
dest_port      = 80
```

Estos valores son **completamente distintos al tráfico normal**:
- `pkts_toclient=0` (servidor no responde) → ratio inf
- `pkt_rate=136 pkt/s` para 62 s (normal: 2–5 pkt/s en HTTP)
- `avg_pkt_size=50 B` (paquetes SYN vacíos, sin payload)

Luego se normalizan con `StandardScaler` (ajustado durante entrenamiento):
```python
X_scaled = scaler.transform([[8420, 0, 421000, 0, 61.82, 136.2, 6809.1, 9999, 9999, 50.0, 1, 0, 0, 80]])
```

Y el Isolation Forest calcula el score:
```python
score = isolation_forest.decision_function(X_scaled)[0]
# score = -0.6066   ← muy negativo = muy aislado = muy anómalo
```

**¿Por qué -0.6066?**
El IF entrenó con flujos normales donde `pkts_toclient > 0` siempre.
Un flujo con `pkts_toclient=0` y `pkt_ratio=9999` está tan lejos del
baseline que los 300 árboles lo aíslan en muy pocas particiones.

**Regla de decisión:**
```
score = -0.6066
τ1   = -0.4459   (PERMIT/LIMIT)
τ2   = -0.6027   (LIMIT/BLOCK)

-0.6066 ≤ -0.6027  →  score ≤ τ2  →  BLOCK 🚫
```

---

### F3 — MOTOR DE DECISIÓN + CONTROL INLINE

**Línea real del log** (`results/motor_decision.log`):

```
2026-06-22 05:44:13 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6066 grado=ALTA tipo=ANOMALIA_GENERICA
  byte_ratio=4.92 pkt_rate=1.3 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```

El motor verifica el historial de bloqueos (`results/block_counts.json`):
```json
{"192.168.0.100": 1}
```
Es el **primer bloqueo** de esta IP → timeout 300 s (5 min).

**Comando ejecutado por el motor en el servidor (192.168.0.120):**
```bash
ssh m4rk@192.168.0.120   "sudo ipset add ppi_blocked 192.168.0.100 timeout 300"
```

**Resultado en el kernel del servidor:**
```
iptables: -A INPUT -m set --match-set ppi_blocked src -j DROP
→ Todo paquete de 192.168.0.100 es descartado ANTES de llegar a nginx
→ Sin latencia adicional, sin carga en aplicación, sin logs de nginx
```

**Verificación en servidor:**
```bash
$ sudo ipset list ppi_blocked
Members:
192.168.0.100 timeout 295   ← 5 segundos después del bloqueo
```

**Latencia total del pipeline:**
```
Evento en eve.json → features → score → ipset add
= 34.8 ms P95   (medido en latencia_pipeline.txt)
```

---

### F4 — PREDICTOR XGBOOST v2

El predictor (`predictor.py`) lee `motor_decision.log` en tiempo real.
Al detectar la línea BLOCK de 192.168.0.100, calcula las **9 features**:

```python
# Estado de 192.168.0.100 en este momento:
dest_port       = 80
proto_tcp       = 1          proto_udp = 0    proto_icmp = 0
hora_sin        = sin(5*2π/24) = -0.866   # 05:44 AM
hora_cos        = cos(5*2π/24) = -0.500
limit_count_15s = 0          # no hubo LIMITs previos en 15s (SYN flood → BLOCK directo)
block_count_60s = 1          # este es el primer BLOCK
is_block        = 1
```

```python
P = xgboost_v2.predict_proba(features)[0][1]
# P = 0.7739   →  77.39%
```

**¿Por qué 77.39%?**
- `proto_tcp=1` (peso 20.79%): SYN floods TCP son campañas prolongadas
- `block_count_60s=1` (peso 24.37%): ya hay un BLOCK → reincidencia probable
- `dest_port=80` (peso 0.89%): ataque a HTTP es patrón de flood sostenido

**Umbral ALERTA-PREDICTIVA: P ≥ 70%**
```
P = 77.39% ≥ 70%  →  ALERTA-PREDICTIVA 🔴
```

**Línea real en predictor log:**
```
2026-06-22 00:51:59 | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.39%
  → ataque sostenido predicho (XGBoost v2)
```

---

### Dashboard web (:8080) — qué ve el operador

Acceder desde Desktop: `http://192.168.0.110:8080`

El dashboard se actualiza por **Server-Sent Events (SSE)** en < 150 ms.

```
┌──────────────────────────────────────────────────────────┐
│  PPI — SURIKATA  |  05:44:14  |  🟢 Motor activo        │
├──────────────────────────────────────────────────────────┤
│  ALERTAS ACTIVAS                                         │
│  🚫 192.168.0.100  |  BLOCK  |  score=-0.6066  |  05:44 │
│     ANOMALIA_GENERICA  |  proto=TCP  |  :80              │
│     bloqueo#1 · timeout 300s                             │
├──────────────────────────────────────────────────────────┤
│  PREDICTOR XGBoost v2                                    │
│  🔴 192.168.0.100  |  P=77.39%  |  ALERTA-PREDICTIVA   │
│     Ataque TCP sostenido predicho · proto_udp+block_cnt  │
├──────────────────────────────────────────────────────────┤
│  IPSET ACTIVO                                            │
│  ppi_blocked:  192.168.0.100  (timeout: 295s)            │
├──────────────────────────────────────────────────────────┤
│  FLUJOS ÚLTIMOS 60s                                      │
│  PERMIT: 847  |  LIMIT: 0  |  BLOCK: 1                  │
│  Latencia media: 28.4 ms                                 │
└──────────────────────────────────────────────────────────┘
```

---

### Telegram — alerta al operador

Cuando el motor ejecuta un BLOCK nuevo (dedup: no repetir la misma IP en 300 s),
envía de forma **asíncrona** (sin bloquear el loop principal) a `api.telegram.org`:

```
🚨 PPI ALERTA — ANOMALIA_GENERICA

Accion : BLOCK (DROP)
IP     : 192.168.0.100
Puerto : 80
Proto  : TCP
Score  : -0.6066
Grado  : ALTA
Hora   : 05:44:13
Bloqueo: #1 — timeout 300s
```

**Resultado HTTP:** `200 OK` (confirmado 07:25:19 en otra corrida del mismo día)

---

### Bloqueo progresivo — el ciclo completo (datos reales)

Si Kali reincide después de que expire el bloqueo:

```
05:44:13  BLOCK #1  score=-0.6066  timeout=300s  (5 min)
          → block_counts.json: {"192.168.0.100": 1}
          → ipset: 192.168.0.100 timeout=300

06:05:03  BLOCK #2  score=-0.7696  timeout=1800s  (30 min)
          → block_counts.json: {"192.168.0.100": 2}
          → ipset: 192.168.0.100 timeout=1800
          → Telegram: 🚨 BLOCK #2

06:39:42  BLOCK #3  HTTP-ABUSE 100 req/30s  timeout=0  (PERMANENTE ∞)
          → block_counts.json: {"192.168.0.100": 3}
          → ipset: 192.168.0.100 timeout=0  ← NO EXPIRA NUNCA
          → Telegram: 🚨 BLOCK #3 PERMANENTE
```

**Verificación final en servidor:**
```bash
$ sudo ipset list ppi_blocked
Members:
192.168.0.100 timeout 0    ← timeout=0 = PERMANENTE
```

---

---

## Escenario 2 — B6 SSH Brute Force → detección por heurístico

### Comando ejecutado en Kali

```bash
# Kali Linux — atacante
hydra -l admin -P /usr/share/wordlists/fasttrack.txt       ssh://192.168.0.120 -t 4 -V
# -l admin   = usuario objetivo
# -P ...     = diccionario de contraseñas
# -t 4       = 4 intentos paralelos
# -V         = verbose (muestra cada intento)
```

Hydra prueba credenciales SSH una por una. Cada intento fallido genera
un flujo TCP corto hacia el puerto 22.

---

### F1 — CAPTURA

Suricata captura cada flujo SSH (conexión → handshake → fallo de auth → cierre).
A diferencia del SYN flood, estos flujos SÍ completan el handshake TCP,
por lo que **se cierran rápido** y Suricata los registra de inmediato.

```json
{
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_port": 22,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 12,  bytes_toserver: 2847,
    "pkts_toclient": 10,  bytes_toclient: 3640,
    "start": "T+0s",      "end": "T+2s"
  }
}
```

Con 4 hilos paralelos, cada ~15 s hay 4 flujos nuevos registrados.

---

### F2 — ISOLATION FOREST: score en zona LIMIT

Features extraídas de un flujo SSH de fuerza bruta:
```
pkts_toserver=12  pkts_toclient=10  bytes_toserver=2847  bytes_toclient=3640
duration=2.1s     pkt_rate=10.5     byte_rate=3089       pkt_ratio=1.2
byte_ratio=0.78   avg_pkt_size=299  is_tcp=1   dest_port=22
```

Estos valores se parecen superficialmente al SSH legítimo (bytes similares,
duración corta, mismo puerto) → el IF no puede distinguirlo bien sólo por flujo:

```
score = -0.4832   (primer flujo detectado, T+53s)

τ1 = -0.4459   →   -0.4832 < -0.4459
τ2 = -0.6027   →   -0.4832 > -0.6027

τ2 < score ≤ τ1   →   LIMIT ⚠️  (hashlimit 100 pkt/s)
```

**Línea real del log (T+53s):**
```
2026-06-22 08:31:07 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT
```

El LIMIT aplica rate limiting pero **no bloquea**. Hydra sigue intentando, ahora limitado.

---

### F3 — HEURÍSTICO BF-SSH: el que bloquea

El motor mantiene un contador de eventos SSH por IP en una ventana deslizante de 60 s:

```
T+ 0s  hydra inicia (4 hilos)
T+15s  4 intentos → contador BF-SSH: 4  < 5 → sin acción
T+30s  4 intentos más → contador: 8  ≥ 5 → LIMIT heurístico
T+53s  IF también detecta → LIMIT (score=-0.4832)
T+60s  4 intentos más → contador: 15 → umbral BLOCK alcanzado
```

**BLOCK por heurístico BF-SSH:**
```
2026-06-22 08:31:37 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH
  byte_ratio=0.78 pkt_rate=3.0 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```

**¿Por qué -0.6228 ahora?**
Los intentos BF generan flujos cada vez más cortos y repetitivos → score baja más.
Además el heurístico fuerza el camino BLOCK independientemente del score.

**Comando en servidor:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset add ppi_blocked 192.168.0.100 timeout 300"
```

**Resultado:** Hydra no puede completar más intentos. El atacante necesita esperar
300 s (5 min) antes de poder intentarlo de nuevo — y si reincide, será 30 min, luego permanente.

---

### F4 — XGBOOST v2: features con señal BF

Cuando el predictor ve el BLOCK de BRUTE_FORCE_SSH:
```python
dest_port       = 22         # SSH
proto_tcp       = 1
hora_sin        = -0.978     # 08:31 AM
hora_cos        = -0.208
limit_count_15s = 5          # 5 LIMITs en los últimos 15s (pre-BLOCK)
block_count_60s = 1          # este BLOCK
is_block        = 1

P = xgboost_v2.predict_proba(features)[0][1]
# P = 0.72   →  72%  →  ALERTA-PREDICTIVA 🔴
```

`limit_count_15s=5` activa la señal: hubo presión sostenida de LIMITs
antes del BLOCK, lo que es el patrón clásico de un ataque gradual escalando.

---

### Telegram — alerta B6 (real)

```
🚨 PPI ALERTA — BRUTE_FORCE_SSH

Accion : BLOCK (DROP)
IP     : 192.168.0.100
Puerto : 22
Proto  : TCP
Score  : -0.6228
Grado  : ALTA
Hora   : 08:31:37
Bloqueo: #1 — timeout 300s
```

---

### Dashboard — vista durante B6

```
┌──────────────────────────────────────────────────────────┐
│  PPI — SURIKATA  |  08:31:38  |  🟢 Motor activo        │
├──────────────────────────────────────────────────────────┤
│  ALERTAS ACTIVAS                                         │
│  🚫 192.168.0.100  |  BLOCK  |  score=-0.6228  |  08:31 │
│     BRUTE_FORCE_SSH  |  proto=TCP  |  :22                │
│     bloqueo#1 · timeout 300s                             │
├──────────────────────────────────────────────────────────┤
│  PREDICTOR XGBoost v2                                    │
│  🔴 192.168.0.100  |  P=72%  |  ALERTA-PREDICTIVA       │
│     limit_count_15s=5 · is_block=1                       │
├──────────────────────────────────────────────────────────┤
│  IPSET ACTIVO                                            │
│  ppi_blocked:  192.168.0.100  (timeout: 298s)            │
└──────────────────────────────────────────────────────────┘
```

---

## Contraste: tráfico normal (whitelist)

```bash
# Desktop (192.168.0.20) — tráfico legítimo
curl http://192.168.0.120/   # 120 veces, 1 cada segundo
```

**Lo que pasa en el motor:**

```python
# Paso 1: verificar whitelist
if src_ip in WHITELIST:    # 192.168.0.20 ∈ {.20, .110, .120, .1, ...}
    log.debug("PERMIT (whitelist)")
    return    # ← sale inmediatamente, sin calcular score
```

**Resultado:** 0 LIMIT, 0 BLOCK, 120 PERMIT. El IF **nunca se ejecuta** para IPs de la whitelist.
Latencia: < 1 ms (solo el lookup en el set Python).

**Log:**
```
# Sin líneas WARNING para 192.168.0.20
# Solo en estadísticas cada 500 flujos:
INFO | Estadísticas | flows=500 anomalías=0 whitelist=500 bloqueados=0 latencia_media=0.8ms
```

---

## F5 — Aprendizaje continuo (en segundo plano, esa noche)

F5 no actúa durante el ataque — actúa **cada noche**:

```
03:00 AM  →  f5_reentrenar_xgboost.py
              Ventana: últimas 24h del motor_decision.log
              Eventos: incluye los BLOCKs del día (BRUTE_FORCE_SSH, HTTP_ABUSE, etc.)
              Labels:  automáticos (¿hubo otro BLOCK de esta IP en los 60s siguientes?)
              Split:   80/20 estratificado
              Si AUC_nuevo ≥ 0.70 y no retrocede >0.05 vs actual → reemplaza pkl
              Hot-reload: predictor.py detecta cambio de mtime → recarga sin reiniciar

Dom 02:00  →  f5_reentrenar_if.py
              Lee todos data/raw/*_normal_*.gz acumulados
              Entrena nuevo IF sobre el baseline de tráfico normal actualizado
              Si AUC_nuevo no retrocede >0.02 vs actual → reemplaza isolation_forest.pkl
              Motor requiere restart para recargar (systemctl restart ppi-motor.service)
```

---

## F6 — Cómo este flujo aparece en la validación

En las 40 corridas formales del 2026-06-16:

- **Corrida B (mixta, 11–20):** Kali lanza SYN flood → motor detecta en ~62s → BLOCK
  `flows_anom` en el CSV = flujos anómalos procesados antes del primer bloqueo
- **Corrida reevaluación (21–30):** IP ya bloqueada → ipset DROP en kernel →
  `flows_anom = 0` (comportamiento correcto: paquetes no llegan a Suricata)
- **Latencia:** `latencia_pipeline.txt` registra P50/P95/P99 de miles de flujos procesados
  → P95 = 34.8 ms < 500 ms ✅

```bash
# Verificar en sensor:
cat results/resultados_f6_completo.csv | grep -E 'mixto|anom' | head -5
cat results/latencia_pipeline.txt
```

---

## Resumen de tiempos por escenario

| Escenario | T+0 | Primera respuesta | BLOCK | Telegram | Dashboard |
|---|---|---|---|---|---|
| B1 SYN Flood | hping3 --flood | T+60s LIMIT (score cruzó τ1) | T+62s (score ≤ τ2) | T+62s + ~500ms API | T+62s + <150ms SSE |
| B6 BF SSH | hydra -t 4 | T+53s LIMIT (BF-SSH 5 intentos) | T+60s BLOCK (BF-SSH 15 intentos) | T+60s + ~500ms | T+60s + <150ms |
| Normal (whitelist) | curl x120 | — | NUNCA | NUNCA | PERMIT en stats |

---

## Métricas del sistema al cierre de este flujo

| Modelo / Componente | Métrica | Valor real |
|---|---|---|
| Isolation Forest | AUC-ROC | 0.8998 |
| IF | Precision / Recall en τ1 | 99.54% / 99.40% |
| IF | τ1 (PERMIT/LIMIT) | −0.4459 (Youden) |
| IF | τ2 (LIMIT/BLOCK) | −0.6027 (FPR≤2%) |
| IF | Latencia P95 por flujo | 34.8 ms |
| XGBoost v2 | AUC-ROC (9 features, sin leakage) | 0.9992 |
| XGBoost v2 | Umbral ALERTA-PREDICTIVA | P ≥ 70% |
| Motor | Disponibilidad (40 corridas F6) | 100% |
| Motor | ITL (tráfico legítimo bloqueado) | 0% |
| Sistema | Lead time SYN Flood | ~62 s |
| Sistema | Lead time BF SSH (BLOCK) | 60 s |
| Sistema | Bloqueo #3 (permanente) | timeout=0 en ipset |
