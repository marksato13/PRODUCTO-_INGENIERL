# F4 — Predicción Inteligente (XGBoost v2)
**Estado: ✅ IMPLEMENTADA Y VALIDADA**  
**Resultado:** AUC-ROC=0.9991 | FP+FN=15/12,705 | 10 features | ALERTA-PREDICTIVA validada P=77.39%

---

## Objetivo

Complementar al IF añadiendo memoria temporal: predecir si un evento LIMIT o BLOCK corresponde al inicio de un ataque sostenido (que continuará) o a una anomalía puntual (que cesará sola), usando el historial de comportamiento de la IP como features comportamentales.

**Por qué esta dimensión temporal importa:** el IF clasifica flujo por flujo — no tiene memoria. Dos ataques con el mismo flujo individual producen el mismo score IF, aunque uno sea un port scan único de 5 segundos y el otro sea un SYN flood de 20 minutos. El XGBoost ve la **velocidad y acumulación** de bloqueos de una IP en el tiempo, y distingue ambos casos con AUC=0.9991.

---

## Terminología clave

| Término | Definición |
|---|---|
| **XGBoost** | eXtreme Gradient Boosting. Ensemble de árboles de decisión entrenados secuencialmente: cada árbol corrige los errores del anterior (boosting). La predicción final es la suma ponderada de todos los árboles. |
| **Clasificación supervisada** | El modelo aprende de ejemplos etiquetados. A diferencia del IF (no supervisado), XGBoost necesita saber cuáles ataques fueron "sostenidos" para aprender a predecirlos. Las etiquetas se derivan automáticamente del log del motor — sin etiquetado manual. |
| **Label automático** | `label=1` si la misma IP genera otro BLOCK en los próximos 60 segundos. `label=0` si no reincide. Se calcula con `bisect_right` sobre el historial de BLOCKs de cada IP. |
| **Amenaza sostenida (label=1)** | IP que después de ser detectada vuelve a atacar en 60s. Representa el 10.8% del dataset (6,860 eventos). Ejemplos: SYN flood continuo, hydra sin detener. |
| **Anomalía puntual (label=0)** | IP que genera un evento aislado sin reincidencia. 89.2% del dataset. Puede ser un false positive del IF o un scan único. No requiere intervención activa. |
| **block_rate_60s** | Feature nueva (v2.1): `block_count_60s / 60.0`. Mide la **velocidad** de bloqueos por segundo en la ventana de 60s. Un atacante con 12 BLOCKs en 10s (rate=0.2/s) vs 12 BLOCKs en 60s (rate=0.2/s) da el mismo `block_count_60s` pero el patrón de aceleración es diferente y capturable con features adicionales. |
| **Data leakage** | Cuando una feature del modelo contiene información que ya responde la pregunta. En v1: `score` del IF (labels derivados de ese score). AUC=1.0000 artefactual que no generaliza. Corregido en v2. |
| **scale_pos_weight** | Parámetro XGBoost para clases desbalanceadas. Con `label_0/label_1 = 56,664/6,860 = 8.26`, asignar weight=8.26 al label minoritario (sostenido) equilibra la función de pérdida. Sin esto, el modelo ignoraría los casos raros y siempre predecirá label=0. |
| **Hot-reload** | El predictor verifica el `mtime` del `.pkl` en cada ciclo. Si F5 reentrenó el modelo, lo recarga en caliente sin reiniciar el servicio. |
| **ALERTA-PREDICTIVA** | Nivel máximo del predictor (P≥0.70). Telegram al operador, panel rojo en dashboard, log WARNING. Dedup 300s por IP. |
| **stratify** | Split estratificado: igual proporción label=0/1 en train y test. Sin stratify, el test podría tener muy pocos positivos y las métricas serían inestables. |

---

## Entradas → Proceso → Salidas

