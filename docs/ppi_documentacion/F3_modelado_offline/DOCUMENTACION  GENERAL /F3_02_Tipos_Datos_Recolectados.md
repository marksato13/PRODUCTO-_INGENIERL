# F3-02 — Identificación y Clasificación de los Datos Recolectados

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F3 — Modelado Offline  
**Fuente de datos:** `dataset_clean.csv` — verificado en sensor 192.168.0.110  
**Fecha:** 2026-06-14  

---

## Origen de los datos

Suricata 7.0.3 inspecciona el tráfico de red en la interfaz `ens35` del sensor (192.168.0.110) en modo pasivo. Por cada flujo de red que cierra (por timeout, FIN o RST), escribe una línea JSON en `/var/log/suricata/eve.json`. El script `parser.py` convierte estos registros en filas CSV, y `etiquetar_limpiar.py` los limpia y etiqueta, produciendo `dataset_clean.csv` con **376,827 flows** y **18 columnas**.

**Columnas del dataset:**
```
timestamp, flow_id, src_ip, src_port, dest_ip, dest_port, proto, app_proto,
bytes_toserver, bytes_toclient, pkts_toserver, pkts_toclient,
flow_start, flow_end, duration, escenario, corrida, label
```

---

## 1. Inventario Completo de Atributos

### Variables Numéricas Continuas

| Variable | Descripción | Rango observado | Media | P95 |
|---|---|---|---|---|
| `bytes_toserver` | Bytes enviados al servidor en el flow | 60 – 436,380 | 197.5 | 490.0 |
| `bytes_toclient` | Bytes recibidos del servidor | 0 – 1,127,557 | 193.6 | 1,134.0 |
| `duration` | Duración del flow en segundos | 0.0 – 1,088.4 | 0.045 | 0.282 |

> **Nota:** El 88.7% de los flows tiene `duration=0.000` porque Suricata registra flows de muy corta duración (e.g. SYN flood, ICMP) con resolución de milisegundos que redondea a cero. Los 42,715 flows con duración > 0 corresponden principalmente a tráfico HTTP y SSH con intercambio de datos.

### Variables Numéricas Discretas

| Variable | Descripción | Rango observado | Media | P95 |
|---|---|---|---|---|
| `pkts_toserver` | Paquetes enviados al servidor | 1 – 7,273 | 1.9 | 6.0 |
| `pkts_toclient` | Paquetes recibidos del servidor | 0 – N/A | — | — |
| `src_port` | Puerto origen del flow | 1 – 65535 | — | — |
| `dest_port` | Puerto destino del flow | 22, 53, 80, … | — | — |
| `flow_id` | Identificador único de flow (Suricata) | entero 64 bits | — | — |
| `corrida` | Número de corrida del escenario | 1 – 10 | — | — |

### Variables Categóricas

| Variable | Descripción | Valores observados | Distribución |
|---|---|---|---|
| `proto` | Protocolo de transporte | TCP, UDP, ICMP | TCP: 59.9% · UDP: 34.7% · ICMP: 5.4% |
| `app_proto` | Protocolo de aplicación | http, ssh, failed, (vacío) | http: 8.9% · ssh: 1.9% · failed: 34.7% · vacío: 54.4% |
| `escenario` | Escenario de captura | 13 valores (ver tabla §2) | — |
| `src_ip` | IP origen | 192.168.0.20 / 192.168.0.100 | — |
| `dest_ip` | IP destino | 192.168.0.120 | — |

> **`app_proto=failed`:** Suricata no pudo identificar el protocolo de aplicación (típico en floods UDP/TCP sin payload reconocible). `app_proto=vacío` corresponde a ICMP (sin capa de aplicación).

### Variables Temporales

| Variable | Descripción | Formato | Ejemplo |
|---|---|---|---|
| `timestamp` | Momento en que Suricata cierra el flow | ISO 8601 UTC | `2026-06-02T04:20:57.314207+0000` |
| `flow_start` | Inicio del flow | ISO 8601 UTC | `2026-06-02T04:19:52.568240+0000` |
| `flow_end` | Fin del flow | ISO 8601 UTC | `2026-06-02T04:19:52.568917+0000` |

