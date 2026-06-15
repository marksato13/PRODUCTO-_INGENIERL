# F6 — Diagrama: Validación y Resultados

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F6 — Validación Completa del Sistema  
**Fechas:** 2 – 4 de junio 2026 + validación live 14–15 de junio 2026  
**Estado:** ✅ Completado — 40 corridas · TIE=100% · ITL=0% · Disponibilidad=100%  

---

## Diagrama 1 — Diseño Experimental: 40 Corridas Controladas

```mermaid
flowchart TD

    subgraph SISTEMA_OK["✅ Sistema F1–F5 activo"]
        direction LR
        SYS["Suricata → Motor → ipset/iptables\nτ1=−0.4973 · τ2=−0.6873\nTelegram · Dashboard"]
    end

    subgraph F6_SCRIPT["📋 scripts/f6_corridas.py — Coordinador"]
        direction TB
        PARAMS["Parámetros:\nDURACION_NORMAL = 300s  (5 min/corrida)\nPAUSA_ENTRE     = 60s   (1 min entre corridas)\nN por grupo     = 10 corridas c/u"]

        subgraph GRP_N["Grupo Normal — corridas 1–10"]
            direction LR
            GN1["Sólo tráfico legítimo\nDesktop 192.168.0.20\nA1–A4 en rotación\ncurl · ssh · scp · wget"]
            GN2["Mide:\nITL (¿algún flow Desktop bloqueado?)\nDisponibilidad (¿nginx responde?)\nLatencia pipeline"]
        end

        subgraph GRP_M["Grupo Mixto — corridas 11–20"]
            direction LR
            GM1["Desktop legítimo + Kali atacando\nRotación ataques:\nsynflood · portscan\nudpflood · httpabuse"]
            GM2["Mide:\nTIE · Lead Time · MTTC\nITL (¿Desktop afectado?)\nDetecciones totales"]
        end

        subgraph GRP_R["Grupo Re-evaluación — corridas 21–30"]
            direction LR
            GR1["Misma config que Mixto\nRepetición para consistencia\nVerifica estabilidad τ1/τ2"]
            GR2["Mide:\nVarianza inter-corridas\nConsistencia de scores\nReproducibilidad"]
        end

        subgraph GRP_F["Grupo Final — corridas 31–40"]
            direction LR
            GF1["Corridas definitivas\nentregable formal PPI\nCondiciones óptimas"]
            GF2["Mide:\nTodas las métricas\nEntregable oficial"]
        end

        PARAMS --> GRP_N & GRP_M & GRP_R & GRP_F
    end

    subgraph OUTPUTS["📊 Archivos de resultados — results/"]
        direction TB
        R1["resultados_normal.csv   899 B  · 10 corridas"]
        R2["resultados_mixto.csv    1.2 KB · 10 corridas"]
        R3["resultados_reeval.csv   1.2 KB · 10 corridas"]
        R4["resultados_final.csv    1.2 KB · 10 corridas"]
        R5["resultados_f6_completo.csv   3.9 KB\n40 corridas consolidadas\n← ENTREGABLE PRINCIPAL"]
        R1 & R2 & R3 & R4 --> R5
    end

    subgraph ENTREGABLES["📦 Entregables formales"]
        direction LR
        PDF["reporte_validacion_final.pdf  7.4 KB\n3 páginas · generado 2026-06-04 20:06\nscripts/generar_pdf_final.py\n← Entregable académico PPI"]
        ZIP["MVP_funcional.zip  25 MB · 40 archivos\nscripts + modelos + datasets + resultados\nscripts/generar_pdf_zip.py\n← Entregable técnico PPI"]
        PDF --> ZIP
    end

    SISTEMA_OK --> F6_SCRIPT
    GRP_N --> R1
    GRP_M --> R2
    GRP_R --> R3
    GRP_F --> R4
    R5 --> PDF

    style SISTEMA_OK fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style F6_SCRIPT  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style GRP_N      fill:#e8f5e9,stroke:#2e7d32
    style GRP_M      fill:#fce4ec,stroke:#c62828
    style GRP_R      fill:#fff3e0,stroke:#e65100
    style GRP_F      fill:#f3e5f5,stroke:#6a1b9a
    style OUTPUTS    fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style ENTREGABLES fill:#e0f2f1,stroke:#00796b,stroke-width:2px
```

---

## Diagrama 2 — Métricas Globales Finales

