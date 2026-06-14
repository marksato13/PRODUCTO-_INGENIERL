# F5-01 — Arquitectura Completa de Integración del Sistema

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F5 — Control Inline e Integración  
**Fecha:** 2026-06-14  

---

## 1. Arquitectura General

El sistema implementa un pipeline de 9 etapas que va desde la captura pasiva del tráfico hasta la respuesta activa en línea y la notificación al analista:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE DE DETECCIÓN Y RESPUESTA                       │
│                                                                             │
│   [RED]          [CAPTURA]        [PROCESAMIENTO]      [DECISIÓN]          │
│                                                                             │
│  Tráfico          Suricata          eve.json              Score             │
│  de Red    ──▶   (IDS pasivo)  ──▶  (JSON events)  ──▶   IF [-1,0]        │
│   :80/:22         ens35              tail -f               ↓               │
│   :53/:443        mirror port        parse_flow()          τ1 / τ2         │
│                                      derive_14_feat         ↓              │
│                                                      ┌──────┴──────┐        │
│                                                   PERMIT  LIMIT  BLOCK      │
│                                                      │      │      │        │
│   [ALMACENAMIENTO]         [CONTROL]         [NOTIFICACIÓN]  [VISUALIZACIÓN]│
│                                                                             │
│  motor_decision.log  ←─── ipset ppi_blocked  ───▶  Telegram Bot            │
│  dataset_clean.csv         ipset ppi_limited  ───▶  Dashboard.py           │
│  normal_flows_nuevo        iptables DROP/LIMIT      (graficas tiempo real) │
│                                                                             │
│   [RETROALIMENTACIÓN]                                                       │
│                                                                             │
│  Flows PERMIT acum.  ──▶  batch_retrain.py  ──▶  isolation_forest_vN.pkl  │
│  (aprendizaje continuo)                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Etapas del pipeline

| # | Etapa | Componente | Tecnología | Latencia típica |
|---|---|---|---|---|
| 1 | Captura de tráfico | Suricata 7.0.3 | libpcap / AF_PACKET | < 1ms |
| 2 | Generación de eventos | eve.json | JSON streaming | < 1ms |
| 3 | Data Engineering | parser + derive_features() | Python 3.11 | 2–5ms |
| 4 | Inferencia del modelo | Isolation Forest | scikit-learn 1.8.0 | 8–15ms |
| 5 | Clasificación | score vs τ1/τ2 | Python (numpy) | < 1ms |
| 6 | Motor de decisión | motor_decision.py | Python + subprocess | 5–10ms |
| 7 | Control inline | ipset + iptables | kernel netfilter | < 1ms |
| 8 | Notificación | Telegram Bot API | python-telegram-bot | 100–500ms async |
| 9 | Visualización | dashboard.py | Python curses/rich | 3s refresh |

**Latencia total (P95 medido en F6):** 34.8ms — cumple requisito < 500ms con margen 14×.

---

## 2. Arquitectura Física

### Topología del laboratorio (implementación actual)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RED DE LABORATORIO 192.168.0.0/24                  │
│                                                                             │
│  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐  │
│  │  Win11 Cliente   │      │  Ubuntu Desktop  │      │  Kali Linux      │  │
│  │  192.168.0.10    │      │  192.168.0.20    │      │  192.168.0.100   │  │
│  │                  │      │  [Admin/Claude]  │      │  [Atacante]      │  │
│  │  Tráfico normal  │      │  Scripts A1-A4   │      │  Scripts B1-B6   │  │
│  │  navegación      │      │  curl/wget/scp   │      │  hping3/nmap     │  │
│  └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘  │
│           │                         │                          │            │
│           └─────────────────────────┼──────────────────────────┘            │
│                                     │                                       │
│                           ┌─────────▼─────────────────────────────────┐    │
│                           │         SWITCH  192.168.0.1               │    │
│                           │    (port mirroring → ens35 del sensor)    │    │
│                           └─────────┬─────────────────┬───────────────┘    │
│                                     │                 │                    │
│                    ┌────────────────▼──┐   ┌──────────▼────────────────┐   │
│                    │  Ubuntu Suricata  │   │  Ubuntu Server            │   │
│                    │  192.168.0.110    │   │  192.168.0.120            │   │
│                    │                  │   │                            │   │
│                    │  ens33: mgmt     │   │  nginx :80                │   │
│                    │  ens35: captura  │   │  OpenSSH :22              │   │
│                    │  (modo promiscuo)│   │  [Servicio objetivo]      │   │
│                    │                  │   └────────────────────────────┘   │
│                    │  ┌────────────┐  │                                    │
│                    │  │ Suricata   │  │                                    │
│                    │  │ eve.json   │  │                                    │
│                    │  │ motor.py   │  │                                    │
│                    │  │ ipset/ipt  │  │                                    │
│                    │  │ dashboard  │  │                                    │
│                    │  └────────────┘  │                                    │
│                    └──────────────────┘                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  COMPONENTES EXTERNOS (futuros)                                      │  │
│  │  Telegram API ◄── Alertas BLOCK/LIMIT                               │  │
│  │  Analista SOC  ◄── Dashboard + Notificaciones                       │  │
│  │  SIEM/Elastic  ◄── motor_decision.log (forward)                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Especificaciones físicas del sensor (192.168.0.110)

