#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
BITACORA="${PROJECT_ROOT}/docs/bitacora/bitacora_escenarios.txt"

if [ "$#" -ne 8 ]; then
  echo "Uso: $0 <grupo> <escenario> <origen> <destino> <hora_inicio> <hora_fin> <herramienta> <archivo_salida>"
  exit 1
fi

GRUPO="$1"
ESCENARIO="$2"
ORIGEN="$3"
DESTINO="$4"
HORA_INICIO="$5"
HORA_FIN="$6"
HERRAMIENTA="$7"
ARCHIVO_SALIDA="$8"
FECHA="$(date +%F)"

mkdir -p "$(dirname "$BITACORA")"

echo "${FECHA} | ${GRUPO} | ${ESCENARIO} | ${ORIGEN} -> ${DESTINO} | ${HORA_INICIO} - ${HORA_FIN} | ${HERRAMIENTA} | ${ARCHIVO_SALIDA}" >> "$BITACORA"

echo "Registro agregado a: $BITACORA"
