# F4 — Especificación Técnica: Motor de Decisión en Tiempo Real

## 1. Objetivo

Procesar flujos de Suricata en tiempo real, puntuar cada flow con el modelo
Isolation Forest y tomar la acción de red correspondiente (PERMIT / LIMIT / BLOCK).
Los umbrales τ1/τ2 se leen automáticamente de `results/metricas_offline.txt` al
arrancar — sin edición manual tras re-entrenamientos.

---

## 2. Entradas

| Entrada | Ruta | Descripción |
|---|---|---|
| Flujos en tiempo real | `/var/log/suricata/eve.json` | tail -f — un JSON por línea |
| Modelo IF | `models/isolation_forest.pkl` | Generado por `fase3_entrenar.py` |
| Scaler | `models/scaler.pkl` | Generado por `fase3_entrenar.py` |
| Features | `models/features.csv` | 14 nombres de columnas — valida orden en cada flow |
| Umbrales | `results/metricas_offline.txt` | τ1 y τ2 — leídos al arrancar el motor |

---

## 3. Salidas

| Salida | Ruta | Descripción |
|---|---|---|
| Log del motor | `results/motor_decision.log` | Decisiones por flow + estadísticas cada 500 flows |
| Bloqueos activos | ipset `ppi_blocked` en servidor .120 | IPs con DROP activo |
| Limitaciones activas | ipset `ppi_limited` en servidor .120 | IPs con hashlimit 100 pkt/s |

---

## 4. Carga de umbrales al arrancar

El motor lee τ1/τ2 de `metricas_offline.txt` en cada inicio:

```python
# scripts/motor_decision.py (arranque)
TAU1, TAU2 = -0.4459, -0.6027   # valores por defecto

_METRICAS = 'results/metricas_offline.txt'
if os.path.exists(_METRICAS):
    for _line in open(_METRICAS):
        if re.match(r'\s*tau1\s*:\s*[-\d]', _line):
            TAU1 = float(_line.split(':')[1].split('#')[0].strip())
        elif re.match(r'\s*tau2\s*:\s*[-\d]', _line):
            TAU2 = float(_line.split(':')[1].split('#')[0].strip())
```

El regex `r'\s*tau1\s*:\s*[-\d]'` previene que se parsee `tau1_fpr` accidentalmente.
Si `metricas_offline.txt` no existe, usa los valores por defecto hardcoded.

---

## 5. Lógica de decisión por flow

```
score = IsolationForest.score_samples(flow_features)   # rango [-1, 0]

1. ip_origen in WHITELIST?      → IGNORAR (nunca bloquear)
2. score > τ1 (-0.4459)?        → PERMIT  (tráfico normal)
3. score > τ2 (-0.6027)?        → LIMIT   (sospechoso → hashlimit 100 pkt/s)
4. score ≤ τ2                   → BLOCK   (anómalo confirmado → DROP)
```

**Whitelist** (hardcoded en el motor):
`192.168.0.1`, `192.168.0.20`, `192.168.0.110`, `192.168.0.120`, `192.168.0.130`,
`192.168.0.140`, `127.0.0.1`

---

## 6. Detectores heurísticos (complementan el modelo IF)

Operan **independientemente** del score IF sobre ventanas deslizantes en memoria (`deque`):

| Detector | Ventana | Umbral LIMIT | Umbral BLOCK | Puerto |
|---|---|---|---|---|
| Brute Force SSH | 60 s | ≥ 5 intentos | ≥ 15 intentos | TCP/22 |
| HTTP Abuse | 30 s | ≥ 50 requests | ≥ 100 requests | TCP/80 |

Un flow puede recibir BLOCK por heurística aunque su score IF indique PERMIT.
Los detectores cubren ataques como BruteForce (B6) y HTTPAbuse (B5) que pueden tener
scores IF moderados pero patrones de frecuencia claramente anómalos.

---

## 7. Enforcement en servidor (192.168.0.120)

