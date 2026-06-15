# F5 — Diagrama: Control Inline e Integración

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F5 — Control Inline, Telegram y Dashboard  
**Estado:** ✅ En producción — ipset/iptables activos · Telegram operativo · Dashboard web en :8080  

---

## Diagrama 1 — Pipeline Completo de Detección y Respuesta (9 Etapas)

```mermaid
flowchart LR

    subgraph RED["🌐 Red LAN 192.168.0.0/24"]
        direction TB
        KL["Kali 192.168.0.100\nhping3 · nmap · hydra"]
        DT["Desktop 192.168.0.20\ncurl · ssh · scp"]
        SV_T["Servidor 192.168.0.120\nnginx :80 · SSH :22"]
        KL -->|"ataque"| SV_T
        DT -->|"normal"| SV_T
    end

    subgraph E1_2["① Captura  ② Eventos\n< 1ms cada etapa"]
        direction TB
        SURI["Suricata 7.0.3\nens35 — modo pasivo\nlibpcap / AF_PACKET\nDPI por flow"]
        EVE_F["/var/log/suricata/eve.json\nJSON-lines streaming\nevent_type: flow"]
        SURI --> EVE_F
    end

    subgraph E3_4["③ Data Eng  ④ Inferencia\n2–15ms"]
        direction TB
        PARSE["parse_flow()\nextract_features()\n→ vector numpy 1×14"]
        INFER["Isolation Forest\nscaler.transform(X)\nclf.score_samples(X)\n→ score ∈ (−1, 0)"]
        PARSE --> INFER
    end

    subgraph E5_6["⑤ Clasificación  ⑥ Decisión\n< 1ms + 5–10ms"]
        direction TB
        CLASS["score vs τ1/τ2\n+ detectores SSH/HTTP"]
        DEC3["PERMIT / LIMIT / BLOCK"]
        CLASS --> DEC3
    end

    subgraph E7["⑦ Control Inline\n< 1ms (kernel)"]
        direction TB
        IPSET_K["ipset add ppi_blocked\nipset add ppi_limited\niptables DROP / hashlimit"]
    end

    subgraph E8["⑧ Notificación\n100–500ms async"]
        direction TB
        TG_N["📱 Telegram Bot\nCola async daemon\n🚨 BLOCK  ⚠️ LIMIT\n🔑 BruteForce  🌐 HTTP"]
    end

    subgraph E9["⑨ Visualización\n3s refresh"]
        direction TB
        DASH_W["🖥️ Dashboard Web\nhttp://192.168.0.110:8080\nFlask + SSE + Chart.js\nAuto-refresca vía SSE"]
        DASH_T["📟 Dashboard Terminal\nscripts/dashboard.py\nLee motor_decision.log\ncada 3s"]
    end

    RED -->|"tráfico LAN"| E1_2
    E1_2 -->|"seguir_eve()\ntail-f"| E3_4
    E3_4 --> E5_6
    E5_6 -->|"bloquear_ip()\nlimitar_ip()\nSSH al servidor"| E7
    E5_6 -->|"telegram_alerta()\nasync"| E8
    E5_6 -->|"log.warning()"| E9

    LATENCIA(["⏱️ Latencia Total\nP95 = 34.8ms\nRequisito < 500ms\nCumple con margen 14×"])
    E7 --> LATENCIA

    style RED    fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style E1_2   fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style E3_4   fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style E5_6   fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style E7     fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
    style E8     fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    style E9     fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style LATENCIA fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
```

---

## Diagrama 2 — Mecanismo ipset + iptables en el Servidor (Netfilter)

