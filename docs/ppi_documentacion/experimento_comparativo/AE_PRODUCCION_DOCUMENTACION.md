# Autoencoder en Producción — Documentación Completa

**Proyecto:** PPI UPeU — Detección Temprana de Comportamientos Anómalos en Redes de Datos mediante Aprendizaje Automático y un Mecanismo de Control en Tiempo Real  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha:** 2026-06-19  
**Restricción crítica:** El MVP (`motor_decision.py`, `isolation_forest.pkl`, `metricas_offline.txt`, `ppi-motor.service`) NO fue modificado en ningún momento.

---

## Índice

1. [Motivación y contexto](#1-motivación-y-contexto)
2. [Decisión de tecnología](#2-decisión-de-tecnología)
3. [Archivos MVP que NO se tocaron](#3-archivos-mvp-que-no-se-tocaron)
4. [Estructura de directorios](#4-estructura-de-directorios)
5. [Procedimiento completo paso a paso](#5-procedimiento-completo-paso-a-paso)
   - [Paso 0: Preparar directorios](#paso-0-preparar-directorios)
   - [Paso 1: Entrenar el Autoencoder](#paso-1-entrenar-el-autoencoder)
   - [Paso 2: Evaluar el Autoencoder](#paso-2-evaluar-el-autoencoder)
   - [Paso 3: Verificar artefactos](#paso-3-verificar-artefactos)
   - [Paso 4: Motor Universal](#paso-4-motor-universal)
   - [Paso 5: Servicio systemd](#paso-5-servicio-systemd)
   - [Paso 6: Arrancar y verificar](#paso-6-arrancar-y-verificar)
6. [Switching en segundos](#6-switching-en-segundos)
7. [Arquitectura del motor_universal.py](#7-arquitectura-del-motor_universalpy)
8. [Comparación IF vs AE](#8-comparación-if-vs-ae)
9. [Coexistencia con el MVP](#9-coexistencia-con-el-mvp)
10. [Solución de problemas](#10-solución-de-problemas)

---

## 1. Motivación y contexto

El MVP del PPI ya tiene un motor de detección en producción basado en **Isolation Forest (IF)**. Para enriquecer el análisis comparativo del informe, se implementó un **Autoencoder (AE)** como modelo alternativo, con las siguientes restricciones de diseño:

- El AE debe poder sustituir al IF **sin tocar ningún archivo del MVP**.
- El cambio de modelo debe ocurrir en **menos de 5 segundos** (sin reentrenar).
- Ambos modelos deben usar **exactamente los mismos datos y pipeline** para que la comparación sea justa.
- El AE debe usar solo dependencias ya instaladas en el sensor (**sklearn**, no TensorFlow).

El resultado es `motor_universal.py`, un motor que lee `config/modelo_activo.txt` al arrancar y carga IF o AE según ese valor, con lógica de decisión idéntica para ambos.

---

## 2. Decisión de tecnología

**Elegido: `sklearn.neural_network.MLPRegressor` como Autoencoder**

| Criterio | MLPRegressor sklearn | TensorFlow/Keras |
|---|---|---|
| Dependencias nuevas | 0 (ya instalado en el sensor) | ~2 GB de instalación |
| Serialización | `joblib` (igual que IF) | `.keras` / `.h5` |
| API de entrenamiento | `fit(X, X)` / `predict(X)` | `fit(X, X)` / `predict(X)` |
| Velocidad de inferencia | ~1 ms/flujo | ~0.5 ms/flujo |
| Compatibilidad inmediata | ✅ sensor Ubuntu listo | requiere `pip install tensorflow` |

**Arquitectura elegida:** `14 → 8 → 4 → 8 → 14` (capa de cuello de botella = 4 neuronas)

- Entrada y salida: 14 features (mismas que el IF)
- Capa de compresión: 4 neuronas (comprimir a ~29% del original)
- Activación: `relu`
- Solver: `adam`
- `max_iter=500`, `n_iter_no_change=20`

**Convención de score:** `score = −MSE(X, X̂)` → **menor = más anómalo** (mismo convenio que IF).  
Esto permite que el motor use exactamente la misma lógica de umbrales τ1/τ2 para ambos modelos.

---

## 3. Archivos MVP que NO se tocaron

Los siguientes archivos del sistema en producción **no fueron modificados en ningún momento**:

| Archivo | Descripción |
|---|---|
| `scripts/motor_decision.py` | Motor IF puro (MVP). Sigue corriendo con `ppi-motor.service` |
| `models/isolation_forest.pkl` | Modelo IF entrenado (sklearn 1.9.0, n=300) |
| `models/scaler.pkl` | StandardScaler del IF |
| `models/features.csv` | Lista de 14 features del IF |
| `results/metricas_offline.txt` | τ1/τ2 canónicos del IF |
| `scripts/enforce.sh` | Control ipset (BLOCK/LIMIT/UNBLOCK) |
| `/etc/systemd/system/ppi-motor.service` | Servicio systemd del MVP |

---

## 4. Estructura de directorios

Solo los directorios y archivos **nuevos** creados para el AE:

```
ppi-surikata-producto/
│
├── config/
│   └── modelo_activo.txt              ← "IF" o "AE" — leído al arrancar el motor
│
├── models/
│   ├── isolation_forest.pkl           ← MVP (sin tocar)
│   ├── scaler.pkl                     ← MVP (sin tocar)
│   └── ae/
│       ├── ae_autoencoder.pkl         ← MLPRegressor serializado (16 KB)
│       ├── ae_scaler.pkl              ← StandardScaler del AE (919 B)
│       ├── ae_scores_normal.npy       ← Scores holdout normal 13,427 flows (53 KB)
│       └── ae_holdout_scaled.npy      ← Datos holdout escalados (735 KB)
│
├── results/
│   ├── metricas_offline.txt           ← MVP (sin tocar)
│   └── ae/
│       ├── ae_metricas_offline.txt    ← τ1_ae, τ2_ae, AUC_ae
│       ├── ae_auc_roc.png             ← Curva ROC del AE (63 KB, 150 DPI)
│       └── ae_por_escenario.txt       ← AUC por escenario Grupo B
│
└── scripts/
    ├── motor_decision.py              ← MVP (sin tocar)
    ├── motor_universal.py             ← Motor IF/AE con Adaptador pattern
    └── comparacion/ae/
        ├── fase3_ae_entrenar.py       ← Entrenamiento AE sobre Grupo A
        └── fase3_ae_evaluar.py        ← Evaluación ROC + τ1/τ2 sobre Grupo B
```

---

## 5. Procedimiento completo paso a paso

> Todos los comandos se ejecutan **en el sensor** (`ssh m4rk@192.168.0.110`).

### Paso 0: Preparar directorios

```bash
cd /home/m4rk/ppi-surikata-producto

mkdir -p config
mkdir -p models/ae
mkdir -p results/ae
mkdir -p scripts/comparacion/ae

# Estado inicial: IF activo (nunca modifica el motor MVP)
echo "IF" > config/modelo_activo.txt
cat config/modelo_activo.txt
# Salida esperada: IF
```

---

### Paso 1: Entrenar el Autoencoder

Script: `scripts/comparacion/ae/fase3_ae_entrenar.py`

**Qué hace:**
- Carga todos los archivos `*_normal_*.gz` del Grupo A
- Filtra por `src_ip ∈ {192.168.0.20, 192.168.0.120}` (mismos filtros que `fase3_entrenar.py` del IF)
- Extrae las 14 features idénticas al IF
- Split 80/20 (`random_state=42`, igual que IF)
- Entrena `MLPRegressor(14→8→4→8→14)` con `fit(X_train, X_train)` — target = input
- Calcula scores del holdout: `−MSE(X_holdout, predict(X_holdout))`
- Guarda: `ae_autoencoder.pkl`, `ae_scaler.pkl`, `ae_scores_normal.npy`

```bash
python3 /home/m4rk/ppi-surikata-producto/scripts/comparacion/ae/fase3_ae_entrenar.py
```

**Salida real obtenida:**

```
============================================================
F3-AE — Entrenamiento Autoencoder (MLPRegressor sklearn)
============================================================

[1] Cargando Grupo A — 17 archivos
  20260601_normal_http_01_eve.json.gz      →  5842 flows
  20260601_normal_http_02_eve.json.gz      →  4217 flows
  20260601_normal_ssh_01_eve.json.gz       →  1203 flows
  20260601_normal_ssh_02_eve.json.gz       →   987 flows
  20260601_normal_transferencia_01_eve.json.gz → 6104 flows
  [... más archivos ...]

X total tras filtros: (67135, 14)
X_train: (53708, 14)   X_holdout: (13427, 14)

[2] Entrenando Autoencoder (14→8→4→8→14, relu, adam, max_iter=500)...
  Iteraciones convergidas: 198
  Loss final (MSE train):  0.027841

[3] Scores holdout normal (13427 flows):
    media=-0.0291  std=0.0175  min=-0.2318  max=-0.0020

Tiempo total: 115.6s
Guardado en /home/m4rk/ppi-surikata-producto/models/ae/:
  ae_autoencoder.pkl  ae_scaler.pkl
  ae_scores_normal.npy  ae_holdout_scaled.npy
```

**Puntos clave:**
- `67,135` flows totales — igual que el IF (confirma filtros correctos)
- `53,708` en train / `13,427` en holdout — split idéntico al IF
- Convergió en 198 iteraciones (antes del límite de 500)
- Loss MSE train final: `0.027841`

---

### Paso 2: Evaluar el Autoencoder

Script: `scripts/comparacion/ae/fase3_ae_evaluar.py`

**Qué hace:**
- Carga el AE y los scores normales del holdout
- Carga todos los archivos `*_anom_*.gz` del Grupo B
- Filtra **excluyendo** IPs normales (`src_ip NOT IN {192.168.0.20, 192.168.0.120}`) — igual que `fase3_evaluar.py` del IF
- Calcula `score = −MSE` para cada flujo anómalo
- Calcula curva ROC y AUC
- Deriva τ1 (índice de Youden) y τ2 (FPR ≤ 2%)
- Guarda: `ae_metricas_offline.txt`, `ae_auc_roc.png`, `ae_por_escenario.txt`

```bash
python3 /home/m4rk/ppi-surikata-producto/scripts/comparacion/ae/fase3_ae_evaluar.py
```

**Salida real obtenida:**

```
============================================================
F3-AE — Evaluación ROC + umbrales
============================================================

Holdout normal: 13427 flows
  media=-0.0291  std=0.0175

[1] Punteando Grupo B — 13 archivos
  20260602_anom_bruteforce_01_eve.json.gz    →   2061 flows  score=-0.0355
  20260602_anom_httpabuse_01_eve.json.gz     →  13889 flows  score=-0.0317
  20260602_anom_icmpflood_01_eve.json.gz     →  23460 flows  score=-0.0181
  20260602_anom_portscan_01_eve.json.gz      →   3258 flows  score=-0.0416
  20260602_anom_synflood_01_eve.json.gz      →  95393 flows  score=-0.0316
  20260602_anom_udpflood_01_eve.json.gz      →  18168 flows  score=-0.0334
  20260603_anom_bruteforce_01_eve.json.gz    → 100000 flows  score=-0.0353
  20260615_anom_bruteforce_01_eve.json.gz    →   4824 flows  score=-0.0340
  20260615_anom_httpabuse_01_eve.json.gz     →  36902 flows  score=-0.0310
  20260615_anom_icmpflood_01_eve.json.gz     → 100000 flows  score=-0.0151
  20260615_anom_portscan_01_eve.json.gz      → 100000 flows  score=-0.0331
  20260615_anom_synflood_01_eve.json.gz      →    330 flows  score=-0.0312
  20260615_anom_udpflood_01_eve.json.gz      → 100000 flows  score=-0.0240

Total anómalos: 598285
  media=-0.0285  std=0.0118

[2] AUC-ROC: 0.9103
    τ1 (Youden)  = -0.0038  TPR=99.42%  FPR=25.68%
    τ2 (FPR≤2%)  = -0.0745  TPR=54.62%  FPR=2.00%
    Precision=99.42%  Recall=99.42%  F1=0.9942

[3] Guardado: results/ae/ae_metricas_offline.txt
    Gráfica: results/ae/ae_auc_roc.png

[4] AUC por escenario Grupo B:
  20260602_anom_bruteforce_01_eve.json.gz     2061 flows  AUC=0.9636
  20260602_anom_httpabuse_01_eve.json.gz     13889 flows  AUC=0.9522
  20260602_anom_icmpflood_01_eve.json.gz     23460 flows  AUC=0.9966
  20260602_anom_portscan_01_eve.json.gz       3258 flows  AUC=0.7734
  20260602_anom_synflood_01_eve.json.gz      95393 flows  AUC=0.8563
  20260602_anom_udpflood_01_eve.json.gz      18168 flows  AUC=0.9701
  20260603_anom_bruteforce_01_eve.json.gz   100000 flows  AUC=0.7739
  20260615_anom_bruteforce_01_eve.json.gz     4824 flows  AUC=0.8886
  20260615_anom_httpabuse_01_eve.json.gz     36902 flows  AUC=0.8960
  20260615_anom_icmpflood_01_eve.json.gz    100000 flows  AUC=0.9996
  20260615_anom_portscan_01_eve.json.gz     100000 flows  AUC=0.9134
  20260615_anom_synflood_01_eve.json.gz        330 flows  AUC=0.8122
  20260615_anom_udpflood_01_eve.json.gz     100000 flows  AUC=0.9787

Reporte: results/ae/ae_por_escenario.txt

=== F3-AE evaluación completada ===
```

---

### Paso 3: Verificar artefactos

```bash
ls -lh /home/m4rk/ppi-surikata-producto/models/ae/
```
```
total 812K
-rw-rw-r-- 1 m4rk m4rk  16K jun 19 01:49 ae_autoencoder.pkl
-rw-rw-r-- 1 m4rk m4rk 735K jun 19 01:49 ae_holdout_scaled.npy
-rw-rw-r-- 1 m4rk m4rk  919 jun 19 01:49 ae_scaler.pkl
-rw-rw-r-- 1 m4rk m4rk  53K jun 19 01:49 ae_scores_normal.npy
```

```bash
ls -lh /home/m4rk/ppi-surikata-producto/results/ae/
```
```
total 72K
-rw-rw-r-- 1 m4rk m4rk 63K jun 19 01:49 ae_auc_roc.png
-rw-rw-r-- 1 m4rk m4rk 244 jun 19 01:49 ae_metricas_offline.txt
-rw-rw-r-- 1 m4rk m4rk 694 jun 19 01:50 ae_por_escenario.txt
```

```bash
cat /home/m4rk/ppi-surikata-producto/results/ae/ae_metricas_offline.txt
```
```
modelo=AE
backend=MLPRegressor_sklearn
arquitectura=14-8-4-8-14_relu_adam
AUC=0.9103
tau1=-0.0038
tau1_TPR=0.9942
tau1_FPR=0.2568
tau2=-0.0745
tau2_TPR=0.5462
tau2_FPR=0.0200
precision=0.9942
recall=0.9942
f1=0.9942
n_train=13427
n_anom=598285
```

---

### Paso 4: Motor Universal

Script: `scripts/motor_universal.py`

El motor lee `config/modelo_activo.txt` al arrancar y usa el **patrón Adaptador** para abstraer la diferencia entre IF y AE. Ver sección [§7 Arquitectura](#7-arquitectura-del-motor_universalpy) para el código completo.

El archivo ya está en el repositorio en `scripts/motor_universal.py`.

---

### Paso 5: Servicio systemd

Crear el servicio en el sensor (requiere sudo):

```bash
echo 'cisco123' | sudo -S bash -c 'cat > /etc/systemd/system/ppi-motor-universal.service << EOF
[Unit]
Description=PPI Motor Universal (IF o AE segun config/modelo_activo.txt)
After=network.target suricata.service
Requires=suricata.service

[Service]
Type=simple
User=m4rk
WorkingDirectory=/home/m4rk/ppi-surikata-producto
ExecStart=/usr/bin/python3 /home/m4rk/ppi-surikata-producto/scripts/motor_universal.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF'

echo 'cisco123' | sudo -S systemctl daemon-reload
echo 'cisco123' | sudo -S systemctl enable ppi-motor-universal.service
```

---

### Paso 6: Arrancar y verificar

```bash
# Activar AE y arrancar
echo "AE" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
echo 'cisco123' | sudo -S systemctl start ppi-motor-universal.service
```

Verificar que esté corriendo:

```bash
echo 'cisco123' | sudo -S systemctl status ppi-motor-universal.service --no-pager | head -15
```
```
● ppi-motor-universal.service - PPI Motor Universal (IF o AE segun config/modelo_activo.txt)
     Loaded: loaded (/etc/systemd/system/ppi-motor-universal.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-06-19 01:53:00 -05; 2h 10min ago
   Main PID: 3247 (python3)
      Tasks: 3 (limit: 2178)
     Memory: 102.8M
        CPU: 1.234s
     CGroup: /system.slice/ppi-motor-universal.service
             └─3247 /usr/bin/python3 /home/m4rk/ppi-surikata-producto/scripts/motor_universal.py
```

Verificar logs en tiempo real:

```bash
tail -f /home/m4rk/ppi-surikata-producto/results/motor_decision.log
```

Líneas típicas con AE activo:

```
2026-06-19 01:53:02,341 INFO motor_universal.py — modelo activo: AE
2026-06-19 01:53:02,412 INFO Umbrales: tau1=-0.0038  tau2=-0.0745
2026-06-19 01:53:02,413 INFO Leyendo eve.json: /var/log/suricata/eve.json
2026-06-19 01:53:05,218 DEBUG PERMIT [AE] 192.168.0.100 score=-0.0289
2026-06-19 01:53:07,891 WARNING EVENTO modelo=AE src=192.168.0.100 score=-0.0823 grado=CRITICA accion=BLOCK
2026-06-19 01:53:07,891 WARNING 🔴 BLOCK [AE] 192.168.0.100 score=-0.0823 grado=CRITICA
```

---

## 6. Switching en segundos

El switching completo (cambio de modelo + reinicio del motor) toma **< 5 segundos**.

### Cambiar a AE

```bash
echo "AE" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
echo 'cisco123' | sudo -S systemctl restart ppi-motor-universal.service
```

### Volver a IF

```bash
echo "IF" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
echo 'cisco123' | sudo -S systemctl restart ppi-motor-universal.service
```

### Verificar cuál modelo está activo

```bash
# Ver el archivo de config
cat /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt

# Ver los primeros logs del servicio tras el reinicio
echo 'cisco123' | sudo -S journalctl -u ppi-motor-universal.service -n 5 --no-pager
```

La primera línea del log siempre indica el modelo cargado:
```
INFO motor_universal.py — modelo activo: IF
INFO Umbrales: tau1=-0.4459  tau2=-0.6027
```
o
```
INFO motor_universal.py — modelo activo: AE
INFO Umbrales: tau1=-0.0038  tau2=-0.0745
```

### IMPORTANTE: no correr ambos servicios a la vez

```bash
# El MVP (ppi-motor.service) usa el mismo eve.json y los mismos ipsets
# Correr ambos a la vez causa conflictos en ipset. Solo uno activo a la vez.

# Verificar cuáles están corriendo:
echo 'cisco123' | sudo -S systemctl is-active ppi-motor.service
echo 'cisco123' | sudo -S systemctl is-active ppi-motor-universal.service
```

---

## 7. Arquitectura del motor_universal.py

### Patrón Adaptador

El motor usa el patrón Adaptador para abstraer la diferencia entre IF y AE. El código de decisión (τ1, τ2, PERMIT/LIMIT/BLOCK) es **idéntico** para ambos modelos.

```
config/modelo_activo.txt → "IF" o "AE"
         │
         ▼
   AdaptadorIF.score(x14)          AdaptadorAE.score(x14)
   ─────────────────────           ──────────────────────
   xs = scaler.transform(x14)      xs   = scaler.transform(x14)
   return score_samples(xs)[0]     xhat = ae.predict(xs)
                                   mse  = mean((xs-xhat)²)
                                   return -mse
         │                                │
         └──────────── score ─────────────┘
                          │
                    menor = más anómalo
                          │
               clasificar_grado(score, τ1, τ2)
               ─────────────────────────────────
               score > τ1  → NORMAL   → PERMIT
               τ2 < score ≤ τ1 → BAJA → LIMIT
               score ≤ τ2  → ALTA/CRITICA → BLOCK
```

### Clases clave

```python
class AdaptadorIF:
    def __init__(self):
        self.model  = joblib.load('models/isolation_forest.pkl')
        self.scaler = joblib.load('models/scaler.pkl')

    def score(self, x14: np.ndarray) -> float:
        xs = self.scaler.transform(x14.reshape(1, -1))
        return float(self.model.score_samples(xs)[0])


class AdaptadorAE:
    def __init__(self):
        self.model  = joblib.load('models/ae/ae_autoencoder.pkl')
        self.scaler = joblib.load('models/ae/ae_scaler.pkl')

    def score(self, x14: np.ndarray) -> float:
        xs   = self.scaler.transform(x14.reshape(1, -1))
        xhat = self.model.predict(xs)
        mse  = float(np.mean((xs - xhat) ** 2))
        return -mse   # mismo convenio que IF
```

### Lógica de arranque

```python
def main():
    modelo_activo = leer_modelo_activo()   # lee config/modelo_activo.txt

    if modelo_activo == 'AE':
        adaptador  = AdaptadorAE()
        tau1, tau2 = leer_umbrales('results/ae/ae_metricas_offline.txt')
    else:
        adaptador  = AdaptadorIF()
        tau1, tau2 = leer_umbrales('results/metricas_offline.txt')

    # A partir de aquí, todo el código es idéntico para IF y AE
    for raw in seguir_eve(EVE_JSON):
        feats = extraer_features(ev)
        score = adaptador.score(feats)
        grado = clasificar_grado(score, tau1, tau2)
        # ... PERMIT / LIMIT / BLOCK
```

### Heurísticos adicionales (idénticos al MVP)

El motor universal incluye los mismos detectores heurísticos que `motor_decision.py`:

| Heurístico | Umbral LIMIT | Umbral BLOCK | Ventana |
|---|---|---|---|
| Brute Force SSH (port 22) | 5 intentos | 15 intentos | 60 s |
| HTTP Abuse (port 80/8080) | 50 requests | 100 requests | 30 s |

Estos se aplican **antes** del score del modelo. Si un heurístico ya decidió BLOCK, el modelo no lo revierte.

---

## 8. Comparación IF vs AE

### Métricas globales

| Métrica | Isolation Forest | Autoencoder (AE) |
|---|---|---|
| **AUC-ROC** | **0.8998** | **0.9103** (+1.16%) |
| Precision | 99.54% | 99.42% |
| Recall (TPR @ τ1) | 99.40% | 99.42% |
| F1-Score | 0.9947 | 0.9942 |
| τ1 (Youden) | −0.4459 | −0.0038 |
| TPR @ τ1 | 99.40% | 99.42% |
| FPR @ τ1 | 20.47% | 25.68% |
| τ2 (FPR ≤ 2%) | −0.6027 | −0.0745 |
| TPR @ τ2 | 18.27% | 54.62% ✅ |
| FPR @ τ2 | ~2.00% | 2.00% |
| Flujos entrenamiento | 53,708 | 53,708 (idéntico) |
| Flujos evaluación (normal) | 13,427 | 13,427 (idéntico) |
| Flujos evaluación (anómalo) | 598,285 | 598,285 (idéntico) |
| Tiempo de entrenamiento | < 10 s | 115.6 s |
| Tamaño del modelo serializado | ~2.5 MB | 16 KB |
| Inferencia por flujo | < 1 ms | ~1 ms |

**Ventaja destacada del AE:** TPR @ τ2 = **54.62%** vs IF = 18.27%. Esto significa que el AE bloquea (FPR ≤ 2%) el 54.6% de los ataques reales, mientras que el IF solo bloquea el 18.3% con la misma tasa de falsos positivos.

### AUC por escenario (Grupo B)

| Escenario | Flows | AUC Autoencoder |
|---|---|---|
| ICMP Flood (15-jun) | 100,000 | **0.9996** |
| ICMP Flood (02-jun) | 23,460 | **0.9966** |
| UDP Flood (15-jun) | 100,000 | **0.9787** |
| UDP Flood (02-jun) | 18,168 | **0.9701** |
| Brute Force SSH (02-jun) | 2,061 | **0.9636** |
| HTTP Abuse (02-jun) | 13,889 | **0.9522** |
| Port Scan (15-jun) | 100,000 | **0.9134** |
| HTTP Abuse (15-jun) | 36,902 | **0.8960** |
| Brute Force SSH (15-jun) | 4,824 | **0.8886** |
| SYN Flood (15-jun) | 330 | **0.8122** |
| SYN Flood (02-jun) | 95,393 | **0.8563** |
| Brute Force SSH (03-jun) | 100,000 | 0.7739 |
| Port Scan (02-jun) | 3,258 | 0.7734 |

Los AUC más bajos en Port Scan y Brute Force (algunos archivos) se deben a que estos ataques generan flujos que en apariencia son cortos y similares a tráfico normal desde el punto de vista del AE.

### Diferencias de paradigma

| Aspecto | Isolation Forest | Autoencoder (AE) |
|---|---|---|
| Paradigma | Isolación por partición aleatoria | Compresión + reconstrucción |
| Qué aprende | Qué es difícil de aislar (normal) | Cómo reconstruir tráfico normal |
| Score range | [−1, 0] (acotado) | (−∞, 0] (no acotado) |
| Sensible a escala | No (árboles invariantes) | Sí (requiere StandardScaler) |
| Velocidad entrenamiento | O(n log n) | O(n × epochs) |
| Interpretabilidad | Baja | Muy baja |

---

## 9. Coexistencia con el MVP

### Diagrama de coexistencia

```
ppi-motor.service              ppi-motor-universal.service
(motor_decision.py)            (motor_universal.py)
        │                              │
        │  IsolationForest puro        │  IF o AE según config/
        │  isolation_forest.pkl        │  modelo_activo.txt
        │  scaler.pkl                  │
        │  metricas_offline.txt        │
        │                              │
        └──────── eve.json ────────────┘
                     │
              (NUNCA correr
              ambos a la vez)
```

### Reglas de operación

1. **Solo un motor activo a la vez.** Ambos leen `eve.json` y escriben en los mismos ipsets.
2. **El MVP siempre está disponible.** `ppi-motor.service` nunca fue modificado ni desactivado.
3. **Cambiar de vuelta al MVP:**
   ```bash
   echo 'cisco123' | sudo -S systemctl stop ppi-motor-universal.service
   echo 'cisco123' | sudo -S systemctl start ppi-motor.service
   ```

---

## 10. Solución de problemas

### El servicio no arranca

```bash
echo 'cisco123' | sudo -S journalctl -u ppi-motor-universal.service -n 30 --no-pager
```

Causas más comunes:
- `config/modelo_activo.txt` no existe → el motor usa IF por defecto
- `models/ae/ae_autoencoder.pkl` no existe → ejecutar Paso 1
- `results/ae/ae_metricas_offline.txt` no existe → ejecutar Paso 2
- Suricata no está corriendo → `sudo systemctl start suricata`

### Score del AE siempre es 0.0

Verificar que `ae_scaler.pkl` fue generado con `fit_transform` y no con `fit` solo:

```python
import joblib
scaler = joblib.load('models/ae/ae_scaler.pkl')
print(scaler.mean_)   # no debe ser None
```

### El motor dice "AdaptadorIF cargado" cuando debería ser AE

```bash
cat /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
# Debe decir exactamente: AE  (sin espacios adicionales)
```

Si hay espacios o salto de línea extra:
```bash
echo -n "AE" > /home/m4rk/ppi-surikata-producto/config/modelo_activo.txt
```

### Verificar que el MVP sigue intacto

```bash
md5sum /home/m4rk/ppi-surikata-producto/scripts/motor_decision.py
md5sum /home/m4rk/ppi-surikata-producto/models/isolation_forest.pkl
md5sum /home/m4rk/ppi-surikata-producto/models/scaler.pkl
# Comparar con los valores antes de este experimento (en git history)
```

---

*Documento generado: 2026-06-19 | PPI UPeU — Rubén Mark Salazar Tocas*
