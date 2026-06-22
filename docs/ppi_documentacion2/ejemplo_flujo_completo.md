# Guion de Demo — Flujo Completo del Sistema
**PPI UPeU 2026 · Rubén Mark Salazar Tocas**  
**Cómo explicar la demo en vivo · Con indicación de capturas**

---

> **Cómo usar este guion:**  
> El texto en cursiva es lo que digo en voz alta.  
> Los bloques de código son lo que ejecuto en pantalla.  
> `📸 CAPTURA` indica que debo mostrar esa pantalla al jurado.

---

## Apertura (30 segundos)

*"Voy a demostrar el sistema funcionando en tiempo real. Tengo tres máquinas activas: el sensor Suricata en 192.168.0.110 que captura todo el tráfico, el servidor nginx en 192.168.0.120 que es el objetivo, y Kali Linux en 192.168.0.100 desde donde voy a lanzar los ataques."*

---

## Paso 0 — Verifico que el sistema está corriendo

*"Lo primero que hago es verificar que todos los servicios estén activos antes de la demo."*

```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
```

**Salida esperada:**
```
active
active
active
active
```

*"Como pueden ver, Suricata está capturando, el motor de decisión está corriendo, el predictor XGBoost está activo y el dashboard web está disponible. Los cuatro servicios responden `active`."*

📸 **CAPTURA:** Pantalla completa de la terminal con los cuatro `active`

---

## Paso 1 — Abro el monitoreo en tiempo real

*"Voy a abrir tres terminales en paralelo para que puedan ver lo que ocurre en cada capa del sistema mientras lanzo el ataque."*

**Terminal 1 — log del motor de decisión:**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
```

*"Esta terminal muestra cada flujo que el motor analiza: el score del Isolation Forest, si es PERMIT, LIMIT o BLOCK, y el tipo de anomalía detectada."*

**Terminal 2 — log del predictor XGBoost:**
```bash
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```

*"Esta es la capa predictiva: el XGBoost v2 evalúa el comportamiento histórico de cada IP y alerta si predice que el siguiente evento será un bloqueo, antes de que ocurra."*

**Terminal 3 — dashboard en el navegador:**  
Abrir `http://192.168.0.110:8080`

*"Y aquí tengo el dashboard web que muestra las estadísticas del sistema en tiempo real: flujos por segundo, anomalías, bloqueos activos y latencia del pipeline."*

📸 **CAPTURA:** Las tres terminales y el navegador abiertos al mismo tiempo (layout 2×2)

---

## Escenario 1 — SYN Flood (ataque volumétrico)

### Lanzo el ataque desde Kali

*"Voy a simular un ataque SYN Flood: el atacante envía miles de paquetes SYN hacia el servidor nginx en el puerto 80, pero nunca completa el handshake TCP. Esto satura la tabla de conexiones del servidor."*

```bash
ssh m4rk@192.168.0.100 "sudo hping3 -S -p 80 -i u5000 192.168.0.120"
```

*"Con `-i u5000` estoy enviando un paquete cada 5 milisegundos, lo que son 200 paquetes por segundo. Para la demo uso esta velocidad controlada, pero el sistema también detecta floods a máxima velocidad con `--flood`."*

📸 **CAPTURA:** Terminal con hping3 corriendo mostrando el contador de paquetes enviados

---

### F1 — Suricata captura el flujo (T+60s)

*"Aquí hay algo importante que explicar. Suricata trabaja con flujos TCP completos, no con paquetes individuales. En un SYN Flood el handshake nunca completa, así que Suricata tiene que esperar el timeout del flujo, que son 60 segundos, antes de registrarlo en el eve.json. Por eso el lead time de detección es aproximadamente 62 segundos."*

*"El flujo que Suricata registra se ve así: miles de paquetes hacia el servidor, cero paquetes de respuesta, porque el servidor no puede responder a conexiones que no completan el handshake."*

```json
{
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "dest_port": 80,
  "flow": {
    "pkts_toserver": 8420,
    "pkts_toclient": 0,
    "bytes_toserver": 421000,
    "bytes_toclient": 0,
    "age": 61
  }
}
```

