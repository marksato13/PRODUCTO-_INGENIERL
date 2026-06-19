# Diagramas de Flujo — Fase 4 y Fase 6

**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Aprendizaje Automático y un Mecanismo de Control en Tiempo Real**
Universidad Peruana Unión · Junio 2026

---

## Fase 4 — Motor de Decisión (`motor_decision.py`)

El motor es el núcleo del sistema: consume el stream en vivo de Suricata, aplica el modelo y emite decisiones de control en tiempo real. Combina dos tipos de detección: **heurística** (contadores de eventos por IP) y **ML** (score Isolation Forest).

---

### Diagrama 4.1 — Arquitectura general (Entradas → Motor → Salidas)

```mermaid
flowchart LR
    classDef archivo  fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef proceso  fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef salida   fill:#EDE9FE,stroke:#7C3AED,color:#3B0764
    classDef accion   fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D

    subgraph ARRANQUE["⚡ Arranque del servicio"]
        direction TB
        IF_PKL[("📦 isolation_forest.pkl\n• n_estimators=300\n• sklearn 1.9.0")]:::archivo
        SC_PKL[("📦 scaler.pkl\n• StandardScaler\n• 14 features")]:::archivo
        MET[("📄 metricas_offline.txt\n• τ1 = −0.4459\n• τ2 = −0.6027")]:::archivo
    end

    subgraph LIVE["🔄 Stream en vivo"]
        direction TB
        EVE[("📜 eve.json\n• Suricata 7.0.3\n• /var/log/suricata/\n• tail -F")]:::archivo
    end

    subgraph MOTOR["⚙️  motor_decision.py  |  ppi-motor.service"]
        direction TB
        M1["👁️ Listener\ntail -F eve.json"]:::proceso
        M2["🔍 Parser JSON\nfiltrar type = flow"]:::proceso
        M3["🛡️ Whitelist\n192.168.0.20 · .110 · .120"]:::proceso
        M4["🔎 Heurísticas\nSSH BF · HTTP Abuse"]:::proceso
        M5["⚙️ Feature Engineering\n14 features por flow"]:::proceso
        M6["📊 StandardScaler\n.transform()"]:::proceso
        M7["🌲 Isolation Forest\n.score_samples()"]:::proceso
        M8["📐 Decisor\nscore vs τ1 / τ2"]:::proceso
        M1 --> M2 --> M3 --> M4 --> M5 --> M6 --> M7 --> M8
    end

    subgraph ENFORCEMENT["🔥 Enforcement en Servidor 192.168.0.120"]
        direction TB
        IP_BLK["⛔ ipset ppi_blocked\niptables DROP"]:::accion
        IP_LIM["⚠️ ipset ppi_limited\nhashlimit 100 pkt/s"]:::accion
    end

    subgraph SALIDAS["📤 Salidas y notificaciones"]
        direction TB
        LOG[("📝 motor_decision.log\nresults/")]:::salida
        TG["📱 Telegram Bot\nalerta dedup 300 s"]:::salida
        DASH["🖥️ Dashboard Web\n:8080 SSE → browser"]:::salida
    end

    ARRANQUE --> MOTOR
    LIVE     --> MOTOR
    MOTOR    --> ENFORCEMENT
    MOTOR    --> SALIDAS
```

---

### Diagrama 4.2 — Flujo de decisión por flow (lógica interna)

