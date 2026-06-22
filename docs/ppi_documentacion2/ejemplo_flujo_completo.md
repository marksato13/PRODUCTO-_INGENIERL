# Guion de Demo — Flujo Completo del Sistema
**PPI UPeU 2026 · Rubén Mark Salazar Tocas**  
**Guion en primera persona · Con indicadores de capturas**

---

> **Cómo usar este guion:**  
> El texto en *cursiva* es lo que digo en voz alta al jurado.  
> Los bloques de código son lo que ejecuto en pantalla en ese momento.  
> `📸 CAPTURA` = tomar pantalla aquí.  
> Tiempo total estimado: **15–20 minutos**.

---

## Qué voy a demostrar (decirlo al inicio)

*"La demo cubre los cuatro componentes del sistema en este orden de importancia:"*

| Prioridad | Componente | Qué se ve en vivo |
|---|---|---|
| 🔴 1 | **Motor de decisión (F2+F3)** | Isolation Forest detecta y bloquea en tiempo real |
| 🔴 2 | **Predictor XGBoost (F4)** | Alerta predictiva ANTES del próximo bloqueo |
| 🟡 3 | **BF-SSH heurístico (F3)** | Segundo tipo de ataque, segunda capa de detección |
| 🟡 4 | **Autoaprendizaje (F5)** | El modelo mejoró con datos nuevos — muestro evidencia |
| 🟢 5 | **Validación completa (F6)** | 16/16 criterios PASS en suite automatizada |
| 🟢 6 | **Tráfico normal (whitelist)** | FPR = 0%, Desktop nunca se bloquea |

*"Si el tiempo lo permite hacemos todo. Si no, los primeros dos son los más importantes."*

---

## Preparación — Verifico el sistema (1 min)

*"Antes de empezar verifico que los cuatro servicios estén activos: Suricata capturando en el sensor, el motor de decisión, el predictor XGBoost, y el dashboard web."*

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

📸 **CAPTURA:** Los cuatro `active` en pantalla

*"Abro también tres terminales de monitoreo para que puedan ver todo en tiempo real mientras ejecuto los ataques."*

```bash
# Terminal 1 — motor de decisión (lo más importante)
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"

# Terminal 2 — predictor XGBoost
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```

Abrir en navegador: `http://192.168.0.110:8080`

📸 **CAPTURA:** Las dos terminales + navegador abiertos (layout 2×2 o side by side)

---

---

## 🔴 PRIORIDAD 1 — Motor de Decisión + Isolation Forest (F2 + F3)

> *Este es el núcleo del sistema. Si solo hay tiempo para una cosa, es esta.*

### Lanzo el ataque SYN Flood desde Kali

*"Voy a simular el ataque más agresivo: un SYN Flood contra el servidor nginx. El atacante en 192.168.0.100 envía 200 paquetes SYN por segundo al puerto 80, pero nunca completa el handshake TCP. El objetivo es saturar la tabla de conexiones del servidor."*

```bash
ssh m4rk@192.168.0.100 "sudo hping3 -S -p 80 -i u5000 192.168.0.120"
```

📸 **CAPTURA:** hping3 corriendo con el contador de paquetes subiendo

---

### Por qué tarda 62 segundos — F1 Captura (Suricata)

*"Aquí hay algo clave que explica el lead time. Suricata trabaja con flujos completos, no paquetes individuales. En un SYN Flood el handshake nunca termina, así que Suricata tiene que esperar el timeout del flujo — 60 segundos — antes de registrar el evento en eve.json. A eso se suman 2 segundos del pipeline. Por eso la detección tarda aproximadamente 62 segundos."*

*"El flujo que Suricata registra muestra claramente la anomalía: 8,420 paquetes enviados al servidor, cero paquetes de vuelta."*

```json
{
  "src_ip": "192.168.0.100",  "dest_port": 80,
  "flow": {
    "pkts_toserver": 8420,  "pkts_toclient": 0,
    "bytes_toserver": 421000,  "bytes_toclient": 0,
    "age": 61
  }
}
```

---

### F2 — Isolation Forest calcula el score (T+62s)

