# Ejemplo de Flujo Completo — Demo del Producto
**PPI UPeU 2026 · Rubén Mark Salazar Tocas**  
**Verificado en vivo: 2026-06-22 · Sensor 192.168.0.110 · Servidor 192.168.0.120**

---

## DEMO RÁPIDA — Comandos verificados (copiar y pegar)

> Ejecutar en orden desde **Desktop (192.168.0.20)**. El sistema debe estar corriendo.

### Paso 0 — Verificar que el sistema está activo

```bash
# En Desktop (192.168.0.20)
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
# Salida esperada: active (×4)
```

### Paso 1 — Abrir monitoreo en tiempo real (3 terminales)

```bash
# TERMINAL 1 — log del motor en vivo
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# TERMINAL 2 — log del predictor en vivo
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"

# TERMINAL 3 — estadísticas cada 3s (dashboard terminal)
ssh m4rk@192.168.0.110 "source /home/m4rk/ppi-sensor/venv/bin/activate && python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py"

# NAVEGADOR — dashboard web
# Abrir http://192.168.0.110:8080
```

### Paso 2 — Lanzar SYN Flood desde Kali (B1)

```bash
# En Desktop (192.168.0.20) — SSHear a Kali y lanzar
ssh m4rk@192.168.0.100 "sudo hping3 -S -p 80 -i u5000 192.168.0.120"
# -S      = SYN packets
# -p 80   = puerto nginx
# -i u5000 = un paquete cada 5000 microsegundos (200 pkt/s)
# (usar --flood para máxima intensidad, -i u5000 para demo controlada)
```

**Qué ver en Terminal 1 (motor log) — ~60s después:**
```
2026-06-22 HH:MM:SS,xxx | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.70XX grado=ALTA tipo=ANOMALIA_GENERICA
  byte_ratio=XX.XX pkt_rate=X.X | BLOCK
```

**Qué ver en Terminal 2 (predictor log) — inmediatamente después del BLOCK:**
```
2026-06-22 HH:MM:SS | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=XX.XX%
  score=-0.70XX limits_15s=0 blocks_60s=1
```

**Verificar bloqueo en servidor:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
# Salida esperada:
# Members:
# 192.168.0.100 timeout 2XX  ← contando hacia 0
```

**Detener ataque:**
```bash
# Ctrl+C en la sesión SSH a Kali
# O desde Desktop:
ssh m4rk@192.168.0.100 "sudo pkill hping3"
```

### Paso 3 — Lanzar Brute Force SSH desde Kali (B6)

```bash
# Primero desbloquear Kali si está bloqueada:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK

# Lanzar hydra desde Desktop → Kali → Servidor
ssh m4rk@192.168.0.100 "hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4"
# -l root          = usuario objetivo
# -P fasttrack.txt = diccionario (existe en Kali ✅)
# -t 4             = 4 hilos paralelos
```

**Qué ver — T+53s:**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 tipo=BAJA_ANOMALIA | LIMIT
```

**Qué ver — T+60s:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 tipo=BRUTE_FORCE_SSH | BLOCK
```

### Paso 4 — Control manual con enforce.sh

```bash
# Desde sensor (192.168.0.110):
# BLOQUEAR una IP manualmente (aplica en servidor 192.168.0.120)
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 120
# → SSH a servidor → sudo ipset add ppi_blocked 192.168.0.100 timeout 120

# LIMITAR una IP
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 LIMIT 300

# DESBLOQUEAR
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

### Paso 5 — Demostrar validación completa

```bash
# Correr suite de validación F1→F6 (tarda ~2 min)
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
# Salida esperada: 16/16 criterios PASS
```

### Paso 6 — Ver métricas del modelo

```bash
# Métricas Isolation Forest
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_offline.txt"

# Métricas XGBoost v2
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_predictor_v2.txt"

# Bloqueo progresivo actual
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/block_counts.json"

# Latencia del pipeline
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/latencia_pipeline.txt"
```

---

## Escenario 1 — B1 SYN Flood → Isolation Forest

### Comando en Kali (desde Desktop vía SSH)

```bash
ssh m4rk@192.168.0.100 "sudo hping3 -S -p 80 -i u5000 192.168.0.120"
```

> Para flood máximo (solo en demo breve): `sudo hping3 -S --flood -p 80 192.168.0.120`

---

### F1 — Captura (Suricata · sensor 192.168.0.110)

Suricata monitorea `ens35` en modo pasivo. Escribe eventos `flow` en `/var/log/suricata/eve.json`
cuando un flujo TCP se cierra (por timeout, RST o FIN).

**Problema del SYN Flood:** el handshake TCP nunca completa (no llega ACK del cliente).
Suricata espera el flow timeout (~60s) antes de registrar el flujo incompleto.
**Por eso el lead time es ~62s.**

```json
{
  "timestamp": "2026-06-22T05:44:09.812Z",
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 8420,
    "pkts_toclient": 0,
    "bytes_toserver": 421000,
    "bytes_toclient": 0,
    "start": "2026-06-22T05:43:07.991Z",
    "end":   "2026-06-22T05:44:09.812Z",
    "age": 61
  }
}
```

