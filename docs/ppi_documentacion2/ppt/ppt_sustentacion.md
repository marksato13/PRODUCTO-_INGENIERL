# PPT — Sustentación PPI UPeU 2026
**Título:** Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Aprendizaje Automático y Control en Tiempo Real  
**Duración total:** 20 minutos | **Expositor:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios | Ing. Fernando Manuel Asin Gomez  
**Slides:** 15 diapositivas

---

## Distribución de tiempo

| Sección | Slides | Min |
|---|---|---|
| Carátula | 1 | 0.5 |
| Problema | 2–3 | 2.5 |
| Objetivos | 4 | 1 |
| Metodología | 5–7 | 3 |
| **Producto (CORE)** | **8–12** | **7** |
| Resultados | 13 | 2 |
| Conclusiones + Cierre | 14–15 | 1.5 |
| **Buffer preguntas** | — | **2.5** |

---

## SLIDE 1 — Carátula
**Tiempo:** 30 seg

### Texto en pantalla
```
DETECCIÓN TEMPRANA DE COMPORTAMIENTOS ANÓMALOS
EN REDES DE DATOS MEDIANTE APRENDIZAJE AUTOMÁTICO
Y UN MECANISMO DE CONTROL EN TIEMPO REAL

Rubén Mark Salazar Tocas

Asesor: Ing. Nemias Saboya Rios
         Ing. Fernando Manuel Asin Gomez

Universidad Peruana Unión — Facultad de Ingeniería
Ingeniería de Sistemas  |  2026
```

### Visual
- Logo UPeU centrado arriba
- Fondo oscuro (azul marino o negro con grid tecnológico sutil)

### Oralidad
> "Buenos días. Mi nombre es Rubén Salazar y hoy les presento el resultado de meses de trabajo sobre un problema real que afecta a cualquier organización que tenga una red de datos."

---

## SLIDE 2 — El Gancho
**Tiempo:** 1.5 min

### Texto en pantalla
```
🕐 2:00 AM — El servidor responde lento.
🕑 3:00 AM — El servidor no responde.
🕗 8:00 AM — El equipo de TI revisa los logs.
              Ya era demasiado tarde.

El tiempo promedio de detección de un ataque de red:
                   207 días
               [IBM Cost of a Data Breach 2023]
```

### Visual
- Fondo oscuro, texto blanco
- "207 días" en rojo, tamaño grande

### Oralidad
> "Imaginen esta situación: son las 2 de la mañana. Un atacante inicia un SYN flood contra el servidor web de su organización. El servidor empieza a degradarse. A las 3 AM ya no responde. El equipo de TI llega al día siguiente y revisa los logs. Para entonces, el daño ya estaba hecho."
>
> "Según IBM, el tiempo promedio que una organización tarda en detectar una brecha de seguridad es 207 días. No semanas: meses. Y ese es exactamente el problema que nosotros atacamos."

---

## SLIDE 3 — Situación Problemática
**Tiempo:** 1 min

### Texto en pantalla
```
El problema es la reactividad

Las redes de datos actuales detectan ataques DESPUÉS de que ocurren.

✗  Firewalls / IDS con reglas fijas → solo detectan ataques conocidos
✗  Análisis manual de logs: lento, costoso, no escala
✗  Sin respuesta automática: requiere intervención humana

¿Cómo detectar y responder a comportamientos anómalos
en tiempo real, antes de que causen daño?
```

### Oralidad
> "Los sistemas de seguridad tradicionales trabajan con reglas estáticas. Solo detectan lo que ya conocen. Además, requieren que alguien revise alertas manualmente. La pregunta que guía este trabajo es: ¿cómo podemos detectar comportamientos anómalos automáticamente y responder en tiempo real?"

---

## SLIDE 4 — Objetivos
**Tiempo:** 1 min

### Texto en pantalla
```
OG: Desarrollar un sistema de detección temprana y control inline
    de comportamientos anómalos, empleando Isolation Forest
    y mecanismos automáticos de bloqueo en tiempo real.

OE1 — Construir pipeline de captura y procesamiento de tráfico
      que genere un dataset válido para entrenamiento.

OE2 — Entrenar y validar modelo de detección con AUC-ROC ≥ 0.80
      sobre datos reales de laboratorio.

OE3 — Integrar el modelo en motor de decisión con control
      automático de acceso y validarlo bajo escenarios reales.
```

