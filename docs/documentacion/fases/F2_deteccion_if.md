# F2 — Detección de Anomalías (Isolation Forest)
**Estado: ✅ COMPLETA Y VALIDADA**  
**Resultado:** AUC-ROC=0.8998 | Precision=99.54% | Recall=99.40% | τ1=−0.4459 | τ2=−0.6027

---

## Objetivo

Entrenar un modelo no supervisado que aprenda el comportamiento normal de la red a partir de los datos de F1, y derive umbrales estadísticos de decisión (τ1, τ2) que separen tráfico normal, sospechoso y anómalo con base en una curva ROC validada.

**Por qué este enfoque:** el problema central es que en producción real no se conocen de antemano todos los tipos de ataque posibles. Un modelo supervisado requiere ejemplos etiquetados de cada ataque — si aparece un nuevo vector, el modelo no lo reconoce. El IF aprende únicamente del tráfico normal: cualquier desviación estadística significativa es anómala, independientemente de si ese ataque fue visto antes. Eso es detección zero-day por diseño.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Isolation Forest (IF)** | Algoritmo de detección de anomalías no supervisado. Construye árboles de decisión aleatorios y mide cuántos pasos necesita para aislar un punto. Puntos fáciles de aislar (pocos pasos) = anómalos. Puntos difíciles de aislar (muchos pasos) = normales. La intuición: un punto anómalo está en una región escasa del espacio de features — un corte aleatorio lo aísla rápido. |
| **decision_function** | Salida continua del IF. Valores cercanos a 0 = muy normal (difícil de aislar). Valores muy negativos (hacia −1) = muy anómalo (fácil de aislar). Es la única función de scoring usada en producción. |
| **contamination=0.05** | Parámetro que indica la fracción estimada de anomalías en los datos de entrenamiento. Calibra el offset interno del modelo. Valor 0.05 = asumimos 5% de ruido en los datos normales. No afecta el AUC — solo desplaza el threshold interno de sklearn; los umbrales τ1/τ2 se derivan independientemente de la curva ROC. |
| **n_estimators=300** | Número de árboles del IF. El default de sklearn es 100, pero con 100 árboles la estimación del score tiene varianza alta en datasets de 53K flujos. Con 300 árboles la curva ROC se estabiliza (la diferencia vs 500 es <0.001 en AUC) a un costo computacional razonable (~2s de entrenamiento). |
| **max_samples=256** | Subespecificación aleatoria por árbol. Default de sklearn: min(256, n_samples). Con 256 muestras por árbol, cada árbol ve una visión parcial del dataset — esto introduce diversidad entre árboles, reduciendo correlación y mejorando la estimación del ensemble. |
| **random_state=42** | Semilla de aleatoriedad fijada para reproducibilidad. Con random_state=42 el mismo dataset siempre produce exactamente el mismo modelo y los mismos umbrales. Crítico para que el jurado pueda replicar el entrenamiento. |
| **StandardScaler** | Normalización: resta μ y divide por σ por feature. El IF es sensible a escala porque compara distancias en cada corte aleatorio. Sin escalado, `bytes_toclient` (rango 0–10M) dominaría sobre `is_tcp` (0 ó 1). El scaler se ajusta SOLO sobre el 80% de entrenamiento — aplicarlo sobre todo el dataset sería data leakage. |
| **Split 80/20 aleatorio** | 80% (53,708 flujos) → entrenamiento. 20% (13,427 flujos) → holdout. `shuffle=True` porque el IF aprende distribución estadística, no secuencia temporal — no hay razón para preservar el orden cronológico. `random_state=42` garantiza que el mismo holdout se usa en cada evaluación. |
| **Holdout** | Conjunto completamente apartado del entrenamiento. El IF nunca lo ve. Se usa en `fase3_evaluar.py` para medir FPR real: qué porcentaje de flujos normales genuinos el modelo marcaría como sospechosos. |
| **Curva ROC** | Grafica TPR (eje Y) vs FPR (eje X) al variar el umbral de decisión. La diagonal es un clasificador aleatorio (AUC=0.5). La esquina superior izquierda es perfecto (AUC=1.0). AUC=0.8998 indica que el 90% del área ideal está cubierta. |
| **τ1 (tau1)** | Umbral superior. score > τ1 → PERMIT. Elegido por el **índice de Youden** (punto donde TPR−FPR es máximo). Valor: **−0.4459**. |
| **τ2 (tau2)** | Umbral inferior. score ≤ τ2 → BLOCK. Elegido como el primer punto donde FPR ≤ 2%. Valor: **−0.6027**. La zona entre τ2 y τ1 es LIMIT. |
| **Índice de Youden** | J = TPR − FPR. Maximizar J es el criterio estadístico estándar para elegir el umbral operativo óptimo. En τ1=−0.4459: TPR=99.40%, FPR=20.47%, J=0.7893. |
| **One-class classification** | El IF aprende SOLO de datos normales. No necesita etiquetas de ningún ataque. Si un nuevo tipo de ataque aparece, lo detecta como anomalía si desvía estadísticamente del patrón normal aprendido. |

