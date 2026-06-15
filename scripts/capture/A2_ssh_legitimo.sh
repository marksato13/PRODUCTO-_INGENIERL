#!/usr/bin/env bash

set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="normal"
ESCENARIO="ssh"
CORRIDA="10"
ORIGEN="192.168.0.20"
DESTINO="192.168.0.120"
HERRAMIENTA="ssh"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

HORA_INICIO="$(date +%T)"

END_TIME=$((SECONDS + 480))

while [ $SECONDS -lt $END_TIME ]; do
  ssh $SSH_OPTS m4rk@"${DESTINO}" "uptime" > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "df -h /" > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "ls /var/www/html/" > /dev/null 2>&1 || true
  sleep 8
  ssh $SSH_OPTS m4rk@"${DESTINO}" "cat /proc/loadavg" > /dev/null 2>&1 || true
  sleep 8
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "Escenario A2 completado"
echo "Inicio: $HORA_INICIO"
echo "Fin:    $HORA_FIN"
echo "Archivo: $ARCHIVO_SALIDA"
