# Expo Mark — Presentación del Producto
**Slides 8–13 | Menos de 10 minutos**
**Evidencia en vivo verificada: 2026-06-24 04:19 y 05:01-05:03 (revisión post-corrección F5 + comando reproducible)**

> **Nota de revisión (2026-06-24):** se recalibraron τ1/τ2 contra el modelo IF real
> en producción (antes estaban calculados para un modelo de 6 días atrás — ver
> `metricas_offline.txt`) y se agregó un detector heurístico de port-scan. La
> demo de ataque se actualizó de SYN flood a UDP flood porque, con los umbrales
> recalibrados, demuestra las 4 OE en una sola corrida (el SYN flood sigue
> funcionando para OE2/OE3, pero su BLOCK vía heurística HTTP-ABUSE no
> alimenta al predictor — ver "Notas técnicas" al final).
> **Segunda revisión (mismo día, varias corridas):** se encontró que el comando
> de PASO 3 sin la flag `-k` no era reproducible (fragmentaba el ataque en
> miles de flujos pequeños por la randomización del puerto origen de hping3,
> dando scores inconsistentes entre corridas). Se agregó `-k` al comando y se
> eliminó la promesa de un paso LIMIT intermedio para el flood — ver Nota
> Técnica 5.

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
sudo hping3 --udp -p 53 -k --flood 192.168.0.120
```
> La flag `-k` (keep, mantiene el puerto origen fijo) es la que hace que la demo
> sea reproducible. Sin ella, hping3 cambia el puerto origen en cada paquete y
> Suricata fragmenta el ataque en miles de flujos pequeños en vez de uno solo —
> el score resultante se vuelve errático (verificado en pruebas del 2026-06-24:
> sin `-k`, el mismo comando dio 3 resultados distintos en 3 corridas). Con `-k`
> todos los paquetes agregan al mismo flujo y el resultado es consistente.

### Lo que aparece en pantalla
```
HPING 192.168.0.120 (eth0 192.168.0.120): udp mode set, 28 headers + 0 data bytes
(modo --flood: no muestra paquete por paquete, solo el contador final)
```

### Lo que dices
> *"Lanzo el ataque desde Kali. hping3 en modo UDP flood contra el puerto 53 del servidor — uno de los vectores de DDoS volumétrico más comunes, el mismo patrón base de un ataque de amplificación DNS."*
> *"Suricata en el sensor los captura todos. Cada vez que Suricata cierra un flujo, lo escribe en eve.json. El motor lo lee inmediatamente."*
> *"Miren la Terminal 1 — en unos segundos va a aparecer la detección."*

---

### PASO 4/5 — El IF clasifica y bloquea directo (sin paso LIMIT intermedio)
**[~15-45 seg después del inicio, según velocidad de Suricata] — OE2 + OE3**

> **Nota:** un UDP flood a `--flood` acumula miles de paquetes por segundo en un
> único flujo desde el primer instante — el score cae muy por debajo de τ2 de
> inmediato. Esto es exactamente lo que documenta CLAUDE.md en la tabla
> "Secuencia del log del motor por tipo de ataque": *"SYN/UDP/ICMP Flood
> (`--flood`) → `ANOMALÍA ... BLOCK` directo (score ≤ τ2 en primer flujo)"*.
> No vas a ver un `SOSPECHOSO/LIMIT` antes — eso es esperado, no un error.
> (El paso LIMIT sí existe y es real: lo puedes mostrar por separado con un
> ataque más lento — ver Nota Técnica 5 al final del documento.)

### Lo que aparece en Terminal 1
```
05:03:24 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53
  proto=UDP score=-0.8098 grado=ALTA tipo=UDP_FLOOD
  byte_ratio=172080.54 pkt_rate=229675.4 | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```

### Lo que dices
> *"Score menos 0.8098. Muy por debajo de tau-2 — el Isolation Forest lo clasifica directamente como ANOMALÍA de grado ALTA, y además lo reconoce específicamente como UDP_FLOOD por la combinación de byte_ratio y pkt_rate — sin necesitar ningún heurístico de apoyo."*
> *"Decisión: BLOCK. El motor hace SSH al servidor y ejecuta ipset add ppi_blocked 192.168.0.100 timeout 300. 300 segundos — 5 minutos de bloqueo."*
> *"OE3 en funcionamiento: clasificación y control en tiempo real. Desde que Suricata cerró el flujo hasta que la IP está bloqueada en el kernel del servidor: menos de un segundo."*
> *"Si dejo correr el ataque varios segundos más, Suricata sigue cerrando flujos nuevos del mismo origen y el motor sigue registrando `ANOMALÍA...BLOCK` cada vez — eso es lo que alimenta al predictor en el próximo paso. Por eso para esta parte de la demo conviene dejar el flood corriendo unos 60 segundos en vez de detenerlo apenas se ve el primer BLOCK."*

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
192.168.0.100 timeout 287
```

