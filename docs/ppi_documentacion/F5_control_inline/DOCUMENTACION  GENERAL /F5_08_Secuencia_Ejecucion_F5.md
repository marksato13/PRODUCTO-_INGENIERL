# F5 — Secuencia exacta de ejecución: control inline con ipset/iptables

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Scripts:** `motor_decision.py` (funciones F5) + `scripts/enforce.sh`

---

## Qué es F5 y qué relación tiene con F4

F5 no es un script que se ejecuta por separado — es la **capa de actuación** que vive dentro de `motor_decision.py`. Cuando F4 toma la decisión BLOCK o LIMIT, F5 es quien ejecuta el comando en el servidor. Son la misma ejecución, funciones distintas:

```
F4: motor_decision.py → decide (score + detectores) → llama funciones F5
F5: bloquear_ip() / limitar_ip() → SSH → ipset en servidor → iptables actúa
```

F5 también incluye `enforce.sh`, que permite control manual independiente del motor automático.

---

## Punto de partida: infraestructura requerida

Para que F5 funcione deben existir en el **servidor (192.168.0.120)**:

```bash
# Verificar que ipset y las reglas están activas
sudo ipset list ppi_blocked    # hash:ip timeout 300
sudo ipset list ppi_limited    # hash:ip timeout 300
sudo iptables -L INPUT --line-numbers -n
```

Salida real verificada (14 junio 2026):

```
Chain INPUT (policy ACCEPT)
num  target  prot opt source        destination
1    DROP    all  --  0.0.0.0/0    0.0.0.0/0    match-set ppi_blocked src
2    DROP    all  --  0.0.0.0/0    0.0.0.0/0    match-set ppi_limited src
                                                  limit: above 100/sec burst 150
                                                  mode srcip
```

Estas estructuras las crea automáticamente `inicializar_servidor()` al arrancar el motor (ver F4-05). Si el servidor se reinicia, el motor las recrea en el próximo arranque.

---

## Cómo se crean las estructuras en el servidor

La función `inicializar_servidor()` en `motor_decision.py` ejecuta por SSH al arrancar:

### Crear ipset BLOCK

```bash
sudo ipset create ppi_blocked hash:ip timeout 300
```

- `hash:ip`: cada entrada es una IP individual (no rangos)
- `timeout 300`: cada IP expira automáticamente a los 300 segundos (5 minutos)
- Si ya existe, el `2>/dev/null || true` evita el error

### Insertar regla DROP para BLOCK (posición 1)

```bash
sudo iptables -I INPUT -m set --match-set ppi_blocked src -j DROP
```

- `-I INPUT`: inserta al inicio de la cadena INPUT (prioridad máxima)
- `--match-set ppi_blocked src`: coincide si la IP origen está en el set
- `-j DROP`: descarta el paquete silenciosamente (sin RST ni ICMP)

### Crear ipset LIMIT

```bash
sudo ipset create ppi_limited hash:ip timeout 300
```

### Insertar regla hashlimit para LIMIT (posición 2)

```bash
sudo iptables -I INPUT 2 -m set --match-set ppi_limited src \
  -m hashlimit \
  --hashlimit-above 100/sec \
  --hashlimit-burst 150 \
  --hashlimit-mode srcip \
  --hashlimit-name ppi_limit \
  -j DROP
```

- Posición 2: justo después del DROP total de BLOCK
- `--hashlimit-above 100/sec`: solo descarta paquetes que superen 100/s
- `--hashlimit-burst 150`: permite ráfagas de hasta 150 paquetes antes de aplicar el límite
- Los paquetes dentro del límite (≤100/s) pasan — la conexión se degrada pero no se corta

---

## Flujo F5 automático: cuando el motor detecta una anomalía

### Caso BLOCK — función `bloquear_ip(ip)`

Se llama desde `motor_decision.py` cuando `score ≤ τ2 (−0.6873)` o cuando un detector heurístico dispara BLOCK:

```python
def bloquear_ip(ip):
    out = _ssh(
        f'sudo ipset add {SET_BLOCK} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
        f'&& echo "BLOCKED {ip}"'
    )
    return out
```

**Comando ejecutado en el servidor:**
```bash
sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist
```

- `-exist`: si la IP ya está en el set, actualiza el timeout sin error
- `timeout 300`: la IP se elimina automáticamente a los 300 segundos
- Desde ese momento: **todo paquete** de esa IP llega al servidor → iptables regla 1 → DROP

**Log generado:**
```
ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP score=−0.7812 grado=ALTA tipo=SYN_FLOOD | BLOCK
```

