# F1-01 — Alcance, Beneficiarios y Tipo de Simulación

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez

---

## 1. Alcance de la Investigación

### 1.1 Alcance Técnico

El presente proyecto desarrolla e implementa un sistema de detección temprana de comportamientos anómalos en redes de datos, operando sobre infraestructura virtualizada con tecnologías de código abierto. El alcance técnico comprende los siguientes componentes integrados:

**Capa de captura y sensado:**
- Despliegue de Suricata 7.0.3 como motor IDS en modo pasivo sobre la interfaz de red `ens35`, en la máquina virtual designada como sensor (`192.168.0.110`), en la red de laboratorio `192.168.0.0/24`
- Generación de eventos en formato EVE JSON mediante el archivo `/var/log/suricata/eve.json`, procesando eventos de tipo `flow`, `alert`, `ssh` y `stats`
- Captura promiscua de todo el tráfico entre las VMs del laboratorio sin intervención sobre el flujo de paquetes

**Capa de modelado:**
- Implementación de Isolation Forest (Liu, Ting y Zhou, 2008) como algoritmo de detección de anomalías no supervisado, entrenado exclusivamente con tráfico normal representativo del laboratorio
- Ingeniería de 14 features derivadas de los campos de flujo de Suricata: volumétricas, temporales, derivadas de tasa y asimetría, y binarias de protocolo
- Normalización mediante StandardScaler ajustado sobre 684 flows normales, preservando el perfil de tráfico legítimo como referencia
- Definición de umbrales de decisión τ1 y τ2 mediante curva ROC (AUC=0.9440), implementando lógica de triple acción: PERMIT / LIMIT / BLOCK

**Capa de decisión:**
- Motor de decisión en tiempo real (`motor_decision.py`) que procesa el stream de `eve.json` con latencia P95=34.8ms
- Detectores temporales complementarios para Brute Force SSH (ventana 60s) y HTTP Abuse (ventana 30s), elevando el recall global de 87.6% a ~92-95%
- Sistema de explainabilidad basado en z-scores de features (v2), que justifica cada decisión BLOCK/LIMIT con las top-3 features más desviadas del perfil normal

**Capa de respuesta:**
- Control inline mediante `ipset` e `iptables` en el servidor objetivo (`192.168.0.120`): bloqueo total (DROP) para BLOCK y limitación de tasa a 100 pkt/s (hashlimit) para LIMIT
- Timeout automático de 300 segundos para garantizar disponibilidad del servicio ante posibles falsos positivos
- Notificaciones en tiempo real vía Telegram Bot API para alertas de anomalías, brute force y HTTP abuse
- Dashboard terminal actualizado cada 3 segundos con estadísticas del sistema

**Límites técnicos explícitos:**
- El sistema opera sobre la red de laboratorio virtualizada `192.168.0.0/24` en VMware
- El sensor captura tráfico L3/L4 (flujos TCP, UDP, ICMP); no realiza inspección profunda de paquetes (DPI) a nivel de contenido de aplicación
- El control inline actúa sobre el servidor objetivo `192.168.0.120`; no gestiona el firewall perimetral de la red completa

---

### 1.2 Alcance Metodológico

El proyecto sigue una metodología de investigación aplicada experimental con las siguientes etapas formales:

**F1 — Diseño y despliegue del entorno:** Configuración de infraestructura virtualizada, instalación de Suricata 7.0.3, validación de captura de tráfico y configuración de servicios objetivo (nginx :80, SSH :22). Evidencia: `suricata_revision.txt` (10 mayo 2026).

**F2 — Captura de tráfico por escenarios controlados:** Ejecución de 13 escenarios (4 normales A1-A4, 6 anómalos B1-B6, 3 mixtos C1-C3) con 49 corridas registradas en bitácora trazable. Dataset resultante: 376,827 flows limpios con etiquetado doble (nombre de archivo + `src_ip`).

**F3 — Modelado offline:** Entrenamiento de Isolation Forest con 684 flows normales seleccionados experimentalmente para maximizar la separación de scores (0.229 unidades entre tráfico normal y anómalo). Evaluación con AUC-ROC, Recall, Precision y F1 sobre conjunto de test independiente (56,525 flows).

**F4 — Motor de decisión:** Integración del modelo en pipeline de tiempo real. Implementación de detectores temporales heurísticos como complemento. Medición de latencia (P95=34.8ms). Validación end-to-end.

**F5 — Control inline:** Configuración de mecanismos de respuesta automática mediante ipset/iptables. Validación de acciones BLOCK, LIMIT y UNBLOCK. Documentación formal de umbrales.

**F6 — Validación y experimentación:** 40 corridas de validación en 4 grupos (normal, mixto, re-evaluación, final). Medición de Disponibilidad (100%), ITL (0%), TIE (100%), Lead Time (26s) y MTTC (28s).

La metodología es **deductiva-experimental**: parte de la hipótesis de que Isolation Forest puede aprender el perfil normal del tráfico de red y detectar desviaciones significativas, y la valida empíricamente mediante experimentos controlados con métricas cuantitativas predefinidas.

---

### 1.3 Alcance Experimental

El experimento se delimita a los siguientes parámetros controlados:

| Parámetro | Valor definido |
|---|---|
| Red de laboratorio | 192.168.0.0/24 (VMware) |
| Hipervisor | VMware Workstation |
| VMs activas en experimentos | 4 (Desktop, Kali, Sensor, Servidor) |
| Protocolo de captura | TCP, UDP, ICMP a nivel de flow |
| Escenarios normales | 4 tipos × 3 corridas c/u (A1-A4) |
| Escenarios anómalos | 6 tipos × al menos 1 corrida (B1-B6) |
| Escenarios mixtos | 3 tipos × 1 corrida (C1-C3) |
| Corridas de validación F6 | 40 (4 grupos × 10 corridas) |
| Duración por corrida F6 | 5 minutos |
| Vectores de ataque cubiertos | DDoS volumétrico (SYN, UDP, ICMP), reconocimiento (Port Scan), abuso de capa de aplicación (HTTP Abuse), acceso no autorizado (Brute Force SSH) |

