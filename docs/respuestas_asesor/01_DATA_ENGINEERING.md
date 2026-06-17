# Respuesta: DATA ENGINEERING — Arquitectura y Preparación de Datos

**Preocupación del asesor:** "No me importa tanto el modelo todavía. Primero explícame qué data tienes y cómo la preparaste."

---

## 1. ¿Qué data tenemos y de dónde viene?

### Fuente de datos: Suricata IDS (flujos de red)

La data proviene de **Suricata 7.0.3**, un motor IDS (Intrusion Detection System) instalado en el Sensor (192.168.0.110). Suricata opera en modo promiscuo sobre la interfaz `ens35`, capturando **todo el tráfico de red** que pasa por la topología del laboratorio.

Suricata produce el archivo `/var/log/suricata/eve.json`, un log en formato **JSON Lines** (un objeto JSON por línea) donde registra eventos de red en tiempo real. Nos interesa específicamente el tipo de evento **`flow`**, que resume un flujo de red completo una vez que termina.

### Ejemplo de evento `flow` crudo en eve.json

```json
{
  "timestamp": "2026-06-02T09:18:44.123456+0000",
  "event_type": "flow",
  "src_ip": "192.168.0.20",
  "src_port": 54321,
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 7,
    "pkts_toclient": 5,
    "bytes_toserver": 790,
    "bytes_toclient": 576,
    "start": "2026-06-02T09:18:44.119331+0000",
    "end":   "2026-06-02T09:18:44.123456+0000"
  }
}
```

Este es el **dato bruto (raw data)**. Contiene información sobre quién habló con quién, cuántos paquetes y bytes se intercambiaron, y cuánto duró la conexión.

---

## 2. Arquitectura del pipeline de datos (F1 → F3)

```
Red de laboratorio
   │  (tráfico TCP/UDP/ICMP)
   ▼
Suricata 7.0.3 — ens35 modo promiscuo
   │  (captura y analiza todos los paquetes)
   ▼
/var/log/suricata/eve.json
   │  (JSON Lines — eventos tipo "flow")
   │  Formato: 1 línea = 1 flujo de red cerrado
   ▼
Scripts de captura por escenario
   │  exportar_eve_por_escenario.sh
   │  → comprime y rota: YYYYMMDD_grupo_escenario_NN_eve.json.gz
   ▼
data/raw/  ← archivos .gz por corrida
   │  Ej: 20260602_normal_http_01_eve.json.gz
   │      20260602_anom_synflood_01_eve.json.gz
   ▼
fase3_entrenar.py  ← TRANSFORMACIÓN + FEATURE ENGINEERING
   │  parse_flows()  → extrae solo eventos "flow"
   │  extract_features()  → crea 14 features derivadas
   │  StandardScaler  → normalización
   ▼
models/isolation_forest.pkl
models/scaler.pkl
models/features.csv
data/normal_holdout.csv
```

---

## 3. Tipo de data

| Característica | Detalle |
|---|---|
| **Formato origen** | JSON Lines (semi-estructurado) |
| **Formato procesado** | Tabular / DataFrame (estructurado) |
| **Granularidad** | 1 fila = 1 flujo de red (conexión completa) |
| **Dominio** | Redes de datos — capa de transporte (TCP/UDP/ICMP) |
| **Naturaleza** | Time-series (flujos ordenados cronológicamente) |
| **Volumen** | ~65,500 flows totales en motor; ~13,428 flows normales en holdout |
| **Etiquetado** | Implícito por escenario (normal vs anómalo) — NO supervisado en entrenamiento |

### Tipos de variables en el dataset final

| Variable | Tipo | Descripción |
|---|---|---|
| `pkts_toserver` | Entero | Paquetes enviados cliente → servidor |
| `pkts_toclient` | Entero | Paquetes enviados servidor → cliente |
| `bytes_toserver` | Entero | Bytes enviados cliente → servidor |
| `bytes_toclient` | Entero | Bytes enviados servidor → cliente |
| `duration` | Float (segundos) | Duración del flujo |
| `pkt_rate` | Float | Tasa de paquetes/seg = (pkts_to + pkts_from) / duration |
| `byte_rate` | Float | Tasa de bytes/seg = (bytes_to + bytes_from) / duration |
| `pkt_ratio` | Float | Asimetría de paquetes = pkts_toserver / (pkts_toclient + 1) |
| `byte_ratio` | Float | Asimetría de bytes = bytes_toserver / (bytes_toclient + 1) |
| `avg_pkt_size` | Float | Tamaño promedio de paquete en bytes |
| `is_tcp` | Binario (0/1) | 1 si protocolo = TCP |
| `is_udp` | Binario (0/1) | 1 si protocolo = UDP |
| `is_icmp` | Binario (0/1) | 1 si protocolo = ICMP |
| `dest_port` | Entero | Puerto destino (80=HTTP, 22=SSH, 53=DNS, 0=ICMP) |

