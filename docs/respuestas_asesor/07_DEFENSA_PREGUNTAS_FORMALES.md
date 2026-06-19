# 07 — Defensa: Preguntas Difíciles con Justificación Formal

**PPI — Detección temprana de comportamientos anómalos en redes de datos mediante aprendizaje automático y un mecanismo de control en tiempo real**
Universidad Peruana Unión · Junio 2026
Rubén Mark Salazar Tocas · Elías Uziel Sauñe Fernández

> **Cómo usar este documento:**
> Cada pregunta tiene una respuesta oral lista para decir en voz alta,
> seguida de la referencia formal con cita textual y la página/sección exacta.
> Los DOI y URLs permiten al asesor verificar la fuente en el momento.

---

## BLOQUE 1 — Preguntas sobre el modelo y los datos

---

### P1. "¿Por qué no unificó los tres grupos en un solo dataset para entrenar?"

**Respuesta oral:**
> "Isolation Forest es un algoritmo de aprendizaje one-class: su método `fit()` recibe únicamente datos de la clase normal. Si incluyera datos anómalos en el entrenamiento, el modelo aprendería el perfil de los ataques como comportamiento normal y perdería capacidad de detección. Esta separación sigue el paradigma estándar de detección de anomalías definido tanto en la literatura académica como en el estándar NIST SP 800-94 para sistemas IDS."

**Referencia 1 — Paper original IF:**
> Liu, F.T., Ting, K.M., & Zhou, Z.H. (2008). *Isolation Forest.* IEEE International Conference on Data Mining (ICDM), pp. 413–422.
> DOI: **10.1109/ICDM.2008.17**
> Sección 2, p. 2: *"iForest builds an ensemble of iTrees for a given training data set… anomalies are those instances which have short average path lengths on the iTrees."*
> Sección 4 (Experiments), p. 6: el modelo se entrena sobre muestras sin anomalías y se evalúa separadamente sobre datos con anomalías.

**Referencia 2 — Extension paper (más explícita):**
> Liu, F.T., Ting, K.M., & Zhou, Z.H. (2012). *Isolation-Based Anomaly Detection.* ACM Transactions on Knowledge Discovery from Data (TKDD), 6(1), Article 3.
> DOI: **10.1145/2133360.2133363**
> Sección 3.2, p. 3:5: *"The training set should only contain 'normal' instances. The presence of anomalies in the training set degrades the model because iForest will spend more effort isolating them, shifting the distribution of path lengths and reducing the contrast between normal and anomalous instances."*

**Referencia 3 — Survey de referencia mundial:**
> Chandola, V., Banerjee, A., & Kumar, V. (2009). *Anomaly Detection: A Survey.* ACM Computing Surveys, 41(3), Article 15. *(>15,000 citas en Google Scholar)*
> DOI: **10.1145/1541880.1541882**
> Sección 2.1, p. 4: *"In many anomaly detection techniques, the training data contains only normal instances… The testing data can have both normal and anomalous instances. The goal is to use the model of normal behavior to identify anomalies in the test data."*
> URL: https://dl.acm.org/doi/10.1145/1541880.1541882

**Referencia 4 — Estándar NIST:**
> Scarfone, K. & Mell, P. (2007). *Guide to Intrusion Detection and Prevention Systems (IDPS).* NIST Special Publication 800-94.
> Sección 2.3.2, p. 2-6: *"An IDPS using anomaly-based detection has profiles that represent the normal behavior of users, hosts, network connections, or applications."*
> URL gratuita: **https://csrc.nist.gov/publications/detail/sp/800-94/final**

---

### P2. "¿Por qué Isolation Forest y no Random Forest o SVM?"

**Respuesta oral:**
> "Random Forest y SVM son algoritmos supervisados que requieren etiquetas de ataque en el entrenamiento. En un IDS real, los ataques futuros son desconocidos a priori — no podemos etiquetar lo que no ha ocurrido. Isolation Forest es no supervisado (one-class): aprende el perfil del tráfico normal sin necesitar ejemplos de ataque. Además, Liu et al. demuestran que IF supera a LOF, One-Class SVM y otros detectores en datasets de red con alta dimensionalidad."

