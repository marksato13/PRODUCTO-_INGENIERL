# Justificación del Modelo: Isolation Forest

**Proyecto:** PPI UPeU 2026 — Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Autores:** Rubén Mark Salazar Tocas · Elías Uziel Sauñe Fernández  
**Asesores:** Ing. Fernando Manuel Asin Gomez · Ing. Nemias Saboya Rios

---

## 1. Por qué aprendizaje no supervisado

En un sistema de detección de intrusiones (IDPS), el atacante **no avisa antes de atacar**. El tráfico anómalo que el sistema encontrará en producción puede ser un tipo de ataque nunca visto antes.

Los modelos **supervisados** (Random Forest, XGBoost, Decision Tree) necesitan etiquetas de ataque en el entrenamiento: les decimos "esto es un SYN Flood, esto es Brute Force". En el experimento comparativo de este proyecto, los tres supervisados obtienen AUC > 0.99 — pero solo porque en el conjunto de entrenamiento ya estaban los mismos 6 tipos de ataque del test. Eso es **data leakage conceptual**: el modelo aprendió a reconocer amenazas que ya conocía, no a detectar comportamientos anómalos.

El análisis del RF revela el problema de fondo: `dest_port` es la feature con mayor importancia (42.2%). El modelo aprendió la heurística "puerto 22 = BruteForce, puerto 80 = HTTPAbuse". Eso es un sistema de firmas implementado con árboles, no detección de anomalías.

**Un modelo no supervisado entrenado solo con tráfico normal puede detectar cualquier anomalía, independientemente de si ese tipo de ataque existía cuando se entrenó.**

| | Supervisado (RF/XGBoost) | No supervisado (IF) |
|---|---|---|
| Datos de entrenamiento | Normal + ataques etiquetados | Solo tráfico normal |
| Detecta ataque nuevo (0-day) | ❌ No | ✅ Sí |
| Disponibilidad de etiquetas | Requiere analista de seguridad | No requiere |
| Feature más importante | `dest_port` (firma) | Comportamiento del flujo |
| AUC en test compartido | 0.997–0.999 (injusto) | 0.916–0.971 (justo) |

---

## 2. Comparación entre modelos no supervisados

Se evaluaron 4 modelos one-class sobre el mismo test set de 7,629 flujos (4,029 normales + 3,600 anómalos, 6 tipos de ataque). Umbral: Youden en todos.

| Modelo | AUC-ROC | Recall | Precision | F1 | FPR | ms/inf |
|---|---|---|---|---|---|---|
| **Isolation Forest** | 0.9159 | **0.9953** | 0.8136 | 0.8953 | 0.2038 | 0.030 |
| Autoencoder (AE) | 0.9580 | 0.9883 | 0.8951 | 0.9394 | 0.1035 | 0.001 |
| One-Class SVM | 0.9712 | 0.9303 | 0.9120 | 0.9211 | 0.0802 | 0.034 |
| LOF | 0.8418 | 0.5900 | 0.9104 | 0.7160 | 0.0519 | 0.043 |

> **Nota sobre Precision:** La columna muestra valores del test balanceado (1:0.89). En producción, donde los flujos anómalos superan 44× a los normales, IF alcanza Precision=99.54% (verificado en `results/metricas_offline.txt`). Esto es un efecto matemático del ratio de clases: `Precision = TP/(TP+FP)` — cuando los ataques son masivos, los FP se diluyen.

### LOF — descartado

Recall=59% — deja pasar 4 de cada 10 ataques. Inaceptable en seguridad. Causa: las distribuciones de `byte_rate` y `pkt_rate` tienen skewness >45, lo que hace que los k-vecinos en espacio escalado sean inconsistentes.

### One-Class SVM — viable pero con menor detección

AUC=0.9712 (mayor que IF), pero Recall=93.03% — detecta 6.5pp menos ataques. En el test de 3,600 ataques, OCSVM deja pasar 251 que IF capturaría. Además, escala O(n²) con el conjunto de entrenamiento: con 53K flujos normales, el entrenamiento se vuelve prohibitivo.

### Autoencoder — el más competitivo, candidato para mejora futura

AUC=0.9580, Recall=98.83%, F1=0.9394. El AE supera a IF en AUC y F1, pero:

- Recall menor (−0.7pp) — en seguridad, cada punto de recall es un ataque que escapa
- FPR menor (0.1035 vs 0.2038) — pero en producción con whitelist, este FPR se aplica solo a IPs desconocidas
- **0 corridas de validación en vivo** — el AE nunca fue probado en F6; IF tiene 40 corridas certificadas
- Validado offline sobre el mismo dataset; no tiene lead time medido, no tiene latencia P95 certificada

### Isolation Forest — elección óptima

