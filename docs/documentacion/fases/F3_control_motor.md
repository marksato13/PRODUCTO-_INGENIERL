# F3 — Control en Tiempo Real (Motor + ipset + Dashboard)
**Estado: ✅ COMPLETA Y VALIDADA**  
**Resultado:** Latencia P95=34.768ms | Disponibilidad=100% | ITL=0% | Lead time B1≈62s | 29 flows/s

---

## Objetivo

Aplicar la decisión del IF sobre cada flujo nuevo en tiempo real de forma automática e inline: clasificar como PERMIT / LIMIT / BLOCK, ejecutar el control de red mediante ipset/iptables, visualizar el estado del sistema y notificar al operador ante eventos críticos.

**Por qué F3 es la fase más crítica del sistema:** sin F3, el IF es solo un clasificador pasivo. F3 lo convierte en un sistema de control activo. La diferencia frente a un IDS tradicional es exactamente esta: no solo detecta, sino que actúa en <35ms sobre el tráfico real.

---

## Entradas → Proceso → Salidas

```
ENTRADAS
  /var/log/suricata/eve.json              (tail en tiempo real)
  models/isolation_forest.pkl             (IF cargado al arrancar)
  models/scaler.pkl                       (StandardScaler μ/σ)
  models/features.csv                     (orden exacto de las 14 features)
  results/metricas_offline.txt            (τ1=−0.4459, τ2=−0.6027)
  config/whitelist.conf                   (IPs nunca bloqueadas)
  config/telegram.conf                    (TG_TOKEN, TG_CHAT_ID — fuera de git)
  results/block_counts.json               (historial bloqueos por IP — persistente)

PROCESO  [motor_decision.py — continuo como servicio systemd]
  tail eve.json → evento type=flow → extraer 14 features
  ¿src_ip en whitelist?   → PERMIT inmediato (sin IF, sin latencia)
  score = IF.decision_function(scaler.transform(features))
  score > τ1              → PERMIT (log INFO)
  τ2 < score ≤ τ1         → LIMIT  → SSH→192.168.0.120 ipset add ppi_limited
  score ≤ τ2              → BLOCK  → SSH→192.168.0.120 ipset add ppi_blocked
  score_medio_10flows < −0.35 → Telegram 👀 TENDENCIA
  Heurístico BF-SSH:    ≥5/60s → LIMIT | ≥15/60s → BLOCK
  Heurístico HTTP-Abuse: ≥50/30s → LIMIT | ≥100/30s → BLOCK
  BLOCK → progresivo: #1=300s, #2=1800s, #3+=permanente (timeout=0)
  BLOCK → Telegram 🚨 alerta (dedup 300s por IP)

SALIDAS
  results/motor_decision.log              (PERMIT/LIMIT/BLOCK por flujo — entrada de F4)
  results/block_counts.json               (conteo de bloqueos por IP, persistente)
  192.168.0.120 ipset ppi_blocked         (IPs con DROP en kernel del servidor)
  192.168.0.120 ipset ppi_limited         (IPs con hashlimit 100pkt/s burst 150)
  Telegram mensajes                        (alertas al operador)
  Dashboard web :8080                      (SSE — tiempo real en navegador)
```

---

## Terminología clave

