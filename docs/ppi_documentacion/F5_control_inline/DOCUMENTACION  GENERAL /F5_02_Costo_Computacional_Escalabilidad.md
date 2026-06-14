# F5-02: Costo Computacional, Escalabilidad y Preparación para Producción

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F5 — Control Inline  
**Documento:** F5-02 — Costo Computacional, Escalabilidad y Preparación para Producción  
**Fecha:** 2026-06-14  
**Estado:** Validado con datos reales del laboratorio

---

## 1. Análisis de Costo Computacional por Etapa

### 1.1 Hardware del Sensor (Medido en Laboratorio)

| Recurso | Especificación | Uso en Reposo | Uso con Tráfico | Uso Pico (Flood) |
|---|---|---|---|---|
| CPU | Intel Xeon Bronze 3204, 4 cores, 1.9GHz | ~3% | ~8–12% | ~22% |
| RAM | 7.8 GB disponibles | ~2.1 GB | ~2.4 GB | ~2.7 GB |
| Disco | SSD, lectura aleatoria ~400MB/s | — | ~2 MB/s | ~8 MB/s |
| Red (ens35) | Captura promiscua Suricata | — | ~5–50 Mbps | ~800 Mbps |

**Observación clave:** Incluso durante ataques flood (hping3 --flood), el uso de CPU no supera el 22%, dejando más del 75% libre. El cuello de botella potencial no es el motor Python sino la escritura de eve.json en disco a alta velocidad de paquetes.

### 1.2 Desglose por Etapa del Pipeline

| Etapa | Proceso | Latencia media | CPU core | RAM peak | Notas |
|---|---|---|---|---|---|
| E1 | Suricata: captura paquetes + disección | — | ~35% (1 core) | ~180 MB | Corren hilos en parallel por AF_PACKET |
| E2 | Suricata: escritura eve.json (JSONL) | — | ~5% (I/O) | — | fsync por flujo cerrado |
| E3 | motor_decision.py: tail + parse JSON | 0.3 ms | <1% | ~45 MB | select() non-blocking |
| E4 | derive_features(): calcular 14 features | 0.1 ms | <1% | — | Solo aritmética NumPy |
| E5 | scaler.transform(): StandardScaler | 0.2 ms | <1% | ~8 MB | Matriz 1×14 |
| E6 | IF.score_samples(): inferencia | 8–15 ms | ~2% | ~2.4 MB | IF pkl cargado en RAM |
| E7 | Evaluación τ1/τ2 + heurísticas | 0.05 ms | <1% | — | Comparaciones simples |
| E8 | enforce.sh: ipset add/del | 2–5 ms | ~1% | — | Shell fork por acción |
| E9 | Log + Telegram (async) | <1 ms | <1% | — | aiohttp non-blocking |
| **TOTAL** | **E2 → E8 (latencia observable)** | **P50=18ms, P95=34.8ms** | **<5% agregado** | **~235 MB** | **Req. <500ms: CUMPLE** |

### 1.3 Análisis del Modelo Isolation Forest

| Parámetro | Valor |
|---|---|
| n_estimators | 300 |
| max_samples | 256 (auto) |
| Flujos de entrenamiento | 684 normales |
| Tiempo de entrenamiento | <1 segundo |
| Tamaño modelo serializdo (.pkl) | 2.4 MB |
| Tamaño scaler (.pkl) | 0.8 KB |
| RAM en ejecución | ~2.4 MB (modelo) + ~45 MB (intérprete Python) |
| Inferencia por flujo | 8–15 ms |
| Throughput máximo medido | ~67 flujos/segundo (1 core) |

**Throughput real vs. capacidad:** En el laboratorio se generan máximo ~15 flujos/segundo durante SYN flood (Suricata agrega paquetes en flujos). El motor procesa 4–5× más rápido de lo necesario.

### 1.4 Costo de Almacenamiento por Corrida

| Tipo de dato | Tamaño por corrida | Corridas totales F6 | Total |
|---|---|---|---|
| eve.json.gz (raw) | ~2–15 MB | 40 | ~220 MB |
| motor_decision.log | ~500 KB | 40 | ~20 MB |
| dataset_clean.csv | 18.3 MB (global) | 1 | 18.3 MB |
| train/val/test.csv | ~12 MB (global) | 1 | 12 MB |
| Modelos (.pkl) | 2.4 MB + 0.8 KB | 1 versión activa | ~2.4 MB |
| **Total laboratorio** | | | **~273 MB** |

**Proyección producción (1 año, red corporativa 500 usuarios):** ~12–18 GB/año en logs comprimidos, manejable con retención de 90 días activa + archivado.