**Telegram enviado:**
```
🚨 PPI ALERTA — SYN_FLOOD
Accion : BLOCK (DROP)
IP     : 192.168.0.100
Proto  : TCP
Puerto : 80
Score  : −0.7812
Grado  : ALTA
Hora   : 2026-06-14 22:15:33
```

---

### Caso LIMIT — función `limitar_ip(ip)`

Se llama cuando `τ2 < score ≤ τ1 (entre −0.6873 y −0.4973)` o detector heurístico dispara LIMIT:

```python
def limitar_ip(ip):
    out = _ssh(
        f'sudo ipset add {SET_LIMIT} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
        f'&& echo "LIMITED {ip}"'
    )
    return out
```

**Comando ejecutado en el servidor:**
```bash
sudo ipset add ppi_limited 192.168.0.100 timeout 300 -exist
```

- La IP entra al set `ppi_limited`
- iptables regla 2: paquetes ≤100/s → ACCEPT; paquetes >100/s → DROP
- La conexión se degrada pero no se corta (hashlimit)

---

### Caso LIMIT → BLOCK (escalamiento)

Si una IP ya estaba en LIMIT y el score empeora a BLOCK:

```python
if src_ip in limitados:
    limitados.discard(src_ip)
    _ssh(f'sudo ipset del {SET_LIMIT} {src_ip} 2>/dev/null || true')
resp = bloquear_ip(src_ip)
```

1. Se elimina del set `ppi_limited` (para que el hashlimit deje de aplicar)
2. Se agrega al set `ppi_blocked` (DROP total)
3. No puede haber una IP en ambos sets simultáneamente

---

### Función auxiliar `_ssh(cmd)`

Toda comunicación con el servidor pasa por esta función:

```python
def _ssh(cmd):
    result = subprocess.run(
        ['ssh',
         '-o', 'StrictHostKeyChecking=no',
         '-o', 'ConnectTimeout=5',
         'm4rk@192.168.0.120',
         cmd],
        capture_output=True,
        text=True,
        timeout=8
    )
    return (result.stdout + result.stderr).strip()
```

- `ConnectTimeout=5`: si el servidor no responde en 5s → falla silenciosa
- `timeout=8`: timeout total del subprocess
- Requiere que la llave SSH del sensor esté autorizada en el servidor (`~/.ssh/authorized_keys`)
- Si el SSH falla: el motor lo captura y sigue procesando flows (no se cuelga)

---

## Ciclo de vida de un bloqueo

```
T=0s    Motor detecta anomalía → bloquear_ip("192.168.0.100")
         │
         ▼
T~1s    SSH al servidor ejecuta: ipset add ppi_blocked 192.168.0.100 timeout 300
         │
         ▼
T=1s    192.168.0.100 queda bloqueada:
        Todo paquete src=192.168.0.100 → iptables DROP (sin respuesta)
         │
         ▼
T=1–299s  Paquetes de 192.168.0.100 → DROP silencioso en el servidor
           Motor sigue procesando otros flows
           Si llegan más flows de esa IP → log.debug (ya bloqueado), sin SSH redundante
         │
         ▼
T=300s  ipset expira la entrada automáticamente
        192.168.0.100 puede volver a conectarse
         │
         ▼
T>300s  Si el ataque continúa → el siguiente flow activa otro ciclo de bloqueo
```

---

## Control manual: `enforce.sh`

Permite aplicar BLOCK/LIMIT/UNBLOCK manualmente sin depender del motor automático. Corre **en el servidor** (192.168.0.120):

```bash
# Sintaxis
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh <ip> <BLOCK|LIMIT|UNBLOCK> [timeout_seg]
```

### BLOCK manual

```bash
bash enforce.sh 192.168.0.100 BLOCK 600
# → sudo ipset add ppi_blocked 192.168.0.100 timeout 600 -exist
# Salida: 2026-06-14 22:30:00 | BLOCK | 192.168.0.100 | timeout=600s
```

### LIMIT manual

```bash
bash enforce.sh 192.168.0.100 LIMIT 300
# → sudo ipset add ppi_limited 192.168.0.100 timeout 300 -exist
# Salida: 2026-06-14 22:30:00 | LIMIT | 192.168.0.100 | 100pkt/s | timeout=300s
```

### UNBLOCK (liberar)

```bash
bash enforce.sh 192.168.0.100 UNBLOCK
# → sudo ipset del ppi_blocked 192.168.0.100
# → sudo ipset del ppi_limited 192.168.0.100
# Salida: 2026-06-14 22:30:00 | UNBLOCK | 192.168.0.100
```

`enforce.sh` usa `-exist` y `|| true` para que nunca falle aunque la IP no esté en el set.

---

## Cómo procesa iptables cada paquete entrante

