# FASE 2 — Captura de Tráfico

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fechas de ejecución:** 2 de junio 2026 – 4 de junio 2026  

---

## Objetivo de la fase

Generar un dataset etiquetado de flujos de red capturados con Suricata que represente fielmente tanto el tráfico legítimo del laboratorio como los ataques controlados. Este dataset es la entrada del modelo de detección de anomalías (F3).

---

## 1. Plan de captura

**Archivo de referencia:** `docs/plan_captura.txt`

Se definieron tres grupos de escenarios con lógica de corridas:

| Grupo | Origen | Destino | Descripción |
|---|---|---|---|
| **A — Normal** | Desktop 192.168.0.20 | Server 192.168.0.120 | Tráfico legítimo |
| **B — Anómalo** | Kali 192.168.0.100 | Server 192.168.0.120 | Ataques controlados |
| **C — Mixto** | Desktop + Kali | Server 192.168.0.120 | Ambos simultáneos |

**Convención de nombres de archivos:**
```
YYYYMMDD_grupo_escenario_NN_eve.json.gz
Ejemplo: 20260602_normal_http_01_eve.json.gz
         20260602_anom_synflood_01_eve.json.gz
         20260602_mixto_http_syn_01_eve.json.gz
```

**Pausa entre corridas:** mínimo 2 minutos para separar flujos en el `eve.json`.

---

## 2. Escenarios del Grupo A — Tráfico Normal

Ejecutados desde **Ubuntu Desktop (192.168.0.20)** hacia **Ubuntu Server (192.168.0.120)**.

| Script | Escenario | Herramienta | Duración | Justificación académica |
|---|---|---|---|---|
| `A1_http_normal.sh` | HTTP normal | curl, wget | 10 min | Tráfico web cotidiano |
| `A2_ssh_legitimo.sh` | SSH legítimo | ssh | 8 min | Administración remota normal |
| `A3_transferencia_legitima.sh` | Transferencia | scp, wget | 10 min | Transferencia de archivos legítima |
| `A4_trafico_sostenido.sh` | Sostenido mixto | curl + ssh | 15 min | Tráfico continuo realista |

**Scripts ubicados en:** `scripts/capture/`

---

## 3. Escenarios del Grupo B — Tráfico Anómalo

Ejecutados desde **Kali Linux (192.168.0.100)** contra **Ubuntu Server (192.168.0.120)**.

**Archivo de referencia:** `docs/guion_ataques.txt`

| Script | Escenario | Herramienta | Comando | Justificación |
|---|---|---|---|---|
| `B1_syn_flood.sh` | SYN Flood | hping3 | `hping3 -S -p 80 -i u5000 --rand-source` | Cloudflare Q2-2025 · ENISA 2025 vector L3/L4 |
| `B2_port_scan.sh` | Port Scan | nmap | `nmap -sS -p 1-1024` | MITRE ATT&CK T1046 · Fortinet 2026 |
| `B3_udp_flood.sh` | UDP Flood | hping3 | `hping3 --udp -p 53 -i u5000 --rand-source` | Cloudflare Q2-2025 amplification |
| `B4_icmp_flood.sh` | ICMP Flood | hping3 | `hping3 -1 --flood` | Prueba de robustez del sensor |
| `B5_acceso_repetitivo.sh` | HTTP Abuse | curl en bucle | `while true; do curl ...; done` | Cloudflare app layer abuse |
| `B6_bruteforce.sh` | Brute Force SSH | hydra | `hydra -l m4rk -P rockyou.txt ssh://` | DBIR 2024 · Fortinet 2026 |

---

## 4. Escenarios del Grupo C — Tráfico Mixto

Ejecutados con **Desktop y Kali simultáneos**, coordinados desde el Desktop.

