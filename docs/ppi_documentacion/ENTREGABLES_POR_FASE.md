# Entregables por Fase — PPI 2026

**Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
**Universidad Peruana Unión · Rubén Mark Salazar Tocas**  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  

> Todos los archivos residen en el sensor **192.168.0.110**  
> Directorio base: `/home/m4rk/ppi-surikata-producto/`  
> Acceso: `ssh m4rk@192.168.0.110`

---

## FASE 1 — Entorno de Laboratorio ✅

| Entregable | Ruta completa en el sensor | Descripción |
|---|---|---|
| Script de validación | `scripts/validation/revisar_suricata.sh` | Verifica Suricata, interfaz y eve.json |
| **Evidencia formal F1** | `scripts/validation/suricata_revision.txt` | Salida del script — fecha 10 may 2026 |
| Configuración Suricata | `/etc/suricata/suricata.yaml` | Interfaz ens35 configurada |
| Output en tiempo real | `/var/log/suricata/eve.json` | Flujos capturados por Suricata 7.0.3 |

**Criterio cumplido:** Suricata 7.0.3 activo en ens35 · eve.json con campos mínimos validados.

---

## FASE 2 — Captura de Tráfico ✅

### Documentación

| Entregable | Ruta completa | Descripción |
|---|---|---|
| Plan de captura | `docs/plan_captura.txt` | Lógica de corridas, convención de nombres |
| Guión de ataques | `docs/guion_ataques.txt` | Comandos y justificación B1-B6 |
| **Bitácora de corridas** | `docs/bitacora/bitacora_escenarios.txt` | 49 entradas con trazabilidad completa |
| Resumen estadístico | `docs/resumen_estadistico.txt` | Estadísticos del dataset |

### Scripts de captura

| Entregable | Ruta completa | Descripción |
|---|---|---|
| A1 HTTP Normal | `scripts/capture/A1_http_normal.sh` | curl/wget · 10 min |
| A2 SSH Legítimo | `scripts/capture/A2_ssh_legitimo.sh` | ssh · 8 min |
| A3 Transferencia | `scripts/capture/A3_transferencia_legitima.sh` | scp/wget · 10 min |
| A4 Tráfico sostenido | `scripts/capture/A4_trafico_sostenido.sh` | curl+ssh · 15 min |
| B1 SYN Flood | `scripts/capture/B1_syn_flood.sh` | hping3 --rand-source |
| B2 Port Scan | `scripts/capture/B2_port_scan.sh` | nmap -sS |
| B3 UDP Flood | `scripts/capture/B3_udp_flood.sh` | hping3 --udp |
| B4 ICMP Flood | `scripts/capture/B4_icmp_flood.sh` | hping3 -1 |
| B5 HTTP Abuse | `scripts/capture/B5_acceso_repetitivo.sh` | curl en bucle |
| B6 Brute Force | `scripts/capture/B6_bruteforce.sh` | hydra |
| C1 HTTP + SYN | `scripts/capture/C1_http_syn_mixto.sh` | Desktop + Kali |
| C2 SSH + Scan | `scripts/capture/C2_ssh_portscan_mixto.sh` | Desktop + Kali |
| C3 Descarga + UDP | `scripts/capture/C3_descarga_udp_mixto.sh` | Desktop + Kali |
| Exportar eve.json | `scripts/capture/exportar_eve_por_escenario.sh` | Copia y comprime |
| Registrar bitácora | `scripts/evaluation/registrar_bitacora.sh` | Escribe entrada |

### Dataset (34 archivos .gz + procesados)

| Entregable | Ruta completa | Tamaño |
|---|---|---|
| Archivos raw (34 .gz) | `data/raw/20260602_*.gz` · `20260604_*.gz` | 4 KB – 4.9 MB c/u |
| **dataset_raw.csv** | `data/dataset_raw.csv` | 75 MB · 412,097 flows |
| dataset_labeled.csv | `data/dataset_labeled.csv` | 75 MB · 412,097 flows |
| **dataset_clean.csv** | `data/dataset_clean.csv` | 69 MB · 376,827 flows |
| train.csv | `data/train.csv` | 263,778 flows (70%) |
| val.csv | `data/val.csv` | 56,524 flows (15%) |
| test.csv | `data/test.csv` | 56,525 flows (15%) |
| resumen_estadistico.txt | `data/resumen_estadistico.txt` | Estadísticos del dataset |

