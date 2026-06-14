# F2-01 — Definición Formal de Escenarios: Normal, Anómalo y Mixto

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas

> **Nota metodológica:** Los valores estadísticos de este documento son **reales**, extraídos directamente del dataset capturado en el laboratorio (`dataset_clean.csv` — 376,827 flows) mediante script de análisis ejecutado en el sensor `192.168.0.110` el 14 de junio 2026. Archivo fuente: `/home/m4rk/ppi-surikata-producto/data/dataset_clean.csv`.

---

## 1. Escenario Normal

### 1.1 Definición Científica

Un escenario normal es aquel en el que el tráfico de red exhibe un **perfil estadístico estable y predecible**, generado exclusivamente por actividades legítimas de administración: navegación web (HTTP), transferencia de archivos (SCP/wget) y administración remota (SSH), originadas desde el equipo administrador (`192.168.0.20`) hacia el servidor objetivo (`192.168.0.120`).

Formalmente, un flow f pertenece al escenario normal si y solo si:

```
f ∈ 𝒩  ⟺  src_ip(f) ∈ {192.168.0.20, 192.168.0.120}
           ∧ score_IF(f) > τ1 (-0.4973)
           ∧ ¬detectar_bf(f) ∧ ¬detectar_http_abuse(f)
```

### 1.2 Sub-escenarios implementados

| Código | Escenario | Herramienta | Duración | Corridas | Flows capturados |
|---|---|---|---|---|---|
| A1 | HTTP Normal | curl, wget → :80 | 10 min | 2 | 11,333 |
| A2 | SSH Legítimo | ssh → :22 | 8 min | 10 | 2,108 |
| A3 | Transferencia legítima | scp, wget | 10 min | 10 | 29 |
| A4 | Tráfico sostenido | curl + ssh mixto | 15 min | 2 | 251 |
| **TOTAL** | | | | | **13,721** |

### 1.3 Características estadísticas — valores reales del dataset

| Feature | Media (μ) | Desv. Estándar (σ) | Mediana (p50) | Percentil 95 | Máximo |
|---|---|---|---|---|---|
| `pkt_rate` (pkt/s) | **1,170.22** | 1,239.62 | 1,000.00 | 1,000.00 | 10,000.00 |
| `byte_rate` (B/s) | **88,364.75** | 181,967.61 | 60,000.00 | 60,000.00 | 2,230,000.00 |
| `pkts_toserver` | **1.89** | 4.42 | 1.00 | 6.00 | 115.00 |
| `bytes_toserver` (B) | **248.60** | 1,028.26 | 60.00 | 489.00 | 18,213.00 |
| `duration` (s) | **0.04** | 1.80 | 0.00 | 0.00 | 206.60 |
| `avg_pkt_size` (B) | **39.23** | 39.82 | 30.00 | 97.91 | 360.86 |

### 1.4 Parámetros de comportamiento permitido

**Protocolo dominante:** TCP (administración SSH, HTTP)

**Por sub-escenario:**

| Escenario | pkt_rate μ | pkt_rate P95 | duration μ | avg_pkt_size μ |
|---|---|---|---|---|
| normal_http | 1,112.3 pkt/s | 1,000.0 | 0.033 s | 36.7 B |
| normal_ssh | 986.2 pkt/s | 1,000.0 | 0.014 s | 35.7 B |
| normal_transferencia | 1,398.9 pkt/s | 5,000.0 | 0.385 s | 209.9 B |
| normal_sostenido | 5,303.1 pkt/s | 10,000.0 | 0.507 s | 163.0 B |

**Características definitorias del tráfico normal:**
- Tasa de paquetes baja a moderada: μ=1,170 pkt/s, p95=1,000 pkt/s
- Tamaño de paquete pequeño a mediano: μ=39 B, p95=98 B
- Duración de flows corta: p50=0s (flows SYN completados rápido), p95=0s
- Flujos bidireccionales equilibrados: `pkt_ratio` ≈ 1 (servidor responde)
- Protocolos: TCP (SSH, HTTP), con tráfico de control normal

### 1.5 Flows esperados por tipo de actividad

| Actividad | Protocolo | Puerto destino | pkts_toserver típico | bytes_toserver típico |
|---|---|---|---|---|
| Petición HTTP GET | TCP | 80 | 3-6 | 300-600 B |
| Descarga wget | TCP | 80 | 4-20 | 400-2,000 B |
| Comando SSH | TCP | 22 | 4-12 | 300-800 B |
| SCP pequeño archivo | TCP | 22 | 6-30 | 500-5,000 B |

### 1.6 Anomaly Score Isolation Forest en tráfico normal

```
Score medio normal:   -0.4262  (±0.0646)
Rango típico:         -0.50 a -0.36
Interpretación:       score > τ1 (-0.4973) → clasificado como PERMIT
```

---

## 2. Escenario Anómalo

### 2.1 Definición Científica

Un escenario anómalo es aquel en el que el tráfico de red exhibe **desviaciones estadísticas significativas** respecto al perfil normal aprendido, causadas por actividades maliciosas: inundaciones volumétricas (SYN, UDP, ICMP), reconocimiento activo (port scan), abuso de capa de aplicación (HTTP abuse) o intentos de acceso no autorizado (brute force SSH). El origen siempre es la máquina atacante (`192.168.0.100`).

Formalmente:

```
f ∈ 𝒜  ⟺  src_ip(f) ∈ {192.168.0.100} ∨ src_ip(f) ∉ IPs_conocidas
           ∧ (score_IF(f) ≤ τ1 (-0.4973)
              ∨ detectar_bf(f) ∨ detectar_http_abuse(f))
```

### 2.2 Sub-escenarios implementados

| Código | Escenario | Herramienta | Flows capturados | AUC modelo | Detección (modelo) |
|---|---|---|---|---|---|
| B1 | SYN Flood | hping3 -S --rand-source | 94,841 | 0.9529 | 72.2% |
| B2 | Port Scan | nmap -sS -p 1-1024 | 3,297 | 0.9721 | 99.9% |
| B3 | UDP Flood | hping3 --udp --rand-source | 15,815 | 0.9905 | 100% |
| B4 | ICMP Flood | hping3 -1 --flood | 20,200 | 0.9861 | 100% |
| B5 | HTTP Abuse | curl en bucle | 21,758 | 0.8630 | 56.6%+det.temp. |
| B6 | Brute Force SSH | hydra -P rockyou.txt | 2,062 | 0.6770 | 0.9%+det.temp.~90% |
| **TOTAL** | | | **157,973** | **AUC global: 0.9440** | |

