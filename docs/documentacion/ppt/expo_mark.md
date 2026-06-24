# Expo Mark — Presentación del Producto
**Slides 8–13 | Menos de 10 minutos**
**Evidencia en vivo verificada: 2026-06-24 01:20**

---

## ESTRUCTURA DE TIEMPO

| # | Parte | Tiempo |
|---|---|---|
| 1 | Slide 8 — ¿Qué hace el producto? | 30 seg |
| 2 | Slide 9 — Arquitectura 4 nodos | 1 min |
| 3 | Slide 10 — Flujo de decisión IF | 1 min |
| 4 | Demo D1–D7 — Ataque en vivo paso a paso | 4 min |
| 5 | Slide 13 — Resultados OE1–OE4 | 2 min |
| 6 | Cierre | 15 seg |
| **TOTAL** | | **~8.5 min** |

---

---

## SLIDE 8 — ¿Qué hace el producto?
**Tiempo: 30 seg**

### Visual
```
SURIKATA — Sistema de Detección y Control Inteligente

  Detecta ataques · Decide en <35ms · Bloquea automáticamente
           sin intervención humana
```

### Lo que dices
> *"Vamos a demostrar que nuestro sistema está funcionando en tiempo real ahora mismo.*
> *El producto hace exactamente tres cosas: detecta tráfico anómalo usando Machine Learning, decide qué hacer en menos de 35 milisegundos, y bloquea automáticamente al atacante sin que ningún humano toque nada.*
> *Para esta demo tenemos tres máquinas activas: el sensor que captura el tráfico de la red, el servidor que es el objetivo de los ataques, y Kali Linux desde donde lanzaré los ataques en vivo."*

---

## SLIDE 9 — Arquitectura General
**Tiempo: 1 min**

### Visual
→ Mostrar la imagen de arquitectura (la que tienes con los 4 nodos y flechas)

### Lo que dices — señalando cada nodo

> *"Cuatro nodos en la misma red. Empiezo por el Sensor — Ubuntu con Suricata corriendo en modo promiscuo en la interfaz ens35. Modo promiscuo significa que captura TODO el tráfico de la red, no solo el dirigido a él. Cada paquete que pasa por el segmento, Suricata lo ve."*

> *"El motor de decisión corre también en el sensor. Toma los flujos que Suricata detecta, extrae 14 características por flujo, y las pasa al Isolation Forest — el modelo de Machine Learning."*

> *"Cuando el modelo decide BLOCK, el motor hace SSH al Servidor — esta máquina de acá — y ejecuta un comando ipset. El kernel del servidor descarta los paquetes del atacante antes de que lleguen a nginx o SSH."*

> *"Dos cosas importantes de esta arquitectura: primero, el sensor y el servidor son máquinas separadas — si el motor falla, el servidor sigue sirviendo. Segundo, Suricata captura en el sensor, no en el servidor — entonces aunque el servidor ya esté bloqueando a Kali, el sensor sigue viendo el tráfico y el motor sigue aprendiendo de él."*

---

## SLIDE 10 — Flujo de Decisión
**Tiempo: 1 min**

### Visual
```
Suricata → eve.json
      ↓ nuevo flujo
¿IP en whitelist? → SÍ → PERMIT (sin cálculo)
      ↓ NO
score = IF.decision_function(14 features)
      ↓
score > −0.4459   →  PERMIT   ✅
−0.6027 < score ≤ −0.4459  →  LIMIT ⚠️  (100 pkt/s)
score ≤ −0.6027   →  BLOCK   🚫  (DROP kernel)
      ↓
BLOCK → SSH → servidor → ipset add timeout [300s / 1800s / ∞]
BLOCK → Telegram 🚨 + predictor.log P=XX%
```

### Lo que dices

> *"El ciclo de decisión funciona así. Suricata genera un evento de flujo en eve.json — el motor lo lee en tiempo real."*

