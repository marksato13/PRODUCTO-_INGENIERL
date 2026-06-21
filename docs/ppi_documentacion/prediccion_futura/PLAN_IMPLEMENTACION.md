# Plan de Implementación por Fases — Módulo de Predicción (REVISADO)

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-21  
**Revisión:** Corrige 5 errores arquitectónicos del plan anterior

---

## Correcciones al plan anterior

| Error | Plan anterior (incorrecto) | Plan corregido |
|---|---|---|
| **E1 — Señal temporal** | Δanomalías cada 60s | Intervalo de tiempo entre stats (gap) |
| **E2 — Tamaño dataset** | ~3,455 ventanas | ~11,000 observaciones (una por línea stats) |
| **E3 — Feature principal** | `anom_lag1`, `Δhttp_abuse` | `gap_segundos`, `gap_lag1`, `gap_delta` |
| **E4 — Formatos del log** | 1 regex | 3 regex distintos (3 formatos reales en el log) |
| **E5 — Paquetes** | shap y statsmodels asumidos instalados | Faltan — instalar antes |

---

## Por qué el GAP es la señal correcta

Las líneas de estadísticas aparecen **cada 500 flows procesados**, no cada N segundos.
El tiempo entre dos stats consecutivas = 500 flows / tasa_de_tráfico:

```
Tráfico normal  → gap ≈ 174 segundos   (500 flows en 3 min)
Inicio ataque   → gap ≈  90 segundos   (tráfico acelerando)
Ataque pleno    → gap ≈  17 segundos   (500 flows en 17s = 29 flows/s)
```

El predictor detecta que el gap **está encogiendo** antes de que el IF acumule
suficientes flows para disparar el primer BLOCK (~62s de lead time).

Línea de tiempo durante SYN Flood:
```
t=0s    gap=174s  → normal
t=30s   gap=90s   → tráfico acelerando  ← predictor puede detectar aquí
t=60s   gap=45s   → aceleración clara   ← predictor alerta aquí
t=90s   gap=17s   → BLOCK del IF        ← motor reactivo actúa aquí
        ────────────────────────────────
        lead time predictivo ≈ 30–60s
```

---

## 3 formatos reales del log (todos deben parsearse)

```python
# Formato 1 — sesiones tempranas (02-jun inicio)
# flows=500 anomalías=500 bloqueados=500
RE_F1 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bloqueados=(\d+)$'
)

# Formato 2 — sesiones intermedias (02-jun tarde)
# flows=500 anomalías=97 bloqueados=0 limitados=1
RE_F2 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bloqueados=(\d+) limitados=(\d+)$'
)

# Formato 3 — sesiones finales (04-jun en adelante) ← el más completo
# flows=500 anomalías=409 bf=0 http_abuse=404 bloqueados=1 limitados=0 latencia_media=34.57ms
RE_F3 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bf=(\d+) http_abuse=(\d+) '
    r'bloqueados=(\d+) limitados=(\d+) latencia_media=([\d.]+)ms'
)

def parsear_stats(linea):
    """Retorna (timestamp, flows, bloqueados) o None."""
    for re_pat, idx_ts, idx_flows, idx_bloq in [
        (RE_F3, 1, 2, 6),
        (RE_F2, 1, 2, 4),
        (RE_F1, 1, 2, 4),
    ]:
        m = re_pat.search(linea)
        if m:
            return (
                pd.to_datetime(m.group(idx_ts)),
                int(m.group(idx_flows)),
                int(m.group(idx_bloq)),
            )
    return None
```

---

## Detección de reinicios de sesión (96 en total)

El motor se reinició 96 veces. Cada reinicio resetea `flows` a 0.
El parser detecta el reset comparando el flows actual con el anterior:

```python
def es_reinicio(flows_actual, flows_anterior):
    """True si el motor se reinició entre estas dos líneas de stats."""
    return flows_actual <= flows_anterior
    # El motor sube en pasos de 500: 500→1000→1500...
    # Un valor igual o menor significa reset.
```