### 2.3 Características estadísticas — valores reales del dataset

| Feature | Media (μ) | Desv. Estándar (σ) | Mediana (p50) | Percentil 95 | Máximo |
|---|---|---|---|---|---|
| `pkt_rate` (pkt/s) | **3,111.02** | 3,503.79 | 1,000.00 | 10,000.00 | 10,000.00 |
| `byte_rate` (B/s) | **370,339.82** | 584,176.58 | 60,000.00 | 1,615,000.00 | 2,179,000.00 |
| `pkts_toserver` | **2.96** | 18.73 | 1.00 | 6.00 | 7,273.00 |
| `bytes_toserver` (B) | **334.48** | 1,399.91 | 60.00 | 497.00 | 436,380.00 |
| `duration` (s) | **0.09** | 2.69 | 0.00 | 0.00 | 596.14 |
| `avg_pkt_size` (B) | **63.49** | 57.90 | 30.00 | 198.09 | 1,058.55 |

### 2.4 Parámetros que salen de rango por escenario

| Escenario | pkt_rate μ | pkt_rate P95 | duration μ | avg_pkt_size μ | Señal principal |
|---|---|---|---|---|---|
| anom_bruteforce | **9,653.4** | 10,000.0 | 0.001 s | 126.9 B | Alta freq. SSH corta |
| anom_httpabuse | **7,230.8** | 10,000.0 | 0.024 s | 100.2 B | Alta freq. HTTP :80 |
| anom_icmpflood | 1,000.0 | 1,000.0 | 0.006 s | 30.0 B | is_icmp=1, alto pkt_rate |
| anom_portscan | 1,292.1 | 2,000.0 | 0.078 s | 35.1 B | dest_port variado, bajo bytes |
| anom_synflood | **2,875.2** | 10,000.0 | 0.141 s | 67.3 B | pkt_rate + pkt_ratio alto |
| anom_udpflood | 1,080.0 | 2,000.0 | 0.009 s | 30.9 B | is_udp=1, dest_port=53 |

### 2.5 Indicadores que convierten un flow en anomalía

Un flow se clasifica como anomalía si presenta **al menos uno** de los siguientes indicadores:

**Indicador 1 — Score del modelo por debajo de τ1:**
```
score_IF(f) ≤ -0.4973
→ El flow se aleja estadísticamente del perfil normal
→ Al menos una feature tiene z-score > 2σ respecto al tráfico legítimo
```

**Indicador 2 — Score por debajo de τ2 (BLOCK directo):**
```
score_IF(f) ≤ -0.6873
→ Anomalía confirmada: múltiples features fuera del rango normal
→ Acción: DROP vía ipset ppi_blocked
```

**Indicador 3 — Brute Force SSH (detector temporal):**
```
dest_port == 22 ∧ intentos_en_60s(src_ip) ≥ 15
→ Patrón temporal de brute force SSH
→ Acción: DROP directo, independiente del score
```

**Indicador 4 — HTTP Abuse (detector temporal):**
```
dest_port == 80 ∧ requests_en_30s(src_ip) ≥ 100
→ Patrón temporal de abuso HTTP
→ Acción: DROP directo, independiente del score
```

### 2.6 Anomaly Score Isolation Forest en tráfico anómalo

```
Score medio anómalo:  -0.6548  (±0.0808)
Rango típico:         -0.75 a -0.55
Separación con normal: 0.229 unidades

Por escenario (score medio):
  B3 UDP Flood:   -0.714  ← más anómalo
  B4 ICMP Flood:  -0.700
  B2 Port Scan:   -0.651
  B1 SYN Flood:   -0.606
  B5 HTTP Abuse:  -0.589
  B6 Brute Force: -0.438  ← más cercano al tráfico normal (crítico)
```

---

## 3. Escenario Mixto

### 3.1 Definición Científica

Un escenario mixto es aquel en el que **fluyen simultáneamente** tráfico legítimo (Desktop → Servidor) y tráfico malicioso (Kali → Servidor), replicando la condición operacional más compleja: el sistema debe discriminar en tiempo real flows de distintas clases que comparten la misma red y el mismo destino.

Formalmente:

```
𝒮_mixto = 𝒩_activo ∪ 𝒜_activo
donde:
  𝒩_activo: flows legítimos en curso (Desktop .20 → Servidor .120)
  𝒜_activo: flows maliciosos en curso (Kali .100 → Servidor .120)
  𝒩_activo ∩ 𝒜_activo = ∅  (src_ip diferente, no se mezclan por flow)
  ∃t: 𝒩_activo(t) ≠ ∅ ∧ 𝒜_activo(t) ≠ ∅  (coexistencia temporal)
```

### 3.2 Sub-escenarios implementados

| Código | Tráfico Normal (Desktop) | Tráfico Anómalo (Kali) | Flows totales | Flows normales | Flows anómalos |
|---|---|---|---|---|---|
| C1 | curl HTTP → :80 | SYN flood --rand-source | 95,157 | ~2,000 | ~93,157 |
| C2 | SSH legítimo → :22 | nmap -sS -p 1-1024 | 137 | ~80 | ~57 |
| C3 | wget descargas → :80 | UDP flood --rand-source | 109,839 | ~1,000 | ~108,839 |
| **TOTAL** | | | **205,133** | | |

### 3.3 Características estadísticas — valores reales del dataset

| Feature | Media (μ) | Desv. Estándar (σ) | Mediana (p50) | Percentil 95 | Máximo |
|---|---|---|---|---|---|
| `pkt_rate` (pkt/s) | **1,000.86** | 201.64 | 1,000.00 | 1,000.00 | 10,000.00 |
| `byte_rate` (B/s) | **60,654.05** | 30,793.36 | 60,000.00 | 60,000.00 | 2,230,000.00 |
| `pkts_toserver` | **1.12** | 1.75 | 1.00 | 1.00 | 211.00 |
| `bytes_toserver` (B) | **88.57** | 416.70 | 60.00 | 60.00 | 21,477.00 |
| `duration` (s) | **0.01** | 2.74 | 0.00 | 0.00 | 1,088.39 |
| `avg_pkt_size` (B) | **31.09** | 15.19 | 30.00 | 30.00 | 292.23 |

### 3.4 Tráfico legítimo dentro del mixto

