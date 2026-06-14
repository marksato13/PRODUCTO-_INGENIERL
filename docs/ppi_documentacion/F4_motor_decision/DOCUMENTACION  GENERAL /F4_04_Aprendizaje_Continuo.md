# F4-04 — Aprendizaje Continuo, Reentrenamiento y Adaptabilidad del Modelo

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fase:** F4 — Motor de Decisión  
**Fecha:** 2026-06-14  

---

## 1. Aprendizaje Continuo

### Contexto del sistema actual

El Isolation Forest (IF) en producción fue entrenado con **684 flows normales** de los escenarios A1–A4 (HTTP normal, SSH legítimo, transferencia legítima, tráfico sostenido). El modelo aprende la **distribución del tráfico normal** — no los patrones de ataque. Esta distinción es fundamental para entender cómo el sistema puede seguir aprendiendo.

La pregunta del asesor ("el modelo debe poder seguir aprendiendo") tiene respuesta directa: **el sistema ya está diseñado para adaptarse**, porque solo necesita datos normales nuevos, no ejemplos de ataques.

---

### 1.1 Aprendizaje Incremental

El aprendizaje incremental consiste en **actualizar el modelo progresivamente** sin descartar el conocimiento previo, incorporando nuevas observaciones a medida que llegan.

**Mecanismo para IF:**

Scikit-learn's Isolation Forest no soporta `partial_fit()` nativo. Sin embargo, el aprendizaje incremental se implementa con un **ensemble evolutivo**:

```
Modelo v1 (300 árboles, entrenado con flujos 1–684)
     +
Modelo incremental (50 árboles nuevos, entrenados con flujos 685–1200)
     ↓
Score final = 0.7 × score_v1 + 0.3 × score_incremental
```

Este esquema de **weighted ensemble** permite:
- Preservar conocimiento del modelo base (estable, validado)
- Incorporar patrones de tráfico normal nuevo (adaptatif)
- Ajustar pesos según la antigüedad del submodelo (decay temporal)

**Ventaja operativa:** Si el servidor incorpora nuevos servicios (ej. HTTPS/443), los flows normales de ese servicio se acumulan → se entrena un sub-modelo incremental → el IF combinado reconoce el nuevo servicio como normal sin reentrenamiento completo.

**Cuándo usar incremental:**
- Nuevos servicios o protocolos legítimos
- Cambios graduales en patrones (horarios, volúmenes)
- Menos de 500 nuevos flows normales disponibles

---

### 1.2 Aprendizaje por Lotes (Batch Retraining)

El aprendizaje por lotes consiste en **acumular un conjunto suficiente de flows nuevos** y reentrenar el modelo desde cero con los datos históricos + nuevos datos normales combinados.

**Pipeline batch:**

```python
# Trigger: 2,000+ nuevos flows normales acumulados
NEW_FLOWS_THRESHOLD = 2000

def batch_retrain():
    # 1. Cargar flows normales históricos (acumulados desde inicio)
    df_historico = pd.read_csv("data/normal_flows_historico.csv")
    
    # 2. Agregar nuevos flows validados como normales
    df_nuevos = pd.read_csv("data/normal_flows_nuevos.csv")
    df_combined = pd.concat([df_historico, df_nuevos]).drop_duplicates()
    
    # 3. Reentrenar IF con toda la base normal
    scaler_nuevo = StandardScaler().fit(X_normal_combined)
    if_nuevo = IsolationForest(
        n_estimators=300,
        contamination=0.05,
        random_state=42
    ).fit(scaler_nuevo.transform(X_normal_combined))
    
    # 4. Recalibrar umbrales desde nueva curva ROC
    tau1_nuevo, tau2_nuevo = calibrar_umbrales(if_nuevo, eval_set)
    
    # 5. Validar antes de guardar
    if validar_calidad(if_nuevo, tau1_nuevo, tau2_nuevo):
        guardar_modelo(if_nuevo, scaler_nuevo, version="v2.0")
```

**Ventaja operativa:** Al reentrenar con más datos normales, el modelo delimita la "zona normal" con mayor precisión → reduce FPR → menos interrupciones a tráfico legítimo.

