# F5 — Aprendizaje Continuo (Reentrenamiento Automático)
**Estado: ✅ IMPLEMENTADA Y VALIDADA**  
**Resultado:** 2 cron jobs activos | 3 corridas registradas | protección anti-regresión funcional

---

## Objetivo

Que el sistema mejore con el tiempo sin intervención manual: cuando el tráfico de la red cambia, los modelos se adaptan automáticamente usando sus propios datos operativos. Esto diferencia un sistema de detección estático de uno que aprende.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Reentrenamiento (retraining)** | Volver a entrenar el modelo con datos nuevos. No "olvida" el anterior — lo reemplaza si el nuevo es mejor. |
| **Aprendizaje continuo** | El sistema aprende de forma periódica de los datos que produce durante su operación normal. No requiere ingeniería de datos manual entre ciclos. |
| **Batch retraining** | Reentrenamiento por lotes: se acumulan datos durante N horas/días y se reentrena en un momento programado. Alternativa más segura que el online learning (ver sección de diseño). |
| **Online learning** | Actualización del modelo con cada nuevo evento en tiempo real. Más reactivo pero vulnerable a envenenamiento adversarial. No implementado por seguridad. |
| **Envenenamiento adversarial** | Técnica de ataque donde el adversario genera tráfico diseñado para "educar" al modelo a clasificar sus ataques futuros como normales. Riesgo del online learning. |
| **Anti-regresión** | Protección que impide que el reentrenamiento empeore el modelo. Si el AUC nuevo retrocede más del umbral tolerable, el modelo anterior se conserva. |
| **cron** | Planificador de tareas de Unix/Linux. Ejecuta comandos en horarios predefinidos. Los scripts F5 se configuran como cron jobs en el sensor. |
| **Hot-reload** | Recarga del modelo en memoria sin reiniciar el proceso. `predictor.py` detecta cambios en el archivo `.pkl` y recarga automáticamente. Minimiza interrupciones. |
| **mtime** | Timestamp de modificación de un archivo (`st_mtime`). El predictor compara el mtime del `.pkl` en cada ciclo para detectar si fue actualizado. |
| **Ventana temporal** | Período de datos que el reentrenamiento considera. `--horas 24` usa las últimas 24h del log. `--horas 720` usa los últimos 30 días. |
| **AUC anterior** | Métrica del modelo activo en producción, medida sobre los mismos datos de test del nuevo modelo. Base de comparación. |
| **reemplazado=SI/NO** | Flag en `metricas_f5_*.txt`. SI = el nuevo modelo pasó el umbral de calidad y reemplazó al anterior. NO = el nuevo no fue suficientemente bueno. |

---

## Entradas → Proceso → Salidas

```
ENTRADAS  [f5_reentrenar_if.py — domingos 02:00]
  data/raw/*_normal_*.gz              (todas las capturas normales acumuladas)
  data/normal_holdout.csv             (evaluación AUC)
  data/raw/*_anom_*.gz               (hasta 3 archivos para comparación AUC)
  models/isolation_forest.pkl         (modelo actual — para comparar AUC)

ENTRADAS  [f5_reentrenar_xgboost.py — diario 03:00]
  results/motor_decision.log          (últimas N horas — default 24h)
  models/predictor_modelo_v2.pkl     (modelo actual — para comparar AUC)

PROCESO  [f5_reentrenar_if.py]
  Cargar *_normal_*.gz → extraer features → split 80/20
  Entrenar nuevo IF (mismos params que F2)
  Calcular AUC_nuevo sobre holdout + anomalías
  AUC_nuevo >= AUC_actual - 0.02  → reemplazar isolation_forest.pkl + scaler.pkl
  AUC_nuevo <  AUC_actual - 0.02  → NO reemplazar (protección anti-regresión)
  Registrar resultado en metricas_f5_if.txt

PROCESO  [f5_reentrenar_xgboost.py]
  Parsear log de N horas → dataset con labels automáticos (mismo que F4)
  Si eventos < 100 o positivos < 10 → abortar (datos insuficientes)
  Entrenar nuevo XGBoost
  AUC_nuevo >= 0.70 Y AUC_nuevo >= AUC_actual - 0.05 → reemplazar .pkl
  predictor.py detecta cambio de mtime → hot-reload en ≤10s (sin reiniciar)
  Registrar resultado en metricas_f5_xgboost.txt

SALIDAS
  models/isolation_forest.pkl         (actualizado si AUC mejoró/estable)
  models/scaler.pkl                   (actualizado junto al IF)
  models/predictor_modelo_v2.pkl     (actualizado si AUC válido)
  results/metricas_f5_if.txt          (historial: fecha|flows|AUC_ant|AUC_new|reemplazado)
  results/metricas_f5_xgboost.txt     (historial: fecha|horas|events|AUC_ant|AUC_new|P|R)
  results/cron_f5_if.log              (stdout/stderr del cron IF)
  results/cron_f5_xgb.log            (stdout/stderr del cron XGBoost)
```


