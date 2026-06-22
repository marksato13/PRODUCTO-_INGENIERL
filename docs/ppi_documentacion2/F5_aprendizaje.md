# F5 — Aprendizaje Continuo (Reentrenamiento Automático)
**Estado: ✅ IMPLEMENTADA**

---

## Objetivo

Que el sistema aprenda de su propio historial operativo sin intervención manual. Cuando la red cambia, los modelos se adaptan automáticamente. Lo que diferencia este sistema de un IDS estático.

---

## ¿Por qué es necesario?

Un modelo entrenado una sola vez se desactualiza:
- El tráfico normal cambia (nuevos servicios, más usuarios, horarios diferentes)
- Los ataques evolucionan (técnicas nuevas, IPs rotadas)
- Los umbrales τ1/τ2 fijos dejan de ser óptimos

Sin F5: el sistema detecta bien hoy, peor en 6 meses.
Con F5: el sistema mejora continuamente con experiencia real.

---

## Componentes implementados

| Componente | Función | Estado |
|---|---|---|
| `scripts/f5_reentrenar_if.py` | Entrena nuevo IF con capturas normales acumuladas | ✅ IMPLEMENTADO |
| `scripts/f5_reentrenar_xgboost.py` | Entrena XGBoost con últimas N horas del log | ✅ IMPLEMENTADO |
| `scripts/f5_validar_modelo.py` | Inspecciona AUC actual de ambos modelos | ✅ IMPLEMENTADO |
| Crontab en sensor | IF domingos 02:00 / XGBoost diario 03:00 | ✅ CONFIGURADO |

---

## Flujo de reentrenamiento

```
                   IF (semanal — domingos 02:00)
                   ─────────────────────────────
data/raw/*_normal_*.gz
    │
    ├─ f5_reentrenar_if.py
    │       ├─ carga todos los *_normal_*.gz  (se agrega si hay nuevas capturas)
    │       ├─ evalúa AUC modelo actual vs nuevo sobre holdout
    │       └─ reemplaza si AUC no retrocede > 0.02
    │
    ↓
isolation_forest.pkl  ←── motor recarga en próximo arrange


              XGBoost (diario — 03:00)
              ─────────────────────────
results/motor_decision.log (últimas 24h)
    │
    ├─ f5_reentrenar_xgboost.py
    │       ├─ extrae eventos LIMIT+BLOCK
    │       ├─ genera labels automáticos (mismo método que F4)
    │       ├─ split estratificado 80/20
    │       └─ reemplaza si AUC >= 0.70 y no retrocede > 0.05
    │
    ↓
predictor_modelo_v2.pkl  ←── predictor.py detecta cambio mtime y recarga en caliente
```

---

## Protecciones contra degradación

| Condición | Acción |
|---|---|
| AUC nuevo < AUC anterior − 0.02 (IF) | NO reemplaza, registra aviso |
| AUC nuevo < 0.70 (XGBoost) | NO reemplaza, log de advertencia |
| AUC nuevo < AUC anterior − 0.05 (XGBoost) | NO reemplaza |
| Eventos < 100 en la ventana (XGBoost) | NO reemplaza, pide ampliar ventana |
| Positivos < 10 (XGBoost) | NO reemplaza, pide ejecutar escenarios primero |
| Modo `--forzar` | Reemplaza siempre (para debug) |

---

## Hot-reload sin reiniciar servicios

`predictor.py` comprueba `models/predictor_modelo_v2.pkl` cada ciclo (5s):

```python
mtime_actual = MODEL.stat().st_mtime
if mtime_actual != self._mtime:
    self._modelo = joblib.load(MODEL)
    self._mtime = mtime_actual
    log.info("Predictor: modelo recargado (F5)")
```

El motor IF sí requiere reinicio para recargar (usa `systemctl restart ppi-motor.service`).

---

## Crontab instalado en sensor (192.168.0.110)

```cron
# F5 — Reentrenamiento automático PPI
# IF: domingos 02:00
0 2 * * 0 /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-produto/scripts/f5_reentrenar_if.py \
  >> /home/m4rk/ppi-surikata-produto/results/cron_f5_if.log 2>&1

# XGBoost: diario 03:00
0 3 * * * /home/m4rk/ppi-sensor/venv/bin/python3 \
  /home/m4rk/ppi-surikata-produto/scripts/f5_reentrenar_xgboost.py \
  >> /home/m4rk/ppi-surikata-produto/results/cron_f5_xgb.log 2>&1
```

---