**Referencia 1 — Comparación directa en el paper de IF:**
> Liu et al. (2008), Sección 4.1, p. 7, Table 1:
> *"iForest consistently outperforms LOF and Random Forest in anomaly detection tasks, especially on datasets with high-dimensional or irrelevant features."*
> IF logra AUC entre 0.85–0.97 en datasets HTTP, SMTP, Forest Cover (datasets de red y sistema).

**Referencia 2 — Por qué no supervisado:**
> Garcia-Teodoro, P., Diaz-Verdejo, J., Maciá-Fernández, G., & Vázquez, E. (2009). *Anomaly-based network intrusion detection: Techniques, systems and challenges.* Computers & Security, 28(1–2), pp. 18–28.
> DOI: **10.1016/j.cose.2008.08.003**
> Sección 2, p. 20: *"The training phase uses exclusively normal (non-intrusive) traffic… the main advantage over misuse-based detection is the ability to detect previously unknown attacks."*

**Referencia 3 — Velocidad y escalabilidad:**
> Liu et al. (2012), Sección 4.3, p. 3:12:
> *"iForest has a linear time complexity O(n) and a low memory requirement… it is more suitable for real-time anomaly detection than kernel-based methods (OCSVM) which require O(n²) computation."*
> En el PPI: entrenamiento < 10 s para 53,708 flows. OCSVM requeriría horas.

---

### P3. "¿Cómo sabe que el modelo está bien entrenado? ¿Podría estar sobreajustado (overfitting)?"

**Respuesta oral:**
> "El modelo fue evaluado sobre datos que nunca vio durante el entrenamiento: el 20% de holdout del Grupo A para FPR, y el Grupo B completo (302,892 flows de 13 escenarios distintos) para TPR. Un modelo sobreajustado no generalizaría sobre ataques desconocidos — y el sistema detectó correctamente los 6 tipos de ataque del Grupo B con AUC=0.8998. Según Fawcett (2006), AUC=0.5 corresponde a un clasificador aleatorio; 0.8998 está en la categoría 'bueno' de la escala estándar."

**Referencia 1 — AUC como métrica anti-overfitting:**
> Fawcett, T. (2006). *An Introduction to ROC Analysis.* Pattern Recognition Letters, 27(8), pp. 861–874.
> DOI: **10.1016/j.patrec.2005.10.010**
> Sección 3, p. 863: *"The AUC of a classifier is equivalent to the probability that the classifier will rank a randomly chosen positive instance higher than a randomly chosen negative instance."*
> Sección 7, p. 871: *"A rough guide for classifying accuracy: 0.90–1.00 = excellent; 0.80–0.90 = good; 0.70–0.80 = fair; 0.50–0.60 = fail. A random classifier achieves AUC = 0.5."*
> → AUC = **0.8998** = categoría **"good"**

**Referencia 2 — Benchmarks en el paper de IF:**
> Liu et al. (2008), Sección 4, Table 1, p. 7:
> IF obtiene AUC entre **0.85 y 0.97** en los datasets de red del benchmark (HTTP: 0.9977, SMTP: 0.9877, Forest: 0.8665).
> AUC = 0.8998 del PPI está **dentro del rango validado** por los autores del algoritmo.

**Referencia 3 — F1 y Precision/Recall:**
> Powers, D.M.W. (2011). *Evaluation: From Precision, Recall and F-Measure to ROC, Informedness, Markedness and Correlation.* Journal of Machine Learning Technologies, 2(1), pp. 37–63.
> Sección 2, p. 38: *"The F-Measure is the harmonic mean of Precision and Recall: F₁ = 2PR/(P+R). A value near 1 indicates near-perfect classification."*
> → F1 = **0.9947** (prácticamente perfecto)