---

### F2 — Isolation Forest calcula el score (T+62s)

*"El motor de decisión lee el evento del eve.json y extrae las 14 features que usa el Isolation Forest. Las más importantes aquí son el pkt_ratio y el byte_ratio: la IP atacante envió 8,420 paquetes y recibió cero, lo que da un ratio de 8,420 a 1. Eso es completamente anómalo para cualquier tráfico legítimo."*

*"El Isolation Forest devuelve un score de −0.6066. Mis umbrales son: si el score es mayor que −0.4459, es tráfico normal y lo permito; si está entre −0.6027 y −0.4459, lo limito; si es menor que −0.6027, lo bloqueo. En este caso el score está por debajo del umbral τ2, así que el motor decide BLOCK."*

```
score = -0.6066
τ2    = -0.6027
score ≤ τ2  →  BLOCK
```

📸 **CAPTURA:** Terminal 1 mostrando la línea de BLOCK en motor_decision.log

*"Aquí lo pueden ver en tiempo real en el log del motor:"*

```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6066 grado=ALTA tipo=ANOMALIA_GENERICA | BLOCK
```

---

### F3 — El motor bloquea la IP en el servidor (T+62s)

*"Lo interesante de la arquitectura es dónde se ejecuta el bloqueo. El sensor Suricata detecta el ataque, pero el bloqueo se aplica en el servidor, que es el que está siendo atacado. El motor hace SSH al servidor y ejecuta el comando ipset para agregar la IP a la lista de bloqueados."*

```bash
# Lo que el motor ejecuta internamente:
ssh m4rk@192.168.0.120 "sudo ipset add ppi_blocked 192.168.0.100 timeout 300 -exist"
```

*"Voy a verificar que la IP del atacante efectivamente está bloqueada en el servidor:"*

```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```

*"Pueden ver que 192.168.0.100 aparece en el set con un timeout de 295 segundos contando hacia atrás."*

📸 **CAPTURA:** Salida de `ipset list ppi_blocked` con la IP del atacante y el timeout

*"El sistema usa bloqueo progresivo: el primer bloqueo dura 5 minutos, el segundo 30 minutos, y si la IP sigue atacando en el tercer bloqueo el timeout se pone en cero, que significa permanente. Tengo evidencia real de esto ocurriendo en mis corridas de validación:"*

```
Primer  BLOCK → timeout = 300s   (5 min)
Segundo BLOCK → timeout = 1800s  (30 min)
Tercer  BLOCK → timeout = 0      (PERMANENTE)
```

📸 **CAPTURA:** `ipset list ppi_blocked` mostrando una IP sin timeout (permanente)

---

### F4 — XGBoost predice el siguiente bloqueo (T+62s + ciclo 10s)

*"Mientras el motor bloquea, el predictor XGBoost está corriendo en paralelo en un ciclo de 10 segundos. Lee el motor_decision.log y evalúa el comportamiento histórico de cada IP. Usa 9 features distintas del Isolation Forest, sin incluir el score de IF para evitar data leakage."*

*"En este momento el predictor calcula: puerto 80, protocolo TCP, un bloqueo en los últimos 60 segundos, ningún LIMIT previo porque el SYN Flood fue directo a BLOCK. El modelo devuelve una probabilidad del 77%. Como supera mi umbral del 70%, emite una alerta predictiva."*

```
2026-06-22 HH:MM:SS | WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```

*"Esto significa que el predictor está diciendo: esta IP tiene alta probabilidad de generar un nuevo evento de bloqueo en los próximos ciclos. Es la capa proactiva del sistema."*

📸 **CAPTURA:** Terminal 2 con la línea de ALERTA-PREDICTIVA del predictor.log

---

### Telegram — notificación al operador

*"Al mismo tiempo, el motor envía una notificación directa a Telegram via la API de Telegram. El operador de seguridad recibe en su celular:"*

