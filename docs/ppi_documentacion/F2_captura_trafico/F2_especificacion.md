# F2 — Especificación Técnica: Captura de Tráfico por Grupos

## 1. Objetivo

Capturar tráfico de red en **tres grupos con propósito único** (normal puro, anómalo puro,
mixto controlado) usando Suricata 7.0.3. Cada grupo produce archivos `.gz` que son la
fuente directa para F3. No hay procesamiento intermedio en F2 — los `.gz` se leen
directamente en F3 por `fase3_entrenar.py` y `fase3_evaluar.py`.

> **Corrección metodológica:** el flujo anterior generaba `train/val/test.csv` con una
> partición 70/15/15 heredada de pipelines supervisados. Isolation Forest es no supervisado
> — no necesita etiquetas ni partición de validación. Esos archivos fueron **eliminados**.
> Ver: `docs/METODOLOGIA_PIPELINE_COMPARATIVA.md`

---

## 2. Entradas

| Entrada | Descripción |
|---|---|
| Topología operativa (F1) | Suricata activo en ens35, SSH keys listas, motor detenido |
| `/var/log/suricata/eve.json` | Log EVE JSON en tiempo real — se comprime y rota al final de cada escenario |
| `scripts_f2/grupoA/run_grupo_A.sh` | Orquestador de escenarios normales (Desktop) |
| `scripts_f2/grupoB/run_grupo_B.sh` | Orquestador de escenarios anómalos (Kali) |
| `scripts_f2/grupoC/run_grupo_C.sh` | Orquestador de escenarios mixtos (Desktop + Kali) |
| Kali Linux 192.168.0.100 | Herramientas de ataque: hping3, nmap, hydra, sshpass |

**Requisito crítico:** `ppi-motor.service` debe estar **DETENIDO** en toda la F2.
El motor filtraría paquetes de Kali antes de que Suricata los registre.

---

## 3. Salidas

| Salida | Ruta (sensor) | Descripción |
|---|---|---|
| Capturas Grupo A | `data/raw/*_normal_*.eve.json.gz` | 28 archivos — tráfico normal puro |
| Capturas Grupo B | `data/raw/*_anom_*.eve.json.gz` | 13 archivos — ataques puros |
| Capturas Grupo C | `data/raw/*_mixto_*.eve.json.gz` | 6 archivos — tráfico mixto |
| Bitácora | `docs/bitacora/bitacora_escenarios.txt` | 64 líneas — registro de cada corrida |

Los archivos `.gz` son la **única salida de F2**. No se generan CSVs intermedios.
F3 lee estos archivos directamente con `gzip.open()`.

---

## 4. Por qué tres grupos separados

| Grupo | Condición de captura | Propósito |
|---|---|---|
| **A — Normal puro** | Kali **apagada** o inaccesible | Entrenar IF + generar holdout de referencia (F3) |
| **B — Ataque puro** | Desktop **sin tráfico**, motor **detenido** | Calcular curva ROC, derivar τ1/τ2 (F3) |
| **C — Mixto controlado** | Ambos activos, motor **detenido** | Validar AUC en condiciones reales por escenario (F3) |

Si se capturara en una sola sesión (como en el flujo anterior), los flows normales del
Desktop ocurrirían bajo condiciones de red alteradas por los ataques de Kali (RST packets,
saturación de colas), contaminando los datos de entrenamiento del IF.

---

## 5. Escenarios del Grupo A — Tráfico normal

Origen: Desktop 192.168.0.20 → Server 192.168.0.120. Kali **apagada**.

| ID | Nombre | Herramienta | Puerto | Duración |
|---|---|---|---|---|
| A1 | http_normal | `curl` en bucle → nginx | TCP/80 | 10 min |
| A2 | ssh_legitimo | `ssh` sesión interactiva | TCP/22 | 8 min |
| A3 | transferencia_legitima | `scp` / `wget` archivos | TCP/22, TCP/80 | 10 min |
| A4 | trafico_sostenido | curl + ssh mixto continuo | TCP/80, TCP/22 | 15 min |

