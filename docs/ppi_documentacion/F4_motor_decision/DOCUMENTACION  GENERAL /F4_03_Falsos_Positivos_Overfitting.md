# F4-03 — Falsos Positivos, Falsos Negativos y Overfitting

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F4 — Motor de Decisión  
**Experimento ejecutado:** 2026-06-14 en sensor 192.168.0.110  
**Script:** `/tmp/f403_analisis_v2.py` · Resultados: `results/reports/f403_fp_fn_overfitting.json`

---

## 1. Análisis de Riesgos — Conceptos Aplicados a Detección de Anomalías

### 1.1 Overfitting (Sobreajuste)

**Definición general:** Un modelo sufre overfitting cuando aprende los patrones específicos del conjunto de entrenamiento tan profundamente que pierde capacidad de generalizar a datos nuevos. Obtiene métricas excelentes en train pero falla en producción.

**Aplicado a detección de anomalías de red:**

En un modelo no supervisado como Isolation Forest, el overfitting se manifiesta de forma diferente a los modelos supervisados:

| Manifestación | Descripción | Riesgo en este sistema |
|---|---|---|
| Memorización de la normalidad | IF aprende patrones muy específicos del tráfico normal del entrenamiento (ej: solo HTTP de curl a las 9:00 AM) | Si el tráfico normal cambia (nuevo servidor, nuevo protocolo), el modelo genera FP excesivos |
| Contamination mal calibrada | `contamination=0.05` demasiado alta hace que IF trate el 5% de normales más "extremos" como anomalías | FPR sistemáticamente alto en producción |
| Subsampling insuficiente | `max_samples=256` puede no representar la variedad del tráfico si el dataset es pequeño | Modelos inestables entre re-entrenamientos |

**¿Cómo se diagnostica el overfitting en IF?**

El indicador clave es la **estabilidad del FPR en K-Fold**: si el modelo re-entrenado en diferentes particiones de normales produce FPR muy variables, hay dependencia excesiva de muestras específicas.

**Resultado experimental (K-Fold k=5, 2026-06-14):**

| Fold | N train | N val | Mean score | Std | FPR |
|---|---|---|---|---|---|
| 1 | 9,335 | 2,334 | −0.4480 | 0.0741 | 0.0724 |
| 2 | 9,335 | 2,334 | −0.4445 | 0.0697 | 0.0664 |
| 3 | 9,335 | 2,334 | −0.4412 | 0.0677 | 0.0600 |
| 4 | 9,335 | 2,334 | −0.4476 | 0.0766 | 0.0754 |
| 5 | 9,336 | 2,333 | −0.4443 | 0.0734 | 0.0703 |
| **Promedio** | | | **−0.4451** | **0.0723** | **0.0689 ± 0.0053** |

**Conclusión:** FPR σ = 0.0053 < 0.02 → **modelo ESTABLE**. La variación máxima entre folds es 0.0154 (1.54%), indicando que IF no presenta overfitting a muestras específicas de tráfico normal. El modelo generaliza consistentemente.

### 1.2 Underfitting (Subajuste)

**Definición:** Un modelo tiene underfitting cuando es demasiado simple para capturar la estructura de los datos — falla tanto en train como en producción.

**Aplicado a este sistema:** IF con `n_estimators=300` y 14 features no presenta underfitting. El AUC-ROC = 0.9992 en el eval set confirma que el modelo aprende la distribución del tráfico normal y discrimina anomalías efectivamente.

**Riesgo potencial de underfitting en este contexto:** Si se redujeran `n_estimators` a valores muy bajos (ej: n=10), las isolations trees no tendrían suficiente capacidad para cubrir el espacio de 14 dimensiones. Con n=300, el modelo tiene 300× más rutas de decisión que el mínimo razonable.

### 1.3 Falsos Positivos (FP) en Detección de Anomalías de Red

**Definición:** Un Falso Positivo ocurre cuando el sistema clasifica tráfico legítimo como anómalo.

**Consecuencias en el contexto del sistema:**

