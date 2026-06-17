# FASE 3 — Construcción del Dataset Supervisado

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Script ejecutado:** `scripts/comparacion/f_construir_dataset_supervisado.py`  
**Output generado:** `results/comparacion/03_dataset_supervisado.txt`  
**Fecha de ejecución:** 2026-06-17  
**Estado:** ✅ COMPLETADA

---

## 1. Diseño del dataset

### Problema a resolver

Los modelos one-class (IF, OCSVM, LOF, Autoencoder) se pueden entrenar directamente con los 53,708 flows normales existentes. Pero los modelos supervisados (RF, XGBoost, DT) necesitan un dataset **etiquetado con ambas clases** para entrenamiento.

### Estrategia de construcción

| Decisión | Valor | Justificación |
|---|---|---|
| Normal (label=0) | **13,427 flows** completos | Todo `data/normal_holdout.csv` (reservado desde FASE 3 original) |
| Anómalo (label=1) | **2,000 por tipo × 6 tipos = 12,000** | Muestra estratificada — evita dominio de un ataque |
| Total dataset | **25,427 flows** | Manejable computacionalmente |
| Ratio resultante | **1:0.89** (casi balanceado) | Ideal para entrenar supervisados sin `class_weight` forzado |
| Split | **70% train / 30% test** | Estratificado — misma proporción de clases en ambos splits |
| Scaler | **`models/scaler.pkl`** existente | Consistencia con pipeline de producción |

### ¿Por qué 2,000 por tipo y no todos los 906K?

Si se usaran los 906,188 flows anómalos completos:
- El dataset tendría ratio 1:67 — los supervisados predecirían casi siempre "anómalo"
- El entrenamiento tardaría horas vs segundos
- No añade calidad al modelo — los ataques son repetitivos por naturaleza (un flood de 600K paquetes es siempre el mismo patrón)
- 2,000 por tipo captura la variabilidad del ataque con margen suficiente

---

## 2. Resultados de la construcción

### Flows disponibles por tipo vs seleccionados

| Tipo de ataque | Disponibles | Seleccionados | % usado |
|---|---|---|---|
| Brute Force SSH | 306,885 | 2,000 | 0.7% |
| HTTP Abuse | 50,791 | 2,000 | 3.9% |
| ICMP Flood | 323,460 | 2,000 | 0.6% |
| Port Scan | 111,161 | 2,000 | 1.8% |
| SYN Flood | 95,723 | 2,000 | 2.1% |
| UDP Flood | 318,168 | 2,000 | 0.6% |
| **TOTAL anómalos** | **1,206,188** | **12,000** | 1.0% |
| Normal | 13,427 | 13,427 | 100% |
| **TOTAL dataset** | — | **25,427** | — |

### Distribución del dataset final

| Clase | Train (70%) | Test (30%) | Total |
|---|---|---|---|
| Normal (label=0) | 9,398 | 4,029 | 13,427 |
| Anómalo (label=1) | 8,400 | 3,600 | 12,000 |
| **TOTAL** | **17,798** | **7,629** | **25,427** |
| Ratio | 1:0.89 | 1:0.89 | 1:0.89 |

### Distribución del TEST SET por tipo de ataque

| Tipo | Flows en test | Label |
|---|---|---|
| Normal | 4,029 | 0 |
| Brute Force | 557 | 1 |
| HTTP Abuse | 636 | 1 |
| ICMP Flood | 597 | 1 |
| Port Scan | 602 | 1 |
| SYN Flood | 597 | 1 |
| UDP Flood | 611 | 1 |
| **TOTAL** | **7,629** | — |

---

## 3. Archivos generados

| Archivo | Forma | Descripción |
|---|---|---|
| `data/dataset_comparacion.csv` | 25,427 × 16 | Dataset completo (features + label + attack_type) |
| `data/X_train_sup.npy` | (17798, 14) | Features train supervisados — escaladas con scaler.pkl |
| `data/X_test.npy` | (7629, 14) | **Test compartido** para TODOS los modelos — escalado |
| `data/y_train_sup.npy` | (17798,) | Etiquetas train supervisados |
| `data/y_test.npy` | (7629,) | **Etiquetas test** para TODOS los modelos |
| `data/attack_type_test.npy` | (7629,) | Tipo de ataque por flow (análisis por escenario en FASE 5) |
| `data/X_train_sup_raw.npy` | (17798, 14) | Features train sin escalar (referencia) |
| `data/X_test_raw.npy` | (7629, 14) | Features test sin escalar (referencia) |

---

## 4. Protocolo de evaluación (clave para la comparación justa)

```
┌─────────────────────────────────────────────────────────────┐
│                PROTOCOLO DE EVALUACIÓN FASE 4               │
│                                                             │
│  MODELOS ONE-CLASS (IF, OCSVM, LOF, Autoencoder)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  TRAIN: 53,708 flows normales (*_normal_*.gz)       │   │
│  │  → NO ven etiquetas, NO ven ataques                 │   │
│  │  TEST:  X_test.npy (7,629 flows etiquetados)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  MODELOS SUPERVISADOS (RF, XGBoost, DT)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  TRAIN: X_train_sup.npy (17,798 flows etiquetados)  │   │
│  │  → SÍ ven etiquetas, SÍ ven ataques (ventaja)       │   │
│  │  TEST:  X_test.npy (7,629 flows etiquetados) ←MISMO │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  EVALUACIÓN: AUC-ROC, Precision, Recall, F1, FPR, FNR     │
│  calculados sobre el MISMO X_test.npy + y_test.npy         │
└─────────────────────────────────────────────────────────────┘
```

**La comparación es justa porque:**
- Todos los modelos son evaluados sobre el **mismo test set** (7,629 flows)
- El test set tiene la misma distribución de tipos de ataque para todos
- La diferencia en AUC entre grupos refleja exclusivamente la **ventaja de tener etiquetas**

---

## 5. Nota sobre el scaler

Se usa `models/scaler.pkl` (entrenado sobre 53,708 flows **normales**) para transformar **todos** los datos, incluyendo el train/test de los supervisados.

**¿Por qué el mismo scaler para todos?**
1. Es el scaler de producción real → comparación bajo condiciones reales
2. Los supervisados reciben features en el mismo espacio que los one-class → comparación directa de los scores
3. Usar un scaler nuevo para supervisados (fit sobre datos mixtos) cambiaría la escala de las features → los modelos no serían directamente comparables

**Advertencia registrada:** sklearn emitió `UserWarning: X does not have valid feature names, but StandardScaler was fitted with feature names` — inofensivo, ocurre porque `scaler.transform()` recibe numpy array en lugar de DataFrame. Los valores escalados son idénticos.

---

**Siguiente fase:** `FASE4_EXPERIMENTOS.md` — entrenamiento y medición de los 7 modelos sobre este mismo test set.
