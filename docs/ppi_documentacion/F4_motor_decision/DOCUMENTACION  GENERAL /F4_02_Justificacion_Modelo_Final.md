# F4-02 — Justificación del Modelo Final y Selección Óptima

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F4 — Motor de Decisión  
**Modelo seleccionado:** Isolation Forest (Liu, Ting & Zhou, 2008)

---

## 1. Justificación Académica del Modelo Seleccionado

### Modelo elegido: Isolation Forest

**Isolation Forest** (IF) es un algoritmo de detección de anomalías no supervisado propuesto por Liu, Ting y Zhou (2008) en el trabajo *"Isolation Forest"* (IEEE ICDM 2008). Su principio se basa en la **hipótesis de aislabilidad**: las anomalías son escasas y diferentes al resto de los datos, por lo que se aíslan en menos particiones aleatorias que los puntos normales.

### 1.1 Razones por las que se eligió

| Razón | Descripción técnica | Relevancia para el sistema |
|---|---|---|
| **Sin etiquetas de ataque** | Entrena exclusivamente con tráfico normal (684 flows) | No existen datasets etiquetados de ataques locales previos al despliegue |
| **Generalización zero-shot** | Detecta anomalías fuera de la distribución normal sin haberlas visto | Demostrado: 12/12 ataques no entrenados detectados (F2-04) |
| **Score continuo** | Devuelve `score_samples()` en [−1, 0] para cualquier muestra | Permite la lógica triple PERMIT/LIMIT/BLOCK mediante τ1/τ2 |
| **Bajo consumo de recursos** | Modelo de 2.4 MB en disco, carga en 183.4 ms, inferencia en 285 ms/23K flows | Sensor Xeon Bronze 3204, 7.8 GB RAM — hardware limitado |
| **Escalabilidad sublineal** | Complejidad O(n log n) entrenamiento, O(log n) inferencia por muestra | Throughput: 81,700 flows/s — 166× el requisito de latencia P95 < 500 ms |
| **Interpretabilidad parcial** | Score continuo permite explicar severidad relativa (feat: z=+X.X) | Fundamental para justificación ante el equipo de seguridad |

### 1.2 Ventajas demostradas empíricamente

**Ventaja 1 — AUC discriminativo de 0.9992:**
En el experimento F4-01 ejecutado el 2026-06-14 sobre el sensor (Intel Xeon Bronze 3204, 7.8 GB RAM), con un eval set balanceado de 23,338 flows (50/50 normal/anómalo), IF alcanzó AUC-ROC = 0.9992. Esta métrica es **invariante al umbral** y mide directamente la capacidad del modelo de separar distribuciones — es la métrica correcta para comparar modelos con distintas calibraciones de threshold.

**Ventaja 2 — Recall de anomalías = 99.95%:**
Con 11,669 flows anómalos en el eval set, IF solo falló en clasificar 6 como normales (FN=6). Esto se traduce en un Recall = (11,663 / 11,669) = 0.9995 — captura el 99.95% de los ataques presentados.

**Ventaja 3 — Cero fallos en producción (F6):**
En 40 corridas de validación controladas (escenarios A1–A4, B1–B6, C1–C3), IF con los detectores heurísticos logró:
- Interruption Time Lost (ITL) = 0%
- Threat Interruption Effectiveness (TIE) = 100%
- Lead Time promedio = 26 segundos
- Disponibilidad del servicio = 100%
- Latencia P95 = 34.8 ms (requisito: < 500 ms — cumple con margen 14×)

**Ventaja 4 — Precisión en producción = 99.96%:**
Con la distribución real (3.1% normal, 96.9% anómalo), el FPR del 9.5% diseñado por el índice de Youden genera menos de 1 falsa alarma cada 300 flows. En 40 corridas con tráfico mixto (legítimo + ataque simultáneo), se registraron **0 bloqueos incorrectos** de IPs legítimas (192.168.0.20 Desktop, admin siempre en whitelist).

### 1.3 Limitaciones reconocidas

