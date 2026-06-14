# F3-04 — Almacenamiento, Escalabilidad y Reducción del Volumen de Datos

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F3 — Modelado Offline  
**Verificado en sensor:** 192.168.0.110 — 2026-06-14  

---

## Inventario de Recursos del Sensor

**Hardware del sensor (192.168.0.110):**

| Recurso | Valor |
|---|---|
| CPU | Intel Xeon Bronze 3204 @ 1.90 GHz — 4 cores |
| RAM total | 7.8 GB |
| RAM disponible | 7.0 GB (816 MB en uso) |
| Disco total | 11 GB |
| Disco usado | 4.9 GB (49%) |
| Disco libre | 5.3 GB |

**Tamaño actual de archivos del proyecto:**

| Archivo | Tamaño | Descripción |
|---|---|---|
| `data/dataset_raw.csv` | **75 MB** | Datos sin limpiar (412,097 flows) |
| `data/dataset_labeled.csv` | **75 MB** | Datos etiquetados (intermedio) |
| `data/dataset_clean.csv` | **69 MB** | Dataset limpio (376,827 flows) |
| `data/train.csv` | **48 MB** | 70% cronológico (263,778 flows) |
| `data/val.csv` | **11 MB** | 15% (56,524 flows) |
| `data/test.csv` | **11 MB** | 15% (56,525 flows) |
| `data/raw/` (todos los .gz) | **73 MB** | 34 capturas comprimidas |
| `models/isolation_forest.pkl` | **2,462 KB** | Modelo serializado (300 árboles) |
| `models/scaler.pkl` | **1.3 KB** | StandardScaler (14 medias + 14 desv.) |
| `results/motor_decision.log` | **7.7 MB** | Log acumulado de decisiones |
| `/var/log/suricata/eve.json` | **34 MB** | Log activo (creciendo ~30-40 MB/día) |
| `/var/log/suricata/eve.json.1.gz` | **7.2 MB** | Ayer (logrotate diario) |
| **Total proyecto** | **~390 MB** | — |

**Rendimiento del modelo (medido en el sensor):**

| Métrica | Valor |
|---|---|
| Tiempo de carga del pkl | 183.4 ms |
| Inferencia 1,000 flows | 55.28 ms |
| Inferencia por flow | 0.055 ms |
| Throughput | **18,088 flows/s** |
| Latencia pipeline real P95 | 34.8 ms (dominada por timeout Suricata) |

---

## 1. Estrategia de Almacenamiento

### Qué conservar (permanente)

| Artefacto | Justificación |
|---|---|
| `models/isolation_forest.pkl` (2.4 MB) | Es el núcleo del sistema. Sin él el motor no funciona |
| `models/scaler.pkl` (1.3 KB) | Normalización sin la cual el modelo da resultados erróneos |
| `models/features.csv` | Define el orden de features — cambiar este orden rompe el modelo |
| `results/umbrales_finales.txt` | τ1/τ2 son el resultado de la curva ROC — difíciles de re-derivar |
| `data/raw/*.gz` (73 MB total) | Evidencia experimental original — requerida por PPI para reproducibilidad |
| `data/dataset_clean.csv` (69 MB) | Dataset auditado y validado — base para re-entrenamiento futuro |

### Qué eliminar (después de validación)

| Artefacto | Tamaño | Condición |
|---|---|---|
| `data/dataset_raw.csv` (75 MB) | 75 MB | Puede regenerarse con `parser.py` desde los `.gz` |
| `data/dataset_labeled.csv` (75 MB) | 75 MB | Intermedio — ya incorporado en `dataset_clean.csv` |
| `data/raw/*.json` (no-gz) | Variable | Las versiones sin comprimir duplican las `.gz` |

> Eliminar `dataset_raw.csv` y `dataset_labeled.csv` libera **150 MB** manteniendo reproducibilidad completa (ambos son regenerables desde los `.gz`).

### Qué resumir (agregar)

| Dato | Frecuencia | Resumen propuesto |
|---|---|---|
| `motor_decision.log` (7.7 MB) | Continuo | Rotar diario, comprimir con gzip, retener 30 días |
| `/var/log/suricata/eve.json` (34 MB) | Continuo | Logrotate diario ya configurado (→ 7.2 MB comprimido) |
| Resultados F6 (CSV) | Por corrida | Consolidar en `resultados_f6_completo.csv` (ya hecho) |
| `stats.log` de Suricata (20 MB) | Continuo | Rotar diario — no relevante para el modelo |

