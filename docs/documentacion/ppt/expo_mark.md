# Expo Mark — Presentación del Producto
**Desde Slide 8 | Menos de 10 minutos**
**Evidencia verificada en vivo 2026-06-24**

---

## ESTRUCTURA DE TIEMPO

| Parte | Contenido | Tiempo |
|---|---|---|
| Slide 8 | ¿Qué hace el producto? | 30 seg |
| Slide 9 | Arquitectura — 4 nodos | 1 min |
| Demo | Video/capturas con guion oral | 4 min |
| Slide 13 | Resultados → OE1–OE4 | 2 min |
| Cierre | Una frase | 15 seg |
| **TOTAL** | | **~8 min** |

---

---

## SLIDE 8 — El Producto: ¿Qué hace?
**Tiempo: 30 seg**

### Visual — texto grande centrado
```
SURIKATA

Detecta ataques en tiempo real y los bloquea automáticamente
sin intervención humana, en menos de 35 milisegundos.

   [Detecta]        [Decide]        [Bloquea]
  tráfico anómalo   en <35ms        en el kernel
  con ML            sin humano      del servidor
```

### Oralidad
> *"Vamos a demostrar que nuestro sistema está funcionando en tiempo real. Tenemos tres máquinas: el sensor que captura el tráfico, el servidor que es el objetivo, y Kali Linux desde donde lanzaré los ataques. El producto hace tres cosas: detecta tráfico anómalo con Machine Learning, decide en menos de 35 milisegundos, y bloquea automáticamente sin intervención humana."*

---

## SLIDE 9 — Arquitectura
**Tiempo: 1 min**

### Visual
→ Usar la imagen de la diapositiva de Arquitectura General (la que tienes con los 4 nodos)

```
[Desktop Admin]    [Kali Atacante]
        ↓ (normal)      ↓ (ataque)
         ────── RED ──────
                ↓
        [Sensor Ubuntu 192.168.0.110]
         Suricata · Isolation Forest
         Motor de decisión · XGBoost
                ↓ SSH → ipset add
        [Servidor 192.168.0.120]
         nginx:80 · SSH:22
         iptables + ipset DROP
```

### Oralidad
> *"Cuatro nodos. El sensor corre Suricata en modo promiscuo — captura todo el tráfico de la red. El motor con el Isolation Forest analiza cada flujo. Cuando decide bloquear, hace SSH al servidor y ejecuta un comando ipset — el kernel del servidor descarta los paquetes del atacante directamente, antes de que lleguen al servicio."*
>
> *"El sensor y el servidor son máquinas separadas. Si el motor falla, el servidor sigue funcionando."*

---

## DEMO — Guion con capturas reales
**Tiempo: 4 min**

> Mostrar capturas en orden — o video pregrabado

---

### [D1] Sistema activo — verificación inicial

**Captura:** terminal con los 4 `active`

```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata ppi-motor.service ppi-predictor.service ppi-dashboard.service"
```
```
active
active
active
active
```

**Oralidad:**
> *"Primero verifico que todo está activo: Suricata capturando, motor de decisión con el IF, predictor XGBoost y dashboard web."*

---

### [D2] Lanzar el ataque — HTTP Flood desde Kali

**Captura:** terminal Kali con hping3 corriendo

```bash
# En Kali:
sudo hping3 -S -p 80 -i u5000 192.168.0.120
```

**Oralidad:**
> *"Lanzo un flood de paquetes SYN hacia el servidor en el puerto 80 — 200 paquetes por segundo. Suricata los captura, el motor los analiza con el Isolation Forest."*

---

### [D3] OE2 — IF detecta la anomalía

**Captura:** motor_decision.log con SOSPECHOSO y BLOCK

```
01:20:17 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.5045 | LIMIT

01:20:21 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6028 tipo=HTTP_ABUSE | BLOCK → BLOCKED (bloqueo#1 timeout=300s)
```

**Oralidad:**
> *"Miren el log del motor. En segundos aparecen las primeras detecciones."*
>
> *"Primer flujo: score −0.5045. Está entre mis dos umbrales — τ1 es −0.4459 y τ2 es −0.6027 — zona SOSPECHOSA. El sistema aplica LIMIT: le limita el ancho de banda a 100 paquetes por segundo en el servidor."*
>
> *"Segundos después: score −0.6028, por debajo de τ2. El detector HTTP-ABUSE confirmó más de 100 requests en 30 segundos. Escala a BLOCK — DROP directo en el kernel del servidor."*
>
> *"Esto es OE2 funcionando: el Isolation Forest asignó un score de anomalía y los umbrales derivados de la curva ROC tomaron la decisión."*

---

### [D4] OE3 — Bloqueo real en el servidor

**Captura:** ipset list ppi_blocked con IP y timeout

```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
```
```
Members:
192.168.0.100 timeout 290
```

**Oralidad:**
> *"Verifico el bloqueo directamente en el servidor. 192.168.0.100 está en el ipset con 290 segundos restantes. La regla iptables hace DROP a todo paquete de esa IP. El atacante está cortado en el kernel — sin llegar a nginx, sin consumir recursos del servidor."*
>
> *"Esto es OE3: motor de decisión en tiempo real, clasificación y control automático."*

---

### [D5] OE4 — Predictor XGBoost predice sostenimiento

**Captura:** predictor.log con la progresión de P%

```
01:20:20 | INFO    | OK               | src=192.168.0.100 P=0.11%  blocks_60s=0
01:20:30 | INFO    | AVISO            | src=192.168.0.100 P=54.65% blocks_60s=3
01:20:40 | WARNING | ALERTA-PREDICTIVA| src=192.168.0.100 P=97.45% blocks_60s=4
01:21:11 | INFO    | ALERTA-PREDICTIVA| src=192.168.0.100 P=99.69% blocks_60s=9
```

