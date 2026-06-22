# Informe de Resultados — Parte V: Discusión y Conclusiones
**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
Universidad Peruana Unión · Ingeniería de Sistemas · 2026

---

## 5. Discusión y Conclusiones

### 5.1 Discusión

#### 5.1.1 Cumplimiento de objetivos

Los tres objetivos específicos del trabajo fueron cumplidos en su totalidad. OE1 se materializó en un pipeline de captura que procesó 47 archivos de capturas comprimidas y produjo un dataset de 667,420 flujos con 14 características por flujo, sin intervención manual en ningún paso del procesamiento. OE2 se cumplió con un AUC-ROC de 0.8998, superando el umbral mínimo de 0.80 en 12.5 puntos porcentuales, con precision y recall superiores al 99% evaluados sobre datos reales de laboratorio. OE3 se validó con 40 corridas que mostraron disponibilidad del 100% e ITL del 0% en todos los casos, y con validaciones en tiempo real que confirmaron la cadena completa de detección, bloqueo y notificación operando de forma autónoma.

El resultado global del objetivo general —un sistema que detecta, decide y bloquea sin intervención humana en menos de 35 ms de latencia por flujo— quedó demostrado de forma reproducible en el entorno de laboratorio.

#### 5.1.2 Sobre el AUC-ROC de 0.8998

Un AUC cercano a 0.9 en un problema de detección de anomalías de red es un resultado sólido, pero requiere contexto para ser interpretado correctamente. El modelo fue entrenado exclusivamente sobre tráfico normal (Grupo A) y evaluado sobre una combinación de tráfico normal de holdout y seis tipos de ataque distintos. El hecho de que un único modelo, sin haber visto ningún ataque durante el entrenamiento, logre separar correctamente el 99.40% de los flujos anómalos evidencia que los ataques generados en el laboratorio producen firmas estadísticas suficientemente distintas del tráfico legítimo en el espacio de las 14 características seleccionadas.

El FPR de 20.47% en τ1 no es un defecto del modelo sino una consecuencia de la elección del criterio de τ1 (índice de Youden): se priorizó no perder ataques (recall alto) sobre evitar todos los falsos positivos. Esta decisión es deliberada y correcta para el contexto de seguridad, donde un falso negativo —un ataque no detectado— tiene consecuencias más graves que un falso positivo —un flujo legítimo temporalmente limitado en velocidad. La mitigación mediante whitelist hace que el ITL operativo sea 0% en las condiciones del laboratorio.

#### 5.1.3 Comparación con enfoques tradicionales

Un sistema IDS basado en firmas, ante los seis escenarios del Grupo B, solo detectaría aquellos cuyas herramientas producen patrones ya conocidos (por ejemplo, el escaneo de puertos con nmap tiene firmas en bases de datos como Snort). Variantes de los mismos ataques con herramientas distintas o con parámetros modificados podrían evadir esas firmas. El sistema desarrollado no tiene esta limitación porque su criterio de detección es estadístico —cualquier comportamiento suficientemente alejado del baseline normal activa la alerta— y no basado en patrones específicos.

La diferencia operativa más relevante, sin embargo, no es la detección sino la respuesta. Un IDS tradicional genera un log o una alerta; la acción de bloqueo queda pendiente de un administrador. El sistema desarrollado cierra ese ciclo de forma autónoma: desde que Suricata escribe el evento hasta que el paquete del atacante es descartado en el kernel del servidor, el tiempo máximo observado fue de 34.8 ms (P95). Ningún IDS pasivo puede ofrecer esa latencia de respuesta porque su arquitectura no incluye el mecanismo de enforcement.

#### 5.1.4 Viabilidad de despliegue en entorno real

La arquitectura desarrollada es directamente transferible a entornos de producción bajo ciertas condiciones. El sensor (Suricata + motor) puede operar sobre cualquier servidor Linux con acceso al tráfico de red en modo promiscuo o mediante port mirroring. El servidor objetivo requiere únicamente que ipset e iptables estén disponibles, lo cual es el caso por defecto en cualquier distribución Linux. La integración con Telegram es opcional y configurable externamente.

Los ajustes necesarios para un despliegue real incluyen ampliar la whitelist con los rangos de IPs de los hosts legítimos de la red, recolectar un período de tráfico normal antes de activar el bloqueo automático (para ajustar el baseline del modelo a ese entorno específico), y configurar los umbrales heurísticos de BF-SSH y HTTP Abuse según el perfil de uso de los servicios protegidos. El mecanismo de reentrenamiento automático de F5 provee la infraestructura para que el modelo se adapte progresivamente a las particularidades del nuevo entorno.