---

### F2 — Isolation Forest (14 features + score)

`motor_decision.py` lee eve.json con tail. Extrae las 14 features en el orden exacto de `models/features.csv`:

```python
pkts_toserver  = 8420    pkts_toclient  = 0
bytes_toserver = 421000  bytes_toclient = 0
duration       = 61.82   # segundos
pkt_rate       = 136.2   # (8420+0) / 61.82
byte_rate      = 6809.1
pkt_ratio      = 8420 / (0+1) = 8420.0   # toclient=0 → ratio muy alto
byte_ratio     = 421000 / (0+1) = 421000.0
avg_pkt_size   = (421000+0) / (8420+0+1) = 50.0
is_tcp=1  is_udp=0  is_icmp=0
dest_port      = 80
```

```python
X_scaled = scaler.transform([features])   # scaler ajustado en entrenamiento
score = isolation_forest.decision_function(X_scaled)[0]
# score = -0.6066  ← muy negativo = muy anómalo
```

**Regla de decisión:**
```
score = -0.6066
τ2    = -0.6027

score ≤ τ2  →  BLOCK 🚫
```

---

### F3 — Motor de decisión + control inline (servidor 192.168.0.120)

**Línea real del motor_decision.log:**
```
2026-06-22 05:44:13,XXX | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6066 grado=ALTA tipo=ANOMALIA_GENERICA
  byte_ratio=4.92 pkt_rate=1.3 | BLOCK
```

**El motor SSHea al servidor y ejecuta:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist"
```

**Bloqueo progresivo** (leído de `results/block_counts.json`):
```
Primer BLOCK  → timeout = 300s  (5 min)
Segundo BLOCK → timeout = 1800s (30 min)
Tercer BLOCK+ → timeout = 0     (PERMANENTE)
```

**Verificar en servidor:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
# Members:
# 192.168.0.100 timeout 295
```

**Latencia total pipeline:** P95 = 34.768ms (medido en `results/latencia_pipeline.txt`)

---

### F4 — Predictor XGBoost v2 (predictor.py · ciclo 10s)

El predictor lee `motor_decision.log` cada 10 segundos. Al detectar el BLOCK calcula 9 features:

```python
dest_port       = 80
proto_tcp       = 1    proto_udp = 0    proto_icmp = 0
hora_sin        = sin(hora * 2π/24)
hora_cos        = cos(hora * 2π/24)
limit_count_15s = 0    # sin LIMITs previos (SYN flood → BLOCK directo)
block_count_60s = 1    # primer BLOCK en ventana
is_block        = 1

P = modelo.predict_proba(features)[0][1]
# P ≈ 0.77  →  77%  →  ALERTA-PREDICTIVA 🔴
```

**Línea real del predictor.log:**
```
2026-06-22 HH:MM:SS | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```

> **Nota:** el predictor.log usa formato con `limits_15s` y `blocks_60s` en la misma línea.
> Si la alerta está en dedup (misma IP en < 300s), aparece como `INFO | ALERTA-PREDICTIVA (dedup)`.

---

### Telegram — alerta al operador

Motor llama `api.telegram.org` directamente (asíncrono, no bloqueante):

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

---

### Bloqueo progresivo — ciclo completo (datos reales 2026-06-22)

```
05:44:13 → BLOCK #1  score=-0.6066  block_counts={"192.168.0.100":1}  timeout=300s
06:05:03 → BLOCK #2  score=-0.7696  block_counts={"192.168.0.100":2}  timeout=1800s
06:39:42 → BLOCK #3  HTTP-ABUSE 100req/30s  block_counts={"192.168.0.100":3}  timeout=0
```

**Verificar bloqueo permanente:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
# Members:
# 192.168.0.100          ← sin timeout = PERMANENTE
```

**Desbloquear manualmente:**
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

---

## Escenario 2 — B6 SSH Brute Force → heurístico BF-SSH

### Comando en Kali

```bash
ssh m4rk@192.168.0.100 "hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4"
# fasttrack.txt existe en Kali: /usr/share/wordlists/fasttrack.txt ✅
```

---

### F1 — Captura

Cada intento hydra genera un flujo TCP corto al puerto 22.
Los flujos SSH completados (handshake + fallo de auth + cierre) se registran rápidamente.

```json
{
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_port": 22,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 12, "bytes_toserver": 2847,
    "pkts_toclient": 10, "bytes_toclient": 3640,
    "age": 2
  }
}
```

---

### F2 — IF: score en zona LIMIT

Un flujo SSH de fuerza bruta se parece superficialmente al SSH legítimo:
```
score = -0.4832   (T+53s)
τ2 < score ≤ τ1   →   LIMIT ⚠️
```

```
2026-06-22 08:31:07,XXX | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT
```

---

### F3 — Heurístico BF-SSH (el que bloquea)

```
Parámetros reales (motor_decision.py):
  BF_VENTANA_SEG  = 60   # ventana de observación
  BF_UMBRAL_LIMIT = 5    # intentos → LIMIT
  BF_UMBRAL_BLOCK = 15   # intentos → BLOCK