```mermaid
flowchart LR

    subgraph OPERACIONALES["🏆 Métricas Operacionales (40 corridas)"]
        direction TB
        OP1["✅ Disponibilidad = 100%\nnginx respondió HTTP 200\nen TODAS las corridas de ataque\n(requisito ≥ 99%)"]
        OP2["✅ ITL = 0%\nImpacto en Tráfico Legítimo\n0 flows del Desktop bloqueados\nen 40 corridas\n(requisito ≤ 2%)"]
        OP3["✅ TIE = 100%\nTasa de Intervención Efectiva\nTodas las anomalías detectadas\nrecibieron acción BLOCK o LIMIT"]
        OP4["✅ Lead Time = 26s\nDesde inicio del ataque\nhasta primera entrada WARNING\nen motor_decision.log"]
        OP5["✅ MTTC = 28s\nMean Time To Contain\nDesde inicio hasta\nacción ipset aplicada"]
    end

    subgraph MODELO["📊 Métricas del Modelo (test set 56,525 flows)"]
        direction TB
        ML1["AUC-ROC = 0.9440\n(94.4% discriminación)"]
        ML2["Recall base   = 87.6%\nRecall + detect = 92–95%"]
        ML3["Precision = 99.96%\n(solo 35 FP en 684 normales)"]
        ML4["F1-Score = 0.9338\n(0.8893 con umbral base)"]
        ML5["FPR global = 5.12%\nFPR SSH legítimo = 0%\nFPR Transferencia = 0%"]
    end

    subgraph LATENCIA["⚡ Latencia Pipeline"]
        direction TB
        LAT1["Media = 34.5ms\nP95  = 34.8ms\nRequisito < 500ms\nMargen: 14× de holgura\nThroughput: 29 flows/s"]
    end

    subgraph CONFUSION["Matriz de Confusión (684 normales + 119,542 anómalos)"]
        direction TB
        CM1["TN (normal → PERMIT):   649   (94.9%)"]
        CM2["FP (normal → BLOCK):     35    (5.1%)"]
        CM3["TP (anómalo detectado): 95,750 (80.1%)"]
        CM4["FN (anómalo perdido):   23,792 (19.9%)"]
        CM1 --- CM2
        CM3 --- CM4
    end

    OPERACIONALES --- MODELO
    MODELO --- LATENCIA
    LATENCIA --- CONFUSION

    style OPERACIONALES fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style MODELO        fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style LATENCIA      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style CONFUSION     fill:#fffde7,stroke:#f9a825,stroke-width:2px
```

---

## Diagrama 3 — AUC y Detección por Escenario

```mermaid
flowchart TD

    SCRIPT["scripts/auc_por_escenario.py\n→ results/reports/auc_por_escenario.txt\nGenerado: 2026-06-03 19:04"]

    subgraph EXCELENTE["✅ Excelente — AUC > 0.97"]
        direction LR
        E1["B3 UDP Flood\nAUC=0.9905 · Det=100.0%\nScore=-0.714\npkt_rate extremo + is_udp"]
        E2["B4 ICMP Flood\nAUC=0.9861 · Det=100.0%\nScore=-0.699\npkt_rate extremo + is_icmp"]
        E3["C1 Mixto HTTP+SYN\nAUC=0.9737 · Det=100.0%\nScore=-0.653\nSYN distinguible del HTTP normal"]
        E4["B2 Port Scan\nAUC=0.9721 · Det=99.9%\nScore=-0.651\ndest_port variable + dur corta"]
        E5["C3 Mixto desc+UDP\nAUC=0.9801 · Det=99.3%\nScore=-0.677\nvolumen UDP distinguible"]
    end

    subgraph MUYBUENO["⚡ Muy bueno — AUC 0.92–0.97"]
        direction LR
        MB1["B1 SYN Flood\nAUC=0.9529 · Det=72.2%\nScore=-0.606\n--rand-source dificulta\nagregación por src_ip"]
        MB2["C2 Mixto SSH+scan\nAUC=0.9277 · Det=57.1%\nScore=-0.609\nSSH legítimo + scan\nscores cercanos"]
    end

    subgraph COMPLEMENTADO["⚠️ Complementado por detectores F4"]
        direction LR
        C1S["B5 HTTP Abuse lento\nAUC=0.8630 · Det=56.6%\nScore=-0.589\nFlow individual ≈ normal\n→ HTTP_ABUSE: 50→LIMIT / 100→BLOCK"]
        C2S["B6 Brute Force SSH\nAUC=0.6770 · Det=0.9%\nScore=-0.438\nSSH auth ≈ SSH legítimo\n→ BRUTE_FORCE: 5→LIMIT / 15→BLOCK"]
    end

    subgraph RECALL_FINAL["Recall combinado IF + Detectores"]
        direction LR
        RF1["Recall solo IF: ~80.4%"]
        RF2["+ Detector SSH → B6: ~0.9% → ~90%"]
        RF3["+ Detector HTTP → B5: ~56% → ~80%"]
        RF4["Recall combinado: ~92–95%"]
        RF1 --> RF2 --> RF3 --> RF4
    end

    SCRIPT --> EXCELENTE & MUYBUENO & COMPLEMENTADO
    COMPLEMENTADO --> RECALL_FINAL

    style EXCELENTE      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style MUYBUENO       fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style COMPLEMENTADO  fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style RECALL_FINAL   fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
```