**Total: 14 features — todas numéricas.**

---

## 4. Metadata del dataset

```
Fuente        : Suricata 7.0.3 — IDS de código abierto (OISF)
Captura       : Interfaz ens35, modo promiscuo, red 192.168.0.0/24
Periodo       : 2026-06-02 a 2026-06-16
Corridas      : 40 corridas documentadas (bitacora_escenarios.txt)
Escenarios    : 13 (A1-A4 normal, B1-B6 anómalo, C1-C3 mixto)
Duración/corr.: 5-15 minutos por corrida de tráfico
Archivo raw   : eve.json comprimido (.gz) por corrida y escenario
Nomenclatura  : YYYYMMDD_grupo_escenario_NN_eve.json.gz
Flows normales: ~67,143 (entrenamiento 80% + holdout 20%)
Flows anomal. : Dataset de evaluación F6 con etiquetas por escenario
```

---

## 5. ¿Cómo llega la data? (Captura y rotación)

1. **Durante la corrida:** Suricata escribe eventos en tiempo real en `/var/log/suricata/eve.json`
2. **Al terminar la corrida:** se ejecuta `exportar_eve_por_escenario.sh` que:
   - Comprime el archivo: `gzip → YYYYMMDD_grupo_escenario_NN_eve.json.gz`
   - Trunca el eve.json activo a 0 bytes
   - Envía señal `suricatasc reopen-log-files` para que Suricata empiece un nuevo log limpio
3. **Espera mínima entre corridas:** 2 minutos para que todos los flujos abiertos se cierren

---

## 6. Data sucia — problemas encontrados y cómo se limpió

### Problema 1: Eventos que no son flujos de red
El eve.json contiene múltiples tipos de eventos (`alert`, `stats`, `dns`, `http`, `tls`, `flow`). Solo nos interesan los de tipo `flow`.

**Solución en código (`fase3_entrenar.py`, función `parse_flows`):**
```python
if e.get('event_type') != 'flow':
    continue  # descarta alerts, stats, dns, http, etc.
```

### Problema 2: Flujos con duración cero o negativa
Suricata a veces cierra flujos sin haber registrado tiempo (paquetes rechazados, resets inmediatos). Una duración de 0 genera división por cero al calcular tasas.

**Solución:**
```python
dur = max((t1 - t0).total_seconds(), 0.001)  # mínimo 1ms
```

### Problema 3: Flujos con 0 paquetes al servidor (flujos incompletos)
Flows donde el cliente nunca completó el envío — ruido de red, no representan una conexión real.

**Solución:**
```python
df = df[df['pkts_toserver'] > 0].reset_index(drop=True)
```

### Problema 4: Valores NaN por campos ausentes en eve.json
No todos los eventos `flow` tienen todos los campos (p.ej., flujos UDP abortados pueden no tener `pkts_toclient`).

**Solución:**
```python
flow.get('pkts_toclient', 0) or 0   # default 0 si ausente o None
df = df[FEATURES].dropna()           # elimina filas con NaN residuales
```

### Problema 5: Flujos de IPs de infraestructura contaminando el dataset
El Sensor (192.168.0.110) genera tráfico de gestión hacia el Servidor; el Desktop también está siempre activo. Si estos se mezclan con tráfico anómalo, el modelo aprende ruido.

**Solución (para entrenamiento):** solo se cargan archivos `*_normal_*.gz` y se filtra por `NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}`.

**Solución (en producción):** WHITELIST hardcodeada en `motor_decision.py` — los flujos de IPs conocidas no se evalúan:
```python
WHITELIST = {"192.168.0.1", "192.168.0.20", "192.168.0.110",
             "192.168.0.120", "192.168.0.130", "192.168.0.140", "127.0.0.1"}
# ...
if src_ip in WHITELIST:
    continue  # se salta el scoring
```