```mermaid
flowchart TD

    PAQUETE["📦 Paquete entrante\nsrc_ip = 192.168.0.100\ndst_ip = 192.168.0.120:80\nproto = TCP"]

    subgraph NETFILTER["🐧 Kernel Linux — Netfilter — Cadena INPUT"]
        direction TB

        R1{"Regla 1\n(línea 1 INPUT)\n¿src_ip ∈ ppi_blocked?"}
        R1_YES["DROP inmediato\n0 paquetes pasan\n0 respuesta al atacante"]

        R2{"Regla 2\n(línea 2 INPUT)\n¿src_ip ∈ ppi_limited?\n+ ¿excede 100 pkt/s?"}
        R2_YES["DROP\npaquetes en exceso de 100/s\nBurst permitido: 150 pkts"]
        R2_NO_LIMIT["ACCEPT hasta 100 pkt/s\n(los primeros 150 pasan)"]

        RESTO["Resto de reglas iptables\n(ACCEPT por defecto)"]
        ACCEPT["ACCEPT\nPaquete llega a nginx/sshd"]

        R1 -->|"SÍ"| R1_YES
        R1 -->|"NO"| R2
        R2 -->|"SÍ + excede"| R2_YES
        R2 -->|"SÍ + bajo límite"| R2_NO_LIMIT
        R2 -->|"NO (no en set)"| RESTO
        RESTO --> ACCEPT
        R2_NO_LIMIT --> ACCEPT
    end

    subgraph IPSETS["Contenedores ipset en servidor 192.168.0.120"]
        direction LR

        subgraph BLOCKED["ppi_blocked — hash:ip"]
            BK_HDR["Type: hash:ip\ntimeout: 300s\nHashsize: 1024\nMaxelem: 65536"]
            BK_EX["Ejemplo activo:\n192.168.0.100  timeout 245s\n(kernel hace countdown)\nAl expirar → eliminado auto"]
        end

        subgraph LIMITED["ppi_limited — hash:ip"]
            LM_HDR["Type: hash:ip\ntimeout: 300s\nHashsize: 1024\nHashlimit: 100/sec burst 150\nmode srcip"]
            LM_EX["Ejemplo activo:\n192.168.0.100  timeout 180s\nhashlimit cuenta por srcip\nindependiente por IP"]
        end
    end

    subgraph IPTABLES_CMDS["Comandos que instalan las reglas (inicializar_servidor())"]
        direction TB
        CMD1["sudo iptables -I INPUT \\\n  -m set --match-set ppi_blocked src \\\n  -j DROP"]
        CMD2["sudo iptables -I INPUT 2 \\\n  -m set --match-set ppi_limited src \\\n  -m hashlimit \\\n    --hashlimit-name ppi_limit \\\n    --hashlimit-above 100/sec \\\n    --hashlimit-mode srcip \\\n    --hashlimit-burst 150 \\\n  -j DROP"]
        CMD1 --- CMD2
    end

    subgraph VERIFY["Verificación real — sesión 2026-06-14"]
        VF1["sudo iptables -L INPUT -n --line-numbers | grep ppi\n\n1  DROP  all  0.0.0.0/0  0.0.0.0/0\n   match-set ppi_blocked src\n2  DROP  all  0.0.0.0/0  0.0.0.0/0\n   match-set ppi_limited src\n   limit: above 100/sec burst 150 mode srcip"]
        VF2["sudo ipset list ppi_limited\n→ 192.168.0.100  timeout 245  ✅"]
    end

    PAQUETE --> NETFILTER
    BLOCKED --> R1
    LIMITED --> R2
    IPTABLES_CMDS -.->|"idempotente\nal arrancar motor"| NETFILTER
    NETFILTER --> VERIFY

    style NETFILTER  fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style IPSETS     fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style BLOCKED    fill:#ffcdd2,stroke:#b71c1c
    style LIMITED    fill:#ffe0b2,stroke:#e65100
    style IPTABLES_CMDS fill:#e8f5e9,stroke:#2e7d32
    style VERIFY     fill:#e3f2fd,stroke:#1565c0
```

---

## Diagrama 3 — Canal SSH: Motor → Servidor (Control Remoto)

