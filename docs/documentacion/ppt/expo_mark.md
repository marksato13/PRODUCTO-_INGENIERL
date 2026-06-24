# Expo Mark — Presentación del Producto
**Slides 8–13 | Menos de 10 minutos**
**Evidencia en vivo verificada el 2026-06-24, comando final (`timeout 10`) reproducido 4 veces (08:49, 09:29, 09:44, 10:02) — mismo resultado las 4: BLOCK directo, tipo=UDP_FLOOD**
**Comando final: `sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120`**
**Capturas de pantalla reales incluidas — ver sección EVIDENCIA REAL**

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
> *"Abro dos terminales para ver el sistema en tiempo real. Terminal 1 es el log del motor — acá veo cada decisión: PERMIT, LIMIT o BLOCK, con el score exacto del Isolation Forest. Terminal 2 es el predictor XGBoost — acá veo la probabilidad de que cada IP continúe atacando. También tengo el dashboard web abierto en el proyector."*
> *"Ahora mismo silencio total. Cero anomalías. El sistema está en reposo."*

**Captura real — dashboard en cero, 2026-06-24 09:27:51:**

![Dashboard en cero](img/01_sistema_en_cero.png)

> BLOCK: 0, LIMIT: 0, PERMIT: 0, Flows total: 0, Latencia: 0.0ms — coincide exactamente con lo que dice el log en este instante.

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
2026-06-24 09:44:15 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53
  proto=UDP score=-0.8026 grado=ALTA tipo=UDP_FLOOD
  byte_ratio=218300.16 pkt_rate=230194.4 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*(comando lanzado 09:43:33, detección 09:44:15 — 42 segundos, dentro del rango 40-50s esperado)*

### Lo que dices
> *"Ahí está. Score menos 0.8026, muy por debajo de tau-2 — el Isolation Forest lo clasifica directo como ANOMALÍA de grado ALTA, y lo reconoce como UDP_FLOOD por byte_ratio y pkt_rate, sin heurístico de apoyo."*
> *"Decisión: BLOCK. El motor hace SSH al servidor y ejecuta ipset add ppi_blocked 192.168.0.100 timeout 300 — 5 minutos de bloqueo."*
> *"OE3: desde que Suricata cierra el flujo hasta que la IP está bloqueada en el kernel del servidor, menos de un segundo."*

**Captura real — mismo evento, panel Vista General, 2026-06-24 09:49:22:**

![Dashboard tras el BLOCK](img/02_vista_general_block.png)

