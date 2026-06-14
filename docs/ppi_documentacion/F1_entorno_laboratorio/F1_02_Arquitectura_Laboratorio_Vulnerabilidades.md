# F1-02 — Arquitectura del Laboratorio y Vulnerabilidades del Escenario

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez

---

## 1. Arquitectura Física del Laboratorio

### 1.1 Descripción General

El laboratorio experimental está implementado sobre un hipervisor VMware Workstation, con 6 máquinas virtuales interconectadas en la red privada `192.168.0.0/24`. La topología replica una red corporativa simplificada con los componentes esenciales para validar el sistema de detección: un perímetro controlado (pfSense), un equipo administrativo legítimo, una máquina atacante externa, un sensor IDS, un servidor objetivo y una unidad de almacenamiento.

```
┌─────────────────────────────────────────────────────────────────┐
│              RED DE LABORATORIO — 192.168.0.0/24                │
│                     VMware vSwitch                              │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ pfSense  │   │ Desktop  │   │  Kali    │   │ BigData  │   │
│  │.0.1 GW   │   │  .0.20   │   │  .0.100  │   │  .0.130  │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └──────────┘   │
│       │              │               │                          │
│  ─────┴──────────────┴───────────────┴──────────────────────   │
│                         │                    │                  │
│                  ┌──────┴──────┐    ┌────────┴──────┐         │
│                  │   Suricata  │    │   Ubuntu Srv  │         │
│                  │   Sensor    │    │   Objetivo    │         │
│                  │   .0.110    │    │   .0.120      │         │
│                  │  ens35 ◄────┼────┼── captura     │         │
│                  └─────────────┘    └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Componentes Físicos (Virtualizados)

#### VM-01: pfSense Gateway — `192.168.0.1`
- **Rol:** Gateway perimetral y firewall de laboratorio
- **OS:** pfSense 2.7.x
- **Función en el experimento:** Enrutamiento entre VMs; simula el perímetro de red de una organización
- **Interfaces:** WAN (NAT hacia host) + LAN (192.168.0.1/24)
- **No interviene activamente** en la generación ni captura de tráfico experimental

#### VM-02: Ubuntu Desktop — `192.168.0.20` *(Origen de tráfico normal)*
- **Rol:** Equipo administrador; simula el usuario legítimo de la organización
- **OS:** Ubuntu 22.04 LTS Desktop
- **Función en el experimento:** Ejecuta los scripts A1-A4 (tráfico normal) y coordina escenarios C1-C3 (mixto)
- **Herramientas:** curl, wget, ssh, scp, iperf3
- **Claude Code:** Entorno de desarrollo del proyecto
- **Conectividad SSH:** Claves configuradas hacia Sensor (.110) y Servidor (.120)

#### VM-03: Kali Linux — `192.168.0.100` *(Máquina atacante)*
- **Rol:** Origen de tráfico anómalo controlado; simula un atacante externo
- **OS:** Kali Linux 2024.1
- **Función en el experimento:** Ejecuta los scripts B1-B6 (ataques) y el componente anómalo de C1-C3
- **Herramientas de ataque:**
  - `hping3` — SYN flood, UDP flood, ICMP flood
  - `nmap` — Port scanning
  - `hydra` — Brute force SSH
  - `curl` en bucle — HTTP abuse
- **Aislamiento:** Solo puede comunicarse con .120 (servidor objetivo); el motor la bloquea vía ipset cuando es detectada

#### VM-04: Ubuntu Suricata — `192.168.0.110` *(Sensor IDS — componente central)*
- **Rol:** Sensor de captura de tráfico; ejecuta el motor de detección
- **OS:** Ubuntu Server 22.04 LTS
- **Función en el experimento:** Captura promiscua en `ens35`; genera `eve.json`; ejecuta `motor_decision.py`; aplica acciones BLOCK/LIMIT en el servidor vía SSH
- **Interfaz de captura:** `ens35` en modo promiscuo (captura todo el tráfico LAN)
- **Componentes del sistema:**
  - Suricata 7.0.3 (modo demonio `-i ens35 -D`)
  - Python 3.12 con venv en `/home/m4rk/ppi-sensor/venv/`
  - Proyecto en `/home/m4rk/ppi-surikata-producto/`
  - `ppi-motor.service` (systemd, activo continuamente)

#### VM-05: Ubuntu Server — `192.168.0.120` *(Servidor objetivo)*
- **Rol:** Servidor de servicios; objetivo de los ataques; punto de aplicación del control inline
- **OS:** Ubuntu Server 22.04 LTS
- **Servicios expuestos:**
  - `nginx 1.18` en puerto 80 (HTTP)
  - `openssh-server 8.9` en puerto 22 (SSH)
- **Mecanismos de control inline:**
  - `ipset` con sets `ppi_blocked` (hash:ip, timeout 300s) y `ppi_limited` (hash:ip, timeout 300s)
  - `iptables` reglas: DROP para ppi_blocked; hashlimit 100pkt/s para ppi_limited
- **Contenido web:**
  ```
  /var/www/html/
  ├── index.nginx-debian.html
  ├── info.html
  ├── health.html
  └── files/
      ├── manual.txt
      └── sample.csv
  ```

#### VM-06: Ubuntu BigData — `192.168.0.130` *(Almacenamiento complementario)*
- **Rol:** Almacenamiento de datos del proyecto (complementario)
- **OS:** Ubuntu Server 22.04 LTS
- **Función en el experimento:** No participa activamente en los escenarios de captura

---

### 1.3 Switch Virtual (VMware vSwitch)

VMware Workstation implementa un switch virtual interno que interconecta todas las VMs en la misma VLAN (`192.168.0.0/24`). Características relevantes:

| Parámetro | Valor |
|---|---|
| Tipo | VMware vSwitch (VMnet interno) |
| Modo | Host-only + NAT para salida a Internet |
| VLAN | Sin segmentación de VLAN (flat network) |
| Promiscuous mode | Habilitado para `ens35` del sensor |
| MTU | 1500 bytes (estándar) |
| Velocidad | 1 Gbps virtual |

El modo promiscuo en `ens35` es fundamental: permite que el sensor capture todo el tráfico entre cualquier par de VMs, no solo el dirigido a su propia IP.

---

## 2. Arquitectura Lógica

### 2.1 Flujo del Tráfico de Red

```
FLUJO DE TRÁFICO — Vista lógica
════════════════════════════════════════════════════════════

  [Desktop .20]                    [Servidor .120]
       │  curl, wget, ssh, scp ──────────────────► nginx :80
       │                                           SSH  :22
       │
  [Kali .100]
       │  hping3 ────────────────────────────────► :80 (SYN/UDP/ICMP flood)
       │  nmap ──────────────────────────────────► 1-1024 (port scan)
       │  curl bucle ────────────────────────────► :80 (HTTP abuse)
       │  hydra ─────────────────────────────────► :22 (brute force)
       │
       └─────── TODO EL TRÁFICO PASA POR EL vSWITCH ──────┐
                                                            │
                                                     [Sensor .110]
                                                     ens35 (promiscuo)
                                                     Suricata captura
                                                     AMBOS flujos