### Variables Binarias / Flags

| Variable | Descripción | Valores | Origen |
|---|---|---|---|
| `label` | Clase del flow | 0=normal, 1=anomalous | Etiquetado dual (escenario + src_ip) |
| `is_tcp` | ¿Protocolo TCP? | 0/1 | Derivada de `proto` |
| `is_udp` | ¿Protocolo UDP? | 0/1 | Derivada de `proto` |
| `is_icmp` | ¿Protocolo ICMP? | 0/1 | Derivada de `proto` |

### Variables Derivadas (Feature Engineering)

Calculadas en `fase3_isolation_forest.py` sobre los campos raw de Suricata:

| Variable | Fórmula | Propósito |
|---|---|---|
| `pkt_rate` | `(pkts_toserver + pkts_toclient) / max(duration, 0.001)` | Detecta floods de alta tasa |
| `byte_rate` | `(bytes_toserver + bytes_toclient) / max(duration, 0.001)` | Detecta transferencias masivas |
| `pkt_ratio` | `pkts_toserver / (pkts_toclient + 1)` | Asimetría envío/recepción |
| `byte_ratio` | `bytes_toserver / (bytes_toclient + 1)` | Asimetría de bytes |
| `avg_pkt_size` | `(bytes_toserver + bytes_toclient) / (pkts_toserver + pkts_toclient + 1)` | Tamaño promedio por paquete |

---

## 2. Clasificación de Datos por Rol en Detección

### IP Origen (`src_ip`)

| Valor | Rol en el sistema | Flows | % |
|---|---|---|---|
| `192.168.0.20` | Desktop — tráfico normal | 11,669 | 3.1% |
| `192.168.0.100` | Kali — tráfico anómalo | 365,158 | 96.9% |

Uso en el modelo: **no se incluye como feature** (evitar sesgo por IP hardcoded). Sí se usa en el etiquetado y en la whitelist del motor para excluir el Desktop del bloqueo.

### IP Destino (`dest_ip`)

En todo el dataset: `192.168.0.120` (servidor nginx/SSH). Variable de identificación, **no incluida como feature** del modelo.

### Puerto Origen (`src_port`)

| Estado | Flows | % |
|---|---|---|
| Presente (TCP/UDP) | 356,662 | 94.6% |
| Ausente (ICMP) | 20,165 | 5.4% |

Efímero en tráfico normal; puede ser fijo en algunos ataques (hping3 usa puertos fijos). **No incluido como feature** — demasiado ruidoso; el modelo usa `dest_port` como indicador más estable.

### Puerto Destino (`dest_port`)

Top puertos observados:

| Puerto | Protocolo | Flows | Escenario |
|---|---|---|---|
| 80 | HTTP | 207,003 | HTTP normal + SYN flood + HTTP abuse + mixto |
| 53 | DNS/UDP | 130,954 | UDP flood |
| — | ICMP (sin puerto) | 20,165 | ICMP flood |
| 22 | SSH | 7,371 | SSH normal + brute force |
| otros | — | 11,334 | Port scan (escanea todos los puertos) |

**Incluido como feature** (`dest_port`): el puerto destino discrimina bien entre tipos de ataque y tráfico legítimo.

### Bytes Enviados / Recibidos

| Variable | Min | Max | Media | Comportamiento en ataques |
|---|---|---|---|---|
| `bytes_toserver` | 60 | 436,380 | 197.5 | SYN flood: 60 bytes (solo SYN) · HTTP normal: 492+ |
| `bytes_toclient` | 0 | 1,127,557 | 193.6 | ICMP/UDP floods: 0 (sin respuesta) · HTTP: 555+ |

**Incluidos como features** directas y en ratios derivados.

### Flow (`flow_id`, `flow_start`, `flow_end`, `duration`)

| Campo | Uso |
|---|---|
| `flow_id` | Identificador único — descartado del modelo |
| `flow_start` / `flow_end` | Usados para calcular `duration` — descartados tras cálculo |
| `duration` | **Feature incluida** — cero en floods, positiva en tráfico real |

