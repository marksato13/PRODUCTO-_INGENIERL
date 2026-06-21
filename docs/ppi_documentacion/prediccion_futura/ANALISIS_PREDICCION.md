# Análisis Técnico: Predicción de Incidentes Futuros como Extensión del Sistema

**Proyecto:** PPI UPeU 2026 — Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Autores:** Rubén Mark Salazar Tocas · Elías Uziel Sauñe Fernández  
**Rol del análisis:** Evaluación crítica independiente — decisión arquitectónica  
**Fecha:** 2026-06-20

---

## Estado del sistema actual (referencia objetiva)

Antes de evaluar cualquier extensión, el punto de partida es este:

| Dimensión | Estado actual | Evidencia |
|---|---|---|
| Fases completadas | F1–F6 (todas) | 40 corridas F6 certificadas |
| AUC-ROC | 0.8998 | `metricas_offline.txt` |
| Recall | 99.40% | 598,285 ataques procesados |
| Latencia P95 | 34.8 ms | `latencia_pipeline.txt` |
| Disponibilidad | 100% | 40/40 corridas |
| ITL | 0% | 0 bloqueos de tráfico legítimo en producción |
| Lead time SYN Flood | 61.92 s | Corrida 11, reproducible |
| Datos disponibles | 17 días, 47 capturas, 40 corridas controladas | `data/raw/`, `results/resultados_f6_completo.csv` |

**El sistema ya cumple todos los requisitos del PPI.** La evaluación de extensiones debe hacerse contra ese baseline, no en el vacío.

---

## 1. ¿La arquitectura actual ya es una propuesta sólida?

**Sí, es una propuesta sólida y diferenciada.**

El sistema no solo detecta anomalías — cierra el ciclo completo: captura → extracción de features → scoring → decisión tri-nivel (PERMIT/LIMIT/BLOCK) → enforcement automático con ipset/iptables en el servidor destino → alerta Telegram. Eso es un IDPS funcional completo, no un prototipo de laboratorio.

Lo que lo diferencia de papers típicos "Suricata + IF":
- Motor de decisión en vivo con dos umbrales calibrados (τ1 Youden, τ2 FPR≤2%)
- Heurísticos complementarios específicos por protocolo (HTTP_ABUSE, BRUTE_FORCE_SSH)
- Control inline real: ipset `ppi_blocked`/`ppi_limited` con timeout, no simulado
- 40 corridas de validación en vivo (la mayoría de papers solo evalúan offline)
- Experimento comparativo con 7 modelos sobre el mismo dataset

No necesita predicción para ser defendible. Ya es más completo que la mayoría de trabajos de pregrado en el tema.

---

## 2. ¿La predicción futura aporta valor?

Técnicamente, sí — en un sistema real de producción. Pero hay que separar dos preguntas:

**¿Aporta valor científico al problema?** Sí. Pasar de detección reactiva a alerta preventiva es un avance real. Si un modelo puede decir "en los próximos 10 minutos hay 80% de probabilidad de ataque SYN Flood", el operador puede activar rate limiting preventivo.

**¿Aporta valor en este proyecto, en este momento, con estos datos?** Esto es lo crítico — y la respuesta es condicionada. Ver §7.

---

## 3. ¿Dónde encaja la predicción?

| Opción | Evaluación |
|---|---|
| **A — Solo detección + mitigación** | Sistema ya completo y certificado. Defensa sólida. |
| **B — Predicción integrada en la tesis** | Posible, pero con riesgo alto dado el estado actual de los datos. |
| **C — Predicción como trabajo futuro** | La más honesta académicamente. Permite mencionarla sin comprometerse. |

**Recomendación anticipada: C**, con un matiz importante explicado en §15.

---

## 4. ¿Qué problema resolvería la predicción que IF+Suricata no resuelve?

IF detecta anomalías *cuando ya ocurren* — es reactivo por definición. Detecta que hay un SYN Flood en curso a los ~62 segundos. Durante esos 62 segundos el servidor ya está bajo ataque.

Un módulo predictivo resolvería:
- **Alerta proactiva:** "En los próximos X minutos, probabilidad de ataque = Y%"
- **Pre-activación de defensas:** habilitar rate limiting antes de que el ataque escale
- **Correlación temporal:** detectar patrones como "siempre hay PortScan 5 minutos antes de SYN Flood" (reconocimiento antes del ataque)

Pero hay una pregunta honesta que responder primero: **¿existen esos patrones temporales en los datos de este laboratorio?**

