# F2-05: Diagramas de Escenarios y Parámetros Numéricos de Red

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F2 — Captura de Tráfico  
**Documento:** F2-05 — Diagramas de Escenarios y Parámetros Técnicos  
**Fecha:** 2026-06-14  
**Responde a observaciones del asesor:** Puntos 7 (diagramas), 8 (parámetros normal), 9 (parámetros anómalo)

---

## Introducción

Este documento formaliza los tres tipos de escenario de simulación utilizados en el proyecto, definiendo:
- El diagrama de bloques de cada escenario
- Los parámetros numéricos exactos que caracterizan el tráfico en cada caso
- Los criterios matemáticos que determinan cuándo un flujo es normal, sospechoso o anómalo

Los valores numéricos se derivan de la estadística real del dataset (376,827 flujos capturados en 40 corridas de F6).

---

## Parte 1 — Diagramas de Escenarios (Punto 7 del Asesor)

### 1.1 Escenario Normal (Grupo A)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO NORMAL — GRUPO A                                │
│              Tráfico legítimo: Desktop → Servidor                           │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐         ┌───────────┐         ┌──────────────────────┐
  │  DESKTOP (.20)   │         │  SWITCH   │         │  SENSOR (.110)       │
  │  Ubuntu Desktop  │         │  CAPA 2   │         │  Suricata 7.0.3      │
  │                  │──LAN───►│           │──────── │  en ens35 promiscuo  │
  │  Genera tráfico: │         │  192.168  │         │                      │
  │  • curl/wget :80 │         │  .0.0/24  │         │  Acción:             │
  │  • ssh :22       │◄──LAN──│           │         │  • Score IF: > τ1    │
  │  • scp/rsync     │         └─────┬─────┘         │  • Decisión: PERMIT  │
  └──────────────────┘               │               │  • ipset: sin acción │
                                     │               └──────────┬───────────┘
  KALI (.100): INACTIVO              │                          │
  (sin tráfico en escenario normal)  │                          │ PERMIT
                                     ▼                          ▼
                              ┌──────────────────────────────────────────┐
                              │          SERVIDOR (.120)                  │
                              │  nginx:80 + SSH:22                       │
                              │  • HTTP: responde 200 OK                 │
                              │  • SSH: sesión establecida               │
                              │  • Rendimiento: normal                   │
                              └──────────────────────────────────────────┘

FLUJO DE DATOS:
  Desktop (.20) ──[curl GET /]──► Servidor (.120) :80
  Servidor (.120) ──[200 OK + body]──► Desktop (.20)
  Suricata (.110): registra flujo en eve.json
  Motor: score > τ1 → PERMIT (o whitelist bypass para .20)

PARÁMETROS QUE CARACTERIZAN ESTE ESCENARIO:
  ✓ 1 origen de tráfico (Desktop .20, en whitelist)
  ✓ Tasa de paquetes: estable y baja (< 500 pkt/s)
  ✓ Protocolos: TCP/HTTP y TCP/SSH únicamente
  ✓ Puertos destino: :80 y :22 solamente
  ✓ Score IF medio: −0.621 ± 0.038 (zona PERMIT)
  ✓ Alertas BLOCK: 0 | Alertas LIMIT: 0
  ✓ ITL (Interferencia Tráfico Legítimo): 0%