### Scripts de procesamiento

| Entregable | Ruta completa | Descripción |
|---|---|---|
| parser.py | `scripts/parser.py` | EVE JSON → dataset_raw.csv |
| etiquetar_limpiar.py | `scripts/etiquetar_limpiar.py` | Etiquetado + limpieza |
| particionar_estadisticos.py | `scripts/particionar_estadisticos.py` | Partición 70/15/15 |

**Criterio cumplido:** 13 escenarios ejecutados · 49 corridas registradas · 376,827 flows limpios.

---

## FASE 3 — Modelado Offline ✅

### Modelo entrenado

| Entregable | Ruta completa | Tamaño | Descripción |
|---|---|---|---|
| **isolation_forest.pkl** | `models/isolation_forest.pkl` | 2.5 MB | Modelo serializado (n=300, cont=0.05) |
| scaler.pkl | `models/scaler.pkl` | 1.4 KB | StandardScaler serializado |
| features.csv | `models/features.csv` | 152 B | Lista de 14 features |

### Scripts

| Entregable | Ruta completa | Descripción |
|---|---|---|
| **fase3_isolation_forest.py** | `scripts/fase3_isolation_forest.py` | Script principal de entrenamiento |
| auc_roc_umbrales.py | `scripts/auc_roc_umbrales.py` | Curva ROC y definición τ1/τ2 |
| auc_por_escenario.py | `scripts/auc_por_escenario.py` | AUC individual por escenario |

### Reportes y gráficos

| Entregable | Ruta completa | Descripción |
|---|---|---|
| **reporte_metricas_v1.txt** | `results/reports/reporte_metricas_v1.txt` | AUC, τ1, τ2, métricas formales |
| auc_por_escenario.txt | `results/reports/auc_por_escenario.txt` | AUC B1-B6, C1-C3 |
| isolation_forest_resultado.png | `results/isolation_forest_resultado.png` | Distribución de scores |
| **auc_roc_umbrales.png** | `results/figures/auc_roc_umbrales.png` | Curva ROC con τ1/τ2 |

**Métricas obtenidas:** Recall=87.6% · Precisión=99.96% · F1=0.9338 · AUC=0.9440  
**Criterio cumplido:** Modelo entrenado · τ1=-0.4973 · τ2=-0.6873 · AUC-ROC calculado.

---

## FASE 4 — Motor de Decisión ✅

| Entregable | Ruta completa | Descripción |
|---|---|---|
| **motor_decision.py** | `scripts/motor_decision.py` | Motor completo con triple umbral + detectores + Telegram + explainabilidad |
| dashboard.py | `scripts/dashboard.py` | Dashboard en tiempo real (actualiza cada 3s) |
| **motor_decision.log** | `results/motor_decision.log` | Log de decisiones en producción |
| **latencia_pipeline.txt** | `results/latencia_pipeline.txt` | P95=34.8ms · Cumple < 500ms ✓ |
| ppi-motor.service | `/etc/systemd/system/ppi-motor.service` | Servicio de inicio automático |

**Detectores implementados:**
- Brute Force SSH: ventana 60s · 5→LIMIT · 15→BLOCK
- HTTP Abuse: ventana 30s · 50→LIMIT · 100→BLOCK
- Notificaciones Telegram en tiempo real
- **Explainabilidad (v2):** top-3 features z-score en log y Telegram para cada BLOCK/LIMIT

**Criterio cumplido:** Pipeline end-to-end · Latencia P95=34.8ms · Log estructurado · Systemd activo · Explainabilidad implementada.

---

## FASE 5 — Control Inline ✅

| Entregable | Ruta completa | Descripción |
|---|---|---|
| **enforce.sh** | `scripts/enforce.sh` | Control manual BLOCK/LIMIT/UNBLOCK |
| **umbrales_finales.txt** | `results/umbrales_finales.txt` | Documento formal de umbrales τ1/τ2 |

**Configuración en servidor 192.168.0.120:**