| Script | Tráfico normal | Tráfico anómalo | Duración |
|---|---|---|---|
| `C1_http_syn_mixto.sh` | curl HTTP (Desktop) | SYN flood --rand-source (Kali) | 10 min |
| `C2_ssh_portscan_mixto.sh` | SSH legítimo (Desktop) | nmap -sS (Kali) | 10 min |
| `C3_descarga_udp_mixto.sh` | wget descargas (Desktop) | UDP flood (Kali) | 10 min |

---

## 5. Mecanismo de exportación y registro

### Script de exportación

**Archivo:** `scripts/capture/exportar_eve_por_escenario.sh`

Al finalizar cada corrida, el script de escenario llama vía SSH al sensor para:
1. Copiar el estado actual de `/var/log/suricata/eve.json`
2. Guardarlo en `data/raw/` con el nombre estandarizado
3. Comprimirlo con gzip

```bash
# Llamada al final de cada script de escenario:
ssh m4rk@192.168.0.110 \
  "bash scripts/capture/exportar_eve_por_escenario.sh $FECHA $GRUPO $ESCENARIO $CORRIDA"
```

### Script de bitácora

**Archivo:** `scripts/evaluation/registrar_bitacora.sh`

Registra automáticamente en `docs/bitacora/bitacora_escenarios.txt`:
```
FECHA | grupo | escenario | origen -> destino | hora_inicio - hora_fin | herramienta | archivo
```

---

## 6. Archivos generados — data/raw/

Se generaron **37 archivos** en `data/raw/` a lo largo de 3 fechas de captura:

### Grupo Normal (label=0)

| Archivo | Fecha | Tamaño |
|---|---|---|
| `20260602_normal_http_01_eve.json.gz` | 2026-06-02 | 533 KB |
| `20260602_normal_http_02_eve.json.gz` | 2026-06-02 | 39 KB |
| `20260602_normal_ssh_01_eve.json.gz` | 2026-06-02 | 5.3 KB |
| `20260602_normal_ssh_02_eve.json.gz` | 2026-06-02 | 82 KB |
| `20260602_normal_transferencia_01_eve.json.gz` | 2026-06-02 | 4.3 KB |
| `20260602_normal_transferencia_02_eve.json.gz` | 2026-06-02 | 7.4 KB |
| `20260602_normal_sostenido_01_eve.json.gz` | 2026-06-02 | 47 KB |
| `20260602_normal_sostenido_02_eve.json.gz` | 2026-06-02 | 19 KB |
| `20260604_normal_ssh_03` a `_10_eve.json.gz` | 2026-06-04 | ~28 KB c/u |
| `20260604_normal_transferencia_03` a `_10_eve.json.gz` | 2026-06-04 | ~7 KB c/u |

### Grupo Anómalo (label=1)

| Archivo | Escenario | Tamaño |
|---|---|---|
| `20260602_anom_synflood_01_eve.json.gz` | B1 SYN Flood | 4.6 MB |
| `20260602_anom_portscan_01_eve.json.gz` | B2 Port Scan | 719 KB |
| `20260602_anom_udpflood_01_eve.json.gz` | B3 UDP Flood | 699 KB |
| `20260602_anom_icmpflood_01_eve.json.gz` | B4 ICMP Flood | 856 KB |
| `20260602_anom_httpabuse_01_eve.json.gz` | B5 HTTP Abuse | 1.2 MB |
| `20260602_anom_bruteforce_01_eve.json.gz` | B6 Brute Force | 85 KB |

### Grupo Mixto (label=1)

| Archivo | Escenario | Tamaño |
|---|---|---|
| `20260602_mixto_http_syn_01_eve.json.gz` | C1 HTTP + SYN | 4.2 MB |
| `20260602_mixto_ssh_portscan_01_eve.json.gz` | C2 SSH + Scan | 31 KB |
| `20260602_mixto_descarga_udp_01_eve.json.gz` | C3 Descarga + UDP | 4.9 MB |

---

## 7. Bitácora de corridas

**Archivo:** `docs/bitacora/bitacora_escenarios.txt`  
**Total de entradas registradas:** 49 corridas

Extracto representativo:

```
2026-06-02 | normal | http         | 192.168.0.20 -> 192.168.0.120 | 01:09:22 - 01:19:23 | curl_wget
2026-06-02 | normal | ssh          | 192.168.0.20 -> 192.168.0.120 | 01:21:25 - 01:29:54 | ssh
2026-06-02 | normal | transferencia| 192.168.0.20 -> 192.168.0.120 | 01:31:56 - 01:42:21 | scp_wget
2026-06-02 | normal | sostenido    | 192.168.0.20 -> 192.168.0.120 | 01:44:23 - 01:59:40 | curl_ssh_mixto
2026-06-02 | anom   | synflood     | 192.168.0.100 -> 192.168.0.120| 03:12:25 - 03:14:25 | hping3
2026-06-02 | anom   | portscan     | 192.168.0.100 -> 192.168.0.120| 04:06:40 - 04:09:01 | nmap
2026-06-02 | anom   | udpflood     | 192.168.0.100 -> 192.168.0.120| 04:09:29 - 04:11:29 | hping3
2026-06-02 | anom   | icmpflood    | 192.168.0.100 -> 192.168.0.120| 04:13:41 - 04:15:41 | hping3
2026-06-02 | anom   | httpabuse    | 192.168.0.100 -> 192.168.0.120| 04:15:55 - 04:20:55 | curl
2026-06-02 | anom   | bruteforce   | 192.168.0.100 -> 192.168.0.120| 04:21:02 - 04:21:28 | hydra
2026-06-02 | mixto  | http_syn     | 192.168.0.20+100 -> .120      | 20:11:46 - 20:21:46 | curl+hping3
2026-06-02 | mixto  | ssh_portscan | 192.168.0.20+100 -> .120      | 09:41:13 - 09:51:13 | ssh+nmap
2026-06-02 | mixto  | descarga_udp | 192.168.0.20+100 -> .120      | 20:23:59 - 20:33:59 | wget+hping3
```

---

## 8. Procesamiento del dataset

### Parser EVE JSON → CSV

**Script:** `scripts/parser.py`  
**Salida:** `data/dataset_raw.csv`

Lee cada archivo `.gz` de `data/raw/`, filtra eventos `event_type=flow` y extrae las columnas:

```
timestamp, flow_id, src_ip, src_port, dest_ip, dest_port,
proto, app_proto, bytes_toserver, bytes_toclient,
pkts_toserver, pkts_toclient, flow_start, flow_end,
duration, escenario, corrida, label
```

**Etiquetado:** `label=0` para archivos con prefijo `normal_`, `label=1` para `anom_` y `mixto_`.

### Etiquetado refinado

**Script:** `scripts/etiquetar_limpiar.py`  
**Salida:** `data/dataset_labeled.csv`

Refina las etiquetas por `src_ip`:
- `src_ip == 192.168.0.20` → `label=0` (Desktop, tráfico normal)
- `src_ip == 192.168.0.100` → `label=1` (Kali, tráfico anómalo)
- IPs random (floods `--rand-source`) → `label=1`

### Limpieza del dataset

**Script:** `scripts/etiquetar_limpiar.py`  
**Salida:** `data/dataset_clean.csv`

| Operación | Registros eliminados |
|---|---|
| Duplicados por `flow_id` | 34 |
| IPs inválidas (broadcast, multicast) | 35,236 |
| **Total conservados** | **376,827** |

### Partición temporal (70/15/15)

**Script:** `scripts/particionar_estadisticos.py`  
**Salida:** `data/train.csv`, `data/val.csv`, `data/test.csv`

Partición cronológica para evitar fuga temporal:

| Conjunto | Flows | Normal | Anómalo |
|---|---|---|---|
| `train.csv` | 263,778 | 11,669 | 252,109 |
| `val.csv` | 56,524 | 0 | 56,524 |
| `test.csv` | 56,525 | 0 | 56,525 |

---

## 9. Estadísticos del dataset

