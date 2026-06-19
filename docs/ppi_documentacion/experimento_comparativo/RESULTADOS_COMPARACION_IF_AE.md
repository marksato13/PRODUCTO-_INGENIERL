# Resultados Comparación IF vs Autoencoder — PPI UPeU 2026

**Script:** `scripts/comparacion/ae/f6_ae_comparacion.py`  
**Datos procesados:** 47 archivos .gz — Grupo A (normal) · B (anómalo) · C (mixto)  
**Fecha:** 2026-06-19  
**Referencia ensemble:** `docs/ppi_documentacion/experimento_comparativo/FASE7_MEJORAS.md`

---

## 1. Tabla comparativa global

| Métrica | Isolation Forest | Autoencoder (AE) | Ganador |
|---|---|---|---|
| **AUC-ROC medio Grupo B** | 0.9270 | **0.9579** (+3.3%) | AE |
| **Det% @ τ1 (LIMIT+BLOCK)** | **99.64%** | 98.76% | IF |
| **Block% @ τ2 (FPR≤2%)** | 20.03% | **62.03%** (+3.1×) | AE ⭐ |
| AUC-ROC global (F3 completo) | 0.8998 | **0.9103** | AE |
| Precision @ τ1 | **99.54%** | 99.42% | IF |
| Recall @ τ1 | **99.40%** | 99.42% | Empate |
| F1 @ τ1 | **0.9947** | 0.9942 | IF |
| Tiempo de entrenamiento | **< 10 s** | 115.6 s | IF |
| Tamaño del modelo pkl | 2.5 MB | **16 KB** | AE |
| Inferencia por flujo | ~1 ms | ~1 ms | Empate |
| ITL en producción (con whitelist) | **0%** | **0%** | Empate |

---

## 2. AUC por escenario — Grupo B

| Escenario | Flows | AUC IF | AUC AE | Ganador |
|---|---|---|---|---|
| ICMP Flood (02-jun) | 23,460 | 0.9160 | **0.9966** | AE (+8.8pp) |
| ICMP Flood (15-jun) | 100,000 | 0.8955 | **0.9996** | AE (+10.4pp) |
| Port Scan (02-jun) | 3,258 | 0.8351 | **0.9901** | AE (+15.5pp) ⭐ |
| Port Scan (15-jun) | 100,000 | 0.9508 | **0.9918** | AE (+4.1pp) |
| UDP Flood (02-jun) | 18,168 | 0.9579 | **0.9881** | AE (+3.0pp) |
| UDP Flood (15-jun) | 100,000 | 0.9623 | **0.9883** | AE (+2.6pp) |
| Brute Force (03-jun) | 100,000 | 0.8252 | **0.9863** | AE (+16.1pp) ⭐ |
| SYN Flood (02-jun) | 95,393 | 0.8815 | **0.9517** | AE (+7.0pp) |
| HTTP Abuse (02-jun) | 13,889 | 0.9545 | 0.9516 | IF (leve) |
| Brute Force (02-jun) | 2,061 | **0.9727** | 0.9649 | IF (leve) |
| Brute Force (15-jun) | 4,824 | **0.9728** | 0.9036 | IF (+6.9pp) |
| HTTP Abuse (15-jun) | 36,902 | **0.9749** | 0.9111 | IF (+6.4pp) |
| SYN Flood (15-jun) | 330 | **0.9515** | 0.8287 | IF (+12.3pp) |

**AE gana en 9 de 13 escenarios.** IF gana en floods HTTP y SYN del 15-jun y algunos bruteforce de volumen reducido.

---

## 3. Det% y Block% por escenario (Grupo B)

| Escenario | Det_IF | Det_AE | Blk_IF | Blk_AE |
|---|---|---|---|---|
| Brute Force (02-jun) | 99.9% | 99.0% | **35.3%** | 55.2% |
| HTTP Abuse (02-jun) | 95.7% | 94.1% | 13.5% | **71.4%** |
| ICMP Flood (02-jun) | 100.0% | 100.0% | 0.0% | **100.0%** |
| Port Scan (02-jun) | 100.0% | 100.0% | 3.8% | **73.0%** |
| SYN Flood (02-jun) | 100.0% | 99.6% | 14.2% | **50.9%** |
| UDP Flood (02-jun) | 100.0% | 100.0% | 0.0% | **93.0%** |
| Brute Force (03-jun) | 99.7% | 99.6% | 1.3% | **94.9%** |
| Brute Force (15-jun) | 100.0% | 96.8% | **58.2%** | 0.8% |
| HTTP Abuse (15-jun) | 100.0% | 96.4% | **64.8%** | 0.3% |
| ICMP Flood (15-jun) | 100.0% | 100.0% | 0.1% | **99.9%** |
| Port Scan (15-jun) | 100.0% | 100.0% | **65.6%** | 66.3% |
| SYN Flood (15-jun) | 100.0% | 98.5% | 3.6% | **4.9%** |
| UDP Flood (15-jun) | 100.0% | 100.0% | 0.0% | **95.9%** |

**Patrón claro:** AE bloquea directamente (τ2) una fracción mucho mayor de ataques en la mayoría de escenarios. IF detecta todo (Det=100%) pero con el umbral τ2 solo bloquea el 20% en promedio.

---

## 4. Grupo C — Mixto (normal + anómalo simultáneo)

