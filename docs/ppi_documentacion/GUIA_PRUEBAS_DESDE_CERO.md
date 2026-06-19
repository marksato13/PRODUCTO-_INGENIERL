# Guía de Pruebas desde Cero — Sistema PPI Surikata

**Universidad Peruana Unión | Rubén Mark Salazar Tocas**
**Motor:** `motor_decision.py` | τ1=−0.4459 | τ2=−0.6027 | sklearn 1.9.0

Esta guía permite reproducir cualquier prueba desde un estado limpio.
Todos los comandos se ejecutan desde **Desktop 192.168.0.20**.

---

## 0. Prerequisitos — Verificar conectividad

```bash
ssh m4rk@192.168.0.110 "echo OK sensor"
ssh m4rk@192.168.0.120 "echo OK servidor"
ssh m4rk@192.168.0.100 "echo OK kali"

# Suricata activo y escribiendo
ssh m4rk@192.168.0.110 "sudo systemctl is-active suricata && ls -lh /var/log/suricata/eve.json"
# Esperado: active + archivo > 0 bytes

# Motor activo
ssh m4rk@192.168.0.110 "sudo systemctl is-active ppi-motor.service"
# Esperado: active
```

---

## 1. Arrancar el sistema desde cero

### 1.1 Limpiar estado anterior

```bash
# Limpiar ipsets en servidor
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null; \
   echo cisco123 | sudo -S ipset flush ppi_limited 2>/dev/null; \
   echo Ipsets limpiados"

# Confirmar vacíos
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null | tail -3"
```

### 1.2 Reiniciar el motor

```bash
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service"
sleep 6

# Verificar arranque correcto
ssh m4rk@192.168.0.110 \
  "grep 'Modelo cargado\|Servidor init' \
   /home/m4rk/ppi-surikata-producto/results/motor_decision.log | tail -2"
```

**Salida esperada:**
```
INFO | Modelo cargado | umbral_base=-0.5660 | τ1=-0.4459 | τ2=-0.6027
INFO | Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=-0.4459 τ2=-0.6027
```

### 1.3 Abrir log y dashboard en tiempo real

```bash
# Terminal 1 — log en vivo (solo WARNING e INFO)
ssh m4rk@192.168.0.110 \
  "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | grep -E 'ANOMALÍA|SOSPECHOSO|BRUTE|HTTP-ABUSE|Estadísticas|TENDENCIA'"

# Terminal 2 — Dashboard en navegador
# http://192.168.0.110:8080  →  pestaña "Alertas"
```

---

## 2. Pruebas Grupo A — Tráfico Normal (sin alertas)

**Objetivo:** confirmar que Desktop .20 nunca genera alertas (whitelist).

```bash
# A1 — HTTP normal (20 requests)
for i in $(seq 1 20); do curl -s -o /dev/null http://192.168.0.120/; sleep 2; done

# A2 — SSH legítimo (5 conexiones)
for i in $(seq 1 5); do
  ssh -o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=no \
    m4rk@192.168.0.120 "echo ok" 2>/dev/null
  sleep 3
done

# Verificar: 0 alertas para .20
ssh m4rk@192.168.0.110 \
  "grep '192.168.0.20' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | grep -E 'ANOMALÍA|LIMIT|BLOCK' | wc -l"
```
**Esperado:** `0`

---

## 3. Pruebas Grupo B — Ataques (BLOCK esperado)

> Limpiar ipsets entre cada test: `ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null"`

### B1 — SYN Flood

```bash
# Iniciar desde Kali
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "nohup sudo hping3 -S --flood -p 80 192.168.0.120 > /dev/null 2>&1 &"

echo "Esperando detección ~65s..."
sleep 65

# Verificar bloqueo
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null | grep 192.168.0.100 \
  && echo BLOQUEADA || echo NO bloqueada aun"

# Log evidencia
ssh m4rk@192.168.0.110 \
  "grep '192.168.0.100' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | grep 'BLOCK' | tail -2"

# Detener
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "sudo pkill hping3 2>/dev/null; echo detenido"
```

**Log esperado:**
```
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.6XXX grado=ALTA
tipo=SYN_FLOOD byte_ratio=XXX.XX pkt_rate=X,XXX.X | BLOCK
```
**Telegram:** `🚨 PPI ALERTA — SYN_FLOOD | Accion: BLOCK (DROP) | IP: 192.168.0.100`

---

### B2 — Port Scan

```bash
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "sudo nmap -sS 192.168.0.120"

sleep 5
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null \
  | grep 192.168.0.100 && echo BLOQUEADA || echo no detectado"
```

**Log esperado:**
```
ANOMALÍA | src=192.168.0.100 ... score=-0.7XXX grado=ALTA tipo=ANOMALIA_GENERICA | BLOCK
```

---

### B5 — HTTP Abuse (heurístico, más rápido ~30s)

```bash
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null"

# Curl infinito desde Kali
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "nohup bash -c 'while true; do curl -s -o /dev/null http://192.168.0.120/; done' \
  > /dev/null 2>&1 &"

echo "Esperando 35s..."
sleep 35

ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null \
  | grep 192.168.0.100 && echo BLOQUEADA"

ssh m4rk@192.168.0.110 \
  "grep 'HTTP-ABUSE' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | tail -2"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "pkill curl 2>/dev/null; echo detenido"
```

**Log esperado:**
```
HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP requests=100/30s | BLOCK
```
**Telegram:** `🚨 PPI ALERTA — HTTP ABUSE | Accion: BLOCK (DROP) | Requests: 100/30s`

---

### B6 — Brute Force SSH

