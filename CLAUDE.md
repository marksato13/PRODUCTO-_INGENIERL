# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

PPI universitario (Universidad Peruana Unión). Sistema de detección temprana de comportamientos anómalos en redes de datos mediante Isolation Forest + control inline con iptables/ipset.
- Estudiante: Rubén Mark Salazar Tocas
- Asesores: Ing. Nemias Saboya Rios, Ing. Fernando Manuel Asin Gomez
- **Estado: todas las fases (F1–F6) completadas y validadas**

## Topología del laboratorio

| IP | VM | Rol |
|---|---|---|
| 192.168.0.10 | Win11 | Cliente |
| 192.168.0.20 | Ubuntu Desktop | Admin / origen tráfico normal — AQUÍ CORRE CLAUDE CODE |
| 192.168.0.100 | Kali Linux | Origen tráfico anómalo |
| 192.168.0.110 | Ubuntu Suricata | Sensor — Suricata 7.0.3 en ens35, eve.json en /var/log/suricata/eve.json |
| 192.168.0.120 | Ubuntu Server | Servicio — nginx:80, SSH:22 |

- Usuario en todas las VMs: `m4rk` / contraseña SSH: `cisco123`
- SSH keys configuradas desde Desktop → Sensor y Desktop → Server

## Comandos frecuentes

```bash
# Verificar conectividad al arrancar
ssh m4rk@192.168.0.110 "echo OK sensor"
ssh m4rk@192.168.0.120 "echo OK servidor"

# Iniciar/detener el motor de decisión (en el sensor)
sudo systemctl start ppi-motor.service
sudo systemctl stop ppi-motor.service
sudo systemctl status ppi-motor.service

# Dashboard en tiempo real (lee motor_decision.log cada 3s)
python3 /home/m4rk/ppi-surikata-producto/scripts/dashboard.py

# Control manual de bloqueos
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh <ip> BLOCK|LIMIT|UNBLOCK [timeout_seg]

# Ver bitácora de corridas
cat /home/m4rk/ppi-surikata-producto/docs/bitacora/bitacora_escenarios.txt

# Ver log del motor
tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log

# Dashboard web (navegador) — corre en sensor puerto 8080
# Acceder desde Desktop: http://192.168.0.110:8080
# Iniciar si no está corriendo:
ssh m4rk@192.168.0.110 "cd ppi-surikata-producto && nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &"
```

## Arquitectura del MVP (scripts en `MVP/scripts/`)

El pipeline tiene 6 fases en cadena; cada script espera los outputs del anterior:

```
eve.json (Suricata)
   │
   ├─ parser.py              F2 — eve.json.gz → dataset_raw.csv
   ├─ etiquetar_limpiar.py   F2 — raw → labeled → clean (dedup, filtros IP)
   ├─ particionar_estadisticos.py  F2 — clean → train/val/test (70/15/15 cronológico)
   │
   ├─ fase3_isolation_forest.py    F3 — entrena IF(n=300), guarda models/isolation_forest.pkl + scaler.pkl
   ├─ auc_roc_umbrales.py          F3/F4 — deriva τ1/τ2 de la curva ROC
   │
   ├─ motor_decision.py     F4+F5 — tail eve.json → features → score → PERMIT/LIMIT/BLOCK vía ipset
   ├─ enforce.sh             F5 — control manual ipset (ppi_blocked / ppi_limited)
   │
   ├─ f6_corridas.py         F6 — validación batch de todas las corridas
   ├─ auc_por_escenario.py   F6 — AUC-ROC desglosado por escenario
   ├─ dashboard.py           Live — estadísticas desde motor_decision.log (terminal)
   └─ dashboard_web.py       Live — dashboard web Flask+SSE en :8080 (browser)
```

### Rutas clave en el sensor (192.168.0.110)

