# F2 — Especificación Técnica: Captura de Tráfico por Grupos

## 1. Objetivo y posición en el pipeline

Capturar tráfico de red en **tres grupos con propósito único y separado** (normal puro,
anómalo puro, mixto controlado) usando Suricata 7.0.3. Cada grupo produce archivos `.gz`
que son la **fuente directa para F3** — sin procesamiento intermedio.

```
POSICIÓN EN EL PIPELINE COMPLETO

F1 (entorno)          F2 (captura)           F3 (modelado)
─────────────  →  ──────────────────  →  ─────────────────────
Suricata activo       Grupo A → .gz         fase3_entrenar.py
SSH keys listas       Grupo B → .gz    →    fase3_evaluar.py
Motor detenido        Grupo C → .gz         auc_por_escenario.py
```

> **Corrección metodológica:** el flujo anterior generaba `train/val/test.csv` con una
> partición 70/15/15 heredada de pipelines supervisados. Isolation Forest es no supervisado
> — no necesita etiquetas ni partición de validación. Esos archivos fueron **eliminados**.
> Ver: `docs/METODOLOGIA_PIPELINE_COMPARATIVA.md`

---

## 2. Terminología clave

### 2.1 EVE JSON (Extensible Event Format)

Suricata escribe `/var/log/suricata/eve.json` como un archivo de **una línea JSON por evento**.
Cada línea tiene un campo `event_type` que indica el tipo:

| `event_type` | Descripción | Usa F2/F3 |
|---|---|---|
| `flow` | Resumen de una conversación de red (bidireccional) cerrada | ✅ SÍ — es la fuente de las 14 features |
| `alert` | Regla de Suricata disparada (IDS) | ❌ NO |
| `http` | Detalles de petición HTTP (URL, método, código) | ❌ NO |
| `ssh` | Metadatos de sesión SSH | ❌ NO |
| `dns` | Consultas/respuestas DNS | ❌ NO |
| `tls` | Handshake TLS | ❌ NO |

**F3 filtra exclusivamente `event_type=flow`** — el resto de eventos se descarta en el parseo.

### 2.2 Registro `event_type=flow` — estructura real

Un flow en Suricata es el **resumen estadístico de una conversación de red** que se emite
cuando la conversación se cierra (por TCP FIN/RST, timeout UDP/ICMP, o timeout global).
Ejemplo real de SYN Flood capturado:

```json
{
  "timestamp": "2026-06-15T21:44:57.123456+0000",
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "src_port": 54321,
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "flow": {
    "pkts_toserver": 1,
    "pkts_toclient": 0,
    "bytes_toserver": 60,
    "bytes_toclient": 0,
    "start": "2026-06-15T21:44:57.100000+0000",
    "end":   "2026-06-15T21:44:57.120000+0000",
    "age": 0,
    "state": "new"
  }
}
```

**Por qué `pkts_toclient=0` en SYN Flood:** el servidor nunca responde SYN-ACK porque
el paquete llega con tasa de flood y el firewall/stack TCP no puede completar el handshake.
Esta asimetría (`pkt_ratio` y `byte_ratio` altos) es la firma detectada por Isolation Forest.

### 2.3 Las 14 features derivadas de cada flow record

| Feature | Derivación desde eve.json | Rango típico normal | Rango ataque SYN |
|---|---|---|---|
| `pkts_toserver` | `flow.pkts_toserver` directo | 3–20 | 1 |
| `pkts_toclient` | `flow.pkts_toclient` directo | 2–18 | 0 |
| `bytes_toserver` | `flow.bytes_toserver` directo | 200–50,000 | 60 |
| `bytes_toclient` | `flow.bytes_toclient` directo | 500–200,000 | 0 |
| `duration` | `(flow.end - flow.start).total_seconds()` | 0.5–60s | ≈0 |
| `pkt_rate` | `(pkts_toserver+pkts_toclient) / max(duration, 0.001)` | 5–50 pkt/s | >1000 pkt/s |
| `byte_rate` | `(bytes_toserver+bytes_toclient) / max(duration, 0.001)` | 500–50K B/s | >10K B/s |
| `pkt_ratio` | `pkts_toserver / (pkts_toclient + 1)` | ≈1 (simétrico) | >>1 (solo envío) |
| `byte_ratio` | `bytes_toserver / (bytes_toclient + 1)` | 0.1–2.0 | >>1 |
| `avg_pkt_size` | `(bytes_toserver+bytes_toclient) / max(pkts_toserver+pkts_toclient, 1)` | 200–1500 B | 60 B |
| `is_tcp` | `1 if proto=="TCP" else 0` | 1 (curl/ssh) | 1 (SYN flood) |
| `is_udp` | `1 if proto=="UDP" else 0` | 0 | 1 (UDP flood) |
| `is_icmp` | `1 if proto=="ICMP" else 0` | 0 | 1 (ICMP flood) |
| `dest_port` | `dest_port` directo (0 para ICMP) | 80 ó 22 | 80, 53, 0 |

