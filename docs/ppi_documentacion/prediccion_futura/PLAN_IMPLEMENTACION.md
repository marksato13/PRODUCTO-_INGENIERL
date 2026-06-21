# Plan de Implementación por Fases — Módulo de Predicción

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-21  
**Tiempo total estimado:** 11–16 horas (2 días a full)

---

## Estructura de archivos completa

```
/home/m4rk/ppi-surikata-producto/
│
├── scripts/
│   ├── motor_decision.py              [EXISTENTE — no se toca]
│   ├── dashboard_web.py               [EXTENDER en Fase 5]
│   ├── enforce.sh                     [EXISTENTE — lo invoca predictor]
│   ├── entrenar_predictor.py          [NUEVO — Fases 1 y 2]
│   └── predictor.py                   [NUEVO — Fase 3]
│
├── models/
│   ├── isolation_forest.pkl           [EXISTENTE]
│   ├── scaler.pkl                     [EXISTENTE]
│   ├── predictor_modelo.pkl           [NUEVO — modelo ganador serializado]
│   ├── predictor_tipo.txt             [NUEVO — "XGBoost" o "RandomForest"]
│   └── features_predictor.txt         [NUEVO — lista de features en orden]
│
├── data/
│   └── series_temporal_60s.csv        [NUEVO — dataset tiempo extraído]
│
├── results/
│   ├── motor_decision.log             [EXISTENTE — input del predictor]
│   ├── predictor.log                  [NUEVO — output del predictor en vivo]
│   ├── comparacion_predictores.txt    [NUEVO — XGBoost vs RF vs ARIMA]
│   ├── metricas_predictor.txt         [NUEVO — métricas del modelo en producción]
│   └── graficas_predictor/
│       ├── roc_comparacion.png        [NUEVO — ROC los 3 modelos superpuestas]
│       ├── shap_predictor.png         [NUEVO — SHAP feature importance]
│       └── timeline_prediccion.png    [NUEVO — P(ataque) vs BLOCKs reales]
│
└── config/systemd/
    ├── ppi-motor.service              [EXISTENTE]
    ├── ppi-dashboard.service          [EXISTENTE]
    └── ppi-predictor.service          [NUEVO — Fase 4]
```

---

## Fase 0 — Extracción del dataset temporal
**Tiempo: 1–2 horas | Archivos: `data/series_temporal_60s.csv`**

### Qué se hace
Parsear `results/motor_decision.log` (1.17M líneas, 11,516 estadísticas) y
convertirlo en ventanas de 60 segundos con features de lag.

### Cómo validar que salió bien
```bash
python3 scripts/entrenar_predictor.py --solo-dataset
# Debe imprimir:
# Ventanas totales : ~3,455
# Con ataque (y=1): ~150–250   (Δbloqueados_{t+1} > 0)
# Sin ataque (y=0): ~3,200–3,300
# Ratio desbalance : ~1:14 a 1:20
# Archivo guardado : data/series_temporal_60s.csv
```

### Criterio de éxito
- Ventanas totales ≥ 2,000
- Positivos (ataques) ≥ 100
- No hay NaN en features de lag (el script hace `dropna()`)

### Si algo falla
El log tiene dos formatos distintos de línea `Estadísticas` (antes y después
de cierta fecha). El regex debe manejar ambos. Revisar con:
```bash
grep 'Estadísticas' results/motor_decision.log | head -5
grep 'Estadísticas' results/motor_decision.log | tail -5
```

---

## Fase 1 — Comparación de modelos (ARIMA vs RF vs XGBoost)
**Tiempo: 2–3 horas | Archivos: `results/comparacion_predictores.txt`, `results/graficas_predictor/roc_comparacion.png`**

### Por qué comparar tres modelos
No elegir XGBoost a ciegas. Con los datos reales del proyecto, dejar que
las métricas decidan. ARIMA actúa como **baseline estadístico** — si XGBoost
no lo supera claramente, no vale la pena la complejidad adicional.

### Split temporal (obligatorio — nunca aleatorio en series de tiempo)
```
Train : ventanas 02-jun → 14-jun  (~80%, ≈2,764 filas)
Test  : ventanas 15-jun → 19-jun  (~20%, ≈691  filas)
```
El test debe ser siempre el período más reciente, no una muestra aleatoria.
Mezclar pasado y futuro en series temporales infla artificialmente el AUC.

### Los tres modelos a comparar

**Modelo A — ARIMA (baseline)**
```python
from statsmodels.tsa.arima.model import ARIMA

# Serie univariada: tasa de anomalías por ventana 60s
serie_train = df_train['Δanom']
modelo_arima = ARIMA(serie_train, order=(3, 1, 2)).fit()
forecast = modelo_arima.forecast(steps=len(df_test))
# Convertir forecast a probabilidad: sigmoid((forecast - mean) / std)
```
- Solo usa `Δanom` — ignora http_abuse, hora, lags cruzados
- Referencia mínima: si los otros no lo superan, usar ARIMA

