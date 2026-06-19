# F4 — Flujo del Motor de Decisión en Tiempo Real

**Fase 4 · PPI — Universidad Peruana Unión · 2026**
Archivo: `scripts/motor_decision.py` · Servicio: `ppi-motor.service`

---

## Diagrama 1 — Arquitectura general (entradas → motor → salidas)

```mermaid
flowchart LR
    classDef archivo  fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef modelo   fill:#FEF9C3,stroke:#CA8A04,color:#713F12
    classDef proceso  fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef bloqueo  fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
    classDef limite   fill:#FED7AA,stroke:#EA580C,color:#7C2D12
    classDef ok       fill:#BBF7D0,stroke:#16A34A,color:#14532D
    classDef salida   fill:#EDE9FE,stroke:#7C3AED,color:#3B0764
    classDef servicio fill:#F0F9FF,stroke:#0284C7,color:#0C4A6E

    %% ══ ENTRADAS EN ARRANQUE ════════════════════════════════════
    subgraph ENT["📥 Entradas — se cargan al iniciar el servicio"]
        direction TB
        IF_PKL[("📦 isolation_forest.pkl\nn_estimators=300\nsklearn 1.9.0")]:::modelo
        SC_PKL[("📦 scaler.pkl\nStandardScaler\n14 features")]:::modelo
        MET[("📄 metricas_offline.txt\nτ1 = −0.4459\nτ2 = −0.6027")]:::archivo
        WL[("🛡️ Whitelist\n.1 · .20 · .110\n.120 · .130 · .140")]:::archivo
    end

    %% ══ STREAM EN VIVO ══════════════════════════════════════════
    subgraph STREAM["📜 Stream en vivo — Suricata 7.0.3"]
        EVE[("📜 eve.json\n/var/log/suricata/\nactualización continua")]:::archivo
    end

    %% ══ MOTOR ═══════════════════════════════════════════════════
    subgraph MOTOR["⚙️  ppi-motor.service  ·  motor_decision.py"]
        direction TB
        P1["👁️ tail -F eve.json\npolling 100 ms"]:::proceso
        P2["🔍 Filtrar eventos\ntype = flow · IPv4 · pkts > 0"]:::proceso
        P3["🛡️ Verificar whitelist\n¿src_ip exento?"]:::proceso
        P4["🔎 Heurísticas\nSSH BF · HTTP Abuse"]:::proceso
        P5["⚙️ Extraer 14 features\npkts · bytes · duración · ratios · proto · puerto"]:::proceso
        P6["📊 StandardScaler\n.transform(X)"]:::proceso
        P7["🌲 Isolation Forest\n.score_samples(X_scaled)\nscore ∈ (−1, 0)"]:::proceso
        P8["📐 Decisor τ1 / τ2\nPERMIT · LIMIT · BLOCK"]:::proceso
        P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8
    end

    %% ══ ENFORCEMENT ═════════════════════════════════════════════
    subgraph ENF["🔥 Enforcement · Servidor 192.168.0.120"]
        direction TB
        BLK["⛔ ipset ppi_blocked\niptables DROP\ntimeout 300 s"]:::bloqueo
        LIM["⚠️ ipset ppi_limited\nhashlimit 100 pkt/s\ntimeout 300 s"]:::limite
    end

    %% ══ SALIDAS ══════════════════════════════════════════════════
    subgraph SAL["📤 Salidas y notificaciones"]
        direction TB
        LOG[("📝 motor_decision.log\nresults/")]:::salida
        TG["📱 Telegram\nalerta · dedup 300 s / IP"]:::salida
        WEB["🖥️ Dashboard Web\n:8080 · SSE → browser"]:::salida
    end

    ENT    --> MOTOR
    STREAM --> MOTOR
    MOTOR  --> ENF
    MOTOR  --> SAL
```

---

## Diagrama 2 — Flujo de decisión por flow (lógica interna detallada)

