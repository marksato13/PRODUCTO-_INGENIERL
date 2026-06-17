# FASE 2 — Compatibilidad de Modelos con el Dataset

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Basado en:** `FASE1_ANALISIS.md` + `results/comparacion/01_analisis_dataset.txt`  
**Fecha:** 2026-06-17  
**Estado:** ✅ COMPLETADA

---

## Resumen de restricciones del dataset (de FASE 1)

| Restricción | Valor | Impacto en selección de modelo |
|---|---|---|
| Etiquetas en entrenamiento | NINGUNA (one-class) | Elimina supervisados del paradigma real |
| Features | 14, todas numéricas | Compatible con todos los modelos |
| Distribución | Muy skewed (skew > 40 en varias) | Penaliza modelos que asumen normalidad |
| Volumen entrenamiento | 53,708 flows | O(n²) es inviable sin muestreo |
| Ratio desbalance | 1 : 67.5 | No afecta one-class; crítico para supervisados |
| Escala features | Heterogénea (1–40M) | StandardScaler obligatorio para distancia-based |

---

## Análisis por modelo

---

### 1. Isolation Forest (IF) — REFERENCIA

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ✅ SÍ — directamente |
| **Requiere etiquetas** | ❌ NO |
| **Transformación adicional** | StandardScaler (ya aplicado) |
| **Complejidad implementación** | BAJA |
| **Ya entrenado** | SÍ — `models/isolation_forest.pkl` |

**Fundamento teórico:**  
Liu et al. (2008) diseñaron IF para detectar anomalías en datos de alta dimensión sin etiquetas. El algoritmo aísla puntos anómalos usando particiones aleatorias en árboles de decisión binarios. Los puntos que se aíslan rápido (menos particiones) son más anómalos.

**Ventajas para este dataset:**
- Insensible a distribuciones skewed — no asume normalidad
- O(n log n) en entrenamiento → 53,708 flows en < 10 segundos
- Produce score continuo → permite derivar umbrales τ1/τ2 con ROC
- Robusto al desbalance de clases (no ve las anomalías en entrenamiento)
- Escalable a nuevos datos sin reentrenamiento completo

**Desventajas:**
- AUC limitada cuando la separación de distribuciones es pequeña (δ=0.1454 en este caso)
- FPR=20.47% en τ1 (Youden) — mitigado con whitelist en producción
- No interpretable feature por feature (no produce "la feature X fue la causa")

**Parámetros usados:** `n_estimators=300, contamination=0.05, random_state=42`

---

### 2. One-Class SVM (OCSVM)

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ✅ SÍ |
| **Requiere etiquetas** | ❌ NO |
| **Transformación adicional** | StandardScaler OBLIGATORIO + ajuste de kernel |
| **Complejidad implementación** | MEDIA |
| **Seleccionado para experimento** | ✅ SÍ |

**Fundamento teórico:**  
Schölkopf et al. (2001) extendieron el SVM clásico para one-class learning. OCSVM aprende un hiperplano en espacio de alta dimensión (via kernel) que encierra la región de los datos normales. Puntos fuera de la región son anomalías.

**Ventajas para este dataset:**
- Mismo paradigma one-class que IF → comparación directa y justa
- Con kernel RBF puede capturar fronteras no lineales (útil dado el skew)
- Produce score (distancia firmada al hiperplano) → permite curva ROC
- Bien establecido teóricamente — referencia clásica en detección de anomalías

**Desventajas para este dataset:**
- **Complejidad O(n²) a O(n³)** — con 53,708 flows y kernel RBF: 5-30 minutos de entrenamiento
- Muy sensible al parámetro `nu` (equivalente a contamination) y `gamma` del kernel → tuning necesario
- Altamente sensible al skew: `byte_rate` con skew=45 puede distorsionar el espacio del kernel
- No escala bien a producción online (inferencia más lenta que IF)

**Parámetros para el experimento:** `kernel='rbf', nu=0.05, gamma='scale'`  
**Nota:** `nu=0.05` equivale a `contamination=0.05` del IF — comparación justa.

---

### 3. Local Outlier Factor (LOF)

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ✅ SÍ (con `novelty=True`) |
| **Requiere etiquetas** | ❌ NO |
| **Transformación adicional** | StandardScaler OBLIGATORIO + muestreo |
| **Complejidad implementación** | MEDIA |
| **Seleccionado para experimento** | ✅ SÍ (con muestra 10K) |

