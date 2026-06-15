# Overview — Pipeline Completo F1 → F6

**Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
**Universidad Peruana Unión · PPI 2026 · Rubén Mark Salazar Tocas**  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Última actualización:** 15 de junio 2026  

---

## Diagrama 1 — Pipeline General F1 → F6 con Scripts y Artefactos

```mermaid
flowchart LR

    subgraph F1["F1 — Entorno\n10 may 2026"]
        direction TB
        F1A["🔍 Suricata 7.0.3\nens35 promiscua\n192.168.0.110"]
        F1B["/var/log/suricata/eve.json\nJSON-lines · tiempo real\nflow|alert|ssh|stats"]
        F1C["revisar_suricata.sh\n→ suricata_revision.txt\nNTP America/Lima\nSSH keys Desktop↔Sensor/Server"]
        F1A --> F1B --> F1C
    end

    subgraph F2["F2 — Captura\n2-4 jun 2026"]
        direction TB
        F2A["13 escenarios A/B/C\n38 corridas · 49 bitácora\nexportar_eve_por_escenario.sh"]
        F2B["parser.py\n412,097 flows · 75MB"]
        F2C["etiquetar_limpiar.py\n376,827 flows · 69MB\n(dedup · IP inválidas)"]
        F2D["particionar_estadisticos.py\ntrain 70% · val 15% · test 15%\ncronológico sin leakage"]
        F2A --> F2B --> F2C --> F2D
    end

    subgraph F3["F3 — Modelo\n2-4 jun 2026"]
        direction TB
        F3A["fase3_isolation_forest.py\n684 flows normales\n(corridas 01-02 · src_ip Desktop)"]
        F3B["StandardScaler\n→ scaler.pkl  1.4KB"]
        F3C["IsolationForest\nn=300 contam=0.05\n→ isolation_forest.pkl  2.5MB"]
        F3D["auc_roc_umbrales.py\nAUC=0.9440\nτ1=−0.4973 · τ2=−0.6873"]
        F3A --> F3B --> F3C --> F3D
    end

    subgraph F4["F4 — Motor\n2-4 jun 2026"]
        direction TB
        F4A["motor_decision.py\n547 líneas\nPID activo como ppi-motor.service"]
        F4B["Filtros (5)\nWhitelist · IPv4 · es_ip_bloqueable\npkts_toserver > 0"]
        F4C["Pipeline: extract→scale→score\nLatencia P95=34.8ms"]
        F4D["3 Capas decisión:\nIF score · Det.SSH · Det.HTTP\n+ Telegram async 🚨⚠️"]
        F4A --> F4B --> F4C --> F4D
    end

    subgraph F5["F5 — Control\n2-4 jun 2026"]
        direction TB
        F5A["SSH sensor→servidor\nbloquear_ip() · limitar_ip()"]
        F5B["ipset ppi_blocked\niptables DROP total"]
        F5C["ipset ppi_limited\nhashlimit 100pkt/s"]
        F5D["enforce.sh manual\ntimeout 300s auto\nDashboard :8080 SSE"]
        F5A --> F5B & F5C --> F5D
    end

    subgraph F6["F6 — Validación\n2-4 jun 2026"]
        direction TB
        F6A["f6_corridas.py\n40 corridas · 4 grupos × 10"]
        F6B["resultados_f6_completo.csv\nDisp=100% · ITL=0%\nTIE=100% · Lead=26s"]
        F6C["reporte_validacion_final.pdf\nMVP_funcional.zip  25MB"]
        F6A --> F6B --> F6C
    end

    F1B ===>|"eve.json\ncada corrida"| F2A
    F2D ===>|"data/raw/\n684 flows normales\ncorridas 01-02"| F3A
    F3D ===>|"*.pkl\nτ1 · τ2"| F4A
    F4D ===>|"bloquear/limitar\nvía SSH"| F5A
    F5D ===>|"sistema operativo\n40 corridas"| F6A

    style F1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style F2 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style F3 fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style F4 fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style F5 fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style F6 fill:#fffde7,stroke:#f9a825,stroke-width:2px
```

---

## Diagrama 2 — Arquitectura Física del Laboratorio

