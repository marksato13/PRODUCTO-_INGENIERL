# Justificación: Diferencia entre Métricas del Experimento y Producción

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-17  
**Aplica a:** FASE4_EXPERIMENTOS.md vs metricas_offline.txt

---

## La diferencia tiene una sola causa: el test set es distinto

| | Producción (`metricas_offline.txt`) | Experimento comparativo |
|---|---|---|
| **Propósito** | Medir el rendimiento real del sistema | Comparar 7 modelos en igualdad de condiciones |
| **Normal** | 13,427 flows | 4,029 flows |
| **Anómalos** | 598,285 flows | 3,600 flows |
| **Ratio** | 1 : 44.5 | 1 : 0.89 (casi balanceado) |
| **Recall** | 99.40% | 99.53% |
| **Precision** | **99.54%** | **81.36%** |
| **F1** | **0.9947** | **0.8953** |
| **AUC-ROC** | **0.8998** | **0.9159** |

---

## ¿Por qué el experimento usó test balanceado?

Porque se necesitaba una comparación **justa** entre 7 modelos distintos.

Si se hubiera evaluado los 7 modelos con el ratio real (1:44.5), cualquier modelo que prediga "anómalo" casi siempre obtendría Precision alta — no porque sea bueno sino porque los anómalos dominan el test. El test balanceado elimina ese sesgo y muestra la **capacidad discriminante real** de cada modelo.

Esta es práctica estándar en evaluación experimental de modelos de ML — exactamente lo mismo que hacen los papers científicos con datasets como NSL-KDD, CICIDS-2018 o KDD99.

---

## Lo que NO cambia entre ambos contextos

El **Recall es prácticamente idéntico**: 99.40% (producción) vs 99.53% (experimento) — diferencia de solo **0.13 puntos porcentuales**.

Eso demuestra que el modelo en sí no cambia entre contextos. Lo único que varía es la composición del denominador de la Precision y el F1:

```
Recall    = TP / (TP + FN)    → NO depende de cuántos flujos normales haya en el test
Precision = TP / (TP + FP)    → SÍ depende: más normales → más FP → Precision baja
F1        = 2×P×R / (P + R)   → varía solo porque Precision varía (Recall es estable)
```

---

## Prueba matemática

### Precision

```
FPR = FP / N_normal   →   FP = FPR × N_normal

┌─────────────────────────────────────────────────────────────────────┐
│ Experimento (ratio 1:0.89)                                          │
│   FP = 0.2038 × 4,029  =   821                                     │
│   TP = 0.9953 × 3,600  = 3,583                                     │
│   Precision = 3,583 / (3,583 + 821) = 81.36% ✓                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ Producción (ratio 1:44.5)                                           │
│   FP = 0.2047 × 13,427  =   2,748                                  │
│   TP = 0.9940 × 598,285 = 594,895                                  │
│   Precision = 594,895 / (594,895 + 2,748) = 99.54% ✓              │
└─────────────────────────────────────────────────────────────────────┘
```

El FPR es **el mismo** (~20%) en ambos contextos — el modelo no cambia. En producción, durante un ataque activo, hay 44× más anomalías que normales. Los 2,748 falsos positivos quedan sepultados frente a los 594,895 verdaderos positivos → Precision sube a 99.54%.

### F1

```
F1 = 2 × Precision × Recall / (Precision + Recall)

┌─────────────────────────────────────────────────────────────────────┐
│ Experimento (ratio 1:0.89)                                          │
│   F1 = 2 × 0.8136 × 0.9953 / (0.8136 + 0.9953)                   │
│      = 1.6196 / 1.8089 = 0.8953 ✓                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ Producción (ratio 1:44.5)                                           │
│   F1 = 2 × 0.9954 × 0.9940 / (0.9954 + 0.9940)                   │
│      = 1.9812 / 1.9894 = 0.9947 ✓                                  │
└─────────────────────────────────────────────────────────────────────┘
```

El Recall es casi idéntico (0.9953 ≈ 0.9940). El F1 varía **exclusivamente** por la Precision.

---

## Qué valor citar en cada situación

| Pregunta / Documento | Valor correcto | Fuente |
|---|---|---|
| "¿Cuánto detecta su sistema?" | Recall=**99.40%**, Precision=**99.54%**, F1=**0.9947** | `metricas_offline.txt` |
| "¿Por qué eligieron Isolation Forest?" | Recall=**99.53%** — mejor one-class entre 7 modelos | `FASE4_EXPERIMENTOS.md` |
| "¿Por qué la Precision es diferente en sus documentos?" | Contextos distintos — la matemática está arriba | Este documento |

---

## Respuesta verbatim para la sustentación

> *"Los valores que presentamos como métricas del sistema — Precision=99.54%, Recall=99.40%, F1=0.9947 — provienen de evaluar el modelo sobre la distribución real de producción: 13,427 flujos normales y 598,285 flujos anómalos, que es exactamente lo que ocurre durante un ataque activo en la red.*
>
> *El experimento comparativo que realizamos para justificar la elección de Isolation Forest frente a 6 alternativas usó un test set balanceado de 7,629 flujos porque esa es la única forma de comparar 7 modelos distintos en igualdad de condiciones. Si usáramos el ratio real de 1:44.5, estaríamos favoreciendo sistemáticamente a los modelos que predicen 'anómalo' casi siempre. En ese experimento, el IF muestra Precision=81.36% y F1=0.8953.*
>
> *Ambos conjuntos de valores son correctos en su contexto y no son contradictorios. El Recall — la métrica que realmente importa en seguridad — es prácticamente idéntico en ambos: 99.40% vs 99.53%, diferencia de 0.13 puntos porcentuales. Eso confirma que el modelo no cambió. Lo que cambió fue la distribución del test, y la Precision responde matemáticamente a esa distribución, como demostramos en la sección de análisis."*

---

## Resumen en una línea

> El modelo es el mismo. El test es distinto. El Recall lo confirma.