El experimento **no incluye**: ataques de día cero, ataques cifrados a nivel de carga útil, inyección SQL, XSS, ataques a la cadena de suministro, ni vectores sobre protocolos distintos a TCP/UDP/ICMP a nivel de flujo.

---

### 1.4 Alcance de Ciberseguridad

El sistema implementa un **IDS/IPS híbrido orientado a comportamiento** (Behavior-Based IDS), complementario a los IDS basados en firmas (como las reglas Suricata por defecto). Su cobertura de ciberseguridad incluye:

**Vectores cubiertos con justificación en literatura:**

| Vector | Escenario | Fuente académica/industria |
|---|---|---|
| SYN Flood (DDoS L3/L4) | B1 | Cloudflare Q2-2025 DDoS Report: vector más prevalente en L3/L4 |
| Port Scan (reconocimiento) | B2 | MITRE ATT&CK T1046; Fortinet 2026 Global Threat Landscape |
| UDP Flood | B3 | Cloudflare Q2-2025: amplification via UDP es segundo vector volumétrico |
| ICMP Flood | B4 | Complementario a B1/B3; prueba robustez del sensor ante tráfico anómalo ICMP |
| HTTP Abuse (capa aplicación) | B5 | Cloudflare Q2-2025: App Layer DDoS en crecimiento sostenido |
| Brute Force SSH | B6 | DBIR 2024: credential attacks en top-3; Fortinet 2026: SSH bajo presión |

**Postura de ciberseguridad del sistema:**
- **Detección proactiva:** identifica comportamiento anómalo antes de que el ataque consolide su impacto (Lead Time: 26s desde inicio)
- **Respuesta automática:** aplica mitigación sin intervención humana (MTTC: 28s)
- **Cero impacto en legítimo:** ITL=0% preserva la disponibilidad del servicio durante el ataque
- **Trazabilidad:** cada decisión queda registrada en log estructurado con score, razón por z-scores y acción aplicada

**Fuera del alcance de ciberseguridad:** cifrado de comunicaciones, autenticación multifactor, seguridad en endpoints, gestión de vulnerabilidades de aplicación, análisis forense post-incidente.

---

### 1.5 Alcance del Modelo Predictivo

El modelo Isolation Forest implementado tiene las siguientes características y límites formales:

**Capacidades del modelo:**
- Aprende el perfil estadístico del tráfico normal a partir de 684 flows representativos (HTTP, SSH, transferencia de archivos, tráfico sostenido mixto)
- Asigna un anomaly score continuo a cada nuevo flow; más negativo = más anómalo
- Opera en tiempo real sobre el stream de Suricata con latencia P95=34.8ms (muy por debajo del límite de 500ms establecido)
- Generaliza correctamente a flows no vistos durante el entrenamiento (AUC=0.9440 sobre 56,525 flows de test)

**Límites del modelo:**
- El modelo aprende el perfil normal del laboratorio específico (2 IPs, 4 escenarios de tráfico, red /24). En una red diferente requeriría reentrenamiento con el tráfico normal de esa red
- No detecta ataques que imiten perfectamente el perfil estadístico del tráfico normal (mismo volumen, mismo protocolo, mismos puertos). Para estos casos se complementa con detectores temporales (B5, B6)
- No realiza inspección de contenido (payloads); opera exclusivamente sobre metadata de flujo

**Justificación de la elección de Isolation Forest sobre alternativas:**

| Alternativa | Por qué no se eligió |
|---|---|
| SVM One-Class | Sensible a la escala y requiere selección manual de kernel; menos eficiente en espacios de alta dimensión (14 features) |
| Autoencoder (Deep Learning) | Requiere más datos de entrenamiento y tiempo de inferencia mayor; dificulta explicabilidad |
| K-Nearest Neighbors (LOF) | Complejidad O(n²) en inferencia; inviable para procesamiento en tiempo real de streams continuos |
| Reglas estáticas (threshold) | No adapta a variaciones del perfil normal; no detecta combinaciones multi-feature de anomalía |
| **Isolation Forest** | Diseñado para aprender de pocos datos normales; O(n log n) en inferencia; robusto a outliers en entrenamiento; validado en detección de anomalías de red en literatura académica |

---

### 1.6 Justificación de los 6 Vectores de Ataque Seleccionados

#### ¿Por qué se trabajó con 6 tipos de ataque?

La selección de los 6 vectores de ataque (B1-B6) no fue arbitraria. Responde a un criterio de **representatividad taxonómica** de las amenazas documentadas en el panorama de amenazas 2024-2026:

**Clasificación por capa del modelo OSI:**
- **Capa 3 (Red):** SYN Flood (B1), ICMP Flood (B4)
- **Capa 4 (Transporte):** UDP Flood (B3), Port Scan (B2)
- **Capa 7 (Aplicación):** HTTP Abuse (B5), Brute Force SSH (B6)

Con 6 vectores se cubren **3 capas OSI distintas** y **4 categorías de amenaza** (DDoS volumétrico, reconocimiento, abuso de capa de aplicación, acceso no autorizado), que representan los vectores de mayor prevalencia según:
- **ENISA Threat Landscape 2025:** DDoS como amenaza #1 con variantes L3/L4/L7
- **Cloudflare Q2-2025 DDoS Report:** SYN flood y UDP flood como vectores L3/L4 más usados
- **DBIR 2024 (Verizon):** Credential attacks (brute force) en top-3 de incidentes
- **MITRE ATT&CK T1046:** Port scanning como técnica de reconocimiento más documentada
- **Fortinet 2026 Global Threat Landscape:** SSH bajo presión de brute force y active scanning con Nmap

#### Respuesta para el jurado: "¿Por qué no entrenaron 20 ataques?"

