# Comparación: Isolation Forest vs Modelos Alternativos

**Proyecto:** PPI UPeU 2026  
**Fecha:** 2026-06-17  
**Basado en:** Experimento comparativo FASE 4 — 7 modelos, mismo test set (7,629 flows)

---

## Conclusión directa

| Ranking | Modelo | Veredicto |
|---|---|---|
| 🥇 1 | **Isolation Forest** | Mejor opción — mayor Recall, pipeline validado |
| 🥈 2 | **Autoencoder** | Segundo mejor — F1 superior, inferencia 30× más rápida |
| 🥉 3 | **One-Class SVM** | Viable — mayor AUC pero Recall insuficiente |
| ✗ 4 | LOF | Descartado — Recall=59% inaceptable |

> Los supervisados (RF, XGBoost, DT) quedan fuera del ranking porque tienen ventaja injusta: conocen los ataques en entrenamiento.

---

## Tabla comparativa completa (solo modelos one-class)

| Métrica | **IF** 🥇 | **Autoencoder** 🥈 | **OCSVM** 🥉 | LOF ✗ |
|---|---|---|---|---|
| AUC-ROC | 0.9159 | 0.9580 | **0.9712** | 0.8418 |
| **Recall** | **0.9953** | 0.9883 | 0.9303 | 0.5900 ❌ |
| Precision (exp.) | 0.8136 | 0.8951 | **0.9120** | 0.9104 |
| **F1** | 0.8953 | **0.9394** | 0.9211 | 0.7160 |
| FPR | 0.2038 | 0.1035 | **0.0802** | 0.0519 |
| Inferencia | 0.0297 ms | **0.0010 ms** | 0.0344 ms | 0.0429 ms |
| T. entrenamiento | pre-ent. | 26.9s | 0.6s | 0.3s |
| n_train | 53,708 | 9,398 | 9,398 | 5,000 |
| Escalable online | ✅ | ✅ | ⚠️ | ❌ |
| **Puntaje ponderado** | **9.75/10** | **8.70/10** | **7.30/10** | **5.05/10** |

---

## 🥇 Por qué IF es el mejor

### 1. Mayor Recall — la métrica que importa en seguridad

```
IF  → 99.53%  detecta 3,583 de 3,600 ataques
AE  → 98.83%  detecta 3,558 de 3,600 ataques  (25 más que escapa)
OCSVM→ 93.03%  detecta 3,349 de 3,600 ataques  (234 más que escapa)
LOF →  59.00%  detecta 2,124 de 3,600 ataques  (1,476 más que escapa)
```

Un ataque no detectado tiene consecuencias reales. IF deja escapar la menor cantidad.

### 2. Precision real en producción: 99.54%

En la distribución real de producción (1:44.5), IF alcanza Precision=**99.54%** — derivado matemáticamente del mismo FPR con 598,285 anomalías reales.

### 3. Pipeline de producción completamente validado

- τ1=−0.4459, τ2=−0.6027 calibrados sobre 598K+ anomalías reales
- Whitelist de 7 IPs (Desktop, Sensor, Servidor, etc.)
- Heurísticos adicionales: BF-SSH (15 intentos/60s) y HTTP-Abuse (100 req/30s)
- 40 corridas de validación F6 — Disponibilidad 100%, Latencia P95=34.8ms
- Integración completa con Suricata → ipset → Telegram → Dashboard

### 4. Entrenado con 5.7× más datos normales

IF fue entrenado con 53,708 flujos normales (el doble del dataset de entrenamiento de AE y OCSVM en el experimento). Mejor caracterización del comportamiento normal = mejor detección de desviaciones.

---

## 🥈 Por qué el Autoencoder es el segundo mejor

### Lo que hace mejor que IF

| Aspecto | IF | Autoencoder | Ventaja |
|---|---|---|---|
| AUC-ROC | 0.9159 | **0.9580** | AE +4.2pp |
| F1 (experimento) | 0.8953 | **0.9394** | AE +4.4pp |
| FPR | 0.2038 | **0.1035** | AE −49% falsas alarmas |
| Inferencia | 0.0297 ms | **0.0010 ms** | AE 30× más rápido |

### Lo que hace peor que IF

| Aspecto | IF | Autoencoder | Ventaja |
|---|---|---|---|
| **Recall** | **0.9953** | 0.9883 | **IF +0.7pp** |
| n_train disponible | **53,708** | 9,398 | IF entrenó con más datos |
| Pipeline validado | ✅ completo | ❌ solo experimental | IF maduro |