```mermaid
flowchart TD
    classDef decision fill:#FEF9C3,stroke:#CA8A04,color:#713F12
    classDef proceso  fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef archivo  fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef permit   fill:#BBF7D0,stroke:#16A34A,color:#14532D
    classDef limit    fill:#FED7AA,stroke:#EA580C,color:#7C2D12
    classDef block    fill:#FECACA,stroke:#DC2626,color:#7F1D1D
    classDef salida   fill:#EDE9FE,stroke:#7C3AED,color:#3B0764

    %% ── ENTRADA ──────────────────────────────────────────────
    EVE[("📜 eve.json — Suricata live")]:::archivo
    EVE --> TAIL

    TAIL["👁️ tail -F eve.json\nnueva línea disponible"]:::proceso
    TAIL --> FTYPE

    FTYPE{"🔍 ¿type = 'flow'?"}:::decision
    FTYPE -->|"❌  alert / dns / tls...  "| TAIL
    FTYPE -->|"✅  flow"| EXTRACT_META

    %% ── METADATOS ────────────────────────────────────────────
    EXTRACT_META["📋 Extraer metadatos\nsrc_ip · dest_ip · dest_port · proto"]:::proceso
    EXTRACT_META --> WCHECK

    %% ── WHITELIST ────────────────────────────────────────────
    WCHECK{"🛡️ ¿src_ip en whitelist?\n.1 · .20 · .110 · .120 · .130 · .140"}:::decision
    WCHECK -->|"✅ Sí"| PERMIT_W

    PERMIT_W["✅ PERMIT — whitelisted\n(sin evaluación IF)"]:::permit
    PERMIT_W --> LOG

    %% ── HEURÍSTICA SSH BF ─────────────────────────────────────
    WCHECK -->|"❌ No"| SSH_CHK

    SSH_CHK{"🔑 ¿dest_port = 22?\ncontar intentos / 60 s"}:::decision
    SSH_CHK -->|"n ≥ 15\n→ BLOCK"| BLK_SSH
    SSH_CHK -->|"5 ≤ n < 15\n→ LIMIT"| LIM_SSH
    SSH_CHK -->|"n < 5\n→ siguiente"| HTTP_CHK

    BLK_SSH["⛔ BLOCK — BF-SSH\nipset ppi_blocked"]:::block
    LIM_SSH["⚠️ LIMIT — BF-SSH\nipset ppi_limited"]:::limit

    %% ── HEURÍSTICA HTTP ABUSE ─────────────────────────────────
    HTTP_CHK{"🌐 ¿dest_port = 80?\ncontar req / 30 s"}:::decision
    HTTP_CHK -->|"n ≥ 100\n→ BLOCK"| BLK_HTTP
    HTTP_CHK -->|"50 ≤ n < 100\n→ LIMIT"| LIM_HTTP
    HTTP_CHK -->|"n < 50\n→ siguiente"| FEAT

    BLK_HTTP["⛔ BLOCK — HTTP Abuse\nipset ppi_blocked"]:::block
    LIM_HTTP["⚠️ LIMIT — HTTP Abuse\nipset ppi_limited"]:::limit

    %% ── ISOLATION FOREST ──────────────────────────────────────
    FEAT["⚙️ Extraer 14 features\npkts · bytes · duration\npkt_rate · byte_rate\npkt_ratio · byte_ratio\navg_pkt_size · is_tcp · is_udp · is_icmp · dest_port"]:::proceso
    FEAT --> SCALE

    SCALE["📊 StandardScaler.transform()\nnormalizar a μ=0 σ=1"]:::proceso
    SCALE --> AVISO

    AVISO{"👀 ¿Tendencia anómala?\nscore_medio < −0.35\n(últimos 10 flows de esa IP)"}:::decision
    AVISO -->|"Sí → 📱 pre-alerta Telegram"| IF_SCORE
    AVISO -->|"No"| IF_SCORE

    IF_SCORE["🌲 Isolation Forest\n.score_samples(X)\nscore ∈ (−1.0 · · · 0.0)"]:::proceso
    IF_SCORE --> TAU

    %% ── DECISOR τ1 / τ2 ──────────────────────────────────────
    TAU{"📐 Comparar score\nvs τ1 y τ2"}:::decision
    TAU -->|"score > −0.4459\n(sobre τ1 — normal)"| PERMIT_IF
    TAU -->|"−0.6027 < score ≤ −0.4459\n(entre τ2 y τ1 — sospechoso)"| LIMIT_IF
    TAU -->|"score ≤ −0.6027\n(bajo τ2 — anómalo)"| BLOCK_IF

    PERMIT_IF["✅ PERMIT\nflujo normal — sin acción"]:::permit
    LIMIT_IF["⚠️ LIMIT\n100 pkt/s · timeout 300 s\nipset ppi_limited"]:::limit
    BLOCK_IF["⛔ BLOCK  DROP\ntimeout 300 s\nipset ppi_blocked"]:::block

    %% ── SALIDAS COMUNES ───────────────────────────────────────
    LOG[("📝 motor_decision.log\nts · tipo · src · dst · score · grado · acción")]:::salida

    PERMIT_IF --> LOG
    LIMIT_IF  --> LOG
    BLOCK_IF  --> LOG
    BLK_SSH   --> LOG
    LIM_SSH   --> LOG
    BLK_HTTP  --> LOG
    LIM_HTTP  --> LOG

    LOG --> TG["📱 Telegram\nalerta (dedup 300 s / IP)"]:::salida
    LOG --> DASH["🖥️ Dashboard Web\nSSE → browser :8080"]:::salida
    LOG --> TAIL
```

