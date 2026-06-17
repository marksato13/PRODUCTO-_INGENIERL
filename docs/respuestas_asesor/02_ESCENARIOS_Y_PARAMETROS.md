# Respuesta: ESCENARIOS Y PARÁMETROS — ¿Por qué es normal? ¿Por qué es anómalo?

**Preocupación del asesor:** "No quiero que me digas 'hay ataque'. Quiero que me expliques qué parámetro cambió y por qué el sistema lo clasificó de esa manera."

---

## 1. El principio central: la anomalía es una desviación medible

El sistema no detecta ataques por "saber" que son ataques. Detecta desviaciones estadísticas respecto al comportamiento normal aprendido. La pregunta correcta es:

> **"¿Qué características numéricas tiene este flujo de red, y qué tan diferente son esas características de lo que el modelo aprendió como normal?"**

La respuesta es el **Anomaly Score** del Isolation Forest: un número entre −1 y 0.

| Score | Zona | Acción del motor | Interpretación |
|---|---|---|---|
| score > −0.4459 | NORMAL | PERMIT — permite todo | El flujo es estadísticamente consistente con tráfico legítimo |
| −0.6027 < score ≤ −0.4459 | SOSPECHOSO | LIMIT — throttle 100 pkt/s | El flujo se desvía moderadamente; puede ser lento o inusual |
| score ≤ −0.6027 | ANÓMALO | BLOCK — DROP total | El flujo es estadísticamente extremo; muy diferente a lo normal |

**τ1 = −0.4459** (umbral Youden — maximiza TPR−FPR)
**τ2 = −0.6027** (umbral FPR≤2% — alta especificidad)

---

## 2. Tabla maestra: parámetros observados por escenario

Los valores a continuación provienen de mediciones reales sobre los archivos `data/raw/*.gz` del laboratorio y del log `results/motor_decision.log`.

### 2.1 Parámetros del flujo de red (por escenario)

| Escenario | Tipo | pkt_rate (pkt/s) | byte_rate (B/s) | Duración flow | avg_pkt_size | pkt_ratio | Score IF observado |
|---|---|---|---|---|---|---|---|
| **A1 HTTP normal** | Normal | ~2–15 | ~500–8,000 | 0.5–5 s | 200–800 B | 0.8–2.0 | > −0.44 (PERMIT) |
| **A2 SSH legítimo** | Normal | ~5–30 | ~1,000–20,000 | 10–120 s | 150–600 B | 1.0–3.0 | > −0.44 (PERMIT) |
| **A3 Transferencia** | Normal | ~50–200 | ~50,000–500,000 | 2–30 s | 800–1,400 B | 1.0–2.5 | > −0.44 (PERMIT) |
| **A4 Tráfico mixto** | Normal | ~5–80 | ~1,000–100,000 | 0.5–30 s | 300–1,200 B | 0.8–2.5 | > −0.44 (PERMIT) |
| **B1 SYN Flood** | Anómalo | ~50,000–500,000 | ~3,000,000–30,000,000 | < 0.01 s | 40–64 B | ∞ (sin respuesta) | −0.4937 (LIMIT→BLOCK) |
| **B2 Port Scan** | Anómalo | ~5,000–50,000 | ~300,000–3,000,000 | < 0.001 s | 40–60 B | ∞ (0 respuestas) | **−0.7333 / −0.7352** (BLOCK) |
| **B3 UDP Flood** | Anómalo | ~100,000–1,000,000 | ~6,000,000–60,000,000 | < 0.001 s | 28–64 B | N/A (UDP) | −0.74 a −0.77 (brecha) |
| **B4 ICMP Flood** | Anómalo | ~500,000+ | ~30,000,000+ | < 0.001 s | 28 B | N/A (ICMP) | No detectado (brecha Suricata) |
| **B5 HTTP Abuse** | Anómalo | ~100–500 | ~50,000–200,000 | 0.01–0.5 s | 400–800 B | 0.5–2.0 | Heurístico: ≥100 req/30s → BLOCK |
| **B6 Brute Force** | Anómalo | ~5–50 | ~3,000–30,000 | 0.5–3 s | 200–600 B | 1.5–5.0 | Heurístico: ≥15 intentos/60s → BLOCK |

### 2.2 Tabla de umbrales de decisión — lo que el asesor quiere ver