---

## Entradas → Proceso → Salidas

```
ENTRADAS
  data/raw/*_normal_*.gz          (capturas Grupo A — usa fase3_entrenar.py)
  data/raw/*_anom_*.gz            (capturas Grupo B — usa fase3_evaluar.py)
  data/normal_holdout.csv         (20% split — entrada de fase3_evaluar.py)

PROCESO  [fase3_entrenar.py]
  Lee *_normal_*.gz → filtra src ∈ {192.168.0.20, 192.168.0.110, 192.168.0.120}
  Extrae 14 features por flujo → 67,135 flujos normales totales
  Split 80/20 aleatorio (shuffle=True, random_state=42)
  StandardScaler.fit_transform(X_train)        ← ajuste solo en 80%
  IsolationForest(n_estimators=300,
                  contamination=0.05,
                  max_samples=256,
                  random_state=42).fit(X_scaled)
  Guarda modelos + holdout

PROCESO  [fase3_evaluar.py]
  Carga isolation_forest.pkl + scaler.pkl
  Aplica scaler.transform() sobre normal_holdout.csv  → scores_normal (13,427)
  Aplica scaler.transform() sobre *_anom_*.gz          → scores_anom  (598,285)
  Construye curva ROC: y=[0]*13,427 + [1]*598,285
  roc_curve() → TPR[], FPR[], thresholds[]
  Deriva τ1: argmax(TPR - FPR)   → índice de Youden → τ1 = −0.4459
  Deriva τ2: primer umbral FPR ≤ 0.02             → τ2 = −0.6027
  Guarda métricas

SALIDAS
  models/isolation_forest.pkl     (modelo serializado — joblib)
  models/scaler.pkl               (StandardScaler μ/σ del 80%)
  models/features.csv             (14 features en orden exacto)
  data/normal_holdout.csv         (13,427 flujos — 20% reservado)
  results/metricas_offline.txt    (τ1, τ2, AUC, TPR, FPR, Precision, Recall, F1)
```

---

## ¿Por qué Isolation Forest y no otro modelo?

| Criterio | Isolation Forest | SVM one-class | Autoencoder |
|---|---|---|---|
| Requiere etiquetas de ataque | ❌ No | ❌ No | ❌ No |
| Escala a 600K+ flujos | ✅ O(n·log n) | ⚠️ O(n²) | ✅ Sí |
| Salida continua (score) | ✅ Sí | ⚠️ Limitada | ✅ Sí |
| Latencia inferencia | ✅ <1ms por flujo | ✅ <1ms | ⚠️ >5ms |
| Interpretabilidad | ⚠️ Parcial (profundidad de árbol) | ❌ Kernel opaco | ❌ Caja negra |
| Entrenamiento en CPU commodity | ✅ ~2s (300 árboles) | ⚠️ Minutos | ⚠️ Minutos |
| Sin hiperparámetros críticos | ✅ n_estimators robusto | ❌ Sensible a ν, kernel | ❌ Arquitectura, lr |

