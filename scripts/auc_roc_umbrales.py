#!/usr/bin/env python3
"""
Fase 3 — AUC-ROC y definición de umbrales τ1 y τ2
Lógica de decisión:
  score > τ1          → PERMIT  (normal)
  τ2 < score ≤ τ1    → LIMIT   (sospechoso — limitar tasa)
  score ≤ τ2          → BLOCK   (anómalo — bloquear)
"""

import joblib, glob, gzip, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

MODEL_DIR  = "/home/m4rk/ppi-surikata-producto/models"
DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data/raw"
FIG_DIR    = "/home/m4rk/ppi-surikata-producto/results/figures"
REPORT_DIR = "/home/m4rk/ppi-surikata-producto/results/reports"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

NORMAL_IPS = {"192.168.0.20", "192.168.0.120"}

clf    = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")

def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e["flow"]["start"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(e["flow"]["end"].replace("Z", "+00:00"))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001

def extract(e):
    flow = e.get("flow", {}); proto = e.get("proto", "").upper()
    dur = flow_duration(e)
    pts = flow.get("pkts_toserver", 0) or 0
    ptc = flow.get("pkts_toclient", 0) or 0
    bts = flow.get("bytes_toserver", 0) or 0
    btc = flow.get("bytes_toclient", 0) or 0
    return [pts, ptc, bts, btc, dur, (pts+ptc)/dur, (bts+btc)/dur,
            pts/(ptc+1), bts/(btc+1), (bts+btc)/(pts+ptc+1),
            int(proto=="TCP"), int(proto=="UDP"),
            int(proto in ("ICMP","IPV6-ICMP")), e.get("dest_port", 0) or 0]

def load_flows(path, src_filter=None, exclude_ips=None, max_flows=30000):
    rows = []
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", errors="ignore") as f:
        for line in f:
            if len(rows) >= max_flows: break
            try:
                e = json.loads(line)
                if e.get("event_type") != "flow": continue
                src = e.get("src_ip", "")
                if src_filter and src not in src_filter: continue
                if exclude_ips and src in exclude_ips: continue
                if (e.get("flow", {}).get("pkts_toserver", 0) or 0) == 0: continue
                rows.append(extract(e))
            except Exception:
                pass
    return np.array(rows) if rows else np.empty((0, 14))

# ── Cargar datos con etiquetas reales ────────────────────────
print("Cargando datos para ROC ...")
X_list, y_list = [], []

for path in sorted(glob.glob(f"{DATA_DIR}/*.gz")):
    nombre = os.path.basename(path)
    if "_normal_" in nombre:
        rows = load_flows(path, src_filter=NORMAL_IPS)
        label = 0
    else:
        rows = load_flows(path, exclude_ips=NORMAL_IPS)
        label = 1
    if len(rows) == 0: continue
    X_list.append(rows)
    y_list.extend([label] * len(rows))
    print(f"  {nombre:<52} {len(rows):>6} flows  label={label}")

X_all = scaler.transform(np.vstack(X_list))
y_all = np.array(y_list)
scores_all = clf.score_samples(X_all)

print(f"\nTotal: {len(y_all):,}  |  Normal: {(y_all==0).sum():,}  |  Anomalo: {(y_all==1).sum():,}")

# ── ROC curve con sklearn ────────────────────────────────────
from sklearn.metrics import roc_curve, roc_auc_score

# Isolation Forest: más negativo = más anómalo → invertir para ROC
fprs, tprs, thresholds_roc = roc_curve(y_all, -scores_all, pos_label=1)
auc = roc_auc_score(y_all, -scores_all)
# thresholds_roc está en espacio invertido (-score), convertir de vuelta
thresholds = -thresholds_roc
print(f"\nAUC-ROC: {auc:.4f}")

# ── Definir τ1 y τ2 desde la curva ROC ───────────────────────
# τ2 (BLOCK): máximo índice de Youden (TPR - FPR) → mejor balance
youden = tprs - fprs
idx_tau2 = np.argmax(youden)
tau2 = thresholds[idx_tau2]
tpr_tau2 = tprs[idx_tau2]
fpr_tau2 = fprs[idx_tau2]

# τ1 (LIMIT): FPR ≤ 2% con mayor TPR posible
mask_fpr2 = fprs <= 0.02
if mask_fpr2.any():
    idx_tau1 = np.where(mask_fpr2)[0][np.argmax(tprs[mask_fpr2])]
else:
    mask_fpr5 = fprs <= 0.05
    idx_tau1 = np.where(mask_fpr5)[0][np.argmax(tprs[mask_fpr5])]
tau1 = thresholds[idx_tau1]
tpr_tau1 = tprs[idx_tau1]
fpr_tau1 = fprs[idx_tau1]

print(f"\nτ1 (LIMIT threshold) : {tau1:.4f}  TPR={tpr_tau1:.3f}  FPR={fpr_tau1:.3f}")
print(f"τ2 (BLOCK threshold) : {tau2:.4f}  TPR={tpr_tau2:.3f}  FPR={fpr_tau2:.3f}")
print(f"Umbral actual modelo : {clf.offset_:.4f}")

# ── Evaluar con τ1 y τ2 ──────────────────────────────────────
def evaluar_umbral(tau, scores, y_true):
    pred = (scores <= tau).astype(int)
    tp = ((pred==1)&(y_true==1)).sum()
    fp = ((pred==1)&(y_true==0)).sum()
    tn = ((pred==0)&(y_true==0)).sum()
    fn = ((pred==0)&(y_true==1)).sum()
    prec = tp/(tp+fp) if (tp+fp) > 0 else 0
    rec  = tp/(tp+fn) if (tp+fn) > 0 else 0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) > 0 else 0
    fpr_v= fp/(fp+tn) if (fp+tn) > 0 else 0
    return tp, fp, tn, fn, prec, rec, f1, fpr_v

