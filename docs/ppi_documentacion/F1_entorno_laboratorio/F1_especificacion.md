# F1 — Especificación Técnica: Entorno de Laboratorio

## Objetivo
Configurar la topología de red virtualizada y validar conectividad entre los 5 nodos antes de iniciar la captura de tráfico.

## Infraestructura desplegada

| VM | IP | SO | Rol | Software clave |
|---|---|---|---|---|
| Win11 Cliente | 192.168.0.10 | Windows 11 | Cliente de red | Navegador, ping |
| Ubuntu Desktop | 192.168.0.20 | Ubuntu 22.04 | Admin / tráfico normal | Claude Code, curl, scp, ssh |
| Kali Linux | 192.168.0.100 | Kali 2024 | Origen de ataques | hping3, nmap, hydra, sshpass |
| Ubuntu Sensor | 192.168.0.110 | Ubuntu 22.04 | Captura + Motor | Suricata 7.0.3, Python 3.12, venv |
| Ubuntu Server | 192.168.0.120 | Ubuntu 22.04 | Servicio objetivo | nginx 1.24 (:80), OpenSSH (:22) |

- **Red:** 192.168.0.0/24 — todos en el mismo segmento (switch virtual)
- **Usuario:** `m4rk` en todas las VMs · contraseña SSH: `cisco123`
- **SSH keys:** Desktop → Sensor (BatchMode), Desktop → Server (BatchMode)

## Suricata — configuración en sensor

| Parámetro | Valor |
|---|---|
| Interfaz de captura | `ens35` (interna de laboratorio) |
| Archivo de salida | `/var/log/suricata/eve.json` (formato EVE JSON) |
| Versión | 7.0.3 |
| Servicio | `systemd: suricata.service` |

## Motor — servicio systemd en sensor

| Parámetro | Valor |
|---|---|
| Servicio | `ppi-motor.service` |
| WorkingDirectory | `/home/m4rk/ppi-surikata-producto` |
| ExecStart | `/home/m4rk/ppi-sensor/venv/bin/python3 scripts/motor_decision.py` |
| Restart | `on-failure` |

## Secuencia de verificación F1

```bash
# 1. Verificar que todos los nodos responden
ssh m4rk@192.168.0.110 "echo OK sensor"
ssh m4rk@192.168.0.120 "echo OK servidor"

# 2. Verificar Suricata activo
ssh m4rk@192.168.0.110 "systemctl is-active suricata"

# 3. Verificar Motor activo
ssh m4rk@192.168.0.110 "systemctl is-active ppi-motor.service"

# 4. Verificar ipsets en servidor
ssh m4rk@192.168.0.120 "sudo ipset list -n"
# Esperado: ppi_blocked, ppi_limited

# 5. Verificar iptables en servidor
ssh m4rk@192.168.0.120 "sudo iptables -L INPUT -n --line-numbers"
# Esperado: líneas 1 y 2 con DROP y hashlimit para los sets PPI
```

## Whitelist de IPs (nunca bloquear)

`192.168.0.1`, `192.168.0.20`, `192.168.0.110`, `192.168.0.120`, `192.168.0.130`, `192.168.0.140`, `127.0.0.1`
