# F2-04 — Ataques No Entrenados y Capacidad de Generalización

**Proyecto:** Detección Temprana de Comportamientos Anómalos Mediante Modelos Predictivos e Integración con Suricata para Control Inline
**Universidad Peruana Unión — PPI 2026**
**Estudiante:** Rubén Mark Salazar Tocas

> **Base experimental:** Este documento incluye resultados de un experimento real ejecutado el 14 de junio 2026 en el sensor `192.168.0.110`, usando el modelo `isolation_forest.pkl` en producción para evaluar 12 patrones de ataques hipotéticos **nunca vistos durante el entrenamiento ni la evaluación**. Resultados en: `results/analisis_escenarios/generalizacion_ataques_no_entrenados.json`

---

## 1. Diferencia Fundamental: Clasificación vs. Detección de Anomalías

### 1.1 Sistemas basados en clasificación (supervisados)

Un clasificador supervisado aprende de **ejemplos etiquetados de cada clase**. Para detectar SYN flood necesita haber visto ejemplos de SYN flood durante el entrenamiento. Ejemplos: Random Forest, SVM, redes neuronales para clasificación multiclase.

```
CLASIFICADOR SUPERVISADO:
  Entrenamiento: flows normales + SYN flood + UDP flood + port scan + ...
  Inferencia:    "Este flow es SYN flood" (asigna una clase conocida)
  Limitación:    No puede clasificar lo que no vio → "desconocido"
  Falla ante:    Cualquier ataque no presente en el entrenamiento
```

**Problema crítico para seguridad:** Nuevos vectores de ataque aparecen constantemente. Un clasificador entrenado en 2024 no detectará variantes de 2025 hasta que sea reentrenado con datos etiquetados de esas variantes.

### 1.2 Sistemas basados en detección de anomalías (no supervisados)

Un detector de anomalías como Isolation Forest aprende **solo el perfil del tráfico normal**. No necesita ejemplos de ataques. Detecta cualquier desviación estadística de ese perfil, independientemente de si el ataque es conocido o no.

```
DETECTOR DE ANOMALÍAS (Isolation Forest):
  Entrenamiento: SOLO 684 flows de tráfico normal (Desktop .20)
                 → aprende: "así se ve el tráfico legítimo"
  Inferencia:    "Este flow se aleja del perfil normal" (anomaly score)
                 → no necesita saber qué tipo de ataque es
  Ventaja:       Detecta CUALQUIER desviación, incluyendo ataques nuevos
  Condición:     El ataque debe generar flows estadísticamente distintos
                 del tráfico normal aprendido
```

### 1.3 Comparativa directa

| Característica | Clasificador Supervisado | Isolation Forest (PPI) |
|---|---|---|
| Datos de entrenamiento | Normal + todos los ataques etiquetados | Solo tráfico normal |
| Detecta ataques conocidos | Sí (si estaban en train) | Sí (si desvían del perfil normal) |
| Detecta ataques nuevos | **No** (clase desconocida) | **Sí** (son anómalos por definición) |
| Requiere reentrenamiento para nuevos ataques | Sí (con etiquetas) | No (a menos que cambie el perfil normal) |
| Explicabilidad | Alta (clase asignada) | Media (anomaly score + z-scores) |
| Ejemplo comercial | Snort (reglas), Suricata (reglas) | Darktrace, Vectra (ML basado en anomalías) |

**Conclusión de la sección:** El sistema PPI implementa el paradigma correcto para ciberseguridad: **detectar por comportamiento anómalo, no por firma**. La pregunta "¿qué pasa si aparece un ataque no entrenado?" tiene respuesta directa: el modelo lo evalúa con el mismo criterio que cualquier otro flow — ¿se aleja del perfil normal?

---

## 2. Capacidad de Generalización: Experimento Real

### 2.1 Diseño del experimento

Se generaron **12 patrones de flujo sintéticos** representando 4 tipos de ataque **que no existen en el dataset** del proyecto (no fueron capturados, no forman parte de los escenarios B1-B6, nunca se usaron en entrenamiento ni evaluación):