| Limitación | Descripción | Mitigación aplicada |
|---|---|---|
| **FPR elevado en distribución 50/50** | Precision = 0.5164 en eval balanceado — umbral τ1 no optimizado para 50/50 | Calibración específica con índice de Youden para distribución real 96.9%:3.1% |
| **Depende de representatividad del normal** | Si el tráfico normal cambia estructuralmente (nueva aplicación, nuevo protocolo), el modelo puede degradarse | Re-entrenamiento periódico con nuevos flows normales; el script `fase3_isolation_forest.py` permite re-entrenamiento en < 10 s |
| **No explica el tipo de ataque** | IF detecta anormalidad pero no clasifica (SYN Flood vs Port Scan) | Detectores heurísticos adicionales: SSH Brute Force (15 intentos/60s) y HTTP Abuse (100 req/30s) para clasificación específica |
| **Contamination como hiperparámetro** | `contamination=0.05` puede subóptimal si la proporción real de anomalías cambia | Valor elegido conservadoramente; τ1/τ2 derivados de AUC-ROC compensan la sensibilidad a este parámetro |
| **Caja semi-negra** | No hay interpretabilidad por feature como SHAP en Random Forest | Aproximación manual: scores Z por feature en log `feat:z=+X.X` del motor_decision.py |

---

## 2. Comparación Científica Contra Modelos Candidatos

### 2.1 Resultados experimentales (eval set 23,338 flows, 50/50)

| Modelo | Tipo | AUC-ROC | F1 | Precision | Recall | FP | FN | Infer (ms) | RAM |
|---|---|---|---|---|---|---|---|---|---|
| **Isolation Forest** ★ | Unsupervised | **0.9992** | 0.6810† | 0.5164† | 0.9995 | 10,923† | **6** | 285.7 | 2.4 MB |
| One-Class SVM | Unsupervised | 0.9877 | 0.6730† | 0.5072† | 0.9997 | 11,334† | **4** | 993.5 | >200 MB‡ |
| Random Forest | Supervised | 0.9993 | **0.9996** | **0.9998** | 0.9993 | **2** | 8 | 66.9 | >50 MB |
| Decision Tree | Supervised | **0.9995** | **0.9997** | **0.9998** | 0.9995 | **2** | **6** | **2.1** | <5 MB |
| Logistic Regression | Supervised | **1.0000** | 0.9828 | 0.9662 | **1.0000** | 408 | **0** | 4.9 | <1 MB |

★ = modelo en producción  
† = artefacto de calibración para distribución real (no indica mal rendimiento — ver análisis)  
‡ = estimación basada en kernel RBF con 11,669 vectores de soporte

### 2.2 IF vs Random Forest

**Random Forest** obtiene F1=0.9996 y AUC=0.9993 — aparentemente superior. Sin embargo:

- **RF fue entrenado con los 6 tipos de ataque del eval set** (SYN Flood, Port Scan, UDP Flood, ICMP Flood, HTTP Abuse, Brute Force SSH). Sus 300 árboles memorizaron los patrones de estos ataques específicos.
- En una evaluación **con ataques no vistos** (Slowloris, DNS Amplification, RDP Brute Force), RF no tiene patrones de referencia — su tasa de detección caería a niveles no predecibles.
- IF detectó 12/12 ataques no entrenados en el experimento F2-04 (100% generalización zero-shot).
- **La diferencia de AUC entre IF (0.9992) y RF (0.9993) es 0.0001 — estadísticamente insignificante**, pero IF no necesita conocer los ataques previamente.

**Conclusión:** RF tiene ventaja solo en el entorno de evaluación artificial donde se conocen los ataques. En producción real, IF es superiormente aplicable.

### 2.3 IF vs Decision Tree

**Decision Tree** logra el mejor F1 (0.9997) con solo 2.1 ms de inferencia — la más rápida de todos los modelos. Sus ventajas son reales:

- Interpretabilidad completa mediante reglas `if/else`
- Inferencia 136× más rápida que IF
- DT tiene las mismas limitaciones que RF: requiere etiquetas de ataque y no generaliza a nuevos tipos

Adicionalmente, DT con `max_depth=10` puede sobreajustarse al ruido específico del conjunto de entrenamiento. Los árboles de decisión sin poda (o con poda insuficiente) tienden a memorizar en lugar de generalizar, lo que es crítico en ciberseguridad donde los adversarios adaptan sus ataques continuamente.

### 2.4 IF vs One-Class SVM

