# Decisión de Modelo en Producción — Por qué nos quedamos con Isolation Forest

**Proyecto:** PPI UPeU — Detección Temprana de Anomalías en Redes  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fecha de decisión:** 2026-06-19  
**Modelo activo:** `config/modelo_activo.txt` = `"IF"`

---

## Resumen ejecutivo

Se implementaron y evaluaron dos modelos de detección de anomalías:
- **Isolation Forest (IF)** — modelo del MVP, validado con 40 corridas en vivo
- **Autoencoder (AE)** — modelo comparativo, evaluado offline sobre 611,712 flows

**Decisión: Isolation Forest permanece como modelo de producción.** El AE queda documentado como experimento comparativo con resultados superiores en algunas métricas, y el Ensemble IF+AE como propuesta de mejora futura.

---

## 1. Cuadro comparativo completo

### 1.1 Métricas de detección (evaluación offline — mismos 611,712 flows)

| Métrica | Isolation Forest | Autoencoder | Diferencia |
|---|---|---|---|
| **AUC-ROC global** | 0.8998 | **0.9103** | AE +1.16% |
| **τ1 — Youden threshold** | −0.4459 | −0.0038 | — |
| **TPR @ τ1** | 99.40% | 99.42% | Empate |
| **FPR @ τ1** | **20.47%** | 25.68% | IF mejor |
| **τ2 — FPR ≤ 2%** | −0.6027 | −0.0745 | — |
| **TPR @ τ2 (Block directo)** | 18.27% | **54.62%** | AE +3× ⭐ |
| **FPR @ τ2** | 1.99% | 2.00% | Empate |
| Precision | **99.54%** | 99.42% | IF +0.12% |
| Recall | 99.40% | **99.42%** | Empate |
| F1-Score | **0.9947** | 0.9942 | IF +0.05pp |

### 1.2 Métricas operativas

| Métrica | Isolation Forest | Autoencoder | Diferencia |
|---|---|---|---|
| **Corridas F6 validadas en vivo** | **40 corridas** | 0 (solo offline) | IF: validación formal |
| **Disponibilidad en F6** | **100%** | No medida | IF: certificado |
| **ITL en F6 (tráfico legítimo afectado)** | **0%** | No medida | IF: certificado |
| **Lead Time SYN Flood** | **61.92 s** | No medida | IF: certificado |
| **Latencia P95** | **34.8 ms** | No medida | IF: certificado |
| Tiempo de entrenamiento | **< 10 s** | 115.6 s | IF 12× más rápido |
| Tamaño modelo serializado | 2.5 MB | **16 KB** | AE más ligero |
| Inferencia por flujo | ~1 ms | ~1 ms | Empate |
| ITL en producción (con whitelist) | **0%** | **0%** | Empate |

### 1.3 AUC por tipo de ataque — Grupo B (13 escenarios)

| Tipo de ataque | AUC IF | AUC AE | Ganador |
|---|---|---|---|
| ICMP Flood (02-jun, 23K flows) | 0.9160 | **0.9966** | AE +8.8pp |
| ICMP Flood (15-jun, 100K flows) | 0.8955 | **0.9996** | AE +10.4pp |
| Port Scan (02-jun, 3K flows) | 0.8351 | **0.9901** | AE +15.5pp |
| Port Scan (15-jun, 100K flows) | 0.9508 | **0.9918** | AE +4.1pp |
| UDP Flood (02-jun, 18K flows) | 0.9579 | **0.9881** | AE +3.0pp |
| UDP Flood (15-jun, 100K flows) | 0.9623 | **0.9883** | AE +2.6pp |
| Brute Force SSH (03-jun, 100K flows) | 0.8252 | **0.9863** | AE +16.1pp |
| SYN Flood (02-jun, 95K flows) | 0.8815 | **0.9517** | AE +7.0pp |
| HTTP Abuse (02-jun, 14K flows) | **0.9545** | 0.9516 | IF +0.3pp |
| Brute Force SSH (02-jun, 2K flows) | **0.9727** | 0.9649 | IF +0.8pp |
| Brute Force SSH (15-jun, 5K flows) | **0.9728** | 0.9036 | IF +6.9pp |
| HTTP Abuse (15-jun, 37K flows) | **0.9749** | 0.9111 | IF +6.4pp |
| SYN Flood (15-jun, 330 flows) | **0.9515** | 0.8287 | IF +12.3pp |
| **PROMEDIO** | **0.9270** | **0.9579** | AE +3.3pp |

AE gana en **9 de 13 escenarios**. IF gana en HTTP Abuse y algunos Brute Force / SYN Flood de menor volumen.

---

## 2. Por qué el AE es técnicamente superior — pero no lo usamos en producción

### 2.1 Ventaja técnica real del AE

La métrica más importante en producción es **Block% @ τ2** (cuántos ataques se bloquean directamente con FPR≤2%):

```
Isolation Forest:  18.27% de ataques bloqueados directamente
Autoencoder:       54.62% de ataques bloqueados directamente
                   ────────────────────────────────────────
                   AE bloquea 3× más ataques con el mismo FPR
```

En un ataque SYN flood real, el AE reacciona con mucha más fuerza. Esto es objetivamente mejor.

