# F1-03: Sincronización Horaria y Zona Horaria — NTP + America/Lima

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F1 — Preparación del Entorno de Laboratorio  
**Documento:** F1-03 — Plan de Migración de Zona Horaria a America/Lima  
**Fecha:** 2026-06-15

---

## 1. Contexto y Motivación

### 1.1 Estado detectado

Al verificar las tres VMs del laboratorio el 2026-06-15, todas operan en zona horaria **UTC (+0000)**:

| VM | IP | Timezone actual | Hora local (momento del diagnóstico) |
|---|---|---|---|
| Desktop Ubuntu (Admin) | 192.168.0.20 | UTC +0000 | 02:25 UTC |
| Sensor Ubuntu | 192.168.0.110 | UTC +0000 | 02:25 UTC |
| Servidor Ubuntu | 192.168.0.120 | UTC +0000 | 02:25 UTC |

> Hora equivalente en Lima al momento del diagnóstico: **21:25 PET (UTC-5)**, día anterior.

El NTP ya está activo y los relojes están sincronizados entre sí (diferencia < 7 segundos). **No existe desincronización entre VMs** — el problema es únicamente de zona horaria de presentación.

### 1.2 Por qué se migra a America/Lima

- El proyecto es desarrollado y evaluado en Perú (Universidad Peruana Unión).
- El jurado evaluará el sistema con referencias horarias peruanas.
- Las alertas de Telegram y el dashboard web mostrarán horas UTC que no corresponden a la realidad local del operador.
- La bitácora de corridas futura debe registrar tiempos en hora local para coherencia con el contexto de defensa.
- Peru Standard Time (PET) = **UTC − 5**, sin horario de verano (Perú no aplica DST).

---

## 2. Análisis de Impacto

### 2.1 Componentes NO afectados por el cambio

| Componente | Razón |
|---|---|
| Modelo Isolation Forest (`.pkl`) | Usa `duration = flow.end − flow.start`: tiempo relativo, nunca timestamps absolutos |
| Features del modelo (14 variables) | `pkt_rate`, `byte_rate`, `duration`, etc. son deltas — independientes de la zona horaria |
| eve.json histórico (40 corridas) | Suricata graba offset explícito (`+0000`) en cada timestamp ISO 8601 — el dato es autosuficiente |
| AUC-ROC, métricas F3/F6 | Calculadas sobre scores IF, no sobre timestamps absolutos |
| ipset / iptables | Reglas de red no dependen del reloj del sistema |
| Conectividad entre VMs | Sin impacto |

### 2.2 Componentes que cambian de presentación (sin pérdida de datos)

| Componente | Cambio | Impacto real |
|---|---|---|
| `motor_decision.log` (entradas nuevas) | `datetime.now()` mostrará hora Lima | Positivo: hora local en alertas |
| Alertas Telegram | Timestamps en hora Lima | Positivo: legible para operador peruano |
| Dashboard web | Hora de eventos en Lima | Positivo |
| eve.json (eventos nuevos) | Suricata escribirá `-0500` en lugar de `+0000` | Cosmético — ambos son correctos |
| Bitácora manual futura | Nuevas entradas en hora Lima | Coherente con el contexto |

### 2.3 Efecto visible en logs (no es un error)

```
# Entradas históricas (UTC — no cambian):
2026-06-15 02:04:26 | INFO | Monitoreando /var/log/suricata/eve.json ...

# Entradas nuevas tras el cambio (Lima = UTC-5):
2026-06-14 21:04:26 | INFO | Monitoreando /var/log/suricata/eve.json ...
```

El "salto" de día (15 → 14) es correcto: las 02:04 UTC del día 15 equivalen a las 21:04 del día 14 en Lima. No es un error del sistema.

---

## 3. Plan de Migración

### 3.1 Orden de ejecución