### Alertas (eventos Suricata)

El sistema usa únicamente `event_type=flow`. Los eventos de tipo `alert` (firmas IDS) se descartan del dataset de ML porque: (a) generarían dependencia circular con las reglas de Suricata, (b) el objetivo es detectar anomalías no firmadas. Los eventos `alert` son complementarios al sistema, no su base.

### Protocolo (`proto`, `app_proto`)

| Campo | Distribución | Tratamiento |
|---|---|---|
| `proto` | TCP 59.9% · UDP 34.7% · ICMP 5.4% | Codificado como `is_tcp`, `is_udp`, `is_icmp` (one-hot) |
| `app_proto` | vacío 54.4% · failed 34.7% · http 8.9% · ssh 1.9% | **No incluido** — demasiados nulos y `failed` ambiguo |

### Timestamp (`timestamp`)

Usado exclusivamente para la **partición cronológica** 70/15/15. No se incluye como feature del modelo (evitar sobreajuste temporal).

---

## 3. Calidad de Datos

### Valores Nulos

| Variable | Nulos | % | Causa | Tratamiento |
|---|---|---|---|---|
| `app_proto` | 205,008 | 54.4% | ICMP no tiene app layer; floods TCP/UDP sin payload | Descartada del modelo |
| `src_port` | 20,165 | 5.4% | ICMP no tiene puertos | Descartada del modelo |
| `dest_port` | 20,165 | 5.4% | ICMP no tiene puertos | Reemplazado por 0 en feature engineering |
| Resto de columnas | 0 | 0% | — | Sin acción |

### Duplicados

| Verificación | Resultado |
|---|---|
| Filas exactamente duplicadas | **0** (verificado con `dataset_clean.csv`) |
| Flows duplicados eliminados en limpieza | **34** (eliminados por `etiquetar_limpiar.py`) |

### Inconsistencias detectadas y resueltas

| Inconsistencia | Causa | Solución |
|---|---|---|
| IPs inválidas (0.0.0.0, 255.255.255.x, multicast) | Tráfico DHCP/broadcast capturado por Suricata | Filtro en `etiquetar_limpiar.py` — **35,236 flows eliminados** |
| `bytes_toclient=0` con `pkts_toclient>0` | Flows asimétricos en SYN flood (sin respuesta del servidor) | Comportamiento válido — conservado como señal de anomalía |
| `duration=0` en 88.7% de flows | Resolución temporal de Suricata insuficiente para floods | Válido — `pkt_rate` usa `max(duration, 0.001)` para evitar división por cero |

### Valores Extremos (Outliers)

| Variable | Valor máximo | Flow | Interpretación |
|---|---|---|---|
| `bytes_toserver` | 436,380 | Transferencia legítima (scp) | Legítimo — conservado |
| `bytes_toclient` | 1,127,557 | Descarga HTTP normal | Legítimo — conservado |
| `pkts_toserver` | 7,273 | SYN flood hping3 | Anómalo — señal clave |
| `duration` | 1,088.4 s | SSH legítimo sesión larga | Legítimo — conservado |
| `pkt_rate` | ~7,000 pkt/s | SYN flood | Anómalo — alta discriminación |

> Los outliers en flows anómalos son exactamente la señal que el modelo debe detectar. No se eliminan; se normalizan con `StandardScaler` para que Isolation Forest opere en espacio estandarizado.

---

## 4. Compatibilidad con Machine Learning

### Isolation Forest ← **Algoritmo seleccionado**

| Característica | Compatibilidad | Detalle |
|---|---|---|
| Variables numéricas continuas | ✅ Óptimo | `bytes_*`, `duration`, `pkt_rate`, `byte_rate` |
| Variables binarias | ✅ Soportado | `is_tcp`, `is_udp`, `is_icmp` |
| Desbalance extremo (96.9% anómalos) | ✅ Inmune | No usa etiquetas — entrenado solo con normales |
| Valores extremos en ataques | ✅ Señal | Las anomalías se aíslan en ramas cortas |
| Variables categóricas string | ❌ Requiere codificación | `proto` → one-hot; `app_proto` descartada |
| IPs y timestamps directos | ❌ No compatibles | Excluidos del modelo |

