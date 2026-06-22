# F3 — Control en Tiempo Real (Motor + ipset)
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Aplicar la decisión del IF en la red de forma automática, inline y en tiempo real: cada flujo nuevo se evalúa y se actúa en < 500ms.

---

## Componentes

| Componente | Función |
|---|---|
| `scripts/motor_decision.py` | tail eve.json → extrae features → IF score → decisión |
| `scripts/enforce.sh` | control manual ipset (BLOCK/LIMIT/UNBLOCK) |
| ipset `ppi_blocked` | IPs en DROP permanente |
| ipset `ppi_limited` | IPs con hashlimit 100pkt/s |
| `scripts/dashboard_web.py` | Flask+SSE → visualización en :8080 |
| `config/systemd/ppi-motor.service` | servicio activo y habilitado |

---

## Flujo de decisión por flujo

```
eve.json (nuevo flujo)
    │
    ▼
Extraer 14 features
    │
    ▼
¿IP en whitelist? → SÍ → PERMIT (skip)
    │ NO
    ▼
IF score = modelo.decision_function(features)
    │
    ├── score > τ1 (-0.4459)          → PERMIT (log INFO)
    ├── τ2 < score ≤ τ1               → LIMIT  (hashlimit 100pkt/s)
    └── score ≤ τ2 (-0.6027)          → BLOCK  (DROP)
    │
    ▼
Detectores heurísticos (sobre τ):
  - BF SSH: 15 intentos/60s → BLOCK (5 → LIMIT)
  - HTTP Abuse: 100 req/30s → BLOCK (50 → LIMIT)
    │
    ▼
enforce.sh → ipset add ppi_blocked/ppi_limited <IP>
```

---

## Whitelist (nunca bloquear)

```
192.168.0.1    (gateway)
192.168.0.20   (Desktop — admin)
192.168.0.110  (Sensor — propio)
192.168.0.120  (Servidor — objetivo protegido)
192.168.0.130  192.168.0.140
127.0.0.1
```

---

## Métricas validadas (40 corridas F6)

| Métrica | Valor | Requisito |
|---|---|---|
| Latencia P95 | **34.8ms** | < 500ms ✅ |
| ITL (bloqueos incorrectos) | **0%** | = 0% ✅ |
| Disponibilidad | **100%** | ≥ 99% ✅ |
| Lead time SYN Flood | **~62s** | < 120s ✅ |

---

## Formato del log (motor_decision.log)

```
# Flujo anómalo bloqueado:
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.6207 grado=ALTA tipo=ANOMALIA_GENERICA
         byte_ratio=0.02 pkt_rate=10000.0 | BLOCK

# Flujo sospechoso limitado:
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
         score=-0.4937 grado=BAJA tipo=BAJA_ANOMALIA
         byte_ratio=1.97 pkt_rate=3000.0 | LIMIT

# Estadísticas cada 500 flujos:
INFO | Estadísticas | flows=500 anomalías=12 bf=0 http_abuse=0
      bloqueados=1 limitados=3 latencia_media=34.32ms
```

---

## Rutas en el sensor (192.168.0.110)

```
/home/m4rk/ppi-surikata-producto/
├── scripts/
│   ├── motor_decision.py
│   ├── enforce.sh
│   └── dashboard_web.py
├── results/
│   └── motor_decision.log     ← 1.1M+ líneas, fuente de F4 y F5
└── config/systemd/
    └── ppi-motor.service
```

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] Latencia P95 < 500ms
- [x] ITL = 0% (whitelist efectiva)
- [x] Disponibilidad ≥ 99%
- [x] SYN flood bloqueado en < 120s desde inicio
- [x] Dashboard web funcional en :8080
- [x] Un solo servicio motor activo (ppi-motor-universal deshabilitado)

---

## Bug resuelto — DUAL MOTOR

`ppi-motor-universal.service` estaba habilitado en paralelo a `ppi-motor.service`, contaminando el log con dos formatos diferentes. Solucionado: universal deshabilitado y stopped.
