# PPT — Sustentación PPI UPeU
**Título:** Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Aprendizaje Automático y Control en Tiempo Real  
**Duración total:** 20 minutos | **Expositores:** E1 = Rubén | E2 = [compañero]  
**Slides:** 15 diapositivas

---

## Distribución de tiempo

| Sección | Slides | Min | Quién |
|---|---|---|---|
| Carátula | 1 | 0.5 | E1 |
| Problema | 2–3 | 2.5 | E1 |
| Objetivos | 4 | 1 | E1 |
| Metodología | 5–7 | 3 | E1 |
| **Producto (CORE)** | **8–12** | **7** | **E2** |
| Resultados | 13 | 2 | E2 |
| Conclusiones + Cierre | 14–15 | 1.5 | E2 |
| **Buffer preguntas** | — | **2.5** | Ambos |

---

---

## SLIDE 1 — Carátula
**Expositor:** E1 | **Tiempo:** 30 seg

### Texto en pantalla
```
DETECCIÓN TEMPRANA DE COMPORTAMIENTOS ANÓMALOS
EN REDES DE DATOS MEDIANTE APRENDIZAJE AUTOMÁTICO
Y UN MECANISMO DE CONTROL EN TIEMPO REAL

Rubén Mark Salazar Tocas
[Nombre E2]

Asesor: Ing. Nemias Saboya Rios
         Ing. Fernando Manuel Asin Gomez

Universidad Peruana Unión — Facultad de Ingeniería
Ingeniería de Sistemas  |  2026
```

### Visual
- Logo UPeU centrado arriba
- Fondo oscuro (azul marino o negro con grid tecnológico sutil)
- Línea divisoria elegante entre título y datos

### Oralidad
> "Buenos días. Somos Rubén Salazar y [nombre E2], y hoy les presentamos el resultado de meses de trabajo sobre un problema real que afecta a cualquier organización que tenga una red de datos."

---

---

## SLIDE 2 — El Gancho (Historia)
**Expositor:** E1 | **Tiempo:** 1.5 min

### Texto en pantalla
*(Solo 3 líneas visibles. Efecto revelación una por una si la herramienta lo permite.)*

```
🕐 2:00 AM — El servidor responde lento.

🕑 3:00 AM — El servidor no responde.

🕗 8:00 AM — El equipo de TI revisa los logs.
              Ya era demasiado tarde.
```

**Cifra impacto (abajo, grande):**
```
El tiempo promedio de detección de un ataque de red:
                   207 días
               [IBM Cost of a Data Breach 2023]
```

### Visual
- Fondo oscuro, texto blanco
- Ícono de reloj o línea de tiempo minimalista
- La cifra "207 días" en rojo o naranja, tamaño grande
- Opcional: imagen sutil de servidor caído o alerta de red

### Oralidad
> "Imaginen esta situación: son las 2 de la mañana. Un atacante inicia un SYN flood contra el servidor web de su organización. El servidor empieza a degradarse. A las 3 AM ya no responde. El equipo de TI llega al día siguiente y revisa los logs. Para entonces, el daño ya estaba hecho."
>
> "Según IBM, el tiempo promedio que una organización tarda en detectar una brecha de seguridad es 207 días. No semanas: meses. Y ese es exactamente el problema que nosotros atacamos."

---

---

## SLIDE 3 — Situación Problemática + Pregunta
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** El problema es la reactividad

```
Las redes de datos actuales detectan ataques DESPUÉS de que ocurren.

✗  Sistemas tradicionales (firewalls, IDS): reglas fijas → solo detectan ataques conocidos
✗  Análisis manual de logs: lento, costoso, no escala
✗  Sin respuesta automática: requiere intervención humana

¿Cómo detectar y responder a comportamientos anómalos
en tiempo real, antes de que causen daño?
```

### Visual
- Diagrama simple: [Ataque] → [Red] → ??? → [Daño] (con interrogante en el centro)
- Bullet points con íconos de ✗ en rojo
- Pregunta de investigación destacada en caja con borde coloreado

### Oralidad
> "Los sistemas de seguridad tradicionales trabajan con firewalls y reglas estáticas. Solo detectan lo que ya conocen. Además, requieren que alguien revise alertas manualmente. Eso no escala."
>
> "La pregunta que guía este trabajo es: ¿cómo podemos detectar comportamientos anómalos automáticamente y responder en tiempo real, antes de que el daño esté hecho?"

