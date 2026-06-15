# F3 — Secuencia exacta de ejecución: de train/val/test al modelo

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha de ejecución F3:** 2–4 de junio 2026

---

## Punto de partida: lo que llega de F2

Al comenzar F3 ya existen en el sensor estos archivos producidos por F2:

```
/home/m4rk/ppi-surikata-producto/data/
├── raw/                        ← archivos eve.json.gz por corrida
│   ├── 20260602_normal_http_01_eve.json.gz
│   ├── 20260602_normal_ssh_01_eve.json.gz
│   ├── 20260602_normal_transferencia_01_eve.json.gz
│   ├── 20260602_normal_sostenido_01_eve.json.gz
│   ├── 20260602_anom_synflood_01_eve.json.gz
│   ├── 20260602_anom_portscan_01_eve.json.gz
│   ├── 20260602_anom_udpflood_01_eve.json.gz
│   ├── 20260602_anom_icmpflood_01_eve.json.gz
│   ├── 20260602_anom_acceso_01_eve.json.gz
│   └── 20260602_anom_bruteforce_01_eve.json.gz
├── dataset_raw.csv             ← parser.py
├── dataset_labeled.csv         ← etiquetar_limpiar.py
├── dataset_clean.csv           ← etiquetar_limpiar.py
├── train.csv                   ← particionar_estadisticos.py  (263,779 flows)
├── val.csv                     ← particionar_estadisticos.py  ( 56,525 flows)
└── test.csv                    ← particionar_estadisticos.py  ( 56,526 flows)
```

> **Nota importante:** aunque `train.csv`, `val.csv` y `test.csv` ya existen, el script de F3 **no los usa directamente**. Lee los archivos `eve.json.gz` de `data/raw/` para garantizar control total sobre el filtro de IPs y el balanceo por escenario. El motivo se explica en el paso 1.

---

## Secuencia de ejecución — script único: `fase3_isolation_forest.py`

```bash
# Ejecutar desde el sensor como usuario m4rk
cd /home/m4rk/ppi-surikata-producto
python3 scripts/fase3_isolation_forest.py
```

El script imprime en consola cada paso numerado. Lo que hace internamente, en orden:

---

### Paso [1] — Carga de datos desde `data/raw/`

**Script:** líneas ~113–152 de `fase3_isolation_forest.py`

El script abre los `.gz` de corridas 01 de la fecha `20260602`:

**Datos normales** — solo archivos `20260602_normal_*_eve.json.gz`:
- Llama a `parse_flows(archivo, src_filter={'192.168.0.20', '192.168.0.120'})`
- El filtro `src_filter` excluye cualquier flow cuya IP de origen no sea Desktop o Servidor
- Agrupa por escenario (http, ssh, transferencia, sostenido) para balancear
- Resultado: flows del Grupo A únicamente

**Datos anómalos** — solo archivos `20260602_anom_*_eve.json.gz`:
- Llama a `parse_flows(archivo, src_filter=None)` — sin filtro porque floods con `--rand-source` cambian la IP origen
- Después filtra manualmente: descarta cualquier flow de Desktop (que quedó registrado en el eve.json mientras Kali atacaba)
- Resultado: flows del Grupo B únicamente

**Por qué no usar `train.csv` directamente:**  
`train.csv` contiene el 70% cronológico de todos los datos incluyendo corridas 03–10 donde Kali estuvo activo. Si se usara para entrenar, el scaler aprendería como "normal" flows contaminados con tráfico de ataque. El filtro `src_ip ∈ {192.168.0.20, 192.168.0.120}` en la carga directa del `.gz` garantiza 684 flows 100% limpios.

**Salida del paso [1]:**
```
    Flows normales listos : 684
    Flows anómalos listos : 7,412
```

---

### Paso [2] — Escalado con StandardScaler

**Script:** líneas ~155–158

```python
scaler = StandardScaler()
X_n = scaler.fit_transform(df_n)   # aprende μ y σ de los 684 normales, luego escala
X_a = scaler.transform(df_a)       # aplica el mismo μ y σ a los anómalos (NO refit)
```

