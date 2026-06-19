# Informe de Resultados — Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos

**Universidad Peruana Unión — Proyecto de Investigación (PPI)**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez
**Fecha:** Junio 2026

---

## 1. Resumen Ejecutivo

Se diseñó, implementó y validó un sistema de detección temprana de comportamientos anómalos en redes de datos universitarias, basado en el algoritmo **Isolation Forest** entrenado sobre 14 features extraídas de flows de red capturados con **Suricata 7.0.3**. El sistema opera en modo inline sobre el sensor de red, emitiendo decisiones de control de tráfico (**PERMIT / LIMIT / BLOCK**) en tiempo real mediante `iptables/ipset`.

### Métricas finales del sistema

| Métrica | Valor obtenido | Requisito |
|---|---|---|
| AUC-ROC | **0.8998** | ≥ 0.85 |
| Precisión | **99.54 %** | — |
| Recall (TPR @ τ1) | **99.40 %** | — |
| F1-Score | **0.9947** | — |
| Latencia P95 (pipeline completo) | **34.8 ms** | < 500 ms |
| Interrupción de Tráfico Legítimo (ITL) | **0 %** | — |
| Disponibilidad del motor | **100 %** | — |
| Corridas de validación F6 completadas | **40 / 40** | — |

El sistema **cumple todos los requisitos definidos** para el PPI. La latencia de decisión es 14× inferior al límite establecido y no se registró ninguna interrupción de tráfico legítimo durante las 40 corridas de validación.


---

## 2. Descripción del Sistema

### 2.1 Topología del laboratorio

El sistema se desplegó en un entorno de laboratorio virtualizado compuesto por cinco máquinas con roles diferenciados:

| IP | Máquina Virtual | Rol |
|---|---|---|
| 192.168.0.10 | Windows 11 | Cliente de red |
| 192.168.0.20 | Ubuntu Desktop | Administrador / origen de tráfico normal |
| 192.168.0.100 | Kali Linux | Origen de tráfico anómalo (ataques controlados) |
| 192.168.0.110 | Ubuntu Sensor | Sensor de red — Suricata 7.0.3 + motor de decisión |
| 192.168.0.120 | Ubuntu Server | Servicio objetivo — nginx :80, SSH :22 |

El sensor (192.168.0.110) actúa como punto de inspección inline: captura todos los flows que atraviesan la red, los clasifica con el modelo y aplica las reglas de control directamente sobre el tráfico mediante `iptables/ipset`.

### 2.2 Pipeline de procesamiento (6 fases)

El sistema se construyó en seis fases encadenadas, cada una con entradas y salidas bien definidas:

```
eve.json (Suricata 7.0.3)
    │
    ├─ F1  Captura de tráfico     → eve.json.gz por escenario (nomenclatura YYYYMMDD_grupo_escenario_NN)
    ├─ F2  Parseo y etiquetado    → dataset_raw.csv → dataset_clean.csv → train/val/test (70/15/15)
    ├─ F3  Modelado offline       → isolation_forest.pkl + scaler.pkl + metricas_offline.txt (τ1, τ2)
    ├─ F4  Motor de decisión      → tail eve.json → features → score IF → PERMIT / LIMIT / BLOCK
    ├─ F5  Control inline         → ipset ppi_blocked / ppi_limited → iptables DROP / HASHLIMIT
    └─ F6  Validación             → 40 corridas (13 escenarios × ~3 repeticiones) → resultados_f6_completo.csv
```

Todas las fases fueron completadas y validadas. Los artefactos de cada fase son prerrequisito de la siguiente: si `metricas_offline.txt` (F3) no existe, el motor (F4) no puede arrancar.

### 2.3 Las 14 features del modelo

Las features se extraen directamente de los campos de cada flow en `eve.json`. Las primeras cuatro son nativas de Suricata; las diez restantes son derivadas calculadas en el parser:

| # | Feature | Tipo | Descripción |
|---|---|---|---|
| 1 | `pkts_toserver` | nativa | Paquetes enviados al servidor |
| 2 | `pkts_toclient` | nativa | Paquetes enviados al cliente |
| 3 | `bytes_toserver` | nativa | Bytes enviados al servidor |
| 4 | `bytes_toclient` | nativa | Bytes enviados al cliente |
| 5 | `duration` | derivada | Duración del flow en segundos |
| 6 | `pkt_rate` | derivada | Paquetes por segundo (`pkts_total / duration`) |
| 7 | `byte_rate` | derivada | Bytes por segundo (`bytes_total / duration`) |
| 8 | `pkt_ratio` | derivada | `pkts_toserver / (pkts_toclient + 1)` |
| 9 | `byte_ratio` | derivada | `bytes_toserver / (bytes_toclient + 1)` |
| 10 | `avg_pkt_size` | derivada | Tamaño promedio de paquete |
| 11 | `is_tcp` | derivada | 1 si el protocolo es TCP, 0 si no |
| 12 | `is_udp` | derivada | 1 si el protocolo es UDP, 0 si no |
| 13 | `is_icmp` | derivada | 1 si el protocolo es ICMP, 0 si no |
| 14 | `dest_port` | derivada | Puerto de destino del flow |


---

## 3. Escenarios de Validación

Se definieron 13 escenarios organizados en tres grupos según el tipo de tráfico generado. Cada escenario fue ejecutado en al menos 3 corridas independientes para garantizar la reproducibilidad de los resultados.

### 3.1 Grupo A — Tráfico Normal (origen: Desktop 192.168.0.20)

