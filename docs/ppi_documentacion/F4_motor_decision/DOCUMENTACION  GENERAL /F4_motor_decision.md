# FASE 4 — Motor de Decisión + Integración con Pipeline

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fecha de ejecución:** 2–4 de junio 2026  

---

## Objetivo de la fase

Implementar el motor de decisión que conecta el sensor Suricata con el modelo de Isolation Forest, procesa los flujos de red en tiempo real, y toma decisiones de acción (PERMIT / LIMIT / BLOCK) sobre cada flow. Integrar el pipeline completo extremo a extremo: `eve.json → features → modelo → decisión → acción`.

---

## 1. Arquitectura del pipeline

```
Suricata (ens35)
      ↓
  eve.json
      ↓  (tail -f en tiempo real)
motor_decision.py
      ↓
  Extracción de 14 features
      ↓
  StandardScaler (scaler.pkl)
      ↓
  Isolation Forest (isolation_forest.pkl)
      ↓  anomaly score
  ┌─────────────────────────────────────────┐
  │         LÓGICA DE DECISIÓN              │
  │  score > τ1 (-0.4973)  →  PERMIT        │
  │  τ2 < score ≤ τ1       →  LIMIT         │
  │  score ≤ τ2 (-0.6873)  →  BLOCK         │
  │  +Detectores temporales SSH / HTTP       │
  └─────────────────────────────────────────┘
      ↓
  Control inline en servidor 192.168.0.120
      ↓
  Notificación Telegram (alertas inmediatas)
```

---

## 2. Implementación del motor

**Script principal:** `scripts/motor_decision.py`

El motor se ejecuta como **servicio systemd** en el sensor:

```bash
# Servicio: /etc/systemd/system/ppi-motor.service
sudo systemctl start ppi-motor.service
sudo systemctl status ppi-motor.service
```

### Componentes principales

#### 2.1 Lectura en tiempo real de eve.json

```python
def seguir_eve(path):
    f = open(path, 'r', errors='ignore')
    f.seek(0, 2)          # posición al final del archivo
    while True:
        line = f.readline()
        if line:
            yield line
        else:
            # Detectar rotación: si tamaño < posición actual
            if os.path.getsize(path) < f.tell():
                f.close()
                f = open(path, 'r', errors='ignore')
                f.seek(0, 2)
            time.sleep(0.2)
```

> **Fix importante:** Se implementó detección de rotación de `eve.json`. Suricata puede rotar el archivo con `logrotate`, lo que dejaba al motor leyendo desde una posición inválida. El fix verifica si el tamaño del archivo es menor que la posición actual y reabre el archivo.

#### 2.2 Filtros de entrada

Antes de clasificar un flow, el motor aplica:

1. Solo flows `event_type == "flow"`
2. Solo IPv4 (excluye IPv6)
3. Excluir IPs en whitelist: `{192.168.0.1, 192.168.0.20, 192.168.0.110, 192.168.0.120, 127.0.0.1, ...}`
4. Excluir IPs no bloqueables: broadcast (`0.0.0.0`, `255.255.255.255`, `*.*.*.255`), multicast
5. Solo flows con `pkts_toserver > 0`

#### 2.3 Extracción de features

Mismas 14 features del modelo (ver F3). Procesamiento en tiempo real:

```python
def extract_features(e):
    flow = e.get('flow', {})
    proto = e.get('proto', '').upper()
    dur = flow_duration(e)
    pts = flow.get('pkts_toserver', 0) or 0
    # ... cálculo de 14 features ...
    return np.array([[pts, ptc, bts, btc, dur,
                      pkt_rate, byte_rate, pkt_ratio,
                      byte_ratio, avg_pkt_size,
                      is_tcp, is_udp, is_icmp, dest_port]])
```

#### 2.4 Clasificación

```python
X = scaler.transform(extract_features(e))
score = clf.score_samples(X)[0]    # anomaly score
accion = decidir(score)             # PERMIT / LIMIT / BLOCK
```

---

## 3. Lógica de decisión triple

### Umbrales del modelo (τ1 y τ2)

```python
TAU1 = -0.4973   # PERMIT / LIMIT  (Youden index, TPR=91%)
TAU2 = -0.6873   # LIMIT  / BLOCK  (FPR≤2%, TPR=40.6%)

def decidir(score):
    if score > TAU1:   return 'PERMIT'
    elif score > TAU2: return 'LIMIT'
    else:              return 'BLOCK'
```

### Detector temporal de Brute Force SSH

Implementado como **heurística adicional** al modelo estadístico:

```python
SSH_PORT        = 22
BF_VENTANA_SEG  = 60    # ventana de 60 segundos
BF_UMBRAL_LIMIT = 5     # 5 intentos → LIMIT
BF_UMBRAL_BLOCK = 15    # 15 intentos → BLOCK directo
```