---

## 2. Estrategias de Optimización

### 2.1 Selección de Features — Reducción sin Pérdida

Feature importance calculada con Random Forest de referencia sobre el dataset de 376,827 flujos:

| Rank | Feature | Importancia RF | ¿Eliminar? |
|---|---|---|---|
| 1 | dest_port | 0.181 | NO — discrimina servicios |
| 2 | is_tcp | 0.176 | NO — protocolo clave |
| 3 | byte_rate | 0.119 | NO — intensidad de ataque |
| 4 | pkt_rate | 0.098 | NO — velocidad flood |
| 5 | bytes_toclient | 0.087 | NO — asimetría C/S |
| 6 | bytes_toserver | 0.079 | NO — asimetría C/S |
| 7 | duration | 0.071 | NO — flujos cortos = scan |
| 8 | avg_pkt_size | 0.065 | NO — tamaño característico |
| 9 | pkt_ratio | 0.048 | Opcional — correlacionada con pkt_rate |
| 10 | byte_ratio | 0.041 | Opcional — correlacionada con byte_rate |
| 11 | pkts_toserver | 0.021 | Reemplazable por pkt_rate |
| 12 | pkts_toclient | 0.018 | Reemplazable |
| 13 | is_udp | 0.010 | Mantener (UDP flood) |
| 14 | is_icmp | 0.006 | Mantener (ICMP flood) |

**Conclusión:** El set de 14 features está ya optimizado. Eliminar pkt_ratio y byte_ratio reduciría a 12 features con pérdida de AUC estimada <0.002. No se recomienda para el MVP actual.

### 2.2 Estrategia Batch vs. Streaming

```
ACTUAL (Streaming puro):
  eve.json → tail line-by-line → proceso inmediato → ipset

ALTERNATIVA Micro-batch (mejora latencia media):
  eve.json → buffer 50ms → lote de N flujos → numpy batch → ipset batch

  Ventaja: score_samples([N flujos]) es ~3× más rápido que N × score_samples([1 flujo])
  Desventaja: agrega 50ms de latencia máxima extra
  Veredicto: Para el MVP con 67 flujos/s max, no necesario.
  
RECOMENDADO EN PRODUCCIÓN (>500 flujos/s):
  Micro-batch con ventana de 100ms
  → throughput aumenta 5–8× (de ~67 a ~350 flujos/s en 1 core)
```

### 2.3 Optimizaciones de Inferencia Aplicables

```python
# Opción 1: Reducir n_estimators en producción con validación previa
# n_estimators=100 reduce latencia E6 de 12ms a ~4ms con AUC-drop < 0.003

# Opción 2: Cache de decisiones para IPs repetidas en ventana 30s
from functools import lru_cache
import time

ip_cache = {}  # {ip: (decision, score, timestamp)}
CACHE_TTL = 30

def get_cached_decision(ip, score):
    if ip in ip_cache:
        cached_decision, cached_score, ts = ip_cache[ip]
        if time.time() - ts < CACHE_TTL:
            # Solo usar cache si score actual ≈ score cacheado (±0.05)
            if abs(score - cached_score) < 0.05:
                return cached_decision
    return None

# Opción 3: Compilar con Numba (JIT) la función derive_features()
# Reduce E4 de 0.1ms a ~0.01ms en Python puro
```

### 2.4 Compresión y Eficiencia de Almacenamiento

| Técnica | Aplicación | Ratio | Impacto |
|---|---|---|---|
| gzip eve.json | Ya implementado (exportar_eve_por_escenario.sh) | ~8:1 | 15MB → ~2MB |
| Parquet para dataset_clean | Reemplazar CSV en producción | ~5:1 + columnar | Queries 10× más rápidas |
| LZ4 para logs en tiempo real | motor_decision.log streaming | ~3:1 + bajo CPU | Para alto volumen |
| Retención escalonada | Hot 30d / Warm 90d / Cold 1yr | — | Control costo almacenamiento |

---

## 3. Escalabilidad

### 3.1 Escalabilidad Vertical (Más Tráfico en el Mismo Sensor)

| Escenario | Flujos/s | 1 Worker | 4 Workers (multiproc) | 8 Workers |
|---|---|---|---|---|
| Lab actual | ≤15 | OK (P95=34.8ms) | — | — |
| Red corporativa 50 usuarios | ~100 | OK (~50ms) | — | — |
| Red corporativa 200 usuarios | ~400 | Saturación | OK (~30ms) | — |
| Red corporativa 1000 usuarios | ~2000 | No viable | OK con micro-batch | OK |
| ISP / Campus universitario | >5000 | No viable | No viable | + balanceo |