**Cuándo usar batch:**
- Cambios significativos en la infraestructura de red
- Acumulación de ≥2,000 flows normales nuevos validados
- Drift detectado en distribución de features (ver sección 3)

---

### 1.3 Reentrenamiento Periódico

El reentrenamiento periódico ejecuta el pipeline batch en **intervalos programados**, independientemente de si el trigger de cantidad de datos fue alcanzado.

**Calendario propuesto:**

| Frecuencia | Condición | Acción |
|---|---|---|
| Semanal | Normal (producción estable) | Batch retrain si ≥2,000 flows nuevos |
| Mensual | Siempre | Batch retrain con todos los flows acumulados |
| Inmediato | FPR detectado > 15% | Diagnóstico + posible retrain de emergencia |
| Semestral | Cambios de infraestructura | Recolección de nuevos escenarios A1–A4 |

**Implementación con cron en el sensor:**

```bash
# /etc/cron.d/ppi-retrain
# Lunes 03:00 — verificar acumulación de flows normales
0 3 * * 1 m4rk /home/m4rk/ppi-surikata-producto/scripts/check_retrain.sh

# 1ro de cada mes — retrain forzado
0 2 1 * * m4rk /home/m4rk/ppi-surikata-produto/scripts/batch_retrain.sh --force
```

**Proceso check_retrain.sh:**
```bash
#!/bin/bash
NUEVOS=$(wc -l < /data/normal_flows_nuevos.csv)
if [ "$NUEVOS" -ge 2000 ]; then
    /home/m4rk/ppi-surikata-produto/scripts/batch_retrain.sh
    logger "PPI: Reentrenamiento ejecutado con $NUEVOS flows nuevos"
fi
```

---

## 2. Ataques No Entrenados

### Principio fundamental: IF no aprende ataques, aprende la normalidad

Esta es la característica más importante del Isolation Forest aplicado a detección de anomalías: **el modelo nunca vio un ataque durante el entrenamiento**. Aprendió qué es tráfico normal; cualquier cosa diferente es anomalía — sin importar si ese tipo de ataque existía o no cuando se entrenó.

**Evidencia experimental (F2-04):** Se probaron **12 tipos de ataque no entrenados**:
- Slowloris (HTTP slow attack)
- DNS Amplification
- RDP Brute Force
- NTP Amplification
- FTP Brute Force
- SMB Scan
- SMTP Flood
- ARP Spoofing  
- Telnet Scan
- SNMP Enumeration
- HTTP Slowloris variant
- ICMP Redirect

**Resultado: 12/12 detectados al 100%** con score promedio en zona BLOCK (< τ2 = −0.6873).

---

### 2.1 Nuevos Ataques

Cuando aparece un ataque completamente nuevo, el IF responde según cómo difiere del tráfico normal en las 14 features:

| Tipo de ataque nuevo | Features principales afectadas | Score esperado | Acción |
|---|---|---|---|
| HTTP/2 Rapid Reset (nuevo en 2023) | `pkt_rate`, `byte_rate`, `pkts_toserver` | < τ2 | BLOCK |
| QUIC Flood | `is_udp`, `pkt_rate`, `dest_port` | < τ2 | BLOCK |
| BGP Hijacking (si afecta al sensor) | `dest_port`, `byte_ratio` | < τ1 | LIMIT/BLOCK |
| IoT Botnet (Mirai-like) | `pkt_rate`, `bytes_toserver`, `is_tcp` | < τ2 | BLOCK |
| Exfiltración lenta (APT) | Sutil — `byte_ratio` elevado, `duration` largo | Posiblemente > τ1 | PERMIT (riesgo) |

**Caso crítico — Ataques low-and-slow (APT):** Estos ataques imitan tráfico legítimo deliberadamente. El IF puede no detectarlos si el flujo individual es indistinguible del normal. **Mitigación:** Agregación temporal (ventana de 60s) + detector heurístico de sesiones largas con alta entropía de destinos.

---

### 2.2 Variantes Desconocidas

Las variantes de ataques conocidos (ej. SYN Flood con TTL alterado, Port Scan con intervalos aleatorios) **siguen siendo detectadas** porque las features volumétricas no cambian:

```
SYN Flood variante (paquetes con TTL=64 en lugar de TTL=128):
├── pkt_rate     → muy alto (igual que SYN Flood estándar)
├── bytes_toserver → muy bajo por paquete (igual)
├── pkts_toclient  → ≈0 (igual — servidor dropea)
└── Score IF     → < τ2 → BLOCK (mismo resultado)
```

El atacante puede modificar el payload o los headers IP, pero **no puede ocultar las características volumétricas** sin sacrificar el impacto del ataque.

---

### 2.3 Patrones Anómalos Emergentes

Los patrones emergentes son aquellos que individualmente parecen normales pero en conjunto revelan un ataque (ej. reconocimiento sigiloso, exfiltración fragmentada).

**Mecanismo de detección complementario:**

El motor_decision.py actual ya implementa detección heurística por ventana temporal:

```python
# Detector de Brute Force SSH (ventana 60s)
if intentos_ssh[src_ip] >= 15:
    enforce(src_ip, "BLOCK", timeout=3600)

# Detector de HTTP Abuse (ventana 30s)  
if requests_http[src_ip] >= 100:
    enforce(src_ip, "BLOCK", timeout=3600)
```

**Extensión propuesta para patrones emergentes:**

```python
# Detector de reconocimiento sigiloso (port scan lento)
# Trigger: >20 dest_ports distintos en 300s desde misma IP
if puertos_visitados[src_ip]["count_300s"] > 20:
    enforce(src_ip, "LIMIT", timeout=1800)
    log_emergent_pattern(src_ip, "slow_scan")

# Detector de exfiltración (ratio upload/download anómalo)
# Trigger: bytes_toserver > 50MB Y byte_ratio > 100 en 600s
if bytes_acumulados[src_ip]["upload_600s"] > 52_428_800 and byte_ratio > 100:
    enforce(src_ip, "LIMIT", timeout=7200)
    log_emergent_pattern(src_ip, "exfiltration_suspect")
```

Estos detectores heurísticos se **actualizan independientemente del modelo IF** y pueden añadirse sin reentrenamiento.

---

## 3. Arquitectura Adaptable

### Diagrama de la arquitectura evolutiva

```
╔══════════════════════════════════════════════════════════════════╗
║                    SISTEMA EN PRODUCCIÓN                        ║
║                                                                  ║
║  [Suricata 7.0.3] ──→ eve.json ──→ [Motor IF v1.X]            ║
║                                          │                       ║
║                              ┌───────────┼───────────┐          ║
║                           PERMIT       LIMIT       BLOCK        ║
║                              │                       │          ║
║                    [Collector Normal]        [Log Ataques]       ║
║                              │                       │          ║
║                    flows normales acum.    patrones detectados   ║
╚══════════════════════════════════════════════════════════════════╝
                               │
                    ¿≥2,000 flows nuevos?
                    ¿FPR drift > 5%?
                    ¿Reentrenamiento semanal?
                               │
                               ▼
╔══════════════════════════════════════════════════════════════════╗
║                    PIPELINE DE ADAPTACIÓN                       ║
║                                                                  ║
║  Paso 1: NUEVA DATA                                             ║
║  ├── normal_flows_nuevos.csv  (flows PERMIT no-whitelist)       ║
║  ├── Validación manual: muestra aleatoria 50 flows revisada     ║
║  └── Filtro automático: FPR simulado < 10% antes de incluir     ║
║                               │                                  ║
║  Paso 2: VALIDACIÓN PREVIA                                      ║
║  ├── FPR en val set histórico con scaler nuevo                  ║
║  ├── Recall en eval set balanceado (23,338 flows)               ║
║  └── AUC-ROC comparado vs. modelo actual                        ║
║                               │                                  ║
║  Paso 3: REENTRENAMIENTO                                        ║
║  ├── IF(n=300, contamination=0.05) en normal_flows_historico    ║
║  ├── StandardScaler fit en nuevos normales acumulados           ║
║  └── Umbral recalibrado con Youden index en nueva curva ROC     ║
║                               │                                  ║
║  Paso 4: CONTROL DE CALIDAD                                     ║
║  ├── Gate 1: FPR ≤ 10% ✓                                       ║
║  ├── Gate 2: Recall ≥ 95% ✓                                    ║
║  ├── Gate 3: AUC ≥ 0.98 ✓                                      ║
║  └── Gate 4: Latencia P95 < 500ms ✓                            ║
║                               │                                  ║
║  Paso 5: NUEVA VERSIÓN DEL MODELO                               ║
║  ├── isolation_forest_v{N}.pkl + scaler_v{N}.pkl               ║
║  ├── umbrales_v{N}.txt (τ1, τ2 nuevos)                         ║
║  ├── Backup de versión anterior (retención: últimas 3)          ║
║  └── Deploy con recarga en caliente (sin downtime)              ║
╚══════════════════════════════════════════════════════════════════╝
                               │
                               ▼
╔══════════════════════════════════════════════════════════════════╗
║                    MOTOR IF v{N+1} EN PRODUCCIÓN                ║
║  ├── Modelo actualizado con nuevos patrones normales            ║
║  ├── Umbrales recalibrados                                      ║
║  └── Detectores heurísticos extendidos (si aplica)             ║
╚══════════════════════════════════════════════════════════════════╝
```