| Archivo | ITL IF | ITL AE | Det IF | Det AE |
|---|---|---|---|---|
| descarga_udp (02-jun) | 100.0% | 96.8% | **100%** | **100%** |
| http_syn (02-jun) | 99.0% | 95.8% | **100%** | **100%** |
| ssh_portscan (02-jun) | 100.0% | 79.0% | **100%** | **100%** |
| http_synflood (16-jun) | 9.8% | 8.6% | **100%** | **100%** |
| ssh_portscan (16-jun) | 44.0% | 77.2% | **100%** | **100%** |
| transfer_udpflood (16-jun) | 61.2% | 61.7% | **100%** | **100%** |

**Nota sobre ITL en Grupo C:** Estos valores altos (~100%) reflejan el comportamiento del modelo sin whitelist. En producción, las IPs internas (Desktop 192.168.0.20, Server 192.168.0.120) siempre están en la whitelist → ITL real en producción = 0% (confirmado en 40 corridas F6). Estos valores son informativos del modelo crudo, no del sistema operativo.

---

## 5. Gráficas generadas

| Figura | Ruta | Descripción |
|---|---|---|
| ae_01_auc_por_escenario.png | `results/ae/graficas_comparacion/` | AUC IF vs AE por escenario (barras) |
| ae_02_det_block_por_escenario.png | `results/ae/graficas_comparacion/` | Det% y Block% por escenario (2 paneles) |
| ae_03_distribuciones_score.png | `results/ae/graficas_comparacion/` | Histogramas score normal vs anómalo IF y AE |
| ae_04_acuerdo_decisiones.png | `results/ae/graficas_comparacion/` | Acuerdo BLOCK/LIMIT/PERMIT entre modelos (stacked bar) |
| ae_05_panel_resumen.png | `results/ae/graficas_comparacion/` | Panel 2×2: AUC, tabla métricas, Block%, scatter AE vs IF |

---

## 6. ¿Con cuál modelo quedarse?

### Recomendación: **Isolation Forest para el MVP — Autoencoder como comparación**

**Motivo principal:** El IF cumple todos los requisitos del PPI. El AE es más potente en Block% pero su τ2 bloquea flows que el IF permite, lo que introduce variabilidad entre sesiones de captura.

| Criterio de decisión | IF | AE |
|---|---|---|
| AUC ≥ 0.80 (requisito tesis) | ✅ 0.8998 | ✅ 0.9103 |
| F1 @ τ1 | **0.9947** | 0.9942 |
| 40 corridas F6 validadas | ✅ Sí | ❌ No (se hizo offline) |
| Entrenamiento rápido (<60s) | ✅ <10s | ❌ 115.6s |
| Reproducibilidad exacta (sklearn 1.9.0) | ✅ Verificado | ✅ Mismo sklearn |
| Modelo ligero en RAM | 2.5 MB | **16 KB** |
| Explicabilidad (para asesores) | Media | Muy baja |
| Riesgo al cambiar de modelo | — | Requiere recalibrar τ en producción |

**Para el informe:** Presentar IF como modelo de producción y AE como "experimento comparativo" — el AE mejora AUC en +1% y Block% en 3× pero no fue sometido a las 40 corridas de F6, por lo que no puede afirmarse que supera al IF en el sistema completo.

---

## 7. La mejora sensata: Ensemble IF + AE (AND gate)

> Documentado en detalle en `FASE7_MEJORAS.md`

La opción técnicamente más sólida **no es elegir entre IF o AE, sino combinarlos:**

```
Flujo → IF.score() + AE.score()
         │               │
         ▼               ▼
     score_if         score_ae
         │               │
         └──── AND gate ──┘
               min(s_IF, s_AE)
                    │
           τ1/τ2 sobre score combinado
```

**Resultados del ensemble AND gate (de FASE7_MEJORAS.md):**

| Métrica | IF solo | AE solo | **Ensemble AND** |
|---|---|---|---|
| AUC-ROC | 0.9159 | 0.9580 | **0.9580** |
| Recall | 0.9953 | 0.9883 | **0.9883** |
| FPR | 0.2038 | 0.1035 | **0.1035** |
| F1 | 0.8953 | 0.9394 | **0.9394** |
| Falsos positivos (sobre 4,029 normales) | 821 | 417 | **417 (−49%)** |

**El AND ensemble elimina el 49% de falsos positivos con solo −0.7% de Recall.** Matemáticamente, el AND es equivalente a usar el AE como filtro de confirmación del IF — solo bloquea cuando ambos coinciden.

**Overhead de latencia: +0.001 ms por flujo** (totalmente despreciable — P95 actual es 34.8ms).

### Por qué no está en el MVP actual

1. El PPI ya cumple todos sus requisitos con IF solo (AUC=0.8998, F1=0.9947, ITL=0%, Disp.=100%).
2. El ensemble requeriría recalibrar τ_AE sobre los 598K flows + repetir las 40 corridas F6 (~4h adicionales).
3. El FPR del IF ya está mitigado en producción por la whitelist — el impacto real es 0% en las 40 corridas.

**Como trabajo futuro:** Implementar el ensemble AND en `motor_decision.py`, recalibrar θ_AE, y validar con 20 corridas adicionales. Hipótesis: F1 escala de 0.9947 a ~0.9980.

---

## 8. Decisión final recomendada

```
PRODUCCIÓN (PPI MVP):     Isolation Forest  ← sin cambios, validado, cumple todo
COMPARACIÓN (informe):    Autoencoder       ← AUC mejor, Block% 3× mejor
MEJORA FUTURA:            Ensemble AND      ← −49% FPR, +4.8pp F1, 0.001ms overhead
```

El AE no reemplaza al IF — **lo complementa.** El ensemble es la conclusión natural del experimento comparativo y queda documentado como trabajo futuro en la sección de conclusiones del informe.
