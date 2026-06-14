# FASE 5 — Control Inline

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fecha de ejecución:** 2–4 de junio 2026  

---

## Objetivo de la fase

Implementar el mecanismo de control inline que aplica las decisiones del motor (PERMIT / LIMIT / BLOCK) sobre el tráfico real en el servidor objetivo `192.168.0.120`, usando `ipset` e `iptables` para el bloqueo total y `iptables hashlimit` para la limitación de tasa.

---

## 1. Arquitectura del control inline

```
Motor de decisión (sensor 192.168.0.110)
              ↓  SSH + sudo
    Servidor objetivo (192.168.0.120)
              ↓
    ┌─────────────────────────────────────────┐
    │           CONTROL INLINE                │
    │                                         │
    │  ipset ppi_blocked  →  iptables DROP    │
    │  ipset ppi_limited  →  iptables LIMIT   │
    │                        (100 pkt/s)      │
    └─────────────────────────────────────────┘
```

El motor en el sensor `192.168.0.110` se comunica con el servidor `192.168.0.120` vía SSH para aplicar las acciones de bloqueo/limitación en tiempo real.

---

## 2. Sets ipset configurados

Se crearon dos sets `hash:ip` en el servidor con **timeout automático de 300 segundos**:

### ppi_blocked — Bloqueo total (DROP)

```bash
sudo ipset create ppi_blocked hash:ip timeout 300
```

| Parámetro | Valor | Descripción |
|---|---|---|
| Tipo | `hash:ip` | Un hash por IP de origen |
| Timeout | 300s | Las IPs se desbloquean automáticamente tras 5 min |
| Acción | DROP | Todo paquete de esta IP es descartado |

### ppi_limited — Limitación de tasa (hashlimit)

```bash
sudo ipset create ppi_limited hash:ip timeout 300
```

| Parámetro | Valor | Descripción |
|---|---|---|
| Tipo | `hash:ip` | Un hash por IP de origen |
| Timeout | 300s | Las IPs se desblimitan automáticamente tras 5 min |
| Acción | DROP si excede 100 pkt/s | Permite tráfico dentro del límite |

---

## 3. Reglas iptables configuradas

Se insertaron dos reglas en la cadena INPUT del servidor, verificadas con:

```bash
sudo iptables -L INPUT -n | grep ppi
```

**Salida real del servidor 192.168.0.120:**
```
DROP  0  --  0.0.0.0/0  0.0.0.0/0  match-set ppi_blocked src
DROP  0  --  0.0.0.0/0  0.0.0.0/0  match-set ppi_limited src limit: above 100/sec burst 150 mode srcip
```

### Regla 1 — BLOCK (DROP total)

```bash
sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP
```

Cualquier paquete cuyo `src_ip` esté en `ppi_blocked` → **DROP inmediato**.

### Regla 2 — LIMIT (rate limit 100 pkt/s)

```bash
sudo iptables -I INPUT 2 \
  -m set --match-set ppi_limited src \
  -m hashlimit \
    --hashlimit-name ppi_limit \
    --hashlimit-above 100/sec \
    --hashlimit-mode srcip \
    --hashlimit-burst 150 \
  -j DROP
```

IPs en `ppi_limited` pueden enviar hasta **100 paquetes/segundo**. El exceso es descartado. El módulo `hashlimit` mantiene un contador independiente por IP de origen (`--hashlimit-mode srcip`).

---

## 4. Funciones de control en el motor

Las acciones se aplican remotamente desde el sensor al servidor vía SSH:

```python
def bloquear_ip(ip):
    """BLOCK: agrega IP al set ppi_blocked → DROP total."""
    out = _ssh(
        f'sudo ipset add {SET_BLOCK} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
        f'&& echo "BLOCKED {ip}"'
    )
    return out

def limitar_ip(ip):
    """LIMIT: agrega IP al set ppi_limited → DROP si excede 100 pkt/s."""
    out = _ssh(
        f'sudo ipset add {SET_LIMIT} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
        f'&& echo "LIMITED {ip}"'
    )
    return out
```

La flag `-exist` evita errores si la IP ya está en el set (idempotente).

---

## 5. Script de control manual

**Archivo:** `scripts/enforce.sh`

Para aplicar acciones manualmente durante demos o mantenimiento:

```bash
# Bloquear una IP manualmente
bash scripts/enforce.sh 192.168.0.100 BLOCK 300

# Limitar una IP manualmente
bash scripts/enforce.sh 192.168.0.100 LIMIT 300

# Desbloquear una IP
bash scripts/enforce.sh 192.168.0.100 UNBLOCK
```

**Salida esperada:**
```
2026-06-04 20:30:00 | BLOCK | 192.168.0.100 | timeout=300s
2026-06-04 20:35:00 | UNBLOCK | 192.168.0.100
```

---

## 6. Inicialización automática del servidor

Al arrancar el motor, la función `inicializar_servidor()` configura todo automáticamente (idempotente):