### Colección de flows normales en producción

Para que la arquitectura adaptable funcione, el motor_decision.py debe **registrar los flows marcados como PERMIT** (excluyendo la whitelist):

```python
# Extensión al motor_decision.py para recolección adaptativa
PERMIT_LOG = "/home/m4rk/ppi-surikata-produto/data/normal_flows_nuevos.csv"

def log_permit_flow(flow_features, src_ip, score):
    """Registra flows PERMIT no-whitelist para reentrenamiento futuro."""
    if src_ip not in WHITELIST and score > TAU1:
        with open(PERMIT_LOG, "a") as f:
            row = {**flow_features, "score": score, "timestamp": time.time()}
            f.write(",".join(str(v) for v in row.values()) + "\n")
```

**Nota de seguridad:** Los flows PERMIT no son automáticamente "buenos" — un atacante podría inyectar flows cuidadosamente crafted que pasen el IF y se añadan al dataset de normales (envenenamiento de datos). Por eso se requiere validación manual de muestra antes de incluir en reentrenamiento.

---

## 4. Estrategia de Actualización

### 4.1 Frecuencia de Actualización

**Modelo base (IF + Scaler):**

| Trigger | Condición | Prioridad | Responsable |
|---|---|---|---|
| Acumulación | ≥2,000 flows normales nuevos validados | Alta | Script automático |
| Semanal | Cada lunes 03:00 (si hay ≥500 flows) | Media | Cron job |
| Mensual | 1ro de cada mes (forzado) | Media | Cron job |
| Drift de FPR | FPR detectado > 15% en producción | Urgente | Alerta + acción manual |
| Infraestructura | Nuevo servicio/protocolo en red | Alta | Manual |
| Semestral | Revisión completa con nuevas corridas A1–A4 | Planificada | Manual (PPI) |

**Detectores heurísticos:**

| Trigger | Condición | Acción |
|---|---|---|
| Nuevo tipo de ataque detectado | Análisis post-incidente | Agregar regla heurística |
| FP en heurística | 3+ reportes de bloqueo incorrecto | Ajustar umbral del detector |
| Nueva vulnerabilidad CVE crítica | Publicación NVD | Evaluar si requiere nueva regla |

---

### 4.2 Versionado del Modelo

**Esquema de versionado semántico:**

```
isolation_forest_v{MAJOR}.{MINOR}.{PATCH}.pkl

MAJOR: Cambio en arquitectura del modelo (features, n_estimators)
MINOR: Reentrenamiento batch con datos nuevos significativos
PATCH: Recalibración de umbrales solamente

Ejemplo:
isolation_forest_v1.0.0.pkl  ← modelo original (F3, 684 flows)
isolation_forest_v1.1.0.pkl  ← primer batch retrain (684 + 2,000 nuevos)
isolation_forest_v1.1.1.pkl  ← recalibración de τ1 solamente
isolation_forest_v2.0.0.pkl  ← añadida feature "dest_ip_entropy" (cambio MAJOR)
```

**Estructura de directorios:**