---

## 7. ¿Cómo se transforma la data? (Feature Engineering)

El dato crudo de Suricata da conteos crudos (`pkts_toserver`, `bytes_toserver`, timestamps). Con eso solo no es posible distinguir un ataque de tráfico normal — un SYN Flood de 5 segundos puede tener los mismos bytes que una descarga legítima de 5 segundos.

La clave es **derivar features que capturan el COMPORTAMIENTO del flujo:**

| Feature derivada | Fórmula | Por qué discrimina |
|---|---|---|
| `pkt_rate` | (pkts_to + pkts_from) / duration | Un SYN Flood tiene miles de pkt/s; HTTP normal ~10 |
| `byte_rate` | (bytes_to + bytes_from) / duration | UDP Flood: millones B/s; SSH legítimo: pocos KB/s |
| `pkt_ratio` | pkts_toserver / (pkts_toclient + 1) | Port Scan: muchos paquetes enviados, 0 respuestas → ratio alto |
| `byte_ratio` | bytes_toserver / (bytes_toclient + 1) | HTTP normal: servidor responde más que el cliente |
| `avg_pkt_size` | (bytes_to + bytes_from) / (pkts_to + pkts_from + 1) | SYN Flood: paquetes pequeños (~64B); transferencia: grandes (~1400B) |
| `is_tcp/udp/icmp` | One-hot del protocolo | ICMP Flood vs TCP HTTP vs UDP DNS — protocolo importa |
| `dest_port` | Puerto destino del flujo | Puerto 22=SSH, 80=HTTP, 53=DNS, 0=ICMP — contextualiza el ataque |

**El código exacto de extracción (`fase3_entrenar.py`):**
```python
rows.append({
    'pkts_toserver':  pts,
    'pkts_toclient':  ptc,
    'bytes_toserver': bts,
    'bytes_toclient': btc,
    'duration':       dur,
    'pkt_rate':       (pts + ptc) / dur,
    'byte_rate':      (bts + btc) / dur,
    'pkt_ratio':      pts / (ptc + 1),
    'byte_ratio':     bts / (btc + 1),
    'avg_pkt_size':   (bts + btc) / (pts + ptc + 1),
    'is_tcp':         int(proto == 'TCP'),
    'is_udp':         int(proto == 'UDP'),
    'is_icmp':        int(proto in ('ICMP', 'IPV6-ICMP')),
    'dest_port':      e.get('dest_port', 0) or 0,
})
```

---

## 8. Normalización (StandardScaler)

Las features tienen escalas muy distintas: `pkt_rate` puede ir de 1 a 100,000; `is_tcp` es 0 o 1. Isolation Forest usa distancias en el espacio de features — sin escalar, las features de mayor magnitud dominarían el modelo.

**Solución:** `StandardScaler` — centra cada feature en μ=0 y escala a σ=1:

```python
scaler = StandardScaler()
X_train = scaler.fit_transform(df_train)  # ajusta solo sobre datos de entrenamiento
```

El scaler se ajusta **solo sobre el 80% de entrenamiento** (no sobre el holdout ni los datos de test), para evitar data leakage.

En producción, el mismo `scaler.pkl` transforma cada flow en tiempo real antes de enviarlo al modelo:
```python
x_scaled = scaler.transform(fv.reshape(1, -1))
score = clf.score_samples(x_scaled)[0]
```

---

## 9. Selección de variables — ¿por qué estas 14 y no otras?

### Variables descartadas conscientemente

| Campo disponible en eve.json | Por qué NO se usó |
|---|---|
| `src_ip` | Identificador de instancia — generaría sobreajuste (el modelo memorizaría IPs, no comportamientos) |
| `dest_ip` | Mismo problema |
| `src_port` | Puerto origen es efímero (asignado aleatoriamente) — no discrimina ataques |
| `timestamp` | El modelo debe ser independiente del momento del día |
| `app_proto` | No siempre presente en todos los flujos |
| `tcp.tcp_flags` | No disponible en todos los flujos (UDP, ICMP no tienen) |

### Variables incluidas — criterio de selección

