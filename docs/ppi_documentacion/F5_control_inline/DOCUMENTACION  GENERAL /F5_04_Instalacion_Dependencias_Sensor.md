# F5-04: Instalación Completa de Dependencias en el Sensor

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F5 — Control Inline e Integración  
**Documento:** F5-04 — Guía de Instalación de Dependencias  
**Sensor:** Ubuntu (.110) — 192.168.0.110  
**Fecha:** 2026-06-14

---

## Resumen de Dependencias

| Capa | Componente | Paquete | Tipo |
|---|---|---|---|
| Sistema operativo | ipset | `ipset` | apt |
| Sistema operativo | iptables | `iptables` | apt (preinstalado) |
| IDS/Captura | Suricata 7.0.3 | `suricata` | apt (PPA) |
| Python entorno | Entorno virtual | `python3-venv` | apt |
| Python ML | Isolation Forest | `scikit-learn==1.8.0` | pip |
| Python ML | Arrays numéricos | `numpy` | pip |
| Python alertas | Cliente HTTP async | `aiohttp` | pip |
| Python serialización | Guardar/cargar modelo | `joblib` | pip |
| Python dashboard | Visualización terminal | `rich` | pip (opcional) |
| Python drift | Test estadístico KS | `scipy` | pip |

---

## 1. Preparación del Sistema Operativo

```bash
# Conectar al sensor
ssh m4rk@192.168.0.110

# Actualizar repositorios
sudo apt update && sudo apt upgrade -y

# Dependencias de sistema base
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    ipset \
    iptables \
    curl \
    wget \
    git \
    tmux \
    net-tools \
    build-essential \
    libssl-dev \
    libffi-dev

# Verificar versiones
python3 --version        # debe ser >= 3.8
ipset --version          # debe aparecer versión
iptables --version       # debe aparecer versión
```

---

## 2. Instalación de Suricata 7.0.3

```bash
# Agregar PPA oficial de Suricata (OISF)
sudo add-apt-repository ppa:oisf/suricata-stable -y
sudo apt update

# Instalar Suricata
sudo apt install -y suricata

# Verificar versión instalada
suricata --version
# Esperado: Suricata 7.0.3 RELEASE

# Habilitar e iniciar el servicio
sudo systemctl enable suricata
sudo systemctl start suricata
sudo systemctl status suricata

# Verificar que captura en ens35 (interfaz de red del laboratorio)
sudo suricata-update          # actualizar reglas
sudo ip link set ens35 promisc on   # modo promiscuo

# Confirmar que eve.json se está generando
tail -f /var/log/suricata/eve.json | head -5
```

---

## 3. Creación del Entorno Virtual Python

```bash
# Crear directorio del proyecto si no existe
mkdir -p /home/m4rk/ppi-sensor
cd /home/m4rk/ppi-sensor

# Crear entorno virtual
python3 -m venv venv

# Activar el entorno (necesario para todos los pasos siguientes)
source /home/m4rk/ppi-sensor/venv/bin/activate

# Verificar que el venv está activo
which python3
# Debe mostrar: /home/m4rk/ppi-sensor/venv/bin/python3

# Actualizar pip dentro del venv
pip install --upgrade pip
```

---

## 4. Instalación de Dependencias Python

```bash
# Asegurarse de tener el venv activo
source /home/m4rk/ppi-sensor/venv/bin/activate

# ── ML y procesamiento numérico ────────────────────────────────────────
pip install scikit-learn==1.8.0
pip install numpy
pip install scipy
pip install joblib

# ── Alertas Telegram (async HTTP) ─────────────────────────────────────
pip install aiohttp

# ── Dashboard terminal (opcional, mejora visual) ───────────────────────
pip install rich

# ── Utilidades de datos ────────────────────────────────────────────────
pip install pandas        # para scripts de análisis offline (F3, F6)

# ── Verificar todas las instalaciones ─────────────────────────────────
python3 -c "
import sklearn; print(f'scikit-learn: {sklearn.__version__}')
import numpy;   print(f'numpy:        {numpy.__version__}')
import scipy;   print(f'scipy:        {scipy.__version__}')
import joblib;  print(f'joblib:       {joblib.__version__}')
import aiohttp; print(f'aiohttp:      {aiohttp.__version__}')
import pandas;  print(f'pandas:       {pandas.__version__}')
try:
    import rich; print(f'rich:         {rich.__version__}')
except:
    print('rich:         no instalado (opcional)')
print('Todas las dependencias OK')
"
```

**Salida esperada:**
```
scikit-learn: 1.8.0
numpy:        1.26.x
scipy:        1.13.x
joblib:       1.4.x
aiohttp:      3.9.x
pandas:       2.2.x
rich:         13.x.x
Todas las dependencias OK
```

---

## 5. Generación del requirements.txt