**Respuesta técnica:**

> *"El objetivo del modelo no es memorizar firmas de ataques específicos, sino aprender el perfil estadístico del tráfico normal y detectar cualquier desviación significativa. Isolation Forest es un algoritmo de detección de anomalías no supervisado: no requiere ejemplos de ataques para entrenarse. En consecuencia, agregar más tipos de ataque al dataset no mejora el modelo de detección — solo enriquece el conjunto de evaluación.*
>
> *Los 6 vectores seleccionados cumplen dos funciones: (1) representar las categorías de amenaza más prevalentes en el panorama 2024-2026 según ENISA, Cloudflare, DBIR y MITRE ATT&CK, y (2) ejercitar el sistema en las 3 capas OSI donde opera el tráfico de red (L3, L4, L7). La calidad de la cobertura es más importante que la cantidad.*
>
> *Un sistema entrenado con 6 vectores bien representativos y evaluado con AUC=0.9440 demuestra mayor solidez metodológica que un sistema evaluado con 20 vectores sin justificación de selección."*

**Respuesta metodológica:**

> *"El alcance de la investigación está delimitado a un entorno de laboratorio universitario con recursos de tiempo y hardware finitos. La norma ISO/IEC 27035 establece que un sistema de detección de intrusiones debe validarse contra una muestra representativa de vectores de amenaza conocidos, no necesariamente exhaustiva. Nuestros 6 vectores satisfacen ese criterio al cubrir las categorías de mayor impacto documentadas en el panorama de amenazas vigente."*

#### Respuesta para el jurado: "¿Cómo reaccionará el sistema ante ataques no contemplados?"

> *"Al ser un detector basado en comportamiento (no en firmas), el sistema puede detectar ataques no vistos durante el entrenamiento, siempre que generen un perfil estadístico de flujo que se aleje del tráfico normal aprendido. Por ejemplo, un ataque SCTP flood nunca visto generaría flows con alto pkt_rate y baja duración — exactamente los patrones que el modelo identifica como anómalos con independencia del protocolo específico.*
>
> *Esto se denomina detección de anomalías zero-day y es la principal ventaja de los detectores basados en comportamiento frente a los basados en firmas (como Snort/Suricata con reglas). La evaluación del sistema ante ataques desconocidos es un ítem explícito de trabajo futuro (Fase 7 propuesta), donde se contemplan ataques como slowloris, DNS amplification y ataques de protocolo específico."*

---

## 2. Beneficiarios de la Investigación

### 2.1 Beneficiarios Directos

#### Administradores de Red

**Perfil:** Profesionales responsables de la operación y seguridad de la infraestructura de red en organizaciones de cualquier tamaño.

**Beneficio concreto:**
- Reducción del tiempo de detección de incidentes: el sistema identifica ataques en progreso en 26 segundos desde el inicio, frente a los 197 días de tiempo medio de detección reportados en el DBIR 2024
- Respuesta automática que no requiere intervención manual inmediata: el motor aplica BLOCK en 28 segundos (MTTC)
- Dashboard en tiempo real que consolida el estado del sistema sin necesidad de revisar logs manualmente
- Notificaciones Telegram instantáneas ante cada anomalía detectada

**Capacitación requerida:** Comprensión básica de Suricata y iptables. El sistema opera como servicio systemd (`ppi-motor.service`) sin intervención continua.

#### Equipos SOC (Security Operations Center)

**Perfil:** Analistas de seguridad que monitorizan eventos de seguridad en tiempo real.

**Beneficio concreto:**
- Reducción de falsos positivos: Precision=99.96% significa que prácticamente cada alerta generada corresponde a una anomalía real, reduciendo el alert fatigue
- Trazabilidad completa: cada decisión BLOCK/LIMIT incluye el score del modelo, las top-3 features responsables de la anomalía (explainabilidad por z-scores) y el timestamp exacto
- Log estructurado (`motor_decision.log`) integrable con SIEM (Splunk, Elastic Stack, Wazuh) mediante parseo de formato estándar
- El sistema actúa como primera línea de respuesta automática; el SOC recibe la alerta cuando la anomalía ya está contenida

#### Centros de Datos

**Perfil:** Operadores de infraestructura de cómputo que alojan múltiples servicios críticos.

**Beneficio concreto:**
- Protección simultánea de múltiples servicios: el motor monitoriza todos los flows de la red hacia cualquier servidor objetivo
- Disponibilidad garantizada: en 40 corridas de validación con ataques reales, el servidor objetivo mantuvo 100% de disponibilidad durante los ataques activos
- Timeout automático de 300 segundos en bloqueos: evita que un falso positivo bloquee permanentemente tráfico legítimo
- Escalabilidad horizontal: el sensor puede reemplazarse por un TAP físico en redes de mayor ancho de banda

### 2.2 Beneficiarios Indirectos

#### Servidores Críticos en Organizaciones

Cualquier servidor expuesto a red (web, base de datos, correo, DNS) se beneficia del control inline que aplica el sistema. La implementación mediante `ipset`/`iptables` es agnóstica al tipo de servicio protegido: el DROP aplica a nivel de kernel antes de que el paquete llegue al servicio.

#### Infraestructuras Empresariales con Presupuesto Limitado

El sistema utiliza exclusivamente software de código abierto: Suricata, Python, scikit-learn, iptables, ipset. El costo de licencias es cero. Para una PYME o institución educativa, representa una alternativa viable frente a soluciones comerciales (Darktrace, Vectra, ExtraHop) con costos de licencia superiores a $50,000/año.

#### Entornos Académicos y de Investigación

- Universidades con laboratorios de redes: el sistema puede desplegarse sobre infraestructura virtualizada existente (VMware, VirtualBox, Proxmox) sin hardware adicional
- Investigadores en detección de anomalías: el dataset generado (376,827 flows etiquetados, `dataset_clean.csv`) y los modelos serializados (`isolation_forest.pkl`, `scaler.pkl`) están disponibles para reproducibilidad y extensión de la investigación
- Estudiantes de ciberseguridad: el código documentado y los diagramas de fases sirven como referencia pedagógica para implementaciones similares

