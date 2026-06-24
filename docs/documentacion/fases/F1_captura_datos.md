# F1 — Captura de Datos
**Estado: ✅ COMPLETA Y VALIDADA**  
**Período:** mayo–junio 2026 | **Resultado:** 47 capturas, 667,420 flujos etiquetados

---

## Objetivo

Registrar tráfico de red real bajo escenarios controlados (normal y anómalo) en un laboratorio virtualizado y almacenarlo como capturas brutas listas para el entrenamiento del modelo. Sin datos reales de calidad, ningún modelo puede aprender.

---

## Entradas → Proceso → Salidas

```
ENTRADAS
  Red física: tráfico real entre Desktop↔Servidor y Kali↔Servidor
  Herramientas: hping3, nmap, hydra, curl, wget, scp (según escenario)
  Configuración: Suricata 7.0.3 en ens35 modo promiscuo

PROCESO
  Suricata captura todos los paquetes del segmento → genera eve.json (JSON/línea)
  Al fin de cada corrida:
    exportar_eve_por_escenario.sh → gzip -c eve.json → archivo .gz
    sudo truncate -s 0 eve.json   → vaciar para siguiente corrida
    suricatasc reopen-log-files   → Suricata rota el fd sin reiniciarse
    registrar_bitacora.sh         → escribe línea en bitácora

SALIDAS
  data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz  (47 archivos)
  docs/bitacora/bitacora_escenarios.txt             (64 entradas)
```


---

## Terminología clave

| Término | Definición |
|---|---|
| **Suricata** | Motor IDS/IPS de código abierto (v7.0.3). Captura paquetes en modo pasivo, analiza el tráfico y genera eventos estructurados en `eve.json`. No bloquea tráfico por sí mismo. |
| **eve.json** | Archivo de log de Suricata en formato JSON por línea. Cada línea es un evento: `flow`, `alert`, `dns`, `http`, `stats`, etc. Es la única entrada de toda la cadena. |
| **Flujo (flow)** | Unidad de tráfico agregada: todos los paquetes entre un par src_ip:port ↔ dst_ip:port con el mismo protocolo, durante una sesión. Suricata los cierra por timeout o FIN/RST. |
| **ens35** | Interfaz de red del sensor (192.168.0.110) conectada al segmento de laboratorio. Configurada en **modo promiscuo**: recibe todos los paquetes del segmento, no solo los dirigidos a ella. |
| **Modo promiscuo** | La NIC acepta paquetes aunque el MAC destino no sea el suyo. Sin este modo, Suricata solo vería tráfico hacia/desde el sensor, no entre Desktop↔Servidor ni Kali↔Servidor. |
| **eve.json.gz** | Compresión gzip del eve.json de una corrida. Reduce el tamaño ~10×. Formato final de almacenamiento de cada captura. |
| **Corrida** | Una sesión de tráfico controlada de un escenario específico (ej: B1 SYN Flood). Cada corrida genera un archivo `.gz` independiente con nomenclatura `YYYYMMDD_grupo_escenario_NN_eve.json.gz`. |
| **EDA** | Exploratory Data Analysis — Análisis Exploratorio de Datos. Estudio estadístico de las features para entender su distribución, rango y poder discriminante antes de entrenar el modelo. |
| **Escenario** | Patrón de tráfico reproducible con herramienta, duración y objetivo definidos. Permite repetir la misma condición de red con resultados comparables. |

---

## Topología del laboratorio

