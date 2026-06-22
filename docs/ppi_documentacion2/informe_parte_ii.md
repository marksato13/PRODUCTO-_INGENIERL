# Informe de Resultados — Parte II: Marco Teórico
**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
Universidad Peruana Unión · Ingeniería de Sistemas · 2026

---

## 2. Marco Teórico

### 2.1 Detección de anomalías en redes de datos

#### 2.1.1 Concepto de anomalía de tráfico

Una anomalía de tráfico de red es un comportamiento estadísticamente inusual en el flujo de paquetes que atraviesa una red, considerado en relación con un baseline del comportamiento esperado. Esta definición es distinta de la de intrusión conocida: una intrusión conocida es un ataque cuyo patrón ha sido previamente catalogado (firma); una anomalía es cualquier desviación del baseline, independientemente de si existe una firma para ese comportamiento.

Chandola, Banerjee y Kumar (2009) clasifican las anomalías en tres categorías: puntuales (un único evento anómalo), contextuales (un evento normal en otro contexto pero anómalo en el actual) y colectivas (un conjunto de eventos que individualmente podrían ser normales pero cuyo patrón conjunto es anómalo). Los ataques volumétricos como SYN flood o UDP flood son anomalías puntuales con alta magnitud estadística —un flujo con tasa de paquetes de 10,000 pkt/s es inusual por sí mismo. Los ataques graduales como el brute force SSH son anomalías colectivas: cada intento de autenticación fallido es un evento relativamente común, pero 15 intentos en 60 segundos desde la misma IP constituyen un patrón colectivamente anómalo.

#### 2.1.2 Enfoques de detección

Los sistemas de detección de anomalías en redes adoptan tres enfoques principales:

**Basados en reglas:** definen umbrales fijos o patrones de comportamiento explícitos (por ejemplo, "más de 1,000 SYN sin SYN-ACK en 10 segundos"). Son simples de implementar y de interpretar, pero requieren conocimiento previo del tipo de ataque y son fácilmente evadibles ajustando los parámetros del ataque para quedar por debajo del umbral.

**Estadísticos:** modelan el tráfico normal con distribuciones de probabilidad y marcan como anómalos los eventos que caen fuera de los intervalos de confianza. Son más robustos ante variantes desconocidas, pero la dificultad de modelar distribuciones multivariadas de tráfico real limita su aplicabilidad en redes con patrones de uso complejos.

**Basados en aprendizaje automático:** aprenden el comportamiento normal (o la distinción normal/anómalo) a partir de datos históricos y generalizan a eventos nuevos. Se subdividen en supervisados (requieren ejemplos etiquetados de ataques), no supervisados (aprenden solo del tráfico normal) y semisupervisados (combinación de ambos). El enfoque no supervisado es el más práctico porque el tráfico normal está siempre disponible, mientras que construir un conjunto de ejemplos etiquetados de ataques requiere un esfuerzo significativo y nunca cubre todas las variantes posibles.

---

### 2.2 Isolation Forest

#### 2.2.1 Principio de funcionamiento

Isolation Forest (Liu, Ting y Zhou, 2008) es un algoritmo de detección de anomalías no supervisado cuyo principio central invierte el enfoque tradicional: en lugar de definir qué es normal y marcar lo que se desvía, aísla directamente las anomalías.

El algoritmo construye un conjunto de *árboles de aislamiento* (isolation trees). Cada árbol se construye seleccionando aleatoriamente una característica y un valor de corte dentro del rango de esa característica, dividiendo recursivamente el espacio de datos hasta que cada punto quede aislado en su propia partición. La observación clave de Liu et al. es que los puntos anómalos —que por definición son escasos y estadísticamente diferentes del resto— quedan aislados en pocas particiones (pocas divisiones del árbol), mientras que los puntos normales, que son más numerosos y similares entre sí, requieren muchas más divisiones para quedar aislados.

La longitud promedio del camino desde la raíz del árbol hasta el nodo que aísla cada punto es la señal de anomalía: un camino corto indica aislamiento fácil (punto anómalo), un camino largo indica aislamiento difícil (punto normal). Esta longitud se normaliza para producir un score de anomalía en el rango [-1, 0], donde valores cercanos a -1 indican alta anomalía y valores cercanos a 0 indican comportamiento normal.

#### 2.2.2 Ventajas para detección de tráfico de red

Isolation Forest tiene tres propiedades que lo hacen especialmente adecuado para la detección de anomalías en tráfico de red:

**Entrenamiento no supervisado sobre tráfico normal.** El algoritmo no requiere ejemplos de ataques para entrenarse. Basta con un período de captura de tráfico legítimo para establecer el baseline. Esto es operativamente viable porque cualquier organización puede capturar tráfico normal antes de activar la detección.

**Complejidad de inferencia O(log n).** Una vez entrenado, calcular el score de anomalía para un flujo nuevo requiere recorrer un árbol de profundidad logarítmica. Con 300 árboles y las características de hardware del sensor de laboratorio, la latencia P95 de inferencia fue de 34.8 ms por flujo, compatible con operación en tiempo real.

**Score continuo como señal de gradación.** A diferencia de clasificadores binarios, el score continuo de Isolation Forest permite definir múltiples umbrales de respuesta (PERMIT, LIMIT, BLOCK) con un único modelo entrenado, ajustando los umbrales estadísticamente desde la curva AUC-ROC.

#### 2.2.3 Hiperparámetros relevantes

El parámetro `n_estimators` define el número de árboles del ensemble. Liu et al. demuestran que el error del estimador converge con n_estimators ≥ 100; en este trabajo se usaron 300 árboles para mayor estabilidad estadística. El parámetro `contamination` es un prior sobre la fracción de anomalías esperada en los datos de entrenamiento y producción; no afecta el aprendizaje del modelo pero sí desplaza el score de decisión interno de scikit-learn. Con `contamination=0.05` se asume que aproximadamente el 5% del tráfico visto podría ser anómalo, un prior conservador y apropiado para entornos corporativos donde la mayor parte del tráfico es legítimo.

#### 2.2.4 Derivación de umbrales desde la curva AUC-ROC

El Área Bajo la Curva ROC (AUC-ROC) mide la capacidad discriminativa del modelo independientemente de cualquier umbral: representa la probabilidad de que el modelo asigne un score más bajo a un flujo anómalo que a uno normal, tomados al azar. Un AUC de 0.5 equivale a clasificación aleatoria; un AUC de 1.0 equivale a separación perfecta.

La derivación de τ1 y τ2 desde la curva ROC permite elegir los umbrales operativos con criterios explícitos y estadísticamente justificados. El índice de Youden J = TPR − FPR identifica el punto de la curva que maximiza la diferencia entre sensibilidad y tasa de falsos positivos, siendo apropiado cuando los costos de falsos negativos y falsos positivos son comparables. Para τ2, el criterio FPR ≤ 2% identifica el umbral donde el modelo tiene muy alta confianza en que el flujo es anómalo, aceptando a cambio un recall bajo en esa zona, lo cual es adecuado para la acción más severa (DROP en kernel).

---

### 2.3 Captura y análisis de flujos de red con Suricata

#### 2.3.1 Flujos de red como unidad de análisis

Un flujo de red (network flow) es el agregado de todos los paquetes intercambiados entre un par de endpoints (IP origen, IP destino, puerto origen, puerto destino, protocolo) en una misma sesión de comunicación. A diferencia del análisis paquete a paquete (Deep Packet Inspection), el análisis por flujos opera sobre metadatos estadísticos: número de paquetes, bytes, duración, tasas. Esta agregación tiene dos ventajas: reduce el volumen de datos a analizar en órdenes de magnitud, y preserva la privacidad del contenido de las comunicaciones (no requiere acceso al payload).

Los flujos son la unidad de análisis estándar en sistemas de monitoreo de red como NetFlow (Cisco), IPFIX (IETF RFC 7011) y el formato `eve.json` de Suricata. El analizador de tráfico Suricata (OISF, 2023) implementa un motor de inspección de estado de conexiones que genera un evento de flujo JSON estructurado cuando la sesión se cierra (señal FIN/RST en TCP, o tras un timeout configurable para protocolos sin cierre explícito como UDP e ICMP).

#### 2.3.2 Características de flujo para detección de anomalías

Las características extraídas de cada flujo pertenecen a cuatro categorías funcionales:

- **Volumen:** número de paquetes y bytes en cada dirección (`pkts_toserver`, `pkts_toclient`, `bytes_toserver`, `bytes_toclient`). Los floods volumétricos producen valores extremadamente altos en estas características.

- **Temporales:** duración del flujo y tasas derivadas (`duration`, `pkt_rate`, `byte_rate`). Los SYN floods generan flujos de duración muy corta (timeout del servidor) con tasas de paquetes altas; las sesiones HTTP normales tienen duraciones variables pero tasas moderadas.

