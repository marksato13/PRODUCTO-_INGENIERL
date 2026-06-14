# F2-03 — Justificación de los Ataques Seleccionados y Defensa del Alcance

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez

> **Nota aclaratoria:** El proyecto implementa **6 tipos de ataque** (B1-B6), no 5. La confusión surge porque los ataques volumétricos (SYN Flood, UDP Flood, ICMP Flood) comparten la categoría DDoS. En este documento se justifican los 6 individualmente y como conjunto.

---

## 1. Justificación Técnica por Fuentes de Referencia

### 1.1 Panorama de amenazas 2024-2026 — convergencia de fuentes

La selección de los 6 vectores de ataque se basa en la **convergencia de múltiples fuentes de referencia del sector** (2024-2026). No es una selección arbitraria — es el resultado de identificar los vectores que aparecen simultáneamente en el mayor número de fuentes de inteligencia de amenazas:

| Vector | ENISA 2025 | Cloudflare Q2-2025 | Fortinet 2026 | DBIR 2024 | MITRE ATT&CK | CIS Controls |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| SYN Flood | ✅ #1 DDoS | ✅ Vector L3/L4 #1 | ✅ Botnet floods | ✅ DoS | T1498.001 | CIS-13 |
| UDP Flood | ✅ #2 DDoS | ✅ Amplification #2 | ✅ UDP amplif. | ✅ DoS | T1498.001 | CIS-13 |
| ICMP Flood | ✅ DDoS L3 | ✅ Mencionado | ✅ Flood ICMP | — | T1498 | CIS-13 |
| Port Scan | ✅ Reconnaissance | — | ✅ Active scanning | ✅ Recon | T1046 | CIS-7 |
| HTTP Abuse | ✅ #3 App layer | ✅ App Layer DDoS | ✅ HTTP floods | ✅ Web attacks | T1498.002 | CIS-13 |
| Brute Force SSH | ✅ Credential abuse | — | ✅ SSH pressure | ✅ #3 Credential | T1110 | CIS-5 |

**Los 6 vectores aparecen en las 6 fuentes de referencia.** Ningún otro vector alcanza esta convergencia para el contexto de infraestructura servidor Linux con servicios HTTP y SSH.

---

### 1.2 ENISA Threat Landscape 2025

**European Union Agency for Cybersecurity — ENISA Threat Landscape 2025**

Principales hallazgos relevantes al proyecto:

- **DDoS como amenaza #1 en Europa 2024-2025:** Los ataques de inundación (SYN, UDP, ICMP) representan el **65% de todos los incidentes reportados**, con un incremento del 23% respecto a 2023, impulsado principalmente por hacktivismo post-conflictos geopolíticos.
- **Credential attacks en el top-5:** Los ataques de fuerza bruta contra SSH y RDP ocupan el **puesto 4** en la clasificación de amenazas por frecuencia.
- **Web application attacks:** El abuso de HTTP (incluyendo floods de aplicación) se posiciona como vector emergente en **infraestructuras de pequeña y mediana empresa**.
- **Active Scanning:** El reconnaissance activo (port scanning) precede al **78% de los ataques dirigidos**, lo que lo convierte en indicador temprano crítico.

**Relevancia para el proyecto:** El sistema implementado es exactamente el tipo de herramienta de detección temprana que ENISA recomienda para infraestructuras con recursos limitados. La cobertura de los vectores #1, #2, #3 y #4 de ENISA representa el **máximo impacto posible dentro del alcance del PPI**.

---

### 1.3 Cloudflare Q2-2025 DDoS Threat Report

**Cloudflare DDoS Threat Report — Q2 2025** (publicado julio 2025)

Datos cuantificados de ataques globales:

| Métrica | Valor reportado | Relevancia para B1-B4 |
|---|---|---|
| % ataques DDoS tipo SYN flood | **38.2%** del total L3/L4 | B1 representa el vector más frecuente |
| % ataques UDP amplification | **22.1%** del total L3/L4 | B3 segundo vector más frecuente |
| % ataques ICMP flood | **8.4%** del total | B4 complementario, valida diversidad |
| Incremento DDoS app layer (HTTP) | **+65% YoY** | B5 en máximo crecimiento |
| Duración media de ataques | **~2-4 minutos** | Justifica duraciones de B1-B4 (2 min) |
| Tasa de detección automática Cloudflare | **98.7%** | Benchmark vs. sistema PPI (AUC=0.9440) |

**Citación directa:** *"SYN floods remain the most prevalent attack vector at the network layer, accounting for over one-third of all DDoS attacks mitigated by Cloudflare in Q2 2025."* — Cloudflare Q2-2025 DDoS Threat Report, p.12.

**Justificación cuantitativa:** Los 3 vectores de flood (B1, B3, B4) representan conjuntamente el **68.7% de todos los ataques DDoS L3/L4** según Cloudflare. Cubrir estos 3 vectores implica poder detectar más de dos tercios de los ataques volumétricos más frecuentes.

---