> *"Primero verifica si la IP origen está en la whitelist. El Desktop administrativo siempre está en whitelist — nunca se bloquea. Si no está en whitelist, extrae las 14 características del flujo y el Isolation Forest le asigna un score."*

> *"El score es continuo, entre 0 y −1. Por encima de tau-1 menos 0.4459: PERMIT, tráfico normal. Entre tau-2 y tau-1: SOSPECHOSO, se aplica LIMIT — hashlimit de 100 paquetes por segundo en el servidor. Por debajo de tau-2 menos 0.6027: ANOMALÍA, BLOCK — DROP directo en el kernel."*

> *"Estos dos umbrales no son arbitrarios. Los derivamos matemáticamente de la curva ROC: tau-1 maximiza el índice de Youden — el punto donde TPR menos FPR es máximo. Tau-2 es el punto donde el FPR cae al 2%."*

> *"Si es BLOCK, además del ipset hay un bloqueo progresivo: primer bloqueo 5 minutos, segundo 30 minutos, tercero permanente. Y el predictor XGBoost evalúa si el ataque continuará."*

---

## DEMO — Paso a Paso con Evidencia Real
**Tiempo: 4 min**

---

### PASO 1 — Verificar que el sistema está activo
**[0:00 de la demo]**

### Lo que ejecutas
```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service \
  ppi-predictor.service ppi-dashboard.service"
```

### Lo que aparece en pantalla
```
active
active
active
active
```

### Lo que dices
> *"Verifico los cuatro servicios. Suricata activo — capturando. Motor de decisión activo — escuchando eve.json en tiempo real. Predictor XGBoost activo — evaluando el historial de comportamiento. Dashboard web activo — visible en el navegador en el puerto 8080."*
> *"El sistema lleva corriendo desde el arranque. Todo en verde."*

---

### PASO 2 — Mostrar el sistema en cero
**[0:20 de la demo]**

### Lo que ejecutas
```bash
# Terminal 1 — decisiones del motor en vivo
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# Terminal 2 — predictor XGBoost en vivo
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```

### Lo que aparece en pantalla
```
Terminal 1: sin entradas WARNING — solo INFO de arranque
Terminal 2: sin alertas — solo INFO "Modelo cargado features=10"
```

### Lo que dices
> *"Abro dos terminales para ver el sistema en tiempo real. Terminal 1 es el log del motor — acá veo cada decisión: PERMIT, LIMIT o BLOCK, con el score exacto del Isolation Forest. Terminal 2 es el predictor XGBoost — acá veo la probabilidad de que cada IP continúe atacando."*
> *"Ahora mismo silencio total. Cero anomalías. El sistema está en reposo."*

---

### PASO 3 — Lanzar el ataque HTTP Flood
**[0:40 de la demo] — OE2 empieza acá**

### Lo que ejecutas (desde la VM Kali)
```bash
sudo hping3 -S -p 80 -i u5000 192.168.0.120
```

### Lo que aparece en pantalla
```
HPING 192.168.0.120 (eth0 192.168.0.120): S set, 40 headers + 0 data bytes
len=44 ip=192.168.0.120 ttl=64 DF id=0 sport=80 flags=SA seq=0 win=... rtt=1.4 ms
len=44 ip=192.168.0.120 ...  (paquetes fluyendo...)
```

### Lo que dices
> *"Lanzo el ataque desde Kali. hping3 con flag SYN hacia el puerto 80 del servidor, un paquete cada 5 milisegundos — 200 paquetes por segundo."*
> *"Suricata en el sensor los captura todos. Cada vez que Suricata cierra un flujo TCP, lo escribe en eve.json. El motor lo lee inmediatamente."*
> *"Miren la Terminal 1 — en unos segundos van a empezar a aparecer las detecciones."*

---

### PASO 4 — IF detecta: LIMIT primero
**[~30 seg después del inicio] — OE2 en acción**

### Lo que aparece en Terminal 1
```
01:20:17 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.5045 grado=BAJA tipo=BAJA_ANOMALIA
  byte_ratio=1.97 pkt_rate=3000.0 | LIMIT
```