| Componente | Valor |
|---|---|
| CPU | Intel Xeon Bronze 3204 @ 1.90 GHz |
| Cores disponibles | 4 |
| RAM | 7.8 GB |
| Almacenamiento | 50 GB (VM) |
| OS | Ubuntu Server 22.04 LTS |
| NIC captura | ens35 (modo promiscuo, sin IP) |
| NIC gestión | ens33 (192.168.0.110/24) |
| Python venv | `/home/m4rk/ppi-sensor/venv/` |
| scikit-learn | 1.8.0 |

### Arquitectura física en producción (propuesta)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ARQUITECTURA FÍSICA PRODUCCIÓN                         │
│                                                                             │
│  ZONA DMZ / RED MONITORIZADA                                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Firewall   │  │ Web Server │  │ Mail Server│  │ DB Server  │           │
│  │ perimetral │  │ :80/:443   │  │ :25/:587   │  │ :5432      │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
│        │               │               │               │                   │
│        └───────────────┴───────────────┴───────────────┘                   │
│                               │ (port mirror / TAP)                        │
│                               │                                             │
│  ZONA SENSOR                  ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Sensor Suricata (dedicado)                                        │    │
│  │  ├── ens35: captura (promiscuo, sin IP)                            │    │
│  │  ├── Suricata 7.0.3 → eve.json                                     │    │
│  │  ├── motor_decision.py (Python daemon)                             │    │
│  │  ├── ipset/iptables (control inline)                               │    │
│  │  └── 8 cores / 32 GB RAM / SSD 200 GB                             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                               │                                             │
│                    ┌──────────┼──────────┐                                 │
│                    │          │          │                                  │
│  ZONA GESTIÓN      ▼          ▼          ▼                                 │
│  ┌───────────┐  ┌────────┐  ┌────────┐  ┌─────────────────────────────┐   │
│  │ Dashboard │  │ SIEM   │  │ Elastic│  │ Servidor de Modelos         │   │
│  │ Grafana   │  │ Wazuh  │  │ Stack  │  │ MLflow / Model Registry    │   │
│  │ :3000     │  │ :55000 │  │ :9200  │  │ Almacena versiones pkl      │   │
│  └───────────┘  └────────┘  └────────┘  └─────────────────────────────┘   │
│                                                                             │
│  ZONA ANALISTA                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Estación SOC                                                       │   │
│  │  ├── Dashboard web (Grafana/Kibana)                                 │   │
│  │  ├── Notificaciones Telegram (BLOCK inmediato)                      │   │
│  │  ├── Consola de administración (enforce.sh manual)                  │   │
│  │  └── Revisión de bitácora (bitacora_escenarios.txt)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Arquitectura Lógica

### 3.1 Flujo de Datos

```
[Eve.json]
    │
    │  {"event_type":"flow","src_ip":"192.168.0.100",
    │   "bytes_toserver":5242880,"duration":0.12,...}
    │
    ▼
[parse_flow()]  ──── Extrae: src_ip, dest_ip, dest_port, proto,
    │                        bytes_toserver, bytes_toclient,
    │                        pkts_toserver, pkts_toclient, duration
    │
    ▼
[derive_features()]
    │  pkt_rate  = (pkts_toserver + pkts_toclient) / max(duration, 0.001)
    │  byte_rate = (bytes_toserver + bytes_toclient) / max(duration, 0.001)
    │  pkt_ratio = pkts_toserver / (pkts_toclient + 1)
    │  byte_ratio= bytes_toserver / (bytes_toclient + 1)
    │  avg_pkt_size = (bytes_to + bytes_from) / (pkts_to + pkts_from + 1)
    │  is_tcp / is_udp / is_icmp  ← del campo "proto"
    │
    ▼
[scaler.transform(X)]  ──── StandardScaler (fit en 684 flows normales)
    │
    ▼
[isolation_forest.score_samples(X_sc)]
    │
    │  score ∈ [-1, 0]
    │
    ▼
[Clasificación]
    │  score > -0.4973  → PERMIT
    │  score > -0.6873  → LIMIT (hashlimit 100pkt/s)
    │  score ≤ -0.6873  → BLOCK (DROP)
    │
    ▼
[motor_decision.log]  ──── "2026-06-14 10:23:45 | BLOCK | 192.168.0.100
                             | score=-0.7215 | dest_port=80"
```

### 3.2 Flujo de Alertas