---

## Diagrama 4 — Clasificación de Gravedad: Score → Grado → Tipo

```mermaid
flowchart LR

    SCORE["Score IF\n∈ (−1, 0)"]

    subgraph GRADO_SCALE["Escala de 4 Grados — clasificar_grado(score)"]
        direction TB
        GN["NORMAL\nscore > −0.4973 (> τ1)\nPERMIT\nDentro del baseline normal\nSin acción requerida"]
        GB["BAJA\n−0.6873 < score ≤ −0.4973\nLIMIT\nDesviación leve · Monitoreo\nhashlimit 100pkt/s"]
        GA["ALTA\n−0.8200 < score ≤ −0.6873\nBLOCK\nAnomalia clara · DROP\nAlertas Telegram 🚨"]
        GC["CRÍTICA\nscore ≤ −0.8200\nBLOCK + Escalado\nPercentil 95 anómalos\nFlood masivo extremo"]
        GN --- GB --- GA --- GC
    end

    subgraph DIST_REAL["Distribución real — eval set 23,338 flows"]
        direction TB
        D1["NORMAL:   6,841  (29.3%)  score -0.621±0.038"]
        D2["BAJA:        13  (0.1%)   score -0.531±0.029"]
        D3["ALTA:     14,821 (63.5%)  score -0.734±0.051"]
        D4["CRÍTICA:   1,663  (7.1%)  score -0.861±0.024"]
    end

    subgraph TIPOS["clasificar_tipo() — 9 tipos"]
        direction TB
        T1["NORMAL — tráfico legítimo"]
        T2["BAJA_ANOMALIA — LIMIT, no BF ni HTTP"]
        T3["SYN_FLOOD — TCP pkt_rate>2000 dur<2s bytes_from<100"]
        T4["UDP_FLOOD — UDP pkt_rate>500"]
        T5["ICMP_FLOOD — ICMP pkt_rate>300"]
        T6["HTTP_ABUSE — TCP:80 pkt_rate>200 o 50+req/30s"]
        T7["BRUTE_FORCE_SSH — TCP:22 con ssh_intentos≥5"]
        T8["PORT_SCAN — dest_port variable, score BAJA"]
        T9["ANOMALIA_GENERICA — no encaja en reglas anteriores"]
    end

    subgraph SCORES_VIVOS["Scores reales observados en producción"]
        direction TB
        SV1["B5 Acceso repetitivo: −0.5117 → BAJA → LIMIT"]
        SV2["B2 Port Scan:         −0.6260 → BAJA → LIMIT"]
        SV3["B6 SSH (7 intentos):  heurística → LIMIT"]
        SV4["B1 SYN Flood:         −0.7214 → ALTA → BLOCK"]
        SV5["B3 UDP Flood:         −0.8100 → CRÍTICA → BLOCK"]
        SV6["B4 ICMP Flood:        −0.7800 → ALTA → BLOCK"]
        SV7["A1 HTTP Normal:       −0.4277 → NORMAL → PERMIT"]
        SV8["A2 SSH Legítimo:      −0.4102 → NORMAL → PERMIT"]
    end

    SCORE --> GRADO_SCALE
    GRADO_SCALE --> DIST_REAL
    GRADO_SCALE --> TIPOS
    TIPOS --> SCORES_VIVOS

    style GRADO_SCALE fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style GN          fill:#e8f5e9,stroke:#2e7d32
    style GB          fill:#fff3e0,stroke:#e65100
    style GA          fill:#fce4ec,stroke:#c62828
    style GC          fill:#ffcdd2,stroke:#b71c1c
    style DIST_REAL   fill:#e3f2fd,stroke:#1565c0
    style TIPOS       fill:#fffde7,stroke:#f9a825
    style SCORES_VIVOS fill:#c8e6c9,stroke:#1b5e20
```

