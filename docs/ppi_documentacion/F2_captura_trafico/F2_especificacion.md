# F2 — Especificación Técnica: Captura de Tráfico

## Objetivo
Capturar tráfico de red en los tres grupos (normal, anómalo, mixto) mediante Suricata y procesarlo para generar los datasets de entrenamiento y evaluación.

## Scripts involucrados

| Script | Entrada | Proceso | Salida |
|---|---|---|---|
| `scripts/capture/exportar_eve_por_escenario.sh` | eve.json activo | gzip + truncate + suricatasc reopen-log-files | `data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz` |
| `scripts/evaluation/registrar_bitacora.sh` | parámetros de corrida | append a bitácora | `docs/bitacora/bitacora_escenarios.txt` |
| `scripts/parser.py` | `data/raw/*.eve.json.gz` | parsea flows EVE JSON | `data/dataset_raw.csv` |
| `scripts/etiquetar_limpiar.py` | `data/dataset_raw.csv` | label=0/1, dedup, filtros IP | `data/dataset_clean.csv` |
| `scripts/particionar_estadisticos.py` | `data/dataset_clean.csv` | split 70/15/15 cronológico | `data/train.csv`, `data/val.csv`, `data/test.csv` |

## Escenarios capturados

### Grupo A — Tráfico normal (origen: Desktop 192.168.0.20, label=0)
| ID | Escenario | Herramienta | Duración |
|---|---|---|---|
| A1 | http_normal | `curl` bucle → nginx :80 | 10 min |
| A2 | ssh_legitimo | `ssh` sesión interactiva → :22 | 8 min |
| A3 | transferencia_legitima | `scp` / `wget` archivos → :80 | 10 min |
| A4 | trafico_sostenido | curl + ssh mixto | 15 min |

### Grupo B — Tráfico anómalo (origen: Kali 192.168.0.100, label=1)
| ID | Escenario | Herramienta | Puerto |
|---|---|---|---|
| B1 | syn_flood | `hping3 -S -p 80 -i u5000` | TCP/80 |
| B2 | port_scan | `nmap -sS -p 1-1024` | 1–1024 |
| B3 | udp_flood | `hping3 --udp -p 53 -i u5000` | UDP/53 |
| B4 | icmp_flood | `hping3 -1 --flood` | ICMP |
| B5 | http_abuse | `curl` bucle rápido → :80 | TCP/80 |
| B6 | bruteforce | `hydra -l root -P wordlist :22` | TCP/22 |

### Grupo C — Tráfico mixto (Desktop + Kali simultáneos, label=1 para flows anómalos)
| ID | Escenario | Desktop | Kali |
|---|---|---|---|
| C1 | http_synflood | curl → :80 | hping3 -S → :80 |
| C2 | ssh_portscan | ssh → :22 | nmap -sS |
| C3 | transfer_udpflood | scp/wget | hping3 --udp → :53 |

## Nomenclatura de archivos raw
```
YYYYMMDD_grupo_escenario_NN_eve.json.gz
Ejemplo: 20260615_anom_synflood_01_eve.json.gz
         20260616_mixto_http_synflood_01_eve.json.gz
```
Total archivos capturados: **51 archivos** en `data/raw/`

## Secuencia de ejecución F2
```bash
# 1. Ejecutar escenarios (en Desktop)
bash scripts_f2/grupoA/run_grupo_A.sh 01
bash scripts_f2/grupoB/run_grupo_B.sh 01    # motor DETENIDO
bash scripts_f2/grupoC/run_grupo_C.sh 01    # motor DETENIDO

# 2. Procesar en sensor
cd /home/m4rk/ppi-surikata-producto
python3 scripts/parser.py
python3 scripts/etiquetar_limpiar.py
python3 scripts/particionar_estadisticos.py
```

## Parámetros clave del dataset final

| Métrica | Valor |
|---|---|
| Flows normales (train) | 53,708 |
| Flows anómalos (eval) | 598,285 |
| Split | 70% train / 15% val / 15% test (cronológico) |
| Features extraídas | 14 (ver F3) |
| Pausa entre escenarios | ≥ 2 minutos (para evitar contaminación) |