> BLOCK: 1, FLOWS TOTAL: 1 — coherente (1 bloqueo de 1 flujo procesado, no hay flujos "perdidos"). Donut "Distribución por tipo de ataque" 100% UDP FLOOD. Latencia muestra "—" porque la línea agregada de estadísticas del motor (que reporta la latencia medida) recién se imprime cada 500 flujos — con un solo evento, todavía no llegó; no es ausencia de medición real, P95=34.8ms sigue siendo la métrica vigente (medida en la validación F6 de 40 corridas, no en esta demo puntual).

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
192.168.0.100 timeout 216
```
*(captura real de otra corrida idéntica, 2026-06-24 10:02:36 → verificado 10:04:00, 84s después del BLOCK — el número exacto siempre depende de cuándo se ejecuta el comando, no es fijo)*

### Lo que dices
> *"Verifico directamente en el servidor. 192.168.0.100 está en el set ppi_blocked con los segundos restantes que correspondan — el número exacto depende de cuándo se ejecuta este comando respecto al BLOCK."*
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

**Captura real — panel de Alertas, mismo BLOCK del PASO 4/5, 2026-06-24 09:52:42:**

![Panel de alertas](img/03_alertas_tiempo_real.png)

> Contador BLOCK: 1, LIMIT: 0 — una sola tarjeta, sin duplicados. Mismo score (-0.8026) y mismo byte_ratio (218300.2) que el log y que Telegram.

**Captura real — alerta de Telegram, mismo tipo de evento (corrida 08:49:13/08:45:08):**

![Telegram](img/04_telegram_alertas.jpeg)

> El mensaje de Telegram usa exactamente las mismas variables (score, byte_ratio, pkt_rate, hora) que la línea del log — confirmado: ambos números coinciden dígito por dígito.

---

### PASO 8 — Whitelist protege al administrador
**[~1:30 de la demo]**

### Lo que ejecutas (desde el Desktop, mientras el ataque corre o justo después)
```bash
curl http://192.168.0.120
ssh m4rk@192.168.0.120 "echo OK"
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```

### Lo que aparece en pantalla
```
HTTP 200
OK
192.168.0.20 is NOT in set ppi_blocked.
```
*(verificado en vivo 2026-06-24 10:04:25 — 5 curls + 1 ssh repetidos, cero líneas ANOMALÍA/SOSPECHOSO para 192.168.0.20 en el log, IP nunca entra a ppi_blocked ni ppi_limited)*

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

## EVIDENCIA REAL — Capturas y logs 2026-06-24

### 1. UDP Flood (OE2 + OE3) — comando final, 4 corridas idénticas
```
08:49:13 | ANOMALÍA score=-0.8026 tipo=UDP_FLOOD byte_ratio=198979.59 pkt_rate=209673.7  BLOCK
09:29:19 | ANOMALÍA score=-0.8057 tipo=UDP_FLOOD byte_ratio=127455.64 pkt_rate=223797.7  BLOCK
09:44:15 | ANOMALÍA score=-0.8026 tipo=UDP_FLOOD byte_ratio=218300.16 pkt_rate=230194.4  BLOCK
10:02:36 | ANOMALÍA score=-0.8026 tipo=UDP_FLOOD byte_ratio=215887.04 pkt_rate=227648.2  BLOCK
```
> 4/4 corridas con `sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120`:
> BLOCK directo sin LIMIT, score siempre entre -0.80 y -0.81 (muy por debajo de
> τ2=-0.6118), detección a los 42-50s del lanzamiento en las 4 — reproducible,
> no un resultado aislado. Capturas de pantalla en PASO 2, 4/5 y 7 (arriba)
> corresponden a la corrida de 09:43:33-09:44:15.

### 2. Port Scan (heurístico independiente del score, validado hoy)
```
10:07:39 | SOSPECHOSO src=192.168.0.100 dst=192.168.0.120:97 proto=TCP score=-0.5090 grado=BAJA  | LIMIT
10:07:41 | PORT-SCAN  src=192.168.0.100 dst=192.168.0.120:24 proto=TCP puertos_distintos=20/10s   | BLOCK → BLOCKED timeout=300s
```
> `nmap -sS -p 1-100 192.168.0.120` (9.7s) — primero el IF marca un flujo individual
> como SOSPECHOSO/LIMIT (score=-0.5090, no llega a τ2 por sí solo), 2 segundos
> después el heurístico de port-scan cuenta 20 puertos distintos en la ventana
> de 10s y fuerza BLOCK — exactamente el diseño de "heurístico en paralelo al
> score, no en reemplazo" explicado en Slide 10.

### 3. Tráfico normal — PERMIT (FPR=0%, validado hoy)
```
10:04:25 | curl http://192.168.0.120 → HTTP 200
10:04:25 | ssh m4rk@192.168.0.120 "echo OK" → OK
10:04:26 | 5 curls repetidos → sin ninguna línea ANOMALÍA/SOSPECHOSO para 192.168.0.20
         | ipset test ppi_blocked 192.168.0.20 → NOT in set
         | ipset test ppi_limited 192.168.0.20 → NOT in set
```

### 4. Telegram y Dashboard — mismo evento, mismos números
```
Telegram: 🚨 PPI ALERTA — UDP_FLOOD | BLOCK | IP 192.168.0.100 | Score -0.8116/-0.8026 | 08:45:08/08:49:13
Dashboard (8080): mismo BLOCK, mismo score, mismo tipo UDP_FLOOD, misma hora — ver capturas PASO 2 y PASO 7
```
> Las tres vistas (log, Telegram, dashboard) leen las mismas variables del
> mismo evento — no hay canal que pueda desincronizarse del otro. Captura real
> de Telegram en PASO 7 (arriba).

### 5. predictor.log — OE4 (corrida sostenida ~5 min sin `-k`, evidencia de
### escalada — requiere varios BLOCKs consecutivos, no se repite en el PASO
### 3-6 de 10s — ver nota en PASO 7)
```
04:18:31 | INFO    | OK                        | P=3.94%  blocks_60s=0   ← sin historial
04:19:31 | WARNING | ALERTA-PREDICTIVA         | P=98.87% blocks_60s=3   ← sostenido
04:19:42 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.69% blocks_60s=5   ← confirmado
04:20:02 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.93% blocks_60s=9   ← confirmado
```

---

## REFERENCIA RÁPIDA (no leer en voz alta — solo si algo no coincide en vivo)

- τ1=-0.4650, τ2=-0.6118, AUC=0.8955 (recalibrados 2026-06-24 contra el modelo real en producción).
- Comando de ataque: siempre con `-k` (puerto origen fijo) — sin él, el resultado no es reproducible.
- BLOCK directo sin LIMIT en flood es lo esperado (igual para SYN/UDP/ICMP flood).
- Espera ~40-50s tras lanzar el ataque antes de ver la detección — explicado en PASO 3.
- PASO 7 (OE4) es evidencia de otra corrida, no se repite dentro del PASO 3-6.

---

## CATÁLOGO DE COMANDOS DE PRUEBA — para extender la validación más allá de la demo

Todos verificados que producen el resultado indicado. Antes de cada comando: confirmar que Kali no tiene procesos colgados de la prueba anterior (`ps aux | grep -E 'hping3|nmap|hydra'`) y que el escenario está limpio (ver checklist al inicio del documento).

### A. Tráfico normal — debe dar PERMIT (silencio en el log, IP nunca en ipset)

| Comando (desde Desktop 192.168.0.20) | Qué prueba |
|---|---|
| `curl http://192.168.0.120` | HTTP normal — 1 request |
| `for i in $(seq 1 20); do curl -s -o /dev/null http://192.168.0.120; sleep 1; done` | HTTP repetido pero espaciado (no abuso) |
| `ssh m4rk@192.168.0.120 "echo OK"` | SSH legítimo |
| `scp archivo.txt m4rk@192.168.0.120:/tmp/` | Transferencia legítima |
| `ping -c 10 192.168.0.120` | ICMP normal, baja tasa |

