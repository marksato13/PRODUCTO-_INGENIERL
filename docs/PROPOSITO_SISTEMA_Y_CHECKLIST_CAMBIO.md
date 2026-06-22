# Propósito Real del Sistema y Checklist de Cambio Arquitectural
## PPI UPeU 2026 — Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos

**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha:** 2026-06-21  
**Documento:** Visión completa del sistema + plan de cambio con checklist

---

## 1. Propósito real del sistema — ¿Para qué existe?

El sistema no es solo un bloqueador de IPs. Es una plataforma de **inteligencia de red en tiempo real** que cumple tres funciones distintas e integradas:

### Función 1 — Detectar (IF + Suricata)
> Identificar automáticamente cualquier comportamiento anómalo en la red, sin conocimiento previo del tipo de ataque.

El sistema debe ser capaz de detectar:
- SYN Flood (inundación de paquetes TCP)
- Port Scan (reconocimiento de puertos)
- UDP/ICMP Flood
- Brute Force SSH (intentos repetidos de autenticación)
- HTTP Abuse (abuso de requests al servidor web)
- Acceso repetitivo anómalo
- Ataques mixtos (normal + anómalo simultáneo)
- Ataques no vistos antes (zero-day por diseño one-class)

### Función 2 — Predecir (XGBoost)
> Emitir una alerta ANTES de que el ataque alcance el umbral de bloqueo, dando tiempo de reacción al operador.

El predictor debe:
- Leer señales tempranas del comportamiento del tráfico
- Calcular P(ataque inminente) cada pocos segundos
- Emitir ALERTA-PREDICTIVA cuando P ≥ 70%
- Hacerlo ANTES de que el motor IF ejecute el BLOCK

### Función 3 — Actuar (ipset/iptables)
> Bloquear o limitar automáticamente el tráfico anómalo sin intervención humana.

El sistema debe:
- BLOCK: DROP total de la IP atacante en el servidor
- LIMIT: rate-limit (100 pkt/s) para tráfico sospechoso
- Whitelist: garantizar que IPs legítimas nunca sean bloqueadas
- Actuar en tiempo real (< 500ms desde detección hasta enforcement)

---

## 2. Lo que el sistema debe permitir hacer — visión completa

### 2.1 Sin intervención humana

```
Red bajo ataque
      │
      ▼
Sistema detecta en T≈5s
      │
      ▼
Sistema predice en T≈2s (ANTES que el bloqueo)
      │
      ▼
Sistema bloquea en T≈5s
      │
      ▼
Operador ve todo en dashboard en tiempo real
      │
      ▼
Operador recibe Telegram con alerta
```

El operador NO necesita intervenir para que el ataque sea bloqueado. El sistema actúa solo.

### 2.2 Lo que el operador SÍ puede hacer (control manual)

- Ver el estado del sistema en `http://192.168.0.110:8080`
- Ver P(ataque) en tiempo real como gauge de probabilidad
- Ver historial de IPs bloqueadas y limitadas
- Desbloquear manualmente una IP: `bash enforce.sh <IP> UNBLOCK`
- Limitar manualmente una IP: `bash enforce.sh <IP> LIMIT`
- Ver el log en vivo: `tail -f results/motor_decision.log`

### 2.3 Lo que el sistema debe garantizar siempre

| Garantía | Valor comprometido | Cómo se logra |
|---|---|---|
| Disponibilidad del servicio protegido | 100% | ipset DROP solo a atacantes, whitelist a IPs legítimas |
| Latencia de detección | < 500ms por flujo | IF con P95=34.8ms |
| Cero bloqueos a tráfico legítimo (ITL=0%) | 0% | Whitelist estricta |
| Detección de ataques conocidos | ≥ 99% | Recall=99.40% en validación F6 |
| Predicción antes del BLOCK | T_alerta < T_block | Nueva arquitectura v2 |
| Disponibilidad del propio sistema | 100% | 3 servicios restart=always |

