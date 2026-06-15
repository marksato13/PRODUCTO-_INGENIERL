# F4 — Diagrama: Motor de Decisión

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F4 — Motor de Decisión (+ F5 Control Inline integrado)  
**Script:** `scripts/motor_decision.py` — 547 líneas  
**Servicio:** `ppi-motor.service` (systemd en sensor 192.168.0.110)  
**Estado:** ✅ En producción — Latencia P95=34.8ms · Telegram activo  

---

## Diagrama 1 — Arquitectura Completa del Motor de Decisión

```mermaid
flowchart TD

    %% ── INICIO / CARGA ──────────────────────────────────────────
    subgraph BOOT["🚀 Inicio — load_model() + inicializar_servidor()"]
        direction LR
        SVC["ppi-motor.service\n(systemd)\nRequires=suricata.service\nRestart=on-failure\nWorkingDir=/home/m4rk/ppi-surikata-producto"]
        LM["load_model()\njoblib.load(models/isolation_forest.pkl) → clf\njoblib.load(models/scaler.pkl) → scaler\nlog: 'Modelo cargado | τ1=−0.4973 | τ2=−0.6873'"]
        IS["inicializar_servidor()\nSSH → 192.168.0.120\n① ipset create ppi_blocked hash:ip timeout 300\n② iptables -I INPUT -m set ppi_blocked -j DROP\n③ ipset create ppi_limited hash:ip timeout 300\n④ iptables -I INPUT 2 ppi_limited hashlimit 100/s -j DROP"]
        TG_TH["threading.Thread(target=_tg_worker, daemon=True)\nCola asyncrónica Telegram (maxsize=100)\nEvita bloquear el loop principal"]
        SVC --> LM --> IS --> TG_TH
    end

    %% ── LECTURA EVE ─────────────────────────────────────────────
    subgraph EVE_READ["📄 seguir_eve() — tail -f con detección de rotación"]
        direction TB
        EVE_FILE["/var/log/suricata/eve.json\nAbierto en modo 'r'\nf.seek(0, 2) → posición al final\nPoll cada 0.2s"]
        EVE_ROT["Detección de rotación:\nif os.path.getsize(path) < f.tell():\n  f.close(); f = open(path); f.seek(0,2)\n  log.info('eve.json rotado — reabriendo')"]
        EVE_FILE --> EVE_ROT
    end

    %% ── FILTROS ─────────────────────────────────────────────────
    subgraph FILTERS["🔽 Filtros de entrada (orden exacto del código)"]
        direction TB
        F1["① event_type == 'flow'\n   descarta: alert · ssh · stats · dns"]
        F2["② ':' not in src_ip\n   descarta: IPv6 (no compatible con ipset hash:ip)"]
        F3["③ src_ip ∉ WHITELIST\n   {192.168.0.1 · .20 · .110 · .120 · 127.0.0.1 · .130 · .140}\n   evita auto-bloqueo de infraestructura"]
        F4["④ es_ip_bloqueable(src_ip)\n   descarta: 0.0.0.0 · 255.255.255.255 · *.255\n             multicast · reserved\n   evita 'Null-valued element' en ipset"]
        F5["⑤ pkts_toserver > 0\n   descarta flows vacíos (sin datos al servidor)"]
        PASA["✅ Flow pasa todos los filtros\ntotal_flows += 1"]
        DESCARTA["❌ Descartado — sin acción"]
        F1 --> F2 --> F3 --> F4 --> F5 --> PASA
        F1 & F2 & F3 & F4 & F5 -->|"falla"| DESCARTA
    end

    %% ── PIPELINE CLASIFICACIÓN ───────────────────────────────────
    subgraph PIPELINE["⚙️ Pipeline de Clasificación (por cada flow válido)"]
        direction TB
        FEAT["extract_features(e)\n→ numpy array (1×14)\n[pkts_to, pkts_from, bytes_to, bytes_from,\n duration, pkt_rate, byte_rate,\n pkt_ratio, byte_ratio, avg_pkt_size,\n is_tcp, is_udp, is_icmp, dest_port]"]
        SCALE["scaler.transform(X_raw)\n→ X_scaled (1×14)\n(X_raw − μ_normal) / σ_normal\nAnómalos → z-scores extremos"]
        SCORE["clf.score_samples(X_scaled)[0]\n→ score ∈ (−1, 0)\nmás negativo = más anómalo\nLatencia: media=34.5ms · P95=34.8ms"]
        FEAT --> SCALE --> SCORE
    end

    %% ── GRADO ───────────────────────────────────────────────────
    subgraph GRADO["🏷️ clasificar_grado(score)"]
        direction LR
        G1["score > −0.4973   → NORMAL"]
        G2["score > −0.6873   → BAJA"]
        G3["score > −0.82     → ALTA"]
        G4["score ≤ −0.82     → CRITICA"]
    end

    %% ── DETECTORES HEURÍSTICOS ───────────────────────────────────
    subgraph DETECT["🔍 Detectores Temporales (parallel al IF)"]
        direction TB

        subgraph BF["detectar_brute_force(ip, dest_port, ts, ssh_intentos)"]
            BF1["if dest_port != 22: return None"]
            BF2["ssh_intentos[ip].append(ts_flow)\npurgar ts fuera de ventana 60s"]
            BF3["n = len(ssh_intentos[ip])\nn ≥ 15 → ('BLOCK', n)\nn ≥ 5  → ('LIMIT',  n)\nresto  → None"]
            BF1 --> BF2 --> BF3
        end

        subgraph HTTP["detectar_http_abuse(ip, dest_port, ts, http_requests)"]
            H1["if dest_port != 80: return None"]
            H2["http_requests[ip].append(ts_flow)\npurgar ts fuera de ventana 30s"]
            H3["n = len(http_requests[ip])\nn ≥ 100 → ('BLOCK', n)\nn ≥ 50  → ('LIMIT',  n)\nresto   → None"]
            H1 --> H2 --> H3
        end
    end

    %% ── EXPLICABILIDAD ───────────────────────────────────────────
    subgraph EXPLAIN["🔬 explicar_anomalia() — solo en LIMIT y BLOCK"]
        direction LR
        EX1["z = (X_raw[0] − scaler.mean_) / scaler.scale_\nCalcula z-score por feature"]
        EX2["Top-3 por |z|\nEjemplos:\nSYN Flood:  pkt_rate:z=+45.2 | pkts_toserver:z=+38.7\nPort Scan:  dest_port:z=+8.3  | pkt_ratio:z=+6.1\nICMP Flood: is_icmp:z=+4.1   | pkt_rate:z=+61.4"]
        EX1 --> EX2
    end

    %% ── DECISIÓN ────────────────────────────────────────────────
    subgraph DECISION["🎯 Lógica de Decisión — decidir(score) + detectores"]
        direction TB
        DET_CHECK{"¿Detector heurístico\nactivó BLOCK o LIMIT?"}
        DET_OVERRIDE["Override por heurística\n(independiente del score IF)"]
        IF_CHECK{"score > τ1\n= −0.4973?"}
        LIM_CHECK{"score > τ2\n= −0.6873?"}
        PERMIT["PERMIT\nlog.debug() — invisible en prod\n(no loguea en WARNING)"]
        LIMIT_ACT["LIMIT\nlog.warning('SOSPECHOSO|...')\n+ razón z-score\n+ Telegram ⚠️"]
        BLOCK_ACT["BLOCK\nlog.warning('ANOMALÍA|...')\n+ razón z-score\n+ Telegram 🚨"]

        DET_CHECK -->|"sí"| DET_OVERRIDE
        DET_CHECK -->|"no"| IF_CHECK
        IF_CHECK -->|"sí"| PERMIT
        IF_CHECK -->|"no"| LIM_CHECK
        LIM_CHECK -->|"sí"| LIMIT_ACT
        LIM_CHECK -->|"no"| BLOCK_ACT
        DET_OVERRIDE --> LIMIT_ACT & BLOCK_ACT
    end

    %% ── ACCIONES ────────────────────────────────────────────────
    subgraph ENFORCE["⚡ Control Inline — SSH al Servidor 192.168.0.120"]
        direction LR
        BLK_ACT["bloquear_ip(src_ip)\nssh m4rk@192.168.0.120\n'sudo ipset add ppi_blocked IP timeout 300 -exist'\n→ DROP total en INPUT chain"]
        LIM_ACT["limitar_ip(src_ip)\nssh m4rk@192.168.0.120\n'sudo ipset add ppi_limited IP timeout 300 -exist'\n→ hashlimit: DROP si > 100 pkt/s"]
        YA_BLK["src_ip ∈ bloqueados (Python set)\n→ 'ya bloqueado' — sin acción duplicada"]
        YA_LIM["src_ip ∈ limitados (Python set)\n→ 'ya limitado' — sin acción duplicada"]
    end

    %% ── SALIDAS ─────────────────────────────────────────────────
    subgraph OUTPUTS["📤 Salidas del Motor"]
        direction TB
        LOG_FILE["results/motor_decision.log  7.6 MB\nFormato WARNING:\n2026-06-14 18:13:13 | WARNING | SOSPECHOSO |\nsrc=192.168.0.100 dst=192.168.0.120:80\nproto=TCP score=-0.5317 | LIMIT\n\nFormato heurística:\n2026-06-14 18:13:21 | WARNING | HTTP-ABUSE |\nsrc=192.168.0.100 dst=192.168.0.120:80\nrequests=100/30s | BLOCK → BLOCKED 192.168.0.100"]
        TG_OUT["📱 Telegram Bot\nTG_TOKEN=8677152686:...\nTG_CHAT_ID=8512353253\n\n🚨 BLOCK:\nAccion: BLOCK · IP: .100\nScore: −0.7214\nRazon: pkt_rate:z=+45.2 | ...\n\n⚠️ LIMIT:\nAccion: LIMIT · IP: .100\nScore: −0.5317\n\n🔑 BRUTE-FORCE SSH (n=15/60s)\n🌐 HTTP-ABUSE (n=100/30s)"]
        STATS["📊 Estadísticas cada 500 flows\ntotal_flows · total_anom\ntotal_bf · total_http_ab\nbloqueados · limitados\nlatencia_media · latencia_p95"]
        DASH["🖥️ scripts/dashboard.py\nLee motor_decision.log\nActualiza cada 3s\nResumen: flows · alertas\nbloqueados · latencia"]
    end

    %% ── FLUJO PRINCIPAL ──────────────────────────────────────────
    BOOT --> EVE_READ
    EVE_READ --> FILTERS
    FILTERS --> PIPELINE
    PIPELINE --> GRADO
    PIPELINE --> DETECT
    PIPELINE --> EXPLAIN
    SCORE --> DECISION
    DETECT --> DECISION
    EXPLAIN --> DECISION
    DECISION --> ENFORCE
    DECISION --> OUTPUTS
    BLOCK_ACT --> BLK_ACT
    LIMIT_ACT --> LIM_ACT

    %% ── CONECTOR F5 ──────────────────────────────────────────────
    F5_CONN(["→ F5: Control Inline en Servidor 192.168.0.120\nppi_blocked: DROP total · timeout 300s\nppi_limited: hashlimit 100pkt/s · timeout 300s\nenforce.sh: control manual BLOCK|LIMIT|UNBLOCK"])
    ENFORCE ==>|"SSH ipset add"| F5_CONN

    %% ── ESTILOS ──────────────────────────────────────────────────
    style BOOT      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EVE_READ  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style FILTERS   fill:#fafafa,stroke:#757575,stroke-width:2px
    style PIPELINE  fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    style GRADO     fill:#f3e5f5,stroke:#6a1b9a
    style DETECT    fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style EXPLAIN   fill:#e1f5fe,stroke:#0277bd
    style DECISION  fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style ENFORCE   fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
    style OUTPUTS   fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style F5_CONN   fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Diagrama 2 — Flujo de un Flow Individual (Traza Completa)

```mermaid
sequenceDiagram
    participant SU  as Suricata 7.0.3
    participant EV  as eve.json
    participant MT  as motor_decision.py
    participant IF  as Isolation Forest
    participant SRV as Servidor :120 (ipset)
    participant TG  as Telegram Bot
    participant LOG as motor_decision.log

    note over SU,LOG: Ejemplo: SYN Flood desde 192.168.0.100

    SU->>EV: flow event (proto=TCP, pkt_rate=92k, pkts_toclient=0)
    MT->>EV: readline() — poll cada 0.2s
    EV-->>MT: línea JSON

    MT->>MT: ① event_type == 'flow' ✓
    MT->>MT: ② ':' not in '192.168.0.100' ✓
    MT->>MT: ③ '192.168.0.100' ∉ WHITELIST ✓
    MT->>MT: ④ es_ip_bloqueable('192.168.0.100') ✓
    MT->>MT: ⑤ pkts_toserver=7432 > 0 ✓

    MT->>MT: extract_features(e) → [7432, 0, 312144, 0, 0.08, 92900, ...]
    MT->>IF: scaler.transform(X) → X_scaled
    IF-->>MT: score_samples(X_scaled) → −0.7214

    MT->>MT: clasificar_grado(−0.7214) → ALTA
    MT->>MT: detectar_brute_force(ip, 80, ts, ...) → None (puerto 80, no 22)
    MT->>MT: detectar_http_abuse(ip, 80, ts, ...) → None (< 50 req/30s)
    MT->>MT: explicar_anomalia() → "pkt_rate:z=+45.2 | pkts_toserver:z=+38.7"

    MT->>MT: decidir(−0.7214): score ≤ τ2=−0.6873 → BLOCK

    MT->>SRV: ssh "sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist"
    SRV-->>MT: "BLOCKED 192.168.0.100"

    MT->>LOG: WARNING | ANOMALÍA | src=192.168.0.100 ... score=-0.7214 | BLOCK → BLOCKED
    MT->>TG: _tg_queue.put_nowait("🚨 PPI ALERTA — ANOMALÍA\n...")
    TG-->>MT: HTTP 200 OK (async, no bloquea)

    note over SRV: iptables: paquetes de 192.168.0.100 → DROP (timeout 300s)