- `fit_transform` sobre `df_n` (684 flows normales): calcula la **media (μ)** y **desviación estándar (σ)** de cada una de las 14 features, luego aplica `z = (x − μ) / σ`
- `transform` sobre `df_a`: usa los mismos μ y σ aprendidos — los anómalos aparecerán como valores muy alejados de 0

**Lo que produce:**
- `X_n`: matriz numpy de shape `(684, 14)` — datos normales escalados
- `X_a`: matriz numpy de shape `(7412, 14)` — datos anómalos escalados
- Internamente el scaler guarda `scaler.mean_` y `scaler.scale_` (14 valores cada uno)

**Salida del paso [2]:** sin impresión visible, continúa al siguiente paso.

---

### Paso [3] — Entrenamiento del Isolation Forest

**Script:** líneas ~161–169

```python
clf = IsolationForest(
    n_estimators=300,       # 300 árboles de decisión aleatorios
    max_samples='auto',     # por defecto: min(256, n_muestras)
    contamination=0.05,     # espera ~5% de ruido en datos de entrenamiento
    random_state=42,        # reproducibilidad
    n_jobs=-1,              # usa todos los núcleos disponibles
)
clf.fit(X_n)               # entrena SOLO con los 684 flows normales escalados
```

- Construye 300 árboles donde cada árbol:
  1. Toma una submuestra aleatoria de los datos normales
  2. Elige features y puntos de corte al azar
  3. Mide cuántas particiones necesita para aislar cada punto
- Un flow **normal** requiere muchas particiones (está rodeado de vecinos similares)
- Un flow **anómalo** queda aislado en pocas particiones

**Salida del paso [3]:**
```
    Modelo entrenado.
```

---

### Paso [4] — Evaluación con datos de validación

**Script:** líneas ~173–203

```python
pred_n = clf.predict(X_n)   # sobre normales: 1=normal, -1=anomalía
pred_a = clf.predict(X_a)   # sobre anómalos: 1=normal, -1=anomalía
```

Calcula la matriz de confusión y métricas con el umbral binario interno (`clf.offset_`):

| Métrica | Valor v1 (2 jun) |
|---|---|
| Precision | 99.96% |
| Recall | 80.4% |
| F1-Score | 0.8912 |
| FPR | 0.04% |
| Score medio normal | −0.08 (±0.09) |
| Score medio anómalo | −0.77 (±0.14) |
| Umbral binario interno (`offset_`) | −0.5481 |

**Salida del paso [4]:** imprime resultados en consola.

---

### Paso [5] — Guardado de artefactos

**Script:** líneas ~207–210

```python
joblib.dump(clf,    "models/isolation_forest.pkl")   # modelo serializado
joblib.dump(scaler, "models/scaler.pkl")             # scaler serializado
pd.Series(FEATURES).to_csv("models/features.csv")   # lista de 14 features
```

**Archivos producidos:**

```
/home/m4rk/ppi-surikata-producto/models/
├── isolation_forest.pkl   ← modelo Isolation Forest (n=300)
├── scaler.pkl             ← StandardScaler con μ y σ de los 684 normales
└── features.csv           ← lista de 14 features en orden exacto
```

Estos tres archivos son los artefactos que usa `motor_decision.py` en tiempo real (F4/F5).

**Salida del paso [5]:**
```
    Guardado en /home/m4rk/ppi-surikata-producto/models/
```

---

### Paso [6] — Generación de gráficos

**Script:** líneas ~214–280

Produce `results/isolation_forest_resultado.png` con:
- Distribución de scores (normales en azul, anómalos en rojo)
- Curva ROC preliminar con AUC del umbral binario

**Salida del paso [6]:**
```
    Gráfico: /home/m4rk/ppi-surikata-producto/results/isolation_forest_resultado.png
✓ Fase 3 completada.
```

---

## Segundo script: `auc_roc_umbrales.py`

Una vez que `fase3_isolation_forest.py` termina, se ejecuta el segundo script:

```bash
python3 scripts/auc_roc_umbrales.py
```

