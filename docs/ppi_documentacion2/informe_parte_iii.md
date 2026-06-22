# Informe de Resultados — Parte III: Metodología
**PPI — Detección Temprana de Comportamientos Anómalos en Redes de Datos**  
Universidad Peruana Unión · Ingeniería de Sistemas · 2026

---

## 3. Metodología

El sistema se construyó siguiendo un pipeline en seis fases encadenadas (F1–F6), donde la salida de cada fase es la entrada de la siguiente. Las fases F1–F3 cubren la obtención de datos y el entrenamiento del modelo; F4–F5 implementan el motor de decisión en producción y su capacidad de aprendizaje continuo; F6 valida el sistema completo bajo condiciones reproducibles. Esta sección describe el diseño e implementación de cada fase.

---

### 3.1 Entorno de laboratorio

El experimento se realizó en una red de laboratorio local (192.168.0.0/24) compuesta por cuatro máquinas virtuales con roles diferenciados. La tabla 3.1 describe la topología.

**Tabla 3.1 — Topología del laboratorio**

| Nodo | IP | SO | Rol |
|---|---|---|---|
| Desktop | 192.168.0.20 | Ubuntu Desktop | Origen de tráfico normal; host del operador |
| Kali | 192.168.0.100 | Kali Linux | Origen de tráfico anómalo (atacante simulado) |
| Sensor | 192.168.0.110 | Ubuntu Server | Suricata 7.0.3 + motor de decisión |
| Servidor | 192.168.0.120 | Ubuntu Server | Objetivo protegido: nginx (:80) y SSH (:22) |

El sensor monitorea el tráfico en la interfaz `ens35` en modo promiscuo. El servidor es el activo protegido y aloja también las listas de control de acceso (ipset). El usuario único de administración fue `m4rk`, con autenticación por clave SSH entre el Desktop, el sensor y el servidor.

Las herramientas de software utilizadas fueron: Suricata 7.0.3 (captura), Python 3.11 con scikit-learn 1.9.0 y XGBoost (modelos), Flask (dashboard web), ipset e iptables (control inline) e integración con la API de Telegram (alertas).

---

### 3.2 F1 — Captura de tráfico de red

#### 3.2.1 Configuración de Suricata

Suricata se configuró en el sensor para capturar en modo pasivo (sin bloqueo) sobre la interfaz `ens35`. Toda la actividad de la red es registrada en el archivo `eve.json` en formato JSON estructurado. Cada evento de tipo `flow` contiene los metadatos de un flujo de red completo: IPs origen/destino, puertos, protocolo, contadores de paquetes y bytes en ambas direcciones, marcas de tiempo de inicio y fin, y estado de cierre del flujo.

#### 3.2.2 Escenarios de captura

Se diseñaron nueve escenarios agrupados en tres categorías según la naturaleza del tráfico generado:

**Grupo A — Tráfico normal** (origen: Desktop 192.168.0.20):
- A1 *http_normal*: solicitudes HTTP al servidor con curl y wget durante 10 minutos
- A2 *ssh_legitimo*: sesiones SSH interactivas durante 8 minutos
- A3 *transferencia_legitima*: transferencias de archivos con SCP y wget durante 10 minutos
- A4 *trafico_sostenido*: combinación continua de HTTP y SSH durante 15 minutos

**Grupo B — Tráfico anómalo** (origen: Kali 192.168.0.100):
- B1 *syn_flood*: inundación de paquetes SYN con hping3 hacia el puerto 80
- B2 *port_scan*: escaneo de puertos con nmap en modo SYN stealth
- B3 *udp_flood*: inundación UDP hacia el puerto 53
- B4 *icmp_flood*: inundación ICMP hacia el servidor
- B5 *acceso_repetitivo*: solicitudes HTTP en bucle desde curl (HTTP Abuse)
- B6 *bruteforce_ssh*: ataque de diccionario SSH con Hydra

**Grupo C — Tráfico mixto** (Desktop + Kali simultáneos):
- C1 *http_syn*: tráfico HTTP normal simultáneo con SYN flood
- C2 *ssh_portscan*: sesión SSH legítima simultánea con escaneo de puertos
- C3 *descarga_udp*: descarga de archivo simultánea con UDP flood

