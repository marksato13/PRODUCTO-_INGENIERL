# FASE 5 — Tablas Comparativas y Gráficas

**Generado:** 2026-06-17 11:40:19  
**Script:** `scripts/comparacion/f_generar_graficas.py`  
**Datos fuente:** `results/comparacion/04_resultados_modelos.json`

---

## Tabla 1 — Rendimiento predictivo (test set compartido 7,629 flows)

| Modelo | Grupo | AUC-ROC | Recall | Precision | F1 | FPR | FNR |
|---|---|---|---|---|---|---|---|
| **Isolation Forest** | one-class | 0.9159 | 0.9953 | 0.8136 | 0.8953 | 0.2038 | 0.0047 |
| **One-Class SVM** | one-class | 0.9712 | 0.9303 | 0.9120 | 0.9211 | 0.0802 | 0.0697 |
| **LOF** | one-class | 0.8418 | 0.5900 | 0.9104 | 0.7160 | 0.0519 | 0.4100 |
| **Autoencoder** | one-class | 0.9580 | 0.9883 | 0.8951 | 0.9394 | 0.1035 | 0.0117 |
| **Random Forest** \* | supervisado | 0.9997 | 0.9986 | 0.9956 | 0.9971 | 0.0040 | 0.0014 |
| **XGBoost** \* | supervisado | 0.9995 | 0.9986 | 0.9953 | 0.9969 | 0.0042 | 0.0014 |
| **Decision Tree** \* | supervisado | 0.9972 | 0.9975 | 0.9942 | 0.9958 | 0.0052 | 0.0025 |

\* Supervisados: conocen los ataques en entrenamiento — comparación no es justa.

## Tabla 2 — Costo computacional

| Modelo | T. train | ms/muestra | n_train | Escalable online |
|---|---|---|---|---|
| Isolation Forest | pre-entrenado | 0.0297 | 53,708 | ✅ SÍ |
| One-Class SVM | 0.6s | 0.0344 | 9,398 | ⚠️ PARCIAL |
| LOF | 0.3s | 0.0429 | 5,000 | ❌ NO |
| Autoencoder | 26.9s | 0.0010 | 9,398 | ✅ SÍ |
| Random Forest | 9.8s | 0.0399 | 17,798 | ✅ SÍ |
| XGBoost | 77.8s | 0.0075 | 17,798 | ✅ SÍ |
| Decision Tree | 0.1s | 0.0001 | 17,798 | ✅ SÍ |

## Tabla 3 — Adecuación al contexto real de producción

| Modelo | Requiere etiquetas ataques | Detecta ataque nuevo | Recall ≥ 90% | Latencia OK |
|---|---|---|---|---|
| Isolation Forest | ❌ | ✅ | ✅ (0.9953) | ✅ |
| One-Class SVM | ❌ | ✅ | ✅ (0.9303) | ✅ |
| LOF | ❌ | ✅ | ❌ (0.5900) | ✅ |
| Autoencoder | ❌ | ✅ | ✅ (0.9883) | ✅ |
| Random Forest | ✅ | ❌ | ✅ (0.9986) | ✅ |
| XGBoost | ✅ | ❌ | ✅ (0.9986) | ✅ |
| Decision Tree | ✅ | ❌ | ✅ (0.9975) | ✅ |

## Tabla 4 — Ranking one-class (comparación justa)

| Ranking AUC | Modelo | AUC | Ranking Recall | Recall | Viable producción |
|---|---|---|---|---|---|
| 1 | One-Class SVM | 0.9712 | 3 | 0.9303 | ✅ SÍ |
| 2 | Autoencoder | 0.9580 | 2 | 0.9883 | ✅ SÍ |
| 3 | Isolation Forest | 0.9159 | 1 | 0.9953 | ✅ SÍ |
| 4 | LOF | 0.8418 | 4 | 0.5900 | ❌ NO (Recall<90%) |

## Gráficas generadas

| Figura | Archivo | Descripción |
|---|---|---|
| Fig. 05_01 | `graficas/05_01_curvas_roc.png` | Curvas ROC superpuestas — todos los modelos |
| Fig. 05_02 | `graficas/05_02_auc_barras.png` | AUC-ROC por modelo (barras) |
| Fig. 05_03 | `graficas/05_03_recall_barras.png` | Recall por modelo — métrica crítica seguridad |
| Fig. 05_04 | `graficas/05_04_scatter_eficiencia.png` | Scatter: AUC vs tiempo de inferencia |
| Fig. 05_05 | `graficas/05_05_metricas_oneclass.png` | Métricas detalladas — solo one-class |

## Conclusiones de la comparación


### Entre modelos one-class (comparación justa)

**Ranking por AUC:** OCSVM (0.9712) > Autoencoder (0.9580) > IF (0.9159) > LOF (0.8418)
**Ranking por Recall:** IF (0.9953) > Autoencoder (0.9883) > OCSVM (0.9303) > LOF (0.5900)

- **IF tiene el mayor Recall** — detecta el 99.53% de los ataques (métrica crítica en seguridad)
- **OCSVM tiene mayor AUC** pero detecta 6.5% menos ataques que IF
- **LOF es inviable** — detecta solo el 59% de los ataques (inaceptable)
- **Autoencoder** es competitivo y candidato para ensemble

### Comparación con supervisados

Los supervisados (RF AUC=0.9997, XGB=0.9995, DT=0.9972) superan a todos los one-class en AUC
y Recall **gracias a que conocen los tipos de ataque de antemano**. Esto demuestra que:

1. Tener etiquetas mejora la clasificación — algo esperado y no sorprendente
2. La ventaja de RF/XGB no invalida la elección de IF — son paradigmas diferentes
3. Un modelo supervisado **no puede detectar un tipo de ataque no visto en entrenamiento**
4. IF logra AUC=0.9159 y Recall=99.53% **sin haber visto ningún ataque**

### Conclusión para la tesis

Entre los modelos que pueden usarse de forma realista en producción (one-class):
**Isolation Forest es la mejor opción según la métrica más importante en seguridad (Recall=99.53%).**

La elección de IF sobre OCSVM se justifica adicionalmente por:
- IF fue entrenado con 5.7× más datos normales (53,708 vs 9,398)
- IF tiene τ1/τ2 calibrados sobre distribución real de producción (598K+ anomalías)
- IF es más escalable (O(n log n) vs O(n²) para OCSVM con más datos)
- IF ya tiene whitelist e heurísticos (BF-SSH, HTTP-Abuse) integrados en el pipeline
