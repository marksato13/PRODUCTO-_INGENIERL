# Arquitectura de archivos en el sensor — relación con fases

**Sensor:** 192.168.0.110  
**Directorio base:** `/home/m4rk/ppi-surikata-producto/`  
**Verificado:** 2026-06-14

---

```
/home/m4rk/ppi-surikata-producto/
│
├── data/
│   ├── raw/                                ← F2: capturas por corrida (eve.json.gz)
│   │   ├── 20260602_normal_http_01_eve.json.gz
│   │   ├── 20260602_normal_ssh_01_eve.json.gz
│   │   ├── 20260602_normal_transferencia_01_eve.json.gz
│   │   ├── 20260602_normal_sostenido_01_eve.json.gz
│   │   ├── 20260602_anom_synflood_01_eve.json.gz
│   │   ├── 20260602_anom_portscan_01_eve.json.gz
│   │   ├── 20260602_anom_udpflood_01_eve.json.gz
│   │   ├── 20260602_anom_icmpflood_01_eve.json.gz
│   │   ├── 20260602_anom_httpabuse_01_eve.json.gz
│   │   ├── 20260602_anom_bruteforce_01_eve.json.gz
│   │   ├── 20260602_mixto_http_syn_01_eve.json.gz
│   │   ├── 20260602_mixto_ssh_portscan_01_eve.json.gz
│   │   ├── 20260602_mixto_descarga_udp_01_eve.json.gz
│   │   └── ... (normal_ssh 03-10, normal_transferencia 03-10)
│   │
│   ├── dataset_raw.csv                     ← F2: salida de parser.py
│   ├── dataset_labeled.csv                 ← F2: salida de etiquetar_limpiar.py
│   ├── dataset_clean.csv                   ← F2: limpio y deduplicado (376,827 flows)
│   ├── train.csv                           ← F2: partición 70% cronológico
│   ├── val.csv                             ← F2: partición 15% cronológico
│   ├── test.csv                            ← F2: partición 15% cronológico
│   └── resumen_estadistico.txt             ← F2: estadísticas del dataset
│
├── models/
│   ├── isolation_forest.pkl                ← F3: modelo entrenado (n_estimators=300)
│   ├── scaler.pkl                          ← F3: StandardScaler (fit en 684 flows normales)
│   └── features.csv                        ← F3: lista de 14 features usadas
│
├── scripts/
│   ├── capture/
│   │   └── exportar_eve_por_escenario.sh   ← F2: gzip + truncate + suricatasc reopen-log
│   ├── evaluation/
│   │   └── registrar_bitacora.sh           ← F2: escribe línea en bitácora_escenarios.txt
│   ├── validation/
│   │   ├── revisar_suricata.sh             ← F1: verificación de Suricata
│   │   └── suricata_revision.txt
│   │
│   ├── parser.py                           ← F2: eve.json.gz → dataset_raw.csv
│   ├── etiquetar_limpiar.py                ← F2: raw → labeled → clean (dedup, filtros IP)
│   ├── particionar_estadisticos.py         ← F2: partición cronológica 70/15/15
│   │
│   ├── fase3_isolation_forest.py           ← F3: entrena IF, guarda isolation_forest.pkl + scaler.pkl
│   ├── auc_roc_umbrales.py                 ← F3/F4: deriva τ1/τ2 desde curva ROC
│   │
│   ├── clasificador.py                     ← F2/F4: 7 tipos anomalía + CVSS v3.1 + MITRE
│   ├── motor_decision.py                   ← F4+F5: pipeline en tiempo real (tail eve.json → ipset)
│   ├── enforce.sh                          ← F5: control manual ipset BLOCK|LIMIT|UNBLOCK
│   ├── dashboard.py                        ← F4: live stats desde motor_decision.log
│   │
│   ├── f6_corridas.py                      ← F6: automatiza 40 corridas
│   ├── auc_por_escenario.py                ← F6: AUC-ROC desglosado por escenario
│   ├── generar_pdf_final.py                ← F6: genera reporte_validacion_final.pdf
│   └── generar_pdf_zip.py                  ← F6: genera MVP_funcional.zip
│
├── results/
│   ├── motor_decision.log                  ← F4: log en tiempo real (PERMIT/LIMIT/BLOCK)
│   ├── umbrales_finales.txt                ← F4: τ1=-0.4973 · τ2=-0.6873 formalizados
│   ├── latencia_pipeline.txt               ← F4: mean=34.533ms · P95=34.768ms
│   ├── isolation_forest_resultado.png      ← F3: visualización de scores
│   ├── resultados_normal.csv               ← F6: corridas 1-10 (ITL=0%)
│   ├── resultados_mixto.csv                ← F6: corridas 11-20 (TIE=100%)
│   ├── resultados_reeval.csv               ← F6: corridas 21-30 (τ1/τ2 consistentes)
│   ├── resultados_final.csv                ← F6: corridas 31-40
│   ├── resultados_f6_completo.csv          ← F6: 40 corridas consolidadas (entregable)
│   ├── reporte_validacion_final.pdf        ← F6: PDF entregable formal (7.4 KB)
│   ├── MVP_funcional.zip                   ← F6: ZIP sistema completo (25 MB, 40 archivos)
│   ├── figures/
│   │   └── auc_roc_umbrales.png            ← F3/F4: curva ROC con τ1 y τ2
│   ├── sensibilidad/
│   │   ├── sensibilidad_n_flows.csv        ← F3: AUC vs N flows (N=50..1500)
│   │   └── sensibilidad_n_flows.png
│   ├── analisis_escenarios/
│   │   ├── scores_por_escenario.json       ← F3/F6: distribución de scores
│   │   ├── stats_por_escenario.json
│   │   ├── stats_por_grupo.json
│   │   ├── clasificacion_tipos.json
│   │   ├── cohensd.json
│   │   ├── rangos_clasificacion.json
│   │   └── generalizacion_ataques_no_entrenados.json  ← F2: experimento 12/12
│   ├── tables/
│   │   └── metricas_por_escenario.csv      ← F6: AUC/Recall/Precision por ataque
│   └── reports/
│       ├── auc_por_escenario.txt           ← F6: AUC desglosado (B3=0.9905..B6=0.6770)
│       ├── reporte_metricas_v1.txt         ← F3: métricas offline
│       └── reporte_validacion_fase6.txt    ← F6: reporte formal de validación
│
├── docs/
│   ├── bitacora/
│   │   └── bitacora_escenarios.txt         ← F2: registro de 49 corridas documentadas
│   ├── plan_captura.txt                    ← F1/F2: plan original de captura
│   ├── guion_ataques.txt                   ← F2: guión detallado de ataques
│   └── info/
│       └── carpetas_y_proposito.txt        ← F1: documentación interna
│
└── README.txt
```

