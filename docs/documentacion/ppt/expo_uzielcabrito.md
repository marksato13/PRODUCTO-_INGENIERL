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
  Proceso : 10 features comportamentales · predict_proba() → P ∈ [0,1]
            P ≥ 0.70 → ALERTA-PREDICTIVA (Telegram 🚨 + dashboard 🔴)
  Salida  : predictor.log · Telegram alertas · dashboard panel predictor
  AUC-ROC = 0.9992 · 10 features sin score (leakage corregido)

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