```
🚨 PPI ALERTA — ANOMALIA_GENERICA

Accion : BLOCK (DROP)
IP     : 192.168.0.100
Puerto : 80
Proto  : TCP
Score  : -0.6066
Grado  : ALTA
Hora   : 05:44:13
Bloqueo: #1 — timeout 300s
```

📸 **CAPTURA:** Captura de pantalla del celular mostrando la notificación de Telegram

*"Detengo el ataque:"*

```bash
ssh m4rk@192.168.0.100 "sudo pkill hping3"
```

---

## Escenario 2 — Brute Force SSH (ataque comportamental)

### Lanzo hydra desde Kali

*"El segundo escenario es un ataque de fuerza bruta sobre SSH. Es más interesante porque el Isolation Forest solo ve flujos individuales y un intento de login SSH puede parecerse al SSH legítimo. Aquí entra el detector heurístico de comportamiento."*

```bash
# Primero desbloqueo a Kali si quedó bloqueada del escenario anterior:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK

# Lanzo el ataque:
ssh m4rk@192.168.0.100 "hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4"
```

*"Hydra prueba contraseñas del diccionario fasttrack.txt con 4 hilos paralelos contra el SSH del servidor."*

📸 **CAPTURA:** Terminal con hydra corriendo mostrando los intentos de login

---

### T+15s — El IF da score intermedio

*"A los 15 segundos el Isolation Forest ya detecta los flujos SSH como ligeramente anómalos, con un score de −0.4832. Ese score está entre mis dos umbrales, así que el motor aplica LIMIT: hashlimit de 100 paquetes por segundo en lugar de bloqueo total."*

```
score = -0.4832
τ2 < score ≤ τ1  →  LIMIT
```

```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT
```

---

### T+60s — El heurístico BF-SSH bloquea

*"Mientras tanto, el motor está contando los intentos de autenticación SSH de esa IP en una ventana deslizante de 60 segundos. A los 30 segundos ya van 8 intentos, que supera el umbral de 5 para LIMIT heurístico. A los 60 segundos llegan a 15 intentos, que supera el umbral de bloqueo. El motor aplica BLOCK por tipo BRUTE_FORCE_SSH."*

```
BF_UMBRAL_LIMIT = 5  intentos/60s → LIMIT
BF_UMBRAL_BLOCK = 15 intentos/60s → BLOCK
```

```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH | BLOCK
```

📸 **CAPTURA:** Terminal 1 mostrando la secuencia LIMIT → BLOCK de hydra en motor_decision.log

*"La diferencia con el SYN Flood es que acá el lead time es exactamente 60 segundos: el tiempo de la ventana del heurístico BF-SSH. Para el SYN Flood eran 62 segundos por el timeout de Suricata."*

---

## Escenario 3 — Tráfico normal (no se bloquea)

*"Ahora muestro que el sistema no bloquea el tráfico legítimo. Desde mi Desktop genero tráfico HTTP normal hacia el servidor."*

```bash
# Desde Desktop 192.168.0.20
for i in $(seq 1 30); do curl -s http://192.168.0.120/ -o /dev/null; sleep 2; done
```

*"El motor verifica antes de calcular el score si la IP está en la whitelist. 192.168.0.20, que es este Desktop, está en la whitelist junto con el sensor y el servidor mismo. La decisión es inmediata: PERMIT, sin ni siquiera llamar al Isolation Forest."*

*"Puedo demostrar que el Desktop no está bloqueado:"*

```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
# Salida: 192.168.0.20 is NOT in set ppi_blocked.
```

📸 **CAPTURA:** Salida de `ipset test` confirmando que la IP del Desktop no está bloqueada

---

## Control manual con enforce.sh

*"El sistema también permite control manual del operador. Desde el sensor puedo bloquear, limitar o desbloquear cualquier IP directamente:"*

