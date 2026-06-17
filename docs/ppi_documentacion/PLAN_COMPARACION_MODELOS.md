# PLAN MAESTRO — Comparación Experimental de Modelos de Detección de Anomalías

**Proyecto:** PPI UPeU — Detección temprana de comportamientos anómalos en redes  
**Objetivo:** Demostrar científicamente que Isolation Forest es la elección óptima para este dataset  
**Fecha:** 2026-06-17  
**Estado:** PLANIFICACIÓN — implementar fase por fase

---

## Contexto real del dataset (antes de planificar)

| Variable | Valor real | Fuente |
|---|---|---|
| Flows normales en entrenamiento | **53,708** | `fase3_entrenar.py` — `*_normal_*.gz` |
| Flows normales holdout (20%) | **13,427** | `data/normal_holdout.csv` |
| Flows anómalos en evaluación | **598,285** | `*_anom_*.gz` (13 archivos) |
| Features | **14** (todas numéricas) | `models/features.csv` |
| Features binarias (0/1) | **3** (`is_tcp`, `is_udp`, `is_icmp`) | idem |
| Features continuas | **11** | idem |
| Features temporales independientes | **0** (duration es una feature derivada, no timestamp) | — |
| Etiquetas en entrenamiento | **0** (one-class: solo tráfico normal) | `fase3_entrenar.py` |
| Etiquetas disponibles para evaluación | **Sí** (implícitas: archivos normal=0, anom=1) | nombres de archivos |
| Ratio normal:anómalo en evaluación | ~1:44 | 13,427 / 598,285 |
| IF actual AUC-ROC | **0.8998** | `results/metricas_offline.txt` |
| IF actual Recall (τ1) | **99.40%** | idem |
| IF actual Precision (τ1) | **99.54%** | idem |
| IF actual F1 | **0.9947** | idem |
| sklearn versión | **1.9.0** | venv sensor |

**Naturaleza del problema:** SEMI-SUPERVISADO
- El entrenamiento es no supervisado (solo normal, sin etiquetas)
- La evaluación tiene ground truth implícito (origen del archivo = etiqueta)
- Esto permite construir un dataset etiquetado para comparar con supervisados

---

## Estructura del plan

```
FASE 1 — Análisis formal del dataset                     [~1h]  → FASE1_ANALISIS.md
FASE 2 — Tabla de compatibilidad de modelos             [~30min] → FASE2_COMPATIBILIDAD.md
FASE 3 — Construcción del dataset etiquetado            [~1h]  → FASE3_DATASET_SUPERVISADO.md
FASE 4 — Experimentos: entrenar y medir todos los modelos [~3h] → FASE4_EXPERIMENTOS.md
FASE 5 — Análisis de resultados + tablas comparativas   [~1h]  → FASE5_RESULTADOS.md
FASE 6 — Justificación final con evidencia              [~1h]  → FASE6_JUSTIFICACION.md
FASE 7 — Propuesta de mejora (ensemble si aplica)       [~2h]  → FASE7_MEJORAS.md
FASE 8 — Documentos finales para la tesis               [~1h]  → FASE8_DOCS_TESIS.md
```

**Duración total estimada:** ~11 horas de trabajo  
**Output final:** 2 documentos para tesis + evidencia experimental completa

---

## FASE 1 — Análisis formal del dataset

**Archivo de implementación:** `FASE1_ANALISIS.md`  
**Script a crear:** `scripts/comparacion/f_analisis_dataset.py`  
**Output:** `results/comparacion/01_analisis_dataset.txt`

### Qué analizará el script

1. **Dimensiones:** n_flows, n_features, distribución por tipo
2. **Estadísticas por feature:**
   - Min, Max, Media, Mediana, Desviación estándar, Skewness, Kurtosis
   - Separación normal vs anómalo por feature (test de Mann-Whitney U)
3. **Distribución de etiquetas:**
   - Normal: 13,427 | Anomalía: 598,285 → ratio 1:44.5
   - Por tipo de ataque: synflood, portscan, udpflood, icmpflood, httpabuse, bruteforce
4. **Naturaleza del problema:**
   - ¿Supervisado? ❌ No — entrenamiento sin etiquetas
   - ¿Semi-supervisado? ✅ Sí — evaluación con ground truth implícito
   - ¿No supervisado? Parcialmente — el paradigma de entrenamiento es one-class
5. **Características que determinan la compatibilidad de modelos:**
   - Alta dimensionalidad relativa (14 features)
   - Desbalance extremo (1:44)
   - Ausencia de etiquetas en entrenamiento (real)
   - Flujos de red con distribuciones no normales (skewed)
   - Escalas muy diferentes entre features (pkts ≈ 2-5, byte_rate ≈ miles)

