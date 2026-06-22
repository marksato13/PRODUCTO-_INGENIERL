# F6 — Validación del Sistema (40 Corridas)
**Estado: ✅ COMPLETA Y VALIDADA — 2026-06-16 + validaciones en vivo 2026-06-22**

---

## Objetivo

Demostrar que el sistema funciona de punta a punta en condiciones reproducibles de laboratorio,
cumpliendo todos los criterios de aceptación formales: disponibilidad, latencia, ausencia de
interrupción de tráfico legítimo y capacidad de detección bajo ataques reales.

---

## Scripts de validación

| Script | Función |
|---|---|
| `scripts/f6_corridas.py` | Ejecuta las 40 corridas y genera `resultados_f6_completo.csv` |
| `scripts/auc_por_escenario.py` | AUC-ROC desglosado por escenario (A/B/C) |
| `scripts/generar_graficas_f6.py` | 7 figuras PNG 300 DPI para informe |

---

## Diseño de la validación

40 corridas ejecutadas el **2026-06-16** (09:17 → 13:22), organizadas en 4 grupos de 10:

| Grupo | Corridas | Tráfico | Propósito |
|---|---|---|---|
| Normal | 1–10 | Solo Desktop (normal) | Verificar ITL = 0% |
| Mixto | 11–20 | Desktop + Kali | Primera detección + bloqueo |
| Reevaluación | 21–30 | IP ya bloqueada en ipset | Confirmar persistencia del bloqueo |
| Final | 31–40 | Bloqueo consolidado | Disponibilidad sostenida |

---

## Resultados — todos los criterios cumplidos ✅

| Métrica | Valor medido | Criterio | Estado |
|---|---|---|---|
| Disponibilidad | **100%** | ≥ 99% | ✅ |
| ITL (Interrupción Tráfico Legítimo) | **0%** | = 0% | ✅ |
| Latencia P95 por flujo | **34.8 ms** | < 500 ms | ✅ |
| Lead time SYN Flood (B1) | **~62 s** | < 120 s | ✅ |
| IPs anómalas bloqueadas (corridas B) | ✅ todas | ≥ 1 | ✅ |
| Flujos normales BLOCK (corridas A) | **0** | = 0 | ✅ |

> **Nota sobre latencia:** `resultados_f6_completo.csv` registra latencia acumulada
> de sesión, no por flujo. La latencia de 34.8 ms P95 es por flujo individual,
> medida en `results/latencia_pipeline.txt`. Ver `results/resultados_f6_README.txt`.

> **Nota sobre flows_anom=0 en corridas 12–40:** es comportamiento correcto.
> La IP de Kali queda bloqueada en ipset desde la corrida 11 → paquetes descartados
> en kernel antes de llegar a Suricata → motor no ve flujos anómalos. No es fallo.

---

## Archivos de salida

```
results/
├── resultados_f6_completo.csv     ← 40 filas, una por corrida
├── resultados_f6_README.txt       ← notas sobre campos del CSV
├── latencia_pipeline.txt          ← distribución P50/P95/P99 por flujo
└── graficas_f6/
    ├── f6_01_disponibilidad.png
    ├── f6_02_flows_anomalos.png
    ├── f6_03_timeline_deteccion.png
    ├── f6_04_auc_por_escenario.png
    ├── f6_05_bloqueo_progresivo.png
    ├── f6_06_latencia_pipeline.png
    └── f6_07_panel_resumen.png    ← ← usar en slide 13 del PPT
```

---

## Validaciones adicionales en vivo — 2026-06-22

Complementan los 40 corridas formales con observación directa del comportamiento real:

### Bloqueo progresivo (B1 SYN Flood)

| Corrida | Timestamp | Trigger | Resultado | ipset timeout |
|---|---|---|---|---|
| 1ª | 05:44:13 | IF score=−0.6066 | BLOCK #1 | 300 s |
| 2ª | 06:05:03 | IF score=−0.7696 | BLOCK #2 | 1 800 s |
| 3ª | 06:39:42 | HTTP-ABUSE 100 req/30s | BLOCK #3 | **0 (PERMANENTE)** |

`block_counts.json` final: `{"192.168.0.100": 3}`

### Lead time B6 — SSH Brute Force (hydra -t 4)

| Evento | Tiempo desde inicio | Score IF | Acción |
|---|---|---|---|
| Primera detección | T + 53 s | −0.4832 | LIMIT (BF-SSH 5 intentos/60s) |
| BLOCK | T + 60 s | −0.6228 | BLOCK #1 (BF-SSH 15 intentos/60s) |

Telegram recibido: `🚨 PPI ALERTA — BRUTE_FORCE_SSH | BLOCK | IP: 192.168.0.100 | Puerto: 22 | 08:31:37`

### Whitelist Desktop

```
curl 120 veces (1 req/s) desde 192.168.0.20 → 192.168.0.120:80
Resultado: 0 BLOCK, 0 LIMIT — todos PERMIT ✅
```

---

## Criterios de aceptación — CUMPLIDOS ✅

| ID | Criterio | Valor | Estado |
|---|---|---|---|
| CA-F6-01 | Disponibilidad ≥ 99% en 40 corridas | 100% | ✅ |
| CA-F6-02 | ITL = 0% (sin bloqueos incorrectos de tráfico normal) | 0% | ✅ |
| CA-F6-03 | Latencia P95 < 500 ms | 34.8 ms | ✅ |
| CA-F6-04 | IP anómala bloqueada en corridas B y C | Sí | ✅ |
| CA-F6-05 | Lead time SYN Flood < 120 s | ~62 s | ✅ |
| CA-F6-06 | Lead time BF SSH — BLOCK < 120 s | 60 s | ✅ |
| CA-F6-07 | Bloqueo progresivo #3 permanente | timeout=0 | ✅ |
| CA-F6-08 | Telegram alerta BLOCK recibida | HTTP 200 | ✅ |

---

## Argumento de defensa

> "F6 es la validación empírica del sistema completo, no del modelo aislado.
> 40 corridas en condiciones reproducibles: disponibilidad del 100%, sin un solo
> bloqueo incorrecto de tráfico legítimo, latencia de 34.8ms —14 veces por debajo
> del requisito—, y detección confirmada bajo todos los vectores de ataque diseñados.
> Las validaciones adicionales del 22 de junio añaden evidencia en vivo:
> bloqueo progresivo hasta permanente, lead time real de 60 segundos en BF SSH,
> y alerta Telegram recibida en tiempo real."
