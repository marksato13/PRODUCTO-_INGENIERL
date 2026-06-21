# Plan de Implementación — Módulo de Predicción

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-21

---

## Estructura de archivos

```
/home/m4rk/ppi-surikata-producto/
│
├── scripts/
│   ├── motor_decision.py          [EXISTENTE — no se toca]
│   ├── dashboard_web.py           [EXTENDER — panel predictor]
│   ├── enforce.sh                 [EXISTENTE — lo llama el predictor]
│   ├── entrenar_predictor.py      [NUEVO — P1+P2]
│   └── predictor.py               [NUEVO — P3 proceso paralelo]
│
├── models/
│   ├── isolation_forest.pkl       [EXISTENTE]
│   ├── scaler.pkl                 [EXISTENTE]
│   ├── xgb_predictor.pkl          [NUEVO — output de entrenar_predictor.py]
│   └── features_predictor.txt     [NUEVO — lista de features del XGB]
│
├── data/
│   ├── dataset_clean.csv          [EXISTENTE]
│   └── series_temporal_60s.csv    [NUEVO — dataset tiempo para XGB]
│
├── results/
│   ├── motor_decision.log         [EXISTENTE — INPUT del predictor]
│   ├── predictor.log              [NUEVO — OUTPUT del predictor]
│   ├── metricas_predictor.txt     [NUEVO — AUC, precision, recall, lead time]
│   └── graficas_predictor/        [NUEVO — carpeta]
│       ├── roc_xgb_predictor.png  [NUEVO — curva ROC del XGB]
│       ├── shap_xgb_predictor.png [NUEVO — importancia de features SHAP]
│       └── timeline_prediccion.png [NUEVO — línea de tiempo P vs ataques reales]
│
└── config/
    ├── modelo_activo.txt          [EXISTENTE]
    └── systemd/
        ├── ppi-motor.service      [EXISTENTE]
        ├── ppi-dashboard.service  [EXISTENTE]
        └── ppi-predictor.service  [NUEVO — systemd para predictor.py]
```

---

## Qué lee y escribe cada archivo nuevo

### `scripts/entrenar_predictor.py`
- **Lee:** `results/motor_decision.log`
- **Escribe:**
  - `data/series_temporal_60s.csv` — dataset de ventanas agregadas
  - `models/xgb_predictor.pkl` — modelo serializado
  - `models/features_predictor.txt` — lista de features en orden
  - `results/metricas_predictor.txt` — AUC, precision, recall, threshold
  - `results/graficas_predictor/roc_xgb_predictor.png`
  - `results/graficas_predictor/shap_xgb_predictor.png`
  - `results/graficas_predictor/timeline_prediccion.png`
- **Se ejecuta:** una sola vez (offline), tarda ~2-3 min
- **Dependencias:** xgboost, shap, joblib, pandas, matplotlib

---

### `scripts/predictor.py`
- **Lee cada 60s:**
  - `results/motor_decision.log` — últimas N líneas (ventana deslizante)
  - `models/xgb_predictor.pkl` — modelo en memoria desde arranque
  - `models/features_predictor.txt` — orden de features
- **Escribe:**
  - `results/predictor.log` — cada predicción con timestamp y P value
- **Llama (si P ≥ 0.70):**
  - `scripts/enforce.sh <ip_sospechosa> LIMIT 120` — pre-LIMIT preventivo
  - Telegram via `motor_decision.py`'s notify helper (o directo)
- **Formato de línea en predictor.log:**
  ```
  2026-06-21 14:32:00 | P=0.83 | ALERTA | anom_lag1=312 anom_lag2=0 delta=312
  2026-06-21 14:33:00 | P=0.21 | OK     | anom_lag1=0   anom_lag2=0 delta=0
  ```
- **Dependencias:** xgboost, joblib, pandas, numpy (ya instaladas en venv)

---

