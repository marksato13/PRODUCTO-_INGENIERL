# FASE 3 — Modelado Offline: Isolation Forest

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fecha de ejecución:** 2–4 de junio 2026  

---

## Objetivo de la fase

Entrenar un modelo de detección de anomalías no supervisado usando Isolation Forest sobre los flujos de red capturados en F2. El modelo debe aprender el patrón del tráfico normal y asignar scores de anomalía a cada flow, diferenciando tráfico legítimo de ataques.

---

## 1. Algoritmo seleccionado: Isolation Forest

### Justificación

Isolation Forest es un algoritmo de detección de anomalías **no supervisado** especialmente adecuado para este problema porque:

- Se entrena **solo con datos normales** — no requiere ejemplos etiquetados de ataques
- Funciona bien en espacios de alta dimensionalidad (14 features)
- Es eficiente en tiempo de inferencia (< 1ms por muestra)
- Es robusto ante outliers en los datos de entrenamiento
- Ampliamente validado en detección de anomalías de red en literatura académica

### Principio de funcionamiento

El algoritmo aísla anomalías construyendo árboles de decisión aleatorios. Un punto anómalo es más fácil de aislar (requiere menos particiones) que uno normal. El **anomaly score** es negativo: cuanto más negativo, más anómalo.

```
score > umbral  → NORMAL   (difícil de aislar)
score ≤ umbral  → ANÓMALO  (fácil de aislar)
```

---

## 2. Feature Engineering

**Script:** `scripts/fase3_isolation_forest.py`  
**Archivo de features:** `models/features.csv`

Se extrajeron **14 features** de cada flow del dataset:

| Feature | Descripción | Tipo |
|---|---|---|
| `pkts_toserver` | Paquetes enviados al servidor | Volumétrico |
| `pkts_toclient` | Paquetes recibidos del servidor | Volumétrico |
| `bytes_toserver` | Bytes enviados al servidor | Volumétrico |
| `bytes_toclient` | Bytes recibidos del servidor | Volumétrico |
| `duration` | Duración del flow en segundos | Temporal |
| `pkt_rate` | Tasa de paquetes por segundo | Derivado |
| `byte_rate` | Tasa de bytes por segundo | Derivado |
| `pkt_ratio` | Asimetría de paquetes (server/client) | Derivado |
| `byte_ratio` | Asimetría de bytes (server/client) | Derivado |
| `avg_pkt_size` | Tamaño medio de paquete | Derivado |
| `is_tcp` | Flag protocolo TCP (0/1) | Categórico |
| `is_udp` | Flag protocolo UDP (0/1) | Categórico |
| `is_icmp` | Flag protocolo ICMP (0/1) | Categórico |
| `dest_port` | Puerto de destino | Categórico |

**Normalización:** `StandardScaler` (media=0, desviación=1), ajustado solo con datos normales para evitar contaminación.

**Decisión de diseño importante:** El `StandardScaler` se entrena **exclusivamente con flujos normales** filtrados por `src_ip == 192.168.0.20`. Esto garantiza que el espacio de features está normalizado con respecto al tráfico legítimo, haciendo que los ataques aparezcan como outliers.

---

## 3. Datos de entrenamiento

El modelo se entrena **solo con tráfico normal** (aprendizaje no supervisado):

| Escenario | Flows limpios | Filtro aplicado |
|---|---|---|
| normal_http (corridas 01, 02) | 345 | `src_ip == 192.168.0.20` |
| normal_sostenido (corridas 01, 02) | 252 | `src_ip == 192.168.0.20` |
| normal_ssh (corridas 01, 02) | 58 | `src_ip == 192.168.0.20` |
| normal_transferencia (corridas 01, 02) | 29 | `src_ip == 192.168.0.20` |
| **TOTAL** | **684 flows** | src_ip filtrado |

**Por qué 684 y no más:** Se aplicó el filtro `src_ip ∈ {192.168.0.20, 192.168.0.120}` para eliminar la contaminación. El `eve.json` de Suricata acumula todo el tráfico histórico, incluyendo ataques ejecutados después de las capturas normales. Sin el filtro, los archivos "normales" contendrían flows de SYN flood y port scans.

---

## 4. Parámetros del modelo

**Archivo del modelo:** `models/isolation_forest.pkl` (2.5 MB)  
**Archivo del scaler:** `models/scaler.pkl` (1.4 KB)

| Parámetro | Valor | Justificación |
|---|---|---|
| `n_estimators` | 300 | Mayor número → mayor estabilidad de scores |
| `contamination` | 0.05 | 5% de ruido esperado en tráfico normal |
| `max_samples` | 256 (auto) | Submuestreo eficiente para árboles |
| `random_state` | 42 | Reproducibilidad del experimento |
| `n_features_in` | 14 | Todas las features extraídas |

**Script de entrenamiento:** `scripts/fase3_isolation_forest.py`

---

## 5. Umbrales de decisión τ1 y τ2

El umbral base del modelo (`clf.offset_ = -0.5481`) se obtuvo de `contamination=0.05`. Para implementar la lógica de triple acción, se definieron dos umbrales adicionales mediante la **curva ROC**.

**Archivo de referencia:** `results/reports/reporte_metricas_v1.txt`  
**Gráfico:** `results/figures/auc_roc_umbrales.png`

| Umbral | Valor | Criterio | TPR | FPR | Acción |
|---|---|---|---|---|---|
| τ1 | **-0.4973** | Índice de Youden máximo (TPR−FPR) | 91.0% | 9.5% | PERMIT / LIMIT |
| τ2 | **-0.6873** | FPR ≤ 2% con máximo TPR | 40.6% | 1.8% | LIMIT / BLOCK |

