#!/usr/bin/env bash
set -euo pipefail
CAPTURE_DIR="/home/m4rk/ppi-surikata-producto/scripts/capture"
LOG="/tmp/run_A1_A4.log"

echo "=== RUN A1-A4 INICIO: $(date) ===" | tee "$LOG"

echo "--- A1 http_normal (10 min) ---" | tee -a "$LOG"
bash "${CAPTURE_DIR}/A1_http_normal.sh" 2>&1 | tee -a "$LOG"

echo "Pausa 2 min..." | tee -a "$LOG"
sleep 120

echo "--- A2 ssh_legitimo (8 min) ---" | tee -a "$LOG"
bash "${CAPTURE_DIR}/A2_ssh_legitimo.sh" 2>&1 | tee -a "$LOG"

echo "Pausa 2 min..." | tee -a "$LOG"
sleep 120

echo "--- A3 transferencia_legitima (10 min) ---" | tee -a "$LOG"
bash "${CAPTURE_DIR}/A3_transferencia_legitima.sh" 2>&1 | tee -a "$LOG"

echo "Pausa 2 min..." | tee -a "$LOG"
sleep 120

echo "--- A4 trafico_sostenido (15 min) ---" | tee -a "$LOG"
bash "${CAPTURE_DIR}/A4_trafico_sostenido.sh" 2>&1 | tee -a "$LOG"

echo "=== RUN A1-A4 FIN: $(date) ===" | tee -a "$LOG"
echo "COMPLETADO"
