# Evaluación del MVP desde Múltiples Perspectivas

**PPI — Universidad Peruana Unión | Rubén Mark Salazar Tocas**

---

## 1. Perspectiva Académica / Investigación

### ¿Qué se evaluá?
Rigor metodológico, reproducibilidad, contribución al conocimiento, comparación con literatura.

| Criterio | Evaluación | Nota |
|---|---|---|
| Hipótesis claramente definida | El IF puede detectar anomalías de red con AUC ≥ 0.85 | **Sí** |
| Metodología reproducible | Pipeline documentado en 6 fases, artefactos versionados en Git | **Alta** |
| Validación estadística | Mann-Whitney en EDA, curva ROC con criterio Youden, 40 corridas | **Adecuada** |
| Comparación con alternativas | IF vs AE en mismas condiciones, métricas idénticas | **Sí** |
| Resultados honestos | Limitaciones documentadas (FPR, lead time, entorno lab) | **Sí** |
| Publicabilidad | AUC=0.8998, F1=0.9947 — competitivo con literatura CICIDS/NSL-KDD | **Media-alta** |

**Fortalezas:**
- Datos propios capturados en entorno controlado reproducible
- EDA previo al modelado con hallazgos concretos (byte_ratio 62.8×)
- Experimento comparativo IF vs AE documentado con números reales
- Código, datos y resultados en repositorio público

**Debilidades:**
- Muestra pequeña de tipos de ataque (6 categorías vs decenas en literatura)
- Sin comparación con baseline trivial (e.g., threshold fijo en byte_rate)
- No se reportan intervalos de confianza en las métricas

**Calificación académica estimada: 16/20**

---

## 2. Perspectiva de Ingeniería / Técnica

### ¿Qué se evalúa?
Diseño del sistema, robustez, eficiencia, mantenibilidad, despliegue.

| Criterio | Evaluación | Calificación |
|---|---|---|
| Arquitectura modular | 6 fases desacopladas, cada una con entradas/salidas definidas | **Excelente** |
| Latencia | P95=34.8ms — 14× bajo el límite de 500ms | **Excelente** |
| Disponibilidad | 100% en 40 corridas | **Excelente** |
| Mantenibilidad | Scripts documentados, venv fijado (sklearn 1.9.0), Git versionado | **Buena** |
| Robustez ante fallos | systemd `Restart=on-failure`, rotación automática de eve.json | **Buena** |
| Escalabilidad | Throughput: 29 flows/s — suficiente para red universitaria pequeña | **Limitada** |
| Seguridad del propio sistema | Token GitHub en remote URL, sin TLS en comunicación sensor↔motor | **Mejorable** |
| Monitoreo | Dashboard web en :8080, log en tiempo real, pero sin alertas activas | **Parcial** |

**Fortalezas:**
- Pipeline completamente automatizable (un comando por fase)
- Motor de decisión como servicio systemd con arranque automático
- Tres niveles de decisión (PERMIT/LIMIT/BLOCK) más granular que binario
- Whitelist ipset garantiza ITL=0% sin modificar el modelo

**Debilidades:**
- Sin alta disponibilidad (único sensor, único motor)
- Throughput de 29 flows/s puede ser insuficiente en redes de alto tráfico
- No hay mecanismo de rollback automático si el nuevo modelo degrada el rendimiento
- Las reglas ipset se pierden al reiniciar el servidor sin script de persistencia

**Calificación técnica estimada: 17/20**

---

## 3. Perspectiva de Seguridad

### ¿Qué se evalúa?
Efectividad de detección, cobertura de amenazas, resistencia a evasión.

| Criterio | Evaluación | Calificación |
|---|---|---|
| Tasa de detección (TPR) | 99.40% @ τ1 | **Excelente** |
| Falsos positivos operativos | ITL=0% con whitelist | **Excelente** |
| Cobertura de tipos de ataque | 6/6 categorías B detectadas | **Buena** |
| Velocidad de respuesta | Lead time ~62s (SYN flood) / < 5s (heurísticos) | **Media** |
| Resistencia a evasión | Sin mecanismo anti-evasión activo | **Baja** |
| Cobertura de protocolos | TCP/UDP/ICMP — sin HTTPS payload | **Parcial** |
| Control inline (bloqueo real) | ipset DROP activo — no solo alertas | **Excelente** |
| Detección de ataques lentos | No evaluada (exfiltración, slow loris) | **No evaluada** |

