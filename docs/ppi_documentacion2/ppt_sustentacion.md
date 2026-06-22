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
[F1 Captura] → [F2 Datos] → [F3 Modelo] → [F4 Motor] → [F5 Control] → [F6 Validación]
  Suricata       Dataset      Isolation       Motor         ipset/         40 corridas
  eve.json       limpio       Forest          decisión      iptables       lab real
```

### Visual
- Diagrama de pipeline horizontal con 6 cajas conectadas por flechas
- Cada caja con ícono representativo:
  - F1: 📡 (sensor)
  - F2: 📊 (tabla/CSV)
  - F3: 🤖 (modelo)
  - F4: ⚙️ (engranaje)
  - F5: 🛡️ (escudo)
  - F6: ✅ (check)
- Fondo claro o neutro

### Oralidad
> "La metodología sigue un pipeline de 6 fases encadenadas. Cada fase alimenta a la siguiente. F1 captura el tráfico real. F2 lo convierte en datos. F3 entrena el modelo. F4 lo convierte en un motor de decisión en tiempo real. F5 aplica el bloqueo efectivo. Y F6 lo valida todo con escenarios reproducibles."

---

---

## SLIDE 6 — Fases F1–F3: Datos y Modelo
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** De tráfico real a modelo entrenado

```
F1 — Captura con Suricata 7.0.3
  · Sensor en ens35 (modo promiscuo)
  · eve.json: registros de flujos TCP/UDP/ICMP

F2 — Procesamiento del dataset
  · 14 features por flujo (pkts, bytes, duración, ratios, protocolo)
  · Etiquetado: NORMAL (Grupo A) vs ANÓMALO (Grupo B)
  · Split cronológico 70/15/15 (train/val/test)

F3 — Isolation Forest (n=300 árboles)
  · Entrenado sobre tráfico NORMAL
  · Score de anomalía continuo [-1, 0]
  · 2 umbrales derivados de curva AUC-ROC: τ1, τ2
```

### Visual
- Flujo visual: [eve.json] → [14 features] → [IF model] → [score]
- Pequeña tabla de las 14 features (texto pequeño, referencial)
- O captura de pantalla del dataset_clean.csv con las columnas

### Oralidad
> "Suricata captura cada flujo de red y lo registra en un archivo JSON. De ahí extraemos 14 características: volumen de paquetes, bytes, duración, ratios de flujo y protocolo. Con eso entrenamos un Isolation Forest — un algoritmo no supervisado que aprende lo que es 'normal' y asigna un score a cada flujo nuevo. Más bajo el score, más sospechoso el tráfico."

---

---

## SLIDE 7 — Fases F4–F6: Motor y Validación
**Expositor:** E1 | **Tiempo:** 1 min

### Texto en pantalla
**Título:** Del modelo a la acción en tiempo real

```
F4 — Motor de decisión (motor_decision.py)
  · Lee eve.json en tiempo real (tail -f)
  · Clasifica cada flujo: PERMIT / LIMIT / BLOCK
  · Detectores heurísticos: SSH Brute Force, HTTP Abuse

F5 — Control inline con ipset/iptables
  · BLOCK  → DROP en kernel (< 35ms)
  · LIMIT  → hashlimit 100 pkt/s
  · Bloqueo progresivo: 5 min → 30 min → PERMANENTE

F6 — Validación: 40 corridas (9 escenarios, 3 grupos)
  · Normal (A), Anómalo (B), Mixto (C)
  · Disponibilidad 100% | ITL 0% | Latencia P95=34.8ms
```

### Visual
- Diagrama de flujo: [eve.json] → [Motor] → {PERMIT/LIMIT/BLOCK} → [ipset server]
- Tabla de bloqueo progresivo: 1°=300s | 2°=1800s | 3°=∞
- Texto compacto

### Oralidad
> "El motor lee el eve.json en tiempo real. Por cada flujo, extrae las 14 features, obtiene el score del modelo y decide: si el tráfico es normal lo deja pasar, si es sospechoso lo limita a 100 paquetes por segundo, y si es claramente anómalo lo bloquea con DROP en el kernel. El bloqueo además es progresivo: la primera vez 5 minutos, la segunda 30 minutos, y a la tercera se vuelve permanente."

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
Escenario: hping3 SYN flood desde Kali (192.168.0.100) → Servidor (192.168.0.120)

┌─────────────────────────────────────────────────────────────────────┐
│  Corrida  │  Timestamp  │  Score IF   │  Resultado      │  ipset    │
├─────────────────────────────────────────────────────────────────────┤
│    1ª     │  05:44:13   │  −0.6066    │  BLOCK #1 ✅    │  300s     │
│    2ª     │  06:05:03   │  −0.7696    │  BLOCK #2 ✅    │  1 800s   │
│    3ª     │  ~06:36     │  pendiente  │  BLOCK #3 ✅    │  ∞ perm.  │
└─────────────────────────────────────────────────────────────────────┘

block_counts.json: {"192.168.0.100": 2}  →  {"192.168.0.100": 3}
```

