#!/usr/bin/env bash
# F3 — Valida motor de decisión: latencia, ITL, umbrales
LAT="/home/m4rk/ppi-surikata-producto/results/latencia_pipeline.txt"
LOG="/home/m4rk/ppi-surikata-producto/results/motor_decision.log"

echo "=== F3: MOTOR DE DECISIÓN ==="
echo ""

# CA-5: Latencia P95
if [ -f "$LAT" ]; then
    p95=$(grep 'P95' "$LAT" | awk '{print $(NF-1)}')
    python3 -c "
p95 = float('$p95')
ok = p95 < 500
print(f'  {\"✅ PASS\" if ok else \"❌ FAIL\"}  CA-5 Latencia P95: {p95}ms  (criterio: < 500ms)')
"
else
    echo "  ⚠️  No existe latencia_pipeline.txt"
fi

# CA-6: Motor activo + entradas en log
if systemctl is-active ppi-motor.service &>/dev/null; then
    echo "  ✅ PASS  CA-6 Motor service: activo"
else
    echo "  ❌ FAIL  CA-6 Motor service: inactivo"
fi

if [ -f "$LOG" ]; then
    total=$(wc -l < "$LOG")
    ultimo=$(tail -1 "$LOG" | grep -oP '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    echo "  ✅ PASS  CA-6 ITL: log con $total entradas — último evento: $ultimo"
else
    echo "  ❌ FAIL  CA-6 motor_decision.log no encontrado"
fi

# CA-7: Umbrales
echo ""
echo "  CA-7 Última estadística del motor:"
grep 'Estadísticas' "$LOG" 2>/dev/null | tail -1 | sed 's/^/    /'
echo ""
echo "  Umbrales cargados (metricas_offline.txt):"
grep -E 'tau[12]\s*:' /home/m4rk/ppi-surikata-producto/results/metricas_offline.txt 2>/dev/null | head -2 | sed 's/^/    /'