### Random Forest

| Característica | Compatibilidad | Detalle |
|---|---|---|
| Variables numéricas | ✅ Óptimo | Todas las 14 features son compatibles |
| Desbalance 96.9%/3.1% | ⚠️ Problemático | Requiere SMOTE o `class_weight='balanced'` |
| Requiere etiquetas | ⚠️ Supervisado | Necesita flows anómalos etiquetados para entrenar |
| Interpretabilidad | ✅ Alta | Feature importance disponible |
| Generalización a ataques nuevos | ❌ Limitada | Solo detecta patrones vistos en entrenamiento |

### One-Class SVM

| Característica | Compatibilidad | Detalle |
|---|---|---|
| Variables numéricas normalizadas | ✅ Requiere normalización (ya aplicada con StandardScaler) | |
| Desbalance | ✅ Inmune | Solo entrena con clase normal |
| Escalabilidad | ❌ O(n²) a O(n³) | Inviable con 376,827 flows en tiempo real |
| Latencia de inferencia | ❌ Alta | No apto para pipeline < 500ms |
| Hiperparámetros sensibles | ⚠️ Difícil tuning | kernel, nu, gamma requieren validación intensiva |

### Redes Neuronales (Autoencoder)

| Característica | Compatibilidad | Detalle |
|---|---|---|
| 14 features numéricas | ✅ Óptimo | Input layer de 14 neuronas |
| Reconstrucción de errores | ✅ Señal de anomalía | Error de reconstrucción alto = anómalo |
| Datos de entrenamiento (684 flows) | ❌ Insuficiente | Autoencoders requieren miles de ejemplos para generalizar |
| Latencia de inferencia | ✅ Baja (GPU) | Sin GPU disponible en el sensor → latencia alta en CPU |
| Interpretabilidad | ❌ Baja | Caja negra; no apto para justificación académica sin SHAP |

### Justificación de la selección — Isolation Forest

Isolation Forest es el algoritmo más adecuado para este problema por cuatro razones concretas derivadas de los datos:

1. **Dataset desbalanceado (96.9% anómalos):** al entrenarse solo con los 684 flows normales, evita completamente el problema de desbalance.
2. **Generalización a ataques no vistos:** el experimento F2-04 confirmó 12/12 ataques no entrenados detectados al 100%.
3. **Latencia O(log n):** inferencia en 34.8ms P95 sobre el sensor con CPU básica.
4. **Score continuo [-1, 0]:** permite la lógica triple PERMIT/LIMIT/BLOCK sin umbral binario.

---

## 5. Tabla Académica de Variables

