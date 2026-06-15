#!/usr/bin/env bash

set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="normal"
ESCENARIO="sostenido"
CORRIDA="02"
ORIGEN="192.168.0.20"
DESTINO="192.168.0.120"
HERRAMIENTA="curl_ssh_mixto"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

HORA_INICIO="$(date +%T)"

END_TIME=$((SECONDS + 900))

while [ $SECONDS -lt $END_TIME ]; do
  curl -s "http://${DESTINO}/" > /dev/null 2>&1 || true
  sleep 5
  ssh $SSH_OPTS m4rk@"${DESTINO}" "uptime" > /dev/null 2>&1 || true
  sleep 5
  curl -s "http://${DESTINO}/info.html" > /dev/null 2>&1 || true
  sleep 5
  wget -q -O /tmp/a4_wget.html "http://${DESTINO}/" 2>/dev/null || true
  sleep 5
  ssh $SSH_OPTS m4rk@"${DESTINO}" "df -h /" > /dev/null 2>&1 || true
  sleep 5
  curl -s "http://${DESTINO}/health.html" > /dev/null 2>&1 || true
  sleep 5
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "Escenario A4 completado"
echo "Inicio: $HORA_INICIO"
echo "Fin:    $HORA_FIN"
echo "Archivo: $ARCHIVO_SALIDA"
