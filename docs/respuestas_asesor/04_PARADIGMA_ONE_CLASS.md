# 04 — Paradigma One-Class: respuesta a la confusión del asesor

**Archivo:** `docs/respuestas_asesor/04_PARADIGMA_ONE_CLASS.md`  
**Relacionado con:** `FASE1_ANALISIS.md`, `F2_diagrama.drawio.md`, `F3_diagrama.drawio.md`  
**Estado:** Respuesta completa con evidencia empírica

---

## 1. Cuál fue la duda del asesor

El asesor observó que el dataset tiene 3 grupos separados:
- Grupo A — Normal (28 archivos, 67,135 flows)
- Grupo B — Anómalo (13 archivos, 906,188 flows)
- Grupo C — Mixto (6 archivos)

Y preguntó: **"¿Por qué no unificar los 3 grupos en un solo dataset para entrenar?"**

La pregunta es razonable desde la perspectiva supervisada clásica: si tienes datos etiquetados de dos clases, lo natural sería mezclarlos y entrenar un clasificador binario.

---

## 2. Por qué esa lógica no aplica aquí

Isolation Forest es un algoritmo **ONE-CLASS**. Su método `fit()` solo recibe datos de una clase (la normal). No existe en su diseño el concepto de "clase anómala en entrenamiento".

```python
# Así funciona IF — solo recibe datos normales
model = IsolationForest(n_estimators=300, contamination=0.05)
model.fit(X_train_normal)   # ← SOLO Grupo A, 53,708 flows

# La evaluación usa los anómalos — pero DESPUÉS de entrenar
scores = model.score_samples(X_anom)   # ← Grupo B, para calcular AUC
```

**Si se mezclaran B y C en el `fit()`:**
- IF aprendería que los floods de SYN, UDP, ICMP también son "normales"
- Al llegar tráfico real de ataque, no lo distinguiría del perfil aprendido
- El modelo colapsaría — AUC caería de 0.8998 hacia 0.5 (aleatorio)

Los 3 grupos separados no son un error metodológico. Son la **condición necesaria** para que IF funcione correctamente.

---

## 3. Evidencia empírica del EDA (FASE1_ANALISIS.md)

### 3.1 Las 14 features SÍ discriminan (Mann-Whitney U, p < 0.001)

El EDA demuestra que el espacio de features separa bien los dos tipos de tráfico:

| Feature más discriminante | Mediana normal | Mediana anómalo | Ratio |
|---|---|---|---|
| `byte_ratio` | 0.955 | 60.0 | **62.8×** |
| `bytes_toclient` | 826 bytes | 0 bytes | — |
| `duration` | 0.044 s | 0.001 s | — |
| `is_tcp` | 1.0 (100%) | 0.0 (0%) | — |

**14/14 features discriminan** — p-valor = 0.0 en todas (Mann-Whitney U no paramétrico).

Esto confirma que IF tiene suficiente señal para aprender el perfil normal y detectar desviaciones.

### 3.2 Desbalance extremo: 1:67.5 (favorable para one-class)

| Clase | Flows usables | % |
|---|---|---|
| Normal (label=0) | 13,427 | 1.5% |
| Anómalo (label=1) | 906,188 | 98.5% |

- Para **one-class (IF):** el desbalance es **irrelevante** — el entrenamiento usa solo la clase normal
- Para **supervisados (RF, XGBoost):** se requiere `class_weight='balanced'` y técnicas de oversampling (SMOTE), lo cual introduce complejidad adicional sin garantía de mejora en producción donde los ataques son desconocidos

### 3.3 El paradigma es semi-supervisado, no no-supervisado

| Pregunta | Respuesta |
|---|---|
| ¿Es supervisado? | NO — entrenamiento sin etiquetas de ataque |
| ¿Es no-supervisado? | PARCIALMENTE — paradigma one-class en entrenamiento |
| ¿Es semi-supervisado? | SÍ — ground truth implícito solo para evaluación |

