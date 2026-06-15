#!/usr/bin/env bash
set -euo pipefail

FECHA="$(date +%Y%m%d)"
GRUPO="anom"
ESCENARIO="portscan"
CORRIDA="01"
ORIGEN="192.168.0.100"
DESTINO="192.168.0.120"
HERRAMIENTA="nmap"
SENSOR="192.168.0.110"
PROJECT_ROOT_SENSOR="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT_SENSOR}/scripts/evaluation/registrar_bitacora.sh"
ARCHIVO_SALIDA="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json"

HORA_INICIO="$(date +%T)"
echo "Iniciando B2 port scan (nmap -sS) → ${DESTINO} | 3 pasadas"

# nmap -sS (SYN stealth scan) — T1046 Active Scanning
for i in 1 2 3; do
  echo "Pasada nmap $i/3"
  echo cisco123 | sudo -S nmap -sS -p 1-1024 --open -T4 \
    -oN "/tmp/nmap_b2_scan_${i}.txt" "$DESTINO" 2>/dev/null || true
  [ "$i" -lt 3 ] && sleep 60
done

HORA_FIN="$(date +%T)"

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${ARCHIVO_SALIDA}"

echo "B2 completado | Inicio: $HORA_INICIO | Fin: $HORA_FIN | Archivo: $ARCHIVO_SALIDA"
