# F1 — Diagrama: Entorno de Laboratorio

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F1 — Preparación del Entorno de Laboratorio  
**Estado:** ✅ Completado — 15 de junio 2026  

---

## Diagrama 1 — Topología de Red y Flujo de Captura

```mermaid
flowchart TD

    %% ── NTP ────────────────────────────────────────────────────
    NTP(["🕐 NTP — pool.ntp.org\nAmerica/Lima UTC−5\nSincronización < 7s entre VMs"])

    %% ── GATEWAY ────────────────────────────────────────────────
    GW(["🔒 pfSense\n192.168.0.1\nGateway / Firewall\nDHCP · NAT"])

    %% ── DESKTOP ────────────────────────────────────────────────
    subgraph DESKTOP["🖥️  Ubuntu Desktop — 192.168.0.20  |  Administrador"]
        direction TB
        DT_ROL["Rol: Origen tráfico normal\nClaude Code — orquestación PPI"]
        DT_TOOLS["Herramientas:\ncurl · wget · ssh · scp"]
        DT_KEYS["🔑 SSH keys configuradas:\n→ m4rk@192.168.0.110  (Sensor)\n→ m4rk@192.168.0.120  (Servidor)"]
        DT_SCRIPTS["Scripts de escenario:\nscripts/escenarios/A1_http_normal.sh\nscripts/escenarios/A2_ssh_legitimo.sh\nscripts/escenarios/A3_transferencia.sh\nscripts/escenarios/A4_trafico_sostenido.sh"]
        DT_ROL --> DT_TOOLS
        DT_TOOLS --> DT_KEYS
    end

    %% ── KALI ────────────────────────────────────────────────────
    subgraph KALI["💀  Kali Linux — 192.168.0.100  |  Atacante"]
        direction TB
        KL_ROL["Rol: Origen tráfico anómalo controlado"]
        KL_TOOLS["Herramientas:\nhping3 · nmap · hydra · curl"]
        KL_SCRIPTS["Scripts de escenario:\nscripts/escenarios/B1_syn_flood.sh\nscripts/escenarios/B2_port_scan.sh\nscripts/escenarios/B3_udp_flood.sh\nscripts/escenarios/B4_icmp_flood.sh\nscripts/escenarios/B5_acceso_repetitivo.sh\nscripts/escenarios/B6_bruteforce.sh"]
        KL_ROL --> KL_TOOLS
    end

    %% ── SERVIDOR ────────────────────────────────────────────────
    subgraph SERVIDOR["🌐  Ubuntu Server — 192.168.0.120  |  Objetivo"]
        direction TB
        SRV_NGX["nginx :80  ✅\n/var/www/html/\n├── index.html\n├── info.html\n├── health.html\n└── files/ (manual.txt · sample.csv)"]
        SRV_SSH["openssh-server :22  ✅\nAcceso legítimo: Desktop → Servidor\nObjetivo brute-force: Kali → Servidor"]
        SRV_IPSET["ipset: ppi_blocked · ppi_limited\niptables: FORWARD chain\n(control inline — F5)"]
        SRV_NGX --- SRV_SSH
    end

    %% ── SENSOR ────────────────────────────────────────────────
    subgraph SENSOR["🔍  Ubuntu Suricata — 192.168.0.110  |  Sensor IDS"]
        direction TB

        subgraph IFACES["Interfaces de red"]
            ENS33["ens33 — 192.168.0.110\nGestión SSH / administración"]
            ENS35["ens35 — sin IP asignada\nCaptura promiscua de LAN"]
        end

        subgraph SURICATA_CFG["Configuración Suricata 7.0.3"]
            YAML["/etc/suricata/suricata.yaml\naf-packet:\n  - interface: ens35\n    threads: auto\n    cluster-type: cluster_flow\noutputs:\n  - eve-log:\n      enabled: yes\n      filename: eve.json"]
            PROC["suricata -i ens35 -D\nPID activo como demonio"]
            YAML --> PROC
        end

        EVE["/var/log/suricata/eve.json\n📄 JSON-lines · actualización en tiempo real\nevent_type: flow | alert | ssh | stats\nFlujos cerrados: TCP SYN_SENT=30s\n             TCP established: RST\n             UDP/ICMP: timeout rápido"]

        subgraph VAL_SCRIPTS["Scripts de validación F1"]
            VAL_SH["scripts/validation/revisar_suricata.sh\nVerifica: servicio activo · versión\ninterfaz ens35 · eve.json con flows"]
            VAL_OUT["scripts/validation/suricata_revision.txt\n← Evidencia formal F1\nSuricata 7.0.3 ✅ · ens35 ✅\neve.json con flows ✅"]
            VAL_SH --> VAL_OUT
        end

        PROC -->|"escribe evento flow\ncada vez que cierra\nun flujo de red"| EVE
        EVE -.->|"ejecutar para validar"| VAL_SH
    end

    %% ── NTP SYNC ────────────────────────────────────────────────
    NTP -.->|"systemd-timesyncd\nAmerica/Lima"| DESKTOP
    NTP -.->|"systemd-timesyncd\nAmerica/Lima"| SENSOR
    NTP -.->|"systemd-timesyncd\nAmerica/Lima"| SERVIDOR
    NTP -.->|"systemd-timesyncd\nAmerica/Lima"| KALI

    %% ── GATEWAY ─────────────────────────────────────────────────
    GW --- DESKTOP
    GW --- KALI
    GW --- SENSOR
    GW --- SERVIDOR

    %% ── TRÁFICO ─────────────────────────────────────────────────
    DESKTOP -->|"A1: curl/wget → :80\nA2: ssh → :22\nA3: scp/wget archivos\nA4: curl+ssh mixto"| SERVIDOR
    KALI -->|"B1: hping3 -S --flood → :80\nB2: nmap -sS 1000 puertos\nB3: hping3 --udp → :53\nB4: hping3 -1 --flood\nB5: curl bucle → :80\nB6: hydra → :22"| SERVIDOR
    SERVIDOR -->|"respuestas HTTP 200\nSSH handshakes"| DESKTOP

    %% ── CAPTURA ─────────────────────────────────────────────────
    ENS35 -.->|"captura COPIA del\ntráfico LAN en modo\npromiscuo — sin\nbloquear flujos"| PROC

    %% ── CONECTOR F2 ──────────────────────────────────────────────
    F2_CONN(["→ F2: Captura y Procesamiento\neve.json es la entrada de todas\nlas corridas A · B · C\nexportar_eve_por_escenario.sh\ncomprime y rota al final de cada corrida"])
    EVE ==>|"input crudo de\ntodos los escenarios"| F2_CONN

    %% ── ESTILOS ─────────────────────────────────────────────────
    style SENSOR    fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style SERVIDOR  fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style KALI      fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style DESKTOP   fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style IFACES    fill:#f1f8e9,stroke:#558b2f
    style SURICATA_CFG fill:#e0f2f1,stroke:#00796b
    style VAL_SCRIPTS  fill:#f3e5f5,stroke:#6a1b9a
    style NTP       fill:#fff9c4,stroke:#f57f17
    style GW        fill:#eceff1,stroke:#455a64
    style F2_CONN   fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style EVE       fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
```