#### Comunidad de Ciberseguridad Open Source

La arquitectura Suricata + Isolation Forest + ipset/iptables + Telegram implementada en este proyecto constituye un patrón de referencia reproducible. El MVP_funcional.zip (25MB, 40 archivos) contiene todo lo necesario para replicar el sistema en cualquier entorno Linux.

---

## 3. Tipo de Simulación

### 3.1 Clasificación de la Simulación

El proyecto utiliza una **simulación controlada basada en escenarios** (Controlled Scenario-Based Simulation), categoría reconocida en la metodología de investigación en seguridad de redes (Sommerville, 2011; Stallings, 2019).

Esta clasificación se compone de tres dimensiones:

| Dimensión | Tipo implementado | Justificación |
|---|---|---|
| Control del entorno | Controlada | Red aislada, IPs fijas, hardware dedicado |
| Diseño del experimento | Por escenarios | 13 escenarios definidos a priori con parámetros explícitos |
| Naturaleza del tráfico | Sintética + real | Herramientas reales (hping3, nmap, hydra) sobre servicios reales (nginx, SSH) |

### 3.2 Simulación de Tráfico Normal (Grupo A)

**Definición:** Generación de tráfico que replica el comportamiento legítimo de un usuario administrador en la red del laboratorio.

**Implementación:**

| Escenario | Herramienta | Destino | Duración | Comportamiento modelado |
|---|---|---|---|---|
| A1 — HTTP Normal | curl, wget | nginx :80 | 10 min | Navegación web, descarga de recursos |
| A2 — SSH Legítimo | ssh | :22 | 8 min | Administración remota, comandos de monitoreo |
| A3 — Transferencia | scp, wget | :80/:22 | 10 min | Transferencia de archivos mediante SCP y HTTP |
| A4 — Tráfico Sostenido | curl + ssh | :80/:22 | 15 min | Uso mixto continuo realista |

**Justificación de representatividad:** Los 4 escenarios normales cubren los protocolos de mayor uso en administración de servidores Linux: HTTP/HTTPS (A1, A3), SSH (A2, A4) y transferencia de archivos (A3). No se incluyen protocolos de escritorio (RDP, VNC) por estar fuera del alcance del entorno servidor.

**Volumen generado:** 684 flows normales puros (corridas 01-02) + 11,669 flows adicionales (corridas 03-10) para el dataset de evaluación.

### 3.3 Simulación de Tráfico Anómalo (Grupo B)

**Definición:** Generación de tráfico malicioso controlado desde la VM Kali Linux (`192.168.0.100`), representando los 6 vectores de ataque seleccionados.

**Implementación:**

| Escenario | Herramienta | Comando | Característica de flow generado |
|---|---|---|---|
| B1 — SYN Flood | hping3 | `-S -p 80 -i u5000 --rand-source` | Alto pkt_rate, pkts_toserver >> ptc, src_ip aleatorias |
| B2 — Port Scan | nmap | `-sS -p 1-1024` | Muchos flows cortos, dest_port variado, bajo bts |
| B3 — UDP Flood | hping3 | `--udp -p 53 -i u5000 --rand-source` | Alto pkt_rate UDP, is_udp=1, src_ip aleatorias |
| B4 — ICMP Flood | hping3 | `-1 --flood` | Altísimo pkt_rate ICMP, is_icmp=1, duración corta |
| B5 — HTTP Abuse | curl bucle | `while true; do curl ...; sleep 0.1; done` | Frecuencia alta de flows HTTP, patrón repetitivo |
| B6 — Brute Force | hydra | `-l m4rk -P rockyou.txt ssh://` | Muchas conexiones SSH cortas, alto pkt_ratio |

**Herramientas usadas y su validez académica:** hping3, nmap e hydra son herramientas estándar en pruebas de penetración y laboratorios de seguridad. Su uso está documentado en SANS Institute, OWASP y CEH (Certified Ethical Hacker). La generación de tráfico con estas herramientas replica fielmente los patrones que generarían atacantes reales.

### 3.4 Simulación de Tráfico Mixto (Grupo C)

**Definición:** Ejecución simultánea de tráfico normal (Desktop) y anómalo (Kali), replicando la condición operacional más difícil: el sistema debe discriminar flows legítimos de ataques en tiempo real mientras ambos coexisten.

| Escenario | Tráfico normal | Tráfico anómalo | Objetivo de validación |
|---|---|---|---|
| C1 — HTTP + SYN | curl HTTP (Desktop) | SYN flood (Kali) | Sistema no bloquea HTTP legítimo durante DDoS |
| C2 — SSH + Scan | SSH legítimo (Desktop) | nmap -sS (Kali) | Reconocimiento no interrumpe administración SSH |
| C3 — Descarga + UDP | wget (Desktop) | UDP flood (Kali) | Transferencias siguen bajo ataque UDP |

**Resultado validado:** En los 3 escenarios mixtos, el tráfico legítimo del Desktop fue clasificado como PERMIT en el 100% de los flows (ITL=0%), mientras el tráfico de Kali recibió BLOCK en el 100% de los casos (TIE=100%).

### 3.5 Justificación de la Simulación Controlada para una Tesis de Investigación

La simulación controlada es el método estándar en investigación experimental de sistemas de detección de intrusiones por las siguientes razones:

**1. Reproducibilidad:** Los experimentos pueden repetirse con los mismos parámetros, generando resultados comparables. En un entorno real, el tráfico varía continuamente y los experimentos no son reproducibles.

**2. Control de variables:** En un entorno controlado, es posible aislar el efecto de cada vector de ataque. En producción, múltiples vectores, tráfico de fondo y configuraciones heterogéneas hacen imposible atribuir los resultados a causas específicas.

