# F1 — Especificación Técnica: Entorno de Laboratorio

## 1. Objetivo

Desplegar y verificar la topología de red virtualizada de 5 nodos que sirve de infraestructura
para todas las fases del PPI. Al final de F1 el entorno debe estar completamente operativo:
conectividad verificada, Suricata capturando tráfico, ipsets y reglas iptables activas en el
servidor, y el motor de decisión listo para iniciar.

---

## 2. Entradas

F1 es la fase de setup inicial. No recibe archivos de fases anteriores.

| Entrada | Descripción |
|---|---|
| Hipervisor (VMware/VirtualBox) | 5 VMs configuradas en red interna 192.168.0.0/24 |
| Paquetes del sistema | suricata, python3, python3-venv, nginx, openssh-server, ipset, iptables |
| Repositorio del proyecto | `github.com/marksato13/PRODUCTO-_INGENIERL` clonado en sensor |

---

## 3. Salidas

| Salida | Ruta | Descripción |
|---|---|---|
| Suricata activo | `suricata.service` (sensor) | Capturando en `ens35`, escribiendo `/var/log/suricata/eve.json` |
| Motor systemd | `ppi-motor.service` (sensor) | Listo para iniciar; arranca `motor_decision.py` con el venv |
| ipset ppi_blocked | servidor 192.168.0.120 | Set tipo `hash:ip timeout 3600` — IPs bloqueadas con DROP |
| ipset ppi_limited | servidor 192.168.0.120 | Set tipo `hash:ip timeout 3600` — IPs con hashlimit 100 pkt/s |
| Reglas iptables | servidor 192.168.0.120 | INPUT -m set --match-set ppi_blocked src -j DROP (línea 1) |
| SSH keys | Desktop → Sensor, Desktop → Server | BatchMode sin contraseña para automatización |
| Entorno virtual Python | `/home/m4rk/ppi-sensor/venv/` (sensor) | Python 3.12, sklearn 1.9.0, suricata-update, flask |
| Whitelist cargada | `motor_decision.py` (en código) | 7 IPs nunca bloqueadas |

---

## 4. Infraestructura desplegada

| VM | IP | SO | Rol en el PPI | Software clave |
|---|---|---|---|---|
| Win11 Cliente | 192.168.0.10 | Windows 11 | Cliente de red (referencia) | Navegador, ping |
| Ubuntu Desktop | 192.168.0.20 | Ubuntu 22.04 LTS | Administrador / origen tráfico normal | curl, wget, scp, ssh, Claude Code |
| Kali Linux | 192.168.0.100 | Kali 2024.2 | Origen de tráfico anómalo (ataques) | hping3, nmap, hydra, sshpass |
| Ubuntu Sensor | 192.168.0.110 | Ubuntu 22.04 LTS | Captura IDS + Motor de decisión | Suricata 7.0.3, Python 3.12, venv |
| Ubuntu Server | 192.168.0.120 | Ubuntu 22.04 LTS | Servicio objetivo | nginx 1.24 (:80), OpenSSH (:22), ipset, iptables |

**Red:** 192.168.0.0/24 — todos los nodos en el mismo segmento (switch virtual sin enrutamiento externo).  
**Usuario:** `m4rk` en todas las VMs. Contraseña SSH: `cisco123`.

---

## 5. Configuración técnica — Suricata (sensor 192.168.0.110)

| Parámetro | Valor |
|---|---|
| Interfaz de captura | `ens35` (interfaz interna del laboratorio) |
| Modo | IDS pasivo (af-packet) — no bloquea, solo genera eventos |
| Formato de salida | EVE JSON (`/var/log/suricata/eve.json`) |
| Versión | 7.0.3 |
| Servicio systemd | `suricata.service` |
| Timeout TCP half-open | ~60 s (valor por defecto de Suricata) — relevante para Lead Time en F6 |
| Tipos de eventos registrados | `flow`, `alert`, `http`, `ssh`, `dns` |