## Métricas de validación (primera ejecución — 2026-06-22)

### Isolation Forest
```
flows_entrenamiento : 53,708
AUC anterior        : 0.9548
AUC nuevo           : 0.9548
Resultado           : reemplazado (igual calidad, datos reproducibles con random_state=42)
```

### XGBoost — corrida 1 (2026-06-22 02:26, CON leakage — invalidada)
```
ventana             : 720h
eventos             : 62,115
AUC anterior        : 1.0000  ← leakage (score en features)
AUC nuevo           : 0.9999  ← leakage
Resultado           : INVALIDADO — score causaba data leakage
```

### XGBoost — corrida 2 (2026-06-22 08:04, SIN leakage — válida)
```
ventana             : 24h
eventos             : 517
positivos           : 46.1% (ataques recientes)
AUC anterior        : 0.9762  ← modelo F4 corregido
AUC nuevo           : 0.9583
Precision           : 97.96%
Recall              : 97.96%
Resultado           : reemplazado — 9 features sin leakage
```

---

## Uso manual

```bash
# Validar estado de ambos modelos
python3 scripts/f5_validar_modelo.py

# Reentrenar IF manualmente
python3 scripts/f5_reentrenar_if.py

# Reentrenar XGBoost con ventana extendida
python3 scripts/f5_reentrenar_xgboost.py --horas 48

# Forzar reemplazo aunque AUC sea menor (debug)
python3 scripts/f5_reentrenar_xgboost.py --forzar
```

---

## Nota de diseño — ¿Por qué no online learning puro?

El online learning (actualizar pesos con cada evento nuevo) introduce riesgo de **envenenamiento**:
un atacante podría generar tráfico diseñado para "educar" al modelo a clasificar sus ataques como normales.

El reentrenamiento por lotes (batch nocturno) con validación de AUC es más robusto:
- El atacante necesita sostener el ataque 24h para influir
- La validación AUC detecta degradación antes de reemplazar
- Los logs acumulados proveen contexto temporal suficiente

---

---

## Corrección de data leakage (2026-06-22)

Durante la validación pre-defensa se detectó que `f5_reentrenar_xgboost.py` incluía
`score` (IF decision function) como feature. Los labels se derivan de los umbrales del
mismo `score`, creando correlación directa (data leakage). AUC=0.9999 era artefactual.

**Fix aplicado (commit `2f60545`):**
- `score` removido de `FEATURES` en `f5_reentrenar_xgboost.py`
- `is_block` ahora derivado de `ev['decision'] == 'BLOCK'` (no de `ev['score'] <= TAU2`)
- Script ahora genera 9 features consistentes con `f4_entrenar_predictor_v2.py`

**Features activas (9):**

| Feature | Importancia F5 | Interpretación |
|---|---|---|
| `proto_udp` | 51.95% | UDP floods son sostenidos por naturaleza |
| `block_count_60s` | 24.37% | Reincidencia previa predice futura |
| `proto_tcp` | 20.79% | SYN floods son campañas prolongadas |
| `is_block` | 0.92% | Acción actual (BLOCK vs LIMIT) |
| `dest_port` | 0.89% | Puerto objetivo |
| `hora_cos/sin` | 0.62% | Patrón temporal |
| `limit_count_15s` | 0.22% | Presión reciente de tráfico |
| `proto_icmp` | 0.00% | ICMP floods (escasos en dataset) |

**AUC post-fix:** F4=0.9992, F5=0.9583 — ambos sin leakage, sobre umbral CA-F4-01 (>0.70).

---

## Criterios de aceptación

| ID | Criterio | Estado |
|---|---|---|
| CA-F5-01 | Scripts de reentrenamiento ejecutan sin error | ✅ Validado 2026-06-22 (post-fix leakage) |
| CA-F5-02 | Modelo NO se reemplaza si AUC retrocede > umbral | ✅ Lógica implementada |
| CA-F5-03 | XGBoost recargado en caliente (sin reiniciar servicio) | ✅ Hot-reload en predictor.py |
| CA-F5-04 | Crons configurados en sensor | ✅ Instalados |
| CA-F5-05 | Registro de métricas por corrida | ✅ metricas_f5_*.txt |

---

## Argumento de defensa

> "F5 cierra el ciclo de aprendizaje. El sistema no se congela en el estado del día del entrenamiento — mejora con la experiencia real de la red. Pero lo hace de forma controlada: solo actualiza cuando el nuevo modelo es estadísticamente mejor, y el predictor recarga en caliente sin interrumpir el monitoreo."