tp1,fp1,tn1,fn1,pr1,re1,f11,fpr1 = evaluar_umbral(tau1, scores_all, y_all)
tp2,fp2,tn2,fn2,pr2,re2,f12,fpr2 = evaluar_umbral(tau2, scores_all, y_all)

# Acción LIMIT: score entre τ2 y τ1
limit_count = ((scores_all > tau2) & (scores_all <= tau1) & (y_all==1)).sum()
permit_anom = (scores_all > tau1) & (y_all==1)

print(f"\n{'='*60}")
print(f"EVALUACIÓN CON TRIPLE UMBRAL")
print(f"{'='*60}")
print(f"  τ1={tau1:.4f} (LIMIT) → Recall={re1:.3f}  FPR={fpr1:.3f}  F1={f11:.3f}")
print(f"  τ2={tau2:.4f} (BLOCK) → Recall={re2:.3f}  FPR={fpr2:.3f}  F1={f12:.3f}")
print(f"  Anomalías en BLOCK : {tp2:,}")
print(f"  Anomalías en LIMIT : {limit_count:,}")
print(f"  Anomalías en PERMIT: {permit_anom.sum():,}")
print(f"{'='*60}")

# ── Gráfico ROC ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Isolation Forest — Curva ROC y Distribución de Scores\nPPI UPeU 2026",
             fontsize=13, fontweight="bold")

# Panel 1: Curva ROC
ax = axes[0]
ax.plot(fprs, tprs, color="steelblue",
        linewidth=2, label=f"ROC (AUC = {auc:.4f})")
ax.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.5, label="Aleatorio")
ax.scatter([fpr_tau1], [tpr_tau1], color="orange", s=120, zorder=5,
           label=f"τ1 LIMIT ({tau1:.3f})  TPR={tpr_tau1:.2f}")
ax.scatter([fpr_tau2], [tpr_tau2], color="crimson", s=120, zorder=5,
           label=f"τ2 BLOCK ({tau2:.3f})  TPR={tpr_tau2:.2f}")
ax.set_xlabel("Tasa de Falsos Positivos (FPR)")
ax.set_ylabel("Tasa de Verdaderos Positivos (TPR / Recall)")
ax.set_title("Curva ROC")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim([-0.02, 1.02]); ax.set_ylim([-0.02, 1.02])

# Panel 2: Distribución de scores con τ1 y τ2
ax = axes[1]
scores_n = scores_all[y_all == 0]
scores_a = scores_all[y_all == 1]
ax.hist(scores_n, bins=60, alpha=0.6, color="steelblue",
        density=True, label=f"Normal (n={len(scores_n):,})")
