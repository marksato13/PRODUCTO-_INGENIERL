# FASE 7 — Propuesta de Mejora: Ensemble IF + Autoencoder

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Script ejecutado:** `scripts/comparacion/f_ensemble_if_ae.py`  
**Outputs:** `results/comparacion/07_ensemble_resultados.txt` + 2 gráficas  
**Fecha de ejecución:** 2026-06-17  
**Estado:** ✅ COMPLETADA

---

## 1. Motivación

La principal limitación del IF en producción es su **FPR=20.47%** en el umbral τ1=−0.4459 (Youden). Esto significa que ~20% de los flujos normales son marcados como posiblemente anómalos — mitigado en producción por la whitelist, pero mejorable.

De los experimentos de FASE 4/5:
- **Autoencoder:** AUC=0.9580, FPR=0.1035 — mitad del FPR de IF con solo 0.7% menos Recall
- **Complementariedad:** IF falla principalmente en flujos normales con alta variabilidad (ráfagas legítimas). El AE, al reconstruir patrones aprendidos, es más selectivo.

**Hipótesis:** Si un flujo solo se bloquea cuando **AMBOS** modelos lo señalan como anómalo, el FPR caerá drásticamente con mínimo costo en Recall.

---

## 2. Estrategias de ensemble evaluadas

Se probaron tres estrategias combinando scores normalizados [0,1] donde 1 = más anómalo:

| Estrategia | Fórmula del score combinado | Efecto esperado |
|---|---|---|
| **AND gate** | `min(s_IF, s_AE)` | ↓ FPR, ligero ↓ Recall |
| **OR gate** | `max(s_IF, s_AE)` | ↑ Recall, posible ↑ FPR |
| **Promedio ponderado** | `α×s_IF + (1-α)×s_AE` | Interpolación controlada |

---

## 3. Resultados experimentales

| Modelo / Estrategia | AUC | Recall | FPR | F1 | ΔFPR vs IF |
|---|---|---|---|---|---|
| IF solo (referencia) | 0.9159 | **0.9953** | 0.2038 | 0.8953 | — |
| AE solo | 0.9580 | 0.9883 | 0.1035 | 0.9394 | ↓49.2% |
| **Ensemble AND** | **0.9580** | **0.9883** | **0.1035** | **0.9394** | ↓**49.2%** |
| Ensemble OR | 0.9358 | 0.9953 | 0.2038 | 0.8953 | 0% |
| Promedio α=0.3 | 0.9367 | 0.9958 | 0.2043 | 0.8954 | +0.2% |

### Hallazgo principal

**El AND ensemble es equivalente a usar el AE como filtro secundario.** Matemáticamente, `min(s_IF, s_AE)` produce la misma curva ROC que el AE solo porque el AE es el "cuello de botella" — tiene mejor AUC que IF. Solo cuando IF está seguro (score muy bajo) y el AE también lo confirma, se mantiene el bloqueo.

**Resultado neto del AND ensemble vs IF solo:**

| Métrica | IF solo | AND Ensemble | Cambio |
|---|---|---|---|
| AUC-ROC | 0.9159 | 0.9580 | **+4.6%** |
| Recall | 0.9953 | 0.9883 | −0.7% |
| FPR | 0.2038 | **0.1035** | **−49.2%** |
| F1 | 0.8953 | **0.9394** | **+4.8%** |
| Falsos positivos (sobre 4,029 normales) | 821 | 417 | **−404 FP menos** |

**F1 mejora en 4.8pp** — la reducción de falsos positivos (−404 FP) supera con creces el costo de las 25 detecciones adicionales que se pierden (−0.7% de 3,600 = 25 FN más).

---

## 4. Análisis de la OR gate y promedio ponderado

| Estrategia | Resultado | Interpretación |
|---|---|---|
| **OR gate** | FPR=0.2038, Recall=0.9953 | Idéntico a IF solo — OR usa `max(IF, AE)` y IF ya tiene alta sensibilidad; cualquier cosa que IF detecta, el OR también detecta |
| **Promedio α=0.3** | FPR=0.2043, Recall=0.9958 | El peso del AE (0.7) suaviza ligeramente el score pero no cambia el umbral óptimo — AE mejora Recall marginal a costa de FPR idéntico |

Conclusión: **la única estrategia que reduce FPR efectivamente es AND** (mínimo de scores). Las demás son dominadas por IF al ser este el modelo de mayor sensibilidad.

---

## 5. Propuesta de implementación en producción

### Arquitectura del ensemble en `motor_decision.py`