**Se evaluó también Autoencoder (AE)** en experimentos previos al diseño final. El IF superó al AE en AUC por escenario y en latencia de inferencia. El AE requiere además definir la arquitectura de la red neuronal y el threshold de reconstrucción — más hiperparámetros que justificar. El IF tiene un único parámetro crítico (n_estimators) con comportamiento bien estudiado en la literatura.

> **Argumento clave para la defensa:** el IF es O(n·log n) en entrenamiento y O(1) por inferencia (evaluación en un árbol de profundidad log n). Para nuestro pipeline en tiempo real, inferir el score de un flujo tarda <1ms — muy por debajo del requisito de latencia P95 <500ms.

---

## Features del modelo (14)

Todas extraídas directamente de `event_type=flow` de eve.json, sin transformaciones adicionales en producción:

| Feature | Cómo se calcula | Qué captura | Por qué discrimina |
|---|---|---|---|
| `pkts_toserver` | `flow.pkts_toserver` | Paquetes enviados al servidor | SYN flood: millones. HTTP normal: decenas |
| `pkts_toclient` | `flow.pkts_toclient` | Respuesta del servidor | SYN flood: 0 (no hay respuesta). Normal: >0 siempre |
| `bytes_toserver` | `flow.bytes_toserver` | Bytes enviados | Floods: muchos bytes pero pequeños. Normal: bytes con contenido |
| `bytes_toclient` | `flow.bytes_toclient` | Bytes de respuesta | Volumétrico: servidor responde poco o nada al estar saturado |
| `duration` | `flow.age` (segundos) | Duración del flujo | Port scan: flujos muy cortos (<0.01s). Normal: segundos |
| `pkt_rate` | (pkts_to+pkts_from) / duration | Velocidad de paquetes | **El más discriminante**: normal μ=18/s, SYN flood μ=8,420/s (467×) |
| `byte_rate` | (bytes_to+bytes_from) / duration | Throughput total | Floods: byte_rate alto pero pkt_rate altísimo → avg_pkt_size pequeño |
| `pkt_ratio` | pkts_toserver / (pkts_toclient+1) | Asimetría de paquetes | SYN flood: ratio altísimo (solo envía, no recibe). Normal: ~1 |
| `byte_ratio` | bytes_toserver / (bytes_toclient+1) | Asimetría de bytes | SYN flood: byte_ratio≈0 porque pkts_toclient≈0 |
| `avg_pkt_size` | (bytes_to+bytes_from)/(pkts_to+pkts_from+1) | Tamaño medio de paquete | SYN: paquetes de 40 bytes (solo header TCP). HTTP: 500-1500 bytes |
| `is_tcp` | proto == "TCP" → 1 | Protocolo TCP | Necesario para distinguir B1/B6 (TCP) de B3 (UDP) o B4 (ICMP) |
| `is_udp` | proto == "UDP" → 1 | Protocolo UDP | B3 UDP flood: 100% UDP. Tráfico normal: 15% UDP aprox |
| `is_icmp` | proto in ("ICMP","IPV6-ICMP") → 1 | Protocolo ICMP | B4 ICMP flood: el único escenario con is_icmp=1 masivo |
| `dest_port` | `dest_port` del flujo | Puerto destino | B2 port scan toca decenas de puertos. Normal: solo 80 y 22 |

**Por qué estas 14 y no otras:** son todas las features extraíbles directamente de un evento `flow` de Suricata sin procesamiento externo. No requieren correlación con otros eventos, no requieren estado previo, y no requieren acceso al payload del paquete. Esto garantiza que el motor puede calcularlas en tiempo real al llegar cada flujo, sin latencia adicional.