---

## 3. El flujo correcto de todos los componentes — orden lógico definitivo

```
╔══════════════════════════════════════════════════════════════════════╗
║              FLUJO COMPLETO DEL SISTEMA (orden correcto)            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  CAPA 0 — CAPTURA (Suricata)                                        ║
║  ┌──────────────────────────────────────────────────────────┐       ║
║  │ Red → ens35 → Suricata 7.0.3 → eve.json                 │       ║
║  │ Genera flujos con 14 features por evento                 │       ║
║  └──────────────────────┬───────────────────────────────────┘       ║
║                         │ tail en tiempo real                        ║
║                         ▼                                            ║
║  CAPA 1 — DETECCIÓN (Isolation Forest)                              ║
║  ┌──────────────────────────────────────────────────────────┐       ║
║  │ motor_decision.py evalúa cada flujo (~35ms)              │       ║
║  │                                                          │       ║
║  │ Whitelist → PERMIT inmediato                             │       ║
║  │ Heurístico BF/HTTP → LIMIT o BLOCK                       │       ║
║  │ IF score > τ1=-0.4459      → PERMIT                      │       ║
║  │ IF τ2 < score ≤ τ1         → LIMIT  ──► señal precursora │       ║
║  │ IF score ≤ τ2=-0.6027      → BLOCK                       │       ║
║  │                                                          │       ║
║  │ Escribe en motor_decision.log:                           │       ║
║  │   WARNING │ SOSPECHOSO │ src=IP │ score │ LIMIT          │       ║
║  │   WARNING │ ANOMALÍA   │ src=IP │ score │ BLOCK          │       ║
║  └────────┬─────────────────────────┬────────────────────────┘       ║
║           │                         │                                ║
║           │ motor_decision.log      │ SSH enforcement                ║
║           │                         ▼                                ║
║           │              CAPA 2 — ACCIÓN (ipset)                    ║
║           │              ┌─────────────────────────────┐            ║
║           │              │ Servidor 192.168.0.120       │            ║
║           │              │ ipset ppi_blocked → DROP     │            ║
║           │              │ ipset ppi_limited → hashlimit│            ║
║           │              └─────────────────────────────┘            ║
║           │                                                          ║
║           ▼                                                          ║
║  CAPA 3 — PREDICCIÓN (XGBoost) ◄── DEBE OCURRIR ANTES QUE CAPA 2  ║
║  ┌──────────────────────────────────────────────────────────┐       ║
║  │ predictor.py lee motor_decision.log cada 2s              │       ║
║  │                                                          │       ║
║  │ Cuenta eventos LIMIT de misma IP en ventana 15s          │       ║
║  │ Features: limit_count, score_min, score_mean, hora       │       ║
║  │ XGBoost → P(BLOCK inminente)                             │       ║
║  │                                                          │       ║
║  │ P ≥ 0.70 → ALERTA-PREDICTIVA  (antes del BLOCK)         │       ║
║  │ P ≥ 0.40 → RIESGO-MEDIO                                  │       ║
║  │ P < 0.40 → OK                                            │       ║
║  │                                                          │       ║
║  │ Escribe en predictor.log                                 │       ║
║  └──────────────────────────┬───────────────────────────────┘       ║
║                             │                                        ║
║                             ▼                                        ║
║  CAPA 4 — VISIBILIDAD (Dashboard + Telegram)                        ║
║  ┌──────────────────────────────────────────────────────────┐       ║
║  │ dashboard_web.py (Flask + SSE) → :8080                   │       ║
║  │                                                          │       ║
║  │ Panel predictor: gauge P(ataque) en tiempo real          │       ║
║  │ Panel eventos:   feed ALERTA → ANOMALÍA → BLOCK          │       ║
║  │ Panel bloqueados: tabla IPs activas en ipset             │       ║
║  │                                                          │       ║
║  │ Telegram relay → notificación móvil al operador          │       ║
║  └──────────────────────────────────────────────────────────┘       ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Línea de tiempo ideal (SYN Flood)

```
T=0s    Kali inicia hping3 --flood → 192.168.0.120:80

