# Guion de Demo — Sustentación PPI
**Rubén Mark Salazar Tocas · PPI UPeU 2026**  
**Verificado en vivo 2026-06-23**

> **Formato:** *cursiva* = lo que digo en voz alta · `código` = lo que ejecuto en pantalla

---

## Tiempo disponible → elige tu plan

| ⏱ Tiempo | Plan | Escenarios |
|---|---|---|
| 5 min | MÍNIMO | Paso 0 → Escenario 1 → Métricas |
| 10 min | **ESTÁNDAR** ← recomendado | Paso 0 → E1 → E2 → 16/16 PASS |
| 15 min | COMPLETO | Paso 0 → E1 → E2 → Predictor → Normal → 16/16 |

---

---

# GUION — PLAN ESTÁNDAR (10 minutos)

---

## [0:00] Apertura — 30 segundos

*"Voy a demostrar el sistema funcionando en tiempo real. Tenemos tres máquinas: el sensor con Suricata en 192.168.0.110 que captura el tráfico, el servidor nginx en 192.168.0.120 que es el objetivo, y Kali Linux en 192.168.0.100 desde donde lanzaré los ataques."*

*"Primero verifico que todo está activo."*

**Mostrar en Desktop:**
```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
```
**Lo que aparece:**
```
active
active
active
active
```
*"Cuatro servicios activos. El sistema está listo."*

📸 **CAPTURA — los 4 `active`**

---

## [0:30] Abrir monitoreo — 30 segundos

*"Abro dos terminales para ver el sistema en vivo mientras corre el ataque."*

**Terminal 1 (dejar abierta y visible):**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
```
*"Esta terminal muestra cada flujo que analiza el motor: el score del modelo y si lo permite, lo limita o lo bloquea."*

**Terminal 2 (dejar abierta y visible):**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```
*"Esta es la capa predictiva — el XGBoost que anticipa si una IP va a reincidir."*

---

## [1:00] Escenario 1 — Ataque HTTP Flood — 4 minutos

*"Lanzo el primer ataque: un flood de paquetes SYN hacia el puerto 80 del servidor."*

**En la VM Kali (abrir terminal en Kali y ejecutar):**
```bash
sudo hping3 -S -p 80 -i u5000 192.168.0.120
```
*"Kali está enviando 200 paquetes por segundo al servidor. El sistema los está viendo ahora mismo a través de Suricata."*

📸 **CAPTURA — hping3 corriendo con el contador de paquetes**

---

*"Miren la Terminal 1. En segundos van a ver aparecer las primeras detecciones."*

**[~30s después — aparece en Terminal 1]:**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
  score=-0.4654 tipo=BAJA_ANOMALIA | LIMIT
```
*"Primer flujo detectado. El Isolation Forest le dio un score de −0.4654. Mis umbrales son τ1=−0.4459 y τ2=−0.6027. El score cae entre los dos, así que el sistema aplica LIMIT: limita a esa IP a 100 paquetes por segundo."*

---

**[~35s después — aparece el BLOCK]:**
```
WARNING | HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80
  requests=100/30s | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 35 segundos el detector HTTP-ABUSE contó 100 requests de esa IP en 30 segundos — supera el umbral. El sistema escala a BLOCK: llama al servidor por SSH y agrega la IP al ipset."*

📸 **CAPTURA — la línea HTTP-ABUSE BLOCK → BLOCKED en Terminal 1**

---

*"Verifico que el bloqueo está activo en el servidor."*

**En Desktop:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```
**Lo que aparece:**
```
Members:
192.168.0.100 timeout 293
```
*"Ahí está: 192.168.0.100 bloqueada con 293 segundos restantes. Todo el tráfico de esa IP cae en DROP por la regla iptables del servidor. El atacante está efectivamente cortado."*

📸 **CAPTURA — ipset list con IP y timeout**

*"Si la misma IP reincide, el bloqueo escala: 5 minutos la primera vez, 30 minutos la segunda, permanente la tercera."*

**En Kali — parar el ataque:**
```bash
# Ctrl+C en la terminal de Kali
```

---

## [5:00] Escenario 2 — Brute Force SSH — 3 minutos

*"Segundo ataque: fuerza bruta sobre SSH. Este es más interesante porque el Isolation Forest solo ve un flujo a la vez — un intento de login SSH individual se parece mucho al SSH legítimo."*

**En Desktop — desbloquear Kali primero:**
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

**En la VM Kali:**
```bash
hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4
```
*"Hydra prueba contraseñas del diccionario con 4 hilos en paralelo."*

📸 **CAPTURA — hydra corriendo con los intentos**

---

**[~30s — aparece LIMIT en Terminal 1]:**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.4832 tipo=BAJA_ANOMALIA | LIMIT
```
*"El IF detecta algo sospechoso pero no está seguro — score intermedio, aplica LIMIT."*