```

### 2.2 Flujo de Captura (Sensor → eve.json)

```
FLUJO DE CAPTURA
════════════════════════════════════════════════════════════

  Red LAN 192.168.0.0/24
        │
        ▼ (modo promiscuo)
  [ens35 — Sensor .110]
        │
        ▼
  Suricata 7.0.3
  │  af-packet: interface ens35
  │  outputs:
  │    eve-log:
  │      enabled: yes
  │      filetype: regular
  │      filename: /var/log/suricata/eve.json
  │      types:
  │        - flow    ← el que usa el modelo
  │        - alert
  │        - ssh
  │        - stats
        │
        ▼
  /var/log/suricata/eve.json   (136 MB activo, crece en tiempo real)
  │  Formato: JSON Lines (una línea = un evento)
  │  Ejemplo flow:
  │  {"timestamp":"2026-06-02T04:09:02+0000",
  │   "event_type":"flow",
  │   "src_ip":"192.168.0.100","dest_ip":"192.168.0.120",
  │   "proto":"TCP","dest_port":80,
  │   "flow":{"pkts_toserver":6,"bytes_toserver":492,...}}
```

### 2.3 Flujo de Procesamiento (eve.json → Score)

```
FLUJO DE PROCESAMIENTO
════════════════════════════════════════════════════════════

  /var/log/suricata/eve.json
        │
        ▼ seguir_eve() — tail -f con detección de rotación
  motor_decision.py
        │
        ├─ Filtros de entrada:
        │    event_type == 'flow' ?         NO → descartar
        │    IPv4 ?                         NO → descartar
        │    src_ip ∉ WHITELIST ?           NO → descartar
        │    es_ip_bloqueable() ?           NO → descartar
        │    pkts_toserver > 0 ?            NO → descartar
        │                                   SÍ ↓
        │
        ├─ extract_features(e) → X_raw [1×14]
        │    pkts_toserver, pkts_toclient
        │    bytes_toserver, bytes_toclient
        │    duration, pkt_rate, byte_rate
        │    pkt_ratio, byte_ratio, avg_pkt_size
        │    is_tcp, is_udp, is_icmp, dest_port
        │
        ├─ scaler.transform(X_raw) → X [1×14 normalizado]
        │    media y std del tráfico normal del laboratorio
        │
        └─ clf.score_samples(X) → score (float, negativo)
             Isolation Forest — 300 árboles — n_estimators=300
             Más negativo = más anómalo
