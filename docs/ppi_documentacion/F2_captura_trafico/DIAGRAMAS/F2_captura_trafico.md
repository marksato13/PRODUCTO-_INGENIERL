# F2 — Diagrama: Captura de Tráfico y Pipeline de Datos

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F2 — Captura de Tráfico y Construcción del Dataset  
**Fechas:** 2 – 4 de junio 2026  
**Estado:** ✅ Completado — 38 corridas · 376,827 flows · 49 entradas de bitácora  

---

## Diagrama 1 — Visión General: Escenarios → Dataset → F3

```mermaid
flowchart TD

    %% ── GRUPOS DE ESCENARIOS ─────────────────────────────────────
    subgraph GRP_A["🖥️  Grupo A — Normal  |  Desktop 192.168.0.20  |  label = 0"]
        direction LR
        A1["A1_http_normal.sh\n10 min · curl + wget → :80\n📁 normal_http_01/02"]
        A2["A2_ssh_legitimo.sh\n8 min · ssh → :22\n📁 normal_ssh_01..10"]
        A3["A3_transferencia_legitima.sh\n10 min · scp + wget\n📁 normal_transferencia_01/02"]
        A4["A4_trafico_sostenido.sh\n15 min · curl + ssh mixto\n📁 normal_sostenido_01/02"]
    end

    subgraph GRP_B["💀  Grupo B — Anómalo  |  Kali 192.168.0.100  |  label = 1"]
        direction LR
        B1["B1_syn_flood.sh\nhping3 -S -p 80\n--flood --rand-source"]
        B2["B2_port_scan.sh\nnmap -sS -p 1-1024"]
        B3["B3_udp_flood.sh\nhping3 --udp -p 53\n--flood --rand-source"]
        B4["B4_icmp_flood.sh\nhping3 -1 --flood"]
        B5["B5_acceso_repetitivo.sh\ncurl bucle → :80"]
        B6["B6_bruteforce.sh\nhydra -l m4rk\n-P rockyou.txt ssh://"]
    end

    subgraph GRP_C["🔀  Grupo C — Mixto  |  Desktop + Kali simultáneos  |  label = 1"]
        direction LR
        C1["C1_http_syn_mixto.sh\nDesktop: curl HTTP\nKali: SYN flood"]
        C2["C2_ssh_portscan_mixto.sh\nDesktop: ssh legítimo\nKali: nmap -sS"]
        C3["C3_descarga_udp_mixto.sh\nDesktop: wget archivos\nKali: UDP flood"]
    end

    %% ── SERVIDOR OBJETIVO ────────────────────────────────────────
    SRV[("🌐 Ubuntu Server\n192.168.0.120\nnginx :80 · SSH :22")]

    GRP_A -->|"tráfico legítimo\nA1–A4 corridas"| SRV
    GRP_B -->|"ataques controlados\nB1–B6 corridas"| SRV
    GRP_C -->|"normal + ataque\nsimultáneos"| SRV

    %% ── CAPTURA EN SENSOR ────────────────────────────────────────
    subgraph SENSOR["🔍  Sensor 192.168.0.110  |  Suricata 7.0.3  |  ens35 promiscua"]
        direction TB

        EVE["/var/log/suricata/eve.json\n📄 acumula flows en tiempo real\nJSON-lines · event_type: flow | alert | ssh"]

        subgraph EXPORT_BLOCK["Al finalizar cada corrida — invocado desde Desktop vía SSH"]
            direction LR
            EXP["exportar_eve_por_escenario.sh\n① gzip -c eve.json → data/raw/ARCHIVO.gz\n② truncate -s 0 eve.json\n③ suricatasc reopen-log-files"]
            BIT["registrar_bitacora.sh\n→ docs/bitacora/bitacora_escenarios.txt\n49 entradas registradas"]
            EXP --> BIT
        end

        subgraph RAW_DIR["data/raw/  —  38 archivos .gz"]
            direction TB
            RN["📦 Normal (label=0)\n20260602_normal_http_01_eve.json.gz  533 KB\n20260602_normal_ssh_01_eve.json.gz   28 KB\n20260602_normal_sostenido_01...\n20260604_normal_ssh_03..10 (8 corridas)"]
            RA["📦 Anómalo (label=1)\n20260602_anom_synflood_01_eve.json.gz   4.6 MB\n20260602_anom_portscan_01_eve.json.gz   860 KB\n20260602_anom_bruteforce_01_eve.json.gz 360 KB\n20260602_anom_udpflood_01...\n20260602_anom_icmpflood_01...\n20260602_anom_httpabuse_01..."]
            RM["📦 Mixto (label=1)\n20260602_mixto_http_syn_01_eve.json.gz    4.2 MB\n20260602_mixto_ssh_portscan_01_eve.json.gz\n20260602_mixto_descarga_udp_01_eve.json.gz"]
        end

        subgraph PIPELINE["📊 Pipeline de Procesamiento"]
            direction TB
            P1["scripts/parser.py\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nEntrada: data/raw/*.gz\nFiltro: event_type == 'flow'\nLabel: infiere por nombre de archivo\n  _normal_ → 0  |  resto → 1\nSalida: data/dataset_raw.csv\n  412,097 flows · 75 MB\n  18 columnas"]

            P2["scripts/etiquetar_limpiar.py\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nRefinamiento de label por src_ip:\n  192.168.0.20 / 192.168.0.120 → 0\n  192.168.0.100 / IPs rand-source → 1\nElimina 34 duplicados por flow_id\nElimina 35,236 IPs inválidas:\n  broadcast · multicast · 0.0.0.0\nSalida: data/dataset_clean.csv\n  376,827 flows · 69 MB"]

            P3["scripts/particionar_estadisticos.py\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nPartición CRONOLÓGICA 70 / 15 / 15\n(sin mezcla temporal — evita data leakage)\n\ndata/train.csv   263,778 flows  48 MB\n  normal (0):  11,669  (4.4%)\n  anómalo (1): 252,109 (95.6%)\n\ndata/val.csv     56,524 flows   11 MB\n  normal (0):  0   ← solo anómalos\n  anómalo (1): 56,524\n\ndata/test.csv    56,525 flows   11 MB\n  normal (0):  0   ← solo anómalos\n  anómalo (1): 56,525"]

            P1 --> P2 --> P3
        end

        EVE --> EXP
        EXP --> RAW_DIR
        RAW_DIR --> P1
    end

    SRV -.->|"captura promiscua\nens35 — sin IP"| EVE

    %% ── CONECTOR F3 ──────────────────────────────────────────────
    F3_CONN(["→ F3: Modelado Offline\nfase3_isolation_forest.py\nlee data/raw/*_normal_*_01/02_eve.json.gz\nfiltro src_ip ∈ {192.168.0.20, 192.168.0.120}\n→ 684 flows normales de entrenamiento\n\nNOTA: NO usa train.csv completo\n(evitar sesgo SSH de corridas 03-10)"])
    P3 ==>|"train/val/test\npara evaluación\nmodelo"| F3_CONN

    %% ── ESTILOS ──────────────────────────────────────────────────
    style GRP_A       fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style GRP_B       fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style GRP_C       fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style SENSOR      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style PIPELINE    fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style EXPORT_BLOCK fill:#e0f2f1,stroke:#00796b
    style RAW_DIR     fill:#fafafa,stroke:#757575
    style F3_CONN     fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style EVE         fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style SRV         fill:#fff3e0,stroke:#e65100,stroke-width:2px
```

