# Demo del Sistema — Qué hace, qué muestro, qué digo
**PPI UPeU 2026 · Rubén Mark Salazar Tocas**  
**Basado en comportamiento real verificado 2026-06-22/23**

---

## Lo que mi sistema hace (en una oración)

Monitorea todo el tráfico de red en tiempo real, detecta comportamiento anómalo con Isolation Forest, y bloquea al atacante directamente en el servidor — sin intervención humana — en segundos.

---

## Qué puede demostrar el sistema en vivo

| Capacidad | Cómo se ve | Dónde se ve |
|---|---|---|
| Detección de flujos anómalos | Score IF < τ → LIMIT o BLOCK en el log | `motor_decision.log` |
| Escalada progresiva LIMIT → BLOCK | Primero limita velocidad, luego bloquea total | `motor_decision.log` |
| Bloqueo real en el servidor | IP en `ppi_blocked` con timeout | `ipset list` en 192.168.0.120 |
| Detección HTTP Abuse | >100 requests/30s → BLOCK | Log: `HTTP-ABUSE` |
| Detección Brute Force SSH | >15 intentos/60s → BLOCK | Log: `BRUTE_FORCE_SSH` |
| Predicción de reincidencia | P=XX% → ALERTA-PREDICTIVA | `predictor.log` |
| Notificación al operador | Mensaje en Telegram | Celular |
| Tráfico legítimo intacto | Desktop nunca aparece en log | `ipset test` → NOT in set |
| Autoaprendizaje | Modelos se reentrenan solos | `crontab -l` + métricas F5 |
| Validación formal | 16 criterios automatizados PASS | `run_all.sh` |

---

## PREPARACIÓN (hacer antes de entrar al auditorio)

```bash
# 1. Verificar que los 4 servicios están activos
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
# Esperado: active × 4

# 2. Limpiar estado para demo limpia
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S ipset flush ppi_blocked && sudo -S ipset flush ppi_limited"
ssh m4rk@192.168.0.110 "echo '{}' > /home/m4rk/ppi-surikata-producto/results/block_counts.json"
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service ppi-predictor.service"
sleep 5

# 3. Abrir las 2 terminales de monitoreo (dejarlas visibles todo el tiempo)
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/predictor.log"
```

---

---

## ESCENARIO 1 — Ataque HTTP / SYN Flood desde Kali (hping3)

### Qué demuestra
Que el sistema detecta tráfico volumétrico anómalo, escala de LIMIT a BLOCK, y ejecuta el bloqueo real en el servidor — todo automáticamente.

### Comando (ejecutar y dejar corriendo)
```bash
ssh m4rk@192.168.0.100 "sudo hping3 -S -p 80 -i u5000 192.168.0.120"
```

### Lo que aparece en `motor_decision.log` (verificado en vivo 2026-06-23)

**Primer flujo detectado — LIMIT (score entre τ1 y τ2):**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
  score=-0.4654 grado=BAJA tipo=BAJA_ANOMALIA
  byte_ratio=60.00 pkt_rate=1000.0 | LIMIT
```
*"El primer flujo tiene un score de −0.4654. Mis umbrales son τ1=−0.4459 y τ2=−0.6027. El score cae entre los dos, así que el sistema lo clasifica como SOSPECHOSO y aplica LIMIT: limita a esa IP a 100 paquetes por segundo."*

**Cuando acumula 100 requests en 30 segundos — BLOCK:**
```
WARNING | HTTP-ABUSE | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP
  requests=100/30s | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los pocos segundos, el detector heurístico HTTP-ABUSE cuenta que esa IP hizo más de 100 requests en 30 segundos. El sistema escala a BLOCK: agrega la IP al ipset del servidor con timeout de 5 minutos."*