```bash
# Con el venv activo, exportar dependencias exactas
source /home/m4rk/ppi-sensor/venv/bin/activate
pip freeze > /home/m4rk/ppi-surikata-producto/requirements.txt

# Ver el archivo generado
cat /home/m4rk/ppi-surikata-producto/requirements.txt
```

**Contenido esperado de requirements.txt:**
```
aiohttp==3.9.5
aiosignal==1.3.1
attrs==23.2.0
frozenlist==1.4.1
joblib==1.4.2
multidict==6.0.5
numpy==1.26.4
pandas==2.2.2
python-dateutil==2.9.0
pytz==2024.1
rich==13.7.1
scikit-learn==1.8.0
scipy==1.13.1
six==1.16.0
threadpoolctl==3.5.0
yarl==1.9.4
```

### Reinstalación desde requirements.txt (en nuevo entorno)

```bash
# Para reproducir el entorno exacto en otro sensor
python3 -m venv venv
source venv/bin/activate
pip install -r /home/m4rk/ppi-surikata-producto/requirements.txt
```

---

## 6. Configuración de ipset

```bash
# Crear los tres conjuntos ipset del sistema
sudo ipset create ppi_whitelist hash:ip comment 2>/dev/null || true
sudo ipset create ppi_blocked   hash:ip timeout 3600 comment 2>/dev/null || true
sudo ipset create ppi_limited   hash:ip timeout 1800 comment 2>/dev/null || true

# Poblar la whitelist con las IPs del laboratorio
sudo ipset add ppi_whitelist 192.168.0.1   comment "Gateway"
sudo ipset add ppi_whitelist 192.168.0.20  comment "Desktop-Admin"
sudo ipset add ppi_whitelist 192.168.0.110 comment "Sensor-propio"
sudo ipset add ppi_whitelist 192.168.0.120 comment "Servidor"
sudo ipset add ppi_whitelist 192.168.0.130 comment "Reservado"
sudo ipset add ppi_whitelist 192.168.0.140 comment "Reservado"
sudo ipset add ppi_whitelist 127.0.0.1     comment "Loopback"

# Verificar conjuntos creados
sudo ipset list ppi_whitelist
sudo ipset list ppi_blocked
sudo ipset list ppi_limited

# Configurar reglas iptables que usan ipset
sudo iptables -I FORWARD 1 -m set --match-set ppi_blocked src -j DROP
sudo iptables -I FORWARD 2 -m set --match-set ppi_limited src \
    -m hashlimit --hashlimit-name ppi_limit \
    --hashlimit-upto 100/sec \
    --hashlimit-burst 200 \
    --hashlimit-mode srcip \
    -j ACCEPT
sudo iptables -I FORWARD 3 -m set --match-set ppi_limited src -j DROP

# Persistir ipset para sobrevivir reinicios
sudo ipset save > /etc/ipset.conf

# Persistir iptables
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

---

## 7. Configuración del Servicio systemd (ppi-motor.service)

```bash
# Crear el archivo de servicio
sudo tee /etc/systemd/system/ppi-motor.service > /dev/null <<'EOF'
[Unit]
Description=PPI Surikata Motor de Decision
After=network.target suricata.service
Requires=suricata.service

[Service]
Type=simple
User=m4rk
Group=m4rk
WorkingDirectory=/home/m4rk/ppi-surikata-producto
ExecStartPre=/sbin/ipset restore -! /etc/ipset.conf
ExecStart=/home/m4rk/ppi-sensor/venv/bin/python3 \
    /home/m4rk/ppi-surikata-producto/scripts/motor_decision.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ppi-motor

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar el servicio
sudo systemctl daemon-reload
sudo systemctl enable ppi-motor.service

# Iniciar el motor
sudo systemctl start ppi-motor.service

# Verificar estado
sudo systemctl status ppi-motor.service
```

---

## 8. Verificación Final del Sistema Completo

```bash
# Script de verificación integral
cat > /tmp/verificar_ppi.sh << 'EOF'
#!/usr/bin/env bash
echo "=== VERIFICACIÓN PPI-SURIKATA ==="
echo ""

# 1. Suricata
echo "[1] Suricata:"
systemctl is-active suricata && echo "    ✅ Activo" || echo "    ❌ Inactivo"
test -f /var/log/suricata/eve.json && echo "    ✅ eve.json existe" || echo "    ❌ eve.json no encontrado"

# 2. Python y venv
echo "[2] Python / venv:"
/home/m4rk/ppi-sensor/venv/bin/python3 -c \
    "import sklearn,numpy,aiohttp,joblib,scipy; print('    ✅ Todas las libs OK')" \
    2>/dev/null || echo "    ❌ Faltan dependencias Python"