T=1s    [CAPA 0] Suricata captura primeros flujos → eve.json
        [CAPA 1] Motor IF: score=-0.48, entre τ2 y τ1
                 → SOSPECHOSO | LIMIT (primer precursor)

T=2s    [CAPA 3] ★ PREDICTOR: lee log, cuenta 2 eventos LIMIT de Kali
                 XGBoost: P(BLOCK)=0.87
                 → ALERTA-PREDICTIVA emitida ← ANTES DEL BLOQUEO
        [CAPA 4] Dashboard: gauge sube a 87%, color rojo
                 Telegram: "⚠️ ALERTA: posible ataque detectado"

T=5s    [CAPA 1] Motor IF: score=-0.74 ≤ τ2=-0.6027
                 → ANOMALÍA | BLOCK confirmado
        [CAPA 2] SSH → ipset add ppi_blocked 192.168.0.100
                 → DROP activo en servidor
        [CAPA 4] Dashboard: tabla bloqueados actualizada

RESULTADO:
  Predictor anticipó el BLOCK por ~3 segundos
  Operador fue notificado antes de que el ataque fuera bloqueado
  Servidor protegido sin intervención humana
  Disponibilidad: 100%
```

---

## 4. Diagnóstico del estado actual vs estado objetivo

### Estado actual (arquitectura v1 — PROBLEMA)

| Componente | Estado | Problema |
|---|---|---|
| Suricata | ✅ Correcto | Ninguno |
| IF (motor_decision.py) | ✅ Correcto | Ninguno |
| ipset enforcement | ✅ Correcto | Ninguno |
| XGBoost predictor | ❌ Orden invertido | Señal demasiado lenta — llega 78s DESPUÉS del BLOCK |
| Dashboard | ✅ Funciona | No muestra alerta predictiva antes del bloqueo |
| Telegram | ✅ Funciona | Alerta llega tarde (después del BLOCK) |

**Causa raíz:** el predictor usa gaps entre STATS (cada 500 flujos), que aparecen 34s mínimo después del inicio del ataque. El IF actúa en T≈5s sobre el flujo #1.

### Estado objetivo (arquitectura v2 — CORRECTO)

| Componente | Estado objetivo | Cambio necesario |
|---|---|---|
| Suricata | ✅ Sin cambio | Ninguno |
| IF (motor_decision.py) | ✅ Sin cambio | Ninguno |
| ipset enforcement | ✅ Sin cambio | Ninguno |
| XGBoost predictor | ✅ Anticipa ~3s al BLOCK | Nueva señal + nuevo modelo + ciclo 2s |
| Dashboard | ✅ Muestra alerta antes de BLOCK | Sin cambio de código (ya lee predictor.log) |
| Telegram | ✅ Alerta llega antes | Sin cambio (depende de predictor.log) |

---

## 5. Evidencia de las corridas de validación (2026-06-21)

Las corridas ejecutadas con la arquitectura v1 confirmaron el problema:

| Corrida | Tipo | T_BLOCK (IF) | T_ALERTA (predictor) | Lead time | Causa |
|---|---|---|---|---|---|
| P1 | Ataque | T+11s | T+89s | **−78s** | Motor fresco, predictor construye historial lento |
| P2 | Ataque | N/A* | T+5s | N/A* | Predictor usó contexto residual de P1 (ataque previo en log) |
| P3 | Ataque | N/A* | T+5s | N/A* | Idem P2. Luego se vuelve inactivo (gap>600s) |
| P4 | Ataque | N/A* | Sin alerta | — | Predictor inactivo todo el tiempo (gap acumulado >800s) |

> *IP ya en `_bloqueados` del motor — no registra nuevo BLOCK en log.

**Conclusión de las corridas:** la señal de gap/500 flujos no es confiable entre corridas. En P2 y P3 alertó por contexto residual (falsa causalidad), en P4 no alertó en absoluto.

---

## 6. Nueva señal del predictor — por qué LIMIT es el precursor correcto

### Fundamento matemático

Los umbrales del IF crean tres zonas en el espacio de scores:

```
─────────────────────────────────────────────────────────────►  score IF
           BLOCK          │    LIMIT     │      PERMIT
    score ≤ τ2=-0.6027   │  τ2 < s ≤ τ1 │   score > τ1=-0.4459
                          │              │
                    τ2=-0.6027      τ1=-0.4459