```mermaid
flowchart TD
    classDef archivo  fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef proceso  fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef decision fill:#FEF9C3,stroke:#CA8A04,color:#713F12
    classDef ok       fill:#BBF7D0,stroke:#16A34A,color:#14532D
    classDef limite   fill:#FED7AA,stroke:#EA580C,color:#7C2D12
    classDef bloqueo  fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
    classDef salida   fill:#EDE9FE,stroke:#7C3AED,color:#3B0764
    classDef heur     fill:#F3E8FF,stroke:#7C3AED,color:#3B0764

    %% ── ENTRADA ────────────────────────────────────────────────
    EVE[("📜 eve.json\nSuricata — live stream")]:::archivo
    EVE --> TAIL

    TAIL["👁️ tail -F eve.json\nnueva línea disponible\npolling 100 ms"]:::proceso
    TAIL --> IS_FLOW

    IS_FLOW{"🔍 ¿type = 'flow'?\n¿src_ip = IPv4?\n¿pkts_toserver > 0?"}:::decision
    IS_FLOW -->|"❌ No cumple"| TAIL
    IS_FLOW -->|"✅ Sí"| META

    META["📋 Extraer metadatos\nsrc_ip · dest_ip · dest_port · proto"]:::proceso
    META --> WHITE

    %% ── WHITELIST ───────────────────────────────────────────────
    WHITE{"🛡️ ¿src_ip\nen whitelist?"}:::decision
    WHITE -->|"✅ Sí — IP interna"| P_WHITE["✅ PERMIT\nwhitelisted · sin evaluar"]:::ok
    WHITE -->|"❌ No"| BF

    P_WHITE --> LOG

    %% ── HEURÍSTICA SSH BF ───────────────────────────────────────
    subgraph H_SSH["🔑 Detector SSH Brute Force  (ventana 60 s)"]
        BF{"dest_port = 22?\ncontar intentos / IP"}:::decision
        BF -->|"n ≥ 15"| BLK_SSH["⛔ BLOCK\nBF-SSH"]:::bloqueo
        BF -->|"5 ≤ n < 15"| LIM_SSH["⚠️ LIMIT\nBF-SSH"]:::limite
        BF -->|"n < 5 → continúa"| HTTP
    end

    %% ── HEURÍSTICA HTTP ABUSE ───────────────────────────────────
    subgraph H_HTTP["🌐 Detector HTTP Abuse  (ventana 30 s)"]
        HTTP{"dest_port = 80?\ncontar req / IP"}:::decision
        HTTP -->|"n ≥ 100"| BLK_HTTP["⛔ BLOCK\nHTTP Abuse"]:::bloqueo
        HTTP -->|"50 ≤ n < 100"| LIM_HTTP["⚠️ LIMIT\nHTTP Abuse"]:::limite
        HTTP -->|"n < 50 → continúa"| FEAT
    end

    %% ── ISOLATION FOREST ────────────────────────────────────────
    FEAT["⚙️ Extraer 14 features\n─────────────────────\npkts_toserver · pkts_toclient\nbytes_toserver · bytes_toclient\nduration · pkt_rate · byte_rate\npkt_ratio · byte_ratio · avg_pkt_size\nis_tcp · is_udp · is_icmp · dest_port"]:::proceso
    FEAT --> SCALE

    SCALE["📊 StandardScaler.transform()\nnormaliza a μ=0 · σ=1\n(ajustado sobre 53,708 flows Grupo A)"]:::proceso
    SCALE --> AVISO

    AVISO{"👀 Tendencia anómala?\nscore_medio < −0.35\nsobre últimos 10 flows de esta IP"}:::decision
    AVISO -->|"Sí → 📱 pre-alerta"| IF_SC
    AVISO -->|"No"| IF_SC

    IF_SC["🌲 Isolation Forest\n.score_samples(X_scaled)\nn_estimators=300 · sklearn 1.9.0\nscore ∈ (−1.0 · · · 0.0)"]:::proceso
    IF_SC --> TAU

    %% ── DECISOR ─────────────────────────────────────────────────
    TAU{"📐 ¿Dónde cae el score?"}:::decision

    TAU -->|"score > −0.4459\nsobre τ1 — normal"| PERMIT["✅ PERMIT\nsin restricción\n(log DEBUG)"]:::ok

    TAU -->|"−0.6027 < score ≤ −0.4459\nentre τ2 y τ1 — sospechoso"| LIMIT["⚠️ LIMIT\nipset ppi_limited\nhashlimit 100 pkt/s\ntimeout 300 s"]:::limite

    TAU -->|"score ≤ −0.6027\nbajo τ2 — anómalo"| BLOCK["⛔ BLOCK · DROP\nipset ppi_blocked\ntimeout 300 s"]:::bloqueo

    %% ── SALIDAS ─────────────────────────────────────────────────
    LOG[("📝 motor_decision.log\ntimestamp · tipo · src · dst\nscore · grado · acción")]:::salida

    PERMIT  --> LOG
    LIMIT   --> LOG
    BLOCK   --> LOG
    BLK_SSH --> LOG
    LIM_SSH --> LOG
    BLK_HTTP--> LOG
    LIM_HTTP--> LOG

    BLOCK   --> TG["📱 Telegram\nalerta BLOCK\n(dedup 300 s/IP)"]:::salida
    LIMIT   --> TG
    BLK_SSH --> TG
    BLK_HTTP--> TG

    LOG --> DASH["🖥️ Dashboard Web\nSSE · browser :8080"]:::salida
    LOG --> TAIL
```

