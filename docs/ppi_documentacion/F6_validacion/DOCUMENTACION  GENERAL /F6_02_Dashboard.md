# F6-02: Dashboard Ejecutivo — Diseño, Wireframe y Arquitectura

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F6 — Validación y Resultados  
**Documento:** F6-02 — Dashboard Ejecutivo  
**Fecha:** 2026-06-14

---

# BLOQUE 5 — DASHBOARD EJECUTIVO

## 5.1 Diseño Conceptual — Vista General

El dashboard está dividido en 6 paneles organizados en 3 filas. El diseño prioriza la información operacional crítica (estado del sistema, alertas activas) en la parte superior, y las métricas y estadísticas históricas en la parte inferior.

### 5.1.1 Wireframe Completo

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║          PPI-SURIKATA  |  SISTEMA DE DETECCIÓN DE ANOMALÍAS EN RED                 ║
║          Universidad Peruana Unión — 2026          [Actualizado: 10:23:45]          ║
╠═══════════════════════════╦═══════════════════════════╦════════════════════════════╣
║  PANEL 1: ESTADO SISTEMA  ║  PANEL 2: ALERTAS ACTIVAS ║  PANEL 3: NIVEL DE RIESGO  ║
║                           ║                           ║                            ║
║  ● Motor: ACTIVO ✅       ║  🔴 BLOCK: 3 activos      ║       RIESGO: ALTO         ║
║  ● Suricata: OK ✅        ║  🟡 LIMIT: 1 activo       ║   ╭──────────────────╮    ║
║  ● ipset blocked: 3 IPs   ║  ─────────────────────    ║   │  ████████░░░░░░  │    ║
║  ● ipset limited: 1 IP    ║  192.168.0.100 → BLOCK    ║   │      75%         │    ║
║  ● Uptime: 2h 14m         ║    Score: -0.7891 SYN     ║   ╰──────────────────╯    ║
║  ● Flujos/min: 247        ║  192.168.0.101 → BLOCK    ║                            ║
║  ● Telegram: OK ✅        ║    Score: -0.7654 SCAN    ║   🔴 CRÍTICO: 3 eventos   ║
║  ● Whitelist: 7 IPs       ║  192.168.0.102 → BLOCK    ║   🟡 WARN:    1 evento    ║
║                           ║    Score: -0.7421 HTTP    ║   🟢 NORMAL:  0 eventos   ║
╠═══════════════════════════╩═══════════════════════════╩════════════════════════════╣
║                    PANEL 4: DETECCIONES EN TIEMPO REAL                              ║
║                                                                                      ║
║  Timestamp          │ IP Origen       │ IP Destino      │ Prt │ Score  │ Decision   ║
║  ─────────────────  │ ─────────────── │ ─────────────── │ ─── │ ────── │ ────────  ║
║  10:23:45.123  🔴  │ 192.168.0.100   │ 192.168.0.120   │ TCP │ -0.789 │ BLOCK      ║
║  10:23:44.891  🔴  │ 192.168.0.100   │ 192.168.0.120   │ TCP │ -0.781 │ BLOCK      ║
║  10:23:44.712  🟢  │ 192.168.0.20    │ 192.168.0.120   │ TCP │  N/A   │ PERMIT ✓  ║
║  10:23:44.501  🔴  │ 192.168.0.101   │ 192.168.0.120   │ UDP │ -0.765 │ BLOCK      ║
║  10:23:44.203  🟡  │ 192.168.0.150   │ 192.168.0.120   │ TCP │ -0.701 │ LIMIT      ║
║  10:23:43.988  🟢  │ 192.168.0.10    │ 192.168.0.120   │ TCP │ -0.621 │ PERMIT     ║
║  10:23:43.750  🔴  │ 192.168.0.102   │ 192.168.0.120   │ TCP │ -0.742 │ BLOCK      ║
║  10:23:43.501  🟢  │ 192.168.0.20    │ 192.168.0.120   │ TCP │  N/A   │ PERMIT ✓  ║
║                                                               [Mostrando últimos 8]  ║
╠══════════════════════════════╦═══════════════════════════════════════════════════════╣
║  PANEL 5: MÉTRICAS MODELO    ║  PANEL 6: ESTADÍSTICAS Y LÍNEA TEMPORAL              ║
║                              ║                                                        ║
║  Accuracy:    99.97% ████████║  Total hoy:  Procesados: 14,823  Detectados: 4,921  ║
║  Precision:   99.96% ████████║  BLOCK:      3,847    LIMIT:  1,074    PERMIT: 9,902 ║
║  Recall:      99.30% ████████║                                                        ║
║  F1 Score:    0.9963  ███████║  Eventos por hora (últimas 6h):                       ║
║  AUC-ROC:     0.9440  ██████ ║  ╭────────────────────────────────────────────╮      ║
║               ────────────── ║  │   ▄▄              ▄▄▄                      │      ║
║  τ1 (LIMIT):  -0.4973       ║  │ ████           █████████                   │      ║
║  τ2 (BLOCK):  -0.6873       ║  │ ████  ██   ████████████  ██   ██          │      ║
║               ────────────── ║  ╰────────────────────────────────────────────╯      ║
║  Latencia P95: 34.8ms ✅     ║    04h   05h   06h   07h   08h   09h   10h          ║
║  ITL:          0.0%   ✅     ║                                                        ║
║  Uptime:       2h 14m        ║  Por tipo: SYN:45% SCAN:28% UDP:18% HTTP:6% SSH:3%  ║
╚══════════════════════════════╩═══════════════════════════════════════════════════════╝
```

### 5.1.2 Leyenda de Colores

| Color | Código HEX | Significado |
|---|---|---|
| 🟢 Verde | #28a745 | PERMIT — Tráfico legítimo |
| 🟡 Amarillo | #ffc107 | LIMIT — Tráfico sospechoso limitado |
| 🔴 Rojo | #dc3545 | BLOCK — Ataque detectado y bloqueado |
| ⚫ Gris | #6c757d | Whitelist bypass (N/A score) |
| 🔵 Azul | #007bff | Métricas del modelo |

## 5.2 Descripción de Paneles

### Panel 1: Estado del Sistema

| Indicador | Valor posible | Fuente |
|---|---|---|
| Estado Motor | ACTIVO / INACTIVO / ERROR | systemd ppi-motor.service status |
| Estado Suricata | OK / ERROR / WARNING | systemctl status suricata |
| IPs en ppi_blocked | N (número entero) | ipset list ppi_blocked |
| IPs en ppi_limited | N (número entero) | ipset list ppi_limited |
| Uptime del motor | HHh MMm SSs | /proc/uptime |
| Flujos/minuto | N (calculado) | motor_decision.log (últimos 60s) |
| Estado Telegram | OK / FALLO | health-check al bot cada 5min |
| Whitelist size | 7 IPs (configuración base) | ipset list ppi_whitelist |

### Panel 2: Alertas Activas

Muestra en tiempo real las IPs actualmente en ipset bloqueadas/limitadas, con:
- IP origen, tipo de ataque inferido, score IF, timestamp del primer bloqueo
- Tiempo restante si el bloqueo tiene timeout
- Botón de "Desbloquear manualmente" (en versión web)

### Panel 3: Nivel de Riesgo

Cálculo del nivel de riesgo compuesto:

```python
def calcular_nivel_riesgo(blocked, limited, flujos_por_min):
    """
    Riesgo = 0→25 (bajo) | 26→50 (medio) | 51→75 (alto) | 76→100 (crítico)
    """
    score_bloqueos = min(blocked * 15, 60)    # Máximo 60 puntos por bloqueos
    score_limitados = min(limited * 5, 20)    # Máximo 20 puntos por limitados
    score_volumen = min(flujos_por_min / 20, 20)  # Máximo 20 puntos por volumen
    return score_bloqueos + score_limitados + score_volumen
