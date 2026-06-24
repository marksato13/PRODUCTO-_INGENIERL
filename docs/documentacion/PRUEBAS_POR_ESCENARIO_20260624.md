# Pruebas por Escenario — Comandos Verificados, Evidencia Real y Falsos Positivos

**Fecha de la campaña: 2026-06-24** | Todas las pruebas se ejecutaron con limpieza completa del escenario entre cada una (matar procesos en Kali → esperar 90s → flush ipset en servidor → reset `block_counts.json` → restart motor+predictor → `/api/clear` en dashboard).

> Esta campaña responde a tres preguntas: (1) ¿qué comandos reproducen cada tipo de ataque de forma confiable?, (2) ¿qué tan rápido detecta el sistema cada uno?, (3) ¿se generan falsos positivos con tráfico legítimo, incluso rápido?

---

## Procedimiento de limpieza usado entre cada prueba

```bash
# 1. Kali — matar procesos colgados
ssh m4rk@192.168.0.100  # o en la VM directamente
ps aux | grep -E 'hping3|nmap|hydra'
sudo pkill -9 hping3   # / nmap / hydra según corresponda

# 2. Esperar 90s (Suricata vacía flujos residuales)

# 3. Servidor — limpiar ipset
ssh m4rk@192.168.0.120 "sudo ipset flush ppi_blocked && sudo ipset flush ppi_limited"

# 4. Sensor — resetear historial y reiniciar servicios
ssh m4rk@192.168.0.110 "echo '{}' > ~/ppi-surikata-producto/results/block_counts.json && \
  sudo systemctl restart ppi-motor.service ppi-predictor.service"

# 5. Dashboard — limpiar contadores
curl -X POST http://192.168.0.110:8080/api/clear
```

---

## Tabla resumen — los 6 escenarios de ataque + 3 de falso positivo

| # | Escenario | Comando | Resultado | Tiempo de detección | Confiabilidad |
|---|---|---|---|---|---|
| 1 | UDP Flood | `sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120` | BLOCK directo, tipo=UDP_FLOOD | 42-50s | ★★★★★ (4/4 corridas idénticas) |
| 2 | Port Scan | `sudo nmap -sS -p 1-100 192.168.0.120` | LIMIT (score IF) → BLOCK 2s después (heurístico) | ~69s | ★★★★☆ (1/1, comportamiento en 2 etapas confirmado) |
| 3 | SYN Flood | `sudo timeout 10 hping3 -S -p 80 -k --flood 192.168.0.120` | BLOCK directo, tipo=HTTP_ABUSE* | **~1s** | ★★★★★ (el más rápido de todos) |
| 4 | ICMP Flood | `sudo timeout 10 hping3 -1 -k --flood 192.168.0.120` | BLOCK directo, tipo=ICMP_FLOOD | **~309s (5 min)** | ★★★☆☆ (correcto pero muy lento) |
| 5 | HTTP Abuse | `for i in $(seq 1 150); do curl -s -o /dev/null http://192.168.0.120; done` | BLOCK directo, tipo=HTTP_ABUSE | ~59-61s | ★★★★☆ (2/2 corridas) |
| 6 | Brute Force SSH | `hydra -l m4rk -P wordlist.txt -t 4 -f ssh://192.168.0.120` | LIMIT confirmado; BLOCK no confirmado en la ventana observada | LIMIT a 64s | ★★☆☆☆ (necesita más tiempo/intentos para confirmar BLOCK) |
| FP1 | Curl rápido desde IP en whitelist | 80 curls/1s desde 192.168.0.20 (Desktop) | PERMIT (bypass total, nunca se evalúa) | N/A | Control — confirma que whitelist funciona |
| FP2 | Curl en ráfaga desde IP normal | 50 curls/1s desde 192.168.0.100 (sin hping3, solo curl) | BLOCK, tipo=HTTP_ABUSE, score=-0.6149 | ~61s | Esperado — 50 req/s es un patrón objetivamente sospechoso |
| FP3 | Una sola conexión normal | 1 curl desde 192.168.0.100, duración 1ms, 10 paquetes | **PERMIT** (correcto, sin alerta) | N/A (silencio = OK) | Resultado favorable — ver nota abajo |

*\*Nota de clasificación: `clasificar_tipo()` etiqueta cualquier anomalía a puerto 80/TCP como `HTTP_ABUSE` por defecto — no existe una categoría `SYN_FLOOD` explícita en el código actual, aunque el ataque real fue un SYN flood. El **score y el BLOCK son correctos**, solo la etiqueta de "tipo" es genérica para ese puerto. Documentado para no generar confusión si el jurado compara la etiqueta con el ataque real ejecutado.*

---

## Detalle por escenario