### Conclusión esperada del análisis

El dataset es **semi-supervisado con paradigma de entrenamiento one-class**, lo que:
- Favorece directamente modelos one-class (IF, OCSVM, LOF)
- Permite comparación con supervisados **solo si se construye un dataset etiquetado** (Fase 3)
- Hace que DBSCAN y Autoencoders sean viables con ajustes

---

## FASE 2 — Tabla de compatibilidad de modelos

**Archivo de implementación:** `FASE2_COMPATIBILIDAD.md`  
**Output:** Tabla analítica (sin código — es análisis)

### Modelos a evaluar

| Modelo | Compatible directo | Requiere etiquetas | Requiere transformación | Complejidad | Viabilidad |
|---|---|---|---|---|---|
| **Isolation Forest** | ✅ SÍ | ❌ NO | StandardScaler (ya aplicado) | Baja | ✅ Implementado |
| **One-Class SVM** | ✅ SÍ | ❌ NO | StandardScaler + kernel RBF | Media | ✅ INCLUIR |
| **Local Outlier Factor** | ✅ SÍ | ❌ NO | StandardScaler | Baja | ✅ INCLUIR |
| **DBSCAN** | ⚠️ PARCIAL | ❌ NO | StandardScaler + epsilon tuning | Alta | ⚠️ INCLUIR con nota |
| **Autoencoder** | ✅ SÍ | ❌ NO (semi) | Normalización + arquitectura NN | Alta | ✅ INCLUIR (simple) |
| **Random Forest** | ⚠️ CON DATOS | ✅ SÍ | Dataset etiquetado (Fase 3) | Media | ✅ INCLUIR (supervisado) |
| **XGBoost** | ⚠️ CON DATOS | ✅ SÍ | Dataset etiquetado + balance | Media | ✅ INCLUIR (supervisado) |
| **LightGBM** | ⚠️ CON DATOS | ✅ SÍ | Dataset etiquetado + balance | Media | ⚠️ OPCIONAL |
| **Redes Neuronales (MLP)** | ⚠️ CON DATOS | ✅ SÍ | Dataset etiquetado + arquitectura | Muy Alta | ❌ EXCLUIR (fuera de scope) |
| **Decision Trees** | ⚠️ CON DATOS | ✅ SÍ | Dataset etiquetado | Baja | ✅ INCLUIR como baseline |

**Modelos seleccionados para el experimento:**

**Grupo A — One-class (mismo paradigma que IF):**
1. Isolation Forest (referencia)
2. One-Class SVM
3. Local Outlier Factor (LOF)
4. Autoencoder simple (1 capa oculta)

**Grupo B — Supervisados (para mostrar ventajas/limitaciones):**
5. Random Forest
6. XGBoost
7. Decision Tree (baseline simple)

**Por qué excluir DBSCAN:** Requiere ajuste fino de epsilon y min_samples específicos para el dataset; no tiene método `predict()` directo; produce outliers=noise que no equivalen directamente a "anómalo".

**Por qué excluir MLP/LightGBM/otras NN:** Fuera del scope razonable de una tesis de pregrado en este tiempo. LightGBM es redundante con XGBoost.

---

## FASE 3 — Construcción del dataset etiquetado

**Archivo de implementación:** `FASE3_DATASET_SUPERVISADO.md`  
**Script a crear:** `scripts/comparacion/f_construir_dataset_supervisado.py`  
**Output:** `data/dataset_comparacion.csv` + `data/X_train_sup.npy` + `data/X_test_sup.npy` + `data/y_train_sup.npy` + `data/y_test_sup.npy`

### Diseño del dataset etiquetado

**Estrategia:**
- Normal (label=0): los 13,427 flows de `data/normal_holdout.csv` (ya disponibles)
- Anómalo (label=1): muestra de los 598,285 flows anómalos de `*_anom_*.gz`
  - **¿Cuántos tomar?** → Muestra estratificada: ~2,000 por tipo de ataque × 6 tipos = 12,000 flows anómalos
  - Total dataset supervisado: ~25,000 flows (13K normal + 12K anómalo)
  - Ratio resultante: ~1:0.9 → casi balanceado para entrenamiento supervisado

**¿Por qué NO usar los 598,285 flows completos?**
- Entrenamiento de supervisados sería extremadamente sesgado hacia anómalos
- One-class models no escalan bien con 600K samples en test (LOF es O(n²))
- Para comparación justa, el test set debe ser el mismo para TODOS los modelos