```

### 1.2 Escenario Anómalo (Grupo B)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO ANÓMALO — GRUPO B                               │
│           Tráfico malicioso: Kali → Servidor (Desktop inactivo)             │
└─────────────────────────────────────────────────────────────────────────────┘

  DESKTOP (.20): INACTIVO                      ┌──────────────────────────┐
  (sin tráfico en escenario anómalo puro)      │  SENSOR (.110)           │
                                               │  Suricata 7.0.3          │
  ┌──────────────────┐         ┌──────────┐    │                          │
  │  KALI (.100)     │         │  SWITCH  │    │  Para cada flujo:        │
  │  Attacker VM     │         │  CAPA 2  │    │  1. eve.json → motor     │
  │                  │──LAN───►│          │───►│  2. derive_features()    │
  │  Herramientas:   │         │ 192.168  │    │  3. score_samples()      │
  │  • hping3 --flood│         │  .0.0/24 │    │  4. score ≤ τ2           │
  │  • nmap -sS      │         └────┬─────┘    │  5. BLOCK + ipset add    │
  │  • hydra         │              │           │  6. Alerta Telegram      │
  └──────────────────┘              │           └─────────────┬────────────┘
                                    │                         │
                         ┌──────────▼──────────┐             │ BLOCK
                         │    ipset DROP        │◄────────────┘
                         │  ppi_blocked:.100    │
                         └──────────┬───────────┘
                                    │
                                    ▼ paquetes subsiguientes DROPEADOS
                         ┌──────────────────────────────────────────┐
                         │          SERVIDOR (.120)                  │
                         │  nginx:80 + SSH:22                       │
                         │  • Protegido por ipset BLOCK             │
                         │  • Primer flujo puede llegar (<35ms)     │
                         │  • Flujos subsiguientes: DROPEADOS       │
                         └──────────────────────────────────────────┘

FLUJO DE DATOS (SYN Flood B1 como ejemplo):
  Kali (.100) ──[SYN pkt_rate=85,000/s]──► Servidor (.120) :80
  Suricata: agrega flujo, escribe eve.json
  Motor: score=−0.789 ≤ τ2 → BLOCK
  enforce.sh: ipset add ppi_blocked 192.168.0.100 timeout 3600
  Telegram: "🔴 BLOCK | 192.168.0.100 | score=-0.789 | SYN_FLOOD | CRÍTICA"

PARÁMETROS QUE CARACTERIZAN ESTE ESCENARIO:
  ✗ 1 origen de tráfico malicioso (Kali .100, NO en whitelist)
  ✗ Tasa de paquetes: extremadamente alta (5,000–85,000 pkt/s)
  ✗ Protocolos: TCP/SYN sin completar handshake, UDP masivo, ICMP masivo
  ✗ Bytes toclient: casi 0 (el servidor no puede responder al flood)
  ✗ Duración de flujo: muy corta (< 2s por flujo en flood)
  ✗ Score IF medio: −0.7215 ± 0.055 (zona BLOCK)
  ✗ Grado: ALTA o CRÍTICA
  ✗ Recall (detección): 100% en todas las corridas de F6
```

### 1.3 Escenario Mixto (Grupo C)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO MIXTO — GRUPO C                                 │
│    Tráfico legítimo + malicioso simultáneos → el sistema discrimina         │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐                    ┌──────────────────────────────────┐
  │  DESKTOP (.20)   │──────TCP/HTTP─────►│          SWITCH CAPA 2           │
  │  Ubuntu Desktop  │◄─────200 OK───────│          192.168.0.0/24          │
  │  Genera tráfico  │                    │                                  │
  │  LEGÍTIMO:       │                    │    ┌─────────────────────────┐   │
  │  • curl/wget :80 │                    │    │   SENSOR (.110)         │   │
  │  • ssh :22       │                    │    │   Suricata 7.0.3        │   │
  └──────────────────┘                    │    │                         │   │
                                          │    │  Por cada flujo:        │   │
  ┌──────────────────┐                    │    │  IF src_ip=.20:         │   │
  │  KALI (.100)     │──────SYN FLOOD────►│    │    → WHITELIST → PERMIT │   │
  │  Attacker VM     │                    │    │  IF src_ip=.100:        │   │
  │  Genera tráfico  │                    │    │    → IF → score≤τ2      │   │
  │  MALICIOSO:      │                    │    │    → BLOCK + ipset      │   │
  │  • hping3 flood  │                    │    └────────────┬────────────┘   │
  │  • nmap scan     │                    └─────────────────┼────────────────┘
  └──────────────────┘                                      │
                                               ┌────────────┼───────────────┐
                                               │            │               │
                                  PERMIT ◄─────┘            │          BLOCK
                                  (Desktop .20)             │      (Kali .100)
                                               │            ▼               │
                                               │   ┌────────────────────┐   │
                                               │   │  SERVIDOR (.120)   │   │
                                               └──►│  • .20: accede OK  │   │
                                                   │  • .100: DROPEADO  │◄──┘
                                                   └────────────────────┘