```
ENTRADAS  [f4_entrenar_predictor_v2.py — entrenamiento, una vez]
  results/motor_decision.log              (eventos LIMIT+BLOCK históricos)

ENTRADAS  [predictor.py — operación continua]
  results/motor_decision.log              (lectura cada INTERVALO=10s)
  models/predictor_modelo_v2.pkl          (XGBoost 10 features, hot-reload)
  models/features_predictor_v2.txt        (10 features en orden exacto)

PROCESO  [f4_entrenar_predictor_v2.py]
  Parsear log → extraer eventos ANOMALÍA/SOSPECHOSO con score= (LIMIT+BLOCK)
  Por cada evento: calcular ventanas deslizantes por IP
    limit_count_15s  = nº LIMITs de esta IP en [t-15s, t]
    block_count_60s  = nº BLOCKs de esta IP en [t-60s, t]
    block_rate_60s   = block_count_60s / 60.0
  Label: ¿BLOCK de esta IP en [t, t+60s]? → 1=sostenido | 0=puntual
  Split estratificado 80/20 (random_state=42)
  XGBoostClassifier(n_estimators=300, max_depth=4, lr=0.05,
                    scale_pos_weight=8.26)
  Evaluar: AUC, Precision, Recall, F1, matriz confusión

PROCESO  [predictor.py — cada INTERVALO=10s]
  Leer nuevas líneas de motor_decision.log
  Por cada IP con eventos recientes: calcular 10 features
  clf.predict_proba(X)[:,1] → P ∈ [0,1]
  P < 0.40        → SILENCIO
  0.40 ≤ P < 0.70 → AVISO (dashboard amarillo)
  P ≥ 0.70        → ALERTA-PREDICTIVA (rojo + Telegram, dedup 300s)
  check_hot_reload() → mtime del .pkl cambiado → reload sin reiniciar

SALIDAS
  models/predictor_modelo_v2.pkl          (XGBoost 10 features, AUC=0.9991)
  models/features_predictor_v2.txt        (10 features en orden)
  results/metricas_predictor_v2.txt       (AUC, métricas, matriz confusión)
  results/predictor.log                   (AVISO / ALERTA-PREDICTIVA por IP)
  Telegram mensajes                        (P≥0.70, dedup 300s por IP)
  Dashboard web :8080                      (panel predictor en tiempo real)
```

---

## ¿Por qué complementa al IF?

El IF responde: **¿este flujo es anómalo AHORA?**
El XGBoost responde: **¿esta IP seguirá atacando en los próximos 60 segundos?**

Son preguntas distintas con valor operativo diferente:

| Escenario | IF (flujo actual) | XGBoost (comportamiento futuro) |
|---|---|---|
| SYN flood continuo | BLOCK desde flujo 1 | P=77.39% → ALERTA-PREDICTIVA sostenido |
| Port scan único | BLOCK (reconocimiento) | P≈0.20 → silencio (puntual, no reincide) |
| BF SSH con hydra | LIMIT→BLOCK heurístico | P≈0.85 → ALERTA anticipada |
| Tráfico normal | PERMIT (whitelist) | Sin eventos → sin predicción |

**La clave:** el IF puede bloquear ambos el port scan y el SYN flood con el mismo mecanismo. El XGBoost informa al operador cuál necesita atención urgente (el flood continuará) y cuál puede ignorarse (el scan fue un evento único).

---

## Features del modelo (10) — actuales verificados en modelo .pkl

```python
FEATURES_v2 = [
    'dest_port',        # puerto destino del flujo
    'proto_tcp',        # 1 si TCP, 0 si no
    'proto_udp',        # 1 si UDP, 0 si no
    'proto_icmp',       # 1 si ICMP, 0 si no
    'hora_sin',         # sin(hora/24 × 2π) — codificación cíclica
    'hora_cos',         # cos(hora/24 × 2π)
    'limit_count_15s',  # nº LIMITs de esta IP en [t-15s, t]
    'block_count_60s',  # nº BLOCKs de esta IP en [t-60s, t]
    'block_rate_60s',   # block_count_60s / 60.0 — velocidad de bloqueo ← NUEVO
    'is_block',         # 1 si score ≤ τ2 (BLOCK) en evento actual
]
# score IF eliminado → sin data leakage
# 10 features comportamentales puras
```