En un entorno real (una empresa con tráfico orgánico 24/7), sí. En un laboratorio donde los ataques los dispara manualmente Kali a pedido, los "patrones temporales" son ruido estadístico, no señales reales.

---

## 5. Riesgo de complejidad innecesaria

| Riesgo | Probabilidad | Impacto |
|---|---|---|
| Los datos no tienen suficiente señal temporal | **Alta** | Los modelos predicen mejor que azar solo por sobreajuste |
| El modelo predictivo se convierte en el foco, eclipsando F1-F6 | Media | Los asesores cuestionan la coherencia del PPI |
| Métricas de predicción son difíciles de validar en laboratorio controlado | **Alta** | No hay forma de saber si el modelo predice real o memoriza |
| Tiempo de implementación > 2 semanas adicionales | Media | Riesgo de presentar algo incompleto |
| Los jurados preguntan por las 40 corridas del módulo predictivo | Media | No hay corridas análogas para el predictor |

El riesgo principal es de **validez metodológica**: si el predictor se entrena sobre ataques disparados manualmente en un laboratorio, las "predicciones" son triviales (el modelo aprende que los ataques pasan en ciertos horarios de las sesiones de prueba, no porque exista una señal real).

---

## 6. Datos históricos que necesitaría un módulo predictivo

Para modelos de series temporales se requiere:

| Dato | Descripción | Formato necesario |
|---|---|---|
| Serie de eventos de ataque | Timestamp + tipo + intensidad por ventana temporal | 1 fila por intervalo (ej. 1 min) |
| Patrones de tráfico previos al ataque | Features de flujos en las N ventanas antes del ataque | Secuencias de longitud fija |
| Regularidad temporal real | Ataques que ocurren por razones externas (no disparados manualmente) | Datos de semanas/meses |
| Diversidad de condiciones | Días con y sin ataque, horas, cargas variables | Balance de clases temporales |

**Mínimos prácticos:**
- ARIMA/SARIMA: ≥200 observaciones en la serie temporal (mínimo 200 ventanas de 1 min = 3.3 horas continuas de datos anotados)
- Prophet: ≥365 observaciones para capturar estacionalidad (no viable en este laboratorio)
- LSTM/GRU: ≥1,000 secuencias de entrenamiento (no se tienen)
- XGBoost temporal: ≥500 ventanas con features de contexto previo

---

## 7. ¿Los datos actuales son suficientes?

**No para un modelo predictivo robusto.**

| Recurso disponible | Cantidad | Suficiente para predicción |
|---|---|---|
| Días de datos | 17 (02-jun al 19-jun) | ❌ Necesita meses para estacionalidad |
| Corridas F6 | 40 | ❌ Muy pocas secuencias temporales para LSTM/GRU |
| Motor decision log | 1,177,819 líneas | ⚠️ Hay series de estadísticas cada 18s, aprovechable solo para XGBoost simple |
| Ataques por tipo | ~7 por tipo (6 tipos) | ❌ Mínimo 50-100 por tipo para predictor robusto |
| Patrón temporal orgánico | Inexistente (ataques manuales) | ❌ No hay señal temporal real |

**Lo que sí es aprovechable:** las estadísticas de `motor_decision.log` (flows, anomalías, http_abuse cada 18 segundos) podrían usarse para un predictor muy simple de "tasa de anomalía en próximos N segundos". Esto es técnicamente un experimento de series temporales, pero con la limitación de que los patrones son de sesiones de laboratorio, no tráfico orgánico.

---

## 8. Comparación de modelos para predicción temporal

| Modelo | AUC típico* | Implementación | Datos mínimos | Interpretabilidad | Viabilidad pregrado |
|---|---|---|---|---|---|
| **ARIMA** | 0.65–0.75 | Fácil (statsmodels) | ~200 obs | Alta | ✅ Alta |
| **SARIMA** | 0.68–0.78 | Media | ~500 obs + estacionalidad | Alta | ⚠️ Media |
| **Prophet** | 0.70–0.80 | Muy fácil (1 función) | ≥365 obs | Media | ⚠️ Datos insuficientes |
| **LSTM** | 0.75–0.90 | Difícil (PyTorch/TF) | ≥1000 seqs | Baja | ❌ Complejo |
| **GRU** | 0.74–0.88 | Difícil | ≥1000 seqs | Baja | ❌ Complejo |
| **XGBoost temporal** | 0.72–0.85 | Media (features manuales) | ~300–500 obs | Media | ✅ Alta |
| **RF temporal** | 0.70–0.82 | Media | ~300–500 obs | Media | ✅ Alta |