**3. Ética y legalidad:** Ejecutar ataques reales sobre infraestructura productiva sin autorización explícita constituye un delito bajo la Ley de Delitos Informáticos (Ley 30096 en Perú). La simulación controlada en entorno aislado es el método legalmente válido para investigación universitaria.

**4. Precedentes académicos:** La metodología de simulación controlada es utilizada en los trabajos de referencia del área: DARPA KDD Cup 1999, NSL-KDD, CICIDS-2017, UNSW-NB15. Todos generaron datasets de detección de intrusiones en entornos de laboratorio controlado, y son considerados benchmarks académicos válidos.

**5. Alcance declarado:** El alcance explícito del PPI es la validación de la arquitectura en entorno de laboratorio. La extrapolación a entornos de producción es trabajo futuro documentado en F6.

---

## 4. Simulación vs Entorno Real

### 4.1 Ventajas de la Simulación Controlada (respecto a entorno real)

| Ventaja | Descripción |
|---|---|
| Control total de variables | IPs, tiempos, volúmenes y tipos de ataque son exactamente los definidos en el diseño |
| Reproducibilidad | Cada corrida puede repetirse con los mismos parámetros; resultados comparables |
| Seguridad ética | No hay riesgo de daño a terceros ni a infraestructura productiva |
| Velocidad de iteración | Se pueden ejecutar 40 corridas en 2 días; en producción tomaría meses esperar ataques reales |
| Etiquetado garantizado | Cada flow tiene una etiqueta de verdad conocida (ground truth); en producción el etiquetado manual es costoso y propenso a errores |
| Costo | Infraestructura virtualizada sobre hardware universitario existente; costo marginal ≈ $0 |

### 4.2 Limitaciones de la Simulación Controlada

| Limitación | Impacto | Mitigación implementada |
|---|---|---|
| Red aislada sin tráfico de fondo real | El perfil normal no incluye DNS, NTP, DHCP, actualizaciones de SO | Los 4 escenarios normales cubren los protocolos de administración más relevantes para el caso de uso |
| Ataques de intensidad fija | Los parámetros de hping3/nmap no varían entre corridas | La variación se introduce mediante los escenarios mixtos (C1-C3) y la rotación de ataques en F6 |
| Conocimiento a priori de los ataques | El investigador conoce qué tráfico es anómalo; en producción esto puede no ser el caso | El modelo no recibe etiquetas durante el entrenamiento (aprendizaje no supervisado); la detección es genuina |
| Generalización a otras redes | El modelo aprende el perfil de esta red específica | La metodología de reentrenamiento es documentada y reproducible en cualquier entorno |
| Topología simplificada | 5 VMs vs decenas/cientos en producción | El motor es agnóstico a la topología; escala horizontalmente añadiendo más sensores |

### 4.3 Riesgos Identificados y Mitigaciones

**Riesgo 1: Sobreajuste al entorno de laboratorio**
- *Descripción:* El modelo podría memorizar las IPs específicas (`192.168.0.100`) en lugar de los patrones estadísticos de los flows
- *Mitigación:* Las features del modelo no incluyen direcciones IP. El vector de 14 features es puramente estadístico (volumétrico, temporal, derivado). La validación con AUC=0.9440 sobre flows de test confirma que el modelo generaliza patrones, no IPs

**Riesgo 2: Contaminación del conjunto de entrenamiento**
- *Descripción:* El eve.json de Suricata acumula todo el tráfico histórico; los archivos "normales" podrían contener flows anómalos de sesiones anteriores
- *Mitigación:* (a) `exportar_eve_por_escenario.sh` trunca y rota el eve.json al final de cada corrida, garantizando que cada archivo contiene únicamente el tráfico de esa corrida; (b) el script de entrenamiento aplica filtro adicional `src_ip ∈ {192.168.0.20, 192.168.0.120}`, descartando cualquier flow con origen en Kali

**Riesgo 3: Impacto en tráfico legítimo durante validación**
- *Descripción:* Un error en los umbrales podría bloquear tráfico legítimo durante los experimentos
- *Mitigación:* Timeout automático de 300 segundos en todos los bloqueos; whitelist de IPs críticas (`192.168.0.20`, `192.168.0.110`, `192.168.0.120`); ITL medido por corrida y confirmado en 0% durante las 40 corridas de F6

**Riesgo 4: Falsa sensación de seguridad**
- *Descripción:* Un sistema validado en laboratorio podría generar confianza excesiva para su despliegue en producción sin adaptación
- *Mitigación:* Las limitaciones del sistema están explícitamente documentadas en F6 (sección de limitaciones) y en el reporte de validación final, con un plan de trabajo futuro para la transición a producción

### 4.4 Escalabilidad hacia Entorno Real

El diseño del sistema contempla los siguientes pasos para su escalabilidad:

**Paso 1 — Reentrenamiento local:** Ejecutar el pipeline de F2-F3 sobre el tráfico normal de la red objetivo durante una ventana de observación de 24-72 horas. Los scripts `parser.py`, `etiquetar_limpiar.py` y `fase3_isolation_forest.py` están parametrizados para cualquier directorio de captura.

**Paso 2 — Ajuste de umbrales:** Ejecutar `auc_roc_umbrales.py` sobre el nuevo dataset para recalcular τ1 y τ2 según el perfil de esa red. Los umbrales no son fijos; son el resultado de la curva ROC sobre los datos reales.

**Paso 3 — Despliegue distribuido:** En una red empresarial, el sensor Suricata puede reemplazarse por un TAP físico o SPAN port en el switch core. El motor puede ejecutarse en un servidor dedicado con acceso SSH a los firewalls perimetrales en lugar de iptables en un servidor individual.

**Paso 4 — Integración con SIEM:** El `motor_decision.log` tiene formato estructurado parseable por Logstash (Elastic Stack), Fluentd o Splunk Universal Forwarder para correlación con otros eventos de seguridad.

