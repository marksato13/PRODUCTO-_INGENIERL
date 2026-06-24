# Evaluación de Puntos Débiles para la Defensa

**PPI — Universidad Peruana Unión | Rubén Mark Salazar Tocas**

Este documento anticipa las preguntas más difíciles que pueden hacer los asesores o jurado durante la defensa, con la respuesta técnica correcta para cada una.

---

## BLOQUE 1 — Preguntas sobre el modelo

### P1. ¿Por qué usaste Isolation Forest y no un modelo supervisado como Random Forest o SVM?

**Por qué es difícil:** si tienes etiquetas (normal/anómalo), un modelo supervisado típicamente supera a uno no supervisado.

**Respuesta:**
El uso de un modelo supervisado requiere un dataset etiquetado representativo de todos los ataques posibles. En una red real, los ataques futuros son desconocidos. Isolation Forest aprende exclusivamente la estructura del tráfico normal (Grupo A), y marca como anómalo cualquier flow que se desvíe de esa estructura — incluyendo ataques no vistos en el entrenamiento. Esta es la ventaja fundamental del enfoque no supervisado para detección de anomalías en redes. Además, el FPR/TPR obtenido (AUC=0.8998, F1=0.9947) supera los requisitos del PPI y es competitivo con resultados de la literatura para este tipo de tarea.

---

### P2. El FPR es 20.47 %. ¿No es eso demasiado alto para un sistema de producción?

**Por qué es difícil:** 1 de cada 5 flows legítimos recibe score de anomalía — suena grave.

**Respuesta:**
Hay que distinguir entre FPR estadístico e impacto operativo real. El FPR=20.47% se mide en el holdout sin whitelist. En producción, el sistema aplica una whitelist de IPs internas que cubre el 100% de los orígenes legítimos del laboratorio → ITL efectivo = 0% en las 40 corridas de validación. Además, τ1 activa LIMIT (rate limiting a 100 pkt/s), no BLOCK — el tráfico legítimo que cae en esa zona no se interrumpe, solo se regula. El umbral de BLOCK es τ2, cuyo FPR es 1.99%. Bajar τ1 para reducir el FPR haría que ataques de SYN flood (score ≈ −0.49) escapen la detección.

---

### P3. ¿Por qué n_estimators=300? ¿Hiciste una búsqueda de hiperparámetros?

**Por qué es difícil:** podría parecer un valor arbitrario.

**Respuesta:**
Se realizó un análisis de estabilidad del AUC en función de n_estimators. El AUC se estabiliza a partir de n=200; se eligió n=300 para garantizar robustez sin costo computacional excesivo (entrenamiento < 10 s). Los demás hiperparámetros (`contamination=0.05`, `max_features=1.0`) están justificados en `F3_especificacion.md §8` con su criterio de selección.

---

### P4. ¿Por qué el umbral τ1 se derivó con el índice de Youden y no con otro criterio?

**Por qué es difícil:** hay muchos criterios posibles (F1-óptimo, costo mínimo, etc.).

**Respuesta:**
El índice de Youden (maximiza TPR − FPR) es el criterio estándar cuando se da igual peso a la sensibilidad y la especificidad. Para un sistema de seguridad donde tanto los falsos negativos (ataques no detectados) como los falsos positivos (bloqueos incorrectos) tienen consecuencias, este criterio es el más equilibrado. τ2 usa un criterio distinto (FPR ≤ 2%) porque BLOCK es una acción más agresiva que requiere alta precisión.

---

## BLOQUE 2 — Preguntas sobre la validación

### P5. 62 segundos de lead time — ¿eso es realmente "detección temprana"?

**Por qué es difícil:** 62 segundos parece mucho para un sistema "en tiempo real".

**Respuesta:**
El lead time de 62 s está determinado por una restricción de Suricata, no del modelo: el motor procesa flows cerrados (evento `netflow`), y Suricata solo cierra un flow TCP cuando recibe FIN/RST o expira el timeout. En un SYN flood los paquetes no completan el handshake, por lo que Suricata acumula el flow. Esta limitación es inherente a la arquitectura de captura basada en flows. Para mitigarla, el sistema incorpora detectores heurísticos (SSH brute force, HTTP abuse) que actúan sobre eventos individuales en < 5 s. En contexto: sistemas IDS comerciales basados en flows (NetFlow/IPFIX) tienen lead times similares o mayores.

---

### P6. ¿Las 40 corridas de F6 son realmente independientes?

**Por qué es difícil:** si los datos se acumulan entre corridas, los resultados no son independientes.

**Respuesta:**
Sí. Al finalizar cada corrida, el script `exportar_eve_por_escenario.sh` comprime el `eve.json` (gzip), trunca el archivo a 0 bytes y envía la señal `suricatasc reopen-log-files` para que Suricata empiece a escribir desde cero. Adicionalmente, se esperan ≥ 2 minutos entre corridas para garantizar la limpieza completa de los ipsets (`ppi_blocked` / `ppi_limited`). Cada corrida parte de un estado limpio del sistema.

---

### P7. Solo tienes 13 escenarios — ¿no es insuficiente para validar el sistema?

**Por qué es difícil:** parece poco comparado con datasets públicos de miles de ataques.