La diferencia en FPR @ τ1 (AE=25.68% vs IF=20.47%) **no importa en producción** porque todas las IPs internas (Desktop 192.168.0.20, Server 192.168.0.120, Sensor 192.168.0.110, Gateway 192.168.0.1) están en la whitelist y nunca son bloqueadas.

### 2.2 Por qué aun así mantenemos el IF

**Razón 1 — Validación formal completa:**
El IF tiene 40 corridas de validación en vivo con tráfico real, registradas en `results/resultados_f6_completo.csv` y en la bitácora oficial `docs/bitacora/bitacora_escenarios.txt`. El AE solo tiene evaluación offline. Para la defensa del PPI, los asesores pueden pedir evidencia de las 40 corridas — solo el IF las tiene.

**Razón 2 — Requisitos cumplidos:**
El PPI establece como hipótesis AUC > 0.80 y latencia < 500ms. El IF cumple ambos (AUC=0.8998, P95=34.8ms). Cambiar el modelo en producción no mejora el cumplimiento de los requisitos — ya están cumplidos.

**Razón 3 — Riesgo de calibración:**
Los umbrales τ1 y τ2 del AE se derivaron sobre los mismos 598K flows de evaluación. No han sido probados bajo tráfico en vivo con variabilidad temporal. Un umbral mal calibrado podría generar más bloqueados de los esperados o dejar pasar ataques que el IF detectaría.

**Razón 4 — Estabilidad del producto:**
El motor MVP (`motor_decision.py` + `ppi-motor.service`) nunca fue modificado. El IF es la base estable del sistema certificado. Cambiar a AE implicaría repetir las 40 corridas de F6 (~4 horas de pruebas en vivo con Kali) y refirmar la bitácora.

**Razón 5 — El AE tiene un comportamiento heterogéneo:**
En Brute Force SSH y HTTP Abuse del 15-jun (archivos grandes), el IF supera al AE por hasta 6.4–6.9pp de AUC. Esto sugiere que el AE puede ser menos robusto en ciertos patrones de ataque que el IF maneja mejor.

---

## 3. El AE en el informe — cómo presentarlo

El AE no es un fracaso — es un **resultado comparativo valioso**. Se presenta así en el informe:

> *"Como experimento comparativo, se implementó un Autoencoder (MLPRegressor sklearn, arquitectura 14→8→4→8→14) entrenado sobre los mismos datos del Grupo A. El AE obtuvo AUC=0.9103 (+1.16% sobre el IF) y una tasa de bloqueo directo de 54.62% frente al 18.27% del IF (ventaja de 3×). Sin embargo, no fue sometido a las 40 corridas de validación en vivo del sistema productivo, por lo que el IF permanece como modelo de producción certificado. El AE y el Ensemble IF+AE se proponen como trabajo futuro."*

---

## 4. La mejora futura: Ensemble IF+AE (AND gate)

Documentado en detalle en `FASE7_MEJORAS.md`. Resumen:

```
Score combinado = min(score_IF, score_AE)
Solo bloquea cuando AMBOS modelos confirman la anomalía
```

| Métrica | IF solo | Ensemble AND |
|---|---|---|
| AUC-ROC | 0.9159 | **0.9580** (+4.6%) |
| Recall | 0.9953 | 0.9883 (−0.7%) |
| FPR | 0.2038 | **0.1035 (−49.2%)** |
| F1 | 0.8953 | **0.9394 (+4.8pp)** |
| Falsos positivos sobre 4,029 normales | 821 | **417 (−404 FP)** |
| Overhead de latencia | — | **+0.001 ms** |

**Cuándo implementarlo:** Como trabajo futuro. Requiere calibrar θ_AE y validar con 20 corridas adicionales. El beneficio es real y medido — no es especulativo.

---

## 5. Resumen de la decisión

```
┌─────────────────────────────────────────────────────────┐
│  HOY (MVP / defensa del PPI)                            │
│  → Isolation Forest                                     │
│    AUC=0.8998  F1=0.9947  40 corridas validadas         │
│    Todos los requisitos CUMPLIDOS                       │
├─────────────────────────────────────────────────────────┤
│  COMPARACIÓN (informe / sección experimento)            │
│  → Autoencoder                                          │
│    AUC=0.9103  Block% 3× mejor  Validación offline      │
│    Resultado: AE > IF en métricas clave                 │
├─────────────────────────────────────────────────────────┤
│  FUTURO (propuesta de mejora)                           │
│  → Ensemble AND (IF + AE)                               │
│    FPR −49%  F1 +4.8pp  Overhead +0.001ms              │
│    Requiere: 20 corridas adicionales de F6              │
└─────────────────────────────────────────────────────────┘
```

**Switching disponible en segundos** (el sistema ya lo soporta):
```bash
# Activar AE:
echo "AE" > config/modelo_activo.txt && sudo systemctl restart ppi-motor-universal.service

# Volver a IF (estado actual):
echo "IF" > config/modelo_activo.txt && sudo systemctl restart ppi-motor-universal.service
```

---

*Documento generado: 2026-06-19 | PPI UPeU — Rubén Mark Salazar Tocas*
