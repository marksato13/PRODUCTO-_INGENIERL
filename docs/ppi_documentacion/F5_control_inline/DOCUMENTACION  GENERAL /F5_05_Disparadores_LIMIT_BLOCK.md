# F5-05: Disparadores de Decisión LIMIT y BLOCK — Flujo del Modelo y Comandos de Verificación

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F5 — Control Inline e Integración  
**Documento:** F5-05 — Disparadores de Decisión LIMIT y BLOCK  
**Fecha:** 2026-06-14

---

## 1. Introducción

Este documento describe con precisión qué condiciones técnicas disparan las decisiones **LIMIT** y **BLOCK** en el motor de decisión (`motor_decision.py`), el flujo interno del modelo que lleva a cada decisión, y los comandos concretos para reproducir cada escenario desde el nodo atacante (Kali, 192.168.0.100).

El propósito es doble:
- **Validación técnica**: demostrar que el sistema reacciona de forma determinista ante tráfico anómalo real.
- **Defensa ante el jurado**: proveer evidencia reproducible de que la clasificación no es arbitraria sino derivada de umbrales calibrados sobre datos reales del laboratorio.

---

## 2. Flujo de Decisión del Motor

### 2.1 Pipeline completo por cada flujo de red

```
┌─────────────────────────────────────────────────────────────┐
│  eve.json (Suricata flow record)                            │
│  Campos: src_ip, dest_ip, dest_port, proto, pkts_toserver,  │
│          pkts_toclient, bytes_toserver, bytes_toclient,      │
│          flow.start, flow.end                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  EXTRACCIÓN DE 14 FEATURES                                  │
│                                                             │
│  Derivadas:                                                 │
│    duration   = flow.end − flow.start (segundos)            │
│    pkt_rate   = (pkts_toserver + pkts_toclient) / duration  │
│    byte_rate  = (bytes_toserver + bytes_toclient) / duration │
│    pkt_ratio  = pkts_toserver / (pkts_toclient + 1)         │
│    byte_ratio = bytes_toserver / (bytes_toclient + 1)       │
│    avg_pkt_size = total_bytes / total_pkts                  │
│                                                             │
│  Binarias:                                                  │
│    is_tcp, is_udp, is_icmp                                  │
│                                                             │
│  Directo: dest_port                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  NORMALIZACIÓN: scaler.pkl (StandardScaler)                 │
│  X_scaled = (X − μ_entrenamiento) / σ_entrenamiento        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  ISOLATION FOREST: isolation_forest.pkl                     │
│  score = model.decision_function(X_scaled)                  │
│  Rango: [−1.0, +1.0]                                        │
│    score cercano a +1 → flujo típico (normal)               │
│    score cercano a −1 → flujo muy aislado (anómalo)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  CLASIFICACIÓN DE GRADO                                     │
│    score > −0.4973          → NORMAL                        │
│    −0.6873 < score ≤ −0.4973 → BAJA                        │
│    −0.8200 < score ≤ −0.6873 → ALTA                        │
│    score ≤ −0.8200          → CRITICA                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DETECTORES HEURÍSTICOS (verificados ANTES que el IF score) │
│                                                             │
│  SSH Brute Force:                                           │
│    contador ssh_intentos[src_ip] en ventana 60s             │
│    ≥ 5  → fuerza LIMIT  (sobreescribe IF score)            │
│    ≥ 15 → fuerza BLOCK  (sobreescribe IF score)            │
│                                                             │
│  HTTP Abuse:                                                │
│    contador http_requests[src_ip] en ventana 30s            │
│    ≥ 50  → fuerza LIMIT  (sobreescribe IF score)           │
│    ≥ 100 → fuerza BLOCK  (sobreescribe IF score)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DECISIÓN FINAL                                             │
│                                                             │
│    score > τ1 (−0.4973)      → PERMIT  (ALLOW)             │
│    τ2 < score ≤ τ1           → LIMIT   (hashlimit 100pkt/s) │
│    score ≤ τ2 (−0.6873)      → BLOCK   (DROP)              │
│                                                             │
│  Whitelist: 192.168.0.1/20/110/120/130/140 → siempre PERMIT │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  ACCIÓN ipset (en servidor 192.168.0.120 vía SSH)          │
│                                                             │
│  LIMIT → ipset add ppi_limited  <src_ip> timeout 1800      │
│  BLOCK → ipset add ppi_blocked  <src_ip> timeout 3600      │
│                                                             │
│  iptables FORWARD:                                          │
│    ppi_blocked  → DROP (absoluto)                           │
│    ppi_limited  → hashlimit 100/s, exceso → DROP           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Origen y calibración de los umbrales τ1 y τ2

| Umbral | Valor | Criterio de selección | Efecto |
|---|---|---|---|
| τ1 = −0.4973 | Índice de Youden | Maximiza TPR − FPR (91% TPR, 9.5% FPR) | Frontera PERMIT/LIMIT |
| τ2 = −0.6873 | FPR ≤ 2% | Alta precisión, mínimos falsos positivos | Frontera LIMIT/BLOCK |

Derivados de la curva ROC calculada sobre el conjunto de validación (val.csv, 15% cronológico del dataset).

---

## 3. Comandos que Disparan LIMIT

> Ejecutar desde Kali Linux (192.168.0.100). El servidor objetivo es 192.168.0.120.

### 3.1 LIMIT por heurística SSH (8 intentos en 60s)

```bash
# En Kali: intentos SSH fallidos — supera umbral de 5 intentos/60s
for i in $(seq 1 8); do
  ssh -o ConnectTimeout=2 -o BatchMode=yes -o StrictHostKeyChecking=no \
      fakeuser@192.168.0.120 exit 2>/dev/null
  sleep 4
