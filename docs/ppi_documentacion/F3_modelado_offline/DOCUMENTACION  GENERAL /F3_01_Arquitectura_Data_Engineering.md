# F3-01 — Arquitectura Completa de Data Engineering

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F3 — Modelado Offline  
**Fecha:** 2026-06-14  

---

## 1. Arquitectura General de Datos

El pipeline transforma tráfico de red capturado pasivamente en decisiones de control inline, pasando por siete etapas encadenadas:

```
Tráfico de Red (192.168.0.0/24)
        │
        ▼
┌───────────────────┐
│    Suricata 7.0.3 │  ← ens35 en modo pasivo (sin DROP)
│  IDS/NIDS sensor  │    Inspección DPI por cada flow TCP/UDP/ICMP
└────────┬──────────┘
         │  eve.json (JSON Lines, append continuo)
         ▼
┌───────────────────┐
│   Conversión      │  ← parser.py
│ eve.json.gz → CSV │    Filtra event_type=flow, extrae campos raw
└────────┬──────────┘
         │  dataset_raw.csv  (campos sin normalizar)
         ▼
┌───────────────────┐
│    Limpieza       │  ← etiquetar_limpiar.py
│  Dedup + filtros  │    Elimina IPs inválidas, broadcasts, duplicados
└────────┬──────────┘
         │  dataset_labeled.csv
         ▼
┌───────────────────┐
│   Etiquetado      │  ← etiquetar_limpiar.py (dual-label)
│ filename + src_ip │    normal si src=.20 · anomalous si src=.100
└────────┬──────────┘
         │  dataset_clean.csv  (376,827 flows · 69 MB)
         ▼
┌───────────────────┐
│Feature Engineering│  ← fase3_isolation_forest.py
│   14 features     │    Derivadas de campos Suricata (ratios, flags)
└────────┬──────────┘
         │  train.csv / val.csv / test.csv  (70/15/15 cronológico)
         ▼
┌───────────────────┐
│ StandardScaler    │  ← fit exclusivo en 684 flows normales de train
│  Normalización    │    Evita que anomalías contaminen la escala
└────────┬──────────┘
         │  X_scaled (matriz normalizada)
         ▼
┌───────────────────┐
│ Isolation Forest  │  ← n_estimators=300 · contamination=0.05
│ Modelo Predictivo │    Score ∈ [-1, 0]: más negativo = más anómalo
└────────┬──────────┘
         │  score por flow  →  τ1=-0.4973  τ2=-0.6873
         ▼
┌───────────────────┐
│ Motor de Decisión │  ← motor_decision.py (F4)
│ PERMIT/LIMIT/BLOCK│    + detectores temporales SSH/HTTP
└────────┬──────────┘
         │  ipset add ppi_blocked / ppi_limited
         ▼
    Dataset Final
    isolation_forest.pkl · scaler.pkl · features.csv
```

---

## 2. Flujo Completo de Procesamiento

### Etapa 1 — Captura (Suricata)

| | Detalle |
|---|---|
| **Entrada** | Tráfico de red en segmento 192.168.0.0/24 |
| **Herramienta** | Suricata 7.0.3 en interfaz ens35, modo pasivo |
| **Transformación** | Deep Packet Inspection por flow; cierre por timeout o FIN/RST |
| **Salida** | `/var/log/suricata/eve.json` — JSON Lines, un objeto por evento |

Campos relevantes extraídos por flow:
```json
{
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 12, "pkts_toclient": 8,
    "bytes_toserver": 720, "bytes_toclient": 4800,
    "start": "2026-06-02T19:41:00.123Z",
    "end":   "2026-06-02T19:41:00.456Z"
  }
}
```

### Etapa 2 — Conversión (`parser.py`)

| | Detalle |
|---|---|
| **Entrada** | `data/raw/YYYYMMDD_*_eve.json.gz` (13 archivos de escenario) |
| **Transformación** | Filtra `event_type=flow`; extrae src_ip, dest_ip, dest_port, proto, pkts_*, bytes_*, start, end |
| **Salida** | `data/dataset_raw.csv` — campos crudos sin normalizar |

