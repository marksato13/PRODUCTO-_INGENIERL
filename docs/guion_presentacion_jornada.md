# Guion de Presentación — XV Jornada Científica EP Ing. Sistemas UPeU 2026

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Isolation Forest  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Orden según pizarrón:** ① Carátula → ② Problema → ③ Objetivos → ④ Método + Producto Ingenieril → ⑤ Resultados → ⑥ Conclusiones

---

## DIAPOSITIVA 1 — CARÁTULA

### Lo que va en la diapositiva
- **Título:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Isolation Forest
- **Subtítulo:** XV Jornada Científica — EP Ingeniería de Sistemas · UPeU
- **Nombre:** Rubén Mark Salazar Tocas
- **Asesor:** Ing. Nemias Saboya Rios
- **Co-asesor:** Ing. Fernando Manuel Asin Gomez
- **Fecha:** Junio 2026
- **Logo UPeU** (ya incluido en plantilla)

### Lo que se dice oralmente
> "Buenos días a todos. Mi nombre es Rubén Mark Salazar Tocas, estudiante de Ingeniería de Sistemas de la Universidad Peruana Unión. El día de hoy presento mi Proyecto de Producto de Investigación, que propone un sistema de detección temprana de comportamientos anómalos en redes de datos mediante el algoritmo Isolation Forest, con control de tráfico en tiempo real."

**Tiempo estimado:** 20 segundos

---

## DIAPOSITIVA 2 — PROBLEMA (¿?)

### Lo que va en la diapositiva
- **Título:** PROBLEMÁTICA
- **Pregunta de investigación destacada:**
  > ¿De qué manera un sistema basado en Isolation Forest puede detectar comportamientos anómalos en la red UPeU y aplicar control inline en tiempo real?
- **3 bullets del problema:**
  - Las redes universitarias reciben ataques cuyas firmas son desconocidas a priori (zero-day)
  - Los IDS basados en firmas solo generan alertas pasivas — no bloquean automáticamente
  - No existe mecanismo de respuesta automática inline en la infraestructura actual
- **Hipótesis:**
  > Un modelo Isolation Forest entrenado sobre tráfico normal puede detectar ataques con AUC > 0.80 y latencia < 500 ms en un entorno universitario real.

### Lo que se dice oralmente
> "El problema que motiva este proyecto es el siguiente: las redes universitarias están expuestas a ataques de red cuyos patrones son desconocidos de antemano. Los sistemas de detección tradicionales, como Suricata o Snort en modo de firma, generan alertas pero no actúan. No bloquean. No limitan. Solo avisan."

> "Frente a eso, nos preguntamos: ¿es posible construir un sistema que aprenda el comportamiento normal de la red y que, cuando detecte una desviación, actúe automáticamente en tiempo real? Esa es la pregunta central de este trabajo."

> "La hipótesis es que sí es posible, y que ese sistema puede alcanzar un AUC mayor a 0.80 con una latencia de respuesta menor a 500 milisegundos."

**Tiempo estimado:** 45 segundos

---

## DIAPOSITIVA 3 — OBJETIVOS

### Lo que va en la diapositiva
- **Título:** OBJETIVOS
- **Objetivo General:**
  > Desarrollar e implementar un sistema de detección temprana de comportamientos anómalos en redes de datos mediante Isolation Forest con control de tráfico inline (iptables/ipset) en tiempo real sobre infraestructura universitaria.
- **Objetivos Específicos:**
  - OE1. Configurar un entorno de laboratorio con Suricata 7.0.3 para captura de tráfico normal y anómalo en 3 grupos separados (A · B · C)
  - OE2. Entrenar un modelo Isolation Forest (n=300) sobre tráfico normal y derivar umbrales de decisión τ1 y τ2 mediante curva ROC
  - OE3. Implementar un motor de decisión en tiempo real con latencia P95 < 500 ms que aplique PERMIT / LIMIT / BLOCK vía iptables e ipset
  - OE4. Validar el sistema en 40 corridas con disponibilidad ≥ 99% e ITL = 0%
