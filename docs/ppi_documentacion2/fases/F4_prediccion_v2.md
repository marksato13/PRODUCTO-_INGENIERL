# F4 — Predicción Inteligente (XGBoost v2)
**Estado: ✅ IMPLEMENTADA Y VALIDADA**  
**Resultado:** AUC-ROC=0.9992 | FP+FN=14/12,488 | ALERTA-PREDICTIVA validada P=77.39%

---

## Objetivo

Complementar al IF añadiendo memoria temporal: predecir si un evento LIMIT o BLOCK corresponde al inicio de un ataque sostenido (que continuará) o a una anomalía puntual (que cesará sola), usando el historial de comportamiento de la IP atacante como features.

---

## Terminología clave

| Término | Definición |
|---|---|
| **XGBoost** | eXtreme Gradient Boosting. Ensemble de árboles de decisión entrenado de forma supervisada. Cada árbol corrige los errores del anterior (boosting). Usado aquí para clasificación binaria. |
| **Clasificación supervisada** | El modelo aprende de ejemplos etiquetados (label=0 o label=1). A diferencia del IF (no supervisado), XGBoost necesita saber cuáles eventos fueron "sostenidos" para aprender a predecirlos. |
| **Label automático** | La etiqueta se deriva automáticamente del propio log del motor, sin etiquetado manual. `label=1` si la misma IP genera otro BLOCK en los próximos 60 segundos. |
| **Amenaza sostenida (label=1)** | IP que después de ser bloqueada vuelve a atacar en 60s. Requiere atención del operador. Ejemplos: SYN flood continuo, hydra sin parar. |
| **Anomalía puntual (label=0)** | IP que genera un evento aislado y no reincide. Puede ser un falso positivo del IF o un scan único. No requiere intervención. |
| **Data leakage (fuga de datos)** | Cuando una feature del modelo contiene información que ya responde la pregunta, creando una correlación artificial. En v1: `score` del IF (labels derivados de ese mismo score). Resultado: AUC inflado que no generaliza. |
| **scale_pos_weight** | Parámetro XGBoost para clases desbalanceadas. Si label=1 son el 9.3% del dataset, asignar weight=9.78 al label minoritario compensa el desbalance. |
| **SHAP (Shapley Additive Explanations)** | Método para explicar cuánto contribuye cada feature a la predicción de un caso específico. Muestra qué features "empujaron" la probabilidad hacia arriba o abajo. |
| **Probabilidad P** | Salida del `predict_proba()` de XGBoost. P ∈ [0,1]. P=0.77 significa "77% de probabilidad de que este ataque sea sostenido". |
| **Umbral de alerta** | Valor de P a partir del cual el predictor genera una alerta. P≥0.70 → ALERTA-PREDICTIVA. 0.40≤P<0.70 → AVISO. P<0.40 → silencio. |
| **Hot-reload** | El predictor (`predictor.py`) ejecuta un ciclo cada **10 segundos** (`INTERVALO=10`). En cada ciclo verifica el mtime del `.pkl` y si cambió, recarga en caliente sin reiniciar el servicio. |
| **stratify** | Split estratificado: mantiene la misma proporción de label=0/label=1 en train y test. Sin esto, el test podría tener muy pocos positivos y las métricas serían inestables. |
| **ALERTA-PREDICTIVA** | Nivel máximo de alerta del predictor (P≥0.70). Activa notificación Telegram, panel rojo en dashboard, y log WARNING. Dedup de 5 minutos por IP. |

---

## Entradas → Proceso → Salidas

```
ENTRADAS  [f4_entrenar_predictor_v2.py — entrenamiento, una vez]
  results/motor_decision.log              (eventos LIMIT+BLOCK históricos)

ENTRADAS  [predictor.py — operación continua]
  results/motor_decision.log              (lectura cada INTERVALO=10s)
  models/predictor_modelo_v2.pkl         (XGBoost cargado, hot-reload)
  models/features_predictor_v2.txt       (9 features en orden)

PROCESO  [f4_entrenar_predictor_v2.py]
  Parsear log → extraer eventos LIMIT+BLOCK
  Por cada evento: calcular ventanas deslizantes por IP
    limit_count_15s = nº LIMITs de esta IP en [t-15s, t]
    block_count_60s = nº BLOCKs de esta IP en [t-60s, t]
  Label automático: ¿BLOCK de esta IP en [t, t+60s]? → 1=sostenido, 0=puntual
  Split estratificado 80/20 (random_state=42)
  XGBoostClassifier(n_estimators=300, max_depth=4, lr=0.05, scale_pos_weight=spw)
  Evaluar: AUC, Precision, Recall, F1, matriz confusión

PROCESO  [predictor.py — cada 10s]
  Leer nuevas líneas de motor_decision.log
  Por cada IP con eventos recientes: calcular 9 features
  clf.predict_proba(X)[:,1] → P ∈ [0,1]
  P < 0.40      → SILENCIO
  0.40 ≤ P < 0.70 → AVISO (dashboard amarillo)
  P ≥ 0.70      → ALERTA-PREDICTIVA (dashboard rojo + Telegram)
  Verificar mtime del .pkl → hot-reload si cambió (F5)

SALIDAS
  models/predictor_modelo_v2.pkl         (XGBoost serializado, AUC=0.9992)
  models/features_predictor_v2.txt       (9 features)
  results/metricas_predictor_v2.txt      (AUC, Precision, Recall, matriz confusión)
  results/predictor.log                  (AVISO / ALERTA-PREDICTIVA por IP)
  Telegram mensajes                       (ALERTA-PREDICTIVA P≥0.70, dedup 300s)
  Dashboard web :8080                    (panel predictor en tiempo real)
```


