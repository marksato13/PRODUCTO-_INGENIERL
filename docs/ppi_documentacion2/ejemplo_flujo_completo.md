# Guion de Demo — Sustentación PPI
**Rubén Mark Salazar Tocas · PPI UPeU 2026**
**Verificado en vivo 2026-06-23**

> **Formato:** *cursiva* = lo que digo en voz alta · `código` = lo que ejecuto · 📸 = tomar captura

---

## Todo lo que el sistema puede demostrar

| # | Capacidad | Cómo se activa | Dónde se ve | Tiempo |
|---|---|---|---|---|
| 1 | Captura de tráfico en tiempo real | Suricata corre siempre | `tail -f eve.json` en sensor | continuo |
| 2 | Score Isolation Forest por flujo | Cualquier flujo no-whitelist | `motor_decision.log` → `score=-0.XXXX` | continuo |
| 3 | Decisión PERMIT (tráfico normal) | curl desde Desktop | log: sin entrada (whitelist skip) | inmediato |
| 4 | Decisión LIMIT (sospechoso) | hping3 primer flujo | log: `SOSPECHOSO … LIMIT` | ~30s |
| 5 | Decisión BLOCK (anomalía IF) | flujo score ≤ τ2 | log: `ANOMALÍA … BLOCK` | ~30s |
| 6 | Heurístico HTTP-ABUSE | >100 req/30s desde hping3 | log: `HTTP-ABUSE … BLOCK → BLOCKED` | ~35s |
| 7 | Heurístico Brute Force SSH | >15 intentos SSH/60s con hydra | log: `ANOMALÍA … BRUTE_FORCE_SSH BLOCK` | 60s |
| 8 | Bloqueo real en servidor (ipset) | Automático tras BLOCK | `sudo ipset list ppi_blocked` en 192.168.0.120 | tras BLOCK |
| 9 | LIMIT real en servidor (hashlimit) | Automático tras LIMIT | `sudo ipset list ppi_limited` en 192.168.0.120 | tras LIMIT |
| 10 | Bloqueo progresivo #1→#2→#3 | Reincidir varias veces | `block_counts.json` + timeout en ipset | por corrida |
| 11 | Bloqueo permanente (timeout=0) | Tercer bloqueo de misma IP | `ipset list` sin timeout | tras 3er BLOCK |
| 12 | Telegram — alerta al operador | Automático en cada BLOCK/LIMIT | Celular del operador | tras detección |
| 13 | Alerta TENDENCIA (pre-aviso) | score_medio_10flows < −0.35 | log: `TENDENCIA … AVISO` + Telegram 👀 | variable |
| 14 | Whitelist — nunca bloquear | curl desde Desktop 192.168.0.20 | `ipset test ppi_blocked 192.168.0.20` → NOT in set | inmediato |
| 15 | Control manual enforce.sh | `enforce.sh <ip> BLOCK\|LIMIT\|UNBLOCK` | ipset en servidor cambia al instante | inmediato |
| 16 | Predictor XGBoost — ALERTA-PREDICTIVA | Automático tras BLOCK (ciclo 10s) | `predictor.log` → `P=XX%` | 10s tras BLOCK |
| 17 | Dashboard web en tiempo real | Abrir navegador :8080 | Browser → stats flows/anomalías/latencia | continuo |
| 18 | Estadísticas del motor | Cada 500 flujos | log: `Estadísticas flows=N latencia=Xms` | cada ~18s |
| 19 | Latencia del pipeline | Verificar metricas | `cat latencia_pipeline.txt` → P95=34.7ms | inmediato |
| 20 | Reentrenamiento IF automático | Mostrar crontab | `crontab -l` → domingos 02:00 | inmediato |
| 21 | Reentrenamiento XGBoost automático | Mostrar crontab | `crontab -l` → diario 03:00 | inmediato |
| 22 | Anti-regresión en reentrenamiento | Mostrar metricas F5 | `metricas_f5_xgboost.txt` → AUC antes/después | inmediato |
| 23 | Hot-reload de modelos | Motor detecta cambio en .pkl | log: `Modelo recargado (hot-reload)` | automático |
| 24 | AUC Isolation Forest = 0.8998 | Mostrar métricas | `cat metricas_offline.txt` | inmediato |
| 25 | Precision 99.54% / Recall 99.40% | Mostrar métricas | `cat metricas_offline.txt` | inmediato |
| 26 | AUC XGBoost v2 = 0.9992 | Mostrar métricas | `cat metricas_predictor_v2.txt` | inmediato |
| 27 | FPR = 0.0% en datos nuevos (CA-16) | Mostrar resultado | `RESULTADOS_VALIDACION.md` → 119 flujos | inmediato |
| 28 | 16/16 criterios PASS | `run_all.sh` | Terminal → 16 líneas PASS | ~2 min |
| 29 | 40 corridas F6 en CSV | Mostrar archivo | `head resultados_f6_completo.csv` | inmediato |
| 30 | Gráficas del modelo (7 PNG) | Abrir imágenes | `graficas_f6/` → AUC, ROC, distribución | inmediato |