---

### Tabla de componentes — Fase 4

| Componente | Tipo | Ruta / Dirección | Descripción |
|---|---|---|---|
| `eve.json` | 📜 Stream | `/var/log/suricata/eve.json` | Eventos de red en tiempo real — Suricata 7.0.3 |
| `isolation_forest.pkl` | 📦 Modelo | `models/` | Isolation Forest n=300, sklearn 1.9.0 |
| `scaler.pkl` | 📦 Modelo | `models/` | StandardScaler ajustado sobre 53,708 flows Grupo A |
| `metricas_offline.txt` | 📄 Config | `results/` | τ1=−0.4459 (Youden) · τ2=−0.6027 (FPR≤2%) |
| `motor_decision.py` | ⚙️ Proceso | `scripts/` | Bucle principal: tail → features → IF → decisión |
| `ppi-motor.service` | 🔧 Servicio | systemd sensor | Mantiene el motor activo y lo reinicia si cae |
| `ipset ppi_blocked` | 🔥 Kernel | 192.168.0.120 | Set netfilter para DROP (BLOCK) |
| `ipset ppi_limited` | 🔥 Kernel | 192.168.0.120 | Set netfilter para hashlimit 100 pkt/s (LIMIT) |
| `motor_decision.log` | 📝 Log | `results/` | Registro de cada decisión con score y features |
| `Telegram Bot` | 📱 Alerta | relay :8889 → api.telegram.org | Alertas de BLOCK/LIMIT con dedup 300 s por IP |
| `dashboard_web.py` | 🖥️ Web | `:8080 SSE` | Dashboard en tiempo real vía Server-Sent Events |

---

### Umbrales del decisor

```
score ∈ (−1.0) ──────────────────────────────────────── (0.0)
          │                   │              │
         ─0.8    BLOCK       ─0.6027   LIMIT   ─0.4459   PERMIT
                ⛔ DROP        τ2 ───────────── τ1        ✅ ok
                              ⚠️ 100 pkt/s
```

| Zona | Rango de score | Acción | Criterio de derivación |
|---|---|---|---|
| **PERMIT** | score > −0.4459 | Sin restricción | τ1 = índice de Youden (TPR − FPR máximo) |
| **LIMIT** | −0.6027 < score ≤ −0.4459 | hashlimit 100 pkt/s · timeout 300 s | τ2 = FPR ≤ 2% en tráfico normal |
| **BLOCK** | score ≤ −0.6027 | iptables DROP · timeout 300 s | Bajo τ2 |

---

## Fase 6 — Validación (40 corridas)