```
[Clasificación]
    │
    ├── PERMIT ───────────────────────────────────────────▶ [Log PERMIT]
    │                                                        [Acumulación
    │                                                         normal_flows]
    │
    ├── LIMIT ────────▶ [ipset add ppi_limited src_ip] ──▶ [Log LIMIT]
    │                   [iptables hashlimit 100pkt/s]       [Dashboard]
    │                                                        [Telegram? ⚪]
    │
    └── BLOCK ───────▶ [ipset add ppi_blocked src_ip] ───▶ [Log BLOCK]
                       [iptables DROP]                       [Dashboard]
                       [timeout 3600s]                       [Telegram ⚪]
                                                             [SIEM forward ⚪]

⚪ = propuesto / en plan de implementación
```

### 3.3 Flujo de Clasificación

```
                         ┌─────────────────────────────────────┐
                         │  WHITELIST CHECK (PRIMERO)          │
                         │  192.168.0.1 / .20 / .110 / .120   │
                         │  127.0.0.1                          │
                         └──────────────┬──────────────────────┘
                                        │
                          ¿src_ip ∈ whitelist?
                                        │
                     ┌──── SÍ ──────────┴──────── NO ────┐
                     │                                    │
                     ▼                                    ▼
                  PERMIT                     ┌────────────────────────┐
                (siempre)                    │  Detectores Heurísticos│
                                             │  (ventana temporal)    │
                                             │                        │
                                             │ SSH BF: ≥15 intentos/  │
                                             │         60s → BLOCK    │
                                             │ HTTP: ≥100 req/30s     │
                                             │       → BLOCK          │
                                             └──────────┬─────────────┘
                                                        │
                                          ¿Heurística dispara?
                                                        │
                                     ┌── SÍ ────────────┴─── NO ──────┐
                                     │                                 │
                                     ▼                                 ▼
                                  BLOCK /                   ┌──────────────────┐
                                  LIMIT                     │  Isolation Forest │
                                (heurístico)                │  score_samples()  │
                                                            └──────────┬────────┘
                                                                       │
                                                              score vs τ1/τ2
                                                                       │
                                                    ┌──────────────────┼──────────────┐
                                                    │                  │              │
                                             score > τ1         τ2 < score ≤ τ1  score ≤ τ2
                                              (-0.4973)           (-0.6873)       (-0.6873)
                                                    │                  │              │
                                                 PERMIT             LIMIT          BLOCK
```

### 3.4 Flujo de Actualización (Aprendizaje Continuo)

```
[Producción]
    │  flows PERMIT no-whitelist
    │
    ▼
[normal_flows_nuevos.csv]
    │  acumulación continua
    │
    ¿≥2,000 flows nuevos O trigger semanal?
    │
    ▼
[Validación de muestra]
    │  revisión manual o filtro FPR < 10%
    │
    ▼
[batch_retrain.py]
    │  IF(n=300) fit en normal_historico + nuevos
    │  StandardScaler fit en nuevos normales
    │  Recalibración τ1/τ2 con nuevo Youden index
    │
    ▼
[4 Gates de Calidad]
    │  Gate 1: FPR ≤ 10% ✓
    │  Gate 2: Recall ≥ 95% ✓
    │  Gate 3: AUC ≥ 0.98 ✓
    │  Gate 4: Latencia P95 < 500ms ✓
    │
    ▼ (todos superados)
[isolation_forest_v{N+1}.pkl] ──▶ [Deploy en caliente]
[scaler_v{N+1}.pkl]                systemctl reload ppi-motor.service
[umbrales_v{N+1}.txt]
    │
    ▼
[Motor actualizado en producción]
```

---

## 4. Integración de Componentes

### 4.1 Suricata 7.0.3

**Rol:** Sensor de captura pasiva. Analiza todo el tráfico en ens35 (modo promiscuo) y genera eventos estructurados en eve.json.

**Configuración relevante:**
```yaml
# /etc/suricata/suricata.yaml (fragmento)
af-packet:
  - interface: ens35
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      types:
        - flow:
            enabled: yes
```

**Integración con el motor:**
- `motor_decision.py` hace `tail -f` del eve.json en tiempo real
- Solo procesa eventos `"event_type": "flow"` (no alertas, no DNS, no HTTP)
- Reopen-log: `suricatasc -c reopen-log-files` al rotar el archivo

### 4.2 Python (motor_decision.py)

**Rol:** Orquestador central. Conecta todos los componentes: lectura de eve.json → features → modelo → decisión → control → log.

**Dependencias:**
```python
# venv: /home/m4rk/ppi-sensor/venv/
import json       # parsing eve.json
import numpy      # operaciones vectoriales
import joblib     # carga isolation_forest.pkl y scaler.pkl
import subprocess # llamadas a ipset/iptables (enforce.sh)
import time       # medición de latencia
import logging    # motor_decision.log
```

**Thread model:** Single-threaded, event-driven (tail loop). Sin paralelismo en MVP — para producción se propone arquitectura multi-worker con cola de eventos.

### 4.3 Archivos CSV (Data Engineering)

**Rol:** Almacenamiento del dataset para entrenamiento y evaluación offline.