Estas features son calculadas por `fase3_entrenar.py` y `fase3_evaluar.py` durante la lectura
de los `.gz`. No se guardan como CSV intermedio — se calculan en memoria para cada flow.

### 2.4 Ciclo gzip → truncate → reopen (rotación de eve.json)

Al final de **cada escenario individual**, `exportar_eve_por_escenario.sh` ejecuta en el sensor:

```
ANTES                        DURANTE EXPORTACIÓN              DESPUÉS
──────────────────────       ─────────────────────────────    ──────────────────────
eve.json: 50MB (escenario)   1. gzip -c eve.json → .gz        eve.json: 0 bytes (vacío)
Suricata: fd abierto            (copia comprimida, sin tocar   .gz: 50MB → ~2MB comprimido
                                el original)                   Suricata: fd reabierto →
                             2. truncate -s 0 eve.json            escribe en archivo limpio
                                (vacía el inode, Suricata
                                 sigue con el fd original)
                             3. suricatasc -c reopen-log-files
                                (Suricata cierra el fd viejo
                                 y abre el nuevo vacío)
```

**¿Por qué `truncate` y no `rm`?** Si se borrara el archivo, Suricata seguiría escribiendo
en el inode original (fd abierto) hasta que lo cerrara — el archivo desaparecería del
filesystem pero el espacio no se liberaría y el siguiente gzip perdería datos.
`truncate -s 0` preserva el inode y vacía el contenido en un solo paso atómico.

### 2.5 Por qué el motor debe estar DETENIDO en toda la F2

`ppi-motor.service` en el sensor monitoriza eve.json y bloquea IPs anómalas via SSH al
servidor (192.168.0.120). Si está activo durante capturas de Grupo B o C:

1. Motor detecta tráfico de Kali (192.168.0.100) → llama `_ssh("sudo ipset add ppi_blocked 192.168.0.100")`
2. Servidor aplica iptables DROP para Kali → sus paquetes no llegan al stack TCP
3. Suricata registra flows **truncados** (pkts_toserver=1–2, bytes_toclient=0)
4. Las features de estos flows parciales no representan el ataque real
5. → datos de evaluación F3 incorrectos, τ1/τ2 mal calibrados

El Desktop (192.168.0.20) está en WHITELIST del motor → sus flows siempre se registran
completos incluso si el motor estuviera activo (pero se mantiene detenido de todas formas
para no alterar la red).

---

## 3. Entradas

| Entrada | Descripción |
|---|---|
| Topología operativa (F1) | Suricata activo en ens35, SSH keys listas, motor detenido |
| `/var/log/suricata/eve.json` | Log EVE JSON en tiempo real — se comprime y rota al final de cada escenario |
| `scripts_f2/grupoA/run_grupo_A.sh` | Orquestador de escenarios normales (Desktop) |
| `scripts_f2/grupoB/run_grupo_B.sh` | Orquestador de escenarios anómalos (Kali) |
| `scripts_f2/grupoC/run_grupo_C.sh` | Orquestador de escenarios mixtos (Desktop + Kali) |
| Kali Linux 192.168.0.100 | Herramientas de ataque: hping3, nmap, hydra, sshpass |

**Requisito crítico:** `ppi-motor.service` debe estar **DETENIDO** en toda la F2 (ver §2.5).

---

## 4. Salidas y su destino en el pipeline