```bash
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "nohup hydra -l root -P /usr/share/wordlists/rockyou.txt \
  -t 4 192.168.0.120 ssh > /tmp/hydra.log 2>&1 &"

echo "Esperando 70s..."
sleep 70

ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null \
  | grep 192.168.0.100 && echo BLOQUEADA"

ssh m4rk@192.168.0.110 \
  "grep 'BRUTE-FORCE' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | tail -2"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 "pkill hydra 2>/dev/null; echo detenido"
```

**Log esperado:**
```
BRUTE-FORCE | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP intentos=15/60s | BLOCK
```

---

## 4. Prueba Mixta C1 — ITL=0% bajo ataque

**Objetivo:** Kali bloqueada, Desktop sin interrupciones simultáneamente.

```bash
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null"
> /tmp/normal_c1.txt

# Lanzar tráfico normal Desktop .20 en background
bash -c 'for i in $(seq 1 60); do
  if curl -s --max-time 2 -o /dev/null http://192.168.0.120/; then
    echo "OK" >> /tmp/normal_c1.txt
  else
    echo "FAIL" >> /tmp/normal_c1.txt
  fi
  sleep 2
done' &
NORMAL_PID=$!

# Lanzar SYN flood desde Kali simultáneo
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "nohup sudo hping3 -S --flood -p 80 192.168.0.120 > /dev/null 2>&1 &"

echo "C1 activo — esperando 70s..."
sleep 70

echo "=== Kali bloqueada? ==="
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>/dev/null \
  | grep 192.168.0.100 && echo SI || echo NO"

echo "=== Desktop requests completados ==="
grep -c 'OK' /tmp/normal_c1.txt 2>/dev/null || echo 0
echo "(esperado > 50)"

echo "=== ITL: alertas para .20 (debe ser 0) ==="
ssh m4rk@192.168.0.110 \
  "grep '192.168.0.20' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | grep -E 'BLOCK|LIMIT' | wc -l"

# Limpiar
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 "sudo pkill hping3 2>/dev/null"
kill $NORMAL_PID 2>/dev/null
```

**Resultado esperado:**
- Kali: `SI` (bloqueada) ✓
- Desktop: ≥ 50 OK ✓
- ITL: `0` ✓

---

## 5. Verificar Dashboard y Telegram tras las pruebas

```bash
# Estado dashboard
curl -s http://192.168.0.110:8080/api/stats \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
    print('block:', d['block'], '| limit:', d['limit'], \
          '| latencia:', d['latencia'], 'ms | sse:', d['sse_clients'])"

# Últimas alertas
curl -s http://192.168.0.110:8080/api/alerts \
  | python3 -c "import sys,json; \
    [print(e['ts'], e['accion'], e['tipo'], e['src'], 'score:', e['score']) \
    for e in json.load(sys.stdin)[:5]]"
```

**Esperado:**
```
block: ≥1 | limit: ≥0 | latencia: <50 ms | sse: ≥1
06:35:29 BLOCK HTTP_ABUSE 192.168.0.100 score: -0.62XX
```

---

## 6. Limpiar al finalizar

```bash
# Desbloquear Kali
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK

# Limpiar ipsets
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset flush ppi_blocked 2>/dev/null; \
   echo cisco123 | sudo -S ipset flush ppi_limited 2>/dev/null; \
   echo Limpio"

# Matar procesos Kali residuales
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.100 \
  "sudo pkill hping3 2>/dev/null; pkill hydra 2>/dev/null; pkill curl 2>/dev/null; echo OK"
```

---

## 7. Tabla resumen — comportamiento esperado

| Test | Origen | Herramienta | Tiempo det. | Decisión | Telegram |
|---|---|---|---|---|---|
| A1–A4 Normal | Desktop .20 | curl/ssh/scp | — | 0 alertas | — |
| B1 SYN Flood | Kali .100 | hping3 -S --flood | ~62 s | BLOCK | 🚨 |
| B2 Port Scan | Kali .100 | nmap -sS | < 5 s | BLOCK | 🚨 |
| B3 UDP Flood | Kali .100 | hping3 --udp | variable | LIMIT | ⚠️ |
| B4 ICMP Flood | Kali .100 | hping3 -1 | variable | LIMIT | ⚠️ |
| B5 HTTP Abuse | Kali .100 | curl loop | ~30 s | BLOCK | 🚨 |
| B6 Brute Force | Kali .100 | hydra | ~60 s | BLOCK | 🚨 |
| C1 Mixto | Ambos | hping3 + curl | ~62 s | Kali BLOCK · .20 libre | 🚨 |

---

## 8. Diagnóstico si algo no funciona

```bash
# Motor caído → reiniciar
ssh m4rk@192.168.0.110 \
  "sudo systemctl status ppi-motor.service --no-pager | head -4"
# Solución: echo cisco123 | sudo -S systemctl restart ppi-motor.service

# ipset no existe → motor lo crea al arrancar
ssh m4rk@192.168.0.120 \
  "echo cisco123 | sudo -S ipset list ppi_blocked 2>&1 | head -1"

# Dashboard sin datos → verificar motor activo y eve.json
curl -s http://192.168.0.110:8080/api/stats \
  | python3 -c "import sys,json; print('flows:', json.load(sys.stdin)['flows_total'])"

# Proceso fantasma motor_universal
ps aux | grep motor_universal | grep -v grep
# Solución: kill <PID>

# Telegram sin alertas → verificar relay Desktop
curl -s http://192.168.0.20:8889/health || \
  ps aux | grep telegram_relay | grep -v grep
```
