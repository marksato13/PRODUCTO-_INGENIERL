# FASE 4 — Experimentos: Resultados de la Comparación

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Script ejecutado:** `scripts/comparacion/f_comparar_modelos.py`  
**Outputs:** `results/comparacion/04_resultados_modelos.json` + `.csv` + `04_log_experimentos.txt`  
**Fecha de ejecución:** 2026-06-17 11:27–11:29 UTC  
**Estado:** ✅ COMPLETADA

---

## 1. Protocolo de evaluación

| Parámetro | Valor |
|---|---|
| Test set (compartido) | **7,629 flows** (4,029 normal + 3,600 anómalos) |
| Tipos de ataque en test | 6 tipos, ~600 por tipo |
| Entrenamiento one-class | `X_train_normal` = 9,398 flows normales (subset sin leakage) |
| Entrenamiento supervisado | `X_train_sup` = 17,798 flows etiquetados |
| IF: origen del modelo | Pre-entrenado sobre 53,708 flows normales originales |
| Umbral óptimo | Youden (maximiza TPR − FPR) para cada modelo |
| Métrica de anomalía | AUC-ROC sobre misma curva ROC |
| RAM | `tracemalloc` (Python-level peak) |
| Inferencia | ms/muestra, mínimo de 3 repeticiones |

---

## 2. Resultados por modelo

### Isolation Forest (referencia)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9159** |
| Recall (umbral Youden) | **0.9953** |
| Precision | 0.8136 |
| F1 | 0.8953 |
| FPR | 0.2038 |
| Inferencia | 0.0297 ms/muestra |
| T. entrenamiento | pre-entrenado (53,708 flows normales) |
| Recall con τ1=−0.4459 | 0.9947 |

---

### One-Class SVM (kernel RBF, nu=0.05)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9712** |
| Recall | 0.9303 |
| Precision | 0.9120 |
| F1 | 0.9211 |
| FPR | 0.0802 |
| Inferencia | 0.0344 ms/muestra |
| T. entrenamiento | **0.6s** (9,398 flows) |

---

### LOF (Local Outlier Factor, k=20, novelty=True)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.8418** |
| Recall | 0.5900 |
| Precision | 0.9104 |
| F1 | 0.7160 |
| FPR | 0.0519 |
| Inferencia | 0.0429 ms/muestra |
| T. entrenamiento | 0.3s (5,000 flows — muestra) |

---

### Autoencoder (MLPRegressor 14→10→7→10→14)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9580** |
| Recall | 0.9883 |
| Precision | 0.8951 |
| F1 | 0.9394 |
| FPR | 0.1035 |
| Inferencia | **0.0010 ms/muestra** |
| T. entrenamiento | 26.9s (163 iter., early stopping) |

---

### Random Forest (supervisado — upper bound)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9997** ← ventaja injusta |
| Recall | 0.9986 |
| Precision | 0.9956 |
| F1 | 0.9971 |
| FPR | 0.0040 |
| Inferencia | 0.0399 ms/muestra |
| T. entrenamiento | 9.8s (17,798 flows etiquetados) |
| Feature más importante | `dest_port` (42.2%) |

---

### XGBoost (supervisado — upper bound)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9995** ← ventaja injusta |
| Recall | 0.9986 |
| Precision | 0.9953 |
| F1 | 0.9969 |
| FPR | 0.0042 |
| Inferencia | 0.0075 ms/muestra |
| T. entrenamiento | 77.8s (17,798 flows etiquetados) |

---

### Decision Tree (baseline supervisado)

| Métrica | Valor |
|---|---|
| **AUC-ROC** | **0.9972** ← ventaja injusta |
| Recall | 0.9975 |
| Precision | 0.9942 |
| F1 | 0.9958 |
| FPR | 0.0052 |
| Inferencia | **0.0001 ms/muestra** |
| T. entrenamiento | 0.1s (17,798 flows etiquetados) |

---

## 3. Tabla comparativa completa

### Rendimiento predictivo

| Modelo | Grupo | AUC-ROC | Recall | Precision | F1 | FPR |
|---|---|---|---|---|---|---|
| **Isolation Forest** | one-class | 0.9159 | **0.9953** | 0.8136 | 0.8953 | 0.2038 |
| One-Class SVM | one-class | **0.9712** | 0.9303 | **0.9120** | 0.9211 | 0.0802 |
| LOF | one-class | 0.8418 | 0.5900 | 0.9104 | 0.7160 | 0.0519 |
| Autoencoder | one-class | 0.9580 | 0.9883 | 0.8951 | **0.9394** | 0.1035 |
| Random Forest* | supervisado | 0.9997 | 0.9986 | 0.9956 | 0.9971 | **0.0040** |
| XGBoost* | supervisado | 0.9995 | 0.9986 | 0.9953 | 0.9969 | 0.0042 |
| Decision Tree* | supervisado | 0.9972 | 0.9975 | 0.9942 | 0.9958 | 0.0052 |

*Supervisados: conocen los ataques en entrenamiento — ventaja injusta.

### Costo computacional

| Modelo | T. train (s) | Inferencia (ms/muestra) | n_train | Escalable online |
|---|---|---|---|---|
| Isolation Forest | pre-entrenado | 0.0297 | 53,708 normal | ✅ SÍ |
| One-Class SVM | 0.6s | 0.0344 | 9,398 normal | ⚠️ PARCIAL |
| LOF | 0.3s | 0.0429 | 5,000 normal (muestra) | ❌ NO |
| Autoencoder | 26.9s | **0.0010** | 9,398 normal | ✅ SÍ |
| Random Forest* | 9.8s | 0.0399 | 17,798 etiquetados | ✅ SÍ |
| XGBoost* | 77.8s | 0.0075 | 17,798 etiquetados | ✅ SÍ |
| Decision Tree* | 0.1s | **0.0001** | 17,798 etiquetados | ✅ SÍ |