**Código de escalado vertical (multiprocessing):**

```python
# motor_decision_parallel.py — extensión para producción
from multiprocessing import Pool, Queue, Manager
import numpy as np

def worker_process(flow_queue, result_queue, model, scaler):
    """Worker que consume flujos y produce decisiones."""
    while True:
        batch = []
        while not flow_queue.empty() and len(batch) < 50:
            batch.append(flow_queue.get(timeout=0.1))
        
        if batch:
            features = np.array([derive_features(f) for f in batch])
            features_scaled = scaler.transform(features)
            scores = model.score_samples(features_scaled)
            for flow, score in zip(batch, scores):
                decision = classify(score, flow)
                result_queue.put((flow['src_ip'], decision, score))

# Lanzar N workers según cores disponibles
NUM_WORKERS = max(1, cpu_count() - 1)  # reservar 1 core para Suricata
```

### 3.2 Escalabilidad Horizontal (Más Servidores Protegidos)

```
Arquitectura Single-Sensor (actual):
  [Kali .100] ──────────────────┐
  [Win11 .10]  ─── SWITCH ───── [Sensor .110] ──── [Servidor .120]
  [Desktop .20] ─────────────────┘      │
                                         └── ipset (ppi_blocked, ppi_limited)

Arquitectura Multi-Server (producción):
  [Internet]
       │
  [Firewall Perimetral]
       │
  [Sensor Central .110] ←── Suricata en SPAN port / TAP óptico
       │                         │
       ├── ipset sync ──────► [Servidor Web .120]
       ├── ipset sync ──────► [Servidor Mail .121]  
       ├── ipset sync ──────► [Servidor BD .122]
       └── ipset sync ──────► [Servidor App .123]

Mecanismo de sincronización:
  ipset save | ssh m4rk@192.168.0.121 "ipset restore -!"
  # Sincronización cada 5s vía rsync o ipset-sync daemon
```

### 3.3 Escalabilidad Multi-Sensor (Campus / ISP)

```
Arquitectura Distribuida:

  Edificio A: [Sensor A] ─── Kafka topic: flows.A ──┐
  Edificio B: [Sensor B] ─── Kafka topic: flows.B ──┤── [Agregador Central]
  Edificio C: [Sensor C] ─── Kafka topic: flows.C ──┘         │
                                                          [Motor IF Central]
                                                                │
                                                     [Policy Distribution]
                                                                │
                                            ┌───────────────────────────────┐
                                            ▼           ▼           ▼
                                      [Sensor A]   [Sensor B]  [Sensor C]
                                      (enforcer)   (enforcer)  (enforcer)

Kafka config mínima:
  topics: flows.raw (partitions=N_sensores, replication=2)
  retention: 1h (solo flujos no procesados)
  consumer group: motor-decision-cluster
```

### 3.4 Escalabilidad ante Nuevos Tipos de Ataques

La arquitectura unsupervised de Isolation Forest escala naturalmente:

| Dimensión | Comportamiento | Requiere acción |
|---|---|---|
| Nuevo ataque (p.ej. DNS amplification) | IF detecta anomalía por score | Solo validar τ1/τ2 siguen válidos |
| Variante de ataque conocido | IF detecta si difiere del baseline | No requiere acción |
| Ataque evasivo (mimics normal) | Score borderline → heurísticas | Agregar heurística específica |
| Volumen 10× más tráfico | Solo afecta throughput, no accuracy | Escalar workers |
| Nuevos protocolos | Requiere nuevas features | Reentrenamiento + nuevo feature set |

### 3.5 Escalabilidad de Usuarios y Roles

| Rol | Acceso actual (lab) | Acceso producción |
|---|---|---|
| Administrador principal | SSH directo al sensor | VPN + SSH con 2FA |
| Analista SOC | Ver dashboard.py | Web dashboard (Grafana) + alertas |
| Ingeniero de redes | Modificar whitelist | API REST limitada a whitelist |
| Auditor | Leer logs | Acceso read-only a Elasticsearch |
| CISO | — | Dashboard ejecutivo (KPIs) |

---

## 4. Gestión de Almacenamiento

### 4.1 Política de Retención

