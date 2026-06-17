# F2 — Especificación Técnica: Captura y Preprocesamiento de Tráfico

## 1. Objetivo

Capturar tráfico de red real en tres grupos (normal, anómalo, mixto) usando Suricata 7.0.3,
y procesarlo mediante una cadena de scripts para generar los datasets `train.csv`, `val.csv`
y `test.csv` listos para entrenar el modelo Isolation Forest en F3.

---

## 2. Entradas

| Entrada | Origen | Descripción |
|---|---|---|
| Topología operativa (F1) | F1 completada | Suricata activo en ens35, ipsets creados, SSH keys listas |
| `/var/log/suricata/eve.json` | sensor 192.168.0.110 | Log EVE JSON con eventos de red en tiempo real |
| `scripts_f2/grupoA/run_grupo_A.sh` | Desktop 192.168.0.20 | Orquestador de escenarios normales |
| `scripts_f2/grupoB/run_grupo_B.sh` | Desktop 192.168.0.20 | Orquestador de escenarios anómalos |
| `scripts_f2/grupoC/run_grupo_C.sh` | Desktop 192.168.0.20 | Orquestador de escenarios mixtos |
| Kali Linux 192.168.0.100 | VM atacante | Herramientas: hping3, nmap, hydra, sshpass |

**Requisito:** `ppi-motor.service` debe estar **DETENIDO** durante toda F2 para no filtrar
flows de Kali antes de capturarlos.

---

## 3. Salidas

| Salida | Ruta (sensor) | Descripción |
|---|---|---|
| Capturas raw | `data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz` | 51 archivos comprimidos (41 con ppi-motor, 10 mixtos) |
| Bitácora | `docs/bitacora/bitacora_escenarios.txt` | Registro de cada corrida: fechas, origen, destino, herramienta |
| Dataset raw | `data/dataset_raw.csv` | Todos los flows parseados, sin limpiar |
| Dataset limpio | `data/dataset_clean.csv` | Deduplicado, filtros IP aplicados, con label 0/1 |
| Dataset entrenamiento | `data/train.csv` | 70% cronológico — solo flows normales (label=0) |
| Dataset validación | `data/val.csv` | 15% cronológico — mixto (label=0 y label=1) |
| Dataset test | `data/test.csv` | 15% cronológico — solo flows anómalos (label=1) para evaluar FPR en F3 |
| Lista de features | `models/features.csv` | 14 nombres de columnas usadas por el modelo |

---

## 4. Escenarios de captura

### Grupo A — Tráfico normal (origen: Desktop 192.168.0.20 → Server 192.168.0.120)

| ID | Nombre | Herramienta | Puerto | Duración | Label |
|---|---|---|---|---|---|
| A1 | http_normal | `curl` en bucle → nginx | TCP/80 | 10 min | 0 |
| A2 | ssh_legitimo | `ssh` sesión interactiva | TCP/22 | 8 min | 0 |
| A3 | transferencia_legitima | `scp` / `wget` archivos grandes | TCP/80, TCP/22 | 10 min | 0 |
| A4 | trafico_sostenido | curl + ssh mixto continuo | TCP/80, TCP/22 | 15 min | 0 |

### Grupo B — Tráfico anómalo (origen: Kali 192.168.0.100 → Server 192.168.0.120)

| ID | Nombre | Herramienta | Flags | Puerto | Duración | Label |
|---|---|---|---|---|---|---|
| B1 | syn_flood | `hping3 -S --flood` | SYN sin completar handshake | TCP/80 | 10 min | 1 |
| B2 | port_scan | `nmap -sS -p 1-1024` en bucle | SYN scan sigiloso | 1–1024 | 10 min | 1 |
| B3 | udp_flood | `hping3 --udp --flood -p 53` | UDP masivo | UDP/53 | 10 min | 1 |
| B4 | icmp_flood | `hping3 -1 --flood` | ICMP echo masivo | ICMP | 10 min | 1 |
| B5 | http_abuse | `curl` bucle agresivo → nginx | HTTP GET repetitivo | TCP/80 | 10 min | 1 |
| B6 | bruteforce | `hydra -l root -P wordlist ssh://` | Intentos de login masivos | TCP/22 | 10 min | 1 |

### Grupo C — Tráfico mixto (Desktop + Kali simultáneos)

| ID | Nombre | Desktop (normal) | Kali (anómalo) | Duración |
|---|---|---|---|---|
| C1 | http_synflood | curl → nginx :80 | hping3 -S --flood → :80 | 10 min |
| C2 | ssh_portscan | ssh → :22 | nmap -sS -p 1-1024 | 10 min |
| C3 | transfer_udpflood | scp/wget | hping3 --udp --flood → :53 | 10 min |

**Nota:** En Grupo C, el motor debe estar **detenido**. Los flows se etiquetan por IP de origen
en `etiquetar_limpiar.py`: `192.168.0.100` → label=1, `192.168.0.20` → label=0.

---

## 5. Nomenclatura de archivos capturados