*"El motor de decisión lee ese evento y extrae 14 features. Las más reveladoras son el pkt_ratio y el byte_ratio: la IP atacante envió 8,420 paquetes y recibió cero. Eso da un ratio de 8,420 a 1. En tráfico legítimo ese ratio está cerca de 1."*

*"El Isolation Forest devuelve un score de −0.6066. Mis dos umbrales son: mayor que −0.4459 es PERMIT, entre los dos umbrales es LIMIT, menor que −0.6027 es BLOCK. El score cae por debajo del umbral τ2, así que la decisión es BLOCK."*

```
score = -0.6066   τ1 = -0.4459   τ2 = -0.6027
score ≤ τ2  →  BLOCK 🚫
```

*"Aquí lo pueden ver en Terminal 1 en tiempo real:"*

```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6066 grado=ALTA tipo=ANOMALIA_GENERICA | BLOCK
```

📸 **CAPTURA:** Terminal 1 con la línea BLOCK del SYN Flood

---

### F3 — El motor bloquea la IP en el servidor (T+62s)

*"Lo que ocurre después es importante para entender la arquitectura. El sensor detecta el ataque, pero el bloqueo se ejecuta en el servidor que está siendo atacado. El motor hace SSH al servidor 192.168.0.120 y agrega la IP atacante al ipset ppi_blocked."*

*"Voy a verificar que efectivamente quedó bloqueada:"*

```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```

*"Pueden ver 192.168.0.100 en el set con un timeout contando hacia atrás. La regla iptables en el servidor hace DROP a todo paquete que venga de una IP en ese set."*

📸 **CAPTURA:** `ipset list ppi_blocked` con la IP del atacante y el timeout

*"El sistema usa bloqueo progresivo: el primer bloqueo dura 5 minutos, el segundo 30 minutos, y si la IP reincide por tercera vez el timeout es cero — permanente."*

```
Bloqueo #1  →  timeout = 300s    (5 min)
Bloqueo #2  →  timeout = 1800s   (30 min)
Bloqueo #3+ →  timeout = 0       (PERMANENTE)
```

*"Y simultáneamente el motor envía alerta a Telegram directamente a la API de Telegram:"*

```
🚨 PPI ALERTA — ANOMALIA_GENERICA
IP: 192.168.0.100  Puerto: 80  Score: -0.6066
Acción: BLOCK  Bloqueo #1 — timeout 300s
```

📸 **CAPTURA:** Notificación de Telegram en el celular

*"Detengo el ataque:"*
```bash
ssh m4rk@192.168.0.100 "sudo pkill hping3"
```

---

---

## 🔴 PRIORIDAD 2 — Predictor XGBoost v2 (F4)

> *Esta es la capa predictiva. Se ve en Terminal 2 inmediatamente después del BLOCK anterior.*

*"Mientras el motor bloqueó el SYN Flood, el predictor XGBoost estaba corriendo en paralelo en un ciclo de 10 segundos. El predictor es una segunda capa de inteligencia: no detecta ataques, predice que una IP va a generar más bloqueos en el futuro basándose en su comportamiento acumulado."*

*"Las features que usa el XGBoost son distintas al Isolation Forest — 9 features comportamentales. La más importante es block_count_60s: cuántos bloqueos generó esa IP en los últimos 60 segundos. No usa el score del IF, porque eso causaría data leakage — el modelo vería su propio resultado como entrada."*

*"Después del primer BLOCK del SYN Flood, el predictor calculó:"*

```python
block_count_60s = 1    # un bloqueo en la ventana de 60s
limit_count_15s = 0    # sin LIMITs previos (fue directo a BLOCK)
dest_port       = 80
proto_tcp       = 1

P = modelo.predict_proba(features)[0][1]
# P ≈ 0.77  →  ALERTA-PREDICTIVA
```

*"Pueden ver en Terminal 2 la alerta predictiva:"*

```
WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```

*"P=77% significa que el predictor estima 77% de probabilidad de que esta IP genere otro evento de bloqueo. Si la IP sigue atacando y acumula más bloqueos, ese porcentaje sube. En mis corridas con Kali llegué a ver P=89.27% después de varios ciclos."*