```

---

## Diagrama 3 — Sistema de Clasificación: Score → Grado → Tipo → Acción

```mermaid
flowchart LR

    SCORE_IN["score\nIF anomaly score\n∈ (−1, 0)"]

    subgraph GRADOS["clasificar_grado(score)"]
        direction TB
        GN["NORMAL\nscore > −0.4973\nTráfico legítimo"]
        GB["BAJA\n−0.6873 < score ≤ −0.4973\nAnomalia leve"]
        GA["ALTA\n−0.82 < score ≤ −0.6873\nAnomalia moderada"]
        GC["CRITICA\nscore ≤ −0.82\nAnomalia severa"]
    end

    subgraph TIPOS["clasificar_tipo(e, score, decision, ...)"]
        direction TB
        TN["NORMAL"]
        TBF["BRUTE_FORCE_SSH\n→ dest_port==22\n+ ssh_intentos ≥ 5"]
        THA["HTTP_ABUSE\n→ dest_port==80\n+ http_req ≥ 50"]
        TBA["BAJA_ANOMALIA\n→ decision==LIMIT\nno BF ni HTTP"]
        TIF["ICMP_FLOOD\n→ is_icmp + pkt_rate > 300"]
        TUF["UDP_FLOOD\n→ is_udp + pkt_rate > 500"]
        TSF["SYN_FLOOD\n→ is_tcp + pkt_rate > 2000\n+ dur < 2s + bytes_from < 100"]
        THA2["HTTP_ABUSE (heurística)\n→ dest_port==80 + pkt_rate > 200"]
        TBS2["BRUTE_FORCE_SSH (heurística)\n→ dest_port==22"]
        TAG["ANOMALIA_GENERICA\n(ninguna regla anterior)"]
    end

    subgraph ACCIONES["Acción resultante"]
        direction TB
        AP["PERMIT\nPermite paso\nlog.debug() (invisible)"]
        AL["LIMIT\nipset ppi_limited\nhashlimit 100pkt/s\nTelegram ⚠️"]
        AB["BLOCK\nipset ppi_blocked\niptables DROP\nTelegram 🚨"]
    end

    SCORE_IN --> GRADOS
    SCORE_IN --> TIPOS
    GN --> AP
    GB --> AL
    GA & GC --> AB
    TN --> AP
    TBF & THA --> AL & AB
    TBA --> AL
    TIF & TUF & TSF & THA2 & TBS2 & TAG --> AB

    subgraph SCORES_REALES["Scores observados en producción (sesión 2026-06-14)"]
        direction TB
        SR1["B5 Acceso repetitivo: −0.5117 → BAJA → LIMIT"]
        SR2["B2 Port Scan:         −0.6260 → BAJA → LIMIT"]
        SR3["B6 SSH (7 intentos):  LIMIT por heurística"]
        SR4["B1 SYN Flood:         −0.7214 → ALTA → BLOCK"]
        SR5["B3 UDP Flood:         −0.8100 → CRITICA → BLOCK"]
        SR6["B4 ICMP Flood:        −0.7800 → ALTA → BLOCK"]
    end

    style GRADOS fill:#f3e5f5,stroke:#6a1b9a
    style TIPOS  fill:#fff3e0,stroke:#e65100
    style ACCIONES fill:#fce4ec,stroke:#c62828
    style SCORES_REALES fill:#e8f5e9,stroke:#2e7d32