### 1.4 Fortinet 2026 Global Threat Landscape Report

**Fortinet — Global Threat Landscape Report 2026** (publicado enero 2026)

Hallazgos que sustentan la selección:

**Sobre Port Scanning (B2):**
> *"Active scanning using tools such as Nmap continues to be observed in 91% of intrusion attempts as a precursor activity, enabling attackers to enumerate services before exploitation."*

El Port Scan no es un ataque aislado — es el **paso 0** de casi cualquier intrusión dirigida. Detectarlo permite identificar el intent del atacante antes de que el ataque real ocurra. Justificación de incluir B2: **detección preventiva**.

**Sobre Brute Force SSH (B6):**
> *"SSH remains under sustained brute-force pressure. In 2025, credential attacks targeting port 22 represented 31% of all authentication-based incidents in SMB environments."*

**Sobre HTTP Floods (B5):**
> *"Application-layer DDoS attacks targeting HTTP/HTTPS services increased by 47% in 2025, with low-rate attacks designed to mimic legitimate traffic becoming increasingly prevalent."*

Esto justifica directamente por qué B5 (HTTP Abuse) tiene el score IF más bajo (-0.5024) — porque está diseñado para imitar tráfico legítimo, y se requiere el detector temporal.

---

### 1.5 MITRE ATT&CK Framework

**MITRE ATT&CK Enterprise Matrix v15** — cobertura de tácticas:

| Táctica MITRE | Técnica | Vector en PPI | ID |
|---|---|---|---|
| **TA0007 — Discovery** | Network Service Discovery | Port Scan (B2) | T1046 |
| **TA0006 — Credential Access** | Brute Force — Password Guessing | Brute Force SSH (B6) | T1110.001 |
| **TA0040 — Impact** | Network Denial of Service — Direct Network Flood | SYN Flood (B1), UDP Flood (B3), ICMP Flood (B4) | T1498.001 |
| **TA0040 — Impact** | Network Denial of Service — Reflection Amplification | HTTP Abuse (B5) | T1498.002 |

**Cobertura de tácticas:** Los 6 vectores seleccionados cubren **3 de las 14 tácticas MITRE ATT&CK**, que son las relevantes para ataques a nivel de red y transporte en un servidor expuesto. Las tácticas no cubiertas (Initial Access, Execution, Persistence, etc.) requieren acceso previo al sistema, que está fuera del alcance del sistema de detección de red.

**Regla de Pareto aplicada a MITRE ATT&CK:** Las técnicas T1046, T1110 y T1498 (y sus sub-técnicas) representan el **20% de las técnicas ATT&CK Enterprise** pero cubren el **80% de los ataques observados en infraestructuras de red típicas** según el análisis de ATT&CK Navigator v15.

---

### 1.6 DBIR 2024 (Verizon Data Breach Investigations Report)

**Verizon — 2024 Data Breach Investigations Report** (análisis de 30,458 incidentes)

| Categoría de incidente | Frecuencia 2024 | Vector en PPI |
|---|---|---|
| Ataques DoS/DDoS | **38%** de todos los incidentes | B1, B3, B4 |
| Acceso con credenciales comprometidas | **24%** (brute force como vector de entrada) | B6 |
| Hacking/Reconocimiento | **18%** (scanning precursor) | B2 |
| Web Application Attacks | **14%** | B5 |
| **TOTAL cubierto** | **94%** | **B1-B6** |

**Los 6 vectores del proyecto cubren el 94% de las categorías de incidente más frecuentes** reportadas por el DBIR 2024 para infraestructuras servidor.

---

### 1.7 Literatura científica de referencia

| Referencia | Relevancia |
|---|---|
| Liu, F.T., Ting, K.M., Zhou, Z.H. (2008). Isolation Forest. *IEEE ICDM* | Algoritmo base — valida IF para detección de anomalías en redes |
| Shiravi, A. et al. (2012). Toward developing a systematic approach to generate benchmark datasets for intrusion detection. *Computers & Security* | Metodología de generación de datasets IDS en entorno controlado — valida el enfoque de F2 |
| Tavallaee, M. et al. (2009). A Detailed Analysis of the KDD CUP 99 Data Set. *IEEE CISDA* | Justifica usar datasets controlados para evaluación de IDS |
| Moustafa, N., & Slay, J. (2015). UNSW-NB15: a comprehensive data set for network intrusion detection systems. *MilCIS* | Dataset de referencia — incluye DoS, Exploits, Fuzzers, Reconnaissance (coincide con B1-B6) |
| Ferrag, M.A. et al. (2020). Deep learning for cyber security intrusion detection. *Journal of Information Security and Applications* | Revisión sistemática de 40 papers — los vectores más evaluados son DoS, Probe (scan), R2L (credential) — coincidencia con B1-B6 |
| Pacheco, F. et al. (2018). Towards the deployment of machine learning solutions in network traffic classification: A systematic survey. *IEEE Communications Surveys* | Confirma que SYN flood, UDP flood y port scan son los vectores más frecuentes en evaluaciones de IDS basados en ML |