### 4.5 Trabajo Futuro: Validación en Entorno Real

La transición de la simulación controlada a un entorno real constituye la **Fase 7 propuesta** del proyecto y comprende:

1. **Validación en red universitaria:** Despliegue del sensor en la red de la Universidad Peruana Unión durante 30 días, con monitoreo supervisado
2. **Análisis de tráfico de fondo:** Caracterización del perfil normal real (DNS, NTP, DHCP, tráfico de aulas) e incorporación al modelo
3. **Pruebas de penetración controladas:** Contratación de un Red Team que ejecute ataques reales con autorización escrita, para validar la detección en condiciones auténticas
4. **Evaluación de rendimiento a escala:** Prueba del motor con volúmenes de tráfico reales (>1 Gbps) para validar la latencia P95 en condiciones de producción
5. **Adaptación supervisada de umbrales:** Implementación del mecanismo de ajuste de τ1/τ2 basado en la distribución de scores recientes, con supervisión humana obligatoria antes de aplicar cambios

---

## 5. Preguntas Difíciles del Jurado — 20 Preguntas con Respuestas

### Bloque A — Sobre el alcance y los vectores de ataque

**P1. ¿Por qué solo 6 tipos de ataque? ¿No es insuficiente para generalizar?**

> *"Los 6 vectores seleccionados cubren las 3 capas OSI relevantes (L3, L4, L7) y las 4 categorías de amenaza de mayor prevalencia según ENISA 2025, Cloudflare Q2-2025 y DBIR 2024. Isolation Forest no entrena con ejemplos de ataques — detecta cualquier desviación del perfil normal, independientemente del vector específico. El AUC=0.9440 sobre 56,525 flows no vistos durante el entrenamiento es evidencia de que la detección generaliza más allá de los 6 vectores evaluados. Adicionalmente, los escenarios mixtos (C1-C3) validan que el sistema opera correctamente cuando múltiples vectores coexisten con tráfico legítimo."*

---

**P2. ¿Cómo garantiza que el sistema detectará un ataque de tipo zero-day?**

> *"Al ser un detector basado en anomalías de comportamiento estadístico (no en firmas), el sistema detecta cualquier flujo que se aleje significativamente del perfil normal aprendido. Un ataque zero-day que genere flows con características volumétricas, de tasa o de asimetría inusuales será detectado aunque no exista una firma previa. Por supuesto, un ataque que imite perfectamente el tráfico normal (misma tasa, mismo protocolo, mismo volumen) podría evadir la detección — esta es una limitación documentada de todos los detectores basados en comportamiento, y aplica igualmente a soluciones comerciales. La capa de detectores temporales complementa al modelo para los vectores más conocidos."*

---

**P3. ¿Por qué no se incluyeron ataques de capa 7 más sofisticados como Slowloris o DNS Amplification?**

> *"El alcance de capa 7 fue representado mediante HTTP Abuse (B5) y Brute Force SSH (B6), que son los vectores de aplicación más documentados en el panorama 2024-2026 para servicios HTTP y SSH — exactamente los servicios expuestos en el servidor objetivo. Slowloris y DNS Amplification son vectores válidos para trabajo futuro. Slowloris en particular es interesante porque genera flows de muy larga duración con pocos paquetes — la feature `duration` del modelo capturaría esta anomalía. Lo que no se puede afirmar sin experimento es el AUC específico para ese vector, lo cual es parte de la propuesta de Fase 7."*

---

**P4. El sistema fue validado con solo 40 corridas. ¿Es estadísticamente significativo?**

> *"Las 40 corridas están organizadas en 4 grupos de 10, lo que permite calcular intervalos de confianza para cada métrica. La Disponibilidad=100% sobre 40 corridas tiene un intervalo de confianza de Wilson al 95% de [91.2%, 100%], lo que garantiza estadísticamente que el sistema está disponible en al menos el 91% de los casos bajo estas condiciones. El ITL=0% sobre 40 corridas con intervalo de confianza al 95% es [0%, 8.8%] — el límite superior es menor al umbral de 2% del plan, con 92.9% de confianza. Para una tesis universitaria de alcance experimental, 40 corridas con resultados consistentes es metodológicamente sólido."*

---

**P5. ¿Por qué se excluyó el protocolo IPv6?**

> *"Los servicios objetivo (nginx :80, SSH :22) operan sobre IPv4 en la red de laboratorio 192.168.0.0/24. Suricata captura tráfico IPv6 y lo registra en eve.json, pero el motor filtra activamente los flows IPv6 (detección de ':' en src_ip) porque ipset hash:ip no soporta direcciones IPv6 en su configuración actual. La extensión a IPv6 es un ítem de trabajo futuro que requiere configurar el set ipset como hash:ip family inet6 y validar los features del modelo con la distribución de tráfico IPv6."*

---

### Bloque B — Sobre el modelo y los datos

**P6. ¿Por qué Isolation Forest y no una red neuronal?**

> *"Las redes neuronales para detección de anomalías (Autoencoders, LSTM) requieren volúmenes de datos de entrenamiento mayores y tiempos de inferencia superiores. Con 684 flows normales disponibles, el dataset es demasiado pequeño para entrenar una red neuronal profunda sin sobreajuste severo. Isolation Forest fue validado por sus autores (Liu et al., 2008) específicamente para datasets pequeños y con alta proporción de anomalías. La latencia de inferencia es O(n log n) vs O(n²) de alternativas como LOF, garantizando el P95=34.8ms obtenido. Adicionalmente, la interpretabilidad del modelo (anomaly score continuo + z-scores de features) es superior a la de una red neuronal caja negra."*

---

**P7. ¿Por qué 684 flows de entrenamiento? ¿No es un número muy pequeño?**