- **Imagen recomendada:** `eda_distribucion_grupos.png` — muestra la distribución de tráfico capturado (justifica la necesidad del proyecto)

### Lo que se dice oralmente
> "El objetivo general es desarrollar e implementar este sistema completo, desde la captura de tráfico hasta el bloqueo automático en tiempo real."

> "Para eso definimos cuatro objetivos específicos. Primero, construir el laboratorio de pruebas con Suricata capturando tráfico real. Segundo, entrenar el modelo de Isolation Forest exclusivamente con tráfico normal — esto es clave y lo vamos a ver en metodología. Tercero, implementar el motor que clasifica cada flujo de red en menos de 500 milisegundos. Y cuarto, validar todo el sistema en 40 corridas controladas."

**Tiempo estimado:** 35 segundos

---

## DIAPOSITIVA 4 — MÉTODO · Etapas del pipeline

### Lo que va en la diapositiva
- **Título:** METODOLOGÍA
- **4 cuadrantes con las 6 fases encadenadas:**

| Cuadrante | Fases | Contenido |
|---|---|---|
| F1 — Entorno | Diagnóstico inicial | 4 VMs: Desktop · Sensor Suricata · Kali · Server · Suricata 7.0.3 en ens35 |
| F2 — Captura | Planificación | Grupo A Normal · B Anómalo · C Mixto · 47 archivos .gz · 105 M flows raw |
| F3+F4 — Modelo+Motor | Ejecución | IF n=300 · AUC=0.8998 · τ1=−0.4459 · τ2=−0.6027 · Latencia P95=34.8 ms |
| F5+F6 — Control+Validación | Evaluación | iptables/ipset · PERMIT/LIMIT/BLOCK · 40 corridas · Disponibilidad 100% |

- **Imagen:** `diagrama_pipeline.png` — flujo completo F1→F6 con scripts y archivos de salida

### Lo que se dice oralmente
> "La metodología se divide en 6 fases encadenadas, que seguimos en orden."

> "La Fase 1 construyó el laboratorio de pruebas con 4 máquinas virtuales: un escritorio desde donde generamos tráfico normal, un sensor con Suricata que captura todo, una máquina Kali que lanza los ataques, y un servidor Ubuntu como objetivo."

> "La Fase 2 capturó el tráfico en tres grupos separados: Grupo A con tráfico normal — Kali apagada —, Grupo B con ataques puros — Desktop quieto —, y Grupo C con tráfico mixto simultáneo. Esta separación no es opcional: es la condición necesaria para que Isolation Forest funcione, porque es un algoritmo one-class que solo aprende de datos normales."

> "La Fase 3 entrenó el modelo Isolation Forest con 53,708 flujos normales del Grupo A. Nunca vio los ataques del Grupo B durante el entrenamiento. Aun así, obtuvo un AUC de 0.8998."

> "La Fase 4 implementó el motor de decisión que lee el eve.json de Suricata en tiempo real, extrae 14 características por flujo, aplica el modelo y decide en menos de 35 milisegundos."

> "Las Fases 5 y 6 implementaron el control inline con iptables e ipset, y validaron el sistema completo en 40 corridas."

**Tiempo estimado:** 90 segundos

---

## DIAPOSITIVA 4B — PRODUCTO INGENIERIL + TIEMPO

> **Nota:** Esta sección puede ir en la misma diapositiva de Metodología o como slide aparte, según el tiempo disponible. El pizarrón la marcó como parte del bloque ④.

### Lo que va en la diapositiva
- **Producto Ingenieril:** Sistema IDPS operativo con 3 componentes:
  1. `motor_decision.py` — clasifica flujos en tiempo real
  2. `enforce.sh` + iptables/ipset — bloquea/limita automáticamente
  3. Dashboard web en `http://192.168.0.110:8080` — monitoreo en vivo
- **Tiempo de desarrollo:**

| Fase | Duración aproximada |
|---|---|
| F1 Entorno | 1 semana |
| F2 Captura (47 escenarios) | 3 semanas |
| F3 Modelado offline | 1 semana |
| F4+F5 Motor + Control | 2 semanas |
| F6 Validación 40 corridas | 1 semana |
| **Total** | **~8 semanas** |

