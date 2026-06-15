#!/usr/bin/env bash
# Ejecutar desde Desktop cuando Kali (192.168.0.100) esté encendida.
# 1) Copia B1-B6 a Kali
# 2) Configura SSH key de Kali → Sensor para que los B scripts exporten sin sshpass
set -euo pipefail

KALI="192.168.0.100"
SENSOR="192.168.0.110"
LOCAL_DIR="/home/m4rk/ppi-surikata-producto/scripts/capture"
REMOTE_DIR="/home/m4rk/ppi-surikata-producto/scripts/capture"
PASS="Cisco123"

echo "=== Verificando Kali (${KALI}) ==="
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
  "mkdir -p ${REMOTE_DIR} && echo 'OK Kali'"

echo ""
echo "=== Copiando scripts B1-B6 a Kali ==="
for script in B1_syn_flood.sh B2_port_scan.sh B3_udp_flood.sh \
              B4_icmp_flood.sh B5_acceso_repetitivo.sh B6_bruteforce.sh; do
  sshpass -p "$PASS" scp -o StrictHostKeyChecking=no \
    "${LOCAL_DIR}/${script}" \
    "m4rk@${KALI}:${REMOTE_DIR}/${script}"
  sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
    "chmod +x ${REMOTE_DIR}/${script}"
  echo "  ok ${script}"
done

echo ""
echo "=== Configurando SSH key Kali → Sensor ==="
# Genera key en Kali si no existe, luego la copia al sensor
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
  "[ -f ~/.ssh/id_rsa.pub ] || ssh-keygen -t rsa -b 2048 -N '' -f ~/.ssh/id_rsa -q"

KALI_PUBKEY=$(sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
  "cat ~/.ssh/id_rsa.pub")

ssh -o StrictHostKeyChecking=no m4rk@"$SENSOR" \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh
   echo '${KALI_PUBKEY}' >> ~/.ssh/authorized_keys
   sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   echo 'Key de Kali registrada en sensor'"

# Verificar que funcione
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" \
  "ssh -o StrictHostKeyChecking=no m4rk@${SENSOR} 'echo OK Kali-a-Sensor'"

echo ""
echo "=== Configurando NOPASSWD sudo en Kali para hping3 y nmap ==="
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no m4rk@"$KALI" "
  echo '${PASS}' | sudo -S bash -c \"
    echo 'm4rk ALL=(ALL) NOPASSWD: /usr/sbin/hping3, /usr/bin/nmap, /usr/bin/timeout' \
      > /etc/sudoers.d/ppi_kali
    chmod 440 /etc/sudoers.d/ppi_kali
    echo 'sudoers actualizado'
  \"
" 2>/dev/null || echo "AVISO: sudo NOPASSWD no se pudo configurar automaticamente — configurar manualmente en Kali"

echo ""
echo "=== Despliegue completo ==="
echo "Kali lista. Scripts disponibles en: ${REMOTE_DIR}/"
echo ""
echo "Orden de ejecucion B (desde Kali, con 2 min de pausa entre cada uno):"
echo "  bash ${REMOTE_DIR}/B1_syn_flood.sh"
echo "  bash ${REMOTE_DIR}/B2_port_scan.sh"
echo "  bash ${REMOTE_DIR}/B3_udp_flood.sh"
echo "  bash ${REMOTE_DIR}/B4_icmp_flood.sh"
echo "  bash ${REMOTE_DIR}/B5_acceso_repetitivo.sh"
echo "  bash ${REMOTE_DIR}/B6_bruteforce.sh"
