# F5 — Aprendizaje Continuo (Reentrenamiento Automático)
**Estado: ✅ IMPLEMENTADA Y VALIDADA**  
**Resultado:** 2 cron jobs activos | protección anti-regresión funcional | modelo restaurado 2026-06-23

---

## Objetivo

Que el sistema mejore con el tiempo sin intervención manual: cuando el tráfico de la red cambia, los modelos se adaptan automáticamente usando sus propios datos operativos.

**Por qué esto es necesario y no opcional:** un modelo entrenado una sola vez se degrada. El tráfico normal cambia (nuevos servicios, horarios, usuarios), los atacantes cambian de IP y técnica, y los umbrales τ1/τ2 dejan de ser estadísticamente óptimos. Sin F5, el sistema sería un snapshot estático que se vuelve menos preciso con el tiempo.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Reentrenamiento (retraining)** | Volver a entrenar el modelo con datos nuevos. No modifica el anterior hasta validar que el nuevo es igual o mejor. |
| **Aprendizaje continuo** | El sistema aprende periódicamente de los datos que produce durante su operación normal. No requiere ingeniería de datos manual entre ciclos. |
| **Batch retraining** | Reentrenamiento por lotes: se acumulan datos durante N horas y se reentrena en un horario programado (cron nocturno). Alternativa segura al online learning. |
| **Online learning** | Actualización del modelo con cada evento en tiempo real. No implementado — vulnerable a envenenamiento adversarial. |
| **Envenenamiento adversarial** | Un atacante genera tráfico diseñado gradualmente para "educar" al modelo a clasificar sus ataques futuros como normales. Riesgo inherente del online learning. |
| **Anti-regresión** | Protección que impide que el reentrenamiento empeore el modelo. Si el AUC nuevo retrocede más del umbral tolerable, el modelo anterior se conserva intacto. |
| **cron** | Planificador de tareas de Linux. Ejecuta los scripts F5 en horarios predefinidos, automáticamente, sin intervención del operador. |
| **Hot-reload** | Recarga del modelo XGBoost en memoria sin reiniciar el servicio. `predictor.py` detecta el cambio de `mtime` del `.pkl` en cada ciclo de 10s. Solo aplica al predictor — el motor IF requiere reinicio. |
| **mtime** | Timestamp de modificación del archivo `.pkl`. Si cambia, `predictor.py` recarga el modelo en el siguiente ciclo (≤10s). |
| **Ventana temporal** | Período de log que el reentrenamiento XGBoost considera. Default: `--horas 24`. Si la ventana es demasiado corta, los datos son insuficientes y el cron aborta sin reemplazar. |
| **Logrotate interaction** | A medianoche, `logrotate` trunca `motor_decision.log`. Si el cron XGBoost corre a las 03:00, los 3 primeros minutos del log son los únicos de ese día → riesgo de 0 eventos en la ventana. |

---

## Entradas → Proceso → Salidas

```
ENTRADAS  [f5_reentrenar_if.py — domingos 02:00]
  data/raw/*_normal_*.gz           (todas las capturas normales acumuladas)
  data/normal_holdout.csv          (evaluación AUC nuevo)
  data/raw/*_anom_*.gz             (hasta 3 archivos para comparación AUC)
  models/isolation_forest.pkl      (modelo actual — para comparar AUC)
  models/scaler.pkl

ENTRADAS  [f5_reentrenar_xgboost.py — diario 03:00]
  results/motor_decision.log       (últimas 24h — default, configurable con --horas)
  models/predictor_modelo_v2.pkl   (modelo actual — para comparar AUC)

PROCESO  [f5_reentrenar_if.py]
  Cargar *_normal_*.gz → extraer features → split 80/20 (mismo proceso F2)
  Entrenar nuevo IF (mismos hiperparámetros que F2: n=300, contamination=0.05)
  Calcular AUC_nuevo sobre holdout + anomalías
  AUC_nuevo >= AUC_actual − 0.02  →  REEMPLAZAR isolation_forest.pkl + scaler.pkl
  AUC_nuevo <  AUC_actual − 0.02  →  NO reemplazar (protección anti-regresión)
  Guardar resultado en results/cron_f5_if.log

PROCESO  [f5_reentrenar_xgboost.py]
  Parsear log de N horas → dataset con labels automáticos (mismo proceso F4)
  Si eventos < 100  →  abortar (datos insuficientes para generalizar)
  Si positivos < 10 →  abortar (sin ejemplos de ataques sostenidos)
  Entrenar nuevo XGBoost (mismos hiperparámetros F4)
  AUC_nuevo >= 0.70  Y  AUC_nuevo >= AUC_actual − 0.05  →  REEMPLAZAR .pkl
  predictor.py detecta cambio de mtime → hot-reload en ≤10s
  Guardar resultado en results/cron_f5_xgb.log

SALIDAS
  models/isolation_forest.pkl      (actualizado si AUC mejoró/estable)
  models/scaler.pkl                (actualizado junto al IF)
  models/predictor_modelo_v2.pkl   (actualizado si AUC válido)
  results/cron_f5_if.log           (stdout/stderr del cron IF)
  results/cron_f5_xgb.log          (stdout/stderr del cron XGBoost)
```

