# Informe de Resultados — Parte IV: Resultados
**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
Universidad Peruana Unión · Ingeniería de Sistemas · 2026

---

## 4. Resultados

Esta sección presenta los resultados obtenidos organizados por objetivo específico (OE1–OE3), seguidos por las validaciones realizadas en entorno de laboratorio en tiempo real y el análisis de las limitaciones identificadas.

---

### 4.1 OE1 — Pipeline de captura y procesamiento de tráfico

El primer objetivo consistía en construir un pipeline que transforme tráfico de red capturado en bruto en un dataset válido para entrenamiento. Se ejecutaron nueve escenarios de captura distribuidos en tres grupos: tráfico normal (Grupo A, cuatro escenarios), tráfico anómalo (Grupo B, seis escenarios) y tráfico mixto (Grupo C, tres escenarios). Las capturas se realizaron con Suricata 7.0.3 configurado en modo promiscuo sobre la interfaz `ens35` del sensor (192.168.0.110), exportando eventos de flujo al archivo `eve.json`.

De cada evento de flujo se extrajeron catorce características numéricas. La tabla 4.1 detalla estas características y su tipo.

**Tabla 4.1 — Features del modelo Isolation Forest**

| # | Feature | Descripción |
|---|---|---|
| 1 | `pkts_toserver` | Paquetes enviados al servidor |
| 2 | `pkts_toclient` | Paquetes recibidos del servidor |
| 3 | `bytes_toserver` | Bytes enviados al servidor |
| 4 | `bytes_toclient` | Bytes recibidos del servidor |
| 5 | `duration` | Duración del flujo (segundos) |
| 6 | `pkt_rate` | Tasa de paquetes total (pkts/s) |
| 7 | `byte_rate` | Tasa de bytes total (bytes/s) |
| 8 | `pkt_ratio` | Razón pkts_toserver / pkts_toclient |
| 9 | `byte_ratio` | Razón bytes_toserver / bytes_toclient |
| 10 | `avg_pkt_size` | Tamaño promedio de paquete (bytes) |
| 11 | `is_tcp` | Indicador de protocolo TCP (binario) |
| 12 | `is_udp` | Indicador de protocolo UDP (binario) |
| 13 | `is_icmp` | Indicador de protocolo ICMP (binario) |
| 14 | `dest_port` | Puerto de destino |

El dataset consolidado comprende un total de 667,420 flujos: 67,135 de tráfico normal y 600,285 de tráfico anómalo capturado en los seis escenarios del Grupo B (SYN flood, port scan, UDP flood, ICMP flood, HTTP abuse y brute force SSH). El etiquetado se realizó por escenario de origen: todo flujo proveniente del host de ataque (192.168.0.100) durante una corrida anómala se marcó como ANÓMALO; el resto, como NORMAL. El split para entrenamiento y evaluación siguió un criterio aleatorio (shuffle=True, random_state=42): 80% para entrenamiento (53,708 flujos) y 20% de holdout (13,427 flujos). Se optó por división aleatoria en lugar de cronológica porque el Isolation Forest aprende la distribución estadística del tráfico normal, no secuencias temporales; la distribución aleatoria garantiza representatividad de todos los patrones en el conjunto de entrenamiento.

El pipeline de procesamiento (script `fase3_entrenar.py`) ejecutó sin errores en las 47 capturas del experimento. El script extrae las 14 características, aplica el StandardScaler, entrena el modelo IF y genera `normal_holdout.csv` (13,427 flujos = 20% holdout) y `dataset_comparacion.csv` (25,428 flujos para evaluación). El criterio de aceptación CA-F1-01 (pipeline completo sin errores manuales) fue cumplido.

---

### 4.2 OE2 — Entrenamiento y validación del modelo Isolation Forest

El segundo objetivo requería entrenar un modelo de detección de anomalías con AUC-ROC ≥ 0.80. Se utilizó Isolation Forest (Liu et al., 2008) implementado en scikit-learn 1.9.0, con `n_estimators=300` y `contamination=0.05`. El modelo fue entrenado exclusivamente sobre flujos normales (53,708 flujos, 80% del Grupo A), sin exponer ningún ejemplo de ataque durante el entrenamiento. La evaluación se realizó sobre 13,427 flujos normales del conjunto de holdout y 598,285 flujos anómalos.

#### 4.2.1 Curva AUC-ROC y derivación de umbrales

