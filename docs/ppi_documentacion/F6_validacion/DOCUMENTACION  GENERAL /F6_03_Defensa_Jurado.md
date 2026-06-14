# F6-03: Defensa ante Jurado — 50 Preguntas Difíciles con Respuestas

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F6 — Validación y Resultados  
**Documento:** F6-03 — Defensa ante Jurado  
**Fecha:** 2026-06-14

---

> **Instrucción de uso:** Cada pregunta tiene una respuesta recomendada de sustentación de 3–5 líneas. Memorizar la respuesta corta; los detalles técnicos están documentados en F4-02, F4-03, F5-01, F5-02 y F6-01.

---

# SECCIÓN A — METODOLOGÍA (10 preguntas)

---

**A01. ¿Por qué eligieron un enfoque no supervisado en lugar de supervisado para detectar ataques?**

*Respuesta:* Los modelos supervisados (Random Forest, SVM) requieren etiquetas de ataques para entrenar, lo que significa que solo detectan ataques vistos previamente. Nuestro sistema usa Isolation Forest no supervisado que aprende exclusivamente del tráfico normal, permitiendo detectar cualquier anomalía estadística sin importar su tipo. Esto fue validado empíricamente en F2-04: el sistema detectó 12/12 variantes de ataque no incluidas en el entrenamiento, con recall del 100%.

---

**A02. ¿Cómo justifican la representatividad de sus escenarios de prueba?**

*Respuesta:* Los 6 escenarios anómalos (B1–B6) mapean directamente a las 5 categorías MITRE ATT&CK de mayor prevalencia en redes universitarias latinoamericanas según UNAM-CERT 2024. Adicionalmente, la naturaleza no supervisada del modelo garantiza que no está limitado a estos 6 escenarios. Se realizaron 40 corridas de validación (F6) con resultados reproducibles (K-Fold CV < 2%), confirmando la solidez estadística.

---

**A03. ¿Por qué particionaron los datos cronológicamente y no de forma aleatoria?**

*Respuesta:* La partición aleatoria introduce data leakage temporal en series de tiempo: el modelo vería datos del "futuro" durante el entrenamiento, inflando artificialmente las métricas. La partición cronológica 70/15/15 garantiza que el modelo se evalúa sobre datos genuinamente posteriores al entrenamiento, que es la condición real de operación. Es metodológicamente más riguroso y más honesto con la realidad.

---

**A04. ¿Por qué no usaron un dataset público como KDD'99 o CICIDS2017?**

*Respuesta:* Los datasets públicos tienen problemas conocidos: KDD'99 tiene réplicas de flujos que inflan artificialmente el recall; CICIDS2017 tiene features inconsistentes con las que genera Suricata. Más importante: nuestro objetivo era validar un sistema end-to-end completo (Suricata → IF → ipset), no solo un clasificador. Los datos propios nos permitieron validar la arquitectura completa en condiciones reproducibles y auditables.

---

**A05. ¿Cómo validan que sus resultados son estadísticamente significativos?**

*Respuesta:* Tres formas. Primero, el conjunto de evaluación tiene 56,524 flujos, dando intervalos de confianza angostos: AUC=0.9440 IC95%=[0.9421, 0.9459] por método DeLong. Segundo, K-Fold cross-validation con k=5 muestra σ<0.001 en todas las métricas, confirmando reproducibilidad. Tercero, las 40 corridas de F6 son réplicas experimentales independientes, cada una con escenario, hora y condiciones distintas.

---

**A06. ¿Cuál es la hipótesis de investigación y cómo fue validada?**

*Respuesta:* La hipótesis es: "Un sistema basado en Isolation Forest entrenado con tráfico normal puede detectar comportamientos anómalos de red en tiempo real con suficiente precisión y latencia para aplicar control inline." Fue validada con evidencia cuantitativa: AUC=0.9440 (discriminación estadística demostrada), Recall=99.3% (detección efectiva), Latencia P95=34.8ms < 500ms requisito (tiempo real cumplido), ITL=0% (sin disrupciones legítimas).

---

