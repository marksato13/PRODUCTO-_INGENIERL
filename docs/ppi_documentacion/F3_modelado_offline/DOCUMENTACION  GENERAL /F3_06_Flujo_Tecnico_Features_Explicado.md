# F3-06 — Flujo Técnico: Features, Scripts y Terminología Explicada

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F3 — Modelado Offline  
**Propósito:** Guía de comprensión técnica para defensa oral — qué entra, de dónde, qué hace cada script y qué significa cada término  

---

## 1. ¿Qué es una Feature?

Una **feature** (característica) es un número que describe un aspecto medible de algo. En este sistema, cada "flow" de Suricata es una conexión de red, y de esa conexión se extraen 14 números que la describen por completo.

### Del eve.json al vector de 14 números

El evento crudo que escribe Suricata en `eve.json` luce así:

```json
{
  "event_type": "flow",
  "src_ip": "192.168.0.20",
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 6,
    "bytes_toserver": 492,
    "pkts_toclient": 4,
    "bytes_toclient": 555,
    "start": "2026-06-02T04:09:02",
    "end":   "2026-06-02T04:09:03"
  }
}
```

La función `extract_features(e)` convierte ese JSON en un vector de 14 números:

```
[6, 4, 492, 555, 0.12, 83.3, 8725, 1.5, 0.89, 94.2, 1, 0, 0, 80]
 ↑  ↑   ↑    ↑    ↑     ↑     ↑    ↑    ↑      ↑   ↑  ↑  ↑   ↑
 1  2   3    4    5     6     7    8    9     10  11 12 13  14
```

### Las 14 features y su propósito

| # | Nombre | Cálculo | Para qué sirve |
|---|---|---|---|
| 1 | `pkts_toserver` | directo del flow | Paquetes enviados al servidor |
| 2 | `pkts_toclient` | directo del flow | Paquetes recibidos del servidor |
| 3 | `bytes_toserver` | directo del flow | Bytes enviados al servidor |
| 4 | `bytes_toclient` | directo del flow | Bytes recibidos del servidor |
| 5 | `duration` | `end − start` (mín. 0.001s) | Duración de la conexión |
| 6 | `pkt_rate` | `(pkts_to + pkts_from) / duration` | Velocidad de paquetes por segundo |
| 7 | `byte_rate` | `(bytes_to + bytes_from) / duration` | Velocidad de bytes por segundo |
| 8 | `pkt_ratio` | `pkts_toserver / (pkts_toclient + 1)` | Asimetría de paquetes — ¿envía mucho y recibe poco? |
| 9 | `byte_ratio` | `bytes_toserver / (bytes_toclient + 1)` | Asimetría de bytes |
| 10 | `avg_pkt_size` | `bytes_totales / (pkts_totales + 1)` | Tamaño promedio de paquete |
| 11 | `is_tcp` | 1 si proto==TCP | Protocolo TCP |
| 12 | `is_udp` | 1 si proto==UDP | Protocolo UDP |
| 13 | `is_icmp` | 1 si proto==ICMP | Protocolo ICMP |
| 14 | `dest_port` | puerto destino | ¿A qué servicio fue? |

### ¿Por qué 14 y no solo 3?

Un ataque **SYN Flood** no se detecta mirando solo el número de paquetes. Se detecta por la **combinación**:

```
HTTP normal (A1):          SYN Flood (B1):
  pkts_toserver = 6          pkts_toserver = 7,432
  pkts_toclient = 4          pkts_toclient = 0      ← servidor no responde
  duration      = 0.12s      duration      = 0.08s  ← cortísima
  pkt_rate      = 83/s       pkt_rate      = 92,900/s ← altísima
  pkt_ratio     = 1.5        pkt_ratio     = 7432    ← extrema asimetría
```

Los 14 números juntos forman la **huella digital** del tráfico. El modelo aprende el espacio de huellas normales y detecta cualquier cosa que se aleje de ese espacio.

---

## 2. El Flujo Técnico Completo de F3

```
¿QUÉ ENTRA?         ¿DE DÓNDE VIENE?          ¿QUÉ SCRIPT?
──────────────────────────────────────────────────────────────────
Archivos .gz    ←   data/raw/                  fase3_isolation_forest.py
(eve.json.gz)        (F2 los generó con
                      exportar_eve_por_escenario.sh)

train.csv       ←   data/                      auc_roc_umbrales.py
test.csv             (F2 los generó con         (para evaluación, NO entrenamiento)
                      particionar_estadisticos.py)
```