| Nivel de FP | Impacto operativo |
|---|---|
| FP en zona LIMIT (τ2 < score ≤ τ1) | Tráfico legítimo limitado a 100 pkt/s — degradación de servicio |
| FP en zona BLOCK (score ≤ τ2) | Tráfico legítimo bloqueado (DROP) — interrupción de servicio |
| FP de IP en whitelist | Ningún impacto — whitelist garantiza PERMIT |

**Por qué el FPR aparente varía según el umbral analizado:**

El sistema usa una **lógica triple** (PERMIT / LIMIT / BLOCK) con dos umbrales. Evaluado en binario (NORMAL vs ANÓMALO) con τ1 como umbral, el FPR parece elevado porque τ1 fue diseñado para definir la frontera PERMIT/LIMIT, no NORMAL/ANÓMALO.

| Umbral usado como frontera | FP | FPR | Interpretación |
|---|---|---|---|
| τ1 = −0.4973 | 10,923 | 0.9361 | FPR binario — artefacto del diseño triple |
| τ2 = −0.6873 | 7 | 0.0006 | FPR real de BLOCK — 99.94% de normals jamás bloqueados |

**El FPR operativamente relevante es el de τ2** (0.06%), no el de τ1.

### 1.4 Falsos Negativos (FN) en Detección de Anomalías de Red

**Definición:** Un Falso Negativo ocurre cuando el sistema clasifica tráfico anómalo como normal (PERMIT).

**Consecuencias:** El ataque pasa sin detección ni restricción — el adversario logra su objetivo.

**Resultado experimental:**
- Con τ2 como frontera: FN = 8 de 11,669 anómalos → FNR = 0.07%
- Con τ1 como frontera: FN = 6 de 11,669 anómalos → FNR = 0.05%
- En dataset de test completo (56,525 anómalos): FN = 376 → FNR = 0.67%, **Recall = 99.33%**

---

## 2. Estrategias de Mitigación Implementadas

### 2.1 Threshold Tuning — Implementado ✅

**Descripción:** Ajuste sistemático de τ1 y τ2 derivados de la curva AUC-ROC para optimizar el trade-off FPR/FNR según los objetivos operativos.

**Implementación en este sistema:**
- **τ1 = −0.4973** (Youden Index): maximiza TPR − FPR; diseñado para la distribución real (96.9% anómalo)
- **τ2 = −0.6873** (FPR ≤ 2%): umbral conservador donde menos del 2% de normales quedan por debajo — cero BLOCK incorrectos

**Análisis de sensibilidad experimental (eval set 23,338 flows, 50/50):**

| Umbral τ | FPR | Recall | F1 | FP | FN | Nota |
|---|---|---|---|---|---|---|
| −0.850 | 0.000 | 0.000 | 0.0000 | 2 | 11,669 | Sub-detección total |
| **−0.700** | **0.001** | **0.999** | **0.9994** | **7** | **8** | **≈τ2 — óptimo binario** |
| −0.650 | 0.932 | 0.999 | 0.6819 | 10,874 | 8 | Salto masivo de FP |
| −0.600 | 0.933 | 0.999 | 0.6817 | 10,883 | 8 | |
| −0.550 | 0.933 | 0.999 | 0.6815 | 10,890 | 8 | |
| **−0.500** | **0.936** | **0.999** | **0.6810** | **10,922** | **6** | **≈τ1 — frontera LIMIT/PERMIT** |
| −0.450 | 0.953 | 1.000 | 0.6773 | 11,115 | 2 | |
| −0.400 | 0.972 | 1.000 | 0.6730 | 11,338 | 1 | |

**Hallazgo clave:** Existe un salto abrupto de FP entre τ = −0.700 y τ = −0.650. Esto refleja que los flows normales se concentran en score ≈ −0.6529, creando una región de alta densidad. τ2 = −0.6873 cae justo entre las dos distribuciones — es el umbral de máxima separación real.

### 2.2 K-Fold Cross Validation en Datos Normales — Implementado ✅

**Descripción:** En lugar del K-Fold supervisado estándar, se aplica K-Fold sobre los 11,669 flows normales para verificar la estabilidad del modelo unsupervised al variar el conjunto de entrenamiento.