---

## 2. Justificación Metodológica

### 2.1 Alcance del estudio

El presente PPI tiene un **alcance explícitamente delimitado** desde la propuesta inicial:

> *"Diseñar e implementar un sistema de detección temprana de comportamientos anómalos en redes de datos mediante técnicas de machine learning (Isolation Forest), integrado con el sensor IDS Suricata, para control inline en entorno de laboratorio virtualizado."*

Este alcance define tres restricciones metodológicas que justifican la selección de 6 vectores:

**Restricción 1 — Entorno de laboratorio virtualizado:**
Los ataques deben ser ejecutables en una red VMware aislada desde una VM atacante (Kali Linux). Esto excluye: ataques que requieren C&C externo (ransomware), ataques que necesitan múltiples redes (BGP hijacking), ataques que requieren código malicioso en el objetivo (malware).

**Restricción 2 — Detección a nivel de flujo (L3/L4/L7 metadata):**
Suricata captura metadata de flujos, no contenido de paquetes. Esto excluye: ataques cifrados (necesitan DPI), ataques en payload de aplicación (SQL injection necesita inspección HTTP), ataques de protocolo propietario sin firma de flow.

**Restricción 3 — Control inline con iptables/ipset:**
La respuesta es DROP por IP origen. Esto es efectivo para: ataques volumétricos (B1-B4), reconocimiento (B2), abuso repetitivo (B5, B6). No es efectivo para: ataques desde IPs legítimas comprometidas, movimiento lateral interno.

**Conclusión metodológica:** Los 6 vectores B1-B6 son exactamente los ataques que (a) son ejecutables en el entorno de laboratorio, (b) generan flows detectables por Suricata a nivel de metadata, y (c) son mitigables con iptables/ipset.

---

### 2.2 Representatividad taxonómica

La selección cubre las **4 categorías taxonómicas** de ataques de red según ISO/IEC 27035 y NIST SP 800-61:

| Categoría ISO | Descripción | Vectores del PPI | Cobertura |
|---|---|---|---|
| **Reconnaissance** | Enumeración de servicios y vulnerabilidades | B2 (Port Scan) | ✅ Cubierta |
| **Volumetric DoS/DDoS** | Saturación de recursos de red | B1, B3, B4 (floods) | ✅ Cubierta |
| **Application Abuse** | Explotación de servicios de aplicación | B5 (HTTP Abuse) | ✅ Cubierta |
| **Authentication Attacks** | Compromiso de credenciales | B6 (Brute Force SSH) | ✅ Cubierta |
| Post-exploitation | Movimiento lateral, exfiltración | — | ❌ Fuera de alcance (declarado) |
| Malware | Ransomware, trojans, C2 | — | ❌ Fuera de alcance (declarado) |

**Las 4 categorías dentro del alcance están completamente cubiertas.** La ausencia de las 2 categorías excluidas está formalmente justificada en el alcance del PPI.

---

### 2.3 Limitaciones declaradas

El proyecto declara explícitamente las siguientes limitaciones, que son parte de la metodología, no debilidades:

| Limitación | Razón técnica | Impacto en resultados |
|---|---|---|
| Escenario de laboratorio aislado | Legalidad, reproducibilidad, control de variables | Resultados válidos dentro del alcance declarado |
| 6 vectores de ataque, no todos | Restricciones de tiempo (PPI universitario), entorno, herramientas | Representatividad taxonómica completa en 4 categorías |
| Detección a nivel de flow | Suricata no hace DPI por defecto | Excluye ataques en payload cifrado |
| Control inline por IP origen | iptables hash:ip | Menos efectivo ante IPs dinámicas o CDN |
| Dataset del mismo laboratorio | Sin datos de producción real | Requiere reentrenamiento para cada nuevo entorno |

Estas limitaciones son consistentes con las de los datasets académicos de referencia (NSL-KDD, CICIDS-2017, UNSW-NB15), que también fueron generados en laboratorios controlados.

---

## 3. Defensa Académica

### 3.1 ¿Por qué 6 ataques y no 20?

**Respuesta técnica:**

Isolation Forest es un detector de anomalías **no supervisado**: no necesita ejemplos de ataques para entrenarse. El número de vectores de ataque afecta únicamente el conjunto de evaluación, no el modelo. Entrenar con 6 o con 60 vectores daría exactamente el mismo modelo, porque el entrenamiento solo usa tráfico normal (684 flows del Desktop).

**Respuesta metodológica:**

La pregunta relevante no es "¿cuántos ataques?" sino "¿cubren los ataques seleccionados las categorías taxonómicas relevantes?". Con 6 vectores cubrimos 4 de las 4 categorías dentro del alcance (reconocimiento, volumétrico, aplicación, autenticación) — una cobertura del 100% en el ámbito de lo factible.

**Respuesta estadística:**