---

## Qué puede demostrar según el tiempo disponible

| ⏱ Tiempo | Plan | Capacidades que muestra |
|---|---|---|
| **5 min** | MÍNIMO | 2, 4, 5, 6, 8, 24, 28 |
| **10 min** | **ESTÁNDAR** ← recomendado | 2, 4, 5, 6, 7, 8, 9, 12, 14, 16, 24, 25, 26, 27, 28 |
| **15 min** | COMPLETO | todas las anteriores + 10, 11, 15, 17, 18, 19, 20, 21, 22 |

---

---

# GUION — PLAN ESTÁNDAR (10 minutos)

---

## [0:00–0:30] Apertura y verificación del sistema

*"Voy a demostrar el sistema funcionando en tiempo real. Tenemos tres máquinas: el sensor con Suricata en 192.168.0.110 que captura el tráfico, el servidor nginx en 192.168.0.120 que es el objetivo, y Kali Linux en 192.168.0.100 desde donde lanzaré los ataques. Primero verifico que todo está activo."*

**Ejecutar desde Desktop:**
```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
```
**Aparece:**
```
active
active
active
active
```
*"Cuatro servicios activos: Suricata capturando, motor de decisión, predictor XGBoost y dashboard web."*

📸 **CAPTURA — los 4 `active`** ← muestra capacidades 1, 2, 16, 17

---

## [0:30–1:00] Abrir monitoreo

*"Abro dos terminales para ver el sistema en vivo."*

**Terminal 1:**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
```
*"Acá veo cada decisión del motor: el score del Isolation Forest y si permite, limita o bloquea el flujo."*

**Terminal 2:**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```
*"Acá veo el predictor XGBoost — evalúa el historial de cada IP y alerta si predice que va a reincidir."*

📸 **CAPTURA — las 2 terminales vacías y limpias** ← confirma sistema en cero

---

## [1:00–4:30] Escenario 1 — HTTP Flood (hping3) → muestra capacidades 2, 4, 5, 6, 8, 12, 16

*"Lanzo el primer ataque: un flood de paquetes SYN/HTTP hacia el servidor nginx en el puerto 80."*

**En la VM Kali (abrir terminal en Kali):**
```bash
sudo hping3 -S -p 80 -i u5000 192.168.0.120
```
*"200 paquetes por segundo hacia el servidor. Suricata los captura, el motor los analiza con el Isolation Forest."*

📸 **CAPTURA — hping3 corriendo** ← capacidad 1 (captura en tiempo real)

---

*"Miren la Terminal 1. En segundos aparecen las primeras detecciones."*

**[~30s — Terminal 1 muestra:]**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
  score=-0.4654 grado=BAJA tipo=BAJA_ANOMALIA
  byte_ratio=60.00 pkt_rate=1000.0 | LIMIT
```
*"Primer flujo detectado. Score −0.4654 — está entre mis dos umbrales τ1=−0.4459 y τ2=−0.6027, zona SOSPECHOSA. El sistema aplica LIMIT: le limita el ancho de banda a 100 paquetes por segundo en el servidor."*

← muestra capacidades 2, 4, 9

---

**[~35s — Terminal 1 muestra:]**
```
WARNING | HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80
  requests=100/30s | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 35 segundos el detector heurístico HTTP-ABUSE contó 100 requests de esa IP en 30 segundos. Supera el umbral — escala a BLOCK. El motor hace SSH al servidor y agrega la IP al ipset con timeout de 5 minutos."*

📸 **CAPTURA — la línea HTTP-ABUSE BLOCK en Terminal 1** ← capacidades 5, 6, 12