| Salida | Ruta (sensor) | Conteo | Destino en F3 |
|---|---|---|---|
| Capturas Grupo A | `data/raw/*_normal_*.eve.json.gz` | 28 archivos | `fase3_entrenar.py` → X_train (80%) + holdout (20%) |
| Capturas Grupo B | `data/raw/*_anom_*.eve.json.gz` | 13 archivos | `fase3_evaluar.py` → curva ROC → τ1/τ2 |
| Capturas Grupo C | `data/raw/*_mixto_*.eve.json.gz` | 6 archivos | `auc_por_escenario.py` → AUC mixto |
| Bitácora | `docs/bitacora/bitacora_escenarios.txt` | 64 líneas | Auditoría / tesis |

Los archivos `.gz` son la **única salida de F2**. No se generan CSVs intermedios.
F3 lee estos archivos directamente con `gzip.open()` + `json.loads()` línea a línea.

**Mapa de globs F2 → scripts F3 (date-agnostic):**

| Glob usado en F3 | Captura | Propósito |
|---|---|---|
| `data/raw/*_normal_*.gz` | Grupo A (28 arch.) | Entrenar IF (53,708 flows) + holdout (13,427) |
| `data/raw/*_normal_*.gz` + `data/raw/*_anom_*.gz` | A+B | Curva ROC → τ1=−0.4459 (Youden), τ2=−0.6027 (FPR≤2%) |
| `data/raw/*_anom_*.gz` | Grupo B (13 arch.) | AUC por tipo de ataque (B1-B6) |
| `data/raw/*_mixto_*.gz` | Grupo C (6 arch.) | AUC en condiciones reales (C1-C3) |

Los patrones `*_normal_*`, `*_anom_*`, `*_mixto_*` capturan cualquier fecha
(20260602_, 20260615_, etc.), permitiendo agregar corridas futuras sin cambiar código F3.

---

## 5. Por qué tres grupos separados

| Grupo | Condición de captura | Propósito en el pipeline IF |
|---|---|---|
| **A — Normal puro** | Kali **apagada** | Entrenar IF (one-class: solo normalidad) + holdout de referencia |
| **B — Ataque puro** | Desktop **quieto**, motor **detenido** | Calcular curva ROC, derivar τ1/τ2 sobre ataques puros sin ruido |
| **C — Mixto controlado** | Ambos activos, motor **detenido** | Validar AUC en condiciones reales: normal+ataque simultáneos |

**Por qué NO se captura en una sola sesión:**
Si Kali genera SYN Flood mientras Desktop hace curl simultáneamente:
- Los flows normales del Desktop se registran bajo condiciones de red alteradas
  (RST packets de Kali, saturación de colas TCP del servidor)
- El IF entrenado con estos flows "contaminados" aprendería una normalidad degradada
- Resultado: mayor FPR en producción (flows normales detectados como anomalías)

Separar la captura garantiza que el IF aprende **normalidad limpia** (Grupo A) y es
evaluado sobre **ataques puros** (Grupo B) antes de validar en **condiciones reales** (C).

---

## 6. Escenarios del Grupo A — Tráfico normal

Origen: Desktop 192.168.0.20 → Server 192.168.0.120. Kali **apagada**.
**Propósito:** construir el perfil de normalidad que aprende Isolation Forest.

| ID | Nombre | Herramienta | Puerto | Duración | Flows típicos |
|---|---|---|---|---|---|
| A1 | http_normal | `curl` en bucle → nginx | TCP/80 | 10 min | ~500–2,000 flows |
| A2 | ssh_legitimo | `ssh` sesión interactiva | TCP/22 | 8 min | ~50–200 flows |
| A3 | transferencia_legitima | `scp` / `wget` archivos | TCP/22, TCP/80 | 10 min | ~100–500 flows |
| A4 | trafico_sostenido | curl + ssh mixto continuo | TCP/80, TCP/22 | 15 min | ~800–3,000 flows |

Características de los flows normales: `pkts_toserver` y `pkts_toclient` balanceados,
`duration` > 0.5s, `byte_ratio` ≈ 0.1–2.0, `avg_pkt_size` > 200 bytes.

---