### Lo que dices
> *"Primer flujo detectado. Score menos 0.5045. Están mirando el Isolation Forest en funcionamiento — ese número es la profundidad promedio de aislamiento del flujo en los 300 árboles del modelo."*
> *"Menos 0.5045 cae entre tau-1 y tau-2 — zona SOSPECHOSA. El motor hace SSH al servidor y agrega la IP 192.168.0.100 al ipset ppi_limited. Desde ese momento, el servidor le aplica hashlimit: máximo 100 paquetes por segundo. Un flood de 200 paquetes queda reducido al 50%."*
> *"Esto es OE2: el Isolation Forest detectando y clasificando la anomalía con un score continuo."*

---

### PASO 5 — IF escala a BLOCK
**[~35 seg después del inicio] — OE2 + OE3**

### Lo que aparece en Terminal 1
```
01:20:21 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6028 grado=ALTA tipo=HTTP_ABUSE
  byte_ratio=120.00 pkt_rate=2000.0 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```

### Lo que dices
> *"Cuatro segundos después: score menos 0.6028. Por debajo de tau-2. Y además el detector heurístico HTTP-ABUSE confirmó más de 100 requests en 30 segundos desde esa IP."*
> *"Decisión: BLOCK. El motor hace SSH al servidor y ejecuta ipset add ppi_blocked 192.168.0.100 timeout 300. 300 segundos — 5 minutos de bloqueo."*
> *"OE3 en funcionamiento: clasificación y control en tiempo real. Desde que Suricata cerró el flujo hasta que la IP está bloqueada en el kernel del servidor: menos de un segundo."*

---

### PASO 6 — Verificar bloqueo real en servidor
**[~40 seg] — OE3 evidencia**

### Lo que ejecutas
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```

### Lo que aparece en pantalla
```
Name: ppi_blocked
Type: hash:ip
Number of entries: 1
Members:
192.168.0.100 timeout 290
```

### Lo que dices
> *"Verifico directamente en el servidor. 192.168.0.100 está en el set ppi_blocked con 290 segundos restantes."*
> *"La regla iptables dice: si el origen está en ppi_blocked, DROP — descartar sin responder. El atacante sigue enviando paquetes, pero el kernel del servidor los tira antes de que lleguen a nginx o al stack TCP. Cero recursos consumidos por el atacante."*
> *"Kali todavía no sabe que está bloqueada — hping3 sigue enviando. Pero Suricata en el sensor sigue viéndolos. Eso alimenta al predictor."*

---

### PASO 7 — Predictor XGBoost evalúa sostenibilidad
**[~50 seg] — OE4**

### Lo que aparece en Terminal 2
```
01:20:20 | INFO    | OK                | src=192.168.0.100 P=0.11%  score=-0.5045 blocks_60s=0
01:20:30 | INFO    | AVISO             | src=192.168.0.100 P=54.65% score=-0.6028 blocks_60s=3
01:20:40 | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=97.45% score=-0.6028 blocks_60s=4
01:21:01 | INFO    | ALERTA-PREDICTIVA | src=192.168.0.100 P=88.93% score=-0.6028 blocks_60s=6
01:21:11 | INFO    | ALERTA-PREDICTIVA | src=192.168.0.100 P=99.69% score=-0.6028 blocks_60s=9
```

### Lo que dices
> *"Terminal 2 — el predictor XGBoost. Cada 10 segundos evalúa el historial de comportamiento de cada IP activa."*

> *"Primer ciclo: P=0.11% — recién empezó el ataque, sin historial de bloqueos. El XGBoost dice 'no hay evidencia de sostenimiento todavía'."*

> *"Segundo ciclo, 10 segundos después: la IP acumuló 3 bloqueos en los últimos 60 segundos. P=54.65% — AVISO. El modelo empieza a detectar el patrón de reincidencia."*

> *"Tercer ciclo: 4 bloqueos acumulados. P=97.45% — ALERTA-PREDICTIVA. 97% de probabilidad de que este ataque sea sostenido y no un evento aislado."*

> *"Esto es OE4: predecir la sostenibilidad del ataque. ¿Para qué sirve? Para el bloqueo progresivo. Si el predictor confirma sostenimiento, el segundo bloqueo de esta IP durará 30 minutos en vez de 5. El tercero será permanente."*

> *"La diferencia con el IF: el IF dice 'este flujo ES anómalo ahora'. El XGBoost dice 'esta IP VA A SEGUIR atacando'. Son preguntas distintas con valor operativo distinto."*

---

### PASO 8 — Whitelist protege al administrador
**[~1:30 de la demo]**

### Lo que ejecutas
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```