| Componente | Comando de verificación | Estado |
|---|---|---|
| ipset ppi_blocked | `sudo ipset list ppi_blocked` | hash:ip timeout=300s |
| ipset ppi_limited | `sudo ipset list ppi_limited` | hash:ip timeout=300s |
| iptables BLOCK | `sudo iptables -L INPUT -n \| grep ppi` | DROP match-set ppi_blocked |
| iptables LIMIT | `sudo iptables -L INPUT -n \| grep hashlimit` | DROP above 100/sec burst 150 |

**Criterio cumplido:** BLOCK=DROP · LIMIT=hashlimit 100pkt/s · enforce.sh operativo · Timeout 300s automático.

---

## FASE 6 — Validación y Experimentación ✅

### Resultados de 40 corridas

| Entregable | Ruta completa | Corridas | Descripción |
|---|---|---|---|
| resultados_normal.csv | `results/resultados_normal.csv` | 1-10 | Tráfico normal · ITL=0% |
| resultados_mixto.csv | `results/resultados_mixto.csv` | 11-20 | Mixto · TIE=100% |
| resultados_reeval.csv | `results/resultados_reeval.csv` | 21-30 | Re-evaluación |
| resultados_final.csv | `results/resultados_final.csv` | 31-40 | Corridas finales |
| **resultados_f6_completo.csv** | `results/resultados_f6_completo.csv` | **40** | Consolidado total |

### Reportes finales

| Entregable | Ruta completa | Descripción |
|---|---|---|
| reporte_validacion_fase6.txt | `results/reports/reporte_validacion_fase6.txt` | Reporte formal F6 |
| **reporte_validacion_final.pdf** | `results/reporte_validacion_final.pdf` | **PDF entregable principal** (7.4 KB) |
| **MVP_funcional.zip** | `results/MVP_funcional.zip` | **ZIP del sistema completo** (25 MB · 40 archivos) |

**Métricas de validación:**

| Métrica | Valor | Criterio del plan |
|---|---|---|
| Disponibilidad | **100%** | ≥ 99% ✓ |
| ITL (impacto tráfico legítimo) | **0%** | ≤ 2% ✓ |
| TIE (tasa intervención efectiva) | **100%** | — ✓ |
| Lead Time | **26 segundos** | Medido en vivo ✓ |
| MTTC | **28 segundos** | Medido en vivo ✓ |
| Latencia pipeline P95 | **34.8 ms** | < 500ms ✓ |

**Criterio cumplido:** 40 corridas ejecutadas · PDF generado · MVP_funcional.zip entregado.

---

## Resumen general de entregables

| Fase | Entregable principal | Ruta |
|---|---|---|
| F1 | Evidencia formal Suricata | `scripts/validation/suricata_revision.txt` |
| F2 | Dataset limpio + bitácora | `data/dataset_clean.csv` · `docs/bitacora/bitacora_escenarios.txt` |
| F3 | Modelo entrenado + métricas | `models/isolation_forest.pkl` · `results/reports/reporte_metricas_v1.txt` |
| F4 | Motor de decisión en producción | `scripts/motor_decision.py` · `results/latencia_pipeline.txt` |
| F5 | Control inline + umbrales | `scripts/enforce.sh` · `results/umbrales_finales.txt` |
| F6 | **PDF + ZIP del MVP** | `results/reporte_validacion_final.pdf` · `results/MVP_funcional.zip` |

---

## Acceso rápido a los entregables

```bash
# Conectar al sensor
ssh m4rk@192.168.0.110

# Navegar al proyecto
cd /home/m4rk/ppi-surikata-producto

# Ver estructura completa
find . -name "*.py" -o -name "*.sh" -o -name "*.csv" -o -name "*.txt" -o -name "*.pdf" -o -name "*.zip" | sort

# Estado del motor en producción
sudo systemctl status ppi-motor.service

# Ver log en tiempo real
tail -f results/motor_decision.log

# Ver IPs bloqueadas en servidor
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```

---

## DOCUMENTACIÓN — Índice completo de archivos .md (54 archivos)

> Ruta base: `docs/ppi_documentacion/` en el sensor 192.168.0.110

### Documentos generales (raíz)