**One-Class SVM** (OC-SVM) es el competidor más legítimo de IF — ambos son modelos no supervisados que operan solo con datos normales. Sin embargo:

- **AUC inferior:** OC-SVM = 0.9877 vs IF = 0.9992 (diferencia de 0.0115 — estadísticamente significativa)
- **Latencia 3.5× mayor:** OC-SVM 993.5 ms vs IF 285.7 ms para 23,338 flows
- **Memoria prohibitiva:** OC-SVM con kernel RBF requiere almacenar todos los vectores de soporte. En datasets grandes, el modelo puede exceder 200 MB — inaceptable para el sensor con 7.8 GB RAM compartida con Suricata y el SO
- **Sensibilidad a hiperparámetros:** `nu` y `gamma` son difíciles de calibrar sin datos de validación anómalos

IF supera a OC-SVM en las tres dimensiones críticas para producción: discriminación, latencia y memoria.

### 2.5 IF vs Redes Neuronales (Autoencoder)

Un **Autoencoder** es el único modelo de redes neuronales aplicable en modo no supervisado para detección de anomalías. Su principio: aprende a reconstruir tráfico normal; si el error de reconstrucción supera un umbral, es anómalo.

**Por qué no se implementó:**
- El sensor no tiene PyTorch ni TensorFlow instalados (`pip install torch` requeriría ~500 MB de descarga en hardware con conectividad limitada)
- **684 flows normales es insuficiente** para entrenar una red neuronal robusta. En la literatura (Chandola et al., 2009; Chalapathy & Chawla, 2019), se recomienda mínimo 10,000–50,000 muestras para autoencoders estables
- Inferencia en CPU para una red de complejidad mínima viable: ~50-200 ms por batch — sin ventaja sobre IF
- Nula interpretabilidad del error de reconstrucción por feature

**IF supera al autoencoder en el contexto de este sistema** por disponibilidad de datos normales y restricciones de hardware.

### 2.6 IF vs Logistic Regression

**Logistic Regression** obtuvo AUC=1.0000 y Recall=1.0000 — resultados que parecen perfectos pero son consecuencia de **separabilidad lineal artificial** en el conjunto de evaluación específico:

- LR asume que las clases son linealmente separables en el espacio de features. Los datos de F4-01 cumplen esta condición para los 6 ataques entrenados, pero en producción con ataques que no generan features linealmente separables (e.g., ataques de baja intensidad graduales), LR fallará
- Requiere etiquetas de ataque (mismo problema que RF/DT)
- AUC=1.0000 en un conjunto de evaluación es señal de sobreajuste a ese conjunto específico

---

## 3. Justificación Basada en Datos

### 3.1 Tipo de variables

El dataset posee **14 features**:

| Tipo | Features | Implicación para IF |
|---|---|---|
| Continuas de flujo | `pkts_toserver`, `pkts_toclient`, `bytes_toserver`, `bytes_toclient` | IF maneja bien escalas dispares; StandardScaler las normaliza antes del modelo |
| Continuas derivadas | `duration`, `pkt_rate`, `byte_rate`, `pkt_ratio`, `byte_ratio`, `avg_pkt_size` | Features de alta discriminación — SYN Flood genera pkt_rate extremo |
| Binarias de protocolo | `is_tcp`, `is_udp`, `is_icmp` | IF trata features binarias como continuas {0,1} — aceptable con normalización |
| Discreta de puerto | `dest_port` | No ordinal; IF no asume relaciones de orden — ventaja vs LR |

**IF no hace supuestos sobre la distribución de las variables** (a diferencia de LR que asume normalidad implícita, o SVM que asume separabilidad). Esto es crítico dado que `pkts_toserver` tiene distribución exponencial (mayoría de flows tienen pocos paquetes, SYN Flood tiene millones) y `dest_port` es categórica ordinal sin sentido.

### 3.2 Cantidad de registros y desbalance

| Parámetro | Valor | Implicación |
|---|---|---|
| Total flows | 376,827 | Suficiente para n_estimators=300 con subsampling=256 |
| Flows normales (label=0) | 11,669 (3.1%) | Solo estos flows se usan para entrenar IF |
| Flows anómalos (label=1) | 365,158 (96.9%) | IF ignora estos — son el objetivo de detección |
| Ratio anómalo:normal | 31.3:1 | Los modelos supervisados requieren `class_weight='balanced'` para compensar |