Se eligieron las 14 features porque:
1. **Están presentes en todos los tipos de flujo** (TCP, UDP, ICMP)
2. **Capturan el comportamiento** del flujo, no su identidad
3. **Son computables en tiempo real** con los datos que Suricata ya provee
4. **Discriminan los ataques del laboratorio** según análisis empírico:
   - Port Scan → `pkt_ratio` muy alto, `duration` muy corta
   - SYN Flood → `pkt_rate` extremo, `avg_pkt_size` pequeño
   - HTTP Abuse → `pkt_rate` alto, `dest_port=80`, ratio equilibrado
   - Brute Force SSH → `duration` larga, `pkt_rate` bajo pero sostenido, `dest_port=22`

---

## 10. ¿Por qué Isolation Forest dado este tipo de data?

Esta pregunta conecta el DATA ENGINEERING con la elección del modelo:

| Característica de la data | Implicación para el modelo |
|---|---|
| **No tenemos data etiquetada de ataques al inicio** | No podemos usar modelos supervisados (necesitan ejemplos de ataques para entrenar) |
| **Tenemos mucha data normal** (Grupo A — Desktop navegando) | Podemos aprender la distribución del tráfico normal |
| **Los ataques son eventos raros** (contamination ≈ 5%) | Isolation Forest asume que las anomalías son pocas y distintas |
| **14 features numéricas continuas** | Isolation Forest funciona bien con espacios de features continuos |
| **Necesitamos score continuo** (no solo binario) | `score_samples()` devuelve un score ∈ [−1, 0] que permite umbrales τ1/τ2 |
| **Tiempo real con baja latencia** | Un árbol de decisión por muestra es O(n_estimators × depth) ≈ 34.8ms P95 |

**Isolation Forest aprende que es "normal"** usando solo el Grupo A (tráfico legítimo de Desktop y Servidor). Cualquier flujo que no encaje en esa distribución recibe un score bajo → anomalía. No necesita ejemplos de ataques.

---

## 11. Etiquetado — ¿cómo sabemos qué es anómalo?

El modelo NO usa etiquetas en entrenamiento (no supervisado). Las etiquetas se usan **solo para evaluación** (Fase 3 y F6):

- **Normal:** flows con `src_ip` en `NORMAL_IPS` capturados durante el Grupo A (Kali apagada)
- **Anómalo:** flows capturados durante los escenarios del Grupo B (Kali activa, hping3/nmap/hydra)

El etiquetado es **implícito por condición experimental**: controlamos exactamente qué tráfico había en la red durante cada corrida. Esto es posible porque tenemos control total del laboratorio.

Para el informe académico: este es un enfoque de **one-class classification** — el modelo solo ve datos de una clase (normal) durante el entrenamiento, y en evaluación se contrasta contra datos etiquetados de ambas clases para calcular AUC-ROC, Recall, Precision.

---

## 12. Resumen del pipeline — lo que el asesor quiere ver

```
FUENTE         Eve.json (Suricata) — JSON Lines semi-estructurado
               ↓
FILTRADO       Solo eventos type=flow
               ↓
LIMPIEZA       Dur > 0, pkts_toserver > 0, dropna()
               ↓
TRANSFORMACIÓN 14 features derivadas (tasas, ratios, flags binarios)
               ↓
NORMALIZACIÓN  StandardScaler (μ=0, σ=1) — ajustado solo en train
               ↓
SPLIT          80% entrenamiento (solo flujos normales, Grupo A)
               20% holdout (para evaluar FPR del modelo)
               ↓
MODELO         IsolationForest(n_estimators=300, contamination=0.05)
               ↓
UMBRALES       Curva ROC → τ1=−0.4459 (Youden), τ2=−0.6027 (FPR≤2%)
               ↓
EVALUACIÓN     AUC=0.8998 | Recall=99.40% | Precision=99.54% | F1=0.9947
```

**Archivos que evidencian cada paso:**
- Raw data: `data/raw/*.gz` (40 corridas)
- Entrenamiento: `scripts/fase3_entrenar.py`
- Modelo: `models/isolation_forest.pkl`, `models/scaler.pkl`, `models/features.csv`
- Holdout: `data/normal_holdout.csv` (13,428 flows)
- Métricas: `results/metricas_offline.txt`, `results/resultados_f6_completo.csv`