---

---

## SLIDE 4 — Objetivos
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Objetivo General:**
> Desarrollar un sistema de detección temprana y control inline de comportamientos anómalos en redes de datos, empleando Isolation Forest para la detección y mecanismos automáticos de bloqueo en tiempo real.

**Objetivos Específicos:**
```
OE1 — Construir un pipeline de captura y procesamiento de tráfico de red
      que genere un dataset válido para entrenamiento supervisado.

OE2 — Entrenar y validar un modelo de detección de anomalías con
      métricas AUC-ROC ≥ 0.80 sobre datos reales de laboratorio.

OE3 — Integrar el modelo en un motor de decisión con control
      automático de acceso y validarlo bajo escenarios de ataque.
```

### Visual
- Diagrama de árbol: OG arriba → OE1, OE2, OE3 abajo
- Texto compacto, sin saturar
- Color diferente para cada OE

### Oralidad
> "Nuestro objetivo general fue construir un sistema completo, no solo un modelo. Que detecte Y que actúe. Los tres objetivos específicos van de lo más técnico —los datos y el modelo— hasta la integración y validación en vivo."

---

---

## SLIDE 5 — Metodología: Visión General de Fases
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** Pipeline en 6 Fases

```
[F1 Captura] → [F2 Modelo IF] → [F3 Motor]  → [F4 XGBoost] → [F5 Aprend.] → [F6 Valid.]
  Suricata       IF n=300        PERMIT/LIMIT   Predictor       Auto-          40 corridas
  47 capturas    AUC=0.8998      /BLOCK+ipset   AUC=0.9992      reentren.      P95=34.8ms
                 τ1/τ2                                           cron noche
```

### Visual
- Diagrama de pipeline horizontal con 6 cajas (usar draw.io XML de `d2_pipeline.md`)
- Cada caja con ícono representativo:
  - F1: 📡 sensor
  - F2: 🤖 modelo IF
  - F3: ⚡ motor (la caja más grande — es el core)
  - F4: 🧠 predictor XGBoost
  - F5: 🔄 aprendizaje automático
  - F6: ✅ validación
- Flecha de retroalimentación F5 → F3/F4 (hot-reload)

### Oralidad
> "La metodología sigue un pipeline de 6 fases. F1 captura el tráfico real con Suricata. F2 entrena el Isolation Forest con ese tráfico y deriva los umbrales de decisión. F3 es el motor en producción: clasifica cada flujo nuevo en tiempo real y aplica el bloqueo directo en el kernel. F4 es el predictor XGBoost que analiza patrones de ataque para anticipar si el ataque va a persistir. F5 reajusta los modelos automáticamente cada noche. Y F6 validó todo el sistema con 40 corridas reproducibles."

---

---

## SLIDE 6 — Fases F1–F2: Captura y Modelo
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** De tráfico real a modelo entrenado

```
F1 — Captura con Suricata 7.0.3
  · ens35 modo pasivo · 9 escenarios (A: normal, B: anómalo, C: mixto)
  · 47 capturas · eve.json: flujos TCP / UDP / ICMP completos

F2 — Dataset + Isolation Forest            (fase3_entrenar.py + fase3_evaluar.py)
  · 14 features por flujo
    pkts / bytes / duración / ratios / protocolo / puerto
  · 53,708 flujos normales para entrenamiento (80%)
  · Split 80/20 aleatorio — shuffle=True, random_state=42
  · IsolationForest(n_estimators=300, contamination=0.05)
  · AUC-ROC = 0.8998 · Precision = 99.54% · Recall = 99.40%
  · τ1 = −0.4459  (Youden — umbral PERMIT/LIMIT)
  · τ2 = −0.6027  (FPR ≤ 2% — umbral LIMIT/BLOCK)
```

### Visual
- Flujo: [47 capturas .gz] → [fase3_entrenar.py] → [IF model] → [fase3_evaluar.py] → [τ1 / τ2]
- Tabla compacta de las 14 features (texto pequeño, dos columnas)
- Curva ROC con τ1 y τ2 marcados (usar `graficas_f6/f6_07_panel_resumen.png` o crear imagen simple)