**Oralidad:**
> *"Aquí está OE4 — el predictor XGBoost. No analiza el flujo actual — analiza el historial de bloqueos de esa IP en los últimos 60 segundos."*
>
> *"Al primer momento: P=0.11% — sin historial todavía. Con 3 bloqueos acumulados: P=54%, aviso. Con 4 bloqueos: P=97.45% — ALERTA-PREDICTIVA. El sistema predice con 97% de certeza que el ataque es sostenido y no un evento aislado."*
>
> *"¿Para qué sirve esto? Para el bloqueo progresivo: si el predictor confirma sostenimiento, el segundo bloqueo dura 30 minutos. El tercero es permanente."*

---

### [D6] Whitelist — tráfico legítimo intacto

**Captura:** ipset test ppi_blocked 192.168.0.20

```bash
ssh m4rk@192.168.0.120 "sudo ipset test ppi_blocked 192.168.0.20 2>&1"
```
```
192.168.0.20 is NOT in set ppi_blocked.
```

**Oralidad:**
> *"Y el Desktop — el administrador — nunca fue bloqueado. Generé 119 flujos normales nuevos desde cero después del entrenamiento: tasa de falsos positivos exactamente 0.0%."*

---

## SLIDE 13 — Resultados → OE1–OE4
**Tiempo: 2 min**

### Visual — tabla de resultados alineada a los OE

| OE | Qué se logró | Métrica clave |
|---|---|---|
| **OE1** | 47 capturas · 9 escenarios · 53,708 flujos entrenamiento | Pipeline F1+F2 completo |
| **OE2** | Isolation Forest detecta anomalías con score continuo | AUC=0.8998 · Precision=99.54% · Recall=99.40% |
| **OE3** | Motor clasifica y bloquea en tiempo real | Latencia P95=34.8ms · ITL=0% · Disponibilidad=100% |
| **OE4** | XGBoost predice sostenibilidad del ataque | AUC=0.9991 · P=97.45% en demo en vivo |
| **General** | 16/16 criterios de aceptación PASS | 40 corridas F6 validadas |

### Oralidad
> *"Los resultados responden directamente a los cuatro objetivos."*
>
> *"OE1: pipeline completo — 47 capturas de tráfico real en 9 escenarios distintos, 53 mil flujos para entrenar."*
>
> *"OE2: el Isolation Forest logró AUC de 0.8998 — por encima del criterio mínimo de 0.85. Precision y Recall del 99%. Los umbrales τ1 y τ2 se derivaron matemáticamente del índice de Youden sobre la curva ROC."*
>
> *"OE3: latencia de 34.8 milisegundos — 14 veces más rápido que el requisito de 500ms. Disponibilidad del servidor 100% durante todos los ataques. Cero interrupciones de tráfico legítimo."*
>
> *"OE4: el predictor XGBoost con AUC 0.9991 — y acabamos de ver P=97.45% en demo en vivo. Distingue ataques sostenidos de eventos aislados para escalar el bloqueo de forma inteligente."*
>
> *"16 de 16 criterios de aceptación: todos PASS."*

---

## CIERRE
**Tiempo: 15 seg**

### Oralidad
> *"El sistema detecta, decide y bloquea. Sin intervención humana. En menos de 35 milisegundos. Muchas gracias."*

---

---

## RESPUESTAS RÁPIDAS — si el jurado pregunta

| Pregunta | Respuesta |
|---|---|
| ¿Por qué Isolation Forest y no supervisado? | No necesitamos etiquetas de ataques — aprende solo de tráfico normal. Cualquier desviación es anomalía. Eso cubre ataques no vistos antes. |
| ¿Por qué FPR=20% en τ1? | Bajar el FPR a 5% haría que los SYN floods escaparan — tienen score ≈−0.49, justo donde estaría el nuevo τ1. El FPR operativo es 0% porque la whitelist protege todas las IPs legítimas. |
| ¿El XGBoost no predice antes del bloqueo? | Predice si el ataque continuará después del primer bloqueo. Eso permite bloqueo progresivo inteligente: 5 min si es dudoso, 30 min si reincide, permanente al tercero. |
| ¿AUC=0.9991 no es sobreajuste? | v1 tenía AUC=1.0000 — ese sí era sobreajuste por data leakage (el score IF como feature). v2 eliminó esa feature. AUC=0.9991 sobre test set nunca visto es generalización real. |
| ¿Qué pasa si el motor falla? | El servidor sigue funcionando — son máquinas separadas. Los bloqueos ya aplicados en ipset persisten aunque el motor se caiga. |
| ¿Cómo se actualiza el modelo? | Reentrenamiento automático: IF los domingos a las 02:00, XGBoost diario a las 03:00. Con protección anti-regresión — si el nuevo modelo es peor, no se reemplaza. |

---

## EVIDENCIA REAL — Capturas del 2026-06-24 01:20

### motor_decision.log
```
01:20:17 | WARNING | SOSPECHOSO | src=192.168.0.100 score=-0.5045 | LIMIT
01:20:21 | WARNING | ANOMALÍA   | src=192.168.0.100 score=-0.6028 | BLOCK → BLOCKED (timeout=300s)
```

### predictor.log
```
01:20:20 | INFO    | OK                | P=0.11%  blocks_60s=0
01:20:30 | INFO    | AVISO             | P=54.65% blocks_60s=3
01:20:40 | WARNING | ALERTA-PREDICTIVA | P=97.45% blocks_60s=4
01:21:11 | INFO    | ALERTA-PREDICTIVA | P=99.69% blocks_60s=9
```

### ipset en servidor
```
Members:
192.168.0.100 timeout 290
```

### block_counts.json
```json
{"192.168.0.100": 1}
```