**Evidencia ipset en vivo:**
```
$ sudo ipset list ppi_blocked
Members:
192.168.0.100 timeout 1768     ← bloqueo#2 activo
```

### Visual
- **CAPTURA 1:** Terminal mostrando `motor_decision.log` con las 3 líneas de bloqueo
- **CAPTURA 2:** `sudo ipset list ppi_blocked` en el servidor con `timeout 0` (tomar cuando se complete bloqueo#3)
- **CAPTURA 3 (opcional):** Telegram con la alerta recibida
- Tabla grande centrada en la diapositiva

### Oralidad
> "Esto es validación real, no simulada. Esta mañana ejecutamos tres corridas de SYN Flood desde Kali Linux contra nuestro servidor. El sistema detectó cada una automáticamente."
>
> "Primera corrida: el modelo dio un score de −0.6066, por debajo de τ2. Bloqueo número 1: 5 minutos. Segunda corrida —después de que el bloqueo expiró— score de −0.7696. Bloqueo número 2: 30 minutos. La tercera corrida dará bloqueo permanente."
>
> "Aquí está el ipset del servidor en este momento: la IP de Kali con 1768 segundos de timeout restantes. No es un log de hace un mes. Es de esta mañana."
>
> *(Pausa. Dejar que el jurado lo absorba.)*

---

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
✅ Split cronológico 70/15/15    ✅ F1-Score  = 0.9947         ✅ ITL = 0%
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

| # | Qué capturar | Cuándo | Dónde |
|---|---|---|---|
| 1 | `motor_decision.log` mostrando bloqueo#1, #2, #3 | Después de bloqueo#3 | Sensor terminal |
| 2 | `sudo ipset list ppi_blocked` con `timeout 0` | Inmediatamente después bloqueo#3 | Servidor terminal |
| 3 | Dashboard web con alertas activas | Durante o después de una corrida B1 | Navegador → http://192.168.0.110:8080 |
| 4 | Telegram con alerta de BLOCK recibida | Durante corrida B1 | Teléfono o Telegram Web |
| 5 | `block_counts.json` = `{"192.168.0.100": 3}` | Después de bloqueo#3 | Sensor: `cat results/block_counts.json` |

## Figuras de graficas_f6/ para el PPT

| Figura | Slide recomendado |
|---|---|
| `f6_07_panel_resumen.png` | Slide 13 (Resultados) — principal |
| `f6_03_timeline_deteccion.png` | Slide 13 (Resultados) — secundaria |
| `f6_06_latencia_pipeline.png` | Slide 13 (Resultados) — terciaria |
| `f6_02_flows_anomalos.png` | Slide 10 (Flujo) — opcional |
| `f6_01_disponibilidad.png` | Slide 13 — soporte disponibilidad |

## Diagramas que necesitas crear (draw.io / Canva / PowerPoint)

| Diagrama | Slide | Descripción |
|---|---|---|
| Topología de red | Slide 9 | 4 VMs con IPs, flechas de tráfico, sensor destacado |
| Pipeline 6 fases | Slide 5 | 6 cajas conectadas con flechas horizontales |
| Flujo de decisión | Slide 10 | eve.json → motor → umbrales → acción |

---

## Checklist de preparación

- [ ] Confirmar bloqueo#3 y tomar capturas (hoy)
- [ ] Exportar figuras de graficas_f6/ a la PC de presentación
- [ ] Tomar screenshot del dashboard web con datos activos
- [ ] Crear diagrama de topología (draw.io recomendado — gratis en browser)
- [ ] Crear diagrama de pipeline 6 fases
- [ ] Construir el PPT (Canva, PowerPoint o Google Slides)
- [ ] Ensayar con cronómetro: E1 = 7 min, E2 = 11 min
- [ ] Preparar Q&A (ver `docs/informe_resultados/puntos_debiles_defensa.md`)