---

## 2. Gestión del Volumen

### 2.1 Rotación de Logs — Suricata (`/var/log/suricata/`)

Suricata ya tiene logrotate configurado con rotación diaria:

```
/var/log/suricata/eve.json → eve.json.1.gz  (34 MB → 7.2 MB, ratio 4.7x)
/var/log/suricata/eve.json.2.gz             (2.7 MB — 2 días)
/var/log/suricata/eve.json.4.gz             (5.6 MB — rotación anterior)
```

El script `exportar_eve_por_escenario.sh` complementa esta rotación al final de cada corrida experimental:

```bash
# Comprime el eve.json actual con nombre de escenario
gzip -c /var/log/suricata/eve.json > data/raw/${FECHA}_${GRUPO}_${ESCENARIO}_${NN}_eve.json.gz

# Trunca el eve.json para la siguiente corrida
truncate -s 0 /var/log/suricata/eve.json

# Notifica a Suricata que reabra el archivo
suricatasc -c reopen-log-files
```

### 2.2 Compresión

**Ratio de compresión observado en el dataset:**

| Escenario | Tamaño .gz | Ratio estimado sin comprimir |
|---|---|---|
| anom_synflood | 4.6 MB | ~25-30 MB (alta repetición → buena compresión) |
| mixto_descarga | 4.9 MB | ~25-30 MB |
| anom_bruteforce (corrida 02) | 50 MB | ~250+ MB |
| normal_http | 533 KB | ~2-3 MB |
| normal_ssh | 5.3 KB | ~20 KB |

**Ratio promedio:** gzip logra ~5x en eve.json (JSON Lines altamente repetitivo).

**Recomendación:** usar `gzip -9` para archivos de largo plazo (mayor compresión), `gzip -1` para archivos operativos (mayor velocidad):

```bash
# Archivo de largo plazo (corrida terminada)
gzip -9 /tmp/corrida_backup.json

# Rotación diaria operativa (logrotate)
compress options = gzip -1
```

### 2.3 Política de Retención

| Datos | Retención | Acción al vencer |
|---|---|---|
| `eve.json` (activo) | Continuo | Rotar diario |
| `eve.json.N.gz` (histórico) | 7 días | Eliminar |
| `data/raw/*.gz` (corridas) | Permanente | Conservar para reproducibilidad PPI |
| `motor_decision.log` | 30 días | Comprimir y archivar |
| `dataset_clean.csv` | Permanente | Conservar |
| Modelos `.pkl` | Permanente (versionar al re-entrenar) | No eliminar sin respaldo |

### 2.4 Agregación de Flujos para Producción

En un entorno de producción con tráfico mayor, en lugar de registrar cada flow individualmente se pueden agregar por ventana temporal:

```
Ventana de 1 segundo por src_ip:
  flows_count, avg_pkt_rate, max_pkt_rate,
  total_bytes, proto_distribution, unique_dest_ports
```

Esto reduciría el volumen de datos por factor 10-100x manteniendo la información estadística relevante para detección.

---

## 3. Reducción de Dimensionalidad

### 3.1 Análisis PCA — Resultados Reales

Se aplicó PCA sobre 10,000 flows del training set (14 features normalizadas con StandardScaler). Resultados medidos en el sensor:

| Componente | Varianza explicada | Varianza acumulada |
|---|---|---|
| PC1 | **56.75%** | 56.75% |
| PC2 | **33.51%** | **90.26%** |
| PC3 | 5.45% | 95.71% |
| PC4 | 2.97% | 98.69% |
| PC5 | 1.07% | **99.75%** |
| PC6 | 0.19% | 99.94% |
| PC7–PC14 | < 0.06% total | 100.00% |

**Conclusión:** 2 componentes capturan el 90.26% de la varianza; 5 componentes el 99.75%.

**Interpretación:** La alta concentración en PC1 (56.75%) sugiere que `pkt_rate` y `byte_rate` (features de alta magnitud) dominan la varianza. PC2 complementa con la asimetría (ratios).

### 3.2 ¿Conviene aplicar PCA al modelo actual?

