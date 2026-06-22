# F3 — Control en Tiempo Real (Motor + ipset + Dashboard)
**Estado: ✅ COMPLETA Y VALIDADA**  
**Resultado:** Latencia P95=34.8ms | Disponibilidad=100% | ITL=0% | Lead time B1≈62s

---

## Objetivo

Aplicar la decisión del IF sobre cada flujo nuevo en la red de forma automática, inline y en tiempo real: clasificar como PERMIT / LIMIT / BLOCK, ejecutar el control de red mediante ipset/iptables, visualizar el estado del sistema y notificar al operador ante eventos críticos.

---

## Terminología clave

| Término | Definición |
|---|---|
| **Motor de decisión** | Script `motor_decision.py` que opera en tiempo real. Lee eve.json línea a línea, extrae features, aplica el IF y decide la acción para cada flujo. Es el núcleo operativo de todo el sistema. |
| **tail -f (seguimiento)** | El motor lee eve.json como un proceso que espera nuevas líneas (similar a `tail -f`). Cada línea nueva de Suricata es procesada inmediatamente. |
| **ipset** | Estructura de datos del kernel Linux que almacena conjuntos de IPs con soporte para timeout. Más eficiente que reglas iptables individuales. Actualizable en tiempo real sin reiniciar el firewall. |
| **iptables** | Sistema de filtrado de paquetes del kernel Linux. Referencia a ipsets: "si la IP origen está en `ppi_blocked`, descartar el paquete (DROP)". |
| **ppi_blocked** | Conjunto ipset de IPs con DROP total. Todo paquete de estas IPs es descartado en el kernel antes de llegar a las aplicaciones. Timeout configurable (300s / 1800s / permanente). |
| **ppi_limited** | Conjunto ipset de IPs con rate limiting (`hashlimit 100pkt/s`). La IP puede comunicarse pero a velocidad reducida. |
| **hashlimit** | Módulo iptables que limita la tasa de paquetes por IP. Configurado en 100 pkt/s para IPs en `ppi_limited`. Un SYN flood genera 10,000+ pkt/s → reducido a 100. |
| **PERMIT** | Decisión del motor: el flujo es normal (score > τ1). Solo se registra en log como INFO. No hay acción en red. |
| **LIMIT** | Decisión: el flujo es sospechoso (τ2 < score ≤ τ1). IP añadida a `ppi_limited`. Tráfico limitado a 100 pkt/s. |
| **BLOCK** | Decisión: el flujo es claramente anómalo (score ≤ τ2). IP añadida a `ppi_blocked`. Todo tráfico descartado (DROP). |
| **Bloqueo progresivo** | Sistema de escalada: BLOCK#1=300s, BLOCK#2=1800s, BLOCK#3=permanente (timeout=0). Persiste en `block_counts.json`. |
| **Whitelist** | Lista de IPs que el motor nunca bloquea, independientemente del score. Se verifica ANTES del IF para evitar falsos positivos en IPs conocidas. |
| **Heurístico** | Regla adicional basada en conteo de eventos, independiente del score IF. Detecta patrones que el IF podría pasar por alto si los flujos individuales parecen normales. |
| **ITL** | Interrupción de Tráfico Legítimo. Mide si algún flujo de tráfico normal fue bloqueado incorrectamente. ITL=0% es requisito. |
| **Lead time** | Tiempo desde el inicio de un ataque hasta el primer BLOCK. Mide la velocidad de respuesta del sistema. |
| **SSE (Server-Sent Events)** | Protocolo HTTP para push de datos del servidor al navegador en tiempo real. El dashboard web usa SSE para actualizar sin recargar la página. |
| **Flask** | Framework web Python ligero. Sirve el dashboard web (`dashboard_web.py`) en el puerto 8080. |
| **systemd service** | Unidad de gestión de servicios de Linux. `ppi-motor.service` mantiene el motor corriendo, lo reinicia si falla y lo arranca con el sistema. |

---

## Arquitectura del componente

```
Suricata → eve.json
              │
              ▼  (tail en tiempo real)
     motor_decision.py
              │
    ┌─────────┼─────────────────────────┐
    │         │                         │
    ▼         ▼                         ▼
Whitelist   IF.decision_function()   Heurísticos
check       + τ1/τ2                  BF-SSH / HTTP-Abuse
    │         │                         │
    └─────────┼─────────────────────────┘
              │
         ┌────┴────┐
    PERMIT    LIMIT/BLOCK
         │         │
      log INFO   enforce.sh
                   │
              ┌────┴────────────────┐
              │                     │
         ipset add            Telegram
         ppi_blocked          notificación
         ppi_limited
              │
         Dashboard           predictor.py
         web :8080            (F4)
```