### Paso 1 — Lectura y doble filtro (`fase3_isolation_forest.py`)

```python
# Lee SOLO corridas 01 y 02 (no las 03-10 que tienen exceso de SSH)
for f in glob("data/raw/*_normal_*_01_eve.json.gz"):
    events = parse_flows(f, src_filter={'192.168.0.20', '192.168.0.120'})
    #                                    ↑ solo Desktop y Servidor
```

**¿Por qué no usa `train.csv` directamente?**

El `eve.json` de Suricata acumula TODO el tráfico de la sesión sin reiniciarse. Un archivo llamado `normal_http_01.gz` puede contener flows de ataques que ocurrieron después en la misma sesión. El filtro por `src_ip` garantiza que solo entren flows del Desktop (tráfico legítimo confirmado por IP origen), eliminando cualquier contaminación.

**¿Por qué solo corridas 01 y 02 y no las 03-10?**

Las corridas 03-10 tienen principalmente SSH legítimo. Si se incluyen, el modelo aprende que "SSH frecuente es muy normal" y pierde capacidad de detectar Brute Force SSH (B6). El análisis de sensibilidad confirmó que N=684 flows de las corridas 01-02 es el punto óptimo.

**Resultado del filtro:** 684 flows normales puros.

```
normal_http_01/02:         345 flows  (50.4%)
normal_sostenido_01/02:    252 flows  (36.8%)
normal_ssh_01/02:           58 flows   (8.5%)  ← bajo para no sesgar B6
normal_transferencia_01/02:  29 flows   (4.2%)
──────────────────────────────────────
TOTAL:                     684 flows
```

---

### Paso 2 — Extract Features

```python
def extract_features(e):
    flow  = e.get('flow', {})
    proto = e.get('proto', '').upper()
    dur   = flow_duration(e)           # calcula end - start
    pts   = flow.get('pkts_toserver',  0) or 0
    ptc   = flow.get('pkts_toclient',  0) or 0
    bts   = flow.get('bytes_toserver', 0) or 0
    btc   = flow.get('bytes_toclient', 0) or 0

    return np.array([[
        pts, ptc, bts, btc,             # volumétricas (4)
        dur,                             # temporal (1)
        (pts + ptc) / dur,               # pkt_rate
        (bts + btc) / dur,               # byte_rate
        pts / (ptc + 1),                 # pkt_ratio
        bts / (btc + 1),                 # byte_ratio
        (bts + btc) / (pts + ptc + 1),  # avg_pkt_size
        int(proto == 'TCP'),             # binarias (3)
        int(proto == 'UDP'),
        int(proto in ('ICMP', 'IPV6-ICMP')),
        e.get('dest_port', 0) or 0,     # discreta (1)
    ]], dtype=float)
```

**Resultado:** una matriz `[684 × 14]` — 684 filas (flows) × 14 columnas (features).

---

### Paso 3 — StandardScaler (normalización)

**El problema sin normalizar:**

```
pkt_rate puede ser 83 (HTTP normal) o 92,000 (SYN flood)
is_tcp siempre es 0 o 1
dest_port puede ser 22 o 80
```

Si se combinan directamente, `pkt_rate` dominaría completamente el modelo porque sus valores son miles de veces más grandes. El Isolation Forest no sabría qué importancia darle a `is_tcp`.

**La solución — StandardScaler:**

```
                  valor − media_del_tráfico_normal
X_escalado = ──────────────────────────────────────────
               desviación_estándar_del_tráfico_normal
```

Ejemplo concreto:

```
pkt_rate normal: media=83, std=15
  HTTP normal:   z = (83 - 83) / 15    =   0.0   → dentro de lo esperado
  SYN Flood:     z = (92000 - 83) / 15 = +6,127   → extremadamente alto
```

Ese número `z` se llama **z-score**: cuántas desviaciones estándar se aleja del tráfico normal. Es exactamente el número que aparece en el log del motor:

```
ANOMALÍA | score=-0.7214 | pkt_rate:z=+45.2 | pkts_toserver:z=+38.7
```