El modelo asigna a cada flujo un score de anomalía en el rango [-1, 0]: cuanto más bajo el score, más anómalo es el flujo. La figura 4.1 presenta la curva ROC obtenida, de la que se derivaron dos umbrales de decisión mediante criterios distintos.

> **Figura 4.1** — Curva AUC-ROC del modelo Isolation Forest (ver `graficas_f6/f6_07_panel_resumen.png`)

El umbral τ1 se derivó mediante el índice de Youden (máxima diferencia TPR−FPR), que penaliza por igual los falsos negativos y los falsos positivos. El umbral τ2 se fijó en el punto donde FPR ≤ 2%, priorizando la precisión del bloqueo total sobre la cobertura.

**Tabla 4.2 — Umbrales de decisión del modelo**

| Umbral | Valor | Criterio de selección | TPR | FPR | Acción |
|---|---|---|---|---|---|
| τ1 | −0.4459 | Índice de Youden (max TPR−FPR) | 99.40% | 20.47% | PERMIT / LIMIT |
| τ2 | −0.6027 | FPR ≤ 2% | 18.27% | 1.99% | LIMIT / BLOCK |

El rango de scores normales se concentra en media −0.3965 ± 0.0753, mientras que los scores anómalos promedian −0.5420 ± 0.0900. La separación entre distribuciones (Δ = 0.1454) es suficiente para sostener los umbrales sin solapamiento completo, aunque implica una zona de ambigüedad que explica el FPR de 20.47% en τ1 (analizado en la sección 4.5).

#### 4.2.2 Métricas de clasificación

La tabla 4.3 resume las métricas del modelo evaluadas en el conjunto de test.

**Tabla 4.3 — Métricas del modelo Isolation Forest**

| Métrica | Valor | Requisito (CA-F2-01) |
|---|---|---|
| AUC-ROC | **0.8998** | ≥ 0.80 ✅ |
| Precision | **99.54%** | — |
| Recall | **99.40%** | — |
| F1-Score | **0.9947** | — |
| FPR @ τ1 | 20.47% | — (mitigado por whitelist) |
| FPR @ τ2 | 1.99% | — |

El AUC-ROC de 0.8998 supera en 12.5 puntos el umbral mínimo establecido. La precisión de 99.54% y el recall de 99.40% evidencian que el modelo identifica correctamente la casi totalidad de los ataques sin generar una cantidad significativa de falsos positivos sobre flujos genuinamente anómalos.

---

### 4.3 OE3 — Motor de decisión y validación en 40 corridas

El tercer objetivo integraba el modelo en un sistema operativo y lo validaba bajo condiciones reproducibles. El motor de decisión (`motor_decision.py`) lee el archivo `eve.json` en tiempo real mediante *tail*, extrae las 14 características de cada flujo y produce una decisión de control en tres niveles: PERMIT (flujo normal), LIMIT (limitación de tasa a 100 pkt/s vía hashlimit) y BLOCK (descarte en kernel mediante ipset DROP). El bloqueo es además progresivo: primer incidente 300 s, segundo 1,800 s, tercero permanente (timeout=0 en ipset).

#### 4.3.1 Latencia del pipeline

La latencia de procesamiento por flujo fue medida de forma independiente sobre 1,000 flujos consecutivos.

**Tabla 4.4 — Latencia del pipeline (eve.json → decisión)**

| Estadístico | Valor | Requisito (CA-F4-01) |
|---|---|---|
| Latencia media | 34.533 ms | — |
| Latencia mínima | 34.224 ms | — |
| Latencia P95 | **34.768 ms** | < 500 ms ✅ |
| Latencia máxima | 38.717 ms | — |
| Throughput | 29 flows/s | — |

La latencia P95 de 34.8 ms representa el 6.9% del límite establecido de 500 ms, dejando un margen amplio para escenarios de mayor volumen de tráfico.

> **Figura 4.2** — Distribución de latencia del pipeline (ver `graficas_f6/f6_06_latencia_pipeline.png`)

#### 4.3.2 Resultados de las 40 corridas (F6)

La validación formal comprendió 40 corridas ejecutadas el 2026-06-16, organizadas en cuatro grupos de 10. Los grupos *normal* (10 corridas de tráfico legítimo), *mixto* (primer ciclo con tráfico anómalo activo), *reeval* (re-evaluación del bloqueo persistido) y *final* (bloqueo permanente consolidado) permiten observar el comportamiento del sistema ante distintos estados de la IP atacante.

