# F5 — Especificación Técnica: Control Inline

## Objetivo
Aplicar las decisiones del motor en tiempo real sobre el tráfico de red mediante ipset/iptables en el servidor, y proveer interfaces de monitoreo (dashboard terminal y web).

## Scripts involucrados

| Script | Rol | Puerto/Interfaz |
|---|---|---|
| `scripts/motor_decision.py` | Enforcement automático (SSH a servidor) | — |
| `scripts/enforce.sh` | Control manual BLOCK/LIMIT/UNBLOCK | CLI |
| `scripts/dashboard.py` | Dashboard terminal ANSI | — |
| `scripts/dashboard_web.py` | Dashboard web Flask + SSE | :8080 |

## Estructura de control (servidor 192.168.0.120)

```
iptables INPUT chain:
  Línea 1: -m set --match-set ppi_blocked src -j DROP
  Línea 2: -m set --match-set ppi_limited src --hashlimit-above 100/sec burst 150 -j DROP

ipset ppi_blocked:  hash:ip timeout 300   → DROP completo
ipset ppi_limited:  hash:ip timeout 300   → limitado a 100 pkt/s
```

## enforce.sh — uso

```bash
# Bloquear IP manualmente (desde sensor o Desktop)
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 300

# Limitar IP manualmente
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 LIMIT 300

# Desbloquear IP
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

**Nota:** enforce.sh hace SSH al servidor (192.168.0.120) donde están los ipsets. El servidor tiene NOPASSWD configurado para `/usr/sbin/ipset` e `/usr/sbin/iptables`.

## Dashboard terminal (dashboard.py)

```bash
# Iniciar en sensor
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py --interval 3
```

Muestra: flows totales, anomalías, bloqueados/limitados, latencia media, eventos recientes.

## Dashboard web (dashboard_web.py)

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Interfaz HTML completa |
| `/api/stats` | GET | JSON con métricas en tiempo real |
| `/api/stream` | GET | SSE — push de nuevos eventos al navegador |
| `/api/alerts` | GET | Historial de alertas (cargado del log) |
| `/api/timeline` | GET | Datos para gráfica temporal |
| `/api/tipos` | GET | Distribución por tipo de anomalía |
| `/api/block` | POST | Bloquear IP manualmente `{"ip":"x.x.x.x"}` |
| `/api/unblock` | POST | Desbloquear IP `{"ip":"x.x.x.x"}` |

```bash
# Iniciar (en sensor, en background)
cd /home/m4rk/ppi-surikata-producto
nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &

# Acceder desde Desktop
# Navegador: http://192.168.0.110:8080
```

## Resultados de pruebas de integración (T3–T5)

| Prueba | Resultado |
|---|---|
| enforce.sh BLOCK | ✓ IP en ppi_blocked timeout 59 |
| enforce.sh LIMIT | ✓ IP en ppi_limited timeout 59 |
| enforce.sh UNBLOCK | ✓ Removido de ambos sets |
| Auto-expiry timeout | ✓ Expirado a los 5s |
| Dashboard web HTTP 200 | ✓ 17ms tiempo de respuesta |
| SSE /api/stream | ✓ Streaming activo |
| API block/unblock | ✓ `{"ok": true}` |