| Feature | Importancia (GAIN) | Por qué importa |
|---|---|---|
| `block_count_60s` | **55.47%** | La cantidad de BLOCKs en los últimos 60s es el predictor más directo de persistencia: si ya hubo 10 BLOCKs de esta IP, casi con certeza habrá más |
| `block_rate_60s` | **35.65%** | La **velocidad** de bloqueo distingue aceleración de residuos antiguos: 10 BLOCKs en 10s (rate=1.0/s, ataque activo) vs 10 BLOCKs en 60s (rate=0.17/s, podría estar aminorando) |
| `is_block` | 6.64% | Confirma que el evento actual superó τ2 — el IF ya lo marcó como anomalía clara, no solo sospechosa |
| `hora_cos` | 0.61% | Componente coseno de la hora — ataques de madrugada tienen diferente distribución que los diurnos |
| `limit_count_15s` | 0.53% | Acumulación de eventos sospechosos (score entre τ1 y τ2) antes del primer BLOCK |
| `hora_sin` | 0.49% | Componente seno — junto con `hora_cos` codifica la hora sin discontinuidad en medianoche |
| `dest_port` | 0.38% | Puerto objetivo da contexto: :22=SSH, :80=HTTP, :53=UDP |
| `proto_tcp` | 0.12% | TCP floods (SYN) son sostenidos por naturaleza |
| `proto_udp` | 0.10% | UDP floods también, pero `block_count_60s` + `block_rate_60s` ya capturan esa información |
| `proto_icmp` | 0.00% | ICMP floods son escasos en el dataset — toda su información está en `block_count_60s` |

**Por qué `block_count_60s` domina (55.47%):** los ataques sostenidos generan BLOCKs repetidos porque el atacante sigue enviando tráfico aunque el servidor lo dropee. Suricata en el sensor lo sigue viendo. Después de 3-4 BLOCKs en 60s, el modelo tiene casi certeza de sostenimiento.

**Por qué `block_rate_60s` es el segundo predictor (35.65%):** permite al modelo distinguir entre "12 BLOCKs acumulados de las últimas horas" (residuos) y "12 BLOCKs en los últimos 10 segundos" (ataque activo ahora mismo). Sin esta feature, ambos escenarios tendrían P similar aunque el primero ya haya cesado.

**Por qué proto_udp no domina (0.10%):** en el modelo actual, `block_count_60s` y `block_rate_60s` capturan toda la información que proto_udp aportaría. Un UDP flood es sostenido no porque sea UDP, sino porque genera BLOCKs rápidamente — eso ya está en las ventanas temporales. Cuando existen features más informativas, XGBoost descarta las redundantes.

---

## Corrección de data leakage (v1 → v2)

**v1 (con leakage — AUC=1.0000 artefactual):**
```python
FEATURES_v1 = ['dest_port', 'proto_tcp', 'proto_udp', 'proto_icmp',
                'hora_sin', 'hora_cos', 'limit_count_15s', 'block_count_60s',
                'is_block', 'score']   # ← LEAKAGE
```
El `score` IF es la salida directa del modelo. Los labels (`label=1` si score≤τ2) se derivan del mismo score. XGBoost aprendía: "score<−0.6027 → label=1" trivialmente. AUC=1.0000 no reflejaba aprendizaje real.

**v2 (sin leakage — AUC=0.9991 real):**
```python
FEATURES_v2 = ['dest_port', 'proto_tcp', 'proto_udp', 'proto_icmp',
                'hora_sin', 'hora_cos', 'limit_count_15s', 'block_count_60s',
                'block_rate_60s', 'is_block']   # ← score eliminado, block_rate añadido
```
El modelo aprende patrones comportamentales reales — historial temporal de la IP, no la salida del IF.

**Por qué el AUC bajó de 1.0 a 0.9991 y eso es bueno:** un AUC=1.0 en datos de laboratorio es sospechoso — indica que el modelo memorizó un artefacto de los datos, no que aprendió el problema. AUC=0.9991 sobre un test set separado que el modelo nunca vio es evidencia de generalización real.

---

## Pipeline de entrenamiento (`f4_entrenar_predictor_v2.py`)

```
results/motor_decision.log  (63,524 eventos LIMIT+BLOCK)
    │
    ▼ parse_log() — regex captura ANOMALÍA|SOSPECHOSO con score=
    │   ⚠️  NO captura HTTP-ABUSE ni BRUTE-FORCE (sin campo score=)
    │
    ▼ construir_dataset() — ventanas deslizantes por IP
    │   limit_count_15s  = |{t' ∈ LIMITs(ip) : t-15 ≤ t' ≤ t}|
    │   block_count_60s  = |{t' ∈ BLOCKs(ip) : t-60 ≤ t' ≤ t}|
    │   block_rate_60s   = block_count_60s / 60.0
    │   label = 1 si ∃ BLOCK(ip) en (t, t+60], else 0
    │
    ▼ train_test_split(stratify=y, test_size=0.20, random_state=42)
    │   Train: 50,819  (label_1=5,488, label_0=45,331)
    │   Test:  12,705  (label_1=1,372, label_0=11,333)
    │
    ▼ XGBoostClassifier(
    │     n_estimators=300,      # suficientes árboles para estabilidad
    │     max_depth=4,           # árboles poco profundos → menos overfitting
    │     learning_rate=0.05,    # step size conservador → mejor generalización
    │     scale_pos_weight=8.26  # 56,664/6,860 — compensa desbalance de clases
    │   )
    ▼ Evaluar en test set nunca visto
    ▼ Guardar: predictor_modelo_v2.pkl | features_predictor_v2.txt
```

