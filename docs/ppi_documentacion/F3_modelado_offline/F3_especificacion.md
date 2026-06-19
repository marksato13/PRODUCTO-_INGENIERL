# F3 — Especificación Técnica: Modelado Offline

## 1. Objetivo y posición en el pipeline

Entrenar el modelo Isolation Forest **exclusivamente con tráfico normal** (Grupo A) y
derivar los umbrales de decisión τ1/τ2 mediante análisis de la curva ROC sobre datos
nunca vistos por el modelo. Producir `metricas_offline.txt` como **fuente única de
verdad** para AUC, τ1, τ2, Precision, Recall y F1.

```
POSICIÓN EN EL PIPELINE COMPLETO

F2 (capturas .gz)      F3 (modelado offline)         F4 (motor tiempo real)
──────────────────  →  ────────────────────────  →   ───────────────────────
*_normal_*.gz          fase3_entrenar.py              motor_decision.py
*_anom_*.gz       →    fase3_evaluar.py        →      lee models/*.pkl
*_mixto_*.gz           auc_por_escenario.py           lee metricas_offline.txt
                        ↓                              aplica τ1/τ2 a cada flow
                        models/*.pkl
                        metricas_offline.txt
```

> **Nota metodológica:** F3 lee directamente los archivos `.gz` de F2. No existe
> ningún CSV intermedio (dataset_raw, dataset_clean, train, val, test). Isolation Forest
> es no supervisado — solo necesita datos normales para aprender, no etiquetas ni
> partición de validación.

---

## 2. Terminología clave

### 2.1 Isolation Forest — qué es y cómo funciona el score

Isolation Forest es un algoritmo de detección de anomalías **no supervisado** que
funciona sobre el principio: **los puntos anómalos son más fáciles de aislar**.

```
NORMAL:  pkts_toserver=4, pkts_toclient=3, duration=2.5s
         → Requiere MUCHOS cortes para aislar (está en zona densa de normalidad)
         → score ≈ -0.39 (cerca de 0 = normal)

ATAQUE:  pkts_toserver=1, pkts_toclient=0, duration≈0 (Port Scan)
         → Se aísla con POCOS cortes (outlier en todas las dimensiones)
         → score ≈ -0.73 (cerca de -1 = muy anómalo)
```

El modelo construye `n_estimators=300` árboles de aislamiento sobre muestras
aleatorias del X_train. Para un nuevo punto, el score es el promedio del número
de cortes necesarios para aislarlo en cada árbol:

| Score IF | Interpretación | Decisión del motor |
|---|---|---|
| > τ1 = −0.4459 | Normal — difícil de aislar | PERMIT |
| τ2 < score ≤ τ1 | Sospechoso — zona gris | LIMIT (100 pkt/s) |
| ≤ τ2 = −0.6027 | Anómalo — fácil de aislar | BLOCK (DROP) |

### 2.2 StandardScaler — por qué es necesario

Las 14 features tienen escalas muy diferentes:

| Feature | Escala típica normal | Sin escalar... |
|---|---|---|
| `byte_rate` | 0 – 50,000 B/s | domina el espacio de decisión |
| `pkt_rate` | 0 – 200 pkt/s | contribuye menos |
| `is_tcp` | 0 ó 1 | virtualmente ignorada |
| `dest_port` | 22, 80, 443... | escala intermedia |

`StandardScaler` transforma cada feature a **media=0, desviación=1**:

```python
X_scaled[:,i] = (X[:,i] - mean_i) / std_i
```

El scaler se ajusta **solo con el 80% de entrenamiento** (`fit_transform(X_train)`)
y luego se aplica al holdout y a los flows del motor con `transform()` únicamente.
Si se aplicara `fit_transform()` al holdout, habría fuga de datos (data leakage).

```
Ejemplo de transformación real:
  byte_rate:   mean=12,440  std=18,500
  Flujo normal (curl): byte_rate=8,200 → scaled = (8,200-12,440)/18,500 = -0.229
  SYN Flood:           byte_rate=2,100 → scaled = (2,100-12,440)/18,500 = -0.559
```

### 2.3 Curva ROC — cómo se construye con datos no supervisados

IF no usa etiquetas durante el entrenamiento, pero para evaluar su calidad de
discriminación necesitamos etiquetas. Se asignan **post-hoc** según el origen del archivo:

```
Datos de evaluación:
  normal_holdout.csv (13,427 flows)   → label = 0  (normal, proviene de *_normal_*.gz)
  *_anom_*.gz        (598,285 flows)   → label = 1  (anómalo, proviene de *_anom_*.gz)

Para cada flow: score = isolation_forest.score_samples([features_scaled])

Curva ROC:
  Eje X = FPR = FP/(FP+TN)  = flows normales clasificados como anómalos / total normal
  Eje Y = TPR = TP/(TP+FN)  = flows anómalos clasificados como anómalos / total anómalo

  Se barre τ de -1.0 a 0.0:
  - Si τ es muy bajo (−1): casi nada se clasifica como anómalo → TPR≈0, FPR≈0
  - Si τ es muy alto (0):  todo se clasifica como anómalo     → TPR≈1, FPR≈1
  - En τ1=−0.4459: TPR=99.40%, FPR=20.47%
```

**AUC-ROC = 0.8998** significa que hay 89.98% de probabilidad de que un flow
anómalo elegido al azar obtenga un score menor (más anómalo) que un flow normal
elegido al azar.

### 2.4 Youden Index — criterio para τ1 (umbral de alerta)

```
J(τ) = TPR(τ) − FPR(τ)

τ1 = argmax J(τ) = −0.4459

En τ1 = −0.4459:
  TPR = 99.40%  (detecta 99.4 de cada 100 ataques)
  FPR = 20.47%  (20.47% de flows normales superan el umbral → potencial LIMIT)
  J   = 0.9940 − 0.2047 = 0.7893  ← máximo posible en esta curva ROC
```

El Youden Index es el criterio estándar en literatura de detección de intrusiones
porque maximiza simultáneamente la sensibilidad (Recall) y la especificidad (1-FPR).
El FPR del 20.47% se mitiga operacionalmente con la whitelist del motor (IPs
conocidas: Desktop, Sensor, Server nunca se evalúan).

### 2.5 Criterio FPR≤2% — criterio para τ2 (umbral de bloqueo)

```
τ2 = max{τ : FPR(τ) ≤ 0.02}  →  −0.6027

En τ2 = −0.6027:
  TPR = 18.27%  (detecta solo 18% de ataques por score puro)
  FPR = 2.00%   (muy pocos falsos positivos)
```

τ2 es el umbral **conservador**: solo flujos con score muy bajo (muy anómalos)
se bloquean directamente. Los flujos en la zona gris (τ2 < score ≤ τ1) reciben LIMIT
y son monitorizados. Los heurísticos BF-SSH y HTTP-ABUSE cubren los ataques que
quedan en la zona gris (BruteForce, HTTP Abuse, SYN Flood gradual).

---

## 3. Entradas

| Entrada | Ruta | Descripción |
|---|---|---|
| Capturas normales | `data/raw/*_normal_*.gz` | 28 archivos Grupo A — Kali apagada |
| Capturas anómalas | `data/raw/*_anom_*.gz` | 13 archivos Grupo B — Desktop quieto |
| Capturas mixtas | `data/raw/*_mixto_*.gz` | 6 archivos Grupo C — ambos activos |
| Modelos (para evaluar) | `models/isolation_forest.pkl`, `models/scaler.pkl` | Solo usados por `fase3_evaluar.py` y `auc_por_escenario.py` — no por `fase3_entrenar.py` |

Los globs son **date-agnostic** — funcionan con cualquier fecha de captura.

---

## 4. Salidas y conexión con fases posteriores

| Salida | Ruta | Generado por | Consumido por |
|---|---|---|---|
| Modelo IF | `models/isolation_forest.pkl` | `fase3_entrenar.py` | Motor F4, `fase3_evaluar.py`, `auc_por_escenario.py` |
| Scaler | `models/scaler.pkl` | `fase3_entrenar.py` | Motor F4, `fase3_evaluar.py`, `auc_por_escenario.py` |
| Lista de features | `models/features.csv` | `fase3_entrenar.py` | Motor F4 (orden exacto de columnas) |
| Holdout normal | `data/normal_holdout.csv` | `fase3_entrenar.py` (20%) | `fase3_evaluar.py` (referencia normal para ROC) |
| **Métricas canónicas** | `results/metricas_offline.txt` | `fase3_evaluar.py` | **Motor F4 al arrancar** — lee τ1, τ2 |
| Curva ROC | `results/auc_roc.png` | `fase3_evaluar.py` | Documentación / tesis |
| AUC por escenario | `results/reports/auc_por_escenario.txt` | `auc_por_escenario.py` | Validación F6, VERIFICACION_ESCENARIOS.md |

