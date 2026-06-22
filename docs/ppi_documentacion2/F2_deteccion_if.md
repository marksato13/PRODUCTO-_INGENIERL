# F2 — Detección de Anomalías (Isolation Forest)
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Entrenar un modelo no supervisado que aprenda el comportamiento normal de la red y clasifique cada flujo nuevo como normal o anómalo, sin necesidad de etiquetas previas.

---

## ¿Por qué Isolation Forest?

- No requiere etiquetas manuales de ataque — aprende solo del tráfico normal
- Eficiente: O(n log n) en entrenamiento, O(log n) por flujo en inferencia
- Robusto ante ataques desconocidos (zero-day): cualquier desviación del baseline es detectada
- Salida continua (score) permite definir zonas PERMIT / LIMIT / BLOCK con umbrales ajustables

---

## Componentes

| Script | Función |
|---|---|
| `scripts/fase3_isolation_forest.py` | Entrena IF n=300, guarda .pkl |
| `scripts/auc_roc_umbrales.py` | Deriva τ1/τ2 de curva ROC |
| `models/isolation_forest.pkl` | Modelo serializado |
| `models/scaler.pkl` | Normalizador StandardScaler |
| `models/features.csv` | Lista de 14 features en orden |
| `results/metricas_offline.txt` | AUC, τ1, τ2 — leídos por el motor al arrancar |

---

## Umbrales de decisión

| Umbral | Valor | Acción | Criterio |
|---|---|---|---|
| τ1 | −0.4459 | score > τ1 → PERMIT | Youden index (TPR=99.40%, FPR=20.47%) |
| τ2 | −0.6027 | τ2 < score ≤ τ1 → LIMIT | FPR≤2% (TPR=18.27%) |
| — | — | score ≤ τ2 → BLOCK | — |

> FPR=20.47% se mitiga con whitelist. Bajar a FPR=5% haría escapar SYN floods (score≈−0.49).

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

## Distribución de scores por origen (datos reales)

| IP origen | Score típico | Zona |
|---|---|---|
| 192.168.0.20 (Desktop) | −0.02 a +0.10 | PERMIT |
| 192.168.0.100 (Kali — SYN flood) | −0.6207 | BLOCK directo |
| 192.168.0.100 (Kali — HTTP abuse) | −0.49 a −0.55 | LIMIT → BLOCK |
| 192.168.0.100 (Kali — port scan) | −0.02 | PERMIT (reconocimiento lento) |

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] AUC-ROC ≥ 0.85 en test set
- [x] Precision ≥ 95%
- [x] Recall ≥ 95%
- [x] Modelo serializado y cargable sin mismatch de versiones
- [x] τ1/τ2 derivados de curva ROC con criterio estadístico
- [x] metricas_offline.txt sincronizado con umbrales_finales.txt

---

## Rutas en el sensor (192.168.0.110)

```
/home/m4rk/ppi-surikata-producto/
├── models/
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   └── features.csv
└── results/
    ├── metricas_offline.txt      ← τ1/τ2 leídos por motor al arrancar
    └── umbrales_finales.txt      ← copia canónica
```