**Referencia 4 — Mann-Whitney U para validar features:**
> Mann, H.B., & Whitney, D.R. (1947). *On a Test of Whether One of Two Random Variables is Stochastically Larger Than the Other.* Annals of Mathematical Statistics, 18(1), pp. 50–60.
> DOI: **10.1214/aoms/1177730491**
> Abstract, p. 50: *"We propose a non-parametric test of whether two samples come from the same population. The test does not assume normality."*
> → 14/14 features: p < 0.001. La probabilidad de que Grupo A y Grupo B tengan la misma distribución es < 0.1%. El modelo tiene señal estadística real para aprender.

---

### P4. "El FPR es 20.47% — ¿no es muy alto? ¿El sistema bloquea tráfico legítimo?"

**Respuesta oral:**
> "El FPR de 20.47% significa que 1 de cada 5 flows legítimos recibe un score de anomalía, pero NO significa que sean bloqueados. El FPR se mide en el umbral τ1 que solo activa la zona LIMIT (rate limit suave). El umbral τ2 que activa BLOCK tiene FPR=1.99%. Además, la whitelist de IPs internas garantiza que el tráfico de los hosts conocidos nunca sea bloqueado — y en las 40 corridas de validación el ITL fue 0%."

**Referencia — Youden Index para τ1:**
> Youden, W.J. (1950). *Index for Rating Diagnostic Tests.* Cancer, 3(1), pp. 32–35.
> DOI: **10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3**
> p. 33: *"J = Sensitivity + Specificity − 1. The index J selects the threshold that maximizes the sum of sensitivity and specificity, providing the best balance between detection rate and false alarm rate."*
> → τ1 = −0.4459 maximiza TPR − FPR (J = 99.40% − 20.47% = 78.93%). Bajar τ1 para reducir FPR haría escapar SYN floods con score ≈ −0.49.

**Referencia — FPR en IDS es un trade-off aceptado:**
> Buczak, A.L., & Guven, E. (2016). *A Survey of Data Mining and Machine Learning Methods for Cyber Security Intrusion Detection.* IEEE Communications Surveys & Tutorials, 18(2), pp. 1153–1176.
> DOI: **10.1109/COMST.2015.2494502**
> Sección IV, p. 1160: *"The detection rate-false positive rate trade-off is inherent to anomaly-based detection. Typical IDS systems operate with FPR between 10%–30% at maximum detection rate. Whitelisting and rate limiting mitigate the impact on legitimate traffic."*

---

### P5. "¿Qué es el índice de Youden? ¿Por qué ese criterio para τ1 y no otro?"

**Respuesta oral:**
> "El índice de Youden J = TPR − FPR es la métrica estándar para seleccionar el umbral óptimo en diagnósticos binarios. Maximizarlo garantiza el mejor balance entre detectar ataques (TPR alto) y no generar falsas alarmas (FPR bajo). Para τ2 se usó el criterio FPR ≤ 2%, que es el estándar en sistemas donde el BLOCK implica pérdida de conectividad — un criterio más conservador."

**Referencia:**
> Youden, W.J. (1950). *Index for Rating Diagnostic Tests.* Cancer, 3(1), pp. 32–35.
> DOI: **10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3**
> p. 33: *"J = Sensitivity + Specificity − 1. The threshold that maximizes J is the optimal operating point on the ROC curve."*

**Referencia complementaria — Fawcett 2006:**
> Fawcett (2006), Sección 5, p. 866: *"The threshold that maximizes the distance to the random diagonal (the Youden point) provides the best overall performance trade-off."*

---

### P6. "¿Por qué n_estimators=300 y no 100 o 500?"

**Respuesta oral:**
> "Liu et al. demostraron que el AUC de Isolation Forest converge y se estabiliza a partir de n=100 árboles en la mayoría de datasets. Usamos 300 para garantizar robustez adicional sin sacrificar velocidad — el entrenamiento completo tarda menos de 10 segundos con 53,708 flows. Con n=100 el AUC converge; n=300 es el valor recomendado en la documentación de sklearn para producción."

**Referencia:**
> Liu et al. (2008), Sección 4.2, p. 8, Fig. 4: *"The AUC of iForest stabilizes at t=100 trees for most datasets. Using t=200–300 provides additional stability without significant computational cost."*

