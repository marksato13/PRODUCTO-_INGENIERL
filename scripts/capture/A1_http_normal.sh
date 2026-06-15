#!/usr/bin/env bash

set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="normal"
ESCENARIO="http"
CORRIDA="02"
ORIGEN="192.168.0.20"
DESTINO="192.168.0.120"
HERRAMIENTA="curl_wget"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"

END_TIME=$((SECONDS + 600))

while [ $SECONDS -lt $END_TIME ]; do
  curl -s "http://${DESTINO}/" > /dev/null || true
  sleep 5
  curl -s "http://${DESTINO}/info.html" > /dev/null || true
  sleep 5
  wget -q -O /tmp/a1_http_test.html "http://${DESTINO}/" || true
  sleep 10
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@192.168.0.110 \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "Escenario A1 completado"
echo "Inicio: $HORA_INICIO"
echo "Fin: $HORA_FIN"
echo "Archivo exportado: $ARCHIVO_SALIDA"