```
YYYYMMDD_grupo_escenario_NN_eve.json.gz

Ejemplos:
  20260602_normal_http_01_eve.json.gz        ← Grupo A, fecha 02-jun, corrida 01
  20260615_anom_synflood_01_eve.json.gz      ← Grupo B, fecha 15-jun
  20260616_mixto_http_synflood_01_eve.json.gz ← Grupo C, fecha 16-jun
```

**Total archivos en `data/raw/`:** 51 archivos (28 normales + 13 anómalos + 10 mixtos)

---

## 6. Pipeline de procesamiento — scripts y secuencia

### 6.1 `scripts/capture/exportar_eve_por_escenario.sh`

Ejecutado automáticamente al final de cada escenario (desde el script run_grupo_X.sh vía SSH).

```bash
# Llamada desde run_grupo_X.sh
ssh m4rk@192.168.0.110 "bash exportar_eve_por_escenario.sh FECHA GRUPO ESCENARIO CORRIDA"
```

**Proceso interno:**
1. `gzip -c /var/log/suricata/eve.json > data/raw/YYYYMMDD_*.eve.json.gz`
2. `truncate -s 0 /var/log/suricata/eve.json` — vacía el archivo para la siguiente captura
3. `suricatasc -c reopen-log-files` — Suricata reabre el handle del archivo

**Requisito crítico:** esperar ≥2 minutos entre escenarios para que Suricata cierre los flows
TCP abiertos (timeout ~60 s) antes de la siguiente captura.

---

### 6.2 `scripts/evaluation/registrar_bitacora.sh`

Agrega una línea al final de `docs/bitacora/bitacora_escenarios.txt`:

```
2026-06-15 | anom | synflood | 192.168.0.100 -> 192.168.0.120 | 21:44:57 - 21:55:02 | hping3 | 20260615_anom_synflood_01_eve.json.gz
```

---

### 6.3 `scripts/parser.py`

**Entrada:** todos los archivos `data/raw/*.eve.json.gz`  
**Salida:** `data/dataset_raw.csv`

Lee cada archivo comprimido, filtra únicamente eventos `event_type == "flow"`, y extrae
las 14 features del flujo (ver sección 7). Los campos que no existen en el evento se rellenan
con 0.

```python
# Campos EVE JSON mapeados a features
flow = event.get("flow", {})
pkts_toserver   = flow.get("pkts_toserver", 0)
bytes_toserver  = flow.get("bytes_toserver", 0)
pkts_toclient   = flow.get("pkts_toclient", 0)
bytes_toclient  = flow.get("bytes_toclient", 0)
# duration = diferencia entre flow.start y flow.end en segundos
proto           = event.get("proto", "").lower()
dest_port       = event.get("dest_port", 0)
```

---

### 6.4 `scripts/etiquetar_limpiar.py`

**Entrada:** `data/dataset_raw.csv`  
**Salida:** `data/dataset_clean.csv`

Proceso en orden:

1. **Etiquetado por IP de origen:**
   - `src_ip == 192.168.0.100` → `label = 1` (anómalo / Kali)
   - `src_ip == 192.168.0.20` → `label = 0` (normal / Desktop)
   - Otros → descartar

2. **Filtro de IPs de whitelist:** elimina flows entre nodos de infraestructura
   (sensor→servidor, gateway, etc.) que distorsionarían el modelo.

3. **Deduplicación:** elimina filas con `flow_id` duplicado (flujos contados dos veces
   por Suricata al cambiar de archivo).

4. **Eliminación de NaN:** filas con features vacías → descartar.

---

### 6.5 `scripts/particionar_estadisticos.py`

**Entrada:** `data/dataset_clean.csv`  
**Salida:** `data/train.csv`, `data/val.csv`, `data/test.csv`

Partición **cronológica** (no aleatoria) para respetar el orden temporal:

| Partición | Porcentaje | Contenido | Uso en F3 |
|---|---|---|---|
| `train.csv` | 70% | Solo label=0 (normal) | Entrenamiento del IF (one-class) |
| `val.csv` | 15% | label=0 y label=1 | Ajuste de hiperparámetros |
| `test.csv` | 15% | Solo label=1 (anómalo) | Evaluación FPR / AUC |

**Nota metodológica:** `test.csv` contiene únicamente flows anómalos porque el IF es
un clasificador one-class. El FPR se mide por separado sobre `normal_holdout.csv`
(20% de los flows normales retenidos).

---

## 7. Las 14 features del modelo

Extraídas por `parser.py` de cada evento `flow` del eve.json:

| # | Feature | Descripción | Tipo |
|---|---|---|---|
| 1 | `pkts_toserver` | Paquetes enviados al servidor | int |
| 2 | `pkts_toclient` | Paquetes recibidos del servidor | int |
| 3 | `bytes_toserver` | Bytes enviados al servidor | int |
| 4 | `bytes_toclient` | Bytes recibidos del servidor | int |
| 5 | `duration` | Duración del flujo en segundos | float |
| 6 | `pkt_rate` | Tasa de paquetes = (pkts_to + pkts_from) / duration | float |
| 7 | `byte_rate` | Tasa de bytes = (bytes_to + bytes_from) / duration | float |
| 8 | `pkt_ratio` | pkts_toserver / (pkts_toserver + pkts_toclient) | float |
| 9 | `byte_ratio` | bytes_toserver / (bytes_toserver + bytes_toclient) | float |
| 10 | `avg_pkt_size` | (bytes_to + bytes_from) / (pkts_to + pkts_from) | float |
| 11 | `is_tcp` | 1 si proto == TCP, 0 si no | int |
| 12 | `is_udp` | 1 si proto == UDP, 0 si no | int |
| 13 | `is_icmp` | 1 si proto == ICMP, 0 si no | int |
| 14 | `dest_port` | Puerto de destino del flujo | int |

**Por qué estas features:** capturan comportamiento volumétrico (bytes, paquetes),
temporal (duración, tasas), de simetría (ratios toserver/toclient) y de protocolo.
Los ataques de flooding tienen `pkt_rate` y `byte_rate` extremadamente altos con
`duration` muy corta; los port scans tienen muchos flows con `dest_port` variado y
`pkts_toserver == 1`.

---

## 8. Secuencia técnica completa F2

```bash
# ─── FASE DE CAPTURA (ejecutar desde Desktop 192.168.0.20) ───────────────────

# PRE-REQUISITO: detener el motor en el sensor
ssh m4rk@192.168.0.110 "sudo systemctl stop ppi-motor.service"

# Grupo A — tráfico normal (43 min total + pausas)
bash /home/m4rk/Descargas/scripts_f2/grupoA/run_grupo_A.sh 01

# Pausa mínima 2 min entre grupos
sleep 120

# Grupo B — tráfico anómalo (63 min total + pausas); motor DETENIDO
bash /home/m4rk/Descargas/scripts_f2/grupoB/run_grupo_B.sh 01

sleep 120

# Grupo C — tráfico mixto (34 min total + pausas); motor DETENIDO
bash /home/m4rk/Descargas/scripts_f2/grupoC/run_grupo_C.sh 01

# ─── FASE DE PROCESAMIENTO (ejecutar en sensor 192.168.0.110) ────────────────

ssh m4rk@192.168.0.110 "
  source /home/m4rk/ppi-sensor/venv/bin/activate
  cd /home/m4rk/ppi-surikata-producto

  # Paso 1: parsear todos los .gz → dataset_raw.csv
  python3 scripts/parser.py

  # Paso 2: etiquetar, limpiar, deduplicar → dataset_clean.csv
  python3 scripts/etiquetar_limpiar.py

  # Paso 3: particionar cronológico 70/15/15 → train/val/test
  python3 scripts/particionar_estadisticos.py
"
```

---

## 9. Volumen de datos capturados (resultado real)

| Archivo / Dataset | Tamaño | Flows |
|---|---|---|
| 28 capturas normales (Grupo A) | ~15 MB comprimido | 67,135 flows |
| 13 capturas anómalas (Grupo B) | ~2.5 GB comprimido | 598,285 flows |
| 10 capturas mixtas (Grupo C) | ~1.8 GB comprimido | ~180,000 flows |
| `dataset_raw.csv` | ~480 MB | >800,000 filas |
| `dataset_clean.csv` | ~210 MB | ~665,420 filas |
| `train.csv` | ~50 MB | 53,708 flows (label=0) |
| `val.csv` | ~90 MB | ~99,800 flows |
| `test.csv` | ~70 MB | ~99,700 flows (label=1) |
| `normal_holdout.csv` | ~10 MB | 13,427 flows (label=0) |

---

## 10. Criterios de éxito (salida de F2)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| Archivos raw generados | `ls data/raw/*.gz \| wc -l` | ≥ 41 archivos |
| Bitácora registrada | `wc -l docs/bitacora/bitacora_escenarios.txt` | ≥ 41 líneas |
| dataset_raw.csv generado | `wc -l data/dataset_raw.csv` | > 500,000 filas |
| dataset_clean.csv sin NaN | `python3 -c "import pandas as pd; print(pd.read_csv('data/dataset_clean.csv').isna().sum().sum())"` | 0 |
| train.csv solo label=0 | `python3 -c "import pandas as pd; print(pd.read_csv('data/train.csv').label.unique())"` | `[0]` |
| test.csv solo label=1 | `python3 -c "import pandas as pd; print(pd.read_csv('data/test.csv').label.unique())"` | `[1]` |
| 14 features presentes | `head -1 data/train.csv` | columnas pkts_toserver…dest_port presentes |
| Split 70/15/15 | Contar filas de cada CSV | Proporciones aproximadas |

**F2 se considera COMPLETADA** cuando `train.csv`, `val.csv` y `test.csv` existen
sin errores y con las 14 features correctas. Estos archivos son la entrada directa de F3.