*En datasets reales de series de eventos de red. En datos de laboratorio controlado, todos pueden sobreajustar.

**Más adecuado para este proyecto si se implementa: XGBoost con ventanas temporales.**

Razones:
- Familiar (ya usamos XGBoost en el experimento comparativo)
- No requiere redes neuronales ni frameworks pesados
- Features interpretables: `anomalias_t-1`, `anomalias_t-2`, `http_abuse_rate`, `hora_del_dia`
- El asesor puede entender y validar los resultados
- Puede entrenarse con las series de estadísticas del motor_decision.log
- Produce probabilidades con `predict_proba`, directamente integrables

---

## 9. Recomendación de modelo (si se implementa)

**XGBoost con features de ventana deslizante** sobre las series de estadísticas del motor.

Pipeline:
```
motor_decision.log (estadísticas cada 18s)
→ Parsear: timestamp, flows, anomalías, http_abuse, bloqueados
→ Agregar en ventanas de 60s
→ Construir features: tasa_anomalía_t-1, tasa_anomalía_t-2, delta_anomalía, hora
→ Target: ¿habrá BLOCK en los próximos 60s? (binario)
→ XGBClassifier con cross-validation temporal (no aleatoria)
→ Output: P(ataque en próximos 60s)
```

Advertencia académica: los resultados serán optimistas porque los ataques fueron manuales y sistemáticos. Debe documentarse explícitamente como **prueba de concepto en entorno controlado**, no como predictor validado en producción.

---

## 10. Arquitectura híbrida (si se elige Opción B)

```
Tráfico en vivo
     │
     ▼
[Suricata] ──────────────────────────────────────────────────────►
     │                                                            │
     ▼                                                     Buffer histórico
[Extracción features 14D]                                  (ventana 5min)
     │                                                            │
     ▼                                                            ▼
[Isolation Forest]                                    [XGBoost Predictor]
     │                                                            │
     ▼                                                            ▼
[Motor de decisión]                                   P(ataque_60s) > θ
  PERMIT / LIMIT / BLOCK                                          │
     │                                              ┌─────────────┘
     ▼                                              ▼
[ipset/iptables]                          [Alerta preventiva Telegram]
[Respuesta en < 35ms]                     [Pre-activar LIMIT preventivo]
```

**Punto de integración:** El módulo predictivo corre en paralelo al motor, no en serie. El motor de detección NO lo espera — su latencia (34.8ms) no debe verse afectada. El predictor actualiza su estimación cada 60 segundos basado en el buffer de estadísticas.

---

## 11. Diferenciación respecto a investigaciones existentes

Trabajos que ya usan Suricata + IF:
- Detectan anomalías offline (sin motor en vivo)
- No tienen enforcement automático (solo alertas)
- No validan con corridas repetidas en laboratorio real
- No comparan contra 6 alternativas

**Tu sistema ya se diferencia** en los cuatro puntos anteriores. Añadir predicción haría la diferenciación más fuerte, pero no es la única forma de diferenciarse — y el riesgo de hacerlo mal supera el beneficio de hacerlo.

Lo que realmente diferencia este PPI: **el ciclo completo en vivo con validación formal de 40 corridas**. Eso es lo que deben enfatizar en la defensa, no si tiene predicción.

---

## 12. ¿La combinación actual ya es contribución suficiente?

**Sí.**

El criterio de un PPI de pregrado no es producir un sistema de producción enterprise. Es demostrar aplicación fundamentada de una metodología de ML sobre un problema real, con validación empírica. Este sistema cumple con creces:

- Metodología: IF no supervisado sobre 14 features de flujos Suricata ✅
- Implementación: motor en vivo con control inline ✅  
- Validación: 40 corridas, AUC=0.8998, Precision=99.54%, Latencia P95=34.8ms ✅
- Experimento comparativo: 7 modelos ✅
- Trabajo futuro documentado: Ensemble IF+AE (+49.2% reducción FPR) ✅

Agregar predicción sin datos suficientes debilitaría metodológicamente el PPI, no lo fortalecería.

---

## 13. Riesgos de agregar predicción en esta etapa

| Riesgo | Severidad |
|---|---|
| **Metodológico:** El predictor se entrena sobre ataques manuales; el asesor o jurado identifica que los "patrones" son artefactos del laboratorio | **Alta** |
| **Técnico:** LSTM/GRU con 40 corridas sobreajusta; métricas infladas que no se sostienen | **Alta** |
| **Temporal:** Implementar + validar + documentar toma 3–4 semanas mínimo | Media |
| **Coherencia:** El PPI se fragmenta entre detección (bien validada) y predicción (POC sin validación formal) | Media |
| **Académico:** Los asesores preguntan las corridas F6 equivalentes del predictor — no existen | Media |