| Variable | Tipo | Fuente | Incluida en Modelo | Importancia | Notas |
|---|---|---|---|---|---|
| `timestamp` | Temporal | Suricata | No | Alta (partición) | Usada para división cronológica 70/15/15 |
| `flow_id` | Numérica discreta | Suricata | No | Nula | Identificador interno, sin valor predictivo |
| `src_ip` | Categórica | Suricata | No | Alta (etiquetado) | Usada para etiquetar; excluida del modelo (sesgo) |
| `src_port` | Numérica discreta | Suricata | No | Baja | 5.4% nulos (ICMP); efímero en tráfico normal |
| `dest_ip` | Categórica | Suricata | No | Nula | Constante en el lab (.120); sin varianza |
| `dest_port` | Numérica discreta | Suricata | **Sí** | **Alta** | Discrimina tipo de servicio atacado (22/53/80) |
| `proto` | Categórica | Suricata | Codificada | **Alta** | TCP/UDP/ICMP → is_tcp / is_udp / is_icmp |
| `app_proto` | Categórica | Suricata | No | Baja | 54.4% nulos; `failed` ambiguo |
| `bytes_toserver` | Numérica continua | Suricata | **Sí** | **Alta** | SYN flood: 60B; HTTP: 492B+ |
| `bytes_toclient` | Numérica continua | Suricata | **Sí** | **Alta** | 0 en floods unidireccionales |
| `pkts_toserver` | Numérica discreta | Suricata | **Sí** | **Alta** | Hasta 7,273 en SYN flood |
| `pkts_toclient` | Numérica discreta | Suricata | **Sí** | **Alta** | 0 en floods sin respuesta |
| `flow_start` | Temporal | Suricata | No | Media | Usada para calcular `duration` |
| `flow_end` | Temporal | Suricata | No | Media | Usada para calcular `duration` |
| `duration` | Numérica continua | Derivada | **Sí** | **Alta** | 0 en floods; positiva en tráfico real |
| `escenario` | Categórica | Etiquetado | No | Alta (evaluación) | Usada para métricas por escenario en F6 |
| `corrida` | Numérica discreta | Etiquetado | No | Baja | Control experimental |
| `label` | Binaria | Etiquetado | No (unsupervised) | Alta (evaluación) | Ground truth para métricas AUC/Precision/Recall |
| `pkt_rate` | Numérica continua | **Derivada** | **Sí** | **Muy alta** | Principal discriminador de floods de alta tasa |
| `byte_rate` | Numérica continua | **Derivada** | **Sí** | **Alta** | Detecta transferencias masivas |
| `pkt_ratio` | Numérica continua | **Derivada** | **Sí** | **Alta** | Asimetría send/recv; alta en floods unidireccionales |
| `byte_ratio` | Numérica continua | **Derivada** | **Sí** | **Alta** | Asimetría bytes; alta en port scan |
| `avg_pkt_size` | Numérica continua | **Derivada** | **Sí** | **Alta** | SYN: 60B/pkt; HTTP: 100-1400B/pkt |
| `is_tcp` | Binaria | **Derivada** | **Sí** | **Media** | 1 en SYN flood, brute force, port scan |
| `is_udp` | Binaria | **Derivada** | **Sí** | **Media** | 1 en UDP flood |
| `is_icmp` | Binaria | **Derivada** | **Sí** | **Media** | 1 en ICMP flood |

**Total variables en el modelo:** 14 (10 numéricas + 3 binarias proto + 1 dest_port)

---

## 6. Distribución por Escenario

| Escenario | Flows | Tipo | Label |
|---|---|---|---|
| `anom_synflood` | 94,841 | Anómalo | 1 |
| `mixto_http` | 95,157 | Mixto (anom. dominante) | 1 |
| `mixto_descarga` | 109,839 | Mixto (anom. dominante) | 1 |
| `anom_udpflood` | 15,815 | Anómalo | 1 |
| `anom_icmpflood` | 20,200 | Anómalo | 1 |
| `anom_httpabuse` | 21,758 | Anómalo | 1 |
| `anom_portscan` | 3,297 | Anómalo | 1 |
| `anom_bruteforce` | 2,062 | Anómalo | 1 |
| `mixto_ssh` | 137 | Mixto | 1 |
| `normal_http` | 11,333 | Normal | 0 |
| `normal_ssh` | 2,108 | Normal | 0 |
| `normal_sostenido` | 251 | Normal | 0 |
| `normal_transferencia` | 29 | Normal | 0 |
| **TOTAL** | **376,827** | — | — |

---

## Referencias de archivos

| Archivo | Ruta en sensor | Descripción |
|---|---|---|
| `dataset_raw.csv` | `data/dataset_raw.csv` | Datos sin limpiar (18 columnas, campos crudos) |
| `dataset_clean.csv` | `data/dataset_clean.csv` | Dataset limpio y etiquetado (376,827 flows) |
| `etiquetar_limpiar.py` | `scripts/etiquetar_limpiar.py` | Limpieza, dedup y etiquetado dual |
| `fase3_isolation_forest.py` | `scripts/fase3_isolation_forest.py` | Feature engineering y entrenamiento |
| `features.csv` | `models/features.csv` | Lista de 14 features del modelo |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