```
PASO 1  Verificar estado NTP en las 3 VMs (diagnóstico)
   │
PASO 2  Cambiar timezone en Desktop (192.168.0.20)
   │
PASO 3  Cambiar timezone en Servidor (192.168.0.120)
   │
PASO 4  Cambiar timezone en Sensor (192.168.0.110)
   │
PASO 5  Reiniciar motor de decisión en Sensor
         (para que datetime.now() tome el nuevo timezone)
   │
PASO 6  Verificar coherencia entre las 3 VMs
   │
PASO 7  Enviar alerta de prueba Telegram — confirmar hora Lima
   │
PASO 8  Registrar cambio en bitácora
```

### 3.2 Comandos por paso

#### PASO 1 — Diagnóstico (verificar antes de cambiar)

```bash
# Desde Desktop — verificar las 3 VMs simultáneamente
echo "=== DESKTOP ===" && timedatectl
echo "=== SENSOR  ===" && ssh m4rk@192.168.0.110 "timedatectl"
echo "=== SERVIDOR ===" && ssh m4rk@192.168.0.120 "timedatectl"
```

Salida esperada antes del cambio:
```
Time zone: UTC (UTC, +0000)
NTP service: active
System clock synchronized: yes
```

---

#### PASO 2 — Cambiar timezone en Desktop (192.168.0.20)

```bash
sudo timedatectl set-timezone America/Lima
timedatectl   # verificar
date          # debe mostrar hora Lima
```

---

#### PASO 3 — Cambiar timezone en Servidor (192.168.0.120)

```bash
ssh m4rk@192.168.0.120 "sudo timedatectl set-timezone America/Lima && timedatectl"
```

---

#### PASO 4 — Cambiar timezone en Sensor (192.168.0.110)

```bash
ssh m4rk@192.168.0.110 "sudo timedatectl set-timezone America/Lima && timedatectl"
```

---

#### PASO 5 — Reiniciar Motor de Decisión en Sensor

Necesario para que `datetime.now()` en `motor_decision.py` use el nuevo timezone:

```bash
ssh m4rk@192.168.0.110 "
  pkill -f motor_decision.py
  sleep 2
  cd /home/m4rk/ppi-surikata-producto
  nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/motor_decision.py \
    >> results/motor_decision.log 2>&1 &
  echo 'Motor reiniciado PID:' \$!
"
```

---

#### PASO 6 — Verificar coherencia entre las 3 VMs

```bash
echo "=== DESKTOP  ===" && date && timedatectl | grep "Time zone"
echo "=== SENSOR   ===" && ssh m4rk@192.168.0.110 "date; timedatectl | grep 'Time zone'"
echo "=== SERVIDOR ===" && ssh m4rk@192.168.0.120 "date; timedatectl | grep 'Time zone'"
```

Salida esperada:
```
=== DESKTOP  ===
dom 14 jun 2026 21:3x:xx PET
Time zone: America/Lima (PET, -0500)

=== SENSOR   ===
dom 14 jun 2026 21:3x:xx PET
Time zone: America/Lima (PET, -0500)

=== SERVIDOR ===
dom 14 jun 2026 21:3x:xx PET
Time zone: America/Lima (PET, -0500)
```

> Las 3 VMs deben mostrar la misma hora Lima y la misma diferencia de segundos que antes del cambio.

---

#### PASO 7 — Verificar alerta Telegram con hora Lima

```bash
ssh m4rk@192.168.0.110 "/home/m4rk/ppi-sensor/venv/bin/python3 - <<'EOF'
import urllib.request, urllib.parse
from datetime import datetime

TG_TOKEN   = '8677152686:AAEUKDJm0gbkc7Vu3NwRcNaxqx3iqQwaa7g'
TG_CHAT_ID = '8512353253'

msg = (
    '✅ PPI — Zona horaria migrada a Lima (PET UTC-5)\n'
    'Hora local: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n'
    'Sensor: 192.168.0.110\n'
    'NTP: activo y sincronizado'
)
url  = f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage'
data = urllib.parse.urlencode({'chat_id': TG_CHAT_ID, 'text': msg}).encode()
req  = urllib.request.Request(url, data=data)
r    = urllib.request.urlopen(req, timeout=10)
print('OK — revisa Telegram')
EOF"
```