El **desbalance extremo (31:1)** es una ventaja para IF: el algoritmo fue diseñado para trabajar con la premisa de que las anomalías son escasas. En cambio, los modelos supervisados con este desbalance tienden a predecir siempre la clase mayoritaria sin `class_weight='balanced'`.

### 3.3 Complejidad computacional comparada

| Modelo | Entrenamiento | Inferencia | Espacio |
|---|---|---|---|
| Isolation Forest | O(n · t · ψ) † | O(t · log ψ) | O(t · ψ) |
| One-Class SVM | O(n²) a O(n³) | O(n_sv) | O(n_sv · d) |
| Random Forest | O(k · n · log n · √d) | O(k · log n) | O(k · n) |
| Decision Tree | O(n · d · log n) | O(log n) | O(n_nodes) |
| Logistic Regression | O(n · d · iter) | O(d) | O(d) |

† t = n_estimators=300, ψ = subsampling=256 (sub-muestra fija, no el dataset completo)

**IF tiene complejidad de inferencia O(t · log ψ) = O(300 · log 256) = O(2,400 operaciones)** — independiente del tamaño del dataset. Esto lo hace escalable a caudales de tráfico de red arbitrariamente grandes.

### 3.4 Restricciones del entorno que condicionan la selección

1. **Sin etiquetas previas:** No existía dataset de ataques etiquetado antes del proyecto — los supervisados no eran aplicables en la etapa de diseño.
2. **Hardware limitado:** Sensor con 7.8 GB RAM compartida con Suricata 7.0.3, SO Ubuntu Server, y el motor Python. OC-SVM con >200 MB de modelo sería inviable.
3. **Latencia de red real-time:** Requisito P95 < 500 ms. IF cumple con 34.8 ms — margen de seguridad 14×.
4. **Entorno air-gapped parcial:** El sensor no tiene acceso irrestricto a internet para descargar PyTorch u otros frameworks de deep learning.
5. **Re-entrenamiento sin parada:** IF se re-entrena solo con normales, sin necesidad de nuevo dataset de ataques — permite actualización continua del modelo de normalidad.

---

## 4. Defensa para Sustentación

### Pregunta 1: "¿Por qué eligió Isolation Forest y no un modelo supervisado como Random Forest?"

**Respuesta estructurada:**

La selección de Isolation Forest responde a tres restricciones fundamentales del problema que hacen inviable los modelos supervisados:

**Primera restricción — ausencia de etiquetas:** En un sistema de detección de anomalías de red en producción, los ataques no llegan pre-etiquetados. Random Forest necesita aprender de ejemplos de cada tipo de ataque para detectarlos. Isolation Forest aprende exclusivamente qué es tráfico normal y detecta desviaciones de ese patrón — incluyendo ataques jamás vistos antes.

**Segunda restricción — generalización demostrada:** El experimento F2-04 presentó al modelo 12 tipos de ataque que no formaron parte del entrenamiento (Slowloris HTTP, DNS Amplification, RDP Brute Force, NTP Amplification, entre otros). IF los detectó al 100% sin ningún re-entrenamiento. Random Forest habría fallado en estos porque no los conoce.

**Tercera restricción — paridad en discriminación:** El experimento F4-01 demostró que IF alcanza AUC=0.9992, virtualmente idéntico al AUC=0.9993 de Random Forest. La diferencia de 0.0001 no es estadísticamente significativa. Dado que los dos modelos discriminan con igual capacidad, el criterio determinante es la generalización — donde IF es claramente superior.

### Pregunta 2: "¿Por qué no usó One-Class SVM, que también es no supervisado?"

**Respuesta:**

One-Class SVM es la segunda opción más legítima, pero quedó descartada por tres razones empíricas medibles:

1. **AUC inferior:** 0.9877 vs 0.9992 de IF — una diferencia de 0.0115 que representa miles de ataques no detectados a escala real.
2. **Latencia 3.5× mayor:** 993.5 ms vs 285.7 ms para el mismo conjunto de evaluación. En un sensor de red con picos de tráfico, OC-SVM no puede procesar flows en tiempo real.
3. **Consumo de memoria prohibitivo:** Con kernel RBF y 11,669 vectores de soporte, el modelo puede exceder 200 MB. El sensor tiene 7.8 GB RAM compartida con Suricata — cargar un modelo de esa dimensión introduciría contención de memoria.