Al finalizar cada corrida, el script `exportar_eve_por_escenario.sh` comprime el `eve.json` activo en un archivo `.gz` con nomenclatura `YYYYMMDD_grupo_escenario_NN_eve.json.gz` y ordena a Suricata rotar el log mediante el comando `suricatasc reopen-log-files`. Se realizaron 47 capturas en total y se registró cada corrida en una bitácora (`bitacora_escenarios.txt`).

---

### 3.3 F2 — Procesamiento del dataset y entrenamiento del modelo

#### 3.3.1 Extracción de características

El script `fase3_entrenar.py` lee los archivos `.gz` del Grupo A (tráfico normal) y extrae, por cada evento de flujo `eve.json`, catorce características numéricas derivadas de los metadatos del flujo. Estas características representan el comportamiento del flujo desde dos perspectivas: volumen (paquetes, bytes, duración) y ratios de comunicación (proporción servidor/cliente, tasa de paquetes, tamaño promedio). La tabla 3.2 detalla las catorce características.

**Tabla 3.2 — Características del modelo Isolation Forest**

| Feature | Descripción | Tipo |
|---|---|---|
| `pkts_toserver` | Paquetes hacia el servidor | Numérico |
| `pkts_toclient` | Paquetes desde el servidor | Numérico |
| `bytes_toserver` | Bytes hacia el servidor | Numérico |
| `bytes_toclient` | Bytes desde el servidor | Numérico |
| `duration` | Duración del flujo (segundos) | Numérico |
| `pkt_rate` | Tasa total de paquetes (pkt/s) | Numérico |
| `byte_rate` | Tasa total de bytes (bytes/s) | Numérico |
| `pkt_ratio` | pkts_toserver / pkts_toclient | Numérico |
| `byte_ratio` | bytes_toserver / bytes_toclient | Numérico |
| `avg_pkt_size` | Tamaño promedio de paquete (bytes) | Numérico |
| `is_tcp` | Indicador de protocolo TCP | Binario |
| `is_udp` | Indicador de protocolo UDP | Binario |
| `is_icmp` | Indicador de protocolo ICMP | Binario |
| `dest_port` | Puerto de destino | Numérico |

Previo al entrenamiento, las características numéricas continuas se estandarizaron con `StandardScaler` (media cero, desviación estándar unitaria) ajustado exclusivamente sobre los datos de entrenamiento, para evitar filtración de información del conjunto de validación. El scaler serializado (`scaler.pkl`) se utiliza en producción para transformar cada flujo antes de la inferencia.

#### 3.3.2 División del dataset

Los 67,135 flujos normales se dividieron con `shuffle=True` (random_state=42): 80% para entrenamiento (53,708 flujos) y 20% de holdout (13,427 flujos) reservado para la evaluación del modelo. Para el Isolation Forest se optó por división aleatoria en lugar de cronológica porque el modelo aprende la distribución estadística del tráfico normal, no secuencias temporales; la distribución aleatoria garantiza representatividad de todos los patrones del Grupo A en el conjunto de entrenamiento.

#### 3.3.3 Entrenamiento del Isolation Forest

Se entrenó un modelo Isolation Forest con `n_estimators=300` árboles de aislamiento y `contamination=0.05`. El parámetro `contamination` es un prior sobre la proporción de anomalías esperada en los datos de producción; con 0.05 se asume que aproximadamente un 5% del tráfico visto en producción podría ser anómalo, lo cual es conservador y apropiado para un entorno corporativo.

El Isolation Forest asigna a cada flujo un score de anomalía en el rango [-1, 0] mediante la función `decision_function`: los flujos normales concentran sus scores cerca de 0, mientras que los flujos anómalos obtienen scores más negativos. El modelo trabaja en modo no supervisado, es decir, aprende exclusivamente del comportamiento normal sin requerir ejemplos etiquetados de ataques.

#### 3.3.4 Derivación de umbrales de decisión

Los umbrales de decisión τ1 y τ2 se derivaron de la curva AUC-ROC construida sobre el conjunto de evaluación (holdout normal + flujos anómalos del Grupo B). Se utilizaron dos criterios distintos:

- **τ1** se calculó mediante el índice de Youden (max(TPR − FPR)), que maximiza la suma de sensibilidad y especificidad. Este umbral separa la zona PERMIT de la zona LIMIT y prioriza capturar la mayor cantidad posible de ataques (alto recall).
- **τ2** se fijó en el punto de la curva donde FPR ≤ 2%, garantizando que los flujos enviados a BLOCK (DROP total) correspondan a anomalías con muy alta confianza. El tradeoff es un TPR bajo en τ2 (18.27%), lo cual se compensa con los detectores heurísticos descritos en la sección 3.4.

Los valores resultantes (τ1 = −0.4459, τ2 = −0.6027) se almacenan en `results/metricas_offline.txt` y son leídos por el motor de decisión cada vez que inicia, sin requerir modificación de código.

---

### 3.4 F3 — Motor de decisión y control inline

#### 3.4.1 Arquitectura del motor

El script `motor_decision.py` implementa el loop principal del sistema. Sigue el archivo `eve.json` en tiempo real mediante un mecanismo equivalente a `tail -f`, procesando cada nuevo evento de flujo sin latencia de polling. El flujo de procesamiento por evento es el siguiente:

1. Leer el evento JSON y verificar que sea de tipo `flow`
2. Verificar que la IP de origen no esté en la whitelist de confianza
3. Extraer las 14 características del evento
4. Transformar con `StandardScaler` y calcular el score con el Isolation Forest
5. Aplicar la lógica de decisión de tres niveles
6. Ejecutar la acción de control correspondiente
7. Registrar la decisión en el log y, si corresponde, enviar alerta

#### 3.4.2 Lógica de decisión en tres niveles

La decisión para cada flujo sigue la siguiente lógica:

```
Si score(flujo) > τ1  (−0.4459):   PERMIT  — flujo normal, sin acción
Si τ2 < score ≤ τ1:                LIMIT   — flujo sospechoso, rate limiting
Si score ≤ τ2  (−0.6027):          BLOCK   — flujo anómalo, descarte total
```

Complementariamente, dos detectores heurísticos actúan sobre contadores de eventos por IP, independientemente del score IF:

- **BF-SSH**: si una IP genera 5 o más intentos de autenticación SSH en 60 segundos, se aplica LIMIT; con 15 o más, BLOCK. Este detector actúa antes de que Suricata cierre los flujos, reduciendo el lead time para ataques de fuerza bruta.
- **HTTP Abuse**: si una IP genera 50 o más solicitudes HTTP en 30 segundos, LIMIT; con 100 o más, BLOCK.

Los detectores heurísticos permiten actuar sobre flujos individuales en ventanas cortas, complementando al IF que opera sobre flujos completos (cerrados).

#### 3.4.3 Bloqueo progresivo

El motor mantiene un historial de bloqueos por IP en `results/block_counts.json`, que persiste entre reinicios del servicio. El timeout de bloqueo en ipset varía según la reincidencia:

- 1.er bloqueo: 300 segundos (5 minutos)
- 2.º bloqueo: 1,800 segundos (30 minutos)
- 3.er bloqueo en adelante: permanente (timeout=0 en ipset)

Este mecanismo permite una respuesta proporcionada: la primera detección puede deberse a un escaneo exploratorio puntual, mientras que la reincidencia indica una campaña sostenida que justifica un bloqueo más severo.

#### 3.4.4 Control inline con ipset e iptables

La acción de bloqueo se ejecuta en el servidor (192.168.0.120) mediante dos listas ipset gestionadas por iptables en el kernel:

- `ppi_blocked`: las IPs incluidas en esta lista tienen sus paquetes descartados por la regla `iptables DROP`. El descarte ocurre en el kernel antes de que el paquete llegue a la aplicación, sin latencia adicional de software.
- `ppi_limited`: las IPs en esta lista tienen el tráfico limitado a 100 paquetes por segundo mediante la extensión `hashlimit` de iptables.

El motor ejecuta los comandos de ipset sobre el servidor vía SSH (`sudo ipset add ppi_blocked <IP> timeout <T>`). La whitelist (`config/whitelist.conf`) define IPs que nunca son procesadas por el motor, garantizando que los hosts de confianza no puedan ser bloqueados.

