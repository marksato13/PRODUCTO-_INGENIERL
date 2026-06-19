# Limitaciones Detalladas del Sistema

**PPI — Universidad Peruana Unión | Rubén Mark Salazar Tocas**

Este documento analiza en profundidad cada limitación conocida del sistema, su origen técnico, su impacto real y las estrategias de mitigación aplicadas o propuestas.

---

## 1. Tasa de Falsos Positivos (FPR = 20.47 % @ τ1)

**Qué significa:** 1 de cada 5 flows de tráfico legítimo recibe un score de anomalía por debajo de τ1. Si el motor actuara sobre τ1 sin whitelist, el 20.47 % del tráfico normal recibiría una decisión LIMIT o BLOCK incorrecta.

**Origen técnico:**
- Isolation Forest es un algoritmo no supervisado: aprende la estructura del tráfico normal pero no tiene noción de "qué es un ataque". Define anomalía como "aislamiento fácil en el árbol", lo que penaliza flows con features inusuales aunque sean legítimos.
- El tráfico de `scp` y transferencias grandes genera `byte_rate` y `pkt_rate` elevados que el modelo interpreta como anómalos.
- El umbral τ1 se derivó maximizando TPR − FPR (índice de Youden): prioriza no perder ataques sobre evitar falsas alarmas.

**Impacto real en el laboratorio:**
- La whitelist de IPs internas (192.168.0.20, 192.168.0.110, 192.168.0.120) cubre todos los orígenes de tráfico legítimo del laboratorio → ITL efectivo = 0%.
- En una red universitaria real con cientos de IPs de usuarios, la whitelist no escalaría sin gestión activa.

**Mitigaciones aplicadas:**
- Whitelist estática en `ipset ppi_whitelist` — IPs internas nunca bloqueadas.
- El umbral τ2 (FPR = 1.99 %) se usa para BLOCK; τ1 solo activa LIMIT (rate limiting), no bloqueo total.

**Mitigaciones propuestas (trabajo futuro):**
- Ensemble IF + AE (AND gate): reduce FPR teórico en ~49 % sin cambiar τ.
- Whitelist dinámica basada en historial de comportamiento.
- Supervisión humana de alertas LIMIT antes de escalar a BLOCK.

---

## 2. Lead Time de Detección ~62 s

**Qué significa:** desde que comienza un ataque SYN flood hasta que el motor emite la primera decisión BLOCK transcurren ~62 segundos. Durante ese período el servidor objetivo recibe el ataque sin control activo.

**Origen técnico:**
- Suricata cierra un flow TCP solo cuando detecta FIN/RST o cuando expira el timeout de inactividad.
- En un SYN flood los paquetes SYN nunca completan el handshake → Suricata acumula el flow durante su ventana de timeout antes de cerrarlo y escribirlo en `eve.json`.
- El motor solo procesa flows cerrados (evento `netflow` en `eve.json`), no paquetes individuales.

**Impacto real:**
- 62 s de exposición en SYN flood → el servidor puede quedar sin recursos en ataques intensos.
- Para brute force SSH y HTTP abuse el impacto es menor porque los detectores heurísticos actúan sobre eventos individuales (no esperan cierre de flow): detección en < 5 s.

**Mitigaciones aplicadas:**
- Detectores heurísticos independientes del score IF para SSH (15 intentos/60s) y HTTP (100 req/30s).
- La whitelist garantiza que el tráfico legítimo no se ve afectado durante los 62 s de espera.

**Mitigaciones propuestas:**
- Integrar procesamiento de `alert` events de Suricata (en tiempo real, por paquete) para reducir el lead time a < 5 s en todos los escenarios.
- Ajustar los timeouts de Suricata para cerrar flows incompletos más rápido.

---

## 3. Modelo Estático (Sin Reentrenamiento Automático)

**Qué significa:** el modelo IF fue entrenado en junio 2026 sobre flows del laboratorio. No se actualiza automáticamente cuando cambian los patrones de tráfico.

**Origen técnico:**
- El pipeline de F3 es batch: requiere ejecutar manualmente `fase3_entrenar.py` + `fase3_evaluar.py` + reinicio del motor.
- No existe mecanismo de detección de deriva de distribución (concept drift).

**Impacto real:**
- Si la red incorpora nuevas aplicaciones (VoIP, streaming, videoconferencias) con patrones distintos al tráfico HTTP/SSH del laboratorio, el FPR podría aumentar.
- Nuevos tipos de ataque no representados en Grupo B podrían no ser detectados.

**Mitigaciones aplicadas:**
- El modelo fue entrenado con la versión 1.9.0 de sklearn fijada en el venv → sin mismatch de versiones al reentrenar.
- El procedimiento de reentrenamiento está documentado paso a paso en `F3_especificacion.md §14`.