### Etapa 3 — Limpieza y Etiquetado (`etiquetar_limpiar.py`)

| | Detalle |
|---|---|
| **Entrada** | `dataset_raw.csv` |
| **Transformación** | Eliminación de duplicados (-34 filas); filtro IPs inválidas, broadcast, multicast (-35,236 filas); etiquetado dual: por nombre de archivo (escenario) y por src_ip (.20→normal, .100→anomalous) |
| **Salida** | `dataset_clean.csv` — 376,827 flows · 3.1% normal · 96.9% anomalous |

Distribución de clases:
```
Normal    :  11,669 flows  (3.1%)
Anomalous : 365,158 flows  (96.9%)
Total     : 376,827 flows
```

### Etapa 4 — Partición Cronológica (`particionar_estadisticos.py`)

| | Detalle |
|---|---|
| **Entrada** | `dataset_clean.csv` ordenado por timestamp |
| **Transformación** | División 70/15/15 **cronológica** (no aleatoria) para evitar data leakage temporal |
| **Salida** | `train.csv` (263,778) · `val.csv` (56,524) · `test.csv` (56,525) |

> **Por qué cronológico:** una partición aleatoria permitiría que el modelo vea flujos futuros durante el entrenamiento, inflando artificialmente las métricas. La partición cronológica replica las condiciones reales de producción.

### Etapa 5 — Feature Engineering (`fase3_isolation_forest.py`)

| | Detalle |
|---|---|
| **Entrada** | `train.csv` |
| **Transformación** | Cálculo de 14 features derivadas (ver tabla) |
| **Salida** | Matriz de features X ∈ ℝⁿˣ¹⁴ |

**14 Features del modelo:**

| # | Feature | Tipo | Descripción |
|---|---|---|---|
| 1 | `pkts_toserver` | Raw | Paquetes enviados al servidor |
| 2 | `pkts_toclient` | Raw | Paquetes recibidos del servidor |
| 3 | `bytes_toserver` | Raw | Bytes enviados al servidor |
| 4 | `bytes_toclient` | Raw | Bytes recibidos del servidor |
| 5 | `duration` | Derivada | Duración del flow en segundos |
| 6 | `pkt_rate` | Derivada | `(pkts_toserver + pkts_toclient) / duration` |
| 7 | `byte_rate` | Derivada | `(bytes_toserver + bytes_toclient) / duration` |
| 8 | `pkt_ratio` | Derivada | `pkts_toserver / (pkts_toclient + 1)` |
| 9 | `byte_ratio` | Derivada | `bytes_toserver / (bytes_toclient + 1)` |
| 10 | `avg_pkt_size` | Derivada | `(bytes_toserver + bytes_toclient) / (pkts_toserver + pkts_toclient + 1)` |
| 11 | `is_tcp` | Flag | 1 si proto=TCP, 0 si no |
| 12 | `is_udp` | Flag | 1 si proto=UDP, 0 si no |
| 13 | `is_icmp` | Flag | 1 si proto=ICMP, 0 si no |
| 14 | `dest_port` | Raw | Puerto destino del flow |

### Etapa 6 — Normalización (`StandardScaler`)

| | Detalle |
|---|---|
| **Entrada** | Matriz X con 14 features |
| **Transformación** | `z = (x - μ) / σ` — media y desviación estándar calculadas **solo sobre los 684 flows normales** del set de entrenamiento |
| **Salida** | `X_scaled` normalizada · `models/scaler.pkl` serializado |

> **Decisión crítica:** el scaler se ajusta exclusivamente con flows normales (no con los 263,778 del train completo). Si se incluyeran anomalías en el fit, la escala quedaría sesgada hacia valores extremos, distorsionando la separabilidad del modelo.

### Etapa 7 — Modelo Predictivo (Isolation Forest)

| | Detalle |
|---|---|
| **Entrada** | `X_scaled` de los 684 flows normales |
| **Parámetros** | `n_estimators=300`, `contamination=0.05`, `random_state=42` |
| **Transformación** | Construcción de 300 árboles de aislamiento; score = profundidad media de aislamiento normalizada |
| **Salida** | `models/isolation_forest.pkl` · scores ∈ [-1, 0] |