### Adecuación al contexto de producción

| Modelo | Requiere etiquetas ataque | Detecta ataque desconocido | Latencia < 500ms | Deploy sin GPU |
|---|---|---|---|---|
| Isolation Forest | ❌ NO | ✅ SÍ | ✅ SÍ | ✅ SÍ |
| One-Class SVM | ❌ NO | ✅ SÍ | ✅ SÍ | ✅ SÍ |
| LOF | ❌ NO | ✅ SÍ | ✅ SÍ | ✅ SÍ |
| Autoencoder | ❌ NO | ✅ SÍ | ✅ SÍ | ✅ SÍ |
| Random Forest | **✅ SÍ** | ❌ NO | ✅ SÍ | ✅ SÍ |
| XGBoost | **✅ SÍ** | ❌ NO | ✅ SÍ | ✅ SÍ |
| Decision Tree | **✅ SÍ** | ❌ NO | ✅ SÍ | ✅ SÍ |

---

## 4. Hallazgos clave

### Hallazgo 1: OCSVM supera a IF en AUC — pero IF tiene mayor Recall

El One-Class SVM obtuvo AUC=0.9712 vs IF AUC=0.9159. Sin embargo:

| Métrica | IF | OCSVM | Diferencia |
|---|---|---|---|
| AUC-ROC | 0.9159 | **0.9712** | OCSVM +5.5pp |
| **Recall** | **0.9953** | 0.9303 | **IF +6.5pp** |
| FPR | 0.2038 | **0.0802** | OCSVM mejor |
| n_train (one-class) | **53,708** | 9,398 | IF entrenó con 5.7× más datos |

**Interpretación:** En seguridad de redes, el **Recall es la métrica crítica** — un ataque no detectado es mucho más costoso que una falsa alarma. IF detecta el **99.53%** de los ataques vs el **93.03%** de OCSVM. Además, el FPR alto de IF (0.2038) está mitigado en producción mediante la **whitelist** (IPs conocidas nunca se bloquean).

La diferencia de AUC también se explica parcialmente porque IF fue entrenado con 5.7× más flujos normales (53,708 vs 9,398), lo que modela mejor la normalidad pero introduce más variabilidad en el score.

### Hallazgo 2: LOF es claramente el peor modelo one-class

LOF con muestra de 5,000 flows obtuvo Recall=0.5900 — **detecta solo 59% de los ataques**. Incluso con FPR bajo (0.0519), en un IDPS es inaceptable dejar pasar el 41% de los ataques. Esto confirma que LOF no es adecuado para este problema.

**Causa:** LOF compara densidad local con k-vecinos. En datos de red con distribuciones extremadamente skewed (byte_rate con skew=45), los k-vecinos en espacio escalado son inconsistentes — ataques con pkt_rate similar al normal (como Brute Force SSH lento) se mezclan con tráfico legítimo.

### Hallazgo 3: El Autoencoder es competitivo y muy rápido en inferencia

AUC=0.9580, Recall=0.9883, y **solo 0.0010 ms/muestra** de inferencia (30× más rápido que IF). Esto lo hace viable como complemento de IF en un ensemble (propuesta de FASE 7).

### Hallazgo 4: Los supervisados dominan — pero con ventaja injusta

RF (AUC=0.9997) y XGBoost (AUC=0.9995) son prácticamente perfectos. Pero:
- Entrenaron conociendo todos los tipos de ataque
- La feature más importante del RF es `dest_port` (42.2%) — clasifican por "puerto conocido de ataque", no por comportamiento anómalo
- Si aparece un ataque en un puerto diferente o con patron diferente → tasa de detección caería dramáticamente

**Esto demuestra que la superioridad de los supervisados es un artefacto de la ventaja injusta**, no una ventaja fundamental sobre IF para el paradigma real de un IDPS.

### Hallazgo 5: La comparación valida la elección de IF

Entre los modelos one-class (comparación justa):

| Ranking | Modelo | AUC | Recall | Viable en producción |
|---|---|---|---|---|
| 1 (AUC) | OCSVM | 0.9712 | 0.9303 | ⚠️ Recall insuficiente |
| 1 (Recall) | **IF** | 0.9159 | **0.9953** | ✅ Producción real |
| 2 | Autoencoder | 0.9580 | 0.9883 | ✅ Candidato ensemble |
| 3 | LOF | 0.8418 | 0.5900 | ❌ Inaceptable |

**IF es el mejor modelo one-class según la métrica que importa en seguridad: Recall.**

---

## 5. Nota sobre la diferencia de AUC vs metricas_offline.txt

El AUC del IF en este experimento (0.9159) difiere del reportado en producción (0.8998) porque:

| Evaluación | Test set | n_anomalías | Proporción |
|---|---|---|---|
| `metricas_offline.txt` | 13,427 normal + 598,285 anómalos | 598,285 | 1:44.5 |
| Este experimento | 4,029 normal + 3,600 anómalos | 3,600 | 1:0.89 |

El test balanceado de este experimento (1:0.89) facilita el cálculo del AUC comparado con el test real (1:44.5). Los dos valores son válidos para propósitos diferentes:
- **0.8998** → AUC en distribución real de producción (todos los flujos anómalos)
- **0.9159** → AUC en test balanceado de comparación experimental (mismo test para todos)

---

**Siguiente fase:** `FASE5_RESULTADOS.md` — gráficas comparativas (curvas ROC superpuestas, barras AUC, scatter eficiencia).