**A07. ¿Por qué limitaron el estudio a una red de 4 nodos en lugar de una red universitaria real?**

*Respuesta:* El MVP en laboratorio controlado es el primer paso de un proceso de maduración de 4 fases. La red controlada permite validar el sistema sin riesgo para usuarios reales, con tráfico reproducible y métricas verificables. La Fase 1 del roadmap (F5-02, Sección 5) lleva el sistema a una red real en modo MONITOR durante 30 días antes de activar bloqueos. Esta es la metodología estándar para sistemas de seguridad críticos.

---

**A08. ¿Qué tan reproducibles son sus experimentos?**

*Respuesta:* Alta reproducibilidad. Todos los scripts de escenario están documentados en CLAUDE.md y la bitácora_escenarios.txt registra cada corrida con timestamp, herramienta, parámetros y archivo de salida. Los 40 eve.json.gz están archivados. El modelo tiene random_state=42. Cualquier investigador puede: clonar el repositorio, correr los scripts de escenario en el mismo entorno, y reproducir métricas dentro del rango IC95% documentado.

---

**A09. ¿Cuáles son las amenazas a la validez interna de su investigación?**

*Respuesta:* Identificamos tres. (1) Amenaza de instrumentación: Suricata puede perder flujos bajo flood extremo, subestimando el total de ataques. Mitigación: contrastamos con logs de hping3. (2) Amenaza de historia: corridas en distintos días pueden tener condiciones de VM diferentes. Mitigación: 40 réplicas y K-Fold. (3) Amenaza de maduración: el tráfico sintetizado de VM tiene varianza menor que tráfico real. Mitigación: documentado como limitación; Fase 1 ataca esta amenaza.

---

**A10. ¿Cuáles son las amenazas a la validez externa?**

*Respuesta:* La principal amenaza es la generalización a redes reales: el tráfico universitario real tiene patrones más complejos (VoIP, videoconferencia, actualizaciones masivas, tráfico cifrado) que nuestro laboratorio. Sin embargo, el diseño unsupervised mitiga esto parcialmente: IF se reentriena con el tráfico real de la nueva red antes de activar bloqueos. Declaramos explícitamente que los resultados son para el entorno validado, con el roadmap como extensión controlada.

---

# SECCIÓN B — DATA ENGINEERING (8 preguntas)

---

**B01. ¿Por qué derivaron 14 features y no más o menos?**

*Respuesta:* Las 14 features fueron seleccionadas por un criterio dual: disponibilidad en eve.json de Suricata (sin requerir captura de payload) y capacidad discriminativa verificada por feature importance de Random Forest de referencia. Las top 3 (dest_port=0.181, is_tcp=0.176, byte_rate=0.119) capturan el 47.6% de la importancia. Se probaron conjuntos de 8, 12 y 14 features; 14 fue el punto de rendimientos decrecientes donde agregar más features no mejoró AUC.

---

**B02. ¿Cómo manejan el desbalance de clases en el dataset?**

*Respuesta:* El dataset tiene desbalance natural (más tráfico normal que de ataque en el grupo A/B/C). Para el Isolation Forest esto es una ventaja, no un problema: el modelo no usa etiquetas durante el entrenamiento, por lo que no hay sesgo por desbalance. Para las métricas de evaluación reportamos AUC-ROC (no depende del threshold), F1, y MCC (Matthews Correlation Coefficient, diseñado para datasets desbalanceados), que son más robustos que Accuracy sola.

---

**B03. ¿Cómo garantizan la calidad del dataset?**

*Respuesta:* El pipeline de Data Engineering (F3) incluye: (1) Deduplicación por (src_ip, dst_ip, timestamp) para eliminar duplicados de eve.json. (2) Filtrado de IPs: se excluyen flujos con src_ip o dst_ip fuera del rango de laboratorio para evitar ruido de VMware. (3) Validación de features: flujos con NaN en features críticas son descartados. (4) Auditoría de partición: se verificó que no hay solapamiento temporal entre train/val/test.

---

**B04. ¿Por qué usar eve.json de Suricata como fuente y no pcap directamente?**

