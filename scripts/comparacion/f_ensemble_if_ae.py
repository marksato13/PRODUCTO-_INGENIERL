#!/usr/bin/env python3
"""
f_ensemble_if_ae.py — FASE 7: Ensemble IF + Autoencoder

Lee:
  models/isolation_forest.pkl + models/scaler.pkl
  data/X_train_sup.npy + data/y_train_sup.npy
  data/X_test.npy + data/y_test.npy

Produce:
  models/autoencoder.pkl
  results/comparacion/07_ensemble_resultados.txt
  results/comparacion/graficas/07_01_roc_ensemble.png
  results/comparacion/graficas/07_02_fpr_recall_tradeoff.png

Estrategias de ensemble evaluadas:
  A) AND gate  — anomalía solo si AMBOS coinciden (reduce FPR)
  B) OR gate   — anomalía si CUALQUIERA detecta (aumenta Recall)
  C) Promedio  — score combinado α×IF + (1-α)×AE

Ejecutar:
  /home/m4rk/ppi-sensor/venv/bin/python3 scripts/comparacion/f_ensemble_if_ae.py
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (roc_auc_score, roc_curve,
                             precision_score, recall_score, f1_score)
from sklearn.neural_network import MLPRegressor

warnings.filterwarnings('ignore')

BASE     = "/home/m4rk/ppi-surikata-producto"
OUT_DIR  = f"{BASE}/results/comparacion"
GRAF_DIR = f"{OUT_DIR}/graficas"
LOG_FILE = f"{OUT_DIR}/07_ensemble_resultados.txt"

os.makedirs(GRAF_DIR, exist_ok=True)

class Tee:
    def __init__(self, path):
        self.f = open(path, 'w')
        self.stdout = sys.stdout
    def write(self, s): self.stdout.write(s); self.f.write(s)
    def flush(self): self.stdout.flush(); self.f.flush()
    def close(self): self.f.close()

tee = Tee(LOG_FILE)
sys.stdout = tee

SEP = "=" * 72
print(SEP)
print("FASE 7 — ENSEMBLE IF + AUTOENCODER")
print(f"PPI UPeU 2026  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# ─── Cargar datos ─────────────────────────────────────────────
print("\n[1] Cargando datos y modelos...")
X_test      = np.load(f"{BASE}/data/X_test.npy")
y_test      = np.load(f"{BASE}/data/y_test.npy")
X_train_sup = np.load(f"{BASE}/data/X_train_sup.npy")
y_train_sup = np.load(f"{BASE}/data/y_train_sup.npy")
X_train_normal = X_train_sup[y_train_sup == 0]

clf_if  = joblib.load(f"{BASE}/models/isolation_forest.pkl")
scaler  = joblib.load(f"{BASE}/models/scaler.pkl")
print(f"  X_test: {X_test.shape}  |  X_train_normal: {X_train_normal.shape}")

# ─── Entrenar / cargar Autoencoder ────────────────────────────
ae_path = f"{BASE}/models/autoencoder.pkl"
print("\n[2] Entrenando Autoencoder (14→10→7→10→14)...")
t0 = time.perf_counter()
ae = MLPRegressor(
    hidden_layer_sizes=(10, 7, 10),
    activation='relu', solver='adam',
    learning_rate_init=0.001, max_iter=200,
    random_state=42, tol=1e-4,
    early_stopping=True, validation_fraction=0.1,
    n_iter_no_change=10,
)
ae.fit(X_train_normal, X_train_normal)
t_ae = time.perf_counter() - t0
joblib.dump(ae, ae_path)
print(f"  Entrenado en {t_ae:.1f}s ({ae.n_iter_} iter) → guardado en models/autoencoder.pkl")

# ─── Scores individuales en test set ──────────────────────────
print("\n[3] Computando scores en test set...")

# IF: score más negativo = más anómalo
scores_if  = clf_if.score_samples(X_test)      # [-1, 0], menor = más anómalo

# AE: MSE más alto = más anómalo
recon_test = ae.predict(X_test)
scores_ae  = np.mean((X_test - recon_test)**2, axis=1)   # [0, ∞), mayor = más anómalo

# Normalizar ambos a [0, 1] donde 1 = más anómalo
def minmax(x):
    mn, mx = x.min(), x.max()
    return (x - mn) / (mx - mn + 1e-12)

# IF normalizado: invertir (más negativo → más anómalo → 1)
s_if_norm = minmax(-scores_if)   # alto = anómalo
s_ae_norm = minmax(scores_ae)    # alto = anómalo

print(f"  IF score  — media normal: {scores_if[y_test==0].mean():.4f}  "
      f"media anom: {scores_if[y_test==1].mean():.4f}")
print(f"  AE score  — media normal: {scores_ae[y_test==0].mean():.4f}  "
      f"media anom: {scores_ae[y_test==1].mean():.4f}")

# ─── Función de métricas con umbral ───────────────────────────
def metrics_at_threshold(scores, y_true, tau):
    y_pred = (scores >= tau).astype(int)
    tp = ((y_pred==1)&(y_true==1)).sum()
    fp = ((y_pred==1)&(y_true==0)).sum()
    fn = ((y_pred==0)&(y_true==1)).sum()
    tn = ((y_pred==0)&(y_true==0)).sum()
    recall = tp/(tp+fn) if (tp+fn) > 0 else 0
    prec   = tp/(tp+fp) if (tp+fp) > 0 else 0
    fpr    = fp/(fp+tn) if (fp+tn) > 0 else 0
    f1     = 2*prec*recall/(prec+recall) if (prec+recall)>0 else 0
    return {'recall':recall,'precision':prec,'fpr':fpr,'f1':f1,'tp':int(tp),'fp':int(fp),'fn':int(fn)}

def find_youden(scores, y_true):
    fpr_arr, tpr_arr, thr = roc_curve(y_true, scores)
    auc = roc_auc_score(y_true, scores)
    idx = np.argmax(tpr_arr - fpr_arr)
    return float(thr[idx]), float(tpr_arr[idx]), float(fpr_arr[idx]), auc, fpr_arr, tpr_arr

# ─── Métricas de modelos individuales ─────────────────────────
tau_if, tpr_if, fpr_if, auc_if, fpr_arr_if, tpr_arr_if = find_youden(s_if_norm, y_test)
tau_ae, tpr_ae, fpr_ae, auc_ae, fpr_arr_ae, tpr_arr_ae = find_youden(s_ae_norm, y_test)

m_if = metrics_at_threshold(s_if_norm, y_test, tau_if)
m_ae = metrics_at_threshold(s_ae_norm, y_test, tau_ae)

print(f"\n  IF  solo: AUC={auc_if:.4f}  Recall={m_if['recall']:.4f}  FPR={m_if['fpr']:.4f}  F1={m_if['f1']:.4f}")
print(f"  AE  solo: AUC={auc_ae:.4f}  Recall={m_ae['recall']:.4f}  FPR={m_ae['fpr']:.4f}  F1={m_ae['f1']:.4f}")

# ─── [A] AND gate ─────────────────────────────────────────────
print("\n[4] Estrategia A — AND gate (anomalía si AMBOS coinciden)...")

# AND: score combinado = min(IF, AE) → anómalo solo si ambos altos
s_and = np.minimum(s_if_norm, s_ae_norm)
tau_and, tpr_and, fpr_and_val, auc_and, fpr_arr_and, tpr_arr_and = find_youden(s_and, y_test)
m_and = metrics_at_threshold(s_and, y_test, tau_and)

print(f"  AND: AUC={auc_and:.4f}  Recall={m_and['recall']:.4f}  FPR={m_and['fpr']:.4f}  F1={m_and['f1']:.4f}")
print(f"  FPR reduction vs IF: {m_if['fpr']-m_and['fpr']:+.4f}  ({(m_if['fpr']-m_and['fpr'])/m_if['fpr']*100:.1f}% menos FP)")
print(f"  Recall change vs IF: {m_and['recall']-m_if['recall']:+.4f}")

# ─── [B] OR gate ──────────────────────────────────────────────
print("\n[5] Estrategia B — OR gate (anomalía si CUALQUIERA detecta)...")
s_or = np.maximum(s_if_norm, s_ae_norm)
tau_or, tpr_or, fpr_or_val, auc_or, fpr_arr_or, tpr_arr_or = find_youden(s_or, y_test)
m_or = metrics_at_threshold(s_or, y_test, tau_or)

print(f"  OR:  AUC={auc_or:.4f}  Recall={m_or['recall']:.4f}  FPR={m_or['fpr']:.4f}  F1={m_or['f1']:.4f}")
print(f"  FPR change vs IF: {m_if['fpr']-m_or['fpr']:+.4f}")
print(f"  Recall change vs IF: {m_or['recall']-m_if['recall']:+.4f}")

# ─── [C] Promedio ponderado — sweep de alpha ─────────────────
print("\n[6] Estrategia C — Promedio ponderado (sweep α)...")
print(f"  {'α_IF':>6s}  {'α_AE':>6s}  {'AUC':>7s}  {'Recall':>7s}  {'FPR':>7s}  {'F1':>7s}")
print(f"  {'-'*6}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*7}")

best_avg = None
results_avg = []
for alpha in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    s_avg = alpha * s_if_norm + (1-alpha) * s_ae_norm
    tau_a, _, _, auc_a, _, _ = find_youden(s_avg, y_test)
    m_a = metrics_at_threshold(s_avg, y_test, tau_a)
    print(f"  {alpha:.1f}    {1-alpha:.1f}    {auc_a:.4f}   {m_a['recall']:.4f}   "
          f"{m_a['fpr']:.4f}   {m_a['f1']:.4f}")
    results_avg.append((alpha, auc_a, m_a['recall'], m_a['fpr'], m_a['f1'], s_avg))
    # Mejor: maximizar F1 con Recall ≥ 0.95
    if m_a['recall'] >= 0.95 and (best_avg is None or m_a['f1'] > best_avg[4]):
        best_avg = (alpha, auc_a, m_a['recall'], m_a['fpr'], m_a['f1'], s_avg)

if best_avg:
    alpha_best = best_avg[0]
    print(f"\n  Mejor α (Recall≥95%, max F1): α_IF={alpha_best:.1f}, α_AE={1-alpha_best:.1f}")
    print(f"  AUC={best_avg[1]:.4f}  Recall={best_avg[2]:.4f}  FPR={best_avg[3]:.4f}  F1={best_avg[4]:.4f}")
    s_best_avg = best_avg[5]
    _, _, _, auc_bavg, fpr_arr_bavg, tpr_arr_bavg = find_youden(s_best_avg, y_test)
else:
    alpha_best = 0.6
    s_best_avg = 0.6*s_if_norm + 0.4*s_ae_norm
    _, _, _, auc_bavg, fpr_arr_bavg, tpr_arr_bavg = find_youden(s_best_avg, y_test)

# ─── Tabla resumen final ──────────────────────────────────────
print(f"\n{SEP}")
print("RESUMEN COMPARATIVO")
print(SEP)

print(f"\n  {'Modelo/Estrategia':>22s}  {'AUC':>7s}  {'Recall':>7s}  {'FPR':>7s}  {'F1':>7s}  {'ΔFPR vs IF':>11s}")
print(f"  {'-'*22}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*11}")

configs = [
    ('IF solo',         auc_if,  m_if['recall'],  m_if['fpr'],      m_if['f1'],   0),
    ('AE solo',         auc_ae,  m_ae['recall'],  m_ae['fpr'],      m_ae['f1'],   m_if['fpr']-m_ae['fpr']),
    ('Ensemble AND',    auc_and, m_and['recall'], m_and['fpr'],     m_and['f1'],  m_if['fpr']-m_and['fpr']),
    ('Ensemble OR',     auc_or,  m_or['recall'],  m_or['fpr'],      m_or['f1'],   m_if['fpr']-m_or['fpr']),
]
if best_avg:
    tau_bavg_val, _, _, _, _, _ = find_youden(s_best_avg, y_test)
    m_bavg = metrics_at_threshold(s_best_avg, y_test, tau_bavg_val)
    configs.append((f'Ensemble α={alpha_best:.1f}+{1-alpha_best:.1f}',
                    auc_bavg, m_bavg['recall'], m_bavg['fpr'], m_bavg['f1'], m_if['fpr']-m_bavg['fpr']))

for nombre, auc, rec, fpr, f1, dfpr in configs:
    direction = '↓' if dfpr > 0 else ('↑' if dfpr < 0 else '—')
    print(f"  {nombre:>22s}  {auc:.4f}   {rec:.4f}   {fpr:.4f}   {f1:.4f}   "
          f"{direction}{abs(dfpr):.4f} ({abs(dfpr)/m_if['fpr']*100:.1f}%)")

# Cuál estrategia se recomienda
fpr_and = m_and['fpr']
rec_and = m_and['recall']
fpr_red = (m_if['fpr'] - fpr_and) / m_if['fpr'] * 100
rec_cost = (m_if['recall'] - rec_and) / m_if['recall'] * 100

print(f"\n  RECOMENDACIÓN:")
print(f"  Ensemble AND reduce FPR en {fpr_red:.1f}% ({m_if['fpr']:.4f}→{fpr_and:.4f})")
print(f"  a costa de reducir Recall en {rec_cost:.1f}% ({m_if['recall']:.4f}→{rec_and:.4f})")
if rec_and >= 0.95:
    print(f"  → Recall={rec_and:.4f} ≥ 0.95: VIABLE para producción")
else:
    print(f"  → Recall={rec_and:.4f} < 0.95: riesgo para producción, considerar OR o promedio")

# ─── FIGURA 1 — ROC comparison ────────────────────────────────
print(f"\n[7] Generando gráficas...")
plt.rcParams.update({'font.size': 11, 'axes.titlesize': 13})

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(fpr_arr_if,   tpr_arr_if,   'b-',  lw=2.5, label=f'IF solo       (AUC={auc_if:.4f})')
ax.plot(fpr_arr_ae,   tpr_arr_ae,   'g--', lw=1.8, label=f'AE solo       (AUC={auc_ae:.4f})')
ax.plot(fpr_arr_and,  tpr_arr_and,  'r-',  lw=2.0, label=f'AND ensemble  (AUC={auc_and:.4f})')
ax.plot(fpr_arr_or,   tpr_arr_or,   'm--', lw=1.8, label=f'OR ensemble   (AUC={auc_or:.4f})')
ax.plot(fpr_arr_bavg, tpr_arr_bavg, 'c:',  lw=1.8,
        label=f'Promedio α={alpha_best:.1f} (AUC={auc_bavg:.4f})')
ax.plot([0,1],[0,1],'k--',lw=1,alpha=0.4,label='Aleatorio')

# Punto de operación IF (τ1)
ax.scatter([m_if['fpr']],  [m_if['recall']],  color='blue',   s=150, zorder=6, marker='o')
ax.scatter([m_and['fpr']], [m_and['recall']], color='red',    s=150, zorder=6, marker='s')

ax.annotate(f'IF\nRecall={m_if["recall"]:.3f}\nFPR={m_if["fpr"]:.3f}',
            (m_if['fpr']+0.01, m_if['recall']-0.05), fontsize=8, color='blue')
ax.annotate(f'AND\nRecall={m_and["recall"]:.3f}\nFPR={m_and["fpr"]:.3f}',
            (m_and['fpr']+0.01, m_and['recall']-0.08), fontsize=8, color='red')

ax.set_xlabel('Tasa de Falsos Positivos (FPR)')
ax.set_ylabel('Tasa de Verdaderos Positivos (Recall)')
ax.set_title('ROC — IF solo vs Estrategias de Ensemble\nPPI UPeU 2026')
ax.legend(loc='lower right', fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim([0,1]); ax.set_ylim([0,1.02])
plt.tight_layout()
p1 = f"{GRAF_DIR}/07_01_roc_ensemble.png"
plt.savefig(p1, dpi=300, bbox_inches='tight')
plt.close()
print(f"  → {p1}")

# ─── FIGURA 2 — FPR vs Recall tradeoff ────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
alphas   = [r[0] for r in results_avg]
fprs_avg = []
recs_avg = []
for alpha, _, _, _, _, s_a in results_avg:
    tau_a, _, _, _, _, _ = find_youden(s_a, y_test)
    m_a = metrics_at_threshold(s_a, y_test, tau_a)
    fprs_avg.append(m_a['fpr'])
    recs_avg.append(m_a['recall'])

ax.plot(fprs_avg, recs_avg, 'c-o', lw=2, markersize=8, label='Promedio α_IF=0.3..0.8')
for i, alpha in enumerate(alphas):
    ax.annotate(f'α={alpha:.1f}', (fprs_avg[i]+0.002, recs_avg[i]-0.008), fontsize=8, color='teal')

ax.scatter([m_if['fpr']],  [m_if['recall']],  s=200, color='blue',  zorder=6, marker='*', label=f'IF solo (FPR={m_if["fpr"]:.4f})')
ax.scatter([m_and['fpr']], [m_and['recall']], s=200, color='red',   zorder=6, marker='s', label=f'AND ensemble (FPR={m_and["fpr"]:.4f})')
ax.scatter([m_ae['fpr']],  [m_ae['recall']],  s=200, color='green', zorder=6, marker='^', label=f'AE solo (FPR={m_ae["fpr"]:.4f})')

ax.axhline(0.95, color='gray', ls='--', lw=1, label='Recall mínimo aceptable (95%)')
ax.set_xlabel('Tasa de Falsos Positivos (FPR) — menor es mejor →')
ax.set_ylabel('Recall — mayor es mejor ↑')
ax.set_title('Tradeoff FPR vs Recall — Estrategias de Ensemble\nPPI UPeU 2026')
ax.legend(loc='lower left', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
p2 = f"{GRAF_DIR}/07_02_fpr_recall_tradeoff.png"
plt.savefig(p2, dpi=300, bbox_inches='tight')
plt.close()
print(f"  → {p2}")

print(f"\n{SEP}")
print(f"Log: {LOG_FILE}")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

sys.stdout = tee.stdout
tee.close()
print(f"\n✓ FASE 7 completa.")
