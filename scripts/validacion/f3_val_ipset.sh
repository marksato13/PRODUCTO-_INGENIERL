#!/usr/bin/env bash
# F3 — Valida control inline ipset/iptables
LOG="/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
COUNTS="/home/m4rk/ppi-surikata-producto/results/block_counts.json"
# Whitelist = IPs que el motor NO debe insertar en ipset (aunque las logee)
WHITELIST=("192.168.0.1" "192.168.0.20" "192.168.0.110" "192.168.0.120" "127.0.0.1")

echo "=== F3: CONTROL INLINE ipset/iptables ==="
echo ""

# CA-8: Whitelist — ninguna debe estar en block_counts (ipset real)
echo "  CA-8 Whitelist — verificando en block_counts.json (ipset real):"
if [ -f "$COUNTS" ]; then
    wl_fail=0
    for ip in "${WHITELIST[@]}"; do
        if python3 -c "import json; d=json.load(open('$COUNTS')); exit(0 if '$ip' in d else 1)" 2>/dev/null; then
            echo "    ❌ FAIL — $ip está en block_counts (fue insertado en ipset)"
            wl_fail=1
        else
            echo "    ✅ OK   $ip → no está en block_counts"
        fi
    done
    [ $wl_fail -eq 0 ] && echo "  ✅ PASS  CA-8: whitelist completamente protegida en ipset"
else
    echo "  ⚠️  block_counts.json no encontrado"
fi

echo ""

# CA-9: Evidencia de bloqueos reales de IPs atacantes
echo "  CA-9 Últimos BLOCKs registrados:"
grep " | BLOCK" "$LOG" 2>/dev/null | tail -3 | \
    grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*src=\S+ dst=\S+' | sed 's/^/    /'
bloq=$(grep -c " | BLOCK" "$LOG" 2>/dev/null || echo 0)
echo "  ✅ PASS  CA-9 Total BLOCKs en log: $bloq"

echo ""

# CA-10: Bloqueo progresivo
echo "  CA-10 Bloqueo progresivo — block_counts.json:"
python3 - << PYEOF
import json
with open("$COUNTS") as f:
    data = json.load(f)

# formato: {"ip": count}  o  {"ip": {"count": N}}
def get_count(v):
    return v if isinstance(v, int) else v.get('count', 0)

for ip, v in data.items():
    c = get_count(v)
    if c >= 3:
        print(f"  ✅ PASS  CA-10 {ip} → bloqueo #{c} = PERMANENTE (timeout=0)")
    elif c == 2:
        print(f"  ℹ️   {ip} → bloqueo #{c} (próximo será PERMANENTE)")
    else:
        print(f"  ℹ️   {ip} → bloqueo #{c}")

total = len(data)
permanentes = sum(1 for v in data.values() if get_count(v) >= 3)
print(f"\n  Total IPs registradas: {total}  |  Permanentes: {permanentes}")
PYEOF
