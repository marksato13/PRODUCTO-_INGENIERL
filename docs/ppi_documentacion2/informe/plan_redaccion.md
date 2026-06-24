# Plan — Informe de Resultados PPI
**Título:** Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Aprendizaje Automático y un Mecanismo de Control en Tiempo Real  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Universidad:** Universidad Peruana Unión — Ingeniería de Sistemas  
**Extensión estimada:** 35–45 páginas

---

## Estructura del informe

### PARTE I — INTRODUCCIÓN (3–4 páginas)

**1. Planteamiento del problema**
- Contexto: crecimiento de ciberataques en redes corporativas (cifras IBM 2023, ENISA)
- Limitación de sistemas reactivos (firewalls estáticos, IDS por firma)
- Necesidad de detección proactiva con respuesta automática
- Pregunta de investigación

**2. Objetivos**
- Objetivo general
- OE1, OE2, OE3 (ya definidos)

**3. Justificación**
- Por qué Isolation Forest (no supervisado, no necesita ataques etiquetados)
- Por qué control inline con ipset/iptables (respuesta sin latencia de red)
- Relevancia para organizaciones sin SOC dedicado

**4. Alcance y limitaciones del estudio**
- Entorno de laboratorio (no producción)
- Topología fija de 4 nodos
- 9 escenarios de prueba definidos

---

### PARTE II — MARCO TEÓRICO (4–5 páginas)

**5. Detección de anomalías en redes**
- Anomalía de tráfico vs intrusión conocida
- Enfoques: estadístico, basado en reglas, ML
- Estado del arte: Isolation Forest en contexto de red

**6. Isolation Forest**
- Principio: aislamiento de observaciones anómalas
- Hiperparámetros clave: n_estimators, contamination
- Score de anomalía: interpretación de [-1, 0]
- Derivación de umbrales desde curva AUC-ROC

**7. Control inline de tráfico**
- ipset + iptables: DROP en kernel
- hashlimit: rate limiting por IP
- Bloqueo progresivo como estrategia adaptativa

**8. XGBoost como predictor de persistencia**
- Predicción de series temporales comportamentales
- Features comportamentales vs features de flujo
- Diferencia con IF: IF detecta, XGBoost predice persistencia

---

### PARTE III — METODOLOGÍA (6–8 páginas)

**9. Entorno de laboratorio**
- Tabla de topología (4 VMs, IPs, roles)
- Herramientas: Suricata 7.0.3, Python 3.x, sklearn 1.9.0, XGBoost, Flask
- Diagrama de red (figura)

**10. Pipeline F1 — Captura de tráfico**
- Suricata en modo promiscuo (ens35)
- eve.json: estructura de un evento de flujo
- 9 escenarios de captura (Grupos A, B, C)
- Nomenclatura de archivos exportados

**11. Pipeline F2 — Procesamiento y dataset**
- 14 features extraídas por flujo (tabla y descripción)
- Etiquetado: NORMAL (Grupo A) vs ANÓMALO (Grupo B)
- Estadísticas del dataset: N total, distribución de clases
- Split 80/20 aleatorio (shuffle=True, random_state=42)

**12. Pipeline F3 — Modelo Isolation Forest**
- Configuración: n=300, contamination=0.05
- Entrenamiento sobre tráfico NORMAL exclusivamente
- Derivación de τ1 y τ2 desde curva AUC-ROC (índice de Youden + FPR≤2%)
- Figura: curva ROC con umbrales marcados

**13. Pipeline F4 — Motor de decisión**
- Arquitectura del motor (tail eve.json → features → score → decisión)
- Lógica de decisión: PERMIT / LIMIT / BLOCK
- Detectores heurísticos: BF-SSH (15 intentos/60s), HTTP-Abuse (100 req/30s)
- Bloqueo progresivo: timeouts 300s / 1800s / permanente
- Whitelist: IPs de confianza nunca bloqueadas

**14. Pipeline F5 — Reentrenamiento automático**
- IF: cada domingo 02:00 (crontab)
- XGBoost: cada día 03:00 (crontab)
- hot-reload del predictor: sin reinicio del servicio
- 10 features comportamentales (tabla) — corrección de data leakage

**15. Pipeline F6 — Validación**
- 40 corridas: 9 escenarios × repeticiones
- Criterios de aceptación (tabla CA-F1 a CA-F6)
- Metodología de medición: latencia P95, ITL, disponibilidad

---

### PARTE IV — RESULTADOS (10–12 páginas) ← NÚCLEO DEL INFORME

**16. Resultados por objetivo**

*OE1 — Pipeline de datos*
- Dataset construido: N flujos, distribución, features
- Figura: distribución de scores IF por clase

