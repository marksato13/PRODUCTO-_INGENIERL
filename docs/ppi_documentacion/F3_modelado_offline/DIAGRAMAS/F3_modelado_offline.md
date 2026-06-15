# F3 — Diagrama: Modelado Offline · Isolation Forest

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F3 — Modelado Offline  
**Fechas:** 2 – 4 de junio 2026 (entrenamiento v1 → recalibración v2)  
**Estado:** ✅ Completado — AUC-ROC=0.9440 · τ1=−0.4973 · τ2=−0.6873  

---

## Diagrama 1 — Pipeline Completo: Datos → Modelo → Umbrales

```mermaid
flowchart TD

    %% ── ENTRADAS ───────────────────────────────────────────────
    subgraph INPUT["📥 Entrada — data/raw/ en Sensor 192.168.0.110"]
        direction LR
        RAW_N["📦 Corridas normales 01 y 02\nnormal_http_01/02_eve.json.gz\nnormal_ssh_01/02_eve.json.gz\nnormal_sostenido_01/02_eve.json.gz\nnormal_transferencia_01/02_eve.json.gz"]
        FILTER["🔽 Filtro doble (en fase3_isolation_forest.py)\n① solo archivos corridas _01_ y _02_\n② src_ip ∈ {192.168.0.20, 192.168.0.120}\nEVITA contaminación de eve.json acumulado"]
        FLOWS684["✅ 684 flows normales puros\nhttp:         345 flows (50.4%)\nsostenido:    252 flows (36.8%)\nssh:           58 flows  (8.5%)\ntransferencia:  29 flows  (4.2%)"]
        RAW_N --> FILTER --> FLOWS684
    end

    %% ── FEATURE ENGINEERING ─────────────────────────────────────
    subgraph FE["⚙️ Feature Engineering — extract_features()"]
        direction TB
        FE_RAW["Por cada flow event en eve.json:"]
        FE_VOL["Volumétricas (4)\npkts_toserver · pkts_toclient\nbytes_toserver · bytes_toclient"]
        FE_TMP["Temporal (1)\nduration = flow.end − flow.start  (mín. 0.001s)"]
        FE_DER["Derivadas (5)\npkt_rate  = (pkts_to + pkts_from) / duration\nbyte_rate = (bytes_to + bytes_from) / duration\npkt_ratio  = pkts_toserver / (pkts_toclient + 1)\nbyte_ratio = bytes_toserver / (bytes_toclient + 1)\navg_pkt_size = (bytes_to+bytes_from) / (pkts_to+pkts_from+1)"]
        FE_BIN["Binarias (3)\nis_tcp  = 1 si proto=='TCP'\nis_udp  = 1 si proto=='UDP'\nis_icmp = 1 si proto in ('ICMP','IPV6-ICMP')"]
        FE_DSC["Discreta (1)\ndest_port  ← puerto destino del servidor"]
        FE_MAT["DataFrame 684 × 14\n(filas × features)"]
        FE_RAW --> FE_VOL & FE_TMP & FE_DER & FE_BIN & FE_DSC --> FE_MAT
    end

    %% ── SCALER ───────────────────────────────────────────────────
    subgraph SCALER["📐 StandardScaler — scaler.fit(X_normal_684)"]
        direction LR
        SC_FIT["Calcula μ y σ SOLO de flows normales\nmean_  = media de cada feature en tráfico legítimo\nscale_ = desviación estándar por feature"]
        SC_TRF["X_scaled = (X − μ) / σ\nCada feature centrada en 0, escala 1\nAnómalos → z-scores extremos por definición"]
        SC_OUT["📄 models/scaler.pkl  1.4 KB\nUsado en producción para transformar\ncada flow nuevo antes de predecir"]
        SC_FIT --> SC_TRF --> SC_OUT
    end

    %% ── ISOLATION FOREST ──────────────────────────────────────────
    subgraph IF_TRAIN["🌲 IsolationForest — clf.fit(X_scaled_normal)"]
        direction TB
        IF_PARAMS["Hiperparámetros:\nn_estimators = 300   ← más árboles = scores más estables\ncontamination = 0.05 ← 5% de ruido esperado en normal\nmax_samples = 'auto' ← 256 por árbol\nrandom_state = 42    ← reproducibilidad\nn_jobs = -1          ← paraleliza en 4 cores"]
        IF_ALGO["Algoritmo:\n① 300 árboles aleatorios sobre submuestra de 256 flows\n② Cada árbol: feature aleatoria → split aleatorio\n③ Un flow anómalo se aísla con MENOS particiones\n④ score = 2^(−media_prof / c(256))\n   más negativo → más fácil de aislar → más anómalo"]
        IF_OUT["📄 models/isolation_forest.pkl  2.5 MB\nclfoffset_ = −0.5481  (v1: umbral automático)"]
        IF_PARAMS --> IF_ALGO --> IF_OUT
    end

    %% ── EVALUACIÓN ───────────────────────────────────────────────
    subgraph EVAL["📊 Evaluación — auc_roc_umbrales.py"]
        direction TB
        EVAL_SET["Conjunto de evaluación balanceado 50/50:\n11,669 flows normales  ← de train.csv\n11,669 flows anómalos  ← de test.csv\nTotal: 23,338 flows"]
        SCORES["Distribución de scores:\nTráfico NORMAL:   μ = −0.4262  σ = 0.0646\nTráfico ANÓMALO:  μ = −0.6548  σ = 0.0808\nSeparación:       Δ = 0.229 unidades"]
        ROC_CURVE["Curva ROC\nAUC-ROC = 0.9440\n(94.4% de discriminación)\n→ results/figures/auc_roc_umbrales.png"]
        EVAL_SET --> SCORES --> ROC_CURVE
    end

    %% ── UMBRALES ────────────────────────────────────────────────
    subgraph UMBRALES["🎯 Derivación de Umbrales — auc_roc_umbrales.py"]
        direction TB
        TAU1["τ1 = −0.4973\nCriterio: Índice de Youden máximo\n  max(TPR − FPR)\nTPR = 91.0%  FPR = 9.5%\nFrontera PERMIT ↔ LIMIT"]
        TAU2["τ2 = −0.6873\nCriterio: FPR ≤ 2% con máximo TPR\n  FPR = 1.8%  TPR = 40.6%\nFrontera LIMIT ↔ BLOCK"]
        DECISION["Lógica triple resultante:\nscore > −0.4973        → PERMIT\n−0.6873 < score ≤ −0.4973 → LIMIT\nscore ≤ −0.6873        → BLOCK"]
        UMBRALES_FILE["📄 results/umbrales_finales.txt\n(τ1 · τ2 · criterios · métricas)"]
        TAU1 & TAU2 --> DECISION --> UMBRALES_FILE
    end

    %% ── ARTEFACTOS ───────────────────────────────────────────────
    subgraph MODELS["📦 Artefactos persistidos — models/"]
        M1["isolation_forest.pkl  2.5 MB\nBorn:  2026-06-02 01:42 (v1)\nModify: 2026-06-04 14:41 (v2 ← en producción)"]
        M2["scaler.pkl  1.4 KB\nModify: 2026-06-04 14:41"]
        M3["features.csv  152 B\nLista ordenada de 14 features"]
    end

    %% ── FLUJO ────────────────────────────────────────────────────
    FLOWS684 --> FE_RAW
    FE_MAT --> SC_FIT
    SC_TRF --> IF_PARAMS
    IF_OUT -->|"clf.score_samples(X_test)"| EVAL_SET
    ROC_CURVE --> TAU1
    ROC_CURVE --> TAU2
    IF_OUT --> M1
    SC_OUT --> M2
    FE_MAT -->|"models/features.csv"| M3

    %% ── AUC POR ESCENARIO ────────────────────────────────────────
    subgraph AUC_ESC["📈 AUC por Escenario — auc_por_escenario.py"]
        direction TB
        AUC_TABLE["results/reports/auc_por_escenario.txt\n\nUDP Flood  B3   AUC=0.9905  Det=100%  ✅ Excelente\nICMP Flood B4   AUC=0.9861  Det=100%  ✅ Excelente\nMixto C3        AUC=0.9801  Det=99.3% ✅ Excelente\nMixto C1        AUC=0.9737  Det=100%  ✅ Excelente\nPort Scan  B2   AUC=0.9721  Det=99.9% ✅ Excelente\nSYN Flood  B1   AUC=0.9529  Det=72.2% ⚡ Muy bueno\nMixto C2        AUC=0.9277  Det=57.1% ⚡ Muy bueno\nHTTP Abuse B5   AUC=0.8630  Det=56.6% ⚠️ → detector HTTP\nBrute F.   B6   AUC=0.6770  Det=0.9%  ⚠️ → detector SSH"]
    end
    IF_OUT --> AUC_ESC

    %% ── CONECTOR F4 ──────────────────────────────────────────────
    F4_CONN(["→ F4: Motor de Decisión\nmodels/isolation_forest.pkl  (joblib.load)\nmodels/scaler.pkl             (joblib.load)\nTAU1 = −0.4973  (hardcoded)\nTAU2 = −0.6873  (hardcoded)\nB5/B6 → detectores temporales complementan IF"])
    MODELS ==>|"cargados al inicio\ndel motor"| F4_CONN
    UMBRALES_FILE ==>|"τ1 · τ2 a\nmotor_decision.py"| F4_CONN

    %% ── ESTILOS ──────────────────────────────────────────────────
    style INPUT    fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style FE       fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style SCALER   fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style IF_TRAIN fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style EVAL     fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style UMBRALES fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style MODELS   fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    style AUC_ESC  fill:#fafafa,stroke:#757575
    style F4_CONN  fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Diagrama 2 — Recalibración: v1 (2 jun) → v2 (4 jun)

```mermaid
flowchart LR

    subgraph V1["🔵 Versión 1  —  2026-06-02 01:42"]
        direction TB
        V1_DATA["Datos disponibles en madrugada:\ncorridas iniciales capturadas\nen las horas previas"]
        V1_TRAIN["fase3_isolation_forest.py\nPrimera ejecución"]
        V1_PKL["isolation_forest.pkl (Born)\nclfoffset_ = −0.5481 (automático)\nLógica: BINARIA (normal / anómalo)"]
        V1_DATA --> V1_TRAIN --> V1_PKL
    end

    subgraph ANALISIS["🔬 Análisis entre sesiones (2-4 jun)"]
        direction TB
        SEN["Análisis de sensibilidad\nN flows vs AUC vs Recall\n(12 valores de N × 5 semillas)"]
        HALL["Hallazgos:\n① AUC estable desde N=200-300\n② Corridas SSH_03-10 sesgan modelo\n③ Con >1000 flows SSH → det(B6) ≈ 0%\n④ Punto óptimo: N=684 flows (corridas 01-02)"]
        ROC2["auc_roc_umbrales.py\nCurva ROC → τ1 y τ2 óptimos"]
        SEN --> HALL --> ROC2
    end

    subgraph V2["🟢 Versión 2  —  2026-06-04 14:41  ← EN PRODUCCIÓN"]
        direction TB
        V2_FILT["Filtro doble aplicado:\n① Solo corridas 01 y 02\n② src_ip Desktop/Servidor"]
        V2_TRAIN["fase3_isolation_forest.py\nSegunda ejecución"]
        V2_PKL["isolation_forest.pkl (Modify)\nscaler.pkl  (Modify)\nLógica: TRIPLE PERMIT/LIMIT/BLOCK\nτ1 = −0.4973  (Youden)\nτ2 = −0.6873  (FPR ≤ 2%)"]
        V2_FILT --> V2_TRAIN --> V2_PKL
    end

    V1_PKL -->|"problema detectado:\nsesgo SSH reduce det(B6)\numbral automático no óptimo"| ANALISIS
    ANALISIS -->|"recalibración con\ndatos filtrados"| V2_FILT

    DELTA["Mejora v1 → v2:\n① Decisión binaria → triple\n② clf.offset_ → τ1/τ2 desde ROC\n③ Sesgo SSH eliminado\n④ 684 flows óptimos validados"]

    V2_PKL --> DELTA

    style V1      fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style ANALISIS fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style V2      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style DELTA   fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