*Respuesta:* Eve.json ofrece flujos ya agregados: múltiples paquetes agrupados en un registro de flujo con estadísticas pre-calculadas (bytes, paquetes, duración). Parsear pcap directamente requeriría implementar la agregación de flujos desde cero (equivalente a re-implementar parte de Suricata). Eve.json también incluye metadata del protocolo detectado, que es una feature valiosa (is_tcp, is_udp, is_icmp). El costo es que la latencia mínima está acotada por cuándo Suricata cierra el flujo.

---

**B05. ¿Cómo manejan flujos que llegan fuera de orden al log?**

*Respuesta:* Eve.json usa append atómico por flujo cerrado. Los flujos se escriben en orden de cierre, no de inicio. Para el motor en tiempo real, cada flujo es procesado independientemente; no hay dependencia de orden. Para el dataset offline, la partición cronológica usa el timestamp de cierre del flujo, que siempre está en orden monótono creciente. No se observaron flujos fuera de orden en las 40 corridas de F6.

---

**B06. ¿Cuántos flujos se perdieron en la captura y por qué?**

*Respuesta:* Suricata en modo AF_PACKET con múltiples hilos tiene pérdida de paquetes prácticamente nula a las velocidades de nuestro laboratorio (<800 Mbps pico durante flood). Los contadores de `suricatasc capture-stats` muestran 0 paquetes perdidos en corridas normales y <0.01% en corridas de flood extremo. Los flujos "perdidos" son en realidad flujos cortados por el timeout de flujo de Suricata (configurable), no pérdida de captura.

---

**B07. ¿Cómo derivaron la feature `pkt_rate` desde eve.json?**

*Respuesta:* Eve.json proporciona `pkts_toserver`, `pkts_toclient`, y `duration` del flujo. La función derive_features() calcula: `pkt_rate = (pkts_toserver + pkts_toclient) / max(duration, 0.001)`. El `max(0.001)` previene división por cero en flujos de duración cero (paquetes únicos RST o SYN sin respuesta). El mismo patrón aplica para `byte_rate`, `pkt_ratio`, `byte_ratio`, y `avg_pkt_size`.

---

**B08. ¿Por qué `dest_port` es la feature más importante (importance=0.181)?**

*Respuesta:* El puerto destino discrimina el tipo de servicio atacado, que correlaciona con el tipo de ataque. Port 80 con alta tasa → HTTP flood. Port 22 con muchos flujos cortos → SSH brute force. Port * con muchos ports distintos en ventana corta → port scan. La distribución de dest_port es muy diferente entre tráfico normal (concentrado en :22, :80) y anómalo (uniforme en port scan, saturado en :80/:22 en flood). Esta discriminación explica la alta importancia.

---

# SECCIÓN C — MACHINE LEARNING (12 preguntas)

---

**C01. ¿Cómo funciona el Isolation Forest internamente?**

*Respuesta:* Isolation Forest construye n_estimators=300 árboles de decisión aleatorios. En cada árbol, selecciona aleatoriamente una feature y un split point, repitiendo recursivamente. Los puntos anómalos son aislados (particionados) en pocos pasos porque son "raros" — están en regiones de baja densidad del espacio de features. El score es: `−(promedio de profundidad de aislamiento normalizada)`. Valores cercanos a 0 son anómalos; cercanos a −0.5 son normales. Nuestros τ1=−0.4973 y τ2=−0.6873 son dos puntos operacionales sobre este score.

---

**C02. ¿Por qué n_estimators=300 y no el default de 100?**

*Respuesta:* Se realizó una búsqueda de hiperparámetros probando n=50, 100, 200, 300, 500. El AUC mejoró de 0.9289 (n=50) a 0.9440 (n=300) y se estabilizó en 0.9442 (n=500) — rendimientos decrecientes. La latencia de inferencia es O(n): n=300 da 12.4ms vs n=500 a 20.8ms. El punto óptimo AUC/latencia es n=300. Además, n=300 es una práctica común en la literatura de IF para datasets medianos.

---