```

### 2.4 Flujo de Detección (Score → Acción)

```
FLUJO DE DETECCIÓN
════════════════════════════════════════════════════════════

  score (anomaly score del flow)
        │
        ├─ Detectores temporales (paralelo al score):
        │    detectar_http_abuse()  → dest_port==80, ventana 30s
        │    detectar_brute_force() → dest_port==22, ventana 60s
        │         │
        │         ▼ si supera umbral → override → BLOCK/LIMIT directo
        │
        ├─ decidir(score):
        │    score > τ1 (-0.4973)              → PERMIT
        │    τ2 < score ≤ τ1                   → LIMIT
        │    score ≤ τ2 (-0.6873)              → BLOCK
        │
        └─ explicar_anomalia(X_raw, scaler):
             z = (X_raw - scaler.mean_) / scaler.scale_
             top-3 features por |z-score|
             → "pkt_rate:z=+45.2 | pkts_toserver:z=+38.7 | ..."
```

### 2.5 Flujo de Alertas y Respuesta

```
FLUJO DE ALERTAS Y RESPUESTA
════════════════════════════════════════════════════════════

  Decisión: BLOCK / LIMIT
        │
        ├─ LOG ──────────────────────────────────────────────►
        │    /home/m4rk/ppi-surikata-producto/results/
        │    motor_decision.log (7.6 MB)
        │    Formato: TIMESTAMP | NIVEL | TIPO | src=IP
        │    dst=IP:PUERTO proto=PROTO score=SCORE
        │    razón=[feat:z=val] | ACCION
        │
        ├─ TELEGRAM ─────────────────────────────────────────►
        │    Bot API: api.telegram.org/bot{TOKEN}/sendMessage
        │    Chat ID: 8512353253
        │    Tipos: 🚨 ANOMALÍA | ⚠️ LIMIT | 🔑 BRUTE FORCE
        │           🌐 HTTP ABUSE
        │    Payload: IP + Proto + Score + Razón + Hora
        │
        ├─ CONTROL INLINE ───────────────────────────────────►
        │    SSH: sensor (.110) → servidor (.120)
        │    BLOCK: sudo ipset add ppi_blocked IP timeout 300
        │    LIMIT: sudo ipset add ppi_limited IP timeout 300
        │    iptables: DROP (blocked) | hashlimit 100pkt/s (limited)
        │    Timeout automático: 300s (kernel gestiona expiración)
        │
        └─ DASHBOARD ────────────────────────────────────────►
             scripts/dashboard.py (terminal, actualiza c/3s)
             flows | anomalías | bloqueados | latencia | alertas