```

---

## Diagrama 3 — Feature Engineering: Cómo se Construyen las 14 Features

```mermaid
flowchart TD

    EVE_FLOW["Eve.json — flow event\n{\n  src_ip, dest_ip, dest_port, proto,\n  flow: { pkts_toserver, pkts_toclient,\n          bytes_toserver, bytes_toclient,\n          start, end }\n}"]

    subgraph CALC["extract_features(event)"]
        direction TB

        subgraph VOL["Volumétricas (directo del event)"]
            direction LR
            V1F["pkts_toserver\n← flow.pkts_toserver"]
            V2F["pkts_toclient\n← flow.pkts_toclient"]
            V3F["bytes_toserver\n← flow.bytes_toserver"]
            V4F["bytes_toclient\n← flow.bytes_toclient"]
        end

        subgraph TMP["Temporal"]
            D["duration\n= max(end−start, 0.001s)\nfromisoformat(start/end)"]
        end

        subgraph DER["Derivadas (calculadas)"]
            direction LR
            D1["pkt_rate\n= (pts+ptc) / dur"]
            D2["byte_rate\n= (bts+btc) / dur"]
            D3["pkt_ratio\n= pts / (ptc+1)"]
            D4["byte_ratio\n= bts / (btc+1)"]
            D5["avg_pkt_size\n= (bts+btc) / (pts+ptc+1)"]
        end

        subgraph BIN["Binarias (proto)"]
            direction LR
            B1F["is_tcp\n= 1 si TCP"]
            B2F["is_udp\n= 1 si UDP"]
            B3F["is_icmp\n= 1 si ICMP"]
        end

        subgraph DSC["Discreta"]
            DP["dest_port\n← event.dest_port"]
        end
    end

    NORMAL_EX["Ejemplo — HTTP normal (A1):\npkts_toserver=6, pkts_toclient=4\nbytes_toserver=492, bytes_toclient=555\nduration=0.12s, pkt_rate=83\nbyte_rate=8725, is_tcp=1, dest_port=80\n→ score = −0.41 (PERMIT)"]

    ANOM_EX["Ejemplo — SYN Flood (B1):\npkts_toserver=7432, pkts_toclient=0\nbytes_toserver=312144, bytes_toclient=0\nduration=0.08s, pkt_rate=92900\nbyte_rate=3.9M, is_tcp=1, dest_port=80\n→ score = −0.78 (BLOCK)"]

    EVE_FLOW --> CALC
    CALC -->|"vector [f1..f14]"| NORMAL_EX & ANOM_EX

    style EVE_FLOW fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    style CALC     fill:#e8f5e9,stroke:#2e7d32
    style VOL      fill:#e3f2fd,stroke:#1565c0
    style TMP      fill:#fff3e0,stroke:#e65100
    style DER      fill:#f3e5f5,stroke:#6a1b9a
    style BIN      fill:#fce4ec,stroke:#c62828
    style DSC      fill:#fffde7,stroke:#f9a825
    style NORMAL_EX fill:#c8e6c9,stroke:#1b5e20
    style ANOM_EX  fill:#ffcdd2,stroke:#b71c1c