La Fase 6 ejecuta el motor en operación continua durante 40 corridas independientes, cubriendo los 13 escenarios definidos. Cada corrida sigue un protocolo fijo: preparar → generar tráfico → exportar → registrar → analizar.

---

### Diagrama 6.1 — Pipeline completo de validación

```mermaid
flowchart TD
    classDef config   fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef script   fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef trafico  fill:#FEF9C3,stroke:#CA8A04,color:#713F12
    classDef sensor   fill:#F3E8FF,stroke:#7C3AED,color:#3B0764
    classDef output   fill:#FCE7F3,stroke:#DB2777,color:#831843
    classDef analisis fill:#ECFDF5,stroke:#059669,color:#065F46

    START(["▶️ Inicio F6\nf6_corridas.py"]):::config

    START --> PREP

    subgraph PREP["🔧 Preparación (antes de cada corrida)"]
        direction LR
        P1["🗑️ ipset flush\nppi_blocked · ppi_limited"]:::script
        P2["🔄 systemctl restart\nppi-motor.service"]:::script
        P3["✅ Verificar motor\ntail log 3 s"]:::script
        P1 --> P2 --> P3
    end

    PREP --> GRUPO

    subgraph GRUPO["📋 Selección de escenario"]
        direction LR
        GA["🟢 Grupo A\nNormal\nDesktop .20\nA1·A2·A3·A4"]:::trafico
        GB["🔴 Grupo B\nAnómalo\nKali .100\nB1·B2·B3·B4·B5·B6"]:::trafico
        GC["🟠 Grupo C\nMixto\nDesktop + Kali\nC1·C2·C3"]:::trafico
    end

    GRUPO --> TRAFICO

    subgraph TRAFICO["🚦 Generación de tráfico (300 s)"]
        direction TB
        T_NORMAL["🟢 curl · wget · ssh · scp\n→ nginx :80 · SSH :22"]:::trafico
        T_ANOM["🔴 hping3 · nmap · hydra\n→ SYN flood · port scan · brute force"]:::trafico
        T_MIXTO["🟠 ambos simultáneos\nnormal ∥ anómalo"]:::trafico
    end

    subgraph SURICATA["📡 Sensor 192.168.0.110 — Suricata 7.0.3"]
        direction TB
        SUR["🔍 Inspección ens35\ncaptura todos los flows"]:::sensor
        EVE_LIVE[("📜 /var/log/suricata/eve.json\nactualización en tiempo real")]:::sensor
    end

    subgraph MOTOR_RT["⚙️ Motor en tiempo real (paralelo al tráfico)"]
        direction TB
        MT["motor_decision.py\ntail -F eve.json\n→ score IF → PERMIT/LIMIT/BLOCK"]:::script
        LOG_RT[("📝 motor_decision.log\nupdated en tiempo real")]:::script
        MT --> LOG_RT
    end

    TRAFICO --> SURICATA
    SURICATA --> MOTOR_RT

    MOTOR_RT --> FIN_COR

    subgraph FIN_COR["📦 Fin de corrida — exportar y registrar"]
        direction LR
        EXP["📤 exportar_eve_por_escenario.sh\ngzip eve.json → data/raw/\ntruncate + reopen-log-files"]:::script
        BIT["📋 registrar_bitacora.sh\nescribe línea en\nbitacora_escenarios.txt"]:::script
        WAIT["⏱️ Esperar 60 s\nentre corridas"]:::script
        EXP --> BIT --> WAIT
    end

    FIN_COR --> NEXT

    NEXT{"🔢 ¿Corridas\ncompletadas?"}
    NEXT -->|"< 40\n→ siguiente"| PREP
    NEXT -->|"= 40\n→ analizar"| ANALISIS

    subgraph ANALISIS["📊 Análisis post-validación"]
        direction TB
        F6["⚙️ f6_corridas.py\ncalcula métricas por corrida"]:::analisis
        AUC["⚙️ auc_por_escenario.py\nAUC-ROC desglosado"]:::analisis
        CSV_OUT[("📊 resultados_f6_completo.csv\n40 filas · FPR · ITL · latencia\nlead_time · TIE · MTTA · MTTC")]:::output
        GRAF[("📈 graficas_f6/\n7 figuras PNG 300 DPI")]:::output
        BIT_OUT[("📋 bitacora_escenarios.txt\nregistro cronológico")]:::output
        RAW[("🗜️ data/raw/\n47 archivos .json.gz\nYYYYMMDD_grupo_esc_NN")]:::output
        F6 --> CSV_OUT
        F6 --> GRAF
        AUC --> GRAF
    end

    ANALISIS --> END_(["✅ F6 completada\n40/40 corridas validadas"])
```

