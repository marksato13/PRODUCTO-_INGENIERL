# Plan de Mejoras — Motor de Decisión + Alertas Telegram + Dashboard

**Fecha:** 2026-06-19
**Alcance:** mejoras incrementales en la capa de salida de F4 y visualización.
**Regla:** cero cambios en la lógica de decisión (τ1/τ2, ipset, IF score).

---

## Diagnóstico del sistema actual

### Lo que ya existe y funciona
- Telegram: `TG_TOKEN`, `TG_CHAT_ID`, `TG_RELAY` configurados, cola no-bloqueante con worker thread
- SSE (Server-Sent Events) en dashboard_web.py: push en ~150ms al browser
- Detectores heurísticos: SSH brute force + HTTP abuse
- `clasificar_grado()` y `clasificar_tipo()` producen contexto cualitativo

### Problemas encontrados (bugs reales en el código actual)

| ID | Archivo | Línea aprox. | Problema |
|---|---|---|---|
| BUG-01 | motor_decision.py | ~432 | HTTP-ABUSE BLOCK: Telegram dice "Accion: LIMIT" pero la acción es BLOCK |
| BUG-02 | motor_decision.py | ~432 | HTTP-ABUSE BLOCK: usa variables `tipo` y `grado` antes de que se calculen |
| BUG-03 | motor_decision.py | todas | Mezcla de f-strings y concatenación en mensajes Telegram — inconsistente |
| BUG-04 | motor_decision.py | todas | Ningún mensaje Telegram incluye `byte_ratio` (la feature más discriminante) |

### Oportunidades de mejora (no bugs, mejoras de valor)

| ID | Descripción | Impacto |
|---|---|---|
| MEJ-01 | Añadir features clave (byte_ratio, pkt_rate, proto) a cada alerta Telegram | El operador sabe POR QUÉ se bloqueó, no solo QUE se bloqueó |
| MEJ-02 | Emitir evento SSE estructurado (JSON con features) además del log de texto | Dashboard puede mostrar tarjeta de alerta con barra de score |
| MEJ-03 | Deduplicación de alertas Telegram por IP (ventana 5 min) | Evita spam cuando la misma IP reintenta tras expirar el ipset |
| MEJ-04 | Alerta de tendencia pre-BLOCK (score < -0.35 pero > τ1) | Aviso anticipado antes de que llegue a BLOCK |

---

## FIX-01 — Corrección de mensajes Telegram inconsistentes (BUG-01, BUG-02, BUG-03)

**Archivo:** `scripts/motor_decision.py`
**Cambio:** unificar todos los `telegram_alerta()` a f-strings, corregir la acción errónea en HTTP-ABUSE BLOCK, mover el cálculo de `tipo`/`grado` antes de los bloques heurísticos.

**Antes (HTTP-ABUSE BLOCK):**
```python
telegram_alerta(
    "⚠️ PPI ALERTA — " + tipo + "\n"          # ← tipo no existe aún
    "Accion : LIMIT (100pkt/s)\n"              # ← incorrecto, es BLOCK
    ...
)
```

**Después:**
```python
telegram_alerta(
    f"🚨 PPI ALERTA — HTTP ABUSE\n"
    f"Accion  : BLOCK (DROP)\n"               # ← correcto
    f"IP      : {src_ip}\n"
    f"Puerto  : {dest_port}\n"
    f"Requests: {hab_n}/{HTTP_VENTANA_SEG}s\n"
    f"Hora    : {datetime.now().strftime(%Y-%m-%d %H:%M:%S)}"
)
```

**Fases afectadas:** solo F4 (capa de salida). Cero impacto en F1/F2/F3/F5/F6.

---

## FIX-02 — Features clave en alertas Telegram (MEJ-01 + BUG-04)

**Archivo:** `scripts/motor_decision.py`
**Cambio:** extraer `byte_ratio` y `pkt_rate` del flow ya procesado y añadirlos al mensaje Telegram de BLOCK y LIMIT del score IF.

**Cómo:** las features ya están calculadas en el vector `X` antes de llamar `score_samples()`. Solo hay que leer los valores del diccionario `e` (el flow de eve.json) que ya está disponible.

**Formato nuevo para BLOCK:**
```
🚨 PPI ALERTA — SYN FLOOD
Accion    : BLOCK (DROP)
IP        : 192.168.0.100
Proto     : TCP → :80
Score IF  : -0.7234  [CRITICA]
byte_ratio: 142.5  (normal ≈ 0.95)
pkt_rate  : 8,420 pkt/s
Hora      : 2026-06-19 14:32:11
```

**Fases afectadas:** solo F4 (salida). Cero impacto en lógica de decisión.

---

## FIX-03 — Evento SSE estructurado con features (MEJ-02)

**Archivo:** `scripts/motor_decision.py` (emisión) + `scripts/dashboard_web.py` (recepción)
**Cambio:** cuando el motor emite BLOCK o LIMIT, además de escribir en el log de texto, escribe una línea JSON en un archivo separado `results/eventos_alerta.jsonl`. El dashboard_web.py lee este archivo con su lector de log existente (mismo patrón que lee motor_decision.log) y lo empuja por SSE.