---

*"Verifico el bloqueo directamente en el servidor."*

**Ejecutar desde Desktop:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```
**Aparece:**
```
Members:
192.168.0.100 timeout 293
```
*"192.168.0.100 está en el set con 293 segundos restantes. La regla iptables hace DROP a todo paquete de esa IP. El atacante está cortado."*

📸 **CAPTURA — ipset list con IP y timeout** ← capacidad 8

---

**[Terminal 2 muestra — predictor reacciona:]**
```
WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```
*"En Terminal 2 el predictor XGBoost calculó P=77%: 77% de probabilidad de que esa IP genere otro bloqueo. El XGBoost no analiza el flujo actual — predice comportamiento futuro usando 9 features de historial."*

📸 **CAPTURA — ALERTA-PREDICTIVA P=XX% en Terminal 2** ← capacidad 16

**Parar el ataque — en Kali: Ctrl+C**

---

## [4:30–7:30] Escenario 2 — Brute Force SSH (hydra) → muestra capacidades 2, 4, 5, 7, 8, 12

*"Segundo ataque: fuerza bruta sobre SSH. Este es más interesante porque un intento de login SSH individual se parece al SSH legítimo en las features — el Isolation Forest solo ve flujos. Aquí entra una segunda capa de detección: el heurístico que cuenta intentos acumulados."*

**Desde Desktop — desbloquear Kali:**
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

**En la VM Kali:**
```bash
hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4
```
*"Hydra prueba contraseñas del diccionario con 4 hilos en paralelo."*

📸 **CAPTURA — hydra corriendo**

---

**[~30s — Terminal 1 muestra LIMIT:]**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.4832 tipo=BAJA_ANOMALIA | LIMIT
```
*"El Isolation Forest detecta algo sospechoso — score intermedio — aplica LIMIT."*

**[~60s — Terminal 1 muestra BLOCK:]**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.6228 tipo=BRUTE_FORCE_SSH | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 60 segundos exactos el heurístico BF-SSH contó 15 intentos de autenticación desde esa IP en la ventana de 60 segundos. Tipo BRUTE_FORCE_SSH — bloqueado. El lead time de este ataque es exactamente 60 segundos: el tiempo de la ventana del heurístico."*

📸 **CAPTURA — BRUTE_FORCE_SSH BLOCK en Terminal 1** ← capacidades 7, 5, 8

---

## [7:30–8:00] Whitelist — tráfico legítimo intacto → muestra capacidad 14, 27

*"Demuestro que el sistema no bloquea tráfico legítimo. Este Desktop está en la whitelist."*

**Ejecutar desde Desktop:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```
**Aparece:**
```
192.168.0.20 is NOT in set ppi_blocked.
```
*"Nunca aparece bloqueado. En la validación formal generé 119 flujos nuevos de tráfico normal — tasa de falsos positivos exactamente 0.0%."*

---

## [8:00–10:00] Validación formal — 16/16 PASS → muestra capacidades 24–28

*"Para cerrar demuestro que el sistema pasa todos los criterios de aceptación del PPI de manera automatizada."*

**Ejecutar desde Desktop:**
```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```
*"Tres resultados clave:"*
*"CA-02: AUC Isolation Forest = 0.8998 — supera el mínimo de 0.85."*
*"CA-09: Latencia P95 = 34.7ms — 14 veces más rápido que el límite de 500ms."*
*"CA-16: FPR en 119 flujos nuevos = 0.0% — el sistema no bloqueó ningún flujo legítimo."*

📸 **CAPTURA — 16/16 PASS en pantalla** ← capacidades 24–28

*"16 de 16 criterios PASS. El sistema detecta, bloquea, aprende y no interrumpe el tráfico legítimo."*

---

---

# ESCENARIOS ADICIONALES — si el jurado pregunta o hay tiempo

---

## Bloqueo progresivo y permanente (capacidades 10, 11) — 2 min

*"Si la misma IP reincide, el bloqueo escala automáticamente."*

```bash
# Ver el contador actual de bloqueos
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/block_counts.json"
```
*"Primer bloqueo: 5 minutos. Segundo: 30 minutos. Tercero en adelante: permanente — timeout=0 en ipset significa sin expiración."*

```bash
# Verificar bloqueo permanente (si ya ocurrió):
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
# IP sin timeout = PERMANENTE
```

---

## Control manual enforce.sh (capacidad 15) — 1 min

*"El operador puede intervenir manualmente en cualquier momento."*

```bash
# Desde el sensor:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 120
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 LIMIT 300
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```
*"BLOCK, LIMIT o UNBLOCK con timeout configurable. Se aplica en el servidor vía SSH al instante."*

---

## Dashboard web (capacidad 17) — 30 seg

*"El sistema tiene un dashboard web con estadísticas en tiempo real."*

Abrir en navegador: `http://192.168.0.110:8080`