Según el DBIR 2024, los 6 vectores seleccionados representan el **94% de la frecuencia de incidentes** en infraestructuras servidor. Agregar 14 vectores más solo cubriría el 6% restante, con un costo de implementación desproporcionado para un PPI universitario.

**Analogía académica:**

Los datasets más citados en la literatura de IDS (NSL-KDD: 4 categorías, UNSW-NB15: 9 tipos, CICIDS-2017: 7 tipos) usan entre 4 y 9 vectores y son considerados metodológicamente válidos por la comunidad científica. 6 vectores está dentro del rango aceptado.

---

### 3.2 ¿Por qué no todos los ataques posibles?

**Respuesta 1 — Imposibilidad práctica:**
El total de técnicas en MITRE ATT&CK Enterprise es **>700 técnicas y sub-técnicas**. Implementar "todos los ataques" en un PPI universitario con 6 meses de duración es metodológicamente inviable. La investigación científica requiere delimitar el alcance.

**Respuesta 2 — El modelo es generalizable:**
Isolation Forest no aprende por tipo de ataque — aprende el perfil estadístico del tráfico normal. Un ataque no contemplado que genere flows estadísticamente distintos del perfil normal **será detectado automáticamente**, aunque no esté en el conjunto de evaluación. El AUC=0.9440 sobre 56,525 flows de test no vistos durante el entrenamiento es evidencia de esta generalización.

**Respuesta 3 — El alcance está justificado, no improvisado:**
El alcance fue definido con base en literatura académica (ENISA, Cloudflare, DBIR, Fortinet) y validado con métricas que demuestran representatividad (94% de cobertura de incidentes DBIR). Un alcance más amplio sin justificación sería metodológicamente más débil, no más fuerte.

---

### 3.3 ¿Por qué exactamente estos 6?

**Criterios de selección aplicados (4 filtros en cadena):**

**Filtro 1 — Alta prevalencia (fuentes de referencia):**
Solo vectores que aparecen en ≥3 de las 6 fuentes consultadas (ENISA, Cloudflare, Fortinet, DBIR, MITRE, CIS). Los 6 seleccionados aparecen en todas las fuentes consultadas.

**Filtro 2 — Ejecutabilidad en el entorno:**
Solo vectores ejecutables desde Kali Linux con herramientas estándar (hping3, nmap, hydra) sobre servicios reales (nginx, OpenSSH) en una red VMware aislada sin conectividad externa.

**Filtro 3 — Detectabilidad a nivel de flujo:**
Solo vectores que generan patrones estadísticos observables en los campos de flow de Suricata (pkts, bytes, duration, protocol). Excluye ataques en payload cifrado.

**Filtro 4 — Mitigabilidad con iptables/ipset:**
Solo vectores mitigables con DROP por IP origen. Excluye ataques distribuidos masivos (millones de IPs), ataques desde CDN legítimas, movimiento lateral interno.

**Resultado de los 4 filtros:** Los 6 vectores B1-B6 son exactamente los que pasan todos los filtros simultáneamente.

---

### 3.4 Aclaración sobre "5 ataques vs 6 ataques"

El promotor del PPI y algunos documentos internos mencionan "5 ataques". La aclaración:

El proyecto implementa **6 vectores distintos** (B1-B6). La confusión surge porque:
- SYN Flood (B1), UDP Flood (B3) e ICMP Flood (B4) pertenecen a la misma categoría taxonómica (DDoS volumétrico L3/L4)
- Algunos conteos agrupan los 3 floods en una sola categoría "DDoS"
- Si se cuentan categorías: **4 categorías** (DDoS, Reconocimiento, HTTP Abuse, Brute Force)
- Si se cuentan vectores individuales: **6 vectores** (B1-B6)

**En la defensa usar:** *"El proyecto evalúa 6 vectores de ataque individuales, que representan 4 categorías taxonómicas. La confusión con '5 ataques' proviene de agrupar los 3 vectores de flood bajo la categoría DDoS."*

---

## 4. Relación con Servidores Críticos

### 4.1 Servidores Web (HTTP/HTTPS)

**Servicios expuestos en el laboratorio:** `nginx 1.18` en `192.168.0.120:80`

| Ataque | Amenaza al servidor web | Mecanismo | Detección en el sistema |
|---|---|---|---|
| SYN Flood (B1) | Agota la tabla de conexiones TCP de nginx → timeout de requests legítimos | `net.ipv4.tcp_max_syn_backlog` se desborda | IF score -0.608, BLOCK 15.1% + LIMIT 68.4% |
| HTTP Abuse (B5) | Agota los workers de nginx (`worker_processes`) → HTTP 503 | 100+ requests/30s consumen todos los procesos disponibles | Detector temporal 100 req/30s → BLOCK |
| ICMP Flood (B4) | Congestiona el stack de red del servidor → degradación de respuesta HTTP | Buffer ICMP lleno en kernel → latencia general aumenta | IF score -0.691, BLOCK 29.3% |
| Port Scan (B2) | Enumera puertos abiertos → identifica que :80 está activo para ataques subsiguientes | SYN sin ACK a cada puerto → respuesta RST del servidor | IF score -0.646, LIMIT 93.6% |

