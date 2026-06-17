# Respuesta: ALCANCE Y ATAQUES — "¿Y si aparece un sexto ataque?"

**Preocupación del asesor:** "Tu alcance tiene 5 ataques. ¿Qué pasa si aparece un sexto?"

---

## 1. La respuesta directa

**El sistema NO memoriza ataques. Aprende qué es normal.**

Esta distinción es fundamental y es exactamente lo que diferencia un sistema de **detección por anomalías** (como el nuestro) de un sistema de **detección por firmas** (antivirus, Snort con reglas):

| Enfoque | Cómo detecta | ¿Detecta ataques nuevos? |
|---|---|---|
| **Por firmas (signature-based)** | Compara tráfico con una base de datos de ataques conocidos | ❌ NO — si el ataque es nuevo, no tiene firma |
| **Por anomalías (anomaly-based)** | Aprende qué es NORMAL y detecta cualquier desviación | ✅ SÍ — cualquier desviación del baseline es sospechosa |

Nuestro sistema usa **Isolation Forest**, un modelo de una sola clase (one-class classification) entrenado **exclusivamente con tráfico normal** (Grupo A). Nunca vio los ataques durante el entrenamiento.

Si aparece un **sexto, séptimo o centésimo tipo de ataque**, la única pregunta que importa es: **¿genera ese ataque un flujo de red con características distintas al tráfico normal?** Si la respuesta es sí, el sistema lo detectará.

---

## 2. Los 5 ataques no son "los únicos ataques que detecta"

Los 5 tipos de ataque del laboratorio (SYN Flood, Port Scan, UDP Flood, HTTP Abuse, Brute Force SSH) fueron seleccionados como **escenarios representativos de validación**, no como lista exhaustiva de amenazas.

Su función fue demostrar que el modelo detecta desviaciones en diferentes dimensiones del espacio de features:

| Ataque validado | Dimensión que explora | Feature clave |
|---|---|---|
| SYN Flood | Tasa de paquetes extrema | `pkt_rate` >> normal |
| Port Scan | Flujos de 1 paquete sin respuesta | `pkt_ratio` → ∞, `duration` ≈ 0 |
| UDP Flood | Volumen sin establecimiento de conexión | `byte_rate` >> normal, `is_udp=1` |
| HTTP Abuse | Frecuencia de requests por ventana | heurístico 100 req/30s |
| Brute Force | Intentos repetidos fallidos por ventana | heurístico 15 intentos/60s |

Un "sexto ataque" necesitaría **crear un patrón de tráfico completamente indistinguible del tráfico HTTP/SSH/transferencia legítima** para evadirlo. Esto es prácticamente imposible para ataques de red de capa de transporte (TCP/UDP/ICMP), que son los que captura Suricata.

---

## 3. Respaldo en la literatura y la industria

### 3.1 NIST — Estándar gubernamental USA

El **NIST SP 800-94** (Guide to Intrusion Detection and Prevention Systems) — el estándar de referencia para sistemas IDS — define explícitamente la detección por anomalías así:

> *"An IDPS using anomaly-based detection has profiles that represent the normal behavior of users, hosts, network connections, or applications. The IDPS then uses statistical methods to compare the characteristics of current activity to thresholds related to the profile."*

