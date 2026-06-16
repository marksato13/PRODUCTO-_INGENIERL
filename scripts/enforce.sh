#!/usr/bin/env bash
# enforce.sh — Control inline PPI
# Aplica accion de bloqueo/limite sobre una IP en el SERVIDOR (192.168.0.120)
# Uso: enforce.sh <ip> <accion> [timeout_seg]
#   accion: BLOCK | LIMIT | UNBLOCK

set -euo pipefail

IP="$1"
ACCION="${2:-BLOCK}"
TIMEOUT="${3:-300}"

SET_BLOCK="ppi_blocked"
SET_LIMIT="ppi_limited"
SERVIDOR="192.168.0.120"
SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

_srv() { ssh $SSH_OPTS m4rk@$SERVIDOR "$1"; }

case "$ACCION" in
  BLOCK)
    _srv "sudo ipset add $SET_BLOCK $IP timeout $TIMEOUT -exist"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | BLOCK | $IP | timeout=${TIMEOUT}s"
    ;;
  LIMIT)
    _srv "sudo ipset add $SET_LIMIT $IP timeout $TIMEOUT -exist"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | LIMIT | $IP | 100pkt/s | timeout=${TIMEOUT}s"
    ;;
  UNBLOCK)
    _srv "sudo ipset del $SET_BLOCK $IP 2>/dev/null || true"
    _srv "sudo ipset del $SET_LIMIT $IP 2>/dev/null || true"
    echo "$(date '+%Y-%m-%d %H:%M:%S') | UNBLOCK | $IP"
    ;;
  *)
    echo "Uso: $0 <ip> <BLOCK|LIMIT|UNBLOCK> [timeout_seg]"
    exit 1
    ;;
esac