### Lo que aparece en pantalla
```
192.168.0.20 is NOT in set ppi_blocked.
```

### Lo que dices
> *"El Desktop — el administrador — nunca fue bloqueado, aunque generó tráfico HTTP y SSH durante todo el ataque."*
> *"Validamos esto formalmente con 119 flujos de tráfico normal nuevos generados en una sesión diferente al entrenamiento: tasa de falsos positivos exactamente 0.0%. El sistema discrimina con precisión."*

---

## SLIDE 13 — Resultados
**Tiempo: 2 min**

### Visual — tabla mapeada a OE

| Objetivo | Evidencia | Métrica |
|---|---|---|
| **OE1** — Capturar tráfico | 47 capturas · 9 escenarios · 13 tipos | 53,708 flujos de entrenamiento |
| **OE2** — Isolation Forest | Score continuo · τ1/τ2 por curva ROC | AUC=0.8998 · Precision=99.54% · Recall=99.40% |
| **OE3** — Motor en tiempo real | LIMIT→BLOCK en <1s · ipset en servidor | Latencia P95=34.8ms · ITL=0% · Disp.=100% |
| **OE4** — Predictor sostenibilidad | P=0% → P=97% en 30 seg de ataque | AUC=0.9991 · 10 features comportamentales |
| **General** | 40 corridas · 4 grupos · 4 ataques distintos | 16/16 criterios de aceptación PASS |

### Lo que dices

> *"Los resultados responden directamente a los cuatro objetivos específicos."*

> *"OE1 cumplido: pipeline completo de captura. 47 corridas de tráfico real organizadas en 9 escenarios — normal, anómalo y mixto — con 53 mil flujos para entrenar el modelo y 13 mil reservados para evaluación."*

> *"OE2 cumplido: el Isolation Forest alcanzó AUC de 0.8998 — el criterio mínimo era 0.85. Precision del 99.54% y Recall del 99.40%. Los umbrales tau-1 y tau-2 se derivaron matemáticamente: tau-1 por índice de Youden, tau-2 fijando el FPR al 2%. Y validamos con datos nuevos: 119 flujos que el modelo nunca vio — tasa de falsos positivos 0.0%."*

> *"OE3 cumplido: el motor clasifica y actúa en tiempo real. Latencia percentil 95 de 34.8 milisegundos — 14 veces más rápido que el límite de 500 milisegundos. Disponibilidad del servidor 100% durante todos los ataques. Cero interrupciones de tráfico legítimo en 40 corridas."*

> *"OE4 cumplido: el predictor XGBoost con AUC de 0.9991. Y acabamos de ver en vivo cómo la probabilidad subió de 0.11% a 97.45% en 30 segundos de ataque real. Predice sostenibilidad para tomar decisiones de bloqueo proporcionales."*

> *"16 de 16 criterios de aceptación definidos antes de las pruebas: todos PASS."*

---

## CIERRE
**Tiempo: 15 seg**

### Lo que dices
> *"El sistema detecta, decide y bloquea. Sin intervención humana. En menos de 35 milisegundos. Muchas gracias."*

> *(Pausa. Mirar al jurado.)*

---

---

## RESPUESTAS RÁPIDAS PARA EL JURADO

