# Comparativa Metodológica del Pipeline — Flujo Anterior vs Flujo Corregido

**PPI — Universidad Peruana Unión 2026**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez

---

## 1. ¿Por qué se rediseñó el pipeline?

El flujo original fue construido siguiendo la lógica de un modelo **supervisado** (train/val/test),
pero Isolation Forest es **no supervisado** — solo necesita datos normales para aprender.
Ese desajuste generó tres problemas que hacían las métricas indefendibles:

| # | Problema en el flujo anterior | Consecuencia |
|---|---|---|
| 1 | `eve.json` acumulaba tráfico normal **y** ataques en la misma sesión | IF aprendía sobre datos "normales" contaminados por flujos de ataque |
| 2 | Se generaba `train/val/test.csv` (70/15/15) que IF **nunca usaba** | Confusión metodológica; parecía supervisado cuando no lo es |
| 3 | Tres evaluaciones distintas → tres métricas distintas (80.4 %, 87.6 %, 99.95 %) | Imposible citar una sola cifra en el informe |

**Solución aplicada:** separar la captura en tres grupos con propósito único cada uno,
eliminar las particiones supervisadas y establecer `metricas_offline.txt` como
**fuente única de verdad** para AUC, τ1, τ2, Precision, Recall y F1.

---

## 2. Flujo ANTERIOR — incorrecto

```mermaid
flowchart TD
    Desktop([Desktop]):::normal -->|curl / ssh / scp| EVE
    Kali([Kali]):::attack    -->|hping3 / nmap / hydra| EVE

    EVE[(eve.json\ntodo mezclado)] --> PAR[parser.py\ndataset_raw.csv]
    PAR --> ETQ[etiquetar_limpiar.py\ndataset_clean.csv]
    ETQ --> PRT[particionar_estadisticos.py]
    PRT --> CSV[(train 70%\nval 15% / test 15%)]

    PAR -->|filtra src_ip\ndatos contaminados| IFA[fase3_isolation_forest.py]
    CSV -. nunca usado por IF .-> IFA

    IFA --> PKL[(isolation_forest.pkl\nscaler.pkl)]
    PKL --> ROC[auc_roc_umbrales.py\nlee test.csv contaminado]
    ROC --> TAU[τ1 y τ2 hardcodeados\nen motor_decision.py]

    TAU --> MOT[motor_decision.py]
    MOT --> ENF[enforce.sh / ipset\nBLOCK · LIMIT · PERMIT]
    ENF --> F6A[f6_corridas.py\nsobre test.csv contaminado]

    classDef normal fill:#d4edda,stroke:#28a745
    classDef attack fill:#f8d7da,stroke:#dc3545
```

**Problemas en este flujo:**

```
❌ Desktop y Kali generan tráfico simultáneo → eve.json contamina datos normales
❌ train/val/test.csv creados pero IF los ignora completamente
❌ IF entrena con datos de sesión contaminada (no sesión "normal pura")
❌ Evaluación sobre test.csv contaminado → métricas sin validez estadística
❌ τ1/τ2 hardcodeados → edición manual en cada re-entrenamiento
❌ Naming de τ1/τ2 invertido entre reporte_metricas_v1.txt y motor_decision.py
❌ auc_por_escenario.py con fecha hardcodeada (20260602_*) → rompía otro día
```

---

## 3. Flujo NUEVO — correcto

```mermaid
flowchart TD
    DA([Desktop]):::normal  -->|curl / ssh / scp\nKali APAGADA| GZA
    KB([Kali]):::attack     -->|hping3 / nmap / hydra\nDesktop QUIETO| GZB
    DAC([Desktop]):::normal -->|tráfico normal| GZC
    KC([Kali]):::attack     -->|ataques\nMotor DETENIDO| GZC

    GZA[("Grupo A\n*_normal_*.gz")]
    GZB[("Grupo B\n*_anom_*.gz")]
    GZC[("Grupo C\n*_mixto_*.gz")]

    GZA --> TR["fase3_entrenar.py\nlee solo Grupo A"]
    TR -->|"80% entrena\nseed=42"| PKL2[("isolation_forest.pkl\nscaler.pkl\nfeatures.csv")]
    TR -->|"20% reservado\nnunca visto por modelo"| HOL[("normal_holdout.csv")]

    HOL --> EV["fase3_evaluar.py"]
    GZB --> EV
    PKL2 --> EV
    EV --> MET[("metricas_offline.txt\nAUC · τ1 · τ2\nPrecision · Recall · F1")]
    EV --> PNG[("auc_roc.png")]

    GZB --> ESC["auc_por_escenario.py\nB1-B6 y C1-C3"]
    GZC --> ESC
    MET -->|"lee τ1"| ESC
    ESC --> RPT[("auc_por_escenario.txt")]

    MET -->|"lee TAU1 TAU2\nal arrancar"| MOT2["motor_decision.py\ntail eve.json → score"]
    PKL2 --> MOT2
    MOT2 --> ENF2["enforce.sh / ipset\nPERMIT · LIMIT · BLOCK"]
    ENF2 --> F6B["f6_corridas.py\nMotor ACTIVO\nvalidación operacional"]

    classDef normal fill:#d4edda,stroke:#28a745
    classDef attack fill:#f8d7da,stroke:#dc3545
```

**Mejoras en este flujo:**