Funciona contando conexiones SSH por IP en una ventana deslizante. **Validado en vivo:** 25 intentos simultáneos desde Kali → detección en 60s → BLOCK.

### Detector temporal de HTTP Abuse

```python
HTTP_PORT         = 80
HTTP_VENTANA_SEG  = 30    # ventana de 30 segundos
HTTP_UMBRAL_LIMIT = 50    # 50 requests → LIMIT
HTTP_UMBRAL_BLOCK = 100   # 100 requests → BLOCK directo
```

**Validado en vivo:** curl en bucle desde Kali → 100 requests/30s → BLOCK + alerta Telegram.

---

## 4. Integración con Telegram

El motor envía alertas automáticas cuando aplica una acción BLOCK o LIMIT:

```python
TG_TOKEN   = "8677152686:..."
TG_CHAT_ID = "8512353253"

def telegram_alerta(mensaje):
    url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": mensaje}).encode()
    urllib.request.urlopen(url, data=data, timeout=3)
```

Tipos de alerta enviadas:
- `🚨 ANOMALÍA` — cuando score ≤ τ2 (BLOCK por modelo)
- `🔑 BRUTE FORCE SSH` — cuando intentos SSH ≥ umbral de bloqueo
- `🌐 HTTP ABUSE` — cuando requests HTTP ≥ umbral de bloqueo
- `⚠️ LIMIT` — cuando τ2 < score ≤ τ1

---

## 5. Medición de latencia del pipeline

**Archivo de referencia:** `results/latencia_pipeline.txt`

Medida sobre 1,000 flows reales:

| Métrica | Valor |
|---|---|
| Latencia media | **34.533 ms** |
| Latencia mínima | 34.224 ms |
| Latencia máxima | 38.717 ms |
| **Latencia P95** | **34.768 ms** |
| Throughput | 29 flows/segundo |
| Requisito del plan (< 500ms) | **CUMPLE** ✓ |

El pipeline completo `eve.json → features → scaler → IsolationForest → decisión` tarda **34.8ms en el percentil 95**, muy por debajo del límite de 500ms establecido en el plan.

---

## 6. Log de decisiones

**Archivo:** `results/motor_decision.log`

Formato de cada entrada:

```
TIMESTAMP | NIVEL | TIPO | src=IP dst=IP:PUERTO proto=PROTO score=SCORE | ACCIÓN
```

Ejemplos reales del log:

```
# Anomalía detectada por modelo (BLOCK)
2026-06-04 15:10:28,019 | WARNING | HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80
                          proto=TCP requests=100/30s | BLOCK → BLOCKED 192.168.0.100

# Tráfico sospechoso (LIMIT)
2026-06-04 15:10:24,271 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
                          proto=TCP score=-0.5382 | LIMIT → LIMITED 192.168.0.100

# Brute Force detectado (BLOCK)
2026-06-03 18:50:03,237 | WARNING | BRUTE-FORCE | src=192.168.0.100 dst=192.168.0.120:22
                          proto=TCP intentos=15/60s | BLOCK → BLOCKED 192.168.0.100

# Estadísticas periódicas cada 500 flows
2026-06-04 15:12:43,665 | INFO | Estadísticas | flows=4000 anomalías=3943
                          bf=0 http_abuse=3904 bloqueados=1 limitados=0 latencia_media=34.53ms
```

---

## 7. Dashboard en tiempo real

**Script:** `scripts/dashboard.py`

Muestra estadísticas actualizadas cada 3 segundos leyendo el log:

```
╔══════════════════════════════════════════════════════════════╗
║   PPI — DASHBOARD DETECCIÓN DE ANOMALÍAS DE RED             ║
║   2026-06-04 20:25:00   Universidad Peruana Unión 2026      ║
╠══════════════╦══════════════╦══════════════╦════════════════╣
║   FLOWS      ║  ANOMALÍAS   ║  BLOQUEADOS  ║   LIMITADOS    ║
║      1,500   ║      1,619   ║          1   ║          0     ║
╠══════════════════════════════════════════════════════════════╣
║  Brute Force SSH :     20   HTTP Abuse:   403  Latencia:34ms║
╠══════════════════════════════════════════════════════════════╣
║  ÚLTIMAS ALERTAS                                             ║
║  ...                                                         ║
╚══════════════════════════════════════════════════════════════╝
```

**Uso:**
```bash
ssh m4rk@192.168.0.110
cd /home/m4rk/ppi-surikata-producto
python3 scripts/dashboard.py
```

---

## 8. Prueba del pipeline end-to-end

Se realizó una prueba de validación con escenarios simultáneos:

**Escenario:** A2 (SSH legítimo desde Desktop) + B2 (port scan desde Kali) simultáneos.

| Flujo | Clasificación | Acción | Score |
|---|---|---|---|
| Desktop 192.168.0.20 → Server:22 | NORMAL | PERMIT | -0.434 |
| Kali 192.168.0.100 → Server:* | ANÓMALO | BLOCK | -0.655 |

**Resultado:** 1,705/1,705 flows de port scan detectados. 0 falsas alarmas en SSH legítimo. Latencia de detección: ~26 segundos desde inicio del ataque.

---

## 9. Explainabilidad de decisiones (mejora v2)

**Fecha de implementación:** 8 de junio 2026

Cada decisión BLOCK o LIMIT del modelo incluye ahora una explicación de las top-3 features con mayor desviación z-score respecto al perfil de tráfico normal entrenado.

### Función implementada

```python
def explicar_anomalia(X_raw, scaler):
    """Top-3 features con mayor desviación z-score respecto al tráfico normal entrenado."""
    z = (X_raw[0] - scaler.mean_) / (scaler.scale_ + 1e-9)
    ranked = sorted(zip(FEATURES, z), key=lambda x: abs(x[1]), reverse=True)[:3]
    return " | ".join(f"{feat}:z={val:+.1f}" for feat, val in ranked)
```

**Principio:** el `scaler` fue ajustado exclusivamente con tráfico normal (Desktop 192.168.0.20). La media (`scaler.mean_`) y desviación (`scaler.scale_`) representan el perfil del tráfico legítimo. Un z-score alto indica que esa feature se aleja significativamente de ese perfil.

### Ejemplos de salida

```
# SYN Flood detectado:
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.7214
  razón=[pkt_rate:z=+45.2 | pkts_toserver:z=+38.7 | bytes_toserver:z=+12.1] | BLOCK

# Port Scan detectado:
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:443 proto=TCP score=-0.6550
  razón=[dest_port:z=+8.3 | pkt_ratio:z=+6.1 | duration:z=-4.2] | BLOCK

# Sospechoso (LIMIT):
SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.5382
  razón=[pkt_rate:z=+12.1 | byte_rate:z=+9.8 | avg_pkt_size:z=-3.1] | LIMIT
```

### Alerta Telegram actualizada

```
🚨 PPI ALERTA — ANOMALÍA
Accion : BLOCK
IP     : 192.168.0.100
Proto  : TCP
Puerto : 80
Score  : -0.7214
Razon  : pkt_rate:z=+45.2 | pkts_toserver:z=+38.7 | bytes_toserver:z=+12.1
Hora   : 2026-06-08 15:30:00
```

### Integración en el motor

- `X_raw = extract_features(e)` se separa de `scaler.transform(X_raw)` para preservar los valores originales
- `razon = explicar_anomalia(X_raw, scaler)` se calcula únicamente en ramas BLOCK y LIMIT (no en PERMIT), sin impacto en latencia para el flujo mayoritario
- El campo `razón=[...]` se agrega a todas las líneas WARNING del log
- El campo `Razon:` se agrega a todas las alertas Telegram de anomalía y sospechoso

### Por qué los detectores temporales no incluyen z-scores

Los detectores de Brute Force SSH y HTTP Abuse son heurísticos temporales, no clasificación por modelo. Su razón ya está explícita en el mensaje (`intentos=15/60s`, `requests=100/30s`), por lo que no requieren z-scores adicionales.

---

## 10. Criterios de cierre de F4

| Criterio | Estado |
|---|---|
| Pipeline `eve.json → features → modelo → decisión` funcionando | ✅ |
| Lógica triple PERMIT / LIMIT / BLOCK implementada | ✅ |
| Detector temporal Brute Force SSH (ventana 60s) | ✅ |
| Detector temporal HTTP Abuse (ventana 30s) | ✅ |
| Notificaciones Telegram en tiempo real | ✅ |
| Latencia P95 = 34.8ms (< 500ms requerido) | ✅ |
| Log de decisiones con formato estructurado | ✅ |
| Dashboard en tiempo real | ✅ |
| Prueba end-to-end validada | ✅ |
| Servicio systemd configurado | ✅ |
| Explainabilidad z-score en log y Telegram (v2) | ✅ |

**F4 CERRADA ✅ — 4 de junio 2026 | Mejora explainabilidad — 8 de junio 2026**

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| `motor_decision.py` | `scripts/` | **Script principal del motor** |
| `dashboard.py` | `scripts/` | Dashboard en tiempo real |
| `motor_decision.log` | `results/` | **Log de decisiones en producción** |
| `latencia_pipeline.txt` | `results/` | Medición formal de latencia |
| `ppi-motor.service` | `/etc/systemd/system/` | Servicio de inicio automático |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
