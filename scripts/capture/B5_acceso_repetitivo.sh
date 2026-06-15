#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="anom"
ESCENARIO="httpabuse"
CORRIDA="01"
ORIGEN="192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="curl"
DURACION_SEGUNDOS=300
SENSOR="192.168.0.110"
PROJECT_ROOT_SENSOR="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando B5 HTTP abusivo → ${DESTINO}:80 por ${DURACION_SEGUNDOS}s (sin pausa)"

END_TIME=$((SECONDS + DURACION_SEGUNDOS))
while [ $SECONDS -lt $END_TIME ]; do
  curl -s "http://${DESTINO}/" > /dev/null || true
  curl -s "http://${DESTINO}/info.html" > /dev/null || true
  curl -s "http://${DESTINO}/health.html" > /dev/null || true
  curl -s "http://${DESTINO}/files/manual.txt" > /dev/null || true
  curl -s "http://${DESTINO}/files/sample.csv" > /dev/null || true
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "B5 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