**Split para supervisados (dentro de los 25K):**
- 70% train (para RF, XGBoost, DT)
- 30% test

**Test set para ONE-CLASS models:**
- El mismo 30% del dataset supervisado (etiquetado) = evaluación justa

**Nota crítica de diseño:**
Los modelos one-class (IF, OCSVM, LOF) se entrenan SOLO con flujos normales (el mismo `X_train` de 53,708 flows que usa el IF actual). Los supervisados se entrenan con el train split del dataset mixto (etiquetado). Pero TODOS son evaluados en el MISMO test set. Esto es una comparación justa.

### Columnas del dataset supervisado

```
pkts_toserver, pkts_toclient, bytes_toserver, bytes_toclient, duration,
pkt_rate, byte_rate, pkt_ratio, byte_ratio, avg_pkt_size,
is_tcp, is_udp, is_icmp, dest_port,
label (0=normal, 1=anómalo),
attack_type (http, ssh, transferencia, synflood, portscan, etc.)
```

---

## FASE 4 — Experimentos: entrenar y medir

**Archivo de implementación:** `FASE4_EXPERIMENTOS.md`  
**Script principal:** `scripts/comparacion/f_comparar_modelos.py`  
**Output:** `results/comparacion/04_resultados_modelos.json` + `results/comparacion/04_resultados_modelos.csv`

### Protocolo experimental

**Para cada modelo se medirá:**

1. **Tiempo de entrenamiento** (wall time, segundos)
2. **Tiempo de inferencia** (ms por muestra en el test set)
3. **Uso de RAM en pico** (MB) — via `tracemalloc`
4. **Métricas predictivas sobre el mismo test set:**
   - AUC-ROC
   - Precision @ τ_youden (umbral óptimo Youden)
   - Recall @ τ_youden
   - F1 @ τ_youden
   - FPR @ τ_youden
   - FNR @ τ_youden

### Protocolo por modelo

**Isolation Forest (referencia):**
```python
# Carga el modelo ya entrenado (models/isolation_forest.pkl)
# NO reentrena — usa el modelo de producción real
# Evalúa sobre el test set etiquetado
# Umbral: τ1 = -0.4459 (ya derivado)
```

**One-Class SVM:**
```python
from sklearn.svm import OneClassSVM
# Entrena sobre X_train_normal (los 53,708 flows normales escalados)
# kernel='rbf', nu=0.05 (equivalente a contamination=0.05 del IF)
# gamma='scale'
```

**LOF (Local Outlier Factor):**
```python
from sklearn.neighbors import LocalOutlierFactor
# novelty=True para poder llamar predict() sobre nuevos datos
# n_neighbors=20, contamination=0.05
# Entrena sobre X_train_normal
# ADVERTENCIA: LOF novelty mode es lento con >10K samples en train
# → Usar muestra de 10,000 normales para entrenamiento
```

**Autoencoder simple:**
```python
# PyTorch o sklearn MLPRegressor como autoencoder
# Arquitectura: 14 → 7 → 14 (bottleneck)
# Entrena sobre X_train_normal
# Anomaly score = MSE(input, reconstrucción)
# Umbral: percentil 95 del MSE en holdout normal
```

**Random Forest (supervisado):**
```python
from sklearn.ensemble import RandomForestClassifier
# n_estimators=300, class_weight='balanced'
# Entrena sobre X_train_sup (dataset mixto etiquetado, 70%)
# Evalúa sobre X_test_sup (30%)
```

**XGBoost (supervisado):**
```python
from xgboost import XGBClassifier
# n_estimators=300, scale_pos_weight=ratio_normal/ratio_anom
# Entrena sobre X_train_sup
# Evalúa sobre X_test_sup
```

**Decision Tree (baseline):**
```python
from sklearn.tree import DecisionTreeClassifier
# max_depth=10, class_weight='balanced'
# Baseline supervisado simple
```

### Advertencia de escalabilidad

| Modelo | n_train | Tiempo estimado |
|---|---|---|
| IF (ya entrenado) | — | < 1s (solo inferencia) |
| OCSVM | 53,708 | ~5-30 min (kernel RBF sobre 14D) |
| LOF (novelty) | 10,000 (muestra) | ~2-10 min |
| Autoencoder | 53,708 | ~1-5 min (10 epochs) |
| RF | ~17,500 (70% de 25K) | ~1-3 min |
| XGBoost | ~17,500 | ~30-60s |
| Decision Tree | ~17,500 | < 5s |

**Total estimado: 30-60 minutos de cómputo en el sensor**

---

## FASE 5 — Análisis de resultados y tablas comparativas