### Lo que se dice oralmente
> "El producto ingenieril resultante es un sistema IDPS completamente operativo. No es solo el modelo — es el pipeline completo: captura, clasificación, acción y monitoreo. El motor corre como servicio en el sensor y actúa de forma autónoma. Hay un dashboard web accesible desde cualquier equipo de la red que muestra en tiempo real qué IPs están bloqueadas, cuántos eventos anómalos se han detectado y cuál es el estado del sistema."

**Tiempo estimado:** 30 segundos

---

## DIAPOSITIVA 5 — RESULTADOS

### Lo que va en la diapositiva
- **Título:** RESULTADOS
- **Tabla de métricas principales:**

| Métrica | Valor obtenido | Requisito | Estado |
|---|---|---|---|
| AUC-ROC | **0.8998** | > 0.80 | CUMPLE |
| Precision | **99.54%** | — | — |
| Recall (TPR) | **99.40%** | — | — |
| F1-Score | **0.9947** | — | — |
| Latencia P95 | **34.8 ms** | < 500 ms | CUMPLE |
| Lead Time SYN Flood | **61.92 s** | — | — |
| Disponibilidad | **100%** | ≥ 99% | CUMPLE |
| ITL (interrupción tráfico legítimo) | **0%** | = 0% | CUMPLE |

- **Imágenes:**
  - `auc_roc.png` — curva ROC con τ1 y τ2 marcados
  - `f6_07_panel_resumen.png` — panel de las 40 corridas
  - `f6_03_timeline_deteccion.png` — timeline de detección corrida 11
  - `f6_06_latencia_pipeline.png` — distribución de latencia por flujo

### Lo que se dice oralmente
> "Los resultados hablan por sí solos. El modelo obtuvo un AUC de 0.8998 — lo que significa que discrimina correctamente el 90% de los casos entre tráfico normal y anómalo, sin haber visto ningún ataque durante el entrenamiento."

> "La precisión es de 99.54% y el recall de 99.40% — prácticamente no hay falsos negativos. El sistema detecta casi todos los ataques reales."

> "En cuanto al tiempo de respuesta: la latencia del pipeline es de 34.8 milisegundos en el percentil 95. Eso está muy por debajo del límite de 500 ms que nos fijamos."

> "El lead time — tiempo desde que inicia un SYN flood hasta el primer bloqueo — es de 62 segundos. Ese tiempo no es del motor, sino del timeout TCP de Suricata para cerrar el flow. El motor en sí actúa en menos de 100 milisegundos."

> "En las 40 corridas de validación: disponibilidad del 100%, cero interrupciones al tráfico legítimo. El sistema no bloqueó ni una vez a un usuario normal."

**Tiempo estimado:** 75 segundos

---

## DIAPOSITIVA 6 — CONCLUSIONES

### Lo que va en la diapositiva
- **Título:** CONCLUSIONES
- **4 conclusiones numeradas:**

1. Isolation Forest es viable para detección de anomalías en redes universitarias en tiempo real (AUC = 0.8998 · Precision = 99.54% · Recall = 99.40%).

2. El paradigma one-class replica el escenario real: el modelo detecta ataques que NUNCA vio durante el entrenamiento, siguiendo el enfoque de detección por perfil (NIST SP 800-94).

3. El control inline (iptables/ipset) actúa en ~100 ms tras la detección, sin intervención humana, con timeout automático de 300 s y whitelist configurable.

4. En 40 corridas de validación: Disponibilidad 100% · ITL 0% · Lead Time SYN Flood = 61.92 s · Latencia P95 = 34.8 ms — todos los requisitos cumplidos.

### Lo que se dice oralmente
> "Como conclusiones finales:"

> "Primero: Isolation Forest sí es viable para este tipo de sistema en producción. Los números lo confirman."

> "Segundo: el enfoque one-class no es una limitación — es la fortaleza del sistema. Al aprender solo tráfico normal, puede detectar cualquier ataque desconocido, no solo los que ya existen en una base de firmas."

