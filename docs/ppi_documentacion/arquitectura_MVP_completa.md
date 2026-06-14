# Arquitectura Completa del MVP — Rutas, Fases y Estado del ZIP

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Sensor:** 192.168.0.110 | Directorio base: `/home/m4rk/ppi-surikata-producto/`  
**Fecha de inventario:** 2026-06-14  
**ZIP actual:** `MVP_funcional.zip` — generado 2026-06-04, **desactualizado**

---

## Leyenda

| Símbolo | Significado |
|---|---|
| ✅ ZIP | Archivo presente en MVP_funcional.zip y actualizado |
| ⚠️ OLD | Presente en ZIP pero versión antigua (modificado después del 2026-06-04) |
| ❌ FALTA | Existe en el sensor, NO está en el ZIP |
| 📁 | Carpeta (no se zipa vacía) |

---

## Árbol completo con anotación de fase

```
/home/m4rk/ppi-surikata-producto/
│
├── README.txt                                          F1  ✅ ZIP
│
├── .gitignore                                          —   ❌ FALTA (nuevo, 2026-06-14)
│
├── config/                                             📁  ❌ FALTA (vacía)
│
├── data/
│   ├── raw/                                            F2  capturas por corrida
│   │   ├── 20260602_normal_http_01_eve.json.gz         F2  ❌ FALTA
│   │   ├── 20260602_normal_http_02_eve.json.gz         F2  ❌ FALTA
│   │   ├── 20260602_normal_ssh_01_eve.json.gz          F2  ❌ FALTA
│   │   ├── 20260602_normal_ssh_02_eve.json.gz          F2  ❌ FALTA
│   │   ├── 20260602_normal_transferencia_01_eve.json.gz F2  ❌ FALTA
│   │   ├── 20260602_normal_transferencia_02_eve.json.gz F2  ❌ FALTA
│   │   ├── 20260602_normal_sostenido_01_eve.json.gz    F2  ❌ FALTA
│   │   ├── 20260602_normal_sostenido_02_eve.json.gz    F2  ❌ FALTA
│   │   ├── 20260602_anom_synflood_01_eve.json.gz       F2  ❌ FALTA
│   │   ├── 20260602_anom_portscan_01_eve.json.gz       F2  ❌ FALTA
│   │   ├── 20260602_anom_udpflood_01_eve.json.gz       F2  ❌ FALTA
│   │   ├── 20260602_anom_icmpflood_01_eve.json.gz      F2  ❌ FALTA
│   │   ├── 20260602_anom_httpabuse_01_eve.json.gz      F2  ❌ FALTA
│   │   ├── 20260602_anom_bruteforce_01_eve.json.gz     F2  ❌ FALTA
│   │   ├── 20260602_mixto_http_syn_01_eve.json.gz      F2  ❌ FALTA
│   │   ├── 20260602_mixto_ssh_portscan_01_eve.json.gz  F2  ❌ FALTA
│   │   ├── 20260602_mixto_descarga_udp_01_eve.json.gz  F2  ❌ FALTA
│   │   ├── 20260603_anom_bruteforce_01_eve.json.gz     F2  ❌ FALTA
│   │   ├── 20260604_normal_ssh_03..10_eve.json.gz      F2  ❌ FALTA (8 archivos)
│   │   └── 20260604_normal_transferencia_03..10.gz     F2  ❌ FALTA (8 archivos)
│   │
│   ├── dataset_raw.csv          (412,097 flows)        F2  ❌ FALTA (solo clean en ZIP)
│   ├── dataset_labeled.csv      (412,097 flows)        F2  ❌ FALTA (nuevo)
│   ├── dataset_clean.csv        (376,827 flows, 69MB)  F2  ✅ ZIP
│   ├── train.csv                (263,778 flows, 70%)   F2  ✅ ZIP
│   ├── val.csv                  (56,524 flows, 15%)    F2  ✅ ZIP
│   ├── test.csv                 (56,525 flows, 15%)    F2  ✅ ZIP
│   ├── resumen_estadistico.txt                         F2  ✅ ZIP
│   ├── processed/                                      📁  ❌ FALTA (vacía)
│   └── staging/                                        📁  ❌ FALTA (vacía)
│
├── models/
│   ├── isolation_forest.pkl     (2.5 MB)               F3  ✅ ZIP
│   ├── scaler.pkl               (1.4 KB)               F3  ✅ ZIP
│   ├── features.csv             (14 features)          F3  ✅ ZIP
│   ├── metrics/                                        📁  ❌ FALTA (vacía)
│   └── trained/                                        📁  ❌ FALTA (vacía)
│
├── results/
│   ├── umbrales_finales.txt     (τ1=-0.4973, τ2=-0.6873) F3/F4  ✅ ZIP
│   ├── latencia_pipeline.txt    (P95=34.8ms)           F4  ✅ ZIP
│   ├── isolation_forest_resultado.png                  F3  ❌ FALTA
│   ├── motor_decision.log       (log activo)           F4  — (excluir del ZIP)
│   ├── reporte_validacion_final.pdf                    F6  ✅ ZIP
│   ├── MVP_funcional.zip        (el propio ZIP)        F6  — (excluir del ZIP)
│   │
│   ├── reports/
│   │   ├── reporte_metricas_v1.txt    (AUC, τ1, τ2)   F3  ✅ ZIP
│   │   ├── reporte_validacion_fase6.txt               F6  ✅ ZIP
│   │   ├── auc_por_escenario.txt      (B1-B6, C1-C3)  F3  ✅ ZIP
│   │   ├── comparacion_modelos_f401.csv               F4  ❌ FALTA (nuevo)
│   │   └── f403_fp_fn_overfitting.json                F4  ❌ FALTA (nuevo)
│   │
│   ├── figures/
│   │   └── auc_roc_umbrales.png       (curva ROC)     F3  ✅ ZIP
│   │
│   ├── tables/
│   │   └── metricas_por_escenario.csv                 F6  ✅ ZIP
│   │
│   ├── analisis_escenarios/                           F3/F6 ❌ FALTA (carpeta nueva)
│   │   ├── clasificacion_tipos.json                   F6  ❌ FALTA
│   │   ├── cohensd.json                               F3  ❌ FALTA
│   │   ├── generalizacion_ataques_no_entrenados.json  F2  ❌ FALTA
│   │   ├── rangos_clasificacion.json                  F4  ❌ FALTA
│   │   ├── scores_por_escenario.json                  F3  ❌ FALTA
│   │   ├── stats_por_escenario.json                   F3  ❌ FALTA
│   │   └── stats_por_grupo.json                       F3  ❌ FALTA
│   │
│   ├── sensibilidad/                                   F3  ❌ FALTA (carpeta nueva)
│   │   ├── sensibilidad_n_flows.csv                   F3  ❌ FALTA
│   │   └── sensibilidad_n_flows.png                   F3  ❌ FALTA
│   │
│   └── resultados F6 (5 CSV):
│       ├── resultados_normal.csv                      F6  ✅ ZIP
│       ├── resultados_mixto.csv                       F6  ✅ ZIP
│       ├── resultados_reeval.csv                      F6  ✅ ZIP
│       ├── resultados_final.csv                       F6  ✅ ZIP
│       └── resultados_f6_completo.csv                 F6  ✅ ZIP
│
├── scripts/
│   ├── parser.py                eve.json.gz→dataset_raw.csv    F2  ✅ ZIP
│   ├── etiquetar_limpiar.py     raw→labeled→clean              F2  ✅ ZIP
│   ├── particionar_estadisticos.py  clean→train/val/test       F2  ✅ ZIP
│   ├── fase3_isolation_forest.py    entrena IF + guarda .pkl   F3  ✅ ZIP
│   ├── auc_roc_umbrales.py          curva ROC, deriva τ1/τ2    F3  ✅ ZIP
│   ├── auc_por_escenario.py         AUC por escenario B/C      F3  ✅ ZIP
│   ├── clasificador.py              clasificador aux            F3  ❌ FALTA (nuevo)
│   ├── motor_decision.py            pipeline F4+F5 completo    F4+F5  ⚠️ OLD
│   │                                (ZIP: v2026-06-04 sin grado/tipo/telegram-thread)
│   │                                (sensor: v2026-06-14 con fixes Telegram+dashboard)
│   ├── motor_decision.py.bak        backup antes de fixes      F4+F5  ❌ FALTA
│   ├── enforce.sh                   BLOCK/LIMIT/UNBLOCK manual F5  ✅ ZIP
│   ├── dashboard.py                 dashboard terminal (3s)    F4  ✅ ZIP
│   ├── dashboard_web.py             dashboard web Flask+SSE    F5  ❌ FALTA (NUEVO)
│   ├── f6_corridas.py               validación batch 40 corridas F6  ✅ ZIP
│   ├── generar_pdf_final.py         genera PDF entregable      F6  ✅ ZIP
│   ├── generar_pdf_zip.py           genera MVP_funcional.zip   F6  ✅ ZIP (pero desactualizado)
│   │
│   ├── capture/
│   │   └── exportar_eve_por_escenario.sh   gzip+rota eve.json F2  ✅ ZIP
│   │
│   ├── evaluation/
│   │   └── registrar_bitacora.sh   escribe línea bitácora      F2  ✅ ZIP
│   │
│   └── validation/                                             F1  ❌ FALTA (nuevo)
│       ├── revisar_suricata.sh     verifica Suricata+eve.json  F1  ❌ FALTA
│       └── suricata_revision.txt   evidencia formal F1         F1  ❌ FALTA
│
├── docs/
│   ├── plan_captura.txt                                        F2  ✅ ZIP
│   ├── guion_ataques.txt           comandos B1-B6              F2  ✅ ZIP
│   ├── resumen_estadistico.txt                                 F2  ✅ ZIP
│   │
│   ├── bitacora/
│   │   └── bitacora_escenarios.txt  49 entradas               F2  ⚠️ OLD
│   │                                (ZIP tiene hasta 06-04, sensor hasta 06-14)
│   │
│   └── ppi_documentacion/          TODA LA DOC F1-F6          —   ❌ FALTA (todo nuevo)
│       ├── ENTREGABLES_POR_FASE.md
│       ├── overview_fases.md
│       ├── arquitectura_archivos_sensor.md
│       ├── F1_entorno_laboratorio/ (F1_01, F1_02, diagramas)
│       ├── F2_captura_trafico/     (F2_01 a F2_05, diagramas)
│       ├── F3_modelado_offline/    (F3_01 a F3_04, justificacion, diagramas)
│       ├── F4_motor_decision/      (F4_01 a F4_04, diagramas)
│       ├── F5_control_inline/      (F5_01 a F5_05, diagramas)
│       └── F6_validacion/          (F6_01 a F6_05, diagramas)
│
├── logs/                                                       —   ❌ FALTA (vacías)
│   ├── suricata/
│   └── system/
│
└── src/                            módulos Python (vacíos)     —   ❌ FALTA
    ├── decision/
    ├── enforcement/
    ├── evaluation/
    ├── features/
    ├── ingest/
    └── models/
```