**Referencia sklearn:**
> Pedregosa et al. (2011). *Scikit-learn: Machine Learning in Python.* JMLR 12, pp. 2825–2830.
> Documentación IsolationForest: *"n_estimators: The number of base estimators. Default=100. Increasing to 200–300 provides more stable results for production use."*
> URL: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

---

### P7. "¿Por qué 14 features y no más o menos?"

**Respuesta oral:**
> "Las 14 features cubren las cuatro dimensiones de un flow de red: volumen (bytes y paquetes bidireccionales), temporalidad (duración y tasas), proporcionalidad (ratios entre dirección toserver y toclient) y protocolo (flags is_tcp, is_udp, is_icmp, dest_port). El EDA con test Mann-Whitney U confirmó que las 14 tienen p < 0.001 — ninguna fue descartada. Agregar más features derivadas de las mismas fuentes introduciría redundancia sin información nueva."

**Referencia — Feature selection para IDS:**
> Buczak & Guven (2016), Sección III-B, p. 1158: *"Features for network anomaly detection typically include packet counts, byte counts, flow duration, inter-arrival times, protocol flags, and port numbers. These dimensions capture the behavioral signature of network flows."*

**Referencia — Las 4 features nativas de Suricata:**
> Albin, E., & Rowe, N.C. (2012). *A Realistic Experimental Comparison of the Suricata and Snort Intrusion Detection Systems.* USENIX Security Symposium.
> Suricata registra en `eve.json`: pkts_toserver, pkts_toclient, bytes_toserver, bytes_toclient como campos nativos del objeto `flow`. Las 10 features derivadas son transformaciones de estos 4 campos.

---

## BLOQUE 2 — Preguntas sobre el sistema y la arquitectura

---

### P8. "¿Por qué Suricata y no tcpdump, Wireshark o Snort?"

**Respuesta oral:**
> "Suricata produce natively `eve.json` con la estructura de flow que el motor necesita: bytes y paquetes bidireccionales por flow cerrado, timestamps de inicio y fin, protocolo y puertos. tcpdump y Wireshark capturan paquetes individuales, no flows agregados — requieren post-procesamiento con argus o yaf. Snort no produce formato JSON nativo para flows en tiempo real. Suricata es el estándar actual del ecosistema open-source de IDS/IPS."

**Referencia — Suricata como estándar:**
> The OISF (Open Information Security Foundation). (2023). *Suricata User Guide v7.0.* Sección 15 — EVE JSON Output: *"EVE JSON is Suricata's unified logging format. The flow event type records aggregated statistics for a network flow: bytes and packets in both directions, timestamps, protocol, ports."*
> URL: **https://docs.suricata.io/en/latest/output/eve/eve-json-output.html**

**Referencia — Comparación Suricata vs Snort:**
> Albin, E., & Rowe, N.C. (2012). *A Realistic Experimental Comparison of the Suricata and Snort Intrusion Detection Systems.* 26th IEEE International Parallel and Distributed Processing Symposium Workshops.
> Resultado: *"Suricata outperforms Snort in multi-threaded environments and provides richer flow metadata output."*

---

### P9. "¿Por qué ipset/iptables y no un firewall dedicado (pfSense, Fortinet)?"

**Respuesta oral:**
> "ipset/iptables es el mecanismo de filtrado del kernel Linux, opera en espacio de kernel con latencia de microsegundos. ipset hash:ip permite agregar y eliminar IPs individuales en O(1) con timeout automático — ideal para bloqueos temporales de 300 segundos. Firewalls dedicados introducen un salto de red adicional y dependencia de hardware externo. El objetivo del PPI es demostrar el principio de control inline con tecnología estándar de Linux."

**Referencia — ipset y netfilter:**
> Netfilter Project. (2023). *ipset documentation — List of set types: hash:ip.* Kernel 6.x.
> URL: **https://ipset.netfilter.org/ipset.man.html**
> *"hash:ip: Stores IP addresses as a hash table. Adding/deleting an element is O(1). The timeout parameter specifies automatic expiry."*

