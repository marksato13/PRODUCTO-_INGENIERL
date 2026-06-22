# Sistema de Detección Temprana de Anomalías en Redes
## PPI — Universidad Peruana Unión | Rubén Mark Salazar Tocas
> Estado: **todas las fases F1–F6 completadas y validadas** · Actualizado 2026-06-22

---

## Flujo del sistema (secuencia de fases)

```
Tráfico de red
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  F1 — CAPTURA                                                   │
│  Suricata 7.0.3 · ens35 pasivo · 9 escenarios · 47 capturas    │
│  Output: data/raw/*_eve.json.gz                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  F2 — MODELO ISOLATION FOREST                                   │
│  fase3_entrenar.py + fase3_evaluar.py                           │
│  14 features · Split 80/20 aleatorio · n=300 árboles           │
│  AUC=0.8998 · τ1=−0.4459 · τ2=−0.6027                         │
│  Output: isolation_forest.pkl · scaler.pkl · metricas_offline  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  F3 — MOTOR DE DECISIÓN + CONTROL INLINE                        │
│  motor_decision.py (tail eve.json → 14 feat → IF score)        │
│  PERMIT (>τ1) · LIMIT (τ2<score≤τ1) · BLOCK (≤τ2)             │
│  + BF-SSH heurístico · + HTTP-Abuse heurístico                 │
│  + Bloqueo progresivo: #1=5min · #2=30min · #3=∞              │
│  SSH → ipset add ppi_blocked/ppi_limited → 192.168.0.120       │
│  Dashboard SSE :8080 · Telegram alerts                          │
│  Output: motor_decision.log · block_counts.json                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  F4 — PREDICTOR XGBOOST v2                                      │
│  predictor.py (lee motor_decision.log en tiempo real)           │
│  9 features comportamentales (sin score — leakage corregido)   │
│  AUC=0.9992 · Split 80/20 estratificado                        │
│  P<40%→silencio · 40-70%→AVISO · ≥70%→ALERTA-PREDICTIVA       │
│  Output: predicciones en dashboard · alertas Telegram           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  F5 — APRENDIZAJE CONTINUO                                      │
│  f5_reentrenar_if.py (domingo 02:00 · cron)                    │
│  f5_reentrenar_xgboost.py (diario 03:00 · cron)               │
│  Hot-reload sin reiniciar servicio · protección AUC             │
│  Output: isolation_forest.pkl · predictor_modelo_v2.pkl        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  F6 — VALIDACIÓN                                                │
│  40 corridas · 9 escenarios (A/B/C) · 2026-06-16              │
│  + validaciones en vivo 2026-06-22                             │
│  Disponibilidad=100% · ITL=0% · P95=34.8ms · Lead≈62s         │
│  Output: resultados_f6_completo.csv · graficas_f6/ (7 PNG)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estado de fases

| Fase | Nombre | Estado | Archivo |
|---|---|---|---|
| F1 | Captura y Preparación de Datos | ✅ COMPLETA | [fases/F1_captura_datos.md](fases/F1_captura_datos.md) |
| F2 | Detección de Anomalías (IF) | ✅ COMPLETA | [fases/F2_deteccion_if.md](fases/F2_deteccion_if.md) |
| F3 | Motor de Decisión + Control Inline | ✅ COMPLETA | [fases/F3_control_motor.md](fases/F3_control_motor.md) |
| F4 | Predictor XGBoost v2 | ✅ COMPLETA | [fases/F4_prediccion_v2.md](fases/F4_prediccion_v2.md) |
| F5 | Aprendizaje Continuo | ✅ COMPLETA | [fases/F5_aprendizaje.md](fases/F5_aprendizaje.md) |
| F6 | Validación (40 corridas) | ✅ COMPLETA | [fases/F6_validacion.md](fases/F6_validacion.md) |

---

## Estructura de carpetas

```
docs/ppi_documentacion2/
├── INDICE.md                        ← este archivo
│
├── fases/                           ← especificación técnica de cada fase
│   ├── F1_captura_datos.md          F1: Suricata, escenarios, capturas .gz
│   ├── F2_deteccion_if.md           F2: IF n=300, 14 features, τ1/τ2, AUC=0.8998
│   ├── F3_control_motor.md          F3: motor_decision.py, ipset, dashboard, Telegram
│   ├── F4_prediccion_v2.md          F4: XGBoost v2, 9 features, AUC=0.9992
│   ├── F5_aprendizaje.md            F5: cron IF/XGBoost, hot-reload, protección AUC
│   └── F6_validacion.md             F6: 40 corridas, métricas, validaciones en vivo
│
├── ppt/                             ← material para la sustentación
│   ├── ppt_sustentacion.md          guión completo (15 slides, 20 min)
│   ├── d1_topologia.md              draw.io XML — topología de red
│   ├── d2_pipeline.md               draw.io XML — pipeline 6 fases
│   ├── d3_flujo.md                  draw.io XML — flujo de decisión
│   └── d4_problema.md               draw.io XML — ANTES/DESPUÉS + árbol OG/OEs
│
├── informe/                         ← partes del informe de resultados
│   ├── parte_i_introduccion.md      planteamiento, objetivos, justificación, alcance
│   ├── parte_ii_marco_teorico.md    IF, Suricata, ipset, XGBoost, SSE, referencias
│   ├── parte_iii_metodologia.md     F1–F6 descripción metodológica
│   ├── parte_iv_resultados.md       OE1–OE3, métricas, validaciones, limitaciones
│   ├── parte_v_conclusiones.md      conclusiones C1–C4, trabajos futuros
│   └── plan_redaccion.md            índice detallado para redacción final
│
└── defensa/                         ← preparación para el jurado
    ├── LIMITACIONES.md              10 limitaciones, mitigaciones, métricas reales
    └── checklist_defensa.md         tareas pendientes y estado de la defensa