---

## Resumen de gaps — qué falta en el ZIP

### Scripts (código)

| Archivo | Fase | Problema |
|---|---|---|
| `scripts/motor_decision.py` | F4+F5 | **VERSIÓN ANTIGUA** — ZIP tiene v2026-06-04 sin: grado/tipo, Telegram thread no-bloqueante, Telegram en LIMIT, clasificar_grado(), clasificar_tipo() |
| `scripts/dashboard_web.py` | F5 | **AUSENTE** — nuevo dashboard Flask+SSE+Bootstrap5, sidebar 6 vistas, regex corregido |
| `scripts/clasificador.py` | F3 | Ausente |
| `scripts/validation/revisar_suricata.sh` | F1 | Ausente — evidencia formal F1 |
| `scripts/validation/suricata_revision.txt` | F1 | Ausente — evidencia formal F1 |

### Datos

| Archivo | Fase | Problema |
|---|---|---|
| `data/raw/*.gz` (34 archivos) | F2 | Ausentes — capturas originales por corrida |
| `data/dataset_labeled.csv` | F2 | Ausente — paso intermedio del pipeline |
| `data/dataset_raw.csv` | F2 | Ausente — primera salida del parser |

### Resultados y análisis

| Archivo | Fase | Problema |
|---|---|---|
| `results/analisis_escenarios/*.json` (7 archivos) | F3/F6 | Ausentes — análisis estadístico por escenario |
| `results/sensibilidad/` (2 archivos) | F3 | Ausente — curva de sensibilidad n_flows |
| `results/isolation_forest_resultado.png` | F3 | Ausente |
| `results/reports/comparacion_modelos_f401.csv` | F4 | Ausente — comparación IF vs RF vs DT vs LR |
| `results/reports/f403_fp_fn_overfitting.json` | F4 | Ausente |
| `docs/bitacora/bitacora_escenarios.txt` | F2 | **VERSIÓN ANTIGUA** — ZIP tiene hasta 06-04, sensor tiene hasta 06-14 |

