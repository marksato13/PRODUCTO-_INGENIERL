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
| 192.168.0.20 | Ubuntu Desktop | Admin / origen tráfico normal |
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
ssh m4rk@192.168.0.110 "cd ppi-surikata-producto && nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/dashboard_web.py &"
# Acceder desde Desktop: http://192.168.0.110:8080
```

## Pipeline real (scripts en `scripts/`)

Isolation Forest es **no supervisado** — solo necesita datos normales para aprender.
Ver: `docs/METODOLOGIA_PIPELINE_COMPARATIVA.md`

```
F2 — Captura (3 grupos separados, motor DETENIDO)
   Grupo A: Desktop → *_normal_*.gz   (Kali apagada)
   Grupo B: Kali   → *_anom_*.gz     (Desktop quieto)
   Grupo C: Ambos  → *_mixto_*.gz    (motor detenido)

F3 — Modelado offline
   fase3_entrenar.py   *_normal_*.gz → IF(n=300) → isolation_forest.pkl + scaler.pkl + normal_holdout.csv (20%)
   fase3_evaluar.py    holdout + *_anom_*.gz → ROC → τ1/τ2 → metricas_offline.txt ← fuente única de verdad
   auc_por_escenario.py  *_anom_*.gz + *_mixto_*.gz → AUC por escenario → auc_por_escenario.txt

F4+F5 — Motor + Control inline
   motor_decision.py   tail eve.json → features → score IF → PERMIT/LIMIT/BLOCK
   enforce.sh          SSH a servidor .120 → ipset add/del (ppi_blocked / ppi_limited)

F6 — Validación (motor ACTIVO, 40 corridas)
   f6_corridas.py      40 corridas (normal + mixto + reeval + final) → resultados_f6_completo.csv
   generar_graficas_f6.py  → 7 PNG 300 DPI para informe

Live monitoring:
   dashboard.py        estadísticas desde motor_decision.log (terminal)
   dashboard_web.py    dashboard web Flask+SSE en :8080
```

## Rutas clave en el sensor (192.168.0.110)

```
/home/m4rk/ppi-surikata-producto/
├── scripts/
│   ├── capture/            ← A1-A4, B1-B6, C1-C3, exportar_eve_por_escenario.sh
│   └── evaluation/registrar_bitacora.sh
├── data/
│   ├── raw/                ← *_normal_*.gz (28), *_anom_*.gz (13), *_mixto_*.gz (6)
│   └── normal_holdout.csv  ← 20% flows normales nunca vistos por el modelo
├── models/
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   └── features.csv        ← 14 features (orden exacto que espera el motor)
├── results/
│   ├── metricas_offline.txt      ← FUENTE ÚNICA: AUC, τ1, τ2, Precision, Recall, F1
│   ├── auc_roc.png
│   ├── latencia_pipeline.txt
│   ├── motor_decision.log
│   ├── resultados_f6_completo.csv ← 40 corridas F6
│   ├── resultados_f6_README.txt
│   ├── graficas_f6/              ← 7 figuras PNG 300 DPI
│   ├── reports/auc_por_escenario.txt
│   ├── informe_final_PPI_UPeU_2026.pdf
│   └── slides_defensa_PPI_UPeU_2026.pptx
└── docs/
    ├── METODOLOGIA_PIPELINE_COMPARATIVA.md
    ├── bitacora/bitacora_escenarios.txt
    └── ppi_documentacion/F1-F6 specs + diagramas
```

## Features del modelo (14)

`pkts_toserver`, `pkts_toclient`, `bytes_toserver`, `bytes_toclient`, `duration`, `pkt_rate`, `byte_rate`, `pkt_ratio`, `byte_ratio`, `avg_pkt_size`, `is_tcp`, `is_udp`, `is_icmp`, `dest_port`

## Umbrales de decisión (modelo final — sklearn 1.9.0)

| Umbral | Valor | Acción | Criterio |
|---|---|---|---|
| τ1 | -0.4459 | score > τ1 → PERMIT | Youden index (TPR=99.40%, FPR=20.47%) |
| τ2 | -0.6027 | τ2 < score ≤ τ1 → LIMIT (hashlimit 100pkt/s) | FPR≤2% (TPR=18.27%) |
| — | — | score ≤ τ2 → BLOCK (DROP) | — |

Motor lee τ1/τ2 de `results/metricas_offline.txt` en cada arranque (sin edición manual).
FPR=20.47% en τ1 es correcto — bajar a 5% haría escapar SYN Flood (score≈−0.49).

Detectores heurísticos adicionales:
- **Brute Force SSH**: 15 intentos/60s → BLOCK (5 → LIMIT)
- **HTTP Abuse**: 100 req/30s → BLOCK (50 → LIMIT)

## Métricas finales validadas (F6 + modelo 2026-06-16)

- AUC-ROC: 0.8998 | Precision: 99.54% | Recall: 99.40% | F1: 0.9947
- Latencia P95: 34.8ms (req. < 500ms: CUMPLE) | ITL: 0% | Disponibilidad: 100%
- Lead Time detección (SYN Flood): ~62s (timeout Suricata TCP half-open, no latencia del motor)
- sklearn: 1.9.0 en venv y modelo — sin mismatch de versiones

## Escenarios de tráfico

### Grupo A — Normal puro (desde Desktop, Kali APAGADA)
A1 http_normal (10 min), A2 ssh_legitimo (8 min), A3 transferencia_legitima (10 min), A4 trafico_sostenido (15 min)

### Grupo B — Anómalo puro (desde Kali, Desktop QUIETO)
B1 syn_flood, B2 port_scan, B3 udp_flood, B4 icmp_flood, B5 acceso_repetitivo, B6 bruteforce

### Grupo C — Mixto (Desktop + Kali, motor DETENIDO)
C1 http_syn, C2 ssh_portscan, C3 descarga_udp

## Nomenclatura de archivos capturados

```
YYYYMMDD_grupo_escenario_NN_eve.json.gz
Globs date-agnostic:  *_normal_*.gz | *_anom_*.gz | *_mixto_*.gz
```

## Whitelist ipset (nunca bloquear)

`192.168.0.1`, `192.168.0.20` (Desktop), `192.168.0.110` (Sensor), `192.168.0.120` (Servidor), `192.168.0.130`, `192.168.0.140`, `127.0.0.1`