*"Muestra flows por segundo, anomalías, IPs bloqueadas activas y latencia del pipeline."*

---

## Autoaprendizaje F5 (capacidades 20, 21, 22, 23) — 1 min

*"El sistema se reentrena con los datos que genera el propio motor."*

```bash
ssh m4rk@192.168.0.110 "crontab -l"
# domingo 02:00 → IF  |  diario 03:00 → XGBoost

ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
# AUC antes vs después de cada reentrenamiento
```
*"Si el modelo nuevo tiene AUC menor al anterior, no se reemplaza — mecanismo anti-regresión. El motor detecta el nuevo archivo .pkl automáticamente y recarga sin reiniciar el servicio."*

---

---

# REFERENCIA RÁPIDA — MÉTRICAS PARA RESPONDER AL JURADO

| Si preguntan... | La respuesta es |
|---|---|
| ¿El modelo tiene sobreajuste? | AUC=0.8998 en datos de PRUEBA (no entrenamiento) — FPR=0% en sesión nueva |
| ¿Cuánto tarda en detectar? | HTTP Flood: ~35s · BF-SSH: 60s exactos |
| ¿Qué pasa si hay falsos positivos? | Whitelist protege la infraestructura; FPR=0.0% en 119 flujos nuevos |
| ¿Por qué τ1=−0.4459? | Maximiza índice de Youden: TPR=99.40%, FPR=20.47% — mejor equilibrio |
| ¿Por qué FPR=20% en τ1 y no bajar? | Bajar FPR a 5% haría escapar SYN floods con score≈−0.49 |
| ¿El XGBoost no tiene leakage? | v2 eliminó el score IF como feature — AUC pasó de 1.0000 (artificial) a 0.9992 real |
| ¿Qué feature es más importante en XGBoost? | `block_count_60s` (24.37%) — comportamiento, no métrica del modelo |
| ¿La latencia cumple? | P95=34.7ms — el requisito era <500ms, cumple 14× |
| ¿Cuántos datos de entrenamiento? | 53,708 flujos normales (80%), 13,427 holdout (20%) |
| ¿Qué métricas tiene el IF? | AUC=0.8998, Precision=99.54%, Recall=99.40%, F1=0.9947 |

---

# DOCUMENTACIÓN DETALLADA — Comandos y resultados verificados

## PASO 0 — Estado limpio garantizado (HACER SIEMPRE ANTES DE LA DEMO)

> Los pasos **0A** se ejecutan **directamente en la VM Kali**.  
> Los pasos **0B al 0G** se ejecutan desde **Desktop (192.168.0.20)**.

---

### 0A — Kali: verificar y limpiar procesos de ataque
> 🖥️ **Ejecutar directamente en la VM Kali** (abrir terminal en la VM)

**Verificar si hay algún ataque corriendo:**
```bash
ps aux | grep -E 'hping3|hydra|nmap|nikto|siege' | grep -v grep || echo KALI_LIMPIA
```

**Resultado esperado (sin ataque):**
```
KALI_LIMPIA
```

**Resultado real verificado 2026-06-23** (con hping3 activo):
```
root  1308  sudo hping3 -S -p 80 -i u5000 192.168.0.120
root  1318  hping3 -S -p 80 -i u5000 192.168.0.120
```

**Si hay procesos activos — matarlos (desde la misma VM Kali):**
```bash
sudo pkill -9 hping3
sudo pkill -9 hydra
sudo pkill -9 nmap
sleep 2
ps aux | grep -E 'hping3|hydra|nmap' | grep -v grep || echo KALI_LIMPIA
```

**Resultado verificado 2026-06-23:**
```
KALI_LIMPIA
```

> ⚠️ **Esperar 90 segundos** después de matar cualquier ataque antes de continuar.  
> Suricata tarda ~60s en vaciar los flows residuales. Si reinicias el motor antes,  
> arrancará con backlog y generará alertas falsas.