> **Nota sobre `models/autoencoder.pkl`:** Este archivo existe en el sensor pero
> **no pertenece al pipeline de producción F3**. Fue generado por
> `scripts/comparacion/f_ensemble_if_ae.py` durante el experimento comparativo.
> No interviene en el motor de decisión ni en ningún script de F3-F6.

---

## 5. Flujo de datos F3 completo (paso a paso)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 1 — fase3_entrenar.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

data/raw/*_normal_*.gz (28 archivos)
  │
  │ gzip.open() + json.loads() línea a línea
  │ filtro: event_type=flow
  │ filtro: src_ip en NORMAL_IPS {192.168.0.20, 192.168.0.120}
  │ filtro: no IPv6 (descarta ':' en src_ip)
  │ extracción: 14 features por flow (ver §7)
  ▼
X_raw  shape=(67,135 × 14)
  │
  │ train_test_split(test_size=0.20, random_state=42, shuffle=True)
  ├──────────────────────────────────────────────────────────────
  │ 80% = 53,708 flows                20% = 13,427 flows
  │         │                                  │
  │  StandardScaler                    scaler.transform()
  │  .fit_transform()                  (aplica parámetros del 80%,
  │  ajusta mean/std de                 NO recalcula — sin leakage)
  │  cada feature                               │
  │         │                                  ▼
  │   X_train_scaled                   X_holdout_scaled
  │  (53,708 × 14)                     (13,427 × 14)
  │         │                                  │
  │  IsolationForest(                  guardado como:
  │   n_estimators=300,                data/normal_holdout.csv
  │   contamination=0.05,
  │   random_state=42
  │  ).fit(X_train_scaled)
  │         │
  ▼         ▼
models/isolation_forest.pkl    ← modelo serializado (~2.5 MB)
models/scaler.pkl              ← StandardScaler (mean, std por feature)
models/features.csv            ← ['pkts_toserver', ..., 'dest_port']

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 2 — fase3_evaluar.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

isolation_forest.pkl + scaler.pkl  ← cargados con joblib.load()

data/normal_holdout.csv            data/raw/*_anom_*.gz (13 arch.)
  13,427 flows — label=0 (normal)    598,285 flows — label=1 (anómalo)
       │                                      │
       │ scaler.transform()                   │ gzip.open() + features
       │ IF.score_samples()                   │ scaler.transform()
       │                                      │ IF.score_samples()
       ▼                                      ▼
  scores_normal (13,427)         scores_anom (598,285)
  media: −0.3965 ± 0.075         media: −0.5420 ± 0.090
       │                                      │
       └──────────────┬───────────────────────┘
                      ▼
          scores_all (611,712 valores)
          labels_all (611,712: 13,427×0 + 598,285×1)
                      │
          roc_curve(labels_all, -scores_all)
          → fpr[], tpr[], thresholds[]
          → AUC = auc(fpr, tpr) = 0.8998
                      │
          τ1 = thresholds[argmax(tpr - fpr)] = −0.4459
               TPR@τ1 = 99.40%,  FPR@τ1 = 20.47%
                      │
          τ2 = max threshold donde FPR ≤ 0.02  = −0.6027
               TPR@τ2 = 18.27%,  FPR@τ2 = 2.00%
                      │
                      ▼
          results/metricas_offline.txt  ← FUENTE ÚNICA DE VERDAD
          results/auc_roc.png           ← curva ROC con τ1, τ2 marcados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 3 — auc_por_escenario.py (desglose individual)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Para cada archivo .gz individual (Grupo B y C):
  20260615_anom_synflood_01.gz     → score → AUC(vs holdout) = 0.8342
  20260615_anom_portscan_01.gz     → score → AUC              = 0.9722
  20260615_anom_udpflood_01.gz     → score → AUC              = 0.9537
  20260615_anom_icmpflood_01.gz    → score → AUC              = 0.8961
  20260615_anom_httpabuse_01.gz    → score → AUC              = 0.9670
  20260615_anom_bruteforce_01.gz   → score → AUC              = 0.8658
  20260616_mixto_http_synflood.gz  → score → AUC              = 0.8206
  20260616_mixto_ssh_portscan.gz   → score → AUC              = 0.8596
  20260616_mixto_transfer_udp.gz   → score → AUC              = 0.9327
       │
       ▼
  results/reports/auc_por_escenario.txt
  (No modifica metricas_offline.txt — es análisis complementario)
```

---

## 6. Scripts del pipeline F3

### 6.1 `scripts/fase3_entrenar.py`

**Entrada:** `data/raw/*_normal_*.gz` (Grupo A, 28 archivos)
**Salida:** `isolation_forest.pkl`, `scaler.pkl`, `features.csv`, `normal_holdout.csv`

```bash
# Ejecución en sensor
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
python3 scripts/fase3_entrenar.py
```

Salida esperada en stdout:
```
Archivos normales encontrados: 28
Flows cargados (raw):          67,135
Flows post-filtro:             67,135
Split: 53,708 train / 13,427 holdout  (random_state=42)
StandardScaler ajustado a X_train (53,708 × 14)
IsolationForest entrenando... (n_estimators=300, sklearn 1.9.0)
Modelo guardado: models/isolation_forest.pkl  (2.47 MB)
Scaler guardado: models/scaler.pkl
Features:        models/features.csv  (14 columnas)
Holdout normal:  data/normal_holdout.csv  (13,427 rows)
```

**Por qué split 80/20 y no 70/15/15:**
El split 70/15/15 es una convención de modelos supervisados donde el 15% de validación
sirve para ajustar hiperparámetros durante el entrenamiento. IF no tiene hiperparámetros
que ajustar por gradiente — `n_estimators=300` y `contamination=0.05` son decisiones de
diseño validadas por análisis de sensibilidad previo. Solo se necesita un holdout de
referencia para construir la curva ROC en el paso siguiente.

---

### 6.2 `scripts/fase3_evaluar.py`

**Entrada:** `data/normal_holdout.csv` + `data/raw/*_anom_*.gz` + modelos `.pkl`
**Salida:** `results/metricas_offline.txt`, `results/auc_roc.png`

```bash
python3 scripts/fase3_evaluar.py
```

Salida esperada en stdout:
```
Modelo cargado: models/isolation_forest.pkl
Scaler cargado: models/scaler.pkl
Holdout normal: 13,427 flows  | score medio: -0.3965 ± 0.0753
Archivos anómalos: 13 .gz     | 598,285 flows
Score anómalos: medio -0.5420 ± 0.0900

Curva ROC construida (611,712 puntos)
AUC-ROC: 0.8998

τ1 (Youden index):  -0.4459  → TPR=99.40%  FPR=20.47%
τ2 (FPR ≤ 2%):     -0.6027  → TPR=18.27%  FPR= 2.00%

Métricas en τ1:
  Precision: 99.54%
  Recall:    99.40%
  F1-Score:  0.9947

Escrito: results/metricas_offline.txt
Figura:  results/auc_roc.png
```

**Contenido real de `results/metricas_offline.txt`:**
```
AUC=0.8998
tau1=-0.4459
tau2=-0.6027
precision=0.9954
recall=0.9940
f1=0.9947
n_train=53708
n_holdout=13427
n_anom=598285
sklearn_version=1.9.0
fecha=2026-06-16
```
El motor (`motor_decision.py`) lee `tau1` y `tau2` de este archivo **al arrancar**,
con `grep` o parsing de cada línea `clave=valor`.

---

### 6.3 `scripts/auc_por_escenario.py`

**Entrada:** `data/raw/*_anom_*.gz` + `data/raw/*_mixto_*.gz` + modelos `.pkl`
**Salida:** `results/reports/auc_por_escenario.txt`

Calcula AUC individual para cada escenario comparando flows de ese escenario contra
`normal_holdout.csv` (mismo holdout de referencia). No modifica `metricas_offline.txt`.

```bash
python3 scripts/auc_por_escenario.py
```

---

## 7. Las 14 features del modelo

Extraídas de cada evento `event_type=flow` en los archivos `.gz`. El orden en
`models/features.csv` es exactamente el mismo que el motor usa en producción:

| # | Feature | Campo eve.json | Fórmula | Tipo |
|---|---|---|---|---|
| 1 | `pkts_toserver` | `flow.pkts_toserver` | directo | int |
| 2 | `pkts_toclient` | `flow.pkts_toclient` | directo | int |
| 3 | `bytes_toserver` | `flow.bytes_toserver` | directo | int |
| 4 | `bytes_toclient` | `flow.bytes_toclient` | directo | int |
| 5 | `duration` | `flow.start`, `flow.end` | `(end-start).total_seconds()` | float |
| 6 | `pkt_rate` | pkts_total, duration | `(pkts_to+pkts_from) / max(dur, 0.001)` | float |
| 7 | `byte_rate` | bytes_total, duration | `(bytes_to+bytes_from) / max(dur, 0.001)` | float |
| 8 | `pkt_ratio` | pkts_toserver, toclient | `pkts_to / (pkts_from + 1)` | float |
| 9 | `byte_ratio` | bytes_toserver, toclient | `bytes_to / (bytes_from + 1)` | float |
| 10 | `avg_pkt_size` | bytes_total, pkts_total | `bytes_total / max(pkts_total, 1)` | float |
| 11 | `is_tcp` | `proto` | `1 if proto=="TCP" else 0` | int |
| 12 | `is_udp` | `proto` | `1 if proto=="UDP" else 0` | int |
| 13 | `is_icmp` | `proto` | `1 if proto=="ICMP" else 0` | int |
| 14 | `dest_port` | `dest_port` | directo (0 para ICMP) | int |

**El orden importa:** el motor aplica `scaler.transform()` y luego `IF.score_samples()`
con estas columnas en este orden exacto. Si se cambia el orden en `features.csv`,
el modelo produce scores incorrectos sin error visible.

---

## 8. Hiperparámetros del modelo

| Parámetro | Valor | Justificación |
|---|---|---|
| `n_estimators` | 300 | AUC estable a partir de n=200; 300 garantiza robustez sin costo excesivo |
| `contamination` | 0.05 | Prior conservador: ~5% de anomalías esperadas en red universitaria |
| `random_state` | 42 | Reproducibilidad exacta del modelo — mismo `.pkl` en cada entrenamiento |
| `max_samples` | `'auto'` | `min(256, n_samples)` — muestras por árbol; valor por defecto sklearn |
| `max_features` | 1.0 | Usa todas las features en cada árbol — adecuado con 14 features |
| `sklearn` | **1.9.0** | Fijado en venv y en el `.pkl` — sin mismatch de versiones con el motor |

**Nota sobre `contamination`:** Este valor afecta el desplazamiento del `decision_function`
pero no modifica los árboles. τ1 y τ2 son derivados de la curva ROC (no de `contamination`),
por lo que el motor ignora el offset de `decision_function` y usa `score_samples()` directamente.

---

## 9. Scores IF por tipo de tráfico

Distribución de scores observada en la evaluación F3 (τ1=−0.4459, τ2=−0.6027):

| Tipo de tráfico | Score medio | Rango típico | Zona de decisión | AUC parcial |
|---|---|---|---|---|
| Normal (curl, ssh, scp) | **−0.3965** ± 0.075 | −0.25 a −0.52 | PERMIT (score > τ1) | referencia |
| SYN Flood (B1) | **−0.490** ± 0.040 | −0.44 a −0.56 | Zona gris LIMIT/BLOCK | 0.8342 |
| Port Scan (B2) | **−0.733** ± 0.020 | −0.71 a −0.76 | BLOCK (score ≤ τ2) | 0.9722 |
| UDP Flood (B3) | **−0.650** ± 0.050 | −0.60 a −0.70 | BLOCK | 0.9537 |
| ICMP Flood (B4) | **−0.640** ± 0.030 | −0.62 a −0.68 | BLOCK | 0.8961 |
| HTTP Abuse (B5) | **−0.550** ± 0.060 | −0.48 a −0.63 | Zona gris + heurístico | 0.9670 |
| BruteForce (B6) | **−0.520** ± 0.070 | −0.45 a −0.61 | Zona gris + heurístico | 0.8658 |

**¿Por qué SYN Flood (B1) tiene el AUC más bajo?**
Un SYN Flood sin completar el handshake produce flows con `pkts_toserver=1`,
`pkts_toclient=0`, `duration≈0`. Algunos requests HTTP legítimos muy cortos tienen
un perfil similar → la separación en el espacio de features es menor → score cae
en la zona gris entre τ1 y τ2 → muchos flows de B1 quedan en LIMIT, no en BLOCK.
El motor los bloquea definitivamente cuando el heurístico HTTP-ABUSE acumula >100
requests en 30s desde la misma IP.

**¿Por qué Port Scan (B2) tiene el AUC más alto?**
nmap -sS emite un paquete SYN por puerto (1-1024) y nunca recibe respuesta (server
descarta). Cada flow tiene exactamente `pkts_toserver=1, pkts_toclient=0, dest_port`
diferente por flow, `duration≈0`. Esta firma es extremadamente anómala en las 14
dimensiones → el IF la aísla en 1-2 cortes → score ≈ −0.73, muy por debajo de τ2.

**Separación de distribuciones:**
```
Normal:  media = −0.3965  ────────────────────────────── τ1=−0.4459 ──
                                    ↑ PERMIT arriba           ↑ LIMIT/BLOCK aquí
SYN Fl.: media = −0.490           ← zona gris →
                                                      τ2=−0.6027
UDP/B3:  media = −0.650  ──────────────────────────────────────── BLOCK aquí
Port Sc: media = −0.733  ───────────────────────────────────────────────── BLOCK
         Delta normal→anómalo medio: 0.1454
```

---

## 10. Umbrales derivados (fuente canónica: `results/metricas_offline.txt`)

| Umbral | Valor | Criterio de derivación | TPR en ese umbral | FPR en ese umbral |
|---|---|---|---|---|
| **τ1** (PERMIT/LIMIT) | **−0.4459** | Youden: `argmax(TPR − FPR)` | **99.40%** | 20.47% |
| **τ2** (LIMIT/BLOCK) | **−0.6027** | `max TPR donde FPR ≤ 2%` | 18.27% | **2.00%** |

**Por qué FPR=20.47% en τ1 es metodológicamente correcto:**
Bajar FPR a ≤5% requeriría τ1=−0.5547. Los flows de SYN Flood tienen score≈−0.49,
que está por encima de −0.5547 → pasarían como PERMIT (no detectados). Reducir el
FPR en el umbral de alerta sacrifica demasiado Recall en la clase de ataques más
difícil. La whitelist opera como mitigación práctica del FPR: los únicos hosts que
generan tráfico legítimo (Desktop .20, Sensor .110, Server .120) nunca son evaluados
por el motor → el FPR operacional observado es 0%.

**Sincronización `umbrales_finales.txt` ↔ `metricas_offline.txt`:**
El motor lee únicamente `metricas_offline.txt`. El archivo `umbrales_finales.txt`
en `results/` es una copia de referencia para documentación — ambos deben estar
sincronizados. Si se reentrena el modelo, ambos archivos deben actualizarse.

---

## 11. Métricas del modelo (resultado final — 2026-06-16)

| Métrica | Valor | Requisito PPI | Estado |
|---|---|---|---|
| AUC-ROC | **0.8998** | ≥ 0.85 | ✅ CUMPLE |
| Precision (en τ1) | **99.54%** | ≥ 95% | ✅ CUMPLE |
| Recall (en τ1) | **99.40%** | ≥ 95% | ✅ CUMPLE |
| F1-Score | **0.9947** | ≥ 0.90 | ✅ CUMPLE |
| Score medio normal | −0.3965 ± 0.075 | — | — |
| Score medio anómalo | −0.5420 ± 0.090 | — | — |
| Delta separación | 0.1454 | > 0 | ✅ CUMPLE |
| AUC mínimo (por escenario) | B1 SYN Flood: **0.8342** | — | Zona gris |
| AUC máximo (por escenario) | B2 Port Scan: **0.9722** | — | — |

**Datos de entrenamiento:**
- `n_train_normal`: **53,708** flows (80% del Grupo A)
- `n_holdout_normal`: **13,427** flows (20% reservado — nunca visto por IF)
- `n_anom_eval`: **598,285** flows (Grupo B completo — solo evaluación)
- sklearn versión: **1.9.0** — sin mismatch entre venv y `.pkl`

---

## 12. Conexión F3 → F4 (cómo el motor usa los artefactos de F3)

Al arrancar `ppi-motor.service`, `motor_decision.py` ejecuta:

```python
# Líneas ~70-90 de motor_decision.py
import joblib
from pathlib import Path

# 1. Carga el modelo y el scaler
clf   = joblib.load('models/isolation_forest.pkl')   # IsolationForest
scaler = joblib.load('models/scaler.pkl')             # StandardScaler
features = open('models/features.csv').read().strip().split(',')  # 14 nombres

# 2. Lee τ1 y τ2 de metricas_offline.txt
metrics = {}
for line in open('results/metricas_offline.txt'):
    k, v = line.strip().split('=')
    metrics[k] = float(v)
TAU1 = metrics['tau1']   # -0.4459
TAU2 = metrics['tau2']   # -0.6027

# 3. Para cada flow de eve.json (en producción):
def evaluar_flow(flow_features):
    x = scaler.transform([flow_features])          # aplica el scaler de F3
    score = clf.score_samples(x)[0]                 # score IF
    if score > TAU1:   return 'PERMIT'
    elif score > TAU2: return 'LIMIT'
    else:              return 'BLOCK'
```

**Si `metricas_offline.txt` no existe al arrancar el motor:**
El motor falla con `FileNotFoundError` y `ppi-motor.service` queda en estado `failed`.
Por eso `systemctl start ppi-motor.service` depende de haber completado F3.

**Si se reentrena el modelo (nuevo F3):**
1. `python3 scripts/fase3_entrenar.py` → nuevo `isolation_forest.pkl` + `scaler.pkl`
2. `python3 scripts/fase3_evaluar.py`  → nuevo `metricas_offline.txt` con nuevos τ1/τ2
3. `sudo systemctl restart ppi-motor.service` → motor carga los nuevos artefactos

---


## 13. EDA — Análisis Exploratorio de Features (previo al split 80/20)

El EDA se realiza **antes del split 80/20**, usando el universo completo de flows capturados (Grupos A, B y C). Es un paso puramente exploratorio: no modifica los datos, no filtra samples ni introduce sesgos hacia el conjunto de entrenamiento. Su propósito es confirmar que las 14 features discriminan efectivamente entre tráfico normal y anómalo.

### 13.1 Datos analizados

| Grupo | Tipo | Flows totales | Archivos |
|---|---|---|---|
| A | Normal (Desktop → Server) | 67,135 | 28 |
| B | Anómalo (Kali → Server) | 302,892 | 13 |
| C | Mixto (Desktop + Kali) | 31,397 | 6 |

> Las gráficas se generan sobre muestras de 15,000 flows por grupo (random_state=42). Las estadísticas descriptivas usan los datos completos.

### 13.2 Hallazgos clave

**Feature más discriminante: `byte_ratio`**

| Grupo | Mediana `byte_ratio` |
|---|---|
| A (Normal) | 0.955 |
| B (Anómalo) | 60.000 |
| **Ratio A→B** | **62.8×** |

`byte_ratio = bytes_toserver / (bytes_toclient + 1)`. En tráfico de inundación (SYN flood, UDP flood) los bytes enviados superan masivamente los recibidos, disparando esta métrica.

**Protocolo por grupo:**

| Protocolo | Grupo A (Normal) | Grupo B (Anómalo) |
|---|---|---|
| TCP | 99.6% | 59.4% |
| UDP | 0.4% | 21.9% |
| ICMP | 0.0% | 18.7% |

El Grupo A usa casi exclusivamente TCP (HTTP/SSH). El Grupo B muestra diversidad de protocolos por los escenarios de flood UDP e ICMP.

**Discriminabilidad estadística:** las 14 features presentan diferencias significativas entre grupos A y B (test Mann-Whitney, p < 0.001 en todas). Las features de volumen (`bytes_*`, `pkts_*`) y las derivadas (`pkt_rate`, `byte_rate`, `byte_ratio`) son las más separables.

### 13.3 Gráficas generadas (`results/eda/`)

| Archivo | Contenido |
|---|---|
| `eda_01_distribuciones.png` | Histogramas log₁₀ de 6 features clave (pkt_rate, byte_rate, duration, byte_ratio, bytes_toserver, pkts_toserver). A=azul, B=rojo, C=verde |
| `eda_02_protocolo.png` | Distribución TCP/UDP/ICMP en barras apiladas por grupo |
| `eda_03_boxplots.png` | Boxplots A vs B en escala log para 6 features (outliers visibles) |
| `eda_04_correlacion.png` | Heatmap Pearson 14×14 para Grupo A y Grupo B (paneles separados) |
| `eda_05_dest_ports.png` | Top-10 puertos destino por grupo (concentración en :80, :22, :53) |
| `eda_06_stats_tabla.png` | Tabla visual de estadísticas descriptivas (mediana, IQR, max) por grupo |

### 13.4 Cómo reproducir el EDA

```bash
# En sensor (192.168.0.110), con el venv activo:
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
python3 scripts/eda_features.py
# Salida: results/eda/eda_0{1..6}_*.png  +  results/eda/eda_stats_completas.txt
# Tiempo estimado: ~3 min (carga 401K flows)
```

> Documentación completa del EDA y justificación metodológica: `docs/respuestas_asesor/05_EDA_FEATURES.md`

---

## 14. Secuencia técnica completa F3

```bash
# ── EN SENSOR (192.168.0.110) ─────────────────────────────────────────────
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto

# Paso 1: entrenar con Grupo A → genera PKL + holdout
python3 scripts/fase3_entrenar.py
# Verificar:
ls -lh models/isolation_forest.pkl models/scaler.pkl models/features.csv
wc -l data/normal_holdout.csv  # → 13,428 (header + 13,427 rows)

# Paso 2: evaluar con holdout + Grupo B → genera metricas_offline.txt
python3 scripts/fase3_evaluar.py
# Verificar:
cat results/metricas_offline.txt
# → AUC=0.8998, tau1=-0.4459, tau2=-0.6027, precision=0.9954, recall=0.9940

# Paso 3: AUC por escenario individual (no modifica metricas_offline)
python3 scripts/auc_por_escenario.py
# Verificar:
cat results/reports/auc_por_escenario.txt

# Paso 4: verificar que el motor lee τ correctamente
sudo systemctl restart ppi-motor.service
sleep 3
grep "tau1\|tau2\|τ1\|τ2" results/motor_decision.log | tail -1
# → debe mostrar τ1=-0.4459 τ2=-0.6027
```

---

## 15. Criterios de éxito (salida de F3)

| Criterio | Comando de verificación | Resultado esperado |
|---|---|---|
| Modelo entrenado | `ls -lh models/isolation_forest.pkl` | Archivo ~2.5 MB, sklearn 1.9.0 |
| Scaler guardado | `ls models/scaler.pkl` | Archivo presente |
| Features registradas | `cat models/features.csv \| tr ',' '\n' \| wc -l` | **14** columnas |
| Holdout generado | `wc -l data/normal_holdout.csv` | **13,428** líneas (header + datos) |
| AUC ≥ 0.85 | `grep 'AUC=' results/metricas_offline.txt` | `AUC=0.8998` |
| τ1 presente | `grep 'tau1=' results/metricas_offline.txt` | `tau1=-0.4459` |
| τ2 presente | `grep 'tau2=' results/metricas_offline.txt` | `tau2=-0.6027` |
| Motor lee τ | `sudo systemctl restart ppi-motor.service && grep "τ1" results/motor_decision.log` | `τ1=-0.4459` |
| sklearn match | `python3 -c "import sklearn; print(sklearn.__version__)"` | `1.9.0` |
| AUC por escenario | `cat results/reports/auc_por_escenario.txt \| grep B2` | `B2.*0.972` |

**F3 se considera COMPLETADA** cuando `metricas_offline.txt` tiene AUC ≥ 0.85 y
el motor arranca leyendo τ1=−0.4459 / τ2=−0.6027. Los archivos `.pkl` y el
`normal_holdout.csv` son prerrequisitos de F4 — sin ellos el motor no puede arrancar.

---

**Siguiente fase:** `F4_especificacion.md` — motor de decisión en tiempo real que
lee `models/*.pkl` y `metricas_offline.txt` para clasificar cada flow de `eve.json`
y aplicar PERMIT / LIMIT / BLOCK via ipset en el servidor.

---

## 16. Experimento comparativo: Autoencoder (AE) en paralelo

Como experimento comparativo, se entrenó un **Autoencoder (MLPRegressor sklearn, 14→8→4→8→14)** usando los mismos datos y filtros que el IF:

| Parámetro | IF (producción) | AE (comparativo) |
|---|---|---|
| n_train | 53,708 flows (Grupo A) | 53,708 flows (Grupo A) |
| Split | 80/20, random_state=42 | 80/20, random_state=42 |
| Scaler | StandardScaler (fit en 80%) | StandardScaler (fit en 80%) |
| Evaluación normal | 13,427 flows holdout | 13,427 flows holdout |
| Evaluación anómala | 598,285 flows Grupo B | 598,285 flows Grupo B |

### Resultados de evaluación (escala de producción completa)

| Métrica | IF | AE |
|---|---|---|
| AUC-ROC | **0.8998** | 0.9103 |
| τ1 (Youden) | −0.4459 | −0.0038 |
| TPR @ τ1 | **99.40%** | 99.42% |
| FPR @ τ1 | **20.47%** | 25.68% |
| τ2 (FPR≤2%) | −0.6027 | −0.0745 |
| TPR @ τ2 (Block) | 18.27% | **54.62%** |
| FPR @ τ2 | 1.99% | 2.00% |
| F1 | **0.9947** | 0.9942 |
| Tiempo entrenamiento | < 10 s | 115.6 s |

**Decisión:** IF permanece como modelo de producción (40 corridas F6 validadas, todos los requisitos cumplidos). El AE queda como experimento comparativo. El Ensemble IF+AE (AND gate) se propone como trabajo futuro (reduce FPR en 49%, +4.8pp F1). Ver `AE_PRODUCCION_DOCUMENTACION.md`, `RESULTADOS_COMPARACION_IF_AE.md`, `DECISION_MODELO_PRODUCCION.md`.
