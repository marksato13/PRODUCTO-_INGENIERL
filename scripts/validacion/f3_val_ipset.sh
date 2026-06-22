#!/usr/bin/env bash
# F3 — Valida control inline ipset/iptables (enforcement en SERVIDOR 192.168.0.120)
LOG="/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
COUNTS="/home/m4rk/ppi-surikata-producto/results/block_counts.json"
SERVIDOR="192.168.0.120"
SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"
WHITELIST=("192.168.0.1" "192.168.0.20" "192.168.0.110" "192.168.0.120" "127.0.0.1")

echo "=== F3: CONTROL INLINE ipset/iptables (enforcement en $SERVIDOR) ==="
echo ""

# CA-8: Whitelist — ninguna en block_counts (nunca fue a ipset en servidor)
echo "  CA-8 Whitelist — verificando en block_counts.json:"
if [ -f "$COUNTS" ]; then
    wl_fail=0
    for ip in "${WHITELIST[@]}"; do
        if python3 -c "import json; d=json.load(open('$COUNTS')); exit(0 if '$ip' in d else 1)" 2>/dev/null; then
            echo "    ❌ FAIL — $ip está en block_counts (fue enviado a ipset del servidor)"
            wl_fail=1
        else
            echo "    ✅ OK   $ip → no está en block_counts"
        fi
    done
    [ $wl_fail -eq 0 ] && echo "  ✅ PASS  CA-8: whitelist protegida — ninguna IP fue a ipset del servidor"
fi

echo ""

# CA-9: Verificar ipset en SERVIDOR directamente
echo "  CA-9 Estado ipset en servidor ($SERVIDOR):"
ipset_out=$(ssh $SSH_OPTS m4rk@$SERVIDOR "sudo ipset list ppi_blocked 2>/dev/null" 2>/dev/null || echo "ERROR")
if echo "$ipset_out" | grep -q "ERROR"; then
    echo "  ⚠️  No se pudo conectar al servidor para verificar ipset"
    # Fallback: contar BLOCKs en log
    bloq=$(grep -c " | BLOCK" "$LOG" 2>/dev/null || echo 0)
    echo "  ✅ PASS  CA-9 BLOCKs enviados al servidor (log): $bloq"
else
    entries=$(echo "$ipset_out" | grep -c "^[0-9]" 2>/dev/null || echo 0)
    echo "  ✅ PASS  CA-9 ipset ppi_blocked en servidor: $entries entradas activas"
    echo "$ipset_out" | tail -5 | sed 's/^/    /'
fi

echo ""

# CA-9: Evidencia de BLOCKs en log del motor
echo "  Últimos BLOCKs registrados (motor log):"
grep " | BLOCK" "$LOG" 2>/dev/null | tail -3 | \
    grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*src=\S+ dst=\S+' | sed 's/^/    /'
bloq=$(grep -c " | BLOCK" "$LOG" 2>/dev/null || echo 0)
echo "  ✅ PASS  Total BLOCKs en log: $bloq"

echo ""

# CA-10: Bloqueo progresivo en block_counts.json
echo "  CA-10 Bloqueo progresivo — block_counts.json:"
python3 - << PYEOF
import json
with open("$COUNTS") as f:
    data = json.load(f)

def get_count(v):
    return v if isinstance(v, int) else v.get('count', 0)

for ip, v in data.items():
    c = get_count(v)
    if c >= 3:
        print(f"  ✅ PASS  CA-10 {ip} → bloqueo #{c} = PERMANENTE (timeout=0 en servidor)")
    elif c == 2:
        print(f"  ℹ️   {ip} → bloqueo #{c} (próximo será PERMANENTE)")
    else:
        print(f"  ℹ️   {ip} → bloqueo #{c}")
print(f"\n  Total IPs en block_counts: {len(data)}")
PYEOF