El mensaje en Telegram debe mostrar la hora Lima correcta.

---

#### PASO 8 — Verificar log del motor con nueva hora

```bash
ssh m4rk@192.168.0.110 "tail -3 /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
```

Las nuevas entradas deben mostrar hora Lima (e.g., `2026-06-14 21:3x:xx`).

---

## 4. Verificación Final

```bash
# Script de verificación completa post-migración
ssh m4rk@192.168.0.110 "bash -s" <<'EOF'
echo "====== VERIFICACIÓN NTP + TIMEZONE ======"
echo ""
echo "[1] Timezone sensor:"
timedatectl | grep -E "Time zone|synchronized|NTP"
echo ""
echo "[2] Hora actual Lima:"
date
echo ""
echo "[3] Motor corriendo:"
ps aux | grep motor_decision | grep -v grep | awk '{print "  PID:", $2, "| Iniciado:", $9}'
echo ""
echo "[4] Últimas 2 líneas del log (hora Lima):"
tail -2 /home/m4rk/ppi-surikata-producto/results/motor_decision.log
echo ""
echo "====== FIN ======"
EOF
```

Salida esperada:
```
====== VERIFICACIÓN NTP + TIMEZONE ======

[1] Timezone sensor:
               Time zone: America/Lima (PET, -0500)
  System clock synchronized: yes
             NTP service: active

[2] Hora actual Lima:
dom 14 jun 2026 21:3x:xx PET

[3] Motor corriendo:
  PID: XXXXXX | Iniciado: 21:3x

[4] Últimas 2 líneas del log (hora Lima):
2026-06-14 21:3x:xx,xxx | INFO | Monitoreando /var/log/suricata/eve.json ...
2026-06-14 21:3x:xx,xxx | INFO | Brute Force SSH : ventana=60s umbral_limit=5 umbral_block=15

====== FIN ======
```

---

## 5. Impacto en la Defensa del Jurado

| Escenario de defensa | Sin migración (UTC) | Con migración (Lima) |
|---|---|---|
| Jurado pregunta "¿a qué hora detectó el ataque?" | "A las 02:37 UTC" (confuso) | "A las 21:37 hora Lima" (natural) |
| Alerta Telegram en vivo | `Hora: 2026-06-15 02:37:12` | `Hora: 2026-06-14 21:37:12` |
| Comparar log con bitácora | Requiere restar 5 horas | Coincide directamente |
| Credibilidad del sistema | Log desconectado de la realidad local | Log refleja el entorno real |

---

## 6. Rollback (si fuera necesario)

Si por alguna razón se necesita revertir a UTC:

```bash
# En cada VM
sudo timedatectl set-timezone UTC

# Reiniciar motor en sensor
ssh m4rk@192.168.0.110 "pkill -f motor_decision.py; sleep 2; \
  cd /home/m4rk/ppi-surikata-producto && \
  nohup /home/m4rk/ppi-sensor/venv/bin/python3 scripts/motor_decision.py \
  >> results/motor_decision.log 2>&1 &"
```

> El rollback no afecta datos históricos — los registros en eve.json y motor_decision.log ya tienen sus timestamps grabados con el offset correspondiente al momento de escritura.

---

## 7. Decisión Final

| Factor | Evaluación |
|---|---|
| Riesgo para el modelo IF | Ninguno |
| Riesgo para datos históricos | Ninguno |
| Riesgo para ipset/iptables | Ninguno |
| Beneficio para la defensa | Alto |
| Complejidad de implementación | Muy baja (1 comando por VM) |
| Reversibilidad | Total |

**Recomendación: APLICAR.** El cambio es seguro, rápido y mejora la legibilidad del sistema para el contexto peruano de la defensa.

---

*Documento generado: 2026-06-15*  
*Estado: pendiente de ejecución*  
*Kali Linux (192.168.0.100) no requiere cambio — es solo origen de tráfico de prueba*
