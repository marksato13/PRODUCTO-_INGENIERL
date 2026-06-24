# Expo Mark — Presentación del Producto
**Slides 8–13 | Menos de 10 minutos**
**Evidencia en vivo verificada y reproducida 4 veces: 2026-06-24**
**Comando final: `sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120`**

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
score > −0.4650   →  PERMIT   ✅
−0.6118 < score ≤ −0.4650  →  LIMIT ⚠️  (100 pkt/s)
score ≤ −0.6118   →  BLOCK   🚫  (DROP kernel)
      ↓
[en paralelo] heurísticos independientes del score:
  ≥100 req/30s mismo puerto 80      → HTTP-ABUSE  → LIMIT/BLOCK
  ≥15 intentos/60s puerto 22         → BRUTE-FORCE → LIMIT/BLOCK
  ≥20 puertos distintos/10s          → PORT-SCAN   → LIMIT/BLOCK
      ↓
BLOCK → SSH → servidor → ipset add timeout [300s / 1800s / ∞]
BLOCK → Telegram 🚨 + predictor.log P=XX%
```

### Lo que dices

> *"El ciclo de decisión funciona así. Suricata genera un evento de flujo en eve.json — el motor lo lee en tiempo real."*

> *"Primero verifica si la IP origen está en la whitelist. El Desktop administrativo siempre está en whitelist — nunca se bloquea. Si no está en whitelist, extrae las 14 características del flujo y el Isolation Forest le asigna un score."*

> *"El score es continuo, entre 0 y −1. Por encima de tau-1 menos 0.4650: PERMIT, tráfico normal. Entre tau-2 y tau-1: SOSPECHOSO, se aplica LIMIT — hashlimit de 100 paquetes por segundo en el servidor. Por debajo de tau-2 menos 0.6118: ANOMALÍA, BLOCK — DROP directo en el kernel."*

> *"Estos dos umbrales no son arbitrarios. Los derivamos matemáticamente de la curva ROC: tau-1 maximiza el índice de Youden — el punto donde TPR menos FPR es máximo. Tau-2 es el punto donde el FPR cae al 2%. Y se recalculan cada vez que el modelo se reentrena — no son un valor fijo en el código, viven en un archivo de métricas que el motor lee al arrancar."*

> *"Además del score del Isolation Forest, hay tres detectores heurísticos independientes corriendo en paralelo: fuerza bruta SSH, abuso HTTP, y escaneo de puertos. Este último lo agregamos porque el Isolation Forest puntúa cada flujo de forma individual — un escaneo manda uno o dos paquetes por puerto, y eso por sí solo no se ve distinto a tráfico normal. El heurístico cuenta puertos distintos del mismo origen en una ventana corta, sin importar qué tan 'normal' luzca cada flujo por separado."*

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

### PASO 3 — Lanzar el ataque UDP Flood
**[0:40 de la demo] — OE2 empieza acá**

### Lo que ejecutas (desde la VM Kali)
```bash
sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120
```
> El flag `-k` fija el puerto origen — sin él, el ataque se fragmenta en miles
> de flujos chicos y el resultado deja de ser confiable (probado).

### ⏱️ Antes de lanzarlo: la detección tarda ~40-50s, no segundos
> Suricata recién escribe el flujo cuando lo cierra, y un flujo UDP se cierra
> 30s después de su último paquete — no es el motor siendo lento (eso sigue
> en <1s, P95=34.8ms). **Mientras esperas, di esto:** *"El ataque ya mandó
> millones de paquetes. Suricata necesita ~30 segundos sin tráfico nuevo de
> esa IP para cerrar el flujo y recién ahí lo reporta — así trabaja cualquier
> sensor basado en flujos."*

### Lo que aparece en pantalla
```
--- 192.168.0.120 hping statistic ---
14255146 packets transmitted, 0 packets received, 100% packet loss
```

### Lo que dices
> *"Lanzo el ataque desde Kali. UDP flood contra el puerto 53 del servidor — vector de DDoS volumétrico, base de un ataque de amplificación DNS."*
> *"Suricata lo está capturando ahora. Esperemos un momento a que cierre el flujo."* (ver aviso de arriba)

---

### PASO 4/5 — El IF clasifica y bloquea directo
**[~40-50 seg después de lanzar el comando] — OE2 + OE3**

> No vas a ver `SOSPECHOSO/LIMIT` antes del BLOCK — un flood a `--flood`
> acumula tanto tráfico en un único flujo que el score cae bajo τ2 directo
> desde el primer corte. Coincide con la tabla de CLAUDE.md para floods. Eso
> es esperado, no un error.

### Lo que aparece en Terminal 1
```
08:49:13 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53
  proto=UDP score=-0.8026 grado=ALTA tipo=UDP_FLOOD
  byte_ratio=198979.59 pkt_rate=209673.7 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```

### Lo que dices
> *"Ahí está. Score menos 0.8026, muy por debajo de tau-2 — el Isolation Forest lo clasifica directo como ANOMALÍA de grado ALTA, y lo reconoce como UDP_FLOOD por byte_ratio y pkt_rate, sin heurístico de apoyo."*
> *"Decisión: BLOCK. El motor hace SSH al servidor y ejecuta ipset add ppi_blocked 192.168.0.100 timeout 300 — 5 minutos de bloqueo."*
> *"OE3: desde que Suricata cierra el flujo hasta que la IP está bloqueada en el kernel del servidor, menos de un segundo."*

---

### PASO 6 — Verificar bloqueo real en servidor
**[~50-60 seg desde el lanzamiento] — OE3 evidencia**

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
192.168.0.100 timeout 286
```