```

---

## Diagrama 4 — Derivación de τ1 y τ2 desde la Curva ROC

```mermaid
flowchart LR

    subgraph SCORES["Distribución de scores IF"]
        direction TB
        SC_N["Tráfico NORMAL (11,669 flows)\nμ = −0.4262  σ = 0.0646\nMayoría entre −0.35 y −0.55"]
        SC_A["Tráfico ANÓMALO (11,669 flows)\nμ = −0.6548  σ = 0.0808\nMayoría entre −0.55 y −0.80"]
        SEP["Separación entre medias:\nΔ = 0.2286 unidades\n↑ Mayor separación = mejor discriminación"]
        SC_N --> SEP
        SC_A --> SEP
    end

    subgraph ROC["Curva ROC — AUC = 0.9440"]
        direction TB
        ROC_DEF["Para cada umbral θ ∈ [−1, 0]:\n  TPR(θ) = P(score ≤ θ | anómalo)\n  FPR(θ) = P(score ≤ θ | normal)"]
        ROC_AUC["Área bajo la curva = 0.9440\n→ 94.4% de probabilidad de que\n  un flow anómalo score < flow normal"]
        ROC_DEF --> ROC_AUC
    end

    subgraph TAU1_BOX["τ1 = −0.4973  (frontera PERMIT / LIMIT)"]
        direction TB
        T1_CRIT["Criterio: Índice de Youden\nmax(TPR − FPR) sobre todos los θ"]
        T1_VALS["En τ1 = −0.4973:\n  TPR = 91.0%  ← 91% ataques detectados\n  FPR = 9.5%   ← 9.5% falsos positivos\n  Youden = 0.815"]
        T1_ACT["Acción: score > τ1 → PERMIT\n(tráfico considerado normal)"]
        T1_CRIT --> T1_VALS --> T1_ACT
    end

    subgraph TAU2_BOX["τ2 = −0.6873  (frontera LIMIT / BLOCK)"]
        direction TB
        T2_CRIT["Criterio: FPR ≤ 2% con máximo TPR\n(Alta precisión — mínimos FP en BLOCK)"]
        T2_VALS["En τ2 = −0.6873:\n  FPR = 1.8%   ← solo 1.8% falsas alarmas de BLOCK\n  TPR = 40.6%  ← 40.6% ataques van directo a BLOCK\n  Resto → IF devuelve LIMIT primero"]
        T2_ACT["Acción: score ≤ τ2 → BLOCK\n(anómalo con alta confianza — DROP)"]
        T2_CRIT --> T2_VALS --> T2_ACT
    end

    subgraph ZONA["Zona τ2 < score ≤ τ1  →  LIMIT"]
        ZN["Tráfico sospechoso pero no confirmado\nhashlimit: 100 pkt/s, burst 150\nSi escala → detector heurístico activa BLOCK\nScore observado en producción:\nPort Scan B2:   −0.6260 (BAJA)\nHTTP Abuse B5:  −0.5117 (BAJA)\nSSH bajo ataque: −0.6281 (BAJA)"]
    end

    SCORES --> ROC
    ROC --> TAU1_BOX & TAU2_BOX
    TAU1_BOX --> ZONA
    TAU2_BOX --> ZONA

    FINAL["📄 results/umbrales_finales.txt\nτ1 = −0.4973  PERMIT/LIMIT\nτ2 = −0.6873  LIMIT/BLOCK\nHardcodeados en motor_decision.py\ncomo TAU1 y TAU2"]
    ZONA --> FINAL

    style SCORES  fill:#e3f2fd,stroke:#1565c0
    style ROC     fill:#fff3e0,stroke:#e65100
    style TAU1_BOX fill:#e8f5e9,stroke:#2e7d32
    style TAU2_BOX fill:#fce4ec,stroke:#c62828
    style ZONA    fill:#fffde7,stroke:#f9a825
    style FINAL   fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Diagrama 5 — Análisis de Sensibilidad: N Flows vs Rendimiento