| Término | Definición |
|---|---|
| **Motor de decisión** | Script `motor_decision.py` corriendo como servicio systemd en el sensor. Lee eve.json línea a línea en tiempo real, extrae features, aplica IF y decide la acción. Es el núcleo operativo de todo el sistema. |
| **tail en tiempo real** | El motor usa `f.seek(0,2)` + loop de lectura con `f.tell()`. Cada línea nueva de Suricata se procesa inmediatamente sin espera. |
| **ipset** | Estructura de datos del kernel Linux que almacena conjuntos de IPs. Más eficiente que reglas iptables individuales: busca una IP en O(1) (hash), actualizable en tiempo real sin reiniciar el firewall. |
| **ppi_blocked** | Conjunto ipset con DROP total, **en el servidor (192.168.0.120)**. El kernel del servidor descarta todos los paquetes de esa IP antes de que lleguen a nginx o SSH. |
| **ppi_limited** | Conjunto ipset con `hashlimit 100pkt/s burst 150`, **en el servidor**. Permite hasta 100 paquetes/segundo con ráfaga de 150 antes de descartar. Un SYN flood a 10,000 pkt/s queda reducido al 1%. |
| **hashlimit burst 150** | La ráfaga inicial de 150 paquetes permite que conexiones TCP legítimas completen su handshake antes de aplicar el límite. Sin burst, incluso conexiones válidas serían cortadas al inicio. |
| **PERMIT** | Flujo normal (score > τ1). Solo registro INFO. Sin acción en red. |
| **LIMIT** | Flujo sospechoso (τ2 < score ≤ τ1). IP añadida a `ppi_limited`. Tráfico reducido a 100 pkt/s. |
| **BLOCK** | Flujo anómalo (score ≤ τ2). IP añadida a `ppi_blocked`. Todo tráfico descartado en el kernel. |
| **Set `bloqueados` en memoria** | Python `set()` en el proceso del motor. Una vez que una IP entra en `bloqueados`, sus flujos posteriores van al `else` (rate-limited log cada 5s) sin llamar a SSH. Persiste mientras el proceso vive — reiniciar el motor limpia este set. |
| **Bloqueo progresivo** | Sistema de escalada: BLOCK#1=300s (5min), BLOCK#2=1800s (30min), BLOCK#3+=permanente (timeout=0). El contador persiste en `block_counts.json` entre reinicios. |
| **Whitelist** | Lista de IPs verificada ANTES del IF. Las IPs whitelisted nunca consumen tiempo de inferencia ni SSH al servidor. |
| **Heurístico** | Regla de conteo acumulado en ventana temporal, independiente del score IF. Detecta patrones que el IF podría pasar por alto si los flujos individuales son estadísticamente normales. |
| **TAU_AVISO=−0.35** | Pre-alerta de tendencia. Si los últimos 10 flujos de una IP promedian score < −0.35 (entre 0 y τ1=−0.4459), se envía aviso Telegram 👀 antes del primer BLOCK. |
| **ITL** | Interrupción de Tráfico Legítimo. ITL=0% = ningún flujo normal fue bloqueado en todas las corridas. |
| **Lead time** | Tiempo desde el inicio del ataque hasta el primer BLOCK efectivo. |
| **SSE (Server-Sent Events)** | Protocolo HTTP para push de datos del servidor al navegador sin polling. El dashboard web usa SSE: el cliente abre una conexión y recibe eventos push. |

---

## Arquitectura — por qué el motor está en el sensor y no en el servidor

```
SENSOR (192.168.0.110)                    SERVIDOR (192.168.0.120)
─────────────────────────────────         ─────────────────────────
Suricata → eve.json                       iptables INPUT chain
    │                                         │
    ▼  tail en tiempo real                    │ DROP  ← ppi_blocked
motor_decision.py                             │ LIMIT ← ppi_limited (hashlimit)
    │                                         │
    ├── Whitelist check (antes del IF)    ipset ppi_blocked
    ├── IF.decision_function()            ipset ppi_limited
    ├── TAU_AVISO tendencia                   ▲
    └── Heurísticos BF/HTTP                  │  SSH m4rk@192.168.0.120
              │                          "sudo ipset add ..."
         ┌────┴──────────────────────────────┘
         │
    PERMIT   → log INFO only
    TENDENCIA → Telegram 👀 (score_medio < −0.35 en 10 flows)
    LIMIT    → SSH → ipset ppi_limited + log WARNING
    BLOCK    → SSH → ipset ppi_blocked + Telegram 🚨 + log WARNING
         │
    Dashboard web :8080        predictor.py
    (Flask + SSE)              (lee motor_decision.log cada 10s)
```

**Por qué el motor en el sensor y no en el servidor:** si el motor corriera en el servidor y fallara (panic, OOM, error de Python), el servidor dejaría de aplicar bloqueos pero seguiría sirviendo tráfico. Al estar en el sensor, un fallo del motor nunca afecta la disponibilidad del servidor. Además, el sensor ya tiene acceso a eve.json (generado por Suricata local) sin latencia de red.

**Por qué SSH al servidor en lugar de un agente:** usar SSH elimina la necesidad de un proceso adicional en el servidor y aprovecha las SSH keys ya configuradas. La latencia de SSH para un `ipset add` es <50ms — insignificante frente al lead time de 60s del sistema.