```

---

## Topología del laboratorio

| IP | VM | Rol |
|---|---|---|
| 192.168.0.10 | Win11 | Cliente |
| 192.168.0.20 | Ubuntu Desktop | Admin / origen tráfico normal |
| 192.168.0.100 | Kali Linux | Origen tráfico anómalo |
| 192.168.0.110 | Ubuntu Sensor | Suricata + motor + predictor + dashboard |
| 192.168.0.120 | Ubuntu Server | Servicio nginx:80, SSH:22 + ipset/iptables |

---

## Métricas finales validadas

| Modelo / Fase | Métrica clave | Valor |
|---|---|---|
| IF (F2) | AUC-ROC | **0.8998** |
| IF (F2) | Precision / Recall / F1 | 99.54% / 99.40% / 0.9947 |
| IF (F2) | Latencia P95 (por flujo) | **34.8 ms** (< 500ms ✅) |
| XGBoost (F4) | AUC-ROC (sin leakage) | **0.9992** |
| Sistema (F6) | Disponibilidad | **100%** |
| Sistema (F6) | ITL | **0%** |
| Sistema (F3/F6) | Lead time SYN Flood | **~62 s** |
| Sistema (F3/F6) | Lead time BF SSH (BLOCK) | **60 s** |

---

## Argumentos clave de defensa

**"¿Por qué Isolation Forest?"**
No requiere etiquetas manuales de ataque. Aprende el comportamiento normal y detecta cualquier desviación — incluyendo ataques que nunca ha visto antes. Ideal para redes reales donde los atacantes constantemente varían sus técnicas.

**"¿Por qué XGBoost complementa al IF?"**
El IF clasifica flujo por flujo sin memoria temporal. El XGBoost analiza el patrón de eventos LIMIT/BLOCK de una IP a lo largo del tiempo para predecir si el ataque va a persistir — permite alertar antes de que escale.

**"El FPR es 20.47% — ¿no es muy alto?"**
Solo en τ1 (zona LIMIT). El FPR operativo es 0% porque la whitelist cubre todos los hosts legítimos. En las 40 corridas de F6, ITL=0%: ningún flujo normal fue bloqueado incorrectamente.

**"¿El sistema aprende solo?"**
Sí. F5 reajusta el IF semanalmente y el XGBoost diariamente con datos operativos reales. El reentrenamiento tiene protecciones: el modelo nuevo solo reemplaza al anterior si AUC no retrocede más del umbral establecido. El predictor recarga en caliente sin interrumpir el monitoreo.