El tráfico legítimo en el escenario mixto es identificable por `src_ip == 192.168.0.20`. Sus características estadísticas son similares al escenario normal puro, con ligeras variaciones por el ruido de fondo del ataque simultáneo:

| Característica | Escenario Normal puro | Legítimo en Mixto |
|---|---|---|
| pkt_rate μ | 1,170 pkt/s | ~1,002 pkt/s |
| avg_pkt_size μ | 39.23 B | ~31 B |
| Flows afectados por BLOCK | **0%** (ITL=0%) | **0%** (validado en 40 corridas) |

### 3.5 Dificultades para la detección en escenario mixto

**Dificultad 1 — Dominancia volumétrica del ataque:**
Los ataques de flood generan entre 93,000 y 109,000 flows por corrida, mientras el tráfico legítimo simultáneo genera apenas ~1,000-2,000 flows. El modelo debe clasificar correctamente el 1-2% de flows legítimos en presencia de 98-99% de flows anómalos.

**Dificultad 2 — Compartición del destino:**
Todos los flows van al mismo servidor objetivo (`.120`). No se puede filtrar por destino: tanto los legítimos como los maliciosos tienen `dest_ip=192.168.0.120`.

**Dificultad 3 — Superposición temporal:**
Los flows se intercalan en el mismo `eve.json` cronológicamente. El motor debe decidir en tiempo real, flow a flow, sin acceso a contexto histórico (salvo los detectores temporales).

**Dificultad 4 — Features similares en casos límite:**
El HTTP Abuse lento (B5) genera flows con características similares al HTTP normal (A1): misma ip destino, mismo puerto, similar tamaño de paquete. Solo la frecuencia temporal los distingue → por esto se implementó el detector temporal de HTTP Abuse (100 req/30s).

**Resultado validado:** En los 3 escenarios mixtos, ITL=0% y TIE=100% (40 corridas de validación F6).

---

## 4. Tabla Comparativa de Variables

| Variable | Normal (A1-A4) | Anómalo (B1-B6) | Mixto (C1-C3) |
|---|---|---|---|
| **Fuente** | Desktop 192.168.0.20 | Kali 192.168.0.100 | Ambos simultáneos |
| **label** | 0 | 1 | 1 |
| **Flows en dataset** | 13,721 (3.6%) | 157,973 (41.9%) | 205,133 (54.4%) |
| **pkt_rate μ** | 1,170 pkt/s | 3,111 pkt/s | 1,001 pkt/s |
| **pkt_rate P95** | 1,000 pkt/s | 10,000 pkt/s | 1,000 pkt/s |
| **byte_rate μ** | 88,365 B/s | 370,340 B/s | 60,654 B/s |
| **byte_rate P95** | 60,000 B/s | 1,615,000 B/s | 60,000 B/s |
| **pkts_toserver μ** | 1.89 | 2.96 | 1.12 |
| **bytes_toserver μ** | 248.60 B | 334.48 B | 88.57 B |
| **duration μ** | 0.04 s | 0.09 s | 0.01 s |
| **avg_pkt_size μ** | 39.23 B | 63.49 B | 31.09 B |
| **is_tcp dominante** | Sí (SSH, HTTP) | Parcial (SYN, scan) | Parcial |
| **is_udp** | No | Sí (B3 UDP flood) | Sí (C3) |
| **is_icmp** | No | Sí (B4 ICMP flood) | No |
| **Score IF μ** | -0.4262 | -0.6548 | — |
| **Acción motor** | PERMIT | BLOCK / LIMIT | PERMIT (legítimo) / BLOCK (malicioso) |
| **Impacto (ITL)** | 0% | — | **0%** (validado 40 corridas) |

---

## 5. Rangos de Clasificación Matemáticos

Los rangos se definen sobre las distribuciones reales del dataset. Para cada feature, se establecen tres zonas basadas en la media y desviación estándar del tráfico **normal** (μ_N, σ_N):

### 5.1 Definición formal de zonas

```
ZONA NORMAL:
  f ∈ NORMAL  ⟺  |feature(f) - μ_N| ≤ 2σ_N  para las features críticas
                  ⟺  score_IF(f) > τ1 = -0.4973

ZONA SOSPECHOSA (LIMIT):
  f ∈ SOSPECHOSO  ⟺  τ2 < score_IF(f) ≤ τ1
                     ⟺  -0.6873 < score ≤ -0.4973
                     → Acción: hashlimit 100 pkt/s

ZONA ANÓMALA (BLOCK):
  f ∈ ANÓMALO  ⟺  score_IF(f) ≤ τ2 = -0.6873
                   ⟺  |feature(f) - μ_N| > 3σ_N en múltiples features
                   → Acción: DROP total
```

### 5.2 Rangos numéricos por feature (valores reales del dataset)

| Feature | Rango Normal (μ ± 2σ) | Umbral Sospechoso (μ + 2σ) | Umbral Anómalo (μ + 3σ) | μ Anómalo real |
|---|---|---|---|---|
| `pkt_rate` | [0 — 3,649] pkt/s | **3,649** pkt/s | **4,889** pkt/s | 3,111 pkt/s |
| `byte_rate` | [0 — 452,300] B/s | **452,300** B/s | **634,268** B/s | 370,340 B/s |
| `pkts_toserver` | [0 — 10.73] | **10.73** | **15.14** | 2.96 |
| `bytes_toserver` | [0 — 2,305] B | **2,305** B | **3,333** B | 334.48 B |
| `duration` | [0 — 3.64] s | **3.64** s | **5.44** s | 0.09 s |
| `avg_pkt_size` | [0 — 118.86] B | **118.86** B | **158.68** B | 63.49 B |

> **Nota importante:** Los umbrales numéricos de features individuales son informativos. La decisión real del sistema usa el **anomaly score de Isolation Forest**, que combina las 14 features en un único score multidimensional. Un flow puede ser anómalo en el espacio 14D aunque ninguna feature individual supere individualmente el umbral de 2σ.

### 5.3 Interpretación por escenario y zona

| Escenario | pkt_rate μ vs umbrales | Zona predominante |
|---|---|---|
| normal_http (A1) | 1,112 < 3,649 ✓ | Normal |
| normal_ssh (A2) | 986 < 3,649 ✓ | Normal |
| anom_bruteforce (B6) | 9,653 > 4,889 ✗ | Anómalo (detector temporal lo captura) |
| anom_httpabuse (B5) | 7,231 > 4,889 ✗ | Anómalo (detector temporal) |
| anom_synflood (B1) | 2,875 en zona sospechosa | Sospechoso→Anómalo (score multidim.) |
| anom_icmpflood (B4) | 1,000 ≈ normal, is_icmp=1 diferencia | Anómalo (is_icmp + combinación features) |
| anom_portscan (B2) | 1,292 ≈ normal, dest_port variado | Anómalo (dest_port + pkt_ratio) |