Cuando llega cualquier paquete al servidor, iptables evalúa las reglas en orden:

```
Paquete entrante src=X
        │
        ▼
Regla 1: ¿X está en ppi_blocked?
        SÍ → DROP  (descarte inmediato, sin evaluar más reglas)
        NO → sigue
        │
        ▼
Regla 2: ¿X está en ppi_limited? 
        NO → sigue a reglas siguientes → ACCEPT (política default)
        SÍ → ¿paquetes de X en el último segundo > 100?
              SÍ → DROP
              NO → ACCEPT (pasa dentro del límite)
        │
        ▼
(otras reglas del sistema si existen)
        │
        ▼
ACCEPT (política por defecto INPUT)
```

Este procesamiento ocurre **en el kernel del servidor**, sin intervención del motor. El motor solo agrega/elimina IPs de los sets; el kernel hace el filtrado por cada paquete.

---

## Resumen del flujo completo F5

```
motor_decision.py (en el sensor 192.168.0.110)
  decide BLOCK/LIMIT
         │
         ▼ subprocess.run(ssh)
         │
  SSH tunnel → m4rk@192.168.0.120
         │
         ▼
  sudo ipset add ppi_blocked <ip> timeout 300   (BLOCK)
  sudo ipset add ppi_limited <ip> timeout 300   (LIMIT)
         │
         ▼
  Kernel del servidor (iptables en tiempo real)
  ┌─────────────────────────────────────────────┐
  │ Regla 1: ppi_blocked src → DROP             │
  │ Regla 2: ppi_limited src + >100/s → DROP    │
  └─────────────────────────────────────────────┘
         │
         ▼
  T+300s: ipset expira la entrada automáticamente

  Paralelamente:
  log.warning → motor_decision.log
  telegram_alerta() → Telegram (hilo separado)
  dashboard.py / dashboard_web.py leen el log
```

---

## Qué produce F5 para F6

| Output | Descripción | Usado en |
|---|---|---|
| `motor_decision.log` (líneas BLOCK/LIMIT) | Registro de cada acción ejecutada | F6 `f6_corridas.py` — validación de acciones correctas |
| `ppi_blocked` (ipset activo) | IPs con DROP total | F6 — verificación manual con `ipset list ppi_blocked` |
| `ppi_limited` (ipset activo) | IPs con hashlimit | F6 — verificación manual con `ipset list ppi_limited` |
| Alertas Telegram | Mensajes en tiempo real | F6 — evidencia de notificaciones |

---

## Preguntas frecuentes de defensa

**¿Por qué usar ipset en vez de iptables directamente para cada IP?**

Si se usara `iptables -I INPUT -s <ip> -j DROP` por cada IP, con 1,000 IPs bloqueadas iptables recorrería 1,000 reglas por cada paquete. `ipset` usa una tabla hash — buscar si una IP está en el set toma O(1) sin importar cuántas IPs haya. Además, ipset soporta `timeout` nativo para expiración automática, algo que iptables no tiene.

**¿Qué pasa si el servidor se reinicia?**

Los sets de ipset e iptables se pierden al reiniciar el servidor (no persisten por defecto). Al reiniciar el motor en el sensor, `inicializar_servidor()` los recrea. Si el servidor se reinicia sin que el motor se reinicie, el motor sigue enviando comandos SSH que crearían los sets nuevamente en el próximo BLOCK/LIMIT. Para producción real se requeriría `ipset save/restore` en el boot.

**¿Por qué timeout de 300 segundos?**

Es un balance entre seguridad y usabilidad. Un timeout corto (30s) permite que atacantes reinicien ataques rápidamente. Uno largo (horas) podría bloquear IPs legítimas que compartían IP con un atacante (NAT). 300 segundos (5 minutos) coincide con el tiempo típico que tarda un ataque automatizado en reiniciarse, sin afectar usuarios legítimos que usarían otra IP por DHCP.

**¿El LIMIT corta la conexión del atacante?**

No la corta — la degrada. Con `hashlimit 100/s burst 150`, los primeros 150 paquetes pasan sin restricción; luego solo pasan 100 por segundo. Una conexión SSH normal usa menos de 10 paquetes por segundo, así que un usuario legítimo no nota diferencia. Un SYN flood que envía 10,000 paquetes/segundo verá 99% de sus paquetes descartados.

**¿Por qué el motor no bloquea en el sensor (donde corre)?**

Suricata necesita ver el tráfico para analizarlo. Si el sensor bloqueara a nivel de red, Suricata dejaría de recibir eventos y el motor perdería visibilidad. El bloqueo va en el servidor (donde llega el tráfico de producción), no en el sensor (que solo escucha en modo promiscuo).
