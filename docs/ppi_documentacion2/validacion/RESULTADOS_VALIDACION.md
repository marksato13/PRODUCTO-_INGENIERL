# Resultados de Validación — PPI UPeU 2026

**Fecha de última actualización:** 2026-06-22  
**Validado por:** Rubén Mark Salazar Tocas

---

## Tabla resumen PASS/FAIL

| CA    | Módulo       | Qué se midió                         | Criterio    | Valor obtenido        | Estado     |
|-------|--------------|--------------------------------------|-------------|------------------------|------------|
| CA-1  | IF offline   | AUC-ROC                              | ≥ 0.85      | **0.8998**             | ✅ PASS    |
| CA-2  | IF offline   | TPR en τ1 = -0.4459                  | ≥ 0.95      | **0.9940** (99.40%)    | ✅ PASS    |
| CA-3  | IF offline   | FPR en τ1 = -0.4459                  | ≤ 0.25      | **0.2047** (20.47%)    | ✅ PASS    |
| CA-4  | IF offline   | Precision en τ1                      | ≥ 0.95      | **0.9954** (99.54%)    | ✅ PASS    |
| CA-5  | Motor        | Latencia P95 pipeline                | < 500ms     | **34.8ms**             | ✅ PASS    |
| CA-6  | Motor        | ITL (inactividad log)                | = 0%        | **0%**                 | ✅ PASS    |
| CA-7  | Motor        | τ1/τ2 cargados al arranque           | -0.4459/-0.6027 | **verificado**     | ✅ PASS    |
| CA-8  | ipset        | Whitelist nunca bloqueada            | 0 entradas  | **0 IPs en ppi_blocked**| ✅ PASS   |
| CA-9  | ipset        | IP bloqueada no alcanza servidor     | curl falla  | **timeout verificado** | ✅ PASS    |
| CA-10 | ipset        | Bloqueo #3 = PERMANENTE              | timeout=0   | **timeout=0 @ 06:39** | ✅ PASS    |
| CA-11 | XGBoost      | AUC-ROC test set (12,488 muestras)   | ≥ 0.95      | **0.9992**             | ✅ PASS    |
| CA-12 | XGBoost      | FP + FN totales en test              | ≤ 30        | **14** (7 FP + 7 FN)   | ✅ PASS    |
| CA-13 | Integración  | Lead time B1 SYN Flood → BLOCK       | ≤ 120s      | **~62s**               | ✅ PASS    |
| CA-14 | Integración  | Lead time B6 BF SSH → BLOCK          | ≤ 90s       | **~60s**               | ✅ PASS    |
| CA-15 | Integración  | Disponibilidad 40 corridas F6        | 100%        | **100%** (40/40)        | ✅ PASS    |
| CA-16 | Nueva data   | FPR IF en captura normal nueva       | ≤ 0.30      | pendiente              | ⏳ PENDIENTE|

---

## Resumen ejecutivo

**15 de 16 criterios verificados. CA-16 pendiente de captura nueva.**

Todos los componentes del sistema cumplen los criterios de aceptación definidos en el plan del PPI:

- El **IF** detecta 99.4% de anomalías reales con AUC=0.8998 — discriminación sólida
- El **motor** responde en 34.8ms P95, 14 veces por debajo del límite de 500ms
- El **enforcement ipset** bloquea efectivamente IPs atacantes, protege whitelist, y escala a bloqueo permanente
- El **XGBoost v2** predice amenazas sostenidas con AUC=0.9992 y solo 14 errores sobre 12,488 muestras
- Las **40 corridas F6** muestran 100% disponibilidad y lead times dentro de criterios
- La **CA-16** (FPR en data nueva) puede ejecutarse siguiendo `v6_datos_nuevos_normal.md`

---

## Evidencias disponibles

| Evidencia | Ruta |
|---|---|
| Métricas IF | `results/metricas_offline.txt` |
| Curva ROC | `results/auc_roc.png` |
| Latencia | `results/latencia_pipeline.txt` |
| Métricas XGBoost | `results/metricas_predictor_v2.txt` |
| Corridas F6 | `results/resultados_f6_completo.csv` |
| Bitácora | `docs/bitacora/bitacora_escenarios.txt` |
| Log motor (bloqueos) | `results/motor_decision.log` |
| Gráficas F6 | `results/graficas_f6/` |