# 3. Modelos
echo "[3] Modelos ML:"
test -f /home/m4rk/ppi-surikata-producto/models/isolation_forest.pkl \
    && echo "    ✅ isolation_forest.pkl" || echo "    ❌ isolation_forest.pkl no encontrado"
test -f /home/m4rk/ppi-surikata-producto/models/scaler.pkl \
    && echo "    ✅ scaler.pkl" || echo "    ❌ scaler.pkl no encontrado"
test -f /home/m4rk/ppi-surikata-producto/results/umbrales_finales.txt \
    && echo "    ✅ umbrales_finales.txt" || echo "    ❌ umbrales_finales.txt no encontrado"

# 4. ipset
echo "[4] ipset:"
ipset list ppi_blocked  > /dev/null 2>&1 && echo "    ✅ ppi_blocked" || echo "    ❌ ppi_blocked no existe"
ipset list ppi_limited  > /dev/null 2>&1 && echo "    ✅ ppi_limited" || echo "    ❌ ppi_limited no existe"
ipset list ppi_whitelist > /dev/null 2>&1 && echo "    ✅ ppi_whitelist" || echo "    ❌ ppi_whitelist no existe"

# 5. Motor de decisión
echo "[5] Motor ppi-motor.service:"
systemctl is-active ppi-motor.service && echo "    ✅ Activo" || echo "    ⚠️  Inactivo (iniciar con: sudo systemctl start ppi-motor.service)"

# 6. Log del motor
echo "[6] Log del motor:"
LOG=/home/m4rk/ppi-surikata-producto/results/motor_decision.log
test -f "$LOG" && echo "    ✅ motor_decision.log existe ($(wc -l < "$LOG") líneas)" \
               || echo "    ⚠️  Log aún no generado (el motor debe estar corriendo)"

echo ""
echo "=== FIN DE VERIFICACIÓN ==="
EOF

bash /tmp/verificar_ppi.sh
```

**Salida esperada cuando todo está correcto:**
```
=== VERIFICACIÓN PPI-SURIKATA ===

[1] Suricata:
    ✅ Activo
    ✅ eve.json existe

[2] Python / venv:
    ✅ Todas las libs OK

[3] Modelos ML:
    ✅ isolation_forest.pkl
    ✅ scaler.pkl
    ✅ umbrales_finales.txt

[4] ipset:
    ✅ ppi_blocked
    ✅ ppi_limited
    ✅ ppi_whitelist

[5] Motor ppi-motor.service:
    ✅ Activo

[6] Log del motor:
    ✅ motor_decision.log existe (14823 líneas)

=== FIN DE VERIFICACIÓN ===
```

---

## 9. Orden de Instalación Recomendado

```
PASO 1  apt update + paquetes base (python3-venv, ipset, curl...)
   │
PASO 2  Instalar Suricata 7.0.3 via PPA + configurar ens35 promiscuo
   │
PASO 3  Crear venv en /home/m4rk/ppi-sensor/venv
   │
PASO 4  pip install: scikit-learn==1.8.0, numpy, scipy, joblib, aiohttp, rich, pandas
   │
PASO 5  Configurar ipset: crear ppi_whitelist, ppi_blocked, ppi_limited + poblar whitelist
   │
PASO 6  Configurar iptables: reglas FORWARD con ipset + persistir con netfilter-persistent
   │
PASO 7  Copiar proyecto a /home/m4rk/ppi-surikata-producto/
         (modelos .pkl, scripts, umbrales_finales.txt)
   │
PASO 8  Crear y habilitar ppi-motor.service en systemd
   │
PASO 9  Ejecutar verificar_ppi.sh → todos los checks deben ser ✅
   │
PASO 10 Dashboard: python3 scripts/dashboard.py (en tmux o segunda terminal)
```

---

## 10. Solución de Problemas Comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ipset: command not found` | ipset no instalado | `sudo apt install ipset` |
| `ModuleNotFoundError: sklearn` | venv no activado | `source /home/m4rk/ppi-sensor/venv/bin/activate` |
| `scikit-learn version mismatch` | Versión incorrecta | `pip install scikit-learn==1.8.0` |
| Motor no inicia (systemd) | eve.json no existe | Verificar que Suricata esté activo |
| Telegram no envía | Token o chat_id incorrecto | Verificar con `curl` el endpoint de Telegram |
| ipset rules perdidas tras reboot | netfilter-persistent no configurado | `sudo netfilter-persistent save` |
| `Permission denied` en ipset | Motor corre sin sudo | Agregar `m4rk` al grupo con permisos ipset o usar sudo en enforce.sh |
| eve.json vacío | Suricata no captura en ens35 | `sudo ip link set ens35 promisc on` |

---

*Documento generado: 2026-06-14*  
*Sensor: Ubuntu 192.168.0.110 | venv: /home/m4rk/ppi-sensor/venv*  
*scikit-learn 1.8.0 validado en producción con 40 corridas F6*