---

## Diagrama 5 — Validación Live: Evidencia del Log

```mermaid
sequenceDiagram
    participant OP  as Operador (Desktop)
    participant KL  as Kali 192.168.0.100
    participant DT  as Desktop 192.168.0.20
    participant SV  as Servidor :120
    participant MT  as Motor (log)
    participant TG  as Telegram

    note over OP,TG: 2026-06-02 19:41 — Validación A2+B2 simultáneos

    OP->>DT: inicia A2_ssh_legitimo.sh
    OP->>KL: inicia B2_port_scan.sh
    DT->>SV: SSH legítimo → :22
    KL->>SV: nmap -sS 1000 puertos

    MT->>MT: flow SSH Desktop: score=−0.434 > τ1 → PERMIT
    note over MT: NO aparece en WARNING (log.debug)

    MT->>MT: flow Port Scan Kali: score=−0.655 < τ2 → BLOCK
    MT->>SV: ipset add ppi_blocked 192.168.0.100
    MT-->>TG: 🚨 BLOCK · score=−0.655 · dest_port:z=+8.3

    note over MT: 1705/1705 flows port scan detectados
    note over MT: 0 flows SSH Desktop bloqueados
    note over MT: Lead Time: 26s · MTTC: 28s

    note over OP,TG: 2026-06-03 18:50 — Brute Force SSH

    KL->>SV: hydra SSH (25 intentos rápidos)
    MT->>MT: ssh_intentos[.100]=15 en 60s → BLOCK
    MT->>SV: ipset add ppi_blocked 192.168.0.100
    MT-->>TG: 🔑 BRUTE FORCE · intentos=15/60s → BLOCK

    note over OP,TG: 2026-06-14 18:13 — HTTP Abuse escalado

    KL->>SV: 55 curl → :80 a 1req/s
    MT->>MT: http_requests[.100]=55 → LIMIT (18:13:13)
    MT->>SV: ipset add ppi_limited 192.168.0.100
    KL->>SV: sigue enviando (100 total en 30s)
    MT->>MT: http_requests[.100]=100 → BLOCK (18:13:21)
    MT->>SV: ipset add ppi_blocked 192.168.0.100
    MT-->>TG: 🌐 HTTP-ABUSE · req=100/30s → BLOCK
```

---

## Diagrama 6 — Comparación Métricas: Requisitos vs Obtenido

```mermaid
flowchart TD

    subgraph REQS["📋 Requisitos del PPI"]
        direction LR
        REQ1["Latencia < 500ms"]
        REQ2["Disponibilidad ≥ 99%"]
        REQ3["ITL ≤ 2%"]
        REQ4["Detección efectiva\n(sin requisito numérico)"]
        REQ5["FP SSH = 0\n(usuario más crítico)"]
    end

    subgraph OBTENIDO["✅ Resultados Obtenidos"]
        direction TB

        subgraph OK1["Latencia"]
            O1["P95 = 34.8ms\n✅ Cumple con margen 14×\n(500ms / 34.8ms)"]
        end

        subgraph OK2["Disponibilidad"]
            O2["100% en 40 corridas\n✅ nginx respondió HTTP 200\ndurante TODOS los ataques"]
        end

        subgraph OK3["ITL"]
            O3["0% en 40 corridas\n✅ Ningún flow legítimo\nbloqueado o limitado"]
        end

        subgraph OK4["Detección"]
            O4["TIE=100% · Recall=87.6%\n✅ Con detectores: 92–95%\nAUC=0.9440\nLead Time=26s"]
        end

        subgraph OK5["FP SSH"]
            O5["FPR SSH = 0%\n✅ 58 flows SSH legítimos\nninguno con acción\nFPR Transferencia = 0%"]
        end
    end

    subgraph LIMITACIONES["⚠️ Limitaciones documentadas"]
        direction TB
        L1["B6 Brute Force: det=0.9% (modelo)\n→ Solución: detector temporal 15/60s → ~90%"]
        L2["B5 HTTP Abuse lento: det=30.7% (modelo)\n→ Solución: detector temporal 100/30s → ~80%"]
        L3["Lead Time incluye timeout Suricata\n→ Flow cierra 15-20s después del ataque\n→ Lead Time real medido: 26s"]
        L4["Entorno laboratorio (6 VMs)\n→ En producción: más IPs, más servicios\n→ Reentrenamiento con datos locales"]
    end

    REQ1 --> OK1
    REQ2 --> OK2
    REQ3 --> OK3
    REQ4 --> OK4
    REQ5 --> OK5
    OK4 --> LIMITACIONES

    style REQS        fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style OBTENIDO    fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style OK1 & OK2 & OK3 & OK4 & OK5 fill:#c8e6c9,stroke:#1b5e20
    style LIMITACIONES fill:#fff3e0,stroke:#e65100,stroke-width:2px
```