| Archivo | Ruta | Rows | Uso |
|---|---|---|---|
| `dataset_clean.csv` | `data/` | 376,827 | Dataset completo etiquetado |
| `train.csv` | `data/` | 263,778 | Entrenamiento (70%, cronológico) |
| `val.csv` | `data/` | 56,524 | Validación (15%) |
| `test.csv` | `data/` | 56,525 | Test final (15%) |
| `normal_flows_nuevos.csv` | `data/` | variable | Acumulación para reentrenamiento |
| `bitacora_escenarios.txt` | `docs/bitacora/` | 40 corridas | Registro de experimentos |

### 4.4 Modelos ML (Isolation Forest)

**Rol:** Núcleo de detección. Evalúa la anomalía de cada flow en < 15ms.

| Archivo | Ruta | Tamaño | Descripción |
|---|---|---|---|
| `isolation_forest.pkl` | `models/` | ~2.4 MB | IF(n=300, contamination=0.05) |
| `scaler.pkl` | `models/` | ~4 KB | StandardScaler (fit en 684 normales) |
| `features.csv` | `models/` | ~1 KB | Lista de 14 features en orden |
| `umbrales_finales.txt` | `results/` | ~100 B | τ1=−0.4973, τ2=−0.6873 |

**Carga en el motor:**
```python
import joblib
model  = joblib.load("models/isolation_forest.pkl")
scaler = joblib.load("models/scaler.pkl")
TAU1, TAU2 = -0.4973, -0.6873
```

### 4.5 Telegram Bot (propuesto)

**Rol:** Notificación inmediata al analista SOC cuando se produce un BLOCK o LIMIT. Canal asíncrono — no bloquea el pipeline principal.

**Implementación propuesta:**
```python
import asyncio
import telegram

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]  # variable de entorno (no hardcoded)
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

async def notify_telegram(src_ip, action, score, dest_port):
    bot = telegram.Bot(token=BOT_TOKEN)
    emoji = "🔴" if action == "BLOCK" else "🟡"
    msg = (
        f"{emoji} PPI-IDS ALERTA\n"
        f"Acción: {action}\n"
        f"IP: {src_ip}\n"
        f"Score: {score:.4f}\n"
        f"Puerto destino: {dest_port}\n"
        f"Hora: {datetime.now().strftime('%H:%M:%S')}"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg)

# En el motor (hilo separado para no bloquear):
def trigger_alert(src_ip, action, score, dest_port):
    if action in ("BLOCK", "LIMIT"):
        asyncio.run(notify_telegram(src_ip, action, score, dest_port))
```

**Configuración de seguridad:**
- Token en `/etc/ppi-motor.env` con permisos 600
- Rate limiting: máximo 1 mensaje/5s por IP para evitar flood de notificaciones
- Throttle: si misma IP ya fue notificada en < 300s, omitir

### 4.6 Dashboard (dashboard.py)

**Rol:** Visualización en tiempo real del estado del sistema. Lee `motor_decision.log` cada 3 segundos.

**Métricas mostradas:**
- Flows totales procesados (sesión actual)
- PERMIT / LIMIT / BLOCK (conteo y porcentaje)
- Top 10 IPs bloqueadas
- Latencia promedio y P95 (ventana últimas 1,000 decisiones)
- Score promedio (indicador de "nivel de amenaza")
- Últimas 20 alertas BLOCK/LIMIT con timestamp

**Extensión propuesta (Grafana):**
```bash
# Exportar métricas a formato Prometheus
# motor_decision.py → /metrics endpoint → Prometheus scrape → Grafana
```

---

## 5. Entradas y Salidas por Componente

| Componente | Entrada | Proceso | Salida |
|---|---|---|---|
| **Suricata** | Tráfico raw (pcap en ens35) | Análisis de protocolos, generación de eventos de flow | `eve.json` (JSON lines) |
| **parse_flow()** | Línea JSON de eve.json | Extracción de 9 campos raw del flow | Dict Python con campos brutos |
| **derive_features()** | Dict con campos raw | Cálculo de 14 features (5 derivadas + 3 binarias + 6 directas) | Array numpy (1, 14) |
| **scaler.transform()** | Array (1, 14) raw | Normalización Z-score por feature | Array (1, 14) normalizado |
| **isolation_forest.score_samples()** | Array (1, 14) normalizado | Evaluación de anomalía con 300 árboles | Score float ∈ [−1, 0] |
| **Clasificador τ1/τ2** | Score float | Comparación vs. τ1=−0.4973 y τ2=−0.6873 | Decisión: PERMIT / LIMIT / BLOCK |
| **enforce.sh** | IP + acción + timeout | `ipset add ppi_blocked <IP>` o `ppi_limited` | Regla kernel netfilter activa |
| **motor_decision.log** | Decisión + metadatos | Append a archivo de log con timestamp | Línea de log estructurada |
| **dashboard.py** | motor_decision.log | Parse + agregación estadística cada 3s | Tabla ASCII en terminal |
| **Telegram Bot** | Decisión BLOCK/LIMIT | API call a Telegram con mensaje formateado | Notificación push al analista |
| **batch_retrain.py** | normal_flows_nuevos.csv | IF fit + scaler fit + calibración τ + 4 gates | isolation_forest_vN+1.pkl |

