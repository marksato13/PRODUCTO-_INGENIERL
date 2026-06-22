# V5 — Validación End-to-End: Escenarios de Integración (F6)

**Criterios:** CA-13, CA-14, CA-15  
**Tiempo estimado:** 20-40 minutos por corrida  
**Requiere:** Motor activo, Kali disponible, Desktop disponible

---

## Qué se valida

Prueba el sistema completo de extremo a extremo: desde la generación de tráfico real hasta la decisión del motor, el enforcement en ipset, la predicción del XGBoost y las notificaciones (Telegram + Dashboard). Esta validación corresponde a la Fase 6 del PPI.

---

## Criterios de aceptación

| CA    | Qué mide                             | Criterio PASS | Valor validado (2026-06-22) | PASS/FAIL |
|-------|--------------------------------------|---------------|-----------------------------|-----------|
| CA-13 | Lead time B1 SYN Flood → primer BLOCK| ≤ 120s        | ~62s                        | ✅ PASS   |
| CA-14 | Lead time B6 BF SSH → primer BLOCK   | ≤ 90s         | ~60s                        | ✅ PASS   |
| CA-15 | Disponibilidad 40 corridas F6        | 100%          | 100% (40/40)                | ✅ PASS   |

---

## Escenarios del F6 (ya ejecutados)

### Grupo A — Tráfico Normal (desde Desktop 192.168.0.20)
| ID | Escenario            | Duración | Herramienta         | Resultado esperado       |
|----|----------------------|----------|---------------------|--------------------------|
| A1 | HTTP normal          | 10 min   | curl/wget → :80     | Solo PERMIT (whitelist)  |
| A2 | SSH legítimo         | 8 min    | ssh → :22           | Solo PERMIT (whitelist)  |
| A3 | Transferencia        | 10 min   | scp/wget            | Solo PERMIT (whitelist)  |
| A4 | Tráfico sostenido    | 15 min   | curl+ssh mixto      | Solo PERMIT (whitelist)  |

### Grupo B — Tráfico Anómalo (desde Kali 192.168.0.100)
| ID | Escenario       | Herramienta                        | CA validado |
|----|------------------|------------------------------------|-------------|
| B1 | SYN Flood        | `hping3 -S --flood 192.168.0.120`  | Lead ≤ 120s |
| B2 | Port Scan        | `nmap -sS 192.168.0.120`           | BLOCK en < 30s |
| B3 | UDP Flood        | `hping3 --udp --flood -p 53`       | BLOCK rápido |
| B4 | ICMP Flood       | `hping3 -1 --flood`                | BLOCK en < 60s |
| B5 | HTTP Abusivo     | `curl` en bucle rápido → :80       | LIMIT → BLOCK |
| B6 | Brute Force SSH  | `hydra -t 4 -l root -P pass.txt`   | Lead ≤ 90s  |

### Grupo C — Mixto (Desktop + Kali simultáneos)
| ID | Escenario        | Descripción                        | Resultado esperado |
|----|------------------|------------------------------------|--------------------|
| C1 | HTTP + SYN       | Desktop HTTP normal + Kali SYN     | Kali BLOCK, Desktop PERMIT |
| C2 | SSH + Port Scan  | Desktop SSH legítimo + Kali nmap   | Kali BLOCK, Desktop PERMIT |
| C3 | Descarga + UDP   | Desktop wget + Kali UDP flood      | Kali BLOCK, Desktop PERMIT |

---

## Prueba de lead time B1 (SYN Flood) — paso a paso

```bash
# 1. En Desktop: asegurar motor activo
ssh m4rk@192.168.0.110 "sudo systemctl status ppi-motor.service"

# 2. Anotar hora de inicio
INICIO=$(date +%T); echo "Inicio: $INICIO"

# 3. En Kali: iniciar SYN flood
ssh m4rk@192.168.0.100 "sudo hping3 -S --flood -p 80 192.168.0.120"

# 4. En Desktop: monitorear log hasta primer BLOCK de Kali
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log" \
  | grep --line-buffered "BLOCK.*192.168.0.100"
# Anotar timestamp del primer BLOCK → lead time = timestamp - INICIO

# 5. Detener en Kali (Ctrl+C en la sesión SSH)
# 6. Lead time esperado: ≤ 62 segundos
```

---

## Prueba de lead time B6 (Brute Force SSH) — paso a paso

```bash
# 1. En Desktop: monitorear log
ssh m4rk@192.168.0.110 "tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log" &

# 2. Anotar hora
INICIO=$(date +%T); echo "Inicio BF SSH: $INICIO"

# 3. En Kali: iniciar hydra
ssh m4rk@192.168.0.100 "hydra -t 4 -l root -P /usr/share/wordlists/rockyou.txt ssh://192.168.0.120"

# 4. Secuencia esperada en el log:
# T+53s: LIMIT 192.168.0.100  reason=BRUTE_FORCE_SSH_warn  score=-0.4832
# T+60s: BLOCK 192.168.0.100  reason=BRUTE_FORCE_SSH       score=-0.6228
```

---

## Prueba de escenario mixto C1 (verificar no hay falsos positivos en Desktop)

```bash
# 1. Iniciar Desktop generando tráfico normal
for i in $(seq 1 20); do curl -s http://192.168.0.120:80 > /dev/null; sleep 3; done &

# 2. Desde Kali: SYN flood simultáneo
ssh m4rk@192.168.0.100 "sudo hping3 -S --flood -p 80 192.168.0.120" &

# 3. Verificar que Desktop NUNCA aparece en log como LIMIT o BLOCK
ssh m4rk@192.168.0.110 "grep 'LIMIT\|BLOCK' /home/m4rk/ppi-surikata-producto/results/motor_decision.log \
  | grep 192.168.0.20"
# Resultado esperado: vacío (whitelist protege al Desktop)
```

---

## Cómo consultar las 40 corridas F6 ya validadas

```bash
cat /home/m4rk/ppi-surikata-producto/results/resultados_f6_completo.csv
# Columnas: corrida, grupo, escenario, fecha, hora, AUC, TPR, FPR, decisiones, lead_time
```

```bash
# Ver bitácora completa con timestamps
cat /home/m4rk/ppi-surikata-producto/docs/bitacora/bitacora_escenarios.txt
```

---

## Resultados F6 resumen

- **40 corridas completadas** (A1×4 + A2×4 + A3×4 + A4×4 + B1×4 + B2×4 + B3×4 + B4×4 + B5×4 + B6×4)
- **Disponibilidad**: 100% (ninguna corrida falló por fallo del sistema)
- **ITL**: 0% en todas las corridas
- **Lead time SYN Flood**: ≈ 62s promedio (CA-13 ✅)
- **Lead time BF SSH**: ≈ 60s (CA-14 ✅)
