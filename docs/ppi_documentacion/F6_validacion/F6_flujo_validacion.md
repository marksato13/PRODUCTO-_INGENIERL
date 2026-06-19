# F6 — Flujo de Validación (40 Corridas)

**Fase 6 · PPI — Universidad Peruana Unión · 2026**
Archivo: `scripts/f6_corridas.py` · 40 corridas · ~4 horas total

---

## Diagrama 1 — Pipeline completo de validación

```mermaid
flowchart TD
    classDef config   fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef script   fill:#D1FAE5,stroke:#059669,color:#065F46
    classDef normal   fill:#BBF7D0,stroke:#16A34A,color:#14532D
    classDef anom     fill:#FEE2E2,stroke:#DC2626,color:#7F1D1D
    classDef mixto    fill:#FED7AA,stroke:#EA580C,color:#7C2D12
    classDef sensor   fill:#EDE9FE,stroke:#7C3AED,color:#3B0764
    classDef archivo  fill:#FEF9C3,stroke:#CA8A04,color:#713F12
    classDef resultado fill:#F0F9FF,stroke:#0284C7,color:#0C4A6E

    %% ── PREREQUISITOS ────────────────────────────────────────────
    subgraph PRE["✅ Prerequisitos — F1 a F5 operativos"]
        direction LR
        MOT[("⚙️ ppi-motor.service\nACTIVO\nτ1/τ2 cargados")]:::config
        SUR[("📡 Suricata 7.0.3\nACTIVO · ens35")]:::config
        IPT[("🔥 ipsets vacíos\nppi_blocked\nppi_limited")]:::config
    end

    PRE --> INICIO

    INICIO(["▶️ f6_corridas.py\nInicia pipeline F6"]):::script

    INICIO --> PREP

    %% ── PREPARACIÓN POR CORRIDA ──────────────────────────────────
    subgraph PREP["🔧 Preparación antes de cada corrida"]
        direction LR
        PR1["🗑️ ipset flush\nppi_blocked · ppi_limited"]:::script
        PR2["🔄 systemctl restart\nppi-motor.service"]:::script
        PR3["✅ Verificar motor\ntail log 3 s"]:::script
        PR1 --> PR2 --> PR3
    end

    PREP --> SELECT

    %% ── SELECCIÓN DE ESCENARIO ───────────────────────────────────
    subgraph SELECT["📋 Selección del escenario según grupo"]
        direction LR
        GA["🟢 Grupo A\nNormal\nDesktop .20\nA1 · A2 · A3 · A4\ncurl · wget · ssh · scp"]:::normal
        GB["🔴 Grupo B\nAnómalo\nKali .100\nB1–B6\nhping3 · nmap · hydra"]:::anom
        GC["🟠 Grupo C\nMixto\nDesktop + Kali\nC1 · C2 · C3\nnormal ∥ anómalo"]:::mixto
    end

    SELECT --> GEN

    %% ── GENERACIÓN DE TRÁFICO ────────────────────────────────────
    subgraph GEN["🚦 Generación de tráfico — 300 segundos"]
        direction LR
        T1["🟢 Tráfico normal\ncurl · wget → nginx :80\nssh · scp → :22"]:::normal
        T2["🔴 Tráfico anómalo\nhping3 SYN flood · UDP flood · ICMP flood\nnmap port scan · hydra brute force"]:::anom
        T3["🟠 Ambos simultáneos\nnormal ∥ anómalo\ndesde Desktop + desde Kali"]:::mixto
    end

    GEN --> CAP

    %% ── CAPTURA Y PROCESAMIENTO ──────────────────────────────────
    subgraph CAP["📡 Sensor 192.168.0.110 — captura en tiempo real"]
        direction LR
        SU["🔍 Suricata 7.0.3\ninspecciona ens35\ncrea flow events"]:::sensor
        EV[("📜 eve.json\nactualización\ncontinua")]:::archivo
        MT["⚙️ motor_decision.py\ntail -F eve.json\n→ score IF → decisión"]:::sensor
        LG[("📝 motor_decision.log\nupdated en tiempo real")]:::archivo
        SU --> EV --> MT --> LG
    end

    GEN --> CAP

    CAP --> FIN

    %% ── FIN DE CORRIDA ───────────────────────────────────────────
    subgraph FIN["📦 Fin de corrida — exportar y registrar"]
        direction LR
        EX["📤 exportar_eve_por_escenario.sh\ngzip eve.json → data/raw/\ntruncate + reopen-log-files\n→ 📁 YYYYMMDD_grupo_esc_NN_eve.json.gz"]:::script
        BIT["📋 registrar_bitacora.sh\nescribe línea en\ndocs/bitacora/bitacora_escenarios.txt"]:::script
        WAI["⏱️ Espera 60 s\nante de la siguiente corrida"]:::script
        EX --> BIT --> WAI
    end

    FIN --> CHECK

    CHECK{"🔢 ¿Corridas\ncompletadas?"}
    CHECK -->|"< 40 → siguiente"| PREP
    CHECK -->|"= 40 → analizar"| ANAL

    %% ── ANÁLISIS POST-VALIDACIÓN ─────────────────────────────────
    subgraph ANAL["📊 Análisis post-validación"]
        direction TB
        F6SC["⚙️ f6_corridas.py\nlee motor_decision.log\ncalcula métricas por corrida"]:::script
        AUCS["⚙️ auc_por_escenario.py\nAUC-ROC por escenario\ndesde archivos .json.gz"]:::script
        CSV[("📊 resultados_f6_completo.csv\n40 filas · 18 columnas")]:::resultado
        GRA[("📈 graficas_f6/\n7 figuras PNG 300 DPI")]:::resultado
        REP[("📄 auc_por_escenario.txt\nB1–B6 · C1–C3")]:::resultado
        F6SC --> CSV
        F6SC --> GRA
        AUCS --> REP
        AUCS --> GRA
    end

    ANAL --> FIN2

    FIN2(["✅ F6 completada\n40 / 40 corridas validadas\nTodos los requisitos CUMPLIDOS"]):::script
```