```bash
# /etc/cron.d/ppi-retention — Ejecutado diariamente a 02:00
0 2 * * * m4rk /home/m4rk/ppi-surikata-producto/scripts/maintenance/retention.sh

# retention.sh
#!/usr/bin/env bash
PROJECT="/home/m4rk/ppi-surikata-producto"
DATA_RAW="${PROJECT}/data/raw"
LOGS="${PROJECT}/results"
ARCHIVE="/mnt/backup/ppi-archive"

# Hot: mantener últimos 30 días en raw/
find "${DATA_RAW}" -name "*.eve.json.gz" -mtime +30 -exec mv {} "${ARCHIVE}/raw/" \;

# motor_decision.log: rotar cuando supera 500MB
LOG_SIZE=$(du -sm "${LOGS}/motor_decision.log" | cut -f1)
if [ "${LOG_SIZE}" -gt 500 ]; then
    mv "${LOGS}/motor_decision.log" "${LOGS}/motor_decision_$(date +%Y%m%d).log"
    gzip "${LOGS}/motor_decision_$(date +%Y%m%d).log"
    touch "${LOGS}/motor_decision.log"
fi

# Cold: eliminar archivos > 365 días
find "${ARCHIVE}" -mtime +365 -delete

echo "[$(date)] Retención ejecutada. Espacio libre: $(df -h ${PROJECT} | tail -1 | awk '{print $4}')"
```

### 4.2 Proyección de Crecimiento de Datos

| Horizonte | Flujos acumulados | eve.json.gz | motor_decision.log | dataset_clean.csv |
|---|---|---|---|---|
| Fin F6 (actual) | 376,827 | ~220 MB | ~20 MB | 18.3 MB |
| 6 meses producción | ~8M | ~2 GB | ~450 MB | ~350 MB |
| 1 año producción | ~18M | ~4.5 GB | ~900 MB | ~750 MB |
| 3 años producción | ~55M | ~14 GB | ~2.8 GB | ~2.2 GB |

**Estrategia:** Con retención 90 días activa + archivado comprimido, el almacenamiento activo nunca supera ~3 GB. El archivado histórico se gestiona con S3/MinIO o NAS externo.

### 4.3 Compresión por Etapa

```
Pipeline de compresión en producción:

eve.json (write stream)
    │ gzip -9 al cierre de corrida → 8:1
    ▼
raw/*.eve.json.gz (30 días hot)
    │ tar + xz al archivar → 12:1 adicional
    ▼  
archive/YYYY/MM/*.tar.xz (cold storage)

motor_decision.log (append stream)
    │ logrotate: compress + rotate semanal
    ▼
results/motor_decision_YYYYWW.log.gz

dataset_clean.csv (static after training)
    │ Convertir a Parquet en producción
    ▼
data/dataset_clean.parquet (5:1 vs CSV + columnar indexing)
```

### 4.4 Backup y Recuperación

| Componente | Backup | Frecuencia | RTO | RPO |
|---|---|---|---|---|
| isolation_forest.pkl + scaler.pkl | rsync a NAS | Tras cada reentrenamiento | 2 min | 0 |
| umbrales_finales.txt | Git + rsync | Tras cada cambio | 1 min | 0 |
| dataset_clean.csv / train/val/test | rsync a NAS | Diario 02:00 | 10 min | 24h |
| motor_decision.log | logrotate + rsync | Horario | 5 min | 1h |
| Configuración Suricata | Git | Tras cada cambio | 3 min | 0 |
| Reglas ipset | `ipset save` al cron | Cada 5 min | 1 min | 5 min |

---

## 5. Roadmap hacia Producción Real

### 5.1 Las 4 Fases de Madurez

