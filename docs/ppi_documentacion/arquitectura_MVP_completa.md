# Arquitectura Completa del MVP — Rutas, Fases y Scripts

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Sensor:** 192.168.0.110 | Directorio base: `/home/m4rk/ppi-surikata-producto/`  
**Última actualización:** 15 de junio 2026  

---

## Diagrama 1 — Árbol de Directorios por Fase

```mermaid
flowchart TD

    ROOT["/home/m4rk/ppi-surikata-producto/"]

    subgraph DATA["data/  ← F2"]
        direction TB
        RAW_D["raw/  38 archivos .gz\nYYYYMMDD_grupo_escenario_NN_eve.json.gz\nnormal · anom · mixto"]
        CSV1["dataset_raw.csv     412,097 flows  75MB"]
        CSV2["dataset_clean.csv   376,827 flows  69MB"]
        CSV3["train.csv           263,778 flows  48MB  (70%)"]
        CSV4["val.csv              56,524 flows  11MB  (15%)"]
        CSV5["test.csv             56,525 flows  11MB  (15%)"]
        RAW_D --- CSV1 --- CSV2 --- CSV3 --- CSV4 --- CSV5
    end

    subgraph MODELS["models/  ← F3"]
        direction TB
        M1["isolation_forest.pkl  2.5MB\nBorn: 2026-06-02  Mod: 2026-06-04"]
        M2["scaler.pkl            1.4KB\nStandardScaler fit en 684 normales"]
        M3["features.csv          152B\n14 features en orden"]
    end

    subgraph SCRIPTS["scripts/  ← F2-F6"]
        direction TB

        subgraph SC_CAP["capture/  ← F2"]
            SC1["A1_http_normal.sh · A2_ssh_legitimo.sh\nA3_transferencia_legitima.sh\nA4_trafico_sostenido.sh\nB1_syn_flood.sh · B2_port_scan.sh\nB3_udp_flood.sh · B4_icmp_flood.sh\nB5_acceso_repetitivo.sh · B6_bruteforce.sh\nC1_http_syn_mixto.sh · C2_ssh_portscan_mixto.sh\nC3_descarga_udp_mixto.sh\nexportar_eve_por_escenario.sh"]
        end

        subgraph SC_ML["ML Pipeline  ← F2-F3"]
            SC2["parser.py\netiquetar_limpiar.py\nparticionar_estadisticos.py\nfase3_isolation_forest.py\nauc_roc_umbrales.py\nauc_por_escenario.py"]
        end

        subgraph SC_MOTOR["Motor + Control  ← F4-F5"]
            SC3["motor_decision.py  547 líneas\n(F4+F5 integrados)\nenforce.sh"]
        end

        subgraph SC_DASH["Dashboard  ← F5"]
            SC4["dashboard.py       (terminal)\ndashboard_web.py   (Flask :8080 SSE)"]
        end

        subgraph SC_VAL["Validación  ← F6"]
            SC5["f6_corridas.py\nclasificador.py\ngenerar_pdf_final.py\ngenerar_pdf_zip.py"]
        end

        subgraph SC_EVAL["Evaluación  ← F3-F6"]
            SC6["scripts/evaluation/\nregistrar_bitacora.sh"]
        end
    end

    subgraph RESULTS["results/  ← F3-F6"]
        direction TB
        R1["motor_decision.log     7.6MB\nresultados_f6_completo.csv  3.9KB\numbrales_finales.txt   1.9KB"]
        R2["reports/\nreporte_metricas_v1.txt\nauc_por_escenario.txt\ncomparacion_modelos_f401.csv\nf403_fp_fn_overfitting.json\nreporte_validacion_fase6.txt"]
        R3["reporte_validacion_final.pdf  7.4KB\nMVP_funcional.zip  25MB"]
        R1 --- R2 --- R3
    end

    subgraph DOCS["docs/  ← Documentación"]
        direction TB
        D1["bitacora/bitacora_escenarios.txt\n49 corridas registradas"]
        D2["ppi_documentacion/\nF1-F6 · overview · arquitectura\nDIAGRAMAS/ por fase (Mermaid)"]
        D3["info/ · evidencia/"]
    end

    subgraph SERVICES["systemd services  ← F4-F5"]
        direction TB
        SV1["/etc/systemd/system/\nppi-motor.service\nppi-dashboard.service"]
    end

    subgraph VENV["Python venv  ← F3-F4"]
        direction TB
        VE1["/home/m4rk/ppi-sensor/venv/\npython3 · scikit-learn 1.8.0\njoblib · numpy · flask"]
    end

    ROOT --> DATA & MODELS & SCRIPTS & RESULTS & DOCS
    SCRIPTS --- SERVICES
    SCRIPTS --- VENV

    style DATA     fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style MODELS   fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style SCRIPTS  fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style RESULTS  fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style DOCS     fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style SERVICES fill:#efebe9,stroke:#4e342e
    style VENV     fill:#fffde7,stroke:#f9a825
```