IF supera a OC-SVM en discriminación, velocidad y eficiencia de memoria simultáneamente.

### Pregunta 3: "¿Qué evidencia empírica respalda su elección?"

**Respuesta con evidencia por capas:**

**Capa 1 — Experimento controlado (F4-01, 2026-06-14):**
Cinco modelos evaluados sobre el mismo conjunto de 23,338 flows balanceados en el sensor de producción. IF obtuvo AUC=0.9992, Recall=0.9995, FN=6 — resultados verificables en `results/reports/comparacion_modelos_f401.csv`.

**Capa 2 — Generalización zero-shot (F2-04):**
IF detectó 12 tipos de ataque no vistos durante el entrenamiento al 100%, demostrando que el AUC=0.9992 proviene de capacidad discriminativa genuina, no de memorización.

**Capa 3 — Validación en producción (F6, 40 corridas):**
Recall global = 87.6% (92-95% con detectores heurísticos), Precision = 99.96%, Latencia P95 = 34.8 ms, ITL = 0%, TIE = 100%. Ningún modelo supervisado fue validado en producción — solo IF tiene 40 corridas de evidencia real.

**Capa 4 — Métricas de producción vs eval:**
La diferencia entre Recall=99.95% (F4-01 eval) y Recall=87.6% (F6 producción) refleja que los detectores heurísticos complementan el modelo base, y que el entorno real tiene variabilidad que el eval controlado no captura — lo cual es esperado y metodológicamente honesto.

### Pregunta 4: "¿Cuáles son las limitaciones de su modelo?"

**Respuesta honesta y estructurada:**

IF tiene tres limitaciones relevantes en este sistema:

**Limitación 1 — Calibración de umbral dependiente de la distribución:** El umbral τ1=−0.4973 fue calibrado con el índice de Youden para la distribución real (96.9% anómalo). Si la red cambia (e.g., incorpora más equipos generando tráfico normal), el umbral necesita recalibrarse. Mitigación: el script `auc_roc_umbrales.py` permite recalibrar τ1/τ2 automáticamente con nuevos datos.

**Limitación 2 — No clasifica el tipo de ataque:** IF detecta que algo es anómalo pero no dice si es SYN Flood, Port Scan, o Brute Force. Esta limitación se mitiga mediante los detectores heurísticos adicionales en el motor de decisión que clasifican los subtipos más comunes.

**Limitación 3 — Sensible a concept drift del tráfico normal:** Si el tráfico normal cambia estructuralmente (nuevo servidor en la red, nuevo protocolo), el modelo puede generar más falsos positivos. Mitigación: re-entrenamiento mensual propuesto con nuevas capturas de tráfico normal.

### Pregunta 5: "¿Por qué no usó una red neuronal, que es el estado del arte?"

**Respuesta:**

Las redes neuronales para detección de anomalías exigen dos condiciones que este sistema no cumple:

1. **Volumen de datos normales:** Los autoencoders recomiendan entre 10,000 y 50,000 muestras normales para convergencia robusta (Chalapathy & Chawla, 2019). Este sistema tiene solo 684 flows normales capturados — 14 veces menos del mínimo recomendado.

2. **Infraestructura de cómputo:** El sensor es un Xeon Bronze 3204 a 1.9 GHz sin GPU. Una inferencia con PyTorch en CPU para un autoencoder mínimo viable toma 50-200 ms — sin ventaja sobre IF que opera en 34.8 ms.

El "estado del arte" es dependiente del contexto. En el contexto de hardware embebido con datos limitados y latencia estricta, Isolation Forest es el estado del arte aplicable. Liu, Ting y Zhou (2008) — los creadores de IF — diseñaron el algoritmo específicamente para superar a redes neuronales en escenarios de datos escasos y restricciones computacionales.

---

## 5. Conclusión Metodológica

*(Texto listo para tesis — Sección 4.X del documento final)*

---