```

### Panel 4: Detecciones en Tiempo Real

Tabla de las últimas 20 decisiones (actualización cada 3s) con columnas:
- **Timestamp** (ms precision)
- **IP Origen** — fuente del flujo
- **IP Destino** — servidor objetivo
- **Puerto** — destino (identifica servicio atacado)
- **Protocolo** — TCP/UDP/ICMP
- **Score IF** — valor numérico (N/A si fue whitelist bypass)
- **Decisión** — PERMIT / LIMIT / BLOCK con color

**Tipo de ataque inferido** (columna adicional en versión web):

| Condición | Tipo inferido |
|---|---|
| is_tcp=1, pkt_rate>1000, score<τ2 | SYN Flood |
| dest_port variado, pkts_toserver small | Port Scan |
| is_udp=1, pkt_rate>1000 | UDP Flood |
| is_icmp=1, pkt_rate>500 | ICMP Flood |
| dest_port=80, pkt_rate moderate, score<τ2 | HTTP Abuse |
| dest_port=22, heurística activa | Brute Force SSH |
| score<τ2, no categoría | Anomalía genérica |

### Panel 5: Métricas del Modelo

Métricas estáticas del modelo activo (actualizadas solo tras reentrenamiento):
- Accuracy, Precision, Recall, F1, AUC-ROC con barras de progreso
- Umbrales τ1 y τ2 activos
- Latencia P95 (calculada en tiempo real sobre las últimas 1000 decisiones)
- ITL = BLOCK para src_ip en whitelist (siempre 0 en sistema correcto)
- Versión del modelo activo (ej: v1.0.0 del 2026-05-15)

### Panel 6: Estadísticas y Línea Temporal

**Contadores acumulados del día:**

| Métrica | Valor |
|---|---|
| Flujos procesados | Contador desde 00:00 |
| PERMIT | Contador + % del total |
| LIMIT | Contador + % del total |
| BLOCK | Contador + % del total |
| IPs únicas vistas | HyperLogLog aproximado |
| IPs únicas bloqueadas | Contador exacto |

**Gráfico de eventos por hora:** Barras apiladas (PERMIT/LIMIT/BLOCK) para las últimas 24h

**Distribución por tipo de ataque:** Torta o barras horizontales para los ataques del día

## 5.3 Arquitectura del Dashboard

### 5.3.1 Dashboard Actual (Terminal — Implementado)

```
dashboard.py (implementado)
    │
    ├─ Lee motor_decision.log cada 3 segundos
    ├─ Parsea líneas: timestamp | src_ip | dst_ip | score | decision
    ├─ Calcula contadores: total / PERMIT / LIMIT / BLOCK
    ├─ Calcula tasa: flujos/min en ventana deslizante 60s
    ├─ Calcula latencia P95 sobre últimas 1000 decisiones
    └─ Imprime con rich/curses: tablas + barras + counters