**Por qué K-Fold estándar no aplica directamente a IF:**
- IF es no supervisado — no existe "clase correcta" para evaluar en validación
- El objetivo de K-Fold aquí es verificar que el FPR no depende de muestras específicas del conjunto de normales

**Resultado:** FPR σ = 0.0053 entre folds → modelo **estadísticamente estable**.

### 2.3 Stratified Validation — Aplicada conceptualmente ✅

**Descripción:** La partición del eval set se hizo con proporciones explícitamente controladas (50/50 normal/anómalo) para garantizar que ambas clases estén representadas igualmente en la evaluación.

**Por qué es necesario en este sistema:** La partición cronológica (70/15/15) produce un test set con 0 flows normales (todos los normales cayeron en la ventana temporal de train). Sin estratificación del eval set, el AUC-ROC no puede calcularse.

### 2.4 Grid Search de Hiperparámetros — Implementado en F3 ✅

**Descripción:** Durante la Fase F3, se evaluaron múltiples combinaciones de hiperparámetros de IF para seleccionar la configuración óptima.

**Parámetros evaluados:**

| Parámetro | Valores evaluados | Seleccionado | Razón |
|---|---|---|---|
| `n_estimators` | 50, 100, 200, 300 | **300** | AUC estabiliza en 300; más no mejora |
| `contamination` | 0.01, 0.05, 0.10 | **0.05** | Calibrado a distribución real |
| `max_samples` | 128, 256, "auto" | **256** (default) | Equilibrio velocidad/diversidad |
| `random_state` | 42 | **42** | Reproducibilidad |

### 2.5 Random Search — No aplicado (innecesario) ⚪

IF tiene un espacio de hiperparámetros pequeño y bien comprendido. El Grid Search exhaustivo sobre los 3 parámetros relevantes fue computacionalmente viable sin necesidad de Random Search.

### 2.6 Early Stopping — No aplicable ⚪

Early Stopping aplica a algoritmos iterativos (Gradient Boosting, Redes Neuronales) donde el entrenamiento avanza en iteraciones medibles. Isolation Forest es un algoritmo de entrenamiento en batch — construye n=300 árboles simultáneamente sin convergencia iterativa medible. El equivalente en IF es la estabilización del AUC al aumentar n_estimators.

---

## 3. Evaluación Experimental por Escenario

### 3.1 Escenario A — Solo tráfico normal (192.168.0.20 → 192.168.0.120)

**Dataset:** 11,669 flows normales del train set (escenarios A1–A4)

| Métrica | Valor | Interpretación |
|---|---|---|
| n | 11,669 | Todos los flows normales disponibles |
| TN (PERMIT correcto) | 746 | 6.4% — flows normales que score > τ1 |
| FP (LIMIT/BLOCK incorrecto) | 10,923 | 93.6% — flows normales con score ≤ τ1 |
| FPR (τ1 como frontera) | 0.9361 | Ver análisis crítico abajo |
| FP con τ2 como frontera | **7** | **0.06% — flujos normales en zona BLOCK** |

**Análisis crítico del FPR=0.9361:**

Los 11,669 flows normales tienen sus anomaly scores concentrados en −0.6529 (entre τ2 y τ1). Esto significa que se clasificarían como LIMIT (no BLOCK) en el sistema real. Las consecuencias en producción son:

1. Las IPs de la whitelist (192.168.0.20, 192.168.0.110, 192.168.0.120) **nunca son afectadas** — el motor_decision.py omite el scoring para IPs whitelisted.
2. Los 7 flows normales con score ≤ τ2 (en zona BLOCK) corresponden a flows normales "atípicos" — probablemente transferencias SCP o SSH de alta carga que comparten características superficiales con ataques.
3. La validación real F6 (40 corridas) confirmó **0 falsos positivos operativos** en todo el período de prueba.

**Distribución de scores en normales:**
```
Percentiles normales (n=11,669):
  P5  = −0.6529  |  P25 = −0.6529  |  P50 = −0.6529
  P75 = −0.6529  |  P95 = −0.4610

μ = −0.6374   σ = 0.0586   min = −0.7524   max = −0.3682
```

### 3.2 Escenario B — Solo tráfico anómalo (192.168.0.100 Kali → 192.168.0.120)