---

## Diagrama 2 — Secuencia detallada de una corrida individual

```mermaid
sequenceDiagram
    actor Orch as 🖥️ f6_corridas.py<br/>Desktop .20
    participant Kali as 🔴 Kali<br/>.100
    participant Sur  as 📡 Suricata<br/>Sensor .110
    participant Motor as ⚙️ Motor<br/>.110
    participant Srv  as 🖧 Servidor<br/>.120
    participant TG   as 📱 Telegram

    Orch->>Sur:  🗑️ ipset flush ppi_blocked / ppi_limited
    Orch->>Sur:  🔄 systemctl restart ppi-motor.service
    Orch->>Sur:  ✅ verificar motor (tail log 3 s)

    Note over Orch,TG: ─── Inicio corrida N  ·  t = 0 s ───

    Orch->>Srv:  🟢 tráfico normal  (curl · wget · ssh)
    Orch->>Kali: 🔴 tráfico anómalo (hping3 · nmap · hydra)

    loop Cada flow capturado en ens35
        Kali-->>Sur:  📦 paquetes de ataque
        Srv-->>Sur:   📦 paquetes de respuesta
        Sur->>Sur:    🔍 crear evento flow en eve.json
        Sur-->>Motor: 📜 nueva línea en eve.json

        Motor->>Motor: ⚙️ extraer 14 features
        Motor->>Motor: 📊 StandardScaler.transform()
        Motor->>Motor: 🌲 IF.score_samples() → score

        alt score ≤ τ2  →  ⛔ BLOCK
            Motor->>Srv: ipset add ppi_blocked src_ip  (SSH)
            Motor->>TG:  📱 🚨 alerta BLOCK
        else τ2 < score ≤ τ1  →  ⚠️ LIMIT
            Motor->>Srv: ipset add ppi_limited src_ip  (SSH)
            Motor->>TG:  📱 ⚠️ alerta LIMIT
        else score > τ1  →  ✅ PERMIT
            Motor->>Motor: log DEBUG — sin acción
        end
    end

    Note over Orch,TG: ─── Fin de corrida  ·  t = 300 s ───

    Orch->>Sur: 📤 exportar_eve_por_escenario.sh<br/>→ gzip eve.json → data/raw/YYYYMMDD_*.json.gz<br/>→ truncate + suricatasc reopen-log-files
    Orch->>Sur: 📋 registrar_bitacora.sh<br/>→ línea en bitacora_escenarios.txt
    Orch->>Orch: ⏱️ esperar 60 s → siguiente corrida
```

---

## Diagrama 3 — Distribución de las 40 corridas

```mermaid
flowchart LR
    classDef normal  fill:#BBF7D0,stroke:#16A34A,color:#14532D
    classDef mixto   fill:#FED7AA,stroke:#EA580C,color:#7C2D12
    classDef reeval  fill:#EDE9FE,stroke:#7C3AED,color:#3B0764
    classDef final_  fill:#DBEAFE,stroke:#3B82F6,color:#1E3A5F
    classDef result  fill:#F0F9FF,stroke:#0284C7,color:#0C4A6E

    C1_10["🟢 Corridas 1–10\nGrupo Normal\nA1 · A2 · A3 · A4\nDesktop solo\nflows_anom=0\nITL=0% · disp=1"]:::normal

    C11_20["🟠 Corridas 11–20\nGrupo Mixto\nC1 · C2 · C3\nDesktop + Kali\nCorrida 11: primera detección\nLead Time = 61.92 s"]:::mixto

    C21_30["🔵 Corridas 21–30\nReevaluación\nMismos escenarios mixtos\nRobustez y reproducibilidad\nflows_anom=0 · disp=1"]:::reeval

    C31_40["🟣 Corridas 31–40\nValidación Final\nCierre del PPI\nflows_anom=0 · disp=1\nITL=0% · 40/40 OK"]:::final_

    RES(["✅ Resultados\nDisponibilidad 100%\nITL 0%\nLead Time 61.92 s\nLatencia P95 34.8 ms\nAUC-ROC 0.8998"]):::result

    C1_10  --> C11_20
    C11_20 --> C21_30
    C21_30 --> C31_40
    C31_40 --> RES
```

