# Plan de Validación — PPI UPeU 2026

**Proyecto:** Detección temprana de anomalías en redes mediante Isolation Forest + control inline  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha:** 2026-06-22  

---

## Objetivo general

Verificar que cada componente del sistema cumple los criterios de aceptación (CA) definidos en el plan del PPI, tanto de forma aislada (pruebas unitarias) como integrada (pruebas de extremo a extremo).

## Estructura de módulos a validar

```
V1 — Modelo Isolation Forest (offline)
V2 — Motor de decisión (latencia + clasificación)
V3 — Control inline ipset/iptables (enforcement)
V4 — Predictor XGBoost v2 (comportamental)
V5 — Escenarios de integración end-to-end (F6)
V6 — Datos normales nuevos (generalización del IF)
```

---

## Tabla de criterios de aceptación

| ID   | Módulo     | Qué se mide                              | Criterio PASS          | Fuente de datos                        |
|------|------------|------------------------------------------|------------------------|----------------------------------------|
| CA-1 | IF offline | AUC-ROC curva ROC                        | ≥ 0.85                 | metricas_offline.txt                   |
| CA-2 | IF offline | TPR en τ1 (Youden)                       | ≥ 0.95                 | metricas_offline.txt                   |
| CA-3 | IF offline | FPR en τ1                                | ≤ 0.25                 | metricas_offline.txt                   |
| CA-4 | IF offline | Precision en τ1                          | ≥ 0.95                 | metricas_offline.txt                   |
| CA-5 | Motor      | Latencia P95 del pipeline                | < 500 ms               | latencia_pipeline.txt                  |
| CA-6 | Motor      | ITL (tiempo sin clasificaciones)         | = 0%                   | motor_decision.log                     |
| CA-7 | Motor      | Umbrales cargados correctamente al init  | τ1=-0.4459 τ2=-0.6027  | log arranque motor                     |
| CA-8 | ipset      | Whitelist — Desktop nunca en ipset       | 0 entradas bloqueadas  | `block_counts.json` (sensor) + ipset en servidor |
| CA-9 | ipset      | IP atacante bloqueada en servidor        | curl timeout/refused   | `ssh 192.168.0.120 "sudo ipset list ppi_blocked"` |
| CA-10| ipset      | Bloqueo progresivo #3 = PERMANENTE       | timeout = 0            | `ssh 192.168.0.120 "sudo ipset list ppi_blocked"` |
| CA-11| XGBoost    | AUC-ROC en test set                      | ≥ 0.95                 | metricas_predictor_v2.txt              |
| CA-12| XGBoost    | FP + FN totales en test (12,488 muestras)| ≤ 30                   | metricas_predictor_v2.txt              |
| CA-13| Integración| Lead time SYN flood (B1) → primer BLOCK  | ≤ 120s                 | motor_decision.log timestamp           |
| CA-14| Integración| Lead time BF SSH (B6) → primer BLOCK     | ≤ 90s                  | motor_decision.log timestamp           |
| CA-15| Integración| Disponibilidad 40 corridas F6            | 100%                   | resultados_f6_completo.csv             |
| CA-16| Nueva data | FPR IF en capturas normales nuevas       | ≤ 0.30                 | score manual sobre nueva eve.json      |

---

## Orden de ejecución recomendado

```
1. test_v1_metricas_if.sh      (2 min — solo lee archivos)
2. test_v2_latencia_motor.sh   (2 min — solo lee archivos)
3. f3_val_ipset.sh             (5 min — requiere SSH a servidor 192.168.0.120)
4. test_v4_xgboost.sh          (2 min — solo lee archivos)
5. test_v5_lead_times.sh       (20-30 min — requiere corridas reales B1+B6)
6. v6_datos_nuevos_normal.md   (manual — requiere captura nueva)
```

Ejecutar el suite completo:
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh
```

---

## Archivos de este módulo

| Archivo                        | Contenido                                      |
|-------------------------------|------------------------------------------------|
| v1_modelo_if.md               | Validación offline del IF (CA-1 a CA-4)        |
| v2_motor_decision.md          | Validación latencia y clasificación (CA-5,6,7) |
| v3_control_ipset.md           | Validación enforcement ipset (CA-8,9,10)       |
| v4_predictor_xgboost.md       | Validación XGBoost v2 (CA-11,12)               |
| v5_escenarios_integracion.md  | Validación end-to-end escenarios (CA-13,14,15) |
| v6_datos_nuevos_normal.md     | Generalización con data nueva (CA-16)          |
| RESULTADOS_VALIDACION.md      | Tabla resumen PASS/FAIL con valores obtenidos  |