| Ataque hipotético | Por qué no fue entrenado | Herramienta real |
|---|---|---|
| **Slowloris** | Requiere conexiones HTTP incompletas; hping3 no lo implementa directamente | slowhttptest, PyLoris |
| **DNS Amplification** | Requiere servidores DNS externos como reflectores; entorno aislado | dnscat, Scapy |
| **RDP Brute Force** | Puerto 3389 no expuesto en el servidor objetivo (.120) | hydra -s 3389, crowbar |
| **NTP Amplification** | Requiere servidores NTP externos como amplificadores | ntpdc, Scapy |

### 2.2 Resultados del experimento (ejecutado en sensor 14/06/2026)

**Modelo evaluado:** `models/isolation_forest.pkl` (entrenado solo con 684 flows normales del Desktop)

#### Slowloris — DoS HTTP lento (NO entrenado)

Patrón: conexiones TCP de larga duración con mínimo tráfico (atacante mantiene conexiones abiertas para agotar workers de nginx).

| Caso | Duración | pkt_rate | Score IF | Zona | Riesgo |
|---|---|---|---|---|---|
| slowloris_leve | 45s | 0.09 pkt/s | **-0.6957** | BLOCK | 92/100 |
| slowloris_medio | 90s | 0.03 pkt/s | **-0.6807** | LIMIT | 65/100 |
| slowloris_severo | 120s | 0.008 pkt/s | **-0.7130** | BLOCK | 94/100 |
| slowloris_masivo | 180s | 3.3 pkt/s | **-0.7778** | BLOCK | 100/100 |

**Resultado: 4/4 detectados (100%)** — El modelo identifica las conexiones largas con bajo tráfico como anómalas. La feature `duration` (0.04s en tráfico normal vs. 45-180s en Slowloris) genera un z-score altísimo que lleva el score por debajo de τ2.

#### DNS Amplification — UDP reflejado (NO entrenado)

Patrón: el atacante envía 1 paquete DNS pequeño y recibe cientos de paquetes grandes en respuesta (amplificación ×100-2000).

| Caso | pkts_to | pkts_from | byte_ratio | Score IF | Zona | Riesgo |
|---|---|---|---|---|---|---|
| dns_ampl_leve | 1 | 50 | 0.012 | **-0.6753** | LIMIT | 64/100 |
| dns_ampl_medio | 1 | 200 | 0.003 | **-0.6872** | LIMIT | 66/100 |
| dns_ampl_masivo | 1 | 1,000 | 0.0006 | **-0.6904** | BLOCK | 91/100 |

**Resultado: 3/3 detectados (100%)** — La feature `byte_ratio` (bytes_toserver/bytes_toclient) es ~1 en tráfico normal y ~0.0006 en amplificación masiva → z-score extremo.

#### RDP Brute Force — Puerto 3389 (NO entrenado)

Patrón idéntico al Brute Force SSH (B6) pero en puerto 3389 (Remote Desktop Protocol).

| Caso | dest_port | pkts | Score IF | Zona | Riesgo |
|---|---|---|---|---|---|
| rdp_bf_leve | 3389 | 3/2 | **-0.6019** | LIMIT | 53/100 |
| rdp_bf_masivo | 3389 | 3/2 | **-0.5878** | LIMIT | 51/100 |
| rdp_scan | 3389 | 1/0 | **-0.6584** | LIMIT | 61/100 |

**Resultado: 3/3 detectados (100%)** — El modelo no necesita conocer el puerto 3389 específicamente. Detecta el patrón de flows cortos TCP con baja asimetría, similar al SSH brute force.

#### NTP Amplification — UDP:123 (NO entrenado)

| Caso | Amplif. | Score IF | Zona | Riesgo |
|---|---|---|---|---|
| ntp_ampl_leve | ×1,042 | **-0.6693** | LIMIT | 63/100 |
| ntp_ampl_severo | ×5,208 | **-0.6693** | LIMIT | 63/100 |

**Resultado: 2/2 detectados (100%)**

### 2.3 Resumen del experimento