```
FASE 0 — LABORATORIO (ESTADO ACTUAL)
══════════════════════════════════════
Entorno:   4 VMs en VMware / red NAT 192.168.0.0/24
Tráfico:   Sintético (hping3, nmap, hydra, curl)
Sensores:  1 (Ubuntu .110)
Servidores: 1 (Ubuntu Server .120)
Métricas:  Recall=99.3%, AUC=0.9440, P95=34.8ms
Estado:    ✅ VALIDADO (F6 — 40 corridas)

FASE 1 — PILOTO CONTROLADO (6–12 meses)
══════════════════════════════════════════
Entorno:   Red real de laboratorio universitario (UPeU)
Tráfico:   Mixto real + simulado
Sensores:  1–2 (span port de switch core)
Usuarios:  50–100 (aula/laboratorio)
Cambios requeridos:
  □ Modo MONITOR (log sin bloquear) por 30 días
  □ Validar τ1/τ2 con tráfico real universitario
  □ Ajustar whitelist (impresoras, APs, VoIP)
  □ Dashboard web básico (Grafana)
  □ Alertas email/Telegram en producción
Riesgo:    BAJO — sin bloqueo en modo monitor

FASE 2 — PRE-PRODUCCIÓN (12–18 meses)
═══════════════════════════════════════
Entorno:   Red de producción controlada (una VLAN)
Tráfico:   Real
Modo:      LIMIT activado, BLOCK con aprobación manual
Sensores:  2–3 (redundancia)
Cambios requeridos:
  □ HA (High Availability): sensor primario + backup
  □ Reentrenamiento mensual automático
  □ Integración SIEM (Wazuh / Elasticsearch)
  □ Proceso de whitelist management
  □ SLA: <500ms latencia garantizado (hoy: P95=34.8ms ✅)
  □ Auditoría de bloqueos (quién bloqueó qué y cuándo)
Riesgo:    MEDIO — LIMIT puede afectar usuarios legítimos

FASE 3 — PRODUCCIÓN (18+ meses)
══════════════════════════════════
Entorno:   Red completa institucional
Modo:      Full BLOCK automático
Sensores:  N (según topología)
Cambios requeridos:
  □ SOC 24/7 o on-call rotativo
  □ Proceso formal de IR (Incident Response)
  □ Cumplimiento normativo (ISO 27001 / NIST CSF)
  □ Penetration testing anual
  □ Escalabilidad multi-sensor validada
  □ Modelo reentrenado con datos de producción
Riesgo:    GESTIONADO — proceso maduro
```

### 5.2 Lista de Verificación por Fase

**Para pasar de Fase 0 → Fase 1:**

```
□ Obtener aprobación de jefatura de TI/redes universitaria
□ Documentar alcance y exclusiones del piloto
□ Instalar sensor en span port (sin tocar producción)
□ Ejecutar 30 días en modo MONITOR (log-only)
□ Analizar falsos positivos con datos reales
□ Capacitar al operador del sistema
□ Establecer canal de alerta (Telegram / email)
□ Tener plan de rollback documentado
```

---

## 6. MLOps — Operacionalización del Modelo

### 6.1 Versionado de Modelos

```
models/
├── isolation_forest_v1.0.0.pkl    ← versión producción actual
├── isolation_forest_v1.0.1.pkl    ← candidato (reentrenado)
├── scaler_v1.0.0.pkl
├── scaler_v1.0.1.pkl
├── features_v1.0.0.csv            ← 14 features que usó v1.0.0
├── CHANGELOG.md                   ← qué cambió y por qué
└── manifest.json                  ← versión activa + checksums SHA256
```

```json
// manifest.json
{
  "active_version": "1.0.0",
  "models": {
    "1.0.0": {
      "isolation_forest": "sha256:a3f2...",
      "scaler": "sha256:b8c1...",
      "features": "sha256:d4e9...",
      "trained_date": "2026-05-15",
      "train_flows": 684,
      "auc_roc": 0.9440,
      "tau1": -0.4973,
      "tau2": -0.6873,
      "status": "production"
    },
    "1.0.1": {
      "status": "candidate",
      "trained_date": "2026-06-14"
    }
  }
}
```

### 6.2 Pipeline de Reentrenamiento

```bash
# retrain_pipeline.sh — ejecutado por cron o trigger manual
#!/usr/bin/env bash
set -euo pipefail

PROJECT="/home/m4rk/ppi-surikata-producto"
VENV="${PROJECT}/../ppi-sensor/venv/bin/python3"
VERSION="$(date +%Y%m%d)"

echo "[$(date)] Iniciando reentrenamiento v${VERSION}"

# 1. Recolectar flujos PERMIT de las últimas 4 semanas
"${VENV}" "${PROJECT}/scripts/collect_permit_flows.py" \
    --log "${PROJECT}/results/motor_decision.log" \
    --days 28 \
    --min-flows 2000 \
    --output "${PROJECT}/data/retrain_${VERSION}.csv"

# 2. Validar calidad del dataset
"${VENV}" "${PROJECT}/scripts/validate_retrain_data.py" \
    --input "${PROJECT}/data/retrain_${VERSION}.csv" \
    --min-flows 2000 || { echo "ABORT: datos insuficientes"; exit 1; }

# 3. Entrenar nuevo modelo
"${VENV}" "${PROJECT}/scripts/retrain_model.py" \
    --data "${PROJECT}/data/retrain_${VERSION}.csv" \
    --output-model "${PROJECT}/models/isolation_forest_v${VERSION}.pkl" \
    --output-scaler "${PROJECT}/models/scaler_v${VERSION}.pkl"

# 4. Evaluar candidato vs. producción (A/B offline con test.csv)
EVAL_RESULT=$("${VENV}" "${PROJECT}/scripts/evaluate_candidate.py" \
    --candidate "${PROJECT}/models/isolation_forest_v${VERSION}.pkl" \
    --baseline "${PROJECT}/models/isolation_forest_v1.0.0.pkl" \
    --testset "${PROJECT}/data/test.csv")

AUC_CANDIDATE=$(echo "${EVAL_RESULT}" | jq '.auc_candidate')
AUC_BASELINE=$(echo "${EVAL_RESULT}" | jq '.auc_baseline')

# 5. Gate: solo promover si AUC_candidato >= AUC_baseline - 0.005
if (( $(echo "${AUC_CANDIDATE} >= ${AUC_BASELINE} - 0.005" | bc -l) )); then
    cp "${PROJECT}/models/isolation_forest_v${VERSION}.pkl" \
       "${PROJECT}/models/isolation_forest.pkl"
    cp "${PROJECT}/models/scaler_v${VERSION}.pkl" \
       "${PROJECT}/models/scaler.pkl"
    echo "[$(date)] Modelo v${VERSION} promovido a producción. AUC=${AUC_CANDIDATE}"
    # 6. Recargar motor (enviar SIGHUP)
    pkill -SIGHUP -f motor_decision.py || systemctl restart ppi-motor.service
else
    echo "[$(date)] WARN: Candidato v${VERSION} rechazado. AUC candidato=${AUC_CANDIDATE} < baseline=${AUC_BASELINE}"
fi
```