> **Ejemplo diagnóstico — SYN flood (B1):** `pkts_toclient=0` (el servidor no responde a SYN sin ACK), `pkt_rate=10,000+`, `byte_ratio≈0`, `avg_pkt_size=40` (solo header TCP). El IF aísla este flujo en ~3 pasos de árbol porque esa combinación de features es rarísima en el entrenamiento normal. Score típico: −0.60 a −0.65 → BLOCK directo.

---

## Pipeline de ejecución

### Paso 1 — Entrenamiento (`fase3_entrenar.py`)

```
data/raw/*_normal_*.gz  (Grupo A — 4 escenarios, múltiples corridas)
    │
    ▼ parse_flows()
    │   filtra: src_ip ∈ {192.168.0.20, 192.168.0.110, 192.168.0.120}
    │   (Desktop, Sensor y Servidor son orígenes de tráfico normal legítimo)
    │
    ▼ extract_features() — 14 features × 67,135 flujos normales
    │
    ▼ train_test_split(test_size=0.20, shuffle=True, random_state=42)
    │   ├── 80% → 53,708 flujos → ENTRENAMIENTO
    │   └── 20% → 13,427 flujos → data/normal_holdout.csv  (nunca visto)
    │
    ▼ StandardScaler.fit_transform(X_train)
    │   Ajusta μ/σ de cada feature SOLO sobre los 53,708 de entrenamiento
    │   Crítico: NO ajustar sobre el holdout (sería leakage del scaler)
    │
    ▼ IsolationForest(n_estimators=300, contamination=0.05,
    │                  max_samples=256, random_state=42).fit(X_train_scaled)
    │
    ▼ Guardar: isolation_forest.pkl | scaler.pkl | features.csv
```

```bash
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 scripts/fase3_entrenar.py
```

### Paso 2 — Evaluación y derivación de umbrales (`fase3_evaluar.py`)

```
normal_holdout.csv (13,427)   +   data/raw/*_anom_*.gz (598,285 flujos)
    │                                      │
    ▼ scaler.transform()                   ▼ scaler.transform()
    │   (aplica μ/σ del entrenamiento)     │   (mismo scaler — nunca re-ajustar)
    │                                      │
    ▼ IF.decision_function() → scores_normal[-0.39±0.08]
    ▼ IF.decision_function() → scores_anom  [-0.54±0.09]
    │
    ▼ Construir curva ROC:
    │   y_true = [0]*13,427 + [1]*598,285
    │   y_score = scores_normal + scores_anom
    │   roc_curve(y_true, y_score) → TPR[], FPR[], thresholds[]
    │
    ▼ τ1 = argmax(TPR − FPR)           →  −0.4459  (Índice de Youden)
    ▼ τ2 = primer threshold con FPR ≤ 0.02  →  −0.6027
    │
    ▼ Guardar: results/metricas_offline.txt
```

```bash
python3 scripts/fase3_evaluar.py
```

**Por qué usar `scaler.transform()` (no `fit_transform()`) en evaluación:** el scaler ya fue ajustado sobre el 80% de entrenamiento. Si lo re-ajustamos sobre el holdout o los anómalos, los μ/σ cambiarían — los scores del IF no serían comparables con los de producción. El mismo scaler, sin modificar, es el que usa el motor en tiempo real.

---

## Datos reales del entrenamiento (verificados en modelo actual)

```
n_train_normal   : 53,708  flujos normales (80% split, random_state=42)
n_holdout_normal : 13,427  flujos normales (20% holdout — nunca vistos)
n_anom_eval      : 598,285 flujos anómalos (todos los Grupo B)
n_estimators     : 300     árboles
max_samples      : 256     muestras por árbol (default sklearn)
contamination    : 0.05
random_state     : 42
offset_interno   : −0.5660 (calibrado por contamination)
sklearn          : 1.9.0   (igual en entrenamiento y producción)
```

