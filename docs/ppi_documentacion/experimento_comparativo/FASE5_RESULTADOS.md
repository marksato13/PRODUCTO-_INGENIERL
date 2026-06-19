# FASE 5 — Resultados: Tablas Comparativas y Gráficas

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Script ejecutado:** `scripts/comparacion/f_generar_graficas.py`  
**Outputs detallados:** `results/comparacion/05_tablas_comparativas.md` + `results/comparacion/graficas/`  
**Fecha de ejecución:** 2026-06-17  
**Estado:** ✅ COMPLETADA

---

## Gráficas generadas (300 DPI, en `results/comparacion/graficas/`)

| Figura | Archivo | Qué muestra |
|---|---|---|
| **Fig. 1** | `05_01_curvas_roc.png` | Curvas ROC superpuestas — los 7 modelos en el mismo gráfico |
| **Fig. 2** | `05_02_auc_barras.png` | AUC-ROC por modelo — separación one-class / supervisados |
| **Fig. 3** | `05_03_recall_barras.png` | Recall por modelo — con línea de mínimo aceptable (90%) |
| **Fig. 4** | `05_04_scatter_eficiencia.png` | Scatter AUC vs tiempo de inferencia — tradeoff eficiencia |
| **Fig. 5** | `05_05_metricas_oneclass.png` | AUC, Recall, Precision, F1, 1-FPR solo para modelos one-class |

---

## Hallazgos visuales clave

### Fig. 1 — Curvas ROC
Los supervisados (RF, XGB, DT) forman un cluster compacto en la esquina superior izquierda (casi perfectos). Entre los one-class, OCSVM sube rápido pero luego se estanca. IF tiene una curva característica: sube bruscamente a FPR≈0.20 alcanzando Recall≈0.99, reflejo de que con τ1=−0.4459 detecta casi todos los ataques a costa de un FPR moderado.

### Fig. 2 — AUC-ROC
La separación visual entre one-class (~0.84–0.97) y supervisados (~0.997–0.999) es marcada. IF (0.9159) no es el mejor one-class en AUC — pero eso no es toda la historia.

### Fig. 3 — Recall (métrica crítica)
**El gráfico más importante para la tesis.** IF tiene el mayor Recall (0.9953) entre todos los one-class — supera incluso al Autoencoder (0.9883) y al OCSVM (0.9303). LOF queda claramente por debajo de la línea mínima aceptable del 90%.

### Fig. 4 — Scatter eficiencia
El Autoencoder está en la zona óptima (alto AUC, inferencia muy baja). IF está en posición competitiva. LOF aparece aislado (peor AUC, mayor latencia). Los supervisados tienen buen AUC pero latencia variable.

### Fig. 5 — Métricas one-class detalladas
IF destaca claramente en **Recall** (barra roja más alta). OCSVM destaca en **1-FPR** (menor tasa de falsas alarmas). El Autoencoder es el más equilibrado en F1. LOF muestra claramente su debilidad en Recall y F1.

---

## Tablas resumen (ver detalle completo en `05_tablas_comparativas.md`)

### Rendimiento predictivo

| Modelo | Grupo | AUC-ROC | Recall | F1 | FPR |
|---|---|---|---|---|---|
| **Isolation Forest** | one-class | 0.9159 | **0.9953** | 0.8953 | 0.2038 |
| One-Class SVM | one-class | **0.9712** | 0.9303 | 0.9211 | 0.0802 |
| LOF | one-class | 0.8418 | 0.5900 ❌ | 0.7160 | 0.0519 |
| Autoencoder | one-class | 0.9580 | 0.9883 | **0.9394** | 0.1035 |

> **Nota AE:** Los valores del Autoencoder en esta tabla corresponden al **experimento comparativo** (n_train=9,398, test balanceado de 7,629 flows). La evaluación de producción del AE con los mismos datos que el IF (n_train=53,708, 611,712 flows reales) da AUC=0.9103, Recall=99.42%, FPR=25.68% @ τ1, Block%=54.62% @ τ2. Ver `AE_PRODUCCION_DOCUMENTACION.md` y `RESULTADOS_COMPARACION_IF_AE.md`.

| Random Forest \* | supervisado | 0.9997 | 0.9986 | 0.9971 | 0.0040 |
| XGBoost \* | supervisado | 0.9995 | 0.9986 | 0.9969 | 0.0042 |
| Decision Tree \* | supervisado | 0.9972 | 0.9975 | 0.9958 | 0.0052 |

\* Ventaja injusta: conocen los ataques en entrenamiento.

### Ranking one-class (comparación justa)

| Por AUC | Modelo | AUC | Por Recall | Recall |
|---|---|---|---|---|
| 1 | OCSVM | 0.9712 | **IF (1)** | **0.9953** |
| 2 | Autoencoder | 0.9580 | Autoencoder (2) | 0.9883 |
| 3 | IF | 0.9159 | OCSVM (3) | 0.9303 |
| 4 | LOF | 0.8418 | LOF (4) | 0.5900 ❌ |

**IF es #1 en Recall — la métrica que importa en seguridad.**  
**LOF eliminado — Recall=59% inaceptable para un IDPS.**

---

## Conclusión de FASE 5

La evidencia experimental confirma que **Isolation Forest es la elección óptima** entre los modelos one-class para este dataset y contexto de producción:

1. **Recall=99.53%** — mayor entre all one-class (supera OCSVM en 6.5pp)
2. **LOF inviable** — Recall=59%, no cumple mínimo aceptable
3. **OCSVM viable pero inferior en Recall** — a pesar de mayor AUC
4. **Autoencoder competitivo** — candidato para ensemble en FASE 7
5. **Supervisados con ventaja injusta** — no son alternativas realistas

---

## Figuras adicionales — EDA y Diagrama de Pipeline

Generadas en respuesta a la preocupación del asesor sobre la unificación de los tres grupos de datos:

| Figura | Archivo | Qué muestra |
|---|---|---|
| **EDA Distribución** | `results/comparacion/eda_distribucion_grupos.png` | 3 paneles: flows raw por grupo (105.7M total), desglose Grupo B por ataque, flows usados por fase |
| **Diagrama Pipeline** | `results/comparacion/diagrama_pipeline.png` | Flujo completo F1→F6: qué grupos (A, B, C) entran en cada script y por qué |

**Punto clave del EDA:** el desbalance raw es 265:1 (anómalo+mixto vs normal). IF se entrena solo con el Grupo A (397,984 flows normales). Los Grupos B y C solo se usan en evaluación y validación F6. Esta separación es la arquitectura correcta para un sistema one-class.


---

**Siguiente fase:** `FASE6_JUSTIFICACION.md` — justificación final con evidencia experimental + texto verbatim para la sustentación.