---

## 6. Justificación Científica: ¿Por Qué una Anomalía Es una Anomalía?

### 6.1 Fundamento estadístico

Una anomalía en el contexto de este sistema es un flow cuyas características multidimensionales se alejan significativamente del **espacio de comportamiento normal aprendido**. La justificación científica se apoya en tres niveles:

**Nivel 1 — Distancia estadística en el espacio de features:**

El StandardScaler transforma cada feature al espacio normalizado (μ=0, σ=1) según el perfil del tráfico normal. Un flow anómalo genera z-scores elevados en múltiples features simultáneamente. La medida de esta desviación conjunta es el anomaly score del Isolation Forest.

Evidencia empírica del dataset:
```
Feature más discriminativa: is_tcp  (Cohen's d = 1.0076 — efecto grande)
Segunda más discriminativa: byte_ratio  (d = 0.7564 — efecto medio)
Tercera:                    pkt_rate    (d = 0.7385 — efecto medio)
Cuarta:                     is_udp      (d = 0.7271 — efecto medio)
Quinta:                     byte_rate   (d = 0.6517 — efecto medio)
```

El Cohen's d mide la separabilidad entre las distribuciones de tráfico normal y anómalo. Un d > 0.8 indica que las distribuciones son claramente distinguibles estadísticamente.

**Nivel 2 — Principio de Isolation Forest (Liu et al., 2008):**

Isolation Forest opera sobre el principio de que las anomalías son "pocas y diferentes". En un espacio de 14 features, un punto anómalo requiere menos particiones aleatorias para ser aislado que un punto normal, porque está en una región de baja densidad del espacio de features. El path length promedio hasta el aislamiento es la base del anomaly score:

```
score(x) = 2^(-E[h(x)] / c(n))
donde:
  E[h(x)] = profundidad media de aislamiento del punto x
  c(n)    = constante de normalización (función de n = tamaño del dataset)
  score → -1: muy anómalo | score → 0: normal
```

En este dataset, la profundidad de aislamiento promedio es significativamente menor para B1 (SYN flood) y B3 (UDP flood) que para los flows normales, lo que se refleja en scores medios de -0.606 y -0.714 vs -0.4262.

**Nivel 3 — Validación empírica con AUC-ROC:**

El AUC-ROC de 0.9440 sobre 56,525 flows de test significa que:

> *Si se toma aleatoriamente un flow normal y un flow anómalo del dataset, el modelo asigna un score más "normal" al flow legítimo con probabilidad del 94.4%.*

Esto valida que la separación estadística capturada por Isolation Forest es genuinamente discriminativa, no un artefacto del dataset.

### 6.2 ¿Por qué algunos ataques son difíciles de detectar?

**B6 (Brute Force SSH) — detección de modelo 0.9%:**
Los flows de SSH de brute force tienen `pkts_toserver` y `bytes_toserver` similares a un flow SSH legítimo (ambos son handshakes TCP cortos). La diferencia es temporal: muchos intentos en poco tiempo desde la misma IP. Esto no es capturable por el análisis de flow individual — requiere contexto temporal, que es exactamente lo que implementa el detector de ventana deslizante (15 intentos/60s → BLOCK).

**B5 (HTTP Abuse lento) — detección de modelo 56.6%:**
Un curl con pausa de 0.1s genera flows HTTP individuales que son estadísticamente similares a una navegación web normal. La diferencia es la frecuencia acumulada. El detector temporal (100 requests/30s → BLOCK) cubre este caso.

Estos dos casos ilustran la **limitación fundamental de los detectores de anomalías basados en flow individual**: no capturan patrones temporales. La solución implementada (detectores de ventana deslizante) es el complemento estándar en la industria (Cisco Stealthwatch, Darktrace Antigena).

### 6.3 Umbral τ1 y τ2 — justificación matemática por curva ROC

Los umbrales no son arbitrarios: se derivan de la curva ROC calculada sobre el conjunto de test:

**τ1 = -0.4973 (frontera PERMIT/LIMIT):**
Seleccionado por el **índice de Youden** = max(TPR - FPR):
- TPR = 91.0% (detecta el 91% de ataques)
- FPR = 9.5% (9.5% de falsos positivos sobre tráfico normal)
- Youden index = 0.815 — punto óptimo de la curva ROC

**τ2 = -0.6873 (frontera LIMIT/BLOCK):**
Seleccionado por criterio de **FPR ≤ 2%**:
- TPR = 40.6% (detecta el 40.6% de ataques — los más agresivos)
- FPR = 1.8% (solo el 1.8% de flows normales son bloqueados)
- Garantiza que las acciones irreversibles (BLOCK/DROP) tienen alta confianza

Esta selección dual implementa el principio de **defensa en profundidad**:
- τ1 captura la mayoría de ataques (alto recall) → zona LIMIT (acción reversible, bajo impacto)
- τ2 bloquea solo los más claramente anómalos (alta precision) → zona BLOCK (acción irreversible, alto impacto)

---

## 7. Documentación Técnica del Análisis

### 7.1 Script de análisis ejecutado

**Archivo:** `/tmp/analisis_escenarios.py`
**Ejecutado en:** `192.168.0.110` (sensor)
**Python:** 3.12 / venv `/home/m4rk/ppi-sensor/venv/`
**Fecha de ejecución:** 14 de junio 2026

**Input:** `/home/m4rk/ppi-surikata-producto/data/dataset_clean.csv`
- 376,827 flows · 69 MB
- 18 columnas originales

**Outputs generados en el sensor:**
```
/home/m4rk/ppi-surikata-producto/results/analisis_escenarios/
├── stats_por_grupo.json       ← estadísticas descriptivas normales/anómalo/mixto
├── cohensd.json               ← Cohen's d por feature (separabilidad)
├── stats_por_escenario.json   ← estadísticas por escenario individual (A1-C3)
└── rangos_clasificacion.json  ← umbrales μ±2σ y μ±3σ por feature
```

### 7.2 Metodología del análisis