**Archivo de implementación:** `FASE5_RESULTADOS.md`  
**Script:** `scripts/comparacion/f_generar_tablas.py`  
**Output:** `results/comparacion/05_tablas_comparativas.md` + `results/comparacion/graficas/`

### Tablas a generar

**Tabla 1 — Rendimiento predictivo**

| Modelo | AUC-ROC | Recall | Precision | F1 | FPR |
|---|---|---|---|---|---|
| Isolation Forest ← referencia | | | | | |
| One-Class SVM | | | | | |
| LOF | | | | | |
| Autoencoder | | | | | |
| Random Forest* | | | | | |
| XGBoost* | | | | | |
| Decision Tree* | | | | | |

*Supervisados: tienen acceso a etiquetas en entrenamiento (ventaja injusta frente a one-class)

**Tabla 2 — Costo computacional**

| Modelo | T_train (s) | T_inferencia (ms/muestra) | RAM pico (MB) | Escalable online |
|---|---|---|---|---|
| Isolation Forest | — (pre-entrenado) | | | ✅ SÍ |
| One-Class SVM | | | | ⚠️ PARCIAL |
| LOF | | | | ❌ NO |
| Autoencoder | | | | ✅ SÍ |
| Random Forest | | | | ✅ SÍ |
| XGBoost | | | | ✅ SÍ |
| Decision Tree | | | | ✅ SÍ |

**Tabla 3 — Adecuación al contexto de producción**

| Modelo | Requiere etiquetas | Online (incremental) | Latencia < 500ms | Deploy en Python | IF-ganador |
|---|---|---|---|---|---|
| Isolation Forest | ❌ NO | ⚠️ Reentrenamiento | ✅ SÍ | ✅ SÍ | ← referencia |
| One-Class SVM | ❌ NO | ❌ NO | ⚠️ DEPENDE | ✅ SÍ | — |
| LOF | ❌ NO | ❌ NO | ❌ NO (n²) | ✅ SÍ | — |
| Autoencoder | ❌ NO | ✅ SÍ | ✅ SÍ | ✅ SÍ | — |
| Random Forest | ✅ SÍ | ❌ NO | ✅ SÍ | ✅ SÍ | — |
| XGBoost | ✅ SÍ | ❌ NO | ✅ SÍ | ✅ SÍ | — |

### Gráficas a generar

1. **Curvas ROC superpuestas** (todos los modelos en el mismo gráfico)
2. **Gráfico de barras: AUC-ROC por modelo** (con IF destacado)
3. **Gráfico scatter: AUC-ROC vs Tiempo de inferencia** (eficiencia)
4. **Gráfico scatter: AUC-ROC vs RAM** (eficiencia de recursos)
5. **Radar chart** (AUC, F1, velocidad, RAM, facilidad deploy)

---

## FASE 6 — Justificación final

**Archivo de implementación:** `FASE6_JUSTIFICACION.md`  
**Output final para tesis:** `docs/ppi_documentacion/F4_06_Justificacion_Final_Isolation_Forest.md`

### Argumento principal

Con los resultados de Fase 5 en mano, la justificación seguirá este esquema:

**Si IF es mejor en AUC-ROC:**
→ Justificación directa: "La evidencia experimental muestra que IF obtiene el mayor AUC-ROC entre los modelos one-class, sin requerir etiquetas de entrenamiento."

**Si IF es comparable a OCSVM:**
→ Justificación por eficiencia: "IF logra igual AUC con X veces menor tiempo de inferencia y sin kernel que calcular."

**Si supervisados (RF/XGBoost) obtienen mayor AUC:**
→ Justificación por realismo: "RF/XGBoost requieren etiquetas de ataques en el entrenamiento, lo cual no es posible en un sistema de detección real donde los ataques son *a priori* desconocidos. IF logra un AUC de 0.8998 *sin haber visto ningún ataque durante el entrenamiento*."

**Este último argumento es el más fuerte y casi seguramente será el caso.**

### Criterios de selección formalizados

La justificación final usará una **matriz de criterios ponderada**:

| Criterio | Peso | IF | OCSVM | LOF | AE | RF | XGB |
|---|---|---|---|---|---|---|---|
| AUC-ROC (rendimiento) | 30% | — | — | — | — | — | — |
| No requiere etiquetas (realismo) | 25% | 10 | 10 | 10 | 10 | 0 | 0 |
| Latencia de inferencia | 20% | — | — | — | — | — | — |
| RAM en producción | 10% | — | — | — | — | — | — |
| Facilidad de reentrenamiento | 10% | — | — | — | — | — | — |
| Interpretabilidad del score | 5% | — | — | — | — | — | — |

