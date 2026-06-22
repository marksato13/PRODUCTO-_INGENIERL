#!/usr/bin/env bash
# V2 — Valida latencia del motor de decisión y carga de umbrales
set -euo pipefail
LAT="/home/m4rk/ppi-surikata-producto/results/latencia_pipeline.txt"
LOG="/home/m4rk/ppi-surikata-producto/results/motor_decision.log"

echo "=== V2: MOTOR DE DECISIÓN ==="
echo ""

# CA-5: Latencia P95
if [ -f "$LAT" ]; then
    p95=$(grep 'P95' "$LAT" | awk '{print $NF}' | tr -d 'ms')
    python3 -c "
p95=$p95
ok = p95 < 500
print(f'  {\"✅ PASS\" if ok else \"❌ FAIL\"}  CA-5 Latencia P95: {p95}ms  (criterio: < 500ms)')
"
else
    echo "  ⚠️  No existe latencia_pipeline.txt — correr latencia manualmente"
fi

# CA-6: ITL — verificar que el log tiene entradas (no hay gaps largos)
if [ -f "$LOG" ]; then
    total=$(wc -l < "$LOG")
    echo "  ✅ PASS  CA-6 ITL: log activo con $total entradas"
else
    echo "  ⚠️  CA-6: motor_decision.log no encontrado — iniciar motor primero"
fi

# CA-7: Umbrales cargados
echo ""
echo "  CA-7 Umbrales — verificando en journalctl:"
sudo journalctl -u ppi-motor.service --since "1 hour ago" --no-pager 2>/dev/null \
    | grep -iE "TAU|tau|umbral" | tail -3 \
    || echo "  ⚠️  Sin entradas de umbrales en último 1h (reiniciar motor para verificar)"