---

## Relación fases → archivos

| Fase | Descripción | Produce | Consume |
|---|---|---|---|
| **F1** | Entorno de laboratorio | `docs/`, Suricata activo en ens35 | — |
| **F2** | Captura y preprocesamiento | `data/raw/*.gz`, `dataset_*.csv`, `train/val/test.csv` | `eve.json` (Suricata) |
| **F3** | Modelado offline | `models/*.pkl`, `results/figures/`, `results/sensibilidad/` | `train.csv` |
| **F4** | Motor de decisión | `results/motor_decision.log`, `results/umbrales_finales.txt` | `models/*.pkl` + `eve.json` live |
| **F5** | Control inline | Bloqueos ipset en servidor (.120) | Decisiones de `motor_decision.py` |
| **F6** | Validación | `results/resultados_*.csv`, `reporte_validacion_final.pdf`, `MVP_funcional.zip` | Todo el pipeline activo |

---

## Pipeline de datos — flujo completo

```
Suricata ens35 → /var/log/suricata/eve.json
    │
    ├─ [F2] exportar_eve_por_escenario.sh → data/raw/FECHA_tipo_escenario_NN_eve.json.gz
    ├─ [F2] parser.py                     → data/dataset_raw.csv
    ├─ [F2] etiquetar_limpiar.py          → data/dataset_clean.csv  (376,827 flows)
    ├─ [F2] particionar_estadisticos.py   → data/train.csv / val.csv / test.csv
    │
    ├─ [F3] fase3_isolation_forest.py     → models/isolation_forest.pkl + scaler.pkl
    ├─ [F3] auc_roc_umbrales.py           → τ1=-0.4973 · τ2=-0.6873
    │
    ├─ [F4] motor_decision.py (live)      → results/motor_decision.log
    │        └─ score > τ1  → PERMIT
    │        └─ τ2 < score ≤ τ1 → LIMIT
    │        └─ score ≤ τ2 → BLOCK
    │
    ├─ [F5] enforce.sh / bloquear_ip()   → ipset ppi_blocked / ppi_limited en .120
    │
    └─ [F6] f6_corridas.py (40 corridas) → results/resultados_f6_completo.csv
             auc_por_escenario.py         → results/reports/auc_por_escenario.txt
             generar_pdf_final.py         → results/reporte_validacion_final.pdf
             generar_pdf_zip.py           → results/MVP_funcional.zip
```

---

## Nomenclatura de capturas en `data/raw/`

```
YYYYMMDD_<grupo>_<escenario>_NN_eve.json.gz

Grupos:   normal | anom | mixto
Escenarios normal:  http · ssh · transferencia · sostenido
Escenarios anom:    synflood · portscan · udpflood · icmpflood · httpabuse · bruteforce
Escenarios mixto:   http_syn · ssh_portscan · descarga_udp

Ejemplos:
  20260602_normal_http_01_eve.json.gz
  20260602_anom_synflood_01_eve.json.gz
  20260602_mixto_ssh_portscan_01_eve.json.gz
```