---

## Diagrama 2 — Qué script produce qué artefacto

```mermaid
flowchart LR

    subgraph F2_SC["F2 — Scripts de captura y procesamiento"]
        direction TB
        EXP["exportar_eve_por_escenario.sh\n→ data/raw/FECHA_grupo_esc_NN.gz\n→ docs/bitacora/bitacora_escenarios.txt"]
        PRS["parser.py\n→ data/dataset_raw.csv  (412K flows)"]
        ETQ["etiquetar_limpiar.py\n→ data/dataset_clean.csv  (377K flows)"]
        PAR["particionar_estadisticos.py\n→ data/train.csv  (264K)\n→ data/val.csv   (57K)\n→ data/test.csv  (57K)"]
        EXP --> PRS --> ETQ --> PAR
    end

    subgraph F3_SC["F3 — Scripts de modelado"]
        direction TB
        F3S["fase3_isolation_forest.py\n→ models/isolation_forest.pkl\n→ models/scaler.pkl\n→ models/features.csv\n→ results/isolation_forest_resultado.png"]
        AUC["auc_roc_umbrales.py\n→ results/umbrales_finales.txt\n→ results/figures/auc_roc_umbrales.png\n→ results/reports/reporte_metricas_v1.txt"]
        AUCES["auc_por_escenario.py\n→ results/reports/auc_por_escenario.txt"]
        F3S --> AUC --> AUCES
    end

    subgraph F4F5_SC["F4+F5 — Motor y control"]
        direction TB
        MOT["motor_decision.py\n→ results/motor_decision.log\n→ SSH: ipset add ppi_blocked/ppi_limited\n→ Telegram alertas async"]
        ENF["enforce.sh\n→ ipset add/del manual"]
        DSHW["dashboard_web.py\n→ HTTP :8080 Flask SSE"]
        DSHT["dashboard.py\n→ terminal stats cada 3s"]
        MOT --> ENF
        MOT --> DSHW & DSHT
    end

    subgraph F6_SC["F6 — Validación y entregables"]
        direction TB
        F6S["f6_corridas.py\n→ results/resultados_normal.csv\n→ results/resultados_mixto.csv\n→ results/resultados_reeval.csv\n→ results/resultados_final.csv\n→ results/resultados_f6_completo.csv"]
        PDF["generar_pdf_final.py\n→ results/reporte_validacion_final.pdf"]
        ZIP["generar_pdf_zip.py\n→ results/MVP_funcional.zip  25MB"]
        F6S --> PDF --> ZIP
    end

    F2_SC ==>|"train.csv → filtro\n684 flows normales"| F3_SC
    F3_SC ==>|"*.pkl + τ1/τ2"| F4F5_SC
    F4F5_SC ==>|"motor_decision.log\nipset activos"| F6_SC

    style F2_SC  fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style F3_SC  fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style F4F5_SC fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style F6_SC  fill:#fffde7,stroke:#f9a825,stroke-width:2px
```

---

## Árbol de archivos clave (texto)