### Visual
- Árbol: OG → OE1, OE2, OE3 con colores distintos
- `d4_problema.md` tiene el draw.io XML listo

### Oralidad
> "Nuestro objetivo general fue construir un sistema completo, no solo un modelo. Que detecte Y que actúe. Los tres objetivos van de lo más técnico —los datos y el modelo— hasta la integración y validación en vivo."

---

## SLIDE 5 — Pipeline en 6 Fases
**Tiempo:** 1 min

### Texto en pantalla
```
[F1 Captura] → [F2 Modelo IF] → [F3 Motor]  → [F4 XGBoost] → [F5 Aprend.] → [F6 Valid.]
  Suricata       IF n=300        PERMIT/LIMIT   Predictor       Auto-          40 corridas
  47 capturas    AUC=0.8998      /BLOCK+ipset   AUC=0.9992      reentren.      P95=34.8ms
                 τ1/τ2                                           cron noche
                                 ← F3 es el CORE del sistema →
```

### Visual
- Pipeline horizontal 6 cajas (usar draw.io XML de `d2_pipeline.md`)
- F3 más grande y destacado
- Flecha retroalimentación F5 → F3/F4 (hot-reload)

### Oralidad
> "La metodología sigue un pipeline de 6 fases encadenadas. F1 captura con Suricata. F2 entrena el Isolation Forest y deriva umbrales de decisión. F3 es el motor en producción — es el core. F4 predice si el ataque va a persistir con XGBoost. F5 reentrena automáticamente cada noche. F6 validó todo con 40 corridas."

---

## SLIDE 6 — F1 y F2: Captura y Modelo
**Tiempo:** 1 min

### Texto en pantalla
```
F1 — Captura con Suricata 7.0.3
  Entrada : tráfico real de red (9 escenarios: A normal, B anómalo, C mixto)
  Proceso : ens35 modo pasivo → eve.json → gzip + truncate por corrida
  Salida  : 47 capturas (.json.gz) · 667,420 flujos registrados

F2 — Dataset + Isolation Forest    (fase3_entrenar.py + fase3_evaluar.py)
  Entrada : data/raw/*_normal_*.gz · data/raw/*_anom_*.gz
  Proceso : extraer 14 features · split 80/20 aleatorio (random_state=42)
            IsolationForest(n_estimators=300, contamination=0.05)
            Curva ROC → τ1 por Youden · τ2 por FPR≤2%
  Salida  : models/isolation_forest.pkl · models/scaler.pkl
            results/metricas_offline.txt · results/auc_roc.png

  AUC-ROC = 0.8998  ·  Precision = 99.54%  ·  Recall = 99.40%
  τ1 = −0.4459 (Youden · PERMIT/LIMIT)
  τ2 = −0.6027 (FPR ≤ 2% · LIMIT/BLOCK)
```

### Visual
- Flujo: [47.gz] → [fase3_entrenar] → [IF pkl] → [fase3_evaluar] → [τ1/τ2]
- Curva ROC con τ1 y τ2 marcados (imagen F2_modelo_IF/f2_auc_roc_curva.png)
- Tabla compacta 14 features (dos columnas)

### Oralidad
> "F1 es trabajo de laboratorio: Suricata captura todo en pasivo, sin interferir. 47 capturas de 9 escenarios: HTTP normal, SSH, SYN flood, brute force, UDP flood."
>
> "F2: de cada flujo extraemos 14 características —paquetes, bytes, duración, ratios, protocolo. Entrenamos el IF con 53,708 flujos normales. El modelo aprende qué es normal y asigna scores: más negativo = más anómalo. De la curva ROC sacamos dos umbrales estadísticos — τ1 por índice de Youden, τ2 donde el FPR cae al 2%."

---

## SLIDE 7 — F3–F6: Motor, Predictor, Aprendizaje y Validación
**Tiempo:** 1 min