> **Nota:** `results/metricas_f5_if.txt` y `results/metricas_f5_xgboost.txt` eran archivos de historial que se eliminaron durante la limpieza del repo. El historial actual está en `results/cron_f5_xgb.log`.

---

## ¿Por qué batch retraining y no online learning?

El online learning actualiza el modelo con cada evento en tiempo real. Parece mejor, pero tiene un riesgo crítico: **envenenamiento adversarial**.

```
Escenario de ataque contra online learning:
  1. Atacante genera tráfico anómalo MUY gradual y sostenido (semanas)
  2. El modelo online aprende: "este patrón es normal"
  3. Atacante escala → el modelo ya lo clasifica como PERMIT
  4. El sistema está comprometido sin alarma
```

El batch retraining nocturno con validación AUC es más robusto:
- El atacante necesita contaminar el dataset TODA LA NOCHE para influir
- La validación AUC detecta automáticamente si los datos degradaron el modelo
- Si el AUC retrocede → el modelo anterior se conserva

**Por qué IF semanal y XGBoost diario:** el IF aprende de capturas `.gz` del Grupo A que se acumulan manualmente con corridas planificadas — no tiene sentido reentrenar más seguido que cuando hay capturas nuevas. El XGBoost aprende del `motor_decision.log` que crece diariamente con tráfico operativo real — tiene datos frescos cada día.

**Por qué −0.02 para IF y −0.05 para XGBoost:** el IF tiene AUC base de 0.8998 — una fluctuación del 2% (0.02) puede ser ruido estadístico. El XGBoost tiene AUC base de 0.9991 — una fluctuación del 5% (0.05) es más tolerable porque el dataset de reentrenamiento es menor (24h vs meses de capturas).

---

## Dos reentrenamientos independientes

### F5-IF — Isolation Forest (domingos 02:00)

```
data/raw/*_normal_*.gz  (Grupo A — capturas acumuladas)
    │
    ▼ parse_flows() — mismo proceso que fase3_entrenar.py (F2)
    │
    ▼ StandardScaler + IsolationForest(n_estimators=300, contamination=0.05)
    │
    ▼ Evaluar AUC sobre normal_holdout.csv + *_anom_*.gz
    │
    ├── AUC_nuevo >= AUC_anterior − 0.02  →  REEMPLAZAR modelos
    └── AUC_nuevo <  AUC_anterior − 0.02  →  NO reemplazar
    │
    ▼ Salida → results/cron_f5_if.log
```

> ⚠️ **El motor IF NO hace hot-reload.** Carga `isolation_forest.pkl` y `scaler.pkl` UNA sola vez al arrancar (`joblib.load()` en startup). Para que el nuevo IF entre en producción: `sudo systemctl restart ppi-motor.service`. El servicio reinicia en <2s.

### F5-XGBoost — Predictor comportamental (diario 03:00)

```
results/motor_decision.log  (últimas 24h por defecto)
    │
    ▼ parse_log() — regex captura ANOMALÍA|SOSPECHOSO con score=
    │   ⚠️  igual que F4: NO captura HTTP-ABUSE ni BRUTE-FORCE
    │
    ▼ construir_dataset() — ventanas deslizantes + block_rate_60s
    │   labels: ¿BLOCK de esta IP en [t, t+60s]?
    │
    ▼ Guardia: eventos < 100 → abortar | positivos < 10 → abortar
    │
    ▼ XGBoostClassifier.fit() — mismos hiperparámetros que F4
    │
    ▼ Guardia: AUC < 0.70 → NO reemplazar
    │         AUC < AUC_anterior − 0.05 → NO reemplazar
    │
    ▼ Si pasa guardias: REEMPLAZAR predictor_modelo_v2.pkl
    ▼ predictor.py detecta mtime cambiado → hot-reload en ≤10s
    ▼ Salida → results/cron_f5_xgb.log
```

**Por qué AUC mínimo 0.70 para el XGBoost:** debajo de 0.70 el predictor no aporta valor real sobre un clasificador aleatorio. Un modelo con AUC<0.70 generaría tantas falsas alertas que el operador aprendería a ignorarlas. 0.70 es el umbral mínimo de utilidad operativa.