**Umbrales derivados de la curva ROC (AUC=0.9440):**

| Umbral | Valor | Criterio | Acción |
|---|---|---|---|
| τ1 | -0.4973 | Youden index máximo (TPR=91.0%, FPR=9.5%) | score > τ1 → **PERMIT** |
| τ2 | -0.6873 | FPR ≤ 2% con máximo TPR (TPR=40.6%, FPR=1.8%) | τ2 < score ≤ τ1 → **LIMIT** |
| — | — | — | score ≤ τ2 → **BLOCK** |

---

## 3. Componentes de la Arquitectura

### Fuentes de Datos

| Componente | Tecnología | Rol |
|---|---|---|
| Interfaz de red ens35 | NIC promiscua en VM sensor | Captura de tráfico pasivo |
| Suricata 7.0.3 | IDS/NIDS open-source | Genera eve.json por flow |
| Desktop .20 (normal) | Ubuntu Desktop, curl/wget/ssh/scp | Origen tráfico normal (A1-A4) |
| Kali .100 (anómalo) | Kali Linux, hping3/nmap/hydra | Origen tráfico anómalo (B1-B6) |

### Procesadores

| Componente | Script | Responsabilidad |
|---|---|---|
| Parser | `scripts/parser.py` | eve.json.gz → CSV raw |
| Limpiador/Etiquetador | `scripts/etiquetar_limpiar.py` | Dedup, filtros, etiquetado dual |
| Particionador | `scripts/particionar_estadisticos.py` | División cronológica 70/15/15 |
| Entrenador | `scripts/fase3_isolation_forest.py` | Entrena IF, guarda pkl |
| Umbral ROC | `scripts/auc_roc_umbrales.py` | Deriva τ1/τ2 desde curva ROC |
| Motor (live) | `scripts/motor_decision.py` | Inferencia en tiempo real |
| Clasificador | `scripts/clasificador.py` | Tipifica anomalías (7 tipos) |

### Almacenamiento

| Artefacto | Ruta | Descripción |
|---|---|---|
| Capturas raw | `data/raw/*.json.gz` | 13 archivos por escenario |
| Dataset crudo | `data/dataset_raw.csv` | Sin limpiar |
| Dataset limpio | `data/dataset_clean.csv` | 376,827 flows · 69 MB |
| Particiones | `data/train/val/test.csv` | 263,778 / 56,524 / 56,525 |
| Modelo | `models/isolation_forest.pkl` | IF serializado |
| Scaler | `models/scaler.pkl` | StandardScaler serializado |
| Features | `models/features.csv` | Lista de 14 features |
| Log live | `results/motor_decision.log` | Decisiones en tiempo real |
| Umbrales | `results/umbrales_finales.txt` | τ1/τ2 formalizados |

### Modelos

| Modelo | Tipo | Parámetros clave | AUC-ROC |
|---|---|---|---|
| Isolation Forest | Unsupervised anomaly detector | n=300, contamination=0.05 | 0.9440 |
| Detector BF-SSH | Heurístico temporal | ventana=60s, umbral=15 intentos | — |
| Detector HTTP-Abuse | Heurístico temporal | ventana=30s, umbral=100 req | — |

### Alertas

| Canal | Trigger | Contenido |
|---|---|---|
| `motor_decision.log` | Cada decisión PERMIT/LIMIT/BLOCK | timestamp · src/dst · score · acción · razón z-score |
| Telegram Bot | BLOCK o LIMIT | Score, tipo anomalía, MITRE ATT&CK ID, CVSS, top-3 features |
| ipset ppi_blocked | BLOCK | DROP total, timeout 300s automático |
| ipset ppi_limited | LIMIT | hashlimit 100pkt/s, timeout 300s automático |

---

## 4. Diagramas

Los diagramas compatibles con Draw.io se encuentran en:

`F3_modelado_offline/DIAGRAMAS/F3_Arquitectura_Data.drawio.md`

Incluye:
- **Diagrama lógico:** componentes y sus relaciones
- **Diagrama de flujo:** transformación paso a paso de los datos
- **Diagrama de procesamiento:** capas de procesamiento con tecnologías