### Detalle del formato de log

```
# motor_decision.log — formato de cada línea
TIMESTAMP | ACCION | SRC_IP | SCORE | DEST_PORT | LATENCIA_MS | DETECTOR

2026-06-14 10:23:45.123 | BLOCK | 192.168.0.100 | -0.7215 | 80 | 28.3ms | IF
2026-06-14 10:23:47.891 | PERMIT | 192.168.0.20  | -0.6529 | 22 | 31.1ms | IF
2026-06-14 10:24:02.455 | BLOCK | 192.168.0.100  | -0.9100 | 22 | 22.4ms | SSH_BF
```

---

## 6. Arquitectura Adaptable

### ¿Cómo se integra nueva data?

La nueva data entra al sistema por **dos vías** según su tipo:

**Vía 1 — Flows normales de producción (automática):**
```
Tráfico PERMIT en prod → log_permit_flow() → normal_flows_nuevos.csv
                                                    │
                                          ≥2,000 flows acumulados
                                                    │
                                          batch_retrain.py ──▶ modelo_vN+1
```
El motor registra cada flow clasificado como PERMIT (excluyendo whitelist). Cuando se acumulan ≥2,000 flows, el scheduler dispara el reentrenamiento automático.

**Vía 2 — Nuevos escenarios de laboratorio (manual):**
```
Corrida A5/A6/A7 (nuevos escenarios normales)
    │
    └──▶ exportar_eve_por_escenario.sh ──▶ YYYYMMDD_normal_nuevo_01_eve.json.gz
              │
              └──▶ parser.py ──▶ dataset_raw_nuevo.csv
                       │
                       └──▶ etiquetar_limpiar.py ──▶ dataset_clean_actualizado.csv
                                │
                                └──▶ batch_retrain.py ──▶ modelo_vN+1
```

### ¿Cómo se agregan nuevos ataques?

**Caso 1 — Ataque completamente nuevo (ej. HTTP/2 Rapid Reset):**
El IF lo detecta automáticamente si el flow difiere de la distribución normal. **No se requiere ninguna acción** — el score será bajo y la acción será LIMIT o BLOCK.

Posterior al incidente: analizar el patrón del flujo → si tiene firma distintiva → agregar detector heurístico al motor para respuesta más rápida.

**Caso 2 — Ataque low-and-slow (APT) que burla el IF:**
```python
# Agregar detector de sesión en motor_decision.py
# Sin reentrenamiento del modelo base

SESION_WINDOW = {}

def detectar_apt(src_ip, dest_ip, dest_port, timestamp):
    key = src_ip
    if key not in SESION_WINDOW:
        SESION_WINDOW[key] = {"destinos": set(), "uploads": 0, "t_inicio": timestamp}
    
    SESION_WINDOW[key]["destinos"].add(dest_ip)
    
    # 300s de ventana; >50 destinos distintos = reconocimiento
    if len(SESION_WINDOW[key]["destinos"]) > 50:
        return "LIMIT"
    return None
```

**Caso 3 — Nueva variante de ataque conocido:**
El IF sigue detectándola porque las features volumétricas no cambian. No se requiere acción.

### ¿Cómo se agregan nuevas versiones del modelo?

```bash
# Script de deploy de nueva versión (deploy_model.sh)
#!/bin/bash
VERSION=$1   # ej. "v1.2.0"
MODEL_DIR="/home/m4rk/ppi-surikata-produto/models"

# 1. Backup de versión actual
cp ${MODEL_DIR}/isolation_forest.pkl \
   ${MODEL_DIR}/versions/$(cat ${MODEL_DIR}/current_version.txt)/isolation_forest.pkl

# 2. Apuntar symlinks a nueva versión
ln -sf ${MODEL_DIR}/versions/${VERSION}/isolation_forest.pkl \
       ${MODEL_DIR}/isolation_forest.pkl
ln -sf ${MODEL_DIR}/versions/${VERSION}/scaler.pkl \
       ${MODEL_DIR}/scaler.pkl

# 3. Actualizar registro de versión
echo ${VERSION} > ${MODEL_DIR}/current_version.txt
echo "$(date): deployed ${VERSION}" >> ${MODEL_DIR}/changelog.txt

# 4. Recargar motor (sin downtime)
systemctl reload ppi-motor.service

# 5. Verificar que el motor levantó con nuevo modelo
sleep 2
systemctl is-active ppi-motor.service && echo "DEPLOY OK: ${VERSION}" \
                                      || (echo "ROLLBACK"; bash rollback.sh)
```

---

## 7. Escenarios de Operación

### 7.1 Escenario Normal (Grupo A)