### Texto en pantalla
```
F3 — Motor de decisión + control inline    (motor_decision.py — servicio 24/7)
  Entrada : eve.json (tail en tiempo real) · isolation_forest.pkl · scaler.pkl
  Proceso : 14 features → score IF → clasificar con τ1/τ2
            score > −0.4459      → PERMIT  (log INFO)
            −0.6027 < s ≤ −0.4459 → LIMIT   → SSH → servidor: ipset hashlimit 100pkt/s
            score ≤ −0.6027      → BLOCK   → SSH → servidor: ipset DROP kernel
            score_medio < −0.35 (10 flows) → Telegram 👀 TENDENCIA (pre-alerta)
            Heurístico BF-SSH:   ≥5/60s → LIMIT · ≥15/60s → BLOCK
            Heurístico HTTP:     ≥50/30s → LIMIT · ≥100/30s → BLOCK
            Bloqueo progresivo:  #1=300s · #2=1800s · #3=PERMANENTE (timeout=0)
  Salida  : motor_decision.log · block_counts.json · ipset servidor · Telegram · Dashboard :8080

F4 — Predictor XGBoost v2                 (predictor.py — ciclo 10s)
  Entrada : motor_decision.log (eventos LIMIT+BLOCK) · predictor_modelo_v2.pkl
  Proceso : 9 features comportamentales · predict_proba() → P ∈ [0,1]
            P ≥ 0.70 → ALERTA-PREDICTIVA (Telegram 🚨 + dashboard 🔴)
  Salida  : predictor.log · Telegram alertas · dashboard panel predictor
  AUC-ROC = 0.9992 · 9 features sin score (leakage corregido)

F5 — Aprendizaje continuo                 (cron en sensor 192.168.0.110)
  IF:      domingos 02:00 → reentrena con nuevas capturas normales
           Guarda si AUC no retrocede > 0.02
  XGBoost: diario 03:00   → reentrena con log de últimas 24h
           Guarda si AUC ≥ 0.70 y no retrocede > 0.05
  Hot-reload: predictor.py detecta mtime del .pkl → recarga en ≤10s sin reiniciar

F6 — Validación: 40 corridas · 4 grupos × 10 · 5 min/corrida
  Grupos: Normal (solo whitelisted) · Mixto (primera detección) ·
          Reeval (Kali ya bloqueada) · Final (bloqueo consolidado)
  Disponibilidad = 100% · ITL = 0% · Latencia P95 = 34.8ms
  Lead time SYN Flood ≈ 62s · BF SSH BLOCK = 60s · CA-16 FPR nuevos datos = 0.0%
```

### Visual
- Resaltar F3 como core (borde grueso verde o azul)
- Diagrama flujo: `d3_flujo.md` tiene XML draw.io

### Oralidad
> "F3 es el motor en producción. Lee eve.json en tiempo real — cada flujo nuevo — extrae features, obtiene el score del IF y decide. PERMIT si es normal, LIMIT si es sospechoso —lo frena a 100 paquetes por segundo en el servidor vía SSH—, o BLOCK —DROP directo en el kernel. Hay además un nivel previo: si el score promedio de los últimos 10 flows cae bajo −0.35 mientras todavía es PERMIT, manda alerta de tendencia. Y un bloqueo progresivo: 5 minutos, 30 minutos, permanente."
>
> "F4 es el predictor XGBoost que lee el log del motor y predice si el ataque va a persistir. F5 reentrena automáticamente cada noche sin intervención humana. F6 validó todo con 40 corridas estructuradas."

---

## SLIDE 8 — Producto: ¿Qué hace?
**Tiempo:** 1 min

### Texto en pantalla
*(Una sola frase, grande, centrada):*
```
SURIKATA — Sistema de Detección y Control Inteligente de Tráfico de Red

Detecta ataques en tiempo real y los bloquea automáticamente
sin intervención humana, en menos de 35 milisegundos.

[📡 Detecta]          [🧠 Decide]          [🛡️ Bloquea]
 tráfico anómalo       en <35ms              automáticamente
 con ML               sin humano             en el kernel del servidor
```

### Oralidad
> "El producto detecta, decide y bloquea. Ese es el core."

---

## SLIDE 9 — Arquitectura General
**Tiempo:** 1.5 min