## 7. Escenarios del Grupo B — Tráfico anómalo

Origen: Kali 192.168.0.100 → Server 192.168.0.120. Desktop **quieto**.
**Propósito:** evaluar IF sobre ataques reales y derivar umbrales τ1/τ2 desde la curva ROC.

| ID | Nombre | Herramienta | Flags/detalle | Puerto | Duración | AUC final |
|---|---|---|---|---|---|---|
| B1 | syn_flood | `hping3 -S --flood` | SYN sin completar handshake | TCP/80 | 10 min | 0.8342 |
| B2 | port_scan | `nmap -sS -p 1-1024` | SYN scan sigiloso (1 pkt/puerto) | 1–1024 | 10 min | 0.9722 |
| B3 | udp_flood | `hping3 --udp --flood -p 53` | UDP masivo sin respuesta | UDP/53 | 10 min | 0.9537 |
| B4 | icmp_flood | `hping3 -1 --flood` | ICMP echo masivo | ICMP | 10 min | 0.8961 |
| B5 | http_abuse | `curl` bucle agresivo | HTTP GET repetitivo | TCP/80 | 10 min | 0.9670 |
| B6 | bruteforce | `hydra -l root -P wordlist` | Intentos masivos SSH | TCP/22 | 10 min | 0.8658 |

Firma IF de cada ataque:

| Ataque | Feature discriminante | Score IF típico |
|---|---|---|
| B1 SYN Flood | `pkt_ratio>>1`, `duration≈0`, `pkts_toclient=0` | ≈ −0.49 (zona gris τ1-τ2) |
| B2 Port Scan | `pkts_toserver=1`, `pkts_toclient=0`, `duration≈0` | ≈ −0.73 → BLOCK |
| B3 UDP Flood | `is_udp=1`, `byte_rate` masivo | ≈ −0.65 → BLOCK |
| B4 ICMP Flood | `is_icmp=1`, `dest_port=0`, `pkts_toclient=0` | ≈ −0.65 → BLOCK |
| B5 HTTP Abuse | `pkt_rate` alto, `avg_pkt_size` pequeño | ≈ −0.55 + heurístico HTTP |
| B6 BruteForce | múltiples flows TCP/22 cortos | ≈ −0.52 + heurístico BF-SSH |

---

## 8. Escenarios del Grupo C — Tráfico mixto

Desktop + Kali simultáneos. Motor **detenido** para capturar todos los flows.
**Propósito:** medir AUC en condiciones reales donde el motor debe distinguir normal de anómalo.

| ID | Nombre | Desktop (normal) | Kali (anómalo) | Duración | AUC final |
|---|---|---|---|---|---|
| C1 | http_synflood | curl → nginx :80 | hping3 -S --flood → :80 | 10 min | 0.8206 |
| C2 | ssh_portscan | ssh → :22 | nmap -sS -p 1-1024 | 10 min | 0.8596 |
| C3 | transfer_udpflood | scp/wget | hping3 --udp --flood → :53 | 10 min | 0.9327 |

Los flows de ambos orígenes se mezclan en el mismo eve.json. `auc_por_escenario.py`
separa por `src_ip` (Desktop=0/normal, Kali=1/anómalo) para calcular el AUC de cada escenario.

---

## 9. Nomenclatura de archivos `.gz`

```
YYYYMMDD_grupo_escenario_NN_eve.json.gz

Campos:
  YYYYMMDD   → fecha de captura (20260602, 20260615, 20260616...)
  grupo      → normal | anom | mixto
  escenario  → http | ssh | transferencia | sostenido | synflood | portscan |
                udpflood | icmpflood | httpabuse | bruteforce |
                http_synflood | ssh_portscan | transfer_udpflood
  NN         → número de corrida (01, 02, 03...)

Ejemplos reales en data/raw/:
  20260602_normal_http_01_eve.json.gz          ← A1, 02-jun, corrida 01
  20260602_normal_ssh_01_eve.json.gz           ← A2, 02-jun, corrida 01
  20260615_anom_synflood_01_eve.json.gz        ← B1, 15-jun, 26.8M flows raw
  20260615_anom_portscan_01_eve.json.gz        ← B2, 15-jun
  20260616_mixto_http_synflood_01_eve.json.gz  ← C1, 16-jun
```

