#!/usr/bin/env bash
# F1 — Valida que Suricata está capturando y eve.json crece
EVE="/var/log/suricata/eve.json"
echo "=== F1: CAPTURA DE DATOS (Suricata) ==="
echo ""

# Suricata activo
if systemctl is-active suricata &>/dev/null; then
    echo "  ✅ PASS  Suricata service: activo"
else
    echo "  ❌ FAIL  Suricata service: inactivo — sudo systemctl start suricata"
fi

# eve.json existe
if [ -f "$EVE" ]; then
    size=$(du -sh "$EVE" | cut -f1)
    lines=$(wc -l < "$EVE")
    echo "  ✅ PASS  eve.json existe: $size ($lines líneas)"
else
    echo "  ❌ FAIL  eve.json no encontrado en $EVE"
    exit 1
fi

# eve.json se está escribiendo (modificado en los últimos 5 min)
mod=$(find "$EVE" -mmin -5 2>/dev/null)
if [ -n "$mod" ]; then
    echo "  ✅ PASS  eve.json actualizado en los últimos 5 minutos"
else
    echo "  ⚠️   eve.json sin cambios recientes (¿hay tráfico de red?)"
fi

# Interfaz ens35 en modo promiscuo
if ip link show ens35 2>/dev/null | grep -q PROMISC; then
    echo "  ✅ PASS  ens35 en modo promiscuo"
else
    echo "  ⚠️   ens35 sin modo promiscuo — Suricata puede no capturar todo"
fi

# Último evento en eve.json
echo ""
echo "  Último evento capturado:"
tail -1 "$EVE" | python3 -c "import sys,json; e=json.loads(sys.stdin.read()); print(f'    {e.get(\"timestamp\",\"?\")}  tipo={e.get(\"event_type\",\"?\")}  src={e.get(\"src_ip\",\"?\")}→{e.get(\"dest_ip\",\"?\")}:{e.get(\"dest_port\",\"?\")}' )" 2>/dev/null || echo "    (no se pudo parsear)"