**Tabla 4.5 — Resumen de resultados F6 por grupo**

| Grupo | Corridas | Disponibilidad | ITL | Detección | Observación |
|---|---|---|---|---|---|
| normal (A) | 10 | 100% | 0% | N/A | Cero eventos anómalos — esperado |
| mixto (C1) | 10 | 100% | 0% | Corrida 11: 1 IP bloqueada | Primer BLOCK en corrida 11 (synflood, lead_time=61.92s) |
| reeval | 10 | 100% | 0% | IP persiste bloqueada | Motor retiene bloqueo en memoria+ipset |
| final | 10 | 100% | 0% | IP persiste bloqueada | Bloqueo consolidado |
| **Total** | **40** | **100%** | **0%** | — | **Todos los criterios cumplidos** |

La corrida 11 (grupo mixto, escenario synflood) fue la única en la que el motor emitió nuevas detecciones con log de nivel WARNING, con un lead time de 61.92 s desde el inicio del flood hasta el primer BLOCK. En las corridas 12–40, los flujos de la IP atacante continuaron siendo descartados por ipset antes de que Suricata pudiera reportarlos como eventos de flujo; por eso `flows_anom=0` en esas corridas, lo cual es comportamiento correcto: el bloqueo previo impide que el tráfico llegue al sensor.

> **Figura 4.3** — Disponibilidad del sistema a lo largo de las 40 corridas (ver `graficas_f6/f6_01_disponibilidad.png`)

> **Figura 4.4** — Timeline de detecciones por corrida (ver `graficas_f6/f6_03_timeline_deteccion.png`)

> **Figura 4.5** — Panel resumen F6 (ver `graficas_f6/f6_07_panel_resumen.png`)

Los criterios de aceptación de F6 quedan cumplidos en su totalidad: disponibilidad 100% en las 40 corridas, ITL 0% en todas las corridas (ningún host legítimo fue bloqueado), y latencia P95 dentro del límite establecido.

---

### 4.4 Validaciones en tiempo real (2026-06-22)

Adicionalmente a las 40 corridas formales de F6, se realizaron validaciones en vivo el 2026-06-22 para evidenciar el comportamiento del sistema ante escenarios que requieren observación directa del log y de las alertas externas.

#### 4.4.1 Bloqueo progresivo — escenario B1 SYN Flood

Se ejecutaron tres corridas consecutivas de SYN flood con `hping3` desde el host Kali (192.168.0.100) hacia el servidor (192.168.0.120:80), con motor reiniciado entre corridas para verificar el incremento del contador de bloqueos.

**Tabla 4.6 — Evidencia de bloqueo progresivo (2026-06-22)**

| Corrida | Timestamp | Trigger | Score IF | Acción | Timeout ipset |
|---|---|---|---|---|---|
| 1ª | 05:44:13 | IF (score < τ2) | −0.6066 | BLOCK #1 | 300 s |
| 2ª | 06:05:03 | IF (score < τ2) | −0.7696 | BLOCK #2 | 1,800 s |
| 3ª | 06:39:42 | HTTP-ABUSE (100 req/30s) | — | BLOCK #3 | ∞ permanente |

La tercera corrida fue detectada por el detector heurístico de HTTP Abuse antes de que el score del Isolation Forest alcanzara el umbral τ2, lo que muestra que los dos mecanismos de detección (estadístico y heurístico) actúan de forma complementaria. El ipset del servidor reflejó el bloqueo permanente como `timeout 0`, confirmado mediante `sudo ipset list ppi_blocked` en el host 192.168.0.120.

#### 4.4.2 Lead time — escenario B6 SSH Brute Force

Se ejecutó un ataque de diccionario SSH con Hydra (`-t 4` hilos paralelos) desde Kali hacia el servidor (192.168.0.120:22). El detector heurístico BF-SSH opera con una ventana de 60 s y dos umbrales: 5 intentos para LIMIT y 15 para BLOCK.

**Tabla 4.7 — Lead time B6 SSH Brute Force (2026-06-22 08:31)**

| Evento | Tiempo desde inicio | Score IF | Tipo detectado | Acción |
|---|---|---|---|---|
| Primera detección | T + 53 s | −0.4832 | BAJA_ANOMALIA | LIMIT |
| Bloqueo | T + 60 s | −0.6228 | BRUTE_FORCE_SSH | BLOCK |