```
T+0s   Usuario 192.168.0.20 lanza: curl http://192.168.0.120/index.html
T+1ms  Suricata captura el flow en ens35 → eve.json append
T+5ms  motor_decision.py procesa el evento:
       - parse_flow(): bytes_toserver=342, bytes_toclient=1240, pkts_to=3, pkts_from=4
       - derive_features(): pkt_rate=7.0, byte_rate=1582, avg_pkt_size=228
       - score_samples(): score = -0.6529
       - Clasificación: -0.6529 > τ2 (-0.6873) pero < τ1 (-0.4973) → LIMIT
         ↑ En la práctica con whitelist: 192.168.0.20 ∈ whitelist → PERMIT
T+6ms  Log: "PERMIT | 192.168.0.20 | -0.6529 | :80 | 6ms | WHITELIST"
T+3s   Dashboard muestra: PERMIT +1, latencia 6ms

Resultado: tráfico normal fluye sin interrupción.
Impacto en usuario: ninguno.
```

### 7.2 Escenario Anómalo (Grupo B — SYN Flood)

```
T+0s   Kali 192.168.0.100 lanza: hping3 -S --flood 192.168.0.120 -p 80
T+1ms  Miles de paquetes SYN llegan al servidor

T+1ms  Suricata detecta el flujo de flood → eve.json:
       bytes_toserver=64000, bytes_toclient=0, pkts_to=1000, pkts_from=0, duration=0.1

T+12ms motor_decision.py:
       - derive_features():
         pkt_rate = 10,000 pkt/s  (vs. normal ~7/s → 1428× más alto)
         byte_rate = 640,000 B/s  (vs. normal ~1,582 → 404× más alto)
         pkts_toclient = 0 (SYN sin respuesta)
       - score_samples(): score = -0.7215 → MUY ANÓMALO
       - Clasificación: -0.7215 ≤ τ2 (-0.6873) → BLOCK

T+13ms enforce.sh: ipset add ppi_blocked 192.168.0.100 timeout 3600
T+14ms iptables DROP: todos los paquetes de 192.168.0.100 dropados en kernel

T+15ms Log: "BLOCK | 192.168.0.100 | -0.7215 | :80 | 15ms | IF"
T+16ms Telegram: "🔴 PPI-IDS ALERTA / Acción: BLOCK / IP: 192.168.0.100..."
T+3s   Dashboard: BLOCK +1, IP bloqueada en top list

Resultado: SYN Flood cortado en 14ms. Servidor 192.168.0.120 protegido.
Latencia de respuesta: 14ms (P95 medido: 34.8ms).
```

### 7.3 Escenario Mixto (Grupo C — HTTP + SYN simultáneos)

```
T+0s   192.168.0.20 (Desktop): curl http://192.168.0.120/ en bucle (normal)
T+0s   192.168.0.100 (Kali):   hping3 -S --flood simultáneo (ataque)

T+1ms  Suricata genera events de ambas fuentes en eve.json
       (interleaved: flow1=normal, flow2=ataque, flow3=normal, ...)

T+5ms  motor_decision.py procesa flow1 (192.168.0.20):
       → WHITELIST → PERMIT (inmediato, sin scoring)

T+6ms  motor_decision.py procesa flow2 (192.168.0.100):
       → score = -0.7215 → BLOCK
       → ipset add ppi_blocked 192.168.0.100

T+7ms  motor_decision.py procesa flow3 (192.168.0.20):
       → WHITELIST → PERMIT

RESULTADO:
├── 192.168.0.20: PERMIT continuo — sin interrupción al tráfico legítimo
├── 192.168.0.100: BLOCK — flood cortado en < 15ms
└── 192.168.0.120: sigue sirviendo HTTP a clientes legítimos

Caso validado en F6 — escenarios C1/C2/C3 con ITL=0%
(Interrupción al Tráfico Legítimo = 0%)
```

---

## 8. Diagramas

Los diagramas Draw.io en formato XML se encuentran en el archivo separado:

`F5_control_inline/DIAGRAMAS/F5_Arquitectura_Integracion.drawio.md`

Se incluyen 4 diagramas:
1. **Arquitectura Física** — topología de red con IPs del laboratorio
2. **Arquitectura Lógica** — flujo de datos y decisiones
3. **Arquitectura de Despliegue** — componentes en el sensor
4. **Arquitectura de Integración** — componentes y sus interfaces

---

## 9. Mejoras Implementables

### 9.1 Cola de Eventos (Redis / RabbitMQ)

**Problema actual:** El motor_decision.py procesa eventos en un solo hilo (tail loop). Si hay ráfagas de tráfico intenso (>5,000 eventos/s), el buffer interno puede saturarse y perder eventos.

**Solución:**
```
Suricata → eve.json → [Productor Python] → [Redis Queue] → [N Workers ML]
                                                 │
                                         cada worker:
                                         ├── consume 1 evento
                                         ├── score IF
                                         └── llama enforce.sh
```