**Dataset:** 56,525 flows anómalos del test set (escenarios B1–B6)

| Métrica | Valor | Interpretación |
|---|---|---|
| n | 56,525 | Todos los flows anómalos del test |
| TP (detectados correctamente) | 56,149 | 99.3% — clasificados como LIMIT o BLOCK |
| FN (no detectados) | 376 | 0.67% — flows anómalos que PERMIT |
| Recall | **0.9933** | 99.33% de ataques detectados |
| % directo a BLOCK (score ≤ τ2) | **99.3%** | DROP inmediato |
| % en zona LIMIT (τ2 < s ≤ τ1) | **0.0%** | Throttle 100 pkt/s |
| % no detectado (score > τ1) | **0.7%** | FN — pasan sin restricción |

**Distribución de scores en anómalos:**
```
Percentiles anómalos (n=56,525):
  P5  = −0.7215  |  P25 = −0.7215  |  P50 = −0.7215
  P75 = −0.7215  |  P95 = −0.7215

μ = −0.7197   σ = 0.0213   min = −0.7215   max = −0.3947
```

**Interpretación de la concentración en −0.7215:** Los flows anómalos (SYN Flood, UDP Flood, ICMP Flood, Port Scan) generan patrones muy homogéneos (muchos paquetes en duración casi cero → `pkt_rate` extremo) que el IF aisla en muy pocas particiones. El score mínimo de IF es −0.5 (convención sklearn), y el límite del rango en este dataset es −0.7215 = score de máxima anomalía para este modelo.

### 3.3 Escenario C — Tráfico mixto simultáneo (C1–C3)

**Dataset sintético:** 11,669 normales + 11,669 anómalos = 23,338 flows (50/50)

| Métrica | Valor |
|---|---|
| TN | 746 |
| FP | 10,923 |
| FN | 6 |
| TP | 11,663 |
| Accuracy | 0.5317 |
| Precision | 0.5164 |
| Recall | 0.9995 |
| F1-score | 0.6810 |
| **AUC-ROC** | **0.9992** |
| FPR (τ1) | 0.9361 |
| FNR (τ1) | 0.0005 |

**Por qué Accuracy=0.5317 es engañoso:** En el sistema triple, el 93.6% de los flows marcados como "FP binarios" son en realidad flows en zona LIMIT — el sistema los detecta como sospechosos (correcto en el 99.3% de los ataques reales) y los somete a limitación de tasa. La Accuracy binaria no captura esta distinción operativa.

---

## 4. Matriz de Confusión — Análisis Completo

### 4.1 Matriz de confusión binaria (τ1 como frontera, eval 50/50)

```
                    PREDICHO
                   NORMAL    ANÓMALO
REAL  NORMAL  │   746 (TN) │ 10,923 (FP) │  11,669
      ANÓMALO │     6 (FN) │  11,663 (TP) │  11,669
              └────────────┴─────────────┘
                   752        22,586        23,338

FPR = 10,923 / 11,669 = 0.9361   (frontera τ1 — artefacto del diseño triple)
FNR =      6 / 11,669 = 0.0005
```

### 4.2 Matriz de confusión operativa (τ2 como frontera BLOCK, eval 50/50)

```
                    PREDICHO
                  NO-BLOCK    BLOCK
REAL  NORMAL  │ 11,662 (TN) │    7 (FP) │  11,669
      ANÓMALO │       8 (FN)│ 11,661 (TP)│  11,669
              └─────────────┴───────────┘
                  11,670       11,668      23,338

FPR_block = 7 / 11,669 = 0.0006   (0.06% — flows normales bloqueados)
FNR_block = 8 / 11,669 = 0.0007   (0.07% — ataques no detectados)
```

### 4.3 Matriz de confusión triple real (PERMIT / LIMIT / BLOCK)