---

## 6. Escenarios del Grupo B — Tráfico anómalo

Origen: Kali 192.168.0.100 → Server 192.168.0.120. Desktop **quieto**.

| ID | Nombre | Herramienta | Flags | Puerto | Duración |
|---|---|---|---|---|---|
| B1 | syn_flood | `hping3 -S --flood` | SYN sin completar handshake | TCP/80 | 10 min |
| B2 | port_scan | `nmap -sS -p 1-1024` en bucle | SYN scan sigiloso | 1–1024 | 10 min |
| B3 | udp_flood | `hping3 --udp --flood -p 53` | UDP masivo | UDP/53 | 10 min |
| B4 | icmp_flood | `hping3 -1 --flood` | ICMP echo masivo | ICMP | 10 min |
| B5 | http_abuse | `curl` bucle agresivo | HTTP GET repetitivo | TCP/80 | 10 min |
| B6 | bruteforce | `hydra -l root -P wordlist ssh://` | Intentos masivos | TCP/22 | 10 min |

---

## 7. Escenarios del Grupo C — Tráfico mixto

Desktop + Kali simultáneos. Motor **detenido** para capturar todos los flows.

| ID | Nombre | Desktop (normal) | Kali (anómalo) | Duración |
|---|---|---|---|---|
| C1 | http_synflood | curl → nginx :80 | hping3 -S --flood → :80 | 10 min |
| C2 | ssh_portscan | ssh → :22 | nmap -sS -p 1-1024 | 10 min |
| C3 | transfer_udpflood | scp/wget | hping3 --udp --flood → :53 | 10 min |

---

## 8. Nomenclatura de archivos

```
YYYYMMDD_grupo_escenario_NN_eve.json.gz

Ejemplos reales:
  20260602_normal_http_01_eve.json.gz          ← Grupo A, 02-jun, corrida 01
  20260615_anom_synflood_01_eve.json.gz        ← Grupo B, 15-jun
  20260616_mixto_http_synflood_01_eve.json.gz  ← Grupo C, 16-jun

Globs usados en F3 (date-agnostic — funcionan en cualquier fecha):
  *_normal_*.gz    ← todos los del Grupo A
  *_anom_*.gz      ← todos los del Grupo B
  *_mixto_*.gz     ← todos los del Grupo C
```

---

## 9. Scripts de automatización

### 9.1 `run_grupo_A.sh` / `run_grupo_B.sh` / `run_grupo_C.sh`

Orquestadores que ejecutan los escenarios de cada grupo en orden. Hacen:

1. Verifican conectividad (sensor, servidor, Kali si aplica)
2. Verifican que `ppi-motor.service` esté detenido
3. Ejecutan los sub-scripts de cada escenario (A1–A4, B1–B6, C1–C3)
4. Esperan `≥ 120 s` entre escenarios (pausa para que Suricata cierre los flows TCP abiertos)

```bash
# Ejemplo de uso — desde Desktop (192.168.0.20)
bash scripts_f2/grupoA/run_grupo_A.sh 01   # corrida 01
bash scripts_f2/grupoB/run_grupo_B.sh 01   # corrida 01
bash scripts_f2/grupoC/run_grupo_C.sh 01   # corrida 01
```

### 9.2 `scripts/capture/exportar_eve_por_escenario.sh`

Ejecutado vía SSH al final de **cada escenario individual**:

```bash
# Llamado automáticamente desde A1.sh, B1.sh, etc.
ssh m4rk@192.168.0.110 "bash exportar_eve_por_escenario.sh FECHA GRUPO ESCENARIO CORRIDA"
```

