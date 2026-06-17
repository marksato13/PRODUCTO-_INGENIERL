# FASE 1 — Análisis Formal del Dataset

**Plan maestro:** `PLAN_COMPARACION_MODELOS.md`  
**Script ejecutado:** `scripts/comparacion/f_analisis_dataset.py`  
**Output generado:** `results/comparacion/01_analisis_dataset.txt`  
**Fecha de ejecución:** 2026-06-17  
**Estado:** ✅ COMPLETADA

---

## 1. Dimensiones del dataset

| Parámetro | Valor |
|---|---|
| Flows normales — entrenamiento (80%) | **53,708** |
| Flows normales — holdout evaluación (20%) | **13,427** |
| Flows normales — total | **67,135** |
| Flows anómalos — total evaluación | **906,188** |
| **Total combinado** | **919,615** |
| Features | **14** |
| Archivos normales (`*_normal_*.gz`) | 28 archivos |
| Archivos anómalos (`*_anom_*.gz`) | 13 archivos |

---

## 2. Distribución de etiquetas y desbalance

| Clase | Flows | % |
|---|---|---|
| Normal (label=0) | 13,427 | 1.5% |
| Anómalo (label=1) | 906,188 | 98.5% |
| **TOTAL** | **919,615** | 100% |
| Ratio normal:anómalo | **1 : 67.5** — DESBALANCE EXTREMO |

### Distribución por tipo de ataque

| Tipo de ataque | Flows | % del total anómalo |
|---|---|---|
| ICMP Flood | 223,460 | 24.7% |
| UDP Flood | 218,168 | 24.1% |
| Brute Force SSH | 206,885 | 22.8% |
| Port Scan | 111,161 | 12.3% |
| SYN Flood | 95,723 | 10.6% |
| HTTP Abuse | 50,791 | 5.6% |
| **TOTAL** | **906,188** | 100% |

**Nota:** El desbalance extremo (1:67.5) es **favorable** para los modelos one-class porque el entrenamiento usa SOLO datos normales (no le afecta el ratio). Para modelos supervisados, se requiere `class_weight='balanced'` obligatoriamente.

---

## 3. Tipología de las 14 features

| Feature | Tipo | Descripción | Rango típico (normal) |
|---|---|---|---|
| `pkts_toserver` | Continua | Paquetes enviados al servidor | 1 – 27 (p99) |
| `pkts_toclient` | Continua | Paquetes recibidos del servidor | 0 – 25 (p99) |
| `bytes_toserver` | Continua | Bytes enviados | 60 – 5,981 (p99) |
| `bytes_toclient` | Continua | Bytes recibidos | 0 – 22,552 (p99) |
| `duration` | Continua | Duración del flujo (segundos) | 0 – 3.03 (p99) |
| `pkt_rate` | Continua | Paquetes por segundo | 0.14 – 5,959 (p99) |
| `byte_rate` | Continua | Bytes por segundo | 13 – 1,411,530 (p99) |
| `pkt_ratio` | Continua | pkts_toserver / (pkts_toclient+1) | 0.03 – 2.0 (p99) |
| `byte_ratio` | Continua | bytes_toserver / (bytes_toclient+1) | 0 – 87 (p99) |
| `avg_pkt_size` | Continua | Tamaño promedio de paquete (bytes) | 30 – 634 (p99) |
| `is_tcp` | Binaria | Protocolo TCP (0/1) | 1.0 (100% normal) |
| `is_udp` | Binaria | Protocolo UDP (0/1) | 0.0 (0% normal) |
| `is_icmp` | Binaria | Protocolo ICMP (0/1) | 0.0 (0% normal) |
| `dest_port` | Discreta | Puerto de destino | 8080 (mediana) |

**Totales:** 10 continuas + 3 binarias + 1 discreta = 14 features  
**Features temporales independientes:** 0 (duration es derivada, no timestamp)  
**Variables categóricas:** 0 (proto ya binarizado)

---