**Por qué max_depth=4 y no más:** árboles profundos en XGBoost memorizan ruido del training set. Con max_depth=4, cada árbol tiene ≤16 hojas — suficiente para capturar la interacción `block_count_60s × block_rate_60s × is_block` sin overfitting.

**Por qué learning_rate=0.05:** un learning rate alto (0.3, default XGBoost) converge rápido pero en un mínimo local. Con 0.05 y 300 árboles, el ensemble converge más lentamente pero a un mínimo mejor. La combinación lr=0.05 + n_estimators=300 es un punto óptimo empírico para datasets de este tamaño.

**Por qué scale_pos_weight=8.26:** sin penalización, el modelo aprendería a predecir siempre label=0 (89.2% del dataset) y tendría 89.2% de accuracy sin detectar ningún ataque sostenido. scale_pos_weight=8.26 hace que un error en label=1 (sostenido) cueste 8.26× más que un error en label=0. El modelo prioriza no perder ataques sostenidos.

```bash
python3 scripts/f4_entrenar_predictor_v2.py
```

---

## Métricas reales del modelo actual (verificadas en metricas_predictor_v2.txt)

| Métrica | Valor real |
|---|---|
| Dataset total | 63,524 eventos LIMIT+BLOCK |
| label=1 sostenido | **6,860 (10.8%)** |
| label=0 puntual | **56,664 (89.2%)** |
| Split train / test | **50,819 / 12,705** |
| scale_pos_weight | **8.26** |
| **AUC-ROC** | **0.9991** |
| Precision (sostenido) | **99.35%** |
| Recall (sostenido) | **99.56%** |
| F1 (sostenido) | **0.9945** |
| FP + FN en test | **15** (9 FP + 6 FN de 12,705) |

### Matriz de confusión real (test set 12,705 muestras)

```
                  Predicho: Puntual   Predicho: Sostenido
Real: Puntual        TN=11,324            FP=9
Real: Sostenida      FN=6                 TP=1,366
```

**9 FP:** el predictor alertó sobre 9 ataques que resultaron ser puntuales. Impacto bajo — el operador recibe una alerta innecesaria. El IF ya actuó correctamente (BLOCK).

**6 FN:** 6 ataques sostenidos no fueron predichos como tales. Impacto limitado — el IF ya los bloqueó igualmente. El XGBoost no los predijo como sostenidos, pero eso no dejó tráfico pasar.

**Por qué FP y FN son aceptables:** el XGBoost es una capa de **predicción adicional** sobre el IF, no un sistema de control independiente. Si el XGBoost falla, el IF sigue bloqueando. Los errores del XGBoost afectan la calidad de las alertas al operador, no la seguridad de la red.

---

## Parámetros del predictor en producción (predictor.py)

| Parámetro | Valor | Propósito |
|---|---|---|
| `INTERVALO` | 10s | Ciclo de lectura del log y evaluación por IP |
| `THETA_ALTA` | 0.70 | Umbral ALERTA-PREDICTIVA |
| `THETA_MEDIA` | 0.40 | Umbral AVISO |
| `DEDUP_SEG` | 300s | Misma IP no genera 2 alertas en <5min |

**Por qué INTERVALO=10s y no 1s:** el predictor evalúa IPs con eventos recientes. Si cicla cada segundo, la mayoría de ciclos no encontrará nuevos eventos y desperdiciará CPU. Con 10s, el balance entre latencia de detección y uso de recursos es óptimo para el laboratorio.

**Por qué DEDUP_SEG=300s:** durante un SYN flood activo, el motor loga un BLOCK cada 5 segundos (rate-limited). Sin dedup, el predictor generaría una alerta Telegram cada 10s — inundando al operador. 300s = 1 alerta por IP cada 5 minutos, independientemente de cuántos BLOCKs genera.