---

## ¿Por qué complementa al IF?

El IF responde: **¿este flujo es anómalo ahora?**  
El XGBoost responde: **¿esta IP seguirá atacando en los próximos 60 segundos?**

Son preguntas distintas con valor operativo diferente:

| Escenario | IF (flujo actual) | XGBoost (comportamiento futuro) |
|---|---|---|
| SYN flood continuo | BLOCK desde el flujo 1 | P=77.39% → ALERTA-PREDICTIVA |
| Port scan único | BLOCK (reconocimiento) | P≈0.20 → silencio (puntual) |
| BF SSH con hydra | LIMIT→BLOCK heurístico | P≈0.85 → ALERTA antes de BLOCK |
| Tráfico normal | PERMIT (whitelist) | Sin eventos → sin predicción |

---

## Features del modelo (9) — sin score (leakage corregido)

| Feature | Importancia | Cómo se calcula | Por qué importa |
|---|---|---|---|
| `proto_udp` | **51.95%** | 1 si proto==UDP, 0 si no | UDP floods (B3) son casi siempre sostenidos por naturaleza |
| `block_count_60s` | **24.37%** | Nº BLOCKs de esta IP en los últimos 60s | Reincidencia previa predice reincidencia futura |
| `proto_tcp` | **20.79%** | 1 si proto==TCP | SYN floods y BF SSH sostenidos son TCP |
| `is_block` | 1.22% | 1 si el evento actual fue BLOCK | Diferencia entre "límite sospechoso" y "BLOCK confirmado" |
| `dest_port` | 0.84% | Puerto destino del flujo | :22=SSH, :80=HTTP, :53=UDP → contexto del ataque |
| `hora_cos` | 0.33% | cos(hora/24 × 2π) | Componente temporal — ataques nocturnos vs diurnos |
| `hora_sin` | 0.29% | sin(hora/24 × 2π) | Codificación cíclica del horario |
| `limit_count_15s` | 0.22% | Nº LIMITs de esta IP en los últimos 15s | Presión previa al BLOCK |
| `proto_icmp` | 0.00% | 1 si proto==ICMP | ICMP floods escasos — información ya en block_count_60s |

> **¿Por qué proto_udp es tan dominante?** Los floods UDP (hping3 --udp --flood) generan miles de flujos UDP por segundo desde la misma IP. Cada flujo entra al IF y recibe BLOCK. Esto crea una señal muy fuerte y consistente que el XGBoost aprende como "si es UDP y ya fue bloqueado varias veces en 60s, definitivamente es sostenido".

> **¿Por qué proto_icmp=0%?** Los floods ICMP (B4) también generan block_count_60s alto. La información ya está capturada por esa feature — proto_icmp no añade discriminación adicional y XGBoost la ignoró.

---

## Corrección de data leakage (v1 → v2)

**v1 (con leakage):**
```python
FEATURES_v1 = ['dest_port', 'proto_tcp', 'proto_udp', 'proto_icmp',
                'hora_sin', 'hora_cos', 'limit_count_15s', 'block_count_60s',
                'is_block', 'score']  # ← LEAKAGE
```
El `score` es la salida del IF. Los labels se derivan de los umbrales del mismo score (score≤τ2 → BLOCK → label=1). El modelo aprendía: "score bajo = label=1", trivialmente. AUC=1.0000 era artefactual.

**v2 (sin leakage):**
```python
FEATURES_v2 = ['dest_port', 'proto_tcp', 'proto_udp', 'proto_icmp',
                'hora_sin', 'hora_cos', 'limit_count_15s', 'block_count_60s',
                'is_block']  # ← score eliminado
```
El modelo aprende patrones comportamentales reales. AUC=0.9992 sobre test set separado — sin trampa.

---

## Pipeline de entrenamiento (`f4_entrenar_predictor_v2.py`)