**Respuesta:**
Los 13 escenarios cubren las categorías de ataque más frecuentes en redes LAN universitarias: flood de capa 3 y 4 (SYN, UDP, ICMP), reconocimiento (port scan), abuso de aplicación (HTTP, SSH brute force) y escenarios mixtos con tráfico legítimo simultáneo. La literatura de detección de anomalías en redes (NSL-KDD, CICIDS2017) también clasifica los ataques en estas mismas categorías. La profundidad de validación (3+ repeticiones por escenario, 40 corridas totales) compensa la amplitud limitada.

---

### P8. ¿Cómo garantizas que el modelo no está sobreajustado al laboratorio?

**Por qué es difícil:** el train y el test son del mismo entorno controlado.

**Respuesta:**
Tres controles evitan el sobreajuste: (1) el modelo se entrena solo con Grupo A (tráfico normal) y nunca ve etiquetas de Grupo B durante el entrenamiento — no puede ajustarse a los ataques; (2) el split 80/20 es cronológico, no aleatorio, para evitar data leakage temporal; (3) el AUC se midió sobre 598,285 flows de Grupo B, un conjunto 11× más grande que el de entrenamiento. La diferencia entre AUC train y AUC test es < 1%, indicando generalización adecuada.

---

## BLOQUE 3 — Preguntas sobre el sistema

### P9. ¿Qué pasa si el atacante aprende los umbrales τ1/τ2 y genera tráfico que los evita?

**Por qué es difícil:** adversarial attacks contra sistemas de detección.

**Respuesta:**
Es una limitación real de cualquier sistema de detección basado en scores estáticos. Las mitigaciones son: (1) los umbrales no son públicos y están en un archivo de configuración del sensor; (2) el modelo IF tiene 300 árboles con particiones aleatorias — un atacante necesita conocer la estructura interna del modelo para evadir sistemáticamente; (3) los detectores heurísticos son más difíciles de evadir porque operan sobre contadores de eventos, no sobre el score IF. Generar exactamente 14 intentos SSH en 60 s (un menos que el umbral) para no ser bloqueado sigue siendo una restricción operativa para el atacante.

---

### P10. ¿Por qué no usaste un dataset público como NSL-KDD o CICIDS para validar?

**Por qué es difícil:** los datasets públicos tienen resultados de referencia comparables.

**Respuesta:**
Los datasets públicos tienen dos problemas para este PPI: (1) no reflejan el tráfico de la red universitaria específica — el objetivo es detectar anomalías en ese entorno, no en un entorno genérico de 2012 o 2017; (2) el objetivo del PPI es un sistema funcional desplegado en laboratorio, no un benchmark académico. Usar datos propios capturados con Suricata en el mismo entorno donde corre el sistema garantiza que el modelo aprende la distribución real del tráfico objetivo. Los resultados (AUC=0.8998, F1=0.9947) son comparables o superiores a los reportados en la literatura con NSL-KDD para Isolation Forest.

---

### P11. ¿El sistema puede funcionar en IPv6?

**Por qué es difícil:** muestra un punto ciego técnico.

**Respuesta:**
El sistema actual opera sobre IPv4. Suricata 7.0.3 soporta IPv6, pero las reglas de `iptables/ipset` usadas (`ppi_blocked`, `ppi_limited`) son específicas de IPv4. Para soporte IPv6 se requeriría migrar a `ip6tables` o usar `nftables` que unifica ambas familias. Es una limitación conocida documentada como trabajo futuro.

---

## BLOQUE 4 — Preguntas sobre el AE y la comparación

### P12. El Autoencoder tiene mejor AUC (0.9103 vs 0.8998). ¿Por qué no lo usas en producción?

**Por qué es difícil:** parece contradictorio elegir el modelo con menor AUC.

**Respuesta:**
Cuatro razones concretas: (1) el IF tiene 40 corridas F6 completamente validadas — el AE no tiene ninguna; reemplazar el modelo en producción requeriría repetir toda la campaña de validación; (2) el FPR del AE @ τ1 es mayor (25.68% vs 20.47%), lo que implicaría más falsas alarmas en tráfico legítimo; (3) la diferencia de AUC es 1.2% — dentro del margen de variabilidad experimental; (4) el entrenamiento del AE es 11× más lento (115 s vs < 10 s), lo que impacta el tiempo de arranque del sistema. Ambos modelos cumplen los requisitos del PPI. El IF es el más probado.

---

## Resumen — Niveles de riesgo por pregunta

| Pregunta | Riesgo | Preparación necesaria |
|---|---|---|
| P1 — Por qué IF y no supervisado | Alto | Explicar ventaja de detección de ataques desconocidos |
| P2 — FPR 20.47% | Alto | Distinguir FPR estadístico vs ITL operativo |
| P5 — Lead time 62s | Alto | Explicar limitación de Suricata + heurísticos |
| P8 — Sobreajuste | Medio | Explicar split cronológico + tamaño del test set |
| P9 — Evasión adversarial | Medio | Reconocer la limitación + mitigaciones |
| P12 — AE mejor AUC | Medio | Explicar validación incompleta del AE |
| P3 — n_estimators | Bajo | Análisis de estabilidad realizado |
| P6 — Independencia corridas | Bajo | Mecanismo de rotación de eve.json |
| P10 — Dataset público | Bajo | Justificación de datos propios |
| P11 — IPv6 | Bajo | Reconocer limitación + trabajo futuro |

