# Overview — Pipeline Completo F1→F6 (Sistema Actual)

**Versión:** 2026-06-17 — Pipeline corregido (sin CSVs intermedios, splits correctos)
**Nota:** El XML Draw.io de esta versión refleja el pipeline **real implementado**.
Ver `docs/METODOLOGIA_PIPELINE_COMPARATIVA.md` para la comparación con el flujo anterior (eliminado).

---

## Scripts reales por fase

| Fase | Script(s) | Entrada | Salida |
|---|---|---|---|
| **F1 — Entorno** | — (configuración manual) | Topología física | Suricata activo, SSH keys |
| **F2 — Captura** | `exportar_eve_por_escenario.sh` | `/var/log/suricata/eve.json` | `data/raw/*_{normal,anom,mixto}_*.gz` |
| **F3 — Modelado** | `fase3_entrenar.py` → `fase3_evaluar.py` → `auc_por_escenario.py` | `data/raw/*_normal_*.gz` (Grupo A) | `models/*.pkl` + `results/metricas_offline.txt` |
| **F4 — Motor** | `motor_decision.py` | `eve.json` live + `models/*.pkl` + `metricas_offline.txt` | `results/motor_decision.log` + ipset actions |
| **F5 — Control** | `enforce.sh` + `dashboard.py` + `dashboard_web.py` | `motor_decision.log` | Bloqueos ipset + visualización |
| **F6 — Validación** | `f6_corridas.py` + `generar_graficas_f6.py` | Motor activo + tráfico A+B+C | `results/resultados_f6_completo.csv` + 7 PNGs |

## Qué grupos se usan en cada fase

| Grupo | F2 Captura | F3 Entrenamiento | F3 Evaluación | F4 Motor | F6 Validación |
|---|---|---|---|---|---|
| **A — Normal** | ✅ captura | ✅ solo este | ✅ holdout 20% | monitor | ✅ 10 corridas |
| **B — Anómalo** | ✅ captura | ❌ NO | ✅ ROC/τ | trigger | ✅ corridas 11-40 |
| **C — Mixto** | ✅ captura | ❌ NO | ❌ NO | operativo | ✅ 10 corridas mixto (11-20) |

> **Estructura interna F6 (`f6_corridas.py`):** 4 fases de 10 corridas:
> Normal(1-10) solo Desktop | Mixto(11-20) Desktop+Kali |
> Reeval(21-30) Kali bloqueada en memoria | Final(31-40) confirmación.
> Los grupos A/B/C de la tabla indican el tipo de tráfico, no las fases internas de F6.

**Principio central:** IF aprende SOLO de tráfico normal (Grupo A). Nunca ve ataques en entrenamiento.

## Splits de datos (flujo real)

```
Grupo A (data/raw/*_normal_*.gz)
  └─ fase3_entrenar.py — Split 80/20 aleatorio (random_state=42)
       ├─ 80% → X_train (53,708 flows) → IsolationForest.fit()
       └─ 20% → data/normal_holdout.csv (13,427 flows) → nunca visto por el modelo

  NO existe: train.csv, val.csv, test.csv (70/15/15)
  NO existe: dataset_raw.csv, dataset_clean.csv
  NO existen: parser.py, etiquetar_limpiar.py, particionar_estadisticos.py
```

## Diagrama Mermaid (pipeline actual)

```mermaid
flowchart TD
    subgraph F2["F2 — Captura (3 grupos separados)"]
        A["Grupo A - Normal\n28 archivos .gz\n397,984 flows raw"]
        B["Grupo B - Anómalo\n13 archivos .gz\n56,080,443 flows raw"]
        C["Grupo C - Mixto\n6 archivos .gz\n49,262,091 flows raw"]
    end

    subgraph F3["F3 — Modelado Offline"]
        ENT["fase3_entrenar.py\nSolo Grupo A\nSplit 80/20"]
        TRAIN["X_train\n53,708 flows"]
        HOLD["normal_holdout.csv\n13,427 flows"]
        IF["IsolationForest\nn=300, sklearn 1.9.0\nisolation_forest.pkl"]
        EVAL["fase3_evaluar.py\nholdout + Grupo B\nCurva ROC"]
        TAU["metricas_offline.txt\nτ1=−0.4459 Youden\nτ2=−0.6027 FPR≤2%"]
    end

    subgraph F4["F4 — Motor Tiempo Real"]
        MOTOR["motor_decision.py\ntail eve.json\nIF score por flow"]
        DEC["PERMIT / LIMIT / BLOCK\nvía ipset + iptables"]
    end

    subgraph F6["F6 — Validación (3 grupos juntos)"]
        F6S["f6_corridas.py\n40 corridas: Normal(10)+Mixto(10)+Reeval(10)+Final(10)\nMotor activo durante validación"]
        RES["Disponibilidad 100%\nLatencia P95=34.8ms\nITL=0%"]
    end

    A --> ENT
    ENT --> TRAIN & HOLD
    TRAIN --> IF
    HOLD --> EVAL
    B --> EVAL
    IF --> EVAL
    EVAL --> TAU
    TAU --> MOTOR
    IF --> MOTOR
    MOTOR --> DEC
    DEC --> F6S
    A & B & C --> F6S
    F6S --> RES
```

## Diagrama de imagen (300 DPI)

El archivo `results/comparacion/diagrama_pipeline.png` contiene el diagrama visual completo del pipeline con código de colores por grupo (azul=normal, rojo=anómalo, naranja=mixto, verde=experimento comparativo, morado=F6).

---

**Ver también:**
- `docs/METODOLOGIA_PIPELINE_COMPARATIVA.md` — comparación flujo anterior vs actual
- `results/comparacion/eda_distribucion_grupos.png` — EDA de distribución de flows por grupo
- `results/comparacion/diagrama_pipeline.png` — diagrama de pipeline visual