---

### 0B — Vaciar bloqueos del servidor (ipset en cero)

```bash
ssh m4rk@192.168.0.120 "sudo ipset flush ppi_blocked && sudo ipset flush ppi_limited && echo IPSETS_VACIOS"
```
**Resultado verificado 2026-06-23:**
```
IPSETS_VACIOS
```

Verificar que está realmente vacío:
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 'Number of entries'"
```
**Resultado verificado:**
```
Number of entries: 0
```

---

### 0C — Resetear historial de bloqueos del motor

```bash
ssh m4rk@192.168.0.110 "echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json && cat /home/m4rk/ppi-surikata-producto/results/block_counts.json"
```
**Resultado verificado 2026-06-23:**
```
{}
```

---

### 0D — Reiniciar motor y predictor (limpiar memoria interna)

> ⚠️ Ejecutar este paso SOLO DESPUÉS de que el paso 0A confirmó `KALI_LIMPIA` y esperaste 90 segundos.
> Si hay flows residuales en eve.json el motor los procesa como ataque activo.

```bash
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service ppi-predictor.service && echo REINICIADOS"
sleep 6
ssh m4rk@192.168.0.110 "systemctl is-active ppi-motor.service ppi-predictor.service"
```
**Resultado verificado 2026-06-23** (ejecutado 90s después de matar hping3):
```
REINICIADOS
active
active
```

---

### 0E — Confirmar que los 4 servicios están activos

```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
```
**Resultado verificado 2026-06-23:**
```
active
active
active
active
```

📸 **CAPTURA aquí** — los 4 `active` en pantalla

---

### 0F — Verificar que el log del motor arrancó limpio

```bash
ssh m4rk@192.168.0.110 "tail -5 /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
```
**Resultado verificado 2026-06-23** (arranque limpio, sin ataques activos):
```
INFO | Motor de decisión PPI — iniciando
INFO | Modelo cargado | umbral_base=-0.5742 | τ1=-0.4459 | τ2=-0.6027
INFO | Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=-0.4459 τ2=-0.6027
INFO | Block counts cargados: 0 IPs en historial
INFO | Monitoreando /var/log/suricata/eve.json ...
INFO | Brute Force SSH : ventana=60s umbral_limit=5 umbral_block=15
INFO | HTTP Abuse      : ventana=30s umbral_limit=50 umbral_block=100
```

> **Si ves WARNING o BLOCK inmediatamente:** el motor arrancó con backlog de Suricata.
> Solución: volver al paso 0A, verificar que Kali está limpia, esperar 90s y repetir 0D.

> **Si ves `Block counts cargados: N IPs`** (N > 0): limpiar block_counts antes de reiniciar:
> ```bash
> ssh m4rk@192.168.0.110 "echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json"
> ```
> Luego repetir el paso 0D.

---

### 0G — Abrir terminales de monitoreo (dejarlas visibles durante toda la demo)

```bash
# Terminal 1 — motor de decisión (la más importante)
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# Terminal 2 — predictor XGBoost
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```

📸 **CAPTURA aquí** — las 2 terminales abiertas con el arranque limpio del motor

---

> ✅ **Sistema listo.** Kali sin procesos, ipsets vacíos, block_counts={}, motor recién arrancado.

---

---

## ESCENARIO 1 — Ataque HTTP / SYN Flood desde Kali (hping3)

### Qué demuestra
Que el sistema detecta tráfico volumétrico anómalo, escala de LIMIT a BLOCK, y ejecuta el bloqueo real en el servidor — todo automáticamente.

### Comando
> 🖥️ **Ejecutar directamente en la VM Kali:**
```bash
sudo hping3 -S -p 80 -i u5000 192.168.0.120
```
> Dejar corriendo — no cerrar la terminal.

### Lo que aparece en `motor_decision.log` (verificado en vivo 2026-06-23)

**Primer flujo detectado — LIMIT (score entre τ1 y τ2):**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
  score=-0.4654 grado=BAJA tipo=BAJA_ANOMALIA
  byte_ratio=60.00 pkt_rate=1000.0 | LIMIT
```
*"El primer flujo tiene un score de −0.4654. Mis umbrales son τ1=−0.4459 y τ2=−0.6027. El score cae entre los dos, así que el sistema lo clasifica como SOSPECHOSO y aplica LIMIT: limita a esa IP a 100 paquetes por segundo."*