📸 **CAPTURA:** Terminal 2 con la línea ALERTA-PREDICTIVA y el valor de P

*"La diferencia conceptual entre los dos modelos es esta:"*

| | Isolation Forest | XGBoost Predictor |
|---|---|---|
| Pregunta | ¿Este flujo es anómalo AHORA? | ¿Esta IP va a atacar de NUEVO? |
| Entrada | 14 features del flujo actual | 9 features de comportamiento histórico |
| Salida | score → PERMIT/LIMIT/BLOCK | P(%) → ALERTA si P > 70% |
| Ciclo | Por cada flujo (~2s) | Cada 10 segundos |

---

---

## 🟡 PRIORIDAD 3 — Brute Force SSH con heurístico (F3 segunda capa)

> *Muestra que el sistema tiene múltiples capas de detección, no solo el IF.*

*"El tercer escenario es fuerza bruta sobre SSH. Es más interesante técnicamente porque el Isolation Forest por sí solo no es suficiente — un intento de login SSH fallido se parece mucho al SSH legítimo en las features. Por eso tengo un detector heurístico adicional que cuenta intentos."*

```bash
# Primero desbloqueo a Kali del escenario anterior:
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK

# Lanzo hydra:
ssh m4rk@192.168.0.100 "hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4"
```

📸 **CAPTURA:** hydra corriendo con los intentos de login

*"Lo que va a ocurrir tiene dos etapas. Primero el IF detecta los flujos como ligeramente anómalos — score −0.4832, que está entre τ1 y τ2 — entonces aplica LIMIT: limita la velocidad de esa IP a 100 paquetes por segundo. No la bloquea todavía."*

```
T+30s: score = -0.4832  →  τ2 < score ≤ τ1  →  LIMIT
```

```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.4832 tipo=BAJA_ANOMALIA | LIMIT
```

*"Pero al mismo tiempo el heurístico BF-SSH está contando: a los 60 segundos lleva 15 intentos de autenticación SSH desde esa IP, que supera el umbral de bloqueo. Ahí el motor aplica BLOCK por tipo BRUTE_FORCE_SSH."*

```
BF_UMBRAL_LIMIT = 5  intentos/60s → LIMIT heurístico
BF_UMBRAL_BLOCK = 15 intentos/60s → BLOCK
```

```
T+60s: BRUTE_FORCE_SSH  →  BLOCK
```

```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  score=-0.6228 tipo=BRUTE_FORCE_SSH | BLOCK
```

📸 **CAPTURA:** Terminal 1 mostrando la secuencia LIMIT → BLOCK del hydra

*"El lead time aquí es 60 segundos exactos, que es la ventana del heurístico — diferente a los 62s del SYN Flood que dependía del timeout de Suricata."*

---

---

## 🟡 PRIORIDAD 4 — Autoaprendizaje (F5)

> *No ejecuto el reentrenamiento en vivo — tarda varios minutos. Muestro la evidencia de que ocurrió y mejoró.*

*"El sistema aprende de los nuevos datos automáticamente. Tengo dos cron jobs configurados en el sensor: el Isolation Forest se reentrena todos los domingos a las 2am con los nuevos flujos capturados desde eve.json, y el XGBoost v2 se reentrena diariamente a las 3am con los nuevos eventos LIMIT y BLOCK del motor."*

```bash
ssh m4rk@192.168.0.110 "crontab -l"
# 0 2 * * 0  → f5_reentrenar_if.py        (domingos 02:00)
# 0 3 * * *  → f5_reentrenar_xgboost.py   (diario 03:00)
```

*"Puedo mostrar el historial de reentrenamientos. El sistema guarda el AUC antes y después de cada ciclo para verificar que el modelo no empeoró:"*

```bash
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
```

📸 **CAPTURA:** Salida de metricas_f5_xgboost.txt con AUC anterior vs nuevo

*"El mecanismo de seguridad es importante: si el modelo nuevo tiene AUC menor que el anterior, el script NO lo reemplaza. El modelo en producción solo se actualiza cuando el reentrenamiento mejora o mantiene la calidad. A esto lo llamo anti-regresión."*

