#!/usr/bin/env bash
# run_all.sh — Suite completa de validación PPI UPeU 2026 (F1–F6)
set -uo pipefail
DIR="$(dirname "$(realpath "$0")")"
LOG="/home/m4rk/ppi-surikata-producto/results/validacion_$(date +%Y%m%d_%H%M%S).log"

echo "========================================================"
echo "  SUITE DE VALIDACIÓN PPI UPeU 2026  —  F1 a F6"
echo "  $(date)"
echo "========================================================"
echo "" | tee "$LOG"

run_test() {
    local nombre="$1"
    local script="$2"
    echo "--- $nombre ---" | tee -a "$LOG"
    bash "$script" 2>&1 | tee -a "$LOG" || echo "  ⚠️  Script salió con error" | tee -a "$LOG"
    echo "" | tee -a "$LOG"
}

run_test "F1 — Captura Suricata"            "$DIR/f1_val_captura.sh"
run_test "F2 — Modelo Isolation Forest"     "$DIR/f2_val_modelo_if.sh"
run_test "F3 — Motor de decisión"           "$DIR/f3_val_motor.sh"
run_test "F3 — Control ipset/iptables"      "$DIR/f3_val_ipset.sh"
run_test "F4 — Predictor XGBoost v2"        "$DIR/f4_val_predictor.sh"
run_test "F5 — Reentrenamiento automático"  "$DIR/f5_val_reentrenamiento.sh"
run_test "F6 — Corridas de validación"      "$DIR/f6_val_corridas.sh"

echo "========================================================"
echo "  Log guardado en: $LOG"
echo "  F2/F6 datos nuevos: ver docs/ppi_documentacion2/validacion/f2_val_datos_nuevos.md"
echo "========================================================"
