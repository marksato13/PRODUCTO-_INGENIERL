# F5 — Control Inline

**Fecha de ejecución:** 2 – 4 de junio 2026
**Objetivo:** Aplicar las decisiones del motor (BLOCK/LIMIT) sobre el tráfico real en el servidor objetivo mediante ipset e iptables, con timeout automático y control manual.

---

## Diagrama

```mermaid
flowchart TD

    subgraph MOTOR["Motor — Sensor 192.168.0.110"]
        DEC["decidir(score)\nBLOCK → bloquear_ip(src_ip)\nLIMIT  → limitar_ip(src_ip)"]
        ENF["scripts/enforce.sh\nControl manual:\nBLOCK · LIMIT · UNBLOCK"]
    end

    subgraph SSH_CANAL["Canal SSH — Sensor → Servidor"]
        SSHC["ssh -o StrictHostKeyChecking=no\n    -o ConnectTimeout=5\n    m4rk@192.168.0.120\n    'sudo ipset add ...'"]
    end

    subgraph SERVIDOR["Servidor — 192.168.0.120"]
        direction TB

        subgraph IPSET_B["ipset ppi_blocked  (hash:ip)"]
            IB["timeout=300s  (5 min, auto-expiración)\nReferencias activas: 2\nEntradas actuales: 0\n(sin IPs bloqueadas en este momento)"]
        end

        subgraph IPSET_L["ipset ppi_limited  (hash:ip)"]
            IL["timeout=300s  (5 min, auto-expiración)\nReferencias activas: 1\nEntradas actuales: 0"]
        end

        subgraph IPTABLES["iptables — cadena INPUT"]
            R1["Regla 1 (línea 1):\nDROP  match-set ppi_blocked src\n→ todo paquete de IP bloqueada se descarta"]
            R2["Regla 2 (línea 2):\nDROP  match-set ppi_limited src\n  hashlimit above 100/sec burst 150 mode srcip\n→ paquetes en exceso de 100/s se descartan"]
        end

        TO["Timeout automático 300s\nEl kernel desregistra la IP del set\nsin intervención del motor"]

        IB --> R1
        IL --> R2
        R1 & R2 --> TO
    end

    subgraph MANUAL["Control manual — scripts/enforce.sh"]
        EM["Uso:\nbash scripts/enforce.sh <ip> BLOCK|LIMIT|UNBLOCK [timeout]\n\nBLOCK:   sudo ipset add ppi_blocked  IP timeout 300 -exist\nLIMIT:   sudo ipset add ppi_limited  IP timeout 300 -exist\nUNBLOCK: sudo ipset del ppi_blocked  IP\n         sudo ipset del ppi_limited  IP"]
    end

    subgraph DOCS["Documentación formal"]
        UD["results/umbrales_finales.txt  1.9 KB\nτ1=-0.4973 · τ2=-0.6873\nBF SSH: 5→LIMIT / 15→BLOCK / ventana 60s\nHTTP:   50→LIMIT / 100→BLOCK / ventana 30s\ntimeout bloqueos: 300s"]
    end

    DEC -->|"bloquear_ip() / limitar_ip()"| SSH_CANAL
    ENF -->|"ejecución manual"| SERVIDOR
    SSH_CANAL --> IPSET_B
    SSH_CANAL --> IPSET_L
    MANUAL --> SERVIDOR

    subgraph TRAFICO["Tráfico entrante al servidor"]
        TN["IP normal (no en sets)\n→ ACCEPT (fluye normalmente)"]
        TB["IP en ppi_blocked\n→ DROP inmediato\n(0 paquetes pasan)"]
        TL["IP en ppi_limited\n→ ACCEPT hasta 100 pkt/s\n→ DROP si excede burst 150"]
    end

    R1 -.->|"IP bloqueada"| TB
    R2 -.->|"IP limitada"| TL

    subgraph INIT["Inicialización automática al arrancar el motor"]
        INI["inicializar_servidor()\n① ipset create ppi_blocked hash:ip timeout 300 (idempotente)\n② ipset create ppi_limited hash:ip timeout 300 (idempotente)\n③ iptables -I INPUT ... DROP ppi_blocked  (si no existe)\n④ iptables -I INPUT 2 ... hashlimit ppi_limited (si no existe)\n→ Log: 'Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s)'"]
    end

    INI -.->|"al iniciar ppi-motor.service"| SERVIDOR
    DOCS -.->|"referencia formal"| UD

    CONECTOR(["→ F6: Validación\nEstado del sistema listo para\n40 corridas de experimentación"])
    TO ==>|"sistema estabilizado"| CONECTOR

    style MOTOR fill:#fce4ec,stroke:#c62828
    style SSH_CANAL fill:#f3f3f3,stroke:#757575
    style SERVIDOR fill:#fff3e0,stroke:#e65100
    style IPSET_B fill:#ffcdd2,stroke:#b71c1c
    style IPSET_L fill:#ffe0b2,stroke:#e65100
    style IPTABLES fill:#e8f5e9,stroke:#2e7d32
    style MANUAL fill:#e3f2fd,stroke:#1565c0
    style DOCS fill:#fffde7,stroke:#f9a825
    style INIT fill:#f3e5f5,stroke:#6a1b9a
    style CONECTOR fill:#fff9c4,stroke:#f57f17
```

---

## Descripción por nodo

### Canal SSH — Sensor → Servidor

El motor en el sensor `192.168.0.110` aplica acciones remotamente en el servidor `192.168.0.120` vía SSH. La conexión usa claves configuradas y `StrictHostKeyChecking=no` para no bloquearse en prompts interactivos:

```python
def _ssh(cmd):
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5',
         'm4rk@192.168.0.120', cmd],
        capture_output=True, text=True, timeout=8
    )
    return (result.stdout + result.stderr).strip()
```

