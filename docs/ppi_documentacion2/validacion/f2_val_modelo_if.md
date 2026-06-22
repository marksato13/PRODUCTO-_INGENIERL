# V1 — Validación del Modelo Isolation Forest (offline)

**Criterios:** CA-1, CA-2, CA-3, CA-4  
**Tiempo estimado:** 2 minutos  
**Requiere:** metricas_offline.txt generado por fase3_evaluar.py

---

## Qué se valida

El modelo IF fue entrenado con 53,708 flujos normales (80%). Esta validación verifica que las métricas sobre el holdout (13,427 flujos normales + 598,285 anómalos) cumplen los umbrales mínimos aceptables para el sistema en producción.

## Por qué importa

Si el AUC cae por debajo de 0.85, el modelo no discrimina suficientemente entre tráfico normal y anómalo. Si el TPR cae bajo 0.95, más del 5% de ataques reales pasarán sin detección. Si el FPR supera 0.25, demasiado tráfico legítimo recibirá LIMIT/BLOCK y el sistema será operativamente inaceptable.

---

## Criterios de aceptación

| CA   | Métrica         | Valor esperado | Valor real (metricas_offline.txt) | PASS/FAIL |
|------|-----------------|----------------|-----------------------------------|-----------|
| CA-1 | AUC-ROC         | ≥ 0.85         | 0.8998                            | ✅ PASS   |
| CA-2 | TPR en τ1       | ≥ 0.95         | 0.9940                            | ✅ PASS   |
| CA-3 | FPR en τ1       | ≤ 0.25         | 0.2047                            | ✅ PASS   |
| CA-4 | Precision en τ1 | ≥ 0.95         | 0.9954                            | ✅ PASS   |

---

## Cómo ejecutar

```bash
# En el sensor (192.168.0.110)
bash /home/m4rk/ppi-surikata-producto/scripts/validacion/test_v1_metricas_if.sh
```

O verificación manual:
```bash
cat /home/m4rk/ppi-surikata-producto/results/metricas_offline.txt
```

Valores clave a leer:
- `AUC-ROC` → debe ser ≥ 0.85
- `tau1_tpr` → debe ser ≥ 0.9500
- `tau1_fpr` → debe ser ≤ 0.2500
- `precision` (sección MÉTRICAS EN tau1) → debe ser ≥ 0.9500

---

## Cómo regenerar las métricas (si el modelo cambia)

```bash
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 scripts/fase3_evaluar.py
# Salida: results/metricas_offline.txt + results/auc_roc.png
```

---

## Interpretación de resultados

**AUC = 0.8998** no es perfecto (1.0), lo cual es esperado y correcto:
- El IF tiene overlap natural entre tráfico normal con patrones inusuales y tráfico anómalo leve
- AUC ≈ 0.90 indica buena discriminación sin señales de sobreajuste
- El AUC del XGBoost (0.9992) es más alto porque su tarea es más estrecha: clasificar eventos ya filtrados por el IF

**FPR = 20.47%** en τ1: el 20% de flujos normales reciben LIMIT. Esto se mitiga con la whitelist (192.168.0.20, 192.168.0.110, 192.168.0.120 nunca se bloquean). El FPR operativo real en producción es **0%** para los hosts del laboratorio.

---

## Referencia de archivos

| Archivo | Ruta en sensor |
|---|---|
| Métricas offline | `results/metricas_offline.txt` |
| Curva ROC PNG | `results/auc_roc.png` |
| Modelo IF | `models/isolation_forest.pkl` |
| Script evaluación | `scripts/fase3_evaluar.py` |