## 4. Estadísticas de discriminabilidad (Mann-Whitney U, n=30,000 muestra)

| Feature | Mediana normal | Mediana anómalo | Ratio | p-valor | Discrimina |
|---|---|---|---|---|---|
| `pkts_toserver` | 7.0 | 1.0 | 0.1x | 0.0e+00 | ✅ SÍ |
| `pkts_toclient` | 5.0 | 0.0 | 0.0x | 0.0e+00 | ✅ SÍ |
| `bytes_toserver` | 790 | 60 | 0.1x | 0.0e+00 | ✅ SÍ |
| `bytes_toclient` | 826 | 0 | 0.0x | 0.0e+00 | ✅ SÍ |
| `duration` | 0.044 | 0.001 | 0.0x | 0.0e+00 | ✅ SÍ |
| `pkt_rate` | 330 | 1,000 | **3.0x** | 0.0e+00 | ✅ SÍ |
| `byte_rate` | 39,794 | 60,000 | **1.5x** | 0.0e+00 | ✅ SÍ |
| `pkt_ratio` | 1.167 | 1.000 | 0.9x | 0.0e+00 | ✅ SÍ |
| `byte_ratio` | 0.955 | 60.0 | **62.8x** | 0.0e+00 | ✅ SÍ |
| `avg_pkt_size` | 124 | 30 | 0.2x | 0.0e+00 | ✅ SÍ |
| `is_tcp` | 1.0 | 0.0 | 0.0x | 0.0e+00 | ✅ SÍ |
| `is_udp` | 0.0 | 0.0 | 0.0x | 0.0e+00 | ✅ SÍ |
| `is_icmp` | 0.0 | 0.0 | 0.0x | 0.0e+00 | ✅ SÍ |
| `dest_port` | 8080 | 53 | 0.0x | 0.0e+00 | ✅ SÍ |

**Resultado: 14/14 features son altamente discriminantes (p < 0.001)**

El test Mann-Whitney U es no paramétrico — no asume distribución normal, lo que es correcto dado que los flujos de red tienen distribuciones skewed (lognormal).

### Feature más discriminante: `byte_ratio`
La razón bytes_toserver/bytes_toclient es **62.8x mayor en anómalos** que en normales. Los ataques de flood son unidireccionales: envían paquetes pero no reciben respuesta proporcional.

---

## 5. Características que determinan la compatibilidad de modelos

### Factor 1 — Ausencia de etiquetas en entrenamiento
- **Valor:** ONE-CLASS (solo datos normales en entrenamiento)
- **Impacto:** Elimina RF, XGBoost y DT del paradigma real. Solo son útiles como "upper bound" teórico con ventaja injusta.

### Factor 2 — Dimensionalidad (14 features)
- **Valor:** BAJA-MEDIA
- **Impacto:** Favorable para todos los modelos. IF no sufre "maldición de la dimensionalidad" hasta ~50D. OCSVM con kernel RBF funciona bien. LOF en 14D es viable computacionalmente.

### Factor 3 — Desbalance extremo (1:67.5)
- **Valor:** MUY ALTO
- **Impacto en one-class:** Irrelevante — el entrenamiento usa solo la clase minoritaria (normal). No hay que balancear.
- **Impacto en supervisados:** `class_weight='balanced'` obligatorio para evitar sesgo.

### Factor 4 — Distribuciones no normales (skewed)
- **Valores de skewness:** `pkts_toserver`=46.6, `bytes_toclient`=66.8, `byte_rate`=45.2 en datos normales
- **Impacto:** StandardScaler no normaliza la distribución — solo la escala.
  - **IF:** insensible (particiona aleatoriamente)
  - **OCSVM:** sensible al skew → StandardScaler es necesario pero insuficiente
  - **LOF:** sensible a outliers extremos en k-vecinos
  - **RF/XGBoost:** invariantes a transformaciones monotónicas → sin problema

