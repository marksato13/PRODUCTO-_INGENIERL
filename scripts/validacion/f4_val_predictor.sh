#!/usr/bin/env bash
METRICS="/home/m4rk/ppi-surikata-producto/results/metricas_predictor_v2.txt"
echo "=== F4: PREDICTOR XGBoost v2 ==="
[ ! -f "$METRICS" ] && echo "  ERROR: No existe $METRICS" && exit 1
source /home/m4rk/ppi-sensor/venv/bin/activate
python3 /home/m4rk/ppi-surikata-producto/scripts/validacion/_f4_xgb_check.py "$METRICS"