El ground truth (qué archivos son normales y cuáles anómalos) existe pero se usa **únicamente para evaluar**, no para entrenar. Esto replica el escenario real donde los ataques futuros son desconocidos a priori (NIST SP 800-94).

---

## 4. Comparación directa: one-class vs supervisado

Para responder si IF es peor que un supervisado, se ejecutó el experimento comparativo en `scripts/comparacion/`:

| Modelo | Paradigma | AUC | Nota |
|---|---|---|---|
| Isolation Forest | One-class (producción) | **0.8998** | Sin ver ataques en entrenamiento |
| Random Forest | Supervisado (upper bound) | > 0.99 | Vio ataques en entrenamiento — ventaja injusta |
| XGBoost | Supervisado (upper bound) | > 0.99 | Idem |
| One-Class SVM | One-class | < IF | Sensible a skew, lento con 53K flows |

**Argumento clave:** Si Random Forest supera a IF, eso demuestra que *conocer los ataques de antemano* mejora la detección — no que IF sea una mala elección. En producción real, los ataques futuros son desconocidos; el supervisado no tiene esa ventaja.

---

## 5. Por qué IF es la elección correcta para este problema

| Factor del dataset | Impacto en la elección |
|---|---|
| Sin etiquetas de ataque en entrenamiento | One-class es el único paradigma realista |
| 14 features, skewness alta | IF insensible; OCSVM y LOF afectados |
| 53K flows de entrenamiento | IF O(n log n) < 10s; OCSVM O(n²) = 5-30 min |
| Desbalance 1:67 | No afecta IF; afecta críticamente a supervisados |
| Ataques futuros desconocidos | IF generaliza; supervisado solo detecta ataques vistos |

---

## 6. Cómo justificarlo verbalmente en la defensa

**Si el asesor pregunta "¿por qué no unificó los datos?":**

> "Isolation Forest es un algoritmo one-class: su método `fit()` recibe únicamente datos de la clase normal. Si incluyera los datos anómalos en el entrenamiento, el modelo aprendería el perfil de los ataques como si fueran normales y perdería capacidad de detección. Los tres grupos están separados por diseño, siguiendo el paradigma de detección de anomalías basado en perfil descrito en NIST SP 800-94. El Grupo A entrena el modelo, los Grupos B y C evalúan su capacidad de generalización sobre ataques que nunca vio."

**Si el asesor pregunta "¿y si hubiera usado Random Forest?":**

> "Lo evaluamos en el experimento comparativo. Un supervisado obtiene mayor AUC porque conoce los ataques de antemano durante el entrenamiento. Esa ventaja es injusta en el escenario real de un IDPS, donde los ataques futuros son desconocidos. IF obtiene AUC=0.8998 sin haber visto ningún ataque — eso es lo que se busca en detección de anomalías en red."

**Si el asesor pregunta "¿cómo sabe que el modelo está bien entrenado?":**

> "Las métricas de evaluación lo confirman: AUC=0.8998, Precision=99.54%, Recall=99.40%, F1=0.9947, latencia P95=34.8ms. Un modelo mal entrenado produciría AUC cercano a 0.5. Además, el EDA muestra que 14/14 features discriminan estadísticamente entre tráfico normal y anómalo con p-valor cero en Mann-Whitney U."

---

## 7. Referencias internas

| Documento | Contenido relevante |
|---|---|
| `FASE1_ANALISIS.md` | EDA completo: estadísticas, discriminabilidad, desbalance |
| `FASE6_JUSTIFICACION.md` | Justificación formal de la elección de IF |
| `COMPARACION_IF_VS_ALTERNATIVAS.md` | Experimento comparativo one-class vs supervisados |
| `F2_diagrama.drawio.md` | Diagrama visual del paradigma one-class (Mermaid + Draw.io) |
| `F3_diagrama.drawio.md` | Flujo de entrenamiento: qué grupos entran a IF.fit() |
| `results/comparacion/eda_distribucion_grupos.png` | Figura EDA: distribución de flows por grupo |
| `results/comparacion/diagrama_pipeline.png` | Diagrama pipeline: qué grupo va a qué script |