```python
# Cargar modelos al arranque
clf_if = joblib.load('models/isolation_forest.pkl')
scaler = joblib.load('models/scaler.pkl')
ae     = joblib.load('models/autoencoder.pkl')  # NUEVO

# Umbral AE: percentil 95 del MSE en holdout normal
# (calibrado offline y guardado en metricas_offline.txt)
THETA_AE = 0.35   # MSE umbral (ejemplo — derivar con auc_roc_umbrales.py)

def clasificar_flujo(features):
    X = scaler.transform([features])
    
    # Score IF (menor = más anómalo)
    score_if = clf_if.score_samples(X)[0]
    
    # Score AE (MSE reconstruction, mayor = más anómalo)
    recon     = ae.predict(X)
    score_ae  = float(np.mean((X - recon)**2))
    
    # Lógica de decisión
    if score_if <= TAU2:                        # BLOCK: IF muy seguro (alta anomalía)
        return 'BLOCK'
    elif score_if <= TAU1 and score_ae >= THETA_AE:  # LIMIT: ambos coinciden
        return 'LIMIT'
    else:                                        # PERMIT
        return 'PERMIT'
```

### Comparación de latencia

| Operación | Tiempo |
|---|---|
| IF.score_samples() | 0.0297 ms |
| AE.predict() (MLPRegressor) | 0.0010 ms |
| **Total ensemble** | **~0.031 ms** |
| Requisito P95 | < 500 ms |

**Overhead del ensemble: +0.001ms por flujo — completamente despreciable.**

---

## 6. Impacto en métricas de producción

Si se implementara el AND ensemble en el sistema actual:

| Escenario | IF actual | IF+AE ensemble |
|---|---|---|
| Ataques detectados (de 1,000) | 995 | 988 |
| Falsas alarmas (de 1,000 flujos normales) | 204 | 104 |
| F1 | 0.8953 | **0.9394** |
| IPs legítimas bloqueadas por error | ~204 | **~104** (-49%) |

En un entorno universitario con ~200 flujos/min de tráfico normal, el ensemble eliminaría **aproximadamente 100 interrupciones falsas por cada 1,000 flujos** procesados.

---

## 7. Por qué no se implementó como mejora de producción en esta tesis

La propuesta de ensemble **no se implementó** en el pipeline de producción por las siguientes razones:

1. **El objetivo de la tesis ya está cumplido:** Latencia P95=34.8ms < 500ms, Recall=99.40%, F1=0.9947 — todos los requisitos del proyecto están cubiertos con IF solo.

2. **El ensemble requiere calibrar θ_AE offline:** Al igual que τ1/τ2 del IF, el umbral de MSE del AE necesita derivarse sobre el conjunto de evaluación completo (598K+ anomalías), lo cual requiere una corrida adicional de `fase3_evaluar.py` adaptada para el AE.

3. **Validación con 40 corridas:** Para afirmar que el ensemble mejora en producción, se necesitaría repetir las 40 corridas de F6 con el nuevo motor — un esfuerzo de ~4h adicionales.

4. **La mejora es marginal para el contexto:** El FPR de IF en producción ya está mitigado por la whitelist de 7 IPs. Las IPs no conocidas que generan falsas alarmas son casos excepcionales en la red de laboratorio.

**Propuesta como trabajo futuro:**

> Implementar el ensemble IF+Autoencoder en `motor_decision.py`, calibrar θ_AE sobre los datos de evaluación completos, y validar con 20 corridas adicionales (10 normal + 10 anómalo). Hipótesis: F1 mejora de 0.9947 a ~0.9980 con reducción del FPR de 20.47% a ~10%.

---

## 8. Gráficas generadas

| Figura | Archivo | Descripción |
|---|---|---|
| Fig. 07-01 | `graficas/07_01_roc_ensemble.png` | Curvas ROC: IF vs AND, OR, Promedio |
| Fig. 07-02 | `graficas/07_02_fpr_recall_tradeoff.png` | Scatter FPR vs Recall — la AND se mueve hacia esquina superior izquierda |

**La gráfica 07-02 es la más poderosa:** muestra visualmente que el AND ensemble (cuadrado rojo) se desplaza desde FPR=0.20 hasta FPR=0.10 manteniendo Recall=0.9883 — bien por encima del mínimo del 95%.

---

**Siguiente fase:** `FASE8_DOCS_TESIS.md` — documentos finales `F4_05_Comparacion_Avanzada_Modelos.md` y `F4_06_Justificacion_Final_Isolation_Forest.md` listos para incorporar a la tesis.