| Criterio | Con 14 features (actual) | Con PCA a 5 componentes |
|---|---|---|
| Varianza preservada | 100% | 99.75% |
| Throughput inferencia | 18,088 flows/s | ~18,500 flows/s (ganancia marginal) |
| Interpretabilidad | ✅ Alta (features con nombres) | ❌ Baja (combinaciones lineales) |
| Explicabilidad (z-score) | ✅ `feat:z=+X.X` visible al usuario | ❌ No aplicable directamente |
| Latencia real (P95) | 34.8 ms | ~34.7 ms |

**Decisión:** PCA **no se implementa** en el sistema actual porque:
1. La ganancia de velocidad es marginal (18,088 → ~18,500 flows/s — ya ambos son >100x el requisito de 29 flows/s).
2. La feature `explicar_anomalia()` del motor usa z-scores directamente sobre las 14 features por nombre. Con PCA esto se perdería.
3. Con solo 14 features el modelo ya es muy ligero (2.4 MB).

### 3.3 Selección de Características

Se evaluó la importancia de cada feature basándose en la separación de scores entre tráfico normal y anómalo:

| Feature | Separación (|μ_anom - μ_norm|/σ) | Importancia |
|---|---|---|
| `pkt_rate` | Alta (P95 normal=1,000 · P95 anom=10,000) | ★★★★★ |
| `byte_rate` | Alta (P95 normal=60K · P95 anom=1.6M B/s) | ★★★★★ |
| `is_icmp` | Perfecta (solo en floods ICMP) | ★★★★★ |
| `is_udp` | Alta (99%+ de UDP es anómalo en el lab) | ★★★★ |
| `dest_port` | Alta (puertos inusuales en port scan) | ★★★★ |
| `pkts_toserver` | Alta (7,273 máx en SYN flood) | ★★★★ |
| `bytes_toclient` | Alta (0 en floods unidireccionales) | ★★★★ |
| `pkt_ratio` | Media-Alta | ★★★ |
| `byte_ratio` | Media | ★★★ |
| `avg_pkt_size` | Media (60B SYN vs 100-1400B HTTP) | ★★★ |
| `pkts_toclient` | Media | ★★★ |
| `bytes_toserver` | Media | ★★ |
| `duration` | Baja-Media (88.7% = 0 en ambas clases) | ★★ |
| `is_tcp` | Baja (TCP aparece en normal y anómalo) | ★★ |

**Subconjunto mínimo viable:** `pkt_rate`, `byte_rate`, `is_icmp`, `is_udp`, `dest_port`, `pkts_toserver`, `bytes_toclient`, `pkt_ratio` (8 features) podrían mantener AUC > 0.93 según la distribución observada.

---

## 4. Optimización para Machine Learning

### 4.1 Tiempo de Entrenamiento

**Entrenamiento actual:**

```python
IsolationForest(n_estimators=300, max_samples='auto', n_jobs=-1)
clf.fit(X_n)   # X_n: 684 flows × 14 features
```

| Parámetro | Valor actual | Impacto |
|---|---|---|
| `n_estimators` | 300 | Mayor = más preciso pero más lento y más RAM |
| `max_samples` | 'auto' = min(256, n) = 256 | Submuestreo por árbol |
| `n_jobs` | -1 (todos los cores) | Paralelismo en construcción |
| Tiempo de entrenamiento | < 5 s sobre 684 flows | Mínimo |

El análisis de sensibilidad (F3) mostró que AUC se estabiliza en N≈200-300 estimadores. Re-entrenar con más datos normales (si se capturan nuevos escenarios) seguirá siendo rápido porque `max_samples=256` limita el tamaño de cada árbol.

**Optimización para re-entrenamiento frecuente:**

```python
# Warm start: añadir estimadores sin reentrenar todos
clf.set_params(n_estimators=clf.n_estimators + 50, warm_start=True)
clf.fit(X_new_normal)
```

### 4.2 Consumo de RAM

| Componente | RAM en uso |
|---|---|
| Modelo IF (pkl cargado) | ~2.4 MB |
| Scaler | < 1 KB |
| Buffer de features (1 flow) | < 1 KB |
| `seguir_eve()` (una línea JSON) | < 10 KB |
| **Motor completo** | **< 5 MB** |

