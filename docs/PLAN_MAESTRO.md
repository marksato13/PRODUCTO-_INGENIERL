# PLAN MAESTRO — Sistema de Detección Temprana de Anomalías en Red
## PPI UPeU 2026 | Rubén Mark Salazar Tocas

> **Última actualización:** 2026-06-21  
> **Estado general:** F1–F6 completadas ✅ | F7 en rediseño 🔄 | F8 completa ✅

---

## Visión del sistema

Un sistema IDS/IPS con tres capacidades integradas que operan en orden secuencial:

```
PREDECIR (T≈2s) → DETECTAR (T≈5s) → ACTUAR (T≈5s)
```

| Capacidad | Componente | Cuándo | Estado |
|---|---|---|---|
| Predecir | XGBoost predictor v2 | Antes del BLOCK | 🔄 Rediseño |
| Detectar | Isolation Forest + Suricata | Por flujo individual | ✅ |
| Actuar | ipset/iptables enforcement | Tras detección | ✅ |
| Visualizar | Dashboard Flask + SSE | Tiempo real | ✅ |
| Aprender | Auto-reentrenamiento XGBoost | Semanal automático | 📋 Pendiente |

---

## Mapa de fases

```
F1 ──► F2 ──► F3 ──► F4 ──► F5 ──► F6       (BASE: completada)
                              │
                              ▼
                         F7 (nuevo) ──► F8    (EXTENSIÓN: en progreso)
                              │
                              ▼
                     Auto-reentrenamiento     (AUTONOMÍA: pendiente)
```

---

## Estado por fase

| Fase | Nombre | Estado | Criterio cumplido |
|---|---|---|---|
| F1 | Entorno laboratorio | ✅ COMPLETA | 5 VMs, Suricata 7.0.3, conectividad SSH |
| F2 | Captura de tráfico | ✅ COMPLETA | 47 capturas, 9 escenarios, split 70/15/15 |
| F3 | Isolation Forest | ✅ COMPLETA | AUC=0.8998, Precision=99.54%, Recall=99.40% |
| F4 | Motor de decisión | ✅ COMPLETA | Latencia P95=34.8ms < 500ms requerido |
| F5 | Control inline | ✅ COMPLETA | ipset BLOCK/LIMIT en servidor, ITL=0% |
| F6 | Validación 40 corridas | ✅ COMPLETA | Disponibilidad=100%, ITL=0% |
| F7 | Predictor v2 (nueva señal) | 🔄 EN PROGRESO | Pendiente: T_alerta < T_block |
| F8 | Dashboard web | ✅ COMPLETA | SSE funcionando, gauge predictor, tabla IPs |
| AUTO | Auto-reentrenamiento | 📋 PENDIENTE | Cron semanal, hot-reload sin reinicio |

---

## Lo que NO cambia (F1–F6 + F8)

Las fases F1 a F6 están validadas con métricas reales. No se modifican.  
El dashboard (F8) funciona y no requiere cambios de código.  
El motor de decisión (F4) y el enforcement (F5) funcionan correctamente.

**Regla:** si no está roto, no se toca.

---

## Lo que cambia — F7 Predictor v2

### Problema con v1
El predictor actual usa gaps entre STATS (cada 500 flujos) como señal.  
Resultado medido: alerta en T=89s, BLOCK del IF en T=11s → orden invertido.

### Solución v2
Usar eventos LIMIT como señal precursora del BLOCK.  
LIMIT aparece en T≈1s, predictor alerta en T≈2s, BLOCK en T≈5s → orden correcto.

### Datos disponibles para entrenamiento (sin correr nada nuevo)
- 50,134 eventos LIMIT en motor_decision.log
- 11,977 eventos BLOCK en motor_decision.log
- Período: 2026-06-02 al 2026-06-21
- Etiquetado: automático (LIMIT→BLOCK/10s = label=1)

---

## Criterios de aceptación globales del sistema completo

Para que el sistema se considere completo y defendible:

### CA-01 Detección (IF)
- [ ] AUC-ROC ≥ 0.85 ← ya cumplido (0.8998) ✅
- [ ] Precision ≥ 95% ← ya cumplido (99.54%) ✅
- [ ] Recall ≥ 95% ← ya cumplido (99.40%) ✅
- [ ] Latencia P95 < 500ms ← ya cumplido (34.8ms) ✅

### CA-02 Predicción (XGBoost v2)
- [ ] T_alerta < T_block en corridas de ataque (predictor anticipa al IF)
- [ ] FPR = 0% en corridas de tráfico normal (sin falsas alarmas)
- [ ] TPR ≥ 80% en corridas de ataque (detecta la mayoría)
- [ ] Lead time promedio ≥ 2s (margen real de anticipación)

### CA-03 Acción (ipset)
- [ ] Disponibilidad servidor = 100% durante ataques ✅
- [ ] ITL (interrupciones tráfico legítimo) = 0% ✅
- [ ] Whitelist nunca bloqueada ✅

### CA-04 Autonomía (auto-reentrenamiento)
- [ ] Cron semanal configrado en sensor
- [ ] Script entrena sin intervención humana
- [ ] Hot-reload: modelo se recarga sin reiniciar servicio
- [ ] Si AUC nuevo < AUC anterior → conserva modelo previo

### CA-05 Visibilidad (dashboard)
- [ ] Gauge P(ataque) actualiza cada 2s ✅
- [ ] ALERTA aparece en dashboard ANTES que BLOCK en tabla ✅ (tras v2)
- [ ] Feed de eventos muestra secuencia: ALERTA → ANOMALÍA → BLOCK

---

## Estructura de carpetas del proyecto

```
docs/
├── PLAN_MAESTRO.md                    ← este archivo
├── arquitectura/
│   ├── FIX_GLOBAL_ARQUITECTURA.md
│   ├── PROPOSITO_SISTEMA_Y_CHECKLIST_CAMBIO.md
│   └── APRENDIZAJE_AUTOMATICO_Y_REENTRENAMIENTO.md
└── ppi_documentacion/
    ├── F1_entorno_laboratorio/        ✅ completa
    ├── F2_captura_trafico/            ✅ completa
    ├── F3_modelado_offline/           ✅ completa
    ├── F4_motor_decision/             ✅ completa
    ├── F5_control_inline/             ✅ completa
    ├── F6_validacion/                 ✅ completa
    ├── F7_predictor_v2/               🔄 en progreso
    │   ├── F7_especificacion.md
    │   ├── F7_checklist.md
    │   └── F7_resultados.md
    └── F8_dashboard/                  ✅ completa
        └── F8_especificacion.md

scripts/
├── motor_decision.py                  ✅ no cambiar
├── predictor.py                       🔄 reescribir señal
├── dashboard_web.py                   ✅ no cambiar
├── enforce.sh                         ✅ no cambiar
└── entrenar_predictor_v2.py           📋 crear nuevo

models/
├── isolation_forest.pkl               ✅ no cambiar
├── scaler.pkl                         ✅ no cambiar
├── predictor_modelo.pkl               ⚠️ obsoleto (señal incorrecta)
└── predictor_modelo_v2.pkl            📋 generar con nuevo script
```

---

## Próximos pasos en orden

1. **[HOY]** Crear `scripts/entrenar_predictor_v2.py`
2. **[HOY]** Correr entrenamiento → generar `predictor_modelo_v2.pkl`
3. **[HOY]** Reescribir `scripts/predictor.py` con nueva señal LIMIT
4. **[HOY]** Reiniciar `ppi-predictor` y validar orden: T_alerta < T_block
5. **[HOY]** Correr 5 corridas de ataque + 5 normales para medir lead time real
6. **[HOY]** Documentar resultados en `F7_resultados.md`
7. **[ESTA SEMANA]** Configurar cron de auto-reentrenamiento
8. **[ESTA SEMANA]** Actualizar slides de defensa con flujo correcto