---

## ¿Por qué es necesario F5?

Un modelo entrenado una sola vez se desactualiza:
- El tráfico normal cambia (nuevos servicios, más usuarios, horarios)
- Los atacantes cambian de IP, técnica o intensidad
- Los umbrales τ1/τ2 fijos dejan de ser óptimos

| Sin F5 | Con F5 |
|---|---|
| Detecta bien el día del entrenamiento | Mejora con cada semana de operación |
| Se vuelve menos preciso con el tiempo | Se adapta al tráfico real de la red |
| Requiere intervención manual para actualizar | Automático, sin downtime |

---

## Dos reentrenamientos independientes

### F5-IF — Isolation Forest (domingos 02:00)

**Qué aprende:** a partir de nuevas capturas normales (`.gz` del Grupo A), actualiza qué es "normal" para el IF.

```
data/raw/*_normal_*.gz   (todos los que existan en data/raw/)
    │
    ▼ parse_flows() — mismo proceso que F2
    │
    ▼ StandardScaler + IsolationForest(n_estimators=300)
    │
    ▼ Evaluar AUC nuevo vs AUC anterior (sobre holdout + anomalías)
    │
    ├── AUC_nuevo >= AUC_anterior - 0.02  →  REEMPLAZAR modelos
    └── AUC_nuevo <  AUC_anterior - 0.02  →  NO reemplazar + aviso
    │
    ▼ Guardar: isolation_forest.pkl | scaler.pkl | metricas_f5_if.txt
```

> El motor IF requiere `systemctl restart ppi-motor.service` para recargar el nuevo modelo.

### F5-XGBoost — Predictor comportamental (diario 03:00)

**Qué aprende:** a partir del `motor_decision.log` de las últimas N horas, actualiza los patrones de comportamiento de IPs atacantes.

```
results/motor_decision.log  (últimas 24h por defecto)
    │
    ▼ parse_log() — extrae eventos LIMIT+BLOCK
    │
    ▼ construir_dataset() — mismo proceso que F4
    │   labels automáticos: ¿BLOCK de esta IP en próximos 60s?
    │
    ▼ XGBoostClassifier.fit(X_train, y_train)
    │
    ▼ Evaluar AUC nuevo vs AUC anterior
    │
    ├── AUC_nuevo >= 0.70  Y
    │   AUC_nuevo >= AUC_anterior - 0.05  →  REEMPLAZAR modelo
    └── AUC_nuevo < 0.70  O
        AUC_nuevo < AUC_anterior - 0.05   →  NO reemplazar + aviso
    │
    ▼ Guardar: predictor_modelo_v2.pkl → predictor.py detecta mtime → hot-reload
```

---

## Protecciones anti-regresión

| Condición | Qué pasa | Por qué existe |
|---|---|---|
| AUC_IF_nuevo < AUC_IF_anterior − 0.02 | NO reemplaza IF | Degradación detectada — datos nuevos de mala calidad |
| AUC_XGB_nuevo < 0.70 | NO reemplaza XGBoost | Umbral mínimo de calidad |
| AUC_XGB_nuevo < AUC_XGB_anterior − 0.05 | NO reemplaza XGBoost | Degradación significativa |
| Eventos < 100 en ventana | NO reemplaza XGBoost | Datos insuficientes para generalizar |
| Positivos < 10 | NO reemplaza XGBoost | No hay suficientes ataques en la ventana |
| `--forzar` | Reemplaza siempre | Debug — solo para desarrollo |

---

## Crontab instalado en sensor (192.168.0.110)

```cron
# F5 — Reentrenamiento automático PPI UPeU 2026

# IF: domingos 02:00 (semanal)
0 2 * * 0 /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_if.py \
  >> /home/m4rk/ppi-surikata-producto/results/cron_f5_if.log 2>&1

# XGBoost: diario 03:00
0 3 * * * /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_xgboost.py \
  >> /home/m4rk/ppi-surikata-producto/results/cron_f5_xgb.log 2>&1
```

---

## Hot-reload del XGBoost (sin reinicio de servicio)

```python
# En predictor.py — ciclo de 10 segundos (INTERVALO=10)
mtime_actual = Path(MODEL_PATH).stat().st_mtime
if mtime_actual != self._mtime_anterior:
    self._modelo = joblib.load(MODEL_PATH)
    self._mtime_anterior = mtime_actual
    log.info("Predictor: modelo F5 recargado en caliente")
```