**Globs date-agnostic usados en F3:**
```python
glob.glob('data/raw/*_normal_*.gz')  # → todos los de Grupo A, cualquier fecha
glob.glob('data/raw/*_anom_*.gz')    # → todos los de Grupo B, cualquier fecha
glob.glob('data/raw/*_mixto_*.gz')   # → todos los de Grupo C, cualquier fecha
```

---

## 10. Flujo paso a paso de un escenario individual

Este es el ciclo completo desde que arranca un escenario hasta que el `.gz` queda en disco.
**Ejemplo: Escenario A1 — http_normal, corrida 01, fecha 2026-06-02**

```
QUIÉN         ACCIÓN                                              QUÉ PRODUCE
──────────    ──────────────────────────────────────────────────  ─────────────────────────────
t=0s
Desktop       bash scripts_f2/grupoA/A1_http_normal.sh 01
A1.sh         Verifica: sensor (192.168.0.110) responde SSH
A1.sh         Verifica: motor DETENIDO (systemctl is-active → inactive)
A1.sh         Verifica: servidor (192.168.0.120) responde HTTP
A1.sh         HORA_INICIO="$(date +%T)"

t=5s
A1.sh         Lanza tráfico en bucle (600 seg):
Desktop       → curl -s http://192.168.0.120/ -o /dev/null
                → curl -s http://192.168.0.120/archivo.html -o /dev/null
                → sleep 2
                → (repite...)
Servidor      Responde HTTP 200 OK para cada request

t=5–605s
Suricata      Captura paquetes en ens35 (copia pasiva — sin alterar tráfico)
              Por cada conversación TCP cerrada (FIN o timeout):
              → escribe 1 línea JSON en /var/log/suricata/eve.json:
                {"event_type":"flow","src_ip":"192.168.0.20",
                 "dest_ip":"192.168.0.120","dest_port":80,"proto":"TCP",
                 "flow":{"pkts_toserver":4,"pkts_toclient":3,
                         "bytes_toserver":280,"bytes_toclient":12500,...}}

t=605s
A1.sh         HORA_FIN="$(date +%T)"
A1.sh         Tráfico curl termina

t=606s                                                            eve.json: ~5MB
A1.sh         ssh m4rk@192.168.0.110 \                           (flows del escenario A1)
                "bash scripts/capture/exportar_eve_por_escenario.sh \
                 20260602 normal http 01"

  SENSOR ejecuta exportar_eve_por_escenario.sh:
  Sensor        1. gzip -c /var/log/suricata/eve.json \           CREA:
                   > data/raw/20260602_normal_http_01_eve.json.gz  data/raw/20260602_normal_http_01_eve.json.gz
                   (compresión: ~5MB → ~300KB)
  Sensor        2. truncate -s 0 /var/log/suricata/eve.json        eve.json: 0 bytes
  Sensor        3. suricatasc -c reopen-log-files                  Suricata: fd reabierto

t=609s
A1.sh         ssh m4rk@192.168.0.110 \
                "bash scripts/evaluation/registrar_bitacora.sh \
                 normal http 192.168.0.20 192.168.0.120 \
                 HH:MM:SS HH:MM:SS curl \                          AGREGA línea a:
                 20260602_normal_http_01_eve.json.gz"              docs/bitacora/bitacora_escenarios.txt

t=610s
A1.sh         exit 0  ← escenario completado

run_grupo_A.sh  sleep 120  ← pausa obligatoria entre escenarios
                            (Suricata necesita cerrar flows TCP abiertos del escenario anterior)

t=730s
run_grupo_A.sh  bash A2_ssh_legitimo.sh 01  ← siguiente escenario
```

**Línea de bitácora resultante:**
```
2026-06-02 | normal | http | 192.168.0.20 -> 192.168.0.120 | 10:30:15 - 10:40:20 | curl | 20260602_normal_http_01_eve.json.gz
```

---

## 11. Cómo F3 lee los archivos `.gz` de F2

F3 lee directamente los `.gz` de F2 sin ningún script de conversión intermedio.
El flujo de datos exacto es:

```python
# fase3_entrenar.py — Grupo A → X_train + holdout

import glob, gzip, json, numpy as np
from sklearn.preprocessing import StandardScaler

archivos = glob.glob('data/raw/*_normal_*.gz')
# Ejemplo: ['data/raw/20260602_normal_http_01_eve.json.gz',
#            'data/raw/20260602_normal_ssh_01_eve.json.gz', ...]  (28 archivos)

WHITELIST = {"192.168.0.1","192.168.0.20","192.168.0.110","192.168.0.120",
             "192.168.0.130","192.168.0.140","127.0.0.1"}

rows = []
for gz_path in archivos:
    with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
        for line in f:
            e = json.loads(line)
            if e.get('event_type') != 'flow':        # solo flows
                continue
            src_ip = e.get('src_ip','')
            if not src_ip or ':' in src_ip:           # descarta IPv6
                continue
            if src_ip in WHITELIST:                   # solo origen fuera de whitelist
                continue                              # (para entrenamiento: filtra el sensor mismo)
            # → extrae las 14 features y agrega a rows
            rows.append(extraer_features(e))

X = np.array(rows)                                   # shape: (67,135, 14) aprox
X_scaled = StandardScaler().fit_transform(X)         # normalización

# Split 80/20 aleatorio (random_state=42)
from sklearn.model_selection import train_test_split
X_train, X_holdout = train_test_split(X_scaled, test_size=0.20, random_state=42)
# X_train  → 53,708 flows → IsolationForest(n_estimators=300).fit(X_train)
# X_holdout → 13,427 flows → guardado en data/normal_holdout.csv → usa fase3_evaluar.py
```

**Resumen del flujo F2 → F3:**

```
data/raw/*_normal_*.gz (28 arch.)  ─► fase3_entrenar.py ─► X_train (53,708)  ─► IF.fit()
                                                          └► X_holdout (13,427) ─► fase3_evaluar.py

data/raw/*_anom_*.gz   (13 arch.)  ─► fase3_evaluar.py  ─► curva ROC ─► τ1=−0.4459
                                                                          τ2=−0.6027

data/raw/*_anom_*.gz   (13 arch.)  ─► auc_por_escenario.py ─► AUC por B1-B6
data/raw/*_mixto_*.gz  (6 arch.)   ─►                         AUC por C1-C3
```

**Salida que F3 deja persistida en disco:**
```
models/isolation_forest.pkl      ← el modelo entrenado
models/scaler.pkl                ← el StandardScaler ajustado a X_train
models/features.csv              ← lista de 14 features (orden exacto)
data/normal_holdout.csv          ← los 13,427 flows holdout (nunca vistos por IF)
results/metricas_offline.txt     ← τ1, τ2, AUC, Recall, Precision, F1
results/reports/auc_por_escenario.txt  ← AUC desglosado por escenario
```

---

## 12. Scripts de automatización

### 12.1 `run_grupo_A.sh` / `run_grupo_B.sh` / `run_grupo_C.sh`

Orquestadores que ejecutan los escenarios de cada grupo en orden. Pasos internos:

1. Verifican conectividad SSH (sensor, servidor, Kali si aplica)
2. Verifican que `ppi-motor.service` esté detenido
3. Ejecutan los sub-scripts de cada escenario (A1→A4, B1→B6, C1→C3) pasando el número de corrida
4. Esperan **≥ 120 segundos** entre escenarios (cierre de flows TCP abiertos)

```bash
# Uso desde Desktop (192.168.0.20)
bash /home/m4rk/Descargas/scripts_f2/grupoA/run_grupo_A.sh 01   # corrida 01
bash /home/m4rk/Descargas/scripts_f2/grupoB/run_grupo_B.sh 01
bash /home/m4rk/Descargas/scripts_f2/grupoC/run_grupo_C.sh 01
```

### 12.2 Sub-scripts de escenario (A1.sh, B1.sh, C1.sh, ...)