**Modelo B — Random Forest**
```python
from sklearn.ensemble import RandomForestClassifier

clf_rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=8,
    class_weight='balanced',   # maneja desbalance 1:16 automáticamente
    random_state=42,
    n_jobs=-1
)
clf_rf.fit(X_train, y_train)
```

**Modelo C — XGBoost**
```python
from xgboost import XGBClassifier

ratio = (y_train == 0).sum() / (y_train == 1).sum()
clf_xgb = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    scale_pos_weight=ratio,    # control fino del desbalance
    subsample=0.8,
    colsample_bytree=0.8,
    early_stopping_rounds=20,  # para automáticamente
    eval_metric='auc',
    random_state=42,
    verbosity=0
)
clf_xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)])
```

### Métricas de comparación (sobre el test set)

| Métrica | Por qué importa |
|---|---|
| **AUC-ROC** | Discriminación global independiente del umbral |
| **Precision@τ** | De las veces que alerta, cuántas son reales |
| **Recall@τ** | De los ataques reales, cuántos anticipa |
| **F1@τ** | Balance precision/recall |
| Tiempo de entrenamiento | Relevante para re-entrenamiento futuro |
| Tamaño modelo (KB) | Relevante para el sensor (RAM limitada) |

Umbral τ: el que maximiza F1 en el test set (no en el train).

### Output de esta fase
```
results/comparacion_predictores.txt
────────────────────────────────────────────────────────
Modelo       AUC-ROC  Precision  Recall   F1    τ
────────────────────────────────────────────────────────
ARIMA        0.XX     0.XX       0.XX     0.XX  —
RandomForest 0.XX     0.XX       0.XX     0.XX  0.XX
XGBoost      0.XX     0.XX       0.XX     0.XX  0.XX
────────────────────────────────────────────────────────
GANADOR: [modelo] con AUC=[valor]
```

---

## Fase 2 — Decisión del modelo de producción
**Tiempo: 30 minutos | Archivos: `models/predictor_modelo.pkl`, `models/predictor_tipo.txt`, `models/features_predictor.txt`, `results/metricas_predictor.txt`, `results/graficas_predictor/shap_predictor.png`**

### Criterio de decisión

```
¿XGBoost AUC > RF AUC por más de 2pp?  → XGBoost gana
¿Diferencia ≤ 2pp?                      → RF gana (más simple, más robusto)
¿Ambos AUC < ARIMA + 5pp?              → revisar features, no implementar
```

El modelo que no gane se documenta en `comparacion_predictores.txt`
como experimento — igual que AE vs IF en el experimento comparativo.

### Serialización del ganador
```python
import joblib

# El archivo se llama siempre igual — predictor.py no sabe ni le importa
# qué modelo ganó, solo carga el pkl
joblib.dump(clf_ganador, 'models/predictor_modelo.pkl')

# Registro del tipo para el informe
with open('models/predictor_tipo.txt', 'w') as f:
    f.write('XGBoost')   # o 'RandomForest'

# Features en orden exacto (predictor.py las lee para construir el vector)
with open('models/features_predictor.txt', 'w') as f:
    f.write('\n'.join(FEATURES))

# Métricas finales
with open('results/metricas_predictor.txt', 'w') as f:
    f.write(f"Modelo: {tipo}\n")
    f.write(f"AUC-ROC: {auc:.4f}\n")
    f.write(f"Precision@τ: {prec:.4f}\n")
    f.write(f"Recall@τ:    {rec:.4f}\n")
    f.write(f"F1@τ:        {f1:.4f}\n")
    f.write(f"Umbral τ:    {tau:.4f}\n")
    f.write(f"Train: 02-jun → 14-jun ({len(X_train)} ventanas)\n")
    f.write(f"Test:  15-jun → 19-jun ({len(X_test)} ventanas)\n")
```

### Gráficas de esta fase
- `roc_comparacion.png` — tres curvas ROC superpuestas (ARIMA / RF / XGBoost)
- `shap_predictor.png` — SHAP del modelo ganador (qué feature más predice)
- `timeline_prediccion.png` — línea de tiempo: P(ataque) vs BLOCKs reales del IF

---

## Fase 3 — Proceso predictor en producción (`predictor.py`)
**Tiempo: 2–3 horas | Archivos: `scripts/predictor.py`, `results/predictor.log`**