done
```

**Flujo del modelo:**

```
8 intentos fallidos al puerto 22 en ~32s
  → ssh_intentos[192.168.0.100] = 8 ≥ 5
  → heurística BRUTE_FORCE_SSH activa → fuerza LIMIT
  → grado = BAJA, tipo = BRUTE_FORCE_SSH
  → ipset add ppi_limited 192.168.0.100 timeout 1800
```

**Log esperado:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
         score=-0.51 grado=BAJA tipo=BRUTE_FORCE_SSH | LIMIT
```

---

### 3.2 LIMIT por IF score — HTTP moderado anómalo (60 req en 20s)

```bash
# En Kali: requests HTTP rápidos — pkt_rate inusual para un flujo TCP único
for i in $(seq 1 60); do
  curl -s http://192.168.0.120/ -o /dev/null
  sleep 0.33
done
```

**Flujo del modelo:**

```
60 requests en ~20s hacia puerto 80
  → duration ≈ 20s, pkts_toserver ≈ 180, bytes_toserver ≈ 9000
  → pkt_rate ≈ 9 pkt/s, byte_rate ≈ 450 B/s
  → X_scaled: pkt_rate y byte_rate 2.1σ sobre media normal
  → IF score ≈ −0.55  (τ2 < −0.55 ≤ τ1)
  → grado = BAJA, tipo = HTTP_ABUSE
  → LIMIT
```

**Log esperado:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.55 grado=BAJA tipo=HTTP_ABUSE | LIMIT
```

---

## 4. Comandos que Disparan BLOCK

### 4.1 BLOCK por heurística SSH (20 intentos rápidos)

```bash
# En Kali: ráfaga de intentos SSH — supera umbral de 15 intentos/60s
for i in $(seq 1 20); do
  ssh -o ConnectTimeout=1 -o BatchMode=yes -o StrictHostKeyChecking=no \
      fakeuser@192.168.0.120 exit 2>/dev/null
done
```

**Flujo del modelo:**

```
20 intentos en < 20s al puerto 22
  → ssh_intentos[192.168.0.100] = 20 ≥ 15
  → heurística BRUTE_FORCE_SSH → fuerza BLOCK (sin esperar IF score)
  → grado = ALTA, tipo = BRUTE_FORCE_SSH
  → ipset add ppi_blocked 192.168.0.100 timeout 3600
```

**Log esperado:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
         score=-0.68 grado=ALTA tipo=BRUTE_FORCE_SSH | BLOCK
```

---

### 4.2 BLOCK por heurística HTTP (120 requests en 30s)

```bash
# En Kali: flood HTTP — supera umbral de 100 req/30s
for i in $(seq 1 120); do
  curl -s http://192.168.0.120/ -o /dev/null
  sleep 0.2
done
```

**Flujo del modelo:**