### Oralidad
> "F1 es puro laboratorio: Suricata captura todo el tráfico de la red en modo pasivo, sin interferir. Obtuvimos 47 capturas de 9 escenarios distintos — tráfico HTTP normal, SSH, pero también SYN flood, brute force, UDP flood."
>
> "En F2, de cada flujo extraemos 14 características: cuántos paquetes, cuántos bytes, duración, ratios de comunicación, protocolo. Con eso entrenamos un Isolation Forest con 300 árboles, usando solo el tráfico normal — el modelo nunca ve ejemplos de ataque durante el entrenamiento. Aprende qué es 'normal' y luego le asigna un score continuo a cada flujo nuevo: cuanto más negativo el score, más anómalo. De la curva AUC-ROC derivamos dos umbrales: τ1 para separar normal de sospechoso, y τ2 para separar sospechoso de claramente anómalo."

---

---

## SLIDE 7 — Fases F3–F6: Motor, Predictor, Aprendizaje y Validación
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** Del modelo a la acción — y el sistema que aprende solo

```
F3 — Motor de decisión + control inline     (motor_decision.py)
  · tail eve.json → 14 features → IF score → PERMIT / LIMIT / BLOCK
  · BLOCK  → ipset DROP en kernel  (Latencia P95 = 34.8ms)
  · LIMIT  → hashlimit 100 pkt/s
  · Heurísticos: BF-SSH (15 intent./60s) · HTTP-Abuse (100 req/30s)
  · Bloqueo progresivo: #1 = 5 min  →  #2 = 30 min  →  #3 = PERMANENTE
  · Dashboard SSE :8080  ·  Telegram alerts (async)

F4 — Predictor XGBoost v2                  (predictor.py)
  · Lee motor_decision.log en tiempo real
  · 9 features comportamentales · AUC = 0.9992
  · P ≥ 70% → ALERTA-PREDICTIVA (Telegram + dashboard 🔴)

F5 — Aprendizaje continuo                  (cron en sensor)
  · IF: cada domingo 02:00 — reajusta baseline de tráfico normal
  · XGBoost: cada noche 03:00 — aprende del log del día anterior
  · Hot-reload: modelos actualizados sin reiniciar ningún servicio

F6 — Validación: 40 corridas · 9 escenarios · 3 grupos (A/B/C)
  · Disponibilidad = 100% | ITL = 0% | Latencia P95 = 34.8ms
  · Lead time SYN Flood ≈ 62s · BF SSH BLOCK = 60s
```

### Visual
- Diagrama de flujo: [eve.json] → [Motor F3] → {PERMIT / LIMIT / BLOCK}
                                              ↓
                                        [XGBoost F4] → Telegram 📱
                                              ↓
                                        [F5 cron] → hot-reload modelos
- Tabla de bloqueo progresivo: #1=300s | #2=1800s | #3=∞ (timeout=0 ipset)
- Resaltar F3 como el core (borde más grueso / color más intenso)

### Oralidad
> "F3 es el motor en producción. Lee el eve.json en tiempo real, extrae las 14 features de cada flujo, obtiene el score del Isolation Forest y decide: PERMIT si es normal, LIMIT si es sospechoso —lo frena a 100 paquetes por segundo—, o BLOCK si es claramente anómalo —DROP directo en el kernel del servidor. El bloqueo es progresivo: 5 minutos la primera vez, 30 la segunda, permanente la tercera."
>
> "F4 es el predictor: un XGBoost que lee los eventos del motor y predice si el ataque va a persistir. Con 9 features de comportamiento temporal, AUC de 0.9992. Cuando supera el 70% de probabilidad, manda alerta al Telegram del operador."
>
> "F5 cierra el ciclo: cada noche los modelos se reajustan automáticamente con los datos del día. Si el nuevo modelo es peor, no reemplaza al anterior."

> *(Aquí E1 entrega a E2)*

---

---

## SLIDE 8 — Producto: ¿Qué hace?
**Expositor:** E2 | **Tiempo:** 1 min

### Texto en pantalla
**Título grande:** SURIKATA — Sistema de Detección y Control Inteligente de Tráfico de Red

*(Una sola frase, grande, centrada):*
```
Detecta ataques en tiempo real y los bloquea automáticamente
sin intervención humana, en menos de 35 milisegundos.
```

**Debajo, 3 íconos con etiquetas:**
```
[📡 Detecta]          [🧠 Decide]          [🛡️ Bloquea]
 tráfico anómalo       en <35ms              automáticamente
 con ML               sin humano             en el kernel
```