**C03. ¿Qué significa contamination=0.05 en el Isolation Forest?**

*Respuesta:* El parámetro `contamination` es la fracción esperada de anomalías en el dataset de entrenamiento. Con contamination=0.05, scikit-learn ajusta el umbral interno del modelo para marcar el 5% de las observaciones de entrenamiento como anómalas. Sin embargo, en nuestro caso el entrenamiento usa SOLO 684 flujos normales (no hay ataques mezclados), por lo que contamination afecta principalmente la normalización del score. Los umbrales operacionales τ1 y τ2 fueron derivados independientemente de contamination, usando la curva ROC sobre el conjunto de validación.

---

**C04. ¿Por qué entrenaron solo con tráfico normal y no con ambas clases?**

*Respuesta:* Este es el diseño correcto para detección de novedad (novelty detection). Si entrenas con ataques, el modelo aprende los ataques específicos y falla ante variantes nuevas. Al entrenar solo con lo "normal", el modelo aprende la distribución del espacio normal y rechaza automáticamente cualquier punto que no pertenezca a esa distribución, independientemente de si es un ataque conocido o no. Esto es superiormente generalizable y fue validado empíricamente en F2-04.

---

**C05. ¿Cuál es la complejidad computacional del Isolation Forest?**

*Respuesta:* Entrenamiento: O(n × t × ψ) donde n=684 flujos, t=300 árboles, ψ=256 muestras por árbol. En la práctica: <1 segundo. Inferencia: O(t × log ψ) por flujo = O(300 × 8) ≈ O(2400) operaciones → ~12ms en CPU moderno. La complejidad es independiente del tamaño del dataset de entrenamiento en tiempo de inferencia, lo que es crítico para sistemas en tiempo real.

---

**C06. ¿Cómo determinaron τ1=−0.4973 y τ2=−0.6873?**

*Respuesta:* Se calcularon sobre el conjunto de validación (val.csv, 56,524 flujos) usando la curva ROC. τ1=−0.4973 fue determinado por el índice de Youden (TPR−FPR maximizado): en ese punto TPR=91%, FPR=9.5%, que es el punto de mayor separación global. τ2=−0.6873 fue determinado como el mayor threshold tal que FPR≤2%: TPR=40.6%, FPR=2%. Esta elección conservadora para BLOCK es deliberada: preferimos perder algunos ataques borderline (LIMIT los contiene) antes que bloquear tráfico legítimo.

---

**C07. ¿Por qué AUC=0.9440 y no 0.99+ como logran modelos supervisados?**

*Respuesta:* La diferencia es el precio de la independencia de etiquetas. Un modelo supervisado entrena con miles de ejemplos etiquetados de cada tipo de ataque y aprende sus características específicas; naturalmente alcanza AUC>0.99 en el mismo dataset. Nuestro IF entrena con 684 flujos normales y no ve ningún ataque. La "brecha" de ~0.05 es el costo de la generalización: nuestro modelo detecta ataques no vistos, el supervisado no. Para el objetivo del proyecto (detección temprana de anomalías desconocidas), AUC=0.9440 es el resultado esperado y aceptable.

---

**C08. ¿Cómo interpretan que el score medio de tráfico normal sea −0.6529 (zona LIMIT)?**

*Respuesta:* Este es un punto importante y no intuitivo. El score −0.6529 para tráfico normal no-whitelisted significa que ese tráfico es "menos normal" que el baseline de entrenamiento, pero no suficientemente anómalo para BLOCK. Recordar que el entrenamiento usó solo 684 flujos muy "puros" — tráfico simple y repetitivo de A1/A2/A3. Tráfico real con más variedad tiene naturalmente scores más bajos. Esto es correcto: el LIMIT actúa como "zona de sospecha" para tráfico fuera del baseline estricto. Como Desktop (.20) está en whitelist, no recibe LIMIT aunque su score sería bajo.

---

**C09. ¿Qué harían si el modelo comienza a tener muchos falsos positivos en producción?**