```mermaid
flowchart TD

    NTP(["☁️ pool.ntp.org\nAmerica/Lima UTC−5"])

    subgraph LAN["Red 192.168.0.0/24 — VMware"]
        direction TB

        GW(["🔒 pfSense 192.168.0.1\nGateway · Firewall · DHCP"])

        subgraph DT["🖥️ Desktop 192.168.0.20 — Administrador"]
            DT1["Claude Code · Orquestación\nScripts A1-A4 · C1-C3\ncurl · ssh · scp · wget\n🔑 SSH keys → Sensor y Servidor"]
        end

        subgraph KL["💀 Kali 192.168.0.100 — Atacante"]
            KL1["Scripts B1-B6\nhping3 · nmap · hydra · curl\nOrigen tráfico anómalo"]
        end

        subgraph SENSOR["🔍 Sensor 192.168.0.110 — IDS + Motor"]
            direction TB
            ENS33["ens33 192.168.0.110\nGestión SSH"]
            ENS35["ens35 sin IP\nCaptura promiscua"]
            SURI["Suricata 7.0.3 → eve.json"]
            MOTOR["motor_decision.py\nppi-motor.service\nIsolation Forest + detectores"]
            DASH["dashboard_web.py :8080\nppi-dashboard.service"]
            ENS35 --> SURI --> MOTOR --> DASH
        end

        subgraph SRV["🌐 Servidor 192.168.0.120 — Objetivo"]
            direction TB
            NGX["nginx :80 ✅"]
            SSHD["openssh-server :22 ✅"]
            IPSET["ipset ppi_blocked → DROP\nipset ppi_limited → hashlimit\niptables INPUT chain"]
            NGX --- SSHD --- IPSET
        end
    end

    subgraph CLOUD["☁️ Servicios externos"]
        TG["📱 Telegram Bot\nchat_id=8512353253\n🚨⚠️🔑🌐"]
        GH["🐙 GitHub\nmarksato13/PRODUCTO-_INGENIERL\ndocumentación + código"]
    end

    NTP -.->|"NTP sync"| DT & SENSOR & SRV & KL
    GW --- DT & KL & SENSOR & SRV
    DT -->|"A1-A4: curl/ssh/scp\nnormal"| SRV
    KL -->|"B1-B6: hping3/nmap/hydra\nataque"| SRV
    SRV -.->|"respuestas"| DT
    ENS35 -.->|"copia promiscua\nde todo el tráfico LAN"| SURI
    MOTOR -->|"SSH bloquear_ip()\nlimitar_ip()"| IPSET
    MOTOR -->|"alerta async\ndaemon thread"| TG
    DT -->|"scp + git push"| GH

    style LAN    fill:#f5f5f5,stroke:#9e9e9e,stroke-width:2px
    style SENSOR fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style SRV    fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style DT     fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style KL     fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style CLOUD  fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
```

---

## Diagrama 3 — Flujo de Datos Completo: eve.json → Acción

