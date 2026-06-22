# Arquitectura del Proyecto — PPI UPeU 2026

**Sistema de detección temprana de anomalías en redes mediante Isolation Forest + control inline**  
**Estudiante:** Rubén Mark Salazar Tocas  
**Sensor:** 192.168.0.110 — Ubuntu 22.04 — `/home/m4rk/ppi-surikata-producto/`

---

## Árbol de carpetas y archivos

```
ppi-surikata-producto/
│
├── ARQUITECTURA.md                    ← este archivo
├── CLAUDE.md                          ← instrucciones para Claude Code
├── README.txt                         ← descripción general del proyecto
├── requirements.txt                   ← dependencias Python (venv en ~/ppi-sensor/venv)
├── .gitignore
│
├── config/                            ← configuración del sistema
│   ├── whitelist.conf                 ← IPs que nunca se bloquean
│   ├── telegram.conf                  ← token + chat_id para alertas
│   ├── modelo_activo.txt              ← qué modelo usa el motor (IF)
│   └── systemd/
│       ├── ppi-motor.service          ← motor_decision.py como servicio
│       ├── ppi-dashboard.service      ← dashboard_web.py como servicio
│       └── ppi-predictor.service      ← predictor.py como servicio
│
├── data/                              ← datos del proyecto
│   ├── normal_holdout.csv             ← 13,427 flujos normales (20% holdout IF)
│   ├── dataset_comparacion.csv        ← 25,428 flujos normal+anómalo etiquetados
│   ├── series_gap_sesiones.csv        ← análisis temporal de gaps entre sesiones
│   ├── raw/                           ← capturas eve.json comprimidas por corrida
│   │   ├── YYYYMMDD_normal_http_NN_eve.json.gz
│   │   ├── YYYYMMDD_anom_synflood_NN_eve.json.gz
│   │   └── ...  (47 capturas totales — A1-A4, B1-B6, C1-C3)
│   └── [*.npy]                        ← arrays numpy para comparación AE (secundario)
│
├── models/                            ← modelos entrenados
│   ├── isolation_forest.pkl           ← IF n=300, entrenado 53,708 flujos normales
│   ├── scaler.pkl                     ← StandardScaler ajustado en F2
│   ├── features.csv                   ← 14 features del IF
│   ├── predictor_modelo_v2.pkl        ← XGBoost v2 (9 features, AUC=0.9992)
│   ├── features_predictor_v2.txt      ← 9 features del XGBoost v2
│   ├── predictor_tipo.txt             ← tipo de predictor activo
│   └── ae/                            ← Autoencoder (comparación, no en producción)
│       ├── ae_autoencoder.pkl
│       └── ae_scaler.pkl
│
├── results/                           ← salidas de todos los scripts
│   ├── metricas_offline.txt           ← AUC=0.8998, τ1=-0.4459, τ2=-0.6027  [F2]
│   ├── umbrales_finales.txt           ← copia canónica de τ1/τ2
│   ├── latencia_pipeline.txt          ← P95=34.8ms, throughput 29 flows/s  [F3]
│   ├── motor_decision.log             ← log en tiempo real: PERMIT/LIMIT/BLOCK  [F3]
│   ├── block_counts.json              ← contador bloqueos por IP (prog. #1/#2/#3)  [F3]
│   ├── auc_roc.png                    ← curva ROC del IF  [F2]
│   ├── metricas_predictor_v2.txt      ← AUC=0.9992, 7FP+7FN  [F4]
│   ├── metricas_f5_if.txt             ← métricas post-reentrenamiento IF  [F5]
│   ├── metricas_f5_xgboost.txt        ← métricas post-reentrenamiento XGBoost  [F5]
│   ├── cron_f5_xgb.log                ← log de ejecuciones cron F5  [F5]
│   ├── resultados_f6_completo.csv     ← 40 corridas validación  [F6]
│   ├── resultados_f6_README.txt       ← descripción de columnas del CSV  [F6]
│   ├── predictor.log                  ← log del predictor XGBoost en tiempo real
│   ├── graficas_f6/                   ← 7 figuras PNG 300 DPI para informe  [F6]
│   │   ├── f6_01_disponibilidad.png
│   │   ├── f6_02_flows_anomalos.png
│   │   ├── f6_03_timeline_deteccion.png
│   │   ├── f6_04_itl.png
│   │   ├── f6_05_flujos_acumulados.png
│   │   ├── f6_06_latencia_pipeline.png
│   │   └── f6_07_panel_resumen.png
│   └── eda/                           ← gráficas de análisis exploratorio  [F1]
│       ├── eda_01_distribuciones.png
│       ├── eda_02_protocolo.png
│       ├── eda_03_boxplots.png
│       ├── eda_04_correlacion.png
│       ├── eda_05_dest_ports.png
│       └── eda_06_stats_tabla.png
│
├── scripts/                           ← todos los scripts del pipeline
│   │
│   ├── [F1 — Captura de datos]
│   ├── capture/
│   │   ├── exportar_eve_por_escenario.sh   ← gzip + truncate + reopen-log al fin de corrida
│   │   ├── A1_http_normal.sh               ← tráfico curl/wget normal 10 min
│   │   ├── A2_ssh_legitimo.sh              ← SSH legítimo 8 min
│   │   ├── A3_transferencia_legitima.sh    ← scp/wget 10 min
│   │   ├── A4_trafico_sostenido.sh         ← curl+ssh mixto 15 min
│   │   ├── B1_syn_flood.sh                 ← hping3 -S --flood → :80
│   │   ├── B2_port_scan.sh                 ← nmap -sS
│   │   ├── B3_udp_flood.sh                 ← hping3 --udp --flood → :53
│   │   ├── B4_icmp_flood.sh                ← hping3 -1 --flood
│   │   ├── B5_acceso_repetitivo.sh         ← curl bucle rápido → :80
│   │   ├── B6_bruteforce.sh                ← hydra → :22
│   │   ├── C1_http_syn_mixto.sh            ← Desktop+Kali simultáneo
│   │   ├── C2_ssh_portscan_mixto.sh
│   │   ├── C3_descarga_udp_mixto.sh
│   │   ├── run_A1_A4.sh                    ← lanzador secuencial grupo A
│   │   └── deploy_kali.sh                  ← instala herramientas en Kali
│   │
│   ├── [F1 — Análisis exploratorio]
│   ├── eda_features.py                     ← genera eda_01..06 en results/eda/
│   │
│   ├── [F2 — Detección con Isolation Forest]
│   ├── fase3_entrenar.py                   ← 53,708 flujos → IF pkl + scaler pkl
│   ├── fase3_evaluar.py                    ← holdout+anomalías → AUC, τ1/τ2
│   │
│   ├── [F3 — Motor de decisión + enforcement]
│   ├── motor_decision.py                   ← tail eve.json → IF → PERMIT/LIMIT/BLOCK
│   ├── enforce.sh                          ← control manual ipset BLOCK/LIMIT/UNBLOCK
│   ├── dashboard.py                        ← estadísticas terminal cada 3s
│   ├── dashboard_web.py                    ← Flask+SSE en :8080
│   │
│   ├── [F4 — Predictor XGBoost v2]
│   ├── f4_entrenar_predictor_v2.py         ← motor_decision.log → XGBoost pkl
│   │
│   ├── [F5 — Aprendizaje continuo]
│   ├── f5_reentrenar_if.py                 ← reentrenamiento incremental IF
│   ├── f5_reentrenar_xgboost.py            ← reentrenamiento incremental XGBoost
│   ├── f5_validar_modelo.py                ← valida modelo post-retrain
│   │
│   ├── [F6 — Validación]
│   ├── f6_corridas.py                      ← batch 40 corridas → resultados_f6_completo.csv
│   ├── auc_por_escenario.py                ← AUC-ROC desglosado por escenario
│   ├── generar_graficas_f6.py              ← 7 PNG 300 DPI para informe
│   │
│   ├── [Auxiliares]
│   ├── generar_informe_pdf.py              ← genera PDF del informe
│   ├── generar_slides_defensa.py           ← genera PPTX defensa
│   ├── motor_universal.py                  ← versión genérica del motor (experimental)
│   │
│   ├── evaluation/
│   │   └── registrar_bitacora.sh           ← escribe línea en bitacora_escenarios.txt
│   │
│   └── validacion/                         ← suite de pruebas por fase
│       ├── run_all.sh                      ← ejecuta F1→F6 completo
│       ├── f1_val_captura.sh               ← Suricata activo, eve.json creciendo
│       ├── f2_val_modelo_if.sh             ← AUC≥0.85, TPR≥0.95, FPR≤0.25
│       ├── f3_val_motor.sh                 ← latencia P95<500ms, τ cargados
│       ├── f3_val_ipset.sh                 ← whitelist protegida, bloqueo #3 permanente
│       ├── f4_val_predictor.sh             ← AUC≥0.95, FP+FN≤30
│       ├── f5_val_reentrenamiento.sh       ← cron configurado, métricas f5 existen
│       ├── f6_val_corridas.sh              ← 40 corridas, disponibilidad 100%
│       ├── _f2_if_check.py                 ← helper Python para f2_val_modelo_if.sh
│       └── _f4_xgb_check.py               ← helper Python para f4_val_predictor.sh
│
└── docs/
    ├── PLAN_MAESTRO.md                     ← plan original del PPI
    ├── bitacora/
    │   └── bitacora_escenarios.txt         ← registro de todas las corridas
    │
    ├── ppi_documentacion2/                 ← documentación principal (versión final)
    │   ├── INDICE.md                       ← índice visual F1→F6 con métricas
    │   ├── ejemplo_flujo_completo.md       ← walkthrough B1 SYN flood y B6 BF SSH
    │   │
    │   ├── fases/                          ← doc técnica de cada fase
    │   │   ├── F1_captura_datos.md
    │   │   ├── F2_deteccion_if.md
    │   │   ├── F3_control_motor.md
    │   │   ├── F4_prediccion_v2.md
    │   │   ├── F5_aprendizaje.md
    │   │   └── F6_validacion.md
    │   │
    │   ├── validacion/                     ← plan y resultados de validación
    │   │   ├── PLAN_VALIDACION.md          ← 16 CAs, orden de ejecución
    │   │   ├── RESULTADOS_VALIDACION.md    ← tabla PASS/FAIL 15/16 verificados
    │   │   ├── f2_val_modelo_if.md         ← F2: IF offline con valores reales
    │   │   ├── f2_val_datos_nuevos.md      ← F2: FPR con captura normal nueva
    │   │   ├── f3_val_motor.md             ← F3: motor latencia e ITL
    │   │   ├── f3_val_ipset.md             ← F3: enforcement whitelist y prog.
    │   │   ├── f4_val_predictor.md         ← F4: XGBoost AUC y matriz confusión
    │   │   └── f6_val_escenarios.md        ← F6: escenarios A/B/C y lead times
    │   │
    │   ├── informe/                        ← partes del informe escrito
    │   │   ├── parte_i_introduccion.md
    │   │   ├── parte_ii_marco_teorico.md
    │   │   ├── parte_iii_metodologia.md
    │   │   ├── parte_iv_resultados.md
    │   │   ├── parte_v_conclusiones.md
    │   │   └── plan_redaccion.md
    │   │
    │   ├── ppt/                            ← presentación de sustentación
    │   │   ├── ppt_sustentacion.md         ← 14 slides con contenido real
    │   │   ├── d1_topologia.md             ← draw.io XML topología de red
    │   │   ├── d2_pipeline.md              ← draw.io XML pipeline F1→F6
    │   │   ├── d3_flujo.md                 ← draw.io XML flujo de decisión IF
    │   │   └── d4_problema.md              ← draw.io XML antes/después
    │   │
    │   └── defensa/
    │       ├── checklist_defensa.md        ← lista de verificación para el día
    │       └── LIMITACIONES.md             ← limitaciones del sistema documentadas
    │
    └── respuestas_asesor/                  ← respuestas formales a preguntas asesores
        ├── 01_DATA_ENGINEERING.md
        ├── 02_ESCENARIOS_Y_PARAMETROS.md
        ├── 03_ALCANCE_Y_ATAQUES.md
        ├── 04_PARADIGMA_ONE_CLASS.md
        ├── 05_EDA_FEATURES.md
        ├── 06_REFERENCIAS_FORMALES.md
        └── 07_DEFENSA_PREGUNTAS_FORMALES.md
```