```bash
# BLOQUEAR una IP manualmente por 2 minutos:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 120

# LIMITAR una IP por 5 minutos:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 LIMIT 300

# DESBLOQUEAR:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

*"Internamente enforce.sh hace SSH al servidor y ejecuta el comando ipset correspondiente. El operador no necesita saber la sintaxis de ipset."*

📸 **CAPTURA:** Ejecución de enforce.sh con BLOCK y la verificación posterior en ipset

---

## F5 — Reentrenamiento automático (explicar sin ejecutar en vivo)

*"El sistema aprende de nuevos datos automáticamente. Tengo dos cron jobs configurados: el Isolation Forest se reentrena todos los domingos a las 2am con los nuevos flujos capturados, y el XGBoost v2 se reentrena diariamente a las 3am con los nuevos eventos de LIMIT y BLOCK del motor."*

*"Puedo mostrar el historial de reentrenamientos y verificar que el modelo mejora o al menos mantiene su AUC con los nuevos datos:"*

```bash
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
```

📸 **CAPTURA:** Salida de metricas_f5_xgboost.txt mostrando AUC antes y después del reentrenamiento

---

## F6 — Validación formal: 16/16 criterios PASS

*"Toda la validación del sistema está automatizada. Tengo una suite de scripts que verifican los 16 criterios de aceptación del PPI, desde que el modelo tiene AUC mayor a 0.85 hasta que la latencia P95 está por debajo de 500ms, pasando por que las IPs whitelisted nunca se bloquean."*

```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```

*"El resultado es 16 de 16 criterios PASS. Voy a destacar tres en particular:"*

📸 **CAPTURA:** Salida completa de run_all.sh con los 16 PASS

*"CA-02: el AUC del Isolation Forest es 0.8998, que supera el mínimo requerido de 0.85."*  
*"CA-09: la latencia P95 del pipeline completo es 34.768 milisegundos, muy por debajo del límite de 500ms."*  
*"CA-16: evalué 119 flujos nuevos de tráfico normal generado en una sesión diferente a la de entrenamiento, y la tasa de falsos positivos fue 0.0%. El sistema no bloqueó ningún flujo legítimo."*

---

## Resumen de métricas finales

*"Para cerrar, estos son los valores finales del sistema validados en las 40 corridas de la fase 6:"*

| Componente | Métrica | Valor |
|---|---|---|
| Isolation Forest | AUC-ROC | **0.8998** |
| IF | Precision / Recall | **99.54% / 99.40%** |
| IF | Umbral PERMIT/LIMIT (τ1) | **−0.4459** |
| IF | Umbral LIMIT/BLOCK (τ2) | **−0.6027** |
| Motor | Latencia P95 | **34.768ms** (req. <500ms ✅) |
| XGBoost v2 | AUC-ROC | **0.9992** |
| XGBoost v2 | Errores en test (de 12,488) | **14** (7 FP + 7 FN) |
| Sistema | Disponibilidad (40 corridas) | **100%** |
| Sistema | Interrupción de tráfico legítimo | **0%** |
| Sistema | Lead time SYN Flood | **~62s** |
| Sistema | Lead time BF SSH | **60s** |
| CA-16 | FPR en 119 flujos nuevos | **0.0%** |
| Validación | Criterios de aceptación | **16/16 PASS** |

📸 **CAPTURA:** Esta tabla en pantalla al cierre de la presentación

---

## Capturas necesarias para la presentación (en orden de prioridad)

| # | Qué capturar | Cuándo |
|---|---|---|
| 1 | Los 4 servicios `active` (Paso 0) | Al inicio de la demo |
| 2 | hping3 corriendo con contador de paquetes | Durante el SYN Flood |
| 3 | motor_decision.log con línea BLOCK del SYN Flood | ~T+62s del SYN Flood |
| 4 | `ipset list ppi_blocked` con IP y timeout | Después del BLOCK |
| 5 | predictor.log con ALERTA-PREDICTIVA y P=XX% | Segundos después del BLOCK |
| 6 | Telegram en el celular con la alerta | Justo al recibir la notificación |
| 7 | motor_decision.log con secuencia LIMIT→BLOCK de hydra | Durante el BF SSH |
| 8 | `ipset test ppi_blocked 192.168.0.20` NOT in set | Escenario normal |
| 9 | run_all.sh con 16/16 PASS | Al final |
| 10 | ipset con IP sin timeout (PERMANENTE) | Si ya hay un bloqueo #3 |