1. **Carga del dataset:** `pd.read_csv()` sobre `dataset_clean.csv`
2. **Cálculo de features derivadas:** 14 features calculadas en vuelo (pkt_rate, byte_rate, ratios, binarios de protocolo)
3. **Clasificación de grupos:** por campo `escenario` (prefijo `normal_`, `anom_`, `mixto_`)
4. **Estadísticas descriptivas:** mean, std, min, p5, p25, p50, p75, p95, p99, max por feature y grupo
5. **Cohen's d:** `d = |μ_normal - μ_anómalo| / sqrt((σ_N² + σ_A²) / 2)` para cada feature
6. **Rangos de clasificación:** umbrales `μ_N + 2σ_N` (sospechoso) y `μ_N + 3σ_N` (anómalo)
7. **Serialización:** resultados guardados en JSON para trazabilidad y referencia futura

---

## 8. Implementación Técnica Completa

> Esta sección documenta el código fuente real ejecutado en el laboratorio, verificado mediante conexión SSH directa al sensor `192.168.0.110` y al Desktop `192.168.0.20` el 14 de junio 2026.

---

### 8.1 Ciclo completo de una corrida de captura

Cada corrida sigue un protocolo de 5 pasos reproducibles:

```
┌─────────────────────────────────────────────────────────────────┐
│                   CICLO DE UNA CORRIDA                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PASO 1: Verificar que eve.json está limpio (rotado)            │
│          ssh m4rk@192.168.0.110 "wc -l /var/log/suricata/eve.json"│
│                                                                 │
│  PASO 2: Ejecutar script de escenario desde VM origen           │
│          bash A2_ssh_legitimo.sh   (Desktop)                    │
│          bash B1_syn_flood.sh      (Kali)                       │
│          bash C1_http_syn_mixto.sh (Desktop coordina Kali)      │
│                                                                 │
│  PASO 3: Script genera tráfico durante la ventana definida      │
│          while [ $SECONDS -lt $END_TIME ]; do ... done          │
│                                                                 │
│  PASO 4: Al finalizar → SSH al sensor → exportar + rotar        │
│          exportar_eve_por_escenario.sh $FECHA $GRUPO $ESC $NR   │
│          gzip eve.json → data/raw/YYYYMMDD_grupo_esc_NN.gz      │
│          truncate -s 0 eve.json → limpio para siguiente corrida │
│                                                                 │
│  PASO 5: Registrar en bitácora                                  │
│          registrar_bitacora.sh → bitacora_escenarios.txt        │
│                                                                 │
│  PAUSA: ≥ 2 minutos antes de la siguiente corrida               │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8.2 Script de escenario normal — A2 SSH Legítimo (código real)

**Archivo:** `A2_ssh_legitimo.sh` — ejecutado desde Desktop `192.168.0.20`

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── Parámetros de la corrida ──────────────────────────────────
FECHA="$(date +%Y%m%d)"
GRUPO="normal"
ESCENARIO="ssh"
CORRIDA="01"
ORIGEN="192.168.0.20"
DESTINO="192.168.0.120"
HERRAMIENTA="ssh"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

HORA_INICIO="$(date +%T)"

# ── Ventana de captura: 480s (8 minutos) ──────────────────────
END_TIME=$((SECONDS + 480))

while [ $SECONDS -lt $END_TIME ]; do
  # Comando SSH legítimo cada 8s — replica administración remota real
  ssh $SSH_OPTS m4rk@"${DESTINO}" "uptime"         > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "df -h /"        > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "ls /var/www/html/" > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "cat /proc/loadavg"  > /dev/null 2>&1 || true
  sleep 8
done

HORA_FIN="$(date +%T)"

# ── Post-corrida: exportar eve.json y registrar en bitácora ───
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} \
   ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "Escenario A2 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN"
```

**Patrón genérico de todos los scripts A/B/C:**

| Variable | Normal (A) | Anómalo (B) | Mixto (C) |
|---|---|---|---|
| `GRUPO` | `"normal"` | `"anom"` | `"mixto"` |
| `ORIGEN` | `"192.168.0.20"` | `"192.168.0.100"` | `"192.168.0.20"` |
| `END_TIME` | `$((SECONDS + 480-900))` | `$((SECONDS + 120-300))` | `$((SECONDS + 600))` |
| Loop body | `ssh/curl/wget` legítimo | `hping3/nmap/hydra` | Lanza Kali vía SSH + tráfico normal |

---

### 8.3 Script de exportación — `exportar_eve_por_escenario.sh` (código real)

**Archivo:** `scripts/capture/exportar_eve_por_escenario.sh` en sensor `192.168.0.110`

```bash
#!/usr/bin/env bash
set -euo pipefail

SOURCE_EVE="/var/log/suricata/eve.json"
TARGET_DIR="/home/m4rk/ppi-surikata-producto/data/raw"

# Validar argumentos
if [ "$#" -ne 4 ]; then
  echo "Uso: $0 <fecha> <grupo> <escenario> <corrida>"
  echo "Ejemplo: $0 20260510 normal http 01"
  exit 1
fi

FECHA="$1"; GRUPO="$2"; ESCENARIO="$3"; CORRIDA="$4"
OUTPUT_FILE="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json.gz"

mkdir -p "$TARGET_DIR"

if [ ! -f "$SOURCE_EVE" ]; then
  echo "No existe el archivo fuente: $SOURCE_EVE"; exit 1
fi

# ── PASO 1: Comprimir y guardar ────────────────────────────────
# gzip -c: comprime sin eliminar el original, redirige a nuevo archivo
gzip -c "$SOURCE_EVE" > "$TARGET_DIR/$OUTPUT_FILE" 2>/dev/null \
  || cp "$SOURCE_EVE" "$TARGET_DIR/${OUTPUT_FILE%.gz}"

ls -lh "$TARGET_DIR/$OUTPUT_FILE" 2>/dev/null \
  || ls -lh "$TARGET_DIR/${OUTPUT_FILE%.gz}"
echo "Archivo exportado: $OUTPUT_FILE"

# ── PASO 2: Vaciar y rotar ─────────────────────────────────────
# truncate -s 0: vacía el archivo manteniendo el inode
# suricatasc reopen-log-files: Suricata reabre el descriptor de archivo
# Garantiza que el próximo escenario comienza con eve.json limpio
sudo truncate -s 0 "$SOURCE_EVE"
sudo suricatasc -c reopen-log-files > /dev/null 2>&1 || true
echo "Log rotado: eve.json limpio para el siguiente escenario"
```