---

## Diagrama 2 — Ciclo de Vida de una Corrida Completa

```mermaid
sequenceDiagram
    participant OP  as Operador (Desktop)
    participant KL  as Kali 192.168.0.100
    participant SV  as Servidor 192.168.0.120
    participant S7  as Suricata 7.0.3
    participant EV  as eve.json
    participant SC  as exportar_eve.sh
    participant BT  as registrar_bitacora.sh
    participant RW  as data/raw/

    note over OP,RW: Ejemplo: Corrida B1 — SYN Flood

    OP->>OP: HORA_INICIO = $(date +%T)
    OP->>KL: ssh kali "B1_syn_flood.sh start"
    KL->>SV: hping3 -S -p 80 --flood --rand-source
    SV-->>KL: TCP RST (servidor dropea)

    S7->>EV: flow event por cada SYN cerrado
    note over EV: {"src_ip":"x.x.x.x","dest_port":80,\n"pkt_rate":muy_alto,"pkts_toclient":0}

    note over OP,RW: ⏱️  Duración del escenario (B1: 5 min)

    OP->>OP: HORA_FIN = $(date +%T)
    OP->>S7: ssh sensor "exportar_eve_por_escenario.sh\n2026-06-02 anom synflood 01"

    SC->>EV: gzip -c eve.json
    SC->>RW: 20260602_anom_synflood_01_eve.json.gz
    SC->>EV: truncate -s 0 (limpia)
    SC->>S7: suricatasc reopen-log-files

    OP->>S7: ssh sensor "registrar_bitacora.sh\nanom synflood 192.168.0.100 192.168.0.120\n03:12:25 03:14:25 hping3 ..."
    BT->>BT: append → bitacora_escenarios.txt

    note over OP,RW: ⏱️  Espera ≥ 2 minutos antes de la siguiente corrida
```