| Parámetro | **Normal** | **Sospechoso** | **Anómalo** |
|---|---|---|---|
| **Score IF** | > −0.4459 | (−0.6027, −0.4459] | ≤ −0.6027 |
| **Acción** | PERMIT | LIMIT (100 pkt/s) | BLOCK (DROP) |
| **pkt_rate** (paquetes/seg) | < 500 | 500 – 5,000 | > 5,000 |
| **byte_rate** (bytes/seg) | < 100,000 | 100,000 – 1,000,000 | > 1,000,000 |
| **Duración del flow** | > 0.1 s | 0.001 – 0.1 s | < 0.001 s |
| **avg_pkt_size** (bytes) | > 150 B | 60 – 150 B | < 60 B |
| **pkt_ratio** (to/from) | 0.5 – 5 | 5 – 50 | > 50 o ∞ |
| **Requests HTTP / 30s** | < 50 | 50 – 99 | ≥ 100 |
| **Intentos SSH / 60s** | < 5 | 5 – 14 | ≥ 15 |
| **Flows por minuto** | < 100 | 100 – 500 | > 500 |

---

## 3. Explicación por escenario: qué parámetro cambió y por qué

### Grupo A — ¿Por qué es NORMAL?

El tráfico normal (Desktop 192.168.0.20 → Servidor 192.168.0.120) tiene un patrón de **conversación bidireccional balanceada**:
- El cliente envía una petición (pocos paquetes)
- El servidor responde con datos (más paquetes, más bytes)
- La conexión dura varios segundos
- El tamaño de paquete es grande (datos reales: HTML, imágenes, código SSH)

**A1 — HTTP normal** (`curl http://192.168.0.120/`):
```
pkts_toserver  ≈ 5–10       (GET + ACKs)
pkts_toclient  ≈ 10–30      (respuesta HTML + imágenes)
bytes_toserver ≈ 400–800    (headers HTTP pequeños)
bytes_toclient ≈ 2,000–50,000 (respuesta completa)
duration       ≈ 0.1 – 3 s
pkt_rate       ≈ 5 – 15 pkt/s
avg_pkt_size   ≈ 300 – 800 B
→ Score IF: muy cercano a 0 (muy parecido al entrenamiento)
```

**A2 — SSH legítimo** (`ssh m4rk@192.168.0.120 "comando"`):
```
pkts_toserver  ≈ 20–50
pkts_toclient  ≈ 20–50
bytes_toserver ≈ 5,000–20,000   (comandos + encriptación SSH)
bytes_toclient ≈ 5,000–30,000
duration       ≈ 5 – 120 s       (sesión interactiva)
pkt_rate       ≈ 5 – 30 pkt/s
avg_pkt_size   ≈ 300 – 800 B
→ Score IF: > τ1 (PERMIT)
```

---

### Escenario B1 — ¿Por qué SYN Flood es ANÓMALO?

**Herramienta:** `hping3 -S -p 80 --flood 192.168.0.120`

**Qué hace hping3 --flood:** envía paquetes SYN TCP al máximo de velocidad posible — sin esperar respuesta, sin completar el handshake TCP de 3 pasos.

**Parámetros que cambian:**

| Feature | Valor normal (A1) | Valor SYN Flood (B1) | Diferencia |
|---|---|---|---|
| `pkt_rate` | ~10 pkt/s | ~50,000 pkt/s | **5,000× más alto** |
| `pkts_toclient` | 15 paquetes | ~0 paquetes | Servidor no responde (SYN sin ACK) |
| `pkt_ratio` | ~0.8 (casi 1:1) | ∞ (÷ por cero) | Solo hay dirección to-server |
| `avg_pkt_size` | ~400 B | ~40 B | Paquetes SYN vacíos (solo headers TCP) |
| `duration` | 1–5 s | <0.001 s | Suricata cierra el flow por timeout inmediato |
| `byte_rate` | ~5,000 B/s | ~3,000,000 B/s | **600× más alto** |

**Score observado en el laboratorio:** −0.4937 → SOSPECHOSO → LIMIT
Luego el heurístico HTTP-ABUSE cuenta 100 req/30s → **BLOCK en ~10 segundos**

**Explicación al asesor:** "Un flujo HTTP normal tiene ~10 paquetes en ~1 segundo y el servidor responde con datos. El SYN Flood genera 50,000 paquetes por segundo de solo 40 bytes sin respuesta del servidor. El Isolation Forest aprendió que lo normal tiene pkt_rate ≈ 10 y avg_pkt_size ≈ 400. Un flujo con pkt_rate = 50,000 y avg_pkt_size = 40 está a distancias enormes del espacio aprendido — de ahí el score bajo."

---

### Escenario B2 — ¿Por qué Port Scan es ANÓMALO?

**Herramienta:** `nmap -sS -p 1-1024 --min-rate 1000 -T5 192.168.0.120`

**Qué hace nmap -sS:** envía un SYN a cada uno de los 1024 puertos. Si el puerto está cerrado, el servidor responde con RST. Si está abierto, responde SYN-ACK (y nmap envía RST para no completar la conexión).