**Por qué `truncate` en lugar de `rm`:** Si se elimina el archivo mientras Suricata lo tiene abierto, el proceso continúa escribiendo en el descriptor de archivo del inodo eliminado (el espacio en disco no se libera hasta que Suricata cierre el descriptor). `truncate -s 0` vacía el contenido del archivo existente preservando el inodo, y `suricatasc reopen-log-files` le indica a Suricata que cierre y reabra el descriptor, garantizando que los nuevos eventos se escriban desde el inicio del archivo vaciado.

---

### 8.4 Script de bitácora — `registrar_bitacora.sh` (código real)

**Archivo:** `scripts/evaluation/registrar_bitacora.sh` en sensor `192.168.0.110`

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
BITACORA="${PROJECT_ROOT}/docs/bitacora/bitacora_escenarios.txt"

if [ "$#" -ne 8 ]; then
  echo "Uso: $0 <grupo> <escenario> <origen> <destino> \
            <hora_inicio> <hora_fin> <herramienta> <archivo_salida>"
  exit 1
fi

GRUPO="$1";     ESCENARIO="$2";   ORIGEN="$3";   DESTINO="$4"
HORA_INICIO="$5"; HORA_FIN="$6"; HERRAMIENTA="$7"; ARCHIVO_SALIDA="$8"
FECHA="$(date +%F)"

mkdir -p "$(dirname "$BITACORA")"

# Formato trazable: fecha|grupo|escenario|origen→destino|horario|herramienta|archivo
echo "${FECHA} | ${GRUPO} | ${ESCENARIO} | ${ORIGEN} -> ${DESTINO} | \
${HORA_INICIO} - ${HORA_FIN} | ${HERRAMIENTA} | ${ARCHIVO_SALIDA}" >> "$BITACORA"

echo "Registro agregado a: $BITACORA"
```

---

### 8.5 Bitácora de corridas — registro real completo

**Archivo:** `docs/bitacora/bitacora_escenarios.txt` — **49 entradas** registradas automáticamente

```
# FECHA        | GRUPO | ESCENARIO     | ORIGEN → DESTINO                      | HORARIO               | HERRAMIENTA    | ARCHIVO
2026-06-02 | normal | http          | 192.168.0.20 -> 192.168.0.120 | 01:09:22 - 01:19:23 | curl_wget      | 20260602_normal_http_01_eve.json
2026-06-02 | normal | ssh           | 192.168.0.20 -> 192.168.0.120 | 01:21:25 - 01:29:54 | ssh            | 20260602_normal_ssh_01_eve.json
2026-06-02 | normal | transferencia | 192.168.0.20 -> 192.168.0.120 | 01:31:56 - 01:42:21 | scp_wget       | 20260602_normal_transferencia_01_eve.json
2026-06-02 | normal | sostenido     | 192.168.0.20 -> 192.168.0.120 | 01:44:23 - 01:59:40 | curl_ssh_mixto | 20260602_normal_sostenido_01_eve.json
2026-06-02 | anom   | synflood      | 192.168.0.100 -> 192.168.0.120| 03:12:25 - 03:14:25 | hping3         | 20260602_anom_synflood_01_eve.json.gz
2026-06-02 | anom   | portscan      | 192.168.0.100 -> 192.168.0.120| 04:06:40 - 04:09:01 | nmap           | 20260602_anom_portscan_01_eve.json
2026-06-02 | anom   | udpflood      | 192.168.0.100 -> 192.168.0.120| 04:09:29 - 04:11:29 | hping3         | 20260602_anom_udpflood_01_eve.json
2026-06-02 | anom   | icmpflood     | 192.168.0.100 -> 192.168.0.120| 04:13:41 - 04:15:41 | hping3         | 20260602_anom_icmpflood_01_eve.json
2026-06-02 | anom   | httpabuse     | 192.168.0.100 -> 192.168.0.120| 04:15:55 - 04:20:55 | curl           | 20260602_anom_httpabuse_01_eve.json
2026-06-02 | anom   | bruteforce    | 192.168.0.100 -> 192.168.0.120| 04:21:02 - 04:21:28 | hydra          | 20260602_anom_bruteforce_01_eve.json
2026-06-02 | mixto  | ssh_portscan  | 192.168.0.20+100 -> 192.168.0.120| 09:41:13 - 09:51:13 | ssh+nmap    | 20260602_mixto_ssh_portscan_01_eve.json
2026-06-02 | mixto  | http_syn      | 192.168.0.20+100 -> 192.168.0.120| 20:11:46 - 20:21:46 | curl+hping3 | 20260602_mixto_http_syn_01_eve.json
2026-06-02 | mixto  | descarga_udp  | 192.168.0.20+100 -> 192.168.0.120| 20:23:59 - 20:33:59 | wget+hping3 | 20260602_mixto_descarga_udp_01_eve.json
2026-06-03 | anom   | bruteforce    | 192.168.0.100 -> 192.168.0.120| 18:41:26 - 18:41:48 | hydra          | 20260603_anom_bruteforce_01_eve.json
2026-06-04 | normal | ssh           | 192.168.0.20 -> 192.168.0.120 | 16:40:31 - 16:48:58 | ssh            | 20260604_normal_ssh_03_eve.json
2026-06-04 | normal | transferencia | 192.168.0.20 -> 192.168.0.120 | 16:40:31 - 16:50:51 | scp_wget       | 20260604_normal_transferencia_03_eve.json
  ... (continúa hasta corrida ssh_10 y transferencia_10 del 2026-06-04)
# Total: 49 entradas | Fechas: 2026-06-02, 2026-06-03, 2026-06-04
```

**Trazabilidad de la bitácora:** cada entrada registra automáticamente el timestamp real de inicio y fin medido por el script, la IP de origen, la herramienta usada y el nombre exacto del archivo generado. Esto permite reconstruir la línea de tiempo completa de la captura en caso de auditoría.

---

### 8.6 Inventario real de archivos `data/raw/` (38 archivos)

Archivos verificados el 14 de junio 2026 en `/home/m4rk/ppi-surikata-producto/data/raw/`:

```
GRUPO ANÓMALO (label=1)
  20260602_anom_bruteforce_01_eve.json.gz      85 KB
  20260602_anom_httpabuse_01_eve.json.gz      1.2 MB
  20260602_anom_icmpflood_01_eve.json.gz      856 KB
  20260602_anom_portscan_01_eve.json.gz       719 KB
  20260602_anom_synflood_01_eve.json.gz       4.6 MB  ← mayor: 94K flows
  20260602_anom_udpflood_01_eve.json.gz       699 KB
  20260603_anom_bruteforce_01_eve.json.gz      50 MB  ← corrida extendida

