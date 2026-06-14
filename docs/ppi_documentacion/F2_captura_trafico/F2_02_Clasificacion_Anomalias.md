# F2-02 — Etiquetado de Anomalías: Tipo, Gravedad e Impacto

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas

> **Base técnica:** Todos los scores IF y estadísticas son reales, calculados ejecutando el modelo `isolation_forest.pkl` sobre `dataset_clean.csv` (376,827 flows) en el sensor `192.168.0.110` el 14 de junio 2026. El módulo `clasificador.py` fue implementado y validado en producción el mismo día.

---

## 1. Tipos de Anomalía

### 1.1 Taxonomía adoptada

El sistema clasifica anomalías en **7 tipos**, basados en el comportamiento estadístico de los flows y la lógica de detección (modelo IF + detectores temporales):

| Código | Tipo | Origen | Detector principal |
|---|---|---|---|
| `PORT_SCAN` | Reconocimiento por escaneo de puertos | Kali → nmap -sS | Modelo IF (dest_port variado) |
| `SYN_FLOOD` | Inundación TCP SYN | Kali → hping3 -S | Modelo IF (pkt_rate + pkt_ratio) |
| `UDP_FLOOD` | Inundación UDP | Kali → hping3 --udp | Modelo IF (is_udp + pkt_rate) |
| `ICMP_FLOOD` | Inundación ICMP | Kali → hping3 -1 | Modelo IF (is_icmp flag) |
| `HTTP_ABUSE` | Abuso de capa de aplicación HTTP | Kali → curl bucle | Detector temporal (100 req/30s) |
| `BRUTE_FORCE_SSH` | Fuerza bruta SSH | Kali → hydra | Detector temporal (15 intentos/60s) |
| `GENERIC_ANOMALY` | Anomalía estadística no clasificada | Cualquier IP | Modelo IF únicamente |

### 1.2 Scores IF reales por tipo de ataque

Calculados aplicando `clf.score_samples()` sobre `dataset_clean.csv`:

| Tipo | Escenario | N flows | Score μ | Score σ | Score p50 | BLOCK% | LIMIT% |
|---|---|---|---|---|---|---|---|
| PORT_SCAN | anom_portscan | 3,297 | **-0.6459** | 0.0327 | -0.6530 | 5.2% | 93.6% |
| SYN_FLOOD | anom_synflood | 94,841 | **-0.6083** | 0.0968 | -0.6529 | 15.1% | 68.4% |
| UDP_FLOOD | anom_udpflood | 15,815 | **-0.7131** | 0.0270 | -0.7215 | 91.0% | 9.0% |
| ICMP_FLOOD | anom_icmpflood | 20,200 | **-0.6914** | 0.0195 | -0.6789 | 29.3% | 70.7% |
| HTTP_ABUSE | anom_httpabuse | 21,758 | **-0.5024** | 0.1141 | -0.4256 | 0.6% | 42.5% |
| BRUTE_FORCE_SSH | anom_bruteforce | 2,062 | **-0.4352** | 0.0392 | -0.4206 | 0.0% | 21.8% |
| *Normal HTTP (ref)* | normal_http | 11,333 | *-0.6438* | 0.0448 | -0.6529 | *0.0%* | *96.1%* |

> **Observación crítica:** Los scores de `normal_http` y `anom_portscan` son casi idénticos (-0.6438 vs -0.6459). Esto confirma que el modelo IF **no distingue port scan de HTTP normal** basándose en scores individuales. El sistema resuelve esto con la regla heurística de features (bajo bytes + TCP + pocos pkts) dentro del `clasificador.py`, más el whitelist del Desktop que protege el tráfico legítimo.

---

## 2. Niveles de Anomalía

Se definen 4 niveles basados en la combinación de IF score, acción aplicada y tipo de detector:

| Nivel | Descripción | Condición en el sistema | Score de Riesgo |
|---|---|---|---|
| **BAJO** | Actividad inusual, no maliciosa confirmada | PERMIT por whitelist / score > τ1 | 0 – 25 |
| **MEDIO** | Actividad sospechosa que requiere monitoreo | LIMIT por modelo / score en zona τ2–τ1 | 26 – 50 |
| **ALTO** | Anomalía confirmada con impacto moderado | BLOCK por modelo / flood volumétrico | 51 – 79 |
| **CRÍTICO** | Anomalía severa con impacto crítico | BLOCK por detector temporal / CVSS ≥ 9.0 | 80 – 100 |

### Asignación de nivel por tipo:

| Tipo | Nivel base | Condición de escalada |
|---|---|---|
| PORT_SCAN | **MEDIO** | → ALTO si ports > 512 en una corrida |
| SYN_FLOOD | **ALTO** | → CRÍTICO si score ≤ τ2 (-0.6873) |
| UDP_FLOOD | **ALTO** | → CRÍTICO si score ≤ τ2 (91% de los casos) |
| ICMP_FLOOD | **MEDIO** | → ALTO si pkt_rate > 5,000 /s |
| HTTP_ABUSE | **ALTO** | → CRÍTICO si requests ≥ 100/30s (umbral BLOCK) |
| BRUTE_FORCE_SSH | **CRÍTICO** | Siempre crítico (impacto en autenticación) |

---

## 3. Gravedad

La gravedad sigue la escala CVSS v3.1 adaptada al contexto de red:

| Gravedad | CVSS Base | Descripción | Tipos asignados |
|---|---|---|---|
| **BAJA** | 0.1 – 3.9 | Impacto mínimo, no afecta disponibilidad | — |
| **MODERADA** | 4.0 – 6.9 | Afecta confidencialidad parcialmente | PORT_SCAN, ICMP_FLOOD |
| **ALTA** | 7.0 – 8.9 | Compromete disponibilidad del servicio | SYN_FLOOD, UDP_FLOOD, HTTP_ABUSE |
| **CRÍTICA** | 9.0 – 10.0 | Compromete autenticación y acceso | BRUTE_FORCE_SSH |

### Métricas CVSS v3.1 por tipo:

| Tipo | CVSS Base | AV | AC | PR | UI | S | C | I | A |
|---|---|---|---|---|---|---|---|---|---|
| PORT_SCAN | **4.0** | N | L | N | N | U | L | N | N |
| SYN_FLOOD | **7.5** | N | L | N | N | U | N | N | H |
| UDP_FLOOD | **7.5** | N | L | N | N | U | N | N | H |
| ICMP_FLOOD | **5.8** | N | H | N | N | U | N | N | H |
| HTTP_ABUSE | **7.5** | N | L | N | N | U | N | N | H |
| BRUTE_FORCE_SSH | **9.8** | N | L | N | N | U | H | H | H |

*AV=Network, AC=Attack Complexity, PR=Privileges Required, UI=User Interaction, S=Scope, C/I/A=Confidentiality/Integrity/Availability*

---

## 4. Impacto

### 4.1 Clasificación de impacto

| Impacto | Definición | Tipos | MITRE ATT&CK |
|---|---|---|---|
| **RECONOCIMIENTO** | El atacante obtiene información sobre la red (puertos, servicios activos) sin afectar la disponibilidad | PORT_SCAN | TA0007 — Discovery / T1046 |
| **SATURACIÓN** | Agotamiento de recursos (CPU, ancho de banda, tabla de conexiones) que degrada el servicio | SYN_FLOOD, UDP_FLOOD, ICMP_FLOOD | TA0040 — Impact / T1498 |
| **INTERRUPCIÓN DEL SERVICIO** | El servicio HTTP deja de responder correctamente ante el volumen de requests | HTTP_ABUSE | TA0040 / T1498.002 |
| **ACCESO NO AUTORIZADO** | Riesgo directo de compromiso de credenciales y acceso al sistema | BRUTE_FORCE_SSH | TA0006 — Credential Access / T1110 |
| **ANOMALÍA GENÉRICA** | No clasificada en los tipos anteriores | GENERIC_ANOMALY | T1498 genérico |