### Qué hace
Corre en paralelo al motor. Cada 60 segundos:
1. Lee las últimas N líneas de `motor_decision.log`
2. Extrae la ventana actual y construye el vector de features
3. Carga `predictor_modelo.pkl` y llama `predict_proba()`
4. Según el resultado, actúa:

```
P < 0.40          → log INFO "OK"           (silencio en Telegram)
0.40 ≤ P < 0.70   → log INFO "RIESGO-MEDIO" (visible en dashboard, no Telegram)
P ≥ 0.70          → log WARNING "ALERTA"    (Telegram + enforce.sh LIMIT)
```

### Formato de `predictor.log`
```
2026-06-21 14:32:00 | INFO    | OK          | P=0.21 | top=anom_lag1=0
2026-06-21 14:33:00 | INFO    | RIESGO-MEDIO| P=0.55 | top=anom_lag2=47
2026-06-21 14:34:00 | WARNING | ALERTA      | P=0.83 | top=anom_lag1=312
```

### Verificación
```bash
# Arrancar manualmente
python3 scripts/predictor.py

# En otra terminal, verificar que escribe cada 60s
tail -f results/predictor.log

# Disparar un ataque desde Kali y ver si P sube
ssh m4rk@192.168.0.100 "hping3 -S -p 80 -i u3000 192.168.0.120 &"
# → En ~60-120s debe aparecer WARNING ALERTA en predictor.log
```

---

## Fase 4 — Servicio systemd (`ppi-predictor.service`)
**Tiempo: 30 minutos | Archivos: `config/systemd/ppi-predictor.service`**

### Contenido del servicio
```ini
[Unit]
Description=PPI Predictor — clasificacion binaria temporal
After=ppi-motor.service
Requires=ppi-motor.service

[Service]
Type=simple
User=m4rk
WorkingDirectory=/home/m4rk/ppi-surikata-producto
ExecStart=/home/m4rk/ppi-sensor/venv/bin/python3 scripts/predictor.py
Restart=always
RestartSec=10
StandardOutput=append:/home/m4rk/ppi-surikata-producto/results/predictor.log
StandardError=append:/home/m4rk/ppi-surikata-producto/results/predictor.log

[Install]
WantedBy=multi-user.target
```

### Instalación
```bash
sudo cp config/systemd/ppi-predictor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ppi-predictor.service
sudo systemctl start ppi-predictor.service
sudo systemctl status ppi-predictor.service
```

### Verificación
```bash
# Los tres servicios deben estar activos simultáneamente
sudo systemctl status ppi-motor.service
sudo systemctl status ppi-predictor.service
sudo systemctl status ppi-dashboard.service
```

---

## Fase 5 — Visibilidad en dashboard (`dashboard_web.py`)
**Tiempo: 2–3 horas | Archivos: `scripts/dashboard_web.py` (extensión)**

### Qué agregar

**1. Segundo lector de log** (hilo paralelo al existente)
```python
PREDICTOR_LOG = BASE + '/results/predictor.log'

PRED_RE = re.compile(
    r'(\d{2}:\d{2}:\d{2}) \| \w+ \| (\w[\w-]*) \| P=([\d.]+)'
)

def predictor_reader():
    pred_state = {"p": 0.0, "nivel": "OK", "ts": "—", "historial": []}
    while True:
        if not os.path.exists(PREDICTOR_LOG):
            time.sleep(5); continue
        with open(PREDICTOR_LOG, "r", errors="ignore") as f:
            f.seek(0, 2)
            while True:
                ln = f.readline()
                if ln:
                    m = PRED_RE.search(ln)
                    if m:
                        ev = {"ts": m.group(1),
                              "nivel": m.group(2),
                              "p": float(m.group(3))}
                        pred_state.update({"p": ev["p"],
                                           "nivel": ev["nivel"],
                                           "ts": ev["ts"]})
                        pred_state["historial"] = \
                            ([ev] + pred_state["historial"])[:10]
                        push_sse({"type": "predictor", **ev})
                else:
                    time.sleep(0.5)
```

**2. Panel HTML en el sidebar**
```html
<!-- Insertar junto al panel de alertas existente -->
<div class="sb-card" id="panel-predictor">
  <div class="sb-title">PREDICTOR XGBoost</div>

  <!-- Gauge de probabilidad -->
  <div style="text-align:center; margin:12px 0">
    <span id="pred-valor" style="font-size:2em; font-weight:700">—%</span>
    <div id="pred-barra" style="height:8px; border-radius:4px;
         background:#2a2a2a; margin:6px 0">
      <div id="pred-fill" style="height:100%; border-radius:4px;
           width:0%; background:var(--green); transition:width .5s"></div>
    </div>
    <span id="pred-nivel" class="mono" style="font-size:.85em">OK</span>
    <span id="pred-ts" class="mono" style="font-size:.75em; opacity:.6"> —</span>
  </div>

  <!-- Historial -->
  <div style="font-size:.8em; opacity:.7; margin-bottom:4px">Últimas alertas</div>
  <div id="pred-historial" style="font-size:.78em; font-family:monospace"></div>
</div>
```