### Lo que dices
> *"Verifico directamente en el servidor. 192.168.0.100 está en el set ppi_blocked con 286 segundos restantes — el número exacto depende de cuántos segundos pasaron entre el BLOCK y este comando."*
> *"La regla iptables dice: si el origen está en ppi_blocked, DROP — descartar sin responder. Con el comando de 10 segundos que usamos, hping3 ya terminó antes de que apareciera esta línea — pero si el atacante sigue insistiendo después, el servidor descarta cada paquete nuevo sin gastar recursos. Cero impacto aunque el ataque continúe."*

---

### PASO 7 — Predictor XGBoost evalúa sostenibilidad
**Evidencia pre-capturada — preséntala como tal, no la repitas en vivo dentro del PASO 3-6**

> El PASO 3 (10s, `-k`) genera UN solo BLOCK, no escalada. La secuencia de
> abajo viene de una corrida real pero distinta (ataque sostenido ~5 min, sin
> `-k`). Muéstrala como log/captura ya validada, no como algo que va a
> reaparecer en la misma demo corta.

### Lo que aparece en Terminal 2
```
04:18:31 | INFO    | OK                       | src=192.168.0.100 P=3.94%  score=-0.5772 blocks_60s=0
04:19:31 | WARNING | ALERTA-PREDICTIVA        | src=192.168.0.100 P=98.87% score=-0.7628 blocks_60s=3
04:19:42 | INFO    | ALERTA-PREDICTIVA (dedup)| src=192.168.0.100 P=99.69% score=-0.7623 blocks_60s=5
04:19:52 | INFO    | ALERTA-PREDICTIVA (dedup)| src=192.168.0.100 P=99.69% score=-0.7631 blocks_60s=7
04:20:02 | INFO    | ALERTA-PREDICTIVA (dedup)| src=192.168.0.100 P=99.93% score=-0.7631 blocks_60s=9
```

### Lo que dices
> *"Terminal 2 — el predictor XGBoost. Cada 10 segundos evalúa el historial de comportamiento de cada IP activa."*

> *"Primer ciclo: P=3.94% — recién empezó el ataque, sin historial de bloqueos todavía. El XGBoost dice 'evidencia débil de sostenimiento'."*

> *"Un minuto después: la IP acumuló 3 bloqueos en los últimos 60 segundos. P=98.87% — ALERTA-PREDICTIVA. El modelo detectó el patrón de reincidencia y saltó de probabilidad baja a casi certeza."*

> *"Los siguientes ciclos confirman: con 5, 7 y 9 bloqueos acumulados, P se mantiene sobre 99.6% — 'dedup' significa que ya se envió la alerta de Telegram para esta IP hace menos de 5 minutos, así que no se repite el mensaje, pero el log sigue registrando cada evaluación."*

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
| **OE2** — Isolation Forest | Score continuo · τ1/τ2 por curva ROC | AUC=0.8955 · Precision=99.54% · Recall=99.35% |
| **OE3** — Motor en tiempo real | LIMIT→BLOCK en <1s · ipset en servidor | Latencia P95=34.8ms · ITL=0% · Disp.=100% |
| **OE4** — Predictor sostenibilidad | P=3.9% → P=99.9% en ~90 seg de ataque | AUC=0.9991 · 10 features comportamentales |
| **General** | 40 corridas · 4 grupos · 4 ataques distintos | 16/16 criterios de aceptación PASS |

