# F3 — Especificación Técnica: Modelado Offline

## 1. Objetivo

Entrenar el modelo Isolation Forest con tráfico normal puro (Grupo A) y derivar los
umbrales de decisión τ1/τ2 mediante análisis de la curva ROC sobre datos nunca vistos
por el modelo. Producir `metricas_offline.txt` como **fuente única de verdad** para
AUC, τ1, τ2, Precision, Recall y F1.

> **Nota metodológica:** F3 lee directamente los archivos `.gz` de captura. No existe
> ningún CSV intermedio (dataset_raw, dataset_clean, train, val, test). Isolation Forest
> es no supervisado — solo necesita datos normales para aprender, no etiquetas ni
> partición de validación.

---

## 2. Entradas

| Entrada | Ruta | Descripción |
|---|---|---|
| Capturas normales | `data/raw/*_normal_*.gz` | 28 archivos Grupo A — Kali apagada |
| Capturas anómalas | `data/raw/*_anom_*.gz` | 13 archivos Grupo B — Desktop quieto |
| Capturas mixtas | `data/raw/*_mixto_*.gz` | 6 archivos Grupo C — ambos activos |
| Modelos entrenados | `models/isolation_forest.pkl`, `models/scaler.pkl` | Solo para `fase3_evaluar.py` y `auc_por_escenario.py` |

Los globs son **date-agnostic** (`*_normal_*` no `20260602_normal_*`) — funcionan
en cualquier fecha de captura.

---

## 3. Salidas

| Salida | Ruta | Generado por |
|---|---|---|
| Modelo IF | `models/isolation_forest.pkl` | `fase3_entrenar.py` |
| Scaler | `models/scaler.pkl` | `fase3_entrenar.py` |
| Lista de features | `models/features.csv` | `fase3_entrenar.py` |
| Holdout normal | `data/normal_holdout.csv` | `fase3_entrenar.py` (20% nunca visto) |
| Métricas canónicas | `results/metricas_offline.txt` | `fase3_evaluar.py` |
| Curva ROC | `results/auc_roc.png` | `fase3_evaluar.py` |
| AUC por escenario | `results/reports/auc_por_escenario.txt` | `auc_por_escenario.py` |

---

## 4. Scripts del pipeline F3

### 4.1 `scripts/fase3_entrenar.py`

**Entrada:** `data/raw/*_normal_*.gz` (Grupo A)  
**Salida:** `isolation_forest.pkl`, `scaler.pkl`, `features.csv`, `normal_holdout.csv`

Proceso:
1. Lee todos los `.gz` con glob `*_normal_*.gz` — extrae eventos `event_type=flow`
2. Filtra por `src_ip in NORMAL_IPS` (`192.168.0.20`, `192.168.0.120`)
3. Extrae las 14 features por flow
4. **Split 80/20 aleatorio** (`train_test_split`, `random_state=42`, `shuffle=True`)
   - 80% → `X_train` — entrenamiento del IF
   - 20% → `normal_holdout.csv` — nunca visto por el modelo, usado en evaluación
5. `StandardScaler.fit_transform(X_train)` — ajuste SOLO sobre el 80%
6. `IsolationForest(n_estimators=300, contamination=0.05, random_state=42).fit(X_train_scaled)`
7. Guarda `.pkl` con `joblib.dump`

```bash
# En sensor
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto
python3 scripts/fase3_entrenar.py
```

**Por qué 80/20 y no 70/15/15:**  
El split 70/15/15 es una convención de modelos supervisados (train / validación / test).
IF no tiene hiperparámetros que ajustar por validación — `n_estimators=300` y
`contamination=0.05` son decisiones de diseño. Solo se necesita un holdout de referencia
para construir la curva ROC en `fase3_evaluar.py`.

---

### 4.2 `scripts/fase3_evaluar.py`

**Entrada:** `data/normal_holdout.csv` + `data/raw/*_anom_*.gz` + modelos `.pkl`  
**Salida:** `results/metricas_offline.txt`, `results/auc_roc.png`

Proceso:
1. Carga `isolation_forest.pkl` y `scaler.pkl`
2. Score sobre `normal_holdout.csv` (20% normal nunca visto) → scores normales
3. Lee `*_anom_*.gz` (Grupo B) → extrae features → score → scores anómalos
4. Construye curva ROC (score como variable continua, label como clase)
5. Calcula AUC-ROC
6. Deriva τ1: punto de máximo índice de Youden (`TPR − FPR`)
7. Deriva τ2: máximo TPR donde `FPR ≤ 2%`
8. Escribe `metricas_offline.txt` — **única fuente de verdad**
9. Genera `auc_roc.png`

```bash
python3 scripts/fase3_evaluar.py
```

---

### 4.3 `scripts/auc_por_escenario.py`

**Entrada:** `data/raw/*_anom_*.gz` + `data/raw/*_mixto_*.gz` + modelos `.pkl`  
**Salida:** `results/reports/auc_por_escenario.txt`

Calcula AUC individual para cada escenario B1-B6 y C1-C3. No modifica
`metricas_offline.txt`. Útil para identificar qué tipos de ataque son más difíciles
de detectar.

```bash
python3 scripts/auc_por_escenario.py
```

---

## 5. Las 14 features del modelo

Extraídas de cada evento `flow` en los archivos `.gz`:

| # | Feature | Descripción | Tipo |
|---|---|---|---|
| 1 | `pkts_toserver` | Paquetes enviados al servidor | int |
| 2 | `pkts_toclient` | Paquetes recibidos del servidor | int |
| 3 | `bytes_toserver` | Bytes enviados al servidor | int |
| 4 | `bytes_toclient` | Bytes recibidos del servidor | int |
| 5 | `duration` | Duración del flow en segundos | float |
| 6 | `pkt_rate` | (pkts_to + pkts_from) / duration | float |
| 7 | `byte_rate` | (bytes_to + bytes_from) / duration | float |
| 8 | `pkt_ratio` | pkts_toserver / pkts_toclient | float |
| 9 | `byte_ratio` | bytes_toserver / bytes_toclient | float |
| 10 | `avg_pkt_size` | bytes_total / pkts_total | float |
| 11 | `is_tcp` | 1 si proto == TCP | int |
| 12 | `is_udp` | 1 si proto == UDP | int |
| 13 | `is_icmp` | 1 si proto == ICMP | int |
| 14 | `dest_port` | Puerto de destino | int |

---

## 6. Hiperparámetros del modelo

| Parámetro | Valor | Justificación |
|---|---|---|
| `n_estimators` | 300 | Validado por análisis de sensibilidad — AUC estable a partir de n=200 |
| `contamination` | 0.05 | Prior conservador: ~5% de anomalías esperadas en red universitaria |
| `random_state` | 42 | Reproducibilidad garantizada |
| `max_samples` | `'auto'` | min(256, n_samples) — valor por defecto de sklearn |
| sklearn | 1.9.0 | Versión fijada en venv — sin mismatch con el `.pkl` guardado |

---

## 7. Umbrales derivados (fuente canónica: `results/metricas_offline.txt`)

| Umbral | Valor | Criterio | TPR | FPR |
|---|---|---|---|---|
| τ1 (PERMIT/LIMIT) | **−0.4459** | Youden: `argmax(TPR − FPR)` | 99.40% | 20.47% |
| τ2 (LIMIT/BLOCK) | **−0.6027** | `max TPR donde FPR ≤ 2%` | 18.27% | 2.00% |

**Por qué FPR=20.47% en τ1 es aceptable:**  
Reducir FPR a ≤5% requeriría τ1=−0.5547. Los flows de SYN Flood obtienen score≈−0.49,
que es mayor que −0.5547 → serían clasificados como PERMIT (no detectados).
El índice de Youden es el umbral metodológicamente correcto. La whitelist mitiga los
falsos positivos de IPs conocidas.

---

## 8. Métricas del modelo (resultado final — 2026-06-16)

| Métrica | Valor | Requisito |
|---|---|---|
| AUC-ROC | **0.8998** | ≥ 0.85 ✓ |
| Precision (en τ1) | **99.54%** | ≥ 95% ✓ |
| Recall (en τ1) | **99.40%** | ≥ 95% ✓ |
| F1-Score | **0.9947** | ≥ 0.90 ✓ |
| Score medio normal | −0.3965 ± 0.0753 | — |
| Score medio anómalo | −0.5420 ± 0.0900 | — |
| Delta separación | 0.1454 | — |
| AUC más bajo por escenario | B1 SYN Flood: 0.8302 | — |
| AUC más alto por escenario | B2 Port Scan: 0.9726 | — |

**Datos de entrenamiento:**
- `n_train_normal`: 53,708 flows (80% del Grupo A)
- `n_holdout_normal`: 13,427 flows (20% reservado)
- `n_anom_eval`: 598,285 flows (Grupo B completo)

---

## 9. Secuencia técnica completa F3

```bash
# En sensor (192.168.0.110)
source /home/m4rk/ppi-sensor/venv/bin/activate
cd /home/m4rk/ppi-surikata-producto

# Paso 1: entrenar con Grupo A → genera PKL + holdout
python3 scripts/fase3_entrenar.py
# Salida esperada:
#   Flows normales cargados: 67,135
#   Split: 53,708 train / 13,427 holdout
#   Modelo guardado: models/isolation_forest.pkl

# Paso 2: evaluar con holdout + Grupo B → genera metricas_offline.txt
python3 scripts/fase3_evaluar.py
# Salida esperada:
#   AUC-ROC: 0.8998
#   tau1: -0.4459  (Youden)
#   tau2: -0.6027  (FPR<=2%)
#   Escrito: results/metricas_offline.txt

# Paso 3: AUC por escenario individual (opcional, no modifica metricas_offline)
python3 scripts/auc_por_escenario.py

# Verificar resultado canónico
cat results/metricas_offline.txt
```

---

## 10. Criterios de éxito (salida de F3)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| Modelo entrenado | `ls -lh models/isolation_forest.pkl` | Archivo ~2.5MB presente |
| Scaler guardado | `ls models/scaler.pkl` | Archivo presente |
| Features registradas | `cat models/features.csv` | 14 nombres de columnas |
| Holdout generado | `wc -l data/normal_holdout.csv` | ~13,428 líneas |
| Métricas escritas | `cat results/metricas_offline.txt` | AUC, tau1, tau2 presentes |
| AUC ≥ 0.85 | `grep AUC results/metricas_offline.txt` | ≥ 0.85 |
| Motor puede leer τ | `sudo systemctl restart ppi-motor.service && grep "τ1=" results/motor_decision.log` | τ1=−0.4459 |

**F3 se considera COMPLETADA** cuando `metricas_offline.txt` existe con AUC ≥ 0.85
y el motor arranca leyendo τ1/τ2 correctamente de ese archivo.