- **Proporcionales:** ratios entre las características direccionales (`pkt_ratio`, `byte_ratio`, `avg_pkt_size`). El tráfico anómalo unidireccional (el atacante envía pero no recibe respuesta, o viceversa) produce ratios extremos. En un SYN flood, `byte_ratio` tiende a valores muy bajos porque el servidor envía pocos bytes de respuesta antes de agotar sus recursos.

- **Categóricas:** protocolo e identificador de servicio (`is_tcp`, `is_udp`, `is_icmp`, `dest_port`). Permiten al modelo separar comportamientos normales que son propios de cada protocolo.

---

### 2.4 Control inline de tráfico con ipset e iptables

#### 2.4.1 Netfilter e iptables

iptables es la interfaz de espacio de usuario al subsistema Netfilter del kernel Linux, que implementa la inspección y filtrado de paquetes en el nivel del sistema operativo (Russel y Welte, 2002). Los paquetes de red que llegan a la interfaz de red del servidor son evaluados contra una serie de reglas organizadas en cadenas (INPUT, FORWARD, OUTPUT) antes de ser entregados a las aplicaciones. Una regla con objetivo DROP descarta el paquete sin notificación al emisor; con ACCEPT lo deja pasar; con la extensión `limit` o `hashlimit` aplica rate limiting antes de aceptarlo.

El procesamiento en Netfilter ocurre en el kernel, sin involucrar código de espacio de usuario para cada paquete. Esto lo hace significativamente más rápido que soluciones de filtrado en aplicación (como un proxy inverso con lógica de rate limiting) y lo hace apropiado para mitigar ataques volumétricos que buscan saturar el servidor.

#### 2.4.2 ipset como estructura de datos para listas de IPs

ipset (Jozsef, 2010) es una extensión de iptables que permite referenciar conjuntos de IPs (o rangos, o pares IP:puerto) directamente desde las reglas de iptables. La ventaja operativa sobre las reglas individuales de iptables es la complejidad de búsqueda: mientras que iptables evalúa las reglas de forma lineal (O(n) con n reglas), ipset usa tablas hash con búsqueda en tiempo constante O(1), independientemente del número de IPs en el conjunto.

En este trabajo se utilizan dos conjuntos:

- `ppi_blocked`: IPs cuyo tráfico es descartado completamente (`iptables -j DROP`). Las entradas tienen un campo `timeout` que especifica cuántos segundos permanece la IP en el conjunto; con `timeout 0` la entrada es permanente hasta eliminación manual.

- `ppi_limited`: IPs cuyo tráfico es aceptado pero limitado en velocidad (`iptables -m hashlimit --hashlimit-above 100/sec -j DROP`). La extensión `hashlimit` mantiene contadores por IP y descarta paquetes que superen la tasa configurada.

#### 2.4.3 Bloqueo progresivo como estrategia de respuesta adaptativa

La respuesta de seguridad proporcional a la reincidencia es un principio presente en múltiples sistemas de protección: los sistemas de autenticación aplican backoff exponencial tras intentos fallidos, los filtros de spam incrementan la penalización de remitentes reincidentes, los sistemas de rate limiting en APIs bloquean temporalmente clientes que exceden cuotas repetidamente.

Aplicado al control de tráfico de red, el bloqueo progresivo permite distinguir entre un primer incidente —que puede corresponder a un escaneo exploratorio sin consecuencias o incluso a un comportamiento legítimo inusual— y la reincidencia confirmada, que es evidencia de una campaña de ataque sostenida. La implementación mediante el campo `timeout` de ipset es directa: el primer bloqueo agrega la IP con `timeout 300`, el segundo con `timeout 1800`, y el tercero con `timeout 0` (permanente), sin requerir lógica adicional en el kernel.

---

### 2.5 XGBoost para predicción de persistencia de ataques

#### 2.5.1 Gradient Boosting y XGBoost

XGBoost (eXtreme Gradient Boosting) es una implementación optimizada del algoritmo de gradient boosting para árboles de decisión, desarrollada por Chen y Guestrin (2016). El gradient boosting construye un ensemble de árboles de forma secuencial, donde cada árbol nuevo corrige los errores residuales del ensemble previo. XGBoost incorpora regularización L1 y L2 sobre los parámetros de los árboles, manejo eficiente de valores faltantes y paralelización de la construcción de árboles, lo que lo hace competitivo con redes neuronales en problemas de clasificación sobre datos tabulares.