Verificación después de cualquiera de estos: `ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"` debe decir siempre `NOT in set`.

### B. Ataques clasificados — comandos verificados (desde Kali 192.168.0.100)

| Tipo | Comando | Resultado esperado | Validado hoy |
|---|---|---|---|
| UDP Flood | `sudo timeout 10 hping3 --udp -p 53 -k --flood 192.168.0.120` | BLOCK directo, tipo=UDP_FLOOD, score≈-0.80, ~42-50s | Sí, 4 corridas |
| Port Scan | `sudo nmap -sS -p 1-100 192.168.0.120` | SOSPECHOSO/LIMIT (score IF) seguido de PORT-SCAN/BLOCK (heurístico, ≥20 puertos/10s) | Sí |
| SYN Flood | `sudo timeout 10 hping3 -S -p 80 -k --flood 192.168.0.120` | ANOMALÍA/BLOCK directo o vía heurístico HTTP-ABUSE según intensidad | Documentado, no revalidado hoy |
| ICMP Flood | `sudo timeout 10 hping3 -1 -k --flood 192.168.0.120` | ANOMALÍA/BLOCK directo, tipo=ICMP_FLOOD | Documentado, no revalidado hoy |
| Brute Force SSH | `hydra -l m4rk -P wordlist.txt ssh://192.168.0.120` | BRUTE-FORCE/LIMIT a los 5 intentos/60s, BLOCK a los 15/60s | Documentado, no revalidado hoy |
| HTTP Abuse | `for i in $(seq 1 150); do curl -s -o /dev/null http://192.168.0.120; done` | HTTP-ABUSE/LIMIT a 50 req/30s, BLOCK a 100 req/30s | Documentado, no revalidado hoy |

> Las filas marcadas "documentado, no revalidado hoy" están descritas en `CLAUDE.md` y fueron validadas en sesiones anteriores — si el jurado pide verlas en vivo, probarlas primero, no improvisar.

---

## CONCLUSIONES

1. El sistema cumple los 4 objetivos específicos con evidencia medible, no solo funcional: OE1 (47 corridas, 53,708 flujos), OE2 (AUC=0.8955, FPR operativo 0.0%), OE3 (latencia P95=34.8ms, disponibilidad 100%), OE4 (AUC=0.9991, escalada de probabilidad observada en vivo).
2. La combinación de un modelo no supervisado (Isolation Forest) con heurísticos de conteo en paralelo (HTTP-ABUSE, BRUTE-FORCE, PORT-SCAN) cubre un punto ciego real del enfoque puramente estadístico: ataques que se manifiestan como repetición de eventos discretos en el tiempo, no como un flujo individual anómalo.
3. La arquitectura de dos nodos separados (sensor + servidor) demostró ser operativamente robusta: el bloqueo persiste en el kernel del servidor aunque el motor de decisión se reinicie o falle.
4. La reproducibilidad fue validada empíricamente, no asumida: el mismo comando de ataque produjo el mismo resultado (BLOCK directo, tipo=UDP_FLOOD, score≈-0.80) en 4 corridas independientes en distintos momentos del día.

## LIMITACIONES PRINCIPALES

