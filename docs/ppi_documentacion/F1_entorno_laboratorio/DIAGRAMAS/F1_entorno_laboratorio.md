# F1 — Entorno de Laboratorio

**Fecha de cierre:** 10 de mayo 2026
**Objetivo:** Desplegar la red virtualizada, instalar Suricata y validar la captura de tráfico en eve.json.

---

## Diagrama

```mermaid
flowchart TD

    subgraph LAN["Red LAN — 192.168.0.0/24  (VMware)"]
        direction TB

        PF(["pfSense\n192.168.0.1\nGateway / Firewall"])

        subgraph DESKTOP["Ubuntu Desktop — 192.168.0.20"]
            DT["Origen tráfico normal\nClaude Code\nSSH keys → Sensor y Servidor"]
        end

        subgraph KALI["Kali Linux — 192.168.0.100"]
            KL["Origen tráfico anómalo\nhping3 · nmap · hydra"]
        end

        subgraph SENSOR["Ubuntu Suricata — 192.168.0.110  ← SENSOR IDS"]
            direction TB
            SYAML["/etc/suricata/suricata.yaml\naf-packet: ens35\n(captura promiscua LAN)"]
            SPROC["suricata -i ens35 -D\nSuricata 7.0.3 RELEASE"]
            EVE["/var/log/suricata/eve.json\n136 MB · activo en tiempo real\nevent_type: flow | alert | ssh | stats"]
            VAL["scripts/validation/\n├── revisar_suricata.sh\n└── suricata_revision.txt  ← evidencia formal F1"]
            SYAML --> SPROC --> EVE
            EVE -.->|"ejecutar para validar"| VAL
        end

        subgraph SERVIDOR["Ubuntu Server — 192.168.0.120  ← OBJETIVO"]
            direction TB
            NGX["nginx :80  (activo)\n/var/www/html/\n├── index.nginx-debian.html\n├── info.html\n├── health.html\n└── files/\n    ├── manual.txt\n    └── sample.csv"]
            SSHD["openssh-server :22  (activo)"]
        end

        subgraph BIGDATA["Ubuntu BigData — 192.168.0.130"]
            BD["Almacenamiento\n(complementario)"]
        end
    end

    PF --- DESKTOP
    PF --- KALI
    PF --- SENSOR
    PF --- SERVIDOR
    PF --- BIGDATA

    DESKTOP -->|"tráfico legítimo\ncurl · ssh · scp · wget"| SERVIDOR
    KALI -->|"tráfico anómalo\nhping3 · nmap · hydra"| SERVIDOR
    SERVIDOR -->|"respuestas HTTP/SSH"| DESKTOP

    SENSOR -.->|"captura promiscua ens35\ntodo el tráfico LAN"| EVE

    CONECTOR(["→ F2: Captura de Tráfico\neve.json es la entrada\nde todos los escenarios"])
    EVE ==>|"input de corridas A/B/C"| CONECTOR

    style LAN fill:#f0f4ff,stroke:#4a6fa5
    style SENSOR fill:#e8f5e9,stroke:#2e7d32
    style SERVIDOR fill:#fff3e0,stroke:#e65100
    style KALI fill:#fce4ec,stroke:#c62828
    style DESKTOP fill:#e3f2fd,stroke:#1565c0
    style BIGDATA fill:#f3e5f5,stroke:#6a1b9a
    style CONECTOR fill:#fff9c4,stroke:#f57f17
```

---

## Descripción por nodo

### Red LAN — 192.168.0.0/24

Desplegada en VMware con 5 VMs activas y una complementaria:

| VM | IP | OS | Rol en el PPI |
|---|---|---|---|
| pfSense | 192.168.0.1 | pfSense | Gateway y firewall de laboratorio |
| Ubuntu Desktop | 192.168.0.20 | Ubuntu 22.04 Desktop | Origen tráfico normal · Claude Code |
| Kali Linux | 192.168.0.100 | Kali Linux 2024 | Origen tráfico anómalo controlado |
| Ubuntu Suricata | **192.168.0.110** | Ubuntu Server 22.04 | **Sensor IDS** (Suricata 7.0.3) |
| Ubuntu Server | **192.168.0.120** | Ubuntu Server 22.04 | **Objetivo**: nginx :80, SSH :22 |
| Ubuntu BigData | 192.168.0.130 | Ubuntu Server 22.04 | Almacenamiento complementario |

---

### Sensor — 192.168.0.110

#### `/etc/suricata/suricata.yaml`
Configuración principal de Suricata. Sección relevante:
```yaml
af-packet:
  - interface: ens35    # captura promiscua de la LAN 192.168.0.0/24
```

#### `suricata -i ens35 -D`
Proceso corriendo como demonio. Interfaz `ens35` monitorea todo el tráfico entre VMs.

#### `/var/log/suricata/eve.json` ← **output clave de F1**
Archivo JSON-lines generado en tiempo real. Cada línea es un evento. Los eventos relevantes para el PPI:

| event_type | Descripción |
|---|---|
| `flow` | Resumen de flujo TCP/UDP/ICMP al cierre — **input del modelo** |
| `alert` | Alerta de regla Suricata |
| `ssh` | Metadata de sesiones SSH |
| `stats` | Estadísticas del sensor |

Ejemplo de evento flow capturado (real):
```json
{
  "timestamp": "2026-06-02T04:09:02+0000",
  "flow_id": 188776050051964,
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "src_port": 42112,
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 6,  "pkts_toclient": 4,
    "bytes_toserver": 492, "bytes_toclient": 555,
    "start": "2026-06-02T04:09:02+0000",
    "end":   "2026-06-02T04:09:02+0000"
  }
}
```

#### `scripts/validation/revisar_suricata.sh`
Script de validación ejecutado el 10/05/2026. Verifica: servicio activo, versión, interfaz, eve.json con flows y stats.

#### `scripts/validation/suricata_revision.txt` ← **evidencia formal F1**
Salida del script de validación. Confirma: Suricata 7.0.3 · ens35 · eve.json con eventos flow ✅

---

### Servidor — 192.168.0.120

#### nginx :80 — `/var/www/html/`
Superficie de tráfico HTTP normal (escenarios A1, A3, A4) y de abuso (B5, C1, C3):
```
/var/www/html/
├── index.nginx-debian.html   (responde HTTP 200)
├── info.html
├── health.html
└── files/
    ├── manual.txt
    └── sample.csv
```
Estado actual: `systemctl is-active nginx → active`

#### openssh-server :22
Servicio SSH activo. Usado para:
- Tráfico legítimo: escenarios A2, A4, C2 (Desktop → Servidor)
- Objetivo de brute force: escenario B6 (Kali → Servidor con hydra)

---

## Conector → F2

El `eve.json` generado en F1 es la **entrada de todos los escenarios de F2**. Al finalizar cada corrida de captura, el script `exportar_eve_por_escenario.sh` comprime el estado actual de `/var/log/suricata/eve.json` y lo guarda en `data/raw/` con nombre trazable.

```
/var/log/suricata/eve.json  →  data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz
```