**Punto clave:** el scaler se ajusta (`fit`) **SOLO con los 684 flows normales**. Aprende la distribución del tráfico legítimo. Todo lo demás se mide respecto a ese baseline. El scaler se guarda en `models/scaler.pkl` (1.4 KB) y se reutiliza en producción para transformar cada flow nuevo antes de pasarlo al modelo.

---

### Paso 4 — IsolationForest (`clf.fit(X_scaled_normal)`)

**¿Qué hace internamente?**

Construye 300 árboles de decisión aleatorios. La idea central es:

> Un punto **anómalo** es fácil de aislar (pocas particiones).  
> Un punto **normal** está rodeado de similares (necesita muchas particiones).

```
Árbol aleatorio (simplificado):

  ¿pkt_rate > 500?
  ├── SÍ → ¿bytes_toclient < 10?
  │         ├── SÍ → AISLADO en 2 cortes   ← anómalo (fácil de separar)
  │         └── NO → más cortes...
  └── NO → ¿dest_port == 80?
             ├── SÍ → muchos más cortes... ← normal (difícil de separar)
             └── NO → ...
```

**El anomaly score:**

```python
score = clf.score_samples(X_scaled)[0]
# Rango: (-1, 0)
# Cercano a  0  → difícil de aislar → NORMAL
# Cercano a -1  → fácil de aislar   → MUY ANÓMALO
```

**Hiperparámetros y su justificación:**

| Parámetro | Valor | Por qué |
|---|---|---|
| `n_estimators` | 300 | Más árboles = scores más estables (default=100 tiene alta varianza) |
| `contamination` | 0.05 | Asume 5% de ruido en tráfico normal (establece `clf.offset_`) |
| `max_samples` | 'auto' (256) | Submuestra de 256 flows por árbol — eficiente y preciso |
| `random_state` | 42 | Reproducibilidad del experimento |
| `n_jobs` | -1 | Paraleliza en los 4 cores del sensor |

**Artefacto generado:** `models/isolation_forest.pkl` (2.5 MB) — el modelo serializado con todos sus 300 árboles.

---

### Paso 5 — Evaluación y Derivación de Umbrales (`auc_roc_umbrales.py`)

**¿Por qué no usar el umbral automático `clf.offset_ = -0.5481`?**

El offset automático es calculado por `contamination=0.05` sin conocer la distribución real del tráfico anómalo. No está optimizado para la lógica PERMIT/LIMIT/BLOCK del sistema.

**Eval set balanceado 50/50:**

```
11,669 flows normales   ← de train.csv (los que el modelo conoce como normales)
11,669 flows anómalos   ← primeros 11,669 de test.csv
= 23,338 flows total    ← base para calcular la curva ROC
```

**Distribución de scores observada:**

```
Tráfico NORMAL:   μ = -0.4262  σ = 0.0646
Tráfico ANÓMALO:  μ = -0.6548  σ = 0.0808
Separación:       Δ = 0.229 unidades ← base de la discriminación
```

**Curva ROC y AUC:**

```
Para cada umbral θ entre -1 y 0:
  TPR(θ) = % ataques detectados (score ≤ θ)
  FPR(θ) = % normales falsamente detectados (score ≤ θ)

AUC = área bajo curva TPR vs FPR = 0.9440
    = 94.4% de probabilidad de que un flow anómalo
      tenga score más bajo que un flow normal
```

**Derivación de τ1 (PERMIT/LIMIT):**

```
Criterio: Índice de Youden = max(TPR − FPR)
          → mejor balance entre detectar y no bloquear legítimo

En τ1 = -0.4973:
  TPR = 91.0%  → detecta el 91% de los ataques
  FPR = 9.5%   → 9.5% del tráfico normal pasa a LIMIT (no a BLOCK)
```

**Derivación de τ2 (LIMIT/BLOCK):**

```
Criterio: FPR ≤ 2% con máximo TPR posible
          → minimizar bloqueos erróneos de tráfico legítimo

En τ2 = -0.6873:
  FPR = 1.8%   → solo 1.8% del tráfico normal va a BLOCK
  TPR = 40.6%  → 40.6% de ataques van directo a BLOCK
                  (el resto pasa por LIMIT primero)
```