**Fortalezas:**
- El sistema no solo detecta sino que **bloquea activamente** (diferencia clave vs IDS puro)
- Tres niveles de respuesta proporcionales a la severidad del score
- Detectores heurísticos complementan al modelo ML para ataques conocidos
- Whitelist estática evita bloqueos accidentales de servicios críticos

**Debilidades:**
- 62 segundos de exposición en SYN flood antes del primer BLOCK
- Sin inspección de payload (Suricata en modo flujo, no IDS completo)
- Un atacante con acceso a la IP de la whitelist (192.168.0.20) no sería bloqueado
- Sin detección de ataques de exfiltración o movimiento lateral

**Calificación de seguridad estimada: 15/20**

---

## 4. Perspectiva Operacional

### ¿Qué se evalúa?
Facilidad de uso, operación diaria, mantenimiento, observabilidad.

| Criterio | Evaluación | Calificación |
|---|---|---|
| Facilidad de arranque | `systemctl start ppi-motor.service` — un comando | **Excelente** |
| Observabilidad en tiempo real | Dashboard web :8080 + terminal + log | **Buena** |
| Gestión de bloqueos manuales | `enforce.sh <ip> BLOCK\|LIMIT\|UNBLOCK` | **Buena** |
| Procedimiento de reentrenamiento | Documentado en F3_especificacion.md §14, 3 comandos | **Buena** |
| Alertas proactivas | No implementadas (email, Slack, etc.) | **Falta** |
| Documentación operativa | CLAUDE.md, 6 fases documentadas, bitácora de corridas | **Excelente** |
| Curva de aprendizaje | Requiere conocimiento de Linux, systemd, Python y Suricata | **Media** |

**Fortalezas:**
- Sistema completamente gestionable por SSH desde el Desktop de administración
- Bitácora automática de corridas para auditoría
- Dashboard web accesible desde navegador sin instalar nada adicional

**Debilidades:**
- Sin alertas: un operador debe revisar activamente el dashboard para enterarse de un BLOCK
- Sin interfaz gráfica de gestión de reglas (solo línea de comandos)
- Sin exportación de logs a SIEM (Splunk, ELK)

**Calificación operacional estimada: 14/20**

---

## 5. Perspectiva de Escalabilidad

### ¿Qué se evalúa?
Capacidad para manejar más tráfico, más nodos, más usuarios.

| Criterio | Estado actual | Límite conocido |
|---|---|---|
| Throughput del motor | 29 flows/s | ~2,500 flows/día en red pequeña |
| Número de sensores | 1 (hardcoded) | Sin soporte multi-sensor |
| Número de modelos | 1 IF activo (motor universal soporta IF/AE) | Ensemble pendiente |
| Tamaño de ipset | No medido | ipset soporta millones de entradas |
| Almacenamiento de logs | eve.json rotado por corrida | Crecimiento lineal sin purga automática |

**Bottleneck principal:** el motor procesa `eve.json` con `tail -f` en un único proceso Python — no paralelo. A 29 flows/s, una red universitaria con 500 usuarios generando 100 flows/usuario/hora excedería el throughput en horas pico.

**Para escalar:**
- Procesar `eve.json` en lotes con múltiples workers
- Desplegar sensores Suricata en múltiples puntos de la red con un motor centralizado
- Migrar de ipset local a una política centralizada (SDN, firewall de borde)

**Calificación de escalabilidad estimada: 10/20**

---

## Resumen de Evaluación por Perspectiva

| Perspectiva | Calificación | Fortaleza clave | Debilidad clave |
|---|---|---|---|
| Académica | **16/20** | Metodología reproducible y honesta | Sin intervalos de confianza |
| Técnica / Ingeniería | **17/20** | Latencia 14× bajo límite, modular | Throughput limitado, sin HA |
| Seguridad | **15/20** | Bloqueo activo, TPR=99.40% | Lead time 62s, sin anti-evasión |
| Operacional | **14/20** | Un comando para arrancar, documentación completa | Sin alertas proactivas |
| Escalabilidad | **10/20** | Motor universal IF/AE | Un solo proceso, un solo sensor |
| **PROMEDIO** | **14.4/20** | Sistema funcional completo para PPI | Listo para escalar en siguiente fase |

### Veredicto general

El MVP cumple su objetivo: es un sistema **funcional, validado y documentado** que demuestra la viabilidad de usar Isolation Forest para detección de anomalías en redes de datos con control inline. Las limitaciones identificadas (escalabilidad, anti-evasión, alertas) son esperadas en un prototipo de investigación de esta escala y están todas documentadas con propuestas concretas de mejora.

**Para un PPI universitario: APROBADO con distinción en ingeniería.**

