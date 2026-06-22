# Checklist de Pendientes — Defensa PPI
**Actualizado:** 2026-06-22 | **Estado general:** L1–L10 implementadas, validación en curso

---

## 🔴 CRÍTICO — El jurado puede atacar directamente

### 1. Capturas de pantalla para el PPT
Sin evidencia visual el PPT queda vacío en la sección de demo.

| Captura | Qué mostrar | Estado |
|---|---|---|
| Terminal motor_decision.log | 3 líneas de bloqueo (#1 300s, #2 1800s, #3 PERMANENTE) | ⏳ pendiente |
| `sudo ipset list ppi_blocked` en servidor | `192.168.0.100 timeout 0` | ⏳ pendiente |
| Dashboard web http://192.168.0.110:8080 | Alertas activas con Kali en lista de bloqueados | ⏳ pendiente |
| Telegram en teléfono | Mensaje de alerta BLOCK recibido | ⏳ pendiente |
| `cat block_counts.json` | `{"192.168.0.100": 3}` | ⏳ pendiente |

**Cómo obtenerlas:** lanzar corrida B1 SYN Flood corta y capturar pantalla en cada paso.

---

### 2. Telegram — verificar alerta llega en tiempo real
El motor tiene integración (38 entradas en log histórico, `telegram_alerta_ip()` en 4 puntos).
Pero se necesita captura en teléfono para la defensa: "¿cómo se entera el admin?"

**Validar:**
```bash
# Desde Desktop, probar envío directo:
python3 -c "
import requests, configparser
cfg = configparser.ConfigParser()
cfg.read('/home/m4rk/ppi-surikata-producto/config/telegram.conf')
token = cfg['DEFAULT']['TG_TOKEN']
chat  = cfg['DEFAULT']['TG_CHAT_ID']
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
    json={'chat_id': chat, 'text': 'TEST alerta Telegram PPI OK'})
print(r.json())
"
```
Luego lanzar ataque B1/B6 y verificar que llega alerta automática.

**Estado:** ⏳ pendiente validación + captura

---

### 3. L3 — AVISO-DETERMINISTA: validar en vivo para B5/B6
CA-F4-02 marcado como ⚠️ en LIMITACIONES.md.
El predictor (predictor.py) tiene lógica de pre-alerta (`TAU_AVISO=-0.35`, `AVISO_MIN_FL=10`).
Se activa cuando la media de scores de una IP baja de TAU_AVISO antes del BLOCK.

**Escenario para demostrar:**
- Escenario B5 (acceso_repetitivo: curl bucle lento → :80)
- Escenario B6 (bruteforce: hydra → :22)
- Verificar en predictor.log que aparece `pre-alerta` o `AVISO-DET` antes del BLOCK

**Estado:** ⏳ pendiente corrida en vivo + log evidence

---

## 🟡 MEDIO — Importante pero menos atacable

### 4. FPR=20.47% — argumentación oral
Ya documentado en LIMITACIONES.md. No requiere implementación.

**Argumento de memoria:**
> "FPR=20.47% a τ1 es una decisión de diseño deliberada. Bajar el umbral reduciría FPR
> pero haría escapar SYN Floods cuyo score cae alrededor de −0.49. La whitelist de IPs
> confiables mitiga los falsos positivos en el entorno operacional."

**Estado:** ✅ documentado — solo ensayar

---

### 5. L8 — Whitelist externa: demostrar que Desktop no se bloquea
Motor lee `config/whitelist.conf`. IPs en whitelist: 192.168.0.20 (Desktop), 192.168.0.110, 192.168.0.120, etc.

**Validar:**
```bash
# En las estadísticas del motor, verificar campo 'whitelist' sube cuando Desktop genera tráfico
ssh m4rk@192.168.0.110 "grep 'whitelist' results/motor_decision.log | tail -3"
# Debe mostrar: whitelist=NNNN (incrementando con tráfico del Desktop)
```

**Estado:** ✅ funciona (visto en log: `whitelist=26319`) — falta captura explícita

---

## 🟢 BAJO — Ya resuelto, solo pulir

### 6. L4 — Monitor kernel_drops Suricata
Evidencia ya existe en log de hoy: `06:36 ALERTA saturacion kernel_drops=43,538,976`.
Documentado en LIMITACIONES.md.
**Estado:** ✅ evidencia en log — anotar timestamp para PPT

### 7. L5 — Bloqueo progresivo
**Estado:** ✅ COMPLETADO HOY (2026-06-22) — commit 689d7da

### 8. AUC=1.0 XGBoost — argumentación
Documentado en LIMITACIONES.md como L6.
**Estado:** ✅ documentado

### 9. Informe de resultados escrito
Pendiente de iniciar. Después de completar PPT y capturas.
**Estado:** ⏳ pendiente — baja prioridad ahora

---

## Orden de ejecución sugerido

1. **Telegram test** → 10 min → captura en teléfono ← SIGUIENTE
2. **L3 AVISO-DET** → corrida B5 o B6 → captura predictor.log
3. **Capturas PPT** → corrida B1 corta → 5 capturas de pantalla
4. **L8 whitelist** → 2 min → grep en log
5. **Informe escrito** → sesión dedicada posterior