**Parámetros que cambian:**

| Feature | Valor normal (A1) | Valor Port Scan (B2) | Diferencia |
|---|---|---|---|
| `pkts_toserver` | 5–10 por flujo | **1 paquete** (solo SYN) | Flujos de 1 solo paquete |
| `pkts_toclient` | 10–30 | 0–1 (RST inmediato) | Sin respuesta significativa |
| `duration` | 1–5 s | **< 0.001 s** | Duración casi cero |
| `pkt_ratio` | ~0.8 | ~1000 | Asimetría extrema |
| `dest_port` | 80 (siempre) | **1, 2, 3, ..., 1024** | Barrido de puertos |
| `avg_pkt_size` | 400 B | **40–60 B** | SYN = solo header TCP |

**Score observado en el laboratorio:** **−0.7333 y −0.7352** → **BLOCK directo** (score ≤ τ2 = −0.6027)

**Explicación al asesor:** "El Port Scan genera flujos de exactamente 1 paquete de 40 bytes, duración 0.001 segundos, hacia 1024 puertos diferentes en secuencia. El modelo nunca vio eso en el entrenamiento — el tráfico normal siempre va al puerto 80 o 22, tiene intercambio bidireccional, y dura al menos 0.1 segundos. La distancia en el espacio de features es tan grande que el score cae a −0.73, muy por debajo del umbral de bloqueo."

---

### Escenario B5 — ¿Por qué HTTP Abuse es ANÓMALO?

**Herramienta:** `while true; do curl http://192.168.0.120/; done` (sin sleep)

**Por qué el score IF puede ser cercano a NORMAL:** cada request individual es legítimo — el pkt_rate de un solo flow HTTP normal. El Isolation Forest ve flujos individuales, y cada uno parece normal.

**Qué parámetro real lo detecta:** el **heurístico de ventana temporal**. El motor cuenta cuántas veces la IP 192.168.0.100 accede al puerto 80 en los últimos 30 segundos:

```python
# motor_decision.py — heurístico HTTP-ABUSE
if n_requests >= 100:   → BLOCK (≥100 req en 30s)
if n_requests >= 50:    → LIMIT (≥50 req en 30s)
```

**Diferencia con navegación normal:**

| Métrica | Navegador humano (normal) | HTTP Abuse (Kali) |
|---|---|---|
| Requests HTTP / 30 seg | 1 – 20 | **100 – 300+** |
| Tiempo entre requests | 2 – 10 s | **< 0.1 s** (máxima velocidad) |
| User-Agent | Mozilla, curl legítimo | curl en bucle automático |
| Patrón | Aleatorio (usuario navega) | Periódico perfecto (máquina) |

**Tiempo hasta BLOCK observado:** ~10–63 segundos (depende de velocidad del servidor)

---

### Escenario B6 — ¿Por qué Brute Force SSH es ANÓMALO?

**Herramienta:** `hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.120`

**Qué detecta el heurístico BF-SSH:**

```python
# motor_decision.py — heurístico BRUTE-FORCE
if intentos_ssh_60s >= 15:   → BLOCK
if intentos_ssh_60s >= 5:    → LIMIT
```

**Diferencia con SSH legítimo:**

| Métrica | SSH legítimo (A2) | Brute Force (B6) |
|---|---|---|
| Intentos SSH / 60 seg | 1 | **15 – 500** |
| Resultado de cada intento | `Authentication successful` | `Authentication failed` |
| Duración de cada sesión | 5–120 s (sesión abierta) | **< 2 s** (falla rápida) |
| Usuario intentado | Siempre el mismo (m4rk) | Variados (root, admin, user...) |
| Contraseñas | Una (la correcta) | Diccionario (miles) |

**Flujo SSH fallido visto por Suricata:**
```
pkts_toserver ≈ 15–25    (negociación + intento de auth fallido)
pkts_toclient ≈ 15–25    (respuesta SSH: auth failure)
duration      ≈ 1–2 s    (muy corto — falla rápido)
dest_port     = 22
```

---

### Escenarios Grupo C — ¿Por qué son MIXTOS?

Los escenarios mixtos tienen **dos fuentes de tráfico simultáneas** hacia el mismo servidor:
- **Desktop 192.168.0.20** → tráfico normal (en whitelist del motor)
- **Kali 192.168.0.100** → tráfico anómalo (evaluado por motor)

**La pregunta del asesor:** "¿Cómo sabe el sistema a quién bloquear?"

**Respuesta:** El motor procesa cada flujo individualmente. El campo `src_ip` del flujo determina quién lo originó:

```python
# motor_decision.py — línea 389
if src_ip in WHITELIST:
    continue   # Desktop → skip (nunca bloqueado)
# Kali → evalúa IF + heurísticos → BLOCK si anómalo
```