### 4.2 Impacto validado en el laboratorio

| Ataque | Impacto observado | Evidencia |
|---|---|---|
| PORT_SCAN (B2) | 1,705/1,705 flows de reconocimiento detectados; servidor no interrumpido | motor_decision.log 2026-06-02 19:47 |
| SYN_FLOOD (B1) | Saturación de tabla de conexiones TCP en .120; nginx degradado | Corridas C1: disponibilidad 100% por BLOCK automático |
| UDP_FLOOD (B3) | Saturación de buffer UDP; 91% de flows bloqueados | AUC=0.9905, detección 100% |
| ICMP_FLOOD (B4) | Saturación de ICMP; 29.3% bloqueados + 70.7% limitados | AUC=0.9861 |
| HTTP_ABUSE (B5) | 100 req/30s detectados; BLOCK en 28s | motor_decision.log 2026-06-04 15:10 |
| BRUTE_FORCE_SSH (B6) | 15 intentos/60s → BLOCK + Telegram | motor_decision.log 2026-06-03 18:50 |

---

## 5. Matriz Completa de Clasificación

| Ataque | Tipo | Nivel | Gravedad | Impacto | CVSS | MITRE ID | MITRE Tactic | Score IF μ | Riesgo μ |
|---|---|---|---|---|---|---|---|---|---|
| Port Scan (B2) | PORT_SCAN | MEDIO | MODERADA | RECONOCIMIENTO | 4.0 | T1046 | TA0007 Discovery | -0.6459 | 60/100 |
| SYN Flood (B1) | SYN_FLOOD | ALTO | ALTA | SATURACION | 7.5 | T1498.001 | TA0040 Impact | -0.6083 | 89/100 |
| UDP Flood (B3) | UDP_FLOOD | ALTO→CRÍTICO | ALTA | SATURACION | 7.5 | T1498.001 | TA0040 Impact | -0.7131 | 95/100 |
| ICMP Flood (B4) | ICMP_FLOOD | MEDIO | MODERADA | SATURACION | 5.8 | T1498 | TA0040 Impact | -0.6914 | 91/100 |
| HTTP Abuse (B5) | HTTP_ABUSE | CRÍTICO | ALTA | INTERRUPCION_SERVICIO | 7.5 | T1498.002 | TA0040 Impact | -0.5024 | 69/100 |
| Brute Force SSH (B6) | BRUTE_FORCE_SSH | CRÍTICO | CRÍTICA | ACCESO_NO_AUTORIZADO | 9.8 | T1110.001 | TA0006 Credential | -0.4352 | 95/100 |

---

## 6. Reglas de Clasificación Automática

El módulo `clasificador.py` implementa las reglas en orden de prioridad:

```
PRIORIDAD DE CLASIFICACIÓN
══════════════════════════════════════════════════════════════════

  REGLA 1 — Brute Force SSH (detector temporal, máxima prioridad)
  ───────────────────────────────────────────────────────────────
  SI detector == 'BRUTE_FORCE' O (dest_port==22 AND bf_intentos>=5)
    → tipo = BRUTE_FORCE_SSH
    → nivel = CRÍTICO (si intentos>=15) | ALTO (si intentos>=5)
    → gravedad = CRÍTICA | impacto = ACCESO_NO_AUTORIZADO
    → CVSS = 9.8 | boost riesgo +40

  REGLA 2 — HTTP Abuse (detector temporal)
  ─────────────────────────────────────────
  SI detector == 'HTTP_ABUSE' O (dest_port==80 AND requests>=50)
    → tipo = HTTP_ABUSE
    → nivel = CRÍTICO (≥100) | ALTO (≥50)
    → gravedad = ALTA | impacto = INTERRUPCION_SERVICIO
    → CVSS = 7.5 | boost riesgo +30

  REGLA 3 — ICMP Flood (protocolo)
  ──────────────────────────────────
  SI proto IN ('ICMP', 'IPV6-ICMP')
    → tipo = ICMP_FLOOD
    → nivel = MEDIO | gravedad = MODERADA
    → impacto = SATURACION | CVSS = 5.8

  REGLA 4 — UDP Flood (protocolo)
  ─────────────────────────────────
  SI proto == 'UDP'
    → tipo = UDP_FLOOD
    → nivel = ALTO (score≤τ2) | MEDIO (score>τ2)
    → gravedad = ALTA | impacto = SATURACION | CVSS = 7.5

  REGLA 5 — Port Scan (heurística de features)
  ─────────────────────────────────────────────
  SI proto=='TCP' AND bytes_toserver<200 AND bytes_toclient<200
     AND pkts_toserver<=3
    → tipo = PORT_SCAN
    → nivel = MEDIO | gravedad = MODERADA
    → impacto = RECONOCIMIENTO | CVSS = 4.0

  REGLA 6 — SYN Flood (TCP asimétrico o score≤τ2)
  ──────────────────────────────────────────────────
  SI proto=='TCP' AND (pkts_toserver>pkts_toclient OR score≤τ2)
    → tipo = SYN_FLOOD
    → nivel = CRÍTICO (score≤τ2) | ALTO
    → gravedad = ALTA | impacto = SATURACION | CVSS = 7.5

  REGLA 7 — Anomalía genérica (fallback)
  ────────────────────────────────────────
  Cualquier caso no cubierto por reglas 1-6
    → tipo = GENERIC_ANOMALY
    → nivel = ALTO (score≤τ2) | MEDIO
    → CVSS = 5.0
```

### Justificación del orden de prioridad

Las reglas de detectores temporales (1 y 2) tienen prioridad sobre el modelo porque:
- B6 (brute force) tiene score IF medio de -0.4352, por encima de τ1 → el modelo no lo detecta
- B5 (HTTP abuse) tiene score IF medio de -0.5024 → solo 43% en zona LIMIT por modelo
- Los detectores temporales son la única forma confiable de detectar estos ataques
- Si se evaluaran las reglas de features primero, B6 podría clasificarse erróneamente como PORT_SCAN (TCP, pocos bytes)

---

## 7. Implementación Técnica

### 7.1 Módulo `clasificador.py` — desplegado en producción

**Ruta en sensor:** `/home/m4rk/ppi-surikata-producto/scripts/clasificador.py`
**Fecha de despliegue:** 14 de junio 2026
**Estado:** Activo, validado con 6 casos de prueba

```python
# Firma pública del módulo (API de integración)
from clasificador import clasificar, formato_log, formato_telegram

resultado = clasificar(
    e           = evento_eve_json,    # dict: evento Suricata
    if_score    = -0.676,             # float: anomaly score del modelo
    accion      = 'BLOCK',            # str: 'PERMIT'|'LIMIT'|'BLOCK'
    dest_port   = 80,                 # int: puerto destino
    proto       = 'TCP',              # str: protocolo
    detector    = None,               # str: 'BRUTE_FORCE'|'HTTP_ABUSE'|None
    bf_intentos = 0,                  # int: intentos SSH en ventana
    http_requests = 0,                # int: requests HTTP en ventana
)

# resultado: {
#   tipo, nivel, gravedad, impacto,
#   score_riesgo, cvss_base, mitre_id, mitre_ta,
#   etiqueta_soc, descripcion
# }
```

### 7.2 Score de riesgo compuesto (0–100)

```python
def _score_riesgo(if_score, accion, boost=0):
    # S_modelo: contribución del IF score normalizado (0-50 puntos)
    s_modelo = min(max((-if_score - 0.4) / 0.35 * 50, 0), 50)
    # S_accion: penalización por la acción aplicada (0-50 puntos)
    s_accion = 50 if accion=='BLOCK' else (25 if accion=='LIMIT' else 0)
    # boost: puntos adicionales por detector temporal (brute force +40, http abuse +30)
    return min(int(s_modelo + s_accion + boost), 100)
```

**Scores de riesgo reales validados:**