---

## Diagrama 2 — Flujo de Scripts y Archivos F1

```mermaid
flowchart LR

    subgraph DESKTOP_D["Desktop 192.168.0.20"]
        direction TB
        SSH_GEN["ssh-keygen -t ed25519\nGenera par de claves"]
        SSH_COPY1["ssh-copy-id m4rk@192.168.0.110\nAutoriza acceso a Sensor"]
        SSH_COPY2["ssh-copy-id m4rk@192.168.0.120\nAutoriza acceso a Servidor"]
        SSH_GEN --> SSH_COPY1
        SSH_GEN --> SSH_COPY2
    end

    subgraph SENSOR_D["Sensor 192.168.0.110"]
        direction TB
        AUTH_K1["~/.ssh/authorized_keys\n← clave pública Desktop"]
        NTP_S["timedatectl set-timezone\nAmerica/Lima\nNTP: activo · offset < 7s"]
        REVISAR["scripts/validation/\nrevisar_suricata.sh"]
        REVISION_TXT["suricata_revision.txt\n← evidencia F1"]
        AUTH_K1 --> NTP_S
        REVISAR --> REVISION_TXT
    end

    subgraph SERVIDOR_D["Servidor 192.168.0.120"]
        direction TB
        AUTH_K2["~/.ssh/authorized_keys\n← clave pública Desktop"]
        NTP_SRV["timedatectl set-timezone\nAmerica/Lima\nNTP: activo"]
        NGX_SRV["nginx :80  activo\nssh :22  activo"]
        AUTH_K2 --> NTP_SRV
    end

    SSH_COPY1 -->|"clave pública\npor SSH"| AUTH_K1
    SSH_COPY2 -->|"clave pública\npor SSH"| AUTH_K2

    SENSOR_D -->|"ssh sin contraseña\ndesde Desktop"| DESKTOP_D
    SERVIDOR_D -->|"ssh sin contraseña\ndesde Desktop"| DESKTOP_D

    REVISION_TXT ==>|"evidencia formal\nF1 completado"| DONE(["✅ F1 VALIDADO\nSuricata 7.0.3\nens35 capturando\neve.json activo\nNTP sincronizado"])

    style DESKTOP_D  fill:#e3f2fd,stroke:#1565c0
    style SENSOR_D   fill:#e8f5e9,stroke:#2e7d32
    style SERVIDOR_D fill:#fff3e0,stroke:#e65100
    style DONE       fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
```