```mermaid
flowchart LR

    subgraph SENSOR["🔍 Sensor 192.168.0.110\nmotor_decision.py"]
        direction TB
        DEC_M["Decisión: BLOCK / LIMIT"]

        subgraph SSH_FUNC["Funciones de control"]
            direction TB
            BLK_F["bloquear_ip(ip)\n_ssh('sudo ipset add ppi_blocked\n      {ip} timeout 300 -exist\n      && echo BLOCKED {ip}')"]
            LIM_F["limitar_ip(ip)\n_ssh('sudo ipset add ppi_limited\n      {ip} timeout 300 -exist\n      && echo LIMITED {ip}')"]
        end

        subgraph SSH_IMPL["_ssh(cmd) — implementación"]
            SSH_CODE["subprocess.run(\n  ['ssh',\n   '-o', 'StrictHostKeyChecking=no',\n   '-o', 'ConnectTimeout=5',\n   'm4rk@192.168.0.120',\n   cmd],\n  capture_output=True,\n  text=True,\n  timeout=8\n)"]
        end

        IN_MEM["Sets en memoria Python:\nbloqueados = set()  ← evita duplicados\nlimitados  = set()\n\nSi src_ip ∈ bloqueados:\n  log 'ya bloqueado' — sin SSH\nSi src_ip ∈ limitados:\n  log 'ya limitado'  — sin SSH"]

        DEC_M --> BLK_F & LIM_F
        BLK_F & LIM_F --> SSH_IMPL
        SSH_IMPL --> IN_MEM
    end

    subgraph TUNNEL["🔐 Canal SSH\nClave pública configurada\nsin contraseña\nDesde F1"]
        CONN["m4rk@192.168.0.120\nPort 22\nStrictHostKeyChecking=no\nConnectTimeout=5s\ntimeout subprocess=8s"]
    end

    subgraph SERVIDOR_S["🌐 Servidor 192.168.0.120"]
        direction TB
        SUDO["sudo (sin contraseña)\npara ipset y iptables\n/etc/sudoers.d/ppi"]
        IPSET_CMD["ipset add ppi_blocked IP timeout 300 -exist\nipset add ppi_limited IP timeout 300 -exist\n-exist → idempotente (no error si ya existe)"]
        RESP["Respuesta al sensor:\n'BLOCKED 192.168.0.100'\n'LIMITED 192.168.0.100'"]
        SUDO --> IPSET_CMD --> RESP
    end

    subgraph MANUAL_SSH["📋 scripts/enforce.sh — Control Manual"]
        direction TB
        ENF_CODE["#!/usr/bin/env bash\nIP=\$1  ACCION=\$2  TIMEOUT=\${3:-300}\n\nBLOCK:\n  sudo ipset add ppi_blocked \$IP timeout \$TIMEOUT -exist\n\nLIMIT:\n  sudo ipset add ppi_limited \$IP timeout \$TIMEOUT -exist\n\nUNBLOCK:\n  sudo ipset del ppi_blocked \$IP 2>/dev/null || true\n  sudo ipset del ppi_limited \$IP 2>/dev/null || true"]
        ENF_OUT["Salida real:\n2026-06-14 | BLOCK | 192.168.0.100 | timeout=300s\n2026-06-14 | UNBLOCK | 192.168.0.100"]
        ENF_CODE --> ENF_OUT
    end

    SENSOR -->|"SSH sin contraseña\n(clave desde F1)"| TUNNEL
    TUNNEL --> SERVIDOR_S
    MANUAL_SSH -.->|"uso manual\ndesde Desktop"| SERVIDOR_S

    style SENSOR     fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style TUNNEL     fill:#fafafa,stroke:#757575
    style SERVIDOR_S fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style MANUAL_SSH fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
```

---

## Diagrama 4 — Ciclo de Vida de un Bloqueo (Motor → Timeout)

```mermaid
sequenceDiagram
    participant MT  as motor_decision.py
    participant SSH as Canal SSH
    participant KN  as Kernel ipset
    participant IP  as iptables INPUT
    participant ATK as Kali 192.168.0.100
    participant SRV as nginx/sshd :120

    note over MT,SRV: T=0 — Ataque detectado

    MT->>MT: decidir(score=−0.72) → BLOCK
    MT->>SSH: bloquear_ip('192.168.0.100')
    SSH->>KN: sudo ipset add ppi_blocked 192.168.0.100 timeout 300
    KN-->>SSH: OK (countdown inicia: 300s)
    SSH-->>MT: "BLOCKED 192.168.0.100"
    MT->>MT: bloqueados.add('192.168.0.100')

    note over MT,SRV: T=1s — Kali sigue enviando paquetes

    ATK->>IP: SYN packet src=192.168.0.100
    IP->>KN: ¿192.168.0.100 ∈ ppi_blocked?
    KN-->>IP: SÍ (timeout=299s)
    IP->>ATK: DROP (sin respuesta)

    note over MT,SRV: T=10s — Nuevo flow del ataque

    MT->>MT: nuevo flow de 192.168.0.100
    MT->>MT: '192.168.0.100' ∈ bloqueados → 'ya bloqueado'
    note over MT: Sin SSH adicional — optimización

    note over MT,SRV: T=300s — Timeout automático

    KN->>KN: contador expira → elimina 192.168.0.100
    note over KN: Sin intervención del motor

    ATK->>IP: SYN packet (nuevo intento)
    IP->>KN: ¿192.168.0.100 ∈ ppi_blocked?
    KN-->>IP: NO (expirado)
    IP->>SRV: ACCEPT (paquete pasa)

    note over MT,SRV: T>300s — Si ataque continúa

    MT->>MT: nuevo flow de 192.168.0.100
    MT->>MT: score=−0.73 → BLOCK (modelo sigue detectando)
    MT->>SSH: bloquear_ip('192.168.0.100') otra vez
    note over MT: Re-bloqueo automático sin config manual
```