*Respuesta:* Protocolo de respuesta en 3 pasos: (1) Inmediato — cambiar τ2 a un valor más bajo (más conservador) vía umbrales_finales.txt, sin reentrenar el modelo; el motor recarga los umbrales automáticamente. (2) Corto plazo — identificar las IPs o rangos que están siendo falsamente bloqueadas y agregarlas a la whitelist. (3) Mediano plazo — recolectar los flujos FP como ejemplos adicionales del nuevo "normal" y reentrenar el modelo con la ventana deslizante expandida.

---

**C10. ¿Qué es el coeficiente de Youden y por qué lo usaron para τ1?**

*Respuesta:* El índice de Youden J = TPR − FPR (también llamado Informedness). Representa la probabilidad de que el clasificador prediga correctamente mejor que el azar. τ1 se elige donde J es máximo, lo que corresponde al threshold que mejor separa las distribuciones de scores para normales y anómalos. En nuestro caso: J_max = 0.91 − 0.095 = 0.815 en τ1=−0.4973. Es la métrica estándar para selección de umbral clínico y de seguridad cuando ambas clases tienen costo similar.

---

**C11. ¿Por qué usaron StandardScaler y no MinMaxScaler o RobustScaler?**

*Respuesta:* StandardScaler (z-score) fue elegido porque el Isolation Forest no depende críticamente del tipo de escalado (a diferencia de SVM o KNN). Sin embargo, el escalado es necesario para que features de distinta escala (pkt_rate en miles vs. is_tcp en {0,1}) no dominen la selección de splits aleatoria. StandardScaler es la opción más robusta y ampliamente usada en la literatura de anomaly detection. RobustScaler sería preferible con outliers extremos en el training set, pero como entrenamos solo con flujos normales los outliers son mínimos.

---

**C12. ¿Cómo saben que el modelo no está memorizando el training set?**

*Respuesta:* Tres evidencias. (1) K-Fold CV con k=5: si hubiera memorización, el modelo fallaría en folds no vistos. El CV del AUC es 0.11%, indicando generalización. (2) AUC en test set (datos del futuro, no vistos): 0.9440, prácticamente idéntico al de validación, confirma que no hay overfitting. (3) IF solo tiene 684 puntos de entrenamiento y 300×256=76,800 "celdas" en los árboles — el espacio del modelo es mucho mayor que los datos; no tiene capacidad de memorizar.

---

# SECCIÓN D — CIBERSEGURIDAD (8 preguntas)

---

**D01. ¿Cuál es la diferencia entre IDS e IPS y cómo clasifican su sistema?**

*Respuesta:* IDS (Intrusion Detection System) detecta y alerta. IPS (Intrusion Prevention System) detecta y bloquea. Suricata actúa como IDS: detecta y registra flujos en eve.json. Nuestro motor_decision.py + enforce.sh convierte el sistema en IPS inline: lee las detecciones de Suricata y aplica bloqueos via ipset en el mismo flujo de paquetes. La arquitectura completa es un NIPS (Network IPS) con detección basada en comportamiento (anomaly-based) en lugar de firmas.

---

**D02. ¿Qué tan efectivo es su sistema contra ataques zero-day?**

*Respuesta:* Efectivo para zero-days que presentan comportamiento volumétrico o estadísticamente anómalo. El IF no conoce los ataques — detecta por desviación del baseline. Un zero-day que genere flood, scan, o tráfico asimétrico será detectado con alta probabilidad. Sin embargo, un zero-day diseñado para imitar perfectamente tráfico normal (low-and-slow APT) podría no ser detectado por el IF. Para ese caso, los detectores heurísticos de sesión (SSH brute force por intentos acumulados, no por tasa) y el análisis de comportamiento de usuario (UEBA, roadmap) son más efectivos.

---

**D03. ¿Podría un atacante evadir su sistema conociendo el algoritmo?**