### Texto en pantalla
```
Arquitectura — 4 nodos, 1 red (192.168.0.0/24)

[Win11 Cliente 192.168.0.10]     [Kali Atacante 192.168.0.100]
                    ↓                         ↓
            ─────────────── RED ───────────────────
                                  ↓
                   [Ubuntu Sensor 192.168.0.110]
                    Suricata 7.0.3 · ens35 promiscuo
                    motor_decision.py · IF + XGBoost
                    predictor.py · dashboard_web.py
                           ↓ SSH + sudo ipset add
                   [Ubuntu Server 192.168.0.120]
                    nginx:80 · SSH:22
                    iptables + ipset ppi_blocked / ppi_limited
```

### Visual
- Diagrama de topología (usar draw.io XML de `d1_topologia.md`)
- Flechas coloreadas: azul=normal, rojo=ataque, naranja=SSH ipset

### Oralidad
> "Cuatro nodos. El sensor corre Suricata en modo promiscuo — captura todo el tráfico. El motor con el modelo ML decide qué hacer. Cuando decide BLOCK, hace SSH al servidor y ejecuta el comando ipset. El servidor tiene el firewall —iptables + ipset— que descarta los paquetes del atacante en el kernel."

---

## SLIDE 10 — Flujo de Decisión
**Tiempo:** 1.5 min

### Texto en pantalla
```
Ciclo de decisión — latencia P95 = 34.8ms

  Suricata → eve.json (nuevo flujo)
       ↓
  ¿IP en whitelist? → SÍ → PERMIT (sin cálculo IF)
       ↓ NO
  score = IF.decision_function(scaler.transform(14 features))
       ↓
  score > −0.4459 (τ1)              →  PERMIT ✅
  −0.6027 < score ≤ −0.4459         →  LIMIT ⚠️  (hashlimit 100 pkt/s)
  score ≤ −0.6027 (τ2)              →  BLOCK 🚫  (DROP kernel)
  score_medio_10flows < −0.35        →  👀 TENDENCIA (Telegram aviso)
       ↓
  BLOCK → SSH → servidor → ipset add ppi_blocked <IP> timeout [300/1800/0]
  BLOCK → Telegram 🚨 + Dashboard 🔴 + predictor.log
```

### Visual
- Diagrama de flujo vertical (usar draw.io XML de `d3_flujo.md`)
- Línea de umbrales: [BLOCK |−0.6027| LIMIT |−0.4459| PERMIT →]
- Imagen F2_modelo_IF/f2_distribucion_scores.png (distribución scores normal vs anómalo)

### Oralidad
> "El ciclo: Suricata detecta, el motor extrae features y el IF da un score. Si está por encima de τ1, es normal. Entre τ2 y τ1, sospechoso —lo limitamos. Por debajo de τ2, anómalo — DROP en el kernel del servidor. Los umbrales vienen de la curva ROC: τ1 maximiza el índice de Youden, τ2 fija el FPR al 2%."

---

## SLIDE 11 — Demo: Bloqueo Progresivo en Vivo
**Tiempo:** 2 min ← SLIDE MÁS IMPORTANTE

### Texto en pantalla
```
Validación en vivo — SYN Flood B1 (2026-06-22) · Kali → Servidor

┌──────────────────────────────────────────────────────────────────────┐
│ Corrida │  Timestamp  │  Trigger                  │ Resultado │ ipset │
├──────────────────────────────────────────────────────────────────────┤
│   1ª    │  05:44:13   │  IF score=−0.6066          │ BLOCK #1  │ 300s  │
│   2ª    │  06:05:03   │  IF score=−0.7696          │ BLOCK #2  │ 1800s │
│   3ª    │  06:39:42   │  HTTP-ABUSE 100 req/30s    │ BLOCK #3  │ ∞ PERM│
└──────────────────────────────────────────────────────────────────────┘

$ ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
Members:
  192.168.0.100 timeout 0    ← SIN timeout = PERMANENTE

block_counts.json: {"192.168.0.100": 3}
```

### Visual — capturas de pantalla reales
- **CAPTURA A:** `tail motor_decision.log | grep BLOCK` — 3 líneas de bloqueo
- **CAPTURA B:** `ssh 192.168.0.120 "sudo ipset list ppi_blocked"` — timeout=0
- **CAPTURA C (opcional):** Telegram con alerta recibida