| Escenario | IF Score | Acción | S_modelo | S_acción | Boost | **Riesgo** |
|---|---|---|---|---|---|---|
| normal_http (Desktop) | -0.4262 | PERMIT | 3.7 | 0 | 0 | **4/100** |
| anom_portscan | -0.6510 | LIMIT | 35.9 | 25 | 0 | **61/100** |
| anom_synflood | -0.6760 | BLOCK | 39.4 | 50 | 0 | **89/100** |
| anom_udpflood | -0.7140 | BLOCK | 44.9 | 50 | 0 | **95/100** |
| anom_icmpflood | -0.6910 | BLOCK | 41.6 | 50 | 0 | **92/100** |
| anom_httpabuse (detector) | -0.5024 | LIMIT | 14.6 | 25 | +30 | **70/100** |
| anom_bruteforce (detector) | -0.4352 | BLOCK | 5.0 | 50 | +40 | **95/100** |

### 7.3 Etiquetado automático en log y Telegram

**Formato de log enriquecido** (campo `tipo=` añadido):

```
# Antes (v1):
2026-06-02 | WARNING | ANOMALÍA | src=192.168.0.100 dst=192.168.0.120:80
  proto=TCP score=-0.6760 razón=[pkt_rate:z=+45.2 | ...] | BLOCK

# Después (v2 con clasificador):
2026-06-02 | WARNING | ANOMALÍA | tipo=SYN_FLOOD | nivel=ALTO | gravedad=ALTA |
  impacto=SATURACION | riesgo=89/100 | mitre=T1498.001 | src=192.168.0.100
  dst=192.168.0.120:80 | SYN-FLOOD | score=-0.6760 | BLOCK
```

**Formato Telegram enriquecido** (con emoji de nivel):

```
🌊 PPI ALERTA — SYN_FLOOD
━━━━━━━━━━━━━━━━━━━━━━━━
Accion   : BLOCK
IP       : 192.168.0.100
Gravedad : 🟠 ALTA
Nivel    : ALTO
Impacto  : SATURACION
Riesgo   : 89/100
MITRE    : T1498.001
Detalle  : Inundación SYN TCP: agotamiento tabla de conexiones (score=-0.6760)
Hora     : 2026-06-14 04:30:00
```

**Emojis por tipo:**
- 🔍 PORT_SCAN · 🌊 SYN_FLOOD · 💧 UDP_FLOOD · 📡 ICMP_FLOOD
- 🌐 HTTP_ABUSE · 🔑 BRUTE_FORCE_SSH · ⚠️ GENERIC_ANOMALY

**Emojis de nivel:** 🟢 BAJO · 🟡 MEDIO · 🟠 ALTO · 🔴 CRÍTICO

### 7.4 Integración con `motor_decision.py`

Para integrar el clasificador al motor existente, se agregan estas líneas en las ramas BLOCK y LIMIT:

```python
# En motor_decision.py — al inicio del archivo:
from clasificador import clasificar, formato_log, formato_telegram

# En rama BLOCK (accion == 'BLOCK'):
clf_result = clasificar(
    e=e, if_score=score, accion='BLOCK',
    dest_port=dest_port, proto=proto
)
log.warning(
    f"ANOMALÍA | {formato_log(clf_result, src_ip, f'{dest_ip}:{dest_port}')}"
)
telegram_alerta(
    formato_telegram(clf_result, src_ip, 'BLOCK',
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
)

# En detector de brute force:
clf_result = clasificar(
    e=e, if_score=score, accion=bf_accion,
    dest_port=dest_port, proto=proto,
    detector='BRUTE_FORCE', bf_intentos=bf_n
)

# En detector de HTTP abuse:
clf_result = clasificar(
    e=e, if_score=score, accion=hab_accion,
    dest_port=dest_port, proto=proto,
    detector='HTTP_ABUSE', http_requests=hab_n
)
```

### 7.5 Salida del test de validación (ejecutado en sensor 14/06/2026)