*Respuesta:* Parcialmente. Si el atacante conoce los umbrales τ1 y τ2, puede intentar generar tráfico con score > τ2 (en zona LIMIT). Esto implicaría imitar el patrón estadístico del tráfico normal en las 14 features, lo que es técnicamente difícil para ataques de alto impacto (no puedes hacer SYN flood manteniendo pkt_rate en rango normal). Adicionalmente: (1) la whitelist protege IPs conocidas, (2) las heurísticas detectan patrones temporales que el IF no ve, (3) el salt de randomState en IF puede ocultarse, (4) el reentrenamiento continuo mueve el decision boundary.

---

**D04. ¿Qué protocolo de respuesta a incidentes tienen definido?**

*Respuesta:* El sistema implementa respuesta automática de nivel 1: BLOCK inmediato via ipset con alerta Telegram al operador. El operador recibe: IP origen, tipo inferido de ataque, score, timestamp, puerto atacado. La respuesta manual de nivel 2 incluye: (1) verificar en motor_decision.log el patrón completo del IP bloqueada, (2) determinar si es ataque en curso o FP, (3) ejecutar enforce.sh UNBLOCK si es FP, o extender el bloqueo/escalar si es ataque. El runbook completo está en docs/ del repositorio.

---

**D05. ¿Cómo protegen el propio sensor de ataques?**

*Respuesta:* El sensor tiene 3 capas de protección: (1) SSH con autenticación solo por llave pública (no contraseña en producción, aunque en el lab se usa cisco123 para facilidad operacional). (2) El sensor (192.168.0.110) está en la whitelist de sí mismo — sus propios flujos nunca son bloqueados. (3) Las reglas ipset aplican al FORWARD chain, no al INPUT chain del sensor, protegiendo el tráfico que pasa a través del sensor sin afectar la comunicación de gestión. En producción se agregaría: fail2ban, UFW, y acceso solo desde VPN.

---

**D06. ¿Cuál es el MTTD (Mean Time To Detect) de su sistema?**

*Respuesta:* El MTTD tiene dos componentes. Primero, el tiempo de cierre del flujo por Suricata: varía de 0.5s (flujos cortos como SYN packets) a varios segundos (flujos TCP largos con timeout configurable). Segundo, el tiempo de procesamiento en el motor: P95=34.8ms. Por lo tanto, el MTTD real depende del tipo de ataque: para SYN flood (flujos muy cortos) MTTD < 1s; para ataques de larga duración como brute force SSH, el MTTD puede ser de 5–30s (tiempo hasta que Suricata cierra el flujo sospechoso).

---

**D07. ¿Qué pasa si el atacante usa IPs de la whitelist (spoofing)?**

*Respuesta:* IP spoofing en TCP es casi imposible en la práctica: el three-way handshake requiere recibir el SYN-ACK, lo que implica ser el dueño legítimo de la IP. Para UDP, el spoofing es posible pero solo en tráfico unidireccional (amplification attacks). La whitelist protege las IPs de los hosts del laboratorio que están físicamente en la red — un atacante externo no puede alcanzar estas IPs en el entorno de laboratorio. En producción, el anti-spoofing se refuerza con filtros de ingreso en el firewall perimetral (uRPF).

---

**D08. ¿Cómo complementaría su sistema con las reglas de firma de Suricata?**

*Respuesta:* Son capas complementarias y no excluyentes. Las reglas de firma de Suricata (ej: ET/Emerging Threats ruleset) detectan ataques conocidos con alta precisión usando patrones de payload. Nuestro IF detecta anomalías comportamentales que no tienen firma. La integración óptima es: Suricata firma detecta ataque conocido → alerta directa de alta confianza; Suricata registra flujo en eve.json → IF detecta comportamiento anómalo → detección de zero-day. Ya tenemos esta integración: el motor lee eve.json que incluye las alertas de Suricata, y podría ponderar mayor severidad a flujos que tienen alerta de firma Y score bajo en IF.

---

# SECCIÓN E — ARQUITECTURA (6 preguntas)

---

**E01. ¿Por qué colocaron el sensor entre el atacante y el servidor y no en el servidor mismo?**