---

## Diagrama 5 — Telegram y Dashboard Web: Arquitectura SSE

```mermaid
flowchart TD

    MOTOR["motor_decision.py\ndetecta anomalía"]

    subgraph TG_PIPE["📱 Pipeline Telegram — Asíncrono"]
        direction TB
        TG_Q["_tg_queue\nQueue(maxsize=100)\nput_nowait() — no bloquea el loop"]
        TG_W["_tg_worker() — daemon thread\nConsume mensajes de la cola\nurllib.request.urlopen(timeout=10)"]
        TG_API["api.telegram.org\n/bot{TOKEN}/sendMessage\nchat_id=8512353253"]
        TG_PHONE["📱 Teléfono del operador\nrecibe en 300–800ms"]
        TG_Q --> TG_W --> TG_API --> TG_PHONE
    end

    subgraph TG_FORMAT["Formatos de alerta Telegram"]
        direction TB
        TG_BLK["🚨 PPI ALERTA — ANOMALÍA\nAccion : BLOCK\nIP     : 192.168.0.100\nProto  : TCP\nPuerto : 80\nScore  : −0.7214\nRazon  : pkt_rate:z=+45.2 | ...\nHora   : 2026-06-14 18:13:21"]
        TG_LIM["⚠️ PPI ALERTA — SOSPECHOSO\nAccion : LIMIT\nIP     : 192.168.0.100\nScore  : −0.5317\nHora   : 2026-06-14 18:13:13"]
        TG_BF["🔑 BRUTE FORCE SSH\nIP: 192.168.0.100\nintent: 15/60s → BLOCK"]
        TG_HTTP["🌐 HTTP ABUSE\nIP: 192.168.0.100\nreq: 100/30s → BLOCK"]
    end

    subgraph DASH_WEB["🖥️ Dashboard Web — http://192.168.0.110:8080"]
        direction TB
        FLASK["dashboard_web.py\nFlask + SSE (Server-Sent Events)\nppi-dashboard.service (systemd)"]

        subgraph SSE_FLOW["Arquitectura SSE"]
            direction LR
            LOG_R["log_reader\nmonitorea motor_decision.log\ncada ~150ms"]
            SSE_PUSH["push_sse(event)\nbrodcast a todos los clientes"]
            BROWSER["Navegador\nauto-refresca sin polling\nEventSource('/stream')"]
            LOG_R --> SSE_PUSH --> BROWSER
        end

        subgraph VISTAS["6 Vistas del Dashboard"]
            direction TB
            V1["🏠 Dashboard\nStats BLOCK/LIMIT/PERMIT\nNivel de riesgo\nGráficos Chart.js"]
            V2["🔔 Alertas\nFeed SSE tiempo real\nGrado · Tipo · Score\nBotón desbloquear"]
            V3["📋 Detecciones\nTabla filtrable BLOCK/LIMIT\nBúsqueda por IP\nExport CSV"]
            V4["📊 Análisis\nTimeline 24h\nDona de tipos\nMétricas IF"]
            V5["🛡️ Control ipset\nVer ppi_blocked/ppi_limited\nDesbloquear IPs\nBloqueo manual"]
            V6["⚙️ Sistema\nConfig IF · Lab\nExplicación SSE"]
        end

        FLASK --> SSE_FLOW
        FLASK --> VISTAS
    end

    subgraph DASH_TERM["📟 Dashboard Terminal"]
        direction TB
        DASH_PY["scripts/dashboard.py\nLee motor_decision.log\nActualiza cada 3s\n\n┌────────────────────────┐\n│ PPI Live Dashboard     │\n│ Flows:    1,432        │\n│ Anomalías:  892        │\n│ Bloqueados:   3        │\n│ Latencia: 34.5ms       │\n│ Última: 18:13:21 BLOCK │\n└────────────────────────┘"]
    end

    MOTOR -->|"_tg_queue.put_nowait()"| TG_Q
    MOTOR -->|"log.warning()"| LOG_R
    MOTOR -->|"motor_decision.log"| DASH_PY
    TG_PIPE --> TG_FORMAT

    TIMING["⚡ Tiempos de notificación:\nSSE dashboard: ~150ms (antes que Telegram)\nTelegram:       300–800ms (async)"]

    DASH_WEB --> TIMING
    TG_PIPE --> TIMING

    style TG_PIPE    fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    style TG_FORMAT  fill:#e3f2fd,stroke:#1565c0
    style DASH_WEB   fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style DASH_TERM  fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style TIMING     fill:#c8e6c9,stroke:#1b5e20
```