---

### 5.2 Conclusiones

**C1 — Isolation Forest es un detector viable para anomalías de red en tiempo real.**

El modelo entrenado exclusivamente sobre tráfico normal logró AUC-ROC de 0.8998, precision del 99.54% y recall del 99.40% sobre una evaluación que incluyó seis tipos distintos de ataque. La latencia de inferencia (P95 = 34.8 ms) es inferior en más de un orden de magnitud al límite establecido de 500 ms, confirmando que el algoritmo es computacionalmente adecuado para operar flujo a flujo en tiempo real. Este resultado responde directamente a OE2.

**C2 — El pipeline completo F1–F6 funciona de extremo a extremo sin intervención humana.**

Las 40 corridas de validación formal mostraron disponibilidad del 100% e ITL del 0% en todos los casos. El sistema captura tráfico (F1), procesa el dataset (F2), entrena el modelo (F3), opera el motor en producción (F4), actualiza los modelos automáticamente (F5) y fue validado bajo condiciones reproducibles (F6) sin requerir modificación de código entre fases. El lead time de detección en SYN Flood fue de 61.92 s, y en SSH Brute Force de 60 s hasta BLOCK, validados en corridas en tiempo real. Este resultado responde a OE1 y OE3.

**C3 — El bloqueo progresivo aporta una capa de control adaptativo que los firewalls estáticos no ofrecen.**

Un firewall estático bloquea o no bloquea —sin gradación ni memoria de comportamiento previo. El mecanismo implementado distingue entre un primer incidente (bloqueo temporal de 5 minutos, que puede corresponder a un escaneo exploratorio sin consecuencias) y la reincidencia confirmada (bloqueo de 30 minutos y luego permanente). Esta escalada proporcional fue validada en vivo el 2026-06-22 con tres corridas consecutivas, observando los tres niveles de bloqueo con los timestamps y scores exactos registrados en el log del motor.

**C4 — La integración dashboard + Telegram cubre la necesidad de visibilidad operativa sin SOC dedicado.**

El dashboard web con Server-Sent Events y las alertas por Telegram dan al administrador de red visibilidad sobre el estado del sistema desde cualquier lugar y dispositivo, sin requerir herramientas de monitoreo adicionales ni personal permanente frente a una consola. La alerta Telegram fue recibida en menos de 800 ms desde la decisión del motor, y el dashboard mostró el evento en menos de 150 ms adicionales. Para organizaciones sin capacidad de mantener un SOC, esta combinación ofrece un nivel de visibilidad operativa que de otro modo requeriría infraestructura y personal significativamente más costosos.

---

### 5.3 Trabajos futuros

El trabajo desarrollado establece una base técnica funcional sobre la que se identifican las siguientes extensiones naturales:

**Despliegue en infraestructura real.** El paso más inmediato y directo es la instalación del sistema en una red de producción real. El mecanismo de reentrenamiento automático de F5 está diseñado para que el modelo se adapte al nuevo entorno con pocas semanas de operación.

**Manejo de tráfico cifrado.** Una proporción creciente del tráfico de red está cifrado con TLS, lo que impide acceder al contenido de los paquetes pero no a sus metadatos de flujo. La extensión al tráfico cifrado requiere incorporar técnicas de *TLS fingerprinting* (análisis de los metadatos del handshake) o usar características basadas exclusivamente en patrones de flujo (tamaño de paquetes, intervalos de tiempo, dirección del tráfico), que son accesibles sin descifrar el contenido.

**Federación de múltiples sensores.** La arquitectura actual opera con un único sensor. En una red con múltiples subredes o puntos de acceso, un modelo federado permitiría compartir señales de detección entre sensores sin centralizar todo el tráfico en un único punto. Esto es relevante para organizaciones con sedes distribuidas o infraestructura en la nube.

**Extensión del predictor a nuevos escenarios.** El predictor XGBoost fue entrenado principalmente sobre los patrones de persistencia observados en el laboratorio. Con datos de producción reales, el modelo podría aprender correlaciones más ricas entre el perfil comportamental de una IP y la probabilidad de que su actividad anómala continúe, mejorando la anticipación ante ataques graduales.

**Integración con respuesta activa multi-capa.** El bloqueo actual opera a nivel de red (ipset DROP). Una extensión natural sería integrar con el servidor de aplicaciones (nginx, por ejemplo) para aplicar bloqueos a nivel HTTP, o con un servidor DNS para mitigar ataques de amplificación. Cada capa adicional de respuesta reduce el impacto de ataques que logran evadir o superar el control de red.
