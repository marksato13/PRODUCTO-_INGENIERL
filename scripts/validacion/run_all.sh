#!/usr/bin/env bash
# run_all.sh — Suite completa de validación PPI UPeU 2026
set -uo pipefail
DIR="$(dirname "$(realpath "$0")")"
LOG="/home/m4rk/ppi-surikata-producto/results/validacion_$(date +%Y%m%d_%H%M%S).log"

echo "================================================"
echo "  SUITE DE VALIDACIÓN PPI UPeU 2026"
echo "  $(date)"
echo "================================================"
echo "" | tee "$LOG"

run_test() {
    local nombre="$1"
    local script="$2"
    echo "--- $nombre ---" | tee -a "$LOG"
    if bash "$script" 2>&1 | tee -a "$LOG"; then
        echo "" >> "$LOG"
    else
        echo "  ⚠️  Script salió con error" | tee -a "$LOG"
    fi
    echo ""
}

run_test "V1 — Isolation Forest offline"   "$DIR/test_v1_metricas_if.sh"
run_test "V2 — Motor de decisión"          "$DIR/test_v2_latencia_motor.sh"
run_test "V3 — Control ipset/enforcement"  "$DIR/test_v3_enforcement.sh"
run_test "V4 — Predictor XGBoost v2"       "$DIR/test_v4_xgboost.sh"

echo "================================================"
echo "  Log guardado en: $LOG"
echo "  V5 (escenarios) y V6 (data nueva): ejecutar manualmente"
echo "  Ver docs: docs/ppi_documentacion2/validacion/"
echo "================================================"