```mermaid
flowchart TD

    EVE["/var/log/suricata/eve.json\nJSON-lines · crece en tiempo real"]

    subgraph MOTOR_LOOP["motor_decision.py — Loop principal"]
        direction TB

        FILTROS["5 Filtros:\n① event_type=='flow'\n② sin IPv6\n③ ∉ WHITELIST\n④ es_ip_bloqueable()\n⑤ pkts_toserver > 0"]

        FEATURES["extract_features(e)\n→ numpy [1×14]\npkts · bytes · duration\npkt_rate · byte_rate · ratios\nis_tcp · is_udp · is_icmp · dest_port"]

        SCALE["scaler.transform(X)\n(X − μ_normal) / σ_normal\nμ y σ del tráfico legítimo"]

        SCORE["clf.score_samples(X)\n→ score ∈ (−1, 0)\n34.5ms media · 34.8ms P95"]

        DETECTORES["Detectores paralelos:\nBrute Force SSH: 5→LIMIT / 15→BLOCK / 60s\nHTTP Abuse:      50→LIMIT / 100→BLOCK / 30s"]

        GRADO["clasificar_grado(score)\nNORMAL > −0.4973\nBAJA   > −0.6873\nALTA   > −0.82\nCRÍTICA ≤ −0.82"]

        DECISION["decidir(score) + override detectores\nscore > τ1  → PERMIT  (log.debug)\nτ2<score≤τ1 → LIMIT   (log.warning)\nscore ≤ τ2  → BLOCK   (log.warning)"]

        EXPLAIN["explicar_anomalia()\nTop-3 z-scores solo en LIMIT/BLOCK\nEj: pkt_rate:z=+45.2 | pkts_to:z=+38.7"]

        FILTROS --> FEATURES --> SCALE --> SCORE
        SCORE --> GRADO
        SCORE --> DETECTORES
        SCORE --> DECISION
        DETECTORES --> DECISION
        EXPLAIN --> DECISION
    end

    subgraph ACCIONES["Acciones por decisión"]
        direction LR
        PERMIT_A["PERMIT\nNo acción\nlog.debug() invisible"]
        LIMIT_A["LIMIT\nipset add ppi_limited\nhashlimit 100pkt/s\nTelegram ⚠️\nlog.warning SOSPECHOSO"]
        BLOCK_A["BLOCK\nipset add ppi_blocked\niptables DROP\nTelegram 🚨\nlog.warning ANOMALÍA"]
    end

    subgraph SERVIDOR["Servidor 192.168.0.120 — Netfilter"]
        direction TB
        R1["Regla 1: match ppi_blocked → DROP"]
        R2["Regla 2: match ppi_limited + >100pkt/s → DROP"]
        TIMEOUT["Timeout 300s → kernel elimina auto"]
        R1 & R2 --> TIMEOUT
    end

    EVE -->|"seguir_eve()\ntail-f · detección rotación"| FILTROS
    DECISION --> PERMIT_A & LIMIT_A & BLOCK_A
    LIMIT_A & BLOCK_A -->|"SSH m4rk@192.168.0.120\nsudo ipset add"| SERVIDOR

    style MOTOR_LOOP fill:#fafafa,stroke:#757575,stroke-width:2px
    style FILTROS    fill:#e3f2fd,stroke:#1565c0
    style FEATURES   fill:#e8f5e9,stroke:#2e7d32
    style SCORE      fill:#fff3e0,stroke:#e65100
    style DECISION   fill:#fce4ec,stroke:#c62828
    style ACCIONES   fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style SERVIDOR   fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
```

---

## Diagrama 4 — Las 3 Capas de Detección + Telegram + Dashboard

```mermaid
flowchart LR

    FLOW["Flow\nevento\neve.json"]

    subgraph CAPA1["Capa 1 — Modelo IF\n(score continuo −1→0)"]
        direction TB
        C1A["✅ B1 SYN Flood  AUC=0.9529"]
        C1B["✅ B2 Port Scan  AUC=0.9721"]
        C1C["✅ B3 UDP Flood  AUC=0.9905"]
        C1D["✅ B4 ICMP Flood AUC=0.9861"]
        C1E["✅ C1 C2 C3 Mixtos"]
        C1F["⚠️ B5 HTTP Abuse Det=56%"]
        C1G["⚠️ B6 BruteForce Det=0.9%"]
    end

    subgraph CAPA2["Capa 2 — Detector SSH\n(ventana 60s)"]
        direction TB
        C2A["5  intentos → LIMIT"]
        C2B["15 intentos → BLOCK"]
        C2C["✅ B6 BruteForce → ~90%"]
    end

    subgraph CAPA3["Capa 3 — Detector HTTP\n(ventana 30s)"]
        direction TB
        C3A["50  req/30s → LIMIT"]
        C3B["100 req/30s → BLOCK"]
        C3C["✅ B5 HTTP Abuse → ~80%"]
    end

    subgraph RESULTADO["Resultado Combinado"]
        direction TB
        R1["Recall base IF:   80.4%"]
        R2["+ SSH detector:  +~10%"]
        R3["+ HTTP detector: +~4%"]
        R4["Recall total:  ~92-95%"]
        R5["Precision:     99.96%"]
        R6["ITL:           0%"]
        R1 --> R2 --> R3 --> R4
    end

    subgraph NOTIF["Notificaciones"]
        direction TB
        TG2["📱 Telegram Bot\n🚨 BLOCK · ⚠️ LIMIT\n🔑 BruteForce · 🌐 HTTP\nCola async daemon\n300-800ms"]
        DW["🖥️ Dashboard Web :8080\nFlask + SSE\nAuto-refresca 150ms\n6 vistas: alerts/control/análisis"]
        DT2["📟 Dashboard Terminal\ndashboard.py cada 3s\nStats en tiempo real"]
    end

    FLOW --> CAPA1 & CAPA2 & CAPA3
    CAPA1 & CAPA2 & CAPA3 --> RESULTADO
    RESULTADO --> NOTIF

    style CAPA1    fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style CAPA2    fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style CAPA3    fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style RESULTADO fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style NOTIF    fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
```