```yaml
# /etc/suricata/suricata.yaml (secciones relevantes)
af-packet:
  - interface: ens35
    cluster-id: 99
    cluster-type: cluster_flow
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      types:
        - flow
        - alert
        - http
        - ssh
        - dns
```

---

## 6. Configuración técnica — Motor de decisión (sensor 192.168.0.110)

| Parámetro | Valor |
|---|---|
| Servicio systemd | `ppi-motor.service` |
| WorkingDirectory | `/home/m4rk/ppi-surikata-producto` |
| ExecStart | `/home/m4rk/ppi-sensor/venv/bin/python3 scripts/motor_decision.py` |
| Restart | `on-failure` |
| Entorno virtual | `/home/m4rk/ppi-sensor/venv/` |
| Dependencias Python | scikit-learn 1.9.0, numpy, pandas, flask, suricata-update |

```ini
# /etc/systemd/system/ppi-motor.service
[Unit]
Description=PPI Motor de Decision IF
After=network.target suricata.service

[Service]
User=m4rk
WorkingDirectory=/home/m4rk/ppi-surikata-producto
ExecStart=/home/m4rk/ppi-sensor/venv/bin/python3 scripts/motor_decision.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 7. Configuración técnica — Control inline (servidor 192.168.0.120)

Los ipsets y reglas iptables residen en el **servidor**, no en el sensor. El motor SSH-ea al servidor para cada operación de bloqueo.

### 7.1 Creación de ipsets

```bash
# Ejecutar en 192.168.0.120 (una sola vez, persiste en memoria)
sudo ipset create ppi_blocked hash:ip timeout 3600 -exist
sudo ipset create ppi_limited hash:ip timeout 3600 -exist
```

### 7.2 Reglas iptables (INPUT — antes de ACCEPT general)

```bash
# Línea 1: bloqueo total para IPs en ppi_blocked
sudo iptables -I INPUT 1 -m set --match-set ppi_blocked src -j DROP

# Línea 2: limitación de velocidad para IPs en ppi_limited
sudo iptables -I INPUT 2 -m set --match-set ppi_limited src \
  -m hashlimit --hashlimit-name ppi_limit \
  --hashlimit-above 100/second --hashlimit-mode srcip -j DROP
```

### 7.3 NOPASSWD para ipset (sudoers en servidor)

```
# /etc/sudoers.d/ppi
m4rk ALL=(ALL) NOPASSWD: /usr/sbin/ipset
```

---

## 8. Whitelist de IPs (nunca bloquear)

Codificada directamente en `scripts/motor_decision.py`:

| IP | Rol |
|---|---|
| 192.168.0.1 | Gateway de red |
| 192.168.0.20 | Desktop (generador tráfico normal) |
| 192.168.0.110 | Sensor (el propio motor) |
| 192.168.0.120 | Servidor (objetivo del sistema) |
| 192.168.0.130 | Reservado |
| 192.168.0.140 | Reservado |
| 127.0.0.1 | Loopback |

---

## 9. Secuencia técnica de implementación F1

### Paso 1 — Clonar repositorio en sensor

```bash
# En sensor (192.168.0.110)
cd /home/m4rk
git clone https://github.com/marksato13/PRODUCTO-_INGENIERL.git ppi-surikata-producto
```

### Paso 2 — Crear entorno virtual Python

```bash
# En sensor
python3 -m venv /home/m4rk/ppi-sensor/venv
source /home/m4rk/ppi-sensor/venv/bin/activate
pip install scikit-learn==1.9.0 numpy pandas flask requests
```

### Paso 3 — Instalar y configurar Suricata

```bash
# En sensor
sudo apt-get install -y suricata
sudo systemctl enable suricata
# Editar /etc/suricata/suricata.yaml → interfaz ens35
sudo systemctl start suricata
```

### Paso 4 — Registrar servicio del motor

```bash
# En sensor
sudo cp /home/m4rk/ppi-surikata-producto/config/ppi-motor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ppi-motor.service
# (no iniciar aún — F2 requiere motor detenido durante captura)
```

### Paso 5 — Configurar ipsets y iptables en servidor

```bash
# En servidor (192.168.0.120)
sudo ipset create ppi_blocked hash:ip timeout 3600 -exist
sudo ipset create ppi_limited hash:ip timeout 3600 -exist
sudo iptables -I INPUT 1 -m set --match-set ppi_blocked src -j DROP
sudo iptables -I INPUT 2 -m set --match-set ppi_limited src \
  -m hashlimit --hashlimit-name ppi_limit \
  --hashlimit-above 100/second --hashlimit-mode srcip -j DROP