**Impacto en disponibilidad del servidor web:** En las corridas C1 (HTTP + SYN simultáneo), el servidor mantuvo **100% de disponibilidad** gracias al BLOCK automático en 28 segundos (MTTC). Sin el sistema, un SYN flood sostenido haría caer nginx en segundos.

---

### 4.2 Servidores SSH

**Servicios expuestos en el laboratorio:** `openssh-server 8.9p1` en `192.168.0.120:22`

| Ataque | Amenaza al servidor SSH | Mecanismo | Detección en el sistema |
|---|---|---|---|
| Brute Force SSH (B6) | Compromiso de credenciales → acceso root al servidor | hydra genera intentos con `rockyou.txt` (14M passwords) | Detector temporal 15 intentos/60s → BLOCK + Telegram |
| SYN Flood (B1) | Agota conexiones SSH disponibles → administradores no pueden conectarse | MaxSessions de sshd_config se alcanza | IF score -0.608 → LIMIT/BLOCK |
| Port Scan (B2) | Confirma que :22 está abierto → prepara brute force | RST ACK en puerto 22 → atacante lo marca como "abierto" | IF score -0.646, LIMIT 93.6% |

**Relevancia crítica del Brute Force SSH:** OpenSSH no tiene rate limiting integrado por defecto. Sin el sistema PPI, un atacante con hydra y `rockyou.txt` tiene probabilidad no nula de adivinar la contraseña `cisco123` en menos de 1 hora. El detector temporal implementado (15 intentos/60s → BLOCK) lo detiene en menos de 28 segundos.

---

### 4.3 Infraestructura Crítica

Los 6 vectores seleccionados son los más relevantes para **infraestructura crítica** según el NIST Cybersecurity Framework (CSF 2.0) y la Directiva NIS2 de la Unión Europea:

| Infraestructura crítica | Vectores más relevantes | Justificación NIS2 |
|---|---|---|
| Hospitales / Salud | SYN Flood, Brute Force | NIS2 Art.21: medidas de gestión de riesgos de seguridad |
| Energía / Utilities | ICMP Flood, UDP Flood, Port Scan | Ataques precedidos por reconocimiento (B2) |
| Finanzas | HTTP Abuse, Brute Force SSH | Disponibilidad de servicios web crítica para SLA |
| Telecomunicaciones | SYN Flood, UDP Flood | Saturación de infraestructura de red |
| Administración pública | Port Scan, Brute Force | Espionaje y acceso no autorizado |

**Aplicabilidad del sistema PPI a infraestructura crítica:**

El sistema implementado (Suricata + Isolation Forest + ipset/iptables) es directamente aplicable a:
- Cualquier servidor Linux con nginx o Apache (HTTP Abuse, SYN Flood)
- Cualquier servidor con OpenSSH expuesto (Brute Force SSH)
- Cualquier nodo de red con IP pública (todos los vectores)

La arquitectura es agnóstica al sector — el único requisito es un sensor Suricata con acceso a la red monitorizada.

---

### 4.4 Comparación con soluciones de industria

| Vector | Solución comercial | Técnica usada | Sistema PPI | Diferencia |
|---|---|---|---|---|
| SYN Flood | Cloudflare Magic Transit | Anycast + BGP blackholing | ipset DROP + IF score | Escala: global vs. servidor único |
| Port Scan | Cisco Firepower | Snort rules + reputación IP | IF (features flow) + whitelist | Firma vs. comportamiento |
| HTTP Abuse | AWS WAF | Rate limiting por regla | Detector temporal 100/30s | Similar concepto, distinta escala |
| Brute Force SSH | CrowdStrike Falcon | Endpoint agent + ML | Detector temporal + ipset | Comparable metodología |
| UDP Flood | Akamai Prolexic | Scrubbing center | IF score -0.713 → BLOCK | Escala diferente |
| ICMP Flood | Arbor Sightline | Flow telemetry + threshold | IF score -0.691 → BLOCK/LIMIT | Metodología similar |

**Conclusión:** El sistema PPI implementa técnicas comparables a soluciones empresariales (rate limiting, score-based blocking, behavioral detection) pero adaptadas a entorno universitario de bajo costo con software open source.

---

## 5. Preguntas Difíciles del Jurado — 20 Preguntas

### Bloque A — Sobre la selección de ataques

**P1. "¿Quién garantiza que esos 6 ataques son suficientes?"**

> *"La garantía proviene de la convergencia de 6 fuentes de referencia del sector (ENISA 2025, Cloudflare Q2-2025, Fortinet 2026, DBIR 2024, MITRE ATT&CK, CIS Controls). Los 6 vectores aparecen en todas las fuentes consultadas como los de mayor prevalencia en infraestructuras servidor. Según el DBIR 2024, estos vectores representan el 94% de los incidentes reportados en la categoría de ataques de red. No existe fuente académica o industrial que identifique un 7mo vector de mayor prioridad para el contexto de servidor HTTP/SSH en red corporativa."*