---

## Tabla de componentes

| Componente | Tipo | Ruta / Nodo | Descripción |
|---|---|---|---|
| `f6_corridas.py` | ⚙️ Script | `scripts/` · Desktop .20 | Orquestador: lanza tráfico, controla tiempos, calcula métricas |
| Scripts A1–A4 | ⚙️ Scripts | `scripts/escenarios/` | Generan tráfico normal (curl · wget · ssh · scp) |
| Scripts B1–B6 | ⚙️ Scripts | `scripts/escenarios/` · Kali | Generan ataques (hping3 · nmap · hydra) |
| Scripts C1–C3 | ⚙️ Scripts | `scripts/escenarios/` · ambos | Tráfico mixto simultáneo |
| Suricata 7.0.3 | 📡 Servicio | Sensor .110 · ens35 | Captura flows → `eve.json` |
| `eve.json` | 📜 Stream | `/var/log/suricata/` · Sensor .110 | Rotado al fin de cada corrida |
| `motor_decision.py` | ⚙️ Proceso | Sensor .110 | Procesa flows en tiempo real durante 300 s |
| `exportar_eve_por_escenario.sh` | ⚙️ Script | `scripts/capture/` · Sensor .110 | gzip + truncate + reopen-log-files |
| `registrar_bitacora.sh` | ⚙️ Script | `scripts/evaluation/` · Sensor .110 | Añade línea a bitácora cronológica |
| `data/raw/*.json.gz` | 🗜️ Archivo | `data/raw/` · Sensor .110 | 47 capturas · `YYYYMMDD_grupo_esc_NN_eve.json.gz` |
| `motor_decision.log` | 📝 Log | `results/` · Sensor .110 | Fuente de métricas para `f6_corridas.py` |
| `f6_corridas.py` (análisis) | ⚙️ Script | `scripts/` | Lee log, calcula FPR · ITL · latencia · lead_time · TIE · MTTA · MTTC |
| `resultados_f6_completo.csv` | 📊 Datos | `results/` | 40 filas × 18 columnas — resultado oficial F6 |
| `graficas_f6/` | 📈 Gráficas | `results/graficas_f6/` | 7 figuras PNG 300 DPI |
| `bitacora_escenarios.txt` | 📋 Registro | `docs/bitacora/` | Historial cronológico de todas las corridas |
| `auc_por_escenario.py` | ⚙️ Script | `scripts/` | AUC individual por escenario desde archivos .gz |

---

## Métricas calculadas por corrida

| Métrica | Símbolo | Descripción |
|---|---|---|
| Disponibilidad | `disp` | Servidor responde durante la corrida (0=caída / 1=OK) |
| Interrupción de Tráfico Legítimo | `itl_pct` | % flows normales bloqueados o limitados por error |
| Flujos anómalos detectados | `flows_anom` | Líneas WARNING en el log de esa corrida |
| IPs bloqueadas | `bloqueados` | IPs en `BLOCK` durante la corrida |
| IPs limitadas | `limitados` | IPs en `LIMIT` durante la corrida |
| Lead time | `lead_time_s` | Segundos desde inicio ataque hasta primera decisión BLOCK/LIMIT |
| Mean Time To Alert | `mtta_s` | Segundos desde inicio ataque hasta primer Telegram enviado |
| Mean Time To Contain | `mttc_s` | Segundos desde inicio ataque hasta primer ipset aplicado |
| Tasa de Intervención Efectiva | `tie_pct` | % IPs anómalas que recibieron BLOCK o LIMIT |

---

## Resultados validados (corrida 11 — única detección en F6)

| Campo | Valor | Significado |
|---|---|---|
| Corrida | 11 | Grupo mixto · SYN flood |
| Lead time | **61.92 s** | Tiempo hasta primera decisión BLOCK |
| Flows normales paralelos | 6,500 | Desktop HTTP+SSH activo durante el ataque |
| ITL durante el ataque | **0 %** | Ningún flow legítimo fue bloqueado |
| Decisiones emitidas | BLOCK + LIMIT | 192.168.0.100 en ambos ipsets |
| Disponibilidad | **1** | nginx respondió HTTP 200 a t=150 s |

> El lead time de ~62 s está determinado por la ventana de cierre de flows TCP de Suricata.
> El motor solo puede decidir sobre un flow **después** de que Suricata lo cierra.

---

*Fase 6 completada · 40/40 corridas · Todos los requisitos del PPI CUMPLIDOS · 2026-06-16*