### Verificar el bloqueo en el servidor (ejecutar en ese momento)
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```
**Salida real:**
```
Members:
192.168.0.100 timeout 293
```
*"Aquí está la confirmación: 192.168.0.100 bloqueada en el servidor con 293 segundos restantes. Todo el tráfico de esa IP cae en DROP por la regla iptables."*

### Bloqueo progresivo (si se repite el ataque)
```
Bloqueo #1 → timeout=300s    (5 minutos)
Bloqueo #2 → timeout=1800s   (30 minutos)
Bloqueo #3 → timeout=0       (PERMANENTE)
```
*"Si la misma IP reincide, el sistema la bloquea progresivamente: 5 minutos, luego 30 minutos, y a la tercera vez el bloqueo es permanente."*

### Parar el ataque
```bash
ssh m4rk@192.168.0.100 "sudo pkill hping3"
```

---

---

## ESCENARIO 2 — Brute Force SSH desde Kali (hydra)

### Qué demuestra
Que el sistema tiene una segunda capa de detección heurística — no solo el Isolation Forest. Un ataque de fuerza bruta SSH se parece al SSH legítimo en las features de flujo, pero el heurístico lo detecta contando intentos.

### Preparar (desbloquear Kali del escenario anterior)
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

### Comando
```bash
ssh m4rk@192.168.0.100 "hydra -l root -P /usr/share/wordlists/fasttrack.txt ssh://192.168.0.120 -t 4"
```

### Lo que aparece en `motor_decision.log`

**Primeros flujos — LIMIT (IF detecta, score intermedio):**
```
WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
  score=-0.4832 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT
```
*"Los primeros intentos de login generan un score de −0.4832, entre los dos umbrales: LIMIT."*

**A los 60 segundos — BLOCK por heurístico BF-SSH:**
```
WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22 proto=TCP
  score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH | BLOCK → BLOCKED 192.168.0.100 (bloqueo#1 timeout=300s)
```
*"A los 60 segundos el contador BF-SSH llega a 15 intentos desde esa IP. Supera el umbral y el sistema bloquea. El tipo es BRUTE_FORCE_SSH, que fue identificado por el heurístico, no solo por el score."*

### Por qué existe el heurístico BF-SSH
*"Un intento SSH fallido individual se parece al SSH legítimo: mismas features, duraciones similares. El Isolation Forest solo ve un flujo a la vez. El heurístico cuenta el comportamiento acumulado en una ventana de 60 segundos, que es lo que delata al atacante."*

---

---

## ESCENARIO 3 — Predictor XGBoost ve el comportamiento (F4)

### Qué demuestra
Que hay una segunda inteligencia corriendo en paralelo: el XGBoost evalúa el historial de cada IP y predice si va a volver a atacar — antes de que lo haga.

### Qué ver en `predictor.log` (aparece automáticamente después de los BLOCKs)
```
WARNING | ALERTA-PREDICTIVA | src=192.168.0.100 P=77.XX%
  score=-0.606X limits_15s=0 blocks_60s=1
```

*"P=77% significa que el predictor estima un 77% de probabilidad de que esa IP genere otro evento de bloqueo en los próximos ciclos. Las features más importantes son cuántos bloqueos acumuló en los últimos 60 segundos — eso no puede fingirlo tráfico legítimo."*

### Diferencia clave entre IF y XGBoost
| | Isolation Forest (F2+F3) | XGBoost Predictor (F4) |
|---|---|---|
| Pregunta | ¿Este flujo es anómalo ahora? | ¿Esta IP va a atacar de nuevo? |
| Entrada | 14 features del flujo actual | 9 features de comportamiento histórico |
| Salida | PERMIT / LIMIT / BLOCK | Probabilidad P(%) de reincidencia |
| Reacción | Inmediata (por flujo) | Cada 10 segundos |

---

---

## ESCENARIO 4 — Tráfico normal no se bloquea (FPR = 0%)

### Qué demuestra
Que el sistema no interrumpe el tráfico legítimo. La whitelist protege las IPs de la infraestructura.

### Generar tráfico normal desde este Desktop
```bash
for i in $(seq 1 20); do curl -s http://192.168.0.120/ -o /dev/null; sleep 1; done
```

### Verificar que Desktop no está bloqueado
```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```
**Salida:**
```
192.168.0.20 is NOT in set ppi_blocked.
```

*"192.168.0.20, que es este Desktop, está en la whitelist. El motor la descarta antes de calcular el score. Nunca aparecerá en el ipset de bloqueados."*

*"En la validación formal, generé 119 flujos de tráfico normal en una sesión completamente nueva — diferente a la de entrenamiento — y la tasa de falsos positivos fue exactamente 0.0%."*

---

---

## ESCENARIO 5 — Autoaprendizaje F5 (mostrar evidencia, no ejecutar en vivo)

### Qué demuestra
Que el sistema mejora con los datos que genera el mismo motor. No necesita re-entrenamiento manual.

```bash
# Ver el crontab activo en el sensor
ssh m4rk@192.168.0.110 "crontab -l"
# Resultado: IF domingos 02:00 / XGBoost diario 03:00

# Ver historial de reentrenamientos XGBoost
ssh m4rk@192.168.0.110 "cat /home/m4rk/ppi-surikata-producto/results/metricas_f5_xgboost.txt"
```

*"El XGBoost se reentrena con los eventos LIMIT y BLOCK del motor_decision.log. Cada reentrenamiento verifica que el AUC nuevo sea mayor o igual al anterior — si el modelo nuevo es peor, no se reemplaza. A eso lo llamo anti-regresión."*

*"El motor detecta el modelo nuevo automáticamente revisando la fecha de modificación del archivo pkl en cada ciclo de 10 segundos, sin necesidad de reiniciar el servicio."*

---

---

## ESCENARIO 6 — Validación formal: 16/16 PASS

### Qué demuestra
Que el sistema cumple todos los criterios de aceptación del PPI, medidos automáticamente.

```bash
ssh m4rk@192.168.0.110 "bash /home/m4rk/ppi-surikata-producto/scripts/validacion/run_all.sh"
```

*"Esta suite verifica 16 criterios: desde que el AUC supera 0.85, hasta que la latencia P95 está bajo 500ms, pasando por que las IPs whitelisted nunca se bloquean."*

**Tres resultados clave:**
- **CA-02:** AUC Isolation Forest = **0.8998** (mínimo 0.85 ✅)
- **CA-09:** Latencia P95 = **34.768ms** (máximo 500ms ✅ — 14× más rápido que el límite)
- **CA-16:** FPR en 119 flujos nuevos = **0.0%** ✅

---

---

## Métricas finales del sistema

| Modelo / Componente | Métrica | Valor |
|---|---|---|
| Isolation Forest | AUC-ROC | **0.8998** |
| IF | Precision / Recall en τ1 | **99.54% / 99.40%** |
| IF | τ1 — límite PERMIT/LIMIT | **−0.4459** |
| IF | τ2 — límite LIMIT/BLOCK | **−0.6027** |
| Motor | Latencia P95 del pipeline | **34.768ms** |
| XGBoost v2 | AUC-ROC | **0.9992** |
| XGBoost v2 | Errores totales (de 12,488) | **14** (7 FP + 7 FN) |
| Sistema | Lead time HTTP Flood | **~5s** (heurístico 100req/30s) |
| Sistema | Lead time BF-SSH | **60s** (heurístico 15intentos/60s) |
| Sistema | Disponibilidad (40 corridas F6) | **100%** |
| Sistema | Interrupción tráfico legítimo | **0%** |
| CA-16 | FPR en datos nuevos | **0.0%** (119 flujos) |
| Validación | Criterios PASS | **16/16** |

---

## Capturas a tomar durante la demo

| # | Qué | Cuándo |
|---|---|---|
| 1 | 4 `active` en terminal | Preparación |
| 2 | hping3 corriendo con paquetes | Al lanzar el ataque |
| 3 | `SOSPECHOSO ... LIMIT` en motor log | ~5s después de hping3 |
| 4 | `HTTP-ABUSE ... BLOCK → BLOCKED` en motor log | ~35s después |
| 5 | `ipset list ppi_blocked` con timeout | Inmediatamente después del BLOCK |
| 6 | `ALERTA-PREDICTIVA P=XX%` en predictor log | Segundos después del BLOCK |
| 7 | Telegram en el celular | Al recibirlo |
| 8 | `BRUTE_FORCE_SSH ... BLOCK` en motor log | Durante el hydra |
| 9 | `ipset test 192.168.0.20 NOT in set` | Escenario normal |
| 10 | `run_all.sh` con 16/16 PASS | Validación final |
