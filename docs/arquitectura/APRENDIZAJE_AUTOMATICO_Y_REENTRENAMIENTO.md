# Aprendizaje Automático y Reentrenamiento — PPI UPeU 2026
## ¿El sistema debe aprender solo? ¿Cómo se entrena? ¿Qué conservamos?

**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha:** 2026-06-21

---

## 1. ¿Debe el sistema aprender por sí solo? — Respuesta directa

**Sí, pero con una distinción importante según el componente:**

| Componente | ¿Auto-reentrenamiento? | Frecuencia | Razón |
|---|---|---|---|
| **Isolation Forest (IF)** | ❌ No automático | Solo cuando cambia la red | "Normal" es definido por un humano, no el log |
| **XGBoost Predictor v2** | ✅ Sí, automático | Semanal | Sus etiquetas nacen solas del log sin intervención |

La diferencia clave:

- El **IF** aprende qué es tráfico *normal*. Eso requiere juicio humano — si la red cambia (nuevo servidor, nueva aplicación), hay que capturar nuevo tráfico normal y reentrenar manualmente. No puede hacerlo solo sin supervisión.

- El **Predictor XGBoost** aprende cuándo un evento LIMIT escala a BLOCK. Esa relación vive completamente en `motor_decision.log` y las etiquetas se generan automáticamente: si un LIMIT de una IP va seguido de un BLOCK en los próximos 10s → label=1. El sistema puede hacer esto solo.

---

## 2. Por qué el predictor puede aprender solo — concepto académico

Este tipo de aprendizaje se llama **self-supervised learning** (aprendizaje auto-supervisado):

```
Sistema en producción
        │
        ▼
motor_decision.log crece continuamente
        │
        ├── Evento: SOSPECHOSO src=192.168.0.100 LIMIT  (T=0s)
        │
        └── Evento: ANOMALÍA   src=192.168.0.100 BLOCK  (T=7s)
                   │
                   └── Label automático: LIMIT → BLOCK en 10s = 1 (positivo)

Si LIMIT ocurre pero NO hay BLOCK en los siguientes 10s → label = 0 (negativo)
```

No necesita etiquetas manuales. El log se etiqueta solo porque el motor ya tomó la decisión (BLOCK o no BLOCK). El predictor aprende de las decisiones pasadas del propio sistema.

**Dato real disponible hoy (2026-06-21):**

```
motor_decision.log — período 2026-06-02 al 2026-06-21 (20 días)
  Líneas totales:  1,178,733
  Eventos LIMIT:      50,134  ← entradas de entrenamiento
  Eventos BLOCK:      11,977  ← fuente de etiquetas positivas
  Ratio positivos: ~24%       ← dataset razonablemente balanceado
```

Estos 50,134 eventos LIMIT son el dataset de entrenamiento. Ya existe. No hay que generar más datos.

---

## 3. Los dos modelos del sistema — roles y ciclos de vida distintos

### Modelo 1 — Isolation Forest (detector, ya entrenado)

```
¿Qué aprende?    Cómo es el tráfico NORMAL de esta red
¿Cómo?           One-class: solo ve ejemplos normales
¿Cuándo reentrenar? Solo si cambia la naturaleza del tráfico legítimo
                    (nuevo servidor, nueva app, cambio de topología)
¿Quién decide?   El administrador de red (juicio humano requerido)
¿Estado actual?  ✅ Entrenado, AUC=0.8998, en producción — NO CAMBIAR
```

**El IF no se toca.** Está funcionando con Precision=99.54%. Reentrenarlo sin causa introduce riesgo de degradar el modelo.

### Modelo 2 — XGBoost Predictor (anticipador, a reentrenar)

```
¿Qué aprende?    Cuándo un LIMIT va a escalar a BLOCK (en esta red, con estos ataques)
¿Cómo?           Supervisado: label viene automáticamente del log
¿Cuándo reentrenar? Automáticamente, cada semana (o cuando hay nuevos escenarios de ataque)
¿Quién decide?   El propio sistema (script programado)
¿Estado actual?  ⚠️ Señal incorrecta (gap/STATS) → cambiar a señal LIMIT
```

---

## 4. La fase de entrenamiento del Predictor v2 — paso a paso

### 4.1 ¿Conservamos los escenarios de F2? — Sí y no