```
┌─────────────────────────────────────────────────────────┐
│                 Red 192.168.0.0/24                       │
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐   │
│  │ Win11        │        │ Ubuntu Desktop           │   │
│  │ 192.168.0.10 │        │ 192.168.0.20 ◄─ ADMIN   │   │
│  └──────────────┘        └──────────────────────────┘   │
│                                      │                   │
│  ┌──────────────┐        ┌──────────────────────────┐   │
│  │ Kali Linux   │        │ Ubuntu Sensor            │   │
│  │ 192.168.0.100│        │ 192.168.0.110            │   │
│  │ ATACANTE     │        │ Suricata 7.0.3 ens35     │   │
│  └──────────────┘        │ Motor + Modelos          │   │
│                          └──────────────────────────┘   │
│                                      │                   │
│                          ┌──────────────────────────┐   │
│                          │ Ubuntu Server            │   │
│                          │ 192.168.0.120            │   │
│                          │ nginx:80  SSH:22         │   │
│                          └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

Suricata en el sensor escucha ens35 en modo promiscuo → captura TODO el tráfico del segmento.

---

## Qué se implementó

### Infraestructura de captura

| Componente | Versión / Configuración |
|---|---|
| Suricata | 7.0.3 — modo pasivo, AF-PACKET en ens35 |
| eve.json | `/var/log/suricata/eve.json` — JSON por línea |
| Rotación | `exportar_eve_por_escenario.sh` — comprime + `suricatasc reopen-log-files` |
| Registro | `registrar_bitacora.sh` → `docs/bitacora/bitacora_escenarios.txt` |

### Scripts de escenarios

```
scripts/capture/
├── A1_http_normal.sh        — curl/wget → :80  (10 min)
├── A2_ssh_legitimo.sh       — ssh → :22         (8 min)
├── A3_transferencia_legitima.sh — scp/wget      (10 min)
├── A4_trafico_sostenido.sh  — curl+ssh mixto    (15 min)
├── B1_syn_flood.sh          — hping3 -S --flood → :80
├── B2_port_scan.sh          — nmap -sS
├── B3_udp_flood.sh          — hping3 --udp --flood → :53
├── B4_icmp_flood.sh         — hping3 -1 --flood
├── B5_acceso_repetitivo.sh  — curl bucle rápido → :80
├── B6_bruteforce.sh         — hydra → :22
├── C1_http_syn_mixto.sh     — Desktop+Kali simultáneo
├── C2_ssh_portscan_mixto.sh
└── C3_descarga_udp_mixto.sh
```

---

## Escenarios capturados

### Grupo A — Tráfico Normal (desde Desktop 192.168.0.20)

| ID | Nombre | Duración | Herramienta | Por qué es importante |
|---|---|---|---|---|
| A1 | http_normal | 10 min | `curl`/`wget` → :80 | Define baseline HTTP real |
| A2 | ssh_legitimo | 8 min | `ssh` → :22 | Define baseline SSH real |
| A3 | transferencia_legitima | 10 min | `scp`/`wget` archivos | Tráfico de alta transferencia normal |
| A4 | trafico_sostenido | 15 min | `curl`+`ssh` mixto | Mezcla realista de servicios |

> **Por qué solo Desktop como origen normal:** el modelo IF aprende de lo que es "normal" para ESTA red. El tráfico legítimo viene de 192.168.0.20 hacia 192.168.0.120. Añadir otros orígenes introduciría variabilidad no controlada.

### Grupo B — Tráfico Anómalo (desde Kali 192.168.0.100)

| ID | Nombre | Herramienta y parámetros | Tipo de ataque |
|---|---|---|---|
| B1 | syn_flood | `hping3 -S --flood -p 80 192.168.0.120` | Volumétrico L4 — agota conexiones TCP |
| B2 | port_scan | `nmap -sS 192.168.0.120` | Reconocimiento — descubrimiento de servicios |
| B3 | udp_flood | `hping3 --udp --flood -p 53 192.168.0.120` | Volumétrico L4 — satura ancho de banda UDP |
| B4 | icmp_flood | `hping3 -1 --flood 192.168.0.120` | Volumétrico L3 — ping flood |
| B5 | acceso_repetitivo | `curl` en bucle rápido → :80 | Aplicación — sobrecarga HTTP |
| B6 | bruteforce_ssh | `hydra -t 4 -l root -P wordlist ssh://192.168.0.120` | Credenciales — fuerza bruta SSH |

### Grupo C — Mixto (Desktop + Kali simultáneos)

| ID | Componentes | Propósito |
|---|---|---|
| C1 | A1 (curl normal) + B1 (SYN flood) | Valida que Desktop no es bloqueado mientras Kali sí |
| C2 | A2 (SSH legítimo) + B2 (port scan) | Valida separación SSH real vs exploración |
| C3 | A3 (descarga) + B3 (UDP flood) | Valida continuidad de descarga bajo ataque UDP |

---

## Protocolo de una corrida completa