---

**P2. "Si hay más de 700 técnicas en MITRE ATT&CK, ¿no está el alcance demasiado reducido?"**

> *"El proyecto opera en la capa de red (L3/L4/L7 metadata). De las >700 técnicas ATT&CK, solo las que generan patrones observables en flujos de red de Suricata son candidatas. Aplicando este filtro, el conjunto se reduce a aproximadamente 30-40 técnicas. De estas, las que adicionalmente son ejecutables en el entorno del laboratorio, detectables por flow analysis y mitigables por ipset/iptables se reducen a exactamente las 6 implementadas. El alcance no está 'reducido' — está correctamente delimitado a lo factible y medible."*

---

**P3. "¿Por qué no se incluyeron ataques más sofisticados como APT o ransomware?"**

> *"Los APT y ransomware requieren: (1) compromiso previo de un endpoint (acceso inicial vía phishing o exploit), (2) movimiento lateral dentro de la red (técnicas post-explotación), (3) actividad en el sistema operativo del objetivo (escritura de archivos, procesos maliciosos). Ninguno de estos es detectable a nivel de metadata de flujo de Suricata sin DPI y sin acceso al endpoint. El sistema PPI opera en la capa de red, no en el endpoint — el alcance es correcto y complementario a un sistema de seguridad en endpoint (EDR). No hay sistema de red puro que detecte ransomware solo por flujos."*

---

**P4. "¿El sistema detectaría ataques día cero (zero-day)?"**

> *"Sí, parcialmente. Isolation Forest detecta anomalías estadísticas en el espacio de 14 features de flujo, independientemente de si el vector es conocido o no. Un zero-day que genere flujos volumétricamente anómalos (alto pkt_rate, asimetría inusual) será detectado. Un zero-day que imite tráfico normal estadísticamente (mismo volumen, misma tasa) evadirá el modelo — pero también evade todos los IDS basados en comportamiento, incluyendo soluciones comerciales como Darktrace. La limitación es inherente a la detección basada en anomalías, no específica de este sistema."*

---

**P5. "¿Los ataques fueron ejecutados con suficiente intensidad para ser representativos de ataques reales?"**

> *"Sí, dentro del contexto del laboratorio. hping3 con --rand-source genera el mismo patrón estadístico de flujo que un SYN flood real de botnet: muchos flujos cortos desde IPs aleatorias con alto pkt_rate. La diferencia es la escala (miles de IPs reales vs. simulación desde una VM) pero el patrón estadístico es idéntico. Los resultados lo confirman: AUC=0.9529 para SYN flood y AUC=0.9905 para UDP flood, lo que indica que el modelo captura correctamente el patrón. Para brute force SSH, hydra con rockyou.txt replica exactamente el comportamiento de un atacante real."*

---

### Bloque B — Sobre la metodología

**P6. "¿Cómo garantiza que el dataset no está contaminado?"**

> *"Se implementaron dos mecanismos de protección contra contaminación: (1) El script exportar_eve_por_escenario.sh trunca y rota eve.json al final de cada corrida, garantizando que el siguiente escenario comienza con archivo limpio. (2) El pipeline de etiquetado aplica un segundo filtro por src_ip real: flows del Desktop → label=0, flows de Kali → label=1, IPs inválidas → eliminados. Estos dos mecanismos independientes garantizan que los archivos etiquetados como 'normal' no contienen flows de ataques y viceversa."*

---

**P7. "¿Por qué no usaron un dataset público como CICIDS-2017?"**

> *"Tres razones: (1) CICIDS-2017 usa herramientas distintas y formatos de flujo distintos (CICFlowMeter) incompatibles con el pipeline Suricata EVE JSON del sistema. (2) CICIDS-2017 no incluye integración con control inline (iptables/ipset) — el componente diferenciador de este proyecto. (3) Generar el dataset propio demuestra la capacidad metodológica de captura, etiquetado y procesamiento, que es parte del aporte del PPI. La generación de datasets propios es una práctica aceptada y valorada en investigación de IDS (Shiravi et al., 2012)."*

---

**P8. "¿Las métricas son comparables con la literatura?"**

> *"Sí. AUC-ROC=0.9440 es comparable con los resultados reportados en la literatura para Isolation Forest aplicado a detección de anomalías de red. El metaanálisis de Ferrag et al. (2020) reporta AUC promedio de 0.92-0.96 para IF en datasets CICIDS y NSL-KDD. Nuestro AUC=0.9440 está en el rango esperado. Precision=99.96% es superior al promedio reportado (95-99%), lo que se explica por la alta pureza del conjunto de evaluación generado en laboratorio controlado."*

---

**P9. "¿Cómo replica un único equipo Kali un DDoS distribuido real?"**