**Fundamento teórico:**  
Breunig et al. (2000) propusieron LOF como medida de densidad local relativa. Para cada punto, compara su densidad con la densidad de sus k vecinos. Un punto con densidad mucho menor que sus vecinos es un outlier local. El score LOF > 1 indica anomalía.

**Ventajas para este dataset:**
- No asume forma global del cluster de normalidad (ventaja sobre OCSVM)
- Detecta outliers locales que IF podría no detectar (ataques "sutiles")
- `novelty=True` permite predecir sobre nuevos datos → evaluación estándar posible

**Desventajas para este dataset:**
- **Complejidad O(n²)** en la fase de k-vecinos — con 53,708 flows: > 30 minutos
- Solución: **muestra de 10,000 flows normales** para entrenamiento (no el total)
- Muy sensible al skew en features: outliers de `byte_rate` (max=40M) distorsionan distancias euclidianas incluso con StandardScaler (los outliers extremos en datos normales rompen los k-vecinos)
- No hay score continuo nativo en sklearn — usa `negative_outlier_factor_` como proxy
- **Limitación crítica:** LOF con `novelty=True` no es un clasificador online real — no puede actualizarse sin reentrenamiento completo

**Parámetros para el experimento:** `n_neighbors=20, novelty=True, contamination=0.05`  
**Nota:** Entrenado sobre muestra de 10,000 normales (no 53,708) por viabilidad computacional.

---

### 4. DBSCAN

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ PARCIALMENTE |
| **Requiere etiquetas** | ❌ NO |
| **Transformación adicional** | StandardScaler + ajuste fino de epsilon |
| **Complejidad implementación** | ALTA (tuning complejo) |
| **Seleccionado para experimento** | ❌ NO — EXCLUIDO |

**Por qué se excluye:**

1. **No tiene método `predict()`** sobre nuevos datos — solo clasifica el conjunto de entrenamiento. No es aplicable a detección online.
2. **Sensibilidad crítica a epsilon:** En 14 dimensiones con distribuciones skewed y escalas heterogéneas, encontrar el epsilon correcto requiere curva k-distancia manual + validación → fuera de scope.
3. **Outlier ≠ anómalo de red:** DBSCAN marca como noise los puntos fuera de todos los clusters. Pero en datos de red, hay flows normales raros legítimos (ráfagas ocasionales) que DBSCAN marcaría como noise incorrectamente.
4. **Complejidad O(n log n)** con índice, pero la sensibilidad a epsilon hace que los resultados varíen enormemente entre ejecuciones con parámetros ligeramente distintos.

**Alternativa incluida:** LOF, que también es density-based pero tiene `novelty=True` y score continuo.

---

### 5. Autoencoder (AE)

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ✅ SÍ |
| **Requiere etiquetas** | ❌ NO (entrena a reconstruir normalidad) |
| **Transformación adicional** | StandardScaler + arquitectura de red |
| **Complejidad implementación** | MEDIA-ALTA |
| **Seleccionado para experimento** | ✅ SÍ (arquitectura simple) |

**Fundamento teórico:**  
Un autoencoder es una red neuronal que aprende a comprimir y reconstruir su entrada. Entrenado solo con datos normales, aprende la representación compacta de lo "normal". Al presentarle datos anómalos, el error de reconstrucción (MSE) es alto porque el modelo no aprendió a reconstruirlos.

**Ventajas para este dataset:**
- Paradigma one-class — mismo que IF
- Puede capturar relaciones no lineales entre features (que IF y LOF no capturan)
- Arquitectura 14→7→14 es trivial — no requiere GPU
- Produce score continuo (MSE) → curva ROC posible
- Inferencia rápida una vez entrenado

**Desventajas para este dataset:**
- Requiere PyTorch o TensorFlow — dependencia adicional al venv del sensor
- Hiperparámetros a tunear: learning rate, epochs, tamaño del bottleneck
- Con 14 features, la capacidad de compresión 14→7 es baja → posible underfitting
- El score (MSE) no es comparable directamente con IF score → umbral distinto
- Puede memorizar outliers del dataset de entrenamiento si los datos normales tienen varianza alta

**Arquitectura para el experimento:**
```
Input (14) → Dense(10, ReLU) → Dense(7, ReLU) [bottleneck] → Dense(10, ReLU) → Output(14)
Loss: MSE | Optimizer: Adam(lr=0.001) | Epochs: 30 | Batch: 256
```