Patrón base (ver §10 para la secuencia completa):
```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="/home/m4rk/ppi-surikata-producto"
EXPORT_SCRIPT="${PROJECT_ROOT}/scripts/capture/exportar_eve_por_escenario.sh"
BITACORA_SCRIPT="${PROJECT_ROOT}/scripts/evaluation/registrar_bitacora.sh"
CORRIDA="${1:-01}"

FECHA="$(date +%Y%m%d)"; HORA_INICIO="$(date +%T)"
END_TIME=$((SECONDS + DURACION_SEGUNDOS))
while [ $SECONDS -lt $END_TIME ]; do
  # tráfico específico del escenario
  sleep PAUSA
done
HORA_FIN="$(date +%T)"

# Exportar y registrar (vía SSH al sensor)
ssh m4rk@192.168.0.110 "bash ${EXPORT_SCRIPT} ${FECHA} ${GRUPO} ${ESCENARIO} ${CORRIDA}"
ssh m4rk@192.168.0.110 "bash ${BITACORA_SCRIPT} ${GRUPO} ${ESCENARIO} ${ORIGEN} ${DESTINO} \
  ${HORA_INICIO} ${HORA_FIN} ${HERRAMIENTA} ${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json.gz"
```

### 12.3 `scripts/capture/exportar_eve_por_escenario.sh`

Ruta en sensor: `/home/m4rk/ppi-surikata-producto/scripts/capture/exportar_eve_por_escenario.sh`

Argumentos: `FECHA GRUPO ESCENARIO CORRIDA`

Proceso interno (ver §2.4 para detalle del ciclo gzip→truncate→reopen):
```bash
EVE="/var/log/suricata/eve.json"
OUT="data/raw/${FECHA}_${GRUPO}_${ESCENARIO}_${CORRIDA}_eve.json.gz"

gzip -c "$EVE" > "$OUT"           # copia comprimida
truncate -s 0 "$EVE"              # vaciar
suricatasc -c reopen-log-files    # Suricata reabre el fd
```

### 12.4 `scripts/evaluation/registrar_bitacora.sh`

Ruta en sensor: `/home/m4rk/ppi-surikata-producto/scripts/evaluation/registrar_bitacora.sh`

Agrega una línea al final de `docs/bitacora/bitacora_escenarios.txt`:
```
2026-06-15 | anom | synflood | 192.168.0.100 -> 192.168.0.120 | 21:44:57 - 21:55:02 | hping3 | 20260615_anom_synflood_01_eve.json.gz
```

---

## 13. Secuencia temporal completa F2 (todos los grupos)

```bash
# ── PRE-REQUISITO ──────────────────────────────────────────────────────────
# Detener motor en sensor (si estuviera activo)
ssh m4rk@192.168.0.110 "sudo systemctl stop ppi-motor.service"
ssh m4rk@192.168.0.110 "sudo systemctl is-active ppi-motor.service"  # → inactive

# ── GRUPO A — tráfico normal (~43 min tráfico + ~9 min pausas = ~52 min) ──
# PRE: Kali apagada o desconectada de la red
bash /home/m4rk/Descargas/scripts_f2/grupoA/run_grupo_A.sh 01
# Internamente: A1(10min)+120s + A2(8min)+120s + A3(10min)+120s + A4(15min)+120s

# Pausa entre grupos (cierre de flows activos)
sleep 120

# ── GRUPO B — tráfico anómalo (~60 min tráfico + ~10 min pausas = ~70 min) ─
# PRE: Desktop sin tráfico hacia el servidor
bash /home/m4rk/Descargas/scripts_f2/grupoB/run_grupo_B.sh 01
# Internamente: B1-B6 (10min cada uno) + 120s entre cada uno

sleep 120

# ── GRUPO C — tráfico mixto (~30 min tráfico + ~4 min pausas = ~34 min) ────
# PRE: Motor sigue detenido
bash /home/m4rk/Descargas/scripts_f2/grupoC/run_grupo_C.sh 01
# Internamente: C1+C2+C3 (10min cada uno) + 120s entre cada uno

# ── VERIFICACIÓN FINAL ──────────────────────────────────────────────────────
ssh m4rk@192.168.0.110 "
  cd /home/m4rk/ppi-surikata-producto
  echo 'Grupo A:' \$(ls data/raw/*_normal_*.gz 2>/dev/null | wc -l) archivos
  echo 'Grupo B:' \$(ls data/raw/*_anom_*.gz   2>/dev/null | wc -l) archivos
  echo 'Grupo C:' \$(ls data/raw/*_mixto_*.gz  2>/dev/null | wc -l) archivos
  echo 'Bitacora:' \$(wc -l < docs/bitacora/bitacora_escenarios.txt) lineas
"
# Resultado esperado (acumulado, todas las corridas):
# Grupo A: 28 archivos
# Grupo B: 13 archivos
# Grupo C: 6 archivos
# Bitacora: 64 lineas
```