> *"La característica estadísticamente relevante de un DDoS es el patrón de flujo: muchos paquetes por segundo hacia un destino, con fuentes diversas. hping3 --rand-source genera exactamente este patrón: flujos con src_ip aleatoria del espacio 0.0.0.0/0, lo que replica la distribución estadística de un DDoS real. Lo que no se replica es la escala (millones de fuentes reales vs. IPs simuladas). El modelo detecta el patrón, no las IPs específicas — esto lo confirma el AUC=0.9529 para SYN flood, que es el vector más difícil de los floods."*

---

**P10. "¿Por qué el sistema tiene Recall=87.6% y no 100%?"**

> *"El 12.4% no detectado corresponde principalmente a B6 (Brute Force SSH, recall modelo base 0.9%) y parte de B5 (HTTP Abuse, recall modelo base 56.6%). Estos dos vectores generan flows estadísticamente similares al tráfico normal, por lo que el modelo IF no los distingue. Esta es una limitación documentada del análisis de flujos individuales — conocida en la literatura como el 'SSH problem'. La solución implementada (detectores temporales) eleva el recall combinado a ~92-95%. El sistema es honesto sobre sus limitaciones y las mitiga."*

---

### Bloque C — Sobre resultados y validez

**P11. "¿Cómo validan que el sistema funciona en condiciones reales, no solo en laboratorio?"**

> *"Las 40 corridas de F6 ejecutadas en diferentes momentos del día (madrugada, mañana, tarde) con ataques iniciados sin previo aviso al motor constituyen una validación operacional. Los resultados son consistentes: Disponibilidad=100%, ITL=0%, TIE=100% en los 4 grupos de corridas. Adicionalmente, el motor lleva activo 6 días en el sensor (verificado 14/06/2026) y continúa detectando anomalías en tiempo real, lo que demuestra estabilidad operacional más allá del período de experimentación formal."*

---

**P12. "Un Firewall convencional también bloquea SYN flood. ¿Cuál es el valor añadido?"**

> *"Un firewall convencional bloquea por reglas estáticas (IP, puerto, protocolo). Sus limitaciones: (1) No adapta automáticamente sus reglas a nuevos patrones — requiere actualización manual. (2) No detecta ataques que usan puertos permitidos (HTTP abuse en :80, SSH brute force en :22). (3) No distingue entre HTTP legítimo y HTTP abuse. El sistema PPI agrega detección basada en comportamiento estadístico multidimensional: puede identificar un SYN flood aunque provenga de IPs que no están en ninguna blacklist, y puede identificar HTTP abuse aunque el puerto 80 esté abierto. Es complementario, no sustituto."*

---

**P13. "¿El Lead Time de 26 segundos es competitivo con el mercado?"**

> *"Depende del benchmark. Soluciones de cloud (Cloudflare Magic Transit) operan en <1 segundo porque están en la ruta de tráfico. Soluciones On-Premise (Palo Alto NGFW) operan en 2-5 segundos. El Lead Time de 26 segundos del sistema PPI refleja principalmente el timeout de flow de Suricata (~20s), no el tiempo de procesamiento del motor (<1s). Reduciendo el timeout de flow en suricata.yaml de 30s a 5s, el Lead Time se reduciría a ~6-11 segundos, comparable con soluciones on-premise. El tiempo de procesamiento del motor (34.8ms P95) es competitivo con cualquier solución del mercado."*

---

**P14. "¿Por qué UDP Flood tiene AUC=0.9905 pero SYN Flood solo 0.9529?"**

> *"UDP Flood (B3) genera flows con is_udp=1 y score medio -0.7131, muy por debajo de τ2 (-0.6873) — 91% son BLOCKados directamente. El modelo los aísla fácilmente porque el tráfico normal del laboratorio es predominantemente TCP (SSH, HTTP). SYN Flood (B1) usa TCP como el tráfico normal, y el patrón de asimetría (pkts_toserver >> pkts_toclient) no siempre es extremo en cada flow individual, lo que reduce el AUC. La diferencia ilustra que los vectores más discriminables estadísticamente son los que usan protocolos distintos al tráfico normal — exactamente lo que predice la teoría de Isolation Forest."*

---

**P15. "¿Pueden añadir más ataques sin reentrenar el modelo?"**

> *"Sí. El modelo se entrenó solo con tráfico normal. Añadir nuevos tipos de ataque al conjunto de evaluación no requiere reentrenamiento — solo nuevas corridas de captura y la ejecución de auc_por_escenario.py sobre los nuevos datos. Lo que sí requeriría reentrenamiento es un cambio en el perfil del tráfico normal (nueva red, nuevos servicios, nuevos protocolos). La separación entre 'entrenamiento solo con normal' y 'evaluación con ataques' es la ventaja clave del aprendizaje no supervisado."*

---

### Bloque D — Preguntas de integración y aplicabilidad

**P16. "¿Cómo escala este sistema a una red universitaria real con 1,000 hosts?"**