**Por qué ipset y no reglas iptables directas:** ipset almacena miles de IPs en una tabla hash consultable en O(1). Con iptables puro, cada paquete se compararía contra cada regla secuencialmente — O(n) con n IPs bloqueadas. A 12,000+ BLOCKs, ipset es órdenes de magnitud más eficiente.

---

## Flujo de decisión detallado por flujo

```
ENTRADA: nueva línea JSON en eve.json con event_type=flow

1. ¿event_type == "flow"?  NO → ignorar
   SÍ ↓

2. ¿src_ip en whitelist?
   SÍ → PERMIT inmediato, log INFO (sin IF, sin latencia de inferencia)
   NO ↓

3. Extraer 14 features (mismo orden que models/features.csv)
   ▼
4. X_scaled = scaler.transform(features)
   score = IF.decision_function(X_scaled)

5. Clasificar por umbral:
   score > −0.4459 (τ1)           → PERMIT  (log INFO)
   −0.6027 < score ≤ −0.4459      → LIMIT   → SSH → ipset add ppi_limited
   score ≤ −0.6027 (τ2)           → BLOCK   → SSH → ipset add ppi_blocked → Telegram 🚨

5b. Pre-alerta TENDENCIA (paralelo al score actual):
    Si score_medio de últimos 10 flows de esta IP < TAU_AVISO (−0.35):
    → Telegram 👀 aviso "IP se acerca al umbral de bloqueo"
    (Actúa cuando la IP aún no superó τ1 pero su tendencia es preocupante)

6. Heurísticos en paralelo (independientes del score IF):
   BF-SSH:      ≥5  intentos SSH en 60s → LIMIT
                ≥15 intentos SSH en 60s → BLOCK
   HTTP-Abuse:  ≥50  requests HTTP en 30s → LIMIT
                ≥100 requests HTTP en 30s → BLOCK

7. Si BLOCK: escalada progresiva
   block_counts[ip] == 1 → timeout 300s  (5 min)
   block_counts[ip] == 2 → timeout 1800s (30 min)
   block_counts[ip] >= 3 → timeout 0     (PERMANENTE)
   Persistido en block_counts.json (sobrevive reinicios del motor)

8. Si IP ya en set `bloqueados` (en memoria):
   → log ANOMALÍA cada 5s (rate-limited, sin SSH al servidor)
   ⚠️  El set `bloqueados` se limpia SOLO al reiniciar el motor
```

---

## Parámetros reales del motor (verificados en motor_decision.py)

| Parámetro | Valor real | Propósito |
|---|---|---|
| `TAU1` | −0.4459 | Leído de metricas_offline.txt al arrancar |
| `TAU2` | −0.6027 | Leído de metricas_offline.txt al arrancar |
| `TAU_AVISO` | −0.35 | Pre-alerta tendencia (entre 0 y τ1) |
| `AVISO_MIN_FL` | 10 | Mínimo flows para activar TAU_AVISO |
| `TG_DEDUP_SEG` | 300s | Misma IP no genera 2 alertas en <5min |
| `BF_VENTANA_SEG` | 60s | Ventana para contar intentos SSH |
| `BF_UMBRAL_LIMIT` | 5 | Intentos SSH/60s → LIMIT |
| `BF_UMBRAL_BLOCK` | 15 | Intentos SSH/60s → BLOCK |
| `HTTP_VENTANA_SEG` | 30s | Ventana para contar requests HTTP |
| `HTTP_UMBRAL_LIMIT` | 50 | Requests HTTP/30s → LIMIT |
| `HTTP_UMBRAL_BLOCK` | 100 | Requests HTTP/30s → BLOCK |
| `BLOCK_TIMEOUTS` | [300, 1800, 0] | Progresión: 5min, 30min, permanente |
| `hashlimit-above` | 100/sec | Rate limit para ppi_limited |
| `hashlimit-burst` | 150 | Ráfaga inicial antes de aplicar límite |
| `_block_repeat_ts` | cada 5s | Rate limit de log para IPs ya bloqueadas |
| `SET_BLOCK` | `ppi_blocked` | Nombre del ipset de BLOCK en servidor |
| `SET_LIMIT` | `ppi_limited` | Nombre del ipset de LIMIT en servidor |

---

## Detección heurística — por qué existe junto al IF

