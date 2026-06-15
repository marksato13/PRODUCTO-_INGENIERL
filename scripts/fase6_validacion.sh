#!/usr/bin/env bash
# Fase 6 — Validación del sistema PPI
# Ejecuta ataques desde Kali, mide detección y bloqueo, prueba falsos positivos.
set -euo pipefail

KALI="192.168.0.100"
SENSOR="192.168.0.110"
SERVIDOR="192.168.0.120"
DESKTOP="192.168.0.20"
CAPTURE_DIR="/home/m4rk/ppi-surikata-producto/scripts/capture"
MOTOR_LOG="/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
REPORT="/home/m4rk/Descargas/validacion_fase6.txt"
SET_NAME="ppi_blocked"
PASS_KALI="Cisco123"

# ──────────────────────────────────────────────────────────────
log() { echo "[$(date '+%H:%M:%S')] $*"; }

reset_bloqueos() {
  ssh -o StrictHostKeyChecking=no m4rk@"$SERVIDOR" \
    "sudo ipset flush ${SET_NAME} 2>/dev/null || true" 2>/dev/null
}

contar_lineas_log() {
  ssh m4rk@"$SENSOR" "wc -l < ${MOTOR_LOG}" 2>/dev/null || echo 0
}

esperar_deteccion() {
  # Espera hasta que aparezca una línea NUEVA con ANOMALÍA para la IP (desde línea DESDE_LINEA)
  local IP="$1"; local TIMEOUT="$2"; local DESDE_LINEA="$3"
  local t=0
  while [ $t -lt "$TIMEOUT" ]; do
    if ssh m4rk@"$SENSOR" \
        "tail -n +${DESDE_LINEA} ${MOTOR_LOG} 2>/dev/null | grep 'ANOMALÍA.*src=${IP}'" 2>/dev/null | grep -q 'ANOMALÍA'; then
      return 0
    fi
    sleep 2; t=$((t+2))
  done
  return 1
}

esperar_bloqueo() {
  local IP="$1"; local TIMEOUT="$2"
  local t=0
  while [ $t -lt "$TIMEOUT" ]; do
    if ssh m4rk@"$SERVIDOR" \
        "sudo ipset test ${SET_NAME} ${IP} 2>/dev/null" 2>/dev/null; then
      return 0
    fi
    sleep 2; t=$((t+2))
  done
  return 1
}

registrar() {
  echo "$*" | tee -a "$REPORT"
}

# ──────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$REPORT")"
cat > "$REPORT" << HEADER
================================================================
INFORME DE VALIDACIÓN — FASE 6
PPI: Detección temprana de comportamientos anómalos en redes
Universidad Peruana Unión — Rubén Mark Salazar Tocas
Fecha: $(date '+%Y-%m-%d %H:%M UTC')
================================================================

Sistema bajo prueba:
  Sensor IDS : ${SENSOR} (Suricata 7.0.3 + Isolation Forest)
  Servidor   : ${SERVIDOR} (nginx, ssh, ipset/iptables)
  Atacante   : ${KALI} (Kali Linux)
  Monitor    : ${DESKTOP} (tráfico normal)

Umbral del modelo: -0.5887 (contamination=0.05)
Timeout bloqueo : 300 s (auto-expiry ipset)

================================================================
PRUEBAS DE DETECCIÓN (GRUPO B — TRÁFICO ANÓMALO)
================================================================
ESCENARIO          | DETECTADO | BLOQUEADO | LATENCIA  | SCORE
HEADER

log "Iniciando Fase 6 — Validación"

# ──────────────────────────────────────────────────────────────
# Definición de escenarios de ataque
declare -A DESCRIPCIONES=(
  [B1]="SYN flood hping3 -S -p 80 -i u5000"
  [B2]="Port scan nmap -sS p1-1024"
  [B3]="UDP flood hping3 --udp -p 53 -i u5000"
  [B4]="ICMP flood hping3 -1 -i u5000"
  [B5]="HTTP abusivo curl sin pausa"
  [B6]="SSH brute force hydra"
)
declare -A DURACIONES=(
  [B1]=90  [B2]=30  [B3]=90  [B4]=90  [B5]=120  [B6]=60
)
declare -A COMANDOS_KALI=(
  [B1]="echo ${PASS_KALI} | sudo -S timeout 90 hping3 -S -p 80 -i u5000 ${SERVIDOR}"
  [B2]="echo ${PASS_KALI} | sudo -S nmap -sS -p 1-1024 --open -T4 ${SERVIDOR} -oN /tmp/nmap_val.txt"
  [B3]="echo ${PASS_KALI} | sudo -S timeout 90 hping3 --udp -p 53 -i u5000 ${SERVIDOR}"
  [B4]="echo ${PASS_KALI} | sudo -S timeout 90 hping3 -1 -i u5000 ${SERVIDOR}"
  [B5]="END=\$((SECONDS+120)); while [ \$SECONDS -lt \$END ]; do curl -s http://${SERVIDOR}/ > /dev/null; done"
  [B6]="printf 'password\n123456\nadmin\nletmein\nqwerty\ntest\nguest\nmaster\nmonkey' > /tmp/pl.txt && timeout 60 hydra -l m4rk -P /tmp/pl.txt -t 4 -f ${SERVIDOR} ssh 2>/dev/null; true"
)

TOTAL=0; DETECTADOS=0; BLOQUEADOS=0

for ESCENARIO in B1 B2 B3 B4 B5 B6; do
  log "=== $ESCENARIO: ${DESCRIPCIONES[$ESCENARIO]} ==="
  reset_bloqueos

  # Reiniciar motor para limpiar set en memoria
  log "  Reiniciando motor..."
  ssh -T m4rk@"$SENSOR" << 'SSHEOF' 2>/dev/null