```

```
T+ 0s  hydra inicia (4 hilos)
T+15s  contador BF-SSH=4   < 5  → sin acción
T+30s  contador BF-SSH=8   ≥ 5  → LIMIT heurístico
T+53s  IF también detecta  → LIMIT (score=-0.4832)
T+60s  contador BF-SSH=15  ≥ 15 → BLOCK
```

**Log real (T+60s):**
```
2026-06-22 08:31:37,XXX | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH | BLOCK
```

---

### F4 — Predictor con señal BF

```python
limit_count_15s = 5    # 5 LIMITs previos en 15s
block_count_60s = 1
dest_port       = 22
proto_tcp       = 1

P ≈ 0.72   →   72%   →   ALERTA-PREDICTIVA 🔴
```

**predictor.log:**
```
2026-06-22 08:31:4X | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=72.XX%
  score=-0.6228 limits_15s=5 blocks_60s=1
```

**Telegram real recibido:**
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

## Escenario 3 — Tráfico normal (whitelist, desde Desktop)

```bash
# Desde Desktop (192.168.0.20) — esto nunca se bloqueará
for i in $(seq 1 120); do curl -s http://192.168.0.120/ -o /dev/null; sleep 1; done
```

**Lo que pasa en el motor:**
```python
# Verificación O(1) antes del IF:
if src_ip in WHITELIST:   # 192.168.0.20 ∈ whitelist
    return "PERMIT"       # sin calcular score
```

**Log** (solo aparece en estadísticas cada 500 flujos):
```
INFO | Estadísticas | flows=500 anomalías=0 bf=0 http_abuse=0 bloqueados=0 limitados=0 latencia_media=34.50ms
```

**Verificar que Desktop no está en ipset:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
# Salida esperada: 192.168.0.20 is NOT in set ppi_blocked.
```

---

## F5 — Reentrenamiento automático (en segundo plano)

```bash
# Ver historial de reentrenamientos
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
# Muestra: fecha | horas | events | auc_anterior | auc_nuevo | precision | recall | reemplazado

# Ver crontab activo
ssh m4rk@192.168.0.110 "crontab -l"
# 0 2 * * 0  → f5_reentrenar_if.py      (domingos 02:00)
# 0 3 * * *  → f5_reentrenar_xgboost.py (diario 03:00)

# Ejecutar reentrenamiento manual XGBoost (con ventana extendida)
ssh m4rk@192.168.0.110 "source /home/m4rk/ppi-sensor/venv/bin/activate && \
  python3 /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_xgboost.py --horas 48"
```

---

## F6 — Validación completa (comandos verificados)

```bash
# Suite completa F1→F6 (tarda ~2 min, resultados en pantalla)
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"

# Ver resultado de validaciones individuales
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/f2_val_modelo_if.sh"
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/f3_val_motor.sh"
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/f6_val_corridas.sh"

# Ver CSV de las 40 corridas
ssh m4rk@192.168.0.110 "head -5 /home/m4rk/ppi-surikata-producto/results/resultados_f6_completo.csv"

# Ver log de validación guardado
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/validacion_20260622_150405.log"
```

---

## Resumen de tiempos y evidencia real

| Escenario | Primer evento | LIMIT | BLOCK | Telegram | Dashboard |
|---|---|---|---|---|---|
| B1 SYN Flood | hping3 T+0s | T+60s (score≤τ1) | T+62s (score≤τ2) | T+62s + ~1s API | T+62s + <150ms SSE |
| B6 BF SSH | hydra T+0s | T+30s (BF-SSH≥5) | T+60s (BF-SSH≥15) | T+60s + ~1s | T+60s + <150ms |
| Normal whitelist | curl T+0s | NUNCA | NUNCA | NUNCA | PERMIT en stats |

## Valores reales verificados (2026-06-22)

| Componente | Métrica | Valor |
|---|---|---|
| Isolation Forest | AUC-ROC | **0.8998** |
| IF | Precision / Recall en τ1 | **99.54% / 99.40%** |
| IF | τ1 (PERMIT/LIMIT) | **−0.4459** (Youden) |
| IF | τ2 (LIMIT/BLOCK) | **−0.6027** (FPR≤2%) |
| Motor | Latencia P95 | **34.768ms** |
| Motor | Latencia media (en vivo) | **34.59ms** |
| XGBoost v2 | AUC-ROC | **0.9992** |
| XGBoost v2 | FP + FN en test | **14** (7+7 de 12,488) |
| Predictor | P actual Kali (en vivo) | **P=89.27%** (ALERTA-PREDICTIVA) |
| Sistema | Disponibilidad 40 corridas | **100%** |
| Sistema | ITL | **0%** |
| Sistema | Lead time SYN Flood | **~62s** |
| Sistema | Lead time BF SSH | **60s** |
| Sistema | Bloqueo #3 permanente | **timeout=0** validado |
| CA-16 | FPR datos nuevos (119 flows) | **0.0%** |
| Validación | Criterios PASS | **16/16** |