El IF clasifica **flujo por flujo**. Un flujo SSH individual de hydra (4 hilos) puede ser breve y tener pocos paquetes → score≈−0.48, cerca de τ1, clasificado como LIMIT o incluso PERMIT en el primer intento.

Los heurísticos cuentan **eventos acumulados en ventana temporal**:
- **5 intentos SSH/60s:** cualquier sesión SSH fallida repetida en un minuto es brute force. No existe uso legítimo de 5 conexiones SSH fallidas desde la misma IP en 60 segundos.
- **15 intentos SSH/60s:** BLOCK definitivo. hydra con `-t 4` genera exactamente este patrón.
- **50 requests HTTP/30s:** tráfico de aplicación anómalo. Un usuario legítimo no hace 50 requests por segundo.
- **100 requests HTTP/30s:** BLOCK. Equivalente a hping3 con `-i u5000` (1 paquete cada 5ms).

**Por qué estos umbrales y no otros:** se calibraron empíricamente con los escenarios B5 (http_repetitivo) y B6 (bruteforce hydra) para detectar el ataque antes de 60 segundos (lead time objetivo). Umbral más bajo → más falsos positivos. Umbral más alto → más lead time.

---

## Set `bloqueados` en memoria — comportamiento crítico para demos

```python
bloqueados = set()   # IPs con BLOCK activo (en memoria del proceso)
limitados  = set()   # IPs con LIMIT activo (en memoria del proceso)
```

Una vez que una IP entra en `bloqueados`, sus flujos subsiguientes van al rama `else`:
- El motor loga `ANOMALÍA | BLOCK` **cada 5 segundos** (rate-limited con `_block_repeat_ts`)
- **NO** llama SSH al servidor (la IP ya está en ipset)
- **NO** actualiza `block_counts.json` (el contador ya fue incrementado)
- El predictor sigue recibiendo esas entradas de log → `block_count_60s` sigue subiendo

**Consecuencia crítica para demostraciones:** si una IP fue bloqueada en una sesión de prueba y el motor NO se reinicia, en la siguiente sesión esa IP ya está en `bloqueados`. Sus nuevos flujos generan log rate-limited pero **no ejecutan SSH al servidor** → el ipset del servidor no se actualiza para el nuevo timeout.

**Procedimiento para demo limpia:**
```bash
# 1. Matar ataques en Kali
# 2. Esperar 90s (Suricata vacía flows residuales)
# 3. Limpiar ipset en servidor
ssh m4rk@192.168.0.120 "sudo ipset flush ppi_blocked && sudo ipset flush ppi_limited"
# 4. Limpiar block_counts
echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json
# 5. REINICIAR MOTOR (limpia bloqueados/limitados en memoria)
echo cisco123 | sudo -S systemctl restart ppi-motor.service ppi-predictor.service
```

---

## Whitelist — IPs nunca bloqueadas

```
192.168.0.1    # Gateway
192.168.0.20   # Desktop (Admin) — origen tráfico normal
192.168.0.110  # Sensor (este host) — no bloquearse a sí mismo
192.168.0.120  # Servidor (objetivo) — no bloquear el destino
192.168.0.130  # Reservada
192.168.0.140  # Reservada
127.0.0.1      # Loopback
```

**Por qué el sensor está en la whitelist:** el motor hace SSH desde el sensor al servidor para aplicar bloqueos. Si el sensor estuviera bloqueado en el servidor, nunca podría ejecutar `ipset add` y el sistema dejaría de funcionar.

**Por qué verificar la whitelist antes del IF:** las IPs whitelisted nunca consumen tiempo de inferencia del IF ni generan SSH al servidor. Reduce latencia para esas IPs a ~0.1ms.

---

## Formato del log del motor

```
# Flujo BLOQUEADO (score muy bajo):
2026-06-22 08:31:37,412 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH byte_ratio=1.97 pkt_rate=3.2 | BLOCK

# Flujo LIMITADO (sospechoso):
2026-06-22 08:31:30,154 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 grado=BAJA tipo=BF_SSH_warn byte_ratio=1.97 pkt_rate=2.1 | LIMIT

# BLOCK de IP ya bloqueada (rate-limited 5s):
2026-06-22 08:31:42,412 | WARNING | ANOMALÍA | src=192.168.0.100 ... | BLOCK

# Heurístico HTTP-ABUSE (sin score IF — formato diferente):
2026-06-22 08:31:50,000 | WARNING | HTTP-ABUSE | src=192.168.0.100 requests=101 ventana=30s | BLOCK

# Estadísticas cada 500 flujos:
2026-06-22 15:04:03,117 | INFO | Estadísticas | flows=138500 anomalías=138500
  latencia_media=34.53ms bloqueados=1 limitados=0
```

