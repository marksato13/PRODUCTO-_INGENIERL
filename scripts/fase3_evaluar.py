#!/usr/bin/env python3
"""
fase3_evaluar.py — Evaluación del modelo: ROC, umbrales τ1/τ2, métricas finales

Lee:
  models/isolation_forest.pkl + models/scaler.pkl  (de fase3_entrenar.py)
  data/normal_holdout.csv                          (20% normal reservado)
  data/raw/*_anom_*.gz                             (Grupo B — ataques puros)

Produce:
  results/metricas_offline.txt  ← fuente única de verdad: AUC, τ1, τ2, P, R, F1
  results/auc_roc.png           ← curva ROC con τ1 y τ2 marcados

Ejecutar en el sensor:
  python3 scripts/fase3_evaluar.py
"""

import glob
import gzip
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import (roc_auc_score, roc_curve,
                             precision_score, recall_score, f1_score)
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
MODEL_DIR  = f"{BASE}/models"
RESULT_DIR = f"{BASE}/results"

os.makedirs(RESULT_DIR, exist_ok=True)

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]


def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001


def parse_flows(path, exclude_ips=None, max_flows=100_000):
    """Lee eve.json(.gz) excluyendo flows de IPs normales (para leer Grupo B)."""
    events = []
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', errors='ignore') as f:
        for line in f:
            if len(events) >= max_flows:
                break
            try:
                e = json.loads(line)
                if e.get('event_type') != 'flow':
                    continue
                if exclude_ips and e.get('src_ip') in exclude_ips:
                    continue
                if (e.get('flow', {}).get('pkts_toserver', 0) or 0) == 0:
                    continue
                events.append(e)
            except Exception:
                pass
    return events