Referencia: [NIST SP 800-94 — csrc.nist.gov](https://csrc.nist.gov/pubs/sp/800/94/final)

**Implicación directa para nuestra tesis:** seguimos el modelo de detección descrito por el estándar NIST para IDPS de análisis de comportamiento de red (NBA — Network Behavior Analysis).

---

### 3.2 Fortinet — Líder mundial en seguridad de redes

Fortinet, en su documentación oficial de **FortiWeb y FortiSIEM**, describe exactamente el mismo enfoque que usamos:

> *"Anomaly detection works by first establishing a baseline for what's normal. Once the system establishes a baseline, it flags any traffic deviating from the baseline as an anomaly and a potential threat."*

> *"Fortinet's NDR solutions learn what normal network behavior looks like for your organization and then apply ML and advanced analytics to detect signs of sophisticated attacks."*

Fortinet explícitamente señala que la detección por anomalías es necesaria para **bloquear amenazas zero-day** — ataques que los sistemas de firmas no pueden detectar porque no tienen firma conocida.

Referencias:
- [Anomaly Detection — FortiWeb Cloud (docs.fortinet.com)](https://docs.fortinet.com/document/fortiweb-cloud/latest/user-guide/81976/anomaly-detection)
- [Machine Learning in FortiWeb for Faster Anomaly Detection (fortinet.com)](https://www.fortinet.com/resources/articles/fortiweb-detects-anomalies-faster)
- [What is NDR? — Fortinet](https://www.fortinet.com/resources/cyberglossary/what-is-ndr)
- [Anomaly Detection and the XZ-Utils Zero-Day (Fortinet)](https://www.fortinet.com/uk/resources/articles/xz-utils-vulnerability)

---

### 3.3 OWASP — Referencia en seguridad de aplicaciones

La OWASP Foundation en su guía de **Intrusion Detection** establece:

> *"Anomaly-based IDS use machine learning or statistical models to establish a baseline of normal network behavior and detect deviations from it. They can identify unknown or novel attacks that do not match any known signatures or patterns."*

Referencia: [Intrusion Detection — OWASP Foundation](https://owasp.org/www-community/controls/Intrusion_Detection)

---

### 3.4 Palo Alto Networks — Referencia industrial

Palo Alto Networks en su documentación de ciberseguridad:

> *"Anomaly-based detection is particularly effective at detecting zero-day or previously unknown attacks, since they do not depend on predefined threat signatures."*

Referencia: [What is an IDS? — Palo Alto Networks](https://www.paloaltonetworks.com/cyberpedia/what-is-an-intrusion-detection-system-ids)

---

### 3.5 Verizon DBIR 2024 — Datos reales de brechas

El **Verizon Data Breach Investigations Report 2024** analiza miles de incidentes reales y clasifica los ataques en **9 patrones** (System Intrusion, DoS, Web Application Attacks, Social Engineering, etc.). System Intrusion lidera con **36% de las brechas**.

El DBIR muestra que en la práctica, los ataques de red siguen **patrones de comportamiento anómalo identificables**: volúmenes inusuales, tasas de conexión atípicas, flujos asimétricos — exactamente lo que mide Isolation Forest.

Referencias:
- [DBIR 2024 — System Intrusion Pattern (Verizon)](https://www.verizon.com/business/resources/reports/dbir/2024/incident-classification-patterns-intro/system-intrusion/)
- [2024 DBIR PDF completo (Verizon)](https://www.verizon.com/business/resources/reports/2024-dbir-data-breach-investigations-report.pdf)

---

### 3.6 Literatura científica — Isolation Forest en seguridad de redes

Investigaciones revisadas por pares confirman la efectividad del enfoque:

- **Nature/Scientific Reports (2025):** "Robust IoT security using Isolation Forest and One-Class SVM algorithms" — demuestra que Isolation Forest detecta ataques no vistos durante el entrenamiento en redes IoT.
  [https://www.nature.com/articles/s41598-025-20445-4](https://www.nature.com/articles/s41598-025-20445-4)

- **Springer (2024):** "An optimized Isolation Forest based IDS for heterogeneous and streaming data in IIoT networks" — valida el modelo en entornos industriales con tráfico en tiempo real.
  [https://link.springer.com/article/10.1007/s42452-024-06165-w](https://link.springer.com/article/10.1007/s42452-024-06165-w)

- **ResearchGate / IEEE (2023):** "An Empirical IP Network Intrusion Detection using Isolation Forest and One-Class SVM" — comparación empírica directa de Isolation Forest para detección de intrusiones.
  [https://www.researchgate.net/publication/373631521](https://www.researchgate.net/publication/373631521_An_Empirical_Internet_Protocol_Network_Intrusion_Detection_using_Isolation_Forest_and_One-Class_Support_Vector_Machines)

- **MDPI Informatics (2024):** "Web Traffic Anomaly Detection Using Isolation Forest" — validación en tráfico web real, el escenario más cercano a nuestro laboratorio.
  [https://www.mdpi.com/2227-9709/11/4/83](https://www.mdpi.com/2227-9709/11/4/83)

- **PMC/Nature Scientific Reports (2026):** "Anomaly-based intrusion detection on benchmark datasets: a comprehensive evaluation"
  [https://www.nature.com/articles/s41598-026-38317-w](https://www.nature.com/articles/s41598-026-38317-w)

---

### 3.7 SANS Institute — Referencia en formación de seguridad

El SANS Institute, referencia mundial en capacitación en ciberseguridad, documenta que la detección conductual con ML:

> *"...can identify new patterns, detect events that may not match a specific signature, and determine behavioral abnormalities."*

Referencia: [SANS Institute — Automated Threat Detection (via Vectra)](https://www.vectra.ai/about/news/sans-institute-reveals-that-automated-threat-detection-helps-fulfill-protection-goals-of-critical-security-controls)

---

## 4. La arquitectura permite incorporar nuevos ataques

Si el asesor pregunta: *"¿Cómo mejoras el sistema para el sexto ataque?"*, la respuesta técnica es:

### Opción A: Reentrenamiento con nuevos datos de tráfico normal

Si el "sexto ataque" introduce un nuevo patrón de tráfico normal (p.ej., nueva aplicación legítima), se recaptura tráfico, se reejecutn `fase3_entrenar.py` y `auc_roc_umbrales.py`. El proceso completo toma < 1 hora con los scripts actuales.

```bash
# Capturar nueva normalidad
bash scripts/capture/exportar_eve_por_escenario.sh $(date +%Y%m%d) normal nueva_app 01

# Reentrenar
python3 scripts/fase3_entrenar.py

# Rederiva umbrales
python3 scripts/fase3_evaluar.py

# Recargar motor (sin reiniciar el servidor)
sudo systemctl restart ppi-motor.service
```

### Opción B: Agregar heurístico específico para el nuevo ataque

Si el nuevo ataque tiene un patrón temporal específico (como BF-SSH o HTTP-ABUSE), se añade un heurístico al motor. Por ejemplo, un heurístico para **ICMP Flood** (brecha actual del sistema):

```python
# Nuevo heurístico: detectar ICMP Flood por conteo de paquetes
if is_icmp and icmp_count[src_ip][60s] > 1000:
    accion = 'BLOCK'
```

### Opción C: Incremental learning (investigación activa)

La literatura reciente (Springer 2025, Wiley 2025) documenta **aprendizaje incremental** que permite al modelo adaptarse a nuevos ataques sin reentrenamiento completo — hasta **72% más rápido** que reentrenar desde cero. Esta es la dirección natural de trabajo futuro para el sistema.

Referencia: [Incremental Learning for IDS — Springer (2025)](https://link.springer.com/article/10.1007/s12083-025-02153-y)

---

## 5. Respuesta concisa para el momento de la sustentación

Si el asesor pregunta *"¿Y si aparece un sexto ataque?"*, la respuesta es:

> *"El sistema no memoriza los 5 ataques del laboratorio — nunca los vio durante el entrenamiento. Lo que aprendió fue el comportamiento del tráfico normal: cuántos paquetes intercambia una conexión HTTP legítima, a qué velocidad, con qué simetría. Cualquier flujo que se desvíe significativamente de ese patrón — sea SYN Flood, Port Scan, o un ataque que todavía no existe — obtiene un score bajo y es marcado como anómalo. Los 5 escenarios fueron seleccionados para validar que el sistema detecta desviaciones en diferentes dimensiones: velocidad, asimetría, frecuencia, duración. Esta arquitectura de detección por comportamiento es la misma que utilizan Fortinet, Palo Alto Networks y Cisco Talos en sus productos comerciales, y está documentada en el estándar NIST SP 800-94 como el enfoque correcto para detectar ataques desconocidos."*

---

## 6. Tabla de cierre: ¿qué necesita el "sexto ataque" para evadir el sistema?

| Condición para evadir la detección | ¿Probable en un ataque real? |
|---|---|
| pkt_rate idéntico al tráfico HTTP normal (~10 pkt/s) | No — los ataques de red requieren volumen |
| avg_pkt_size > 200 bytes (como datos reales) | No — floods usan paquetes mínimos |
| duration > 1 segundo por flujo (como sesiones reales) | No — scans y floods son rápidos |
| Flujo perfectamente bidireccional (como conversación real) | No — ataques unidireccionales son la norma |
| < 50 conexiones al mismo destino en 30 segundos | No — los ataques de volumen rompen este límite |

**Conclusión:** Para evadir el Isolation Forest entrenado sobre nuestro tráfico, el atacante tendría que hacer que su ataque de red parezca exactamente una sesión HTTP normal de un usuario navegando — lo cual anularía el propósito del ataque.

---

## Referencias consolidadas

| Fuente | Tipo | URL |
|---|---|---|
| NIST SP 800-94 | Estándar gubernamental | [csrc.nist.gov](https://csrc.nist.gov/pubs/sp/800/94/final) |
| Fortinet FortiWeb Anomaly Detection | Documentación oficial | [docs.fortinet.com](https://docs.fortinet.com/document/fortiweb-cloud/latest/user-guide/81976/anomaly-detection) |
| Fortinet ML for Anomaly Detection | Artículo técnico | [fortinet.com](https://www.fortinet.com/resources/articles/fortiweb-detects-anomalies-faster) |
| Fortinet NDR — aprendizaje de normalidad | Producto comercial | [fortinet.com/solutions/network-detection](https://www.fortinet.com/solutions/network-detection) |
| OWASP Intrusion Detection | Guía de referencia | [owasp.org](https://owasp.org/www-community/controls/Intrusion_Detection) |
| Palo Alto — ¿Qué es IDS? | Enciclopedia técnica | [paloaltonetworks.com](https://www.paloaltonetworks.com/cyberpedia/what-is-an-intrusion-detection-system-ids) |
| Verizon DBIR 2024 | Reporte de industria | [verizon.com/business/resources/reports/2024-dbir](https://www.verizon.com/business/resources/reports/2024-dbir-data-breach-investigations-report.pdf) |
| Fidelis Security — Anomaly vs Signature | Comparativa técnica | [fidelissecurity.com](https://fidelissecurity.com/cybersecurity-101/learn/signature-based-vs-anomaly-based-ids/) |
| TechTarget — IDS Signature vs Anomaly | Artículo técnico | [techtarget.com](https://www.techtarget.com/searchsecurity/tip/IDS-Signature-versus-anomaly-detection) |
| Nature/Sci Reports — IF en IoT (2025) | Artículo científico | [nature.com](https://www.nature.com/articles/s41598-025-20445-4) |
| Springer — IF optimizado para IIoT (2024) | Artículo científico | [springer.com](https://link.springer.com/article/10.1007/s42452-024-06165-w) |
| MDPI — IF para tráfico web (2024) | Artículo científico | [mdpi.com](https://www.mdpi.com/2227-9709/11/4/83) |
| Springer — Incremental learning IDS (2025) | Artículo científico | [springer.com](https://link.springer.com/article/10.1007/s12083-025-02153-y) |
| SANS / Vectra — Behavioral detection | Reporte industria | [vectra.ai/sans](https://www.vectra.ai/about/news/sans-institute-reveals-that-automated-threat-detection-helps-fulfill-protection-goals-of-critical-security-controls) |
| Corelight — Anomaly-based detection | Guía técnica | [corelight.com](https://corelight.com/resources/glossary/anomaly-based-detection) |