### Lógica de decisión resultante

```
score > τ1  (-0.4973)              →  PERMIT  (tráfico normal)
τ2 (-0.6873) < score ≤ τ1         →  LIMIT   (sospechoso — rate limit)
score ≤ τ2  (-0.6873)              →  BLOCK   (anómalo confirmado — DROP)
```

---

## 6. Métricas del modelo

**AUC-ROC global: 0.9440** — el modelo distingue tráfico anómalo del normal con 94.4% de probabilidad.

### Métricas con umbral base (clf.offset_ = -0.5481)

| Métrica | Valor |
|---|---|
| **Recall (Detección)** | **87.6%** |
| **Precisión** | **99.96%** |
| **F1-Score** | **0.9338** |
| Tasa Falsos Positivos | 5.1% |
| TN (normal correcto) | 649 (94.9%) |
| FP (falsa alarma) | 35 (5.1%) |
| TP (anomalía detectada) | 96,422 (87.6%) |
| FN (anomalía perdida) | 13,644 (12.4%) |
| Score medio normal | -0.4262 (±0.0646) |
| Score medio anómalo | -0.6548 (±0.0808) |
| Separación de scores | **0.229** |

La separación de 0.229 entre la media de scores normales (-0.426) y anómalos (-0.655) es la que permite la discriminación efectiva.

---

## 7. AUC-ROC por escenario individual

**Archivo:** `results/reports/auc_por_escenario.txt`  
**Script:** `scripts/auc_por_escenario.py`

| Escenario | AUC | Detección | Score medio | Estado |
|---|---|---|---|---|
| UDP Flood (B3) | **0.9905** | 100% | -0.714 | Excelente |
| ICMP Flood (B4) | **0.9861** | 100% | -0.700 | Excelente |
| Mixto C3 | **0.9801** | 99.3% | -0.677 | Excelente |
| Mixto C1 | **0.9737** | 100% | -0.653 | Excelente |
| Port Scan (B2) | **0.9721** | 99.9% | -0.651 | Excelente |
| SYN Flood (B1) | 0.9529 | 72.2% | -0.606 | Muy bueno |
| Mixto C2 | 0.9277 | 57.1% | -0.609 | Muy bueno |
| HTTP Abuse (B5) | 0.8630 | 56.6% | -0.589 | Bueno |
| Brute Force (B6) | 0.6770 | 0.9% | -0.438 | Limitado* |

> *B6 (Brute Force SSH): los flows SSH individuales se parecen al tráfico normal. Se resuelve en F4 con un detector temporal (ventana 60s).

---

## 8. Gráficos generados

**Archivo:** `results/isolation_forest_resultado.png`  
**Archivo:** `results/figures/auc_roc_umbrales.png`

Los gráficos incluyen:
1. **Distribución de anomaly scores** — normal vs. anómalo con umbral marcado
2. **Curva ROC** — con τ1 y τ2 señalados
3. **Scatter plot** — packet rate vs. bytes_toserver por clase
4. **Tabla de métricas** resumen

---

## 9. Limitaciones conocidas y su tratamiento

| Limitación | Causa | Solución implementada |
|---|---|---|
| Brute Force (B6) detección 0.9% | Flows SSH son similares a SSH normal | Detector temporal en F4 (15 intentos/60s → BLOCK) |
| HTTP Abuse (B5) detección 56.6% | Curl lento imita HTTP normal | Detector temporal en F4 (100 req/30s → BLOCK) |
| Más SSH normal reduce recall | Isolation Forest sensible a distribución | Se mantiene dataset balanceado de 684 flows normales |

---

## 10. Criterios de cierre de F3

| Criterio | Estado |
|---|---|
| Feature engineering implementado (14 features) | ✅ |
| StandardScaler ajustado solo con datos normales | ✅ |
| Isolation Forest entrenado (`isolation_forest.pkl`) | ✅ |
| Umbral base `clf.offset_` = -0.5481 calculado | ✅ |
| AUC-ROC = 0.9440 calculado | ✅ |
| Curva ROC generada con τ1=-0.4973 y τ2=-0.6873 | ✅ |
| Recall 87.6%, Precisión 99.96%, F1=0.9338 | ✅ |
| AUC por escenario individual calculado | ✅ |
| Gráficos generados en `results/figures/` | ✅ |
| Reporte de métricas en `results/reports/` | ✅ |

**F3 CERRADA ✅ — 4 de junio 2026**

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| `fase3_isolation_forest.py` | `scripts/` | **Script principal de entrenamiento** |
| `auc_por_escenario.py` | `scripts/` | Cálculo AUC por escenario |
| `auc_roc_umbrales.py` | `scripts/` | Curva ROC y definición de τ1/τ2 |
| `isolation_forest.pkl` | `models/` | **Modelo entrenado serializado** (2.5 MB) |
| `scaler.pkl` | `models/` | StandardScaler serializado |
| `features.csv` | `models/` | Lista de 14 features del modelo |
| `isolation_forest_resultado.png` | `results/` | Gráfico de distribución de scores |
| `auc_roc_umbrales.png` | `results/figures/` | Curva ROC con τ1/τ2 |
| `reporte_metricas_v1.txt` | `results/reports/` | **Reporte formal de métricas F3** |
| `auc_por_escenario.txt` | `results/reports/` | AUC individual por escenario |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
