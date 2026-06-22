# Informe de Resultados — Parte I: Introducción
**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
Universidad Peruana Unión · Ingeniería de Sistemas · 2026

---

## 1. Introducción

### 1.1 Planteamiento del problema

Las redes de datos son el sostén de la operación de cualquier organización: conectan servicios, usuarios, sistemas de información y comunicaciones. Esa centralidad las convierte también en el principal objetivo de ataques externos. Según el reporte *Cost of a Data Breach 2023* de IBM Security, el tiempo promedio que una organización tarda en identificar una brecha de seguridad en su red es de 207 días, y otros 73 días adicionales para contenerla —un total de 280 días de exposición en promedio (IBM Security, 2023). El mismo reporte estima que las brechas detectadas y contenidas en menos de 200 días cuestan, en promedio, un millón de dólares menos que aquellas que se prolongan más.

Este problema no es exclusivo de grandes corporaciones. El informe *ENISA Threat Landscape 2024* de la Agencia de Ciberseguridad de la Unión Europea señala que los ataques de denegación de servicio (DoS/DDoS), el escaneo de puertos y los intentos de acceso no autorizado por fuerza bruta siguen siendo los vectores de mayor frecuencia en infraestructuras de red de todos los tamaños (ENISA, 2024). La disponibilidad de herramientas de ataque accesibles —como hping3, nmap o Hydra— hace que incluso atacantes sin capacidades técnicas avanzadas puedan generar tráfico anómalo significativo.

Los sistemas de seguridad de red tradicionales, como firewalls basados en reglas y sistemas de detección de intrusiones (IDS) por firma, tienen una limitación estructural: solo detectan lo que ya conocen. Una regla de firewall bloquea un puerto específico; una firma de IDS identifica un patrón conocido. Ninguno de los dos puede detectar una variante nueva de ataque o un comportamiento anómalo que no haya sido previamente catalogado. Adicionalmente, ambos sistemas requieren intervención humana para interpretar las alertas y tomar acciones de bloqueo, lo que introduce latencia operativa que puede ser crítica cuando el ataque es volumétrico.

Frente a este contexto, la pregunta que orienta este trabajo es:

> **¿Cómo detectar y responder automáticamente a comportamientos anómalos en el tráfico de red en tiempo real, sin conocimiento previo del tipo de ataque y sin requerir intervención humana para la acción de bloqueo?**

---

### 1.2 Objetivos

**Objetivo general:**

Desarrollar un sistema de detección temprana y control inline de comportamientos anómalos en redes de datos, empleando Isolation Forest para la detección no supervisada y mecanismos automáticos de bloqueo de tráfico en tiempo real.

**Objetivos específicos:**

- **OE1:** Construir un pipeline de captura y procesamiento de tráfico de red que genere un dataset válido para el entrenamiento del modelo, a partir de escenarios controlados de tráfico normal y anómalo ejecutados en un entorno de laboratorio real.

- **OE2:** Entrenar y validar un modelo de detección de anomalías basado en Isolation Forest con métricas AUC-ROC ≥ 0.80, derivando umbrales de decisión con base estadística a partir de la curva ROC.

- **OE3:** Integrar el modelo en un motor de decisión que opere en tiempo real sobre el tráfico capturado, con control automático de acceso mediante ipset/iptables, y validar su comportamiento bajo nueve escenarios de ataque reproducibles en laboratorio.

---

### 1.3 Justificación

#### 1.3.1 Detección no supervisada como alternativa a las firmas

Los ataques de red modernos no siguen patrones fijos. El mismo objetivo —agotar los recursos de un servidor— puede conseguirse con SYN flood, UDP flood, ICMP flood o solicitudes HTTP en ráfaga. Un sistema basado en firmas necesita una regla separada para cada variante; un sistema basado en aprendizaje automático no supervisado aprende lo que es normal y marca cualquier desviación significativa, independientemente de si ya ha visto ese tipo de ataque antes.

Isolation Forest (Liu et al., 2008) es adecuado para este problema por tres razones concretas. Primero, no requiere ejemplos etiquetados de ataques —entrena solo con tráfico normal, que es el que una organización siempre tiene disponible. Segundo, su salida es un score continuo que permite definir múltiples niveles de respuesta (no solo "normal" o "ataque") sin reentrenar el modelo. Tercero, su complejidad de inferencia es O(log n) por flujo, lo que permite latencias de procesamiento inferiores a 35 ms incluso sobre hardware modesto.