### Visual
- Slide de alto impacto visual
- Fondo oscuro, texto grande en blanco/azul
- Los 3 íconos grandes, estilo infographic
- Sin saturar con texto

### Oralidad
> "Aquí está el producto. Le llamamos SURIKATA — aunque el nombre formal es el del informe. En una frase: detecta ataques en tiempo real y los bloquea de forma automática, sin que nadie tenga que intervenir, en menos de 35 milisegundos."
>
> "Detecta, decide y bloquea. Ese es el core."

---

---

## SLIDE 9 — Arquitectura General
**Expositor:** E2 | **Tiempo:** 1.5 min

### Texto en pantalla
**Título:** Arquitectura del sistema — 4 nodos, 1 red

```
[Win11 Cliente]     [Kali Atacante]
      ↓                   ↓
   ─────────── RED (192.168.0.0/24) ───────────
                           ↓
              [Ubuntu Sensor — Suricata + Motor]
                     192.168.0.110
                           ↓ SSH + ipset commands
              [Ubuntu Server — nginx + ipset]
                     192.168.0.120
```

**Componentes del sensor:**
```
eve.json → motor_decision.py → Isolation Forest → PERMIT/LIMIT/BLOCK
                ↑
        detectores heurísticos (BF-SSH, HTTP-Abuse)
                ↓
        Telegram + Dashboard web :8080
```

### Visual
- **FIGURA PRINCIPAL:** Diagrama de topología de red (crear en draw.io o similar)
  - 4 VMs con sus IPs
  - Flechas de tráfico
  - Sensor con los componentes internos destacados
- Puede ser el más importante en esta sección

### Oralidad
> "La arquitectura tiene 4 nodos en una red de laboratorio. El sensor corre Suricata —que captura todo el tráfico de la red— y el motor de decisión con el modelo ML. El servidor es el objetivo que queremos proteger. Cuando el motor decide BLOCK, le envía el comando al servidor para que bloquee la IP en el kernel de red, con ipset."
>
> "El sensor también envía alertas por Telegram y tiene un dashboard web en tiempo real."

---

---

## SLIDE 10 — Flujo de Funcionamiento
**Expositor:** E2 | **Tiempo:** 1.5 min

### Texto en pantalla
**Título:** Ciclo de decisión en tiempo real

```
1. Suricata detecta nuevo flujo → eve.json
2. Motor lee el evento (< 1ms)
3. Extrae 14 features del flujo
4. Isolation Forest calcula score [-1, 0]

   score > τ1 (−0.4459)  →  PERMIT ✅
   τ2 < score ≤ τ1       →  LIMIT ⚠️  (hashlimit 100 pkt/s)
   score ≤ τ2 (−0.6027)  →  BLOCK 🚫  (DROP kernel)

5. Si BLOCK: ipset add ppi_blocked <IP> timeout [300/1800/0]
6. Alerta Telegram + log + dashboard
```

### Visual
- Diagrama de flujo vertical o circular
- Los 3 umbrales visualizados en una línea: [BLOCK | LIMIT | PERMIT →]
- Código simplificado o pseudocódigo de los 2 umbrales
- **FIGURA:** Usar `f6_07_panel_resumen.png` de graficas_f6/ como referencia visual de fondo o esquina

### Oralidad
> "El ciclo es simple: Suricata ve un flujo, el motor lo procesa, el modelo da un score. Si el score supera τ1 es tráfico normal —pasa. Si está entre τ2 y τ1 es sospechoso —se limita. Si cae por debajo de τ2 es claramente anómalo —se bloquea con DROP directo en el kernel del servidor."
>
> "Los umbrales τ1 y τ2 no son arbitrarios: los derivamos de la curva AUC-ROC del modelo, optimizando el índice de Youden para τ1 y fijando FPR≤2% para τ2."

---

---

## SLIDE 11 — Demo: Bloqueo Progresivo en Vivo
**Expositor:** E2 | **Tiempo:** 2 min ← SLIDE MÁS IMPORTANTE

### Texto en pantalla
**Título:** Validación en vivo — SYN Flood B1 (2026-06-22)