```
/home/m4rk/ppi-surikata-producto/
├── scripts/
│   ├── capture/exportar_eve_por_escenario.sh   ← gzip + rota eve.json al final de cada corrida
│   └── evaluation/registrar_bitacora.sh        ← escribe línea en bitacora_escenarios.txt
├── data/
│   ├── raw/          ← eve.json.gz por corrida (YYYYMMDD_grupo_escenario_NN_eve.json.gz)
│   ├── dataset_clean.csv
│   ├── train.csv / val.csv / test.csv
├── models/
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   └── features.csv   ← lista de 14 features usadas
├── results/
│   ├── motor_decision.log
│   ├── umbrales_finales.txt      ← τ1/τ2 canónicos (sincronizados con metricas_offline.txt)
│   ├── metricas_offline.txt      ← fuente de τ leída por el motor en arranque
│   ├── latencia_pipeline.txt
│   ├── resultados_f6_completo.csv ← 40 corridas F6
│   ├── resultados_f6_README.txt  ← notas sobre campos del CSV
│   └── graficas_f6/              ← 7 figuras PNG 300 DPI para informe
└── docs/bitacora/bitacora_escenarios.txt
```

### Features del modelo (14)

`pkts_toserver`, `pkts_toclient`, `bytes_toserver`, `bytes_toclient`, `duration`, `pkt_rate`, `byte_rate`, `pkt_ratio`, `byte_ratio`, `avg_pkt_size`, `is_tcp`, `is_udp`, `is_icmp`, `dest_port`

### Umbrales de decisión (modelo activo — retrenado 2026-06-16)

| Umbral | Valor | Acción | Criterio |
|---|---|---|---|
| τ1 | -0.4650 | score > τ1 → PERMIT | Youden index (TPR=99.35%, FPR=20.27%) |
| τ2 | -0.6118 | τ2 < score ≤ τ1 → LIMIT (hashlimit 100pkt/s) | FPR≤2% (TPR=17.01%) |
| — | — | score ≤ τ2 → BLOCK (DROP) | — |

Motor lee τ1/τ2 de `results/metricas_offline.txt` en cada arranque.

Detectores heurísticos adicionales sobre τ:
- **Brute Force SSH**: 15 intentos/60s → BLOCK (5 → LIMIT)
- **HTTP Abuse**: 100 req/30s → BLOCK (50 → LIMIT)

### Métricas finales validadas (F6 — 40 corridas, 2026-06-16)

- AUC-ROC: 0.8955 | Precision: 99.54% | Recall: 99.35% | F1: 0.9945
- Latencia P95: 34.8ms (req. < 500ms: CUMPLE) | ITL: 0% | Disponibilidad: 100%
- Lead Time detección (corrida 11, SYN Flood): 61.92s

## Escenarios de tráfico

### Grupo A — Normal (desde Desktop 192.168.0.20)
A1 http_normal (10 min, curl/wget → :80), A2 ssh_legitimo (8 min, ssh → :22),
A3 transferencia_legitima (10 min, scp/wget), A4 trafico_sostenido (15 min, curl+ssh mixto)

### Grupo B — Anómalo (desde Kali 192.168.0.100)
B1 syn_flood (hping3 -S --flood → :80), B2 port_scan (nmap -sS),
B3 udp_flood (hping3 --udp --flood → :53), B4 icmp_flood (hping3 -1 --flood),
B5 acceso_repetitivo (curl bucle → :80), B6 bruteforce (hydra → :22)

### Grupo C — Mixto (Desktop + Kali simultáneos)
C1 http_syn, C2 ssh_portscan, C3 descarga_udp

## Nomenclatura de archivos exportados

```
YYYYMMDD_grupo_escenario_NN_eve.json.gz
Ejemplo: 20260601_normal_http_01_eve.json.gz
         20260601_anom_synflood_01_eve.json.gz
```

## Patrón base de scripts de escenario

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

FECHA="$(date +%Y%m%d)"; HORA_INICIO="$(date +%T)"
END_TIME=$((SECONDS + DURACION_SEGUNDOS))
while [ $SECONDS -lt $END_TIME ]; do
  # tráfico del escenario
  sleep PAUSA
done
HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"
```

Al finalizar cada corrida: `exportar_eve_por_escenario.sh` comprime y rota el eve.json (truncate + suricatasc reopen-log-files). Esperar ≥2 min entre escenarios.

## Whitelist ipset (nunca bloquear)

`192.168.0.1`, `192.168.0.20` (Desktop), `192.168.0.110` (Sensor), `192.168.0.120` (Servidor), `192.168.0.130`, `192.168.0.140`, `127.0.0.1`