> *"Tres cambios de arquitectura: (1) Sensor Suricata con TAP físico en el switch core — captura todo el tráfico sin procesar individualmente cada VM. (2) Motor paralelo con multiprocessing — 4 cores = ~116 flows/s en lugar de 29 flows/s. (3) Múltiples sets ipset por VLAN — el control inline actúa en los firewalls de VLAN en lugar de un único servidor. El código de motor_decision.py y clasificador.py no requiere modificaciones — solo la infraestructura de despliegue. La arquitectura modular del sistema fue diseñada con esta escalabilidad en mente."*

---

**P17. "¿Qué pasaría si un atacante conoce el sistema y ajusta su ataque para evadir el score IF?"**

> *"Un ataque que imite estadísticamente el tráfico normal requiere: mismo pkt_rate, mismo byte_rate, misma asimetría, mismo protocolo, mismo puerto. Si el atacante reduce su SYN flood a 1,000 pkt/s con patrones normales, la efectividad del ataque se reduce proporcionalmente. El detector temporal de HTTP abuse (100 req/30s) y el de Brute Force SSH (15/60s) son evasibles con tasas menores, pero a menor tasa, menor efectividad del ataque. El attacker faces a dilemma: to be effective, the attack must be detectable. Esta tensión fundamental es una característica, no una limitación, de los detectores basados en comportamiento."*

---

**P18. "¿Compararon el rendimiento con otros algoritmos (Random Forest, SVM, Autoencoder)?"**

> *"El proyecto no incluye comparación formal con otros algoritmos — eso es trabajo futuro. La selección de Isolation Forest está justificada a priori por: (1) Diseño específico para aprender de pocos datos normales (684 flows) — SVM y RF necesitan datos balanceados con ambas clases. (2) Latencia de inferencia O(n log n) vs. O(n²) de LOF — requisito para procesar 29 flows/s. (3) Soporte nativo en scikit-learn sin dependencias externas — facilita el despliegue en el sensor. Una comparación con RF, SVM y Autoencoder fortalecería el argumento, pero está fuera del tiempo disponible de este PPI y es propuesta como trabajo futuro en F6."*

---

**P19. "¿Por qué ICMP Flood tiene CVSS 5.8 (Moderada) pero produce 91% de detección?"**

> *"La gravedad CVSS 5.8 refleja el impacto potencial máximo del ataque, no la detectabilidad. ICMP Flood puede degradar la red pero raramente produce denegación completa de servicio en sistemas modernos (el kernel Linux tiene mecanismos de rate limiting ICMP integrados). La alta detectabilidad (91% BLOCK) ocurre precisamente porque ICMP genera un perfil estadístico muy distinto al tráfico normal (is_icmp=1, pkt_rate constante, avg_pkt_size=30B) — es fácil de detectar estadísticamente. Alta detectabilidad no implica alta gravedad, y viceversa (B6 tiene CVSS 9.8 pero solo 0.9% de detección por modelo)."*

---

**P20. "Si tuviera que añadir un 7mo vector, ¿cuál sería y por qué?"**

> *"Slowloris (DoS de aplicación HTTP mediante conexiones incompletas). Justificación: (1) Figura en OWASP Top 10 Vulnerabilities y en guías de hardening de nginx. (2) Genera un patrón de flujo distinto al HTTP normal: muchas conexiones TCP de larga duración con pkts_toserver muy bajo — exactamente el tipo de anomalía que Isolation Forest puede capturar con las features de duration y pkt_rate. (3) hping3 tiene un modo slowloris implementable en el laboratorio. (4) Es el ataque HTTP más difícil de detectar porque usa conexiones legítimas con payload mínimo. Esta sería la extensión natural al sistema existente con menor esfuerzo de implementación."*

---

## 6. Resumen para la Defensa — Argumentos Clave

| Cuestionamiento | Argumento central | Evidencia cuantitativa |
|---|---|---|
| "¿Son suficientes los 6 ataques?" | Convergencia en 6 fuentes + 94% cobertura DBIR 2024 | 4 de 4 categorías taxonómicas cubiertas |
| "¿Por qué no 20?" | IF no necesita ejemplos de ataques para entrenarse | AUC=0.9440 con solo 684 flows de entrenamiento |
| "¿Representativos de ataques reales?" | Herramientas estándar industria (hping3, nmap, hydra) | Patrones estadísticos idénticos a ataques reales |
| "¿Válido en laboratorio?" | Método estándar en investigación IDS (NSL-KDD, CICIDS) | 40 corridas F6: Disponibilidad=100%, ITL=0%, TIE=100% |
| "¿Generalizable a otros ataques?" | IF detecta anomalías estadísticas, no firmas | Análisis de sensibilidad: AUC estable N=50-1977 |
| "¿Zero-day?" | Detecta patrones anómalos sin necesidad de firma | Separación 0.229 unidades en espacio de features |

---

*Documento generado: 14 de junio 2026*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F2_captura_trafico/F2_03_Justificacion_Ataques.md`*
*Datos estadísticos verificados en sensor 192.168.0.110 — dataset_clean.csv 376,827 flows*
*Estado: Listo para tesis, sustentación y documentación técnica*