Los escenarios F2 (A1–A4 normales, B1–B6 anómalos, C1–C3 mixtos) generaron `eve.json.gz` que fue usado para entrenar el **IF**. Esos datos NO se usan directamente para entrenar el predictor v2.

El predictor v2 se entrena sobre `motor_decision.log`, no sobre `eve.json`. La razón:

```
eve.json      → contiene flujos individuales (features de red)
               → para entrenar el IF (¿es este flujo anómalo?)

motor_decision.log → contiene decisiones del motor (LIMIT/BLOCK con timestamps)
                   → para entrenar el predictor (¿este LIMIT va a escalar a BLOCK?)
```

Los escenarios F2 contribuyeron indirectamente: al ejecutarlos, el motor generó los eventos LIMIT/BLOCK que ahora están en `motor_decision.log`. No hay que repetir nada.

### 4.2 Dataset de entrenamiento — construcción automática

```
motor_decision.log
    │
    ▼
Script: entrenar_predictor_v2.py
    │
    ├── PASO 1: Extraer todos los eventos LIMIT del log
    │   Ejemplo: "2026-06-19 16:21:12 | SOSPECHOSO | src=192.168.0.100 score=-0.47 | LIMIT"
    │
    ├── PASO 2: Para cada LIMIT, mirar si hay BLOCK de misma IP en los 10s siguientes
    │   LIMIT @ T=0s, BLOCK @ T=7s → label = 1 (BLOCK inminente)
    │   LIMIT @ T=0s, sin BLOCK en T=10s → label = 0 (no escaló)
    │
    ├── PASO 3: Construir features para cada LIMIT
    │   feat = {
    │     'limit_count_15s':  cuántos LIMITs de esa IP en los 15s previos,
    │     'limit_rate_15s':   LIMITs por segundo en esa ventana,
    │     'score_min_15s':    score más bajo visto en esa ventana,
    │     'score_mean_15s':   score promedio en esa ventana,
    │     'hora_sin':         sin(2π × hora / 24),
    │     'hora_cos':         cos(2π × hora / 24),
    │   }
    │
    ├── PASO 4: Split cronológico (no aleatorio)
    │   Train: 70%  (datos más antiguos)
    │   Val:   15%
    │   Test:  15%  (datos más recientes — evalúa generalización)
    │
    └── PASO 5: Entrenar XGBoost, evaluar, guardar modelo
        → models/predictor_modelo_v2.pkl
        → results/metricas_predictor_v2.txt
```

### 4.3 El ciclo de reentrenamiento automático

Una vez implementado, el sistema puede reentrenarse solo con este flujo:

```
┌─────────────────────────────────────────────────────────┐
│           CICLO DE AUTO-REENTRENAMIENTO (semanal)       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Domingo 02:00 (sin tráfico)                            │
│       │                                                 │
│       ▼                                                 │
│  entrenar_predictor_v2.py                               │
│       │                                                 │
│       ├── Lee motor_decision.log completo               │
│       ├── Construye dataset auto-etiquetado             │
│       ├── Entrena XGBoost con split cronológico         │
│       ├── Evalúa en test: AUC, Precision, Recall        │
│       │                                                 │
│       ├── ¿AUC nuevo > AUC anterior?                    │
│       │     SÍ → reemplaza predictor_modelo_v2.pkl      │
│       │     NO → conserva modelo anterior               │
│       │                                                 │
│       └── predictor.py recarga modelo en próximo ciclo │
│           (hot-reload: comprueba fecha del .pkl)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

El servicio `ppi-predictor` no necesita reiniciarse. El script de predicción verifica si el archivo `.pkl` cambió y lo recarga automáticamente.

---

## 5. Flujo completo del aprendizaje — desde escenario hasta predicción

```
FASE F2 — Escenarios de laboratorio
┌─────────────────────────────────────────────────────┐
│  Desktop (normal): curl, scp, wget, ssh             │
│  Kali (anómalo): hping3, nmap, hydra                │
│       │                                             │
│       ▼                                             │
│  Suricata → eve.json.gz  (datos crudos de red)      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
FASE F3 — Entrenamiento del IF (una sola vez)
┌─────────────────────────────────────────────────────┐
│  eve.json → parser.py → dataset_clean.csv           │
│  Solo tráfico normal (70% train) → IF.fit()         │
│  → isolation_forest.pkl  (modelo permanente)        │
│  AUC=0.8998, Precision=99.54%, Recall=99.40%        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
FASE F4/F5 — Motor en producción (continuo)
┌─────────────────────────────────────────────────────┐
│  motor_decision.py corre 24/7                       │
│  Evalúa cada flujo → PERMIT / LIMIT / BLOCK         │
│  Escribe en motor_decision.log (crece ~50K líneas/día)│
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
FASE F7 — Entrenamiento del Predictor v2 (primera vez + auto)
┌─────────────────────────────────────────────────────┐
│  motor_decision.log → entrenar_predictor_v2.py      │
│  50,134 LIMIT + 11,977 BLOCK disponibles hoy        │
│  Auto-etiquetado: LIMIT→BLOCK/10s = label           │
│  XGBoost.fit() → predictor_modelo_v2.pkl            │
│                                                     │
│  Auto-reentrenamiento: cada semana (cron)           │
│  Hot-reload: predictor.py recarga sin reiniciarse   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
FASE F7 — Predictor en producción (continuo, ciclo 2s)
┌─────────────────────────────────────────────────────┐
│  predictor.py corre 24/7                            │
│  Lee motor_decision.log cada 2s                     │
│  Cuenta LIMITs en ventana 15s → XGBoost → P(BLOCK) │
│  P≥0.70 → ALERTA-PREDICTIVA (antes del BLOCK)       │
└─────────────────────────────────────────────────────┘
```

---

## 6. Ciclo de vida completo del sistema — autonomía por capa

### Lo que ocurre sin ninguna intervención humana (24/7)

```
Siempre corriendo:
  ppi-motor.service     → detecta y bloquea (restart=always)
  ppi-predictor.service → predice y alerta  (restart=always)
  ppi-dashboard.service → visualiza          (restart=always)