El servicio `ppi-predictor.service` nunca se interrumpe. El nuevo modelo entra en operación en el siguiente ciclo (≤10 segundos).

---

## Historial de corridas F5 (registrado en metricas_f5_*.txt)

### Isolation Forest — 2026-06-22 02:27
```
flows_entrenamiento : 53,708
AUC anterior        : 0.9548
AUC nuevo           : 0.9548    (igual — random_state=42 reproduce el resultado)
Reemplazado         : SI        (calidad idéntica, modelo actualizado)
```

### XGBoost — corrida 1 (2026-06-22 02:26) — INVALIDADA
```
horas=720 | events=62,115
AUC anterior : 1.0000    ← artefacto de data leakage (score en features)
AUC nuevo    : 0.9999    ← ídem
Reemplazado  : SI        ← modelo con leakage
Estado       : INVALIDADO — ver corrección leakage en F4
```

### XGBoost — corrida 2 (2026-06-22 08:04) — VÁLIDA
```
horas=24 | events=517 | positivos=238 (46.1%)
AUC anterior : 0.9762    ← modelo F4 corregido (sin leakage)
AUC nuevo    : 0.9583    (bajó 0.0179 — dentro del margen de ±0.05)
Precision    : 97.96%
Recall       : 97.96%
Reemplazado  : SI        ← degradación aceptable, datos de ventana corta
```

### XGBoost — corrida 3 (2026-06-22 08:05) — VÁLIDA
```
horas=24 | events=517
AUC anterior : 0.9583    ← modelo de la corrida 2
AUC nuevo    : 0.9583    (igual)
Reemplazado  : SI        ← estable
```

### Protección en acción — cron 03:00 (ventana pequeña)
```
horas=24 | events=91
AVISO: Muy pocos eventos (<100) — modelo NO reemplazado
→ La protección funcionó: datos insuficientes detectados automáticamente
```

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

# Reentrenar XGBoost (últimas 48h)
python3 scripts/f5_reentrenar_xgboost.py --horas 48

# Forzar reemplazo (debug)
python3 scripts/f5_reentrenar_xgboost.py --forzar
```

---

## ¿Por qué batch y no online learning?

El online learning actualiza el modelo con cada evento en tiempo real. Parece mejor, pero tiene un riesgo crítico: **envenenamiento adversarial**.

Un atacante sofisticado podría:
1. Generar tráfico anómalo de forma muy gradual y sostenida
2. El modelo online aprende que ese patrón "es normal"
3. El atacante escala el ataque — el modelo ya no lo detecta

El batch retraining nocturno con validación de AUC es más robusto:
- El atacante necesita sostener el ataque TODA LA NOCHE para influir
- La validación AUC detecta si los nuevos datos degradaron el modelo
- Los 24h de log proveen contexto temporal suficiente

---

## Imágenes de referencia (pendientes de captura)

| Imagen | Descripción |
|---|---|
| `F5_aprendizaje/captura_cron_configurado.png` | `crontab -l` con los 2 cron jobs activos |
| `F5_aprendizaje/captura_reentrenamiento_xgb.png` | Salida de `f5_reentrenar_xgboost.py` con comparación AUC |
| `F5_aprendizaje/captura_metricas_f5_historial.png` | `cat results/metricas_f5_xgboost.txt` con 3 corridas |
| `F5_aprendizaje/captura_proteccion_antiregresion.png` | Aviso "muy pocos eventos — modelo no reemplazado" |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado |
|---|---|---|
| CA-13 | Cron jobs de reentrenamiento configurados | ✅ 2 crons activos |
| CA-14 | ≥1 corrida de reentrenamiento registrada | ✅ 3 corridas documentadas |
| CA-F5-01 | Protección anti-regresión implementada | ✅ 5 condiciones de guarda |
| CA-F5-02 | Hot-reload sin reiniciar ppi-predictor.service | ✅ mtime check cada 10s (INTERVALO=10) |
| CA-F5-03 | Datos insuficientes detectados automáticamente | ✅ cron 03:00 con 91 eventos rechazado |
| CA-F5-04 | Leakage corregido en reentrenamiento | ✅ score eliminado de FEATURES en v2 |

---

## Argumento de defensa

> "F5 es lo que hace que el sistema sea de largo plazo y no un proyecto de laboratorio que se degrada. El reentrenamiento batch nocturno con validación AUC garantiza que el modelo mejora cuando hay datos nuevos de calidad y se protege solo cuando no los hay. El hot-reload del XGBoost asegura que las mejoras entran en producción en segundos sin interrumpir el monitoreo. La decisión de batch sobre online learning es una decisión de seguridad: un sistema que se actualiza con cada paquete es un sistema que un atacante sofisticado puede manipular."