**3. Handler SSE en JavaScript**
```javascript
// Dentro de la función que procesa eventos SSE existente
case 'predictor':
  const p = Math.round(ev.p * 100);
  document.getElementById('pred-valor').textContent = p + '%';
  document.getElementById('pred-ts').textContent = ' ' + ev.ts;
  document.getElementById('pred-nivel').textContent = ev.nivel;

  const fill = document.getElementById('pred-fill');
  fill.style.width = p + '%';
  fill.style.background = p >= 70 ? 'var(--red)'
                        : p >= 40 ? 'var(--yellow)'
                        : 'var(--green)';

  // Agregar al historial
  const hist = document.getElementById('pred-historial');
  const color = p >= 70 ? 'var(--red)' : p >= 40 ? 'var(--yellow)' : 'var(--green)';
  hist.innerHTML = `<div><span style="color:${color}">${ev.ts} ${p}% ${ev.nivel}</span></div>`
                 + hist.innerHTML.split('<div>').slice(0,6).join('<div>');
  break;
```

### Aspecto final del panel en el browser
```
┌──────────────────────────────┐
│  PREDICTOR XGBoost           │
│                              │
│         83%                  │
│  ████████████████░░░░  🔴    │
│         ALERTA  14:34        │
│                              │
│  Últimas alertas             │
│  14:34  83%  ALERTA          │
│  14:33  55%  RIESGO-MEDIO    │
│  14:32  21%  OK              │
│  14:20  76%  ALERTA          │
│  14:19  18%  OK              │
└──────────────────────────────┘
```

---

## Fase 6 — Corridas de validación del predictor
**Tiempo: 2–3 horas | Archivos: ninguno nuevo — mide sobre los existentes**

### 10 corridas adicionales (no reemplazan las F6)

| Corridas | Escenario | Qué se mide |
|---|---|---|
| 5 con ataque | SYN Flood o HTTP Abuse desde Kali | Lead time: Δt(ALERTA predictor) − Δt(BLOCK del IF) |
| 5 sin ataque | Solo tráfico normal desde Desktop | Falsos despertares: ¿el predictor alerta sin ataque? |

### Métrica clave: lead time predictivo
```
lead_time = t(WARNING predictor.log) - t(WARNING motor_decision.log)

Si lead_time > 0  → el predictor anticipó al IF  ← resultado esperado
Si lead_time < 0  → el predictor fue más lento que el IF ← resultado malo
Si lead_time = 0  → predictor y motor detectaron al mismo tiempo
```

Anotar en bitácora igual que las corridas F6.

---

## Fase 7 — Actualización del informe PDF
**Tiempo: 1–2 horas | Archivos: `scripts/generar_informe_pdf.py`**

### Sección nueva en el PDF
Agregar entre §9 Experimento Comparativo y §10 F6 Corridas:

**§9b — Módulo de Predicción Temporal**
- Justificación: Tipo 1 clasificación binaria temporal
- Comparación ARIMA vs RF vs XGBoost (tabla + `roc_comparacion.png`)
- Modelo de producción seleccionado + SHAP (`shap_predictor.png`)
- Arquitectura integrada (texto + diagrama)
- Métricas de validación: AUC, precision, recall, lead time
- `timeline_prediccion.png`

---

## Resumen ejecutivo

| Fase | Qué produce | Tiempo |
|---|---|---|
| 0 — Dataset | `series_temporal_60s.csv` | 1–2h |
| 1 — Comparación | `comparacion_predictores.txt` + `roc_comparacion.png` | 2–3h |
| 2 — Decisión | `predictor_modelo.pkl` + `metricas_predictor.txt` + SHAP | 30min |
| 3 — Predictor vivo | `predictor.py` + `predictor.log` | 2–3h |
| 4 — Servicio | `ppi-predictor.service` activo | 30min |
| 5 — Dashboard | Panel gauge + historial en :8080 | 2–3h |
| 6 — Validación | Lead time medido en 10 corridas | 2–3h |
| 7 — PDF | Sección §9b con métricas y gráficas | 1–2h |
| **TOTAL** | | **11–16h** |

---

*Ruta: `docs/ppi_documentacion/prediccion_futura/PLAN_IMPLEMENTACION.md`*  
*Relacionado: `TIPOS_PREDICCION.md` — justificación Tipo 1 | `ANALISIS_PREDICCION.md` — arquitectura detallada*