```
Escenarios ejecutados el 2026-06-22 desde Kali (192.168.0.100) → Servidor (192.168.0.120)

┌──────────────────────────────────────────────────────────────────────────────┐
│  Corrida │  Timestamp  │  Trigger / Score IF      │  Resultado    │  ipset   │
├──────────────────────────────────────────────────────────────────────────────┤
│    1ª    │  05:44:13   │  IF  score=−0.6066       │  BLOCK #1 ✅  │  300s    │
│    2ª    │  06:05:03   │  IF  score=−0.7696       │  BLOCK #2 ✅  │  1 800s  │
│    3ª    │  06:39:42   │  HTTP-ABUSE 100 req/30s  │  BLOCK #3 ✅  │  ∞ perm  │
└──────────────────────────────────────────────────────────────────────────────┘

block_counts.json: {"192.168.0.100": 3}
```

**Evidencia ipset — bloqueo#3 permanente:**
```
$ sudo ipset list ppi_blocked          (en servidor 192.168.0.120)
Members:
192.168.0.100 timeout 0               ← timeout=0 = PERMANENTE
```

### Visual
- **CAPTURA 1:** Terminal mostrando `motor_decision.log` con las 3 líneas de bloqueo
- **CAPTURA 2:** `sudo ipset list ppi_blocked` en el servidor con `timeout 0` (tomar cuando se complete bloqueo#3)
- **CAPTURA 3 (opcional):** Telegram con la alerta recibida
- Tabla grande centrada en la diapositiva

### Oralidad
> "Esto es validación real, no simulada. Esta mañana ejecutamos tres corridas de SYN Flood desde Kali Linux contra nuestro servidor. El sistema detectó cada una automáticamente."
>
> "Primera corrida: SYN flood, score de −0.6066, por debajo de τ2. Bloqueo número 1: 5 minutos. Segunda corrida —después de que expiró— score de −0.7696. Bloqueo número 2: 30 minutos. Tercera corrida: el detector HTTP-Abuse registró 100 solicitudes en 30 segundos. Bloqueo número 3: permanente."
>
> "Aquí está el ipset del servidor en este momento: la IP de Kali con timeout=0. Eso significa que ese bloqueo no expira. No es un log de hace un mes. Es de esta mañana."
>
> *(Pausa. Dejar que el jurado lo absorba.)*

---

---

---

---

## SLIDE 11b — Demo: SSH Brute Force y Telegram
**Expositor:** E2 | **Tiempo:** 1 min (integrar en slide 11 si hay tiempo, o usar como respaldo)

### Texto en pantalla
**Título:** Validación adicional — B6 SSH Brute Force (2026-06-22 08:31)

```
Escenario: hydra -l admin -P fasttrack.txt ssh://192.168.0.120 -t 4 -V

┌─────────────────────────────────────────────────────────────────────┐
│  Evento    │  T desde inicio  │  Score IF   │  Tipo                 │
├─────────────────────────────────────────────────────────────────────┤
│  1ª detec. │  T + 53s         │  −0.4832    │  LIMIT → SOSPECHOSO   │
│  BLOCK     │  T + 60s         │  −0.6228    │  BRUTE_FORCE_SSH ✅   │
└─────────────────────────────────────────────────────────────────────┘

Alerta Telegram recibida: 🚨 PPI ALERTA — BRUTE_FORCE_SSH
                           Accion : BLOCK (DROP)   IP: 192.168.0.100
                           Puerto : 22   Score: −0.6228   Hora: 08:31:37
```

**Conclusión:** el detector heurístico BF-SSH actúa antes de que el atacante
               logre suficientes intentos para un acceso exitoso.

### Visual
- Captura del teléfono/Telegram Web con la alerta recibida
- Tabla de lead time centrada
- Línea de tiempo: [T+0 hydra] → [T+53s LIMIT] → [T+60s BLOCK]

### Oralidad
> "Para los ataques de brute force en SSH también hay evidencia real. Lanzamos Hydra con 4 hilos paralelos. En 53 segundos el sistema levantó la primera alerta de LIMIT. En 60 segundos exactos, BLOCK. El detector cuenta los intentos de autenticación en una ventana de 60 segundos — cuando supera 15, bloquea."
>
> "Y aquí está la alerta que llegó al teléfono en tiempo real. 'Brute Force SSH, BLOCK, Puerto 22, 08:31:37'. El administrador sabe lo que pasa antes de llegar a la oficina."

---

## SLIDE 12 — Dashboard Web en Tiempo Real
**Expositor:** E2 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** Visibilidad en tiempo real — http://192.168.0.110:8080

*(Slide principalmente visual — captura del dashboard)*

**Debajo de la imagen, 3 bullets:**
```
· Flujos por segundo clasificados (PERMIT / LIMIT / BLOCK)
· Alertas activas con IP origen, score y timestamp
· Actualización automática via Server-Sent Events (SSE)
```

### Visual
- **FIGURA PRINCIPAL:** Screenshot del dashboard web en el navegador (http://192.168.0.110:8080)
  - Tomar la captura cuando tenga datos activos (alertas visibles)
  - Mostrar la sección de bloqueos activos con Kali en la lista

### Oralidad
> "El sistema no opera en negro. Tiene un dashboard web al que cualquier administrador puede acceder desde su navegador. Muestra en tiempo real los flujos clasificados, las IPs bloqueadas y el estado del sistema. Se actualiza solo, sin recargar la página."

---

---

## SLIDE 13 — Resultados
**Expositor:** E2 | **Tiempo:** 2 min

### Texto en pantalla
**Título:** Resultados — todos los criterios de aceptación cumplidos

**Tres columnas (una por OE):**

```
OE1 — Pipeline de datos          OE2 — Modelo IF              OE3 — Motor + Validación
────────────────────             ──────────────               ───────────────────────
✅ 9 escenarios capturados       ✅ AUC-ROC = 0.8998          ✅ 40 corridas ejecutadas
✅ 14 features extraídas         ✅ Precision = 99.54%         ✅ Latencia P95 = 34.8ms
✅ Dataset etiquetado            ✅ Recall    = 99.40%         ✅ Disponibilidad = 100%
✅ Split 80/20 aleatorio         ✅ F1-Score  = 0.9947         ✅ ITL = 0%
                                 ✅ FPR@τ1   = 20.47%*         ✅ Lead time SYN ≈ 62s

                                 *mitigado con whitelist

OBJETIVO GENERAL: Sistema funcional, validado en laboratorio real, con control automático inline
```

### Visual
- **FIGURA 1:** `f6_07_panel_resumen.png` — panel de resumen F6 (esquina o centro)
- **FIGURA 2:** `f6_03_timeline_deteccion.png` — timeline de detecciones
- **FIGURA 3:** `f6_06_latencia_pipeline.png` — distribución de latencia
- Diseño en 3 columnas, una por objetivo específico

### Oralidad
> "Los resultados responden directamente a los tres objetivos. Para OE1: el pipeline está completo, 9 escenarios, 14 features, dataset limpio. Para OE2: el modelo alcanzó AUC de 0.8998, con Precision y Recall superiores al 99%. Para OE3: 40 corridas de validación, latencia P95 de 34.8 milisegundos —el requisito era menos de 500ms, cumplimos con margen—, disponibilidad del 100%."
>
> "El único indicador que merece una nota es el FPR de 20.47%. No lo ignoramos: está mitigado con una whitelist de IPs confiables, y bajar ese umbral generaría falsos negativos en SYN Flood —lo documentamos como limitación con su mitigación."

---

---

## SLIDE 14 — Conclusiones
**Expositor:** E2 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** Conclusiones

```
1. Es posible construir un sistema de detección de anomalías en tiempo real
   con Isolation Forest, latencia < 35ms y sin conocimiento previo del ataque.

2. El pipeline completo (captura → modelo → motor → control) funciona
   de extremo a extremo en un entorno de laboratorio real, con disponibilidad del 100%.

3. El bloqueo progresivo (5 min → 30 min → permanente) aporta una capa
   de control adaptativo que los firewalls estáticos no ofrecen.
```

### Visual
- Tres conclusiones en caja, numeradas, texto limpio
- Fondo neutro
- Ícono pequeño a la izquierda de cada conclusión (reloj, check, escudo)

### Oralidad
> "Tres conclusiones. Primera: Isolation Forest en modo no supervisado es suficientemente robusto para detección en tiempo real, con AUC casi 0.9. Segunda: el sistema funciona de punta a punta —no es un prototipo académico, corrió durante horas con 40 escenarios. Tercera: el bloqueo progresivo es una mejora concreta sobre firewalls estáticos, porque adapta la respuesta a la reincidencia."

---

---

## SLIDE 15 — Trabajos Futuros + Cierre
**Expositor:** E2 | **Tiempo:** 30 seg

### Texto en pantalla
**Título:** Trabajos futuros

```
→ Despliegue en infraestructura real (no laboratorio)
→ Reentrenamiento continuo con datos de producción (F5 implementada — base lista)
→ Extensión a tráfico cifrado (TLS fingerprinting)
→ Federación de sensores múltiples
```

**Frase de cierre (grande, centrada):**
```
"El sistema detecta, decide y bloquea.
 Sin intervención humana. En menos de 35ms."
```

```
Gracias.
```

### Visual
- Bullets de trabajos futuros (compactos, arriba)
- Frase de cierre grande y destacada (abajo, negrita)
- Logo UPeU pequeño en esquina

### Oralidad
> "Para cerrar: el trabajo abre líneas claras de extensión, sobre todo hacia entornos reales y tráfico cifrado. La base de reentrenamiento automático ya está implementada en F5."
>
> *(Breve pausa, mirar al jurado.)*
>
> "El sistema detecta, decide y bloquea. Sin intervención humana. En menos de 35 milisegundos. Muchas gracias. Quedamos a disposición para las preguntas."

---

---

## Capturas de pantalla que necesitas tomar

| # | Qué capturar | Estado | Dónde obtener |
|---|---|---|---|
| 1 | `motor_decision.log` — líneas bloqueo#1, #2, #3 | ⚠️ pendiente captura | `grep "bloqueo#" results/motor_decision.log` |
| 2 | `sudo ipset list ppi_blocked` con `timeout 0` | ⚠️ pendiente captura | En servidor 192.168.0.120 |
| 3 | Dashboard web — vista Alertas o Predictor activo | ✅ capturado hoy (09:05) | http://192.168.0.110:8080 |
| 4 | Telegram — alerta BRUTE_FORCE_SSH o BLOCK | ✅ recibida 07:25 | Teléfono / Telegram Web |
| 5 | `block_counts.json` = `{"192.168.0.100": 3}` | ⚠️ pendiente captura | `cat results/block_counts.json` (reset motor entre sesiones) |

## Figuras de graficas_f6/ para el PPT

| Figura | Slide recomendado |
|---|---|
| `f6_07_panel_resumen.png` | Slide 13 (Resultados) — principal |
| `f6_03_timeline_deteccion.png` | Slide 13 (Resultados) — secundaria |
| `f6_06_latencia_pipeline.png` | Slide 13 (Resultados) — terciaria |
| `f6_02_flows_anomalos.png` | Slide 10 (Flujo) — opcional |
| `f6_01_disponibilidad.png` | Slide 13 — soporte disponibilidad |

## Diagramas que necesitas crear (draw.io / Canva / PowerPoint)

| Diagrama | Slide | Archivo | Estado |
|---|---|---|---|
| Topología de red | Slide 9 | `d1_topologia.md` | ✅ XML draw.io listo |
| Pipeline 6 fases | Slide 5 | `d2_pipeline.md` | ✅ XML draw.io listo |
| Flujo de decisión | Slide 10 | `d3_flujo.md` | ✅ XML draw.io listo |
| Problema + Objetivos | Slides 2+4 | `d4_problema.md` | ✅ XML draw.io listo |

---

## Checklist de preparación

- [x] Bloqueo#3 confirmado — 06:39:42, timeout=0, HTTP-ABUSE 100 req/30s
- [x] B6 SSH BF validado — LIMIT T+53s, BLOCK T+60s (08:31:37)
- [x] Telegram alerta recibida — HTTP 200, 07:25
- [x] Whitelist Desktop validada — 120 req → 0 BLOCK/LIMIT
- [x] Dashboard web verificado — predictor activo P=55% AVISO, AUC=0.9992
- [ ] Exportar figuras de graficas_f6/ a la PC de presentación
- [ ] Tomar capturas finales para slides 11/12 (ver tabla abajo)
- [x] Diagrama topología creado — pegar XML de d1_topologia.md en draw.io
- [x] Diagrama pipeline creado — pegar XML de d2_pipeline.md en draw.io
- [ ] Construir el PPT (Canva, PowerPoint o Google Slides)
- [ ] Ensayar con cronómetro: E1 = 7 min, E2 = 11 min
- [ ] Preparar Q&A (ver `LIMITACIONES.md` para respuestas técnicas)