### Oralidad
> "Esto es validación real. Esta mañana ejecutamos tres corridas de SYN Flood desde Kali contra el servidor."
>
> "Primera: score −0.6066, bajo τ2. BLOCK número 1: 5 minutos. Segunda corrida —después de expirar— score −0.7696. BLOCK número 2: 30 minutos. Tercera: el detector de HTTP Abuse registró 100 solicitudes en 30 segundos. BLOCK número 3: permanente."
>
> "Aquí está el ipset del servidor: timeout=0. Sin expiración. El bloqueo es definitivo hasta que un administrador lo levante manualmente."
>
> *(Pausa. Dejar que el jurado lo absorba.)*

---

## SLIDE 11b — Demo: BF SSH + Telegram
**Tiempo:** 1 min (usar como respaldo o integrar en slide 11)

### Texto en pantalla
```
Validación adicional — B6 SSH Brute Force (2026-06-22 08:31)
Herramienta: hydra -l admin -P wordlist ssh://192.168.0.120 -t 4

┌───────────────────────────────────────────────────────────┐
│ Evento       │ T desde inicio │ Score IF  │ Tipo          │
├───────────────────────────────────────────────────────────┤
│ 1ª detección │ T + 53s        │ −0.4832   │ LIMIT → WARN  │
│ BLOCK        │ T + 60s        │ −0.6228   │ BRUTE_FORCE_SSH│
└───────────────────────────────────────────────────────────┘

Alerta Telegram recibida (08:31:37):
🚨 PPI ALERTA — BRUTE_FORCE_SSH
   Accion : BLOCK (DROP)   IP: 192.168.0.100
   Puerto : 22   Score: −0.6228
```

### Visual
- Screenshot de Telegram con la alerta
- Línea de tiempo: T+0 → T+53s LIMIT → T+60s BLOCK

### Oralidad
> "Para BF SSH: Hydra con 4 hilos. En 53 segundos, alerta LIMIT —5 intentos en ventana de 60s. En 60 segundos exactos, BLOCK —15 intentos superados. Y aquí está la alerta que llegó al teléfono: puerto 22, score −0.6228, 08:31:37. El administrador sabe antes de llegar a la oficina."

---

## SLIDE 12 — Dashboard Web
**Tiempo:** 1 min

### Texto en pantalla
```
Visibilidad en tiempo real — http://192.168.0.110:8080

[Screenshot del dashboard web con alertas activas]

· Flujos clasificados en tiempo real: PERMIT / LIMIT / BLOCK
· IPs bloqueadas activas con timeout restante
· Panel predictor XGBoost: P% por IP · AVISO / ALERTA-PREDICTIVA
· Actualización automática vía Server-Sent Events (SSE) — sin polling
```

### Visual
- Screenshot del dashboard web (capturar con alertas visibles)
- Mostrar panel con Kali en lista de bloqueados

### Oralidad
> "El sistema no opera en negro. Dashboard web en el sensor, accesible desde cualquier navegador. Muestra flujos, bloqueos activos, predicciones del XGBoost. Se actualiza solo en tiempo real."

---

## SLIDE 13 — Resultados
**Tiempo:** 2 min

### Texto en pantalla
```
Resultados — 16/16 criterios de aceptación cumplidos

OE1 — Pipeline F1+F2                OE2 — Modelo IF (F2)         OE3 — Motor + Valid. (F3–F6)
────────────────────                ────────────────             ────────────────────────────
✅ 9 escenarios · 3 grupos          ✅ AUC-ROC    = 0.8998       ✅ Latencia P95   = 34.8ms (<500ms)
✅ 47 capturas (.json.gz)           ✅ Precision  = 99.54%       ✅ Disponibilidad = 100%
✅ 14 features por flujo            ✅ Recall     = 99.40%       ✅ ITL            = 0%
✅ 667,420 flujos etiquetados       ✅ F1-Score   = 0.9947       ✅ 40 corridas · 4 grupos × 10
✅ 53,708 flujos entrenamiento      ✅ τ1 = −0.4459 (Youden)     ✅ Lead time SYN Flood  ≈ 62s
✅ Split 80/20 aleatorio            ✅ τ2 = −0.6027 (FPR ≤ 2%)  ✅ Lead time BF SSH     = 60s
                                    ✅ FPR@τ1 = 20.47%*         ✅ XGBoost v2 AUC       = 0.9992
                                       *FPR operativo = 0%       ✅ Bloqueo #3 PERMANENTE validado
                                       (whitelist activa)        ✅ Telegram alerta (HTTP 200) ✅
                                    ✅ CA-16: FPR datos nuevos   ✅ Predictor ALERTA-PREDICTIVA
                                       = 0.0% (119 flows)          P=77.39% en SYN Flood

── OBJETIVO GENERAL ──────────────────────────────────────────────────────────────────────
  Sistema funcional de extremo a extremo · F1→F6 implementadas y validadas
  16/16 criterios de aceptación PASS · laboratorio real · sin intervención humana
```

