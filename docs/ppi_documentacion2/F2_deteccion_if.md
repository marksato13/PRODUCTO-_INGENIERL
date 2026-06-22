# F2 — Detección de Anomalías (Isolation Forest)
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Entrenar un modelo no supervisado que aprenda el comportamiento normal de la red y asigne un score de anomalía a cada flujo, derivando umbrales de decisión con base estadística.

---

## ¿Por qué Isolation Forest?

- No requiere etiquetas manuales de ataque — aprende solo del tráfico normal (Grupo A)
- Salida continua (score) permite tres zonas: PERMIT / LIMIT / BLOCK
- Eficiente en inferencia: O(log n) por flujo → latencia < 1ms
- Robusto ante ataques desconocidos: cualquier desviación del baseline es detectada

---

## Scripts (en orden de ejecución)

| Script | Lee | Produce |
|---|---|---|
| `scripts/fase3_entrenar.py` | `data/raw/*_normal_*.gz` | `models/isolation_forest.pkl`, `models/scaler.pkl`, `models/features.csv`, `data/normal_holdout.csv` |
| `scripts/fase3_evaluar.py` | modelos + `normal_holdout.csv` + `data/raw/*_anom_*.gz` | `results/metricas_offline.txt`, `results/auc_roc.png` |
| `scripts/fase3_evaluar.py` | `normal_holdout.csv` + anomalías | deriva τ1/τ2 de la curva ROC → `metricas_offline.txt` |

---

## Lo que hace `fase3_entrenar.py`

```
[1] Lee data/raw/*_normal_*.gz
    → filtra src_ip: 192.168.0.20 / 192.168.0.120 (solo tráfico normal)
[2] Extrae 14 features de cada flujo eve.json
[3] Split 80/20 aleatorio (shuffle=True, random_state=42)
    → 80% → entrenamiento
    → 20% → data/normal_holdout.csv (reservado para evaluación)
[4] StandardScaler ajustado sobre el 80% de entrenamiento
[5] IsolationForest(n_estimators=300, contamination=0.05, random_state=42)
[6] Guarda modelos + holdout
```

> **Split es aleatorio, no cronológico.** Se usa `shuffle=True` porque el IF aprende distribución, no secuencia temporal.

---

## Lo que hace `fase3_evaluar.py`

```
[1] Carga modelos entrenados
[2] Scores sobre normal_holdout.csv → mide FP del modelo
[3] Scores sobre data/raw/*_anom_*.gz → mide TP (detección de ataques reales)
[4] Construye curva ROC con los scores combinados
[5] Deriva τ1 (Youden) y τ2 (FPR≤2%)
[6] Guarda results/metricas_offline.txt ← leído por motor al arrancar
```

---

## Features del modelo (14)

```
pkts_toserver    pkts_toclient    bytes_toserver   bytes_toclient
duration         pkt_rate         byte_rate        pkt_ratio
byte_ratio       avg_pkt_size     is_tcp           is_udp
is_icmp          dest_port
```

Orden exacto preservado en `models/features.csv` — el motor usa este mismo orden.

---

## Umbrales de decisión

| Umbral | Valor | Acción | Criterio |
|---|---|---|---|
| τ1 | −0.4459 | score > τ1 → PERMIT | Youden index (TPR=99.40%, FPR=20.47%) |
| τ2 | −0.6027 | τ2 < score ≤ τ1 → LIMIT | FPR≤2% (TPR=18.27%) |
| — | — | score ≤ τ2 → BLOCK | — |

> FPR=20.47% en τ1 se mitiga con whitelist. Bajar a 5% haría escapar SYN floods (score≈−0.49).

---

## Métricas validadas

| Métrica | Valor |
|---|---|
| AUC-ROC | **0.8998** |
| Precision | **99.54%** |
| Recall | **99.40%** |
| F1-score | **0.9947** |
| Latencia inferencia | < 1ms por flujo |
| sklearn versión | 1.9.0 (sin mismatch) |

---

## Archivos de salida (entrada de F3)

```
/home/m4rk/ppi-surikata-producto/
├── models/
│   ├── isolation_forest.pkl    ← modelo IF serializado
│   ├── scaler.pkl              ← StandardScaler (μ/σ del tráfico normal)
│   └── features.csv           ← 14 features en orden exacto
├── data/
│   └── normal_holdout.csv     ← 20% flujos normales para evaluación
└── results/
    ├── metricas_offline.txt   ← τ1, τ2, AUC, Precision, Recall, F1
    └── auc_roc.png            ← curva ROC con τ1/τ2 marcados
```

El motor (`motor_decision.py`) lee `metricas_offline.txt` al arrancar para cargar τ1 y τ2.

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] AUC-ROC ≥ 0.85
- [x] Precision ≥ 95% | Recall ≥ 95%
- [x] τ1/τ2 derivados de curva ROC con criterio estadístico
- [x] `metricas_offline.txt` generado y leído correctamente por el motor
- [x] Sin mismatch de versión sklearn entre entrenamiento y producción (1.9.0)
- [x] FP sobre holdout normal documentado y aceptable