El motor en el sensor ejecuta `enforce.sh` que hace SSH al servidor para manipular ipset:

```bash
# scripts/enforce.sh — ejecutado por motor_decision.py
SERVIDOR="192.168.0.120"
_srv() { ssh -o BatchMode=yes m4rk@$SERVIDOR "$1"; }

case "$ACCION" in
  BLOCK)   _srv "sudo ipset add ppi_blocked $IP timeout $TIMEOUT -exist" ;;
  LIMIT)   _srv "sudo ipset add ppi_limited $IP timeout $TIMEOUT -exist" ;;
  UNBLOCK) _srv "sudo ipset del ppi_blocked $IP 2>/dev/null || true"
           _srv "sudo ipset del ppi_limited $IP 2>/dev/null || true" ;;
esac
```

| Acción | Mecanismo | Timeout por defecto |
|---|---|---|
| BLOCK | `ipset ppi_blocked` → iptables DROP | 300 s |
| LIMIT | `ipset ppi_limited` → hashlimit 100 pkt/s | 300 s |
| UNBLOCK | elimina de ambos sets | inmediato |

**Los ipsets residen en el servidor (.120), no en el sensor (.110.**
El servidor tiene `NOPASSWD` para `/usr/sbin/ipset` en sudoers.

---

## 8. Formato del log (`results/motor_decision.log`)

```
# Arranque — lee τ de metricas_offline.txt
2026-06-16 17:38:01 | INFO | Modelo cargado | τ1=-0.4459 | τ2=-0.6027

# Flow normal (DEBUG, no aparece en log estándar)
# Flow sospechoso (WARNING):
2026-06-16 19:38:01 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.5045 | LIMIT

# Flow anómalo (WARNING):
2026-06-16 19:38:42 | WARNING | ANOMALÍA   | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.7100 | BLOCK

# Estadísticas cada 500 flows:
2026-06-16 19:39:06 | INFO | Estadísticas | flows=500 anomalías=2 bf=0 http_abuse=0 bloqueados=1 limitados=1 latencia_media=34.51ms
```

---

## 9. Métricas de rendimiento validadas

| Métrica | Valor | Requisito |
|---|---|---|
| Latencia media por flow | 34.5 ms | < 500 ms ✓ |
| Latencia P95 | 34.8 ms | < 500 ms ✓ |
| Lead Time detección SYN Flood | ~62 s | < 120 s ✓ |
| ITL (interrupción tráfico legítimo) | 0% | = 0% ✓ |
| Disponibilidad servicio | 100% | > 99% ✓ |

**Lead Time de ~62 s** se explica por el timeout de Suricata para flows TCP
half-open (~60 s). Suricata no emite el evento `flow` hasta que la conexión
se cierra o expira — el motor no puede actuar antes de recibir el evento.

---

## 10. Secuencia de operación F4

```bash
# Iniciar motor en sensor
sudo systemctl start ppi-motor.service

# Verificar que leyó τ correctamente
grep "τ1=" results/motor_decision.log | tail -1
# Esperado: τ1=-0.4459 τ2=-0.6027

# Ver log en tiempo real
tail -f results/motor_decision.log

# Control manual
bash scripts/enforce.sh 192.168.0.100 BLOCK 300
bash scripts/enforce.sh 192.168.0.100 UNBLOCK

# Dashboard web en tiempo real (puerto 8080)
nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &
# Acceder desde Desktop: http://192.168.0.110:8080
```

---

## 11. Criterios de éxito (salida de F4)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| Motor activo | `systemctl is-active ppi-motor.service` | `active` |
| τ leídos de archivo | `grep τ1 results/motor_decision.log` | τ1=−0.4459 |
| Flow procesado | `tail -5 results/motor_decision.log` | Líneas de eventos |
| BLOCK funciona | `bash enforce.sh 192.168.0.100 BLOCK 10` | IP en `ipset list ppi_blocked` en servidor |
| Latencia OK | estadísticas en log | latencia_media < 500 ms |