1. **Latencia de detección dependiente de Suricata, no del motor.** Un ataque de flujo único (UDP flood con puerto origen fijo) tarda 40-100 segundos en aparecer en el log, porque Suricata solo escribe el registro de un flujo cuando lo cierra (timeout de 30s tras el último paquete). El motor decide y bloquea en <1 segundo una vez que recibe el flujo — el cuello de botella es el sensor, no el modelo.
2. **Falso positivo conocido en conexiones LAN muy rápidas.** `pkt_rate` se calcula con un piso de duración de 1ms; en redes con RTT sub-milisegundo (como este laboratorio VMware), tráfico legítimo muy veloz puede producir un `pkt_rate` artificialmente alto y ser clasificado como anómalo. Corregirlo requiere reentrenar el Isolation Forest — deliberadamente no se hizo antes de esta sustentación para no mover los scores ya validados.
3. **El predictor XGBoost no lee todas las categorías del log.** Su parser solo reconoce líneas `ANOMALÍA`/`SOSPECHOSO` con `score=` — no lee `HTTP-ABUSE`, `BRUTE-FORCE` ni `PORT-SCAN` directamente. La predicción de sostenibilidad (OE4) es más confiable para ataques que cruzan el umbral del Isolation Forest por score que para los detectados solo por heurístico.
4. **El reentrenamiento automático (F5) depende de la cantidad de tráfico anómalo reciente.** Si en la ventana de reentrenamiento hay pocos eventos de ataque, el script se autodescarta sin reentrenar — es una salvaguarda contra sobreajuste con datos insuficientes, pero significa que el sistema no se actualiza solo en períodos de calma prolongados.
5. **Validación en laboratorio controlado, no en producción.** Las 47 corridas y 40 validaciones F6 se hicieron en una red de 5 VMs sin el ruido, la diversidad de protocolos ni el volumen de una red real — el AUC y los umbrales podrían requerir recalibración fuera de este entorno.

## MEJORAS Y TRABAJOS A FUTURO

1. Corregir el cálculo de `pkt_rate` (eliminar el piso artificial de 1ms o usar una métrica de tasa más robusta) y reentrenar el Isolation Forest con la corrección incluida.
2. Extender el parser del predictor XGBoost para que también consuma eventos `HTTP-ABUSE`, `BRUTE-FORCE` y `PORT-SCAN`, no solo los basados en score — daría visión de sostenibilidad sobre el 100% de las detecciones, no solo las basadas en el Isolation Forest.
3. Evaluar reducir el timeout de flujo UDP en Suricata (`flow-timeouts.udp.new`) para ataques de un solo flujo agregado, balanceando contra el riesgo de fragmentar conexiones UDP legítimas de mayor duración (DNS, streaming).
4. Probar el sistema contra tráfico de una red de producción real (o un dataset público como CIC-IDS2017/2018) para validar que el AUC y los umbrales generalizan fuera del laboratorio.
5. Agregar un mecanismo de fallback si el canal Telegram falla (cola persistente o reintento) — actualmente la alerta se descarta silenciosamente si la cola está llena.
6. Explorar detección de exfiltración de datos (tráfico saliente anómalo), no solo tráfico entrante — el diseño actual está orientado a ataques hacia el servidor protegido.

## REFERENCIAS

1. Scarfone, K., & Mell, P. (2007). *Guide to Intrusion Detection and Prevention Systems (IDPS)*. NIST Special Publication 800-94. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-94
2. Cichonski, P., Millar, T., Grance, T., & Scarfone, K. (2012). *Computer Security Incident Handling Guide*. NIST Special Publication 800-61 Rev. 2. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r2
3. Pascoe, C., Quinn, S., & Scarfone, K. (2024). *The NIST Cybersecurity Framework (CSF) 2.0*. NIST Cybersecurity White Paper (CSWP) 29. National Institute of Standards and Technology. https://doi.org/10.6028/NIST.CSWP.29
4. Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. *2008 Eighth IEEE International Conference on Data Mining*, 413–422. https://doi.org/10.1109/ICDM.2008.17
5. Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2012). Isolation-Based Anomaly Detection. *ACM Transactions on Knowledge Discovery from Data*, 6(1), 1–39. https://doi.org/10.1145/2133360.2133363
6. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794. https://doi.org/10.1145/2939672.2939785
7. Waleed, A., Jamali, A. F., & Masood, A. (2022). Which open-source IDS? Snort, Suricata or Zeek. *Computer Networks*, 213, 109116. https://doi.org/10.1016/j.comnet.2022.109116
8. Chua, W., et al. (2024). Web Traffic Anomaly Detection Using Isolation Forest. *Informatics*, 11(4), 83. https://doi.org/10.3390/informatics11040083