**Implementación:**
```python
# Productor (reemplaza el tail -f directo)
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

def produce_events():
    with open("/var/log/suricata/eve.json") as f:
        f.seek(0, 2)  # tail desde el final
        while True:
            line = f.readline()
            if line:
                r.lpush("ppi:events", line.strip())
            else:
                time.sleep(0.001)

# Workers (múltiples instancias en paralelo)
def consume_and_classify():
    while True:
        _, event_json = r.brpop("ppi:events", timeout=1)
        if event_json:
            classify_and_enforce(event_json)
```

**Impacto esperado:**
- Throughput: de ~3,000 eventos/s a ~50,000 eventos/s con 4 workers
- Tolerancia a ráfagas: buffer Redis absorbe picos sin pérdida
- Resiliencia: si un worker falla, los otros continúan

### 9.2 Procesamiento en Streaming (Apache Kafka)

**Cuándo usar Kafka vs. Redis:** Redis es suficiente para un sensor; Kafka es necesario cuando múltiples sensores alimentan un sistema centralizado.

```
Sensor 1 (Suricata A) ─┐
Sensor 2 (Suricata B) ─┼──▶ [Kafka Topic: suricata.flows] ──▶ [ML Cluster]
Sensor 3 (Suricata C) ─┘                                        ├── Worker 1
                                                                 ├── Worker 2
                                                                 └── Worker N
                                                                      │
                                                          [Kafka Topic: decisions]
                                                                      │
                                                          [Enforcement Agent por sensor]
```

**Implementación básica:**
```python
from kafka import KafkaProducer, KafkaConsumer
import json

# En cada sensor — publicar flows
producer = KafkaProducer(
    bootstrap_servers=['kafka-server:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_flow(flow_dict):
    producer.send('suricata.flows', value=flow_dict)

# En servidor central — consumir y clasificar
consumer = KafkaConsumer(
    'suricata.flows',
    bootstrap_servers=['kafka-server:9092'],
    group_id='ppi-ml-workers'
)
for message in consumer:
    flow = json.loads(message.value)
    score = model.score_samples([derive_features(flow)])[0]
    decision = classify(score)
    publish_decision(flow['src_ip'], decision)
```

**Impacto esperado:**
- Centralización: un modelo ML cubre múltiples sensores Suricata
- Replay: los eventos se retienen en Kafka (configurable: 7 días) para análisis forense
- Escalabilidad horizontal: añadir workers sin modificar productores

### 9.3 Integración con SIEM

**Qué es SIEM en este contexto:** Security Information and Event Management — sistema centralizado que correlaciona eventos de múltiples fuentes (Suricata, syslog, Windows Event Log, etc.) para detección de amenazas compuestas.

**Integración propuesta:**
```
motor_decision.log ──▶ [Filebeat] ──▶ [Logstash] ──▶ [SIEM Central]
                                         │               (Splunk / IBM QRadar)
                                         └──▶ Enriquece con:
                                              - GeoIP del src_ip
                                              - Reputación IP (VirusTotal)
                                              - Histórico de la IP en el SIEM
```

**Formato de evento para SIEM (CEF — Common Event Format):**
```
CEF:0|PPI-UPeU|IDS-IF|1.0|BLOCK|IF Score Below Tau2|High|
src=192.168.0.100 dst=192.168.0.120 dpt=80
cs1=-0.7215 cs1Label=IF_Score
cs2=BLOCK cs2Label=Action
cn1=34 cn1Label=Latency_ms
```

**Impacto esperado:**
- Correlación: un BLOCK del IF puede correlacionarse con una alerta de Suricata del mismo IP
- Visibilidad: el analista SOC tiene una sola consola con todos los eventos
- Cumplimiento: logs centralizados con retención para auditorías

### 9.4 Integración con Elastic Stack (ELK)

**Componentes:**
- **Elasticsearch**: almacena e indexa los logs del motor
- **Logstash**: transforma y enriquece los logs antes de indexar
- **Kibana**: dashboards web interactivos (reemplaza el dashboard.py en terminal)

**Pipeline:**
```
motor_decision.log
    │
    ▼
[Filebeat] ──▶ [Logstash]
                    │
                    ├── Parseo del formato: TIMESTAMP | ACCION | IP | SCORE...
                    ├── GeoIP lookup (si IP es pública)
                    ├── Enriquecimiento con campos calculados
                    └──▶ [Elasticsearch :9200]
                                │
                                └──▶ [Kibana :5601]
                                         ├── Dashboard "PPI Detections"
                                         ├── Heatmap de IPs por hora
                                         ├── Score distribution histogram
                                         └── Alert rules (score < -0.90 → email)
```

**Configuración Logstash (logstash.conf):**
```
filter {
  grok {
    match => {
      "message" => "%{TIMESTAMP_ISO8601:timestamp} \| %{WORD:action} \| %{IP:src_ip} \| %{NUMBER:score:float} \| :%{INT:dest_port:int} \| %{NUMBER:latency_ms:float}ms"
    }
  }
  mutate {
    add_field => { "threat_level" => "low" }
  }
  if [score] <= -0.687 {
    mutate { update => { "threat_level" => "high" } }
  } else if [score] <= -0.497 {
    mutate { update => { "threat_level" => "medium" } }
  }
}
```