Este script toma el modelo ya entrenado y encuentra los umbrales óptimos τ1 y τ2:

**Entrada:**
- `models/isolation_forest.pkl` (ya entrenado)
- `models/scaler.pkl` (ya guardado)
- `data/val.csv` — aquí sí usa el CSV de F2: el conjunto de validación con 56,525 flows etiquetados (mixto normal+anómalo)

**Qué hace:**
1. Carga el modelo y el scaler
2. Extrae features de `val.csv` con `extract_features()`
3. Llama a `clf.score_samples(X_val)` → scores continuos (no binarios) para cada flow
4. Barre todos los posibles umbrales y calcula TPR y FPR en cada punto → curva ROC completa
5. Calcula AUC-ROC = 0.9440
6. Encuentra τ1 = −0.4973 (máximo índice de Youden: TPR−FPR)
7. Encuentra τ2 = −0.6873 (primer umbral donde FPR ≤ 2%)

**Salida:**
```
results/umbrales_finales.txt
```
```
tau1 = -0.4973   # PERMIT vs LIMIT
tau2 = -0.6873   # LIMIT vs BLOCK
AUC-ROC = 0.9440
```

---

## Resumen de la secuencia completa

```
F2 produce:
  data/raw/*.json.gz  +  train.csv / val.csv / test.csv
         │
         ▼
[Script 1] fase3_isolation_forest.py
  Lee: data/raw/20260602_normal_*  (corrida 01, src∈{Desktop,Server})
  Lee: data/raw/20260602_anom_*    (corrida 01, sin src Desktop)
         │
  [1] parse_flows() → 684 normales + 7,412 anómalos
  [2] StandardScaler.fit_transform(684 normales) → X_n escalado
  [3] IsolationForest(n=300).fit(X_n) → modelo entrenado
  [4] clf.predict() → métricas con umbral binario (offset=−0.5481)
  [5] joblib.dump → models/isolation_forest.pkl + scaler.pkl + features.csv
  [6] Gráfico → results/isolation_forest_resultado.png
         │
         ▼
[Script 2] auc_roc_umbrales.py
  Lee: models/*.pkl + data/val.csv (56,525 flows etiquetados)
         │
  score_samples() → scores continuos
  ROC curve → AUC = 0.9440
  Youden index → τ1 = −0.4973
  FPR ≤ 2%   → τ2 = −0.6873
         │
         ▼
  Salida: results/umbrales_finales.txt
         │
         ▼
  F4 (motor_decision.py) carga los 3 .pkl + usa τ1 y τ2 en tiempo real
```

---

## Qué artefactos consume cada fase siguiente

| Artefacto producido en F3 | Ruta | Usado en |
|---|---|---|
| `isolation_forest.pkl` | `models/` | F4 `motor_decision.py` — inferencia en tiempo real |
| `scaler.pkl` | `models/` | F4 `motor_decision.py` — escalar cada flow entrante |
| `features.csv` | `models/` | F4 `motor_decision.py` — orden de features al armar vector |
| `umbrales_finales.txt` | `results/` | F4 `motor_decision.py` — leer τ1 y τ2 al arrancar |
| `isolation_forest_resultado.png` | `results/` | F6 — documentación de métricas offline |

---

## Pregunta frecuente de defensa

**¿Por qué no entrenar con `train.csv` que ya tiene 263,779 flows?**

Porque `train.csv` incluye corridas 03–10 donde Kali estaba activo en la red. Esos flows contaminan el conjunto de entrenamiento: el scaler aprendería como "normal" los picos de tráfico de los ataques. El resultado sería un modelo que no detecta anomalías porque las aprendió como normales. Por eso se leen los `.gz` directamente con filtro de IP, seleccionando solo las corridas 01 del Grupo A (100% normales).

**¿Por qué 684 y no más flows para entrenar?**

El análisis de sensibilidad (F3-05) demostró que con N=684 se obtiene la mejor separación de scores (δ = 0.69 entre normal y anómalo). Añadir más flows de corridas posteriores introduce ruido que colapsa esa separación a δ < 0.2, haciendo indetectables los ataques B6 (brute force SSH).