### 6.3 Monitoreo de Deriva (Concept Drift)

```python
# drift_monitor.py — detecta si el tráfico actual difiere del entrenamiento
from scipy.stats import ks_2samp
import numpy as np
import json

DRIFT_THRESHOLD = 0.05  # p-value KS test

def check_drift(train_scores: np.ndarray, recent_scores: np.ndarray) -> dict:
    """
    Compara distribución de scores de entrenamiento vs. últimas 24h.
    Si p-value < threshold, hay deriva significativa → alerta de reentrenamiento.
    """
    stat, p_value = ks_2samp(train_scores, recent_scores)
    
    drift_detected = p_value < DRIFT_THRESHOLD
    severity = "NONE"
    if drift_detected:
        if stat > 0.3:
            severity = "CRITICAL"
        elif stat > 0.15:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
    
    return {
        "ks_statistic": float(stat),
        "p_value": float(p_value),
        "drift_detected": drift_detected,
        "severity": severity,
        "recommendation": "RETRAIN" if severity in ["HIGH", "CRITICAL"] else "MONITOR"
    }

# Integrado en cron diario:
# Carga últimas 24h de scores del motor_decision.log
# Compara contra distribución del training set
# Si drift MEDIUM+: alerta Telegram
# Si drift HIGH+: trigger retrain_pipeline.sh
```

### 6.4 Auditoría y Trazabilidad

```
Cada decisión del motor registra:
  timestamp | src_ip | dst_ip | dst_port | proto | score | decision | trigger | corrida_id

Ejemplo línea motor_decision.log:
  2026-06-14T10:23:45.123 | 192.168.0.100 | 192.168.0.120 | 80 | TCP | -0.7218 | BLOCK | IF_score | corrida_015

Auditoría disponible:
  grep "BLOCK" motor_decision.log | awk '{print $3}' | sort | uniq -c | sort -rn
  → Top IPs bloqueadas en período

  grep "192.168.0.100" motor_decision.log | tail -100
  → Historial completo de IP específica

  awk -F'|' '$6 > -0.4973' motor_decision.log | wc -l
  → Flujos PERMIT en período

Retención de auditoría: 365 días mínimo (cumplimiento)
```

---

## 7. Análisis de Riesgos

### 7.1 Riesgos Técnicos

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| T1 | Sensor cae → sin detección | Media | Alto | Watchdog systemd (Restart=always) + alertas de heartbeat |
| T2 | eve.json crece sin control (atacante genera flood masivo) | Alta | Medio | logrotate + cuota de disco + alerta >80% uso |
| T3 | Falso positivo bloquea IP legítima | Baja (FPR=9.5% con τ1) | Alto | Whitelist + LIMIT antes de BLOCK + timeout auto-unlock |
| T4 | Modelo desactualizado (drift) | Media | Medio | KS-test drift monitor + reentrenamiento automático |
| T5 | Python motor crash silencioso | Baja | Alto | systemd Restart=always + health-check endpoint |
| T6 | ipset rules perdidas tras reboot | Media | Alto | `ipset save /etc/ipset.conf` + `ExecStartPre=ipset restore` en systemd |
| T7 | Ataque evasivo (low-and-slow) | Media | Medio | Heurísticas temporales + umbral τ2 conservador |