**Archivo:** `data/resumen_estadistico.txt` (también en `docs/resumen_estadistico.txt`)

| Métrica | Valor |
|---|---|
| Total flows (dataset_clean) | 376,827 |
| Label=0 Normal | 11,669 (3.1%) |
| Label=1 Anómalo | 365,158 (96.9%) |
| Protocolo TCP | 225,718 (59.9%) |
| Protocolo UDP | 130,944 (34.7%) |
| Protocolo ICMP | 20,165 (5.4%) |
| Ventana temporal | 04:09 – 20:34 del 2026-06-02 |

**Distribución por escenario (dataset_clean):**

| Escenario | Flows | Label |
|---|---|---|
| anom_synflood | 94,841 | 1 |
| mixto_descarga | 109,839 | 1 |
| mixto_http | 95,157 | 1 |
| anom_httpabuse | 21,758 | 1 |
| anom_icmpflood | 20,200 | 1 |
| normal_http | 11,333 | 0 |
| anom_udpflood | 15,815 | 1 |
| anom_portscan | 3,297 | 1 |
| anom_bruteforce | 2,062 | 1 |
| normal_sostenido | 251 | 0 |
| normal_transferencia | 29 | 0 |

---

## 10. Criterios de cierre de F2

| Criterio | Estado |
|---|---|
| Plan de captura documentado (`plan_captura.txt`) | ✅ |
| Guión de ataques documentado (`guion_ataques.txt`) | ✅ |
| Scripts A1-A4 ejecutados (tráfico normal) | ✅ |
| Scripts B1-B6 ejecutados (tráfico anómalo) | ✅ |
| Scripts C1-C3 ejecutados (tráfico mixto) | ✅ |
| 37 archivos eve.json exportados en `data/raw/` | ✅ |
| Bitácora con 49 entradas de trazabilidad | ✅ |
| `parser.py` → `dataset_raw.csv` (412,097 flows) | ✅ |
| `dataset_labeled.csv` con etiquetas refinadas | ✅ |
| `dataset_clean.csv` (376,827 flows limpios) | ✅ |
| Partición train/val/test (70/15/15) | ✅ |
| `resumen_estadistico.txt` generado | ✅ |

**F2 CERRADA ✅ — 4 de junio 2026**

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| `plan_captura.txt` | `docs/plan_captura.txt` | Plan de captura documentado |
| `guion_ataques.txt` | `docs/guion_ataques.txt` | Comandos y justificación de ataques |
| `bitacora_escenarios.txt` | `docs/bitacora/bitacora_escenarios.txt` | **Trazabilidad de todas las corridas** |
| `A1_http_normal.sh` … `A4` | `scripts/capture/` | Scripts tráfico normal |
| `B1_syn_flood.sh` … `B6` | `scripts/capture/` | Scripts tráfico anómalo |
| `C1_http_syn_mixto.sh` … `C3` | `scripts/capture/` | Scripts tráfico mixto |
| `exportar_eve_por_escenario.sh` | `scripts/capture/` | Exportación automática |
| `registrar_bitacora.sh` | `scripts/evaluation/` | Registro de bitácora |
| `parser.py` | `scripts/parser.py` | Parser EVE JSON → CSV |
| `etiquetar_limpiar.py` | `scripts/etiquetar_limpiar.py` | Etiquetado y limpieza |
| `particionar_estadisticos.py` | `scripts/particionar_estadisticos.py` | Partición y estadísticos |
| `dataset_raw.csv` | `data/dataset_raw.csv` | Dataset sin procesar (412,097 flows) |
| `dataset_labeled.csv` | `data/dataset_labeled.csv` | Dataset etiquetado |
| `dataset_clean.csv` | `data/dataset_clean.csv` | **Dataset limpio final (376,827 flows)** |
| `train.csv / val.csv / test.csv` | `data/` | Particiones para entrenamiento |
| `resumen_estadistico.txt` | `data/` y `docs/` | Estadísticos del dataset |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-producto/`