> ⚠️ **Importante para el predictor (F4):** las líneas `HTTP-ABUSE` y `BRUTE-FORCE` tienen formato distinto (sin campo `score=`). El predictor solo captura líneas con `score=` (ANOMALÍA y SOSPECHOSO). Los heurísticos no alimentan al predictor.

---

## Rendimiento del motor (verificado en latencia_pipeline.txt)

```
Flows medidos   : 1,000
Latencia media  : 34.533 ms
Latencia mínima : 34.224 ms
Latencia máxima : 38.717 ms
Latencia P95    : 34.768 ms    ← 14× por debajo del límite de 500ms
Throughput      : 29 flows/s
```

**Por qué P95 y no promedio:** el promedio puede ocultar picos. P95=34.768ms significa que el 95% de todos los flujos procesados tardó ≤34.768ms. El 5% restante (picos de latencia de red SSH, garbage collection de Python) se mantiene por debajo de 38.7ms — siempre dentro del requisito de 500ms.

**Throughput de 29 flows/s:** en el laboratorio, el tráfico normal genera ~5-10 flows/s. Un SYN flood genera hasta 50-100 flows/s (Suricata los agrupa en flujos UDP de 1-packet). El motor maneja holgadamente la carga del laboratorio. En producción con 10Gbps, el bottleneck sería la generación de flujos de Suricata, no el motor Python.

---

## Dashboard terminal (`dashboard.py`)

```bash
# En el sensor — actualiza cada 3 segundos
python3 scripts/dashboard.py
```
Muestra: flujos/min, anomalías, IPs bloqueadas activas, latencia media, últimas alertas.

## Dashboard web (`dashboard_web.py`)

```bash
# Acceder desde Desktop: http://192.168.0.110:8080
systemctl is-active ppi-dashboard.service   # verificar estado

# Iniciar manualmente si no está como servicio:
ssh m4rk@192.168.0.110 \
  "nohup /home/m4rk/ppi-sensor/venv/bin/python3 \
   /home/m4rk/ppi-surikata-producto/scripts/dashboard_web.py &"
```

**Por qué Flask+SSE en lugar de polling:** SSE mantiene una conexión HTTP abierta y el servidor hace push de eventos al cliente cuando ocurren. El polling (request cada N segundos) introduce latencia artificial y carga innecesaria. Con SSE, el dashboard muestra cada BLOCK en <1s desde que ocurre.

---

## Telegram — notificaciones al operador

- **Cuándo:** primer BLOCK de una IP (dedup 300s — misma IP no genera 2 alertas en <5min)
- **Qué incluye:** IP, tipo de ataque, score IF, puerto, timestamp
- **Implementación:** llamada HTTP **directa** a `https://api.telegram.org/bot{TOKEN}/sendMessage`
- **No bloqueante:** `threading.Queue(maxsize=100)` + hilo daemon. Si Telegram no responde, la alerta se descarta — el motor nunca se pausa por la notificación

**Por qué dedup 300s:** sin dedup, un SYN flood que genera una alerta por cada flow de log (cada 5s rate-limited) inundaría el chat de Telegram con cientos de mensajes por minuto. 300s = una alerta por ataque, no una por paquete.

Evidencia real: `🚨 PPI ALERTA — BRUTE_FORCE_SSH | BLOCK | IP: 192.168.0.100 | Puerto: 22 | 08:31:37`

---

## enforce.sh — control manual

```bash
# Bloqueo manual con timeout personalizado
bash scripts/enforce.sh 192.168.0.100 BLOCK 120
# → SSH m4rk@192.168.0.120 "sudo ipset add ppi_blocked 192.168.0.100 timeout 120 -exist"

bash scripts/enforce.sh 192.168.0.100 LIMIT 300
bash scripts/enforce.sh 192.168.0.100 UNBLOCK
```