```
/home/m4rk/ppi-surikata-produto/models/
├── current/
│   ├── isolation_forest.pkl      ← symlink → v1.1.0
│   ├── scaler.pkl                ← symlink → scaler_v1.1.0
│   └── umbrales_finales.txt      ← τ1=-0.4832, τ2=-0.6941 (actualizados)
├── versions/
│   ├── v1.0.0/
│   │   ├── isolation_forest_v1.0.0.pkl
│   │   ├── scaler_v1.0.0.pkl
│   │   ├── umbrales_v1.0.0.txt
│   │   └── metrics_v1.0.0.json   ← AUC, FPR, Recall al momento del deploy
│   ├── v1.1.0/                   ← versión actual
│   └── v1.0.0_backup/            ← rollback disponible
└── changelog.txt                 ← historial de versiones
```

**Rollback automático:**

```bash
#!/bin/bash
# rollback.sh — restaurar versión anterior si nueva versión falla
PREV_VERSION=$(cat /models/versions/prev_version.txt)
ln -sf /models/versions/${PREV_VERSION}/isolation_forest.pkl \
       /models/current/isolation_forest.pkl
systemctl restart ppi-motor.service
logger "PPI ROLLBACK: restaurado ${PREV_VERSION}"
```

---

### 4.3 Control de Calidad

**4 Gates de validación antes de cada deploy:**

```
┌─────────────────────────────────────────────────────────────────┐
│  GATE 1 — Tasa de Falsos Positivos                             │
│  Métrica: FPR en val set (684 flows normales originales)       │
│  Umbral: FPR ≤ 10%                                             │
│  Falla: Si el nuevo modelo rechaza más del 10% del tráfico     │
│          normal conocido → ROLLBACK automático                  │
├─────────────────────────────────────────────────────────────────┤
│  GATE 2 — Recall de Ataques Conocidos                          │
│  Métrica: Recall en eval set balanceado (11,669 ataques)       │
│  Umbral: Recall ≥ 95%                                          │
│  Falla: Si nuevo modelo pierde más del 5% de ataques           │
│          conocidos → Investigar y NO deploy                     │
├─────────────────────────────────────────────────────────────────┤
│  GATE 3 — Discriminación (AUC-ROC)                             │
│  Métrica: AUC en eval set balanceado (23,338 flows)            │
│  Umbral: AUC ≥ 0.98                                            │
│  Falla: Si AUC cae más de 0.01 vs. modelo actual → NO deploy  │
├─────────────────────────────────────────────────────────────────┤
│  GATE 4 — Rendimiento Operativo                                │
│  Métrica: Latencia P95 de inferencia                           │
│  Umbral: P95 < 500ms                                           │
│  Falla: Si nuevo modelo es >2x más lento → Revisar             │
└─────────────────────────────────────────────────────────────────┘
```

**Script de validación automática:**

```python
def validar_calidad(modelo_nuevo, scaler_nuevo, tau1_nuevo, tau2_nuevo):
    """
    Retorna True si el modelo pasa todos los gates de calidad.
    """
    # Gate 1: FPR en normales originales
    X_val_normal = cargar_normales_originales()
    scores = modelo_nuevo.score_samples(scaler_nuevo.transform(X_val_normal))
    fpr = (scores <= tau2_nuevo).mean()
    assert fpr <= 0.10, f"GATE 1 FALLA: FPR={fpr:.4f} > 0.10"
    
    # Gate 2: Recall en ataques conocidos
    X_eval, y_eval = cargar_eval_balanceado()
    scores_eval = modelo_nuevo.score_samples(scaler_nuevo.transform(X_eval))
    y_pred = (scores_eval <= tau1_nuevo).astype(int)
    recall = recall_score(y_eval, y_pred)
    assert recall >= 0.95, f"GATE 2 FALLA: Recall={recall:.4f} < 0.95"
    
    # Gate 3: AUC
    auc = roc_auc_score(y_eval, -scores_eval)
    assert auc >= 0.98, f"GATE 3 FALLA: AUC={auc:.4f} < 0.98"
    
    # Gate 4: Latencia
    t0 = time.time()
    for _ in range(100):
        modelo_nuevo.score_samples(scaler_nuevo.transform(X_eval[:100]))
    latencia_p95 = (time.time() - t0) / 100 * 1000  # ms
    assert latencia_p95 < 500, f"GATE 4 FALLA: Latencia={latencia_p95:.1f}ms"
    
    return True
```