def extract_features(events):
    rows = []
    for e in events:
        flow  = e.get('flow', {})
        proto = e.get('proto', '').upper()
        dur   = flow_duration(e)
        pts   = flow.get('pkts_toserver',  0) or 0
        ptc   = flow.get('pkts_toclient',  0) or 0
        bts   = flow.get('bytes_toserver', 0) or 0
        btc   = flow.get('bytes_toclient', 0) or 0
        rows.append({
            'pkts_toserver':  pts,
            'pkts_toclient':  ptc,
            'bytes_toserver': bts,
            'bytes_toclient': btc,
            'duration':       dur,
            'pkt_rate':       (pts + ptc) / dur,
            'byte_rate':      (bts + btc) / dur,
            'pkt_ratio':      pts / (ptc + 1),
            'byte_ratio':     bts / (btc + 1),
            'avg_pkt_size':   (bts + btc) / (pts + ptc + 1),
            'is_tcp':         int(proto == 'TCP'),
            'is_udp':         int(proto == 'UDP'),
            'is_icmp':        int(proto in ('ICMP', 'IPV6-ICMP')),
            'dest_port':      e.get('dest_port', 0) or 0,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("FASE 3 — Evaluación: ROC + Umbrales + Métricas")
print("=" * 60)

# ── [1] Cargar modelo ─────────────────────────────────────────
print("\n[1] Cargando modelo y scaler...")

clf    = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")
print(f"  offset_ interno: {clf.offset_:.4f}")

# ── [2] Cargar holdout normal ─────────────────────────────────
print("\n[2] Cargando holdout normal (data/normal_holdout.csv)...")

holdout_path = f"{BASE}/data/normal_holdout.csv"
if not os.path.exists(holdout_path):
    raise FileNotFoundError(
        "No existe data/normal_holdout.csv\n"
        "Ejecuta primero: python3 scripts/fase3_entrenar.py"
    )

df_holdout = pd.read_csv(holdout_path)[FEATURES].dropna()
X_normal   = scaler.transform(df_holdout)
scores_n   = clf.score_samples(X_normal)
print(f"  Flows normales (holdout): {len(df_holdout):,}")
print(f"  Score medio normal      : {scores_n.mean():.4f} ± {scores_n.std():.4f}")

# ── [3] Cargar Grupo B (ataques) ──────────────────────────────
print("\n[3] Cargando Grupo B (anomalías)...")

archivos_b = sorted(glob.glob(f"{DATA_DIR}/*_anom_*.gz"))
if not archivos_b:
    raise FileNotFoundError(
        f"No se encontraron archivos *_anom_*.gz en {DATA_DIR}\n"
        "Ejecuta primero: bash scripts_f2/grupoB/run_grupo_B.sh 01"
    )

anom_events = []
for path in archivos_b:
    evs = parse_flows(path, exclude_ips=NORMAL_IPS)
    nombre = os.path.basename(path)
    print(f"  {nombre:55s} → {len(evs):5d} flows")
    anom_events.extend(evs)

df_anom  = extract_features(anom_events)[FEATURES].dropna()
df_anom  = df_anom[df_anom['pkts_toserver'] > 0].reset_index(drop=True)
X_anom   = scaler.transform(df_anom)
scores_a = clf.score_samples(X_anom)

print(f"\n  Total flows anómalos: {len(df_anom):,}")
print(f"  Score medio anómalo : {scores_a.mean():.4f} ± {scores_a.std():.4f}")
print(f"  Separación (δ)      : {scores_n.mean() - scores_a.mean():.4f}")

# ── [4] Curva ROC y AUC ───────────────────────────────────────
print("\n[4] Calculando curva ROC...")

# y_true: 0=normal, 1=anómalo
# y_score: negamos scores IF (más negativo IF = más anómalo → más positivo para ROC)
y_true  = np.array([0] * len(scores_n) + [1] * len(scores_a))
y_score = np.concatenate([-scores_n, -scores_a])

fpr_arr, tpr_arr, thresholds = roc_curve(y_true, y_score)
auc = roc_auc_score(y_true, y_score)
print(f"  AUC-ROC: {auc:.4f}")

# Los umbrales de sklearn sobre -scores son negativados → revertir
thresholds_if = -thresholds   # scores IF originales

# ── [5] Derivar τ1 (Youden) y τ2 (FPR ≤ 2%) ─────────────────
print("\n[5] Derivando umbrales...")

# τ1 — índice de Youden: máximo (TPR - FPR)
youden   = tpr_arr - fpr_arr
idx_tau1 = np.argmax(youden)
tau1     = float(thresholds_if[idx_tau1])
tpr_tau1 = float(tpr_arr[idx_tau1])
fpr_tau1 = float(fpr_arr[idx_tau1])

# τ2 — primer umbral donde FPR ≤ 2% con máximo TPR
candidatos = np.where(fpr_arr <= 0.02)[0]
if len(candidatos) > 0:
    idx_tau2 = candidatos[np.argmax(tpr_arr[candidatos])]
else:
    idx_tau2 = np.argmin(fpr_arr)
tau2     = float(thresholds_if[idx_tau2])
tpr_tau2 = float(tpr_arr[idx_tau2])
fpr_tau2 = float(fpr_arr[idx_tau2])

print(f"  τ1 = {tau1:.4f}  → PERMIT/LIMIT  (Youden: TPR={tpr_tau1:.1%}, FPR={fpr_tau1:.1%})")
print(f"  τ2 = {tau2:.4f}  → LIMIT/BLOCK   (FPR≤2%: TPR={tpr_tau2:.1%}, FPR={fpr_tau2:.1%})")

# ── [6] Métricas en τ1 (umbral operacional principal) ─────────
print("\n[6] Métricas de clasificación en τ1...")

# Predicción binaria con τ1: score ≤ τ1 → anómalo (1)
y_pred_n = (scores_n <= tau1).astype(int)   # FP si =1
y_pred_a = (scores_a <= tau1).astype(int)   # TP si =1

y_pred = np.concatenate([y_pred_n, y_pred_a])

precision = precision_score(y_true, y_pred, zero_division=0)
recall    = recall_score(y_true, y_pred, zero_division=0)
f1        = f1_score(y_true, y_pred, zero_division=0)
fp_count  = y_pred_n.sum()
fn_count  = (y_pred_a == 0).sum()

print(f"  Precision : {precision:.4f}  ({precision:.2%})")
print(f"  Recall    : {recall:.4f}  ({recall:.2%})")
print(f"  F1-Score  : {f1:.4f}")
print(f"  FP        : {fp_count}  (flows normales mal clasificados)")
print(f"  FN        : {fn_count}  (ataques no detectados)")

# ── [7] Guardar metricas_offline.txt ─────────────────────────
print("\n[7] Guardando results/metricas_offline.txt...")

metricas_path = f"{RESULT_DIR}/metricas_offline.txt"
timestamp     = datetime.now().strftime("%Y-%m-%d %H:%M")

with open(metricas_path, 'w') as f:
    f.write("=" * 60 + "\n")
    f.write("MÉTRICAS OFFLINE — PPI UPeU 2026\n")
    f.write(f"Generado: {timestamp}\n")
    f.write("=" * 60 + "\n\n")
    f.write("DATOS\n")
    f.write(f"  n_train_normal  : {len(df_holdout) * 4:,}  (80% usado en entrenamiento)\n")
    f.write(f"  n_holdout_normal: {len(df_holdout):,}  (20% usado en evaluación)\n")
    f.write(f"  n_anom_eval     : {len(df_anom):,}\n\n")
    f.write("MODELO\n")
    f.write(f"  algoritmo       : IsolationForest(n_estimators=300, contamination=0.05)\n")
    f.write(f"  offset_interno  : {clf.offset_:.4f}\n\n")
    f.write("CURVA ROC\n")
    f.write(f"  AUC-ROC         : {auc:.4f}\n\n")
    f.write("UMBRALES\n")
    f.write(f"  tau1            : {tau1:.4f}   # PERMIT/LIMIT — Youden\n")
    f.write(f"  tau1_tpr        : {tpr_tau1:.4f}   # TPR en tau1\n")
    f.write(f"  tau1_fpr        : {fpr_tau1:.4f}   # FPR en tau1\n")
    f.write(f"  tau2            : {tau2:.4f}   # LIMIT/BLOCK  — FPR<=2%\n")
    f.write(f"  tau2_tpr        : {tpr_tau2:.4f}   # TPR en tau2\n")
    f.write(f"  tau2_fpr        : {fpr_tau2:.4f}   # FPR en tau2\n\n")
    f.write("MÉTRICAS EN tau1\n")
    f.write(f"  precision       : {precision:.4f}\n")
    f.write(f"  recall          : {recall:.4f}\n")
    f.write(f"  f1_score        : {f1:.4f}\n")
    f.write(f"  fp              : {fp_count}\n")
    f.write(f"  fn              : {fn_count}\n\n")
    f.write("SEPARACIÓN DE SCORES\n")
    f.write(f"  score_medio_normal: {scores_n.mean():.4f} ± {scores_n.std():.4f}\n")
    f.write(f"  score_medio_anom  : {scores_a.mean():.4f} ± {scores_a.std():.4f}\n")
    f.write(f"  delta_separacion  : {scores_n.mean() - scores_a.mean():.4f}\n\n")
    f.write("ACTUALIZAR EN motor_decision.py:\n")
    f.write(f"  TAU1 = {tau1:.4f}   # PERMIT/LIMIT\n")
    f.write(f"  TAU2 = {tau2:.4f}   # LIMIT/BLOCK\n")
    f.write("=" * 60 + "\n")

print(f"  Guardado: {metricas_path}")

# ── [8] Gráfico ROC ───────────────────────────────────────────
print("\n[8] Generando curva ROC...")

fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(fpr_arr, tpr_arr, 'b-', linewidth=2, label=f'IF (AUC={auc:.4f})')
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Aleatorio (AUC=0.5)')

ax.scatter([fpr_tau1], [tpr_tau1], color='green', s=100, zorder=5,
           label=f'τ1={tau1:.4f} (Youden, TPR={tpr_tau1:.1%})')
ax.scatter([fpr_tau2], [tpr_tau2], color='orange', s=100, zorder=5,
           label=f'τ2={tau2:.4f} (FPR≤2%, TPR={tpr_tau2:.1%})')

ax.set_xlabel('Tasa de Falsos Positivos (FPR)')
ax.set_ylabel('Tasa de Verdaderos Positivos (TPR / Recall)')
ax.set_title('Curva ROC — Isolation Forest | PPI UPeU 2026')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
ax.set_xlim([0, 1])
ax.set_ylim([0, 1.02])

roc_path = f"{RESULT_DIR}/auc_roc.png"
plt.tight_layout()
plt.savefig(roc_path, dpi=150)
plt.close()
print(f"  Guardado: {roc_path}")

# ── Resumen final ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("✓ Evaluación completada.")
print(f"  AUC-ROC   : {auc:.4f}")
print(f"  τ1        : {tau1:.4f}  (PERMIT/LIMIT)")
print(f"  τ2        : {tau2:.4f}  (LIMIT/BLOCK)")
print(f"  Precision : {precision:.4f}")
print(f"  Recall    : {recall:.4f}")
print(f"  F1        : {f1:.4f}")
print("")
print("  Actualizar en motor_decision.py:")
print(f"    TAU1 = {tau1:.4f}")
print(f"    TAU2 = {tau2:.4f}")
print("")
print("  Ejecutar a continuación: python3 scripts/auc_por_escenario.py")
print("=" * 60)
