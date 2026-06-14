#!/usr/bin/env bash
set -euo pipefail

SOURCE_EVE="/var/log/suricata/eve.json"
TARGET_DIR="/home/m4rk/ppi-surikata-producto/data/raw"

if [ "$#" -ne 4 ]; then
  echo "Uso: $0 <fecha> <grupo> <escenario> <corrida>"
  echo "Ejemplo: $0 20260510 normal http 01"
  exit 1
fi

FECHA="$1"
GRUPO="$2"
ESCENARIO="$3"
CORRIDA="$4"

OUTPUT_FILE="${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json.gz"

mkdir -p "$TARGET_DIR"

if [ ! -f "$SOURCE_EVE" ]; then
  echo "No existe el archivo fuente: $SOURCE_EVE"
  exit 1
fi

# Exportar comprimido para ahorrar disco
gzip -c "$SOURCE_EVE" > "$TARGET_DIR/$OUTPUT_FILE" 2>/dev/null || cp "$SOURCE_EVE" "$TARGET_DIR/${OUTPUT_FILE%.gz}"
ls -lh "$TARGET_DIR/$OUTPUT_FILE" 2>/dev/null || ls -lh "$TARGET_DIR/${OUTPUT_FILE%.gz}"
echo "Archivo exportado: $OUTPUT_FILE"

# Vaciar log y rotar en Suricata
sudo truncate -s 0 "$SOURCE_EVE"
sudo suricatasc -c reopen-log-files > /dev/null 2>&1 || true
echo "Log rotado: eve.json limpio para el siguiente escenario"