---

## 5. Implementación Futura en Producción

### Arquitectura de producción preparada para escala

La arquitectura actual (MVP en VM de laboratorio) puede evolucionar hacia un sistema de producción real con los siguientes componentes:

```
╔══════════════════════════════════════════════════════════════════════╗
║                    ARQUITECTURA PRODUCCIÓN FUTURA                   ║
║                                                                      ║
║  ┌─────────────────────────────────────────────────────────────┐    ║
║  │              CAPA DE CAPTURA (sin cambios)                  │    ║
║  │  Suricata 7.0.3 → eve.json → motor_decision.py             │    ║
║  └──────────────────────────┬──────────────────────────────────┘    ║
║                             │                                        ║
║  ┌──────────────────────────▼──────────────────────────────────┐    ║
║  │              CAPA DE DATOS ADAPTATIVA                       │    ║
║  │  ┌─────────────────┐   ┌────────────────────────────────┐   │    ║
║  │  │  Flow Store     │   │  Feature Drift Monitor         │   │    ║
║  │  │  (SQLite/CSV)   │   │  (KS-test cada 1h en features) │   │    ║
║  │  │  PERMIT logs    │   │  Alert si p-value < 0.05       │   │    ║
║  │  └────────┬────────┘   └──────────────┬─────────────────┘   │    ║
║  └───────────┼──────────────────────────┼─────────────────────┘    ║
║              │                          │                            ║
║  ┌───────────▼──────────────────────────▼─────────────────────┐    ║
║  │              CAPA DE ENTRENAMIENTO ADAPTATIVO               │    ║
║  │  ┌──────────────────────────────────────────────────────┐   │    ║
║  │  │  Retrain Scheduler                                   │   │    ║
║  │  │  ├── Trigger: 2000 flows / semanal / drift alert     │   │    ║
║  │  │  ├── Ejecuta: batch_retrain.py                       │   │    ║
║  │  │  └── Valida: 4 Gates → deploy o rollback             │   │    ║
║  │  └──────────────────────────────────────────────────────┘   │    ║
║  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │    ║
║  │  │ Model v1.X  │  │ Model v2.X   │  │ A/B Test (24h)     │  │    ║
║  │  │ (producción)│  │ (candidato)  │  │ 90% v1 / 10% v2    │  │    ║
║  │  └─────────────┘  └──────────────┘  └────────────────────┘  │    ║
║  └────────────────────────────────────────────────────────────┘    ║
║                                                                      ║
║  ┌─────────────────────────────────────────────────────────────┐    ║
║  │              CAPA DE CONTROL EN LÍNEA (sin cambios)         │    ║
║  │  ipset ppi_blocked / ppi_limited → iptables DROP/LIMIT      │    ║
║  └─────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Componentes nuevos para producción

| Componente | Tecnología | Función |
|---|---|---|
| Flow Store | SQLite o PostgreSQL | Persistir flows PERMIT para reentrenamiento |
| Feature Drift Monitor | SciPy KS-test | Detectar cambios en distribución de features |
| Retrain Scheduler | APScheduler (Python) | Orquestar disparadores de reentrenamiento |
| A/B Testing | nginx + iptables mark | Validar modelo nuevo en subconjunto de tráfico |
| Model Registry | Sistema de archivos + changelog.txt | Versionado y rollback |
| Alerting | syslog + mail | Notificar gates fallidos o drift detectado |

### Detección de drift de features

```python
from scipy import stats

def detectar_drift(features_hist, features_nuevo, umbral_pvalue=0.05):
    """
    Kolmogorov-Smirnov test para detectar si la distribución de features
    ha cambiado significativamente vs. datos históricos.
    """
    resultados = {}
    for feat in FEATURES:
        ks_stat, p_value = stats.ks_2samp(
            features_hist[feat].values,
            features_nuevo[feat].values
        )
        if p_value < umbral_pvalue:
            resultados[feat] = {
                "drift_detectado": True,
                "ks_statistic": round(ks_stat, 4),
                "p_value": round(p_value, 6)
            }
    
    if resultados:
        logger.warning(f"DRIFT en features: {list(resultados.keys())}")
        trigger_retrain(motivo="feature_drift", detalles=resultados)
    
    return resultados