### 7.2 Riesgos Operacionales

| # | Riesgo | Mitigación |
|---|---|---|
| O1 | Administrador no disponible para atender alerta | Runbook documentado + on-call rotativo |
| O2 | Whitelist desactualizada (nuevo servidor) | Proceso formal de change management para whitelist |
| O3 | Reentrenamiento degrada modelo | Gate de AUC en retrain_pipeline.sh (no promover si AUC baja) |
| O4 | Telegram bot caído → sin alertas | Fallback a email + log local siempre activo |
| O5 | SSH keys expiradas → no puede conectar al sensor | Gestión de llaves con rotación anual documentada |

### 7.3 Riesgos Metodológicos (Sustentación)

| # | Riesgo | Respuesta preparada |
|---|---|---|
| M1 | "684 flujos de entrenamiento es muy poco" | IF es unsupervised: solo necesita representación del baseline normal. Con 684 flujos normales captura la distribución. Validado en 376,827 flujos. |
| M2 | "Tráfico de laboratorio no representa producción" | Cierto para Fase 0. Por eso existe el roadmap F0→F1 con modo MONITOR 30 días en red real antes de activar bloqueo. |
| M3 | "Isolation Forest es obsoleto, ¿por qué no deep learning?" | IF: interpretable, O(n log n), sin GPU, latencia <15ms. LSTM requiere GPU, latencia >100ms, no interpretable. Para inline enforcement, IF es la elección correcta. |
| M4 | "FPR=9.5% con τ1 es alto" | τ1 es el umbral PERMIT/LIMIT, no PERMIT/BLOCK. El FPR real (flujos erroneamente BLOCKeados) con τ2 es FPR=2%. Los que caen entre τ1 y τ2 son limitados, no bloqueados. |

---

## 8. Preguntas de Defensa — Costo y Escalabilidad

### Pregunta 1: "¿Cuánto cuesta en CPU procesar un flujo?"

**Respuesta:**
El pipeline completo desde que Suricata cierra un flujo hasta que motor_decision.py aplica la acción toma en promedio 18ms (P95=34.8ms), muy por debajo del requisito de 500ms. En términos de CPU: el motor usa menos del 5% de un core durante operación normal. Esto incluye:
- Parseo JSON: 0.3ms
- Derivación de 14 features: 0.1ms  
- Normalización StandardScaler: 0.2ms
- Inferencia Isolation Forest (300 árboles): 8–15ms
- Evaluación τ1/τ2 + heurísticas: 0.05ms
- enforce.sh (ipset): 2–5ms

El modelo en RAM ocupa 2.4 MB. En el hardware del sensor (Xeon Bronze 3204, 4 cores, 7.8 GB RAM), el motor podría manejar hasta 67 flujos/segundo en un solo core, mientras que el laboratorio genera máximo ~15 flujos/segundo durante ataques flood. Hay margen de 4× antes de requerir paralelismo.

### Pregunta 2: "¿Cómo escala si la red crece de 4 nodos a 500 usuarios?"

**Respuesta:**
La arquitectura escala en tres dimensiones:

1. **Vertical:** Con micro-batching (lotes de 50 flujos cada 100ms), el throughput aumenta de 67 a ~350 flujos/segundo en el mismo hardware, suficiente para 500 usuarios.

2. **Horizontal:** Para múltiples servidores protegidos, el sensor actúa como policía central y sincroniza reglas ipset vía SSH a cada servidor en <1 segundo. No requiere cambios en el modelo.

3. **Multi-sensor:** Para campus o edificios separados, se introduce una capa Kafka donde cada sensor publica flujos a un topic, y un motor central agrega y distribuye decisiones. Los sensores remotos actúan como enforcers. Esta arquitectura soporta miles de flujos/segundo.

El modelo IF no necesita reentrenamiento al escalar la red — solo necesita que el tráfico nuevo sea estadísticamente similar al baseline. Si hay nuevos servicios, se recolectan flujos PERMIT de 30 días y se reentrena.

### Pregunta 3: "¿Qué pasa con los datos después de 3 años? ¿No colapsará el disco?"

**Respuesta:**
Se implementa una política de retención escalonada:
- **Hot (0–30 días):** Datos activos en SSD del sensor. ~3 GB máximo con política de logs.
- **Warm (30–90 días):** Archivado comprimido local (gzip, ratio 8:1). ~8 GB para red mediana.
- **Cold (>90 días):** NAS o almacenamiento externo (S3/MinIO). Solo se necesitan para auditoría legal.