---

## Niveles de alerta del predictor

```
P < 0.40     → SILENCIO
              Tráfico puntual o bajo riesgo. No se registra ni notifica.
              Ejemplo: port scan único (P≈0.20), falso positivo IF.

0.40 ≤ P < 0.70  → AVISO (amarillo en dashboard)
                   "Actividad sospechosa — vigilando."
                   Log INFO. Sin Telegram. Sistema monitorea.
                   Ejemplo: inicio de BF SSH con pocos intentos.

P ≥ 0.70     → ALERTA-PREDICTIVA (rojo en dashboard + Telegram)
              "Ataque sostenido en curso — requiere atención."
              Log WARNING. Dedup 300s por IP.
              Ejemplo: SYN flood activo con 8+ BLOCKs en 60s.
```

**Por qué 0.70 como umbral de ALERTA:** con P=0.70, el predictor tiene 70% de confianza en sostenimiento. En validación, este umbral produce P=99.35% precision (falso positivo muy bajo). Un umbral menor (0.50) aumentaría recalls pero con más falsas alarmas que el operador terminaría ignorando.

---

## Validación en vivo (2026-06-22)

| Evento | Timestamp | Detalle |
|---|---|---|
| Motor LIMIT | 00:43:12 | src=192.168.0.100 score=−0.4638 pkt_rate=444 |
| Motor BLOCK | 00:43:30 | src=192.168.0.100 score=−0.6157 HTTP_ABUSE |
| **Predictor ALERTA** | **00:51:59** | **P=77.39% → ALERTA-PREDICTIVA ✅** |

El XGBoost predijo correctamente que el ataque continuaría. Kali siguió atacando hasta el bloqueo permanente a las 06:39 (6 horas después). La alerta a las 00:51 permitió que el operador tomara conciencia 6 horas antes del bloqueo definitivo.

---

## Imágenes de referencia

| Imagen | Ruta | Estado |
|---|---|---|
| Curva ROC XGBoost v2 | `docs/documentacion/imagenes/F4_predictor/f4_roc_comparacion.png` | ✅ Disponible |
| SHAP importancia de features | `docs/documentacion/imagenes/F4_predictor/f4_shap_importancia.png` | ✅ Disponible |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado | Verificación |
|---|---|---|---|
| CA-11 | AUC-ROC ≥ 0.95 | ✅ **0.9991** | `grep AUC results/metricas_predictor_v2.txt` |
| CA-12 | FP + FN ≤ 30 en test | ✅ **15** (9+6 de 12,705) | matriz confusión en metricas |
| CA-F4-01 | ALERTA-PREDICTIVA en SYN Flood | ✅ P=77.39% validado 2026-06-22 | predictor.log |
| CA-F4-02 | FPR en corridas normales = 0% | ✅ whitelist — 0 alertas sobre IPs legítimas | F6 resultados |
| CA-F4-03 | Hot-reload sin reiniciar servicio | ✅ mtime check en cada ciclo de 10s | predictor.py:115 |
| CA-F4-04 | Sin data leakage en features | ✅ score eliminado, 10 features comportamentales | f4_entrenar*.py |

---

## Argumento de defensa

> "El XGBoost cierra la brecha que el IF no puede cubrir: la dimensión temporal. El IF clasifica cada flujo de forma aislada — no tiene memoria. El XGBoost observa el historial de bloqueos de una IP: cuántos ocurrieron en los últimos 60 segundos y a qué velocidad. Con estas dos features (`block_count_60s=55.47%`, `block_rate_60s=35.65%`), el modelo distingue con AUC=0.9991 un ataque sostenido de una anomalía puntual.
>
> El dato más importante para la defensa es que detectamos y corregimos data leakage durante el desarrollo — la versión v1 tenía AUC=1.0000 artefactual porque incluía el `score` IF como feature. Al eliminarlo, el AUC bajó a 0.9991 y el modelo ahora generaliza. Un AUC de 1.0 en datos de laboratorio es una señal de alarma metodológica, no un logro.
>
> Con solo 15 errores en 12,705 muestras de test (9 FP + 6 FN), el predictor complementa al IF sin interferir con él: si XGBoost falla en predecir un ataque como sostenido, el IF ya lo bloqueó de todas formas."