El motor `motor_decision.py` procesa flows **uno por uno** (streaming), nunca carga el dataset completo en memoria. Esto lo hace viable en el sensor con 7.8 GB RAM usando menos del 0.1% de RAM disponible.

**Comparación con alternativas:**

| Algoritmo | RAM para inferencia | RAM para entrenamiento |
|---|---|---|
| Isolation Forest (actual) | ~5 MB | ~50 MB con dataset completo |
| One-Class SVM | ~200 MB (kernel matrix) | >1 GB |
| Random Forest (100 árboles) | ~50 MB | ~500 MB |
| Autoencoder PyTorch | ~100 MB (modelo) | >2 GB con GPU |

### 4.3 Consumo de CPU

**En producción (motor_decision.py):**

```
Ciclo por flow:
  1. readline() eve.json     → < 0.1 ms
  2. json.loads()            → < 0.2 ms
  3. extract_features()      → < 0.5 ms
  4. scaler.transform()      → < 0.5 ms
  5. clf.score_samples()     → 0.055 ms (medido)
  6. decidir() + ipset SSH   → 5-30 ms (latencia de red domina)
```

El motor consume < 1% de CPU en idle (sin tráfico), con picos de ~5% durante ataques de alta tasa. Los 4 cores del Xeon Bronze 3204 son más que suficientes.

**En entrenamiento (fase3_isolation_forest.py):**

Con `n_jobs=-1` Isolation Forest usa los 4 cores para construir los 300 árboles en paralelo. Con 684 flows de entrenamiento el tiempo total es < 10 segundos.

---

## 5. Arquitectura Escalable

### 5.1 Crecimiento de Datos

**Proyección de crecimiento de eve.json:**

| Escenario | Flows/día | eve.json/día | Comprimido |
|---|---|---|---|
| Lab actual (ocioso) | ~1,000 | ~2 MB | ~400 KB |
| Lab con escenarios | ~100,000 | ~200 MB | ~40 MB |
| Red universitaria real | ~1M+ | ~2 GB | ~400 MB |
| Red empresarial | ~10M+ | ~20 GB | ~4 GB |

**El sistema actual es viable hasta ~100,000 flows/día** con la infraestructura del sensor. Para redes más grandes se requieren los cambios de §5.2.

### 5.2 Nuevos Escenarios de Ataque

Agregar un nuevo escenario de ataque requiere:

1. **Capturar** una corrida con `exportar_eve_por_escenario.sh`
2. **Procesar** con `parser.py` → `etiquetar_limpiar.py`
3. **Evaluar** si el nuevo ataque es detectado (sin re-entrenar — generalización)
4. **Re-entrenar** solo si el AUC baja significativamente
5. **Derivar** nuevos τ1/τ2 con `auc_roc_umbrales.py`
6. **Actualizar** `motor_decision.py` y reiniciar `ppi-motor.service`

El tiempo estimado de todo el ciclo: **30-60 minutos** en el hardware actual.

### 5.3 Nuevos Datasets

**Para incorporar tráfico de una nueva red:**

```
Nueva red → Suricata en nuevo sensor → eve.json
    ↓
parser.py (mismo script, sin cambios)
    ↓
etiquetar_limpiar.py (ajustar NORMAL_IPS para las IPs de la nueva red)
    ↓
Concatenar con dataset_clean.csv existente
    ↓
Re-entrenar IF con los flows normales del nuevo entorno
    ↓
Nuevo isolation_forest.pkl + scaler.pkl
```

El único cambio de código necesario es ajustar `NORMAL_IPS` en `etiquetar_limpiar.py` y `motor_decision.py`.

### 5.4 Arquitectura Propuesta para Escala Mayor

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE INGESTIÓN                        │
│  Suricata 1  →  eve.json  ─┐                               │
│  Suricata 2  →  eve.json  ─┤→  Kafka Topic: eve-flows      │
│  Suricata N  →  eve.json  ─┘    (particionado por sensor)  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE PROCESAMIENTO                      │
│  motor_decision.py (por sensor)  →  scores en tiempo real  │
│  Agregación 1min/5min por src_ip (ventana deslizante)       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE ALMACENAMIENTO                     │
│  Hot:  Redis/ClickHouse  →  últimas 24h de flows           │
│  Warm: Parquet + gzip    →  últimos 30 días                 │
│  Cold: S3/MinIO          →  histórico comprimido            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              CAPA DE MODELOS (Multi-tenant)                 │
│  Modelo global (entrenado en todos los sensores)            │
│  Modelo local  (fine-tuned por red/sensor)                  │
│  Re-entrenamiento automático semanal (cron + CI/CD)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Mejoras Implementables