Cada semana (cron automático — domingo 02:00):
  entrenar_predictor_v2.py → reentrena si mejora AUC
  predictor.py hot-reload  → recarga modelo sin cortar servicio

Nunca automático (requiere humano):
  Reentrenar IF            → solo si cambia la red legítima
  Agregar nuevos escenarios→ solo para capturar nuevos tipos de ataque
  Ajustar τ1/τ2            → solo si FPR/TPR del IF se degrada
```

### Lo que el administrador hace periódicamente (mantenimiento ligero)

```
Mensual:
  Revisar metricas_predictor_v2.txt → ¿AUC sigue sobre 0.75?
  Revisar FPR del IF en producción  → ¿hay muchos falsos positivos?
  Revisar bitácora de ataques       → ¿hay nuevos tipos no vistos?

Solo si hay cambios en la red:
  Capturar nuevo tráfico normal (escenarios A1-A4)
  Reentrenar IF manualmente
  Recalcular τ1/τ2 con nueva curva ROC
```

---

## 7. Comparación: entrenamiento v1 vs v2

### Predictor v1 (actual — señal de gap/STATS)

```
Dataset:    Gaps temporales entre líneas STATS (cada 500 flujos)
            11,376 observaciones generadas manualmente
Etiquetas:  Manuales — corridas etiquetadas como "ataque" o "normal"
Features:   gap, gap_lag1..3, gap_mean5, gap_std5, bloqueados, hora
Problema:   Señal aparece 34s+ después del inicio del ataque
            → no puede anticipar el BLOCK del IF
Auto-regen: No — requiere correr corridas y etiquetar manualmente
```

### Predictor v2 (nuevo — señal de LIMIT como precursor)

```
Dataset:    Eventos LIMIT del motor + etiqueta automática (→BLOCK en 10s?)
            50,134 observaciones YA DISPONIBLES en motor_decision.log
Etiquetas:  Automáticas — el motor mismo genera BLOCK o no
Features:   limit_count_15s, limit_rate, score_min, score_mean, hora
Ventaja:    Señal aparece en T≈1s desde inicio del ataque
            → ALERTA en T≈2s, BLOCK del IF en T≈5s → predictor anticipa
Auto-regen: SÍ — el log crece solo, las etiquetas se generan solas
```

---

## 8. Implementación del hot-reload (recarga sin reiniciar)

Para que el predictor recargue el modelo automáticamente cuando cambia:

```python
# En predictor.py — agregar en el bucle principal:

MODEL_PATH = BASE / 'models' / 'predictor_modelo_v2.pkl'
_modelo_mtime = MODEL_PATH.stat().st_mtime  # timestamp del archivo

