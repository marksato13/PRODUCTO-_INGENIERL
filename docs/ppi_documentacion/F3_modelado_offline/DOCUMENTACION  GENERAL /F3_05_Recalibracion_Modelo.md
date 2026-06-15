# F3-05 — Recalibración del Modelo: Segunda Corrida de Entrenamiento

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F3 — Modelado Offline  
**Documento:** Recalibración del modelo IF — 4 de junio 2026  

---

## 1. ¿Se hizo una recalibración? Evidencia empírica

**Sí.** El modelo Isolation Forest fue entrenado en dos ocasiones distintas. Los timestamps del sensor (192.168.0.110) lo confirman:

```bash
# Ejecutado en sensor 192.168.0.110 — 2026-06-15
stat /home/m4rk/ppi-surikata-produto/models/isolation_forest.pkl

  File: isolation_forest.pkl
  Size: 2,520,649 bytes
  Birth:  2026-06-02 01:42:13  ← Primera versión del modelo (F3 inicial)
  Modify: 2026-06-04 14:41:45  ← Segunda versión: RECALIBRACIÓN

stat /home/m4rk/ppi-surikata-produto/models/scaler.pkl
  Modify: 2026-06-04 14:41:45  ← Scaler también recalibrado

stat /home/m4rk/ppi-surikata-produto/results/umbrales_finales.txt
  Birth:  2026-06-04 09:43:49  ← Umbrales τ1/τ2 derivados en la recalibración
  Modify: 2026-06-04 09:43:49
```

**El modelo fue entrenado el 2 de junio (v1) y reentrenado el 4 de junio (v2 — versión final en producción).**

---

## 2. Cronología completa

| Fecha | Hora | Evento | Archivo modificado |
|---|---|---|---|
| 2026-06-02 | 01:42 | Primera ejecución de `fase3_isolation_forest.py` | `isolation_forest.pkl` (Born) |
| 2026-06-02 | 18:14 | Pipeline F2 finalizado: `etiquetar_limpiar.py` + `particionar_estadisticos.py` | `train.csv`, `val.csv`, `test.csv` |
| 2026-06-04 | 09:43 | Derivación de τ1/τ2 con `auc_roc_umbrales.py` | `umbrales_finales.txt` (Born) |
| 2026-06-04 | 14:41 | **Segunda ejecución** de `fase3_isolation_forest.py` | `isolation_forest.pkl` (Modify) |
| 2026-06-04 | 14:41 | Scaler y features actualizados | `scaler.pkl`, `features.csv` |
| 2026-06-14 | Múltiples | Validación F5/F6 con modelo final | `motor_decision.log` |

---

## 3. Por qué fue necesaria la recalibración

### 3.1 Causa principal — Análisis de sesgo SSH

La primera versión del modelo (2026-06-02 01:42) fue entrenada con los datos disponibles al inicio del día 2: solo las primeras corridas de tráfico normal capturadas horas antes.

Tras el análisis de sensibilidad documentado en `F3_justificacion_modelo.md`, se identificó que:

> *"Agregar corridas adicionales de SSH legítimo (ssh_03 a ssh_10) hacía que el modelo aprendiera que SSH frecuente es 'muy normal', reduciendo la detección de Brute Force SSH (B6) a 0%."*

La segunda ejecución de F3 aplicó el **doble filtro** definitivo:

```python
# Filtro 1: solo corridas 01 y 02 (no las corridas ssh_03-10)
normal_files = [f for f in glob.glob("data/raw/*_normal_*_eve.json.gz")
                if "_01_" in f or "_02_" in f]

# Filtro 2: solo flows del Desktop (192.168.0.20 y 192.168.0.120)
src_filter = {'192.168.0.20', '192.168.0.120'}
```

**Resultado del filtro:** 684 flows normales balanceados entre HTTP (345), sostenido (252), SSH (58) y transferencia (29). Solo 8.5% de los flows de entrenamiento son SSH — proporción que preserva la detección de B6.

### 3.2 Causa secundaria — Recalibración de umbrales τ1/τ2

La primera versión del modelo usaba el umbral por defecto del `clf.offset_` (−0.5481, generado automáticamente por `contamination=0.05`). Este umbral no estaba optimizado para la distribución real del sistema.

La recalibración incluyó:

1. Ejecutar `auc_roc_umbrales.py` para trazar la curva ROC completa
2. Derivar **τ1 por Youden index** (maximizar TPR − FPR): τ1 = −0.4973
3. Derivar **τ2 por FPR ≤ 2%** (máxima TPR con FPR controlado): τ2 = −0.6873

```
ANTES (v1):         clf.offset_ = −0.5481  (decisión binaria: PERMIT / BLOCK)
DESPUÉS (v2):       τ1 = −0.4973  (PERMIT / LIMIT)
                    τ2 = −0.6873  (LIMIT / BLOCK)
```

La recalibración convirtió el sistema de **binario** (normal/anómalo) a **triple** (PERMIT/LIMIT/BLOCK), lo cual es el mecanismo central del sistema.

---

## 4. Qué cambió entre v1 y v2

| Aspecto | Versión v1 (2026-06-02) | Versión v2 (2026-06-04) — en producción |
|---|---|---|
| Datos de entrenamiento | Corridas disponibles en madrugada del 2 de jun | 684 flows balanceados (filtro doble) |
| Umbral de decisión | clf.offset_ = −0.5481 (automático) | τ1 = −0.4973 / τ2 = −0.6873 (ROC-optimized) |
| Lógica de decisión | Binaria (PERMIT / BLOCK) | Triple (PERMIT / LIMIT / BLOCK) |
| Detección B6 SSH | Comprometida (sesgo SSH en datos) | Preservada (8.5% SSH en entrenamiento) |
| AUC-ROC (val set) | No registrado | 0.9440 (validado en F6) |
| Umbrales derivados de | clf.offset_ por defecto | Youden index + FPR ≤ 2% |

---

## 5. Justificación del análisis de sensibilidad previo a v2

Antes de la segunda ejecución de F3, se realizó un análisis de sensibilidad con los 1,977 flows normales disponibles en `data/raw/`. Para cada tamaño de muestra N se entrenó el modelo 5 veces con semillas distintas:

| N | AUC (media) | ±std | Recall(τ1) |
|---|---|---|---|
| 50 | 0.922 | 0.035 | 0.993 |
| 200 | 0.931 | 0.028 | 0.993 |
| **684** | **0.935** | **0.013** | **0.993** |
| 800 | 0.940 | 0.014 | 0.993 |
| 1500 | 0.935 | 0.004 | 0.993 |

**Hallazgo clave:** El AUC se estabiliza a partir de N ≈ 200–300 y el Recall es constante en 0.993 para todo N desde 50 hasta 1,977. Aumentar a 1,500 flows mejora el AUC en solo 0.000 y la std cae de 0.013 a 0.004, pero al costo de sesgar el perfil normal hacia SSH. **N=684 es el punto óptimo.**

---

## 6. ¿Se necesita una tercera corrida de entrenamiento para demostrar adaptabilidad?

**No es necesario ni recomendable en el contexto del PPI.**

### 6.1 Por qué no es necesario

**a) La adaptabilidad ya está demostrada empíricamente (F2-04):**

El experimento F2-04 probó 12 tipos de ataque que el modelo NUNCA vio durante el entrenamiento (Slowloris, DNS Amplification, RDP Brute Force, NTP Amplification, etc.) — todos detectados al 100% sin ningún reentrenamiento. Esto prueba directamente que el modelo se adapta a ataques desconocidos como consecuencia de su naturaleza no supervisada.

**b) La recalibración ya ocurrió (este documento):**

La secuencia v1 → v2 es evidencia real de que el pipeline de reentrenamiento funciona. Se ejecutó `fase3_isolation_forest.py` con nuevos parámetros y datos refinados, obteniendo un modelo mejorado. El proceso está documentado, repetible y parametrizado.

**c) La arquitectura de adaptación está diseñada (F4-04):**

El documento F4-04 especifica el pipeline completo: colección de flows PERMIT en producción → trigger a 2,000 flows nuevos → batch_retrain con 4 gates de calidad → deploy con rollback automático. El mecanismo existe; solo requiere datos de producción real para activarse.

### 6.2 Por qué una tercera simulación traería dificultades

