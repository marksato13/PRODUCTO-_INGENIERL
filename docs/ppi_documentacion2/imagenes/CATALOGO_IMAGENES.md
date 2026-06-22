# Catálogo de Imágenes — PPI UPeU 2026

**Carpeta:** `docs/ppi_documentacion2/imagenes/`  
**Estado:** ✅ existente | ⏳ captura pendiente (manual) | 🔧 generar con script

---

## F1 — Captura de Datos (EDA)

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F1_captura/eda_01_distribuciones.png` | Distribución de las 14 features IF (histogramas) | ✅ | Informe § Análisis exploratorio |
| `F1_captura/eda_02_protocolo.png` | Distribución por protocolo TCP/UDP/ICMP | ✅ | PPT slide 6, Informe |
| `F1_captura/eda_03_boxplots.png` | Boxplots features por tipo de tráfico | ✅ | Informe § Separabilidad |
| `F1_captura/eda_04_correlacion.png` | Mapa de correlación entre features | ✅ | Informe § Features |
| `F1_captura/eda_05_dest_ports.png` | Puertos destino más frecuentes por grupo | ✅ | Informe § Escenarios |
| `F1_captura/eda_06_stats_tabla.png` | Tabla estadística completa (media, std, min, max) | ✅ | Informe § EDA |
| `F1_captura/captura_suricata_activo.png` | Screenshot: `systemctl status suricata` | ⏳ | Defensa — evidencia F1 |
| `F1_captura/captura_eve_json.png` | Screenshot: `tail -f /var/log/suricata/eve.json` en vivo | ⏳ | Defensa — evidencia F1 |
| `F1_captura/captura_raw_archivos.png` | Screenshot: `ls -lh data/raw/` (47 capturas) | ⏳ | Informe § Dataset |

---

## F2 — Detección Isolation Forest

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F2_modelo_IF/f2_auc_roc_curva.png` | Curva ROC completa del IF (AUC=0.8998), τ1/τ2 marcados | ✅ | PPT slide 8, Informe § Resultados |
| `F2_modelo_IF/captura_entrenamiento.png` | Screenshot: `python3 fase3_entrenar.py` — salida con n=53,708 | ⏳ | Defensa — evidencia F2 |
| `F2_modelo_IF/captura_metricas_offline.png` | Screenshot: `cat results/metricas_offline.txt` completo | ⏳ | Defensa — evidencia F2 |
|  | Distribución de scores normal vs anómalo — τ1/τ2 marcados, zonas PERMIT/LIMIT/BLOCK | ✅ | Informe § IF |

---

## F3 — Motor de Decisión + Control Inline

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F3_motor_control/captura_motor_log_block.png` | Screenshot: motor_decision.log con BLOCKs de Kali en tiempo real | ⏳ | PPT slide 9, Defensa |
| `F3_motor_control/captura_motor_log_limit.png` | Screenshot: motor_decision.log con LIMIT → BLOCK (escalada B6) | ⏳ | Defensa — lead time BF SSH |
| `F3_motor_control/captura_dashboard_terminal.png` | Screenshot: `python3 scripts/dashboard.py` en terminal | ⏳ | PPT slide 10, Defensa |
| `F3_motor_control/captura_dashboard_web.png` | Screenshot: navegador http://192.168.0.110:8080 con alertas | ⏳ | PPT slide 10, Defensa |
| `F3_motor_control/captura_telegram_alerta.png` | Screenshot: notificación Telegram de BLOCK/ALERTA-PREDICTIVA | ⏳ | PPT slide 11, Defensa |
| `F3_motor_control/captura_ipset_bloqueados.png` | Screenshot: `sudo ipset list ppi_blocked` con Kali bloqueada | ⏳ | Defensa — evidencia enforcement |
| `F3_motor_control/captura_bloqueo_permanente.png` | Screenshot: ipset con timeout=0 (bloqueo #3 permanente) | ⏳ | Defensa — CA-10 |
| `F3_motor_control/captura_latencia_pipeline.png` | Screenshot: `cat results/latencia_pipeline.txt` (P95=34.8ms) | ⏳ | Defensa — CA-5 |

---

## F4 — Predictor XGBoost v2

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F4_predictor/f4_roc_comparacion.png` | Curva ROC XGBoost v2 (AUC=0.9992) vs v1 | ✅ | Informe § F4, PPT slide 8 |
| `F4_predictor/f4_shap_importancia.png` | SHAP values — importancia de features XGBoost | ✅ | Informe § F4, Defensa |
| `F4_predictor/captura_metricas_xgboost.png` | Screenshot: `cat results/metricas_predictor_v2.txt` | ⏳ | Defensa — CA-11/12 |
| `F4_predictor/captura_alerta_predictiva.png` | Screenshot: log predictor con ALERTA-PREDICTIVA (P≥0.70) | ⏳ | Defensa — evidencia F4 |
| `F4_predictor/captura_entrenamiento_xgb.png` | Screenshot: `python3 f4_entrenar_predictor_v2.py` salida | ⏳ | Defensa — evidencia F4 |

---