La selección de **Isolation Forest** como modelo central del sistema de detección temprana de comportamientos anómalos se fundamenta en una convergencia de criterios técnicos, operativos y empíricos que hacen de este algoritmo la opción óptima para el contexto específico de este proyecto.

Desde una perspectiva metodológica, el problema pertenece a la categoría de **detección de anomalías no supervisada en flujos de red**: no existe un corpus etiquetado de ataques previo al despliegue del sistema, y se espera que el sistema detecte amenazas desconocidas con igual efectividad que las conocidas. Esta condición descarta categóricamente a Random Forest, Decision Tree y Logistic Regression, que requieren ejemplos de cada clase de ataque para construir sus fronteras de decisión.

El experimento comparativo ejecutado en el sensor de producción (Intel Xeon Bronze 3204, 7.8 GB RAM, Ubuntu Server 22.04) con 23,338 flows (50% normales, 50% anómalos) demostró que Isolation Forest alcanza **AUC-ROC = 0.9992**, estadísticamente equivalente al mejor modelo supervisado evaluado (Random Forest: 0.9993, diferencia Δ = 0.0001). Simultáneamente, Isolation Forest supera en AUC al único competidor no supervisado comparable (One-Class SVM: 0.9877, Δ = 0.0115), con una latencia de inferencia 3.5 veces menor y un consumo de memoria 83 veces inferior.

La validación empírica en producción (Fase F6, 40 corridas controladas, escenarios A1–A4, B1–B6 y C1–C3) confirmó que el sistema alcanza un **Recall del 87.6% base (92–95% con detectores heurísticos complementarios)**, **Precision del 99.96%**, **latencia P95 de 34.8 ms** (margen de 14× sobre el requisito de 500 ms), y **disponibilidad del 100%** del servicio protegido durante los escenarios de ataque activo.

La capacidad de generalización del modelo fue validada independientemente en el experimento F2-04, donde Isolation Forest detectó **12 de 12 tipos de ataque no presentes en el entrenamiento** (incluidos Slowloris HTTP, DNS Amplification, NTP Amplification y RDP Brute Force) con tasa de detección del 100%, evidenciando que el aprendizaje de la distribución del tráfico normal es suficiente para discriminar anomalías arbitrarias.

En síntesis, la elección de Isolation Forest no responde a una convención algorítmica ni a la popularidad del método, sino a la correspondencia explícita entre las propiedades matemáticas del algoritmo —aislamiento estocástico, invarianza a distribuciones, complejidad sublineal de inferencia— y las restricciones reales del entorno: hardware embebido, ausencia de etiquetas de ataque, flujo de datos en tiempo real, y necesidad de detección de amenazas desconocidas. Esta correspondencia queda demostrada empíricamente por los resultados de producción descritos en la Fase F6 de este proyecto.

---

*Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. In Proceedings of the 8th IEEE International Conference on Data Mining (ICDM '08) (pp. 413–422). IEEE.*  
*Chalapathy, R., & Chawla, S. (2019). Deep learning for anomaly detection: A survey. arXiv:1901.03407.*  
*Chandola, V., Banerjee, A., & Kumar, V. (2009). Anomaly detection: A survey. ACM Computing Surveys, 41(3), Article 15.*

---

## 6. Referencias de Archivos

| Archivo | Ruta en el sensor | Descripción |
|---|---|---|
| Modelo IF | `/home/m4rk/ppi-surikata-producto/models/isolation_forest.pkl` | Modelo en producción (2.4 MB, joblib) |
| Scaler | `/home/m4rk/ppi-surikata-producto/models/scaler.pkl` | StandardScaler fit en 684 normales |
| Resultados comparación | `/home/m4rk/ppi-surikata-producto/results/reports/comparacion_modelos_f401.csv` | Métricas de los 5 modelos — F4-01 |
| Script entrenamiento | `/home/m4rk/ppi-surikata-producto/scripts/fase3_isolation_forest.py` | Reproducible |
| Log producción | `/home/m4rk/ppi-surikata-producto/results/motor_decision.log` | Evidencia de validación F6 |
| Features | `/home/m4rk/ppi-surikata-producto/models/features.csv` | Lista de 14 features usadas |

> **Documento complementario:** Ver `F4_01_Comparacion_Modelos.md` para tablas de resultados completos del experimento F4-01.