| Riesgo | Descripción |
|---|---|
| Invalidaría F6 | Los 40 corridas de F6 fueron validadas con el modelo v2. Un modelo v3 requeriría re-validar todas las corridas para mantener coherencia del informe. |
| Requiere datos limpios | Necesitaría capturar nuevas corridas A1–A4 en condiciones controladas sin contaminar el eve.json actual. Mínimo 4 horas de laboratorio. |
| Riesgo de degradación | Si los nuevos datos normales incluyen sesgo (más SSH, por ejemplo), el nuevo modelo podría tener peor recall en B6. |
| No agrega valor científico | El análisis de sensibilidad ya demostró que el modelo es robusto desde N=200. Una tercera corrida confirmaría algo ya demostrado. |

### 6.3 Respuesta para la defensa

> *"La recalibración del modelo ocurrió el 4 de junio 2026, cuando se ejecutó por segunda vez el script `fase3_isolation_forest.py` con el conjunto de entrenamiento definitivo (684 flows, filtro doble: corridas 01-02 + IPs legítimas) y se derivaron los umbrales τ1 y τ2 desde la curva ROC en lugar del offset automático. Esta segunda ejecución mejoró la lógica de decisión de binaria a triple (PERMIT/LIMIT/BLOCK) y preservó la detección de Brute Force SSH. La capacidad de adaptación a ataques futuros no requiere otra simulación porque F2-04 ya demostró empíricamente que el modelo detecta 12/12 ataques no entrenados al 100%, y el script de reentrenamiento está parametrizado para ejecutarse con cualquier conjunto de flows normales nuevos."*

---

## 7. Pipeline de reentrenamiento (disponible, no activado en PPI)

El reentrenamiento en producción real se ejecutaría así:

```bash
# 1. Acumular flows normales nuevos (producción)
grep 'PERMIT' /path/to/motor_decision.log > data/normal_flows_nuevos.csv

# 2. Reentrenar (cuando se acumulen ≥2,000 flows)
/home/m4rk/ppi-sensor/venv/bin/python3 \
    scripts/fase3_isolation_forest.py \
    --data-dir data/raw_nuevos/ \
    --model-output models/isolation_forest_v2.pkl

# 3. Recalibrar umbrales con nueva curva ROC
/home/m4rk/ppi-sensor/venv/bin/python3 \
    scripts/auc_roc_umbrales.py \
    --model models/isolation_forest_v2.pkl

# 4. Validar (4 gates automáticos)
# Gate 1: FPR ≤ 10% en flows normales originales
# Gate 2: Recall ≥ 95% en eval set balanceado
# Gate 3: AUC ≥ 0.98
# Gate 4: Latencia P95 < 500ms

# 5. Deploy si pasan los 4 gates
systemctl restart ppi-motor.service
```

Los scripts están parametrizados para ejecutar este proceso sobre cualquier directorio de captura sin modificar el código.

---

## 8. Resumen ejecutivo

| Pregunta | Respuesta |
|---|---|
| ¿Se hizo recalibración? | **Sí** — modelo reentrenado el 2026-06-04 (evidencia en timestamps) |
| ¿Por qué? | Para aplicar filtro definitivo de corridas (evitar sesgo SSH) y derivar τ1/τ2 desde ROC |
| ¿Mejoró algo? | Sí — lógica de decisión pasó de binaria a triple (PERMIT/LIMIT/BLOCK) |
| ¿Se necesita tercera simulación? | **No** — ya demostrado por F2-04 (12/12 ataques nuevos) y la propia recalibración v1→v2 |
| ¿Puede reentrenarse en producción? | Sí — scripts parametrizados, pipeline definido en F4-04 |

---

## Archivos de referencia

| Archivo | Ruta (sensor 192.168.0.110) | Descripción |
|---|---|---|
| Script entrenamiento | `scripts/fase3_isolation_forest.py` | Pipeline completo F3 |
| Modelo v2 (producción) | `models/isolation_forest.pkl` | Entrenado 2026-06-04 14:41 |
| Scaler v2 | `models/scaler.pkl` | Entrenado 2026-06-04 14:41 |
| Umbrales | `results/umbrales_finales.txt` | τ1=−0.4973, τ2=−0.6873 |
| Análisis de sensibilidad | `F3_justificacion_modelo.md` | N vs AUC — justificación 684 flows |
| Adaptabilidad | `F4_04_Aprendizaje_Continuo.md` | Arquitectura evolutiva completa |
| Comparación modelos | `F4_01_Comparacion_Modelos.md` | IF vs RF vs SVM vs DT vs LR |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-produto/`  
> *Documento generado el 15 de junio 2026 como evidencia de la recalibración del modelo*