---

## Diagrama 6 — Inicialización del Sistema (boot del motor)

```mermaid
flowchart TD

    START["systemctl start ppi-motor.service"]

    subgraph BOOT_SEQ["Secuencia de arranque — inicializar_servidor()"]
        direction TB
        B1["load_model()\njoblib.load(isolation_forest.pkl)\njoblib.load(scaler.pkl)\nlog: τ1=−0.4973 · τ2=−0.6873"]

        B2["① SSH → servidor:\nipset create ppi_blocked hash:ip timeout 300\n2>/dev/null || true\n(idempotente — no falla si ya existe)"]

        B3["② SSH → servidor:\nipset create ppi_limited hash:ip timeout 300\n2>/dev/null || true"]

        B4["③ SSH → servidor:\niptables -C INPUT -m set --match-set ppi_blocked src -j DROP\n→ si NO existe: iptables -I INPUT ... -j DROP\n→ si YA existe: no hace nada (idempotente)"]

        B5["④ SSH → servidor:\niptables -C INPUT 2 -m set ppi_limited hashlimit ...\n→ si NO existe: iptables -I INPUT 2 ... -j DROP\n→ si YA existe: no hace nada"]

        B6["⑤ threading.Thread(target=_tg_worker, daemon=True)\nInicia cola Telegram async"]

        B7["⑥ log.info('Servidor init: OK')\nlog.info('Monitoreando /var/log/suricata/eve.json ...')\n\nLoop principal: seguir_eve() inicia"]

        B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7
    end

    subgraph LOG_BOOT["Log de arranque real"]
        direction TB
        LB["2026-06-14 19:42:19 | INFO | ============================================================\n2026-06-14 19:42:19 | INFO | Motor de decisión PPI — iniciando\n2026-06-14 19:42:19 | INFO | ============================================================\n2026-06-14 19:42:21 | INFO | Modelo cargado | umbral_base=−0.5481 | τ1=−0.4973 | τ2=−0.6873\n2026-06-14 19:42:21 | INFO | Brute Force SSH: ventana=60s umbral_limit=5 umbral_block=15\n2026-06-14 19:42:21 | INFO | HTTP Abuse: ventana=30s umbral_limit=50 umbral_block=100\n2026-06-14 19:42:21 | INFO | Servidor init: OK | BLOCK=ipset+DROP | LIMIT=ipset+hashlimit(100pkt/s)\n2026-06-14 19:42:21 | INFO | Monitoreando /var/log/suricata/eve.json ..."]
    end

    subgraph RECOVERY["Recuperación automática — Restart=on-failure"]
        direction LR
        CRASH["Motor cae\n(excepción no capturada\no kill accidental)"]
        SYSTEMD_R["systemd espera 10s\n(RestartSec=10)"]
        REBOOT["Reinicia motor\nbootstrap de nuevo:\n- Recarga modelos\n- Reconfigura ipsets\n- Retoma eve.json"]
        CRASH --> SYSTEMD_R --> REBOOT
    end

    START --> BOOT_SEQ
    BOOT_SEQ --> LOG_BOOT
    BOOT_SEQ --> RECOVERY

    style BOOT_SEQ  fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style LOG_BOOT  fill:#fafafa,stroke:#757575
    style RECOVERY  fill:#fff3e0,stroke:#e65100
```

---

## Diagrama 7 — Pruebas Live y Evidencia de Control Inline