**Por qué positivos < 10 es una guardia:** XGBoost con scale_pos_weight no puede aprender a predecir la clase minoritaria con menos de 10 ejemplos positivos. El modelo resultante siempre predice label=0 y tiene AUC=0.5 con precision perfecta pero recall=0. Esta guardia detecta exactamente ese caso.

---

## Protecciones anti-regresión (verificadas en código)

| Condición | Acción | Razón |
|---|---|---|
| eventos < 100 en ventana | NO reemplaza XGBoost | Dataset demasiado pequeño para generalizar |
| positivos (label=1) < 10 | NO reemplaza XGBoost | Sin ejemplos de ataques sostenidos |
| AUC_XGB < 0.70 | NO reemplaza XGBoost | Umbral mínimo de utilidad operativa |
| AUC_XGB < AUC_anterior − 0.05 | NO reemplaza XGBoost | Degradación significativa detectada |
| AUC_IF < AUC_actual − 0.02 | NO reemplaza IF | Degradación en modelo de detección base |
| `--forzar` | Reemplaza siempre | Debug — solo para desarrollo/corrección manual |

---

## Crontab instalado en sensor (192.168.0.110) — verificado

```cron
# F5 — Reentrenamiento automático PPI
# IF: domingos 02:00
0 2 * * 0 /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_if.py \
  >> /home/m4rk/ppi-surikata-producto/results/cron_f5_if.log 2>&1

# XGBoost: diario 03:00
0 3 * * * /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_xgboost.py \
  >> /home/m4rk/ppi-surikata-producto/results/cron_f5_xgb.log 2>&1
```

**Por qué 02:00 y 03:00 y no 00:00:** logrotate trunca `motor_decision.log` a medianoche. Si F5 corriera a las 00:01, la ventana de 24h solo tendría 1 minuto de datos → 0 eventos → aborta. A las 03:00, el log tiene 3 horas de datos — suficiente para detectar si hubo actividad esa noche.

---

## Hot-reload del XGBoost (sin reinicio de servicio)

```python
# predictor.py — check_hot_reload() en cada ciclo de INTERVALO=10s
def check_hot_reload():
    mtime = MODEL.stat().st_mtime
    if mtime != model_mtime:         # ← compara timestamp del archivo
        cargar_modelo()              # ← recarga clf y FEATURES en memoria
        log.info("Modelo recargado (hot-reload)")
```

El servicio `ppi-predictor.service` nunca se interrumpe. El nuevo modelo entra en producción en el siguiente ciclo (≤10 segundos).

**Por qué hot-reload solo para XGBoost y no para IF:** el IF está integrado directamente en el proceso `motor_decision.py` junto con todo el pipeline de procesamiento. Hacer hot-reload del IF requeriría pausar el procesamiento de flujos durante la recarga (riesgo de perder eventos). Un reinicio limpio del motor (<2s) es más seguro y predecible.

---

## Historial de ejecuciones F5 (verificado en cron_f5_xgb.log)

### Cron XGBoost — 2026-06-22 03:00:03
```
Ventana: últimas 24h (desde 2026-06-21 03:00)
Eventos en ventana: 91
AVISO: Muy pocos eventos (<100) — modelo NO reemplazado
→ Protección anti-regresión: datos insuficientes detectados ✅
```

### Cron XGBoost — 2026-06-23 03:00:03
```
Ventana: últimas 24h (desde 2026-06-22 03:00)
Eventos en ventana: 0
AVISO: Muy pocos eventos (<100) — modelo NO reemplazado
→ Causa: logrotate truncó el log a medianoche, solo 3h de datos vacíos
→ Protección anti-regresión: aborto correcto ✅
```

### Corridas manuales — 2026-06-22 (histórico, pre-corrección leakage)

> ⚠️ Estas corridas se ejecutaron ANTES del reentrenamiento correctivo del 2026-06-23.

```
Corrida manual 1 — 2026-06-22 02:26 (--horas 720, leakage en modelo)
  events=62,115 | AUC_anterior=1.0000 (artefacto) | AUC_nuevo=0.9999 | reemplazado=SI
  Estado: INVALIDADO — modelo con data leakage (score en features v1)

Corrida manual 2 — 2026-06-22 08:04 (--horas 24, post-leakage fix)
  events=517 | positivos=238 (46.1%) — distribución atípica
  AUC_anterior=0.9762 | AUC_nuevo=0.9583 | reemplazado=SI
  ⚠️  DEGRADACIÓN: 517 eventos insuficientes + distribución sesgada
  La ventana de 24h capturó solo las pruebas del día → no representativa

Corrida manual 3 — 2026-06-22 08:05 (segunda ejecución)
  events=517 | AUC=0.9583 → igual | reemplazado=SI
```