**Cuando acumula 100 requests en 30 segundos — BLOCK:**
```
WARNING | HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
  requests=100/30s | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los pocos segundos, el detector heurístico HTTP-ABUSE cuenta que esa IP hizo más de 100 requests en 30 segundos. El sistema escala a BLOCK: agrega la IP al ipset del servidor con timeout de 5 minutos."*

### Verificar el bloqueo en el servidor (ejecutar en ese momento)
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```
**Salida real:**
```
Members:
192.168.0.100 timeout 293
```
*"Aquí está la confirmación: 192.168.0.100 bloqueada en el servidor con 293 segundos restantes. Todo el tráfico de esa IP cae en DROP por la regla iptables."*

### Bloqueo progresivo (si se repite el ataque)
```
Bloqueo #1 → timeout=300s    (5 minutos)
Bloqueo #2 → timeout=1800s   (30 minutos)
Bloqueo #3 → timeout=0       (PERMANENTE)
```
*"Si la misma IP reincide, el sistema la bloquea progresivamente: 5 minutos, luego 30 minutos, y a la tercera vez el bloqueo es permanente."*

### Parar el ataque
> 🖥️ **En la VM Kali:** presionar `Ctrl+C` en la terminal donde corre hping3, o:
```bash
sudo pkill -9 hping3
```

---

---

## ESCENARIO 2 — Brute Force SSH desde Kali (hydra)

### Qué demuestra
Que el sistema tiene una segunda capa de detección heurística — no solo el Isolation Forest. Un ataque de fuerza bruta SSH se parece al SSH legítimo en las features de flujo, pero el heurístico lo detecta contando intentos.

### Preparar (desde Desktop — desbloquear Kali)
```bash
# Desde Desktop (192.168.0.20):
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

### Comando
> 🖥️ **Ejecutar directamente en la VM Kali:**
```bash
hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4
```

### Lo que aparece en `motor_decision.log`

**Primeros flujos — LIMIT (IF detecta, score intermedio):**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
  score=-0.4832 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT
```
*"Los primeros intentos de login generan un score de −0.4832, entre los dos umbrales: LIMIT."*

**A los 60 segundos — BLOCK por heurístico BF-SSH:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
  score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 60 segundos el contador BF-SSH llega a 15 intentos desde esa IP. Supera el umbral y el sistema bloquea. El tipo es BRUTE_FORCE_SSH, que fue identificado por el heurístico, no solo por el score."*

### Por qué existe el heurístico BF-SSH
*"Un intento SSH fallido individual se parece al SSH legítimo: mismas features, duraciones similares. El Isolation Forest solo ve un flujo a la vez. El heurístico cuenta el comportamiento acumulado en una ventana de 60 segundos, que es lo que delata al atacante."*

---

---

## ESCENARIO 3 — Predictor XGBoost ve el comportamiento (F4)

### Qué demuestra
Que hay una segunda inteligencia corriendo en paralelo: el XGBoost evalúa el historial de cada IP y predice si va a volver a atacar — antes de que lo haga.

### Qué ver en `predictor.log` (aparece automáticamente después de los BLOCKs)
```
WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```

*"P=77% significa que el predictor estima un 77% de probabilidad de que esa IP genere otro evento de bloqueo en los próximos ciclos. Las features más importantes son cuántos bloqueos acumuló en los últimos 60 segundos — eso no puede fingirlo tráfico legítimo."*

### Diferencia clave entre IF y XGBoost
| | Isolation Forest (F2+F3) | XGBoost Predictor (F4) |
|---|---|---|
| Pregunta | ¿Este flujo es anómalo ahora? | ¿Esta IP va a atacar de nuevo? |
| Entrada | 14 features del flujo actual | 9 features de comportamiento histórico |
| Salida | PERMIT / LIMIT / BLOCK | Probabilidad P(%) de reincidencia |
| Reacción | Inmediata (por flujo) | Cada 10 segundos |

---

---

## ESCENARIO 4 — Tráfico normal no se bloquea (FPR = 0%)

### Qué demuestra
Que el sistema no interrumpe el tráfico legítimo. La whitelist protege las IPs de la infraestructura.

### Generar tráfico normal desde este Desktop
```bash
for i in $(seq 1 20); do curl -s http://192.168.0.120/ -o /dev/null; sleep 1; done
```