```mermaid
flowchart TD

    subgraph PRUEBAS["✅ Pruebas validadas en sesión 2026-06-14/15"]
        direction TB

        subgraph T_LIMIT["LIMIT validado"]
            direction LR
            TL1["B6 Hydra SSH (7 intentos)\n→ ssh_intentos[.100]=7 en 60s\n→ n=7 ≥ 5 → LIMIT a los 42s\nVerificado:\nipset list ppi_limited\n→ 192.168.0.100  timeout 245"]
            TL2["B2 Port Scan nmap -sS\n→ score=−0.6260 (BAJA)\n→ LIMIT por modelo\nLog: SOSPECHOSO score=-0.6260"]
            TL3["B5 Acceso repetitivo 55 curl\n→ score=−0.5117 (BAJA)\n→ LIMIT por modelo\nLog: SOSPECHOSO score=-0.5117"]
        end

        subgraph T_BLOCK["BLOCK validado"]
            direction LR
            TB1["B1 SYN Flood\n→ score=−0.72 → BLOCK\nLog: ANOMALÍA score=-0.7214\nKali en ppi_blocked 300s"]
            TB2["B3 UDP Flood\n→ score=−0.81 → BLOCK\nLog: ANOMALÍA score=-0.8100"]
            TB3["B4 ICMP Flood\n→ score=−0.78 → BLOCK\nLog: ANOMALÍA score=-0.7800"]
            TB4["B5 HTTP Abuse escalado\n→ 100 req/30s → BLOCK heurística\nLog: HTTP-ABUSE requests=100/30s"]
        end

        subgraph T_FP["Falsos Positivos — 0 encontrados"]
            TFP["grep 'SOSPECHOSO|ANOMALÍA' motor_decision.log\n| grep '2026-06-1[45]'\n| grep -v '192.168.0.100'\n\n→ 0 resultados\n✅ Ningún flow legítimo disparó LIMIT/BLOCK"]
        end

        subgraph T_TIMEOUT["Timeout automático validado"]
            TTO["Después de 300s:\nKali puede volver a conectar\nMotor re-detecta y re-bloquea\nautomáticamente (score persiste)"]
        end
    end

    subgraph UMBRALES_DOC["📄 results/umbrales_finales.txt — Documento formal"]
        direction TB
        UD1["ISOLATION FOREST — Umbral base\n  clf.offset_ = −0.5481\n  n_estimators = 300  random_state = 42"]
        UD2["UMBRALES τ1/τ2 (curva ROC — AUC=0.9440)\n  τ1 = −0.4973  PERMIT/LIMIT  (Youden: TPR=91% FPR=9.5%)\n  τ2 = −0.6873  LIMIT/BLOCK   (FPR≤2%:  TPR=40.6%)"]
        UD3["DETECTORES HEURÍSTICOS\n  Brute Force SSH: LIMIT=5/60s · BLOCK=15/60s\n  HTTP Abuse:      LIMIT=50/30s · BLOCK=100/30s\n  Timeout bloqueos: 300s (kernel ipset)"]
        UD1 --> UD2 --> UD3
    end

    PRUEBAS --> UMBRALES_DOC

    F6_CONN(["→ F6: Validación\nSistema completo operativo\n40 corridas controladas:\n- TIE=100% (detección en tiempo)\n- ITL=0%   (sin falsos positivos)\n- Lead Time=26s promedio\n- Disponibilidad=100%"])
    UMBRALES_DOC ==>|"sistema listo\npara validación"| F6_CONN

    style PRUEBAS   fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style T_LIMIT   fill:#fff3e0,stroke:#e65100
    style T_BLOCK   fill:#fce4ec,stroke:#c62828
    style T_FP      fill:#c8e6c9,stroke:#1b5e20
    style T_TIMEOUT fill:#e3f2fd,stroke:#1565c0
    style UMBRALES_DOC fill:#fffde7,stroke:#f9a825
    style F6_CONN   fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Resumen de componentes F5

| Componente | Ubicación | Rol |
|---|---|---|
| `motor_decision.py` | Sensor :110 | Toma la decisión e invoca SSH |
| `_ssh(cmd)` | Sensor :110 | Canal subprocess SSH al servidor |
| `bloquear_ip()` / `limitar_ip()` | Sensor :110 | Funciones de control remoto |
| `inicializar_servidor()` | Sensor :110 | Boot idempotente de ipsets/iptables |
| `ppi_blocked` (ipset) | Servidor :120 | Hash:ip con timeout 300s → DROP |
| `ppi_limited` (ipset) | Servidor :120 | Hash:ip con timeout 300s → hashlimit |
| iptables INPUT regla 1 | Servidor :120 | DROP match-set ppi_blocked |
| iptables INPUT regla 2 | Servidor :120 | hashlimit 100/s ppi_limited |
| `enforce.sh` | Sensor :110 | Control manual BLOCK/LIMIT/UNBLOCK |
| `dashboard_web.py` | Sensor :110 | Flask+SSE en :8080 |
| `dashboard.py` | Sensor :110 | Dashboard terminal cada 3s |
| `ppi-motor.service` | Sensor :110 | systemd gestiona el proceso |
| `ppi-dashboard.service` | Sensor :110 | systemd para Flask web |
| Telegram Bot | Cloud | Notificación async 🚨⚠️🔑🌐 |
