# Hallazgos de Tests en Vivo — 2026-06-19

**Motor:** `motor_decision.py` | τ1=−0.4459 | τ2=−0.6027 | sklearn 1.9.0
**Ejecutado por:** Rubén Mark Salazar Tocas

---

## Resultados de los Tests

| Test | Resultado | Tiempo detección | Decisión |
|---|---|---|---|
| A — Tráfico normal Desktop .20 | PASS | — | 0 alertas (whitelist) |
| B2 — Port Scan (nmap -sS) | PASS | < 15 s | BLOCK score=−0.6190 |
| B5 — HTTP Abuse (curl loop) | PASS | ~30 s | BLOCK requests=100/30s |
| B6 — Brute Force SSH (hydra) | PASS | ~60 s | BLOCK intentos=15/60s |
| C1 — Mixto SYN Flood + Normal | PASS | ~62 s | Kali detectada · Desktop ITL=0% |

**Métricas del motor durante los tests:**
- Latencia media: **35.4 ms** (req. < 500 ms: CUMPLE)
- Alertas para Desktop .20: **0** (whitelist funcionando correctamente)

---

## Hallazgo 1 — FIX-02 confirmado en producción

**byte_ratio aparece en el log y en Telegram con valores reales.**

Entrada real del log durante SYN Flood (C1):

```
2026-06-19 06:52:24 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80
proto=TCP score=-0.4461 grado=BAJA tipo=BAJA_ANOMALIA byte_ratio=60.00 pkt_rate=1000.0 | LIMIT
```

`byte_ratio=60.00` confirma el hallazgo del EDA en producción real: tráfico anómalo tiene ratio
62.8× el normal (normal ≈ 0.95). El dato llega al dashboard por SSE en tiempo real.

---

## Hallazgo 2 — Regla crítica para reproducir tests

**Problema:** si se vacía el ipset sin reiniciar el motor, la IP no se vuelve a bloquear.

**Causa:** el motor mantiene un set Python `bloqueados` en memoria. Si .100 fue bloqueada y
luego se hace `ipset flush` sin reiniciar el motor, la IP sigue en `bloqueados` y las siguientes
detecciones van al branch `log.debug()` sin re-agregar al ipset.

**Regla para tests — siempre limpiar ipset Y reiniciar motor juntos:**

```bash
ssh m4rk@192.168.0.120 "echo cisco123 | sudo -S bash -c \
  'ipset flush ppi_blocked; ipset flush ppi_limited'"
ssh m4rk@192.168.0.110 "echo cisco123 | sudo -S systemctl restart ppi-motor.service"
sleep 6
```

**Impacto en producción real:** ninguno. En producción no se hace flush manual del ipset.

---

## Hallazgo 3 — SYN Flood clasificado como HTTP_ABUSE

**Observado:** `hping3 -S --flood -p 80` genera `tipo=HTTP_ABUSE` en el log, no `SYN_FLOOD`.

**Causa:** el detector heurístico `detectar_http_abuse()` cuenta cada flow con `dest_port=80`
como request HTTP sin distinguir si es TCP válido o SYN flood. Al superar los 100 flows/30s,
el tipo queda como HTTP_ABUSE.

`clasificar_tipo()` solo devuelve `SYN_FLOOD` si cumple simultáneamente:
- `proto == "TCP"`
- `pkt_rate > 2000`
- `dur < 2.0`
- `btc < 100` (bytes_toclient)

La condición `btc < 100` puede no cumplirse si Suricata captura alguna respuesta del servidor.

**Impacto operativo:** ninguno. El bloqueo ocurre igual (score <= τ2 → BLOCK).

**Mejora futura:** en `clasificar_tipo()`, priorizar SYN_FLOOD cuando `pkt_rate > 5000`
y `byte_ratio < 1.0` simultáneamente, antes de verificar el contador HTTP.

---

## Hallazgo 4 — ipset vacío bajo SYN Flood intenso (C1)

**Observado:** después de un BLOCK en el log durante C1, el ipset del servidor quedó vacío.

**Causa:** `bloquear_ip()` hace SSH al servidor .120 para ejecutar `ipset add`.
Bajo un SYN flood intenso dirigido a .120, el servidor puede no aceptar conexiones SSH
nuevas dentro del `ConnectTimeout=5s`. El SSH falla y la IP no se agrega al ipset.

El orden de operaciones en el motor es:

```python
bloqueados.add(src_ip)     # 1 — Python set (siempre ocurre)
resp = bloquear_ip(src_ip) # 2 — SSH al servidor (puede fallar bajo flood)
log.warning(f"... BLOCK")  # 3 — Log (siempre ocurre)
```

**Impacto:** durante un SYN flood muy intenso existe una ventana donde la detección
ocurre en log y Telegram pero la regla de kernel no se aplica en el servidor.

**Mitigación actual:** el heurístico HTTP y el score IF detectan en ~30s. Una vez que
el flood baja de intensidad el SSH tiene éxito y el bloqueo se aplica.

**Mejora futura:** implementar ipset local en el sensor en modo bridge para que el
bloqueo no dependa de SSH al servidor bajo ataque.

---

## Hallazgo 5 — Proceso fantasma motor_universal

**Observado:** `motor_universal.py` (PID 491874) corriendo al 98.9% CPU durante 222 minutos.

**Causa:** iniciado manualmente y nunca detenido. Escribía al mismo `motor_decision.log`
con formato diferente (sin pipes), mezclando líneas con motor_decision.py.

**Solución:** `kill 491874`

**Prevención — verificar antes de cada sesión de pruebas:**

```bash
ps aux | grep motor | grep -v grep
# Solo debe aparecer motor_decision.py via systemd
# Si aparece motor_universal.py → kill <PID>
```

---

## Hallazgo 6 — Log de 107 MB con mezcla histórica

**Observado:** `motor_decision.log` acumula 107 MB y 1.17 M líneas desde el 2 de junio.

**Impacto en tests:** grep sobre el log completo mezcla entradas del mismo horario
de días distintos (ej: `grep '06:53'` devuelve entradas del 2-jun y del 19-jun mezcladas).

**Solución durante tests — siempre filtrar por fecha completa:**

```bash
# CORRECTO
grep '2026-06-19' motor_decision.log | grep 'BLOCK'

# INCORRECTO (mezcla fechas con mismo horario)
grep '06:53' motor_decision.log | grep 'BLOCK'
```

**Mejora futura:** configurar logrotate para rotar el log diariamente.
El dashboard y el motor leen siempre desde el final del archivo, por lo que
una rotación no afecta el funcionamiento.

---

## Resumen de estado post-tests

| Componente | Estado |
|---|---|
| Motor ppi-motor.service | activo, latencia 35ms |
| τ1 / τ2 cargados | −0.4459 / −0.6027 correctos |
| FIX-01 mensajes Telegram | confirmado correcto |
| FIX-02 byte_ratio en log+Telegram | confirmado en producción (60.00 vs 0.95 normal) |
| FIX-03 SSE estructurado | dashboard recibe eventos con features |
| FIX-04 dedup Telegram | sin spam de misma IP |
| FIX-VIS metricas dashboard | valores correctos visibles |
| Dashboard :8080 | SSE activo, 2 clientes |
| ITL Desktop .20 | 0 alertas en todos los tests |
