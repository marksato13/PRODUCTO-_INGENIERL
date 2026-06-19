# Plan: Autoencoder en Producción — Comparación con Isolation Forest

**Fecha:** 2026-06-19  
**Estado:** PLANIFICACIÓN → IMPLEMENTACIÓN  
**Restricción crítica:** El MVP (motor_decision.py, isolation_forest.pkl, metricas_offline.txt) NO se toca en ningún momento.

---

## Decisión de tecnología

**MLPRegressor (sklearn)** como autoencoder, no TensorFlow/Keras.

| Criterio | MLPRegressor sklearn | TensorFlow/Keras |
|---|---|---|
| Dependencias nuevas | 0 (ya instalado) | ~2 GB instalación |
| Serialización | joblib (igual que IF) | .keras / .h5 |
| API | `fit(X, X)` / `predict(X)` | `fit(X, X)` / `predict(X)` |
| Velocidad inferencia | ~1 ms/flujo | ~0.5 ms/flujo |
| Compatibilidad sensor | ✅ inmediata | requiere pip install |

Arquitectura: `14 → 8 → 4 → 8 → 14` (relu, max_iter=500, solver=adam)  
Score: `−MSE(X, reconstruct(X))` → mismo convenio que IF (menor = más anómalo)

---

## Qué cambia en cada fase

### F1 — Entorno de laboratorio
**Sin cambios.** Misma topología, mismas VMs, mismo Suricata.

### F2 — Captura de tráfico
**Sin cambios.** El AE consume los mismos .gz que el IF.  
- `*_normal_*.gz` → entrenamiento AE  
- `*_anom_*.gz` → evaluación ROC AE  
- `*_mixto_*.gz` → AUC por escenario AE

### F3 — Modelado offline ⭐ CAMBIOS NUEVOS

| Archivo nuevo | Función |
|---|---|
| `scripts/comparacion/ae/fase3_ae_entrenar.py` | Lee Grupo A · split 80/20 · entrena MLPRegressor(14→8→4→8→14) · guarda pkl |
| `scripts/comparacion/ae/fase3_ae_evaluar.py` | ROC sobre −MSE · deriva τ1_ae y τ2_ae · escribe ae_metricas_offline.txt |
| `models/ae/ae_autoencoder.pkl` | MLPRegressor serializado con joblib |
| `models/ae/ae_scaler.pkl` | StandardScaler ajustado solo en 80% (igual que IF) |
| `results/ae/ae_metricas_offline.txt` | τ1_ae, τ2_ae, AUC_ae — fuente de verdad para el motor |
| `results/ae/ae_auc_roc.png` | Curva ROC del AE |

**Invariante:** Se usa el mismo X_train del IF (mismos .gz, mismos filtros, mismo split random_state=42).  
Esto garantiza comparación justa: ambos modelos ven exactamente los mismos datos de entrenamiento.

### F4 — Motor de decisión ⭐ ARCHIVO NUEVO, MVP INTACTO

**NO se modifica** `scripts/motor_decision.py` (IF puro, MVP).

Se crea `scripts/motor_universal.py` con patrón Adaptador:

```
config/modelo_activo.txt → "IF" o "AE"
         │
         ▼
   AdaptadorIF.score(X)          AdaptadorAE.score(X)
   = model.score_samples(X)      = −MSE(X, model.predict(X))
         │                                │
         └──────────── score ─────────────┘
                          │
               (mismo rango: menor = más anómalo)
                          │
               clasificar_grado(score, τ1, τ2)
               → PERMIT / LIMIT / BLOCK
```

**Lógica de switching (segundos):**
```bash
# Activar AE:
echo "AE" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
sudo systemctl restart ppi-motor-universal.service

# Volver a IF:
echo "IF" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
sudo systemctl restart ppi-motor-universal.service
```

El MVP sigue disponible siempre:
```bash
sudo systemctl start ppi-motor.service    # ← IF puro, nunca tocado
sudo systemctl start ppi-motor-universal.service  # ← IF o AE según config
# NUNCA correr ambos a la vez (conflicto ipset)
```

### F5 — Control inline
**Sin cambios.** `enforce.sh`, iptables, ipset, whitelist, dashboard — todo igual.  
El motor universal emite exactamente las mismas llamadas SSH a enforce.sh.

### F6 — Validación
**Sin cambios para el MVP.**  
Nuevo: `scripts/comparacion/ae/f6_ae_comparacion.py` — corre 10 corridas con AE y compara métricas contra resultados_f6_completo.csv del IF.

---

## Estructura de directorios (solo lo nuevo)

```
ppi-surikata-producto/
├── config/
│   └── modelo_activo.txt              ← "IF" (default) o "AE"
│
├── models/
│   ├── isolation_forest.pkl           ← MVP sin tocar
│   ├── scaler.pkl                     ← MVP sin tocar
│   └── ae/
│       ├── ae_autoencoder.pkl         ← NUEVO
│       └── ae_scaler.pkl              ← NUEVO
│
├── results/
│   ├── metricas_offline.txt           ← MVP sin tocar
│   └── ae/
│       ├── ae_metricas_offline.txt    ← NUEVO
│       ├── ae_auc_roc.png             ← NUEVO
│       └── ae_por_escenario.txt       ← NUEVO
│
└── scripts/
    ├── motor_decision.py              ← MVP sin tocar (IF puro)
    ├── motor_universal.py             ← NUEVO (IF o AE según config)
    └── comparacion/ae/
        ├── fase3_ae_entrenar.py       ← NUEVO
        ├── fase3_ae_evaluar.py        ← NUEVO
        └── f6_ae_comparacion.py       ← NUEVO
```

**Archivos del MVP que NUNCA se modifican:**
- `scripts/motor_decision.py`
- `models/isolation_forest.pkl`
- `models/scaler.pkl`
- `models/features.csv`
- `results/metricas_offline.txt`
- `scripts/enforce.sh`
- `systemd/ppi-motor.service`

---

## Comparación técnica IF vs AE

| Aspecto | Isolation Forest | Autoencoder (MLPRegressor) |
|---|---|---|
| Paradigma | Isolation (partición aleatoria) | Reconstrucción (compresión) |
| Score | `score_samples(X)` ∈ [−1, 0] | `−MSE(X, X̂)` ∈ (−∞, 0] |
| Entrenamiento | O(n log n), <10s | O(n × epochs), ~30-60s |
| Sensible a escala | No (árboles invariantes) | Sí (requiere StandardScaler) |
| Interpretabilidad | Baja | Muy baja |
| Ventaja esperada | Robusto, rápido, probado | Puede capturar patrones no lineales complejos |

---

## Orden de implementación

1. `mkdir -p config models/ae results/ae scripts/comparacion/ae`
2. `echo "IF" > config/modelo_activo.txt`
3. Escribir y ejecutar `fase3_ae_entrenar.py` → genera ae_autoencoder.pkl
4. Escribir y ejecutar `fase3_ae_evaluar.py` → genera ae_metricas_offline.txt
5. Escribir `motor_universal.py`
6. Crear `ppi-motor-universal.service`
7. Arrancar servicio con AE y verificar logs
8. Cambiar a IF y verificar que el MVP sigue intacto
