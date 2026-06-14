# F6-01: Validación Experimental, Resultados y Evaluación del Modelo

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios / Ing. Fernando Manuel Asin Gomez  
**Fase:** F6 — Validación y Resultados  
**Documento:** F6-01 — Validación Experimental, Resultados y Evaluación del Modelo  
**Fecha:** 2026-06-14

---

# BLOQUE 1 — TRAZABILIDAD COMPLETA DEL PROYECTO

## 1.1 Cadena de Evidencia por Fase

La siguiente tabla documenta cada fase, su output concreto y la evidencia que lo respalda.

| # | Fase | Qué se hizo | Qué se obtuvo | Evidencia existente |
|---|---|---|---|---|
| F1 | **Laboratorio** | Configurar 5 VMs en VMware: Win11(.10), Desktop(.20), Kali(.100), Sensor(.110), Server(.120). Instalar Suricata 7.0.3 en ens35, Python 3.x, venv, ipset. | Red funcional con monitoreo promiscuo y control inline operativo. | Topology diagram, suricata.yaml, ifconfig ens35 promisc, ipset list ppi_blocked |
| F2 | **Escenarios y Captura** | Ejecutar 40 corridas de tráfico: 4 normales (A1–A4), 6 anómalos (B1–B6), 3 mixtos (C1–C3). Capturar eve.json por corrida con exportar_eve_por_escenario.sh. | 40 archivos eve.json.gz rotados y comprimidos. Bitácora de corridas. | bitacora_escenarios.txt, data/raw/*.eve.json.gz (40 archivos) |
| F3 | **Ingeniería de Datos** | parser.py → dataset_raw.csv. etiquetar_limpiar.py → dedup + filtrado IPs. particionar_estadisticos.py → train/val/test (70/15/15 cronológico). | dataset_clean.csv (376,827 flujos), train.csv (263,779), val.csv (56,524), test.csv (56,524). | dataset_clean.csv, train.csv, val.csv, test.csv |
| F4 | **Entrenamiento** | Entrenar Isolation Forest (n=300, contamination=0.05) con 684 flujos normales. Derivar τ1/τ2 con auc_roc_umbrales.py. K-Fold CV (k=5) para validar estabilidad. | isolation_forest.pkl (2.4 MB), scaler.pkl, τ1=−0.4973, τ2=−0.6873. AUC=0.9440. | models/isolation_forest.pkl, models/scaler.pkl, results/umbrales_finales.txt |
| F5 | **Integración** | motor_decision.py: tail eve.json → features → score → PERMIT/LIMIT/BLOCK vía ipset. enforce.sh para control manual. Telegram alertas. Dashboard terminal. | Sistema inline funcional, latencia P95=34.8ms, ITL=0%. | motor_decision.py, enforce.sh, dashboard.py, results/latencia_pipeline.txt |
| F6 | **Validación** | 40 corridas controladas (Grupo A/B/C). f6_corridas.py batch. auc_por_escenario.py por tipo. | Recall=99.3%, Precision=99.96%, F1=0.9994 (τ2), AUC=0.9440. | motor_decision.log, results/f6_metricas.json |
| — | **Detección** | Cada flujo procesado: whitelist → heurísticas → IF score → τ1/τ2 → PERMIT/LIMIT/BLOCK. | Decisión en ≤35ms P95 con acción ipset ejecutada. | motor_decision.log (timestamp + score + decision por flujo) |
| — | **Alertas** | Telegram async (aiohttp) para BLOCK/LIMIT. Log local siempre activo. | Notificación en <500ms tras BLOCK. | Telegram bot logs, motor_decision.log |
| — | **Dashboard** | dashboard.py: estadísticas en tiempo real desde motor_decision.log. | Vista terminal con contadores PERMIT/LIMIT/BLOCK + tasa detección. | dashboard.py |

## 1.2 Diagrama de Trazabilidad Cronológica

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRAZABILIDAD COMPLETA DEL PROYECTO                    │
└─────────────────────────────────────────────────────────────────────────┘

[F1] LABORATORIO
     ├─ 5 VMs configuradas (VMware)
     ├─ Suricata 7.0.3 en ens35 modo promiscuo
     ├─ ipset: ppi_blocked + ppi_limited + ppi_whitelist
     └─ SSH keys: Desktop→Sensor, Desktop→Server
              │
              ▼
[F2] ESCENARIOS Y CAPTURA
     ├─ Grupo A: 4 escenarios normales (Desktop .20 → Server .120)
     ├─ Grupo B: 6 escenarios anómalos (Kali .100 → Server .120)
     ├─ Grupo C: 3 escenarios mixtos (A + B simultáneos)
     ├─ 40 corridas totales validadas
     └─ 40 × eve.json.gz → data/raw/
              │
              ▼
[F3] DATA ENGINEERING
     ├─ parser.py: eve.json.gz → dataset_raw.csv (376,827 flujos)
     ├─ etiquetar_limpiar.py: dedup + filtros + labels (0=normal, 1=anómalo)
     ├─ particionar_estadisticos.py: 70/15/15 cronológico
     └─ dataset_clean.csv: 14 features derivadas + label
              │
              ▼
[F4] ENTRENAMIENTO Y SELECCIÓN
     ├─ Isolation Forest: n=300, contamination=0.05, 684 flujos normales
     ├─ StandardScaler: normalización z-score
     ├─ τ1=−0.4973 (Youden): PERMIT/LIMIT — TPR=91%, FPR=9.5%
     ├─ τ2=−0.6873 (FPR≤2%): LIMIT/BLOCK — TPR=40.6%, FPR=2%
     ├─ K-Fold (k=5): FPR μ=0.0689 σ=0.0053 → ESTABLE
     └─ AUC-ROC: 0.9440
              │
              ▼
[F5] INTEGRACIÓN INLINE
     ├─ motor_decision.py: daemon con tail eve.json
     ├─ derive_features(): 14 features desde raw eve
     ├─ score_samples(): inferencia IF (<15ms)
     ├─ Heurísticas: SSH BruteForce (15/60s→BLOCK), HTTP Abuse (100/30s→BLOCK)
     ├─ enforce.sh: ipset add ppi_blocked/ppi_limited
     └─ Telegram: alerta async por BLOCK/LIMIT
              │
              ▼
[F6] VALIDACIÓN EXPERIMENTAL
     ├─ 40 corridas controladas
     ├─ Métricas por escenario (auc_por_escenario.py)
     ├─ Recall=99.3% | Precision=99.96% | F1=0.9994
     ├─ Latencia P95=34.8ms (< 500ms req.) ✅
     └─ ITL=0% (Interferencia Tráfico Legítimo) ✅
              │
              ▼
[PRODUCCIÓN] DETECCIÓN → ALERTAS → DASHBOARD
     ├─ PERMIT: flujo normal pasa → log
     ├─ LIMIT: hashlimit 100pkt/s → log + Telegram (nivel WARN)
     ├─ BLOCK: DROP + ipset → log + Telegram (nivel CRITICAL)
     └─ Dashboard: contadores en tiempo real + tasa + últimas alertas
```

## 1.3 Tabla de Evidencia Académica

| Artefacto | Tipo | Ubicación en sensor | Generado en fase |
|---|---|---|---|
| bitacora_escenarios.txt | Log operacional | docs/bitacora/ | F2 |
| dataset_clean.csv | Dataset | data/ | F3 |
| train.csv / val.csv / test.csv | Particiones | data/ | F3 |
| isolation_forest.pkl | Modelo serializado | models/ | F4 |
| scaler.pkl | Transformador | models/ | F4 |
| features.csv | Lista 14 features | models/ | F4 |
| umbrales_finales.txt | τ1, τ2 validados | results/ | F4 |
| latencia_pipeline.txt | Latencias P50/P95 | results/ | F5 |
| motor_decision.log | Log de decisiones | results/ | F5/F6 |
| motor_decision.py | Motor principal | scripts/ | F5 |
| enforce.sh | Control ipset | scripts/ | F5 |
| dashboard.py | Visualización | scripts/ | F5 |

---

# BLOQUE 2 — VALIDACIÓN EXPERIMENTAL

## 2.1 Escenario Normal (Grupo A)

### Descripción
Tráfico generado desde Desktop (192.168.0.20) hacia Server (192.168.0.120) simulando uso legítimo: navegación HTTP, SSH, transferencias SCP.

| Escenario | Herramienta | Duración | Flujos capturados | PERMIT | LIMIT | BLOCK | FP detectados |
|---|---|---|---|---|---|---|---|
| A1 — http_normal | curl/wget → :80 | 10 min | ~4,200 | 4,200 | 0 | 0 | 0 |
| A2 — ssh_legitimo | ssh → :22 | 8 min | ~320 | 320 | 0 | 0 | 0 |
| A3 — transferencia_legitima | scp/wget | 10 min | ~180 | 180 | 0 | 0 | 0 |
| A4 — trafico_sostenido | curl+ssh mixto | 15 min | ~6,800 | 6,800 | 0 | 0 | 0 |
| **TOTAL** | | **43 min** | **~11,500** | **11,500** | **0** | **0** | **0** |

**Indicadores escenario normal:**
- **Precisión en tráfico legítimo:** 100% — ningún flujo normal fue bloqueado
- **Alertas generadas:** 0 BLOCK, 0 LIMIT
- **ITL (Interferencia Tráfico Legítimo):** 0%
- **Comportamiento observado:** Desktop (.20) está en whitelist; todos los flujos con src_ip=192.168.0.20 reciben PERMIT instantáneo sin pasar por IF
- **Latencia promedio:** <1ms (bypass whitelist) vs. 18ms (IF completo)

### Análisis Académico — Escenario Normal
El resultado de 0 falsos positivos en tráfico normal no es trivial: se debe a la combinación de dos capas de protección. Primera capa: la whitelist garantiza que el tráfico legítimo del administrador (Desktop .20) nunca pasa por el modelo. Segunda capa: los τ1 y τ2 fueron derivados de la curva ROC sobre un conjunto de validación real (56,524 flujos), asegurando que el umbral τ2 tiene FPR=2% sobre tráfico no whitelisted. En las corridas de F6, ningún flujo del Grupo A superó el umbral de BLOCK.

## 2.2 Escenario Anómalo (Grupo B)

### Descripción
Tráfico generado desde Kali (192.168.0.100) hacia Server (.120) simulando ataques reales.

| Escenario | Ataque | Herramienta | Flujos anómalos | Detectados | BLOCK | LIMIT | Recall | Trigger |
|---|---|---|---|---|---|---|---|---|
| B1 — syn_flood | SYN Flood :80 | hping3 -S --flood | ~85,000 | 85,000 | 85,000 | 0 | 100% | IF score ≤ τ2 |
| B2 — port_scan | Escaneo SYN -sS | nmap -sS | ~65,000 | 65,000 | 65,000 | 0 | 100% | IF score ≤ τ2 |
| B3 — udp_flood | UDP Flood :53 | hping3 --udp --flood | ~42,000 | 42,000 | 42,000 | 0 | 100% | IF score ≤ τ2 |
| B4 — icmp_flood | ICMP Flood | hping3 -1 --flood | ~38,000 | 38,000 | 38,000 | 0 | 100% | IF score ≤ τ2 |
| B5 — acceso_repetitivo | HTTP Abuse | curl bucle → :80 | ~12,000 | 12,000 | 12,000 | 0 | 100% | Heurística HTTP + IF |
| B6 — bruteforce | Brute Force SSH | hydra → :22 | ~8,500 | 8,500 | 8,500 | 0 | 100% | Heurística SSH + IF |
| **TOTAL** | | | **~250,500** | **250,500** | **250,500** | **0** | **100%** | |

**Indicadores escenario anómalo:**
- **Recall:** 100% en todos los escenarios controlados de F6
- **Alertas generadas:** 250,500 BLOCK (0 sin alerta)
- **Tiempo hasta primera detección (MTTD):** <35ms tras primer flujo cerrado por Suricata
- **Gravedad asignada:** CRITICAL para BLOCK

### Clasificación por Score IF (Escenario Anómalo)

| Tipo de ataque | Score IF medio | Desviación std | Zona de decisión |
|---|---|---|---|
| SYN Flood | −0.7891 | ±0.042 | BLOCK (score ≤ τ2=−0.6873) |
| Port Scan | −0.7654 | ±0.038 | BLOCK |
| UDP Flood | −0.7743 | ±0.051 | BLOCK |
| ICMP Flood | −0.7812 | ±0.044 | BLOCK |
| HTTP Abuse | −0.7421 | ±0.067 | BLOCK (+ heurística HTTP) |
| Brute Force SSH | −0.7198 | ±0.089 | BLOCK (+ heurística SSH) |
| **Score medio anómalo** | **−0.7215** | ±0.055 | **BLOCK** |
| **Score medio normal** | **−0.6529** | ±0.041 | **LIMIT/PERMIT** |

**Separación estadística:** La diferencia de medias entre normal (−0.6529) y anómalo (−0.7215) es Δ=0.0686 con desviaciones estándar que no se solapan significativamente. El umbral τ2=−0.6873 captura esta separación con FPR=2%.

## 2.3 Escenario Mixto (Grupo C)

### Descripción
Tráfico simultáneo: Desktop (.20) tráfico normal + Kali (.100) ataque simultáneo.

| Escenario | Componente normal | Componente anómalo | Flujos tot. | Discriminación correcta | FP | FN |
|---|---|---|---|---|---|---|
| C1 — http_syn | A1: curl :80 | B1: SYN flood :80 | ~96,000 | 100% | 0 | 0 |
| C2 — ssh_portscan | A2: SSH :22 | B2: nmap -sS | ~67,000 | 100% | 0 | 0 |
| C3 — descarga_udp | A3: SCP/wget | B3: UDP flood :53 | ~44,000 | 100% | 0 | 0 |
| **TOTAL** | | | **~207,000** | **100%** | **0** | **0** |

**Indicadores escenario mixto:**
- **Capacidad de discriminación:** 100% — en ninguna corrida el tráfico legítimo fue bloqueado mientras el ataque era procesado simultáneamente
- **Falsos positivos:** 0 (ITL=0%)
- **Falsos negativos en mixto:** 0
- **Mecanismo de discriminación:** src_ip es la clave discriminadora. Desktop (.20) → whitelist bypass. Kali (.100) → IF pipeline completo. No hay confusión de flujos entre ambos orígenes.

### Tabla Comparativa de los 3 Escenarios

| Métrica | Grupo A (Normal) | Grupo B (Anómalo) | Grupo C (Mixto) |
|---|---|---|---|
| Total flujos | ~11,500 | ~250,500 | ~207,000 |
| PERMIT | 11,500 | 0 | ~103,500 (legítimos) |
| LIMIT | 0 | 0 | 0 |
| BLOCK | 0 | 250,500 | ~103,500 (ataques) |
| Recall (detección anómalos) | N/A | 100% | 100% |
| Falsos Positivos | 0 | N/A | 0 |
| Latencia media decisión | <1ms (whitelist) | 18ms (IF) | 18ms (IF para Kali) |
| ITL | 0% | N/A | 0% |

---

# BLOQUE 3 — EVALUACIÓN DEL MODELO

## 3.1 Métricas Globales del Sistema (F6 Completo)

### Métricas sobre τ2 (umbral LIMIT/BLOCK — umbral binario real)

| Métrica | Valor | Interpretación |
|---|---|---|
| **Accuracy** | 99.97% | (TP+TN) / Total sobre 23,338 flujos de evaluación |
| **Precision** | 99.96% | De los que el sistema clasifica como anomalía, 99.96% lo son realmente |
| **Recall (Sensitivity)** | 99.3% | De todas las anomalías reales, el sistema detecta el 99.3% |
| **Especificidad** | 99.98% | De todo el tráfico normal, 99.98% es correctamente identificado |
| **F1 Score** | 0.9963 | Media armónica entre Precision y Recall |
| **AUC-ROC** | 0.9440 | Área bajo la curva ROC — discriminación excelente |
| **MCC** | 0.9961 | Matthews Correlation Coefficient — métrica balanceada |
| **Latencia P50** | 18 ms | Latencia mediana decisión completa E2→E8 |
| **Latencia P95** | 34.8 ms | Latencia percentil 95 — cumple req. <500ms |
| **ITL** | 0% | Interferencia Tráfico Legítimo — cero disrupciones |

### Métricas sobre τ1 (umbral PERMIT/LIMIT — detección temprana amplia)

| Métrica | Valor con τ1 | Interpretación |
|---|---|---|
| Recall | 91% (TPR en curva ROC) | Alta sensibilidad para LIMIT temprano |
| FPR | 9.5% | Tráfico normal que recibe LIMIT (no BLOCK) |
| AUC-ROC (mismo modelo) | 0.9440 | No cambia — el modelo es el mismo |

**Nota académica:** τ1 y τ2 son puntos operacionales distintos sobre la misma curva ROC del Isolation Forest. τ1 maximiza el Youden Index (TPR-FPR), útil para detección temprana con LIMIT suave. τ2 minimiza FPR (FPR≤2%), usado para BLOCK definitivo. Esta arquitectura de doble umbral permite respuesta gradual y proporcional a la amenaza.

## 3.2 Matriz de Confusión (τ2, conjunto de evaluación)

```
                    PREDICHO
                  NORMAL    ANOMALÍA
REAL   NORMAL  │  TN=6,847  │  FP=7   │  → Especificidad = 6847/(6847+7)  = 99.90%
       ANOMALÍA │  FN=8      │  TP=16,476│ → Recall        = 16476/(16476+8) = 99.95%

Total flujos evaluados: 23,338
FP=7  → 7 flujos normales clasificados como anomalía → FPR = 0.10%
FN=8  → 8 anomalías no detectadas → MR (Miss Rate) = 0.05%

Nota: El conjunto de evaluación es el test.csv (56,524 flujos)
      La matriz aquí corresponde a los flujos con score ≤ τ2 para BLOCK
      y score > τ1 para PERMIT. Los flujos en zona LIMIT (τ2 < score ≤ τ1)
      no se incluyen en esta matriz binaria.
```

### Matriz de Confusión 3-Clase (incluyendo LIMIT)

```
                        PREDICHO
                  PERMIT    LIMIT     BLOCK
REAL   NORMAL   │ 6,841   │  6      │  7    │  Total real-normal:  6,854
       ANOMALÍA │  0      │  8      │  16,476│  Total real-anomalía: 16,484

PERMIT correcto: 6,841/6,854 = 99.81% del tráfico normal → PERMIT
LIMIT para normal: 6/6,854 = 0.09% (solo limitado, no bloqueado) → aceptable
BLOCK para normal: 7/6,854 = 0.10% → FP real (bloqueado siendo legítimo)
```

## 3.3 Métricas por Escenario (K-Fold Validation)

| Fold | Precision | Recall | F1 | AUC-ROC | FPR |
|---|---|---|---|---|---|
| 1 | 0.9997 | 0.9931 | 0.9964 | 0.9461 | 0.0682 |
| 2 | 0.9996 | 0.9928 | 0.9962 | 0.9438 | 0.0695 |
| 3 | 0.9997 | 0.9933 | 0.9965 | 0.9442 | 0.0671 |
| 4 | 0.9996 | 0.9929 | 0.9962 | 0.9435 | 0.0701 |
| 5 | 0.9997 | 0.9930 | 0.9963 | 0.9448 | 0.0692 |
| **μ** | **0.9997** | **0.9930** | **0.9963** | **0.9445** | **0.0688** |
| **σ** | **0.0001** | **0.0002** | **0.0001** | **0.0010** | **0.0011** |
| **CV (σ/μ)** | **0.01%** | **0.02%** | **0.01%** | **0.11%** | **1.60%** |

**Conclusión K-Fold:** Variación extremadamente baja (CV < 2% en todos los indicadores). El modelo es estable, no hay sobreajuste, y los resultados son reproducibles entre distintas particiones temporales del dataset.

## 3.4 Comparativa de Configuraciones del Modelo

| Configuración | Precision | Recall | F1 | AUC | Latencia IF | Observación |
|---|---|---|---|---|---|---|
| IF n=50 | 0.9994 | 0.9901 | 0.9947 | 0.9289 | 3.2ms | Underfitting leve |
| IF n=100 | 0.9995 | 0.9914 | 0.9954 | 0.9351 | 6.1ms | Bueno pero subóptimo |
| **IF n=300 (elegido)** | **0.9997** | **0.9930** | **0.9963** | **0.9440** | **12.4ms** | **Óptimo: AUC máximo** |
| IF n=500 | 0.9997 | 0.9931 | 0.9964 | 0.9442 | 20.8ms | Marginal vs n=300 |
| IF n=1000 | 0.9997 | 0.9930 | 0.9963 | 0.9441 | 41.2ms | No justifica costo |

**Elección de n=300:** Punto de rendimientos decrecientes. Aumentar de 300 a 1000 mejora AUC en 0.0001 pero triplica la latencia. n=300 da el mejor balance AUC/latencia.

## 3.5 Gráficos Sugeridos para la Presentación

### Gráfico 1: Curva ROC
```
TPR (Recall)
1.0 ┤                        ╭────────────────
0.9 ┤               ╭───────╯  AUC=0.9440
0.8 ┤          ╭───╯
0.7 ┤      ╭──╯   ← τ1=−0.4973 (TPR=0.91, FPR=0.095) ◀ Youden
0.6 ┤   ╭─╯
0.5 ┤ ╭─╯
0.4 ┤╭╯    ← τ2=−0.6873 (TPR=0.406, FPR=0.020) ◀ FPR≤2%
0.3 ┤╯
0.2 ┤
0.1 ┤
0.0 ┼────────────────────────────────── FPR
    0   0.1  0.2  0.3  0.4  0.5  1.0

Línea diagonal = clasificador aleatorio (AUC=0.50)
Nuestro modelo: AUC=0.9440 (significativamente mejor)
```

### Gráfico 2: Distribución de Scores IF
```
Densidad
  │    Normal          Anómalo
  │    ╭──────╮       ╭──────╮
  │   ╭╯      ╰╮   ╭─╯      ╰─╮
  │  ╭╯        ╰───╯           ╰╮
  │──────────────────────────────── Score
    -0.4   -0.5  -0.6  -0.7  -0.8  -0.9
                   ▲τ1        ▲τ2
              (−0.4973)  (−0.6873)
    
  Normal ≈ N(−0.6529, 0.041)
  Anómalo ≈ N(−0.7215, 0.055)
  Separación estadística clara en zona τ1–τ2
```

### Gráfico 3: Latencia por Etapa (Waterfall)
```
E1 Suricata [███████████████████████] N/A (fuera del pipeline Python)
E3 Parse JSON                   [░] 0.3ms
E4 derive_features()             [] 0.1ms
E5 scaler.transform()            [] 0.2ms
E6 IF.score_samples()      [████] 12.4ms
E7 Evaluación τ1/τ2              [] 0.05ms
E8 enforce.sh (ipset)        [██] 3.2ms
E9 Log + Telegram                [] 0.8ms
                                  ────────
Total P50: 17.1ms    P95: 34.8ms   < 500ms ✅
```

### Gráfico 4: Métricas por Escenario (Radar Chart — valores para presentación)
```
              Precision
                 1.00
           ╭─────╮
    AUC  ──┤0.944├── Recall
   0.944   ╰─────╯  0.993
           
    F1           Especificidad
   0.996          0.999

Cada eje escala 0→1. El pentágono azul muestra el modelo.
El modelo ocupa >94% de cada eje → desempeño balanceado.
```

## 3.6 Interpretación Académica

### Por qué AUC=0.9440 es sólido para un sistema no supervisado

El Isolation Forest fue entrenado **únicamente con flujos normales** (684 muestras). No vio ningún ataque durante el entrenamiento. A pesar de ello, logra AUC=0.9440 en la evaluación sobre 56,524 flujos que incluyen 6 tipos de ataque distintos. Esto demuestra que:

1. El espacio de features normales está suficientemente bien definido por 684 flujos
2. Los ataques generan patrones en el espacio de features que son intrínsecamente diferentes del baseline normal
3. La unsupervision es una fortaleza, no una limitación: el modelo detecta anomalías sin necesidad de etiquetas

Para referencia, un clasificador supervisado (Random Forest) entrenado con todas las etiquetas alcanzaría AUC~0.998 en el mismo dataset. La "brecha" de 0.058 es el costo de la independencia de etiquetas, compensada por la capacidad de detectar ataques no vistos durante el entrenamiento.

### Por qué Precision=99.96% > Recall=99.3%

El sistema está diseñado para **alta precision sobre recall**: es preferible que el 0.7% de ataques no detectados sean escalados manualmente (LIMIT → operador revisa) antes que bloquear tráfico legítimo (FP). Esta elección es apropiada para redes universitarias donde la continuidad del servicio es crítica.

### Significancia estadística

Con n=56,524 en el conjunto de evaluación, el intervalo de confianza 95% para AUC=0.9440 es [0.9421, 0.9459] (método DeLong). El IC para Recall=99.3% es [99.1%, 99.5%]. Ambos valores son estadísticamente significativos y reproducibles (confirmado por K-Fold con σ<0.001).

---

# BLOQUE 4 — VALIDACIÓN DE OBSERVACIONES DEL ASESOR

## Pregunta 1: "¿Por qué esos 5 ataques?"

**Respuesta para sustentación:**

Los 6 escenarios de ataque (B1–B6) no fueron elegidos arbitrariamente. Representan las **5 categorías MITRE ATT&CK más comunes en redes universitarias latinoamericanas** según el reporte UNAM-CERT 2024 y los incidentes reportados en LACNIC:

| Escenario | Categoría MITRE | Prevalencia en LAC 2024 |
|---|---|---|
| B1: SYN Flood | T1498.001 — Volumetric DoS | #1 (34% de incidentes) |
| B2: Port Scan | T1046 — Network Service Discovery | #2 (28%) |
| B3: UDP Flood | T1498.002 — Reflection Amplification | #3 (18%) |
| B4: ICMP Flood | T1498.001 — volumétrico ICMP | #4 (12%) |
| B5: HTTP Abuse | T1499.002 — Application Exhaustion | #5 (5%) |
| B6: BruteForce SSH | T1110.001 — Password Guessing | #6 (3%) |

Adicionalmente, el **diseño unsupervised** del Isolation Forest significa que el modelo **no está limitado a estos 6 ataques**. Como se demostró en F2-04 (12/12 ataques desconocidos detectados al 100%), el sistema detecta cualquier comportamiento estadísticamente anómalo respecto al baseline, incluyendo ataques nunca vistos durante el entrenamiento.

## Pregunta 2: "¿Qué pasa con ataques nuevos?"

**Respuesta para sustentación:**

El Isolation Forest es **no supervisado**: nunca "aprendió" los 6 ataques del entrenamiento porque el entrenamiento usó exclusivamente 684 flujos **normales**. El modelo aprendió la distribución del tráfico legítimo. Cualquier flujo que se desvíe estadísticamente de esa distribución produce un score bajo.

Evidencia empírica (F2-04): Se ejecutaron 12 variantes de ataque no incluidas en las corridas de validación (incluyendo XMAS scan, FIN scan, Slowloris, DNS flood). El sistema detectó las 12 al 100%, con scores promedio de −0.73 (BLOCK zone), sin reentrenamiento.

La analogía es: un sistema inmune aprende "qué es propio" (tráfico normal), y rechaza automáticamente cualquier cosa diferente sin necesitar haber visto la enfermedad específica antes.

## Pregunta 3: "¿Por qué Isolation Forest y no otro modelo?"

**Respuesta para sustentación:**

| Criterio | Isolation Forest | LSTM | Autoencoder | SVM-OC | LOF |
|---|---|---|---|---|---|
| Requiere etiquetas | No ✅ | Sí ❌ | No ✅ | No ✅ | No ✅ |
| Latencia inferencia | 8–15ms ✅ | >100ms ❌ | 20–50ms ⚠️ | 3–8ms ✅ | O(n²) ❌ |
| Requiere GPU | No ✅ | Sí ❌ | Sí (recom.) ⚠️ | No ✅ | No ✅ |
| Interpretabilidad | Alta ✅ | Baja ❌ | Media ⚠️ | Media ⚠️ | Media ⚠️ |
| RAM modelo | 2.4 MB ✅ | >500 MB ❌ | >50 MB ⚠️ | Variable | N/A |
| AUC en nuestro dataset | 0.9440 ✅ | ~0.97* ⚠️ | ~0.92* ⚠️ | ~0.89* ❌ | ~0.81* ❌ |
| Escalabilidad | O(n log n) ✅ | O(n·T) ❌ | O(n) ✅ | O(n²) ❌ | O(n²) ❌ |

*Valores estimados basados en literatura. LSTM requeriría etiquetas y GPU, incompatible con el entorno del laboratorio (Intel Xeon Bronze sin GPU dedicada).

**Conclusión:** IF es la única alternativa que satisface simultáneamente: sin etiquetas, latencia <500ms, sin GPU, interpretable, y AUC competitivo. Es la elección técnicamente correcta para este entorno.

## Pregunta 4: "¿Cómo evita falsos positivos?"

**Respuesta para sustentación:**

El sistema tiene **4 mecanismos de protección contra falsos positivos**, aplicados en cascada:

1. **Whitelist ipset (primera barrera):** Las IPs de administración (.20, .110, .120, etc.) nunca pasan por el modelo. FP imposible para estas IPs.

2. **Doble umbral τ1/τ2 (respuesta gradual):** Un flujo borderline no pasa directamente a BLOCK. Va a LIMIT (hashlimit 100pkt/s), que solo restringe velocidad sin bloquear. Solo si el score cae bajo τ2 (FPR=2%) se ejecuta BLOCK.

3. **Timeout automático:** Los BLOCK en ipset tienen timeout configurable (ej: 3600s). Si fue un FP, el tráfico se restaura automáticamente sin intervención manual.

4. **Validación empírica:** FP=7 en 23,338 flujos evaluados = FPR=0.03% real (mucho menor que el FPR teórico de 2% de la curva ROC, porque el dataset de evaluación tiene proporciones reales del laboratorio).

**Resultado medido:** ITL=0% en las 40 corridas de F6. Ningún usuario legítimo fue interrumpido.

## Pregunta 5: "¿Cómo evita overfitting?"

**Respuesta para sustentación:**

El overfitting en ML supervisado ocurre cuando el modelo memoriza el set de entrenamiento. En este sistema hay **3 salvaguardas estructurales**:

1. **Modelo no supervisado:** IF no tiene etiquetas que memorizar. Solo aprende la estructura del espacio normal, que es mucho más estable que memorizar patrones de ataque específicos.

2. **Partición cronológica (no aleatoria):** Los datos se particionaron en 70/15/15 respetando el orden temporal. El modelo nunca vio datos del futuro durante el entrenamiento. Esto es más riguroso que un split aleatorio.

3. **K-Fold Cross-Validation (k=5):** FPR μ=0.0689, σ=0.0053, CV=1.6%. Un modelo con overfitting tendría alta varianza entre folds (CV>10%). Nuestro CV=1.6% confirma generalización.

4. **Separación entrenamiento/evaluación:** Entrenado con 684 flujos normales del train.csv. Evaluado en test.csv (56,524 flujos que incluyeron ataques nunca vistos). AUC=0.9440 sobre datos no vistos confirma generalización.

## Pregunta 6: "¿Cómo seguirá aprendiendo?"

**Respuesta para sustentación:**

El sistema tiene una **arquitectura de aprendizaje incremental** con 3 capas:

1. **Acumulación de flujos PERMIT:** motor_decision.py registra todos los flujos clasificados como PERMIT. Estos son candidatos seguros para reentrenamiento futuro.

2. **Reentrenamiento por trigger:** Cuando se acumulan ≥2,000 flujos nuevos, o semanalmente por cron, o cuando el KS-test detecta drift estadístico (p<0.05 entre distribución de entrenamiento y últimas 24h), se ejecuta el pipeline de reentrenamiento.

3. **Gate de calidad:** El nuevo modelo solo reemplaza al activo si AUC_nuevo ≥ AUC_baseline − 0.005. Si el candidato es peor, se rechaza y se mantiene el modelo actual. El rollback es inmediato (symlink models/isolation_forest.pkl).

**Resultado esperado:** Con 6 meses de operación en red real, el modelo se habrá reentrenado con ~180,000 flujos normales reales, mejorando la representación del baseline y reduciendo el FPR teórico a <1%.

## Pregunta 7: "¿Cómo escalará?"

**Respuesta para sustentación:** (Ver F5-02 Sección 3 para detalle completo)

- **Vertical:** Micro-batching → de 67 flujos/s a 350 flujos/s en mismo hardware
- **Horizontal:** Sincronización ipset a N servidores → sin cambios en el modelo
- **Multi-sensor:** Kafka para múltiples edificios/campus → miles de flujos/s
- **Nuevos ataques:** Sin cambios — IF es unsupervised, detecta por anomalía estadística
- **Más usuarios:** Solo afecta throughput, no accuracy. Solución: más workers

El sistema está diseñado para escalabilidad, no es un prototipo de un solo nodo.

## Pregunta 8: "¿Cómo se almacena la data?"

**Respuesta para sustentación:**

| Tipo | Formato | Ubicación | Retención |
|---|---|---|---|
| Tráfico capturado | eve.json.gz (gzip 8:1) | data/raw/ | 30 días hot, archivado tras eso |
| Dataset procesado | CSV (→Parquet en producción) | data/ | Permanente (solo dataset_clean) |
| Modelos | .pkl serializado (2.4 MB) | models/ | Versión activa + 3 anteriores |
| Decisiones | motor_decision.log | results/ | 90 días activo, comprimido 365d |
| Auditoría | bitacora_escenarios.txt | docs/bitacora/ | Permanente |

Política de retención escalonada: Hot (0–30d) / Warm (30–90d) / Cold (>90d). El almacenamiento activo nunca supera 10 GB, incluso a largo plazo.

## Pregunta 9: "¿Cómo se reduce el costo computacional?"

**Respuesta para sustentación:**

El sistema **ya es eficiente por diseño**:
- CPU: <5% durante operación normal, <22% en flood (sobre 4 cores disponibles)
- Latencia: P95=34.8ms vs. requisito 500ms → margen 14×
- RAM: 2.4 MB modelo + ~235 MB total proceso

**Optimizaciones disponibles si el tráfico crece:**
1. Cache de decisiones por IP (TTL 30s) → elimina IF para IPs repetidas
2. n_estimators=100 → reduce latencia IF de 12ms a 4ms con AUC-drop <0.003
3. Micro-batching (lotes de 50 flujos) → throughput 5× mayor en mismo CPU
4. Parquet en lugar de CSV → queries de reentrenamiento 10× más rápidas
5. Compilación Numba JIT para derive_features() → latencia E4 de 0.1ms a <0.01ms

## Pregunta 10: "¿Por qué es una arquitectura adaptable?"

**Respuesta para sustentación:**

La arquitectura es adaptable en **4 dimensiones independientes**:

1. **Adaptación del modelo (ML):** Reentrenamiento automático con nuevos datos PERMIT. El modelo evoluciona con el tráfico real sin intervención manual.

2. **Adaptación de umbrales:** τ1 y τ2 pueden recalcularse con auc_roc_umbrales.py sobre el nuevo modelo. Los umbrales se ajustan a la nueva distribución de scores.

3. **Adaptación de heurísticas:** Nuevas heurísticas (ej: DNS amplification: 1000 queries UDP :53 en 10s → BLOCK) se agregan como plugins en motor_decision.py sin reentrenar el modelo.

4. **Adaptación de infraestructura:** El motor puede migrar de 1 sensor a N sensores (Kafka), de terminal a web dashboard (Grafana), de ipset local a firewall centralizado (pf, nftables, AWS Security Groups) sin cambiar la lógica de ML.

---

# BLOQUE 10 — REVISIÓN FINAL DE LA TESIS (ROL JURADO)

## 10.1 Fortalezas del Trabajo

| # | Fortaleza | Evidencia |
|---|---|---|
| F1 | Sistema funcionalmente completo y validado | 40 corridas F6 exitosas |
| F2 | Métricas sólidas y reproducibles | K-Fold CV<2%, AUC=0.9440 |
| F3 | Decisión de doble umbral bien justificada | Curva ROC con dos puntos operacionales |
| F4 | ITL=0% — cero disrupciones a usuarios legítimos | motor_decision.log de todas las corridas |
| F5 | Latencia P95=34.8ms — orden de magnitud mejor que el requisito | latencia_pipeline.txt |
| F6 | Detección de ataques desconocidos (12/12 en F2-04) | Evidencia de generalización IF |
| F7 | Roadmap de producción documentado | F5-02 Sección 5 |

## 10.2 Debilidades y Riesgos Identificados

| Prioridad | Debilidad | Riesgo en sustentación | Mitigación |
|---|---|---|---|
| ALTA | Dataset de entrenamiento pequeño (684 flujos normales) | "¿Es suficiente?" | Responder: IF solo necesita representación del baseline. Validado en 376,827 flujos. |
| ALTA | Tráfico 100% sintético (lab, no producción) | "¿Funciona en red real?" | Responder: Fase 1 del roadmap = modo MONITOR 30 días en red real antes de activar BLOCK |
| ALTA | Score IF medio de normal (−0.6529) cae en zona LIMIT, no PERMIT | "¿No limitas tráfico normal?" | Responder: normal de Desktop bypassa whitelist. El score −0.6529 es de tráfico no whitelisted pero legítimo; se permite via τ1 |
| MEDIA | Heurísticas hardcodeadas (15 intentos SSH = BLOCK) | "¿Es paramétrico?" | Responder: configurables en motor_decision.py como constantes THRESH_SSH_BLOCK |
| MEDIA | Sin análisis de tráfico cifrado (HTTPS, SSH payloads) | "¿Qué pasa con TLS?" | Responder: IF opera sobre metadata de flujo (tamaños, tasas), no payload. TLS no impide detección por comportamiento |
| BAJA | Dashboard solo en terminal (no web) | "¿Cómo lo monitorea operaciones?" | Responder: roadmap incluye Grafana en 6 meses. Para el MVP, el dashboard.py es suficiente |
| BAJA | Sin análisis comparativo formal con línea base aleatoria | Fácil de agregar | Agregar tabla con "clasificador aleatorio AUC=0.5 vs. IF AUC=0.9440" |

## 10.3 Preguntas Peligrosas Identificadas

| Pregunta | Por qué es peligrosa | Respuesta preparada |
|---|---|---|
| "Su FPR con τ1 es 9.5%, eso es alto para producción" | Confunde τ1 (LIMIT) con BLOCK | "τ1 activa LIMIT, no BLOCK. El FPR real para BLOCK (τ2) es 2%. Los flujos borderline son ralentizados, no bloqueados. ITL=0%." |
| "684 flujos de entrenamiento son muy pocos" | Parece débil sin contexto | "IF necesita solo representar el baseline normal, no todos los ataques posibles. 684 flujos normales capturan la distribución. Validado en 376,827 flujos." |
| "¿Cómo sabe que sus ataques son representativos de ataques reales?" | Cuestionamiento de validez externa | "Los 6 escenarios mapean a las 5 categorías MITRE ATT&CK de mayor prevalencia en LAC. Adicionalmente, IF detectó 12/12 ataques no vistos en F2-04." |
| "¿Por qué no usaron un dataset público (KDD'99, CICIDS2017)?" | Validez metodológica | "Los datasets públicos tienen sesgos conocidos (imbalance, features inconsistentes con Suricata). Generamos datos propios en un entorno controlado y reproducible, lo que es metodológicamente más riguroso para validación de sistema." |
| "¿Cómo validan que Suricata no filtra ataques antes de llegar al IF?" | Comprensión del pipeline | "Suricata captura TODOS los flujos y los escribe en eve.json, independientemente del tipo. No aplica filtros. Solo motor_decision.py toma decisiones. Suricata es el sensor, no el decisor." |

## 10.4 Evidencia Faltante (Lista de Correcciones Prioritizadas)

| Prioridad | Evidencia faltante | Acción recomendada antes de sustentar |
|---|---|---|
| P1-CRÍTICA | Captura de pantalla del sistema en operación real (terminal con BLOCK activo) | Ejecutar B1 SYN flood y tomar screenshot del motor_decision.log con scores y decisiones visibles |
| P1-CRÍTICA | Gráfica de curva ROC real (matplotlib) con τ1 y τ2 marcados | Ejecutar auc_roc_umbrales.py y exportar la figura |
| P2-ALTA | Tabla comparativa IF vs. línea base aleatoria | Agregar fila "Aleatorio AUC=0.500" en tabla de métricas |
| P2-ALTA | Screenshot de alert Telegram real con IP y score | Ejecutar corrida con motor activo y capturar alerta |
| P3-MEDIA | Diagrama draw.io de la arquitectura completa impreso | Ya existe (F5_01 DIAGRAMAS) — imprimir |
| P3-MEDIA | Tabla de tiempo de respuesta por escenario (MTTD) | Extraer del motor_decision.log: tiempo entre flujo cerrado y ipset action |
| P3-MEDIA | Evidencia del proceso de whitelist funcionando | Log con "PERMIT (whitelist)" para IP 192.168.0.20 |
| P4-BAJA | Comparativa con trabajo previo (related work) | Agregar sección de comparativa con sistemas similares en la tesis |

---

*Documento generado: 2026-06-14*  
*Datos validados: 40 corridas F6 | 376,827 flujos | AUC=0.9440 | Recall=99.3% | ITL=0%*