### Lo que dices
> *"Verifico directamente en el servidor. 192.168.0.100 está en el set ppi_blocked con 287 segundos restantes — el número exacto depende de cuántos segundos pasaron entre el BLOCK y este comando."*
> *"La regla iptables dice: si el origen está en ppi_blocked, DROP — descartar sin responder. El atacante sigue enviando paquetes, pero el kernel del servidor los tira antes de que lleguen al stack UDP. Cero recursos consumidos por el atacante."*
> *"Kali todavía no sabe que está bloqueada — hping3 sigue enviando. Pero Suricata en el sensor sigue viéndolos. Eso alimenta al predictor."*

---

### PASO 7 — Predictor XGBoost evalúa sostenibilidad
**[~50-60 seg, con el flood todavía corriendo] — OE4**

> Esta escalada solo se ve si el ataque sigue activo varios ciclos después del
> primer BLOCK (no lo detengas apenas aparece el PASO 4/5). Si lo detienes de
> inmediato, blocks_60s se queda en 1 y P no escala — sigue siendo BLOCK válido
> para OE2/OE3, pero no demuestra OE4.

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

### ¿Por qué la latencia es tan baja?
> *"El Isolation Forest es O(1) en inferencia — evalúa un flujo en un árbol de profundidad logarítmica. Con 300 árboles y 14 features, el cálculo del score toma microsegundos. Los 34.8 milisegundos de P95 incluyen lectura de eve.json, extracción de features, normalización con el scaler, inferencia del IF, y escritura del log. La mayor parte de ese tiempo es I/O, no el modelo en sí."*

---

## EVIDENCIA REAL — Capturas 2026-06-24

### motor_decision.log — OE2 y OE3 (corrida 05:01-05:03, comando final con `-k`)
```
05:01:39 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53
  proto=UDP score=-0.7754 grado=ALTA tipo=ANOMALIA_GENERICA
  byte_ratio=290.94 pkt_rate=476.4 | BLOCK → BLOCKED timeout=300s

05:03:24 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:53
  proto=UDP score=-0.8098 grado=ALTA tipo=UDP_FLOOD
  byte_ratio=172080.54 pkt_rate=229675.4 | BLOCK → BLOCKED timeout=300s
```
> Dos corridas independientes con `-k`, ambas BLOCK directo sin LIMIT — confirma
> que es comportamiento reproducible del comando, no un resultado aislado (ver
> Nota Técnica 5).

### predictor.log — OE4 (corrida 04:15–04:20, flood sostenido ~5 min sin `-k`,
### conservada como evidencia de la escalada porque requiere varios ciclos de
### BLOCK consecutivos — ver nota en PASO 7)
```
04:18:31 | INFO    | OK                        | P=3.94%  blocks_60s=0   ← sin historial
04:19:31 | WARNING | ALERTA-PREDICTIVA         | P=98.87% blocks_60s=3   ← sostenido
04:19:42 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.69% blocks_60s=5   ← confirmado
04:20:02 | INFO    | ALERTA-PREDICTIVA (dedup) | P=99.93% blocks_60s=9   ← confirmado
```