**Mitigaciones propuestas:**
- Programar reentrenamiento mensual automático con nuevas capturas de tráfico normal.
- Implementar monitoreo de deriva: alertar si el FPR observado supera el 25 % en producción.

---

## 4. Entorno de Laboratorio (No Red Universitaria Real)

**Qué significa:** todo el tráfico fue generado de forma controlada entre 5 VMs. Los resultados pueden no generalizarse exactamente a una red universitaria real con cientos de usuarios y patrones de tráfico heterogéneos.

**Origen técnico:**
- Restricción inherente al PPI: no se contaba con autorización para desplegar el sistema en la red de producción de la universidad durante el desarrollo.
- El Grupo A cubre solo 4 tipos de tráfico normal (HTTP, SSH, SCP, mixto) cuando en una red real existen decenas de patrones distintos.

**Impacto real:**
- El modelo podría tener FPR más alto en red real (más variedad de tráfico legítimo).
- Los umbrales τ1/τ2 pueden necesitar recalibración para la red destino.

**Mitigaciones aplicadas:**
- Los escenarios del Grupo A cubren los protocolos dominantes en redes universitarias LAN (HTTP y SSH representan > 95 % del tráfico tipico).
- La whitelist mitiga el riesgo de bloquear usuarios mientras el modelo se recalibra.

**Mitigaciones propuestas:**
- Fase de observación: desplegar el motor en modo `monitor` (sin aplicar bloqueos) durante 2 semanas en red real para recalibrar τ antes de activar control inline.

---

## 5. Dependencia de Suricata como Único Punto de Captura

**Qué significa:** si Suricata se detiene, el motor deja de recibir flows y no puede tomar decisiones de control. El sistema no tiene redundancia en la capa de captura.

**Origen técnico:**
- El motor hace `tail -f eve.json` — si Suricata para de escribir, el motor queda esperando indefinidamente sin emitir alertas.
- No existe un watchdog que detecte la ausencia de flows y genere una alarma.

**Impacto real en el laboratorio:**
- Disponibilidad medida: 100 % en 40 corridas → Suricata fue estable durante toda la validación.
- En producción prolongada, actualizaciones del kernel o del SO podrían detener Suricata.

**Mitigaciones aplicadas:**
- `ppi-motor.service` tiene `Restart=on-failure` → se reinicia si falla el proceso Python.
- Suricata corre como servicio systemd con `Restart=always`.

**Mitigaciones propuestas:**
- Watchdog en el motor: si no llega ningún flow en X segundos, enviar alerta y registrar en log.
- Monitoreo externo (Nagios/Zabbix) del proceso `suricata` y del tamaño de `eve.json`.

---

## 6. Cobertura Limitada de Tipos de Ataque

**Qué significa:** el modelo fue entrenado y validado con 6 tipos de ataque del Grupo B. Ataques no representados (exfiltración lenta, ataques cifrados, lateral movement) pueden no ser detectados.

**Escenarios cubiertos:** SYN flood, port scan, UDP flood, ICMP flood, HTTP abuse, brute force SSH.

**Escenarios NO cubiertos:**
- Exfiltración de datos (tráfico de salida elevado pero lento)
- Ataques sobre HTTPS (tráfico cifrado — Suricata no inspecciona payload)
- Lateral movement (tráfico entre IPs internas)
- Ataques de día cero con patrones de tráfico similares al tráfico normal

**Mitigaciones aplicadas:**
- El modelo IF es no supervisado: puede detectar anomalías de patrones no vistos durante el entrenamiento si alteran las 14 features.
- Los detectores heurísticos (SSH brute force, HTTP abuse) cubren los ataques más frecuentes con lógica directa.

**Mitigaciones propuestas:**
- Ampliar el Grupo B con escenarios de exfiltración y escaneo horizontal.
- Integrar inspección de certificados TLS con Suricata para cobertura parcial de HTTPS.

---

## Resumen de Limitaciones

| # | Limitación | Severidad | Mitigación actual | ¿Resuelto en lab? |
|---|---|---|---|---|
| 1 | FPR = 20.47 % @ τ1 | Media | Whitelist + LIMIT (no BLOCK) en τ1 | Sí (ITL=0%) |
| 2 | Lead time ~62 s | Media | Heurísticos SSH/HTTP | Parcial |
| 3 | Modelo estático | Baja | Reentrenamiento manual documentado | Sí |
| 4 | Entorno laboratorio | Baja | Escenarios representativos | Aceptable para PPI |
| 5 | Un solo punto de captura | Baja | Restart automático systemd | Sí |
| 6 | Cobertura de ataques limitada | Media | IF no supervisado + heurísticos | Parcial |