```
/home/m4rk/ppi-surikata-produto/          ← directorio del motor (sin 'c')
└── scripts/motor_decision.py              ← script en producción (symlink o copia)

/home/m4rk/ppi-surikata-producto/         ← repositorio git
├── data/
│   ├── raw/         38 .gz               ← F2: corridas capturadas
│   ├── dataset_clean.csv    69MB         ← F2: dataset limpio
│   ├── train.csv            48MB         ← F2: partición entrenamiento
│   ├── val.csv              11MB         ← F2: validación
│   └── test.csv             11MB         ← F3: evaluación modelo
│
├── models/
│   ├── isolation_forest.pkl  2.5MB       ← F3: modelo v2 (2026-06-04)
│   ├── scaler.pkl            1.4KB       ← F3: scaler fit en 684 normales
│   └── features.csv          152B        ← F3: orden de las 14 features
│
├── scripts/
│   ├── capture/                          ← F2: A1-A4, B1-B6, C1-C3
│   │   └── exportar_eve_por_escenario.sh
│   ├── parser.py                         ← F2
│   ├── etiquetar_limpiar.py              ← F2
│   ├── particionar_estadisticos.py       ← F2
│   ├── fase3_isolation_forest.py         ← F3
│   ├── auc_roc_umbrales.py              ← F3
│   ├── auc_por_escenario.py             ← F3
│   ├── motor_decision.py   547L         ← F4+F5 (núcleo del sistema)
│   ├── enforce.sh                        ← F5: control manual
│   ├── dashboard.py                      ← F5: terminal
│   ├── dashboard_web.py                  ← F5: Flask :8080
│   ├── f6_corridas.py                   ← F6: 40 corridas
│   ├── generar_pdf_final.py             ← F6
│   └── generar_pdf_zip.py               ← F6
│
├── results/
│   ├── motor_decision.log    7.6MB       ← F4: log en tiempo real
│   ├── umbrales_finales.txt  1.9KB       ← F3: τ1/τ2 + heurísticas
│   ├── resultados_f6_completo.csv 3.9KB  ← F6: 40 corridas
│   ├── reporte_validacion_final.pdf 7.4KB← F6: entregable académico
│   ├── MVP_funcional.zip     25MB        ← F6: entregable técnico
│   └── reports/
│       ├── reporte_metricas_v1.txt       ← F3: AUC, Recall, FPR
│       ├── auc_por_escenario.txt         ← F3: AUC por B1-B6 C1-C3
│       └── comparacion_modelos_f401.csv  ← F4: IF vs RF vs SVM vs DT vs LR
│
└── docs/
    ├── bitacora/bitacora_escenarios.txt  ← F2: 49 corridas
    └── ppi_documentacion/               ← Documentación completa F1-F6
        ├── overview_fases.md
        ├── arquitectura_MVP_completa.md
        ├── ENTREGABLES_POR_FASE.md
        ├── F1_entorno_laboratorio/DIAGRAMAS/F1_entorno_laboratorio.md
        ├── F2_captura_trafico/DIAGRAMAS/F2_captura_trafico.md
        ├── F3_modelado_offline/DIAGRAMAS/F3_modelado_offline.md
        ├── F4_motor_decision/DIAGRAMAS/F4_motor_decision.md
        ├── F5_control_inline/DIAGRAMAS/F5_control_inline.md
        └── F6_validacion/DIAGRAMAS/F6_validacion.md
```

---

## Nota sobre dos directorios en el sensor

| Directorio | Git | Motor activo | Descripción |
|---|---|---|---|
| `ppi-surikata-producto/` | ✅ Sí | No directamente | Repositorio git · docs · scripts · modelos |
| `ppi-surikata-produto/` | ❌ No | ✅ Sí (ppi-motor.service) | WorkingDirectory del systemd service |

El servicio `ppi-motor.service` usa `WorkingDirectory=/home/m4rk/ppi-surikata-producto` (con 'c'). Los archivos pkl y scripts están sincronizados entre ambos.
