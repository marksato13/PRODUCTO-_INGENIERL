#!/usr/bin/env bash
# Ejecutar en el SERVIDOR (192.168.0.120) con sudo.
# Uso: bloqueo_servidor.sh <init|block|unblock|status> [IP]
set -euo pipefail

SET_NAME="ppi_blocked"
TIMEOUT=300          # segundos antes de desbloqueo automático
LOG="/var/log/ppi_bloqueos.log"
WHITELIST=("192.168.0.1" "192.168.0.20" "192.168.0.110" "127.0.0.1")

is_whitelisted() {
  local ip="$1"
  for w in "${WHITELIST[@]}"; do
    [ "$ip" = "$w" ] && return 0
  done
  return 1
}

case "${1:-}" in

  init)
    # Crear ipset y regla iptables (idempotente)
    ipset list "$SET_NAME" &>/dev/null || \
      ipset create "$SET_NAME" hash:ip timeout "$TIMEOUT"
    iptables -C INPUT -m set --match-set "$SET_NAME" src -j DROP 2>/dev/null || \
      iptables -I INPUT -m set --match-set "$SET_NAME" src -j DROP
    iptables -C FORWARD -m set --match-set "$SET_NAME" src -j DROP 2>/dev/null || \
      iptables -I FORWARD -m set --match-set "$SET_NAME" src -j DROP
    echo "$(date '+%F %T') | INIT | ipset=$SET_NAME timeout=${TIMEOUT}s" >> "$LOG"
    echo "OK init"
    ;;

  block)
    IP="${2:-}"
    [ -z "$IP" ] && { echo "Uso: $0 block <IP>"; exit 1; }
    if is_whitelisted "$IP"; then
      echo "WHITELIST $IP — no bloqueado"
      exit 0
    fi
    ipset add "$SET_NAME" "$IP" timeout "$TIMEOUT" 2>/dev/null || \
      ipset add "$SET_NAME" "$IP" timeout "$TIMEOUT" -exist
    echo "$(date '+%F %T') | BLOCK | $IP | timeout=${TIMEOUT}s" >> "$LOG"
    echo "BLOCKED $IP"
    ;;

  unblock)
    IP="${2:-}"
    [ -z "$IP" ] && { echo "Uso: $0 unblock <IP>"; exit 1; }
    ipset del "$SET_NAME" "$IP" 2>/dev/null || true
    echo "$(date '+%F %T') | UNBLOCK | $IP" >> "$LOG"
    echo "UNBLOCKED $IP"
    ;;

  status)
    echo "=== ipset $SET_NAME ==="
    ipset list "$SET_NAME" 2>/dev/null || echo "(vacío o no inicializado)"
    echo ""
    echo "=== Últimas 10 acciones ==="
    tail -10 "$LOG" 2>/dev/null || echo "(sin log)"
    ;;

  *)
    echo "Uso: $0 <init|block|unblock|status> [IP]"
    exit 1
    ;;
esac