### Por qué el Autoencoder es sólido como segunda opción

1. **F1=0.9394** — la métrica que equilibra Precision y Recall es mayor que IF en el test balanceado
2. **FPR=10.35%** — genera la mitad de falsas alarmas que IF
3. **Inferencia 0.001ms** — 30 veces más rápido que IF, ideal para sistemas de tiempo real
4. **Arquitectura simple** — 14→10→7→10→14, implementado con `sklearn.MLPRegressor` sin GPU
5. **Candidato ideal para ensemble** — cuando se combina con IF en AND gate:
   - FPR cae de 20.38% a **10.35% (−49.2%)**
   - F1 sube de 0.8953 a **0.9394 (+4.8pp)**
   - Recall se mantiene en **98.83%** (solo −0.7pp vs IF solo)

---

## 🥉 Por qué OCSVM queda tercero

OCSVM tiene la **mayor AUC entre todos los one-class (0.9712)**, pero:

| Problema | Detalle |
|---|---|
| Recall=93.03% | 234 ataques más que escapan vs IF en el mismo test |
| O(n²) entrenamiento | Con 53,708 flows tardaría 30+ minutos — inviable para reentrenamiento mensual |
| Sin pipeline de producción | Solo experimental — necesita calibración de umbrales, whitelist, etc. |
| Puntaje ponderado 7.30/10 | vs IF=9.75 y AE=8.70 |

OCSVM sería viable como alternativa al IF si se aceptara un Recall menor (~93%) a cambio de menor FPR (~8%). Sin embargo, en un sistema de detección de intrusiones, **detectar el 93% de los ataques no es suficiente** cuando el IF detecta el 99.5%.

---

## Comparación directa: IF vs Autoencoder

| Criterio | IF gana | AE gana |
|---|---|---|
| Recall (ataques detectados) | ✅ 99.53% vs 98.83% | |
| AUC-ROC | | ✅ 0.9580 vs 0.9159 |
| F1 (experimento balanceado) | | ✅ 0.9394 vs 0.8953 |
| FPR (falsas alarmas) | | ✅ 10.35% vs 20.38% |
| Velocidad de inferencia | | ✅ 0.001ms vs 0.030ms |
| Datos de entrenamiento | ✅ 53,708 vs 9,398 | |
| Pipeline en producción | ✅ validado 40 corridas | |
| Reentrenamiento | ✅ systemctl restart | |
| **Puntaje ponderado** | ✅ **9.75/10** | 8.70/10 |

**Resultado:** IF gana en Recall y madurez del pipeline. AE gana en casi todo lo demás.

**Solución óptima:** Ensemble AND (IF + AE) — combina las fortalezas de ambos:
- Recall=98.83% (casi igual a IF solo)
- FPR=10.35% (igual a AE solo = −49% vs IF solo)
- F1=0.9394 (igual a AE solo = mejor que IF solo)

---

## Respuesta verbatim para la sustentación

> *"El modelo ideal para nuestro sistema es Isolation Forest. En el experimento comparativo con 7 modelos, IF obtuvo el mayor Recall entre todos los modelos one-class: 99.53%, frente al 98.83% del Autoencoder y el 93.03% del One-Class SVM. En el sistema en producción, con la distribución real de tráfico, IF alcanza Precision=99.54% y F1=0.9947.*
>
> *El segundo mejor modelo es el Autoencoder. Obtuvo mayor AUC (0.9580 vs 0.9159), mayor F1 en el experimento (0.9394 vs 0.8953), y la mitad de falsas alarmas (FPR=10.35% vs 20.38%). Su única debilidad frente a IF es el Recall, apenas 0.7 puntos porcentuales menor.*
>
> *De hecho, cuando combinamos IF y Autoencoder en un ensemble AND — donde se bloquea solo cuando AMBOS modelos coinciden — obtenemos lo mejor de los dos: el FPR cae un 49% y el F1 sube 4.8 puntos porcentuales, con un costo de solo 0.7pp en Recall. Esta mejora está validada experimentalmente y la proponemos como trabajo futuro."*

---

## Resumen en tres líneas

> **IF detecta más ataques (99.53% Recall) — es el modelo correcto para producción.**  
> **El Autoencoder genera menos falsas alarmas y tiene mejor F1 — es el mejor complemento.**  
> **Juntos como ensemble AND, superan a cualquier modelo individual en el balance Recall/FPR.**