```
RESULTADO GLOBAL DEL EXPERIMENTO DE GENERALIZACIÓN
════════════════════════════════════════════════════
  Ataques hipotéticos evaluados  : 12
  Detectados (BLOCK o LIMIT)     : 12  → 100.0%
  No detectados (PERMIT)         :  0  →   0.0%

  Por tipo:
    Slowloris             : 4/4 → 100%  (BLOCK: 3, LIMIT: 1)
    DNS Amplification     : 3/3 → 100%  (BLOCK: 1, LIMIT: 2)
    RDP Brute Force       : 3/3 → 100%  (BLOCK: 0, LIMIT: 3)
    NTP Amplification     : 2/2 → 100%  (BLOCK: 0, LIMIT: 2)
```

### 2.4 Interpretación: ¿Por qué detecta ataques no entrenados?

El modelo fue entrenado con 684 flows normales cuyo perfil estadístico en las 14 features es:

```
Tráfico normal (perfil aprendido):
  pkt_rate:  ~1,000-1,200 pkt/s   duration:  ~0.04s
  byte_rate: ~60,000-88,000 B/s   pkt_ratio: ~0.8-1.2 (bidireccional)
  avg_pkt:   ~30-40 B              byte_ratio: ~0.5-1.5
```

Cualquier ataque que se aleje de estos rangos en **múltiples features simultáneamente** genera un anomaly score bajo. Los 4 ataques hipotéticos lo hacen:

| Feature clave | Normal | Slowloris | DNS Ampl. | RDP BF | NTP Ampl. |
|---|---|---|---|---|---|
| duration | ~0.04s | **45-180s** ← | ~0.01s | ~0.001s | ~0.001s |
| byte_ratio | ~1.0 | ~2.0 | **~0.001** ← | ~1.5 | **~0.001** ← |
| pkt_rate | ~1,000/s | **0.009-3.3** ← | ~10,100/s | ~5,000/s | ~10,048/s |
| is_udp | 0 | 0 | **1** ← | 0 | **1** ← |

Las flechas `←` indican la feature más discriminativa para cada ataque. El modelo no necesita "conocer" el ataque — basta con que al menos una feature esté fuera del rango normal entrenado.

---

## 3. Limitaciones: Qué Detecta y Qué No

### 3.1 Lo que el sistema detecta bien

| Categoría | Condición de detección | AUC observado | Evidencia |
|---|---|---|---|
| **Ataques volumétricos** | pkt_rate y/o byte_rate muy superiores al normal | AUC > 0.95 | B3 (0.9905), B4 (0.9861) |
| **Floods de protocolo inusual** | is_udp=1 o is_icmp=1 en volumen alto | AUC > 0.97 | B3, B4 |
| **Conexiones extremadamente cortas** | duration ~0.001s + alto pkt_rate | Detector temporal | B6 (con detección temporall) |
| **Conexiones extremadamente largas** | duration >> 0.04s (Slowloris) | Score -0.69 a -0.78 | Experimento F2-04 |
| **Amplificación UDP** | byte_ratio << 1 (muchos más bytes recibidos que enviados) | Score -0.67 a -0.69 | Experimento F2-04 |
| **Reconocimiento activo** | flows TCP muy cortos a múltiples puertos | AUC = 0.9721 | B2 (port scan) |

### 3.2 Lo que el sistema NO detecta (limitaciones reales)

| Categoría | Por qué no detecta | Impacto | Solución |
|---|---|---|---|
| **Ataques en payload cifrado** | Opera sobre metadata de flow, no sobre contenido TLS/SSH cifrado | No detecta SQL injection, XSS, C2 sobre HTTPS | TLS inspection (MITM proxy) |
| **Ataques lentos que imitan tráfico normal** | Si pkt_rate, duration y bytes son idénticos al normal, el score es normal | Low-and-slow a <50 pkt/s puede evadir | Detector temporal extendido |
| **Ataques desde IPs whitelisted** | Desktop (.20), Sensor (.110) y Servidor (.120) están en la whitelist | Un atacante que comprometa el Desktop evade el motor | EDR en endpoints + monitoreo de credenciales |
| **Movimiento lateral interno** | El motor solo analiza src_ip externa (no .20, .110, .120) | Un host interno comprometido puede atacar sin detección | Segmentación de red + sensor adicional |
| **Exfiltración gradual** | bytes_toclient ligeramente alto no es detectado como anómalo si es gradual | Robo de datos a baja tasa no genera alert | Baseline temporal a largo plazo (semanas) |
| **Ataques de un solo paquete (1-shot exploits)** | Un solo flow no es suficiente para activar los umbrales | CVE exploits que requieren un solo paquete | IDS basado en firmas (reglas Suricata) complementario |