| Archivo | Descripción |
|---|---|
| `overview_fases.md` | Pipeline F1→F6 · 5 diagramas Mermaid · arquitectura física · métricas finales |
| `arquitectura_MVP_completa.md` | Árbol de directorios · scripts → artefactos · índice completo |
| `ENTREGABLES_POR_FASE.md` | Este documento — índice de entregables por fase |
| `arquitectura_archivos_sensor.md` | Árbol de archivos del sensor con anotación de fase |

### F1 — Entorno de Laboratorio

| Archivo | Descripción |
|---|---|
| `F1_entorno_laboratorio/DIAGRAMAS/F1_entorno_laboratorio.md` | **3 diagramas**: topología red, flujo SSH keys, sequence Suricata |
| `F1_entorno_laboratorio/DOCUMENTACION  GENERAL /F1_entorno_laboratorio.md` | Documento principal F1 |
| `F1_entorno_laboratorio/DOCUMENTACION  GENERAL /F1_03_Sincronizacion_Horaria_NTP.md` | NTP + timezone America/Lima en 4 VMs |
| `F1_entorno_laboratorio/F1_01_Alcance_Beneficiarios_Simulacion.md` | Alcance del PPI |
| `F1_entorno_laboratorio/F1_02_Arquitectura_Laboratorio_Vulnerabilidades.md` | Arquitectura y vulnerabilidades |
| `F1_entorno_laboratorio/F1_Arquitectura_General.drawio.md` | Diagrama drawio arquitectura |

### F2 — Captura de Tráfico

| Archivo | Descripción |
|---|---|
| `F2_captura_trafico/DIAGRAMAS/F2_captura_trafico.md` | **6 diagramas**: escenarios, ciclo corrida, transformación dataset, pie distribución, nomenclatura, conector |
| `F2_captura_trafico/DOCUMENTACION  GENERAL /F2_captura_trafico.md` | Documento principal F2 |
| `F2_captura_trafico/DOCUMENTACION  GENERAL /F2_05_Escenarios_Diagramas_Parametros.md` | Parámetros por escenario |
| `F2_captura_trafico/F2_01_Definicion_Escenarios.md` | Definición A/B/C |
| `F2_captura_trafico/F2_02_Clasificacion_Anomalias.md` | Clasificación tipos |
| `F2_captura_trafico/F2_03_Justificacion_Ataques.md` | Justificación académica B1-B6 |
| `F2_captura_trafico/F2_04_Ataques_No_Entrenados.md` | 12 ataques no entrenados detectados |
| `F2_captura_trafico/diagramas/F2_Escenario_*.drawio.md` | 3 diagramas drawio escenarios |

### F3 — Modelado Offline

| Archivo | Descripción |
|---|---|
| `F3_modelado_offline/DIAGRAMAS/F3_modelado_offline.md` | **7 diagramas**: pipeline, recalibración v1→v2, feature engineering, τ1/τ2, sensibilidad, AUC escenarios, artefactos |
| `F3_modelado_offline/DIAGRAMAS/F3_sensibilidad_n_flows.md` | Análisis N flows vs AUC (tabla + gráfico) |
| `F3_modelado_offline/DIAGRAMAS/F3_Arquitectura_Data.drawio.md` | Diagrama drawio componentes |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_modelado_offline.md` | Documento principal F3 |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_justificacion_modelo.md` | Por qué 684 flows · análisis sesgo SSH |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_05_Recalibracion_Modelo.md` | ⭐ **NUEVO** — Evidencia recalibración v1→v2 (timestamps) |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_01_Arquitectura_Data_Engineering.md` | Data engineering F3 |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_02_Tipos_Datos_Recolectados.md` | Tipos de datos |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_03_Limpieza_Transformacion_Features.md` | Limpieza y features |
| `F3_modelado_offline/DOCUMENTACION  GENERAL /F3_04_Almacenamiento_Escalabilidad.md` | Almacenamiento |

### F4 — Motor de Decisión