pkill -f motor_decision.py 2>/dev/null || true
sleep 2
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate
nohup python3 scripts/motor_decision.py >> /tmp/motor_stdout.log 2>&1 &
disown
SSHEOF
  sleep 6  # esperar que el motor arranque y cargue el modelo

  LINEAS_ANTES=$(contar_lineas_log)
  T_INICIO=$(date +%s)

  # Lanzar ataque desde Kali (en background)
  sshpass -p "$PASS_KALI" ssh -o StrictHostKeyChecking=no \
    m4rk@"$KALI" "${COMANDOS_KALI[$ESCENARIO]}" > /dev/null 2>&1 &
  KALI_PID=$!

  # Esperar detección (máx 120s) — solo líneas nuevas
  DETECTADO="NO"
  BLOQUEADO="NO"
  LATENCIA="--"
  SCORE="--"

  if esperar_deteccion "$KALI" 120 "$LINEAS_ANTES"; then
    T_DETECCION=$(date +%s)
    LATENCIA="$((T_DETECCION - T_INICIO))s"
    DETECTADO="SI"
    DETECTADOS=$((DETECTADOS+1))

    # Obtener score del log (solo líneas nuevas)
    SCORE=$(ssh m4rk@"$SENSOR" \
      "tail -n +${LINEAS_ANTES} ${MOTOR_LOG} 2>/dev/null | grep 'ANOMALÍA.*src=${KALI}' | tail -1 | grep -oP 'score=\K[-0-9.]+'" 2>/dev/null || echo "--")

    # Verificar bloqueo (máx 30s adicionales)
    if esperar_bloqueo "$KALI" 30; then
      BLOQUEADO="SI"
      BLOQUEADOS=$((BLOQUEADOS+1))
    fi
  fi

  TOTAL=$((TOTAL+1))
  LINE=$(printf "%-18s | %-9s | %-9s | %-9s | %s" \
    "$ESCENARIO" "$DETECTADO" "$BLOQUEADO" "$LATENCIA" "$SCORE")
  registrar "$LINE"
  log "  → Detectado: $DETECTADO | Bloqueado: $BLOQUEADO | Latencia: $LATENCIA | Score: $SCORE"

  kill "$KALI_PID" 2>/dev/null || true
  wait "$KALI_PID" 2>/dev/null || true
  reset_bloqueos
  log "  Pausa 30s antes del siguiente escenario..."
  sleep 30
done

# ──────────────────────────────────────────────────────────────
# Prueba de falsos positivos (tráfico normal A1)
log "=== FP: Tráfico normal (curl/wget → servidor, 3 min) ==="
registrar ""
registrar "================================================================"
registrar "PRUEBA DE FALSOS POSITIVOS (GRUPO A — TRÁFICO NORMAL)"
registrar "================================================================"

reset_bloqueos
FP_INICIO=$(date +%s)

# Generar tráfico normal desde Desktop
END=$((SECONDS+180))
while [ $SECONDS -lt $END ]; do
  curl -s "http://${SERVIDOR}/" > /dev/null 2>&1 || true
  curl -s "http://${SERVIDOR}/info.html" > /dev/null 2>&1 || true
  wget -q -O /tmp/fp_test.html "http://${SERVIDOR}/" 2>/dev/null || true
  sleep 8
done

# Verificar si Desktop fue bloqueado
FP_BLOQUEADO="NO"
if ssh m4rk@"$SERVIDOR" \
    "sudo ipset test ${SET_NAME} ${DESKTOP} 2>/dev/null" 2>/dev/null; then
  FP_BLOQUEADO="SI"
fi

FP_DURATION=$(($(date +%s) - FP_INICIO))
FALSOS_EN_LOG=$(ssh m4rk@"$SENSOR" \
  "grep 'ANOMALÍA.*src=${DESKTOP}' ${MOTOR_LOG} 2>/dev/null | wc -l" 2>/dev/null || echo 0)

registrar "Duración tráfico normal  : ${FP_DURATION}s"
registrar "Desktop (${DESKTOP}) bloqueado: ${FP_BLOQUEADO}"
registrar "Entradas ANOMALÍA (Desktop en log): ${FALSOS_EN_LOG}"
if [ "$FP_BLOQUEADO" = "NO" ] && [ "$FALSOS_EN_LOG" -eq 0 ]; then
  registrar "Resultado: SIN FALSOS POSITIVOS ✓"
else
  registrar "Resultado: FALSOS POSITIVOS DETECTADOS ✗ (revisar modelo)"
fi

# ──────────────────────────────────────────────────────────────
# Resumen final
DR=$(echo "scale=4; $DETECTADOS / $TOTAL" | bc)
BR=$(echo "scale=4; $BLOQUEADOS / $TOTAL" | bc)

registrar ""
registrar "================================================================"
registrar "RESUMEN FINAL"
registrar "================================================================"
registrar "Escenarios probados     : $TOTAL"
registrar "Detectados              : $DETECTADOS / $TOTAL  ($(echo "scale=1; $DETECTADOS*100/$TOTAL" | bc)%)"
registrar "Bloqueados              : $BLOQUEADOS / $TOTAL  ($(echo "scale=1; $BLOQUEADOS*100/$TOTAL" | bc)%)"
registrar "Falsos positivos        : ${FP_BLOQUEADO}"
registrar "Modelo Isolation Forest : n_estimators=300, contamination=0.05"
registrar "Umbral decisión         : -0.5887"
registrar "Timeout bloqueo ipset   : 300s"
registrar ""
registrar "Generado: $(date '+%Y-%m-%d %H:%M:%S UTC')"
registrar "================================================================"

log "=== Validación completada. Informe en: $REPORT ==="
cat "$REPORT"