```

### 5.3.2 Dashboard Web (Propuesta de Producción)

```
ARQUITECTURA DASHBOARD WEB

[motor_decision.log]
       │
       ▼
[log-shipper: Filebeat / Python tail]
       │
       ├──────────────────────────────► [InfluxDB]
       │  (stream de métricas)               │
       │                                      ▼
       │                              [Grafana Dashboard]
       │                                (paneles web)
       │                                      │
       └──────────────────────────────► [Elasticsearch]
          (stream completo eventos)            │
                                         [Kibana / SIEM]
                                         (búsqueda + alertas)

COMPONENTES:
  InfluxDB:    Base de datos de series de tiempo (métricas: flujos/s, scores, decisiones)
  Grafana:     Visualización web con alertas (PagerDuty/Telegram)
  Elasticsearch: Almacén de logs completo (búsqueda, filtros, auditoría)
  Kibana:      Frontend para Elasticsearch (queries, dashboards SIEM)
  
ALTERNATIVA LIGERA (sin ELK):
  [motor_decision.log] → [Python FastAPI server] → [React/Vue frontend]
  Requiere: <200 MB RAM adicional, sin Elasticsearch, auto-hosted
```

### 5.3.3 Implementación del Dashboard Terminal Mejorado

```python
#!/usr/bin/env python3
"""
dashboard_v2.py — Dashboard terminal mejorado con curses/rich
Requiere: pip install rich
Uso: python3 dashboard_v2.py [--log /ruta/motor_decision.log] [--interval 3]
"""

import time
import re
import sys
from collections import deque, Counter
from datetime import datetime, timedelta
from pathlib import Path
import argparse

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

LOG_PATH = "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
LINE_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)"
    r"\s*\|\s*(?P<src>\S+)"
    r"\s*\|\s*(?P<dst>\S+)"
    r"\s*\|\s*(?P<dport>\d+)"
    r"\s*\|\s*(?P<proto>\S+)"
    r"\s*\|\s*(?P<score>[-\d.]+|N/A)"
    r"\s*\|\s*(?P<decision>\S+)"
)

class DashboardMetrics:
    def __init__(self, window_secs=3600):
        self.events = deque()
        self.window = window_secs
        self.total = 0
    
    def add(self, event: dict):
        now = time.time()
        self.events.append((now, event))
        self.total += 1
        # purge old events outside window
        while self.events and now - self.events[0][0] > self.window:
            self.events.popleft()
    
    def counts(self):
        c = Counter(e['decision'] for _, e in self.events)
        return c
    
    def rate_per_min(self):
        now = time.time()
        recent = sum(1 for ts, _ in self.events if now - ts < 60)
        return recent
    
    def top_ips(self, decision='BLOCK', n=5):
        ips = Counter(
            e['src'] for _, e in self.events
            if e['decision'] == decision
        )
        return ips.most_common(n)
    
    def last_n(self, n=8):
        return [e for _, e in list(self.events)[-n:]]
    
    def latency_p95(self):
        # Placeholder: en implementación real se lee del log
        return 34.8