```

Durante un SYN flood, el score de los flujos de Kali evoluciona así:

```
T=0s  Primeros flujos: score ≈ -0.45 a -0.52  → zona LIMIT
T=2s  Flujos más anómalos: score ≈ -0.55 a -0.65 → zona LIMIT profunda
T=5s  Flujos plenos del flood: score ≈ -0.74   → zona BLOCK
```

El score BAJA gradualmente hasta cruzar τ2. La zona LIMIT es el **corredor de transición obligatorio** hacia el BLOCK. Detectar la acumulación de eventos LIMIT de una misma IP = detectar que esa IP está bajando hacia el BLOCK.

### Por qué XGBoost y no una regla simple

Una regla heurística ("si limit_count ≥ 3 → ALERTA") funcionaría para SYN flood pero fallaría para:
- Ataques lentos (pocos LIMITs pero sostenidos)
- Hora de noche (patron de tráfico diferente)
- Múltiples IPs coordinadas (ninguna supera 3 LIMITs sola)

XGBoost aprende la **combinación** de features que predice BLOCK con mayor precisión. Además produce P(·) continuo que alimenta el gauge del dashboard, y permite explicabilidad via SHAP.

---

## 7. CHECKLIST COMPLETO — Cambio arquitectural v1 → v2

### FASE A — Preparación y datos

- [ ] **A1** Detener corridas actuales (script `correr_corridas_predictor_v2.sh` en background)
- [ ] **A2** Verificar que `motor_decision.log` tiene eventos LIMIT y BLOCK históricos suficientes
  ```bash
  ssh m4rk@192.168.0.110 "grep -c 'SOSPECHOSO\|ANOMALÍA' /home/m4rk/ppi-surikata-producto/results/motor_decision.log"
  # Necesitamos ≥ 500 eventos para entrenar
  ```
- [ ] **A3** Exportar los logs históricos de F6 que tengan ataques (fuente de datos de entrenamiento)
  ```bash
  # Los logs de F6 están en data/raw/ como .eve.json.gz
  # Reprocesar con motor para generar eventos LIMIT/BLOCK etiquetados
  ```
- [ ] **A4** Definir la ventana de predicción: "BLOCK dentro de los próximos N segundos"
  - Propuesta: N=10s (ventana corta, señal clara)

### FASE B — Nuevo script de entrenamiento

- [ ] **B1** Crear `scripts/entrenar_predictor_v2.py`
  - Parsear `motor_decision.log` para extraer eventos LIMIT/BLOCK con timestamps
  - Construir dataset: para cada evento LIMIT, verificar si hay BLOCK de misma IP en los siguientes 10s
  - Label=1 si hay BLOCK en T+10s, Label=0 si no
  - Features: `limit_count_15s`, `limit_rate_15s`, `score_min_15s`, `score_mean_15s`, `hora_sin`, `hora_cos`

- [ ] **B2** Entrenar modelo XGBoost con validación cruzada
  - Split cronológico (no aleatorio) — mantener buena práctica de F3
  - Reportar AUC-ROC, Precision, Recall en conjunto de test

- [ ] **B3** Guardar artefactos
  - `models/predictor_modelo_v2.pkl`
  - `models/features_predictor_v2.txt`
  - `results/metricas_predictor_v2.txt`

### FASE C — Reescribir predictor.py

- [ ] **C1** Cambiar señal de entrada: de gap/STATS a conteo LIMIT/ventana
  ```python
  # ANTES: parsear líneas "Estadísticas" → gap temporal
  # DESPUÉS: parsear líneas "SOSPECHOSO" → limit_count por IP en 15s
  ```

- [ ] **C2** Cambiar ciclo de ejecución
  ```python
  # ANTES: INTERVALO = 10
  # DESPUÉS: INTERVALO = 2
  ```

- [ ] **C3** Nueva función `construir_features_v2(lineas, ventana_seg=15)`
  - Extraer eventos LIMIT del log en los últimos `ventana_seg` segundos
  - Calcular: count, rate, score_min, score_mean
  - Incluir hora_sin, hora_cos

- [ ] **C4** Actualizar referencia al modelo
  ```python
  # ANTES: MODEL = BASE / 'models' / 'predictor_modelo.pkl'
  # DESPUÉS: MODEL = BASE / 'models' / 'predictor_modelo_v2.pkl'
  ```

- [ ] **C5** Actualizar docstring y comentarios para reflejar nueva arquitectura

- [ ] **C6** Mantener lógica de alerta sin cambios (THETA_ALTA=0.70, dedup, Telegram)

### FASE D — Validación

- [ ] **D1** Reiniciar servicio `ppi-predictor` con nuevo código
  ```bash
  sudo systemctl restart ppi-predictor
  ```

- [ ] **D2** Verificar que el predictor arranca sin errores
  ```bash
  tail -5 results/predictor.log
  # Debe mostrar: "Modelo v2 cargado | features=6 | θ_alta=0.7"
  ```

- [ ] **D3** Correr corrida de ataque manual (SYN flood desde Kali, 3 min)
  - Registrar T_inicio exacto
  - Anotar T_alerta (primer ALERTA-PREDICTIVA en predictor.log)
  - Anotar T_block (primer BLOCK en motor_decision.log)
  - Verificar: T_alerta < T_block (predictor anticipa)

- [ ] **D4** Correr 10 corridas de validación v3 (5 ataque + 5 normal)
  - Esperado: P1-P5 con T_alerta 2-4s antes de T_block
  - Esperado: P6-P10 sin ALERTA-PREDICTIVA falsa

- [ ] **D5** Documentar resultados en `results/corridas_predictor_v3.txt`

- [ ] **D6** Calcular métricas finales del predictor v2
  - TPR (corridas de ataque con alerta correcta)
  - FPR (corridas normales con falsa alerta)
  - Lead time promedio (T_block - T_alerta en segundos)

### FASE E — Documentación y cierre

- [ ] **E1** Actualizar `docs/FIX_GLOBAL_ARQUITECTURA.md` con resultados reales de corridas v3

- [ ] **E2** Actualizar `METODOLOGIA_FASES_PPI.md` — sección F7 con nueva arquitectura

- [ ] **E3** Actualizar sección §12 del informe PDF con:
  - Nueva señal (LIMIT como precursor)
  - Nuevas features del modelo
  - Nuevas métricas (lead time real medido)
  - Diagrama de flujo corregido

- [ ] **E4** Actualizar `results/metricas_predictor_v2.txt` con métricas finales

- [ ] **E5** Commit y push a GitHub
  ```
  feat(predictor-v2): nueva arquitectura LIMIT→ALERTA→BLOCK
  - Nueva señal: conteo eventos LIMIT en ventana 15s
  - Ciclo: 2s (antes 10s)
  - Lead time: T_alerta ≈ 2-3s antes de T_block
  - Orden correcto: PREDICCIÓN → DETECCIÓN → ACCIÓN
  ```

- [ ] **E6** Actualizar slides de defensa con el flujo corregido

### FASE F — Verificación final del sistema completo

- [ ] **F1** Los 3 servicios activos y en venv correcto
  ```bash
  systemctl is-active ppi-motor ppi-predictor ppi-dashboard
  ps aux | grep -E 'motor_decision|predictor|dashboard' | grep venv
  ```

- [ ] **F2** El orden de eventos en un ataque real es correcto:
  ```
  ALERTA-PREDICTIVA (predictor.log) ANTES que BLOCK (motor_decision.log)
  ```

- [ ] **F3** Dashboard muestra el gauge subir ANTES de que aparezca el BLOCK en la tabla

- [ ] **F4** Telegram llega ANTES de que el BLOCK sea ejecutado

- [ ] **F5** Corrida de demostración grabada para la defensa (pantallazos o video)

- [ ] **F6** Tráfico legítimo (Desktop → servidor) no interrumpido durante ataque

---

## 8. Resumen de archivos que cambian vs los que no cambian

### Sin cambios (no tocar)
```
scripts/motor_decision.py        ← ya funciona perfecto
scripts/enforce.sh               ← ya funciona perfecto
scripts/dashboard_web.py         ← ya lee predictor.log, no requiere cambios
config/telegram.conf             ← credenciales ya externalizadas
models/isolation_forest.pkl      ← modelo IF no cambia
models/scaler.pkl                ← scaler no cambia
```

### Archivos nuevos (crear)
```
scripts/entrenar_predictor_v2.py ← nuevo script de entrenamiento
models/predictor_modelo_v2.pkl   ← modelo XGBoost reentrenado
models/features_predictor_v2.txt ← 6 features nuevas
results/metricas_predictor_v2.txt← métricas del nuevo modelo
results/corridas_predictor_v3.txt← resultados de validación con v2
```

### Archivos que se modifican
```
scripts/predictor.py             ← nueva señal + ciclo 2s + nuevas features
docs/FIX_GLOBAL_ARQUITECTURA.md  ← actualizar con resultados reales
```

---

## 9. Justificación académica del cambio — argumentos para la defensa

### ¿Por qué cambiar si el sistema ya detecta y bloquea ataques?

**Argumento:** La detección y el bloqueo ya funcionan (IF + ipset). El cambio al predictor no modifica esas capas — mejora la capa de **inteligencia anticipatoria** que es el aporte original del PPI.

Un sistema que solo detecta y bloquea es un **IPS reactivo** (tecnología de los años 2000).  
Un sistema que predice antes de bloquear es un **IPS adaptativo con inteligencia temporal** — que es exactamente el título del PPI: "Detección *Temprana*".

### ¿Por qué la señal LIMIT es correcta académicamente?

La zona LIMIT (τ2 < score ≤ τ1) representa el espacio de **incertidumbre del clasificador**: el IF no está seguro de que sea un ataque, pero tampoco es normal. Monitorear la acumulación de eventos en esta zona de incertidumbre y predecir su escalada es un enfoque de **predicción de umbral** (threshold crossing prediction), reconocido en la literatura de sistemas de detección de intrusiones (Lippmann et al., 2000; Sommer & Paxson, 2010).

### ¿Qué aporta XGBoost sobre una regla heurística?

| Aspecto | Regla heurística | XGBoost |
|---|---|---|
| "si limit_count ≥ 3 → ALERTA" | ✅ Simple | ❌ No aprende |
| Interacción entre features | ❌ No captura | ✅ Árboles capturan |
| Robustez a variaciones de hora | ❌ No | ✅ hora_sin/cos |
| Probabilidad continua P(·) | ❌ Binario | ✅ Para gauge |
| Explicabilidad SHAP | ❌ No | ✅ Importancia features |
| Sustenta objetivo PPI (ML) | ❌ No es ML | ✅ Es ML supervisado |

El PPI tiene como objetivo demostrar el uso de **aprendizaje automático** para detección temprana. Una regla heurística no cumple ese objetivo. XGBoost sí.