```
120 requests en ~24s hacia puerto 80
  → http_requests[192.168.0.100] = 120 ≥ 100 en ventana 30s
  → heurística HTTP_ABUSE → fuerza BLOCK
  → grado = ALTA, tipo = HTTP_ABUSE
  → ipset add ppi_blocked 192.168.0.100 timeout 3600
```

**Log esperado:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.71 grado=ALTA tipo=HTTP_ABUSE | BLOCK
```

---

### 4.3 BLOCK por IF score — SYN Flood (score ≤ τ2)

```bash
# En Kali (requiere sudo): SYN flood al puerto 80
sudo hping3 -S -p 80 --flood -c 2000 192.168.0.120
```

**Flujo del modelo:**

```
2000 SYN en < 1s al puerto 80
  → duration ≈ 0.8s, pkts_toserver ≈ 2000, pkts_toclient ≈ 0
  → pkt_rate ≈ 2500 pkt/s, bytes_toclient ≈ 0, avg_pkt_size ≈ 40B
  → pkt_ratio = 2000/1 = 2000 (desbalance extremo)
  → X_scaled: pkt_rate +18σ, byte_ratio +12σ → punto muy aislado
  → IF score ≈ −0.87 (≤ τ2 = −0.6873) → grado = CRITICA
  → tipo = SYN_FLOOD
  → BLOCK inmediato
```

**Features que determinan el score:**

| Feature | Valor normal (μ) | Valor SYN flood | σ sobre μ |
|---|---|---|---|
| pkt_rate | 12.3 pkt/s | 2500 pkt/s | +18σ |
| bytes_toclient | 4800 B | ~0 B | −3.1σ |
| avg_pkt_size | 512 B | 40 B | −9.2σ |
| pkt_ratio | 1.2 | 2000 | +14σ |
| duration | 45s | 0.8s | −2.8σ |

**Log esperado:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.87 grado=CRITICA tipo=SYN_FLOOD | BLOCK
```

---

### 4.4 BLOCK por IF score — UDP Flood

```bash
# En Kali (requiere sudo): UDP flood al puerto 53
sudo hping3 --udp -p 53 --flood -c 2000 192.168.0.120
```

**Flujo del modelo:**

```
2000 paquetes UDP en < 1s
  → pkt_rate > 500/s, is_udp = 1, bytes_toclient ≈ 0
  → pkt_rate +15σ sobre media UDP normal
  → IF score ≈ −0.84 → grado = CRITICA
  → tipo = UDP_FLOOD → BLOCK
```

---

### 4.5 BLOCK por IF score — ICMP Flood

```bash
# En Kali (requiere sudo): ICMP flood
sudo hping3 -1 --flood -c 2000 192.168.0.120
```

**Flujo del modelo:**

```
2000 paquetes ICMP en < 1s
  → pkt_rate > 300/s, is_icmp = 1, bytes_toclient ≈ 0
  → avg_pkt_size ≈ 28B (muy pequeño)
  → IF score ≈ −0.91 → grado = CRITICA
  → tipo = ICMP_FLOOD → BLOCK
```

---

## 5. Tabla Resumen de Disparadores

| Escenario | Comando base | Mecanismo | Umbral | Decisión | Score típico | Grado |
|---|---|---|---|---|---|---|
| SSH 8 intentos/60s | `ssh fakeuser@.120` ×8 | Heurística SSH | ≥5/60s | LIMIT | −0.51 | BAJA |
| HTTP 60 req/20s | `curl http://.120` ×60 | IF score | τ2<s≤τ1 | LIMIT | −0.55 | BAJA |
| SSH 20 intentos rápidos | `ssh fakeuser@.120` ×20 | Heurística SSH | ≥15/60s | BLOCK | −0.68 | ALTA |
| HTTP 120 req/24s | `curl http://.120` ×120 | Heurística HTTP | ≥100/30s | BLOCK | −0.71 | ALTA |
| SYN flood 2000 pkt | `hping3 -S --flood` | IF score | ≤τ2 | BLOCK | −0.87 | CRITICA |
| UDP flood 2000 pkt | `hping3 --udp --flood` | IF score | ≤τ2 | BLOCK | −0.84 | CRITICA |
| ICMP flood 2000 pkt | `hping3 -1 --flood` | IF score | ≤τ2 | BLOCK | −0.91 | CRITICA |

---

