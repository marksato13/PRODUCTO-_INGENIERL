# F3 — Especificación Técnica: Modelado Offline

## Objetivo
Entrenar el modelo Isolation Forest con tráfico normal y derivar los umbrales de decisión τ1/τ2 mediante análisis de la curva ROC.

## Scripts involucrados

| Script | Entrada | Proceso | Salida |
|---|---|---|---|
| `scripts/fase3_isolation_forest.py` | `data/train.csv` | Escala features + entrena IF | `models/isolation_forest.pkl`, `models/scaler.pkl`, `models/features.csv` |
| `scripts/fase3_evaluar.py` | `data/test.csv` + modelos | Score en test, calcula AUC, deriva τ | `results/metricas_offline.txt`, `results/auc_roc.png` |
| `scripts/auc_roc_umbrales.py` | scores del modelo | Curva ROC por escenario | `results/reports/auc_por_escenario.txt` |
| `scripts/auc_por_escenario.py` | scores + labels | AUC desglosado B1-B6, C1-C3 | `results/reports/auc_por_escenario.txt` |

## Features del modelo (14)

| Feature | Descripción | Tipo |
|---|---|---|
| `pkts_toserver` | Paquetes enviados al servidor | Volumen |
| `pkts_toclient` | Paquetes recibidos del servidor | Volumen |
| `bytes_toserver` | Bytes enviados al servidor | Volumen |
| `bytes_toclient` | Bytes recibidos del servidor | Volumen |
| `duration` | Duración del flow en segundos | Timing |
| `pkt_rate` | Tasa de paquetes por segundo | Rate |
| `byte_rate` | Tasa de bytes por segundo | Rate |
| `pkt_ratio` | pkts_toserver / pkts_toclient | Ratio |
| `byte_ratio` | bytes_toserver / bytes_toclient | Ratio |
| `avg_pkt_size` | Tamaño medio de paquete | Tamaño |
| `is_tcp` | 1 si protocolo TCP | Flag |
| `is_udp` | 1 si protocolo UDP | Flag |
| `is_icmp` | 1 si protocolo ICMP | Flag |
| `dest_port` | Puerto destino | Puerto |

## Parámetros del modelo

| Parámetro | Valor | Justificación |
|---|---|---|
| `n_estimators` | 300 | Validado por análisis de sensibilidad (`sensibilidad_n_flows.png`) |
| `contamination` | 0.05 | Prior conservador (5% esperado de anomalías en red empresarial) |
| `random_state` | 42 | Reproducibilidad |
| `offset_` interno | −0.5742 | Calculado por scikit-learn |

## Umbrales derivados (fuente canónica: `results/metricas_offline.txt`)

| Umbral | Valor | Criterio | TPR | FPR |
|---|---|---|---|---|
| τ1 (PERMIT/LIMIT) | **−0.4650** | Youden index máximo (TPR−FPR óptimo) | 99.35% | 20.27% |
| τ2 (LIMIT/BLOCK) | **−0.6118** | FPR ≤ 2% con máximo TPR | 17.01% | 2.00% |

## Métricas del modelo

| Métrica | Valor |
|---|---|
| AUC-ROC | 0.8955 |
| Precision (en τ1) | 99.54% |
| Recall (en τ1) | 99.35% |
| F1-Score | 0.9945 |
| AUC por escenario más bajo | B1 SYN Flood: 0.8302 |
| AUC por escenario más alto | B2 Port Scan: 0.9726 |

## Secuencia de ejecución F3
```bash
cd /home/m4rk/ppi-surikata-producto
python3 scripts/fase3_isolation_forest.py   # entrena y guarda PKL
python3 scripts/fase3_evaluar.py            # evalúa, deriva τ, genera auc_roc.png
python3 scripts/auc_por_escenario.py        # AUC desglosado por escenario
```