**[~60s — aparece BLOCK en Terminal 1]:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.6228 tipo=BRUTE_FORCE_SSH | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 60 segundos el detector heurístico BF-SSH contó 15 intentos de autenticación desde esa IP en una ventana de 60 segundos. Supera el umbral — BLOCK por tipo BRUTE_FORCE_SSH. El lead time es exactamente 60 segundos: el tiempo de la ventana del heurístico."*

📸 **CAPTURA — BRUTE_FORCE_SSH BLOCK en Terminal 1**

*"La clave aquí: el IF solo ve flujos individuales. El heurístico detecta el patrón acumulado — eso es lo que delata al atacante."*

---

## [8:00] Validación formal — 2 minutos

*"Para cerrar muestro que el sistema pasa todos los criterios de aceptación formales del PPI."*

**En Desktop:**
```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```

*"Esta suite verifica 16 criterios automáticamente. Los tres más importantes:"*

*"CA-02: AUC del Isolation Forest = 0.8998 — supera el mínimo de 0.85."*  
*"CA-09: Latencia P95 del pipeline = 34.7 milisegundos — el límite era 500ms, el sistema es 14 veces más rápido."*  
*"CA-16: generé 119 flujos de tráfico normal en una sesión nueva, diferente a la de entrenamiento — tasa de falsos positivos 0.0%."*

📸 **CAPTURA — 16/16 PASS en pantalla**

*"16 de 16 criterios PASS. El sistema funciona, detecta, bloquea y no interrumpe el tráfico legítimo."*

---

---

# ESCENARIOS ADICIONALES (si hay tiempo o el jurado pregunta)

---

## Escenario 3 — Predictor XGBoost (1 min)

*"Mientras ocurrían los ataques, la Terminal 2 registró esto:"*

**Mostrar Terminal 2 (predictor.log):**
```
WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```
*"P=77%: el predictor estimó 77% de probabilidad de que esa IP generara otro bloqueo. El XGBoost no detecta el flujo actual — predice el comportamiento futuro. Usa 9 features de historial, sin el score del IF para evitar data leakage."*

---

## Escenario 4 — Tráfico normal no se bloquea (1 min)

*"El sistema no bloquea tráfico legítimo. Desktop está en la whitelist."*

**En Desktop:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```
**Lo que aparece:**
```
192.168.0.20 is NOT in set ppi_blocked.
```
*"En la validación formal, 119 flujos nuevos de tráfico normal: FPR = 0.0%."*

---

## Escenario 5 — Autoaprendizaje (30 seg, sin ejecutar)

*"El sistema se reentrena solo. El XGBoost se actualiza diariamente a las 3am con los eventos del motor. El IF se reentrena los domingos a las 2am."*

```bash
ssh m4rk@192.168.0.110 "crontab -l"
```
*"Si el modelo nuevo tiene AUC menor al anterior, no se reemplaza — mecanismo anti-regresión."*

---

---

# REFERENCIA RÁPIDA — MÉTRICAS PARA RESPONDER AL JURADO

| Pregunta | Respuesta |
|---|---|
| ¿AUC del IF? | **0.8998** (mínimo requerido 0.85) |
| ¿Precision / Recall? | **99.54% / 99.40%** |
| ¿Cuánto tarda en detectar? | HTTP Flood: **~35s** · BF-SSH: **60s** |
| ¿Latencia del pipeline? | **P95 = 34.7ms** (límite 500ms) |
| ¿AUC del XGBoost? | **0.9992** |
| ¿Errores del XGBoost? | **14** de 12,488 (7 FP + 7 FN) |
| ¿Falsos positivos? | **FPR = 0.0%** en 119 flujos nuevos |
| ¿Criterios de aceptación? | **16/16 PASS** |
| ¿Disponibilidad en F6? | **100%** en 40 corridas |

---

---

# DOCUMENTACIÓN DETALLADA — ESCENARIOS COMPLETOS

> Lo que sigue es la documentación técnica completa de cada escenario con todos los comandos y outputs verificados.

---
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