Cuando hay reinicio: NO computar gap (sería artificialmente largo).
Iniciar una nueva sesión y esperar al menos 3 stats para tener lags válidos.

---

## Features correctas del modelo

Cada observación = una línea de stats (cada 500 flows procesados):

```python
FEATURES = [
    'gap',          # segundos entre esta stats y la anterior (señal principal)
    'gap_lag1',     # gap anterior
    'gap_lag2',     # gap hace 2 stats
    'gap_lag3',     # gap hace 3 stats
    'gap_delta',    # gap - gap_lag1  (¿acelerando? valor negativo = sí)
    'gap_mean5',    # media de últimos 5 gaps (rolling)
    'gap_std5',     # desviación estándar de últimos 5 gaps
    'bloq_activos', # bloqueados en esta stats (IPs actualmente bloqueadas)
    'hora_sin',     # sin(2π·hora/24)  codificación cíclica
    'hora_cos',     # cos(2π·hora/24)
]
```

**Target:** `¿el gap de la SIGUIENTE stats es < 50% del gap actual?`

```python
# Target: el gap siguiente cae a menos de la mitad → tráfico acelerando
df['target'] = (df['gap'].shift(-1) < df['gap'] * 0.5).astype(int)

# Alternativa (más directa): ¿hay un BLOCK nuevo en los próximos 60s reales?
df['target'] = df.apply(
    lambda row: int(any(
        (block_ts > row['ts']) and
        (block_ts <= row['ts'] + pd.Timedelta(seconds=60))
        for block_ts in block_timestamps
    )), axis=1
)
```

Usar **alternativa** (BLOCK en próximos 60s) — más directamente accionable.
`block_timestamps` se extrae del log parseando las líneas `WARNING.*BLOCK → BLOCKED`.

---

## Tamaño real del dataset

```
Stats lines totales   : 11,516
Menos arranques (×3)  : 96 × 3 = 288  (primeras 3 de cada sesión: sin lags)
Observaciones válidas : ~11,228
Positivos esperados   : ~500–1,500  (stats durante/previas a ataque)
Negativos esperados   : ~9,700–10,700
Ratio desbalance      : ~1:7 a 1:20  (usar scale_pos_weight)
```

Mucho mejor que los 3,455 del plan anterior.

---

## Feature de predicción en TIEMPO REAL (predictor.py)

En producción, el predictor NO espera la siguiente stats. Calcula:

```python
# En predictor.py, cada 60s:
tiempo_desde_ultima_stats = (datetime.now() - ultima_stats_ts).total_seconds()

# Si este valor es PEQUEÑO, el motor está procesando flows muy rápido → ataque probable
# Si es GRANDE, tráfico lento → normal

feat_realtime = {
    'gap': tiempo_desde_ultima_stats,   # ← gap parcial actual
    'gap_lag1': gap_lag1,
    'gap_lag2': gap_lag2,
    'gap_lag3': gap_lag3,
    'gap_delta': tiempo_desde_ultima_stats - gap_lag1,
    'gap_mean5': np.mean([gap_lag1, gap_lag2, gap_lag3, gap_lag4, gap_lag5]),
    'gap_std5':  np.std([gap_lag1, gap_lag2, gap_lag3, gap_lag4, gap_lag5]),
    'bloq_activos': bloqueados_ultima_stats,
    'hora_sin': np.sin(2*np.pi*datetime.now().hour/24),
    'hora_cos': np.cos(2*np.pi*datetime.now().hour/24),
}
p = clf.predict_proba([list(feat_realtime.values())])[0, 1]
```

Esta es la clave: el predictor mide cuánto tiempo lleva sin aparecer una nueva stats.
Si llevan 30s sin stats pero antes tardaban 174s → el tráfico explotó → alerta.

---

## Estructura de archivos (sin cambios respecto al plan anterior)