*(Los valores — se llenan con resultados reales de Fase 4)*

---

## FASE 7 — Mejoras / Ensemble

**Archivo de implementación:** `FASE7_MEJORAS.md`

### Hipótesis de mejora

Si el Autoencoder muestra alta complementariedad con IF (detecta lo que IF falla y viceversa), proponer:

**Ensemble IF + Autoencoder (AND gate):**
```
score_final = 'BLOCK' if (IF_score < τ2 AND AE_error > θ_ae)
score_final = 'LIMIT' if (IF_score < τ1 AND AE_error > θ_ae)
score_final = 'PERMIT' otherwise
```
- Ventaja esperada: reducir FPR del 20.47% actual
- Desventaja: mayor latencia, más complejidad de mantenimiento
- Viabilidad: alta — ambos modelos son sklearn/PyTorch, inferencia < 10ms cada uno

### Si ningún modelo complementa IF:
→ Proponer **IF con umbral adaptativo** (ajuste dinámico de τ1 basado en hora del día o carga de red) como mejora realista sin cambiar el modelo base.

---

## FASE 8 — Documentación final para tesis

**Archivo de implementación:** `FASE8_DOCS_TESIS.md`  
**Documentos a producir:**

### Doc 1: `F4_05_Comparacion_Avanzada_Modelos.md`
- Análisis del dataset (Fase 1)
- Tabla de compatibilidad (Fase 2)
- Metodología del experimento (Fase 3+4)
- Tablas comparativas con resultados reales (Fase 5)
- Gráficas (Fase 5)
- Ruta: `docs/ppi_documentacion/F4_05_Comparacion_Avanzada_Modelos.md`

### Doc 2: `F4_06_Justificacion_Final_Isolation_Forest.md`
- Resumen ejecutivo (1 página)
- Matriz de criterios completa
- Respuesta directa a la pregunta del jurado
- Texto verbatim para la sustentación
- Comparación con literatura revisada
- Ruta: `docs/ppi_documentacion/F4_06_Justificacion_Final_Isolation_Forest.md`

---

## Resumen ejecutivo del plan

```
ESTADO ACTUAL:
  IF solo → AUC=0.8998, F1=0.9947, Latencia P95=34.8ms

LO QUE VAMOS A HACER:
  1. Caracterizar formalmente el dataset (Fase 1)
  2. Decidir qué modelos son comparables (Fase 2)
  3. Construir dataset etiquetado para supervisados (Fase 3)
  4. Entrenar y medir 7 modelos con el mismo protocolo (Fase 4)
  5. Generar tablas y gráficas comparativas (Fase 5)
  6. Escribir justificación formal con evidencia real (Fase 6)
  7. Proponer mejora concreta si aplica (Fase 7)
  8. Redactar 2 documentos para tesis (Fase 8)

HIPÓTESIS ESPERADA:
  IF es el mejor modelo one-class para este dataset en la combinación:
  AUC-ROC × latencia × no-requiere-etiquetas
  Los supervisados (RF/XGB) obtienen mayor AUC pero requieren etiquetas de ataques
  conocidos → irrealistas para detección de anomalías en producción.

RESPUESTA AL JURADO (versión corta):
  "Comparamos IF con 6 modelos alternativos usando el mismo dataset y protocolo.
   IF obtuvo [resultado] sin requerir etiquetas de entrenamiento.
   Los supervisados que lo superaron necesitan conocer los ataques de antemano,
   lo cual contradice el objetivo de detectar comportamientos desconocidos."
```

---

## Orden de ejecución

```
[ ] FASE1_ANALISIS.md         → crear script + ejecutar + revisar output
[ ] FASE2_COMPATIBILIDAD.md   → escribir documento de análisis
[ ] FASE3_DATASET_SUPERVISADO.md → crear script + ejecutar + verificar CSV
[ ] FASE4_EXPERIMENTOS.md     → crear script principal + ejecutar (30-60min)
[ ] FASE5_RESULTADOS.md       → crear script tablas + gráficas
[ ] FASE6_JUSTIFICACION.md    → redactar con resultados reales
[ ] FASE7_MEJORAS.md          → decidir ensemble si aplica
[ ] FASE8_DOCS_TESIS.md       → documentos finales para GitHub
```

**Ruta de los scripts:** `scripts/comparacion/` (directorio nuevo en el sensor)  
**Ruta de outputs:** `results/comparacion/` (directorio nuevo en el sensor)  
**Ruta de docs tesis:** `docs/ppi_documentacion/` (ya existe)

---

*Plan generado: 2026-06-17 | Estado: lista para implementación fase por fase*