---

## Diagrama 3 — Transformación del Dataset Paso a Paso

```mermaid
flowchart LR

    subgraph RAW["data/raw/  38 archivos .gz"]
        R1["20260602_normal_http_01.gz\n20260602_normal_ssh_01.gz\n20260602_normal_sostenido_01.gz\n20260602_normal_transferencia_01.gz\n20260604_normal_ssh_03..10.gz  (8 archivos)\n..."]
        R2["20260602_anom_synflood_01.gz\n20260602_anom_portscan_01.gz\n20260602_anom_udpflood_01.gz\n20260602_anom_icmpflood_01.gz\n20260602_anom_httpabuse_01.gz\n20260602_anom_bruteforce_01.gz"]
        R3["20260602_mixto_http_syn_01.gz\n20260602_mixto_ssh_portscan_01.gz\n20260602_mixto_descarga_udp_01.gz"]
    end

    subgraph P1B["parser.py"]
        direction TB
        P1_IN["Lee todos los .gz\nFiltro: event_type == 'flow'"]
        P1_LBL["Label por nombre:\n_normal_ → 0\nresto    → 1"]
        P1_OUT["dataset_raw.csv\n412,097 flows\n75 MB\n18 columnas"]
        P1_IN --> P1_LBL --> P1_OUT
    end

    subgraph P2B["etiquetar_limpiar.py"]
        direction TB
        P2_IP["Refina label por src_ip\n192.168.0.20 → 0 (normal)\n192.168.0.100 → 1 (anómalo)\nIPs rand-source → 1"]
        P2_DUP["Elimina 34 duplicados\n(mismo flow_id)"]
        P2_INV["Elimina 35,236 IPs inválidas\nbroadcast · multicast\n0.0.0.0 · *.255"]
        P2_OUT["dataset_clean.csv\n376,827 flows · 69 MB\nNormal:   11,669  (3.1%)\nAnómalo: 365,158 (96.9%)"]
        P2_IP --> P2_DUP --> P2_INV --> P2_OUT
    end

    subgraph P3B["particionar_estadisticos.py"]
        direction TB
        P3_ORD["Ordena por timestamp\npartición CRONOLÓGICA\n(sin shuffle — evita leakage)"]
        TRAIN["train.csv\n263,778 flows  48 MB\n70% cronológico\nNormal:  11,669\nAnóm: 252,109"]
        VAL["val.csv\n56,524 flows  11 MB\n15% cronológico\nNormal:  0\nAnóm: 56,524"]
        TEST["test.csv\n56,525 flows  11 MB\n15% cronológico\nNormal:  0\nAnóm: 56,525"]
        P3_ORD --> TRAIN & VAL & TEST
    end

    subgraph F3_USE["Uso en F3 (IF entrenamiento)"]
        F3_RAW["Lee raw/*_normal_*_01/02.gz\nFiltro: src_ip Desktop/Servidor\n→ 684 flows normales\n(corridas 01-02 únicamente)"]
        F3_NOTE["⚠️ No usa train.csv\nEvita sesgo SSH\nde corridas 03-10"]
    end

    subgraph F3_EVAL["Uso en F3/F4 (evaluación)"]
        EVAL_SET["Eval balanceado 50/50:\n11,669 normales de train.csv\n11,669 anómalos de test.csv\n= 23,338 flows total\npara comparar modelos"]
    end

    RAW --> P1B --> P2B --> P3B
    TRAIN -.->|"684 normales\ncorridas 01-02"| F3_USE
    TRAIN & TEST -.->|"evaluación\nAUC · F1 · Recall"| F3_EVAL

    style RAW    fill:#fafafa,stroke:#757575
    style P1B    fill:#e3f2fd,stroke:#1565c0
    style P2B    fill:#e8f5e9,stroke:#2e7d32
    style P3B    fill:#fff3e0,stroke:#e65100
    style F3_USE fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style F3_EVAL fill:#f3e5f5,stroke:#6a1b9a
    style TRAIN  fill:#c8e6c9,stroke:#1b5e20
    style VAL    fill:#bbdefb,stroke:#1565c0
    style TEST   fill:#ffccbc,stroke:#bf360c
```

---

## Diagrama 4 — Distribución del Dataset por Escenario

