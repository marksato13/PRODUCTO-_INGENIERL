# F3-ipset — Validación del Control Inline (enforcement en SERVIDOR 192.168.0.120)

**Criterios:** CA-8, CA-9, CA-10  
**Tiempo estimado:** 5-10 minutos  
**Requiere:** ipset activo en **servidor 192.168.0.120**, acceso SSH a Kali (192.168.0.100)

---

## Qué se valida

El módulo de enforcement (`enforce.sh` + ipset) ejecuta las decisiones del motor en la red real.
> ⚠️ **ipset/iptables corre en el SERVIDOR (192.168.0.120)**, no en el sensor. El motor hace SSH al servidor para añadir IPs.
- **ppi_blocked**: IPs con DROP total (iptables -j DROP) — en servidor
- **ppi_limited**: IPs con hashlimit 100pkt/s — en servidor
- **Whitelist**: IPs nunca bloqueadas independientemente del score

---

## Criterios de aceptación

| CA    | Qué mide                                          | Criterio PASS              | PASS/FAIL |
|-------|---------------------------------------------------|----------------------------|-----------|
| CA-8  | Desktop (192.168.0.20) nunca en ppi_blocked       | 0 entradas                 | ✅ PASS   |
| CA-9  | IP atacante bloqueada no alcanza servidor         | curl timeout / connection refused | Verificar |
| CA-10 | Bloqueo progresivo #3 tiene timeout=0 (PERMANENTE)| timeout = 0 en ipset list  | ✅ PASS   |

---

## Prueba CA-8: Whitelist nunca bloqueada

```bash
# En el SERVIDOR (192.168.0.120) — donde corre ipset
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked" | grep -E "192.168.0.20|192.168.0.110|192.168.0.120|192.168.0.1 |127.0.0.1"
# Resultado esperado: vacío (ninguna de estas IPs debe aparecer)
# O verificar via block_counts.json en sensor:
cat /home/m4rk/ppi-surikata-producto/results/block_counts.json
```

IPs en whitelist del sistema:
- `192.168.0.1` — gateway
- `192.168.0.20` — Desktop (Admin)
- `192.168.0.110` — Sensor (propio)
- `192.168.0.120` — Servidor (objetivo)
- `192.168.0.130`, `192.168.0.140` — reservadas
- `127.0.0.1` — loopback

---

## Prueba CA-9: Bloqueo efectivo de IP atacante

**Paso 1** — Bloquear manualmente la IP de Kali:
```bash
# Desde Desktop — enforce.sh hace SSH al servidor automáticamente
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK 120
# Resultado esperado: "BLOCK aplicado a 192.168.0.100 (timeout=120s)"
# (enforce.sh SSHea a 192.168.0.120 y ejecuta sudo ipset add ppi_blocked)
```

**Paso 2** — Verificar que está en ipset del servidor:
```bash
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 192.168.0.100"
# Esperado: 192.168.0.100 timeout 119 (contando hacia 0)
```

**Paso 3** — Intentar acceder al servidor desde Kali:
```bash
# En Kali (192.168.0.100) — SSH desde Desktop
ssh m4rk@192.168.0.100 "curl -s --max-time 5 http://192.168.0.120:80"
# Resultado esperado: curl: (28) Operation timed out  o  connection refused
```

**Paso 4** — Desbloquear:
```bash
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 UNBLOCK
```

---

## Prueba CA-10: Bloqueo progresivo hasta PERMANENTE

El sistema escala automáticamente con cada nuevo bloqueo de la misma IP:
- Bloqueo #1 → timeout = 300s (5 min)
- Bloqueo #2 → timeout = 1800s (30 min)
- Bloqueo #3+ → timeout = 0 (PERMANENTE)

**Verificar el estado actual de block_counts.json:**
```bash
cat /home/m4rk/ppi-surikata-producto/results/block_counts.json
# Buscar IPs con count >= 3 → deben tener timeout=0 en ipset
```

**Verificar en ipset:**
```bash
# Verificar en el SERVIDOR:
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked"
# IPs con "timeout 0" = permanentes
# IPs con "timeout NNN" = temporales
```

**Simular escalada completa (solo en entorno de laboratorio):**
```bash
# Forzar 3 ciclos de bloqueo en Kali para ver la escalada
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK  # #1 → 300s
# Esperar que expire
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK  # #2 → 1800s
# Esperar que expire (o resetear block_counts.json para prueba rápida)
bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh 192.168.0.100 BLOCK  # #3 → timeout=0
ssh m4rk@192.168.0.120 "sudo ipset list ppi_blocked | grep 192.168.0.100"
# Esperado: 192.168.0.100  (sin timeout = PERMANENTE)
```

---

## Estado actual verificado (2026-06-22)

Evidencia de bloqueo progresivo validado en producción:
```
05:44:13  BLOCK #1  192.168.0.100  timeout=300s
06:05:03  BLOCK #2  192.168.0.100  timeout=1800s
06:39:42  BLOCK #3  192.168.0.100  timeout=0 (PERMANENTE)
```