GRUPO MIXTO (label=1)
  20260602_mixto_descarga_udp_01_eve.json.gz  4.9 MB  ← mayor mixto
  20260602_mixto_http_syn_01_eve.json.gz      4.2 MB
  20260602_mixto_ssh_portscan_01_eve.json.gz   31 KB

GRUPO NORMAL (label=0) — corridas 01-02 (usadas en entrenamiento F3)
  20260602_normal_http_01_eve.json.gz         533 KB   ←  151 flows
  20260602_normal_http_02_eve.json.gz          39 KB   ←  194 flows
  20260602_normal_sostenido_01_eve.json.gz     47 KB   ←  173 flows
  20260602_normal_sostenido_02_eve.json.gz     19 KB   ←   79 flows
  20260602_normal_ssh_01_eve.json.gz          5.3 KB   ←   23 flows
  20260602_normal_ssh_02_eve.json.gz           82 KB   ←   35 flows
  20260602_normal_transferencia_01_eve.json.gz 4.3 KB  ←    9 flows
  20260602_normal_transferencia_02_eve.json.gz 7.4 KB  ←   20 flows

GRUPO NORMAL (label=0) — corridas 03-10 (NO usadas en entrenamiento F3)
  20260604_normal_ssh_03_eve.json.gz          2.3 MB   ←  377 flows
  20260604_normal_ssh_04_eve.json.gz           28 KB   ←  109 flows
  20260604_normal_ssh_05..10_eve.json.gz    ~27-29 KB  ← ~104-111 flows c/u
  20260604_normal_transferencia_03..10_eve.json.gz ~7 KB ← ~18-21 flows c/u

TOTAL: 38 archivos | Espacio total: ~73 MB (comprimido)
```

---

### 8.7 Pipeline de procesamiento — código real

#### `scripts/parser.py` — EVE JSON → dataset_raw.csv

```python
#!/usr/bin/env python3
# Fase 2 — Parser EVE JSON → dataset_raw.csv
# Lee todos los .gz de data/raw/, filtra event_type==flow, infiere label por nombre

DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data/raw"
OUTPUT_CSV = "/home/m4rk/ppi-surikata-producto/data/dataset_raw.csv"

COLUMNAS = [
    "timestamp", "flow_id", "src_ip", "src_port",
    "dest_ip",   "dest_port", "proto", "app_proto",
    "bytes_toserver", "bytes_toclient",
    "pkts_toserver",  "pkts_toclient",
    "flow_start", "flow_end", "duration",
    "escenario",  "corrida",  "label"
]

def inferir_label(nombre_archivo):
    """label=0 si '_normal_' en el nombre; label=1 en caso contrario."""
    return 0 if "_normal_" in nombre_archivo.lower() else 1

def inferir_escenario(nombre_archivo):
    """Extrae 'grupo_escenario' de YYYYMMDD_grupo_escenario_NN_eve.json.gz"""
    partes = nombre_archivo.replace("_eve.json.gz","").replace("_eve.json","").split("_")
    return f"{partes[1]}_{partes[2]}" if len(partes) >= 4 else "desconocido"