#### 3.4.5 Dashboard web y notificaciones

El sistema cuenta con dos mecanismos de visibilidad en tiempo real:

- **Dashboard web** (`dashboard_web.py`): servidor Flask disponible en el puerto 8080 del sensor. Usa *Server-Sent Events* (SSE) para empujar cada nueva detección al navegador del operador sin necesidad de polling. Presenta estadísticas de flujos, alertas activas con IP origen y score, IPs en ipset, métricas del modelo y las predicciones del XGBoost.

- **Alertas Telegram**: cuando el motor ejecuta un BLOCK nuevo (no visto en los últimos 300 s para esa IP), encola de forma asíncrona un mensaje a la API de Telegram con los datos del evento: IP, puerto, tipo de ataque, score y timestamp. La cola es no bloqueante, de manera que un fallo de red o de la API no detiene el loop principal del motor.

Ambos mecanismos son simultáneos: la alerta en el dashboard aparece ~150 ms después de la decisión del motor (tiempo del lector de log SSE), mientras que la notificación Telegram llega en ~300–800 ms adicionales según la latencia de la API.

---

### 3.5 F4 — Predictor XGBoost de persistencia

#### 3.5.1 Motivación

El Isolation Forest clasifica cada flujo de forma independiente y sin memoria temporal: no distingue entre una anomalía puntual (que puede ignorarse) y el inicio de un ataque sostenido que continuará. El predictor XGBoost cubre esta brecha analizando el patrón comportamental de cada IP atacante a lo largo del tiempo para predecir si el ataque persistirá en los próximos 60 segundos.

#### 3.5.2 Señal de entrada y etiquetado automático

El predictor (`predictor.py`) lee el archivo `results/motor_decision.log` en tiempo real, extrayendo los eventos LIMIT y BLOCK. Por cada IP activa mantiene un estado en memoria con los últimos eventos observados: cuántos LIMITs ha acumulado en los últimos 15 segundos (`limit_count_15s`) y cuántos BLOCKs en los últimos 60 segundos (`block_count_60s`), además del último score IF observado y el protocolo predominante.

El etiquetado para entrenamiento es automático: si dentro de los 60 segundos siguientes a un evento se observa otro BLOCK de la misma IP, el evento se etiqueta como `label=1` (ataque sostenido); en caso contrario, `label=0` (anomalía puntual o falso positivo). Este esquema de etiquetado no requiere intervención humana y permite reentrenamiento continuo con datos operativos reales.

#### 3.5.3 Características del modelo (9 features)

Tras la corrección del data leakage identificado durante la validación (sección 4.5.3), el modelo opera con nueve características comportamentales:

**Tabla 3.3 — Características del predictor XGBoost**

| Feature | Descripción |
|---|---|
| `dest_port` | Puerto de destino del evento |
| `proto_tcp` | Indicador protocolo TCP (binario) |
| `proto_udp` | Indicador protocolo UDP (binario) |
| `proto_icmp` | Indicador protocolo ICMP (binario) |
| `hora_sin` | Componente sin(hora × 2π/24) — codificación cíclica de hora |
| `hora_cos` | Componente cos(hora × 2π/24) — codificación cíclica de hora |
| `limit_count_15s` | Número de LIMITs de esta IP en los últimos 15 s |
| `block_count_60s` | Número de BLOCKs de esta IP en los últimos 60 s |
| `is_block` | 1 si el evento es BLOCK, 0 si es LIMIT |

La codificación cíclica de la hora (componentes seno y coseno) evita la discontinuidad que generaría usar la hora como entero (23 y 0 serían numéricamente lejanos aunque sean temporalmente consecutivos).

#### 3.5.4 Niveles de alerta

El predictor produce una probabilidad P ∈ [0, 1] de que el ataque persista. Se definieron tres zonas:

- **P < 40%**: silencio — no se registra ni notifica
- **40% ≤ P < 70%**: AVISO — registro en log y visualización en dashboard (amarillo), sin Telegram
- **P ≥ 70%**: ALERTA-PREDICTIVA — registro en log WARNING, envío a Telegram con deduplicación de 300 s por IP, visualización en dashboard (rojo)