---

## Diagrama 3 — Flujo de Captura Suricata en Detalle

```mermaid
sequenceDiagram
    participant D  as Desktop 192.168.0.20
    participant K  as Kali 192.168.0.100
    participant SV as Servidor 192.168.0.120
    participant E  as ens35 (promiscua)
    participant S  as Suricata 7.0.3
    participant J  as eve.json

    note over D,SV: Escenario A1 — HTTP Normal (ejemplo)
    D->>SV: GET /index.html HTTP/1.1 (TCP :80)
    SV-->>D: HTTP 200 OK (response)

    E->>S: copia del paquete (mirror)
    E->>S: copia de respuesta (mirror)

    note over S: acumula paquetes del flow\nhasta cierre de conexión

    S->>J: flow event (al cerrar TCP)
    note over J: {"event_type":"flow",\n"src_ip":"192.168.0.20",\n"dest_ip":"192.168.0.120",\n"dest_port":80,\n"pkts_toserver":6,\n"bytes_toserver":492,...}

    note over D,SV: Escenario B1 — SYN Flood (ejemplo)
    K->>SV: hping3 -S --flood (miles de SYN)
    SV-->>K: RST / timeout

    E->>S: copia de SYN flood
    S->>J: flow events masivos (src_ip=192.168.0.100)
    note over J: pkt_rate muy alto\nbytes_toserver bajo\npkts_toclient ≈ 0

    note over J: eve.json → F2 (parser.py extrae flows)
```

---

## Descripción de nodos clave

### Sensor — 192.168.0.110

| Componente | Detalle |
|---|---|
| `ens33` | Interfaz de gestión con IP 192.168.0.110 — SSH de administración |
| `ens35` | Interfaz de captura sin IP — modo promiscuo — espeja todo el tráfico LAN |
| `/etc/suricata/suricata.yaml` | Configura af-packet en ens35, outputs eve-log en /var/log/suricata/ |
| `suricata -i ens35 -D` | Proceso demonio activo — escribe flow events al cerrar cada conexión |
| `/var/log/suricata/eve.json` | Output principal — JSON-lines — entrada de todos los scripts de F2 |
| `scripts/validation/revisar_suricata.sh` | Verifica: `systemctl is-active`, versión, interfaz, eventos en eve.json |
| `scripts/validation/suricata_revision.txt` | Evidencia formal de F1 — confirma entorno listo |

### Timeouts de flow en Suricata (relevantes para el modelo)

| Protocolo | Estado | Timeout | Impacto en detección |
|---|---|---|---|
| TCP | SYN_SENT (sin respuesta) | 30 s | SYN Flood → flow cerrado rápido |
| TCP | RST / FIN | Inmediato | Conexiones normales → flow exacto |
| TCP | Established | 600 s | SSH sessions largas |
| UDP | — | 30 s | UDP Flood → flows rápidos |
| ICMP | — | 30 s | ICMP Flood → flows rápidos |

### NTP — Sincronización América/Lima

```
Servidor NTP: pool.ntp.org
Zona horaria: America/Lima (UTC − 5, sin DST)
Aplicado en: Desktop · Sensor · Servidor · Kali
Offset entre VMs: < 7 segundos
Impacto: timestamps en eve.json y motor_decision.log coherentes
```

---

## Conector → F2

```
eve.json (F1 output)
    │
    ▼  scripts/capture/exportar_eve_por_escenario.sh
    │  (ejecutado desde Desktop vía SSH al Sensor al final de cada corrida)
    │
    ▼
data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz
    │
    ▼  F2: parser.py → etiquetar_limpiar.py → particionar_estadisticos.py
```

**F1 entrega:** entorno de red funcional con Suricata capturando en ens35 y generando eve.json verificado.  
**F1 no hace:** procesamiento de datos, entrenamiento, ni bloqueo de IPs — eso es F2–F5.