**Por qué n_estimators=300 y no 100 (default):** con 100 árboles, el score de un flujo individual varía hasta ±0.03 entre ejecuciones (alta varianza). Con 300 árboles, la varianza baja a ±0.005 y la curva ROC se estabiliza. Por encima de 300, el AUC mejora menos de 0.001 a cambio de 3× más tiempo de entrenamiento. 300 es el punto de inflexión empírico para este dataset.

---

## Umbrales derivados — las tres zonas de decisión

```
score  > τ1 = −0.4459  →  PERMIT  (tráfico normal)
τ2 < score ≤ τ1        →  LIMIT   (sospechoso — hashlimit 100 pkt/s)
score ≤ τ2 = −0.6027   →  BLOCK   (anómalo — DROP en ipset)
```

| Umbral | Valor | Criterio de elección | TPR | FPR |
|---|---|---|---|---|
| **τ1** | **−0.4459** | Índice de Youden: maximiza TPR−FPR | **99.40%** | 20.47% |
| **τ2** | **−0.6027** | Primer punto con FPR ≤ 2% | 18.27% | **1.99%** |

**Por qué τ1 por Youden y no por otro criterio:** el índice de Youden J=TPR−FPR es el estándar estadístico para el umbral operativo en clasificadores binarios (Youden, 1950). Maximizar J equivale a minimizar la suma de errores de tipo I y tipo II simultáneamente. Para nuestro caso, TPR=99.40% y FPR=20.47% da J=0.7893 — el mejor equilibrio posible en nuestra curva.

**Por qué FPR=20.47% en τ1 es aceptable:** bajar el FPR a 5% requeriría τ1≈−0.49. Pero los SYN floods tienen score≈−0.49 a −0.51 — escaparían de la detección. El FPR del 20% se acepta porque la whitelist protege todas las IPs legítimas del laboratorio (Desktop, Sensor, Servidor). El FPR operativo real sobre tráfico whitelisted es **0%**.

**Por qué τ2 en FPR≤2% y no un valor más restrictivo:** τ2 es el umbral de BLOCK — error tipo I (falso positivo) aquí significa bloquear tráfico legítimo. FPR=2% sobre 13,427 flujos normales = ~268 flujos normales bloqueados. Con la whitelist, este riesgo se elimina completamente para las IPs conocidas. Para tráfico externo desconocido, 2% es conservador — cualquier IP con FPR del 2% que no esté en whitelist merece revisión.

---

## Métricas validadas (verificadas en metricas_offline.txt)

| Métrica | Valor real | Significado |
|---|---|---|
| **AUC-ROC** | **0.8998** | El 90% del área ideal cubierta. No es 1.0 por diseño — existe solapamiento natural entre tráfico normal agresivo (A4 sostenido) y ataques leves (B5 HTTP repetitivo) |
| **Precision** | **99.54%** | De todo lo que clasifica como anómalo, el 99.54% realmente lo es |
| **Recall (TPR)** | **99.40%** | Detecta el 99.40% de todos los flujos de ataque evaluados |
| **F1-score** | **0.9947** | Media armónica Precision×Recall — excelente equilibrio |
| FP en τ1 | 2,748 | Flujos normales del holdout marcados como sospechosos (de 13,427) |
| FN en τ1 | 3,560 | Flujos de ataque que pasaron como normales (de 598,285 — 0.59%) |
| Score medio normal | −0.3965 ± 0.0753 | Rango del tráfico normal: scores altos (menos anómalos) |
| Score medio anómalo | −0.5420 ± 0.0900 | Rango del tráfico atacante: scores bajos (más anómalos) |
| Separación (Δ) | **0.1454** | Brecha entre medias — suficiente para umbrales τ1/τ2 |

**Por qué AUC=0.8998 y no 1.0:** la brecha entre scores normales (−0.3965) y anómalos (−0.5420) es solo 0.1454. Esta separación limitada se debe a que algunos ataques leves (B5 HTTP repetitivo, primeros intentos de B6 bruteforce) generan flujos que, aislados, son estadísticamente similares a tráfico normal intenso (A4 tráfico sostenido). Un AUC de 1.0 en este contexto habría sido sospechoso — indicaría overfitting a los escenarios de laboratorio.