ax.hist(scores_a, bins=60, alpha=0.6, color="crimson",
        density=True, label=f"Anomalo (n={len(scores_a):,})")
ax.axvline(tau1, color="orange", linestyle="--", linewidth=2,
           label=f"τ1 LIMIT = {tau1:.3f}")
ax.axvline(tau2, color="darkred", linestyle="--", linewidth=2,
           label=f"τ2 BLOCK = {tau2:.3f}")
ax.axvspan(tau2, tau1, alpha=0.08, color="orange", label="Zona LIMIT")
ax.axvspan(scores_all.min()-0.1, tau2, alpha=0.08, color="red", label="Zona BLOCK")
ax.set_xlabel("Anomaly Score"); ax.set_ylabel("Densidad")
ax.set_title("Distribución de Scores y Umbrales")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.tight_layout()
fig_path = f"{FIG_DIR}/auc_roc_umbrales.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight")
print(f"\nGráfico guardado: {fig_path}")

# ── Guardar reporte τ1 τ2 ─────────────────────────────────────
hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
reporte = f"""================================================================
REPORTE AUC-ROC Y UMBRALES τ1/τ2 — FASE 3
Sistema de Detección Temprana de Anomalías de Red
PPI — Universidad Peruana Unión 2026
Generado: {hoy}
================================================================

1. AUC-ROC
----------
   AUC = {auc:.4f}
   Interpretación: el modelo distingue tráfico anómalo del
   normal con {auc*100:.1f}% de probabilidad para una muestra aleatoria.

2. UMBRALES DEFINIDOS
---------------------
   Los scores de Isolation Forest son negativos.
   Más negativo = más anómalo.

   τ1 = {tau1:.4f}  (umbral LIMIT)
     Criterio : FPR ≤ 2% con máximo TPR posible
     TPR en τ1: {tpr_tau1:.4f} ({tpr_tau1*100:.1f}%)
     FPR en τ1: {fpr_tau1:.4f} ({fpr_tau1*100:.1f}%)

   τ2 = {tau2:.4f}  (umbral BLOCK)
     Criterio : índice de Youden máximo (TPR - FPR)
     TPR en τ2: {tpr_tau2:.4f} ({tpr_tau2*100:.1f}%)
     FPR en τ2: {fpr_tau2:.4f} ({fpr_tau2*100:.1f}%)

3. LÓGICA DE DECISIÓN (3 ACCIONES)
------------------------------------
   score > τ1 ({tau1:.4f})               → PERMIT  (tráfico normal)
   τ2 ({tau2:.4f}) < score ≤ τ1 ({tau1:.4f}) → LIMIT   (sospechoso)
   score ≤ τ2 ({tau2:.4f})               → BLOCK   (anómalo confirmado)

4. EVALUACIÓN CON TRIPLE UMBRAL
---------------------------------
   τ1 (LIMIT):
     Recall (TPR) : {re1:.4f} ({re1*100:.1f}%)
     FPR          : {fpr1:.4f} ({fpr1*100:.1f}%)
     F1-Score     : {f11:.4f}

   τ2 (BLOCK):
     Recall (TPR) : {re2:.4f} ({re2*100:.1f}%)
     FPR          : {fpr2:.4f} ({fpr2*100:.1f}%)
     F1-Score     : {f12:.4f}

   Distribución de acciones sobre anomalías:
     BLOCK  : {tp2:,} flows  ({100*tp2/(tp2+limit_count+permit_anom.sum()):.1f}%)
     LIMIT  : {limit_count:,} flows  ({100*limit_count/(tp2+limit_count+permit_anom.sum()):.1f}%)
     PERMIT : {permit_anom.sum():,} flows  ({100*permit_anom.sum()/(tp2+limit_count+permit_anom.sum()):.1f}%)

5. UMBRAL ORIGINAL DEL MODELO
-------------------------------
   clf.offset_ = {clf.offset_:.4f}  (contamination=0.05)
   Este umbral equivale aproximadamente a τ2 en la lógica dual.

================================================================
"""
rpt_path = f"{REPORT_DIR}/reporte_metricas_v1.txt"
with open(rpt_path, "w") as f:
    f.write(reporte)

print(reporte)
print(f"Reporte guardado: {rpt_path}")