---

### Diagrama 6.2 — Detalle de una corrida individual

```mermaid
sequenceDiagram
    actor Script as 🖥️ Desktop<br/>f6_corridas.py
    participant Kali as 🔴 Kali<br/>192.168.0.100
    participant Sur as 📡 Sensor<br/>Suricata 7.0.3
    participant Motor as ⚙️ Motor<br/>motor_decision.py
    participant Server as 🖧 Servidor<br/>192.168.0.120
    participant TG as 📱 Telegram

    Script->>Sur: 🗑️ flush ipset ppi_blocked / ppi_limited
    Script->>Sur: 🔄 systemctl restart ppi-motor.service
    Script->>Sur: ✅ verificar motor activo (tail log)

    Note over Script,TG: ─── Inicio corrida N (duración 300 s) ───

    Script->>Server: 🟢 Tráfico normal<br/>curl · wget · ssh (si Grupo A o C)
    Script->>Kali: 🔴 Tráfico anómalo<br/>hping3 · nmap · hydra (si Grupo B o C)

    loop Cada flow capturado
        Server-->>Sur: 📦 paquetes de red
        Kali-->>Sur: 📦 paquetes de red
        Sur->>Sur: 🔍 crear evento flow en eve.json
        Sur-->>Motor: 📜 nueva línea en eve.json
        Motor->>Motor: ⚙️ extraer features → score IF
        Motor->>Motor: 📐 comparar vs τ1/τ2
        alt score ≤ τ2 — BLOCK
            Motor->>Server: ⛔ ipset add ppi_blocked <src_ip>
            Motor->>TG: 📱 alerta BLOCK
        else τ2 < score ≤ τ1 — LIMIT
            Motor->>Server: ⚠️ ipset add ppi_limited <src_ip>
            Motor->>TG: 📱 alerta LIMIT
        else score > τ1 — PERMIT
            Motor->>Motor: ✅ log PERMIT
        end
    end

    Note over Script,TG: ─── Fin de corrida (t = 300 s) ───

    Script->>Sur: 📤 exportar_eve_por_escenario.sh<br/>→ gzip eve.json → data/raw/<br/>→ truncate + reopen-log-files
    Script->>Sur: 📋 registrar_bitacora.sh<br/>→ línea en bitacora_escenarios.txt
    Script->>Script: ⏱️ esperar 60 s → siguiente corrida
```

---

### Tabla de componentes — Fase 6