```mermaid
flowchart TD

    subgraph METODO["Metodología del análisis"]
        direction LR
        M1S["Pool: 1,977 flows normales\n(data/raw/*_normal_*_eve.json.gz)"]
        M2S["Para cada N ∈\n{50,100,200,300,400,\n500,684,800,1000,1500}"]
        M3S["5 semillas × N\n= 50-100 modelos\ncada uno evaluado en\nflows normales no usados\n+ 5,000 flows anómalos"]
        M1S --> M2S --> M3S
    end

    subgraph TABLA["Resultados — AUC y Recall(τ1)"]
        direction TB
        T_HEAD["  N   |  AUC  | ±std  | Recall"]
        T_50  ["  50  | 0.922 | 0.035 | 0.993 ← alta varianza"]
        T_200 [" 200  | 0.931 | 0.028 | 0.993"]
        T_300 [" 300  | 0.929 | 0.018 | 0.993 ← varianza cae"]
        T_500 [" 500  | 0.937 | 0.011 | 0.993"]
        T_684 [" 684★ | 0.935 | 0.013 | 0.993 ← ELEGIDO"]
        T_800 [" 800  | 0.940 | 0.014 | 0.993"]
        T_1000["1000  | 0.936 | 0.005 | 0.993"]
        T_1500["1500  | 0.935 | 0.004 | 0.993"]
        T_HEAD --> T_50 --> T_200 --> T_300 --> T_500 --> T_684 --> T_800 --> T_1000 --> T_1500
    end

    subgraph HALLAZGOS["3 Hallazgos clave"]
        direction TB
        H1["① Recall(τ1) = 0.993\n   CONSTANTE para todo N desde 50 hasta 1500\n   → la detección no depende del tamaño"]
        H2["② AUC se estabiliza en N ≈ 200–300\n   N=684 está en la meseta óptima\n   N=1500 da AUC=0.935 (igual que 684)"]
        H3["③ N=684 no es arbitrario\n   Es el punto donde ssh=8.5% del total\n   Con corridas 03-10: ssh=65% → det(B6)=0%\n   Filtrar a corridas 01-02 preserva detección B6"]
        H1 --> H2 --> H3
    end

    METODO --> TABLA
    TABLA --> HALLAZGOS

    CONCL["✅ Conclusión:\n684 flows es suficiente porque:\n- AUC(684)=0.935 ≈ AUC(1500)=0.935\n- Recall es constante desde N=50\n- std=0.013 (baja varianza, modelo estable)\n- Usar más datos introduce sesgo SSH"]
    HALLAZGOS --> CONCL

    style METODO    fill:#e3f2fd,stroke:#1565c0
    style TABLA     fill:#fafafa,stroke:#757575
    style HALLAZGOS fill:#e8f5e9,stroke:#2e7d32
    style CONCL     fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style T_684     fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Diagrama 6 — AUC por Escenario y Detecciones Complementarias

```mermaid
flowchart TD

    subgraph AUC_RES["AUC por Escenario — scripts/auc_por_escenario.py"]
        direction TB

        subgraph EXCELENTE["✅ Excelente  AUC > 0.97"]
            direction LR
            E1["B3 UDP Flood\nAUC=0.9905 Det=100%\npkt_rate extremo + is_udp"]
            E2["B4 ICMP Flood\nAUC=0.9861 Det=100%\npkt_rate extremo + is_icmp"]
            E3["C3 Mixto desc+udp\nAUC=0.9801 Det=99.3%\nvolumen UDP distinguible"]
            E4["C1 Mixto http+syn\nAUC=0.9737 Det=100%\nSYN separado del HTTP"]
            E5["B2 Port Scan\nAUC=0.9721 Det=99.9%\ndest_port variado + bajo pkt_rate"]
        end

        subgraph MUYBUENO["⚡ Muy bueno  AUC 0.92–0.97"]
            direction LR
            MB1["B1 SYN Flood\nAUC=0.9529 Det=72.2%\n--rand-source dificulta\nagregación por src_ip"]
            MB2["C2 Mixto ssh+scan\nAUC=0.9277 Det=57.1%\nSSH legítimo + scan\nscores solapados"]
        end

        subgraph COMPLEMENTADO["⚠️ Complementado por F4"]
            direction LR
            C1E["B5 HTTP Abuse lento\nAUC=0.8630 Det=56.6%\nflow individual ≈ HTTP normal\n→ Detector HTTP_ABUSE:\n  50 req/30s → LIMIT\n  100 req/30s → BLOCK"]
            C2E["B6 Brute Force SSH\nAUC=0.6770 Det=0.9%\nSSH auth = SSH legítimo\n→ Detector BRUTE_FORCE:\n  5 intentos/60s → LIMIT\n  15 intentos/60s → BLOCK"]
        end
    end

    subgraph TOTAL["Recall combinado (IF + detectores)"]
        direction LR
        R_BASE["Recall base (solo IF):\n~80.4%"]
        R_DET["Recall con detectores F4:\n~92-95%"]
        R_BASE -->|"+ BRUTE_FORCE_SSH\n+ HTTP_ABUSE"| R_DET
    end

    AUC_RES --> TOTAL

    F4_CONECT(["→ F4: Motor de Decisión\nIF cubre B1–B4 y escenarios C\nDetector SSH cubre B6\nDetector HTTP cubre B5\nJuntos: 3 capas de detección"])
    TOTAL ==> F4_CONECT

    style AUC_RES    fill:#fafafa,stroke:#757575
    style EXCELENTE  fill:#e8f5e9,stroke:#2e7d32
    style MUYBUENO   fill:#fff3e0,stroke:#e65100
    style COMPLEMENTADO fill:#fce4ec,stroke:#c62828
    style TOTAL      fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style F4_CONECT  fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```

---

## Diagrama 7 — Artefactos Generados y Conector a F4

```mermaid
flowchart LR

    subgraph SCRIPTS_F3["Scripts de F3"]
        direction TB
        S1["fase3_isolation_forest.py\n→ entrena IF + scaler\n→ genera gráficos scores\n→ muestra métricas en consola"]
        S2["auc_roc_umbrales.py\n→ curva ROC sobre test.csv\n→ deriva τ1 y τ2\n→ genera umbrales_finales.txt"]
        S3["auc_por_escenario.py\n→ AUC individual B1-B6 C1-C3\n→ detecta gaps para F4"]
    end

    subgraph MODELS_OUT["models/  — Artefactos de producción"]
        direction TB
        M1["isolation_forest.pkl  2.5 MB\n📅 Born:   2026-06-02 01:42 (v1)\n📅 Modify: 2026-06-04 14:41 (v2)"]
        M2["scaler.pkl  1.4 KB\n📅 Modify: 2026-06-04 14:41"]
        M3["features.csv  152 B\n14 líneas, una feature por línea\nDefine orden del vector de entrada"]
    end

    subgraph RESULTS_OUT["results/  — Reportes y gráficos"]
        direction TB
        R1["umbrales_finales.txt\nτ1=−0.4973  τ2=−0.6873"]
        R2["reports/reporte_metricas_v1.txt\nAUC=0.9440 · Recall=87.6%\nPrec=99.96% · F1=0.9338"]
        R3["reports/auc_por_escenario.txt\nAUC por B1-B6 y C1-C3"]
        R4["isolation_forest_resultado.png\nDistribución scores + scatter"]
        R5["figures/auc_roc_umbrales.png\nCurva ROC con τ1/τ2 marcados"]
    end

    subgraph F4_USE["F4 — Motor de Decisión consume:"]
        direction TB
        F4_A["joblib.load('models/isolation_forest.pkl')\njoblib.load('models/scaler.pkl')"]
        F4_B["TAU1 = -0.4973  # hardcoded\nTAU2 = -0.6873  # hardcoded"]
        F4_C["features = pd.read_csv('models/features.csv')\n→ define orden de columnas\nantes de clf.score_samples()"]
    end

    SCRIPTS_F3 --> MODELS_OUT & RESULTS_OUT
    MODELS_OUT ==>|"carga al inicio\nppi-motor.service"| F4_A
    R1 ==>|"τ1 y τ2"| F4_B
    M3 ==>|"orden columnas"| F4_C

    style SCRIPTS_F3  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style MODELS_OUT  fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style RESULTS_OUT fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style F4_USE      fill:#fff9c4,stroke:#f57f17,stroke-width:2px
```