Permite control manual para pruebas o para desbloquear una IP antes de que expire el timeout.

---

## Bloqueo progresivo — evidencia real (2026-06-22)

| Bloqueo | Timestamp | Trigger | Score | Timeout |
|---|---|---|---|---|
| #1 | 05:44:13 | SYN flood continuo | −0.6066 | 300s (5 min) |
| #2 | 06:05:03 | Reincidencia | −0.7696 | 1,800s (30 min) |
| #3 | 06:39:42 | HTTP-ABUSE 100 req/30s | heurístico | **0 (PERMANENTE)** |

**Por qué esta escalada:** un atacante que solo genera un flujo anómalo podría ser un falso positivo — 5 minutos de penalización es razonable. Un atacante que reincide después de 5 minutos demuestra intención — 30 minutos. Un atacante que reincide por tercera vez después de 30 minutos es definitivamente malicioso — bloqueo permanente. Esta lógica de tres strikes está inspirada en sistemas de fail2ban industriales.

---

## Imágenes de referencia

| Imagen | Ruta | Estado |
|---|---|---|
| Servicios activos en sensor | `docs/documentacion/imagenes/demo/paso0_servicios_activos.png` | ✅ Disponible |
| Terminales de monitoreo (motor + predictor) | `docs/documentacion/imagenes/demo/paso1_terminales_monitoreo.png` | ✅ Disponible |
| hping3 corriendo + dashboard | `docs/documentacion/imagenes/demo/paso2_hping3_corriendo.png` | ✅ Disponible |
| Log con BLOCKs de Kali | `docs/documentacion/imagenes/F3_motor_control/captura_motor_log_block.png` | ⏳ Pendiente captura |
| ipset list ppi_blocked | `docs/documentacion/imagenes/F3_motor_control/captura_ipset_bloqueados.png` | ⏳ Pendiente captura |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado | Verificación |
|---|---|---|---|
| CA-5 | Latencia P95 < 500ms | ✅ **34.768ms** (×14 margen) | `cat results/latencia_pipeline.txt` |
| CA-6 | Motor activo / ITL=0% | ✅ 1.18M entradas / 0% | `systemctl is-active ppi-motor.service` |
| CA-7 | τ1/τ2 cargados al arranque | ✅ −0.4459 / −0.6027 | `grep tau results/metricas_offline.txt` |
| CA-8 | Whitelist nunca bloqueada | ✅ 0/5 IPs en block_counts | `cat results/block_counts.json` |
| CA-9 | IP atacante efectivamente bloqueada | ✅ 12,811 BLOCKs a 192.168.0.100 | log motor F6 |
| CA-10 | Bloqueo #3 = PERMANENTE | ✅ timeout=0 validado 06-22 | evidencia en tabla arriba |
| CA-F3-01 | Dashboard web accesible :8080 | ✅ Flask+SSE activo | `http://192.168.0.110:8080` |
| CA-F3-02 | Telegram sin bloquear motor | ✅ HTTP 200 + threading.Queue | log `08:31:37` alerta recibida |
| CA-F3-03 | Heurísticos BF-SSH y HTTP-Abuse activos | ✅ Validado con B5 y B6 | log BRUTE_FORCE_SSH / HTTP-ABUSE |

---

## Argumento de defensa

> "F3 es donde el modelo se convierte en control de red real. La diferencia frente a un IDS pasivo es exactamente esta: no solo detecta, sino que actúa en menos de 35ms desde que Suricata registra el flujo hasta que el kernel del servidor descarta los paquetes. Logramos esto con una arquitectura que separa deliberadamente el plano de detección (sensor 192.168.0.110) del plano de enforcement (servidor 192.168.0.120): el motor en el sensor nunca puede afectar la disponibilidad del servidor.
>
> Los heurísticos complementan al IF donde los flujos individuales son sutiles: hydra con 4 hilos genera conexiones SSH breves que individualmente tienen score≈−0.48, pero el patrón acumulado de 15 intentos en 60 segundos es inequívoco. El sistema los detecta y bloquea en T+60s — dentro del requisito de 90s para B6.
>
> El bloqueo progresivo aplica el principio de proporcionalidad: 5 minutos para el primer incidente, 30 para el segundo, permanente para el tercero. Un atacante que reincide tres veces en horas es una amenaza persistente, no un falso positivo."