---

## 14. Análisis de datos disponibles para predicción

Del `motor_decision.log` (1,177,819 líneas, 02-jun al 19-jun):

```python
# Series extraíbles para XGBoost temporal:
# - Estadísticas cada ~18s: flows, anomalias, http_abuse, bloqueados, latencia_media
# - WARNING entries: SOSPECHOSO, HTTP-ABUSE, BRUTE-FORCE, BLOCK timestamps

# Ventanas de 60s disponibles: ~(17 días × 24h × 60min) = ~24,480 ventanas
# Pero: el motor estuvo activo solo durante sesiones de prueba (~8h/día en pico)
# Ventanas reales útiles: ~2,000-3,000
# Ventanas con ataque en curso: ~150-200 (las de las 40 corridas activas)
# → Desbalance severo: 2,800 normales vs 200 con ataque = 14:1
```

Esto es suficiente para un XGBoost con SMOTE (sobremuestreo), pero los resultados deben presentarse como **POC en entorno controlado**, no como sistema predictivo validado.

---

## 15. Recomendación final

### Opción recomendada: **C + POC mínimo**

**La recomendación primaria es C**: predicción futura como trabajo futuro, documentada en la sección de conclusiones del informe con el diseño de arquitectura y los requisitos de datos.

**Si el entregable o presentación exige demostrar Option B**, el único camino viable sin comprometer la integridad metodológica es:

> Implementar un **XGBoost temporal de prueba de concepto** sobre las series de estadísticas del `motor_decision.log`, con validación temporal explícita (no aleatoria), y presentarlo como "experimento exploratorio" — no como componente validado del sistema.

Esto permite:
- Mostrar que la arquitectura híbrida es factible técnicamente
- Tener código ejecutable y gráficas para la presentación
- No comprometer las 40 corridas F6 ya certificadas
- Ser honesto sobre las limitaciones (datos de laboratorio controlado)

### Lo que NO hacer
- Implementar LSTM/GRU con los datos actuales — sobreajuste garantizado, métricas no creíbles
- Presentar el predictor como si tuviera la misma validez que el IF (que tiene 40 corridas)
- Reemplazar el énfasis de la defensa en la detección IF para ponerlo en predicción

### Resumen ejecutivo de la decisión

```
¿El sistema sin predicción es defendible?      SÍ — completamente
¿La predicción añade valor científico?          SÍ — si los datos lo soportan
¿Los datos actuales soportan predicción?        PARCIALMENTE — solo XGBoost POC
¿Agregar predicción mejora la nota?             INCIERTO — depende de la ejecución
¿Agregar predicción puede dañar la defensa?     SÍ — si los jurados auditan los datos

RECOMENDACIÓN: C como posición académica principal.
               XGBoost POC como demostración técnica opcional para la presentación.
```

---

## Apéndice: Script de extracción de series temporales (si se implementa POC)

```python
# parse_motor_log_timeseries.py
# Extrae ventanas de 60s desde motor_decision.log para XGBoost temporal

import re
import pandas as pd
from datetime import datetime

STATS_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomalías=(\d+) bf=(\d+) http_abuse=(\d+) '
    r'bloqueados=(\d+) limitados=(\d+) latencia_media=([\d.]+)ms'
)

rows = []
with open('results/motor_decision.log') as f:
    for line in f:
        m = STATS_RE.search(line)
        if m:
            rows.append({
                'ts': datetime.fromisoformat(m.group(1)),
                'flows': int(m.group(2)),
                'anomalias': int(m.group(3)),
                'http_abuse': int(m.group(5)),
                'bloqueados': int(m.group(6)),
                'latencia': float(m.group(8)),
            })

df = pd.DataFrame(rows).set_index('ts')
# Agregar en ventanas 60s, calcular deltas
df_60s = df.resample('60s').last().diff()
# Target: ¿hay un BLOCK en los próximos 60s?
df_60s['target'] = (df_60s['bloqueados'] > 0).shift(-1).astype(int)
df_60s.to_csv('data/series_temporal_60s.csv')
print(f"Ventanas: {len(df_60s)}, con ataque: {df_60s['target'].sum()}")
```

---

*Análisis basado en estado real del proyecto al 2026-06-20.*  
*Datos verificados: 17 días de log, 47 capturas, 40 corridas F6, 1.17M líneas motor_decision.log.*