```mermaid
%%{init: {"pie": {"textPosition": 0.55}}}%%
pie title dataset_clean.csv — 376,827 flows por escenario
    "C3 mixto_descarga_udp  109,839" : 109839
    "C1 mixto_http_syn       95,157" : 95157
    "B1 anom_synflood        94,841" : 94841
    "A1 normal_http          11,333" : 11333
    "B5 anom_httpabuse       21,758" : 21758
    "B4 anom_icmpflood       20,200" : 20200
    "B3 anom_udpflood        15,815" : 15815
    "B2 anom_portscan         3,297" : 3297
    "B6 anom_bruteforce       2,062" : 2062
    "A4 normal_sostenido        251" : 251
    "A3 normal_transferencia     29" : 29
```

---

## Diagrama 5 — Nomenclatura de Archivos y Trazabilidad

```mermaid
flowchart TD
    NOMBRE["Nombre de archivo:\n20260602_normal_http_01_eve.json.gz"]

    subgraph PARSE["Componentes del nombre"]
        direction LR
        F1N["20260602\n← Fecha YYYYMMDD"]
        F2N["normal\n← Grupo A/B/C\nnormal · anom · mixto"]
        F3N["http\n← Escenario\nhttp · ssh · synflood\nportscan · bruteforce..."]
        F4N["01\n← Número de corrida\n(01, 02, 03...)"]
        F5N["eve.json.gz\n← Tipo de archivo\nsalida de Suricata\ncomprimido con gzip"]
    end

    NOMBRE --> PARSE

    subgraph TRAZA["Trazabilidad del archivo"]
        direction TB
        T1["parser.py infiere label=0\npor '_normal_' en el nombre"]
        T2["etiquetar_limpiar.py\nconfirma por src_ip=192.168.0.20"]
        T3["bitácora registra:\nfecha · grupo · escenario · corrida\nIP origen · IP destino\nhora inicio/fin · herramienta"]
        T1 --> T2 --> T3
    end

    NOMBRE --> TRAZA

    EJEMPLOS["Ejemplos reales:\n20260602_normal_http_01_eve.json.gz     → label=0 · 533 KB\n20260602_anom_synflood_01_eve.json.gz   → label=1 · 4.6 MB\n20260602_mixto_http_syn_01_eve.json.gz  → label=1 · 4.2 MB\n20260604_normal_ssh_03_eve.json.gz      → label=0 ·  28 KB"]

    TRAZA --> EJEMPLOS

    style NOMBRE fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style PARSE  fill:#e3f2fd,stroke:#1565c0
    style TRAZA  fill:#e8f5e9,stroke:#2e7d32
    style EJEMPLOS fill:#fafafa,stroke:#757575
```

---

## Diagrama 6 — Conector Completo F1 → F2 → F3

```mermaid
flowchart LR

    F1(["F1\neve.json\nactivo\nens35"])

    subgraph F2_BOX["F2 — Captura y Procesamiento"]
        direction TB
        C1F["Escenarios A/B/C\n13 tipos · 38 corridas"]
        C2F["exportar_eve_por_escenario.sh\n38 archivos .gz en data/raw/"]
        C3F["parser.py\n412,097 flows"]
        C4F["etiquetar_limpiar.py\n376,827 flows"]
        C5F["particionar_estadisticos.py\ntrain / val / test"]
        C1F --> C2F --> C3F --> C4F --> C5F
    end

    F3A(["F3a\n684 flows\nnormales\n(raw directo)"])
    F3B(["F3b\neval set\n23,338 flows\n(train+test)"])

    F1 ==>|"eve.json\nes la entrada\nde cada corrida"| C1F
    C5F ==>|"corridas 01-02\nsrc_ip Desktop"| F3A
    C5F ==>|"11,669 normales\n+ 11,669 anómalos"| F3B

    style F1      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style F2_BOX  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style F3A     fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style F3B     fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Resumen de archivos producidos en F2

| Archivo | Ruta | Tamaño | Descripción |
|---|---|---|---|
| `*.gz` (38 archivos) | `data/raw/` | 4 MB – 4.6 MB c/u | Eve.json comprimido por corrida |
| `dataset_raw.csv` | `data/` | 75 MB | 412,097 flows sin limpiar |
| `dataset_clean.csv` | `data/` | 69 MB | 376,827 flows limpios y etiquetados |
| `train.csv` | `data/` | 48 MB | 263,778 flows (70% cronológico) |
| `val.csv` | `data/` | 11 MB | 56,524 flows (15%) |
| `test.csv` | `data/` | 11 MB | 56,525 flows (15%) |
| `bitacora_escenarios.txt` | `docs/bitacora/` | — | 49 corridas registradas |
| `resumen_estadistico.txt` | `data/` | — | Stats del dataset por escenario |