---

## Pipeline de ejecución (orden correcto)

```
F1  scripts/capture/A1_http_normal.sh       → data/raw/*.json.gz
    scripts/eda_features.py                 → results/eda/

F2  scripts/fase3_entrenar.py               → models/isolation_forest.pkl + scaler.pkl
    scripts/fase3_evaluar.py                → results/metricas_offline.txt + auc_roc.png

F3  sudo systemctl start ppi-motor.service  → results/motor_decision.log (continuo)
    scripts/enforce.sh <ip> BLOCK|LIMIT|UNBLOCK

F4  scripts/f4_entrenar_predictor_v2.py     → models/predictor_modelo_v2.pkl
                                              results/metricas_predictor_v2.txt

F5  scripts/f5_reentrenar_if.py             → models/isolation_forest.pkl (actualizado)
    scripts/f5_reentrenar_xgboost.py        → models/predictor_modelo_v2.pkl (actualizado)
    [cron 03:00 diario]

F6  scripts/f6_corridas.py                  → results/resultados_f6_completo.csv
    scripts/auc_por_escenario.py            → results/reports/auc_por_escenario.txt
    scripts/generar_graficas_f6.py          → results/graficas_f6/*.png
```

---

## Validación por fase (ejecutable)

```bash
# Validar todo (F1→F6):
bash scripts/validacion/run_all.sh

# Validar fase individual:
bash scripts/validacion/f1_val_captura.sh
bash scripts/validacion/f2_val_modelo_if.sh
bash scripts/validacion/f3_val_motor.sh
bash scripts/validacion/f3_val_ipset.sh
bash scripts/validacion/f4_val_predictor.sh
bash scripts/validacion/f5_val_reentrenamiento.sh
bash scripts/validacion/f6_val_corridas.sh
```

---

## Métricas clave (validadas 2026-06-22)

| Fase | Componente            | Métrica principal       | Valor       |
|------|-----------------------|-------------------------|-------------|
| F1   | Suricata 7.0.3        | Flujos capturados        | 667,420     |
| F2   | Isolation Forest n=300| AUC-ROC                 | **0.8998**  |
| F2   | IF τ1 (Youden)        | TPR / FPR               | 99.40% / 20.47% |
| F3   | Motor pipeline        | Latencia P95            | **34.8ms**  |
| F3   | Enforcement           | Disponibilidad          | **100%**    |
| F4   | XGBoost v2 (9 feat.)  | AUC-ROC                 | **0.9992**  |
| F4   | XGBoost test 12,488   | FP + FN                 | **14**      |
| F5   | Reentrenamiento       | Cron 03:00 diario       | configurado |
| F6   | 40 corridas           | Disponibilidad / ITL    | **100% / 0%** |
| F6   | Lead time SYN flood   | T → primer BLOCK        | **~62s**    |
| F6   | Lead time BF SSH      | T → primer BLOCK        | **~60s**    |