## 6. Verificación en Tiempo Real

### 6.1 Monitoreo del log del motor (desde Desktop 192.168.0.20)

```bash
# Filtrar solo decisiones LIMIT y BLOCK
ssh m4rk@192.168.0.110 \
  "tail -f /home/m4rk/ppi-surikata-produto/results/motor_decision.log \
   | grep --line-buffered -E 'LIMIT|BLOCK'"
```

### 6.2 Confirmar ipset en tiempo real

```bash
# Ver IPs bloqueadas y limitadas (actualiza cada 2s)
ssh m4rk@192.168.0.110 \
  "watch -n2 'echo \"=== BLOCKED ===\"; sudo ipset list ppi_blocked 2>/dev/null; \
              echo \"=== LIMITED ===\"; sudo ipset list ppi_limited 2>/dev/null'"
```

### 6.3 Desbloquear manualmente entre pruebas

```bash
# Desbloquear Kali antes de siguiente escenario
ssh m4rk@192.168.0.110 \
  "bash /home/m4rk/ppi-surikata-produto/scripts/enforce.sh 192.168.0.100 UNBLOCK"
```

### 6.4 Verificar desde dashboard web

```
http://192.168.0.110:8080 → vista "Alertas"
```
Las alertas LIMIT/BLOCK aparecen en tiempo real vía SSE (latencia ≈ 63ms desde escritura del log).

---

## 7. Orden Recomendado para la Demo ante el Jurado

```
PASO 1  Verificar sistema activo
        → ssh m4rk@192.168.0.110 "systemctl is-active ppi-motor.service"
        → Abrir dashboard: http://192.168.0.110:8080

PASO 2  Disparar LIMIT (heurística SSH — visible e intuitivo)
        → Ejecutar comando 3.1 desde Kali
        → Mostrar alerta "LIMIT / BRUTE_FORCE_SSH" en dashboard

PASO 3  Desbloquear antes de continuar
        → bash enforce.sh 192.168.0.100 UNBLOCK

PASO 4  Disparar BLOCK (SYN flood — demuestra IF score extremo)
        → Ejecutar comando 4.3 desde Kali (sudo hping3 -S --flood)
        → Mostrar alerta "BLOCK / SYN_FLOOD / grado=CRITICA" en dashboard
        → Mostrar ipset list ppi_blocked con 192.168.0.100 + timeout

PASO 5  Mostrar que el bloqueo es efectivo
        → Intentar curl http://192.168.0.120/ desde Kali → sin respuesta (DROP)
        → Intentar curl desde Desktop (.20) → responde normalmente (whitelist)

PASO 6  Explicar los umbrales τ1 y τ2 en la curva ROC
        → "Estos umbrales fueron calibrados sobre datos reales del laboratorio,
           no son arbitrarios: τ1 maximiza TPR−FPR (91%/9.5%), τ2 garantiza FPR≤2%"
```

---

## 8. Justificación para el Jurado

**P: ¿Por qué los límites son exactamente −0.4973 y −0.6873 y no valores redondos?**

Porque se derivaron matemáticamente de la curva ROC calculada sobre val.csv (2,847 flujos). τ1 es el punto de Youden J = max(TPR − FPR). τ2 es el punto donde FPR cae por debajo del 2%. Son valores de la curva, no supuestos.

**P: ¿Qué pasa si un atacante envía tráfico lento para no superar los umbrales heurísticos?**

El Isolation Forest evalúa cada flujo individualmente sin importar la velocidad. Un flujo con `pkt_ratio` extremo, `bytes_toclient=0` o `avg_pkt_size` atípico obtiene score bajo aunque sea un único paquete. Las heurísticas son un complemento, no el mecanismo principal.

**P: ¿Puede el sistema bloquear tráfico legítimo?**

En producción (40 corridas, F6): 0 falsos positivos de tráfico legítimo bloqueado. La whitelist protege las IPs del laboratorio. El FPR a nivel τ2 es ≤2%, y en la práctica fue 0% porque el tráfico normal real no produce scores cercanos a τ2.

---

*Documento generado: 2026-06-14*  
*Sensor: Ubuntu 192.168.0.110 | Atacante: Kali 192.168.0.100 | Servidor: 192.168.0.120*  
*Umbrales validados en 40 corridas F6 — AUC-ROC: 0.9440*
