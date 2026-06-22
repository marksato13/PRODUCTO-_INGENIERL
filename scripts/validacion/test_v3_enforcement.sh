#!/usr/bin/env bash
# V3 — Valida whitelist y estado de ipset
set -euo pipefail

WHITELIST=("192.168.0.1" "192.168.0.20" "192.168.0.110" "192.168.0.120" "192.168.0.130" "192.168.0.140" "127.0.0.1")

echo "=== V3: CONTROL INLINE ipset ==="
echo ""

# Verificar que ipset existe
if ! sudo ipset list ppi_blocked &>/dev/null; then
    echo "  ⚠️  ipset ppi_blocked no existe — iniciar motor para crearlo"
    exit 1
fi

# CA-8: Whitelist nunca bloqueada
echo "  CA-8 Whitelist:"
fail=0
for ip in "${WHITELIST[@]}"; do
    if sudo ipset test ppi_blocked "$ip" 2>/dev/null; then
        echo "    ❌ FAIL — $ip está en ppi_blocked!"
        fail=1
    else
        echo "    ✅ OK   $ip no está bloqueada"
    fi
done
[ $fail -eq 0 ] && echo "  ✅ PASS  CA-8: ninguna IP de whitelist bloqueada"

echo ""

# CA-10: Mostrar bloqueos permanentes
echo "  CA-10 Bloqueos permanentes (timeout=0):"
perma=$(sudo ipset list ppi_blocked | grep -v "timeout [1-9]" | grep -E "^[0-9]" || true)
if [ -n "$perma" ]; then
    echo "  ✅ PASS  CA-10: IPs con bloqueo permanente:"
    echo "$perma" | while read -r line; do echo "    → $line"; done
else
    echo "  ℹ️   Sin bloqueos permanentes activos (normal si no hubo ataque #3)"
fi

echo ""
echo "  Estado actual ppi_blocked:"
sudo ipset list ppi_blocked | tail -20