### `config/systemd/ppi-predictor.service`
```ini
[Unit]
Description=PPI Predictor — XGBoost temporal
After=ppi-motor.service
Requires=ppi-motor.service

[Service]
Type=simple
User=m4rk
WorkingDirectory=/home/m4rk/ppi-surikata-producto
ExecStart=/home/m4rk/ppi-sensor/venv/bin/python3 scripts/predictor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### `scripts/dashboard_web.py` — extensión mínima

Agregar un segundo lector de log que tailee `results/predictor.log` y empuje
eventos SSE de tipo `"predictor"` al browser. El browser recibe:

```json
{
  "type": "predictor",
  "ts": "14:32:00",
  "p": 0.83,
  "nivel": "ALERTA",
  "top_feature": "anom_lag1=312"
}
```

Panel nuevo en el sidebar:
```
┌─────────────────────────────┐
│  PREDICTOR XGBoost          │
│                             │
│  P(ataque_60s) = 83%  🔴   │  ← gauge color: verde<40 / amarillo<70 / rojo≥70
│  Última: 14:32:00           │
│                             │
│  Historial (últimas 5):     │
│  14:32 83% ALERTA           │
│  14:31 21% OK               │
│  14:30 18% OK               │
│  14:29 76% ALERTA ✓         │  ← ✓ = hubo BLOCK después (confirmado)
│  14:28 14% OK               │
└─────────────────────────────┘
```

---

## Flujo de integración completo

```
[Tráfico de red]
      │
      ▼
[Suricata → eve.json]
      │
      ├──────────────────────────────────────────────────────►
      │                                                       │
      ▼                                                       │ (cada 60s lee log)
[motor_decision.py]                                  [predictor.py]
  - IF.score() por flujo                               - parsea últimas ventanas
  - BLOCK/LIMIT/PERMIT                                 - construye feat_t
  - escribe motor_decision.log                         - XGB.predict_proba()
      │                                                       │
      ▼                                                       ▼
[motor_decision.log] ──────────────────────────► [predictor.log]
      │                                                       │
      │                            ┌──────────────────────────┤
      │                            │  P ≥ 0.70?               │
      │                            ▼                          │
      │                    [enforce.sh LIMIT 120s]            │
      │                    [Telegram ⚠️ PREDICTIVA]           │
      │                                                       │
      ▼                                                       ▼
[dashboard_web.py — puerto 8080]
  - lector 1: motor_decision.log → eventos BLOCK/LIMIT/stats
  - lector 2: predictor.log → eventos predictor (P, nivel)
      │
      ▼ SSE push al browser
[Browser http://192.168.0.110:8080]
  - Panel existente: flows, bloqueados, latencia, alertas
  - Panel NUEVO: gauge P(ataque), historial predictivo
```

---

## Orden de implementación

| Paso | Archivo | Acción | Tiempo est. |
|---|---|---|---|
| 1 | `entrenar_predictor.py` | Crear y ejecutar → verificar AUC > 0.70 | 3-4h |
| 2 | `predictor.py` | Crear proceso paralelo, probar con motor activo | 2-3h |
| 3 | `ppi-predictor.service` | Crear e instalar, verificar arranque automático | 30min |
| 4 | `dashboard_web.py` | Agregar lector predictor.log + panel HTML/JS | 2-3h |
| 5 | Corridas de validación | 5 con ataque + 5 sin ataque → medir lead time | 2-3h |
| 6 | `generar_informe_pdf.py` | Agregar sección predictor con métricas y gráficas | 1-2h |

**Total estimado: 11-16 horas (2 días a full)**

---

## Métricas que el módulo predictivo aportará al informe

| Métrica | Cómo se obtiene |
|---|---|
| AUC-ROC predictor | `entrenar_predictor.py` → curva ROC test set |
| Precision alertas | TP_alertas / (TP+FP) en corridas de validación |
| Recall predictivo | TP_alertas / total_ataques en corridas de validación |
| **Lead time predictivo** | Δt(alerta P≥0.70) − Δt(primer BLOCK del IF) |
| Falsos despertares | FP_alertas en las 5 corridas sin ataque |
| Top feature predictora | SHAP plot → qué variable más contribuye |

---

## Restricciones de diseño

- `motor_decision.py` y `ppi-motor.service` → **no se modifican**
- La latencia del motor (P95=34.8ms) → **no se ve afectada** (predictor corre en proceso separado)
- Las 40 corridas F6 ya validadas → **siguen siendo válidas** (no se re-corren)
- El predictor usa solo lo que el motor ya produce → **sin nueva captura de datos**
- Corridas de validación del predictor → **10 adicionales** (no reemplazan las F6)

---

*Ruta: `docs/ppi_documentacion/prediccion_futura/PLAN_IMPLEMENTACION.md`*  
*Relacionado: `TIPOS_PREDICCION.md`, `ANALISIS_PREDICCION.md`*
