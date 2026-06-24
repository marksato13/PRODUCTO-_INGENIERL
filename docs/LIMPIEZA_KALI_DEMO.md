# Procedimiento de Limpieza Kali para Demo Limpia

Cuando necesites hacer una demo o prueba limpia, sigue estos pasos para asegurarte de que:
- No hay ataques residuales en Kali
- El sensor y servidor no bloquean la IP de Kali
- Todo está reseteable para una nueva prueba

## Paso 1: Matar procesos de ataque en Kali

```bash
# Desde Kali (vía SSH o directo en VM)
sudo pkill -9 hping3

# Verificar que está limpio
ps aux | grep hping3
# (No debe salir nada, solo el grep mismo)
```

## Paso 2: Esperar 90 segundos

```bash
# Esperar a que Suricata vacíe flows residuales (~60s)
# y que los timeouts de bloqueo se procesen
sleep 90
```

## Paso 3: Limpiar ipset en servidor (192.168.0.120)

```bash
ssh m4rk@192.168.0.120 "sudo ipset flush ppi_blocked && sudo ipset flush ppi_limited"
```

**Verifica:**
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked && echo '---' && sudo ipset list ppi_limited"
# Deben estar vacíos
```

## Paso 4: Limpiar block_counts en sensor (192.168.0.110)

```bash
ssh m4rk@192.168.0.110 "echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json"
```

## Paso 5: Reiniciar motor y predictor

```bash
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service ppi-predictor.service"

# Verificar que están activos
ssh m4rk@192.168.0.110 "systemctl status ppi-motor.service ppi-predictor.service"
```

## Paso 6: Verificar que Kali NO está bloqueado

```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 192.168.0.100"
# Si NO sale nada → ✅ Kali no está bloqueado
```

## Paso 7: Probar tráfico normal desde Kali

```bash
# Desde Kali:
curl -I http://192.168.0.120:80

# Debe responder:
# HTTP/1.1 200 OK
```

## Resumen (Script automático)

Si quieres hacerlo todo de una vez:

```bash
#!/bin/bash
echo "1. Matando procesos en Kali..."
ssh m4rk@192.168.0.100 "sudo pkill -9 hping3" || true

echo "2. Esperando 90 segundos..."
sleep 90

echo "3. Limpiando ipset en servidor..."
ssh m4rk@192.168.0.120 "sudo ipset flush ppi_blocked && sudo ipset flush ppi_limited"

echo "4. Limpiando block_counts en sensor..."
ssh m4rk@192.168.0.110 "echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json"

echo "5. Reiniciando motor..."
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service ppi-predictor.service"

echo "6. Verificando que Kali no está bloqueado..."
BLOQUEADO=$(ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 192.168.0.100")
if [ -z "$BLOQUEADO" ]; then
  echo "✅ Kali LIMPIO - NO está bloqueado"
else
  echo "❌ Kali aún está bloqueado"
fi

echo "7. Probando tráfico normal..."
ssh m4rk@192.168.0.100 "curl -I http://192.168.0.120:80"
```

## Notas críticas

- **Contraseña sudo Kali:** Es `Cisco123` (C mayúscula) en sesión interactiva. Para SSH sin TTY, usar `echo cisco123 | sudo -S` en sensor/servidor.
- **logrotate:** El motor_decision.log se rota a medianoche — si haces demo después de la medianoche, tendrás log nuevo limpio.
- **block_counts.json:** Almacena el historial de bloqueos en memoria del proceso. Reiniciando el motor se resetea.