### Verificar que Desktop no está bloqueado
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```
**Salida:**
```
192.168.0.20 is NOT in set ppi_blocked.
```

*"192.168.0.20, que es este Desktop, está en la whitelist. El motor la descarta antes de calcular el score. Nunca aparecerá en el ipset de bloqueados."*

*"En la validación formal, generé 119 flujos de tráfico normal en una sesión completamente nueva — diferente a la de entrenamiento — y la tasa de falsos positivos fue exactamente 0.0%."*

---

---

## ESCENARIO 5 — Autoaprendizaje F5 (mostrar evidencia, no ejecutar en vivo)

### Qué demuestra
Que el sistema mejora con los datos que genera el mismo motor. No necesita re-entrenamiento manual.

```bash
# Ver el crontab activo en el sensor
ssh m4rk@192.168.0.110 "crontab -l"
# Resultado: IF domingos 02:00 / XGBoost diario 03:00

# Ver historial de reentrenamientos XGBoost
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
```

*"El XGBoost se reentrena con los eventos LIMIT y BLOCK del motor_decision.log. Cada reentrenamiento verifica que el AUC nuevo sea mayor o igual al anterior — si el modelo nuevo es peor, no se reemplaza. A eso lo llamo anti-regresión."*

*"El motor detecta el modelo nuevo automáticamente revisando la fecha de modificación del archivo pkl en cada ciclo de 10 segundos, sin necesidad de reiniciar el servicio."*

---

---

## ESCENARIO 6 — Validación formal: 16/16 PASS

### Qué demuestra
Que el sistema cumple todos los criterios de aceptación del PPI, medidos automáticamente.

```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```

*"Esta suite verifica 16 criterios: desde que el AUC supera 0.85, hasta que la latencia P95 está bajo 500ms, pasando por que las IPs whitelisted nunca se bloquean."*

**Tres resultados clave:**
- **CA-02:** AUC Isolation Forest = **0.8998** (mínimo 0.85 ✅)
- **CA-09:** Latencia P95 = **34.768ms** (máximo 500ms ✅ — 14× más rápido que el límite)
- **CA-16:** FPR en 119 flujos nuevos = **0.0%** ✅

---

---

## Métricas finales del sistema

| Modelo / Componente | Métrica | Valor |
|---|---|---|
| Isolation Forest | AUC-ROC | **0.8998** |
| IF | Precision / Recall en τ1 | **99.54% / 99.40%** |
| IF | τ1 — límite PERMIT/LIMIT | **−0.4459** |
| IF | τ2 — límite LIMIT/BLOCK | **−0.6027** |
| Motor | Latencia P95 del pipeline | **34.768ms** |
| XGBoost v2 | AUC-ROC | **0.9992** |
| XGBoost v2 | Errores totales (de 12,488) | **14** (7 FP + 7 FN) |
| Sistema | Lead time HTTP Flood | **~5s** (heurístico 100req/30s) |
| Sistema | Lead time BF-SSH | **60s** (heurístico 15intentos/60s) |
| Sistema | Disponibilidad (40 corridas F6) | **100%** |
| Sistema | Interrupción tráfico legítimo | **0%** |
| CA-16 | FPR en datos nuevos | **0.0%** (119 flujos) |
| Validación | Criterios PASS | **16/16** |

---

## Capturas a tomar durante la demo

| # | Qué | Cuándo |
|---|---|---|
| 1 | 4 `active` en terminal | Preparación |
| 2 | hping3 corriendo con paquetes | Al lanzar el ataque |
| 3 | `SOSPECHOSO ... LIMIT` en motor log | ~5s después de hping3 |
| 4 | `HTTP-ABUSE ... BLOCK → BLOCKED` en motor log | ~35s después |
| 5 | `ipset list ppi_blocked` con timeout | Inmediatamente después del BLOCK |
| 6 | `ALERTA-PREDICTIVA P=XX%` en predictor log | Segundos después del BLOCK |
| 7 | Telegram en el celular | Al recibirlo |
| 8 | `BRUTE_FORCE_SSH ... BLOCK` en motor log | Durante el hydra |
| 9 | `ipset test 192.168.0.20 NOT in set` | Escenario normal |
| 10 | `run_all.sh` con 16/16 PASS | Validación final |