```

---

## Diagrama 4 — Detectores Heurísticos: Ventanas Temporales

```mermaid
flowchart TD

    subgraph BF_DET["🔑 detectar_brute_force() — Brute Force SSH"]
        direction TB
        BF_IN["Flow TCP destino :22\nsrc_ip = IP atacante"]
        BF_ADD["ssh_intentos[ip].append(ts_flow)\n(timestamp del flow)"]
        BF_PURGE["Purga ts < ahora − 60s\n(ventana deslizante de 60s)"]
        BF_COUNT["n = len(ssh_intentos[ip])"]
        BF_DEC{"n ≥ ?"}
        BF_BLOCK["n ≥ 15 → ('BLOCK', n)\nlog: BRUTE-FORCE intentos=15/60s\nTelegram 🔑 BLOQUEO"]
        BF_LIMIT["5 ≤ n < 15 → ('LIMIT', n)\nlog: BRUTE-FORCE intentos=N/60s\nTelegram 🔑 LIMITADO"]
        BF_NONE["n < 5 → None\nno acción heurística"]
        BF_IN --> BF_ADD --> BF_PURGE --> BF_COUNT --> BF_DEC
        BF_DEC -->|"≥ 15"| BF_BLOCK
        BF_DEC -->|"5-14"| BF_LIMIT
        BF_DEC -->|"< 5"| BF_NONE
    end

    subgraph HTTP_DET["🌐 detectar_http_abuse() — HTTP Abuse"]
        direction TB
        H_IN["Flow TCP destino :80\nsrc_ip = IP atacante"]
        H_ADD["http_requests[ip].append(ts_flow)"]
        H_PURGE["Purga ts < ahora − 30s\n(ventana deslizante de 30s)"]
        H_COUNT["n = len(http_requests[ip])"]
        H_DEC{"n ≥ ?"}
        H_BLOCK["n ≥ 100 → ('BLOCK', n)\nlog: HTTP-ABUSE requests=100/30s\nTelegram 🌐 BLOQUEO"]
        H_LIMIT["50 ≤ n < 100 → ('LIMIT', n)\nlog: HTTP-ABUSE requests=N/30s\nTelegram 🌐 LIMITADO"]
        H_NONE["n < 50 → None\nno acción heurística"]
        H_IN --> H_ADD --> H_PURGE --> H_COUNT --> H_DEC
        H_DEC -->|"≥ 100"| H_BLOCK
        H_DEC -->|"50-99"| H_LIMIT
        H_DEC -->|"< 50"| H_NONE
    end

    subgraph OVERRIDE["Override sobre el score IF"]
        OV["Si detector devuelve BLOCK/LIMIT:\n→ OVERRIDE: acción del detector prevalece\n→ Score IF sigue calculándose y logueándose\n→ No interrumpe el pipeline de clasificación\n\nSi detector devuelve None:\n→ Score IF determina la acción"]
    end

    subgraph VALIDADO["✅ Validado en producción — sesión 2026-06-14"]
        V1["B6 Brute Force SSH (Hydra 7 intentos)\n→ ssh_intentos[.100] = [t1..t7] en 60s\n→ n=7 ≥ 5 → LIMIT a los 42s\n→ Kali en ppi_limited, timeout 245s"]
        V2["B5 HTTP Abuse (55 curl 1req/s)\n→ http_requests[.100] = 55 en 30s\n→ n=55 ≥ 50 → LIMIT en 18:13:13\n→ n=100 ≥ 100 → BLOCK en 18:13:21"]
    end

    BF_DET --> OVERRIDE
    HTTP_DET --> OVERRIDE
    OVERRIDE --> VALIDADO

    style BF_DET   fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style HTTP_DET fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style OVERRIDE fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style VALIDADO fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