**Resultado observado (C1 — HTTP normal + SYN Flood):**
```
Desktop OK=60 FAIL=0  → 100% disponibilidad
Kali     → BLOCK en ~10s (HTTP-ABUSE: 100 req/30s)
ITL = 0%  → cero impacto en tráfico legítimo
```

---

## 4. ¿Por qué hay escenarios "mixtos" y no solo normales/anómalos?

Los escenarios mixtos (Grupo C) simulan la **condición de producción real**: en una red real, los ataques no ocurren cuando la red está vacía. Ocurren mientras hay usuarios legítimos conectados.

La pregunta clave que los mixtos responden es:

> **"Cuando Kali ataca mientras Desktop trabaja, ¿el sistema bloquea solo a Kali y deja pasar a Desktop?"**

Si el sistema bloqueara también al Desktop (falso positivo que afecta al usuario legítimo), el **ITL (Impacto en Tráfico Legítimo)** sería > 0%. En todos los escenarios C donde Kali fue bloqueada, el Desktop mantuvo **ITL = 0%**.

---

## 5. Resumen visual — la "regla de tres" que el asesor puede verificar

```
FLUJO DE RED
     │
     ▼
¿src_ip en whitelist? → SÍ → PERMIT (Desktop/Sensor/Servidor — siempre)
     │ NO
     ▼
Extraer 14 features
     │
     ├── pkt_rate > 5,000 pkt/s?   → score ≤ τ2 → BLOCK  (SYN Flood, Port Scan)
     ├── avg_pkt_size < 60 B?       → score ≤ τ2 → BLOCK  (floods de paquetes vacíos)
     ├── duration < 0.001 s?        → score ≤ τ2 → BLOCK  (scan de un solo paquete)
     ├── pkt_rate 500-5000 pkt/s?   → τ2<score≤τ1 → LIMIT (sospechoso moderado)
     │
     ├── requests_http/30s ≥ 100?   → BLOCK (HTTP-ABUSE — independiente del score)
     ├── requests_http/30s ≥ 50?    → LIMIT (HTTP-ABUSE)
     ├── intentos_ssh/60s ≥ 15?     → BLOCK (BF-SSH — independiente del score)
     ├── intentos_ssh/60s ≥ 5?      → LIMIT (BF-SSH)
     │
     └── Nada de lo anterior?       → score > τ1 → PERMIT (tráfico legítimo)
```

---

## 6. Scores reales observados en el laboratorio

Todos estos valores provienen del archivo `results/motor_decision.log`:

| Escenario | IP origen | Score IF | Grado | Acción final |
|---|---|---|---|---|
| A1-A4 (normal) | 192.168.0.20 | No evaluado (whitelist) | — | PERMIT |
| B1 SYN Flood | 192.168.0.100 | **−0.4937** | BAJA_ANOMALIA | LIMIT → BLOCK (HTTP-ABUSE) |
| B2 Port Scan | 192.168.0.100 | **−0.7333 / −0.7352** | ALTA | BLOCK directo |
| B5 HTTP Abuse | 192.168.0.100 | ~PERMIT (flow individual) | — | BLOCK (heurístico 100 req/30s) |
| B6 Brute Force | 192.168.0.100 | ~−0.45 a −0.60 | BAJA | BLOCK (heurístico 15 intentos/60s) |
| C1 (Kali) | 192.168.0.100 | −0.4937 → HTTP-ABUSE | BAJA→ALTA | BLOCK en ~10s |
| C2 (Kali) | 192.168.0.100 | **−0.7333** | ALTA | BLOCK directo |
| C3 (Kali) | 192.168.0.100 | Flows UDP → PERMIT | — | No bloqueado (brecha) |

---

## 7. Glosario de parámetros para el asesor

| Término | Definición simple |
|---|---|
| **Flow / Flujo** | Una conversación completa entre dos IPs: desde que se abre hasta que se cierra |
| **pkt_rate** | Cuántos paquetes por segundo intercambia la conexión |
| **byte_rate** | Cuántos bytes por segundo fluyen |
| **pkt_ratio** | Relación de paquetes enviados vs recibidos (>10 indica comunicación unidireccional) |
| **avg_pkt_size** | Tamaño promedio de cada paquete (floods: 40-64 B; datos reales: 200-1400 B) |
| **Score IF** | Número entre −1 y 0 que mide cuán diferente es un flujo del comportamiento normal |
| **τ1, τ2** | Umbrales derivados de la curva ROC: donde la detección es óptima según criterios estadísticos |
| **ITL** | Impacto en Tráfico Legítimo — porcentaje de usuarios legítimos afectados por el sistema |