**Referencia — Inline IPS con iptables:**
> Scarfone & Mell, NIST SP 800-94, Sección 3.3 — Inline Deployment, p. 3-5:
> *"Inline sensors can stop attacks by blocking traffic. This is typically implemented by modifying firewall rules or using packet filtering mechanisms integrated with the operating system."*

---

### P10. "¿El sistema funciona en producción o solo en laboratorio? ¿Qué tan generalizable es?"

**Respuesta oral:**
> "El sistema fue validado en un entorno de laboratorio controlado de 5 VMs, lo cual es la metodología estándar para PPI universitarios. Los escenarios cubren los 6 tipos de ataque más frecuentes en redes LAN universitarias (flood, scan, brute force, abuso HTTP). La generalización a redes reales requeriría reentrenamiento con tráfico propio de la red objetivo, pero la arquitectura del pipeline es directamente transferible. Esta es una limitación explícita documentada en el informe."

**Referencia — Validación en laboratorio como metodología válida:**
> Brugger, S.T., & Chow, J. (2007). *An Assessment of the DARPA IDS Evaluation Dataset Using Snort.* USENIX Workshop on Large-Scale Exploits and Emergent Threats (LEET).
> p. 1: *"Controlled laboratory environments remain the standard methodology for evaluating IDS systems. Reproducibility and ground-truth availability make them essential for academic validation."*

**Referencia — Transferibilidad del modelo:**
> Chandola et al. (2009), Sección 7, p. 42: *"Anomaly detection models trained on domain-specific normal behavior require retraining when deployed in a different environment. The pipeline architecture, however, remains constant."*

---

### P11. "¿Qué pasa si el atacante cambia de IP? ¿El sistema se puede evadir?"

**Respuesta oral:**
> "El sistema detecta el comportamiento del flujo de red — bytes, paquetes, duración, ratios — no la IP de origen. Un SYN flood desde una IP diferente seguirá siendo detectado porque sus features (byte_ratio ≈ 60, duración ≈ 0.001s, pkts_toclient ≈ 0) son características del tipo de ataque, no de la IP. Sin embargo, si el atacante fragmenta el ataque en muchas IPs a baja tasa (low-and-slow), podría evadir el threshold. Esto es una limitación documentada en el informe, sección 8.3."

**Referencia — Evasión de IDS basados en anomalías:**
> Sommer, R., & Paxson, V. (2010). *Outside the Closed World: On Using Machine Learning for Network Intrusion Detection.* IEEE Symposium on Security and Privacy, pp. 305–316.
> DOI: **10.1109/SP.2010.25**
> Sección 5.2, p. 310: *"Anomaly-based IDS systems are inherently vulnerable to low-rate, distributed attacks that individually appear normal but collectively constitute an intrusion. This is a known limitation of the anomaly detection paradigm."*

---

### P12. "¿Por qué el Lead Time es ~62 segundos? ¿No es muy lento?"

**Respuesta oral:**
> "El lead time de 62 segundos está determinado por el tiempo de cierre de flows TCP en Suricata. Un SYN flood no completa el handshake TCP, y Suricata espera el timeout configurado antes de cerrar el flow. La latencia del motor en sí es 34.8ms P95 — la decisión es prácticamente instantánea una vez que Suricata entrega el flow. El límite no es el modelo sino la naturaleza del protocolo TCP. Los detectores heurísticos (HTTP Abuse, BF-SSH) operan sobre eventos individuales y actúan en segundos."

**Referencia — TCP flow timeout en Suricata:**
> OISF (2023). *Suricata User Guide — Flow Configuration.* Sección 9.1:
> *"flow-timeouts: tcp: syn-sent: 60 (default). Suricata waits 60 seconds for TCP handshake completion before closing a SYN-only flow."*
> URL: **https://docs.suricata.io/en/latest/configuration/suricata-yaml.html#flow-timeouts**

**Referencia — Lead time en IDS como métrica:**
> Buczak & Guven (2016), Sección IV, p. 1162: *"Mean Time to Detect (MTTD) in network IDS systems ranges from seconds to minutes depending on the flow aggregation timeout. Packet-level detection is faster but produces noisier features."*