### Visual — 3 figuras de graficas_f6/
- `f6_07_panel_resumen.png` — panel resumen 7-en-1 (principal)
- `f6_03_timeline_deteccion.png` — lead time por escenario
- `f6_06_latencia_pipeline.png` — distribución latencia P95

### Oralidad
> "Los resultados responden directamente a los tres objetivos."
>
> "OE1: pipeline completo — 9 escenarios, 47 capturas, 667 mil flujos etiquetados, split 80/20 aleatorio."
>
> "OE2: AUC de 0.8998 —por encima del criterio de 0.80—, Precision y Recall del 99%. Los umbrales derivados estadísticamente de la curva ROC. El FPR de 20.47% en τ1 es la única limitación conocida, pero el FPR operativo es cero porque la whitelist protege todos los hosts legítimos. Adicionalmente, validamos con 119 flujos normales nuevos de una sesión diferente — FPR 0.0%, el modelo generaliza correctamente."
>
> "OE3: 40 corridas, latencia P95 de 34.8ms — catorce veces por debajo del límite —, disponibilidad 100%, cero interrupciones de tráfico legítimo. Lead time 62s y 60s. XGBoost AUC 0.9992. Bloqueo permanente validado en vivo. Telegram recibido. 16 de 16 criterios de aceptación: todos PASS."

---

## SLIDE 14 — Conclusiones
**Tiempo:** 1 min

### Texto en pantalla
```
Conclusiones

1. Es posible construir un sistema de detección en tiempo real con
   Isolation Forest sin conocimiento previo del ataque (one-class),
   latencia < 35ms y AUC-ROC = 0.8998 sobre tráfico real de laboratorio.

2. El pipeline completo F1→F6 funciona de extremo a extremo con
   disponibilidad del 100%, ITL = 0% y lead time ≤ 62s en todos
   los vectores de ataque validados.

3. El bloqueo progresivo (5 min → 30 min → permanente) y el predictor
   XGBoost (AUC=0.9992) añaden capas de control adaptativo y anticipación
   que los firewalls estáticos no ofrecen.
```

### Oralidad
> "Tres conclusiones. Primero: IF en modo no supervisado es suficientemente robusto para detección en tiempo real. Segundo: el sistema funciona de punta a punta — no es prototipo académico, corrió con 40 escenarios reales. Tercero: el bloqueo progresivo y el predictor XGBoost son mejoras concretas sobre firewalls estáticos."

---

## SLIDE 15 — Trabajos Futuros + Cierre
**Tiempo:** 30 seg

### Texto en pantalla
```
Trabajos futuros

→ Despliegue en infraestructura de producción real
→ Extensión a tráfico cifrado (TLS fingerprinting)
→ Federación de sensores múltiples
→ Reentrenamiento F5 en entorno de producción (base implementada)


"El sistema detecta, decide y bloquea.
 Sin intervención humana. En menos de 35ms."

                    Gracias.
```

### Oralidad
> "El trabajo abre líneas claras de extensión, sobre todo hacia entornos reales y tráfico cifrado. La base de reentrenamiento automático ya está implementada en F5."
>
> *(Pausa, mirar al jurado.)*
>
> "El sistema detecta, decide y bloquea. Sin intervención humana. En menos de 35 milisegundos. Muchas gracias. Quedamos a disposición para las preguntas."

---

---

## Capturas de pantalla para el PPT