### ¿Por qué Isolation Forest y no un modelo supervisado?
> *"Porque no necesitamos ejemplos de ataques para entrenar. El IF aprende solo del tráfico normal. Cualquier desviación estadística significativa es anomalía — aunque sea un ataque que nunca vimos antes. Un modelo supervisado necesitaría etiquetas de ataque, y los ataques nuevos que no tiene en entrenamiento no los detecta."*

### ¿Por qué FPR=20.47% en tau-1?
> *"Si bajamos el FPR a 5%, tau-1 subiría a aproximadamente menos 0.49. El problema: los SYN floods tienen score entre menos 0.49 y menos 0.51 — escaparían de la detección. Preferimos tolerar el 20% de FPR porque la whitelist lo anula operativamente: todas las IPs legítimas del laboratorio están en whitelist y nunca se bloquean. El FPR operativo real fue 0.0%."*

### ¿El XGBoost predice ANTES de que el sistema bloquee?
> *"Predice si el ataque va a CONTINUAR después del primer bloqueo. No predice el ataque futuro desde cero — observa el patrón de bloqueos acumulados de esa IP en los últimos 60 segundos y la velocidad a la que llegan. Con esa información decide si el bloqueo debe ser corto o progresivo hacia permanente."*

### ¿AUC=0.9991 no es sospechosamente alto?
> *"Versión 1 tenía AUC=1.0000 — ese sí era sospechoso porque era data leakage: el score del IF estaba como feature y los labels se derivaban de ese mismo score. Al eliminarlo, el AUC bajó a 0.9991 en datos de test que el modelo nunca vio. Ese 0.9991 es real porque los ataques en laboratorio son consistentes — un UDP flood desde Kali siempre genera el mismo patrón de bloqueos rápidos."*

### ¿Qué pasa si el motor se cae?
> *"Tres capas de protección. Primero: los bloqueos ya aplicados en ipset persisten en el servidor aunque el motor se caiga — el kernel sigue bloqueando. Segundo: el motor corre como servicio systemd con restart automático. Tercero: el sensor y el servidor son máquinas separadas — un fallo del motor no afecta la disponibilidad del servicio que protege."*

### ¿Funciona con ataques que el modelo no conoce?
> *"El IF es one-class: aprende qué es 'normal' y detecta cualquier desviación. No necesita conocer el ataque específico. En la validación CA-16, usamos 119 flujos de una sesión nueva que el modelo nunca vio — todos fueron PERMIT. Si hubieran sido anómalos, el IF los habría detectado por su desviación del patrón normal, sin importar el tipo de ataque."*

### ¿Por qué la latencia es tan baja?
> *"El Isolation Forest es O(1) en inferencia — evalúa un flujo en un árbol de profundidad logarítmica. Con 300 árboles y 14 features, el cálculo del score toma microsegundos. Los 34.8 milisegundos de P95 incluyen lectura de eve.json, extracción de features, normalización con el scaler, inferencia del IF, y escritura del log. La mayor parte de ese tiempo es I/O, no el modelo en sí."*

---

## EVIDENCIA REAL — Capturas 2026-06-24 01:20

### motor_decision.log — OE2 y OE3
```
01:20:17 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.5045 byte_ratio=1.97 pkt_rate=3000.0 | LIMIT

01:20:21 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6028 tipo=HTTP_ABUSE | BLOCK → BLOCKED timeout=300s
```

### predictor.log — OE4
```
01:20:20 | INFO    | OK                | P=0.11%  blocks_60s=0   ← sin historial
01:20:30 | INFO    | AVISO             | P=54.65% blocks_60s=3   ← acumulando
01:20:40 | WARNING | ALERTA-PREDICTIVA | P=97.45% blocks_60s=4   ← sostenido
01:21:11 | INFO    | ALERTA-PREDICTIVA | P=99.69% blocks_60s=9   ← confirmado
```

### ipset en servidor — OE3
```
Members:
192.168.0.100 timeout 290   ← bloqueado en kernel
```

### Whitelist — FPR=0%
```
192.168.0.20 is NOT in set ppi_blocked.   ← admin nunca bloqueado
```