---

## 5. Justificación Metodológica

### Por qué Isolation Forest para detección de anomalías en red

**1. Aprendizaje no supervisado con datos solo-normales**  
El sistema entrena exclusivamente con tráfico normal (684 flows), sin requerir ejemplos de ataques etiquetados. Esto es crítico en seguridad de redes: los ataques son continuamente nuevos y no se pueden anticipar completamente. El experimento de generalización (F2-04) confirmó que el modelo detectó 12/12 ataques no entrenados (Slowloris, DNS Amplification, RDP Brute Force, NTP Amplification) al 100%.

**2. Complejidad O(n log n) adecuada para tiempo real**  
Isolation Forest aísla puntos anómalos en pocos pasos (anomalías quedan en ramas cortas), lo que resulta en latencia de inferencia de 34.8ms P95 — muy por debajo del requisito de 500ms.

**3. Score continuo para decisión graduada**  
A diferencia de clasificadores binarios (normal/anómalo), el score continuo [-1, 0] permite la lógica triple PERMIT/LIMIT/BLOCK, reduciendo el impacto en tráfico legítimo que cometería un sistema todo-o-nada.

**4. Robustez al desbalance extremo**  
Con 96.9% de anomalías en el dataset (producido por capturas de ataques de alta tasa como SYN flood), algoritmos supervisados como Random Forest o SVM tenderían a sesgarse. Isolation Forest ignora las etiquetas completamente.

**5. Complemento con detectores heurísticos**  
Los casos donde el modelo base tiene recall bajo (BF-SSH ~1%, HTTP Abuse ~31%) son cubiertos por detectores temporales que operan sobre ventanas de tiempo, elevando el recall combinado a ~92-95%.

**6. Partición cronológica como garantía de validez**  
La división 70/15/15 cronológica previene el data leakage temporal: el modelo nunca ve flows futuros durante el entrenamiento, replicando fielmente las condiciones de un despliegue real.

**7. Scaler ajustado solo en datos normales**  
Ajustar el StandardScaler únicamente con los 684 flows normales garantiza que la normalización refleje la distribución del tráfico legítimo, maximizando la separación entre scores normales y anómalos (separación medida: 0.229 unidades entre -0.434 SSH normal y -0.655 port scan).

---

## 6. Métricas de Calidad del Pipeline

| Etapa | Métrica | Valor |
|---|---|---|
| Captura (Suricata) | Flows procesados | 376,827 |
| Limpieza | Flows eliminados | 35,270 (dedup + IPs inválidas) |
| Partición | Set de entrenamiento | 263,778 flows (70%) |
| Normalización | Flows para fit del scaler | 684 (solo normales) |
| Modelo | AUC-ROC | 0.9440 |
| Modelo | Precision | 99.96% |
| Modelo | F1-Score | 0.9338 |
| Pipeline live | Latencia P95 | 34.8 ms |
| Pipeline live | Throughput | 29 flows/s |
| Validación F6 | Disponibilidad | 100% (40/40 corridas) |
| Validación F6 | ITL | 0% |
| Validación F6 | TIE | 100% |

---

## Referencias de archivos

| Archivo | Ruta en sensor | Descripción |
|---|---|---|
| `parser.py` | `scripts/parser.py` | Etapa 2: conversión |
| `etiquetar_limpiar.py` | `scripts/etiquetar_limpiar.py` | Etapa 3: limpieza y etiquetado |
| `particionar_estadisticos.py` | `scripts/particionar_estadisticos.py` | Etapa 4: partición |
| `fase3_isolation_forest.py` | `scripts/fase3_isolation_forest.py` | Etapas 5-7: features + modelo |
| `auc_roc_umbrales.py` | `scripts/auc_roc_umbrales.py` | Derivación de τ1/τ2 |
| `isolation_forest.pkl` | `models/isolation_forest.pkl` | Modelo serializado |
| `scaler.pkl` | `models/scaler.pkl` | Scaler serializado |
| `features.csv` | `models/features.csv` | 14 features |
| `umbrales_finales.txt` | `results/umbrales_finales.txt` | τ1/τ2 formalizados |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