---

## Diagrama 5 — Resumen de Métricas Finales

```mermaid
flowchart TD

    subgraph PIPELINE_MET["Métricas de Pipeline"]
        direction LR
        PM1["Latencia P95 = 34.8ms\nRequisito < 500ms ✅ (14× margen)"]
        PM2["Throughput = 29 flows/s"]
        PM3["Disponibilidad = 100%\n(40/40 corridas)"]
    end

    subgraph MODELO_MET["Métricas del Modelo"]
        direction LR
        MM1["AUC-ROC = 0.9440"]
        MM2["Recall base = 87.6%\nRecall total = 92–95%"]
        MM3["Precision = 99.96%\nF1-Score = 0.9338"]
        MM4["FPR SSH = 0%\nFPR Transferencia = 0%"]
    end

    subgraph OPERACION_MET["Métricas Operacionales (40 corridas)"]
        direction LR
        OM1["ITL = 0%\n(0 flows legítimos afectados)"]
        OM2["TIE = 100%\n(todas anomalías con acción)"]
        OM3["Lead Time = 26s\nMTTC = 28s"]
    end

    subgraph RECAL["Recalibración: v1 → v2"]
        direction LR
        RC1["v1: 2026-06-02 01:42\nUmbral binario clf.offset_=−0.5481"]
        RC2["v2: 2026-06-04 14:41\nTriple PERMIT/LIMIT/BLOCK\nτ1=−0.4973 · τ2=−0.6873"]
        RC1 -->|"análisis sensibilidad\nfiltro doble corridas"| RC2
    end

    subgraph ENTREGABLES_MET["Entregables"]
        direction LR
        E1["reporte_validacion_final.pdf  7.4KB\nF6 formal PPI"]
        E2["MVP_funcional.zip  25MB\nSistema completo"]
        E3["GitHub\nmarksato13/PRODUCTO-_INGENIERL\n+ 35 commits · docs F1-F6"]
    end

    PIPELINE_MET --- MODELO_MET --- OPERACION_MET
    RECAL --- ENTREGABLES_MET

    style PIPELINE_MET  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style MODELO_MET    fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style OPERACION_MET fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style RECAL         fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style ENTREGABLES_MET fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
```

---

## Conectores entre fases

| Conector | Desde | Hacia | Artefacto transferido |
|---|---|---|---|
| **eve.json** | F1 | F2 | `/var/log/suricata/eve.json` — `exportar_eve_por_escenario.sh` gzip+rota al fin de cada corrida |
| **data/raw/*.gz** | F2 | F3 | 38 archivos · `fase3_isolation_forest.py` filtra corridas 01-02 + src_ip Desktop → 684 flows |
| **models/*.pkl + τ** | F3 | F4 | `isolation_forest.pkl` + `scaler.pkl` por `joblib.load()` · TAU1=−0.4973 TAU2=−0.6873 hardcoded |
| **bloquear/limitar** | F4 | F5 | `_ssh('sudo ipset add ppi_blocked IP timeout 300')` via subprocess SSH |
| **sistema activo** | F5 | F6 | ipsets + iptables configurados · motor corriendo · `f6_corridas.py` mide desde log |

---

## Estado del sistema (verificado 2026-06-15)

| Componente | VM | Estado |
|---|---|---|
| Suricata 7.0.3 | 192.168.0.110 | ✅ active — eve.json tiempo real |
| ppi-motor.service | 192.168.0.110 | ✅ active — P95=34.8ms |
| ppi-dashboard.service | 192.168.0.110 | ✅ active — http://192.168.0.110:8080 |
| Telegram Bot | cloud | ✅ activo — alertas 🚨⚠️🔑🌐 |
| nginx :80 | 192.168.0.120 | ✅ active |
| openssh-server :22 | 192.168.0.120 | ✅ active |
| ipset ppi_blocked | 192.168.0.120 | ✅ configurado · timeout 300s |
| ipset ppi_limited | 192.168.0.120 | ✅ configurado · hashlimit 100/s |
| iptables DROP/hashlimit | 192.168.0.120 | ✅ reglas líneas 1 y 2 activas |
| GitHub repo | cloud | ✅ main · d07e0a4 · docs F1-F6 completos |