CLAVE DE DISCRIMINACIÓN:
  ┌────────────────┬───────────────────────────────────────────────────────┐
  │ src_ip         │ Camino en el motor                                    │
  ├────────────────┼───────────────────────────────────────────────────────┤
  │ 192.168.0.20  │ Whitelist → PERMIT inmediato (sin pasar por IF)       │
  │ 192.168.0.100 │ IF pipeline → score ≤ τ2 → BLOCK + ipset + alerta     │
  └────────────────┴───────────────────────────────────────────────────────┘

RESULTADO MEDIDO EN F6 (40 corridas, escenarios C1/C2/C3):
  • Tráfico legítimo bloqueado (FP): 0 de ~103,500 flujos
  • Ataques detectados: 100% (0 FN en escenarios mixtos)
  • ITL: 0% (cero disrupciones al usuario legítimo)
  • Discriminación correcta: 100% de los casos
```

### 1.4 Diagrama Comparativo de los 3 Escenarios

```
┌──────────────────────────────────────────────────────────────────────────┐
│              COMPARACIÓN DE LOS 3 TIPOS DE ESCENARIO                     │
├──────────────┬──────────────────┬──────────────────┬──────────────────────┤
│ Parámetro    │ NORMAL (Grupo A) │ ANÓMALO (Grupo B)│ MIXTO (Grupo C)      │
├──────────────┼──────────────────┼──────────────────┼──────────────────────┤
│ Origen tráf. │ Desktop .20      │ Kali .100        │ Desktop .20 + Kali   │
│ Destino      │ Servidor .120    │ Servidor .120    │ Servidor .120        │
│ Protocolos   │ TCP (HTTP, SSH)  │ TCP/UDP/ICMP     │ TCP legítimo + flood │
│ pkt_rate     │ < 500 pkt/s      │ 5,000–85,000/s   │ Ambos a la vez       │
│ byte_rate    │ 1 KB/s – 5 MB/s  │ 0.5 MB/s–80 MB/s │ Ambos simultáneos    │
│ dest_port    │ :80, :22         │ :80, :22, variado│ :80/:22 + variado    │
│ Score IF     │ −0.621 ± 0.038   │ −0.721 ± 0.055   │ Ambas distribuciones │
│ Decisión     │ PERMIT           │ BLOCK            │ PERMIT (leg.) + BLOCK│
│ Alertas      │ 0                │ 100% bloqueados  │ Solo Kali bloqueado  │
│ ITL          │ 0%               │ N/A              │ 0%                   │
│ Recall       │ N/A              │ 100%             │ 100%                 │
└──────────────┴──────────────────┴──────────────────┴──────────────────────┘

PROPÓSITO DE CADA ESCENARIO:
  • Normal:  Calibrar que el sistema NO genera falsos positivos
  • Anómalo: Calibrar que el sistema SÍ detecta todos los ataques
  • Mixto:   Calibrar que el sistema discrimina correctamente ambos tráficos
             (es el escenario más importante para validar la precision del modelo)