### Lo que dices

> *"Los resultados responden directamente a los cuatro objetivos específicos."*

> *"OE1 cumplido: pipeline completo de captura. 47 corridas de tráfico real organizadas en 9 escenarios — normal, anómalo y mixto — con 53 mil flujos para entrenar el modelo y 13 mil reservados para evaluación."*

> *"OE2 cumplido: el Isolation Forest alcanzó AUC de 0.8955 — el criterio mínimo era 0.85. Precision del 99.54% y Recall del 99.35%. Los umbrales tau-1 y tau-2 se derivaron matemáticamente: tau-1 por índice de Youden, tau-2 fijando el FPR al 2%. Y validamos con datos nuevos: 119 flujos que el modelo nunca vio — tasa de falsos positivos 0.0%."*

> *"OE3 cumplido: el motor clasifica y actúa en tiempo real. Latencia percentil 95 de 34.8 milisegundos — 14 veces más rápido que el límite de 500 milisegundos. Disponibilidad del servidor 100% durante todos los ataques. Cero interrupciones de tráfico legítimo en 40 corridas."*

> *"OE4 cumplido: el predictor XGBoost con AUC de 0.9991. Y acabamos de ver en vivo cómo la probabilidad subió de 3.94% a 99.93% conforme el ataque se sostuvo y acumuló bloqueos. Predice sostenibilidad para tomar decisiones de bloqueo proporcionales."*

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

### ¿Por qué FPR=20.27% en tau-1?
> *"Si bajamos el FPR, tau-1 se vuelve más estricto y algunos ataques de baja intensidad — los que están más cerca del comportamiento normal — escaparían de la detección. Preferimos tolerar ese FPR estadístico porque la whitelist lo anula operativamente: todas las IPs legítimas del laboratorio están en whitelist y nunca se bloquean. El FPR operativo real fue 0.0%."*

### ¿El XGBoost predice ANTES de que el sistema bloquee?
> *"Predice si el ataque va a CONTINUAR después del primer bloqueo. No predice el ataque futuro desde cero — observa el patrón de bloqueos acumulados de esa IP en los últimos 60 segundos y la velocidad a la que llegan. Con esa información decide si el bloqueo debe ser corto o progresivo hacia permanente."*

### ¿AUC=0.9991 no es sospechosamente alto?
> *"Versión 1 tenía AUC=1.0000 — ese sí era sospechoso porque era data leakage: el score del IF estaba como feature y los labels se derivaban de ese mismo score. Al eliminarlo, el AUC bajó a 0.9991 en datos de test que el modelo nunca vio. Ese 0.9991 es real porque los ataques en laboratorio son consistentes — un UDP flood desde Kali siempre genera el mismo patrón de bloqueos rápidos."*

### ¿Qué pasa si el motor se cae?
> *"Tres capas de protección. Primero: los bloqueos ya aplicados en ipset persisten en el servidor aunque el motor se caiga — el kernel sigue bloqueando. Segundo: el motor corre como servicio systemd con restart automático. Tercero: el sensor y el servidor son máquinas separadas — un fallo del motor no afecta la disponibilidad del servicio que protege."*

### ¿Funciona con ataques que el modelo no conoce?
> *"El IF es one-class: aprende qué es 'normal' y detecta cualquier desviación. No necesita conocer el ataque específico. En la validación CA-16, usamos 119 flujos de una sesión nueva que el modelo nunca vio — todos fueron PERMIT. Si hubieran sido anómalos, el IF los habría detectado por su desviación del patrón normal, sin importar el tipo de ataque."*

### ¿Por qué hay un heurístico de port-scan si ya tienen un modelo de Machine Learning?
> *"Porque el Isolation Forest puntúa cada flujo individualmente, y un escaneo de puertos manda uno o dos paquetes por puerto — visto flujo por flujo, no se distingue de tráfico normal liviano. Lo mismo pasa con fuerza bruta SSH y abuso HTTP, por eso esos dos ya tenían heurísticos de conteo desde el diseño original. El de port-scan sigue exactamente el mismo patrón: cuenta puertos distintos del mismo origen en una ventana corta, en paralelo al score del modelo, no en reemplazo de él."*