---

## Diagrama 5 — Telegram + Dashboard: Salidas en Tiempo Real

```mermaid
flowchart LR

    MOTOR["motor_decision.py\n(loop principal)"]

    subgraph TG_ASYNC["📱 Cola Telegram — No Bloqueante"]
        direction TB
        TG_Q["_tg_queue\nQueue(maxsize=100)\nPut: put_nowait() — descarta si llena"]
        TG_W["_tg_worker() — daemon thread\nConsume mensajes de la cola\nurllib.request.urlopen(timeout=10)\nSi error: log.warning('Telegram ERROR')"]
        TG_FORMAT["Formatos de alerta:\n\n🚨 BLOCK:\n  Accion : BLOCK\n  IP     : 192.168.0.100\n  Proto  : TCP\n  Puerto : 80\n  Score  : −0.7214\n  Razon  : pkt_rate:z=+45.2 | ...\n  Hora   : 2026-06-14 18:13:21\n\n⚠️ LIMIT:\n  Accion : LIMIT\n  Score  : −0.5317\n\n🔑 BRUTE FORCE (n intentos/60s)\n🌐 HTTP ABUSE (n req/30s)"]
        TG_Q --> TG_W --> TG_FORMAT
    end

    subgraph LOG_STRUCT["📋 motor_decision.log — Estructura"]
        direction TB
        L1["PERMIT (debug — invisible en prod):\n[no aparece en log — log.debug()]"]
        L2["LIMIT (warning):\n2026-06-14 18:13:13,197 | WARNING | SOSPECHOSO |\nsrc=192.168.0.100 dst=192.168.0.120:80\nproto=TCP score=-0.5317 | LIMIT"]
        L3["BLOCK (warning):\n2026-06-14 18:13:21,833 | WARNING | ANOMALÍA |\nsrc=192.168.0.100 dst=192.168.0.120:80\nproto=TCP score=-0.6281 | BLOCK → BLOCKED"]
        L4["Heurística (warning):\n2026-06-14 18:13:21,833 | WARNING | HTTP-ABUSE |\nsrc=192.168.0.100 requests=100/30s | BLOCK"]
        L5["Stats (info cada 500 flows):\n2026-06-14 | INFO | Estadísticas |\nflows=1500 anomalías=1619 bf=20\nbloqueados=1 latencia_media=35.44ms"]
    end

    subgraph DASHBOARD["🖥️ scripts/dashboard.py"]
        direction TB
        DW["Lee motor_decision.log\nActualiza cada 3s\n\nPantalla terminal:\n┌─────────────────────────────┐\n│ PPI Dashboard — LIVE        │\n│ Flows totales:    1,432     │\n│ Anomalías:          892     │\n│ Bloqueados:           3     │\n│ Limitados:            1     │\n│ Latencia media:   34.5ms    │\n│ Última alerta: 18:13:21     │\n└─────────────────────────────┘"]
    end

    MOTOR -->|"_tg_queue.put_nowait(msg)"| TG_Q
    MOTOR -->|"log.warning(msg)"| LOG_STRUCT
    LOG_STRUCT -->|"tail / grep"| DASHBOARD

    style TG_ASYNC  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style LOG_STRUCT fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style DASHBOARD fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
```

