#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="mixto"
ESCENARIO="ssh_portscan"
CORRIDA="01"
ORIGEN="192.168.0.20+192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="ssh+nmap"
DURACION_SEGUNDOS=600
KALI="192.168.0.100"
SENSOR="192.168.0.110"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando C2: SSH legítimo (Desktop) + port scan (Kali) — ${DURACION_SEGUNDOS}s"

# SSH legítimo desde Desktop en background
(
  END_T=$((SECONDS + DURACION_SEGUNDOS))
  while [ $SECONDS -lt $END_T ]; do
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
      m4rk@"$DESTINO" "uptime; df -h /" 2>/dev/null || true
    sleep 30
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
      m4rk@"$DESTINO" "ls /var/log/ | head -5" 2>/dev/null || true
    sleep 30
  done
) &
NORMAL_PID=$!

# Port scan repetido desde Kali en background
ssh -o StrictHostKeyChecking=no m4rk@"$KALI" "
  for i in 1 2 3 4; do
    echo cisco123 | sudo -S nmap -sS -p 1-1024 --open -T4 \
      -oN /tmp/nmap_c2_scan_\${i}.txt ${DESTINO} 2>/dev/null || true
    sleep 90
  done
" &
KALI_PID=$!

echo "Tráfico en curso (${DURACION_SEGUNDOS}s)..."
sleep "$DURACION_SEGUNDOS"

kill "$NORMAL_PID" 2>/dev/null || true
kill "$KALI_PID" 2>/dev/null || true
wait 2>/dev/null || true

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "C2 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
