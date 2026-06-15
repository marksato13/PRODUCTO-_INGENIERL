#!/usr/bin/env bash

set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="normal"
ESCENARIO="transferencia"
CORRIDA="10"
ORIGEN="192.168.0.20"
DESTINO="192.168.0.120"
HERRAMIENTA="scp_wget"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

SSH_OPTS="-o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no"

HORA_INICIO="$(date +%T)"

END_TIME=$((SECONDS + 600))

while [ $SECONDS -lt $END_TIME ]; do
  scp $SSH_OPTS m4rk@"${DESTINO}":/var/www/html/index.html /tmp/a3_index.html > /dev/null 2>&1 || true
  sleep 10
  wget -q -O /tmp/a3_manual.txt "http://${DESTINO}/files/manual.txt" 2>/dev/null || true
  sleep 10
  scp $SSH_OPTS m4rk@"${DESTINO}":/var/www/html/info.html /tmp/a3_info.html > /dev/null 2>&1 || true
  sleep 10
  wget -q -O /tmp/a3_sample.csv "http://${DESTINO}/files/sample.csv" 2>/dev/null || true
  sleep 10
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "Escenario A3 completado"
echo "Inicio: $HORA_INICIO"
echo "Fin:    $HORA_FIN"
echo "Archivo: $ARCHIVO_SALIDA"