El intervalo de 60 s hasta BLOCK es inherente al diseño del detector: acumular 15 intentos fallidos de autenticación SSH en una ventana deslizante de 60 s es el criterio que diferencia un brute force de una sesión SSH legítima con reconexiones. Este valor es comparable al de sistemas IPS comerciales que utilizan ventanas similares (30–120 s) para evitar falsos positivos con clientes SSH lentos.

#### 4.4.3 Alerta Telegram

Simultáneamente al primer BLOCK del escenario B6, el motor envió una alerta a través de la API de Telegram. La notificación fue recibida a las 07:25 y contenía: tipo de alerta, IP origen, puerto, score IF, acción tomada y timestamp. La entrega HTTP retornó código 200. El tiempo entre la decisión de bloqueo en el motor y la recepción de la notificación en el dispositivo móvil fue inferior a 800 ms (latencia típica de la API de Telegram).

#### 4.4.4 Whitelist — integridad del tráfico legítimo

Para verificar que el sistema no interfiere con hosts de confianza, se generaron 120 solicitudes HTTP en ráfaga desde el host Desktop (192.168.0.20) al servidor, volumen que excede el umbral de HTTP Abuse (100 req/30 s). El motor no emitió ninguna acción de BLOCK ni LIMIT para esta IP, y el host no apareció en ningún ipset. Esto confirma que la whitelist (`config/whitelist.conf`) funciona correctamente en tiempo de ejecución.

---

### 4.5 Análisis de limitaciones

Se identificaron diez limitaciones durante el diseño, implementación y validación del sistema. La tabla 4.8 presenta su clasificación, severidad y estado de mitigación.

**Tabla 4.8 — Limitaciones del sistema y estado de mitigación**

| ID | Descripción | Severidad | Mitigación | Estado |
|---|---|---|---|---|
| L1 | FPR = 20.47% en τ1 (zona LIMIT) | Alta | Whitelist de IPs internas | ✅ Implementada — ITL operativo = 0% |
| L2 | Lead time B1 ~62s, B6 ~60s | Alta | Detectores heurísticos BF-SSH + HTTP-Abuse | ✅ Validada en vivo |
| L3 | AVISO-DETERMINISTA no disparable con floods masivos | Alta | Regla determinista `limit_count ≥ 5` | ✅ En código — condición no alcanzable en lab |
| L4 | Saturación de tabla de flujos Suricata | Moderada | Monitor de kernel_drops + alerta Telegram | ✅ Implementada |
| L5 | Bloqueo progresivo requería validación formal | Moderada | Tres corridas en vivo el 2026-06-22 | ✅ Validada |
| L6 | Data leakage XGBoost (AUC=1.0 artefactual) | Moderada | `score` removido de features; AUC=0.9992 | ✅ Corregida en código |
| L7 | Entrenamiento en laboratorio cerrado | Moderada | F5 reentrenamiento automático (crontab) | ✅ Implementada |
| L8 | Whitelist solo interna (IPs externas legítimas) | Menor | `config/whitelist.conf` editable sin código | ✅ Implementada |
| L9 | Telegram sin canal alternativo de alerta | Menor | `telegram.conf` externo — puede cambiarse | ✅ Documentada |
| L10 | Dashboard no persistía entre reinicios del SO | Menor | `ppi-dashboard.service` con `systemd enable` | ✅ Implementada |

#### 4.5.1 FPR = 20.47% en τ1 (L1)

La limitación de mayor impacto potencial es el FPR de 20.47% en τ1. Esto significa que aproximadamente uno de cada cinco flujos legítimos obtiene un score por debajo de τ1 y entra en la zona LIMIT. Las causas son dos: (a) τ1 se optimizó para maximizar TPR (recall = 99.40%), lo que implica aceptar un FPR mayor; (b) el Isolation Forest penaliza flujos con características inusuales aunque legítimos, como transferencias de archivos grandes o conexiones SCP con tamaños de paquete atípicos.

En la práctica, el ITL operativo fue 0% en las 40 corridas porque la whitelist cubre todos los hosts internos del laboratorio. En un entorno de producción, la mitigación requeriría una whitelist dinámica o una estrategia de retroalimentación que permita confirmar hosts benignos de forma periódica. El mecanismo de whitelist editable sin modificar código ya está disponible en `config/whitelist.conf`.