```python
def inicializar_servidor():
    # Crear sets si no existen
    _ssh(f'sudo ipset create {SET_BLOCK} hash:ip timeout {TIMEOUT_SEC} 2>/dev/null || true')
    _ssh(f'sudo ipset create {SET_LIMIT} hash:ip timeout {TIMEOUT_SEC} 2>/dev/null || true')
    
    # Regla BLOCK (idempotente)
    _ssh(f'sudo iptables -C INPUT -m set --match-set {SET_BLOCK} src -j DROP 2>/dev/null '
         f'|| sudo iptables -I INPUT -m set --match-set {SET_BLOCK} src -j DROP')
    
    # Regla LIMIT con hashlimit (idempotente)
    _ssh(f'sudo iptables -C INPUT -m set --match-set {SET_LIMIT} src '
         f'-m hashlimit --hashlimit-name ppi_limit --hashlimit-above 100/sec '
         f'--hashlimit-mode srcip --hashlimit-burst 150 -j DROP 2>/dev/null '
         f'|| sudo iptables -I INPUT 2 ...')
```

**Log de confirmación:**
```
2026-06-04 19:42:21 | INFO | Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=-0.4973 τ2=-0.6873
```

---

## 7. Comportamiento ante IPs broadcast/multicast

Se implementó un filtro para prevenir errores de ipset con IPs que no pueden almacenarse en sets `hash:ip`:

```python
def es_ip_bloqueable(ip: str) -> bool:
    obj = ipaddress.ip_address(ip)
    return not (obj.is_unspecified       # 0.0.0.0
                or obj.is_multicast      # 224.x.x.x - 239.x.x.x
                or obj.is_reserved
                or str(obj).endswith('.255')  # broadcasts de subred
                or obj == ipaddress.ip_address('255.255.255.255'))
```

**Problema original:** Los flows DHCP (`0.0.0.0 → 255.255.255.255`) pasaban al motor y al intentar bloquearlos generaban el error:
```
ipset v7.19: Null-valued element, cannot be stored in a hash type of set
```
**Solución:** Filtro aplicado antes de cualquier intento de clasificación o bloqueo.

---

## 8. Timeout automático de bloqueos

Todos los bloqueos y límites tienen un **timeout de 300 segundos (5 minutos)**. Esto garantiza que:

- Las IPs bloqueadas se desbloquean automáticamente sin intervención manual
- El sistema no acumula bloqueos permanentes de IPs legítimas mal clasificadas
- El servidor mantiene disponibilidad ante falsos positivos

El timeout se gestiona directamente por el kernel vía `ipset`, sin necesidad de un proceso adicional.

---

## 9. Validaciones del control inline realizadas

| Prueba | Comando desde Kali | Resultado observado |
|---|---|---|
| BLOCK por model (port scan) | `nmap -sS 192.168.0.120` | IP bloqueada en < 60s, paquetes DROPeados |
| BLOCK por Brute Force | `25 intentos SSH simultáneos` | BLOCK tras 15 intentos/60s |
| BLOCK por HTTP Abuse | `curl en bucle continuo` | BLOCK tras 100 requests/30s |
| LIMIT validado | `curl en bucle (B5)` | `SOSPECHOSO score=-0.51 LIMIT → LIMITED` |
| UNBLOCK automático | Esperar 300s | IP removida del set automáticamente |
| IPs broadcast | Tráfico DHCP | Filtradas silenciosamente, sin error ipset |

---

## 10. Umbrales finales documentados

**Archivo:** `results/umbrales_finales.txt`

Documento formal que registra todos los umbrales del sistema:

| Umbral | Valor | Criterio |
|---|---|---|
| `clf.offset_` | -0.5481 | contamination=0.05 |
| τ1 (PERMIT/LIMIT) | -0.4973 | Youden index máximo |
| τ2 (LIMIT/BLOCK) | -0.6873 | FPR ≤ 2% |
| BF SSH LIMIT | 5 intentos/60s | Heurístico temporal |
| BF SSH BLOCK | 15 intentos/60s | Heurístico temporal |
| HTTP LIMIT | 50 requests/30s | Heurístico temporal |
| HTTP BLOCK | 100 requests/30s | Heurístico temporal |
| Timeout bloqueos | 300s | Desbloqueo automático |

---

## 11. Criterios de cierre de F5

| Criterio | Estado |
|---|---|
| ipsets `ppi_blocked` y `ppi_limited` creados | ✅ |
| Regla iptables DROP para `ppi_blocked` | ✅ |
| Regla iptables hashlimit (100 pkt/s) para `ppi_limited` | ✅ |
| Función `bloquear_ip()` implementada y probada | ✅ |
| Función `limitar_ip()` implementada y probada | ✅ |
| `enforce.sh` para control manual | ✅ |
| Filtro IPs broadcast/multicast implementado | ✅ |
| Timeout automático de 300s configurado | ✅ |
| Inicialización automática al arranque del motor | ✅ |
| BLOCK validado en vivo (port scan, brute force, HTTP abuse) | ✅ |
| LIMIT validado en vivo (HTTP abuse lento) | ✅ |
| `umbrales_finales.txt` generado | ✅ |

**F5 CERRADA ✅ — 4 de junio 2026**

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| `motor_decision.py` | `scripts/` | Contiene `bloquear_ip()`, `limitar_ip()`, `inicializar_servidor()` |
| `enforce.sh` | `scripts/` | **Script de control manual BLOCK/LIMIT/UNBLOCK** |
| `umbrales_finales.txt` | `results/` | Documento formal de todos los umbrales |
| `motor_decision.log` | `results/` | Evidencia de acciones BLOCK/LIMIT aplicadas |

**Comandos de verificación en el servidor (192.168.0.120):**
```bash
# Ver IPs actualmente bloqueadas
sudo ipset list ppi_blocked

# Ver IPs actualmente limitadas
sudo ipset list ppi_limited

# Ver reglas iptables activas
sudo iptables -L INPUT -n | grep ppi
```

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