*OE2 — Modelo Isolation Forest*
- Tabla de métricas: AUC-ROC, Precision, Recall, F1, FPR@τ1, FPR@τ2
- Figura: curva AUC-ROC con τ1 y τ2
- Figura: distribución de latencia (histograma P95=34.8ms)
- Comparativa por escenario (tabla)

*OE3 — Motor + validación en vivo*
- 40 corridas F6: tabla resumen por escenario
- Figura: timeline de detecciones (f6_03)
- Figura: disponibilidad del sistema (f6_01)
- Figura: panel resumen F6 (f6_07)

**17. Validaciones en vivo (2026-06-22)**

| Validación | Resultado | Evidencia |
|---|---|---|
| Bloqueo progresivo B1 — 3 corridas | ✅ | Log + ipset timeout=0 |
| Lead time B1 SYN Flood | ~62s hasta BLOCK | Motor log 05:44:13 |
| Lead time B6 SSH BF (hydra -t4) | LIMIT 53s / BLOCK 60s | Motor log 08:31:30/37 |
| Telegram BLOCK alerta | ✅ HTTP 200 + recibida | 07:25 |
| Whitelist Desktop (120 req HTTP) | ✅ 0 BLOCK/LIMIT | Motor log + ipset |
| Dashboard web SSE | ✅ Predictor P=55% activo | Captura 09:05 |
| Data leakage XGBoost corregido | AUC 1.0→0.9992 | commit ad573f0 |

**18. Análisis de limitaciones**
- Tabla completa L1–L10 con severidad, mitigación e impacto residual
- FPR=20.47%: análisis del trade-off con TPR (por qué no se baja τ1)
- Lead time ~62s: inherente a arquitectura basada en Netflow
- AVISO-DETERMINISTA: condición no alcanzable en lab con Kali (explicación)
- Comparativa: AUC IF (0.8998) vs AUC XGBoost (0.9992) — propósitos distintos

---

### PARTE V — DISCUSIÓN Y CONCLUSIONES (4–5 páginas)

**19. Discusión**
- Cumplimiento de criterios de aceptación (tabla CA por fase)
- Comparativa con trabajo relacionado (IDS tradicionales)
- Qué hace diferente este sistema: no supervisado + control inline
- Viabilidad de despliegue en entorno real

**20. Conclusiones**
- C1: Isolation Forest es viable para detección en tiempo real (AUC=0.8998, P95=34.8ms)
- C2: Pipeline completo F1-F6 funciona de extremo a extremo con disponibilidad 100%
- C3: Bloqueo progresivo aporta control adaptativo que firewalls estáticos no tienen
- C4: La integración dashboard + Telegram da visibilidad operativa sin SOC dedicado

**21. Trabajos futuros**
- Despliegue en infraestructura real
- Tráfico cifrado (TLS fingerprinting)
- Federación de sensores múltiples
- Reentrenamiento con datos de producción (F5 es la base)

---

### PARTE VI — REFERENCIAS Y ANEXOS

**Referencias**
- IBM Cost of a Data Breach 2023
- Liu et al. (2008) — Isolation Forest paper original
- Suricata documentation
- sklearn IsolationForest docs
- ENISA Threat Landscape 2024

**Anexos**
- A: Dataset — estadísticas completas
- B: Configuración Suricata (suricata.yaml relevante)
- C: Código motor_decision.py (extracto clave)
- D: Bitácora de corridas (bitacora_escenarios.txt)
- E: Resultados F6 completos (resultados_f6_completo.csv)

---

## Plan de redacción

| Sección | Páginas est. | Prioridad | Fuente principal |
|---|---|---|---|
| I Introducción | 3–4 | Alta | Planteamiento ya redactado |
| II Marco teórico | 4–5 | Media | Literatura + CLAUDE.md |
| III Metodología | 6–8 | Alta | CLAUDE.md + scripts |
| **IV Resultados** | **10–12** | **CRÍTICA** | **F6 CSV + logs + capturas** |
| V Conclusiones | 4–5 | Alta | LIMITACIONES.md + métricas |
| VI Refs + Anexos | 3–4 | Media | Bibliografía + archivos |

**Orden de redacción recomendado:**
1. Resultados (IV) — es el core, lo más concreto
2. Metodología (III) — ya tienes todo en CLAUDE.md
3. Conclusiones (V) — derivan de los resultados
4. Introducción (I) — se escribe mejor al final
5. Marco teórico (II) — más bibliográfico
6. Anexos — copiar archivos existentes

**Tiempo estimado:** 3–4 sesiones de trabajo intenso (6–8h totales)