while True:
    # Verificar si el modelo fue actualizado
    mtime_actual = MODEL_PATH.stat().st_mtime
    if mtime_actual != _modelo_mtime:
        clf = joblib.load(MODEL_PATH)
        _modelo_mtime = mtime_actual
        log.info(f"Modelo recargado automáticamente ({MODEL_PATH.name})")
    
    # ... resto del ciclo de predicción
    time.sleep(INTERVALO)
```

Esto permite que el cron del domingo actualice `predictor_modelo_v2.pkl` y el servicio lo recargue en el siguiente ciclo de 2s sin necesidad de `systemctl restart`.

---

## 9. Cron de auto-reentrenamiento — implementación

```bash
# En el sensor (192.168.0.110)
# Agregar con: crontab -e

# Reentrenamiento automático del predictor — domingos 2 AM
0 2 * * 0 /home/m4rk/ppi-sensor/venv/bin/python3 \
    /home/m4rk/ppi-surikata-producto/scripts/entrenar_predictor_v2.py \
    >> /home/m4rk/ppi-surikata-producto/results/reentrenamiento.log 2>&1
```

El script de entrenamiento:
1. Lee `motor_decision.log`
2. Construye dataset auto-etiquetado
3. Entrena XGBoost
4. Si AUC_nuevo > AUC_anterior → reemplaza el `.pkl`
5. Si AUC_nuevo ≤ AUC_anterior → conserva el modelo anterior y registra en log
6. Escribe `metricas_predictor_v2.txt` con la fecha y métricas

---

## 10. Justificación académica — por qué este diseño es correcto

### Self-supervised learning en seguridad de redes

El enfoque de auto-etiquetado que usamos (LIMIT→BLOCK = label positivo) es una forma de **weak supervision** o **programmatic labeling**, reconocida en la literatura de ML aplicado a ciberseguridad:

- Las etiquetas son ruidosas pero consistentes (el motor IF ya validó que BLOCK es correcto con 99.54% de precisión)
- El volumen compensa el ruido (50K+ muestras)
- El split cronológico garantiza evaluación realista

### Por qué no usar online learning (aprendizaje en línea puro)

El **online learning** (actualizar pesos por cada muestra) con XGBoost no es nativo y tiene riesgos:

- **Concept drift malicioso:** un atacante podría enviar tráfico diseñado para "enseñar" al modelo que sus ataques son normales
- **Inestabilidad:** un burst anómalo podría degradar el modelo en minutos
- **Trazabilidad:** un modelo que cambia constantemente no es auditado

El **reentrenamiento semanal por batch** es más seguro y auditado:
- El modelo cambia solo en horario de bajo riesgo (domingo 2 AM)
- Hay un historial de versiones de modelos
- Un humano puede revisar las métricas antes de validar el cambio
- Si el modelo se degrada, el sistema conserva el anterior automáticamente

### Arquitectura de dos velocidades — justificación

El sistema implementa lo que la literatura llama **two-speed architecture**:

```
Velocidad rápida (tiempo real):
  IF + ipset → respuesta en milisegundos
  Predictor → respuesta en segundos
  Dashboard SSE → actualización en tiempo real

Velocidad lenta (aprendizaje):
  Reentrenamiento XGBoost → semanal
  Reentrenamiento IF → cuando cambia la red (meses/años)
```

Esta separación es un patrón reconocido en sistemas de ML en producción (Lambda Architecture, Kappa Architecture) y es directamente defendible ante el asesor.

---

## 11. Resumen para la defensa — qué decir sobre el aprendizaje

> "El sistema implementa dos ciclos de aprendizaje con distintas velocidades. El Isolation Forest fue entrenado una sola vez sobre tráfico normal de laboratorio y no requiere reentrenamiento mientras la red no cambie. El módulo XGBoost predictor en cambio utiliza aprendizaje auto-supervisado: extrae automáticamente etiquetas del log de producción (eventos LIMIT que escalan a BLOCK) y puede reentrenarse semanalmente mediante un cron, recargando el modelo en caliente sin interrumpir el servicio. Esto da al sistema capacidad de adaptación ante nuevos patrones de ataque sin intervención manual continua."

**Datos que respaldan esto:**
- 50,134 eventos LIMIT y 11,977 BLOCK disponibles desde el 2 de junio
- Dataset completamente auto-generado por el propio motor en producción
- Cero etiquetado manual necesario para el predictor v2
- El IF mantiene AUC=0.8998 estable desde su entrenamiento inicial