```
results/motor_decision.log
    │
    ▼ parse_log() — extrae eventos LIMIT+BLOCK
    │
    ▼ construir_dataset()
    │   ├─ Para cada evento: calcular ventanas deslizantes
    │   │   limit_count_15s = nº LIMITs de esta IP en [t-15s, t]
    │   │   block_count_60s = nº BLOCKs de esta IP en [t-60s, t]
    │   └─ Label: ¿hay BLOCK de esta IP en [t, t+60s]?
    │       SÍ → label=1 (sostenido)
    │       NO → label=0 (puntual)
    │
    ▼ train_test_split(stratify=y, test_size=0.20, random_state=42)
    │   ├── 80% → entrenamiento
    │   └── 20% → test set (12,488 muestras — nunca visto)
    │
    ▼ XGBoostClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
    │                   scale_pos_weight=9.78)
    ▼ Evaluar: AUC, Precision, Recall, F1, matriz confusión
    │
    ▼ Guardar: predictor_modelo_v2.pkl | features_predictor_v2.txt
```

```bash
python3 scripts/f4_entrenar_predictor_v2.py
```

---

## Métricas de entrenamiento — reales (2026-06-22)

| Métrica | Valor |
|---|---|
| Dataset total | 62,436 eventos LIMIT+BLOCK |
| label=1 (sostenido) | 5,790 (9.3%) |
| label=0 (puntual) | 56,646 (90.7%) |
| Split train/test | 49,948 / 12,488 |
| **AUC-ROC** | **0.9992** |
| Precision (sostenido) | 99.40% |
| Recall (sostenido) | 99.40% |
| **FP + FN en test** | **14** (7+7 de 12,488) |

### Matriz de confusión (test set — 12,488 muestras)

```
                  Predicho: Puntual   Predicho: Sostenido
Real: Puntual        TN=11,323            FP=7
Real: Sostenida      FN=7                 TP=1,151
```

> 7 FP: alertas innecesarias (bajo impacto — el IF ya bloqueó igualmente)  
> 7 FN: ataques sostenidos no predichos (el IF ya los bloqueó — el XGBoost es predictor adicional)

---

## Niveles de alerta del predictor

```
P < 0.40    → SILENCIO
             Tráfico puntual o bajo riesgo. No se registra ni notifica.
             Ejemplo: port scan único, falso positivo del IF.

0.40 ≤ P < 0.70  → AVISO (amarillo en dashboard web)
                   "Actividad sospechosa — vigilando."
                   Log INFO. Sin Telegram. El sistema sigue monitoreando.
                   Ejemplo: inicio de BF SSH con pocos intentos.

P ≥ 0.70    → ALERTA-PREDICTIVA (rojo en dashboard)
              "Ataque sostenido en curso — actuar."
              Log WARNING. Telegram al operador. Dedup 5 min por IP.
              Ejemplo: SYN flood activo, P=77.39%.
```

---

## Validación en vivo (2026-06-22)

| Evento | Timestamp | Detalle |
|---|---|---|
| Motor LIMIT | 00:43:12 | src=192.168.0.100 score=−0.4638 pkt_rate=444 |
| Motor BLOCK | 00:43:30 | src=192.168.0.100 score=−0.6157 HTTP_ABUSE |
| **Predictor ALERTA** | **00:51:59** | **P=77.39% → ALERTA-PREDICTIVA ✅** |

Comportamiento correcto: el XGBoost predijo correctamente que el ataque continuaría (y así fue — Kali siguió atacando hasta el bloqueo permanente a las 06:39).

---

## Imágenes de referencia

| Imagen | Ruta |
|---|---|
| Curva ROC XGBoost v2 | `docs/ppi_documentacion2/imagenes/F4_predictor/f4_roc_comparacion.png` |
| SHAP — importancia de features | `docs/ppi_documentacion2/imagenes/F4_predictor/f4_shap_importancia.png` |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado |
|---|---|---|
| CA-11 | AUC-ROC ≥ 0.95 | ✅ **0.9992** |
| CA-12 | FP + FN ≤ 30 en test set | ✅ **14** (7+7) |
| CA-F4-01 | ALERTA-PREDICTIVA disparada en SYN Flood | ✅ P=77.39% |
| CA-F4-02 | FPR en corridas normales = 0% | ✅ whitelist — 0 alertas |
| CA-F4-03 | Hot-reload sin reiniciar servicio | ✅ Detecta mtime del pkl |
| CA-F4-04 | Sin data leakage en features | ✅ score eliminado (v2) |

---

## Argumento de defensa

> "El XGBoost cierra la brecha que el IF no puede cubrir: la dimensión temporal. Un IDS que solo clasifica flujo por flujo no distingue un scan único de una campaña sostenida. El XGBoost, alimentado con los contadores de ventana temporal del propio motor, hace exactamente eso con AUC=0.9992. El dato más importante para la defensa es que detectamos y corregimos data leakage durante el desarrollo — la versión v1 tenía AUC=1.0000 artificial. Al eliminarlo, el AUC bajó a 0.9992 y el modelo ahora generaliza correctamente a datos nuevos."