| Archivo | Descripción |
|---|---|
| `F4_motor_decision/DIAGRAMAS/F4_motor_decision.md` | **7 diagramas**: arquitectura boot→enforce, sequence flow individual, score→grado→tipo, detectores heurísticos, Telegram+dashboard, systemd, 3 capas |
| `F4_motor_decision/DOCUMENTACION  GENERAL /F4_motor_decision.md` | Documento principal F4 |
| `F4_motor_decision/DOCUMENTACION  GENERAL /F4_01_Comparacion_Modelos.md` | ⭐ **REAL DATA** — IF vs RF vs OC-SVM vs DT vs LR (5 modelos, CSV empírico) |
| `F4_motor_decision/DOCUMENTACION  GENERAL /F4_02_Justificacion_Modelo_Final.md` | Justificación elección IF |
| `F4_motor_decision/DOCUMENTACION  GENERAL /F4_03_Falsos_Positivos_Overfitting.md` | Análisis FP y overfitting |
| `F4_motor_decision/DOCUMENTACION  GENERAL /F4_04_Aprendizaje_Continuo.md` | Reentrenamiento adaptativo · arquitectura evolutiva |

### F5 — Control Inline

| Archivo | Descripción |
|---|---|
| `F5_control_inline/DIAGRAMAS/F5_control_inline.md` | **7 diagramas**: pipeline 9 etapas, netfilter ipset/iptables, canal SSH, ciclo bloqueo, Telegram+Dashboard SSE, boot motor, pruebas live |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_control_inline.md` | Documento principal F5 |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_01_Arquitectura_Integracion.md` | Integración completa 9 etapas |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_02_Costo_Computacional_Escalabilidad.md` | Costo y escalabilidad |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_03_Telegram_Dashboard.md` | Telegram Bot + Dashboard web Flask+SSE |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_04_Instalacion_Dependencias_Sensor.md` | Instalación del entorno |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_05_Disparadores_LIMIT_BLOCK.md` | Disparadores LIMIT/BLOCK |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_06_Plan_Pruebas_Disparadores.md` | Plan de pruebas · T1-T8 + B2 + B5 |
| `F5_control_inline/DOCUMENTACION  GENERAL /F5_07_Evidencia_Pruebas_Live.md` | ⭐ **NUEVO** — Evidencia live 10 escenarios (logs reales, ipset verificado) |
| `F5_control_inline/DIAGRAMAS/F5_Arquitectura_Integracion.drawio.md` | Diagrama drawio |

### F6 — Validación y Resultados

| Archivo | Descripción |
|---|---|
| `F6_validacion/DIAGRAMAS/F6_validacion.md` | **7 diagramas**: 40 corridas, métricas globales, AUC escenarios, gravedad score→grado→tipo, sequence live, requisitos vs obtenido, integración F1→F6 |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_validacion.md` | Documento principal F6 |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_01_Validacion_Resultados.md` | Resultados completos 40 corridas |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_02_Dashboard.md` | Dashboard web detalle |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_03_Defensa_Jurado.md` | Preguntas y respuestas para defensa |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_04_Trabajo_Futuro.md` | Trabajo futuro y extensiones |
| `F6_validacion/DOCUMENTACION  GENERAL /F6_05_Clasificacion_Anomalias_Gravedad.md` | Escala NORMAL/BAJA/ALTA/CRÍTICA · 9 tipos |

---

## Entregables adicionales (sesión 2026-06-14/15)

| Entregable | Ruta / Ubicación | Descripción |
|---|---|---|
| **Dashboard Web** | `scripts/dashboard_web.py` + `ppi-dashboard.service` | Flask + SSE en http://192.168.0.110:8080 · 6 vistas |
| **Comparación modelos CSV** | `results/reports/comparacion_modelos_f401.csv` | IF vs RF vs OC-SVM vs DT vs LR — datos empíricos reales |
| **Evidencia pruebas live** | `docs/ppi_documentacion/F5_control_inline/DOCUMENTACION GENERAL/F5_07_Evidencia_Pruebas_Live.md` | 10 escenarios probados con logs y ipset verificado |
| **Recalibración modelo** | `docs/ppi_documentacion/F3_modelado_offline/DOCUMENTACION GENERAL/F3_05_Recalibracion_Modelo.md` | Evidencia v1→v2 con timestamps de archivos |
| **GitHub repositorio** | https://github.com/marksato13/PRODUCTO-_INGENIERL | 35+ commits · docs F1-F6 · 44 diagramas Mermaid |

---

*Documento actualizado el 2026-06-15 · Proyecto PPI Universidad Peruana Unión*