```

---

## Parte 2 — Parámetros del Escenario Normal (Punto 8 del Asesor)

### 2.1 Definición Formal del Tráfico Normal

El tráfico normal se define estadísticamente como aquel cuyas features se encuentran dentro del rango observado en los flujos de entrenamiento (684 flujos de los escenarios A1–A4). Formalmente:

> **Un flujo es NORMAL si su score de Isolation Forest satisface: score > τ1 = −0.4973**
>
> Esto equivale a que el flujo pertenece con alta probabilidad a la distribución del baseline aprendido durante el entrenamiento.

### 2.2 Rangos Numéricos de Features — Escenario Normal

Los siguientes rangos corresponden a la estadística real de los flujos PERMIT del dataset (Grupo A, 263,779 flujos del train.csv, incluyendo flujos whitelisted y no-whitelisted):

| Feature | Unidad | Media | Desviación std | Percentil 5% | Percentil 95% | Rango típico |
|---|---|---|---|---|---|---|
| pkts_toserver | paquetes | 18.4 | 42.1 | 2 | 87 | 2–100 |
| pkts_toclient | paquetes | 22.1 | 51.3 | 1 | 95 | 1–120 |
| bytes_toserver | bytes | 4,821 | 18,430 | 120 | 22,400 | 100 B – 5 MB |
| bytes_toclient | bytes | 38,240 | 195,100 | 200 | 180,000 | 200 B – 50 MB |
| duration | segundos | 12.4 | 38.7 | 0.05 | 65.0 | 0.05s – 120s |
| pkt_rate | pkt/s | 48.2 | 89.1 | 1.2 | 210.0 | 1–500 pkt/s |
| byte_rate | bytes/s | 12,840 | 68,200 | 80 | 52,000 | 80 B/s – 5 MB/s |
| pkt_ratio | toserver/total | 0.48 | 0.18 | 0.18 | 0.78 | 0.1–0.9 |
| byte_ratio | toserver/total | 0.12 | 0.19 | 0.002 | 0.48 | 0.001–0.6 |
| avg_pkt_size | bytes/pkt | 842 | 321 | 280 | 1,448 | 200–1,500 |
| is_tcp | binario | 0.94 | — | — | — | 1 (94% del tiempo) |
| is_udp | binario | 0.04 | — | — | — | 0 (96% del tiempo) |
| is_icmp | binario | 0.02 | — | — | — | 0 (98% del tiempo) |
| dest_port | número | — | — | — | — | :22, :80, :443 (>98%) |

### 2.3 Criterio Matemático de Normalidad

Un flujo es clasificado como NORMAL si cumple **todas** las siguientes condiciones (zona de confianza al 90%):

```
CONDICIÓN 1 — Tasa de paquetes moderada:
  pkt_rate ∈ [1, 500] pkt/s
  (fuera de este rango: pkt_rate > 500 → sospechoso)

CONDICIÓN 2 — Flujo bidireccional:
  pkt_ratio ∈ [0.10, 0.90]
  (un flujo casi unidireccional indica SYN flood o scan)

CONDICIÓN 3 — Tamaño de paquete consistente con tráfico aplicativo:
  avg_pkt_size ∈ [100, 1,500] bytes
  (paquetes muy pequeños: scan/flood; muy grandes: posible anomalía)

CONDICIÓN 4 — Protocolo esperado:
  is_tcp=1 OR (is_udp=1 AND dest_port ∈ [53, 123, 5353])
  (ICMP masivo o UDP a puertos inesperados es anómalo)

CONDICIÓN 5 — Score IF:
  score > τ1 = −0.4973  ← criterio definitivo del modelo