```

**Ejemplo de drift real:** Si la red incorpora tráfico de video streaming (RTSP), las features `byte_rate` y `bytes_toclient` cambiarían drásticamente para flows normales. El KS-test lo detectaría y dispararía un reentrenamiento para que el modelo aprenda que ese volumen de datos ya es "normal".

---

## 6. Relación con las Observaciones del Asesor

### Observación: "El modelo debe poder seguir aprendiendo"

**Respuesta completa:**

El sistema tiene **tres capas de aprendizaje continuo**:

**Capa 1 — Modelo IF (reentrenamiento batch):**
El IF acumula flows normales del tráfico PERMIT en producción. Cuando se acumulan ≥2,000 flows nuevos, se ejecuta un reentrenamiento batch que amplía el "mapa de normalidad" del modelo. Los umbrales τ1 y τ2 se recalibran automáticamente con el nuevo Youden index. Resultado: el modelo aprende que el nuevo tráfico legítimo (nuevos servicios, nuevos horarios, nuevas IPs autorizadas) es normal.

**Capa 2 — Detectores heurísticos (actualización en caliente):**
Las reglas de Brute Force SSH y HTTP Abuse pueden modificarse sin reentrenar el modelo. Nuevas heurísticas se agregan editando `motor_decision.py` y reiniciando el servicio. No hay downtime ni pérdida del modelo entrenado.

**Capa 3 — Umbrales adaptativos (recalibración):**
Si el FPR en producción sube sobre el 15%, los umbrales τ1/τ2 pueden recalibrase con el script `auc_roc_umbrales.py` usando los nuevos datos acumulados, sin reentrenar el modelo completo.

---

### Observación: "¿Cómo evitar que quede limitado a 5 ataques?"

**Respuesta directa: el sistema NUNCA estuvo limitado a 5 ataques.**

Esta es la diferencia fundamental entre el IF y los modelos supervisados:

```
Modelo supervisado (ej. Random Forest):
├── Entrenado CON patrones de SYN Flood, Port Scan, UDP Flood, ICMP Flood, BruteForce
├── Aprende: "estos patrones específicos son ataques"
├── Nuevo ataque (Slowloris): no visto → puede NO detectarlo
└── Para detectar nuevo ataque: NECESITA reentrenarse con ejemplos del nuevo ataque

Isolation Forest (sistema actual):
├── Entrenado SOLO con tráfico normal (HTTP, SSH, SCP legítimos)
├── Aprende: "la distribución del espacio normal"
├── Nuevo ataque (Slowloris): diferente a lo normal → DETECTADO (score < τ)
└── Para detectar nuevo ataque: NO necesita reentrenamiento
```

Los 5 tipos de ataque (B1–B6 del Grupo B) fueron los escenarios de **laboratorio para generar datos de evaluación**, no los patrones que el modelo aprendió a reconocer. El modelo aprendió los 4 escenarios normales (A1–A4).

**Evidencia empírica:** F2-04 probó 12 ataques adicionales no vistos durante el entrenamiento — todos detectados al 100% sin ningún reentrenamiento.

**Para el futuro, el sistema se extiende así:**
- Nuevos tipos de ataque → detectados automáticamente por IF (si difieren de normal)
- Nuevos tipos de ataque de bajo volumen → añadir heurística específica en motor_decision.py
- Nuevos protocolos de ataque → evaluar si requiere nueva feature en el modelo

---

### Observación: "¿Cómo detectar comportamientos nuevos?"

**Tres mecanismos complementarios:**

**Mecanismo 1 — Score IF (ya operativo):**
Cualquier tráfico que difiera de la distribución normal aprendida recibirá un score bajo → LIMIT o BLOCK. No requiere conocer el tipo de ataque. Es el mecanismo principal.

**Mecanismo 2 — Detección de drift de comportamiento:**
El Feature Drift Monitor (propuesto en sección 5) analiza continuamente si la distribución de features de los flows PERMIT está cambiando. Un cambio brusco puede indicar:
- a) Nueva aplicación legítima → reentrenamiento para incorporarla como normal
- b) Ataque low-and-slow que burló el IF → investigación manual + nueva heurística

**Mecanismo 3 — Análisis de sesiones (extensión futura):**
Los flows individuales son la granularidad del IF actual. Un atacante sofisticado puede distribuir el ataque en muchos flows individuales "normales". La extensión es:

```python
# Agregación de sesiones por IP en ventana de 5 minutos
def analizar_sesion(src_ip, ventana_segundos=300):
    flows = obtener_flows_recientes(src_ip, ventana_segundos)
    
    # Comportamiento nuevo: IP visita >50 destinos distintos en 5 min
    destinos_unicos = len(set(f["dest_ip"] for f in flows))
    if destinos_unicos > 50:
        trigger_alerta("reconnaissance", src_ip, destinos_unicos)
    
    # Comportamiento nuevo: ratio upload/download > 100:1 sostenido
    total_upload = sum(f["bytes_toserver"] for f in flows)
    total_download = sum(f["bytes_toclient"] for f in flows)
    if total_upload > 0 and total_download > 0:
        if total_upload / total_download > 100:
            trigger_alerta("exfiltration_suspect", src_ip, total_upload)