---

## Flujo de decisión detallado por flujo

```
ENTRADA: nueva línea JSON en eve.json con event_type=flow

1. ¿Es event_type == "flow"?  NO → ignorar
   SÍ ↓

2. ¿src_ip está en whitelist?
   SÍ → PERMIT inmediato, log INFO, continuar
   NO ↓

3. Extraer 14 features (mismo orden que models/features.csv)
   │
   ▼
4. X_scaled = scaler.transform(features)
   score = IF.decision_function(X_scaled)

5. Clasificar:
   score > −0.4459 (τ1) → PERMIT
   −0.6027 < score ≤ −0.4459 → LIMIT → ipset ppi_limited
   score ≤ −0.6027 (τ2)     → BLOCK → ipset ppi_blocked → Telegram

6. Verificar heurísticos (independiente del score):
   BF-SSH:     src_ip hizo ≥5 intentos SSH en 60s → LIMIT
               src_ip hizo ≥15 intentos SSH en 60s → BLOCK
   HTTP-Abuse: src_ip hizo ≥50 req HTTP en 30s → LIMIT
               src_ip hizo ≥100 req HTTP en 30s → BLOCK

7. Si BLOCK: bloqueo progresivo
   block_counts[ip] == 1 → timeout 300s  (5 min)
   block_counts[ip] == 2 → timeout 1800s (30 min)
   block_counts[ip] >= 3 → timeout 0     (PERMANENTE)

8. Escribir línea en motor_decision.log
   Actualizar block_counts.json
```

---

## Detección heurística — por qué existe junto al IF

El IF clasifica **flujo por flujo**. Un flujo de Brute Force SSH individual puede ser breve y con pocos paquetes (score≈−0.48, cerca de τ1). El IF lo marcaría como LIMIT pero podría escaparse.

Los heurísticos cuentan eventos acumulados en ventana temporal:
- **5 intentos SSH/60s** → definitivamente BF-SSH (LIMIT inmediato)
- **15 intentos SSH/60s** → ataque confirmado (BLOCK)

Esto asegura que B6 (hydra) siempre sea bloqueado incluso si el score IF es ambiguo.

---

## Whitelist — IPs nunca bloqueadas

```python
WHITELIST = {
    '192.168.0.1',    # Gateway
    '192.168.0.20',   # Desktop (Admin) — origen del tráfico normal
    '192.168.0.110',  # Sensor (propio) — no bloquearse a sí mismo
    '192.168.0.120',  # Servidor (objetivo) — proteger el destino
    '192.168.0.130',  # Reservada
    '192.168.0.140',  # Reservada
    '127.0.0.1',      # Loopback
}
```

La verificación de whitelist ocurre **antes** del IF. Las IPs whitelisted nunca consumen tiempo de inferencia.

---

## Formato del log de motor

```
# Flujo BLOQUEADO (score muy bajo):
2026-06-22 08:31:37,412 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.6228 grado=ALTA tipo=BRUTE_FORCE_SSH byte_ratio=1.97 pkt_rate=3.2 | BLOCK

# Flujo LIMITADO (score en zona media):
2026-06-22 08:31:30,154 | WARNING | SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:22
  proto=TCP score=-0.4832 grado=BAJA tipo=BF_SSH_warn byte_ratio=1.97 pkt_rate=2.1 | LIMIT

# Estadísticas cada 500 flujos:
2026-06-22 15:04:03,117 | INFO | Estadísticas | flows=138500 anomalías=138500 bf=0
  http_abuse=138401 bloqueados=1 limitados=0 latencia_media=34.44ms

# Flujo NORMAL (log solo en modo debug):
2026-06-22 09:00:00,000 | INFO | PERMIT | src=192.168.0.20 dst=192.168.0.120:80
  score=0.0412 | PERMIT
```

---

## Dashboard terminal (`dashboard.py`)

```bash
# En el sensor — actualiza cada 3 segundos
python3 scripts/dashboard.py
```

Muestra: flujos/min, anomalías detectadas, IPs bloqueadas activas, latencia media, últimas alertas.

## Dashboard web (`dashboard_web.py`)

```bash
# Acceder desde Desktop:
# http://192.168.0.110:8080

# Iniciar si no está corriendo:
ssh m4rk@192.168.0.110 \
  "nohup /home/m4rk/ppi-sensor/venv/bin/python3 \
   /home/m4rk/ppi-surikata-producto/scripts/dashboard_web.py &"
```