```

---

## 3. Inventario del Laboratorio

### 3.1 Sistemas Operativos y Máquinas Virtuales

| VM | IP | OS | Versión | RAM | vCPU | Almacenamiento |
|---|---|---|---|---|---|---|
| pfSense | 192.168.0.1 | pfSense | 2.7.x | 512 MB | 1 | 8 GB |
| Ubuntu Desktop | 192.168.0.20 | Ubuntu Desktop | 22.04.3 LTS | 4 GB | 2 | 40 GB |
| Kali Linux | 192.168.0.100 | Kali Linux | 2024.1 | 2 GB | 2 | 30 GB |
| Ubuntu Suricata | 192.168.0.110 | Ubuntu Server | 22.04.3 LTS | 4 GB | 2 | 50 GB |
| Ubuntu Server | 192.168.0.120 | Ubuntu Server | 22.04.3 LTS | 2 GB | 1 | 20 GB |
| Ubuntu BigData | 192.168.0.130 | Ubuntu Server | 22.04.3 LTS | 2 GB | 1 | 100 GB |

### 3.2 Servicios Desplegados

| VM | Servicio | Versión | Puerto | Propósito en experimento |
|---|---|---|---|---|
| Sensor .110 | Suricata | 7.0.3 RELEASE | — | Captura de tráfico, generación de eve.json |
| Sensor .110 | Python | 3.12.x | — | Ejecución del motor de decisión |
| Sensor .110 | scikit-learn | 1.3.x | — | Isolation Forest, StandardScaler |
| Sensor .110 | systemd | — | — | Gestión del servicio ppi-motor.service |
| Servidor .120 | nginx | 1.18.0 | 80/TCP | Objetivo HTTP; tráfico normal + ataques |
| Servidor .120 | openssh-server | 8.9p1 | 22/TCP | Objetivo SSH; tráfico normal + brute force |
| Servidor .120 | ipset | 7.19 | — | Sets ppi_blocked y ppi_limited |
| Servidor .120 | iptables/netfilter | 1.8.7 | — | DROP y hashlimit de tráfico bloqueado |
| Desktop .20 | curl | 7.81.0 | — | Generación tráfico HTTP normal |
| Desktop .20 | wget | 1.21.2 | — | Generación tráfico HTTP/descarga normal |
| Desktop .20 | openssh-client | 8.9p1 | — | Generación tráfico SSH legítimo |
| Kali .100 | hping3 | 3.0.0-alpha-2 | — | SYN flood, UDP flood, ICMP flood |
| Kali .100 | nmap | 7.94 | — | Port scanning |
| Kali .100 | hydra | 9.4 | — | Brute force SSH |

### 3.3 Herramientas del Pipeline de Análisis

| Herramienta | Versión | Ubicación | Función |
|---|---|---|---|
| Python | 3.12.x | `/home/m4rk/ppi-sensor/venv/` | Runtime del motor |
| scikit-learn | 1.3.x | venv | Isolation Forest, StandardScaler |
| numpy | 1.26.x | venv | Operaciones matriciales |
| pandas | 2.1.x | venv | Procesamiento de CSVs |
| joblib | 1.3.x | venv | Serialización de modelos (.pkl) |
| matplotlib | 3.8.x | venv | Generación de gráficos |
| urllib (stdlib) | Python 3.12 | stdlib | Integración Telegram API |

### 3.4 Artefactos del Proyecto (en sensor .110)

| Artefacto | Ruta | Tamaño | Descripción |
|---|---|---|---|
| isolation_forest.pkl | `models/isolation_forest.pkl` | 2.5 MB | Modelo serializado |
| scaler.pkl | `models/scaler.pkl` | 1.4 KB | StandardScaler serializado |
| features.csv | `models/features.csv` | 152 B | Lista de 14 features |
| dataset_clean.csv | `data/dataset_clean.csv` | 69 MB | 376,827 flows etiquetados |
| train/val/test.csv | `data/*.csv` | 48+11+11 MB | Particiones 70/15/15 |
| data/raw/*.gz | `data/raw/` | 4KB-4.9MB c/u | 38 capturas por escenario |
| motor_decision.log | `results/motor_decision.log` | 7.6 MB | Log de decisiones en producción |
| MVP_funcional.zip | `results/MVP_funcional.zip` | 25 MB | Sistema completo empaquetado |

---

## 4. Clasificación de Vulnerabilidades del Escenario

### 4.1 Respuesta a la Observación del Asesor

> *"¿Cuáles vulnerabilidades pertenecen específicamente al escenario de red?"*

Las vulnerabilidades del escenario se clasifican según dos dimensiones: **capa del modelo OSI** donde operan y **tipo de explotación**. La siguiente clasificación distingue explícitamente entre las que están **dentro del alcance del proyecto** y las que están **fuera del alcance** con justificación técnica.

### 4.2 Taxonomía Completa de Vulnerabilidades

#### 4.2.1 Reconocimiento (Reconnaissance)

| Aspecto | Detalle |
|---|---|
| **Definición** | Fase previa al ataque en la que el atacante recopila información sobre la red objetivo |
| **Capa OSI** | L3/L4 (activo) / L7 (pasivo) |
| **MITRE ATT&CK** | TA0043 — Reconnaissance; T1046 — Network Service Discovery |
| **Manifestación en flujos** | Múltiples flows TCP cortos hacia puertos distintos; bajo bytes_toserver; alta variabilidad en dest_port |
| **Dentro del alcance** | ✅ **SÍ** — Cubierto por escenario B2 (nmap -sS) |
| **Herramienta usada** | nmap 7.94, técnica SYN Scan (-sS) |
| **Detección en el sistema** | AUC=0.9721 · Detección=99.9% · Score medio=-0.651 |

#### 4.2.2 Port Scanning

| Aspecto | Detalle |
|---|---|
| **Definición** | Técnica de reconocimiento activo que enumera puertos abiertos en el objetivo |
| **Capa OSI** | L4 (TCP/UDP) |
| **MITRE ATT&CK** | T1046 — Network Service Scanning |
| **Manifestación en flujos** | Patrón: un flow por cada puerto; pkts_toserver=1; pkts_toclient=0 (puerto cerrado) o =1 (abierto); dest_port varía de 1 a 1024 |
| **Dentro del alcance** | ✅ **SÍ** — Cubierto por escenario B2 |
| **Variantes no cubiertas** | UDP Scan, Xmas Scan, FIN Scan, OS fingerprinting (-O) — trabajo futuro |
| **Detección en el sistema** | Score medio=-0.651 → clasificado como BLOCK vía modelo base |

#### 4.2.3 Fuerza Bruta (Brute Force)

| Aspecto | Detalle |
|---|---|
| **Definición** | Intento sistemático de credenciales contra un servicio de autenticación |
| **Capa OSI** | L7 (Aplicación) |
| **MITRE ATT&CK** | T1110 — Brute Force; T1110.001 — Password Guessing |
| **Manifestación en flujos** | Muchos flows TCP cortos hacia :22; pkts_toserver bajo; alta frecuencia por IP |
| **Dentro del alcance** | ✅ **SÍ** — Cubierto por escenario B6 (hydra sobre SSH) |
| **Limitación conocida** | Modelo base detecta solo 0.9% (flows individuales similares a SSH normal); detector temporal (ventana 60s, umbral 15) eleva a ~90% |
| **Variantes no cubiertas** | Brute force HTTP (formularios), RDP brute force, credential stuffing |

#### 4.2.4 DoS — Denial of Service

| Aspecto | Detalle |
|---|---|
| **Definición** | Ataque que agota recursos del servidor objetivo para impedir el servicio a usuarios legítimos |
| **Capa OSI** | L3/L4 |
| **MITRE ATT&CK** | T1498 — Network Denial of Service |
| **Manifestación en flujos** | Altísimo pkt_rate; pkts_toserver >> pkts_toclient; bytes_toserver elevado; duración corta |
| **Dentro del alcance** | ✅ **SÍ** — Cubierto por B1 (SYN Flood), B3 (UDP Flood), B4 (ICMP Flood) |
| **Variantes no cubiertas** | Slowloris (DoS de aplicación mediante conexiones incompletas), ReDoS, Fork bomb en servicio |

#### 4.2.5 DDoS — Distributed Denial of Service

| Aspecto | Detalle |
|---|---|
| **Definición** | DoS distribuido desde múltiples fuentes, amplificando el volumen de ataque |
| **Capa OSI** | L3/L4/L7 |
| **MITRE ATT&CK** | T1498.001 — Direct Network Flood |
| **Manifestación en flujos** | Mismo patrón que DoS + muchas src_ip distintas (`--rand-source`) |
| **Dentro del alcance** | ✅ **PARCIALMENTE** — B1 y B3 usan `--rand-source` que simula fuentes distribuidas desde una sola VM |
| **Limitación** | Un DDoS real proviene de miles de IPs autónomas (botnet); la simulación usa IPs aleatorias desde una VM. La detección estadística (pkt_rate, asimetría) sigue siendo válida |
| **Variantes no cubiertas** | DNS Amplification, NTP Amplification, SSDP Amplification (requieren servidores de terceros) |

#### 4.2.6 ICMP Abuse

| Aspecto | Detalle |
|---|---|
| **Definición** | Uso abusivo del protocolo ICMP para causar denegación de servicio o exfiltración encubierta |
| **Capa OSI** | L3 |
| **MITRE ATT&CK** | T1498 — Network DoS; T1095 — Non-Application Layer Protocol (tunneling) |
| **Manifestación en flujos** | is_icmp=1; pkt_rate muy alto; avg_pkt_size inusual; duración corta |
| **Dentro del alcance** | ✅ **SÍ (flood)** — Cubierto por B4 (hping3 -1 --flood) |
| **Fuera del alcance** | ICMP tunneling (exfiltración de datos encubierta en payload ICMP) — requiere DPI |

#### 4.2.7 HTTP Abuse

| Aspecto | Detalle |
|---|---|
| **Definición** | Uso abusivo del protocolo HTTP para sobrecargar el servidor web o extraer información |
| **Capa OSI** | L7 |
| **MITRE ATT&CK** | T1498.002 — Reflection Amplification; T1595 — Active Scanning |
| **Manifestación en flujos** | Alto número de flows TCP hacia :80 por IP/ventana; bytes_toserver moderado; alta frecuencia |
| **Dentro del alcance** | ✅ **SÍ** — Cubierto por B5 (curl en bucle); detector temporal 100 req/30s → BLOCK |
| **Variantes no cubiertas** | Slowloris, HTTP/2 Rapid Reset (CVE-2023-44487), Web scraping, SQL Injection |

#### 4.2.8 SSH Abuse

| Aspecto | Detalle |
|---|---|
| **Definición** | Explotación del protocolo SSH para acceso no autorizado o uso abusivo del servicio |
| **Capa OSI** | L7 |
| **MITRE ATT&CK** | T1110 — Brute Force; T1021.004 — Remote Services: SSH |
| **Manifestación en flujos** | Muchos flows cortos hacia :22; variable: bajo bytes en brute force, alto bytes en sesión legítima larga |
| **Dentro del alcance** | ✅ **SÍ (brute force)** — Cubierto por B6 |
| **Fuera del alcance** | SSH tunneling, SSH hijacking, uso de credenciales robadas (post-explotación) |

#### 4.2.9 Exfiltración de Datos

| Aspecto | Detalle |
|---|---|
| **Definición** | Transferencia no autorizada de datos desde la red objetivo hacia el atacante |
| **Capa OSI** | L4/L7 |
| **MITRE ATT&CK** | TA0010 — Exfiltration; T1041 — Exfiltration Over C2 Channel |
| **Manifestación en flujos** | bytes_toclient >> bytes_toserver; duración larga; conexiones hacia IPs externas |
| **Dentro del alcance** | ❌ **NO** |
| **Justificación de exclusión** | La exfiltración requiere acceso previo al sistema (post-explotación). El alcance del proyecto cubre la detección de intrusión en la fase inicial (DDoS, reconocimiento, brute force). La exfiltración es post-brecha y requiere acceso al contenido de los paquetes (DPI) para diferenciarse de una descarga legítima |
| **Trabajo futuro** | Detección de exfiltración basada en volumen: ratio bytes_toclient/bytes_toserver anormalmente alto en sesiones nocturnas |

#### 4.2.10 Movimiento Lateral (Lateral Movement)

| Aspecto | Detalle |
|---|---|
| **Definición** | Movimiento del atacante dentro de la red interna tras comprometer un primer nodo |
| **Capa OSI** | L3/L4/L7 |
| **MITRE ATT&CK** | TA0008 — Lateral Movement; T1021 — Remote Services |
| **Dentro del alcance** | ❌ **NO** |
| **Justificación de exclusión** | El movimiento lateral presupone que el atacante ya ha comprometido un nodo interno. En el laboratorio, el atacante opera desde Kali (.100), que es externa al servidor objetivo (.120). La detección de movimiento lateral requiere correlación de eventos entre múltiples nodos y análisis de comportamiento de usuario (UEBA), fuera del alcance de este PPI |
| **Trabajo futuro** | Extensión del sensor a múltiples nodos internos + correlación temporal de flows entre hosts internos |

---

## 5. Matriz de Vulnerabilidades, Ataques e Impacto

| Vulnerabilidad | Ataque implementado | Herramienta | Impacto en servidor | Severidad (CVSS v3) | Escenario | En alcance | AUC modelo |
|---|---|---|---|---|---|---|---|
| Reconocimiento de red | Port Scan SYN | nmap -sS -p 1-1024 | Exposición de puertos abiertos; información para ataques subsiguientes | **Media** (4.0) | B2 | ✅ | 0.9721 |
| DoS L3 — SYN Flood | TCP SYN Flood con rand-source | hping3 -S -p 80 --rand-source | Agotamiento de tabla de conexiones TCP; denegación de servicio HTTP | **Alta** (7.5) | B1 | ✅ | 0.9529 |
| DoS L4 — UDP Flood | UDP Flood puerto 53 | hping3 --udp -p 53 --rand-source | Saturación de ancho de banda; CPU 100% en stack UDP | **Alta** (7.5) | B3 | ✅ | 0.9905 |
| DoS L3 — ICMP Flood | ICMP Echo Request Flood | hping3 -1 --flood | Saturación de buffer ICMP; degradación de rendimiento | **Media** (5.8) | B4 | ✅ | 0.9861 |
| HTTP Abuse — App Layer | HTTP Request Flood | curl en bucle (0.1s) | Agotamiento de conexiones nginx; degradación de respuesta HTTP | **Alta** (7.5) | B5 | ✅ | 0.8630 |
| Autenticación débil SSH | Brute Force SSH | hydra -P rockyou.txt | Acceso no autorizado al servidor si credencial adivinada | **Crítica** (9.8) | B6 | ✅ | 0.6770* |
| DDoS distribuido (simul.) | SYN + UDP con rand-source | hping3 --rand-source | Combinación de impactos anteriores desde múltiples IPs | **Alta** (7.5) | B1, B3 (C1, C3) | ✅ parcial | — |
| Exfiltración de datos | No implementado | — | Pérdida de confidencialidad de datos | **Crítica** (9.0) | — | ❌ | — |
| Movimiento lateral | No implementado | — | Compromiso de nodos adicionales | **Alta** (8.8) | — | ❌ | — |

> *AUC B6=0.6770 con modelo base. Con detector temporal (ventana 60s, umbral 15 intentos): recall ~90%.*

**Leyenda de Severidad (CVSS v3.1):**
- Crítica: 9.0–10.0 | Alta: 7.0–8.9 | Media: 4.0–6.9 | Baja: 0.1–3.9

---

## 6. Riesgos del Laboratorio

### 6.1 Limitaciones Técnicas

| Limitación | Descripción | Impacto en resultados |
|---|---|---|
| **Red aislada sin tráfico de fondo** | La red del laboratorio no tiene DNS, NTP, DHCP dinámico, actualizaciones de SO ni tráfico de múltiples usuarios | El perfil normal es más limpio que en producción; el FPR real en producción podría ser ligeramente mayor |
| **Un solo servidor objetivo** | Todo el tráfico converge hacia 192.168.0.120:80 y :22 | En redes reales con múltiples servidores, el motor necesitaría gestionar múltiples destinos |
| **Ataques desde una sola VM** | Kali simula DDoS con --rand-source desde una IP real | Un DDoS real proviene de miles de fuentes autónomas; la escala es distinta aunque el patrón estadístico es similar |
| **Procesamiento secuencial** | motor_decision.py procesa flows en un solo hilo (29 flows/s) | En redes de alto volumen (>1 Gbps), el throughput sería insuficiente sin paralelización |
| **eve.json no particionado** | Suricata escribe un único archivo eve.json; al rotar, el motor detecta el truncado pero hay una brecha de ~0.2s | Posibilidad mínima de perder flows en el momento exacto de la rotación |

### 6.2 Riesgos Metodológicos

| Riesgo | Descripción | Probabilidad | Mitigación implementada |
|---|---|---|---|
| **Contaminación del dataset** | Flows anómalos en archivos etiquetados como "normal" | Media | Filtro src_ip + truncado de eve.json por corrida |
| **Sesgo de selección de corridas** | Las corridas 01-02 para entrenamiento podrían no ser representativas | Baja | 4 escenarios A1-A4 cubren los patrones principales; análisis de sensibilidad confirma estabilidad |
| **Overfitting al horario de captura** | Los ataques se capturaron en ventanas horarias específicas | Baja | Los 4 grupos de F6 (40 corridas) se ejecutaron en distintos momentos del día |
| **Métricas autoconfirmatorias** | Evaluar el modelo en datos del mismo lab que generó el entrenamiento | Media | El test set (56,525 flows) se evaluó cronológicamente después del entrenamiento; corridas F6 son independientes temporalmente |
| **Lead Time subóptimo documentado** | El Lead Time medido incluye el artefacto del timeout de Suricata | Alta | Lead Time real medido manualmente: 26s; artefacto documentado en informe F6 |

### 6.3 Riesgos Técnicos

| Riesgo | Descripción | Probabilidad | Mitigación implementada |
|---|---|---|---|
| **Rotación de eve.json** | Suricata o logrotate trunca el archivo; el motor pierde su posición | Baja | `seguir_eve()` detecta truncado por tamaño y reabre el archivo |
| **SSH bloqueado en WHITELIST** | Error de configuración podría añadir Desktop (.20) al ipset bloqueado | Muy baja | WHITELIST hardcodeada incluye .20 y .110; `es_ip_bloqueable()` verifica antes de toda acción |
| **Fallos en la conexión SSH sensor→servidor** | Si SSH falla, las acciones BLOCK/LIMIT no se aplican | Baja | Timeout de 8s en `_ssh()`; el motor sigue procesando flows aunque la acción falle |
| **Telegram sin conectividad** | Si el sensor no tiene salida a Internet, las alertas no llegan | Media | `try/except` en `telegram_alerta()` con `pass`; el motor no se bloquea ante fallos de Telegram |
| **Agotamiento de disco por eve.json** | eve.json crece sin límite durante corridas largas (actualmente 136 MB) | Media | `exportar_eve_por_escenario.sh` trunca el archivo al final de cada corrida |

---

## 7. Mejoras Propuestas a la Arquitectura

### 7.1 Mejora 1: Reducción del Lead Time mediante ajuste del timeout de Suricata

**Problema:** El Lead Time de 26 segundos incluye ~15-20 segundos del timeout de flow de Suricata.

**Propuesta:**
```yaml
# En /etc/suricata/suricata.yaml
flow:
  timeouts:
    tcp:
      established: 10   # reducir de 30s a 10s
      closed: 5
      new: 10
    udp:
      new: 10
      established: 10
    icmp:
      new: 5
```

**Impacto esperado:** Lead Time reducido de ~26s a ~11-16s sin modificar el modelo ni el motor.
**Riesgo:** Flows TCP de larga duración (transferencias legítimas) podrían dividirse en múltiples flows; mitigable con umbral de duración en los features.

---

### 7.2 Mejora 2: Paralelización del motor para alto volumen

**Problema:** Procesamiento secuencial limita el throughput a 29 flows/segundo.

**Propuesta:**
```python
# Arquitectura multiprocess con cola compartida
from multiprocessing import Process, Queue

def reader_process(queue):
    for line in seguir_eve(EVE_PATH):
        queue.put(line)

def worker_process(queue, clf, scaler):
    while True:
        line = queue.get()
        # procesar, decidir, actuar
```

**Impacto esperado:** N workers = N × 29 flows/s. Con 4 cores → ~116 flows/s; suficiente para redes de hasta ~100 Mbps en tráfico promedio.
**Riesgo:** Condiciones de carrera en el ipset (dos workers intentando bloquear la misma IP simultáneamente); mitigable con lock de threading.

---

### 7.3 Mejora 3: Segmentación de VLAN para escenarios más realistas

**Problema:** La red flat (sin VLANs) no replica la segmentación típica de redes corporativas.

**Propuesta:**
```
VLAN 10 — Usuarios (Desktop .20)        → 192.168.10.0/24
VLAN 20 — DMZ (Servidor .120)           → 192.168.20.0/24
VLAN 30 — Gestión (Sensor .110)         → 192.168.30.0/24
VLAN 99 — Simulación ataques (Kali .100) → 192.168.99.0/24
pfSense como router inter-VLAN con ACLs
```

**Impacto esperado:** Escenario más fiel a entornos corporativos reales; permite validar el sistema en presencia de filtros perimetrales; enriquece el dataset con tráfico inter-VLAN.
**Complejidad:** Media — requiere configurar 802.1Q en VMware y pfSense como router VLAN.

---

### 7.4 Mejora 4: Integración con SIEM (Elastic Stack)

**Problema:** El log `motor_decision.log` es un archivo plano; no tiene capacidades de búsqueda, correlación ni visualización avanzada.

**Propuesta:**
```
motor_decision.log
      │
      ▼ Filebeat (agente ligero)
Logstash (parseo de formato estructurado)
      │
      ▼
Elasticsearch (indexación y búsqueda)
      │
      ▼
Kibana (dashboards, alertas, correlación)
```

**Impacto esperado:** Correlación de eventos entre múltiples fuentes (Suricata alerts + motor decisions + system logs); dashboards históricos; retención configurable; alertas por email/Slack adicionales a Telegram.
**Complejidad:** Alta — requiere instalar y configurar ELK Stack (viable en Ubuntu BigData .130 como nodo Elasticsearch).

---

### 7.5 Mejora 5: Reentrenamiento periódico supervisado (Fase 7)

**Problema:** El modelo es estático; si el tráfico normal de la red cambia con el tiempo, el perfil aprendido queda desactualizado y la FPR aumenta.

**Propuesta:**
```python
# Algoritmo de adaptación supervisada (pseudo-código)
def adaptar_umbrales(ventana_dias=7):
    flows_permit_recientes = obtener_flows_permit(ultimos_dias=ventana_dias)
    scores_recientes = clf.score_samples(scaler.transform(flows_permit_recientes))
    
    nueva_media = np.percentile(scores_recientes, 50)  # mediana
    nuevo_tau1  = np.percentile(scores_recientes, 10)  # P10 → nuevo PERMIT/LIMIT
    
    if abs(nuevo_tau1 - TAU1) > UMBRAL_CAMBIO:
        solicitar_aprobacion_humana(nuevo_tau1)  # NO aplicar automáticamente
        # Solo aplicar tras confirmación manual
```

**Impacto esperado:** Modelo adaptativo que mantiene FPR bajo ante cambios graduales en el tráfico normal; previene degradación silenciosa del rendimiento.
**Riesgo principal:** Data poisoning — si el atacante introduce tráfico anómalo lentamente, podría desplazar el umbral. Por esto se requiere aprobación humana antes de aplicar cualquier cambio de umbral.

---

*Documento generado: 14 de junio 2026*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F1_entorno_laboratorio/F1_02_Arquitectura_Laboratorio_Vulnerabilidades.md`*
*Estado: Listo para tesis, sustentación y documentación técnica*
