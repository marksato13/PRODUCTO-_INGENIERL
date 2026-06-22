#!/usr/bin/env bash
# V1 — Valida métricas offline del Isolation Forest
METRICS="/home/m4rk/ppi-surikata-producto/results/metricas_offline.txt"
echo "=== F2: MODELO ISOLATION FOREST ==="
[ ! -f "$METRICS" ] && echo "  ERROR: No existe $METRICS" && exit 1
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 /home/m4rk/ppi-surikata-producto/scripts/validacion/_f2_if_check.py "$METRICS"