```
✓ Grupo A: captura dedicada con Kali apagada → datos normales 100% limpios
✓ Grupo B: Desktop quieto → datos de ataque puros, sin mezcla
✓ Grupo C: ambos activos con motor detenido → escenario mixto controlado
✓ Split 80/20 aleatorio (seed=42) sobre normales puros → holdout nunca visto
✓ fase3_evaluar.py produce UNA sola ejecución → metricas_offline.txt
✓ τ1/τ2 derivados automáticamente de ROC; motor los lee sin edición manual
✓ Naming consistente: τ1=PERMIT/LIMIT, τ2=LIMIT/BLOCK en todos los artefactos
✓ Globs date-agnostic (*_normal_*.gz) → scripts corren en cualquier fecha
✓ F6 valida con motor ACTIVO sobre tráfico real, no sobre CSV contaminado
```

---

## 4. Comparativa fase por fase

| Fase | Antes ❌ | Ahora ✓ | Por qué cambia |
|---|---|---|---|
| **F2 — Captura** | Un solo `eve.json` con normal + ataque mezclados | 3 grupos separados: A=normal, B=ataques, C=mixto | IF entrena SOLO con normales; mezclar contamina el aprendizaje |
| **F2 — Partición** | `train/val/test.csv` (70/15/15 cronológico) | Eliminado | IF no usa etiquetas ni partición supervisada |
| **F3 — Entrenamiento** | `dataset_raw.csv` filtrado por IP (sesión contaminada) | `*_normal_*.gz` de Grupo A (sesión dedicada) | Contaminación colapsa delta de scores de 0.69 a <0.20 |
| **F3 — Holdout** | Ninguno — evaluación sobre datos ya vistos | `normal_holdout.csv` 20% nunca visto por IF | Regla básica de ML: no evaluar sobre datos de entrenamiento |
| **F3 — Métricas** | Hasta 3 ejecuciones → 3 cifras distintas | `fase3_evaluar.py` → `metricas_offline.txt` único | Una sola cifra citada en informe, diapositivas y motor |
| **F3 — Umbrales τ** | Hardcodeados; naming invertido entre archivos | Escritos en `metricas_offline.txt`; motor los lee al arrancar | Reproducible y sin edición manual tras re-entrenamiento |
| **F4 — Motor** | `TAU1=-0.4973` constante en código | Lee `metricas_offline.txt` al iniciar | Actualización automática al re-entrenar |
| **F6 — Validación** | Sobre `test.csv` contaminado | Motor ACTIVO + tráfico mixto en tiempo real | Valida el sistema completo, no solo el modelo offline |

---

## 5. Por qué el flujo anterior producía 3 métricas distintas

```
Recall 80.4%  ← test.csv cronológico (corridas 03-10, contaminado con ataques)
Recall 87.6%  ← dataset_raw filtrado en f401_v2.py (distinto split, misma sesión)
Precision 99.95% ← F3_justificacion_modelo.md (comparación con modelos supervisados)
```

Tres pipelines distintos, tres "verdades" → ninguna era defendible.

Con el flujo corregido:

```
metricas_offline.txt ← UNA ejecución de fase3_evaluar.py
                        holdout normal (20%) + Grupo B (ataques puros)
                        AUC / τ1 / τ2 / Precision / Recall / F1
                        mismo valor en informe, diapositivas y motor
```

---

## 6. Artefactos: antes vs ahora

```
ANTES (generados, mayoría innecesarios para IF):        AHORA (solo lo necesario):
  data/dataset_raw.csv                                    data/raw/*_normal_*.gz  (Grupo A)
  data/dataset_clean.csv                                  data/raw/*_anom_*.gz    (Grupo B)
  data/train.csv  ← IF nunca lo usó                      data/raw/*_mixto_*.gz   (Grupo C)
  data/val.csv    ← IF nunca lo usó                      data/normal_holdout.csv
  data/test.csv   ← IF nunca lo usó                      models/isolation_forest.pkl
  models/isolation_forest.pkl                             models/scaler.pkl
  models/scaler.pkl                                       models/features.csv
  results/reporte_metricas_v1.txt  (τ naming invertido)  results/metricas_offline.txt ← único
  results/umbrales_finales.txt     (duplicado)            results/auc_roc.png
  results/auc_roc_umbrales.png     (nombre distinto)      results/reports/auc_por_escenario.txt
```

---

## 7. Respuestas clave para la defensa

**¿Por qué no usaste train/val/test?**
> IF es no supervisado — no usa etiquetas. Generar esas particiones era metodológicamente
> incorrecto y generaba la falsa apariencia de un modelo supervisado.

**¿Cómo garantizas datos normales puros?**
> Grupo A se captura con Kali **completamente apagada**. El script verifica conectividad
> fallida a Kali antes de iniciar. Adicionalmente, `src_filter={Desktop, Servidor}` descarta
> cualquier flujo residual de otra IP.

**¿Por qué el holdout no contamina el entrenamiento?**
> `train_test_split` divide los datos **antes** de ajustar el `StandardScaler`.
> El scaler hace `fit_transform` solo sobre el 80%; el holdout recibe solo `transform` →
> cero data leakage.

**¿Cómo se derivan τ1 y τ2?**
> De la curva ROC sobre datos nunca vistos (holdout + Grupo B):
> τ1 = `argmax(TPR − FPR)` (Youden) · τ2 = `max TPR donde FPR ≤ 2%`

**¿Por qué AUC y no accuracy?**
> AUC es independiente del umbral y mide separabilidad intrínseca. Con datos
> desbalanceados (mayoría normal), accuracy infla el resultado artificialmente.

---

*Generado: 2026-06-15 | Scripts: `scripts_f2/grupoA-C/` · `scripts/fase3_*.py`*
