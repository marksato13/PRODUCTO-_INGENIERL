# F4 — Especificación Técnica: Motor de Decisión

## Objetivo
Procesar flows de Suricata en tiempo real, puntuar cada flow con el modelo Isolation Forest y tomar la acción de red correspondiente (PERMIT / LIMIT / BLOCK).

## Scripts involucrados

| Script | Entrada | Proceso | Salida |
|---|---|---|---|
| `scripts/motor_decision.py` | `/var/log/suricata/eve.json` (tail -f) | Extrae features → escala → puntúa → decide | `results/motor_decision.log`, acciones ipset en 192.168.0.120 |

## Lógica de decisión triple

```
score = IsolationForest.score_samples(flow)   # rango [-1, 0]

if ip in WHITELIST:
    accion = IGNORAR

elif score > τ1 (-0.4650):
    accion = PERMIT           # tráfico normal

elif score > τ2 (-0.6118):
    accion = LIMIT            # sospechoso → hashlimit 100 pkt/s

else:                         # score ≤ τ2
    accion = BLOCK            # anómalo confirmado → DROP
```

## Detectores heurísticos (complementan el modelo IF)

| Detector | Ventana | Umbral LIMIT | Umbral BLOCK | Puerto |
|---|---|---|---|---|
| Brute Force SSH | 60 s | 5 intentos | 15 intentos | TCP/22 |
| HTTP Abuse | 30 s | 50 requests | 100 requests | TCP/80 |

Los detectores operan **independientemente** del score IF y pueden activar LIMIT/BLOCK aunque el score del flow individual sea normal.

## Enforcement en servidor (192.168.0.120)

| Acción | Mecanismo | Comando |
|---|---|---|
| BLOCK | ipset + iptables DROP | `sudo ipset add ppi_blocked <IP> timeout 300` |
| LIMIT | ipset + iptables hashlimit | `sudo ipset add ppi_limited <IP> timeout 300` |
| UNBLOCK | eliminar de ambos sets | `bash scripts/enforce.sh <IP> UNBLOCK` |

- Timeout por defecto: **300 s** (auto-expiry)
- Los sets se crean en el servidor en el arranque del motor
- `enforce.sh` hace SSH al servidor para manipular los sets directamente

## Parámetros de arranque

El motor lee τ1/τ2 de `results/metricas_offline.txt` en cada inicio. Si el archivo no existe, usa los valores por defecto hardcoded:
```python
TAU1, TAU2 = -0.4650, -0.6118  # valores por defecto
```

## Formato del log (`results/motor_decision.log`)

```
# Evento de anomalía:
2026-06-16 15:39:01 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=-0.5045 | LIMIT

# Estadísticas cada 500 flows:
2026-06-16 15:39:06 | INFO | Estadísticas | flows=500 anomalías=2 bf=0 http_abuse=0 bloqueados=1 limitados=1 latencia_media=34.51ms
```

## Métricas de rendimiento validadas

| Métrica | Valor | Requisito |
|---|---|---|
| Latencia media por flow | 34.5 ms | < 500 ms ✓ |
| Latencia P95 | 34.8 ms | < 500 ms ✓ |
| Throughput | 29 flows/segundo | — |
| ITL (interrupción tráfico legítimo) | 0% | = 0% ✓ |

## Secuencia de operación F4
```bash
# Iniciar motor (sensor)
sudo systemctl start ppi-motor.service
sudo systemctl status ppi-motor.service

# Ver log en tiempo real
tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log

# Control manual
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 300
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```