### Documentación (todo ausente del ZIP)

| Carpeta | Archivos | Fases |
|---|---|---|
| `docs/ppi_documentacion/F1_entorno_laboratorio/` | 5 .md | F1 |
| `docs/ppi_documentacion/F2_captura_trafico/` | 8 .md | F2 |
| `docs/ppi_documentacion/F3_modelado_offline/` | 8 .md + 1 PNG | F3 |
| `docs/ppi_documentacion/F4_motor_decision/` | 6 .md | F4 |
| `docs/ppi_documentacion/F5_control_inline/` | 8 .md | F5 |
| `docs/ppi_documentacion/F6_validacion/` | 7 .md | F6 |
| `docs/ppi_documentacion/` (raíz) | 3 .md | — |

**Total documentación ausente: ~45 archivos .md**

---

## Relación archivo → fase

| Archivo | Fase | Qué hace |
|---|---|---|
| `scripts/validation/revisar_suricata.sh` | **F1** | Valida que Suricata esté activo y eve.json tenga campos mínimos |
| `scripts/validation/suricata_revision.txt` | **F1** | Evidencia formal de validación (salida del script, 10-may-2026) |
| `scripts/parser.py` | **F2** | Lee eve.json.gz → extrae flows → genera dataset_raw.csv |
| `scripts/etiquetar_limpiar.py` | **F2** | Etiqueta por src_ip + nombre archivo, filtra duplicados y IPs internas |
| `scripts/particionar_estadisticos.py` | **F2** | Partición cronológica 70/15/15 → train/val/test |
| `scripts/capture/exportar_eve_por_escenario.sh` | **F2** | Comprime eve.json y lo rota al finalizar cada corrida |
| `scripts/evaluation/registrar_bitacora.sh` | **F2** | Escribe entrada en bitacora_escenarios.txt |
| `data/raw/*.gz` | **F2** | Capturas brutas por escenario (A1-A4, B1-B6, C1-C3, corridas F6) |
| `data/dataset_raw.csv` | **F2** | Salida del parser (412,097 flows sin filtrar) |
| `data/dataset_labeled.csv` | **F2** | Con etiqueta grupo/escenario por flow |
| `data/dataset_clean.csv` | **F2** | Dataset final limpio (376,827 flows) |
| `data/train.csv / val.csv / test.csv` | **F2** | Particiones para entrenamiento y evaluación |
| `docs/plan_captura.txt` | **F2** | Plan de corridas, convención de nombres |
| `docs/guion_ataques.txt` | **F2** | Comandos exactos B1-B6 con justificación |
| `docs/bitacora/bitacora_escenarios.txt` | **F2** | 49 corridas registradas con trazabilidad |
| `scripts/fase3_isolation_forest.py` | **F3** | Entrena IF (n=300, contamination=0.05), guarda .pkl y scaler |
| `scripts/auc_roc_umbrales.py` | **F3** | Calcula curva ROC, deriva τ1 (Youden) y τ2 (FPR≤2%) |
| `scripts/auc_por_escenario.py` | **F3** | AUC individual por escenario B1-B6, C1-C3 |
| `scripts/clasificador.py` | **F3** | Módulo auxiliar de clasificación |
| `models/isolation_forest.pkl` | **F3** | Modelo serializado — 2.5 MB |
| `models/scaler.pkl` | **F3** | StandardScaler serializado — 1.4 KB |
| `models/features.csv` | **F3** | Lista de 14 features en orden |
| `results/umbrales_finales.txt` | **F3** | Documento formal τ1=-0.4973, τ2=-0.6873 |
| `results/reports/reporte_metricas_v1.txt` | **F3** | AUC=0.9440, Recall, Precision, F1 |
| `results/reports/auc_por_escenario.txt` | **F3** | AUC por escenario individual |
| `results/figures/auc_roc_umbrales.png` | **F3** | Gráfico curva ROC con τ1/τ2 marcados |
| `results/isolation_forest_resultado.png` | **F3** | Distribución de scores IF |
| `results/analisis_escenarios/*.json` | **F3** | Estadísticos y scores por escenario/grupo |
| `results/sensibilidad/` | **F3** | Curva sensibilidad número de flows de entrenamiento |
| `scripts/motor_decision.py` | **F4+F5** | Motor principal: tail eve.json → features → IF score → PERMIT/LIMIT/BLOCK → ipset |
| `scripts/dashboard.py` | **F4** | Dashboard terminal actualizado cada 3s |
| `scripts/dashboard_web.py` | **F5** | Dashboard web Flask+SSE+Bootstrap5, sidebar 6 vistas |
| `scripts/enforce.sh` | **F5** | Control manual: BLOCK/LIMIT/UNBLOCK con timeout |
| `results/latencia_pipeline.txt` | **F4** | Latencia P95=34.8ms medida en producción |
| `results/reports/comparacion_modelos_f401.csv` | **F4** | IF vs RF vs DT vs OC-SVM vs LR |
| `results/reports/f403_fp_fn_overfitting.json` | **F4** | Análisis de falsos positivos y overfitting |
| `scripts/f6_corridas.py` | **F6** | Validación batch de las 40 corridas |
| `scripts/generar_pdf_final.py` | **F6** | Genera reporte_validacion_final.pdf |
| `scripts/generar_pdf_zip.py` | **F6** | Empaqueta MVP_funcional.zip (desactualizado — ver sección siguiente) |
| `results/resultados_*.csv` (5 archivos) | **F6** | Resultados por grupo: normal, mixto, reeval, final, completo |
| `results/reporte_validacion_final.pdf` | **F6** | Entregable PDF formal |
| `results/tables/metricas_por_escenario.csv` | **F6** | Métricas desglosadas por escenario |
| `results/reports/reporte_validacion_fase6.txt` | **F6** | Reporte texto F6 |