---

## Diagrama 6 — Servicio systemd y Dependencias

```mermaid
flowchart TD

    subgraph SYSTEMD["/etc/systemd/system/ppi-motor.service"]
        direction TB
        UNIT["[Unit]\nDescription=PPI Motor de Decision\nAfter=network.target suricata.service\nRequires=suricata.service"]
        SERVICE_SEC["[Service]\nType=simple\nUser=m4rk\nWorkingDirectory=/home/m4rk/ppi-surikata-producto\nExecStart=/home/m4rk/ppi-sensor/venv/bin/python3\n          scripts/motor_decision.py\nRestart=on-failure\nRestartSec=10\nStandardOutput=null\nStandardError=journal"]
        INSTALL["[Install]\nWantedBy=multi-user.target"]
        UNIT --> SERVICE_SEC --> INSTALL
    end

    subgraph DEPS["Dependencias de arranque"]
        direction LR
        SURICATA_SVC["suricata.service\n(debe estar activo)\neve.json debe existir"]
        NETWORK["network.target\n(red LAN disponible\npara SSH al servidor)"]
        VENV["/home/m4rk/ppi-sensor/venv/\n├── python3\n├── scikit-learn 1.8.0\n├── joblib\n└── numpy"]
        REPO["/home/m4rk/ppi-surikata-producto/\n├── scripts/motor_decision.py\n├── models/isolation_forest.pkl\n├── models/scaler.pkl\n└── results/motor_decision.log"]
    end

    subgraph CICLO["Ciclo de vida del servicio"]
        direction LR
        START["systemctl start ppi-motor\n→ load_model()\n→ inicializar_servidor()\n→ seguir_eve() loop"]
        RESTART["Restart=on-failure\nRestartSec=10s\n(si el proceso muere,\nreinicia automáticamente)"]
        STOP["systemctl stop ppi-motor\n→ proceso termina\n→ ipset y reglas\n   permanecen activas\n   en el servidor"]
        STATUS["systemctl status ppi-motor\n● ppi-motor.service - PPI Motor\n   Active: active (running)\n   PID: 444305"]
        START --> RESTART --> STOP
        START --> STATUS
    end

    DEPS --> SYSTEMD
    SYSTEMD --> CICLO

    style SYSTEMD fill:#efebe9,stroke:#4e342e,stroke-width:2px
    style DEPS    fill:#e3f2fd,stroke:#1565c0
    style CICLO   fill:#e8f5e9,stroke:#2e7d32
```

