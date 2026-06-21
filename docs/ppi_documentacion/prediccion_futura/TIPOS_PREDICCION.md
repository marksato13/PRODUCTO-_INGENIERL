# Tipos de Predicción en Detección de Intrusiones

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-21

---

## Los 6 objetivos de predicción posibles

### Tipo 1 — Clasificación binaria temporal ← ESTE ES EL NUESTRO
**Pregunta:** ¿Habrá un ataque en los próximos N segundos? (sí / no)  
**Output:** probabilidad ∈ [0,1] → umbral → alerta preventiva  
**Label:** derivado de los BLOCKs del IF → `Δbloqueados_{t+1} > 0`  
**Modelos:** XGBoost, Random Forest, LSTM clasificador  
**Por qué encaja:** el IF ya produce la señal de BLOCK que usamos como ground truth. No necesitamos etiquetas externas — el propio sistema las genera.

---

### Tipo 2 — Regresión de tasa de anomalías
**Pregunta:** ¿Cuántas anomalías habrá en los próximos N segundos?  
**Output:** valor numérico (número de flows anómalos esperados)  
**Diferencia con Tipo 1:** predice magnitud, no presencia/ausencia  
**Modelos:** ARIMA, Prophet, LSTM regressor  
**Por qué no lo usamos:** saber que habrá "312 anomalías" en los próximos 60s no cambia la decisión de alerta. Solo nos importa si hay ataque o no → Tipo 1 es suficiente y más directo.

---

### Tipo 3 — Clasificación multi-clase temporal
**Pregunta:** ¿Qué tipo de ataque vendrá? (SYN Flood / BruteForce / PortScan / ...)  
**Output:** clase discreta (1 de 6 tipos)  
**Modelos:** XGBoost multiclass, LSTM con softmax  
**Por qué no lo usamos:** no tenemos suficientes corridas por tipo (6-8 por clase) para entrenar un clasificador multi-clase confiable. Además, la respuesta del sistema (LIMIT / BLOCK) no cambia según el tipo — la acción es la misma.

---

### Tipo 4 — Predicción de tiempo hasta el evento (Time-to-Event)
**Pregunta:** ¿En cuántos segundos ocurrirá el próximo ataque?  
**Output:** duración estimada (segundos)  
**Modelos:** Análisis de supervivencia (Kaplan-Meier, Cox, Weibull)  
**Por qué no lo usamos:** requiere modelar la distribución de tiempos entre ataques. Con 40 corridas controladas y disparadas manualmente, esos intervalos no tienen ningún patrón estadístico real — son artefactos de cuándo el estudiante ejecutó las pruebas.

---

### Tipo 5 — Forecasting prospectivo (predecir la serie + detectar desviación)
**Pregunta:** ¿La tasa de anomalías del siguiente período se desvía de lo esperado?  
**Output:** "la serie real supera el intervalo de confianza del forecast" → anomalía prospectiva  
**Modelos:** ARIMA/Prophet como detector, no como clasificador  
**Por qué no lo usamos:** es un detector de anomalías en la serie temporal, no un predictor de ataques. Repite el mismo rol del IF pero sobre la serie agregada — no añade una capa nueva al sistema.

---

### Tipo 6 — Predicción de secuencia de ataques (kill chain)
**Pregunta:** Dado que ocurrió PortScan → ¿qué ataque viene después?  
**Output:** siguiente evento en la cadena de ataque  
**Modelos:** Cadenas de Markov, LSTM seq2seq, N-gramas de eventos  
**Por qué no lo usamos:** requiere secuencias de ataques encadenados (reconocimiento → explotación → lateral movement). En este laboratorio cada corrida es un ataque aislado — no hay kill chains multi-etapa observables.

---

## Por qué elegimos Tipo 1 — Clasificación binaria temporal

Tres razones concretas:

**1. El label ya existe en nuestros datos.**  
El campo `bloqueados` en el log del motor sube cada vez que IF bloquea una IP. `Δbloqueados_{t+1} > 0` es el target sin necesidad de etiquetado manual.

**2. El output es directamente accionable.**  
`P(ataque) = 0.82` → activar alerta y pre-LIMIT. No necesitamos saber cuántos ataques ni de qué tipo. La respuesta del sistema es binaria: actuar o no actuar.

**3. Se integra naturalmente con el IF existente.**  
El IF detecta anomalías flujo a flujo en tiempo real (reactivo).  
El predictor XGBoost observa la serie de decisiones del IF en ventanas de 60s y predice si en la próxima ventana IF volverá a disparar (preventivo).  
Son capas complementarias, no competidoras.

```
IF:         flujo → score → BLOCK/LIMIT/PERMIT     (reactividad, <35ms)
Predictor:  serie de scores → P(BLOCK en t+1)      (prevención, cada 60s)
```

El predictor no reemplaza al IF — lo anticipa.

---

*Relacionado: `ANALISIS_PREDICCION.md` — arquitecturas secuenciales y plan de implementación*