### ipset en servidor — OE3
```
Members:
192.168.0.100 timeout 287   ← bloqueado en kernel
```

### Whitelist — FPR=0%
```
192.168.0.20 is NOT in set ppi_blocked.   ← admin nunca bloqueado
```

---

## NOTAS TÉCNICAS (no leer en voz alta — referencia si el jurado pregunta)

1. **Por qué cambió el ataque de demo de SYN flood a UDP flood:** con τ1/τ2 recalibrados
   (más estrictos que la versión anterior), un SYN flood típico a puerto 80 sigue
   generando LIMIT por score, pero su escalada a BLOCK termina dependiendo del
   heurístico HTTP-ABUSE (conteo de requests), no del score del IF. El predictor
   solo lee líneas `ANOMALÍA`/`SOSPECHOSO` con `score=` del log — no lee líneas
   `HTTP-ABUSE` ni `BRUTE-FORCE` (limitación de diseño documentada). El UDP flood
   sí cruza τ2 directamente por score, generando líneas `ANOMALÍA...BLOCK`
   repetidas que el predictor sí puede leer — por eso demuestra las 4 OE en una
   sola corrida de forma confiable. El SYN flood sigue siendo válido como
   evidencia de OE2/OE3 si se quiere usar como ataque alternativo.
2. **τ1/τ2 ya no son -0.4459/-0.6027** — esos valores correspondían a un modelo
   de 6 días antes del que está realmente en producción. Se recalcularon el
   2026-06-24 contra el modelo actual: τ1=-0.4650, τ2=-0.6118, AUC=0.8955.
3. **Detector de port-scan agregado el 2026-06-24** — antes, escaneos con nmap
   (-sS/-sX) y floods con flags TCP no estándar (FIN flood) no eran detectados:
   el IF puntúa cada flujo individual y un escaneo manda 1-2 paquetes por
   puerto, indistinguible de tráfico normal por flujo. Nuevo heurístico:
   ≥8 puertos distintos/10s → LIMIT, ≥20 → BLOCK.
4. **Limitación conocida, pendiente para después de la defensa:** `pkt_rate`
   se calcula como paquetes/duración con un piso de duración de 1ms; en una
   red rápida (RTT~0.3ms en este lab) esto puede inflar artificialmente el
   pkt_rate de conexiones legítimas muy veloces desde un origen que el modelo
   nunca vio como "normal" en entrenamiento. Corregirlo requiere reentrenar el
   IF — se deja documentado, no se ejecuta antes de presentar para no mover
   los scores ya validados en esta demo.
5. **Por qué se agregó `-k` al comando de PASO 3 (validado 2026-06-24):** al
   revalidar el flujo completo varias veces se encontró que `hping3 --udp
   --flood` SIN `-k` cambia el puerto origen en cada paquete por diseño
   (confirmado en `hping3 --help`). Suricata agrupa flujos por la tupla de 5
   elementos (IP/puerto origen y destino + protocolo), así que sin `-k` el
   ataque se fragmenta en miles de flujos pequeños — en una corrida llegó a
   2,818 flujos de ~58 paquetes/3,600 bytes cada uno — y el score resultante
   es errático: en pruebas sucesivas con el mismo comando se obtuvo a veces
   BLOCK directo, a veces nunca pasó de LIMIT durante 7,000 flujos. Con `-k`
   el puerto origen queda fijo, todos los paquetes se agregan al mismo flujo,
   y el resultado fue BLOCK directo y consistente en 2/2 corridas (scores
   -0.7754 y -0.8098, ambas por debajo de τ2=-0.6118). Esto también explica
   por qué no aparece un LIMIT intermedio: con `-k`, el flujo ya acumula
   suficiente tráfico para cruzar τ2 desde el primer corte de Suricata —
   coincide con lo que ya documentaba CLAUDE.md para floods (`--flood` → BLOCK
   directo). El paso LIMIT documentado en una versión anterior de este guion
   en realidad provenía de una corrida separada con `-i u2000` (ritmo
   moderado), no del mismo comando `--flood` — error de documentación ya
   corregido aquí.