---

### ipset en el servidor — estado verificado

#### `ppi_blocked` — hash:ip timeout 300

```bash
# Comando de verificación:
sudo ipset list ppi_blocked

# Salida real:
Name: ppi_blocked
Type: hash:ip
Header: family inet hashsize 1024 maxelem 65536 timeout 300 bucketsize 12
References: 2
Number of entries: 0
Members:
```

Cuando una IP es bloqueada:
```bash
sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist
# La IP permanece en el set 300 segundos
# El kernel la elimina automáticamente al expirar
# -exist evita error si ya estaba en el set (idempotente)
```

#### `ppi_limited` — hash:ip timeout 300

```bash
# Salida real:
Name: ppi_limited
Type: hash:ip
Header: family inet hashsize 1024 maxelem 65536 timeout 300 bucketsize 12
References: 1
Number of entries: 0
Members:
```

---

### Reglas iptables — estado verificado en servidor

```bash
# Comando de verificación:
sudo iptables -L INPUT -n --line-numbers | grep ppi

# Salida real:
1    DROP  0  --  0.0.0.0/0  0.0.0.0/0  match-set ppi_blocked src
2    DROP  0  --  0.0.0.0/0  0.0.0.0/0  match-set ppi_limited src limit: above 100/sec burst 150 mode srcip
```

#### Regla 1 — BLOCK (DROP total)
```bash
sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP
```
Cualquier paquete cuyo `src_ip` esté en `ppi_blocked` → **DROP inmediato**, sin procesar.

#### Regla 2 — LIMIT (rate limit hashlimit)
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
IPs en `ppi_limited` pueden enviar hasta **100 paquetes/segundo** con burst de 150. El exceso es descartado. El módulo `hashlimit` mantiene contadores independientes por IP (`--hashlimit-mode srcip`).

---

### Timeout automático de 300 segundos

El timeout es gestionado directamente por el kernel de Linux a través del módulo `ipset`. Garantías:
- Las IPs se desbloquean automáticamente sin que el motor intervenga
- No se acumulan bloqueos permanentes de IPs legítimas mal clasificadas
- El servidor mantiene disponibilidad ante falsos positivos del modelo (FPR=5.1%)
- En validación F6: **ITL=0%** — ningún flow legítimo fue afectado

---

### `scripts/enforce.sh` — Control manual

```bash
# Bloquear IP manualmente (para demo o emergencia)
bash scripts/enforce.sh 192.168.0.100 BLOCK 300

# Limitar IP manualmente
bash scripts/enforce.sh 192.168.0.100 LIMIT 300

# Desbloquear IP
bash scripts/enforce.sh 192.168.0.100 UNBLOCK
```

Salida real:
```
2026-06-04 20:30:00 | BLOCK | 192.168.0.100 | timeout=300s
2026-06-04 20:35:00 | UNBLOCK | 192.168.0.100
```

---

### `inicializar_servidor()` — Arranque idempotente

Al iniciar `ppi-motor.service`, el motor configura automáticamente el servidor si los sets o reglas no existen:

```python
# Crear sets si no existen (|| true = idempotente)
_ssh('sudo ipset create ppi_blocked hash:ip timeout 300 2>/dev/null || true')
_ssh('sudo ipset create ppi_limited hash:ip timeout 300 2>/dev/null || true')

# Insertar regla iptables solo si no existe (-C verifica, -I inserta)
_ssh('sudo iptables -C INPUT -m set --match-set ppi_blocked src -j DROP 2>/dev/null '
     '|| sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP')
```

Log de confirmación al iniciar:
```
2026-06-04 19:42:21 | INFO | Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s) | τ1=-0.4973 τ2=-0.6873
```

---

### Validaciones del control inline realizadas (F5)

| Prueba | Ataque ejecutado | Resultado observado |
|---|---|---|
| BLOCK por modelo | nmap -sS (port scan) | IP bloqueada en < 60s, DROP confirmado |
| BLOCK Brute Force | 25 intentos SSH simultáneos | BLOCK tras 15/60s + Telegram |
| BLOCK HTTP Abuse | curl en bucle continuo | BLOCK tras 100 req/30s + Telegram |
| LIMIT validado | curl en bucle lento (B5) | score=-0.51 → LIMIT → hashlimit activo |
| UNBLOCK automático | Esperar 300s | IP removida automáticamente por kernel |
| IPs broadcast/DHCP | Tráfico 0.0.0.0→255.255.255.255 | Filtradas silenciosamente en motor |

---

### `results/umbrales_finales.txt` — Documento formal

Ubicación real: `/home/m4rk/ppi-surikata-producto/results/umbrales_finales.txt` (1.9 KB)

Registra todos los umbrales del sistema como referencia oficial:

| Umbral | Valor | Criterio |
|---|---|---|
| `clf.offset_` | -0.5481 | contamination=0.05 del modelo |
| τ1 (PERMIT/LIMIT) | -0.4973 | Youden index máximo |
| τ2 (LIMIT/BLOCK) | -0.6873 | FPR ≤ 2% |
| BF SSH LIMIT | 5 intentos/60s | Heurístico temporal |
| BF SSH BLOCK | 15 intentos/60s | Heurístico temporal |
| HTTP LIMIT | 50 requests/30s | Heurístico temporal |
| HTTP BLOCK | 100 requests/30s | Heurístico temporal |
| Timeout bloqueos | 300s | Desbloqueo automático kernel |

---

## Conector → F6

Con el sistema completo funcionando (Suricata → Motor → ipset/iptables), F6 ejecuta 40 corridas controladas midiendo si el control inline opera correctamente: detecta ataques, aplica acciones, no impacta el tráfico legítimo.