**Lógica triple resultante:**

```
score > -0.4973              → PERMIT  (normal con alta confianza)
-0.6873 < score ≤ -0.4973   → LIMIT   (sospechoso, rate limit 100 pkt/s)
score ≤ -0.6873              → BLOCK   (anómalo confirmado, DROP)
```

---

## 3. Flujo Completo en 8 Líneas

```
data/raw/*_normal_*_01/02.gz        ← F2 generó estos archivos
   ↓ parse_flows() + filtro src_ip
684 flows normales [texto JSON]
   ↓ extract_features()
Matriz [684 × 14]  [números]
   ↓ StandardScaler.fit()           → scaler.pkl  (guarda μ y σ del tráfico normal)
Matriz [684 × 14] escalada (z-scores)
   ↓ IsolationForest.fit()          → isolation_forest.pkl  (300 árboles)
Modelo entrenado
   ↓ auc_roc_umbrales.py (sobre test.csv)
τ1 = -0.4973  ·  τ2 = -0.6873       → umbrales_finales.txt
   ↓
F4: motor_decision.py carga los .pkl y aplica en tiempo real
```

---

## 4. Analogía para la Defensa

> *"Imagina que tienes 684 personas normales caminando por un corredor. Les mides 14 características: velocidad, peso, altura, color de ropa, dirección, etc. Luego construyes 300 cámaras inteligentes (los árboles). Cada cámara hace preguntas aleatorias: '¿camina más rápido de X?', '¿pesa más de Y?'. Una persona normal necesita muchas preguntas para ser identificada porque se parece a las otras 684. Una persona sospechosa es identificada en pocas preguntas porque es muy diferente a las demás. Eso es Isolation Forest: aprende el perfil de las 684 personas normales y señala automáticamente todo lo que no encaja, sin necesitar haber visto nunca a un atacante."*

---

## 5. Resumen de Scripts F3

| Script | Entrada | Salida | Cuándo ejecutar |
|---|---|---|---|
| `fase3_isolation_forest.py` | `data/raw/*_normal_*_01/02.gz` | `models/isolation_forest.pkl`, `models/scaler.pkl`, `models/features.csv` | Una vez para entrenar (o cuando se recalibra) |
| `auc_roc_umbrales.py` | `models/isolation_forest.pkl`, `data/test.csv` | `results/umbrales_finales.txt`, `results/figures/auc_roc_umbrales.png` | Después del entrenamiento |
| `auc_por_escenario.py` | `models/isolation_forest.pkl`, `data/test.csv` | `results/reports/auc_por_escenario.txt` | Para análisis por tipo de ataque |

---

## 6. Preguntas Frecuentes en Defensa

**¿Por qué 684 flows y no más?**
> El análisis de sensibilidad demostró que el AUC se estabiliza desde N=200-300 flows. Agregar más flows de SSH sesgaría el modelo y reduciría la detección de Brute Force SSH (B6) a 0%. N=684 es el punto óptimo entre estabilidad y equilibrio de protocolos.

**¿Por qué Isolation Forest y no Random Forest?**
> Random Forest es supervisado: necesita ejemplos etiquetados de ataques para entrenar. En producción real no se tienen ataques etiquetados de antemano. Isolation Forest aprende solo del tráfico normal y detecta cualquier desviación, incluyendo ataques nunca vistos antes. La comparación empírica (F4-01) mostró que IF tiene AUC=0.9992 equivalente a RF=0.9993, con la ventaja de no necesitar etiquetas.

**¿Qué pasa con ataques nuevos que el modelo nunca vio?**
> IF detecta anomalías, no patrones específicos de ataque. Si el nuevo ataque genera tráfico diferente al normal (más volumen, asimetría, puerto inusual), el score será bajo y será detectado. El experimento F2-04 probó 12 ataques no entrenados y los detectó todos al 100%.

**¿Qué significa AUC=0.9440?**
> Significa que en el 94.4% de los casos, el modelo asigna un score más bajo a un flow anómalo que a uno normal. Es la probabilidad de que el modelo discrimine correctamente entre tráfico legítimo y ataque, independientemente del umbral elegido.

---

*Documento generado el 15 de junio 2026 como material de apoyo para la defensa del PPI*
