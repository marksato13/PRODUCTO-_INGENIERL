#!/usr/bin/env bash
# enforce.sh — Control inline PPI
# Aplica accion de bloqueo/limite sobre una IP en el servidor
# Uso: enforce.sh <ip> <accion> [timeout_seg]
#   accion: BLOCK | LIMIT | UNBLOCK

set -euo pipefail

IP="$1"
ACCION="${2:-BLOCK}"
TIMEOUT="${3:-300}"

SET_BLOCK="ppi_blocked"
SET_LIMIT="ppi_limited"

case "$ACCION" in
  BLOCK)
    sudo ipset add "$SET_BLOCK" "$IP" timeout "$TIMEOUT" -exist
    echo "$(date '+%Y-%m-%d %H:%M:%S') | BLOCK | $IP | timeout=${TIMEOUT}s"
    ;;
  LIMIT)
    sudo ipset add "$SET_LIMIT" "$IP" timeout "$TIMEOUT" -exist
    echo "$(date '+%Y-%m-%d %H:%M:%S') | LIMIT | $IP | 100pkt/s | timeout=${TIMEOUT}s"
    ;;
  UNBLOCK)
    sudo ipset del "$SET_BLOCK" "$IP" 2>/dev/null || true
    sudo ipset del "$SET_LIMIT" "$IP" 2>/dev/null || true
    echo "$(date '+%Y-%m-%d %H:%M:%S') | UNBLOCK | $IP"
    ;;
  *)
    echo "Uso: $0 <ip> <BLOCK|LIMIT|UNBLOCK> [timeout_seg]"
    exit 1
    ;;
esac