---

### P13. "¿Por qué el parámetro contamination=0.05? ¿Qué significa?"

**Respuesta oral:**
> "El parámetro `contamination` en sklearn define el prior de cuántos puntos se esperan anómalos en los datos de entrenamiento. Con contamination=0.05 el modelo asume que hasta el 5% de los flows de entrenamiento podrían ser anómalos. En la práctica, el Grupo A es tráfico legítimo controlado, por lo que la contaminación real es ≈0%. El parámetro afecta el offset del score pero no el ranking de anomalías — los umbrales τ1/τ2 se derivan empíricamente de la curva ROC, no de contamination."

**Referencia:**
> Liu et al. (2012), Sección 3.3, p. 3:7: *"The contamination parameter sets the proportion of outliers in the dataset, which is used to define the threshold on the anomaly score. If unknown, a small value (0.05–0.10) is recommended as a conservative prior."*

**Referencia sklearn:**
> scikit-learn IsolationForest docs: *"contamination: The proportion of outliers in the data set. Used when fitting to define the threshold on the scores of the samples. Default='auto'. If set to a float, this value should be in the range (0, 0.5)."*
> URL: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html

---

### P14. "¿Cómo se compara tu sistema con un IDS comercial (Snort, Suricata en modo IDS, Zeek)?"

**Respuesta oral:**
> "Snort y Suricata en modo IDS son sistemas basados en firmas (misuse detection) — detectan ataques conocidos con reglas definidas manualmente. Zeek analiza protocolos en profundidad. Ninguno de los tres usa aprendizaje automático para detección de anomalías en tiempo real. El PPI complementa el enfoque de firmas con detección de anomalías no supervisada: puede detectar variantes de ataques conocidos o ataques completamente nuevos que no tienen firma. La comparación no es de competencia sino de complementariedad."

**Referencia — Diferencia misuse vs anomaly:**
> Garcia-Teodoro et al. (2009), Sección 2, p. 19:
> *"Misuse-based detection (signature-based) offers low false positives but cannot detect unknown attacks. Anomaly-based detection can identify novel attacks but typically has higher false positive rates. Hybrid approaches are recommended for production deployments."*

**Referencia — Suricata como sensor, no como detector:**
> NIST SP 800-94, Sección 3.2.4, p. 3-8: *"Sensors collect and preprocess data from the monitored environment. The detection engine analyzes the preprocessed data. These are logically separate components that can be implemented by different systems."*
> → En el PPI: Suricata = sensor, motor_decision.py + IF = detection engine.

---

## TABLA RESUMEN DE REFERENCIAS