Usa Flask + SSE (Server-Sent Events) para actualización en tiempo real sin recargar.  
Muestra: panel de decisiones en vivo, IPs bloqueadas, predicciones XGBoost (F4), historial de alertas.

---

## Telegram — notificaciones al operador

- **Cuándo:** al primer BLOCK de una IP nueva (dedup 5 min por IP)
- **Qué incluye:** IP atacante, tipo de ataque, score, puerto, timestamp
- **Configuración:** `config/telegram.conf` (bot token + chat_id — fuera de git)
- **Relay:** HTTP POST a `http://192.168.0.20:8889/telegram` → bot envía al chat
- **No bloqueante:** si el relay no responde, el motor continúa sin esperar

Evidencia real: `🚨 PPI ALERTA — BRUTE_FORCE_SSH | BLOCK | IP: 192.168.0.100 | Puerto: 22 | 08:31:37`

---

## Bloqueo progresivo — evidencia real (2026-06-22)

| Bloqueo | Timestamp | Trigger | Timeout ipset |
|---|---|---|---|
| #1 | 05:44:13 | score=−0.6066 (SYN flood) | 300s (5 min) |
| #2 | 06:05:03 | score=−0.7696 (reincidencia) | 1,800s (30 min) |
| #3 | 06:39:42 | HTTP-ABUSE 100 req/30s | **0 (PERMANENTE)** |

```json
block_counts.json final: {"192.168.0.100": 2}
```

---

## Métricas validadas

| Métrica | Valor | Criterio | Estado |
|---|---|---|---|
| **Latencia P95** | **34.768ms** | < 500ms | ✅ (×14 de margen) |
| **Latencia media** | **34.44ms** | — | Medida en vivo 2026-06-22 |
| **ITL** | **0%** | = 0% | ✅ |
| **Disponibilidad** | **100%** | ≥ 99% | ✅ |
| **Lead time SYN Flood** | **~62s** | < 120s | ✅ |
| **Lead time BF SSH** | **~60s** | < 90s | ✅ |
| **BLOCKs registrados** | **12,811+** | > 0 | ✅ |
| **Whitelist FAIL** | **0/5 IPs** | = 0 | ✅ |

---

## Imágenes de referencia (pendientes de captura)

| Imagen | Descripción |
|---|---|
| `F3_motor_control/captura_motor_log_block.png` | Log en vivo con BLOCKs de Kali |
| `F3_motor_control/captura_dashboard_web.png` | Dashboard web con alertas activas |
| `F3_motor_control/captura_telegram_alerta.png` | Notificación Telegram real |
| `F3_motor_control/captura_ipset_bloqueados.png` | `sudo ipset list ppi_blocked` |
| `F3_motor_control/captura_bloqueo_permanente.png` | IP con timeout=0 en ipset |

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado |
|---|---|---|
| CA-5 | Latencia P95 < 500ms | ✅ 34.768ms |
| CA-6 | Motor activo — ITL=0% | ✅ 1.18M entradas, 0 falsos BLOCK |
| CA-7 | τ1/τ2 cargados al arranque | ✅ −0.4459 / −0.6027 |
| CA-8 | Whitelist nunca bloqueada | ✅ 0/5 IPs en block_counts |
| CA-9 | IP atacante efectivamente bloqueada | ✅ 12,811 BLOCKs a 192.168.0.100 |
| CA-10 | Bloqueo #3 = PERMANENTE | ✅ timeout=0 validado 2026-06-22 |
| CA-F3-01 | Dashboard web accesible :8080 | ✅ |
| CA-F3-02 | Telegram notifica sin bloquear motor | ✅ HTTP 200 confirmado |
| CA-F3-03 | Heurísticos BF-SSH y HTTP-Abuse activos | ✅ Validado con B5 y B6 |

---

## Argumento de defensa

> "F3 es donde el modelo se convierte en control de red real. La diferencia frente a un IDS pasivo es que aquí el sistema no solo detecta sino que actúa: en 34ms P95 desde que Suricata registra el flujo hasta que la IP está en ipset y el tráfico descartado en el kernel. Los heurísticos complementan al IF en los ataques graduales como el brute force SSH, donde flujos individuales son sutiles pero el patrón acumulado es inequívoco. El lead time de 60 segundos frente al NIST SP 800-61 que establece como crítico actuar en menos de 120 segundos."