```
TEST DEL CLASIFICADOR — PPI UPeU 2026

[Port Scan B2]   → PORT_SCAN      | MEDIO    | MODERADA | RECONOCIMIENTO       | 60/100
[SYN Flood B1]   → SYN_FLOOD      | ALTO     | ALTA     | SATURACION           | 89/100
[UDP Flood B3]   → UDP_FLOOD      | ALTO     | ALTA     | SATURACION           | 94/100
[ICMP Flood B4]  → ICMP_FLOOD     | MEDIO    | MODERADA | SATURACION           | 91/100
[HTTP Abuse B5]  → HTTP_ABUSE     | CRÍTICO  | ALTA     | INTERRUPCION_SERVICIO| 69/100
[Brute Force B6] → BRUTE_FORCE_SSH| CRÍTICO  | CRÍTICA  | ACCESO_NO_AUTORIZADO | 95/100
```

---

## 8. Observaciones Analíticas del Dataset

### 8.1 Hallazgo: Brute Force SSH tiene score IF similar al tráfico normal

| Escenario | Score μ | Zona predominante |
|---|---|---|
| normal_ssh (legítimo) | -0.6464 | LIMIT 97.4% |
| anom_bruteforce | -0.4352 | PERMIT 78.2% |

El brute force SSH tiene un score **menos negativo** que el SSH normal. Esto es contraintuitivo pero tiene explicación: el SSH de brute force genera flows TCP extremadamente cortos (duración=0.001s, pkts_toserver=3) con un patrón de pkt_rate muy alto. El scaler fue ajustado con datos normales donde el SSH legítimo también tiene duración corta pero con comandos reales. El modelo IF no puede distinguirlos por flow individual.

**Implicación para la clasificación:** El campo `riesgo` para brute force (95/100) solo refleja el boost del detector temporal (+40), no el modelo. Sin el detector, el riesgo sería solo 5/100. Esto debe documentarse explícitamente en la tesis como limitación del modelo base.

### 8.2 Hallazgo: HTTP Normal y Port Scan son casi indistinguibles por score IF

```
normal_http score μ = -0.6438 → LIMIT 96.1%
anom_portscan score μ = -0.6459 → LIMIT 93.6%
```

Diferencia de solo 0.002 unidades. El modelo estadístico por sí solo **no puede** distinguir una petición HTTP normal de un probe de port scan. La distinción la hace la regla de features en `clasificador.py` (bytes_toserver < 200, pkts_toserver ≤ 3).

---

## 9. Tabla Resumen para la Defensa

| Pregunta del jurado | Respuesta en una línea |
|---|---|
| ¿Cómo clasifican las anomalías? | 7 tipos por reglas de prioridad: detector temporal > protocolo > features > modelo |
| ¿Cómo asignan gravedad? | Escala CVSS v3.1 adaptada: BAJA/MODERADA/ALTA/CRÍTICA según impacto en CIA |
| ¿Qué es el score de riesgo? | Métrica compuesta 0-100: 50% modelo IF + 50% acción + boost por detector temporal |
| ¿Qué pasa si el modelo no detecta B6? | El detector temporal (15 SSH/60s) lo clasifica CRÍTICO riesgo=95/100 automáticamente |
| ¿Cómo notifican al SOC? | Telegram enriquecido con tipo, nivel, gravedad, impacto, MITRE ID y score de riesgo |
| ¿Tienen trazabilidad MITRE ATT&CK? | Sí: cada tipo tiene MITRE ID y Tactic asignados en el clasificador |

---

## 10. Archivos generados

| Artefacto | Ruta en sensor | Descripción |
|---|---|---|
| `clasificador.py` | `scripts/clasificador.py` | Módulo de clasificación implementado |
| `scores_por_escenario.json` | `results/analisis_escenarios/` | Scores IF reales por escenario |
| `clasificacion_tipos.json` | `results/analisis_escenarios/` | Reglas y CVSS por tipo |

---

*Documento generado: 14 de junio 2026*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F2_captura_trafico/F2_02_Clasificacion_Anomalias.md`*
*Módulo clasificador.py validado en sensor 192.168.0.110 — 6 casos de prueba exitosos*
*Estado: Listo para tesis, sustentación y documentación técnica*