Para el modelo de ML, el dataset no crece indefinitamente: el reentrenamiento usa una ventana deslizante de los últimos 28 días de flujos PERMIT, manteniendo un tamaño máximo de ~50,000 flujos (~50 MB). Los datos históricos no se necesitan para el modelo — solo para auditoría.

Con estas políticas, el almacenamiento activo en el sensor nunca supera 10 GB incluso después de 3 años.

---

## 9. Mejoras Futuras (Roadmap 3 Años)

### 9.1 Horizonte 6 Meses — Consolidación

| Mejora | Justificación | Esfuerzo |
|---|---|---|
| Dashboard web (Grafana + InfluxDB) | Reemplazar dashboard.py terminal-only | 2 semanas |
| API REST de gestión (Flask/FastAPI) | Gestión remota sin SSH directo | 1 semana |
| Modo MONITOR configurable en runtime | Fase 1 del roadmap producción | 3 días |
| Alerta Telegram enriquecida con whois | Contexto inmediato al operador | 2 días |
| Tests automáticos del motor (pytest) | Prevenir regresiones en actualizaciones | 1 semana |
| Script de instalación automatizado | Onboarding nuevos sensores | 3 días |

### 9.2 Horizonte 1 Año — Madurez

| Mejora | Justificación | Impacto |
|---|---|---|
| Integración Wazuh/Elasticsearch | Correlación con otros IDS/IPS | AUC mejora por más contexto |
| Reentrenamiento automático mensual | Modelo siempre actualizado | Recall sostenido >90% |
| Análisis de flujos cifrados (TLS metadata) | Detectar ataques en HTTPS | Cobertura extendida |
| Scoring por reputación de IP (threat intel) | Capa adicional de contexto | Reducción FPR |
| Multi-sensor con Kafka | Campus o multi-edificio | Escalabilidad horizontal |
| Clustering de anomalías (DBSCAN) | Identificar familias de ataques | Inteligencia táctica |

### 9.3 Horizonte 3 Años — Evolución

| Mejora | Descripción | Prerrequisito |
|---|---|---|
| Ensemble IF + AutoEncoder | Deep Anomaly Detection para ataques evasivos | GPU en sensor o inferencia remota |
| Federated Learning | Múltiples instituciones comparten patrones sin compartir datos | Acuerdo institucional + privacidad diferencial |
| Análisis de comportamiento de usuario (UEBA) | Correlación flujos de red + logs de aplicación | Integración SIEM completa |
| Respuesta automática adaptativa | El sistema ajusta τ1/τ2 en runtime según contexto | MLOps maduro + supervisión humana |
| Certificación ISO 27001 del proceso | Cumplimiento formal para licitaciones | 18 meses madurez operacional |
| Publicación académica | Resultados F6 como paper en congreso | Asesor Saboya + revisión par |

---

## 10. Resumen Ejecutivo

### Para la Sustentación

**¿Es costoso computacionalmente?**  
No. El motor usa <5% de CPU en reposo y <22% en picos de ataque flood. Latencia P95=34.8ms vs. requisito de 500ms → margen de 14×. El modelo ocupa 2.4 MB en RAM en un sistema con 7.8 GB disponibles.

**¿Escala con más tráfico?**  
Sí. Con micro-batching, el throughput pasa de 67 a 350 flujos/segundo en el mismo hardware. Para redes más grandes, la arquitectura multi-sensor con Kafka soporta miles de flujos/segundo.

**¿Está listo para producción?**  
El MVP (Fase 0 — laboratorio) está completamente validado. El roadmap F0→F3 define los pasos controlados hacia producción real, comenzando con modo MONITOR en Fase 1 para recolectar datos de tráfico real sin riesgo.

**¿Qué pasa con los datos a largo plazo?**  
La política de retención escalonada (Hot 30d / Warm 90d / Cold 1yr) mantiene el almacenamiento activo en <10 GB indefinidamente. El modelo se reentriena con ventana deslizante de 28 días, no con toda la historia.

**¿Es mantenible por un equipo pequeño?**  
Sí. El sistema está diseñado para operar autónomamente (systemd + cron + reentrenamiento automático) con supervisión mínima. El operador solo interviene ante alertas de drift o incidentes de alto impacto.

---

*Documento generado: 2026-06-14*  
*Basado en datos reales del laboratorio PPI UPeU 2026*  
*Hardware validado: Intel Xeon Bronze 3204 / 4 cores / 7.8 GB RAM*  
*Métricas base: Recall=99.3% | AUC=0.9440 | Latencia P95=34.8ms | ITL=0%*