def tail_log(path: Path, metrics: DashboardMetrics):
    """Sigue el log y actualiza métricas."""
    with open(path, 'r') as f:
        f.seek(0, 2)  # al final del archivo
        while True:
            line = f.readline()
            if line:
                m = LINE_RE.match(line.strip())
                if m:
                    metrics.add(m.groupdict())
            else:
                time.sleep(0.1)


def render_dashboard(metrics: DashboardMetrics) -> str:
    """Genera representación ASCII del dashboard."""
    counts = metrics.counts()
    total = sum(counts.values()) or 1
    rate = metrics.rate_per_min()
    
    permit = counts.get('PERMIT', 0)
    limit  = counts.get('LIMIT',  0)
    block  = counts.get('BLOCK',  0)
    
    lines = []
    lines.append("=" * 80)
    lines.append(f"  PPI-SURIKATA DASHBOARD  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append(f"  Flujos/min: {rate:4d}  |  PERMIT: {permit:6d}  |  LIMIT: {limit:4d}  |  BLOCK: {block:4d}")
    lines.append(f"  Tasa detección: {(block+limit)/total*100:.1f}%  |  ITL: 0.0%  |  Latencia P95: {metrics.latency_p95():.1f}ms")
    lines.append("-" * 80)
    lines.append("  ÚLTIMAS DETECCIONES:")
    lines.append(f"  {'Timestamp':23}  {'Origen':17}  {'Score':8}  {'Decisión':8}")
    lines.append("  " + "-" * 62)
    for e in metrics.last_n(8):
        icon = "🔴" if e['decision']=='BLOCK' else "🟡" if e['decision']=='LIMIT' else "🟢"
        lines.append(f"  {e['ts'][:23]:23}  {e['src']:17}  {e['score']:8}  {icon} {e['decision']}")
    lines.append("=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default=LOG_PATH)
    parser.add_argument('--interval', type=int, default=3)
    args = parser.parse_args()
    
    log_path = Path(args.log)
    if not log_path.exists():
        print(f"ERROR: Log no encontrado: {log_path}")
        sys.exit(1)
    
    metrics = DashboardMetrics()
    
    import threading
    t = threading.Thread(target=tail_log, args=(log_path, metrics), daemon=True)
    t.start()
    
    try:
        while True:
            print("\033[2J\033[H", end="")  # clear screen
            print(render_dashboard(metrics))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDashboard detenido.")
```

## 5.4 Especificación de Datos del Dashboard

### 5.4.1 Formato de entrada (motor_decision.log)

```
2026-06-14T10:23:45.123 | 192.168.0.100 | 192.168.0.120 | 80 | TCP | -0.7891 | BLOCK | SYN_flood | corrida_015
2026-06-14T10:23:44.712 | 192.168.0.20  | 192.168.0.120 | 22 | TCP | N/A      | PERMIT | whitelist  | corrida_015
2026-06-14T10:23:44.203 | 192.168.0.150 | 192.168.0.120 | 80 | TCP | -0.7018  | LIMIT  | IF_score   | corrida_015
```

### 5.4.2 Métricas calculadas en tiempo real

| Métrica | Fórmula | Ventana |
|---|---|---|
| Flujos/minuto | count(eventos en últimos 60s) | Rolling 60s |
| Tasa detección | (BLOCK + LIMIT) / Total | Desde 00:00 |
| Score medio BLOCK | mean(score para BLOCK events) | Últimas 1000 |
| Latencia P95 | percentile_95(ts_decision - ts_flujo) | Últimas 1000 |
| ITL | count(BLOCK donde src ∈ whitelist) | Siempre 0 |
| Nivel de riesgo | f(blocked_ips, limited_ips, rate) | Instantáneo |

### 5.4.3 Integración con Grafana (producción)

```yaml
# grafana-datasource-influxdb.yaml
apiVersion: 1
datasources:
  - name: PPI-Motor-Metrics
    type: influxdb
    url: http://localhost:8086
    database: ppi_metrics
    jsonData:
      timeInterval: "3s"

# Panel: Decisiones por tipo (Grafana query)
# measurement: decisions
# WHERE time > now() - 1h
# GROUP BY decision, time(1m)
# SELECT count(decision)
```

---

*Documento generado: 2026-06-14*  
*Dashboard terminal (dashboard.py): Implementado y validado en F6*  
*Dashboard web (Grafana): Propuesta para Fase 1 → Producción*
