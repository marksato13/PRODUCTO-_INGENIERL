# Checklist de Pendientes — Defensa PPI
**Actualizado:** 2026-06-22 07:40 | **Sesión de validación en vivo completada**

---

## Resumen de lo completado hoy (2026-06-22)

| Item | Estado | Evidencia |
|---|---|---|
| L5 bloqueo progresivo #1 (300s) | ✅ VALIDADO | motor_decision.log 05:44:13 |
| L5 bloqueo progresivo #2 (1800s) | ✅ VALIDADO | motor_decision.log 06:05:03 |
| L5 bloqueo progresivo #3 (PERMANENTE) | ✅ VALIDADO | motor_decision.log 06:39:42, ipset timeout=0 |
| L9 Telegram alerta BLOCK en vivo | ✅ VALIDADO | Alerta recibida 07:25:19, HTTP 200 ✅ |
| L4 Monitor kernel_drops | ✅ EVIDENCIA EN LOG | WARNING 05:55:30 kernel_drops=43.5M |
| L1 Whitelist FPR operativo=0% | ✅ EVIDENCIA EN LOG | stats whitelist=26000+ flows |
| LIMITACIONES.md actualizado con tabla L5 | ✅ | commit 689d7da |
| ppt_sustentacion.md pusheado | ✅ | commit c74076d |
| checklist_defensa.md creado | ✅ | commit 36ec2e8 |

---

## 🔴 CRÍTICO — Pendiente

### 1. Capturas de pantalla para el PPT (5 capturas)
Sin estas el Slide 11 (demo bloqueo progresivo) y Slide 12 (dashboard) quedan vacíos.

| Captura | Qué mostrar | Cómo obtener |
|---|---|---|
| A. Terminal motor_decision.log | 3 líneas bloqueo#1/2/3 juntas | `grep 'bloqueo#[123]' results/motor_decision.log \| grep '05:44\|06:05\|06:39'` |
| B. `ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"` con timeout=0 | Kali bloqueada permanente en servidor | Repetir corrida B1 hasta bloqueo#3 |
| C. Dashboard web con alertas activas | http://192.168.0.110:8080 | Abrir navegador durante corrida |
| D. Telegram alerta en teléfono | Mensaje "🚨 PPI ALERTA — BLOCK" | Ya recibida 07:25 — tomar captura del historial |
| E. `cat block_counts.json` = `{"192.168.0.100": 3}` | Historial persistido | Repetir hasta bloqueo#3 |

**Estado:** ❌ pendiente tomar screenshots

---

### 2. L2 — Lead time heurístico SSH <5s — verificar en vivo
LIMITACIONES.md dice "<5s" para BF SSH pero no hay timestamp que lo confirme.

**Cómo validar:**
```bash
# En Kali:
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.120 -t 4 -f 2>&1 &
# En sensor — medir tiempo entre primer intento y BLOCK en log:
tail -f results/motor_decision.log | grep -E 'BF-SSH|BLOCK'
```
**Estado:** ❌ pendiente corrida B6 + medición de tiempo

---

## 🟡 MEDIO — Pendiente

### 3. L3 — AVISO-DETERMINISTA: demostración
El código existe en `motor_decision.py` líneas 580-598. En vivo NO se puede disparar con Kali porque los flows residuales del flood ya puntúan < τ2 → BLOCK directo antes de acumular 10 flows PERMIT.

**Para la defensa — usar argumento de código:**
```
"El AVISO-DETERMINISTA está implementado en motor_decision.py (línea 580).
Dispara alerta Telegram '👀 PPI AVISO — TENDENCIA ANÓMALA' cuando la IP
acumula 10 flows con score medio < -0.35 pero aún en zona PERMIT.
La limitación CA-F4-02 (documentada) es que tráfico de flood contamina
el historial, llevando a BLOCK antes de completar los 10 flows."
```
También: regla determinista en `predictor.py` — `limit_count_15s >= 5` → AVISO sin esperar XGBoost.

**Estado:** ✅ código implementado | ❌ no demostrable en vivo | ✅ documentado en LIMITACIONES.md

---

### 4. L8 — Whitelist externa: verificar lectura de config/whitelist.conf
El motor lee `config/whitelist.conf`. Verificar que Desktop (192.168.0.20) aparece en stats como `whitelist` y NO como anomalía.

```bash
grep 'whitelist' results/motor_decision.log | tail -5
# Debe mostrar whitelist=NNNN incrementando
```
**Estado:** ✅ funcionando (whitelist=26000+ visto en log) | ❌ falta captura explícita

---

## 🟢 BAJO — Ya resuelto

| Item | Estado |
|---|---|
| L4 kernel_drops monitor | ✅ evidencia en log hoy |
| L5 bloqueo progresivo | ✅ validado en vivo + documentado |
| L6 AUC=1.0 argumentado | ✅ LIMITACIONES.md |
| L7 Lab cerrado / F5 reentrenamiento | ✅ documentado |
| L9 Telegram directo | ✅ HTTP 200 + alerta recibida |
| L10 Dashboard systemd | ✅ active + enabled |

---

## Orden de ejecución sugerido (sesión siguiente)

1. **Capturas PPT** — Slide 11 y 12 → lanzar corrida B1, tomar 5 screenshots
2. **L2 lead time B6** → corrida hydra SSH, medir segundos hasta BLOCK
3. **Informe de resultados** → sesión dedicada posterior