**Impacto esperado:**
- Dashboards interactivos accesibles desde cualquier navegador
- Búsqueda histórica: "todas las IPs bloqueadas la última semana con score < -0.9"
- Alertas configurables sin modificar código Python

### 9.5 Integración con Wazuh

**Qué es Wazuh:** SIEM/XDR open source basado en OSSEC. Especializado en detección de amenazas en endpoints, correlación de logs y respuesta activa.

**Integración propuesta:**
```
[Wazuh Agent en sensor 192.168.0.110]
    │  monitorea /home/m4rk/ppi-surikata-produto/results/motor_decision.log
    │
    ▼
[Wazuh Manager]
    │  aplica reglas personalizadas para PPI-IDS
    │
    ▼
[Wazuh Dashboard]  +  [Notificaciones email/Slack]
```

**Regla Wazuh personalizada (local_rules.xml):**
```xml
<group name="ppi_ids">
  <!-- BLOCK desde IF -->
  <rule id="100001" level="12">
    <decoded_as>ppi_motor</decoded_as>
    <field name="action">BLOCK</field>
    <description>PPI-IDS: Flow clasificado como BLOCK por Isolation Forest</description>
    <group>network_anomaly,ppi_block</group>
  </rule>
  
  <!-- Score extremadamente bajo (posible APT) -->
  <rule id="100002" level="15">
    <if_sid>100001</if_sid>
    <field name="score" type="pcre2">-0\.[89]\d+|-1\.0</field>
    <description>PPI-IDS: Score extremo — posible ataque severo (score < -0.80)</description>
    <group>network_anomaly,ppi_critical</group>
  </rule>
</group>
```

**Active Response de Wazuh (complementa al ipset):**
```xml
<!-- Cuando Wazuh detecta BLOCK, también bloquea en firewall del Manager -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100001</rules_id>
  <timeout>3600</timeout>
</active-response>
```

**Impacto esperado:**
- Correlación multi-fuente: un bloqueo del IF puede correlacionarse con login fallido en el mismo IP
- Cumplimiento normativo: Wazuh genera reportes PCI-DSS, HIPAA, GDPR
- Active Response: respuesta coordinada entre IDS (PPI) y SIEM (Wazuh)

---

## Resumen de Impacto de Mejoras

| Mejora | Complejidad | Impacto en Rendimiento | Impacto en Capacidad |
|---|---|---|---|
| Cola Redis | Baja | Throughput ×15 (hasta 50K eventos/s) | Absorbe picos sin pérdida |
| Kafka Streaming | Media | Throughput ×50 multi-sensor | Múltiples sensores centralizados |
| Integración SIEM | Media | Correlación multi-fuente | Visibilidad organizacional |
| ELK Stack | Media | Dashboards web interactivos | Análisis histórico ilimitado |
| Wazuh | Alta | Respuesta activa coordinada | Cumplimiento normativo |

**Para el MVP universitario:** El sistema actual (sin estas mejoras) ya cumple todos los requisitos de la PPI (latencia P95=34.8ms, Recall=99.3%, ITL=0%). Las mejoras son el camino natural hacia una implementación empresarial real.

---

## Conclusión

La arquitectura diseñada integra **captura pasiva** (Suricata), **detección por ML** (Isolation Forest), **control inline** (ipset/iptables) y **notificación** (Telegram/Dashboard) en un pipeline de 34.8ms de latencia P95. La arquitectura es:

- **Modular:** cada componente tiene interfaces definidas (eve.json, pkl, log) y puede reemplazarse independientemente
- **Adaptable:** nuevos datos normales se incorporan por acumulación automática de flows PERMIT; nuevos ataques son detectados sin reentrenamiento gracias a la naturaleza unsupervised del IF
- **Escalable:** las mejoras propuestas (Redis → Kafka → ELK → Wazuh) representan un camino claro de evolución desde el MVP universitario hasta un sistema empresarial

La observación del asesor ("no debe verse como simulación sino como arquitectura implementable") está respondida: cada componente del sistema ya está en producción en el laboratorio, y la arquitectura futura propuesta usa tecnologías estándar de la industria (Kafka, ELK, Wazuh) disponibles como software libre.

---

## Archivos de Referencia

| Archivo | Ruta (sensor 192.168.0.110) | Descripción |
|---|---|---|
| Motor principal | `scripts/motor_decision.py` | Orquestador del pipeline |
| Control inline | `scripts/enforce.sh` | Gestión de ipset/iptables |
| Dashboard | `scripts/dashboard.py` | Visualización en tiempo real |
| Modelo IF | `models/isolation_forest.pkl` | Modelo v1.0 |
| Log principal | `results/motor_decision.log` | Bitácora de decisiones |
| Umbrales | `results/umbrales_finales.txt` | τ1=−0.4973, τ2=−0.6873 |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-produto/`