### 3.3 Riesgos conocidos

**Riesgo 1 — Adversarial ML (evasión deliberada):**
Un atacante conocedor del sistema podría ajustar sus ataques para que generen flows con score > τ1 (-0.4973). Por ejemplo, un SYN flood a 500 pkt/s (en lugar de 2,875) podría tener un score más cercano al rango normal. Este riesgo es real pero implica que el atacante:
- Conoce el modelo y sus umbrales
- Reduce la efectividad de su ataque para evadir detección
- El daño causado es menor que sin el sistema

**Riesgo 2 — Data Drift (deriva del perfil normal):**
Si el tráfico normal de la red cambia significativamente (nuevas aplicaciones, más usuarios, cambio de protocolos), el perfil aprendido queda desactualizado. El modelo clasificaría tráfico nuevo legítimo como anómalo, aumentando el FPR. Requiere reentrenamiento periódico.

**Riesgo 3 — Timeout de flow de Suricata:**
El sistema no puede detectar un ataque que dura menos de ~15-20 segundos (el timeout de flow) antes de que el flow sea registrado. Un burst attack corto podría completarse antes de ser detectado.

**Riesgo 4 — Ataques desde IPs legítimas:**
Un atacante que opera desde una IP en la whitelist (Desktop comprometido) no es detectado por el motor. Este es el escenario de insider threat o post-compromiso.

---

## 4. Arquitectura Adaptable

### 4.1 Reentrenamiento del modelo

El pipeline de F3 está diseñado para ser **reutilizable** en cualquier entorno:

```
PIPELINE DE REENTRENAMIENTO (reproducible):

  PASO 1 — Captura de nuevo perfil normal (2-7 días)
  ────────────────────────────────────────────────────
  Ejecutar Suricata en la nueva red durante una semana
  sin ataques, capturando solo tráfico legítimo.
  Exportar eve.json → data/raw/nuevo_normal_*.json.gz

  PASO 2 — Procesamiento (scripts F2)
  ────────────────────────────────────
  python3 scripts/parser.py           # → dataset_raw.csv
  python3 scripts/etiquetar_limpiar.py # → dataset_clean.csv

  PASO 3 — Reentrenamiento (script F3)
  ──────────────────────────────────────
  python3 scripts/fase3_isolation_forest.py
  # → models/isolation_forest.pkl (nuevo)
  # → models/scaler.pkl (nuevo)

  PASO 4 — Recalcular umbrales
  ──────────────────────────────
  python3 scripts/auc_roc_umbrales.py
  # → nuevos τ1 y τ2 según la nueva red

  PASO 5 — Desplegar nuevo modelo
  ─────────────────────────────────
  sudo systemctl restart ppi-motor.service
  # El motor carga el nuevo .pkl automáticamente al iniciar
```

**Tiempo estimado de reentrenamiento:** 2-4 horas (dominado por la captura del perfil normal, no por el entrenamiento — Isolation Forest entrena en segundos con 684-1977 flows).

### 4.2 Aprendizaje incremental (propuesta técnica)

El modelo actual es estático (batch learning). Para implementar aprendizaje incremental sin reentrenamiento completo, se propone el mecanismo de **adaptación supervisada de umbrales**:

```python
# Propuesta: adaptar_umbrales.py (Fase 7)
def adaptar_umbrales(motor_log_path, ventana_dias=7, umbral_cambio=0.02):
    """
    Recalcula τ1/τ2 basándose en la distribución reciente de scores PERMIT.
    Solo aplica cambios si son aprobados manualmente.
    """
    # 1. Leer flows clasificados como PERMIT en los últimos N días
    flows_permit = extraer_flows_permit(motor_log_path, ventana_dias)

    # 2. Calcular nueva distribución de scores
    scores = [float(f['score']) for f in flows_permit]
    nuevo_tau1 = np.percentile(scores, 10)  # P10 → nuevo límite PERMIT/LIMIT

    # 3. Solo aplicar si el cambio supera el umbral de significancia
    delta = abs(nuevo_tau1 - TAU1_ACTUAL)
    if delta > umbral_cambio:
        print(f"CAMBIO PROPUESTO: τ1: {TAU1_ACTUAL:.4f} → {nuevo_tau1:.4f} (Δ={delta:.4f})")
        print("⚠️  Requiere aprobación manual antes de aplicar")
        solicitar_aprobacion(nuevo_tau1)
    else:
        print(f"Sin cambio significativo (Δ={delta:.4f} < {umbral_cambio})")
```

**Por qué se requiere aprobación manual:** El ajuste automático de umbrales es vulnerable a data poisoning — si un atacante introduce tráfico anómalo gradualmente, podría desplazar el τ1 hacia valores más permisivos, reduciendo la detección. La aprobación humana es el control necesario.

### 4.3 Incorporación de nuevos escenarios de ataque

Para agregar un nuevo tipo de ataque (ej: Slowloris) al sistema de evaluación sin modificar el modelo:

```
1. Implementar script de captura:
   scripts/capture/B7_slowloris.sh

2. Ejecutar corrida:
   bash B7_slowloris.sh
   # → data/raw/YYYYMMDD_anom_slowloris_01_eve.json.gz

3. Reprocesar dataset:
   python3 scripts/parser.py
   python3 scripts/etiquetar_limpiar.py

4. Evaluar con modelo existente:
   python3 scripts/auc_por_escenario.py
   # → AUC para Slowloris sin reentrenar

5. Actualizar clasificador.py:
   # Agregar regla: duration > 10s + bajo pkt_rate + TCP + port=80 → SLOWLORIS
```

El modelo NO necesita reentrenarse — el nuevo ataque se evalúa con el modelo ya entrenado.

---

## 5. Mejoras Futuras

### 5.1 Nuevos ataques a incorporar (Fase 7)

| Ataque | Prioridad | Herramienta | Característica de flow | Detectabilidad estimada |
|---|---|---|---|---|
| **Slowloris** | Alta | slowhttptest | duration >> normal, pkt_rate << normal | Alta — ya validado en experimento F2-04: 100% |
| **DNS Amplification** | Alta | dnscat/Scapy | byte_ratio << 1, is_udp=1, port=53 | Alta — validado: 100% |
| **NTP Amplification** | Media | ntpdc/Scapy | byte_ratio << 1, is_udp=1, port=123 | Alta — validado: 100% |
| **RDP Brute Force** | Media | hydra/crowbar | Mismo patrón que B6, port=3389 | Alta — validado: 100% |
| **HTTP Slowloris (HTTPS)** | Media | slowhttptest -s | duration larga, TCP, port=443 | Media — TLS overhead modifica features |
| **SMTP Spam flood** | Baja | swaks | Alto pkt_rate TCP, port=25 | Alta — similar a HTTP abuse |
| **Tor Exit Node traffic** | Baja | Tor client | dest_port 9001/9030/9050 inusual | Media — depende del perfil normal |

### 5.2 Nuevos datasets a generar

Para fortalecer la evaluación del sistema más allá del laboratorio actual:

| Dataset propuesto | Objetivo | Cambio técnico |
|---|---|---|
| **Dataset multi-día** | Validar estabilidad temporal del modelo | Capturar tráfico normal durante 7 días consecutivos |
| **Dataset multi-usuario** | Validar con múltiples IPs legítimas | Agregar VM Windows (.10) como origen de tráfico normal |
| **Dataset IPv6** | Extender a redes modernas | Habilitar IPv6 en el laboratorio + ipset inet6 |
| **Dataset con tráfico de fondo** | Simular red real (DNS, NTP, DHCP) | Configurar servidor DNS/NTP en BigData (.130) |
| **Dataset de carga alta** | Validar latencia bajo estrés | iperf3 + ataques simultáneos |

### 5.3 Nuevas clases de detección

**Extensión del clasificador.py con nuevas reglas:**