```

### Paso 6 — Configurar SSH keys Desktop → Sensor/Servidor

```bash
# En Desktop (192.168.0.20)
ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
ssh-copy-id m4rk@192.168.0.110   # → sensor
ssh-copy-id m4rk@192.168.0.120   # → servidor
# Verificar BatchMode
ssh -o BatchMode=yes m4rk@192.168.0.110 "echo OK"
ssh -o BatchMode=yes m4rk@192.168.0.120 "echo OK"
```

---

## 10. Secuencia de verificación F1

```bash
# Desde Desktop (192.168.0.20) — ejecutar todo en orden

# 1. Conectividad básica
ssh -o BatchMode=yes m4rk@192.168.0.110 "echo OK sensor"
ssh -o BatchMode=yes m4rk@192.168.0.120 "echo OK servidor"

# 2. Suricata activo y escribiendo eve.json
ssh m4rk@192.168.0.110 "systemctl is-active suricata && \
  ls -lh /var/log/suricata/eve.json"
# Esperado: active  y archivo presente

# 3. Motor registrado (no necesariamente activo en F1)
ssh m4rk@192.168.0.110 "systemctl status ppi-motor.service | head -5"

# 4. ipsets presentes en servidor
ssh m4rk@192.168.0.120 "sudo ipset list -n"
# Esperado: ppi_blocked  ppi_limited

# 5. Reglas iptables activas en servidor
ssh m4rk@192.168.0.120 "sudo iptables -L INPUT -n --line-numbers | head -6"
# Esperado: líneas 1 y 2 referenciando ppi_blocked / ppi_limited

# 6. Entorno virtual con sklearn correcto
ssh m4rk@192.168.0.110 \
  "/home/m4rk/ppi-sensor/venv/bin/python3 -c \
  'import sklearn; print(sklearn.__version__)'"
# Esperado: 1.9.0
```

---

## 11. Criterios de éxito (salida de F1)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| Conectividad Desktop → Sensor | `ssh BatchMode echo OK` | `OK sensor` |
| Conectividad Desktop → Servidor | `ssh BatchMode echo OK` | `OK servidor` |
| Suricata activo | `systemctl is-active suricata` | `active` |
| eve.json generándose | `ls -lh /var/log/suricata/eve.json` | Archivo presente y creciendo |
| ipset ppi_blocked existe | `ipset list -n` | Nombre listado |
| ipset ppi_limited existe | `ipset list -n` | Nombre listado |
| Regla DROP activa | `iptables -L INPUT -n` | Línea 1 con `ppi_blocked` |
| sklearn 1.9.0 en venv | `python3 -c 'import sklearn; print(sklearn.__version__)'` | `1.9.0` |
| SSH keys sin contraseña | `ssh -o BatchMode=yes` | Sin prompt |

**F1 se considera COMPLETADA** cuando todos los criterios anteriores pasan sin errores.  
El entorno validado es el punto de partida para F2 (captura de tráfico).

---

## 12. Rutas clave del proyecto (sensor)

```
/home/m4rk/ppi-surikata-producto/
├── scripts/          ← todos los scripts Python y bash
├── data/raw/         ← capturas eve.json.gz (se pobla en F2)
├── models/           ← modelo entrenado (se genera en F3)
├── results/          ← métricas, logs, gráficas (F3–F6)
└── docs/             ← esta documentación

/home/m4rk/ppi-sensor/venv/   ← entorno Python aislado
/var/log/suricata/eve.json     ← salida live de Suricata
/etc/systemd/system/ppi-motor.service
```