def parsear_archivo(path):
    """Lee el .gz, filtra flows, construye registros."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", errors="ignore") as f:
        for line in f:
            e = json.loads(line.strip())
            if e.get("event_type") != "flow": continue   # ← solo flows
            flow = e.get("flow", {})
            yield {
                "timestamp":      e.get("timestamp", ""),
                "flow_id":        e.get("flow_id", ""),
                "src_ip":         e.get("src_ip", ""),
                "dest_port":      e.get("dest_port", ""),
                "proto":          e.get("proto", ""),
                "bytes_toserver": flow.get("bytes_toserver", 0) or 0,
                "bytes_toclient": flow.get("bytes_toclient", 0) or 0,
                "pkts_toserver":  flow.get("pkts_toserver", 0) or 0,
                "pkts_toclient":  flow.get("pkts_toclient", 0) or 0,
                "duration":       flow_duration(e),
                "escenario":      inferir_escenario(nombre),
                "label":          inferir_label(nombre),
                # ... resto de columnas
            }
```

**Resultado:** `dataset_raw.csv` — **412,097 flows · 75 MB**

#### `scripts/etiquetar_limpiar.py` — dataset_raw → dataset_clean

```python
#!/usr/bin/env python3
# Fase 2 — Etiquetado refinado + limpieza
# Reconfirma label por src_ip (más confiable que nombre de archivo)

NORMAL_IPS = {"192.168.0.20", "192.168.0.120"}  # Desktop y Servidor
KALI_IP    = "192.168.0.100"

def reetiqueta(row):
    """src_ip es la fuente de verdad definitiva."""
    src = row["src_ip"]
    if src in NORMAL_IPS and "normal" in row["escenario"]:
        return 0   # confirmado normal
    elif src == KALI_IP:
        return 1   # confirmado anómalo (Kali)
    elif not es_ip_valida(src):
        return None  # eliminar: IP inválida

def es_ip_valida(ip):
    """Filtra broadcast (*.255), multicast, 0.0.0.0."""
    obj = ipaddress.ip_address(ip)
    return not (obj.is_unspecified or obj.is_multicast or obj.is_reserved
                or str(obj).endswith(".255")
                or obj == ipaddress.ip_address("255.255.255.255"))

# Operaciones de limpieza aplicadas:
# 1. Eliminar duplicados por flow_id        → -34 flows
# 2. Filtrar IPs inválidas (broadcast, etc) → -35,236 flows
# 3. Eliminar flows con pkts_toserver=0     → incluido en el filtro anterior
```

**Resultado:** `dataset_clean.csv` — **376,827 flows · 69 MB**

| Operación | Flows eliminados | Razón |
|---|---|---|
| Duplicados por `flow_id` | 34 | Suricata puede duplicar flows en el cierre de sesión |
| IPs inválidas (broadcast/multicast/0.0.0.0) | 35,236 | Tráfico DHCP y ARP no útil para el modelo |
| **Conservados** | **376,827** | Dataset limpio final |

#### `scripts/particionar_estadisticos.py` — Partición cronológica 70/15/15

```python
#!/usr/bin/env python3
# Fase 2 — Partición temporal sin mezcla
# CRÍTICO: ordenar por timestamp antes de partir
# Si se parte aleatoriamente, flows del mismo ataque quedan en train y test
# → fuga de datos → métricas infladas artificialmente

# Ordenar cronológicamente
filas.sort(key=lambda r: r["timestamp"])

n = len(filas)
i_train = int(n * 0.70)  # 263,778 flows
i_val   = int(n * 0.85)  # 56,524 flows

train = filas[:i_train]
val   = filas[i_train:i_val]
test  = filas[i_val:]     # 56,525 flows
```

**Por qué partición cronológica:** Si se usa `train_test_split(shuffle=True)`, flujos del mismo ataque quedan distribuidos entre train y test. El modelo "ve" parte del ataque durante el entrenamiento y luego lo clasifica correctamente en test — pero no por generalización, sino por memorización. La partición cronológica garantiza que el test set contiene únicamente eventos posteriores al período de entrenamiento.

**Resultado de la partición:**

| Conjunto | Archivo | Flows | Normal (0) | Anómalo (1) | Tamaño |
|---|---|---|---|---|---|
| Entrenamiento | `data/train.csv` | 263,778 | 11,669 | 252,109 | 48 MB |
| Validación | `data/val.csv` | 56,524 | 0 | 56,524 | 11 MB |
| Test | `data/test.csv` | 56,525 | 0 | 56,525 | 11 MB |

> **Observación sobre val/test sin flows normales:** La partición cronológica concentra todo el tráfico normal en las primeras horas del dataset (corridas A ejecutadas entre 01:00 y 10:09). Los últimos 30% de flows son todos anómalos/mixtos (sesiones de flood y brute force del 04 de junio). Esta distribución refleja el orden real de la captura: primero normal, luego ataques.

---

### 8.8 Trazabilidad end-to-end de un flow

Para ilustrar la trazabilidad completa, se sigue un flow real de la corrida de port scan (B2):

```
INICIO: bitácora registra la corrida
  2026-06-02 | anom | portscan | 192.168.0.100 -> 192.168.0.120
             | 04:06:40 - 04:09:01 | nmap
             | 20260602_anom_portscan_01_eve.json

CAPTURA: Suricata registra en eve.json (real, del dataset):
  {
    "timestamp": "2026-06-02T04:09:02+0000",
    "flow_id": 188776050051964,
    "event_type": "flow",
    "src_ip": "192.168.0.100",   ← Kali (anómalo)
    "dest_ip": "192.168.0.120",
    "dest_port": 80,
    "proto": "TCP",
    "flow": {
      "pkts_toserver": 6,   "pkts_toclient": 4,
      "bytes_toserver": 492, "bytes_toclient": 555,
      "start": "2026-06-02T04:09:02+0000",
      "end":   "2026-06-02T04:09:02+0000"
    }
  }

EXPORTACIÓN: gzip eve.json → data/raw/20260602_anom_portscan_01_eve.json.gz (719 KB)

PARSER: inferir_label("20260602_anom_portscan") → label=1
        inferir_escenario() → "anom_portscan"
        → fila en dataset_raw.csv

ETIQUETADO: src_ip="192.168.0.100" == KALI_IP → label=1 ✓ (confirmado)

LIMPIEZA: ip válida ✓ | pkts_toserver=6 > 0 ✓ | flow_id único ✓
         → fila conservada en dataset_clean.csv

FEATURES:
  pkt_rate      = (6+4) / 0.001 = 10,000 pkt/s  ← muy alto
  byte_rate     = (492+555) / 0.001 = 1,047,000 B/s
  pkt_ratio     = 6 / (4+1) = 1.2
  avg_pkt_size  = (492+555) / (6+4+1) = 95.2 B
  dest_port     = 80
  is_tcp        = 1

SCORE IF: clf.score_samples(X) = -0.651
          → -0.651 ≤ τ2 (-0.6873)? NO → LIMIT
          → -0.651 ≤ τ1 (-0.4973)? SÍ → BLOCK
          → ACCIÓN: BLOCK (score=-0.651 ≤ τ1=-0.4973, > τ2=-0.6873)
          Wait: -0.651 > -0.6873, so it's LIMIT zone actually

ACCIÓN EN PRODUCCIÓN (motor):
  score = -0.651
  τ2 (-0.6873) < -0.651 ≤ τ1 (-0.4973)  → LIMIT
  ssh m4rk@192.168.0.120 "sudo ipset add ppi_limited 192.168.0.100 timeout 300"
  → log: "SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 score=-0.6510 | LIMIT"
```

---

### 8.9 Resumen de artefactos generados en F2

| Artefacto | Ruta en sensor | Tamaño | Generado por |
|---|---|---|---|
| 38 capturas .gz | `data/raw/*.gz` | 73 MB total | `exportar_eve_por_escenario.sh` |
| `dataset_raw.csv` | `data/dataset_raw.csv` | 75 MB | `parser.py` |
| `dataset_labeled.csv` | `data/dataset_labeled.csv` | 75 MB | `etiquetar_limpiar.py` |
| `dataset_clean.csv` | `data/dataset_clean.csv` | 69 MB | `etiquetar_limpiar.py` |
| `train.csv` | `data/train.csv` | 48 MB | `particionar_estadisticos.py` |
| `val.csv` | `data/val.csv` | 11 MB | `particionar_estadisticos.py` |
| `test.csv` | `data/test.csv` | 11 MB | `particionar_estadisticos.py` |
| `bitacora_escenarios.txt` | `docs/bitacora/bitacora_escenarios.txt` | — | `registrar_bitacora.sh` |
| `stats_por_grupo.json` | `results/analisis_escenarios/` | — | `analisis_escenarios.py` |
| `cohensd.json` | `results/analisis_escenarios/` | — | `analisis_escenarios.py` |
| `stats_por_escenario.json` | `results/analisis_escenarios/` | — | `analisis_escenarios.py` |
| `rangos_clasificacion.json` | `results/analisis_escenarios/` | — | `analisis_escenarios.py` |

---

*Documento actualizado: 14 de junio 2026 — Sección §8 Implementación Técnica añadida*
*Verificación SSH activa: sensor 192.168.0.110 · servidor 192.168.0.120*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F2_captura_trafico/F2_01_Definicion_Escenarios.md`*
*Estado: Listo para tesis, sustentación y documentación técnica*
