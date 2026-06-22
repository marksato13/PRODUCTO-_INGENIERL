# Resultados de Validación — PPI UPeU 2026

**Ejecución:** `bash scripts/validacion/run_all.sh`  
**Fecha:** 2026-06-22 15:04:05  
**Log completo:** `results/validacion_20260622_150405.log`  
**Validado por:** Rubén Mark Salazar Tocas

---

## Tabla resumen PASS/FAIL — ejecución real 2026-06-22

| CA    | Fase | Qué se midió                              | Criterio        | Valor obtenido              | Estado        |
|-------|------|-------------------------------------------|-----------------|-----------------------------|---------------|
| CA-1  | F2   | AUC-ROC Isolation Forest                  | ≥ 0.85          | **0.8998**                  | ✅ PASS       |
| CA-2  | F2   | TPR en τ1 = −0.4459 (Youden)              | ≥ 0.95          | **0.9940** (99.40%)         | ✅ PASS       |
| CA-3  | F2   | FPR en τ1                                 | ≤ 0.25          | **0.2047** (20.47%)         | ✅ PASS       |
| CA-4  | F2   | Precision en τ1                           | ≥ 0.95          | **0.9954** (99.54%)         | ✅ PASS       |
| CA-5  | F3   | Latencia P95 pipeline eve→decisión        | < 500ms         | **34.768ms**                | ✅ PASS       |
| CA-6  | F3   | Motor activo + ITL log                    | activo / 0%     | **1,180,360 entradas**      | ✅ PASS       |
| CA-7  | F3   | τ1/τ2 cargados — estadística motor        | −0.4459/−0.6027 | **verificado en log**       | ✅ PASS       |
| CA-8  | F3   | Whitelist 5 IPs nunca en ipset BLOCK      | 0 entradas      | **0/5 en block_counts**     | ✅ PASS       |
| CA-9  | F3   | IP atacante bloqueada (evidencia log)     | BLOCKs reales   | **12,811 BLOCKs a Kali**    | ✅ PASS       |
| CA-10 | F3   | Bloqueo progresivo activo                 | registro en JSON| **Kali #2 → próximo perm.** | ✅ PASS       |
| CA-11 | F4   | AUC-ROC XGBoost v2 (test 12,488 muestras)| ≥ 0.95          | **0.9992**                  | ✅ PASS       |
| CA-12 | F4   | FP + FN totales en test set               | ≤ 30            | **14** (7 FP + 7 FN)        | ✅ PASS       |
| CA-13 | F5   | Cron jobs reentrenamiento configurados    | 2 cron activos  | **IF dom 02:00 / XGB 03:00**| ✅ PASS       |
| CA-14 | F5   | Corridas de reentrenamiento registradas   | ≥ 1 corrida     | **3 corridas en métricas**  | ✅ PASS       |
| CA-15 | F6   | Corridas completadas                      | 40/40           | **40/40 — 100%**            | ✅ PASS       |
| CA-16 | F2   | FPR con captura normal nueva              | ≤ 0.30          | pendiente                   | ⏳ PENDIENTE  |

---

## Resumen ejecutivo

**15 de 16 criterios verificados — 1 pendiente (CA-16, requiere captura nueva).**

### F1 — Captura de datos
- Suricata 7.0.3 activo en ens35 (modo promiscuo)
- eve.json: 500 MB — 843,323 líneas — actualizado en tiempo real
- Último evento: `2026-06-22T15:04:05` tipo=flow src=192.168.0.20→192.168.0.110:8080

### F2 — Isolation Forest (offline)
- Entrenado con 53,708 flujos normales (80% split aleatorio)
- Holdout 13,427 flujos + 598,285 anómalos → AUC = **0.8998**
- τ1 = −0.4459 (Youden): TPR=99.40%, FPR=20.47%
- τ2 = −0.6027 (FPR≤2%): TPR=18.27%

### F3 — Motor de decisión + enforcement
- Latencia P95 = **34.768ms** (×14 por debajo del límite de 500ms)
- Log activo: 1,180,360 entradas registradas en tiempo real
- Latencia media del motor: **34.44ms** (estadística en vivo del log)
- Whitelist: 5/5 IPs protegidas — ninguna en ipset BLOCK
- BLOCKs ejecutados: **12,811** (todos sobre 192.168.0.100 — Kali)
- 192.168.0.100 en bloqueo #2 → próximo bloqueo será PERMANENTE (timeout=0)

### F4 — Predictor XGBoost v2
- Test set: 12,488 muestras (20% estratificado, nunca visto en entrenamiento)
- AUC-ROC = **0.9992**
- Errores: 7 FP + 7 FN = **14 totales** de 12,488 (0.11%)
- 9 features comportamentales (sin score IF — leakage corregido)

### F5 — Aprendizaje continuo
- **IF:** cron domingos 02:00 — última corrida 2026-06-22 02:27 → reemplazado=SI (AUC estable 0.9548)
- **XGBoost:** cron diario 03:00 — 3 corridas registradas:
  - horas=720, events=62,115 → AUC 1.0000→0.9999, reemplazado=SI
  - horas=24, events=517 → AUC 0.9762→0.9583, reemplazado=SI (degradación < 0.05)
  - horas=24, events=517 → AUC estable 0.9583, reemplazado=SI
- Protección anti-regresión activa: cron con 91 eventos → rechazado (<100 mínimo)
- Modelos actuales: IF (jun 22 02:28) — XGBoost (jun 22 08:05)

### F6 — Validación corridas
- **40/40 corridas completadas** — disponibilidad 100%
- Distribución: 10 normal + 10 final + 10 mixto + 10 reeval
- 7 gráficas PNG 300 DPI generadas en `results/graficas_f6/`
- 64 entradas en bitácora de escenarios

---

## CA-16 pendiente — cómo completarla

Capturar tráfico normal nuevo (diferente sesión/horario) y verificar FPR del IF:

```bash
# En sensor (192.168.0.110)
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate
# Ver instrucciones completas:
cat docs/ppi_documentacion2/validacion/f2_val_datos_nuevos.md
```

Criterio: FPR ≤ 0.30 en la nueva captura → CA-16 ✅ PASS

---

## Evidencias archivadas

| Archivo | Contenido |
|---|---|
| `results/validacion_20260622_150405.log` | Output completo del run_all.sh |
| `results/metricas_offline.txt` | Métricas IF — AUC, τ, TPR/FPR |
| `results/latencia_pipeline.txt` | P95=34.768ms, throughput |
| `results/metricas_predictor_v2.txt` | XGBoost AUC=0.9992, matriz confusión |
| `results/metricas_f5_if.txt` | Historial reentrenamiento IF |
| `results/metricas_f5_xgboost.txt` | Historial reentrenamiento XGBoost |
| `results/resultados_f6_completo.csv` | 40 corridas detalladas |
| `results/block_counts.json` | Estado bloqueo progresivo por IP |
| `results/graficas_f6/` | 7 PNG 300 DPI para informe |
| `docs/bitacora/bitacora_escenarios.txt` | 64 entradas de corridas |