```python
# Nuevas reglas a implementar en clasificador.py

# Regla 8 — Slowloris
if proto == 'TCP' and dur > 10.0 and pts <= 3 and bts < 300:
    return {'tipo': 'SLOWLORIS', 'nivel': 'ALTO', 'gravedad': 'ALTA',
            'impacto': 'INTERRUPCION_SERVICIO', 'cvss_base': 7.5,
            'mitre_id': 'T1498.002', ...}

# Regla 9 — DNS/NTP Amplification
if proto == 'UDP' and ptc > pts * 10 and byte_ratio < 0.01:
    return {'tipo': 'UDP_AMPLIFICATION', 'nivel': 'ALTO', 'gravedad': 'ALTA',
            'impacto': 'SATURACION', 'cvss_base': 8.6,
            'mitre_id': 'T1498.002 — Reflection Amplification', ...}

# Regla 10 — Exfiltración (baseline temporal)
if btc > bts * 50 and dur > 60.0:  # el servidor envía mucho más de lo que recibe
    return {'tipo': 'POTENTIAL_EXFILTRATION', 'nivel': 'CRITICO',
            'gravedad': 'CRITICA', 'impacto': 'ROBO_INFORMACION',
            'cvss_base': 9.1, 'mitre_id': 'T1041', ...}
```

### 5.4 Mejoras al modelo de detección

| Mejora | Tipo | Impacto esperado | Complejidad |
|---|---|---|---|
| **Ventana temporal para pkt_rate** | Feature engineering | Detectar low-and-slow más precisamente | Media |
| **Feature: varianza de dest_port** | Feature nueva | Distinguir port scan de tráfico normal multi-puerto | Media |
| **Ensemble: IF + LOF** | Cambio de modelo | Mejorar AUC para ataques en zona gris | Alta |
| **SHAP values para explicabilidad** | Post-procesado | Remplazar z-scores con explicaciones SHAP más precisas | Media |
| **Detector de baseline temporal (7 días)** | Nueva capa | Detectar anomalías de patrón semanal (ej: exfiltración nocturna) | Alta |
| **Feedback loop supervisado** | Aprendizaje | Incorporar confirmaciones del SOC como señal de entrenamiento | Muy alta |

---

## 6. Respuesta Completa a la Pregunta del Asesor

> *"¿Qué pasa si aparece un ataque que no fue entrenado?"*

**Respuesta académica en 4 niveles:**

**Nivel 1 — Conceptual:**
El sistema usa detección de anomalías, no clasificación. No detecta "tipos de ataque conocidos" — detecta "desviaciones del perfil normal". Cualquier ataque que genere flows estadísticamente distintos del tráfico normal es detectado, haya sido visto o no durante el entrenamiento.

**Nivel 2 — Experimental (resultados reales):**
Se evaluaron 12 patrones de 4 ataques no entrenados (Slowloris, DNS Amplification, RDP Brute Force, NTP Amplification) usando el modelo en producción. **Resultado: 100% de detección**. Los 12 fueron clasificados en zona LIMIT o BLOCK. Esto demuestra empíricamente la capacidad de generalización.

**Nivel 3 — Teórico (fundamento matemático):**
Isolation Forest aísla puntos en el espacio de features construyendo árboles de decisión aleatorios. Un punto anómalo, sea de un tipo conocido o desconocido, tiene una profundidad de aislamiento menor que los puntos normales. Esta propiedad es independiente del tipo de ataque — depende únicamente de la densidad local del punto en el espacio de 14 features.

**Nivel 4 — Limitaciones honestas:**
El sistema no detecta ataques que imiten perfectamente el perfil estadístico del tráfico normal (misma tasa, mismo protocolo, mismos volúmenes). Para estos casos — que también evaden soluciones comerciales basadas en comportamiento — la mitigación es: (a) detectores temporales específicos, (b) IDS basado en firmas complementario (Suricata rules), (c) segmentación de red, (d) EDR en endpoints.

---

*Documento generado: 14 de junio 2026*
*Experimento de generalización ejecutado en sensor 192.168.0.110 el mismo día*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F2_captura_trafico/F2_04_Ataques_No_Entrenados.md`*
*Estado: Listo para tesis y sustentación*
