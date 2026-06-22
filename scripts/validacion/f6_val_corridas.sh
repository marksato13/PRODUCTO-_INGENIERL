#!/usr/bin/env bash
# F6 — Valida resultados de las 40 corridas de validación
PROJECT="/home/m4rk/ppi-surikata-producto"
CSV="$PROJECT/results/resultados_f6_completo.csv"
BITACORA="$PROJECT/docs/bitacora/bitacora_escenarios.txt"

echo "=== F6: VALIDACIÓN — 40 CORRIDAS ==="
echo ""

# CSV existe
[ ! -f "$CSV" ] && echo "  ❌ FAIL  resultados_f6_completo.csv no encontrado" && exit 1

source /home/m4rk/ppi-sensor/venv/bin/activate
python3 - << PYEOF
import csv, sys

csv_path = "$CSV"
rows = []
with open(csv_path) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total = len(rows)
ca15_ok = total >= 40

# Disponibilidad: buscar columna de disponibilidad o contar errores
fallos = [r for r in rows if r.get('disponibilidad','1') == '0' or r.get('error','') != '']
disponibilidad = (total - len(fallos)) / total * 100 if total > 0 else 0

print(f"  {'✅ PASS' if ca15_ok else '❌ FAIL'}  CA-15 Corridas completadas: {total}/40")
print(f"  {'✅ PASS' if disponibilidad == 100 else '❌ FAIL'}  CA-15 Disponibilidad: {disponibilidad:.1f}%")

if total > 0:
    grupos = {}
    for r in rows:
        g = r.get('grupo', r.get('escenario','?')[:2])
        grupos[g] = grupos.get(g,0) + 1
    print(f"\n  Distribución por grupo:")
    for g,n in sorted(grupos.items()):
        print(f"    {g}: {n} corridas")
PYEOF

echo ""

# Gráficas F6
graficas=$(ls "$PROJECT/results/graficas_f6/"*.png 2>/dev/null | wc -l)
if [ "$graficas" -ge 7 ]; then
    echo "  ✅ PASS  Gráficas F6: $graficas PNG generados"
else
    echo "  ⚠️   Gráficas F6: solo $graficas PNG (esperados 7)"
fi

# Bitácora
if [ -f "$BITACORA" ]; then
    lineas=$(wc -l < "$BITACORA")
    echo "  ✅ PASS  Bitácora: $lineas entradas registradas"
fi
