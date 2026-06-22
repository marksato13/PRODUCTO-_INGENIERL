# F2 — Detección de Anomalías (Isolation Forest)
**Estado: ✅ COMPLETA Y VALIDADA**  
**Resultado:** AUC-ROC=0.8998 | Precision=99.54% | Recall=99.40% | τ1=−0.4459 | τ2=−0.6027

---

## Objetivo

Entrenar un modelo no supervisado que aprenda el comportamiento normal de la red a partir de los datos de F1, y derive umbrales estadísticos de decisión (τ1, τ2) que separen tráfico normal, sospechoso y anómalo con base en una curva ROC validada.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Isolation Forest (IF)** | Algoritmo de detección de anomalías. Construye árboles de decisión aleatorios y mide cuántos pasos necesita para aislar un punto. Puntos fáciles de aislar (pocos pasos) = anómalos. Puntos difíciles de aislar (muchos pasos) = normales. |
| **decision_function** | Función del IF que devuelve el score de anomalía. Valores cercanos a 0 = muy normal. Valores muy negativos (−1) = muy anómalo. En producción: score > τ1 → PERMIT. |
| **contamination** | Parámetro del IF que indica la fracción estimada de anomalías en los datos de entrenamiento. Se usa para calibrar el offset interno del modelo. Valor usado: 0.05 (5%). |
| **n_estimators** | Número de árboles en el IF. Más árboles = estimación más estable pero más lento. Valor usado: 300 árboles. |
| **StandardScaler** | Normalización de features: resta la media y divide por la desviación estándar de cada feature. Necesario porque el IF es sensible a la escala. Ajustado SOLO en el 80% de entrenamiento. |
| **Split 80/20 aleatorio** | División del dataset: 80% para entrenar el modelo (53,708 flujos) y 20% reservado como holdout (13,427 flujos) para evaluación posterior. `shuffle=True` porque el IF aprende distribución, no secuencia temporal. |
| **Holdout** | Conjunto de datos completamente separado del entrenamiento. El IF nunca lo ve. Se usa en `fase3_evaluar.py` para medir FPR real (cuántos flujos normales el modelo clasificaría mal). |
| **Curva ROC** | Receiver Operating Characteristic. Grafica TPR (eje Y) vs FPR (eje X) al variar el umbral de decisión. Una curva ideal va por la esquina superior izquierda (TPR=1, FPR=0). |
| **AUC-ROC** | Área Bajo la Curva ROC. Valor entre 0 y 1. AUC=0.5 es un clasificador aleatorio; AUC=1.0 es perfecto. AUC=0.8998 indica buena discriminación entre normal y anómalo. |
| **TPR (Recall)** | True Positive Rate = TP/(TP+FN). De todos los ataques reales, ¿cuántos detecta el modelo? En τ1: TPR=99.40%. |
| **FPR** | False Positive Rate = FP/(FP+TN). De todo el tráfico normal, ¿cuánto clasifica erróneamente como anómalo? En τ1: FPR=20.47% (mitigado por whitelist). |
| **τ1 (tau1)** | Umbral superior de decisión. score > τ1 → PERMIT. Elegido por el **índice de Youden** (punto donde TPR−FPR es máximo). Valor: −0.4459. |
| **τ2 (tau2)** | Umbral inferior de decisión. score ≤ τ2 → BLOCK. Elegido como el punto donde FPR ≤ 2%. Valor: −0.6027. |
| **Índice de Youden** | J = TPR − FPR. El umbral τ1 que maximiza J es el que mejor equilibra sensibilidad y especificidad. Es el criterio estadístico estándar para elegir el umbral operativo. |
| **One-class classification** | El IF aprende SOLO de datos normales (no necesita etiquetas de ataque). Es ideal cuando los ataques son desconocidos o raros. Cualquier desviación del patrón normal es anomalía. |

---

## ¿Por qué Isolation Forest y no otro modelo?

| Criterio | Isolation Forest | SVM one-class | Autoencoder |
|---|---|---|---|
| Requiere etiquetas de ataque | ❌ No | ❌ No | ❌ No |
| Escala a 600K+ flujos | ✅ Sí (O(n·log n)) | ⚠️ Difícil | ✅ Sí |
| Salida continua (score) | ✅ Sí | ⚠️ Limitada | ✅ Sí |
| Sensible a escala de features | ⚠️ Con scaler | ✅ Sí | ✅ Sí |
| Interpretable | ⚠️ Parcial | ❌ No | ❌ No |
| Latencia inferencia | ✅ <1ms | ✅ <1ms | ⚠️ >5ms |