```
scripts/
  entrenar_predictor.py   ← NUEVO (Fases 0-2)
  predictor.py            ← NUEVO (Fase 3)
  dashboard_web.py        ← EXTENDER (Fase 5)

models/
  predictor_modelo.pkl    ← ganador entre XGBoost y RF
  predictor_tipo.txt      ← "XGBoost" o "RandomForest"
  features_predictor.txt  ← lista FEATURES en orden

data/
  series_gap_sesiones.csv ← dataset (renombrado: gap-based, no 60s-based)

results/
  predictor.log
  comparacion_predictores.txt
  metricas_predictor.txt
  graficas_predictor/
    roc_comparacion.png
    shap_predictor.png
    timeline_gaps_vs_blocks.png   ← renombrado: muestra gaps + BLOCKs

config/systemd/
  ppi-predictor.service
```

---

## Requisitos previos a implementar (checklist)

```bash
# 1. Instalar paquetes faltantes
/home/m4rk/ppi-sensor/venv/bin/pip install shap statsmodels

# 2. Verificar instalación
/home/m4rk/ppi-sensor/venv/bin/python3 -c "
import shap, statsmodels, xgboost, joblib
print('shap:', shap.__version__)
print('statsmodels:', statsmodels.__version__)
print('xgboost:', xgboost.__version__)
print('OK — todos listos')
"

# 3. Verificar acceso al log
wc -l /home/m4rk/ppi-surikata-producto/results/motor_decision.log
# Debe mostrar ~1,177,820
```

---

## Fases de implementación (corregidas)

### Fase 0 — Dataset con gaps (1–2h)
- Parsear log con los 3 regex
- Detectar 96 reinicios de sesión
- Extraer timestamps de BLOCK (de WARNING lines)
- Computar gap por observación
- Construir features y target
- Guardar `data/series_gap_sesiones.csv`
- **Criterio OK:** ≥10,000 obs, ≥300 positivos, sin NaN

### Fase 1 — Comparación ARIMA vs RF vs XGBoost (2–3h)
- Split temporal: train < 2026-06-15, test ≥ 2026-06-15
- ARIMA sobre serie univariada de gaps
- RF con `class_weight='balanced'`
- XGBoost con `scale_pos_weight=ratio`
- Guardar `comparacion_predictores.txt` + `roc_comparacion.png`

### Fase 2 — Decisión y serialización (30min)
- Criterio: XGBoost si AUC > RF + 2pp, sino RF
- Guardar `predictor_modelo.pkl`, `predictor_tipo.txt`, `features_predictor.txt`
- Guardar `metricas_predictor.txt`, `shap_predictor.png`, `timeline_gaps_vs_blocks.png`

### Fase 3 — predictor.py con gap en tiempo real (2–3h)
- Leer log cada 60s
- Calcular `tiempo_desde_ultima_stats` como feature principal
- Mantener historial de gaps en memoria
- Escribir `predictor.log`, llamar `enforce.sh` si P ≥ 0.70

### Fase 4 — Servicio systemd (30min)
- Crear e instalar `ppi-predictor.service`
- Verificar que arranca con el motor

### Fase 5 — Dashboard (2–3h)
- Segundo lector de `predictor.log` en `dashboard_web.py`
- Panel gauge P(ataque) + historial + gráfica de gaps en tiempo real
- SSE push al browser igual que las alertas existentes

### Fase 6 — 10 corridas de validación (2–3h)
- 5 con ataque (SYN Flood, HTTP Abuse)
- 5 sin ataque (solo Desktop)
- Medir lead time: Δt(alerta predictor) vs Δt(BLOCK motor)
- Anotar en bitácora

### Fase 7 — Sección PDF (1–2h)
- Agregar §9b al informe con métricas, gráficas y arquitectura
- Regenerar PDF y pushear

**Total: 11–16 horas (2 días a full)**

---

*Relacionado: `TIPOS_PREDICCION.md` · `ANALISIS_PREDICCION.md`*  
*Última actualización: 2026-06-21 — reemplaza plan anterior*