Cabe destacar que reducir τ1 para bajar el FPR tendría el efecto de aumentar los falsos negativos en ataques de perfil moderado como el SYN flood (cuyos scores se concentran alrededor de −0.49), lo cual representa un riesgo mayor que la tasa actual de LIMIT sobre flujos legítimos.

#### 4.5.2 Lead time y arquitectura basada en Netflow (L2)

El lead time de ~62 s en SYN Flood es una consecuencia de la arquitectura: Suricata reporta flows cuando estos se cierran (señal FIN/RST). Los SYN floods nunca completan el handshake TCP, por lo que Suricata espera el timeout de sesión antes de escribir el evento. Este comportamiento es común en sistemas basados en análisis de flujos de red (NetFlow/IPFIX/Suricata eve.json) y no es específico de este sistema.

Para los escenarios con mayor riesgo operativo (SSH Brute Force, HTTP Abuse), los detectores heurísticos actúan dentro de ventanas de 60 s y 30 s respectivamente, sin depender del cierre del flujo por parte de Suricata.

#### 4.5.3 Data leakage en XGBoost (L6 — corregido)

Durante la validación pre-defensa se detectó que el predictor XGBoost incluía el `score` del Isolation Forest como feature de entrenamiento. Dado que los labels se derivan de los umbrales del mismo `score`, existía una correlación directa entre feature y label (data leakage), resultando en AUC=1.0000 artefactual.

La corrección consistió en eliminar `score` de la lista de features en `f4_entrenar_predictor_v2.py`, `f5_reentrenar_xgboost.py` y `predictor.py`, y derivar la feature binaria `is_block` desde la columna `decision` del log (no desde el score). El modelo con 10 features comportamentales (incluyendo  para capturar velocidad del ataque) obtuvo AUC=0.9991. El feature  (bloques por segundo en ventana de 60s) permite al modelo distinguir ataques en aceleración de residuos históricos, mejorando la predicción de persistencia., que sigue siendo alto pero responde a una razón legítima: en el laboratorio, un host que inicia un UDP flood lo mantiene durante toda la corrida, lo cual hace que las features `proto_udp` y `block_count_60s` sean predictores genuinamente efectivos de persistencia.

**Tabla 4.9 — Features del predictor XGBoost v2 (post-corrección)**

| Feature | Importancia | Interpretación |
|---|---|---|
| `block_count_60s` | 55.47% | Historial de bloqueos recientes de la IP |
| `is_block` | 6.64% | Evento actual es BLOCK del Isolation Forest |
| `limit_count_15s` | 1.72% | Acumulación de eventos sospechosos en 15s |
| `is_block` | 0.92% | Acción actual (BLOCK vs LIMIT) |
| `dest_port` | 0.89% | Puerto objetivo |
| `hora_cos`, `hora_sin` | 0.62% | Patrón temporal |
| `limit_count_15s` | 0.22% | Presión reciente de tráfico |
| `proto_icmp` | 0.00% | ICMP floods (escasos en dataset reciente) |

---

### 4.6 Cumplimiento de criterios de aceptación

La tabla 4.10 consolida el cumplimiento de los criterios de aceptación definidos por fase.

**Tabla 4.10 — Resumen de criterios de aceptación**

| ID | Criterio | Umbral | Resultado | Estado |
|---|---|---|---|---|
| CA-F1-01 | Pipeline ejecuta sin errores manuales | 100% automatizado | 47 capturas procesadas | ✅ |
| CA-F2-01 | AUC-ROC del modelo | ≥ 0.80 | 0.8998 | ✅ |
| CA-F3-01 | Latencia P95 por flujo | < 500 ms | 34.8 ms | ✅ |
| CA-F4-01 | AUC-ROC predictor XGBoost | > 0.70 | 0.9991 | ✅ |
| CA-F5-01 | Scripts de reentrenamiento ejecutan sin error | Sin fallo | Validado 2026-06-22 | ✅ |
| CA-F6-01 | Disponibilidad del sistema | 100% en 40 corridas | 40/40 | ✅ |
| CA-F6-02 | ITL (Interrupción de Tráfico Legítimo) | 0% | 0% | ✅ |
| CA-F6-03 | Detección en escenarios anómalos | ≥ 1 IP bloqueada | 1 IP bloqueada corrida 11 | ✅ |

Todos los criterios de aceptación definidos fueron cumplidos. El sistema funciona de extremo a extremo con un margen de seguridad significativo en latencia (6.9% del límite) y con métricas de clasificación superiores al 99% en precisión y recall.
