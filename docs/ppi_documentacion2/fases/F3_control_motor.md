# F3 — Control en Tiempo Real (Motor + ipset + Dashboard)
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Aplicar la decisión del IF sobre cada flujo nuevo en la red de forma automática, inline y en tiempo real. Visualizar el estado del sistema en vivo. Notificar al operador ante eventos críticos.

---

## Componentes

| Componente | Función |
|---|---|
| `scripts/motor_decision.py` | tail eve.json → extrae features → IF score → decide PERMIT/LIMIT/BLOCK |
| `scripts/enforce.sh` | control manual ipset (BLOCK/LIMIT/UNBLOCK + timeout) |
| ipset `ppi_blocked` | IPs en DROP con timeout 300s (5 min) vía iptables |
| ipset `ppi_limited` | IPs con hashlimit 100pkt/s vía iptables, timeout 300s |
| `scripts/dashboard_web.py` | Servidor Flask+SSE en :8080 → dashboard en navegador |
| `scripts/dashboard.py` | Dashboard terminal (estadísticas cada 3s) |
| `config/systemd/ppi-motor.service` | Servicio systemd activo y habilitado |
| Telegram relay | Notificaciones BLOCK al operador (config/telegram.conf) |

---

## Flujo de decisión por flujo

```
eve.json (nuevo flujo)
    │
    ▼
Extraer 14 features (mismo orden que models/features.csv)
    │
    ▼
¿IP en whitelist? ──── SÍ ──→ PERMIT (skip)
    │ NO
    ▼
score = IF.decision_function(scaler.transform(features))
    │
    ├── score > τ1 (-0.4459)     → PERMIT  (log INFO)
    ├── τ2 < score ≤ τ1          → LIMIT   (hashlimit 100pkt/s)
    └── score ≤ τ2 (-0.6027)     → BLOCK   (DROP)
    │
    ▼
Detectores heurísticos:
    BF SSH:     ≥ 5 intentos/60s → LIMIT | ≥ 15 → BLOCK
    HTTP Abuse: ≥ 50 req/30s    → LIMIT | ≥ 100 → BLOCK
    │
    ▼
enforce.sh → ipset add ppi_blocked / ppi_limited <IP>
    │
    ▼
BLOCK → Telegram notificación al operador
```

---

## Dashboard web (puerto :8080)

Accesible desde Desktop: `http://192.168.0.110:8080`

Muestra en tiempo real:
- Flujos PERMIT / LIMIT / BLOCK (últimos 60s)
- IPs bloqueadas activas en ipset
- Latencia del pipeline
- Panel de predictor (P% del XGBoost — F4)
- Historial de alertas del predictor

```bash
# Iniciar si no está corriendo:
ssh m4rk@192.168.0.110 \
  "cd ppi-surikata-producto && nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &"
```

---

## Telegram (notificaciones)

- Configuración: `config/telegram.conf` (fuera de git — credenciales)
- Relay: `http://192.168.0.20:8889/telegram`
- Motor envía alerta cuando: BLOCK de IP no vista antes (dedup configurable)
- Cola no bloqueante: si el relay no responde, la alerta se descarta sin afectar el motor

---

## Whitelist (nunca bloquear)

```
192.168.0.1    192.168.0.20 (Desktop)
192.168.0.110  192.168.0.120 (Servidor)
192.168.0.130  192.168.0.140
127.0.0.1
```

---

## Formato del log (motor_decision.log)

```
# Flujo bloqueado:
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.6207 grado=ALTA tipo=ANOMALIA_GENERICA
         byte_ratio=0.02 pkt_rate=10000.0 | BLOCK

# Flujo limitado:
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.4937 grado=BAJA tipo=BAJA_ANOMALIA
         byte_ratio=1.97 pkt_rate=3000.0 | LIMIT

# Estadísticas cada 500 flujos:
INFO | Estadísticas | flows=500 anomalías=12 bf=0 http_abuse=0
      bloqueados=1 limitados=3 latencia_media=34.32ms
```

> Este log es la entrada de F4 (predictor XGBoost).

---

## Métricas validadas (40 corridas F6)

| Métrica | Valor | Requisito |
|---|---|---|
| Latencia P95 | **34.8ms** | < 500ms ✅ |
| ITL (bloqueos incorrectos) | **0%** | = 0% ✅ |
| Disponibilidad | **100%** | ≥ 99% ✅ |
| Lead time SYN Flood | **~62s** | < 120s ✅ |

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] Latencia P95 < 500ms
- [x] ITL = 0% (whitelist efectiva, ningún PERMIT bloqueado)
- [x] SYN flood bloqueado en < 120s desde inicio
- [x] Dashboard web accesible en :8080
- [x] Telegram notifica BLOCKs sin bloquear el motor
- [x] Un solo servicio motor activo (ppi-motor-universal deshabilitado)

---

## Bug resuelto

`ppi-motor-universal.service` corría en paralelo contaminando el log con dos formatos. Solucionado: universal stopped y disabled permanentemente.