> "Tercero: el control inline cierra el ciclo. No es solo detección: es detección más respuesta automática en menos de 100 milisegundos."

> "Y cuarto: el sistema pasó 40 corridas de validación sin un solo error. Cero interrupciones al tráfico legítimo. Eso es lo más importante: la red sigue funcionando mientras el sistema protege."

**Tiempo estimado:** 60 segundos

---

## DIAPOSITIVA EXTRA — REFERENCIAS *(no se expone, solo se muestra)*

### Lo que va en la diapositiva
1. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation Forest. *IEEE ICDM*, 413–422.
2. NIST SP 800-94 (2007). *Guide to Intrusion Detection and Prevention Systems*. NIST.
3. Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR 12*, 2825–2830.
4. Roesch, M. (1999). Snort — Lightweight Intrusion Detection for Networks. *USENIX LISA*.
5. Albin, E., & Rowe, N. (2012). A realistic experimental comparison of Suricata and Snort. *ICITST*.

### Lo que se dice oralmente
> "Las referencias están en pantalla para quien quiera consultarlas. La base teórica principal es el paper original de Isolation Forest de Liu et al. 2008, y el marco normativo es el NIST SP 800-94."

**Tiempo estimado:** 15 segundos

---

## DIAPOSITIVA CIERRE — GRACIAS

### Lo que va en la diapositiva
- **"GRACIAS"** — diseño original de la plantilla UPeU
- Nombre del estudiante y correo de contacto (opcional)

### Lo que se dice oralmente
> "Eso es todo de mi parte. Quedo a disposición para responder las preguntas del jurado."

**Tiempo estimado:** 10 segundos

---

## Resumen de tiempos totales

| Sección | Tiempo |
|---|---|
| ① Carátula | 20 s |
| ② Problema | 45 s |
| ③ Objetivos | 35 s |
| ④ Método + Producto Ingenieril | 90 + 30 s |
| ⑤ Resultados | 75 s |
| ⑥ Conclusiones | 60 s |
| Referencias + Cierre | 25 s |
| **TOTAL** | **~6 minutos** |

---

## Preguntas frecuentes del jurado — respuestas preparadas

**"¿Por qué usó Isolation Forest y no Random Forest o XGBoost?"**
> "Porque en un IDPS real los ataques futuros son desconocidos — no tenemos sus etiquetas al momento de entrenar. Random Forest necesita ver ejemplos de ataque para aprender. IF no: aprende el perfil de lo normal y detecta cualquier desviación, incluidos ataques que nunca ha visto. Eso es lo que se necesita en producción."

**"¿Por qué los 3 grupos de datos están separados?"**
> "Es la condición necesaria del paradigma one-class. Si metiera los ataques del Grupo B al entrenamiento, IF aprendería que los floods también son normales y perdería la capacidad de detectarlos. La separación es BY DESIGN, no un error metodológico."

**"¿El 20% de falsos positivos no es demasiado alto?"**
> "El FPR de 20.47% se mitiga con la whitelist — las IPs de la red interna jamás son bloqueadas. En tráfico externo, un FPR alto en τ1 es aceptable porque τ1 no bloquea: solo clasifica como BAJA anomalía. Solo τ2 bloquea, y ahí el FPR es 2%. Si bajáramos τ1 al 5% de FPR, perderíamos detección de SYN floods que tienen score alrededor de −0.49."

**"¿Qué pasa si el motor falla?"**
> "El sistema falla abierto: si el motor se detiene, iptables mantiene las reglas activas hasta que se limpien manualmente. La disponibilidad del 100% en 40 corridas confirma que el motor no falló en ninguna corrida de 5 minutos. Para producción real se recomienda monitorear con el dashboard web y el servicio systemd."

**"¿Se puede escalar a una red más grande?"**
> "Sí. El cuello de botella es Suricata, no el motor. Suricata puede procesar múltiples interfaces. El modelo IF es pequeño (~2.5 MB) y la inferencia es O(log n) por flujo. La latencia de 34.8 ms es por flujo individual — se puede paralelizar."