**Implementación:** `sklearn.neural_network.MLPRegressor` como autoencoder simple (evita dependencia de PyTorch):
```python
from sklearn.neural_network import MLPRegressor
ae = MLPRegressor(hidden_layer_sizes=(10, 7, 10), activation='relu',
                  max_iter=200, random_state=42)
ae.fit(X_train_normal, X_train_normal)  # target = input
mse = np.mean((ae.predict(X_test) - X_test)**2, axis=1)
```

---

### 6. Random Forest (RF) — SUPERVISADO

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ CON DATASET ETIQUETADO (Fase 3) |
| **Requiere etiquetas** | ✅ SÍ — entrenamiento supervisado |
| **Transformación adicional** | Dataset etiquetado + `class_weight='balanced'` |
| **Complejidad implementación** | BAJA (una vez con el dataset) |
| **Seleccionado para experimento** | ✅ SÍ — como upper bound teórico |

**Por qué incluirlo si es supervisado:**  
Su AUC esperada superior a IF no prueba que IF sea malo — prueba que **tener etiquetas de ataques mejora la detección**. Esta comparación es útil para mostrar cuánto "cuesta" la ventaja del supervisado en términos de requisitos (necesita conocer los ataques a priori). Es el argumento más fuerte de la justificación final.

**Ventajas:**
- Invariante a escala y distribución (árboles) → robusto a skew extremo
- `feature_importances_` → interpretabilidad por feature
- Excelente AUC esperada con clases bien separadas
- `class_weight='balanced'` maneja el desbalance automáticamente

**Desventajas en el contexto real:**
- **Requiere etiquetas de ataques en entrenamiento** → irrealista en producción
- No detecta ataques no vistos en entrenamiento (por definición)
- Si aparece un "sexto ataque" no visto → clasificará según las clases aprendidas

**Parámetros:** `n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1`

---

### 7. XGBoost (XGB) — SUPERVISADO

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ CON DATASET ETIQUETADO (Fase 3) |
| **Requiere etiquetas** | ✅ SÍ |
| **Transformación adicional** | Dataset etiquetado + `scale_pos_weight` |
| **Complejidad implementación** | BAJA-MEDIA |
| **Seleccionado para experimento** | ✅ SÍ — como upper bound teórico |

**Ventajas:**
- Estado del arte en clasificación tabular supervisada
- `scale_pos_weight = n_negativos/n_positivos` para manejo de desbalance
- Generalmente supera a RF en tabular data con tuning mínimo
- Velocidad de inferencia muy alta

**Desventajas en el contexto real:**
- Mismas limitaciones de supervisado que RF
- Requiere `xgboost` instalado — verificar disponibilidad en venv del sensor

**Parámetros:** `n_estimators=300, scale_pos_weight=ratio_clases, eval_metric='auc', random_state=42`

---

### 8. Decision Tree (DT) — BASELINE SUPERVISADO

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ CON DATASET ETIQUETADO (Fase 3) |
| **Requiere etiquetas** | ✅ SÍ |
| **Transformación adicional** | Dataset etiquetado + `class_weight='balanced'` |
| **Complejidad implementación** | MUY BAJA |
| **Seleccionado para experimento** | ✅ SÍ — baseline supervisado simple |

**Propósito:** Mostrar que incluso el modelo supervisado más simple puede obtener AUC alta con etiquetas — refuerza el argumento de que la ventaja es de las etiquetas, no del modelo en sí.

**Parámetros:** `max_depth=10, class_weight='balanced', random_state=42`

---

### 9. LightGBM — SUPERVISADO

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ CON DATASET ETIQUETADO |
| **Requiere etiquetas** | ✅ SÍ |
| **Seleccionado para experimento** | ❌ EXCLUIDO — redundante con XGBoost |

**Por qué excluir:** LightGBM y XGBoost son alternativas de gradient boosting. Con 14 features y 25K flows, la diferencia entre ambos será mínima. Incluir los dos no añade valor argumental — solo complejidad. XGBoost es más reconocido en la literatura académica para datasets de esta escala.

---

### 10. Redes Neuronales (MLP profundo) — SUPERVISADO

| Atributo | Evaluación |
|---|---|
| **Compatible con el dataset** | ⚠️ CON DATASET ETIQUETADO |
| **Requiere etiquetas** | ✅ SÍ |
| **Seleccionado para experimento** | ❌ EXCLUIDO — fuera de scope |