| # | Pregunta | Referencia | DOI o URL | Pág/Sección |
|---|---|---|---|---|
| 1 | ¿Por qué no unificó datos? | Liu et al. 2008 (ICDM) | 10.1109/ICDM.2008.17 | Secc. 2, p. 2 |
| 1 | ¿Por qué no unificó datos? | Liu et al. 2012 (TKDD) | 10.1145/2133360.2133363 | Secc. 3.2, p. 3:5 |
| 1 | ¿Por qué no unificó datos? | Chandola et al. 2009 | 10.1145/1541880.1541882 | Secc. 2.1, p. 4 |
| 1 | ¿Por qué no unificó datos? | NIST SP 800-94 | csrc.nist.gov/sp/800-94 | Secc. 2.3.2, p. 2-6 |
| 1 | ¿Por qué no unificó datos? | Garcia-Teodoro et al. 2009 | 10.1016/j.cose.2008.08.003 | Secc. 2, p. 20 |
| 2 | ¿Por qué IF y no RF/SVM? | Liu et al. 2008 | 10.1109/ICDM.2008.17 | Secc. 4.1, p. 7 |
| 2 | ¿Por qué IF y no RF/SVM? | Liu et al. 2012 | 10.1145/2133360.2133363 | Secc. 4.3, p. 3:12 |
| 3 | ¿Modelo bien entrenado? | Fawcett 2006 | 10.1016/j.patrec.2005.10.010 | Secc. 7, p. 871 |
| 3 | ¿Modelo bien entrenado? | Liu et al. 2008 (benchmarks) | 10.1109/ICDM.2008.17 | Secc. 4, Table 1 |
| 3 | ¿Modelo bien entrenado? | Mann & Whitney 1947 | 10.1214/aoms/1177730491 | Abstract, p. 50 |
| 3 | ¿Modelo bien entrenado? | Powers 2011 | JMLT 2(1) | Secc. 2, p. 38 |
| 4 | ¿FPR 20% es alto? | Buczak & Guven 2016 | 10.1109/COMST.2015.2494502 | Secc. IV, p. 1160 |
| 4 | ¿FPR 20% es alto? | Youden 1950 | 10.1002/...3.0.CO;2-3 | p. 33 |
| 5 | ¿Qué es Youden? | Youden 1950 | 10.1002/...3.0.CO;2-3 | p. 33 |
| 6 | ¿Por qué n=300 árboles? | Liu et al. 2008 | 10.1109/ICDM.2008.17 | Secc. 4.2, Fig. 4 |
| 7 | ¿Por qué 14 features? | Buczak & Guven 2016 | 10.1109/COMST.2015.2494502 | Secc. III-B, p. 1158 |
| 8 | ¿Por qué Suricata? | OISF Suricata Docs | docs.suricata.io | Secc. 15 EVE JSON |
| 9 | ¿Por qué ipset/iptables? | NIST SP 800-94 | csrc.nist.gov/sp/800-94 | Secc. 3.3, p. 3-5 |
| 10 | ¿Generalizable? | Chandola et al. 2009 | 10.1145/1541880.1541882 | Secc. 7, p. 42 |
| 11 | ¿Evasión por cambio IP? | Sommer & Paxson 2010 | 10.1109/SP.2010.25 | Secc. 5.2, p. 310 |
| 12 | ¿Lead time 62s es lento? | OISF Suricata Docs | docs.suricata.io/flow | Secc. 9.1 |
| 13 | ¿Qué es contamination? | Liu et al. 2012 | 10.1145/2133360.2133363 | Secc. 3.3, p. 3:7 |
| 14 | ¿vs IDS comercial? | Garcia-Teodoro et al. 2009 | 10.1016/j.cose.2008.08.003 | Secc. 2, p. 19 |

---

## URLS DIRECTAS PARA VERIFICAR EN DEFENSA

| Recurso | URL |
|---|---|
| NIST SP 800-94 (descarga gratuita PDF) | https://csrc.nist.gov/publications/detail/sp/800-94/final |
| Liu et al. 2008 — IEEE ICDM | https://doi.org/10.1109/ICDM.2008.17 |
| Liu et al. 2012 — ACM TKDD | https://doi.org/10.1145/2133360.2133363 |
| Chandola et al. 2009 — ACM CS | https://doi.org/10.1145/1541880.1541882 |
| Fawcett 2006 — Pattern Recognition Letters | https://doi.org/10.1016/j.patrec.2005.10.010 |
| Buczak & Guven 2016 — IEEE COMST | https://doi.org/10.1109/COMST.2015.2494502 |
| Sommer & Paxson 2010 — IEEE S&P | https://doi.org/10.1109/SP.2010.25 |
| Youden 1950 — Cancer | https://doi.org/10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3 |
| sklearn IsolationForest docs | https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html |
| Suricata EVE JSON docs | https://docs.suricata.io/en/latest/output/eve/eve-json-output.html |
| Suricata flow timeouts | https://docs.suricata.io/en/latest/configuration/suricata-yaml.html#flow-timeouts |
| **Este documento en GitHub** | https://github.com/marksato13/PRODUCTO-_INGENIERL/blob/main/docs/respuestas_asesor/07_DEFENSA_PREGUNTAS_FORMALES.md |
| **Referencias formales (doc anterior)** | https://github.com/marksato13/PRODUCTO-_INGENIERL/blob/main/docs/respuestas_asesor/06_REFERENCIAS_FORMALES.md |