#### 1.3.2 Control inline como respuesta sin latencia humana

Detectar un ataque y notificarlo no es suficiente si la respuesta depende de que un administrador reciba el correo, lo lea, decida actuar y ejecute el comando de bloqueo. En un SYN flood de 10,000 paquetes por segundo, cada segundo de demora representa decenas de miles de paquetes adicionales contra el servidor.

El control inline con ipset e iptables permite ejecutar el bloqueo directamente en el kernel del sistema operativo del servidor, sin pasar por software de usuario ni esperar acción humana. La decisión del modelo se traduce en un comando `ipset add` que tiene efecto inmediato en el nivel de red. Este enfoque es el mismo que utilizan sistemas de protección de red empresariales, pero implementado sobre infraestructura de software libre y sin costo de licencias.

#### 1.3.3 Relevancia para organizaciones sin SOC dedicado

La mayoría de las organizaciones en Perú —empresas medianas, instituciones educativas, entidades gubernamentales locales— no disponen de un Centro de Operaciones de Seguridad (SOC) con analistas disponibles las 24 horas. Para estas organizaciones, un sistema que detecta, decide y bloquea de forma autónoma, y que notifica al responsable de TI en su teléfono cuando ocurre algo relevante, tiene un valor práctico inmediato que va más allá del ámbito académico.

---

### 1.4 Alcance

El trabajo se desarrolló sobre un entorno de laboratorio local controlado compuesto por cuatro máquinas virtuales interconectadas en la red 192.168.0.0/24. El sistema protege un único servidor objetivo con dos servicios expuestos: un servidor web nginx en el puerto 80 y un servicio SSH en el puerto 22. El tráfico anómalo fue generado de forma deliberada y controlada desde un único host atacante (Kali Linux) ejecutando herramientas disponibles públicamente.

Se diseñaron y ejecutaron nueve escenarios de ataque diferenciados, cubriendo los vectores más comunes en redes empresariales: inundación de paquetes TCP, UDP e ICMP, escaneo de puertos, abuso de HTTP y fuerza bruta sobre SSH. Complementariamente, cuatro escenarios de tráfico normal fueron utilizados para establecer el baseline del modelo.

La validación formal comprendió 40 corridas ejecutadas en una única jornada de laboratorio (2026-06-16), más validaciones adicionales en tiempo real el 2026-06-22 para verificar comportamientos específicos (bloqueo progresivo, lead time, alertas Telegram) que requieren observación directa del sistema en operación.

---

### 1.5 Limitaciones del estudio

Los resultados de este trabajo deben interpretarse dentro de los límites del entorno en que fueron obtenidos:

**Entorno de laboratorio cerrado.** La topología de red es fija, con un número reducido de hosts y sin tráfico externo real. En una red de producción, el volumen y la diversidad del tráfico son significativamente mayores, lo que podría afectar la tasa de falsos positivos del modelo.

**Atacante único con herramientas conocidas.** El tráfico anómalo fue generado desde una única IP con herramientas cuyo comportamiento es predecible y reproducible. Ataques distribuidos (DDoS con múltiples IPs origen) o técnicas de evasión avanzadas no fueron evaluados.

**Modelo entrenado en el mismo laboratorio.** El Isolation Forest fue entrenado con tráfico generado en el mismo entorno en que opera. La generalización a redes con perfiles de tráfico distintos (aplicaciones web complejas, VoIP, videoconferencia) requeriría re-entrenamiento con datos representativos de ese entorno. El mecanismo de reentrenamiento automático implementado en F5 provee la infraestructura necesaria para ello.

**Servicio objetivo único.** El servidor protegido expone solo dos servicios (HTTP y SSH). La arquitectura del sistema es extensible a entornos más complejos, pero los umbrales heurísticos (HTTP Abuse, BF-SSH) están ajustados al perfil de tráfico observado en este laboratorio específico.

Estas limitaciones están identificadas, documentadas y, en los casos aplicables, mitigadas en el diseño del sistema. El detalle técnico de cada una se presenta en la sección 4.5 del informe.