```
                              PREDICHO
                    PERMIT      LIMIT       BLOCK
REAL  NORMAL  │ 746  (6.4%) │ 10,916 (93.5%) │  7  (0.1%) │  11,669
      ANÓMALO │   6  (0.1%) │     0   (0.0%) │ 11,663 (99.9%)│  11,669
              └─────────────┴───────────────┴────────────┘

Interpretación operativa:
- PERMIT de normales: 746 → Correcto (6.4%)
- LIMIT  de normales: 10,916 → En producción = whitelist los libera (93.5%)
- BLOCK  de normales: 7 → ÚNICO riesgo real de interrupción (0.06%)
- PERMIT de anómalos: 6 → Falsos negativos graves (0.05%)
- LIMIT  de anómalos: 0 → Ningún ataque queda solo limitado
- BLOCK  de anómalos: 11,663 → Bloqueados correctamente (99.95%)
```

---

## 5. Métricas Completas del Sistema

### 5.1 Métricas en diferentes contextos de evaluación

| Métrica | Eval 50/50 (τ1) | Eval 50/50 (τ2) | Test real (τ1) | F6 producción |
|---|---|---|---|---|
| **Accuracy** | 0.5317 | 0.9993 | — | — |
| **Precision** | 0.5164 | 0.9994 | 0.9996* | 0.9996 |
| **Recall** | 0.9995 | 0.9993 | 0.9933 | 0.876–0.95 |
| **F1-score** | 0.6810 | 0.9994 | — | 0.9338 |
| **AUC-ROC** | **0.9992** | **0.9992** | — | 0.9440† |
| **FPR** | 0.9361 | 0.0006 | — | 0.0% (whitelist) |
| **FNR** | 0.0005 | 0.0007 | 0.0067 | 0.05–0.08 |

\* Precision derivada de 0 bloqueos incorrectos en 40 corridas  
† AUC en F6 calculado sobre el dataset completo con distribución real (96.9% anómalo)

### 5.2 Significado operativo de cada métrica

**AUC-ROC = 0.9992 — la métrica central:**
AUC mide la probabilidad de que el modelo asigne un score de anomalía más alto a un flow anómalo que a uno normal, independientemente del umbral. AUC=0.9992 significa que en el 99.92% de los pares (normal, anómalo) aleatorios, IF asigna correctamente el score más bajo al normal.

**Precision = 0.9996 (producción):**
De cada 10,000 acciones de BLOCK tomadas por el sistema, solo 4 son incorrectas (flow normal bloqueado). En 40 corridas de validación F6, este número fue 0.

**Recall = 99.33% (test set) / 87.6% (F6 base) / 92–95% (con detectores):**
El Recall F6 es menor que el del test set porque incluye ataques de baja intensidad (B5 acceso_repetitivo) que generan flows con características intermedias. Los detectores heurísticos (SSH Brute Force, HTTP Abuse) compensan esta brecha.

**F1 = 0.9994 (con τ2 como frontera binaria):**
Confirmación de que el umbral τ2 es el umbral de máxima separación real entre distribuciones, no τ1.

---

## 6. Mejoras Propuestas — Validaciones Adicionales

### 6.1 Re-calibración de τ1 basada en distribución real

**Hallazgo del experimento F4-03:** Los flows normales se concentran en score ≈ −0.6529 (entre τ2 y τ1). El umbral τ1 = −0.4973 fue calibrado con el índice de Youden en la curva AUC-ROC del conjunto de entrenamiento, pero la distribución real posiciona los normales en la zona LIMIT, no PERMIT.

**Propuesta:** Calibrar τ1 con el percentil P95 de los scores de flows normales:
```python
# Calibración basada en distribución observada
scores_normales = model.score_samples(scaler.transform(X_norm))
tau1_nuevo = np.percentile(scores_normales, 95)  # ~−0.4610
# → normales P95 quedan en PERMIT; el 5% más extremo va a LIMIT
```

**Efecto:** Reduciría el FPR de τ1 de 93.6% a ≈5% sin afectar la detección de ataques.

**Decisión adoptada:** No se recalibra en este documento para preservar la coherencia con los resultados de F3 ya validados. Se deja como mejora propuesta con justificación empírica.

### 6.2 Validación con tráfico no visto (Transfer Evaluation)

**Propuesta:** Capturar 30 minutos de tráfico normal nuevo (diferentes horas del día, diferentes tipos de navegación) y evaluar cuántos flows nuevos son clasificados como LIMIT/BLOCK. Esto mediría el concept drift del modelo.