> Se comparó con Autoencoder (AE) — resultados en `results/ae/`. El IF superó al AE en AUC por escenario y latencia de inferencia.

---

## Features del modelo (14)

Estas 14 features se extraen de cada flujo `event_type=flow` de eve.json:

| Feature | Cómo se calcula | Qué captura |
|---|---|---|
| `pkts_toserver` | `flow.pkts_toserver` | Paquetes enviados al servidor |
| `pkts_toclient` | `flow.pkts_toclient` | Paquetes recibidos del servidor (respuesta) |
| `bytes_toserver` | `flow.bytes_toserver` | Bytes enviados |
| `bytes_toclient` | `flow.bytes_toclient` | Bytes recibidos |
| `duration` | `flow.age` (segundos) | Duración del flujo |
| `pkt_rate` | (pkts_to + pkts_from) / duration | Velocidad de paquetes |
| `byte_rate` | (bytes_to + bytes_from) / duration | Throughput |
| `pkt_ratio` | pkts_toserver / (pkts_toclient + 1) | Asimetría de paquetes |
| `byte_ratio` | bytes_toserver / (bytes_toclient + 1) | Asimetría de bytes |
| `avg_pkt_size` | (bytes_to + bytes_from) / (pkts_to + pkts_from + 1) | Tamaño medio de paquete |
| `is_tcp` | proto == "TCP" → 1 | Protocolo TCP |
| `is_udp` | proto == "UDP" → 1 | Protocolo UDP |
| `is_icmp` | proto == "ICMP" → 1 | Protocolo ICMP |
| `dest_port` | `dest_port` | Puerto destino |

> Un SYN flood tiene: `pkts_toclient=0` (no hay respuesta), `pkt_rate=10,000+`, `byte_ratio≈0`. Eso lo hace fácil de aislar para el IF.

---

## Pipeline de ejecución

### Paso 1 — Entrenamiento (`fase3_entrenar.py`)

```
data/raw/*_normal_*.gz (Grupo A)
    │
    ▼ parse_flows() — filtro src_ip ∈ {192.168.0.20, 192.168.0.120}
    │   (Desktop Y Servidor — ambos son fuentes de tráfico normal)
    │
    ▼ extract_features() — 14 features por flujo
    │
    ▼ train_test_split(test_size=0.20, shuffle=True, random_state=42)
    │   ├── 80% → 53,708 flujos → ENTRENAMIENTO
    │   └── 20% → 13,427 flujos → data/normal_holdout.csv
    │
    ▼ StandardScaler.fit_transform(X_train)
    │   → ajusta μ/σ de cada feature sobre el 80%
    │
    ▼ IsolationForest(n_estimators=300, contamination=0.05).fit(X_train_scaled)
    │
    ▼ Guardar: isolation_forest.pkl | scaler.pkl | features.csv
```

```bash
# Ejecutar entrenamiento:
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 scripts/fase3_entrenar.py
```

### Paso 2 — Evaluación y umbrales (`fase3_evaluar.py`)

```
normal_holdout.csv (13,427 flujos — nunca vistos)   +   data/raw/*_anom_*.gz
    │                                                        │
    ▼ scaler.transform()                                     ▼ scaler.transform()
    │                                                        │
    ▼ IF.decision_function() → scores_normal               ▼ IF.decision_function() → scores_anom
    │
    ▼ Construir curva ROC:
    │   X = scores_normal + scores_anom
    │   y = [0]*13,427 + [1]*598,285
    │   roc_curve(y, scores) → TPR[], FPR[], thresholds[]
    │
    ▼ Derivar τ1: max(TPR - FPR)  →  Índice de Youden  →  τ1 = −0.4459
    ▼ Derivar τ2: primer umbral donde FPR ≤ 0.02       →  τ2 = −0.6027
    │
    ▼ Guardar: results/metricas_offline.txt | results/auc_roc.png
```

```bash
python3 scripts/fase3_evaluar.py
```

---

## Datos reales del entrenamiento

```
n_train_normal  : 53,708  flujos normales (80% split)
n_holdout_normal: 13,427  flujos normales (20% holdout, evaluación)
n_anom_eval     : 598,285 flujos anómalos (todos los escenarios B)
sklearn versión : 1.9.0   (igual en entrenamiento y producción — sin mismatch)
```