| Componente | Tipo | Origen / Nodo | Descripción |
|---|---|---|---|
| `f6_corridas.py` | ⚙️ Script | Desktop .20 | Orquestador: lanza tráfico, controla tiempos, recolecta métricas |
| Scripts de escenario (A1–C3) | ⚙️ Scripts | Desktop .20 / Kali .100 | Generan tráfico normal o anómalo según el escenario |
| `curl · wget · ssh · scp` | 🟢 Tool | Desktop .20 | Tráfico normal hacia nginx :80 y SSH :22 |
| `hping3 · nmap · hydra` | 🔴 Tool | Kali .100 | Ataques controlados: flood, scan, brute force |
| Suricata 7.0.3 | 📡 Servicio | Sensor .110 | Captura todos los flows en ens35 → eve.json |
| `eve.json` | 📜 Stream | Sensor .110 | Eventos de red en vivo — rotado al fin de cada corrida |
| `motor_decision.py` | ⚙️ Proceso | Sensor .110 | Procesa flows en tiempo real durante las 300 s |
| `exportar_eve_por_escenario.sh` | ⚙️ Script | Sensor .110 | Comprime eve.json → `.json.gz`, trunca y reabre el log |
| `registrar_bitacora.sh` | ⚙️ Script | Sensor .110 | Agrega línea de metadatos a `bitacora_escenarios.txt` |
| `data/raw/*.json.gz` | 🗜️ Archivo | Sensor .110 | 47 capturas comprimidas — nomenclatura `YYYYMMDD_grupo_esc_NN_eve.json.gz` |
| `motor_decision.log` | 📝 Log | Sensor .110 | Registro de 40 corridas — fuente para `f6_corridas.py` |
| `f6_corridas.py` (análisis) | ⚙️ Script | Sensor .110 | Lee el log, calcula FPR · ITL · latencia · lead_time · TIE · MTTA · MTTC |
| `resultados_f6_completo.csv` | 📊 Datos | `results/` | 40 filas × N columnas — resultado oficial de la Fase 6 |
| `graficas_f6/` | 📈 Gráficas | `results/` | 7 figuras PNG 300 DPI para el informe |
| `bitacora_escenarios.txt` | 📋 Registro | `docs/bitacora/` | Historial cronológico de todas las corridas ejecutadas |

---

### Grupos y distribución de las 40 corridas

```mermaid
gantt
    title Distribución de las 40 corridas de validación F6
    dateFormat  X
    axisFormat  Corrida %s

    section 🟢 Normal (A1–A4)
    Corridas 1–10  : 1, 10

    section 🟠 Mixto (C1–C3)
    Corridas 11–20 : 11, 20

    section 🔁 Reevaluación
    Corridas 21–30 : 21, 30

    section 🏁 Final
    Corridas 31–40 : 31, 40
```

| Grupo | Corridas | Escenarios | Tráfico anómalo | Detección esperada |
|---|---|---|---|---|
| **Normal** | 1 – 10 | A1 · A2 · A3 · A4 | Ninguno | ITL=0% · Disponibilidad=100% |
| **Mixto** | 11 – 20 | C1 · C2 · C3 | SYN flood · port scan · UDP flood | BLOCK + LIMIT · ITL=0% |
| **Reevaluación** | 21 – 30 | C1 · C2 · C3 | Mismos escenarios mixtos | Robustez y reproducibilidad |
| **Final** | 31 – 40 | C1 · C2 · C3 | Mismos escenarios mixtos | Validación de cierre |

---

### Métricas calculadas por corrida

| Métrica | Símbolo | Descripción |
|---|---|---|
| Falsos Positivos | FPR | % flows legítimos con score < τ1 |
| Interrupción Tráfico Legítimo | ITL | % flows normales bloqueados o limitados por error |
| Latencia de decisión | lat_ms | Tiempo medio entre lectura del flow y emisión de la decisión (ms) |
| Lead time | LT_s | Segundos desde inicio del ataque hasta primer log BLOCK/LIMIT |
| Tasa de Intervención Efectiva | TIE | % flows anómalos que recibieron BLOCK o LIMIT |
| Mean Time To Alert | MTTA_s | Tiempo desde inicio ataque hasta primer Telegram enviado |
| Mean Time To Contain | MTTC_s | Tiempo desde inicio ataque hasta primer ipset aplicado en servidor |
| Disponibilidad | disp | Servidor responde curl/ping durante la corrida (0=caída / 1=ok) |

---

*Diagramas generados el 2026-06-19.*
*Scripts fuente: `scripts/motor_decision.py` · `scripts/f6_corridas.py` · `scripts/capture/exportar_eve_por_escenario.sh`*