*Respuesta:* El sensor en posición inline (entre el switch y el servidor) actúa sobre todos los flujos antes de que lleguen al servidor, protegiendo incluso protocolos que el servidor no puede analizar fácilmente (UDP flood, SYN flood que no llegan a establecer conexión). Un agente en el servidor solo vería tráfico que ya llegó. Adicionalmente, el sensor centralizado protege múltiples servidores simultáneamente sin necesitar instalar software en cada uno.

---

**E02. ¿Cuál es el punto único de falla (SPOF) de su arquitectura?**

*Respuesta:* El sensor (192.168.0.110) es el SPOF del MVP. Si el sensor falla, no hay detección ni bloqueo. Para el MVP de laboratorio esto es aceptable. En producción, la mitigación es: (1) HA con sensor primario + backup en modo activo-pasivo (VRRP), (2) keepalived para failover automático en <1s, (3) ipset rules persistidas en disco para restauración rápida, (4) alertas de heartbeat para detectar fallo del sensor antes de que afecte la operación. El roadmap F5-02 Fase 2 incluye redundancia como requisito.

---

**E03. ¿Cómo escala si necesitan monitorear 10 servidores en lugar de 1?**

*Respuesta:* El sensor actual protege todos los servidores en el mismo segmento de red con una sola instancia. Para expandir: el motor genera bloqueos en ipset que se sincronizan a los otros servidores via `ipset save | ssh servidor "ipset restore -!"` ejecutado cada 5 segundos. El modelo IF no cambia — evalúa cada flujo independientemente del servidor destino. Solo se necesita ajustar la whitelist para incluir las IPs de los nuevos servidores y verificar que el span port del switch captura todo el tráfico relevante.

---

**E04. ¿Qué pasa con el tráfico durante el tiempo que tarda el bloqueo (34.8ms)?**

*Respuesta:* Durante los 34.8ms P95, los paquetes del flujo anómalo pasan al servidor. Sin embargo, este tiempo es extremadamente corto: un SYN flood a 1Gbps genera ~83,000 paquetes en 34.8ms, pero el servidor (nginx) es capaz de manejar este volumen brevemente. El bloqueo ipset es retroactivo: bloquea los paquetes subsiguientes del mismo flujo y del mismo IP. Para ataques volumétricos, el impacto de los primeros 34.8ms es mínimo comparado con la protección que sigue. Además, TCP syn cookies en el servidor protegen contra el impacto del SYN flood inicial.

---

**E05. ¿Por qué usaron ipset y no iptables directamente para los bloqueos?**

*Respuesta:* iptables con reglas individuales por IP tiene complejidad O(n) por paquete: cada paquete recorre todas las reglas hasta encontrar un match. Con 1000 IPs bloqueadas, eso es 1000 comparaciones por paquete. ipset usa tablas hash con complejidad O(1): el lookup es independiente del número de IPs bloqueadas. Para un sistema que puede bloquear cientos de IPs durante un ataque, ipset es órdenes de magnitud más eficiente. La diferencia es prácticamente invisible para 10 IPs pero crítica para 10,000.

---

**E06. ¿Cómo garantizan que los bloqueos ipset persisten tras un reinicio del sistema?**

*Respuesta:* En el MVP de laboratorio, los bloqueos son temporales (timeout configurable por corrida). En producción, la persistencia se implementa con: (1) `ipset save > /etc/ipset.conf` ejecutado periódicamente por cron (cada 5 min) y al shutdown. (2) En el unit file de systemd `ppi-motor.service`: `ExecStartPre=/sbin/ipset restore -! /etc/ipset.conf` para restaurar bloqueos al inicio. (3) La whitelist se define en el script de inicio y se recrea en cada arranque, asegurando que nunca se bloqueen IPs críticas por error.

---

# SECCIÓN F — ESTADÍSTICA (4 preguntas)

---

**F01. ¿Cómo calcularon el AUC-ROC y por qué es la métrica principal?**

*Respuesta:* AUC-ROC (Area Under the Receiver Operating Characteristic Curve) se calcula como el área bajo la curva que grafica TPR vs FPR para todos los posibles umbrales del score IF. Usamos el estimador de Mann-Whitney U equivalente: AUC = P(score_anómalo < score_normal). Un AUC=0.9440 significa que en el 94.4% de los pares (flujo_normal, flujo_anómalo), el modelo asigna un score más bajo (más anómalo) al flujo realmente anómalo. Es la métrica principal porque es independiente del umbral elegido y mide la capacidad discriminativa del modelo.