### Mejora 1 — Eliminar archivos intermedios redundantes

**Viabilidad:** Inmediata · **Ahorro:** ~150 MB

```bash
# Liberar espacio conservando reproducibilidad
rm /home/m4rk/ppi-surikata-producto/data/dataset_raw.csv
rm /home/m4rk/ppi-surikata-producto/data/dataset_labeled.csv
# Ambos son regenerables con: python3 scripts/parser.py && python3 scripts/etiquetar_limpiar.py
```

### Mejora 2 — Rotación automática de motor_decision.log

**Viabilidad:** Inmediata · **Archivo:** `/etc/logrotate.d/ppi-motor`

```
/home/m4rk/ppi-surikata-producto/results/motor_decision.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl kill -s HUP ppi-motor.service
    endscript
}
```

Esto mantiene 30 días de historial y comprime automáticamente los logs anteriores.

### Mejora 3 — Convertir dataset_clean.csv a Parquet

**Viabilidad:** Media (requiere instalar pyarrow en venv) · **Ahorro:** ~50% en tamaño

```python
import pandas as pd
df = pd.read_csv('data/dataset_clean.csv')
df.to_parquet('data/dataset_clean.parquet', compression='snappy')
# 69 MB CSV → ~35 MB Parquet (estimado)
# Lectura 3-5x más rápida para re-entrenamiento
```

### Mejora 4 — Reducir n_estimators a 100

**Viabilidad:** Inmediata · **Ganancia:** modelo 3x más pequeño (800 KB vs 2.4 MB), carga en ~60 ms

El análisis de sensibilidad (F3) mostró que AUC se estabiliza en N≈200-300 flows de entrenamiento, no en estimadores. Con 100 estimadores:
- AUC estimado: 0.940-0.944 (pérdida < 0.5%)
- Tamaño pkl: ~800 KB
- Carga: ~60 ms vs 183 ms actual
- Throughput inferencia: ~25,000 flows/s

### Plan de Implementación

| Mejora | Prioridad | Tiempo | Riesgo |
|---|---|---|---|
| Eliminar CSV redundantes | Alta | 5 min | Bajo (regenerables) |
| Logrotate motor_decision.log | Alta | 15 min | Bajo |
| Parquet dataset_clean | Media | 30 min | Bajo |
| Reducir n_estimators a 100 | Baja | 1 hora (re-entrenar + validar) | Bajo |
| Arquitectura Kafka/ClickHouse | Baja (futuro) | Semanas | Alto |

---

## Resumen Ejecutivo

| Aspecto | Estado actual | Estado propuesto |
|---|---|---|
| Disco usado | 390 MB proyecto | ~240 MB (−150 MB con mejoras 1-2) |
| RAM motor | < 5 MB | Sin cambio |
| Throughput | 18,088 flows/s | ~25,000 flows/s (con n_estimators=100) |
| Latencia P95 | 34.8 ms | Sin cambio (dominada por Suricata timeout) |
| Log management | Manual | Automático con logrotate |
| Escalabilidad | 1 sensor · lab | Multi-sensor con Kafka/Parquet |

> El sistema actual está bien dimensionado para el laboratorio universitario. Los cuellos de botella no son computacionales sino de I/O (latencia Suricata) — el modelo IF es 600x más rápido de lo necesario (18,088 flows/s vs 29 flows/s requeridos).

---

## Referencias

| Archivo | Ruta | Descripción |
|---|---|---|
| `exportar_eve_por_escenario.sh` | `scripts/capture/` | Compresión y rotación de capturas |
| `fase3_isolation_forest.py` | `scripts/` | Entrenamiento con n_jobs=-1 |
| `motor_decision.py` | `scripts/` | Inferencia streaming (1 flow a la vez) |
| `isolation_forest.pkl` | `models/` | 2.4 MB — 300 árboles serializado |
| `ppi-motor.service` | `/etc/systemd/system/` | Servicio systemd del motor |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