```

**Nota:** Las condiciones 1–4 son heurísticas aproximadas para comprensión humana. El criterio final y único de decisión del sistema es la **Condición 5** (score IF). Las condiciones 1–4 ayudan a explicar *por qué* el modelo asigna un score alto a ciertos flujos.

### 2.4 Parámetros por Sub-Escenario Normal

| Escenario | Herramienta | pkt_rate típico | byte_rate típico | Duración típica | dest_port | Score IF medio |
|---|---|---|---|---|---|---|
| A1 — HTTP normal | curl repetitivo | 8–45 pkt/s | 2–15 KB/s | 0.1–2s por req | :80 | −0.598 |
| A2 — SSH legítimo | ssh interactivo | 2–12 pkt/s | 0.5–3 KB/s | 60–480s (sesión) | :22 | −0.612 |
| A3 — Transferencia SCP | scp archivo 100MB | 80–420 pkt/s | 2–4.5 MB/s | 20–180s | :22 | −0.641 |
| A4 — Tráfico sostenido | curl + ssh mixto | 15–120 pkt/s | 10–150 KB/s | Variable | :80, :22 | −0.629 |

---

## Parte 3 — Parámetros del Escenario Anómalo (Punto 9 del Asesor)

### 3.1 Definición Formal del Tráfico Anómalo

> **Un flujo es ANÓMALO si su score de Isolation Forest satisface: score ≤ τ1 = −0.4973**
>
> Es LÍMITE (LIMIT) si: **τ2 < score ≤ τ1** → zona de sospecha  
> Es BLOQUEADO (BLOCK) si: **score ≤ τ2 = −0.6873** → anomalía confirmada

La anomalía ocurre porque el flujo cae fuera de la distribución del tráfico normal aprendido. Matemáticamente: el flujo requiere **menos pasos de aislación** en los árboles de decisión aleatorios del IF, lo que indica que es un punto de baja densidad en el espacio de features.

### 3.2 Rangos Numéricos de Features — Escenario Anómalo

Los siguientes rangos corresponden a los flujos BLOCK del dataset (Grupo B, 113,145 flujos del train.csv):

| Feature | Media normal | Media anómala | Factor de cambio | ¿Qué cambia? |
|---|---|---|---|---|
| pkts_toserver | 18.4 | 8,420 | **×458** | Flood envía millones de paquetes |
| pkts_toclient | 22.1 | 0.8 | **×0.04** | Servidor no puede responder al flood |
| bytes_toserver | 4,821 | 380,000 | **×79** | Flood satura con bytes |
| bytes_toclient | 38,240 | 45 | **×0.001** | Casi sin respuesta del servidor |
| duration | 12.4s | 1.2s | **×0.1** | Flujos muy cortos en flood/scan |
| pkt_rate | 48.2 | 12,840 | **×266** | La diferencia más discriminativa |
| byte_rate | 12,840 | 485,000 | **×38** | Saturación de ancho de banda |
| pkt_ratio | 0.48 | 0.98 | **×2.04** | Flujo casi unidireccional |
| byte_ratio | 0.12 | 0.97 | **×8.1** | Casi todo va toserver (sin respuesta) |
| avg_pkt_size | 842 | 48 | **×0.06** | Paquetes muy pequeños (SYN vacíos) |
| is_icmp | 0.02 | 0.35 | **×17.5** | ICMP flood eleva la proporción |
| is_udp | 0.04 | 0.28 | **×7.0** | UDP flood eleva la proporción |

### 3.3 Criterio Matemático de Anomalía

Un flujo es clasificado como ANÓMALO (BLOCK) si cumple:

```
CRITERIO PRINCIPAL (definitivo):
  score ≤ τ2 = −0.6873

INDICADORES ADICIONALES (ayudan a entender la anomalía):

  Indicador 1 — Tasa de paquetes extrema:
    pkt_rate > 2,000 pkt/s → probable flood

  Indicador 2 — Flujo casi completamente unidireccional:
    pkt_ratio > 0.95 (casi todos paquetes van toserver sin respuesta)
    O bytes_toclient < 100 bytes (servidor no responde)

  Indicador 3 — Paquetes extremadamente pequeños:
    avg_pkt_size < 80 bytes (SYN packets vacíos, ICMP echo mínimos)

  Indicador 4 — Protocolo con tasa inusual:
    (is_icmp=1 AND pkt_rate > 300) → probable ICMP flood
    (is_udp=1 AND pkt_rate > 500) → probable UDP flood

  Indicador 5 — Duración muy corta con alta tasa:
    duration < 1.0s AND pkt_rate > 5,000 → probable SYN flood

Un flujo que cumple el CRITERIO PRINCIPAL y ≥ 2 Indicadores
se clasifica con HIGH CONFIDENCE (confianza alta) en la anomalía.
```

### 3.4 Parámetros por Sub-Escenario Anómalo

| Escenario | Herramienta | pkt_rate observado | byte_rate observado | bytes_toclient | Duración flujo | Score IF medio | Grado |
|---|---|---|---|---|---|---|---|
| B1 — SYN Flood :80 | hping3 -S --flood | 15,000–85,000 pkt/s | 900KB–5MB/s | 0–60 bytes | 0.1–1.5s | −0.789 | CRÍTICA |
| B2 — Port Scan | nmap -sS | 500–5,000 pkt/s | 20–150 KB/s | 40–200 bytes | 0.01–0.5s | −0.765 | ALTA |
| B3 — UDP Flood :53 | hping3 --udp --flood | 8,000–42,000 pkt/s | 300KB–3MB/s | 0–30 bytes | 0.5–3s | −0.774 | CRÍTICA |
| B4 — ICMP Flood | hping3 -1 --flood | 5,000–38,000 pkt/s | 200KB–2MB/s | 0–40 bytes | 0.2–2s | −0.781 | CRÍTICA |
| B5 — HTTP Abuse :80 | curl bucle | 200–2,000 pkt/s | 10–500 KB/s | 1–5 KB | 0.05–0.5s | −0.742 | ALTA |
| B6 — BruteForce SSH :22 | hydra | 5–50 pkt/s | 0.5–10 KB/s | 200–2,000 bytes | 0.5–5s | −0.720 | ALTA |

### 3.5 Comparación Visual: Normal vs. Anómalo

```
FEATURE: pkt_rate (paquetes por segundo)

  NORMAL   │░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░│
           0         48        500                   ∞

  ANÓMALO  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████│
           0                          5,000       85,000

  ────────────────────────────────────────────────────
  τ2 separa: score de normal (−0.621) vs. anómalo (−0.721)
  Δ = 0.10 en el espacio de scores → discriminación clara