```

---

## 7. Estado Actual vs. Estado Futuro

| Capacidad | Estado Actual (MVP) | Estado Futuro (Producción) |
|---|---|---|
| Detección de ataques conocidos | ✅ 99.3% Recall (F6) | ✅ Mejorado con reentrenamiento |
| Detección de ataques nuevos | ✅ 12/12 en F2-04 | ✅ Sin cambios (propiedad del IF) |
| Reentrenamiento automático | ⚪ Manual (script disponible) | ✅ Cron job + triggers |
| Versionado de modelos | ⚪ Un solo modelo | ✅ Sistema de versiones semánticas |
| Colección de datos normales | ⚪ Solo corridas de laboratorio | ✅ Acumulación automática en producción |
| Detección de drift | ⚪ No implementado | ✅ KS-test cada hora |
| A/B testing | ⚪ No implementado | ✅ Deploy gradual 10%→100% |
| Detectores heurísticos | ✅ SSH BF + HTTP Abuse | ✅ Extensibles sin downtime |
| Rollback de modelo | ⚪ Manual | ✅ Automático si gates fallan |

---

## Conclusión

El sistema de detección fue diseñado desde su base con **capacidad de adaptación inherente**, porque:

1. **IF es unsupervised** — no necesita ejemplos de ataque para aprender. Cualquier desviación de la normalidad es detectable, sea el ataque que sea.

2. **La adaptación no requiere ataques etiquetados** — solo flows normales nuevos, que se obtienen automáticamente del tráfico PERMIT en producción.

3. **La arquitectura es modular** — el modelo IF, los umbrales y los detectores heurísticos son componentes independientes que se actualizan en momentos distintos y por razones distintas.

4. **El umbral τ2 es el verdadero clasificador binario** (FP=7, FN=8 en 23,338 flows) — su recalibración periódica mantiene la precisión a medida que el tráfico normal evoluciona.

La respuesta a la observación del asesor es: **el sistema ya puede seguir aprendiendo**, y el plan de producción propuesto en este documento define exactamente cuándo, cómo y con qué criterios de calidad lo hará.

---

## Archivos de referencia

| Archivo | Ruta | Descripción |
|---|---|---|
| Motor de decisión | `scripts/motor_decision.py` | Implementación de detectores heurísticos |
| Modelo IF | `models/isolation_forest.pkl` | Modelo v1.0 en producción |
| Scaler | `models/scaler.pkl` | StandardScaler fit en 684 normales |
| Umbrales | `results/umbrales_finales.txt` | τ1=−0.4973, τ2=−0.6873 |
| Reporte F6 | `results/reports/` | Validación en producción (40 corridas) |

> **Directorio base en el sensor:** `/home/m4rk/ppi-surikata-produto/`