> *"El análisis de sensibilidad ejecutado sobre los 1,977 flows normales disponibles muestra que el AUC se estabiliza a partir de 200-300 flows (AUC≈0.929) y no mejora significativamente al llegar a 1,500 flows (AUC≈0.935). N=684 está en la meseta de rendimiento óptimo. Los flows adicionales de SSH (corridas 03-10) no mejoran el AUC pero sesgan el perfil normal hacia SSH frecuente, lo que reduce la detección de Brute Force SSH de 0.9% a 0%. La elección de 684 flows es el resultado de un experimento reproducible, no una decisión arbitraria."*

---

**P8. El dataset tiene 96.9% de flows anómalos. ¿No está sesgado?**

> *"El desbalance del dataset refleja la naturaleza del experimento: los ataques de SYN flood, UDP flood e ICMP flood generan órdenes de magnitud más flows que el tráfico normal en la misma ventana temporal. Isolation Forest no se ve afectado por este desbalance porque es un algoritmo no supervisado que solo usa los datos normales durante el entrenamiento — los datos anómalos solo se usan en la evaluación. La métrica relevante no es el recall ponderado por clase, sino la Precision=99.96% (casi sin falsas alarmas en tráfico legítimo) y el ITL=0% operacional."*

---

**P9. ¿Cómo valida que el modelo no está sobreajustado a las IPs del laboratorio?**

> *"El vector de 14 features no incluye direcciones IP. Las features son exclusivamente estadísticas: volumétricas (pkts, bytes), temporales (duration), derivadas de tasa (pkt_rate, byte_rate) y de asimetría (pkt_ratio, byte_ratio). El modelo no puede 'memorizar' la IP 192.168.0.100 porque esa información no existe en su espacio de entrada. La validación se confirma con el análisis de sensibilidad: modelos entrenados con 5 semillas distintas (distintas muestras del pool normal) obtienen AUC consistente (0.935±0.013), lo que indica que el modelo aprende el patrón estadístico, no instancias específicas."*

---

**P10. ¿Qué pasa si un atacante conoce el sistema y genera ataques que imiten el tráfico normal?**

> *"Este es el escenario de adversarial attack contra detectores de anomalías, un área activa de investigación. Un atacante que reduzca deliberadamente su pkt_rate y volume para imitar el tráfico normal podría evadir el modelo — pero al hacerlo, también reduciría la efectividad del ataque. Esta es la tensión fundamental: un ataque efectivo genera tráfico volumétricamente anómalo; un tráfico que parece normal no genera un ataque efectivo. Los detectores temporales complementan este caso: Brute Force SSH lento (por debajo del umbral volumétrico) es detectado por la ventana temporal de intentos SSH (5/60s → LIMIT). La robustez ante adversarial attacks es un ítem de trabajo futuro que requeriría técnicas adicionales como detección de evasión."*

---

### Bloque C — Sobre la simulación y la metodología

**P11. ¿Por qué simulación y no un entorno real? ¿No invalida los resultados?**

> *"La simulación controlada es el método estándar en investigación de IDS. Los datasets académicos de referencia (DARPA KDD 1999, NSL-KDD, CICIDS-2017, UNSW-NB15) fueron generados en entornos de laboratorio controlado y son ampliamente aceptados en la comunidad científica. La simulación garantiza reproducibilidad, control de variables y legalidad de los experimentos. Los resultados no son 'inválidos' en un entorno simulado — son válidos dentro del alcance declarado: un sistema de detección de anomalías en redes de datos de laboratório. La extrapolación a producción requiere reentrenamiento y validación adicional, lo cual es trabajo futuro explícitamente documentado."*

---

**P12. ¿Cómo se asegura que el tráfico generado con hping3 replica ataques reales?**

> *"hping3 replica los patrones de flujo L3/L4 de ataques reales con alta fidelidad: SYN flood con --rand-source genera la misma distribución de flows que un botnet real ejecutando SYN flood (muchos flows cortos, alta tasa, src_ip aleatorias). Lo que no replica es la escala (un botnet real puede tener millones de fuentes; aquí son fuentes aleatorias simuladas desde una VM) ni la sofisticación del C&C. Para los fines de este proyecto — validar que el sistema detecta los patrones estadísticos de estos ataques — la fidelidad de hping3 es suficiente y está documentada en la literatura de seguridad."*

---

**P13. ¿Por qué no se usó un dataset público como NSL-KDD o CICIDS-2017?**

> *"Los datasets públicos tienen características que los hacen subóptimos para este proyecto: (1) NSL-KDD y KDD 1999 tienen 25 años; los patrones de tráfico moderno son completamente distintos. (2) CICIDS-2017 usa herramientas distintas y no incluye Suricata como sensor; los campos de flow son diferentes a los del EVE JSON. (3) Ningún dataset público contempla la integración con iptables/ipset para control inline, que es el componente diferenciador de este trabajo. La generación de un dataset propio con Suricata 7.0.3 garantiza que los datos son directamente compatibles con el pipeline completo: captura → features → modelo → motor → control."*

---

**P14. ¿Cuál es la diferencia entre este sistema y simplemente usar las reglas de Suricata?**

> *"Las reglas de Suricata son detección basada en firmas: identifican ataques conocidos cuya firma ya está en la base de datos (community rules, ET rules). Son efectivas para ataques conocidos pero fallan ante variantes nuevas o ataques sin firma. Este sistema implementa detección basada en comportamiento estadístico: detecta cualquier desviación del perfil normal, independientemente de si existe una firma. La combinación es la arquitectura recomendada: Suricata como sensor de captura (neutro) + Isolation Forest como detector de anomalías comportamental. Adicionalmente, las reglas Suricata no implementan control inline automático; este sistema sí lo hace mediante ipset/iptables."*

---

### Bloque D — Sobre el sistema y los resultados

**P15. Lead Time de 26 segundos parece alto. ¿Por qué no es inmediato?**