---

## Umbrales derivados de la curva ROC

| Umbral | Valor | Zona → Acción | Criterio de elección |
|---|---|---|---|
| **τ1** | **−0.4459** | score > τ1 → **PERMIT** | Índice de Youden: TPR=99.40%, FPR=20.47% |
| **τ2** | **−0.6027** | τ2 < score ≤ τ1 → **LIMIT** | Primer punto donde FPR ≤ 2%: TPR=18.27% |
| — | — | score ≤ τ2 → **BLOCK** | Zona de alta anomalía |

> **¿Por qué FPR=20.47% es aceptable en τ1?**
> Bajar el FPR a 5% requeriría un τ1≈−0.49. Pero los SYN floods tienen score≈−0.49 a −0.51 → escaparían. El FPR del 20% se acepta porque la whitelist protege las IPs legítimas del laboratorio. El FPR operativo real es **0%**.

---

## Métricas validadas

| Métrica | Valor | Significado |
|---|---|---|
| **AUC-ROC** | **0.8998** | La curva ROC cubre el 90% del área ideal |
| **Precision** | **99.54%** | De lo que clasifica como anómalo, el 99.54% realmente lo es |
| **Recall (TPR)** | **99.40%** | Detecta el 99.40% de los ataques reales |
| **F1-score** | **0.9947** | Media armónica Precision×Recall |
| FP en τ1 | 2,748 | Flujos normales marcados como sospechosos |
| FN en τ1 | 3,560 | Ataques que pasaron sin detectar (de 598,285) |
| Score medio normal | −0.3965 ± 0.0753 | Rango característico del tráfico normal |
| Score medio anómalo | −0.5420 ± 0.0900 | Rango característico del tráfico atacante |
| Separación (Δ) | **0.1454** | Diferencia entre medias — brecha discriminante |

---

## Archivos de salida (entrada de F3)

```
models/
├── isolation_forest.pkl   ← modelo IF serializado (joblib)
├── scaler.pkl             ← StandardScaler (μ/σ del 80% de entrenamiento)
└── features.csv           ← 14 features en orden exacto (crítico para el motor)

data/
└── normal_holdout.csv     ← 13,427 flujos normales reservados

results/
├── metricas_offline.txt   ← τ1, τ2, AUC, TPR, FPR, Precision, Recall, F1
└── auc_roc.png            ← curva ROC con τ1/τ2 marcados (300 DPI)
```

> `metricas_offline.txt` es leído por el motor (`motor_decision.py`) en cada arranque para cargar τ1 y τ2. Es la única fuente de verdad de los umbrales.

---

## Imágenes de referencia

| Imagen | Ruta |
|---|---|
| Curva ROC con τ1/τ2 | `docs/ppi_documentacion2/imagenes/F2_modelo_IF/f2_auc_roc_curva.png` |
| Distribución scores normal vs anómalo | `docs/ppi_documentacion2/imagenes/F2_modelo_IF/f2_distribucion_scores.png` |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado |
|---|---|---|
| CA-1 | AUC-ROC ≥ 0.85 | ✅ **0.8998** |
| CA-2 | TPR@τ1 ≥ 95% | ✅ **99.40%** |
| CA-3 | FPR@τ1 ≤ 25% | ✅ **20.47%** |
| CA-4 | Precision@τ1 ≥ 95% | ✅ **99.54%** |
| CA-F2-05 | τ1/τ2 derivados con criterio estadístico | ✅ Youden + FPR≤2% |
| CA-F2-06 | Sin mismatch sklearn entre entrenamiento y motor | ✅ 1.9.0 en ambos |
| CA-F2-07 | `metricas_offline.txt` leído correctamente al arrancar | ✅ Verificado F3 |

---

## Argumento de defensa

> "Elegimos Isolation Forest por dos razones fundamentales: primero, no requiere ejemplos de ataques para entrenarse — aprende únicamente del tráfico normal, lo que lo hace robusto frente a ataques zero-day. Segundo, su salida continua (score) nos permite definir tres zonas de riesgo con criterio estadístico formal: τ1 por índice de Youden maximizando la separación TPR−FPR, y τ2 fijando el FPR al 2%. El AUC de 0.8998 no es perfecto por diseño — hay solapamiento natural entre tráfico normal agresivo y ataques leves, y eso está documentado. Lo importante es que el 99.4% de los ataques reales capturados en el laboratorio fueron detectados."