*"El motor detecta el modelo nuevo automáticamente — el predictor.py verifica la fecha de modificación del archivo .pkl en cada ciclo de 10 segundos y recarga sin necesidad de reiniciar el servicio."*

---

---

## 🟢 PRIORIDAD 5 — Validación formal F6 — 16/16 PASS

*"Toda la validación está automatizada en una suite de 16 criterios de aceptación que cubren desde el AUC mínimo del modelo hasta la latencia del pipeline. Los corro todos con un solo comando:"*

```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```

📸 **CAPTURA:** run_all.sh con los 16 PASS en pantalla

*"Destaco tres resultados clave:"*

*"CA-02: AUC del Isolation Forest = 0.8998. El mínimo requerido era 0.85. Lo supera."*

*"CA-09: Latencia P95 del pipeline completo = 34.768 milisegundos. El requisito era menos de 500ms. El sistema es 14 veces más rápido que el límite."*

*"CA-16: Generé 119 flujos de tráfico normal en una sesión completamente nueva, diferente a la de entrenamiento, y la tasa de falsos positivos fue exactamente 0.0%. El sistema no bloqueó ningún flujo legítimo."*

---

---

## 🟢 PRIORIDAD 6 — Tráfico normal no se bloquea (whitelist + FPR=0%)

*"Para cerrar demuestro que el sistema no afecta el tráfico legítimo. Genero tráfico HTTP normal desde este Desktop:"*

```bash
for i in $(seq 1 20); do curl -s http://192.168.0.120/ -o /dev/null; sleep 1; done
```

*"El motor verifica primero si la IP está en la whitelist. Este Desktop es 192.168.0.20 y está en la whitelist junto con el sensor y el servidor. La decisión es PERMIT instantáneo, sin calcular score."*

*"Lo verifico directamente en el servidor:"*

```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
# Salida: 192.168.0.20 is NOT in set ppi_blocked.
```

📸 **CAPTURA:** `ipset test` confirmando que Desktop no está bloqueado

---

---

## Cierre — Tabla de métricas finales (decirla de memoria o mostrar)

| Componente | Métrica | Valor |
|---|---|---|
| Isolation Forest | AUC-ROC | **0.8998** |
| IF | Precision / Recall | **99.54% / 99.40%** |
| IF | Umbral τ1 (PERMIT/LIMIT) | **−0.4459** |
| IF | Umbral τ2 (LIMIT/BLOCK) | **−0.6027** |
| Motor | Latencia P95 | **34.768ms** (req. <500ms ✅) |
| XGBoost v2 | AUC-ROC | **0.9992** |
| XGBoost v2 | Errores totales (de 12,488) | **14** |
| Sistema | Disponibilidad | **100%** |
| Sistema | Interrupción tráfico legítimo | **0%** |
| Sistema | Lead time SYN Flood | **~62s** |
| Sistema | Lead time BF SSH | **60s** |
| CA-16 | FPR en datos nuevos (119 flows) | **0.0%** |
| F6 | Criterios de aceptación | **16/16 PASS** |

📸 **CAPTURA:** Esta tabla en diapositiva de cierre

---

## Resumen de capturas (en orden de la demo)

| # | Qué capturar | Cuándo |
|---|---|---|
| 1 | 4 servicios `active` | Preparación |
| 2 | hping3 corriendo + contador de paquetes | SYN Flood activo |
| 3 | motor_decision.log con línea BLOCK del SYN Flood | ~T+62s |
| 4 | `ipset list ppi_blocked` con IP + timeout | Después del BLOCK |
| 5 | Telegram en el celular con la alerta | Al recibir notificación |
| 6 | predictor.log con ALERTA-PREDICTIVA + P=XX% | Terminal 2 después del BLOCK |
| 7 | motor_decision.log con LIMIT→BLOCK del hydra | Durante BF SSH |
| 8 | metricas_f5_xgboost.txt con AUC antes/después | F5 autoaprendizaje |
| 9 | run_all.sh con 16/16 PASS | F6 validación |
| 10 | `ipset test` Desktop NOT in set | Cierre |
