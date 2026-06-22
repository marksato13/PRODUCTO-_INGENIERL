#!/usr/bin/env bash
METRICS="/home/m4rk/ppi-surikata-producto/results/metricas_predictor_v2.txt"
echo "=== V4: PREDICTOR XGBoost v2 ==="
[ ! -f "$METRICS" ] && echo "  ERROR: No existe $METRICS" && exit 1
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 /home/m4rk/ppi-surikata-producto/scripts/validacion/_v4_check.py "$METRICS"