**Estructura del evento JSON:**
```json
{
  "ts": "2026-06-19T14:32:11",
  "accion": "BLOCK",
  "ip": "192.168.0.100",
  "proto": "TCP",
  "dest_port": 80,
  "score": -0.7234,
  "grado": "CRITICA",
  "tipo": "SYN_FLOOD",
  "byte_ratio": 142.5,
  "pkt_rate": 8420.1,
  "bytes_toserver": 2847320
}
```

**En el dashboard:** la tarjeta de alerta existente se enriquece con:
- Barra de score (rojo si BLOCK, naranja si LIMIT)
- Valor de `byte_ratio` con referencia "normal ≈ 0.95"
- Tipo de ataque detectado

**Fases afectadas:** F4 (escribe eventos_alerta.jsonl), dashboard (lee el nuevo archivo). No afecta F3/F5/F6.

---

## FIX-04 — Deduplicación de alertas Telegram por IP (MEJ-03)

**Archivo:** `scripts/motor_decision.py`
**Cambio:** añadir un diccionario `_last_tg_alert: dict[str, float]` con timestamp de última notificación por IP. Antes de llamar `telegram_alerta()`, verificar si han pasado ≥ 5 minutos desde la última alerta de esa IP.

```python
_last_tg_alert: dict = {}
TG_DEDUP_SEG = 300  # 5 minutos

def telegram_alerta_dedup(ip: str, mensaje: str):
    ahora = time.time()
    if ahora - _last_tg_alert.get(ip, 0) < TG_DEDUP_SEG:
        log.debug(f"Telegram dedup: {ip} — alerta suprimida (< {TG_DEDUP_SEG}s)")
        return
    _last_tg_alert[ip] = ahora
    telegram_alerta(mensaje)
```

**El log sigue registrando todos los eventos** — solo Telegram se filtra.
**Fases afectadas:** solo F4. Cero impacto en bloqueo real.

---

## FIX-05 — Alerta de tendencia pre-BLOCK (MEJ-04)

**Archivo:** `scripts/motor_decision.py`
**Cambio:** mantener un buffer deslizante de los últimos 10 scores por IP. Si la media de los últimos 10 flows de una IP cae por debajo de un umbral de aviso (-0.35, entre PERMIT y τ1) se envía una alerta de nivel "AVISO" a Telegram y al dashboard, antes de que llegue a BLOCK.

```python
TAU_AVISO = -0.35  # parámetro en config, entre τ0 (0) y τ1 (-0.4459)
_score_hist: dict = defaultdict(lambda: deque(maxlen=10))

# En el loop principal, después de calcular score:
_score_hist[src_ip].append(score)
if len(_score_hist[src_ip]) == 10:
    media = sum(_score_hist[src_ip]) / 10
    if media < TAU_AVISO and accion == PERMIT:
        telegram_alerta_dedup(src_ip,
            f"👀 PPI AVISO — TENDENCIA ANÓMALA\n"
            f"IP      : {src_ip}\n"
            f"Score media (10 flows): {media:.4f}\n"
            f"Umbral aviso: {TAU_AVISO}\n"
            f"Hora    : {datetime.now().strftime(%Y-%m-%d %H:%M:%S)}"
        )
```

**Fases afectadas:** solo F4 (nueva señal de salida). No modifica la decisión PERMIT/LIMIT/BLOCK.

---

## Orden de implementación recomendado

| Prioridad | Fix | Esfuerzo | Riesgo | Valor |
|---|---|---|---|---|
| 1 | FIX-01 — Bug mensajes Telegram | Bajo (30 min) | Ninguno | Corrige bugs reales |
| 2 | FIX-02 — Features en Telegram | Bajo (30 min) | Ninguno | Alta utilidad operativa |
| 3 | FIX-04 — Dedup Telegram | Bajo (20 min) | Ninguno | Evita spam |
| 4 | FIX-03 — SSE estructurado | Medio (1h) | Bajo | Dashboard más informativo |
| 5 | FIX-05 — Pre-alerta tendencia | Medio (45 min) | Bajo | Detección anticipada |

---

## Resumen de impacto por fase

| Fase | ¿Afectada? | Detalle |
|---|---|---|
| F1 — Captura (Suricata) | NO | Sin cambios |
| F2 — Parseo/Etiquetado | NO | Sin cambios |
| F3 — Modelo IF | NO | τ1/τ2/pkl sin tocar |
| F4 — Motor decisión | SÍ (mejoras) | Solo capa de salida/notificación |
| F5 — Control inline (ipset) | NO | Bloqueos idénticos |
| F6 — Validación (40 corridas) | NO | Las corridas validadas siguen siendo válidas |
| Dashboard web | SÍ (mejoras) | SSE más rico, no breaking |

**Las 40 corridas F6 y todas las métricas (AUC, F1, latencia) quedan completamente inalteradas.**

---

## Archivos a modificar / crear

| Archivo | Acción | Fix |
|---|---|---|
| `scripts/motor_decision.py` | Modificar | FIX-01, FIX-02, FIX-04, FIX-05 |
| `scripts/dashboard_web.py` | Modificar | FIX-03 |
| `results/eventos_alerta.jsonl` | Crear (motor lo genera) | FIX-03 |