#### 3.5.5 Hot-reload sin interrupción del servicio

El predictor comprueba en cada ciclo el tiempo de modificación (`mtime`) del archivo de modelo. Si detecta un cambio, recarga el modelo y las features en memoria sin reiniciar el proceso. Esto permite que F5 actualice el modelo de forma automática sin interrumpir el monitoreo.

---

### 3.6 F5 — Reentrenamiento automático

#### 3.6.1 Ciclos de reentrenamiento

F5 implementa dos ciclos de reentrenamiento automático programados mediante `crontab` en el sensor:

- **Isolation Forest**: cada domingo a las 02:00. El script `f5_reentrenar_if.py` lee todos los archivos `_normal_*.gz` acumulados en `data/raw/` (incluyendo nuevas capturas si las hubiera) y entrena un nuevo IF. El nuevo modelo reemplaza al anterior solo si AUC no retrocede más de 0.02 puntos respecto al modelo en producción.

- **XGBoost**: diariamente a las 03:00. El script `f5_reentrenar_xgboost.py` lee las últimas 24 horas del `motor_decision.log`, extrae los eventos LIMIT y BLOCK, genera los labels automáticos y entrena un nuevo XGBoost. El reemplazo ocurre si AUC ≥ 0.70 y no retrocede más de 0.05 puntos. Si la ventana contiene menos de 100 eventos o menos de 10 positivos, el script cancela el reentrenamiento y registra el aviso.

#### 3.6.2 Protecciones contra degradación

El diseño de F5 incluye varias salvaguardas para evitar que un reentrenamiento deficiente reemplace un modelo bueno. Además de los umbrales de AUC mencionados, se verifica que el número mínimo de ejemplos sea suficiente para un split estratificado confiable. El flag `--forzar` permite omitir estas protecciones en entornos de depuración.

La decisión de usar reentrenamiento por lotes nocturnos en lugar de *online learning* (actualización continua con cada evento) responde a una consideración de seguridad: el online learning es susceptible a ataques de envenenamiento, en los cuales un atacante genera tráfico diseñado para que el modelo aprenda a clasificarlo como normal. El reentrenamiento por lotes con validación de AUC es más robusto ante este vector de ataque.

---

### 3.7 F6 — Validación del sistema

#### 3.7.1 Diseño de la validación

La validación formal del sistema se estructuró en 40 corridas organizadas en cuatro grupos de 10, ejecutadas de forma continua el 2026-06-16 entre las 09:17 y las 13:22. Esta distribución permitió observar el comportamiento del sistema ante distintos estados acumulados del mecanismo de bloqueo progresivo:

- **Grupo normal** (corridas 1–10): tráfico exclusivamente normal desde Desktop. Sirve para verificar que el sistema no genera falsos positivos (ITL = 0%).
- **Grupo mixto** (corridas 11–20): tráfico mixto con tráfico anómalo activo desde Kali. Permite observar la primera detección y el bloqueo inicial.
- **Grupo reeval** (corridas 21–30): continúa con el bloqueo ya establecido, verificando que la IP permanece bloqueada en ipset.
- **Grupo final** (corridas 31–40): bloqueo consolidado, verifica disponibilidad sostenida.

#### 3.7.2 Métricas de validación

Para cada corrida se registraron los siguientes indicadores:

- **Disponibilidad**: el sistema procesa flujos sin interrupción durante toda la corrida (binario: 1/0)
- **ITL** (Interrupción de Tráfico Legítimo): porcentaje de flujos normales afectados por un BLOCK incorrecto. Un ITL de 0% indica que la whitelist funciona correctamente
- **Lead time**: tiempo transcurrido entre el inicio del tráfico anómalo y el primer BLOCK registrado en el log
- **Latencia**: latencia acumulada de la ventana de análisis de cada corrida (referencial; la latencia por flujo se midió de forma independiente en `latencia_pipeline.txt`)

Los criterios de aceptación de F6 (disponibilidad 100%, ITL 0%, y al menos una IP bloqueada en escenarios anómalos) se verificaron contra los 40 registros del archivo `resultados_f6_completo.csv`.