### 1. UDP Flood
```bash
sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120
```
**Log real (una de las 4 corridas, 09:44:15):**
```
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53 proto=UDP score=-0.8026 grado=ALTA
  tipo=UDP_FLOOD byte_ratio=218300.16 pkt_rate=230194.4 | BLOCK → BLOCKED timeout=300s
```
**Alertas:** Telegram y dashboard confirmados coherentes con el log (ver `expo_mark.md`).
**Por qué tarda 42-50s:** Suricata solo escribe el flujo cuando lo cierra; con `-k` (puerto origen fijo) todo el ataque es UN flujo, y un flujo UDP en estado "new" cierra 30s después de su último paquete — no es lentitud del motor (ese sigue en <1s, P95=34.8ms).

### 2. Port Scan
```bash
sudo nmap -sS -p 1-100 192.168.0.120
```
**Log real:**
```
10:07:39 | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:97 proto=TCP score=-0.5090 grado=BAJA | LIMIT
10:07:41 | PORT-SCAN  | src=192.168.0.100 dst=192.168.0.120:24 proto=TCP puertos_distintos=20/10s | BLOCK → BLOCKED timeout=300s
```
Primero el Isolation Forest marca un flujo individual como SOSPECHOSO (no llega a τ2 por sí solo — un escaneo manda 1-2 paquetes por puerto, no se ve distinto a tráfico normal liviano). 2 segundos después el heurístico dedicado de port-scan (≥20 puertos distintos/10s) fuerza el BLOCK. Confirma el diseño "heurístico en paralelo al score, no en su reemplazo".

### 3. SYN Flood — el más rápido
```bash
sudo timeout 10 hping3 -S -p 80 -k --flood 192.168.0.120
```
**Log real:**
```
10:36:41 | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.7245 grado=ALTA
  tipo=HTTP_ABUSE byte_ratio=58.26 pkt_rate=135227.3 | BLOCK → BLOCKED timeout=300s
```
Lanzado a las 10:36:40, detectado a las 10:36:41 — **prácticamente instantáneo**. La hipótesis más probable: el puerto 80 tiene un servicio activo (nginx) que responde al handshake TCP, lo que hace que Suricata cierre y registre el flujo mucho más rápido que un flujo UDP/ICMP de una sola dirección sin respuesta. **Este es el mejor candidato si se necesita una demo con detección casi inmediata**, mejor que el UDP flood actualmente documentado en `expo_mark.md`.

### 4. ICMP Flood — el más lento (hallazgo importante)
```bash
sudo timeout 10 hping3 -1 -k --flood 192.168.0.120
```
**Log real:**
```
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:0 proto=ICMP score=-0.7826 grado=ALTA
  tipo=ICMP_FLOOD byte_ratio=1.07 pkt_rate=329621.3 | BLOCK → BLOCKED timeout=300s
```
Lanzado a las 10:40:22, detectado a las 10:45:41 — **309 segundos, poco más de 5 minutos**. Causa confirmada en `/etc/suricata/suricata.yaml`: el servidor responde a los pings (echo-reply), así que el flujo entra en estado **"established"** (timeout=300s) en vez de "new" (timeout=30s, el que usa UDP). No hay heurístico dedicado de respaldo para ICMP (sí existe para HTTP-ABUSE/BRUTE-FORCE/PORT-SCAN, no para ICMP) — **esto es una limitación real a documentar**: un ICMP flood tarda mucho más en detectarse que cualquier otro ataque probado.

### 5. HTTP Abuse
```bash
for i in $(seq 1 150); do curl -s -o /dev/null http://192.168.0.120; done
```
**Log real:**
```
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.6149 grado=ALTA
  tipo=HTTP_ABUSE byte_ratio=0.42 pkt_rate=10000.0 | BLOCK → BLOCKED timeout=300s
```
Detectado ~59-61s después del lanzamiento, 2/2 corridas. Consistente con el timeout TCP "closed" (60s) de Suricata para conexiones que se cierran correctamente (a diferencia de UDP/ICMP que usan el timeout "new"/"established").

### 6. Brute Force SSH — resultado parcial, necesita más tiempo de prueba
```bash
hydra -l m4rk -P wordlist_18_passwords_incorrectas.txt -t 4 -f ssh://192.168.0.120
```
**Log real (corrida limpia):**
```
10:51:42 | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP score=-0.4794 grado=BAJA
  tipo=BAJA_ANOMALIA byte_ratio=0.84 pkt_rate=211.7 | LIMIT
```
18 intentos fallidos en 14 segundos generaron LIMIT (vía score del IF) a los 64s, pero no se confirmó una escalada a BLOCK dentro de la ventana de observación (~3 min) en esta corrida específica, ni se vio disparar la línea de log dedicada `BRUTE-FORCE` (heurístico de conteo, ≥15 intentos/60s) en ninguna de las 2 corridas de hoy — en una corrida anterior sí se confirmó un BLOCK pero por el score del IF directamente (tipo=BRUTE_FORCE_SSH, score=-0.6483), con ~3 minutos de retraso, no por el heurístico de conteo. **Conclusión honesta: el bloqueo de fuerza bruta SSH funciona (ya documentado funcionando en sesiones anteriores con corridas más largas), pero esta campaña no logró aislar limpiamente el disparo del heurístico dedicado — recomendado repetir con más intentos (≥20) y una ventana de observación de al menos 5 minutos antes de la próxima validación.**