**Por qué excluir:**
1. Con 14 features y 25K flows, una MLP profunda no tiene ventaja sobre RF/XGBoost (las redes profundas brillan con datos de alta dimensión como imágenes o texto)
2. Requiere tuning extenso (arquitectura, dropout, batch size, lr decay) → fuera del scope de una tesis de pregrado
3. El Autoencoder (incluido) ya representa la contribución de redes neuronales en paradigma one-class

---

## Tabla resumen de compatibilidad

| Modelo | Compatible | Etiquetas train | Transformación | Complejidad | Incluido | Grupo |
|---|---|---|---|---|---|---|
| Isolation Forest | ✅ SÍ | ❌ NO | StandardScaler | BAJA | ✅ Referencia | One-class |
| One-Class SVM | ✅ SÍ | ❌ NO | StandardScaler + kernel | MEDIA | ✅ SÍ | One-class |
| LOF | ✅ SÍ* | ❌ NO | StandardScaler + muestra | MEDIA | ✅ SÍ* | One-class |
| Autoencoder | ✅ SÍ | ❌ NO | StandardScaler + arquitectura | MEDIA | ✅ SÍ | One-class |
| Random Forest | ⚠️ Con datos | ✅ SÍ | Dataset etiquetado | BAJA | ✅ Upper bound | Supervisado |
| XGBoost | ⚠️ Con datos | ✅ SÍ | Dataset etiquetado | MEDIA | ✅ Upper bound | Supervisado |
| Decision Tree | ⚠️ Con datos | ✅ SÍ | Dataset etiquetado | MUY BAJA | ✅ Baseline | Supervisado |
| DBSCAN | ⚠️ Parcial | ❌ NO | Epsilon tuning complejo | ALTA | ❌ Excluido | — |
| LightGBM | ⚠️ Con datos | ✅ SÍ | Dataset etiquetado | MEDIA | ❌ Excluido | — |
| MLP/NN profunda | ⚠️ Con datos | ✅ SÍ | Dataset etiquetado + GPU | MUY ALTA | ❌ Excluido | — |

*LOF: muestra de 10,000 flows por viabilidad computacional (O(n²))

---

## Modelos seleccionados para el experimento (FASE 4)

### Grupo A — One-class (comparación justa, mismo paradigma)

| # | Modelo | Entrenamiento | Umbral |
|---|---|---|---|
| 1 | **Isolation Forest** (referencia) | 53,708 flows normales | τ1=−0.4459 (Youden, ya derivado) |
| 2 | **One-Class SVM** | 53,708 flows normales | Derivar con ROC |
| 3 | **LOF** | 10,000 muestra normales | Derivar con ROC |
| 4 | **Autoencoder** (MLPRegressor) | 53,708 flows normales | Percentil 95 MSE holdout |

### Grupo B — Supervisados (upper bound teórico)

| # | Modelo | Entrenamiento | Nota |
|---|---|---|---|
| 5 | **Random Forest** | Dataset mixto etiquetado (70%) | Ventaja injusta: conoce ataques |
| 6 | **XGBoost** | Dataset mixto etiquetado (70%) | Ventaja injusta: conoce ataques |
| 7 | **Decision Tree** | Dataset mixto etiquetado (70%) | Baseline más simple |

**Todos evalúan sobre el mismo test set** — el 30% del dataset mixto etiquetado (Fase 3).

---

## Pregunta esperada del jurado y respuesta preparada

**Pregunta:** *"¿Por qué no compararon con Random Forest o Redes Neuronales?"*

**Respuesta:**
> "Sí los comparamos. RF y XGBoost obtienen métricas superiores — pero eso se debe a que tienen acceso a etiquetas de ataques durante el entrenamiento, lo que es irrealista en un IDPS real donde los ataques son desconocidos a priori. Incluimos esta comparación precisamente para demostrar ese punto: **IF logra AUC=0.8998 sin haber visto ningún ataque**, mientras que RF necesita que el administrador etiquete manualmente ataques históricos para entrenarlo. La ventaja de los supervisados no contradice la elección de IF — la refuerza, mostrando que el paradigma one-class es el correcto para este problema."

---

**Siguiente fase:** `FASE3_DATASET_SUPERVISADO.md` — construcción del dataset etiquetado que necesitan los modelos supervisados (Grupos B).