---

## Diagrama 7 — Las 3 Capas de Detección y su Complementariedad

```mermaid
flowchart LR

    FLUJO["Flow\nevento\nde red"]

    subgraph C1["Capa 1 — Modelo IF\n(score continuo)"]
        direction TB
        C1_COV["Cubre:\n✅ B1 SYN Flood\n✅ B2 Port Scan\n✅ B3 UDP Flood\n✅ B4 ICMP Flood\n✅ C1 C2 C3 Mixtos"]
        C1_GAP["No cubre bien:\n⚠️ B5 HTTP Abuse lento\n⚠️ B6 Brute Force SSH\n(flows individuales ≈ normal)"]
        C1_MET["Recall IF solo: 80.4%\nAUC: 0.9440"]
    end

    subgraph C2["Capa 2 — Detector SSH\n(ventana temporal 60s)"]
        direction TB
        C2_COV["Cubre:\n✅ B6 Brute Force SSH\n   5+ intentos → LIMIT\n   15+ intentos → BLOCK"]
        C2_GAP["No cubre:\n(solo analiza TCP:22)"]
        C2_MET["Umbral: 5/15 intentos/60s"]
    end

    subgraph C3["Capa 3 — Detector HTTP\n(ventana temporal 30s)"]
        direction TB
        C3_COV["Cubre:\n✅ B5 HTTP Abuse\n   50 req → LIMIT\n   100 req → BLOCK"]
        C3_GAP["No cubre:\n(solo analiza TCP:80)"]
        C3_MET["Umbral: 50/100 req/30s"]
    end

    subgraph COMBINED["Resultado combinado"]
        direction TB
        REC["Recall combinado: ~92–95%\nPrecision: 99.96%\nITL: 0% (40 corridas F6)"]
        DESIGN["Diseño de ingeniería:\nIF para volumetría anómala\nDetectores para patrones\nque escapan al scoring individual"]
    end

    FLUJO --> C1 & C2 & C3
    C1 & C2 & C3 --> COMBINED

    style C1       fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style C2       fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style C3       fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style COMBINED fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
```