```bash
# 1. Verificar Suricata activo
systemctl is-active suricata

# 2. Verificar eve.json vacío o en rotación limpia
wc -l /var/log/suricata/eve.json

# 3. Ejecutar el escenario (ej: B1 SYN Flood)
FECHA=$(date +%Y%m%d); CORRIDA=01; HORA_INI=$(date +%T)
bash scripts/capture/B1_syn_flood.sh
HORA_FIN=$(date +%T)

# 4. Exportar eve.json → comprime + rota
bash scripts/capture/exportar_eve_por_escenario.sh $FECHA anom synflood $CORRIDA
# → data/raw/20260602_anom_synflood_01_eve.json.gz

# 5. Registrar en bitácora
bash scripts/evaluation/registrar_bitacora.sh \
  anom synflood 192.168.0.100 192.168.0.120 \
  $HORA_INI $HORA_FIN "hping3 -S --flood" \
  "20260602_anom_synflood_01_eve.json.gz"

# 6. Esperar mínimo 2 minutos antes de la siguiente corrida
sleep 120
```

---

## Análisis Exploratorio de Datos (EDA)

El EDA se realiza sobre el dataset completo (`data/dataset_comparacion.csv`) generado con las capturas de F1.

```bash
# Generar las 6 gráficas EDA
python3 scripts/eda_features.py
# → results/eda/eda_01_distribuciones.png  ... eda_06_stats_tabla.png
```

### Gráficas generadas

| Imagen | Qué muestra | Hallazgo clave |
|---|---|---|
| `eda_01_distribuciones.png` | Histogramas de las 14 features | bytes_toclient tiene cola larga en ataques volumétricos |
| `eda_02_protocolo.png` | % TCP / UDP / ICMP por grupo | Grupo A: 85% TCP. Grupo B: mix según escenario |
| `eda_03_boxplots.png` | Rangos de features normal vs anómalo | `pkt_rate` y `byte_rate` son los más discriminantes |
| `eda_04_correlacion.png` | Mapa de calor — correlación entre features | `pkts_*` y `bytes_*` altamente correlacionadas (~0.95) |
| `eda_05_dest_ports.png` | Puertos destino más frecuentes | :80 (HTTP), :22 (SSH), :53 (UDP) dominan en ataques |
| `eda_06_stats_tabla.png` | Estadísticas completas (μ, σ, min, max) | `pkt_rate` normal: μ=18, anómalo: μ=8,420 |

> **Imágenes:** `docs/documentacion/imagenes/F1_captura/`

---

## Dataset final generado

```
data/
├── raw/                           ← 47 archivos .json.gz
│   ├── 20260602_normal_http_01_eve.json.gz
│   ├── 20260602_anom_synflood_01_eve.json.gz
│   └── ...
├── dataset_comparacion.csv        ← 25,428 flujos etiquetados (normal/anómalo)
└── normal_holdout.csv             ← 13,427 flujos normales (sale de F2)

docs/bitacora/
└── bitacora_escenarios.txt        ← 64 entradas registradas
```

**667,420 flujos totales** capturados en eve.json a través de todas las corridas.

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado |
|---|---|---|
| CA-F1-01 | Suricata captura en ens35 modo pasivo | ✅ Activo — 500MB eve.json |
| CA-F1-02 | Mínimo 9 escenarios distintos capturados | ✅ 13 escenarios (A1-A4, B1-B6, C1-C3) |
| CA-F1-03 | ≥ 1 corrida por escenario archivada en `.gz` | ✅ 47 capturas |
| CA-F1-04 | Nomenclatura `YYYYMMDD_grupo_escenario_NN` | ✅ Todas las capturas |
| CA-F1-05 | Bitácora con timestamp por corrida | ✅ 64 entradas |
| CA-F1-06 | eve.json rotado correctamente post-corrida | ✅ `suricatasc reopen-log-files` |

---

## Argumento de defensa

> "F1 no es solo 'capturar tráfico'. Diseñamos 13 escenarios distintos que representan el espectro real de tráfico en una red corporativa: 4 escenarios de uso legítimo y 6 vectores de ataque reconocidos (OWASP, MITRE ATT&CK). Los escenarios mixtos del Grupo C son especialmente valiosos porque prueban que el sistema discrimina entre tráfico normal y anómalo cuando ocurren simultáneamente, que es exactamente la condición real. El EDA confirmó que las 14 features elegidas son discriminantes: la tasa de paquetes en un SYN flood (8,420 pkt/s) es 467 veces mayor que en tráfico normal (18 pkt/s)."