En el contexto de este trabajo, XGBoost se usa para un problema de clasificación binaria: dado el estado comportamental actual de una IP (cuántos eventos LIMIT y BLOCK ha generado en las últimas ventanas temporales, qué protocolo usa, a qué puerto se dirige, en qué hora del día), predecir si esa IP generará otro evento BLOCK en los próximos 60 segundos.

#### 2.5.2 Diferencia funcional con Isolation Forest

El Isolation Forest y el predictor XGBoost resuelven problemas distintos y se complementan:

- **Isolation Forest** clasifica cada flujo de forma independiente y sin memoria temporal. Responde a la pregunta: *¿es este flujo estadísticamente anómalo respecto al baseline normal?* No sabe nada de lo que ocurrió antes ni de lo que podría ocurrir después.

- **XGBoost predictor** analiza el historial comportamental reciente de cada IP y responde a la pregunta: *dado el patrón de eventos que ha generado esta IP hasta ahora, ¿continuará generando ataques en los próximos 60 segundos?* Tiene memoria temporal implícita a través de las features `limit_count_15s` y `block_count_60s`.

Esta complementariedad es operativamente valiosa: el IF actúa de forma reactiva sobre cada flujo (detecta y bloquea), mientras que el XGBoost actúa de forma anticipatoria sobre la tendencia de la IP (advierte al operador antes de que el ataque escale o confirma que el ataque persistirá).

#### 2.5.3 Codificación cíclica de variables temporales

Las horas del día tienen una propiedad que los valores enteros no capturan adecuadamente: la hora 23 y la hora 0 son temporalmente adyacentes pero numéricamente distantes. Representarlos como enteros introduciría una discontinuidad artificial que el modelo interpretaría como una diferencia grande entre comportamientos que ocurren en horarios consecutivos.

La codificación cíclica mediante seno y coseno resuelve este problema: `hora_sin = sin(hora × 2π/24)` y `hora_cos = cos(hora × 2π/24)` mapean las 24 horas del día a un círculo unitario, donde las horas adyacentes tienen representaciones vectoriales cercanas, incluyendo la transición de 23 a 0. Esta técnica es estándar en el tratamiento de features temporales cíclicas en aprendizaje automático (Goodfellow, Bengio y Courville, 2016).

---

### 2.6 Server-Sent Events para visualización en tiempo real

Server-Sent Events (SSE) es un protocolo estándar del W3C (HTML Living Standard) que permite a un servidor enviar eventos al navegador de forma unidireccional a través de una conexión HTTP persistente, sin que el cliente tenga que realizar solicitudes periódicas (*polling*). A diferencia de WebSockets, SSE es unidireccional (solo del servidor al cliente), más simple de implementar y de mantener, y compatible nativamente con todos los navegadores modernos sin librerías adicionales.

En el contexto del dashboard, el servidor Flask mantiene una conexión SSE abierta por cada navegador conectado. Cuando el lector de log detecta una nueva línea en `motor_decision.log`, construye el evento JSON correspondiente y lo envía a todos los clientes conectados en menos de 150 ms. Esto elimina el retraso y el tráfico adicional que generaría un polling periódico cada N segundos, y garantiza que cada alerta aparezca en el dashboard prácticamente en el momento en que el motor toma la decisión.

---

### Referencias

Chen, T. y Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.

Chandola, V., Banerjee, A. y Kumar, V. (2009). Anomaly detection: A survey. *ACM Computing Surveys*, 41(3), 1–58.

ENISA (2024). *ENISA Threat Landscape 2024*. European Union Agency for Cybersecurity.

Goodfellow, I., Bengio, Y. y Courville, A. (2016). *Deep Learning*. MIT Press.

IBM Security (2023). *Cost of a Data Breach Report 2023*. IBM Corporation.

Jozsef, K. (2010). *ipset: A tool for managing sets in Linux kernel*. NetFilter Workshop.

Liu, F. T., Ting, K. M. y Zhou, Z. H. (2008). Isolation Forest. *Proceedings of the 8th IEEE International Conference on Data Mining (ICDM)*, 413–422.

OISF (2023). *Suricata User Guide 7.0*. Open Information Security Foundation. https://docs.suricata.io

Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

Russel, R. y Welte, H. (2002). *Linux Netfilter Hacking HOWTO*. The Netfilter Core Team.

W3C (2015). *Server-Sent Events — HTML Living Standard*. WHATWG.