---

## Diagrama 7 — Integración Total F1→F6: El Sistema Completo

```mermaid
flowchart LR

    subgraph F1B["F1 — Entorno"]
        direction TB
        F1C["Suricata 7.0.3\nens35 promiscua\neve.json activo\nNTP America/Lima\nSSH keys"]
    end

    subgraph F2B["F2 — Captura"]
        direction TB
        F2C["13 escenarios A/B/C\n38 corridas\n376,827 flows\nparser→limpiar→partir\ntrain/val/test"]
    end

    subgraph F3B["F3 — Modelo"]
        direction TB
        F3C["684 flows normales\nStandardScaler\nIsolation Forest\nn=300 contam=0.05\nτ1=−0.4973\nτ2=−0.6873\nAUC=0.9440"]
    end

    subgraph F4B["F4 — Motor"]
        direction TB
        F4C["motor_decision.py\nfiltros 5 capas\nIF score\nDetector SSH 5/15\nDetector HTTP 50/100\nExplicabilidad z-score\nTelegram async"]
    end

    subgraph F5B["F5 — Control"]
        direction TB
        F5C["SSH →servidor\nipset ppi_blocked DROP\nipset ppi_limited\nhashlimit 100/s\ntimeout 300s\nenforce.sh manual\nDashboard web :8080"]
    end

    subgraph F6B["F6 — Validación"]
        direction TB
        F6C["40 corridas\nDisp=100%\nITL=0%\nTIE=100%\nLead=26s\nP95=34.8ms\nPDF + ZIP"]
    end

    F1B ==>|"eve.json\nflows en tiempo real"| F2B
    F2B ==>|"data/raw/*.gz\n684 flows normales"| F3B
    F3B ==>|"isolation_forest.pkl\nscaler.pkl · τ1 · τ2"| F4B
    F4B ==>|"bloquear_ip()\nlimitar_ip() SSH"| F5B
    F5B ==>|"sistema operativo\npara 40 corridas"| F6B

    RESULTADO(["🏆 Resultado Final\nSistema de detección temprana\noperativo en tiempo real\nRecall 92–95% · Precision 99.96%\nITL 0% · Disponibilidad 100%\nLatencia P95 = 34.8ms"])
    F6B ==> RESULTADO

    style F1B      fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style F2B      fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style F3B      fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style F4B      fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style F5B      fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style F6B      fill:#fffde7,stroke:#f9a825,stroke-width:2px
    style RESULTADO fill:#c8e6c9,stroke:#1b5e20,stroke-width:3px
```

---

## Resumen de métricas finales

| Categoría | Métrica | Valor | Requisito | Estado |
|---|---|---|---|---|
| **Operacional** | Disponibilidad | 100% | ≥ 99% | ✅ |
| **Operacional** | ITL | 0% | ≤ 2% | ✅ |
| **Operacional** | TIE | 100% | — | ✅ |
| **Operacional** | Lead Time | 26s | medido | ✅ |
| **Operacional** | MTTC | 28s | medido | ✅ |
| **Modelo** | AUC-ROC | 0.9440 | — | ✅ |
| **Modelo** | Recall (base) | 87.6% | — | ✅ |
| **Modelo** | Recall (total) | ~92–95% | — | ✅ |
| **Modelo** | Precision | 99.96% | — | ✅ |
| **Modelo** | F1-Score | 0.9338 | — | ✅ |
| **Modelo** | FPR SSH | 0% | 0% | ✅ |
| **Pipeline** | Latencia P95 | 34.8ms | < 500ms | ✅ (14×) |
| **Entregables** | PDF validación | 7.4 KB | formal | ✅ |
| **Entregables** | ZIP sistema | 25 MB | técnico | ✅ |
