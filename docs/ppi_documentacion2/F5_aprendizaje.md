# F5 — Aprendizaje Continuo (Reentrenamiento Automático)
**Estado: 📋 PLANIFICADA**

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

## Componentes a implementar

| Componente | Función | Estado |
|---|---|---|
| `scripts/reentrenar_if.py` | Entrena nuevo IF con PERMIT recientes | ⬜ PENDIENTE |
| `scripts/reentrenar_xgboost.py` | Entrena nuevo XGBoost con log 24h | ⬜ PENDIENTE |
| `scripts/validar_modelo.py` | Compara AUC nuevo vs actual → decide si reemplazar | ⬜ PENDIENTE |
| Cron semanal (IF) | Ejecuta reentrenar_if.py cada domingo 02:00 | ⬜ PENDIENTE |
| Cron noche (XGBoost) | Ejecuta reentrenar_xgboost.py cada día 03:00 | ⬜ PENDIENTE |
| Hot-reload en predictor.py | Detecta nuevo .pkl por mtime → recarga sin reiniciar | ⬜ PENDIENTE |

---

## Lógica de reentrenamiento IF

```
Cada domingo 02:00:
  1. Extraer flujos PERMIT de los últimos 7 días desde motor_decision.log
  2. Entrenar nuevo IF con esos flujos (solo tráfico normal)
  3. Derivar nuevos τ1/τ2 con auc_roc_umbrales.py
  4. Validar: ¿AUC nuevo ≥ AUC actual?
     SÍ → reemplazar isolation_forest.pkl + metricas_offline.txt
     NO → mantener modelo actual, log de aviso
  5. Motor lee τ1/τ2 al arranque siguiente (o señal de reload)

⚠️ NUNCA entrenar IF con flujos BLOCK/LIMIT — normalizaría los ataques
```

---

## Lógica de reentrenamiento XGBoost

```
Cada día 03:00:
  1. Extraer LIMIT+BLOCK de las últimas 24h desde motor_decision.log
  2. Generar labels automáticos (BLOCK en próximos 60s = 1)
  3. Entrenamiento incremental: xgb.train(..., xgb_model=modelo_actual)
  4. Validar: ¿AUC nuevo ≥ AUC actual?
     SÍ → reemplazar predictor_modelo_v2.pkl
     NO → mantener actual
  5. predictor.py detecta cambio de mtime → hot-reload automático

✅ XGBoost SÍ puede entrenar con BLOCK+LIMIT — es supervisado
```

---

## Hot-reload (sin reiniciar servicios)

```python
# En predictor.py — ciclo cada 10s
mtime_actual = os.path.getmtime('models/predictor_modelo_v2.pkl')
if mtime_actual != mtime_cargado:
    modelo = joblib.load('models/predictor_modelo_v2.pkl')
    mtime_cargado = mtime_actual
    log.info("Modelo recargado automáticamente")
```

---

## Riesgo: envenenamiento del modelo

Un atacante podría disfrazar tráfico malicioso como normal para que el IF "aprenda" que es correcto.

**Mitigación:**
- IF solo entrena con PERMIT (score > τ1) — el atacante necesita pasar el IF para envenenar
- Validación de AUC antes de reemplazar — una degradación brusca se rechaza
- Reentrenamiento periódico (no en tiempo real) — reduce la superficie de ataque

---

## Criterios de aceptación

| ID | Criterio | Estado |
|---|---|---|
| CA-F5-01 | Cron IF ejecuta sin errores cada domingo | ⬜ pendiente |
| CA-F5-02 | Cron XGBoost ejecuta sin errores cada noche | ⬜ pendiente |
| CA-F5-03 | Modelo reemplazado solo si AUC mejora | ⬜ pendiente |
| CA-F5-04 | Hot-reload sin reiniciar ppi-predictor.service | ⬜ pendiente |
| CA-F5-05 | IF nunca entrena con flujos BLOCK/LIMIT | ⬜ pendiente |
| CA-F5-06 | Log de cada reentrenamiento con AUC antes/después | ⬜ pendiente |

---

## Argumento de defensa

> "En la versión 2, el sistema se adapta automáticamente. El IF se reajusta al tráfico normal de la red actual, y el XGBoost actualiza sus predicciones con ataques reales recientes. No dependemos de reglas fijas ni de reentrenamiento manual. El sistema mejora con la experiencia operativa."

> "No usamos aprendizaje online puro para evitar el riesgo de envenenamiento. En cambio, el reentrenamiento periódico con validación de AUC garantiza que el modelo solo mejora, nunca regresiona."