---

## Resumen: Funciones clave de motor_decision.py

| Función | Líneas aprox. | Rol |
|---|---|---|
| `load_model()` | ~5 | Carga pkl con joblib, loguea τ1/τ2 |
| `inicializar_servidor()` | ~20 | SSH al servidor: crea ipsets y reglas iptables |
| `seguir_eve(path)` | ~15 | tail -f con detección de rotación |
| `es_ip_bloqueable(ip)` | ~7 | Filtra IPs inválidas para ipset |
| `extract_features(e)` | ~15 | Construye vector numpy 1×14 |
| `flow_duration(e)` | ~7 | Calcula duración en segundos |
| `decidir(score)` | ~5 | Devuelve PERMIT/LIMIT/BLOCK según τ1/τ2 |
| `clasificar_grado(score)` | ~5 | NORMAL/BAJA/ALTA/CRITICA |
| `clasificar_tipo(...)` | ~25 | Infiere tipo: SYN_FLOOD, BRUTE_FORCE... |
| `detectar_brute_force(...)` | ~15 | Ventana 60s, umbrales 5/15 |
| `detectar_http_abuse(...)` | ~15 | Ventana 30s, umbrales 50/100 |
| `explicar_anomalia(...)` | ~5 | Top-3 z-scores para LIMIT/BLOCK |
| `bloquear_ip(ip)` | ~8 | SSH → ipset add ppi_blocked |
| `limitar_ip(ip)` | ~8 | SSH → ipset add ppi_limited |
| `telegram_alerta(msg)` | ~5 | put_nowait a la cola async |
| `_tg_worker()` | ~12 | Thread daemon: consume cola y envía HTTP |
| `main()` | ~100 | Loop principal de procesamiento |