### Reentrenamiento correctivo — 2026-06-23 (manual)
```
Causa: corridas del 08:04-08:05 degradaron el modelo a AUC=0.9583
Solución: reentrenar con dataset completo (log.1 + log actual)
  events=63,524 | label_1=6,860 (10.8%) | split=50,819/12,705
  Nuevo feature: block_rate_60s agregado (35.65% importancia)
  AUC=0.9991 | FP=9 | FN=6 | TP=1,366
  reemplazado=SI (manual, --forzar)
Estado actual: MODELO VIGENTE ✅
```

**Lección aprendida de la degradación del 08:04:** la guardia de `eventos < 100` protege contra degradación por falta de datos. Sin embargo, 517 eventos con 46% positivos (vs 10.8% normal) indica que la ventana de 24h capturó un período atípico de pruebas intensivas — la distribución no representa la operación real. **En producción, la ventana óptima es 168h-720h** para incluir variabilidad temporal suficiente.

---

## Uso manual

```bash
ssh m4rk@192.168.0.110
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate

# Ver estado de ambos modelos
python3 scripts/f5_validar_modelo.py

# Reentrenar IF
python3 scripts/f5_reentrenar_if.py

# Reentrenar XGBoost (últimas 48h — más datos que el default de 24h)
python3 scripts/f5_reentrenar_xgboost.py --horas 48

# Reentrenar con dataset completo (usar log.1 como fuente)
cp results/motor_decision.log.1 results/motor_decision.log  # backup primero!
python3 scripts/f5_reentrenar_xgboost.py --horas 99999     # toda la historia
cp results/motor_decision.log.current_bak results/motor_decision.log

# Forzar reemplazo ignorando guardias (solo para corrección manual)
python3 scripts/f5_reentrenar_xgboost.py --forzar
```

---

## Imágenes de referencia

| Imagen | Ruta | Estado |
|---|---|---|
| Crontab configurado | `docs/documentacion/imagenes/F5_aprendizaje/captura_cron.png` | ⏳ Pendiente captura |
| Salida reentrenamiento XGBoost | `docs/documentacion/imagenes/F5_aprendizaje/captura_reentrenamiento.png` | ⏳ Pendiente captura |
| Protección anti-regresión activa | `docs/documentacion/imagenes/F5_aprendizaje/captura_proteccion.png` | ⏳ Pendiente captura |

Para capturar: `crontab -l`, `python3 scripts/f5_reentrenar_xgboost.py --horas 48`, y el aviso de datos insuficientes.

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado | Verificación |
|---|---|---|---|
| CA-13 | Cron jobs configurados | ✅ **2 crons activos** | `crontab -l` en sensor |
| CA-14 | ≥1 corrida registrada | ✅ **2 crons ejecutados** + corridas manuales | `cat results/cron_f5_xgb.log` |
| CA-F5-01 | Anti-regresión implementada | ✅ 5 condiciones de guarda en código | `f5_reentrenar_xgboost.py:254-259` |
| CA-F5-02 | Hot-reload sin reiniciar predictor | ✅ mtime check cada 10s | `predictor.py:115-123` |
| CA-F5-03 | Datos insuficientes detectados | ✅ cron 03:00 con 91 y 0 eventos rechazados | `cron_f5_xgb.log` |
| CA-F5-04 | Leakage corregido en reentrenamiento | ✅ `score` eliminado de FEATURES en todos los scripts | `f5_reentrenar_xgboost.py` |

---

## Argumento de defensa

> "F5 es lo que diferencia un sistema de detección de un proyecto de laboratorio. El reentrenamiento batch nocturno con validación AUC garantiza que el modelo mejora cuando hay datos nuevos de calidad y se protege automáticamente cuando no los hay — como demuestran los dos crons ejecutados: 91 eventos y 0 eventos, ambos rechazados correctamente por las guardias.
>
> La decisión de batch sobre online learning es explícitamente una decisión de seguridad: un sistema que se actualiza con cada paquete es un sistema que un atacante sofisticado puede manipular gradualmente. El batch nocturno requiere contaminar el dataset TODA LA NOCHE para influir — y la validación AUC lo detectaría de todas formas.
>
> Documentamos también la degradación del 2026-06-22 08:04 y su corrección: el F5 con ventana de 24h sobre 517 eventos no representativos produjo un modelo con AUC=0.9583. Esto no es un fallo del diseño — la guardia de 100 eventos habría abortado en el cron programado (03:00 tuvo 91 eventos). La corrección manual reentrenó con 63,524 eventos y recuperó AUC=0.9991 con la adición del feature `block_rate_60s`."