### Factor 5 — Escalas heterogéneas
- **Rango:** `pkts_toserver` ≈ 1-20 vs `byte_rate` ≈ 0-40,000,000
- **Impacto:** StandardScaler **obligatorio** para OCSVM, LOF, Autoencoder. IF y árboles son invariantes a escala.

### Factor 6 — Volumen (53,708 flows de entrenamiento)
- **Complejidad computacional:**

| Modelo | Complejidad entrenamiento | Tiempo estimado (53K flows) |
|---|---|---|
| Isolation Forest | O(n log n) | < 10 segundos |
| One-Class SVM | O(n²) ~ O(n³) con kernel | 5 – 30 minutos |
| LOF (novelty) | O(n²) | > 30 min con 53K → usar muestra 10K |
| Autoencoder | O(n × epochs) | 1 – 5 minutos |
| Random Forest | O(n log n × k_trees) | 1 – 3 minutos |
| XGBoost | O(n log n) | 30 – 60 segundos |

---

## 6. Naturaleza formal del problema

### Clasificación: SEMI-SUPERVISADO con paradigma ONE-CLASS

```
¿Es supervisado?    ❌ NO — entrenamiento sin etiquetas
¿Es semi-sup.?      ✅ SÍ — evaluación con ground truth implícito
¿Es no-supervisado? ⚠️ PARCIALMENTE — paradigma de entrenamiento one-class
```

**¿Por qué NO es supervisado puro?**  
El IF fue entrenado exclusivamente con tráfico normal. Nunca vio los ataques durante el entrenamiento. Esto replica el escenario real donde los ataques son desconocidos a priori (NIST SP 800-94).

**¿Por qué NO es no-supervisado puro?**  
Disponemos de ground truth implícito: archivos `*_normal_*.gz` = label 0, archivos `*_anom_*.gz` = label 1. Esto permite calcular AUC-ROC, Precision, Recall y F1 sobre el modelo no supervisado.

**¿Por qué semi-supervisado?**  
El ground truth existe pero no se usa para entrenar — solo para evaluar. Paradigma idéntico al "profile-based anomaly detection" del NIST SP 800-94.

### Implicación central para la comparación

| Grupo | Modelos | Paradigma | Etiquetas en train |
|---|---|---|---|
| **One-class** | IF, OCSVM, LOF, Autoencoder | Mismo que producción | ❌ NO |
| **Supervisados** | RF, XGBoost, DT | Upper bound teórico | ✅ SÍ (ventaja injusta) |

**El argumento más fuerte para la tesis:**
> IF obtiene AUC=0.8998 **sin haber visto ningún ataque en entrenamiento**. Si un supervisado lo supera, eso solo demuestra que conocer los ataques de antemano mejora la detección — no que IF sea una mala elección para el paradigma real de un IDPS.

---

## 7. Conclusión de la Fase 1

El dataset PPI UPeU 2026 tiene las siguientes características que lo hacen **óptimo para Isolation Forest**:

1. **Sin etiquetas de entrenamiento** → one-class es el único paradigma realista
2. **14 features, 14/14 discriminantes** → espacio de features bien definido
3. **Distribuciones skewed** → IF insensible; OCSVM y LOF afectados
4. **53K flows de entrenamiento** → IF es el más eficiente computacionalmente
5. **Desbalance 1:67** → no afecta a one-class; afecta críticamente a supervisados

La elección de IF está respaldada por el análisis formal del dataset, no fue arbitraria.

---

## Archivos generados

| Archivo | Ruta | Descripción |
|---|---|---|
| Script de análisis | `scripts/comparacion/f_analisis_dataset.py` | Genera estadísticas completas |
| Output del análisis | `results/comparacion/01_analisis_dataset.txt` | Texto completo con todas las métricas |
| Este documento | `docs/ppi_documentacion/FASE1_ANALISIS.md` | Resumen para tesis |

---

**Siguiente fase:** `FASE2_COMPATIBILIDAD.md` — tabla formal de compatibilidad de modelos con justificación técnica por cada modelo.