---

## 14. Flows raw vs flows usables

Los archivos `.gz` contienen **todos los eventos** registrados por Suricata, pero F3 solo
utiliza un subconjunto filtrado. La diferencia es grande en ataques de flood:

| Grupo | Archivos | Flows raw (event_type=flow) | Flows usables en F3 | Ratio |
|---|---|---|---|---|
| Grupo A — Normal | 28 | **397,984** | 67,135 | 16.9% |
| Grupo B — Anómalo | 13 | **56,080,443** | 906,188 | 1.6% |
| Grupo C — Mixto | 6 | **49,262,091** | incluido en eval. | — |
| **TOTAL** | **47** | **105,740,518** | — | — |

**¿Por qué tan pocos flows usables en Grupo B (1.6%)?**

Filtros aplicados en F3 sobre cada flow del `.gz`:

1. `event_type != 'flow'` → descarta alerts, http, ssh, dns (≈ 5–15% de líneas)
2. `':' in src_ip` → descarta IPv6 (Suricata emite ICMP flood en IPv6)
3. `src_ip in WHITELIST` → descarta flows del sensor, Desktop, Server
4. `src_ip` fuera del rango esperado → descarta broadcasts, multicast
5. Features con NaN (ej. `dest_port=0` en ICMP sin payload válido) → en Grupo B

Ejemplo concreto: `20260615_anom_icmpflood_01_eve.json.gz` tiene **26,800,000 flows raw**
de ICMP echo. Suricata los registra por IPv6 con src con `:` → filtro 2 los descarta todos.
AUC=0.8961 se calculó sobre runs donde Suricata sí emitió ICMP IPv4 (ver VERIFICACION_ESCENARIOS.md §B4).

---

## 15. Volumen de datos capturados

| Grupo | Archivos | Tamaño comprimido | Contenido |
|---|---|---|---|
| Grupo A (normal) | 28 `.gz` | ~15 MB | Flows normales — curl, ssh, scp, wget |
| Grupo B (anómalo) | 13 `.gz` | ~2.5 GB | Floods y scans — B1-B6 |
| Grupo C (mixto) | 6 `.gz` | ~800 MB | Normal + ataque simultáneos |
| **Total** | **47 archivos** | **~3.3 GB** | Fuente directa para F3 |

---

## 16. Criterios de éxito (salida de F2)

| Criterio | Comando de verificación | Resultado esperado |
|---|---|---|
| Archivos Grupo A generados | `ls data/raw/*_normal_*.gz \| wc -l` | **28** archivos |
| Archivos Grupo B generados | `ls data/raw/*_anom_*.gz \| wc -l` | **13** archivos |
| Archivos Grupo C generados | `ls data/raw/*_mixto_*.gz \| wc -l` | **6** archivos |
| Bitácora completa | `wc -l docs/bitacora/bitacora_escenarios.txt` | **64** líneas |
| Motor sigue detenido | `systemctl is-active ppi-motor.service` | `inactive` |
| NO existen CSVs intermedios | `ls data/dataset_*.csv 2>/dev/null \| wc -l` | **0** |
| Globs F3 encuentran archivos | `ls data/raw/*_normal_*.gz data/raw/*_anom_*.gz` | sin error |

**F2 se considera COMPLETADA** cuando existen los 47 archivos `.gz` en `data/raw/`
y la bitácora tiene 64 entradas. No se genera ningún CSV — F3 lee los `.gz` directamente.

---

**Siguiente fase:** `F3_especificacion.md` — entrenamiento de Isolation Forest con los `.gz`
del Grupo A, derivación de τ1/τ2 con el Grupo B, y evaluación por escenario con el Grupo C.