---

**F02. ¿Qué es el MCC (Matthews Correlation Coefficient) y por qué reportarlo?**

*Respuesta:* MCC = (TP×TN − FP×FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN)). Es el único indicador binario que considera todos los cuatro componentes de la matriz de confusión. A diferencia de Accuracy (engañosa con datasets desbalanceados) y F1 (ignora TN), MCC varía de −1 (clasificación inversa) a 1 (clasificación perfecta), con 0 indicando no mejor que azar. Nuestro MCC=0.9961 confirma discriminación casi perfecta incluso considerando el desbalance de clases en el dataset de evaluación.

---

**F03. ¿Cómo calcularon los intervalos de confianza del AUC?**

*Respuesta:* Usamos el método DeLong (1988), que es no paramétrico y el estándar en la literatura médica y de seguridad para comparación de curvas ROC. DeLong estima la varianza del AUC usando la representación U-estadística y calcula IC sin asumir normalidad. Con n_positivos=16,484 y n_negativos=6,854 en el test set, el IC 95% es [0.9421, 0.9459]. La anchura del intervalo (<0.002) confirma que la estimación es precisa dado el tamaño del conjunto de evaluación.

---

**F04. ¿Por qué reportan P95 de latencia y no P99 o la media?**

*Respuesta:* La media de latencia es engañosa cuando la distribución es asimétrica (como en latencias de red, donde hay colas largas). P99 es relevante para SLAs estrictos pero puede ser dominado por eventos raros (GC pause, I/O spike). P95 es el estándar industrial para sistemas de tiempo real: garantiza que el 95% de las operaciones cumplen el SLA y filtra los outliers extremos. En nuestro caso, P50=18ms y P95=34.8ms — la cola existe pero es manejable. Para sustentación: P95=34.8ms < 500ms requisito con margen de 14×.

---

# SECCIÓN G — RESULTADOS (2 preguntas)

---

**G01. Sus resultados son "demasiado buenos" (Recall=99.3%, ITL=0%). ¿No sospecha de overfitting o data leakage?**

*Respuesta:* Es la pregunta más importante. Tres evidencias contra overfitting: (1) IF fue entrenado con 684 flujos normales, evaluado en 56,524 flujos — la cantidad de evaluación es 82× el entrenamiento, no hay memorización posible. (2) Los ataques en el test set son los mismos tipos que en la validación, pero son corridas distintas en días distintos con condiciones de red diferentes; el modelo no "vio" esas corridas. (3) K-Fold CV con σ<0.001 confirma que no hay varianza entre particiones que indica memorización. Los resultados altos son esperables porque los ataques sintéticos (hping3 flood) son estadísticamente muy diferentes del tráfico normal — no es un dataset de benchmark, es un laboratorio donde los ataques son deliberadamente extremos.

---

**G02. ¿Por qué el FPR real (0.10%) es tan menor que el FPR teórico de la curva ROC (2% para τ2)?**

*Respuesta:* El FPR de la curva ROC se calcula sobre el conjunto de validación completo con su distribución de scores. El FPR real en F6 es menor por dos razones: (1) La whitelist elimina las IPs del laboratorio que son las que generan el volumen principal de tráfico normal — esos flujos ni siquiera pasan por el modelo. (2) El tráfico real de las corridas de evaluación es relativamente homogéneo y dentro del espacio normal aprendido, produciendo scores más "normales" (más altos) que los ejemplos marginales del conjunto de validación que determinaron el FPR=2%. Esto es consistente y esperado, no es una anomalía.

---

*Documento generado: 2026-06-14*  
*50 preguntas clasificadas: Metodología (10) | Data Engineering (8) | Machine Learning (12) | Ciberseguridad (8) | Arquitectura (6) | Estadística (4) | Resultados (2)*
