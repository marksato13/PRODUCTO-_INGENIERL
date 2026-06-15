#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="mixto"
ESCENARIO="descarga_udp"
CORRIDA="01"
ORIGEN="192.168.0.20+192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="wget+hping3"
DURACION_SEGUNDOS=600
KALI="192.168.0.100"
SENSOR="192.168.0.110"
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando C3: descarga HTTP (Desktop) + UDP flood (Kali) — ${DURACION_SEGUNDOS}s"

# Descarga legítima desde Desktop en background
(
  END_T=$((SECONDS + DURACION_SEGUNDOS))
  while [ $SECONDS -lt $END_T ]; do
    wget -q -O /tmp/c3_index.html "http://${DESTINO}/" 2>/dev/null || true
    sleep 10
    wget -q -O /tmp/c3_manual.txt "http://${DESTINO}/files/manual.txt" 2>/dev/null || true
    sleep 10
    wget -q -O /tmp/c3_sample.csv "http://${DESTINO}/files/sample.csv" 2>/dev/null || true
    sleep 10
    wget -q -O /tmp/c3_grande.bin "http://${DESTINO}/files/archivo_grande.bin" 2>/dev/null || true
    sleep 20
  done
) &
NORMAL_PID=$!

# UDP flood desde Kali en background
sshpass -p 'Cisco123' ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
  "sudo timeout ${DURACION_SEGUNDOS} hping3 --udp -p 53 -i u5000 --rand-source ${DESTINO} 2>/dev/null || true" &
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

echo "C3 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