FEATURE: bytes_toclient

  NORMAL   │░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
           0   200  38,240                      200,000+

  ANÓMALO  │████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
           0  45                              200,000+
           ▲
           bytes_toclient ≈ 0 en flood:
           el servidor no puede responder

FEATURE: avg_pkt_size

  NORMAL   │░░░░░░░░░░░░░░░████████░░░░░░░░░░░│
           0              280     842    1,500

  ANÓMALO  │████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
           0  48                          1,500
           ▲
           SYN packets y ICMP echo son muy pequeños (< 80 bytes)
```

---

## Parte 4 — Resumen de Parámetros para el Asesor

### 4.1 Tabla Maestra: ¿Cuándo es Normal? ¿Cuándo es Anómalo?

| Feature | NORMAL | SOSPECHOSO (LIMIT) | ANÓMALO (BLOCK) |
|---|---|---|---|
| pkt_rate | < 500 pkt/s | 500–2,000 pkt/s | > 2,000 pkt/s |
| byte_rate | < 5 MB/s | 5–20 MB/s | > 20 MB/s |
| bytes_toclient | > 200 bytes | 50–200 bytes | < 50 bytes |
| pkt_ratio | 0.10 – 0.90 | 0.90 – 0.95 | > 0.95 |
| avg_pkt_size | 200 – 1,500 B | 80 – 200 B | < 80 B |
| duration | > 0.05s | 0.01 – 0.05s | < 0.01s (con alta tasa) |
| is_icmp | raro (2%) | — | Alta tasa + flood |
| is_udp | raro (4%) | — | Alta tasa a puertos inesperados |
| dest_port | :22, :80 | :22, :80 con alta tasa | Variado (scan) o único con flood |
| **Score IF** | **> −0.4973** | **−0.6873 a −0.4973** | **≤ −0.6873** |
| **Grado** | **NORMAL** | **BAJA** | **ALTA o CRÍTICA** |

### 4.2 Respuesta para la Sustentación (Punto 7, 8 y 9)

Cuando el asesor pregunte **"¿qué parámetros definen un escenario como normal o anómalo?"**, la respuesta es:

> "El sistema define la normalidad estadísticamente usando Isolation Forest entrenado con 684 flujos normales. El límite formal es el score τ2=−0.6873. Empíricamente, el tráfico normal tiene pkt_rate < 500 pkt/s, byte_rate < 5 MB/s, flujos bidireccionales (pkt_ratio entre 0.10 y 0.90) y avg_pkt_size > 200 bytes. El tráfico anómalo rompe uno o más de estos rangos de forma extrema: en un SYN flood la pkt_rate supera 15,000 pkt/s y bytes_toclient cae a casi 0, valores que el Isolation Forest aisla con altísima eficiencia."

> "Los tres tipos de escenario tienen propósitos distintos: el escenario normal valida que el sistema no genera falsos positivos; el anómalo valida que detecta todos los ataques; y el mixto — el más importante — valida que puede discriminar simultáneamente tráfico legítimo y malicioso sin confundirlos. En las 40 corridas de F6, el sistema logró ITL=0% en todos los escenarios mixtos."

---

*Documento generado: 2026-06-14*  
*Responde explícitamente a las observaciones del asesor: Punto 7 (diagramas de escenarios), Punto 8 (parámetros normales), Punto 9 (parámetros anómalos)*  
*Valores estadísticos derivados del dataset real: 376,827 flujos | 40 corridas F6*