---

## Diagrama 3 — Escala de score y zonas de decisión

```
  score ∈  (−1.0) ────────────────────────────────── (0.0)
            │                    │             │
          −0.80    ⛔ BLOCK     −0.6027  ⚠️ LIMIT  −0.4459   ✅ PERMIT
                   DROP          τ2 ──────────── τ1          normal
                                 hashlimit 100 pkt/s
```

| Zona | Rango | Acción | Criterio derivación |
|---|---|---|---|
| ✅ **PERMIT** | score > −0.4459 | Sin restricción | τ1 = índice de Youden (max TPR−FPR) |
| ⚠️ **LIMIT** | −0.6027 < score ≤ −0.4459 | hashlimit 100 pkt/s · timeout 300 s | τ2 = FPR ≤ 2 % en tráfico normal |
| ⛔ **BLOCK** | score ≤ −0.6027 | iptables DROP · timeout 300 s | Bajo τ2 |

---

## Tabla de componentes

| Componente | Tipo | Ruta / Nodo | Descripción |
|---|---|---|---|
| `eve.json` | 📜 Stream | `/var/log/suricata/` · Sensor .110 | Eventos de red en tiempo real — Suricata 7.0.3 |
| `isolation_forest.pkl` | 📦 Modelo | `models/` · Sensor .110 | IF n=300, entrenado sobre 53,708 flows normales |
| `scaler.pkl` | 📦 Modelo | `models/` · Sensor .110 | StandardScaler ajustado sobre Grupo A |
| `metricas_offline.txt` | 📄 Config | `results/` · Sensor .110 | τ1=−0.4459 · τ2=−0.6027 (leídos en arranque) |
| `motor_decision.py` | ⚙️ Script | `scripts/` · Sensor .110 | Bucle principal: tail → features → score → decisión |
| `ppi-motor.service` | 🔧 Servicio | systemd · Sensor .110 | Restart=on-failure · Requires=suricata.service |
| `WHITELIST` | 🛡️ Constante | motor_decision.py | IPs internas exentas de evaluación |
| Detector SSH BF | 🔎 Heurística | motor_decision.py | Ventana 60 s · ≥5→LIMIT · ≥15→BLOCK |
| Detector HTTP Abuse | 🔎 Heurística | motor_decision.py | Ventana 30 s · ≥50→LIMIT · ≥100→BLOCK |
| `ipset ppi_blocked` | 🔥 Kernel | Servidor .120 | hash:ip · timeout 300 s · iptables DROP |
| `ipset ppi_limited` | 🔥 Kernel | Servidor .120 | hash:ip · timeout 300 s · hashlimit 100 pkt/s |
| `motor_decision.log` | 📝 Log | `results/` · Sensor .110 | Registro de cada decisión con score y features |
| Telegram Bot | 📱 Alerta | relay :8889 → api.telegram.org | Alertas BLOCK/LIMIT · dedup 300 s por IP |
| `dashboard_web.py` | 🖥️ Web | `:8080` · Sensor .110 | Dashboard en tiempo real vía SSE |

---

## Constantes clave

| Constante | Valor | Descripción |
|---|---|---|
| `TAU1` | −0.4459 | Umbral PERMIT/LIMIT — índice de Youden |
| `TAU2` | −0.6027 | Umbral LIMIT/BLOCK — FPR ≤ 2 % |
| `TAU_AVISO` | −0.35 | Score medio de pre-alerta de tendencia |
| `AVISO_MIN_FL` | 10 | Flows mínimos para activar pre-alerta |
| `TIMEOUT_SEC` | 300 | Duración del bloqueo/límite en ipset |
| `BF_VENTANA_SEG` | 60 | Ventana SSH Brute Force |
| `BF_UMBRAL_LIMIT` | 5 | Intentos SSH → LIMIT |
| `BF_UMBRAL_BLOCK` | 15 | Intentos SSH → BLOCK |
| `HTTP_VENTANA_SEG` | 30 | Ventana HTTP Abuse |
| `HTTP_UMBRAL_LIMIT` | 50 | Requests HTTP → LIMIT |
| `HTTP_UMBRAL_BLOCK` | 100 | Requests HTTP → BLOCK |
| `TG_DEDUP_SEG` | 300 | Supresión de alertas duplicadas por IP |

---

*Fase 4 completada y validada · sklearn 1.9.0 · Suricata 7.0.3 · 2026-06-16*