---

## Pruebas de falsos positivos

### FP1 — Control: tráfico rápido desde IP en whitelist
```bash
for i in $(seq 1 80); do curl -s -o /dev/null http://192.168.0.120; done   # desde 192.168.0.20
```
Resultado: **PERMIT garantizado** — la whitelist se verifica antes de calcular cualquier score, así que esta IP nunca se evalúa. Confirmado: `ipset test ppi_blocked 192.168.0.20` → `NOT in set`.

### FP2 — Ráfaga rápida desde IP normal (no whitelist)
```bash
for i in $(seq 1 50); do curl -s -o /dev/null http://192.168.0.120; done   # desde 192.168.0.100, SIN hping3
```
Resultado: **BLOCK** (score=-0.6149, tipo=HTTP_ABUSE) a los 61s. **Esto no es realmente un falso positivo** — 50 requests en 1 segundo al mismo endpoint es, objetivamente, un patrón de tasa anómala incluso si la herramienta (`curl`) no es maliciosa. El sistema reaccionó correctamente al *patrón*, no a la *herramienta*.

### FP3 — Una sola conexión legítima, sin ráfaga
```bash
curl -s -o /dev/null -w 'HTTP %{http_code} en %{time_total}s\n' http://192.168.0.120   # desde 192.168.0.100
```
Resultado real: `HTTP 200 en 0.001071s` (1.07ms) → **PERMIT**, sin ninguna línea de alerta, IP nunca entra a ipset. Confirmado vía `ipset test` (NOT in set) y silencio total en el log durante >95 segundos de espera.

**Esto matiza la limitación documentada de `pkt_rate`** (CLAUDE.md y `expo_mark.md` la mencionan como riesgo conocido): una sola conexión rápida y aislada en este laboratorio **no** disparó el problema. El riesgo de falso positivo por `pkt_rate` inflado parece requerir una combinación más específica (más paquetes/bytes en una ventana de tiempo aún más corta, o un patrón distinto al de un solo request-response HTTP) — no es tan fácil de reproducir como "cualquier tráfico rápido". Sigue siendo una limitación real y documentada (no se corrigió, por decisión explícita, antes de la defensa), pero su severidad práctica en este escenario de prueba fue menor a lo que el texto original sugería.

---

## RESUMEN FINAL — ¿qué funcionó mejor?

**Para la demo en vivo (necesita ser rápido y confiable):**
1. 🥇 **SYN Flood a puerto 80** (`hping3 -S -p 80 -k --flood`) — detección en ~1 segundo, el más rápido de los 6 por lejos. Mejor opción si el objetivo es minimizar el tiempo de espera en vivo frente al jurado.
2. 🥈 **UDP Flood a puerto 53** (`hping3 --udp -p 53 -k --flood`) — el más probado y documentado (4/4 corridas idénticas), 42-50s de espera, ya integrado en `expo_mark.md` con capturas y evidencia completa.
3. 🥉 **Port Scan** (`nmap -sS -p 1-100`) — único que muestra las DOS capas de detección en una sola corrida (score del IF + heurístico dedicado), buena opción si se quiere explicar la arquitectura híbrida.

**Para argumentar robustez ante el jurado (mostrar que cubre varios tipos de ataque):**
HTTP Abuse y Port Scan confirmaron el diseño de heurísticos en paralelo al modelo. Brute Force SSH necesita una repetición más larga antes de usarse como evidencia en vivo — no se descarta, simplemente no se confirmó limpiamente hoy.

**Hallazgo más importante de toda la campaña:**
**El tiempo de detección varía enormemente según el protocolo** (1s para SYN flood vs 309s para ICMP flood) — no por una falla del motor (que siempre reacciona en <1s una vez que Suricata entrega el flujo), sino por los `flow-timeouts` de Suricata, que son distintos según el protocolo y si el destino responde o no. **Esto debería documentarse como limitación/hallazgo técnico explícito**, y es información valiosa para decidir qué ataque usar según cuánto tiempo se tenga disponible en la demo.

**Sobre falsos positivos:** la whitelist funciona perfectamente (control FP1). Una ráfaga rápida de muchas conexiones SÍ se bloquea — correctamente, porque es un patrón objetivamente sospechoso (FP2). Una sola conexión rápida aislada NO se bloquea (FP3) — el riesgo conocido de `pkt_rate` no se reprodujo con tráfico verdaderamente normal en esta campaña, aunque sigue siendo una limitación documentada y no corregida por decisión deliberada.