Proceso interno:
1. `gzip -c /var/log/suricata/eve.json > data/raw/YYYYMMDD_*.gz`
2. `truncate -s 0 /var/log/suricata/eve.json` — vacía para la siguiente captura
3. `suricatasc -c reopen-log-files` — Suricata reabre el handle del archivo

### 9.3 `scripts/evaluation/registrar_bitacora.sh`

Agrega una línea al final de `docs/bitacora/bitacora_escenarios.txt`:

```
2026-06-15 | anom | synflood | 192.168.0.100 -> 192.168.0.120 | 21:44:57 - 21:55:02 | hping3 | 20260615_anom_synflood_01_eve.json.gz
```

---

## 10. Secuencia técnica completa F2

```bash
# ── PRE-REQUISITO ──────────────────────────────────────────────────────────
# Detener motor en sensor
ssh m4rk@192.168.0.110 "sudo systemctl stop ppi-motor.service"

# ── GRUPO A — tráfico normal (~43 min + pausas) ────────────────────────────
# Kali debe estar apagada o inaccesible
bash /home/m4rk/Descargas/scripts_f2/grupoA/run_grupo_A.sh 01

# Pausa mínima entre grupos (flows TCP deben cerrarse)
sleep 120

# ── GRUPO B — tráfico anómalo (~63 min + pausas) ───────────────────────────
# Desktop: NO generar tráfico hacia el servidor
bash /home/m4rk/Descargas/scripts_f2/grupoB/run_grupo_B.sh 01

sleep 120

# ── GRUPO C — tráfico mixto (~34 min + pausas) ─────────────────────────────
# Motor DETENIDO (ya está detenido desde el inicio de F2)
bash /home/m4rk/Descargas/scripts_f2/grupoC/run_grupo_C.sh 01

# ── VERIFICACIÓN ────────────────────────────────────────────────────────────
# Contar archivos por grupo
ssh m4rk@192.168.0.110 "
  echo 'Grupo A:' \$(ls data/raw/*_normal_*.gz 2>/dev/null | wc -l) archivos
  echo 'Grupo B:' \$(ls data/raw/*_anom_*.gz   2>/dev/null | wc -l) archivos
  echo 'Grupo C:' \$(ls data/raw/*_mixto_*.gz  2>/dev/null | wc -l) archivos
  echo 'Bitacora:' \$(wc -l < docs/bitacora/bitacora_escenarios.txt) lineas
"
```

---

## 11. Volumen de datos capturados

| Grupo | Archivos | Tamaño comprimido | Contenido |
|---|---|---|---|
| Grupo A (normal) | 28 `.gz` | ~15 MB | Flows normales — curl, ssh, scp, wget |
| Grupo B (anómalo) | 13 `.gz` | ~2.5 GB | Floods y scans — B1-B6 |
| Grupo C (mixto) | 6 `.gz` | ~800 MB | Normal + ataque simultáneos |
| **Total** | **47 archivos** | **~4.3 GB** | Fuente directa para F3 |

---

## 12. Criterios de éxito (salida de F2)

| Criterio | Verificación | Resultado esperado |
|---|---|---|
| Archivos Grupo A generados | `ls data/raw/*_normal_*.gz \| wc -l` | ≥ 4 archivos |
| Archivos Grupo B generados | `ls data/raw/*_anom_*.gz \| wc -l` | ≥ 6 archivos |
| Archivos Grupo C generados | `ls data/raw/*_mixto_*.gz \| wc -l` | ≥ 3 archivos |
| Bitácora registrada | `wc -l docs/bitacora/bitacora_escenarios.txt` | ≥ 64 líneas |
| Motor sigue detenido | `systemctl is-active ppi-motor.service` | `inactive` |
| NO existen CSVs intermedios | `ls data/dataset_*.csv 2>/dev/null` | Sin resultado |

**F2 se considera COMPLETADA** cuando existen los 47 archivos `.gz` en `data/raw/`
y la bitácora tiene 64 entradas. No se genera ningún CSV — F3 lee los `.gz` directamente.