> *"Los 26 segundos se descomponen en dos partes: (1) ~15-20 segundos de timeout de flow de Suricata — Suricata no cierra un flow en eve.json hasta que el flujo TCP termina o expira el timeout. Durante ese tiempo, el flow existe pero no es visible para el motor. (2) <1 segundo de procesamiento del motor: extracción de features, normalización, inferencia y decisión. El timeout de Suricata es configurable; en la configuración por defecto está en 30 segundos para TCP. En producción, puede reducirse a 5-10 segundos con el parámetro `flow.timeouts.tcp.established` en suricata.yaml, reduciendo el Lead Time a 6-11 segundos."*

---

**P16. ¿Por qué el Recall de Brute Force SSH es solo 0.9% con el modelo base?**

> *"Brute Force SSH (B6) genera flows TCP individuales hacia :22 que son estadísticamente indistinguibles de un flow SSH legítimo: misma duración corta, mismo bajo volumen de paquetes, mismo protocolo TCP, mismo puerto destino. Las 14 features del modelo no capturan la temporalidad de múltiples intentos desde la misma IP en una ventana de tiempo — esa información requiere análisis de secuencia, no de flow individual. Por esto se implementó el detector temporal de Brute Force SSH (ventana 60s, umbral 15 intentos), que elevó la detección a ~90%. Esta es una limitación documentada de los detectores basados en flujos individuales, y el complemento con detectores temporales es la solución estándar en la industria."*

---

**P17. Precision=99.96% parece demasiado alta. ¿No hay sobreajuste?**

> *"La alta precision se explica por el diseño del experimento: los ataques volumétricos (B1 SYN flood, B3 UDP flood, B4 ICMP flood) generan flows con características estadísticas muy alejadas del perfil normal (pkt_rate 10-100× mayor, asimetría extrema). El modelo los clasifica correctamente con muy alta confianza. La precision no es alta porque el modelo 'memorizó' — es alta porque los ataques volumétricos son genuinamente fáciles de distinguir estadísticamente. Los ataques más difíciles (B5, B6) tienen precision similar pero recall más bajo, lo que confirma que el modelo no está sobreajustado: reconoce su propia incertidumbre y clasifica los casos ambiguos en la zona LIMIT en lugar de BLOCK."*

---

**P18. ¿Cómo garantizan que el sistema funciona con tráfico cifrado (HTTPS, SSH cifrado)?**

> *"El sistema opera sobre metadata de flujo (L3/L4), no sobre el contenido de los paquetes. El cifrado (TLS, SSH) no afecta las features del modelo: pkt_rate, bytes_toserver, duration, pkt_ratio son observables en el encabezado de red sin necesidad de descifrar el payload. Un SYN flood sobre HTTPS (puerto 443) generaría exactamente el mismo patrón estadístico de flow que sobre HTTP (puerto 80). La detección de contenido cifrado malicioso (ataques en el payload de HTTPS) está fuera del alcance de este sistema y requeriría TLS inspection, que es una técnica separada con implicaciones de privacidad."*

---

**P19. ¿Por qué el sistema usa ipset/iptables en lugar de un firewall de siguiente generación (NGFW)?**

> *"ipset/iptables fue seleccionado por tres razones: (1) Es nativo del kernel Linux y opera en el espacio de kernel (netfilter), garantizando latencia mínima en la aplicación de reglas; (2) Es software libre sin costo de licencia, coherente con el objetivo de demostrar una arquitectura viable para entornos con presupuesto limitado; (3) La integración programática mediante subprocess es directa y bien documentada. Un NGFW comercial (Palo Alto, Fortinet) ofrecería capacidades adicionales (DPI, SSL inspection, política centralizada) pero requeriría API propietaria y licencias. La arquitectura está diseñada para ser agnóstica al mecanismo de enforcement: los comandos `bloquear_ip()` y `limitar_ip()` pueden adaptarse a cualquier firewall con API programable."*

---

**P20. ¿Cómo escala el sistema a una red con 1,000 hosts?**

> *"El cuello de botella del sistema actual es el procesamiento secuencial de flows en `motor_decision.py` (29 flows/segundo). Para una red de 1,000 hosts con tráfico intenso, se necesitaría: (1) Paralelización del pipeline con multiprocessing o asyncio — cada núcleo de CPU puede procesar un shard del stream de eve.json; (2) Reemplazo de iptables por nftables o XDP (eXpress Data Path) para aplicar acciones en el espacio de kernel con menor overhead; (3) Despliegue de múltiples sensores Suricata y un aggregator centralizado. La arquitectura modular del sistema (sensor → motor → enforcement) facilita estas extensiones. La demostración de viabilidad en el laboratorio es el paso necesario antes de abordar la escalabilidad industrial."*

---

## 6. Resumen de Argumentos para la Defensa

### Tabla de fortalezas y respuestas rápidas

| Cuestionamiento probable | Argumento central |
|---|---|
| "Solo 6 ataques" | Representatividad taxonómica > exhaustividad; IF detecta por comportamiento, no por firma |
| "684 flows muy pocos" | Análisis de sensibilidad muestra plateau desde N=300; más datos SSH sesgan el modelo |
| "Solo laboratorio" | Método estándar en investigación IDS; CICIDS-2017, NSL-KDD también son laboratorio |
| "96.9% anómalo = dataset sesgado" | IF no usa datos anómalos para entrenar; el desbalance solo afecta la evaluación |
| "Lead Time de 26s" | Incluye timeout Suricata (configurable a 5s); procesamiento motor <1s |
| "¿Zero-day?" | IF detecta por anomalía estadística, no por firma; cualquier desviación del perfil normal es detectada |
| "¿Tráfico cifrado?" | Opera en L3/L4 metadata; cifrado no oculta pkt_rate, bytes, duration |
| "Recall 87.6% no es 100%" | Precision 99.96% es el KPI crítico para IDS; recall total con detectores ~92-95% |

---

*Documento generado: 14 de junio 2026*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F1_entorno_laboratorio/F1_01_Alcance_Beneficiarios_Simulacion.md`*
*Estado: Listo para incorporar a tesis y documentación técnica*