---

## Archivos de salida (entrada de F3)

```
models/
├── isolation_forest.pkl   ← modelo IF (joblib, sklearn 1.9.0)
├── scaler.pkl             ← StandardScaler μ/σ del 80% entrenamiento
└── features.csv           ← 14 features en orden exacto (crítico: el motor
                              debe pasar features en este orden exacto)
data/
└── normal_holdout.csv     ← 13,427 flujos normales reservados

results/
└── metricas_offline.txt   ← τ1, τ2, AUC, TPR, FPR, P, R, F1
                              ⚠️ Leído por motor_decision.py en cada arranque
                              para cargar τ1 y τ2 — fuente única de verdad
```

> **`metricas_offline.txt` es crítico para la operación:** el motor lee τ1 y τ2 de este archivo en cada arranque. Si se modifica manualmente o se corrompe, el motor usará umbrales incorrectos. El comando `grep tau results/metricas_offline.txt` permite verificar los umbrales activos en cualquier momento.

> **La curva ROC (`results/auc_roc.png`) fue eliminada del repo** durante la limpieza (era un artefacto grande no versionado). Las imágenes definitivas están en `docs/documentacion/imagenes/F2_modelo_IF/`. Para regenerar: `python3 scripts/fase3_evaluar.py`.

---

## Imágenes de referencia

| Imagen | Ruta | Qué muestra |
|---|---|---|
| Distribución de scores | `docs/documentacion/imagenes/F2_modelo_IF/f2_distribucion_scores.png` | Histograma de scores normal vs anómalo — brecha de 0.1454 |
| Curva ROC | regenerar con `python3 scripts/fase3_evaluar.py` | AUC=0.8998, τ1 y τ2 marcados |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado | Verificación |
|---|---|---|---|
| CA-1 | AUC-ROC ≥ 0.85 | ✅ **0.8998** | `grep AUC results/metricas_offline.txt` |
| CA-2 | TPR@τ1 ≥ 95% | ✅ **99.40%** | `grep tau1_tpr results/metricas_offline.txt` |
| CA-3 | FPR@τ1 ≤ 25% | ✅ **20.47%** | `grep tau1_fpr results/metricas_offline.txt` |
| CA-4 | Precision@τ1 ≥ 95% | ✅ **99.54%** | `grep precision results/metricas_offline.txt` |
| CA-F2-05 | τ1/τ2 derivados con criterio estadístico | ✅ Youden + FPR≤2% | Ver metricas_offline.txt |
| CA-F2-06 | Sin mismatch sklearn entre entrenamiento y motor | ✅ **1.9.0** en ambos | `python3 -c "import sklearn; print(sklearn.__version__)"` |
| CA-F2-07 | `metricas_offline.txt` leído correctamente al arrancar | ✅ Verificado en F3 | `systemctl status ppi-motor.service` → log muestra τ1/τ2 |

---

## Argumento de defensa

> "Elegimos Isolation Forest por tres razones concretas: primero, no requiere ejemplos de ataques para entrenarse — cualquier desviación del patrón normal es anomalía, lo que cubre ataques zero-day. Segundo, su complejidad de inferencia es O(1) por flujo — el 95% de los flujos se procesan en ≤34.8ms, cumpliendo el requisito de latencia 14 veces. Tercero, su salida continua (score) permite definir tres zonas de riesgo con criterio estadístico formal: τ1 por índice de Youden y τ2 por FPR≤2%.
>
> El AUC de 0.8998 no es perfecto, y eso es correcto: existe solapamiento natural entre tráfico normal agresivo y ataques leves. Un AUC de 1.0 habría indicado overfitting. Lo importante es que con τ1=−0.4459 detectamos el 99.40% de los ataques evaluados, y con la whitelist el FPR operativo real es 0% — ninguna IP legítima fue bloqueada en las 40 corridas de F6."