| # | Qué capturar | Dónde | Estado |
|---|---|---|---|
| 1 | `motor_decision.log` — 3 bloques B1 (05:44, 06:05, 06:39) | `grep "BLOCK\|bloqueo" results/motor_decision.log \| grep "192.168.0.100"` | ⏳ pendiente |
| 2 | `ipset list ppi_blocked` con timeout=0 en servidor | `ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"` | ⏳ pendiente (requiere bloqueo#3 activo) |
| 3 | Dashboard web con alertas activas | `http://192.168.0.110:8080` | ⏳ pendiente |
| 4 | Telegram alerta BRUTE_FORCE_SSH o BLOCK | Teléfono / Telegram Web | ⏳ pendiente captura pantalla |
| 5 | `cat results/metricas_offline.txt` | En sensor | ⏳ pendiente |
| 6 | `cat results/metricas_predictor_v2.txt` | En sensor | ⏳ pendiente |
| 7 | `crontab -l` con los 2 jobs F5 | En sensor | ⏳ pendiente |
| 8 | `bash scripts/validacion/run_all.sh` — 16/16 PASS | En sensor | ✅ Log guardado en `results/validacion_20260622_150405.log` |

---

## Figuras de graficas_f6/ para el PPT

| Figura | Slide | Descripción |
|---|---|---|
| `f6_07_panel_resumen.png` | Slide 13 principal | Panel 7-en-1 todas las métricas |
| `f6_03_timeline_deteccion.png` | Slide 13 | Lead time por escenario |
| `f6_06_latencia_pipeline.png` | Slide 13 | Distribución latencia P95 |
| `f6_01_disponibilidad.png` | Slide 13 soporte | 40/40 barras verdes |
| `f6_02_flows_anomalos.png` | Slide 10 opcional | Flujos anómalos por escenario |
| `f2_auc_roc_curva.png` | Slide 6 | Curva ROC con τ1/τ2 |
| `f2_distribucion_scores.png` | Slide 10 | Distribución scores normal vs anómalo |

---

## Diagramas draw.io listos para pegar

| Diagrama | Slide | Archivo XML | Estado |
|---|---|---|---|
| Topología de red | Slide 9 | `ppt/d1_topologia.md` | ✅ listo |
| Pipeline 6 fases | Slide 5 | `ppt/d2_pipeline.md` | ✅ listo |
| Flujo de decisión | Slide 10 | `ppt/d3_flujo.md` | ✅ listo |
| Problema + OE árbol | Slides 3+4 | `ppt/d4_problema.md` | ✅ listo |

---

## Checklist de preparación

### Sistema validado ✅
- [x] 16/16 criterios de aceptación PASS (run_all.sh 2026-06-22 15:04)
- [x] CA-16 PASS — FPR=0.0% en 119 flows normales nuevos
- [x] Bloqueo #3 permanente (timeout=0) — validado 06:39:42
- [x] BF SSH lead time 60s — validado 08:31:37
- [x] Telegram alerta recibida — HTTP 200 confirmado
- [x] Whitelist Desktop — 0 BLOCK/LIMIT en 120 req HTTP
- [x] XGBoost ALERTA-PREDICTIVA P=77.39% en SYN Flood
- [x] metricas_offline.txt: AUC=0.8998, τ1=−0.4459, τ2=−0.6027
- [x] metricas_predictor_v2.txt: AUC=0.9992, FP=7, FN=7
- [x] latencia_pipeline.txt: P95=34.768ms

### Por hacer antes de la sustentación
- [ ] Tomar capturas de pantalla (ver tabla de capturas arriba)
- [ ] Exportar figuras de graficas_f6/ a PC de presentación
- [ ] Copiar diagramas draw.io a draw.io/Canva/PowerPoint
- [ ] Construir el PPT en la herramienta elegida (Canva, PowerPoint, Google Slides)
- [ ] Ensayar con cronómetro: objetivo 20 minutos + 2.5 preguntas
- [ ] Preparar respuestas Q&A (ver `defensa/LIMITACIONES.md`)
- [ ] Verificar que el projector muestra correctamente las figuras PNG

### Para la demo en vivo (opcional)
```bash
# Mostrar motor corriendo en tiempo real:
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# Mostrar dashboard web:
# Abrir http://192.168.0.110:8080 en navegador

# Ejecutar suite de validación:
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```