---

## Cómo actualizar el ZIP

El script `scripts/generar_pdf_zip.py` genera el ZIP pero está desactualizado. Para regenerarlo con todos los archivos nuevos:

```bash
# En el sensor (192.168.0.110)
ssh m4rk@192.168.0.110

cd /home/m4rk/ppi-surikata-producto

# Regenerar ZIP actualizado (excluye venv, logs, git, el propio zip y motor_decision.log)
zip -r results/MVP_funcional_v2.zip \
    README.txt \
    scripts/ \
    models/ \
    data/dataset_clean.csv \
    data/dataset_raw.csv \
    data/dataset_labeled.csv \
    data/train.csv \
    data/val.csv \
    data/test.csv \
    data/resumen_estadistico.txt \
    results/umbrales_finales.txt \
    results/latencia_pipeline.txt \
    results/reporte_validacion_final.pdf \
    results/isolation_forest_resultado.png \
    results/reports/ \
    results/figures/ \
    results/tables/ \
    results/analisis_escenarios/ \
    results/sensibilidad/ \
    results/resultados_normal.csv \
    results/resultados_mixto.csv \
    results/resultados_reeval.csv \
    results/resultados_final.csv \
    results/resultados_f6_completo.csv \
    docs/plan_captura.txt \
    docs/guion_ataques.txt \
    docs/resumen_estadistico.txt \
    docs/bitacora/ \
    docs/ppi_documentacion/ \
    --exclude "scripts/__pycache__/*" \
    --exclude "scripts/motor_decision.py.bak" \
    --exclude "results/motor_decision.log" \
    --exclude "results/MVP_funcional*.zip"

# Ver tamaño del ZIP nuevo
ls -lh results/MVP_funcional_v2.zip

# Copiar al Desktop para acceso fácil
scp results/MVP_funcional_v2.zip m4rk@192.168.0.20:~/Descargas/
```

---

## Conteo total

| Categoría | ZIP actual (2026-06-04) | Sensor actual (2026-06-14) | Diferencia |
|---|---|---|---|
| Scripts Python | 11 | 13 | +2 (dashboard_web.py, clasificador.py) |
| Scripts Bash | 3 | 4 | +1 (revisar_suricata.sh) |
| Modelos (.pkl) | 3 | 3 | = |
| Datos CSV | 5 | 8 | +3 (raw, labeled, raw.csv) |
| Capturas raw .gz | 0 | 34 | +34 |
| Resultados/Reports | 12 | 23 | +11 |
| Documentación .md | 0 | ~47 | +47 |
| **TOTAL archivos** | **40** | **~132** | **+92** |

---

*Inventario generado: 2026-06-14*  
*Base del inventario: `find /home/m4rk/ppi-surikata-producto` + `unzip -l MVP_funcional.zip`*