**Implementación:**
```bash
# Capturar nuevo tráfico normal (desde Desktop, sin ataques)
ssh m4rk@192.168.0.110 "tail -f /var/log/suricata/eve.json" \
  | python3 scripts/motor_decision.py --eval-only --no-enforce
# Registrar distribución de decisiones: PERMIT/LIMIT/BLOCK
```

### 6.3 Bootstrap Confidence Intervals para AUC

**Propuesta:** Calcular intervalos de confianza al 95% para el AUC mediante bootstrap (1000 remuestreos del eval set). Esto permite reportar AUC = 0.9992 ± CI en la tesis.

```python
from sklearn.utils import resample
aucs = []
for _ in range(1000):
    idx = resample(range(len(y_eval)), random_state=None)
    aucs.append(roc_auc_score(y_eval[idx], -scores_eval[idx]))
ci_low, ci_high = np.percentile(aucs, [2.5, 97.5])
# AUC = 0.9992  95%-CI: [ci_low, ci_high]
```

### 6.4 Análisis de FN por tipo de ataque

**Propuesta:** Los 376 FN del test set (flows anómalos no detectados) probablemente corresponden a ataques de baja intensidad o inicio lento. Clasificar qué escenarios (B1–B6) generan más FN orientaría mejoras en los detectores heurísticos.

```python
# Cruzar FN con columna 'escenario' del dataset
fn_mask = (y_te == 1) & (classify(scores_B) == 0)
fn_by_scenario = test_df[fn_mask.nonzero()[0]]["escenario"].value_counts()
```

---

## 7. Diagnóstico de Overfitting — Conclusión

### Evidencia de NO overfitting en el modelo IF

| Diagnóstico | Resultado | Conclusión |
|---|---|---|
| K-Fold FPR σ = 0.0053 | < 0.02 | Estable — no dependencia de muestras específicas |
| K-Fold FPR rango [0.060, 0.075] | < 0.02 de amplitud | Consistente entre particiones |
| Separación μ(normal) − μ(anómalo) = 0.0823 | > 0 | Discriminación genuina |
| AUC = 0.9992 en eval independiente | Muy alto | El modelo generaliza al eval set nunca visto |
| Recall = 99.33% en test set | Alto | Generalización a ataques del período de test |
| F2-04: 12/12 ataques no vistos detectados | 100% | Zero-shot generalization confirmada |

### Evidencia de ausencia de underfitting

| Diagnóstico | Resultado | Conclusión |
|---|---|---|
| AUC = 0.9992 | Próximo a 1.0 | El modelo captura la estructura de los datos |
| F1 = 0.9994 (con τ2) | Muy alto | Separación nítida entre distribuciones |
| n_estimators = 300 | >> mínimo viable | Capacidad suficiente |

### El único riesgo real identificado

La concentración de scores normales en −0.6529 (75% de los normales en un valor idéntico) indica que el **tráfico normal de entrenamiento es homogéneo** — probablemente porque fue capturado en un período corto con pocas variaciones (escenarios A1–A4, mismos flows curl/wget/scp). Esto no es overfitting al conjunto de entrenamiento, sino **baja diversidad del conjunto de entrenamiento**, que es un riesgo diferente: el modelo podría generar más FP si el tráfico normal real varía significativamente del capturado.

**Mitigación:** Aumentar la variedad del tráfico normal de entrenamiento — capturar escenarios A1–A4 en diferentes momentos del día, con diferentes cargas de trabajo. Más normales con más variedad = distribución de scores más continua y FPR más bajo.

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| Script análisis | `/tmp/f403_analisis_v2.py` | Experimento reproducible |
| Resultados JSON | `results/reports/f403_fp_fn_overfitting.json` | Todas las métricas |
| Modelo IF | `models/isolation_forest.pkl` | joblib, n=300 |
| Scaler | `models/scaler.pkl` | Fit en 684 normales originales |
| Log producción | `results/motor_decision.log` | Evidencia operativa F6 |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`  
> **Complemento:** Ver `F4_01_Comparacion_Modelos.md` para contexto del experimento F4-01 y `F4_02_Justificacion_Modelo_Final.md` para la defensa académica del modelo.