| ID | Escenario | Herramienta | Duración | Objetivo |
|---|---|---|---|---|
| A1 | `http_normal` | `curl` / `wget` → :80 | 10 min | Tráfico HTTP de navegación típica |
| A2 | `ssh_legitimo` | `ssh` → :22 | 8 min | Sesión SSH interactiva legítima |
| A3 | `transferencia_legitima` | `scp` / `wget` | 10 min | Descarga y transferencia de archivos |
| A4 | `trafico_sostenido` | `curl` + `ssh` mixto | 15 min | Carga continua combinada HTTP+SSH |

### 3.2 Grupo B — Tráfico Anómalo (origen: Kali 192.168.0.100)

| ID | Escenario | Herramienta | Objetivo del ataque |
|---|---|---|---|
| B1 | `syn_flood` | `hping3 -S --flood` → :80 | Inundación de paquetes SYN (DoS) |
| B2 | `port_scan` | `nmap -sS` | Escaneo de puertos sigiloso |
| B3 | `udp_flood` | `hping3 --udp --flood` → :53 | Inundación UDP |
| B4 | `icmp_flood` | `hping3 -1 --flood` | Inundación ICMP (ping flood) |
| B5 | `acceso_repetitivo` | `curl` en bucle → :80 | Abuso HTTP (scraping agresivo) |
| B6 | `bruteforce` | `hydra` → :22 | Fuerza bruta SSH |

### 3.3 Grupo C — Tráfico Mixto (Desktop + Kali simultáneos)

| ID | Escenario | Tráfico normal | Tráfico anómalo |
|---|---|---|---|
| C1 | `http_syn` | HTTP normal (:80) | SYN flood simultáneo |
| C2 | `ssh_portscan` | SSH legítimo (:22) | Port scan simultáneo |
| C3 | `descarga_udp` | Descarga de archivos | UDP flood simultáneo |

El Grupo C es el escenario más exigente: el motor debe mantener ITL=0% (no bloquear tráfico legítimo) mientras detecta y bloquea el tráfico anómalo que llega simultáneamente desde la misma red.


---

## 4. Análisis Exploratorio de Features (EDA)

Antes de realizar el split 80/20 y entrenar el modelo, se realizó un análisis exploratorio descriptivo sobre el universo completo de flows capturados. El objetivo es verificar que las 14 features discriminan entre tráfico normal y anómalo, y entender la distribución de cada grupo.

### 4.1 Datos analizados

| Grupo | Tipo | Flows totales | Archivos |
|---|---|---|---|
| A | Normal | 67,135 | 28 |
| B | Anómalo | 302,892 | 13 |
| C | Mixto | 31,397 | 6 |
| **Total** | — | **401,424** | **47** |

### 4.2 Feature más discriminante: `byte_ratio`

`byte_ratio = bytes_toserver / (bytes_toclient + 1)`

En tráfico normal el servidor responde con volumen similar al recibido. En ataques de inundación (SYN flood, UDP flood) los paquetes enviados superan masivamente los recibidos, disparando esta métrica:

| Estadístico | Grupo A (Normal) | Grupo B (Anómalo) | Ratio |
|---|---|---|---|
| Mediana | 0.955 | 60.000 | **62.8×** |

![Distribuciones log₁₀ de features clave — A (azul), B (rojo), C (verde)](../../results/eda/eda_01_distribuciones.png)

![Boxplots Grupo A vs Grupo B — escala logarítmica](../../results/eda/eda_03_boxplots.png)

### 4.3 Distribución de protocolos por grupo

| Protocolo | Grupo A (Normal) | Grupo B (Anómalo) |
|---|---|---|
| TCP | 99.6 % | 59.4 % |
| UDP | 0.4 % | 21.9 % |
| ICMP | 0.0 % | 18.7 % |

El tráfico normal usa casi exclusivamente TCP (HTTP y SSH). El tráfico anómalo muestra diversidad de protocolos por los escenarios de flood UDP e ICMP, lo que hace que las features `is_udp` e `is_icmp` sean útiles para el modelo.

![Distribución de protocolos por grupo](../../results/eda/eda_02_protocolo.png)

### 4.4 Correlación entre features

![Heatmap de correlación Pearson 14×14 — Grupo A (izquierda) y Grupo B (derecha)](../../results/eda/eda_04_correlacion.png)

En el Grupo A las features de bytes y paquetes presentan alta correlación entre sí (r > 0.9), lo esperado en tráfico HTTP/SSH simétrico. En el Grupo B esta correlación se rompe: `byte_ratio` y `pkt_ratio` se desacoplan de las features de volumen absoluto, señal característica de los ataques de inundación unidireccionales.

### 4.5 Puertos de destino

![Top-10 puertos de destino por grupo](../../results/eda/eda_05_dest_ports.png)

El Grupo A concentra el 100% del tráfico en los puertos :80 (HTTP) y :22 (SSH). El Grupo B distribuye el tráfico en :80, :22 y :53 (UDP flood al DNS), con menor concentración por puerto al incluir escaneos de múltiples puertos (B2 port scan).

### 4.6 Discriminabilidad estadística

Las 14 features fueron evaluadas con el test no paramétrico Mann-Whitney U (Grupo A vs Grupo B). Resultado: **14/14 features con p < 0.001**, confirmando que todas contribuyen información discriminante al modelo.

![Tabla de estadísticas descriptivas por grupo](../../results/eda/eda_06_stats_tabla.png)