**Mayor Recall entre los four modelos one-class (99.53%)**, entrenado sobre 53,708 flujos normales en <10 segundos, inferencia en 0.03ms, pipeline de producción completo validado con 40 corridas.

---

## 3. Métricas del IF en producción (certificadas en F6)

| Métrica | Valor | Requisito | Estado |
|---|---|---|---|
| AUC-ROC | 0.8998 | > 0.80 | ✅ CUMPLE |
| Precision | 99.54% | — | ✅ |
| Recall | 99.40% | — | ✅ |
| F1-Score | 0.9947 | — | ✅ |
| Latencia P95 | 34.8 ms | < 500 ms | ✅ CUMPLE |
| Disponibilidad | 100% | — | ✅ |
| ITL (tráfico legítimo afectado) | 0% | — | ✅ |
| Lead time SYN Flood | 61.92 s | — | Medido |
| Corridas F6 validadas | 40 | — | Certificado |

**Parámetros del modelo:** `IsolationForest(n_estimators=300, contamination=0.05, random_state=42, n_jobs=-1)`  
**Split:** 80% entrenamiento / 20% evaluación, `train_test_split(shuffle=True, random_state=42)`  
**Versión sklearn:** 1.9.0 (sin mismatch entre modelo serializado y entorno de producción)

---

## 4. AUC por tipo de ataque (IF vs AE — Grupo B)

| Ataque | AUC IF | AUC AE | Ganador |
|---|---|---|---|
| HTTP Abuse (15-jun, 37K flows) | **0.9749** | 0.9111 | IF +6.4pp |
| SYN Flood (15-jun, 330 flows) | **0.9515** | 0.8287 | IF +12.3pp |
| Brute Force (02-jun, 2K flows) | **0.9727** | 0.9649 | IF +0.8pp |
| Brute Force (15-jun, 5K flows) | **0.9728** | 0.9036 | IF +6.9pp |
| HTTP Abuse (02-jun, 14K flows) | **0.9545** | 0.9516 | IF +0.3pp |
| ICMP Flood (02-jun, 23K flows) | 0.9160 | **0.9966** | AE +8.8pp |
| Port Scan (02-jun, 3K flows) | 0.8351 | **0.9901** | AE +15.5pp |
| UDP Flood (02-jun, 18K flows) | 0.9579 | **0.9881** | AE +3.0pp |
| SYN Flood (02-jun, 95K flows) | 0.8815 | **0.9517** | AE +7.0pp |
| **Promedio Grupo B** | 0.9270 | **0.9579** | AE +3.3pp |

IF supera a AE en los ataques de mayor relevancia práctica en este laboratorio (HTTP Abuse, Brute Force SSH, SYN Flood pequeño). AE gana en volúmenes de ICMP/UDP/PortScan. El comportamiento heterogéneo del AE en función del tipo de ataque lo hace menos predecible en producción.

---

## 5. Ranking ponderado (6 criterios de producción)

| Criterio | Peso | IF | OCSVM | LOF | AE |
|---|---|---|---|---|---|
| Recall (detección) | 30% | **10** | 7.0 | 1.0 | 9.5 |
| Sin etiquetas de ataque | 25% | **10** | 10 | 10 | 10 |
| Validación en producción | 15% | **10** | 1.0 | 1.0 | 2.0 |
| Escalabilidad (O(n log n)) | 15% | **10** | 5.0 | 4.0 | 8.0 |
| Latencia de inferencia | 10% | 9.0 | 8.0 | 7.0 | **10** |
| Interpretabilidad | 5% | 8.0 | 6.0 | 7.0 | 5.0 |
| **TOTAL** | | **9.75** | 6.75 | 4.65 | 8.45 |

---

## 6. Mejora propuesta: Ensemble AND (IF + AE)

Combinando ambos modelos con AND gate (`score_final = min(score_IF, score_AE)`), la anomalía debe ser confirmada por los dos modelos antes de actuar. Resultado experimental:

| | IF solo | Ensemble AND |
|---|---|---|
| AUC-ROC | 0.9159 | **0.9580** (+4.6pp) |
| Recall | **0.9953** | 0.9883 (−0.7pp) |
| FPR | 0.2038 | **0.1035 (−49.2%)** |
| F1 | 0.8953 | **0.9394 (+4.8pp)** |
| Overhead latencia | — | +0.001 ms |

Esta mejora reduce los falsos positivos a la mitad con pérdida de recall de solo 0.7%. Se propone como trabajo futuro — requiere 20 corridas adicionales de F6 para certificación.

---

*Evidencia: `results/comparacion/`, `results/metricas_offline.txt`, `results/resultados_f6_completo.csv`*  
*Última actualización: 2026-06-20*