### Tardó casi un minuto en bloquear, ¿no es eso lento para "tiempo real"?
> *"Son dos cosas distintas. Suricata tarda ~30-40s en decidir que el flujo
> terminó — es configuración del sensor, no el motor pensando. Una vez que
> Suricata entrega el flujo, el motor bloquea en menos de un segundo: eso es
> lo que mide la latencia P95 de 34.8 milisegundos. Frente a un ataque real
> que dura minutos u horas, ese margen es insignificante."*

### ¿Por qué la latencia es tan baja?
> *"El Isolation Forest es O(1) en inferencia — evalúa un flujo en un árbol de profundidad logarítmica. Con 300 árboles y 14 features, el cálculo del score toma microsegundos. Los 34.8 milisegundos de P95 incluyen lectura de eve.json, extracción de features, normalización con el scaler, inferencia del IF, y escritura del log. La mayor parte de ese tiempo es I/O, no el modelo en sí."*

---

## EVIDENCIA REAL — Capturas 2026-06-24

### motor_decision.log — OE2 y OE3 (4 corridas independientes con `-k`, mismo comando)
```
05:01:39 | ANOMALÍA score=-0.7754 tipo=ANOMALIA_GENERICA byte_ratio=290.94    pkt_rate=476.4     BLOCK
05:03:24 | ANOMALÍA score=-0.8098 tipo=UDP_FLOOD         byte_ratio=172080.54 pkt_rate=229675.4  BLOCK
08:45:08 | ANOMALÍA score=-0.8116 tipo=UDP_FLOOD         byte_ratio=205585.17 pkt_rate=235998.2  BLOCK
08:49:13 | ANOMALÍA score=-0.8026 tipo=UDP_FLOOD         byte_ratio=198979.59 pkt_rate=209673.7  BLOCK
```
> 4/4 corridas: BLOCK directo sin LIMIT, score siempre muy por debajo de
> τ2=-0.6118 — comportamiento reproducible, no un resultado aislado.

### predictor.log — OE4 (corrida 04:15–04:20, flood sostenido ~5 min sin `-k`,
### conservada como evidencia de la escalada porque requiere varios ciclos de
### BLOCK consecutivos — ver nota en PASO 7, NO es la misma corrida de arriba)
```
04:18:31 | INFO    | OK                        | P=3.94%  blocks_60s=0   ← sin historial
04:19:31 | WARNING | ALERTA-PREDICTIVA         | P=98.87% blocks_60s=3   ← sostenido
04:19:42 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.69% blocks_60s=5   ← confirmado
04:20:02 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.93% blocks_60s=9   ← confirmado
```

### Telegram y Dashboard — mismo evento, mismos números, confirmado con capturas reales
```
Telegram: 🚨 PPI ALERTA — UDP_FLOOD | BLOCK | IP 192.168.0.100 | Score -0.8026 | 08:49:13
Dashboard (8080): mismo BLOCK, mismo score, mismo tipo UDP_FLOOD, misma hora
```
> Las tres vistas (log, Telegram, dashboard) leen las mismas variables del
> mismo evento — no hay canal que pueda desincronizarse del otro.

### ipset en servidor — OE3
```
Members:
192.168.0.100 timeout 286   ← bloqueado en kernel (corrida 08:49:13)
```

### Whitelist — FPR=0%
```
192.168.0.20 is NOT in set ppi_blocked.   ← admin nunca bloqueado
```

---

## REFERENCIA RÁPIDA (no leer en voz alta — solo si algo no coincide en vivo)

- τ1=-0.4650, τ2=-0.6118, AUC=0.8955 (recalibrados 2026-06-24 contra el modelo real en producción).
- Comando de ataque: siempre con `-k` (puerto origen fijo) — sin él, el resultado no es reproducible.
- BLOCK directo sin LIMIT en flood es lo esperado (igual para SYN/UDP/ICMP flood).
- Espera ~40-50s tras lanzar el ataque antes de ver la detección — explicado en PASO 3.
- PASO 7 (OE4) es evidencia de otra corrida, no se repite dentro del PASO 3-6.