## F5 — Aprendizaje Continuo

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F5_aprendizaje/captura_cron_configurado.png` | Screenshot: `crontab -l` con 2 jobs F5 | ⏳ | Defensa — CA-13 |
| `F5_aprendizaje/captura_reentrenamiento_if.png` | Screenshot: `python3 f5_reentrenar_if.py` — comparación AUC | ⏳ | Defensa — F5 IF |
| `F5_aprendizaje/captura_reentrenamiento_xgb.png` | Screenshot: `python3 f5_reentrenar_xgboost.py` — AUC anterior vs nuevo | ⏳ | Defensa — F5 XGBoost |
| `F5_aprendizaje/captura_metricas_f5_historial.png` | Screenshot: `cat results/metricas_f5_xgboost.txt` (3 corridas) | ⏳ | Defensa — CA-14 |
| `F5_aprendizaje/captura_proteccion_antiregresion.png` | Screenshot: aviso "muy pocos eventos" — modelo no reemplazado | ⏳ | Defensa — protección F5 |

---

## F6 — Validación

| Archivo | Descripción | Estado | Uso |
|---|---|---|---|
| `F6_validacion/f6_01_disponibilidad.png` | Disponibilidad 100% por corrida (40 barras) | ✅ | Informe § F6, PPT slide 13 |
| `F6_validacion/f6_02_flows_anomalos.png` | Flows anómalos detectados por escenario | ✅ | Informe § F6 |
| `F6_validacion/f6_03_timeline_deteccion.png` | Timeline lead time por escenario | ✅ | Informe § Lead time |
| `F6_validacion/f6_04_itl.png` | ITL=0% en todas las corridas | ✅ | Informe § F6 |
| `F6_validacion/f6_05_flujos_acumulados.png` | Flujos acumulados por sesión | ✅ | Informe § Dataset |
| `F6_validacion/f6_06_latencia_pipeline.png` | Latencia del pipeline por corrida | ✅ | Informe § Latencia |
| `F6_validacion/f6_07_panel_resumen.png` | Panel 7-en-1 con todas las métricas F6 | ✅ | PPT slide 13, Defensa |
| `F6_validacion/captura_run_all_completo.png` | Screenshot: `bash run_all.sh` — 16/16 PASS completo | ⏳ | Defensa — evidencia validación |
| `F6_validacion/captura_resultados_csv.png` | Screenshot: `head resultados_f6_completo.csv` (40 corridas) | ⏳ | Defensa — CA-15 |
| `F6_validacion/captura_bitacora.png` | Screenshot: `cat docs/bitacora/bitacora_escenarios.txt` | ⏳ | Defensa — trazabilidad |

---

## Resumen de estado

| Fase | Existentes | Pendientes | Total |
|------|-----------|------------|-------|
| F1   | 6         | 3          | 9     |
| F2   | 2         | 2          | 4     |
| F3   | 0         | 8          | 8     |
| F4   | 2         | 3          | 5     |
| F5   | 0         | 5          | 5     |
| F6   | 7         | 3          | 10    |
| **TOTAL** | **17** | **24** | **41** |

---

## Prioridad para la sustentación (capturar primero)

Las 10 capturas más importantes si el tiempo es limitado:

| Prioridad | Archivo | Por qué es clave |
|---|---|---|
| 1 | `F3_motor_control/captura_motor_log_block.png` | Evidencia principal de detección en tiempo real |
| 2 | `F6_validacion/captura_run_all_completo.png` | Demuestra 16/16 PASS en un solo screenshot |
| 3 | `F3_motor_control/captura_telegram_alerta.png` | Impacto visual más fuerte para la defensa |
| 4 | `F3_motor_control/captura_dashboard_web.png` | Muestra el sistema completo operando |
| 5 | `F2_modelo_IF/captura_metricas_offline.png` | AUC, τ1/τ2, TPR/FPR — base técnica |
| 6 | `F4_predictor/captura_metricas_xgboost.png` | AUC=0.9992, matriz confusión |
| 7 | `F3_motor_control/captura_ipset_bloqueados.png` | Bloqueo real a nivel red |
| 8 | `F5_aprendizaje/captura_metricas_f5_historial.png` | Evidencia de reentrenamiento real |
| 9 | `F3_motor_control/captura_bloqueo_permanente.png` | Bloqueo #3 permanente |
| 10 | `F1_captura/captura_eve_json.png` | Captura Suricata en vivo |

---

## Cómo tomar las capturas pendientes

```bash
# En el sensor, con el motor corriendo:

# 1. Motor log con BLOCKs (F3)
ssh m4rk@192.168.0.110
tail -20 results/motor_decision.log
# → captura de pantalla de la terminal

# 2. Dashboard web (F3)
# Abrir navegador en Desktop → http://192.168.0.110:8080

# 3. ipset (F3) — necesita sudo en terminal del sensor
sudo ipset list ppi_blocked

# 4. run_all.sh completo (F6)
bash scripts/validacion/run_all.sh

# 5. Métricas offline (F2)
cat results/metricas_offline.txt

# 6. Métricas XGBoost (F4)
cat results/metricas_predictor_v2.txt

# 7. Crontab (F5)
crontab -l

# 8. Reentrenamiento XGBoost en vivo (F5)
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 scripts/f5_reentrenar_xgboost.py --horas 168
```
