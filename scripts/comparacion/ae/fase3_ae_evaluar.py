#!/usr/bin/env python3
"""
F3-AE — Evaluar Autoencoder: ROC, τ1_ae, τ2_ae, AUC por escenario.
Filtro Grupo B: src_ip NOT IN {192.168.0.20, 192.168.0.120} (igual que fase3_evaluar.py del IF).
Salida: results/ae/ae_metricas_offline.txt  +  ae_auc_roc.png  +  ae_por_escenario.txt
"""
import os, gzip, json, glob
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.metrics import roc_curve, auc as sk_auc

ROOT    = '/home/m4rk/ppi-surikata-producto'
RAW_DIR = os.path.join(ROOT, 'data/raw')
AE_DIR  = os.path.join(ROOT, 'models/ae')
OUT_DIR = os.path.join(ROOT, 'results/ae')

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES = [
    'pkts_toserver','pkts_toclient','bytes_toserver','bytes_toclient',
    'duration','pkt_rate','byte_rate','pkt_ratio','byte_ratio',
    'avg_pkt_size','is_tcp','is_udp','is_icmp','dest_port',
]

def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z','+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z','+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except:
        return 0.001

def parse_flows(path, exclude_ips=None, max_flows=100_000):
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
                events.append(e)
            except:
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
            'is_icmp':        int(proto in ('ICMP','IPV6-ICMP')),
            'dest_port':      e.get('dest_port', 0) or 0,
        })
    return pd.DataFrame(rows)

def score_ae(ae, scaler, events):
    if not events:
        return np.array([])
    df   = extract_features(events)[FEATURES].dropna()
    df   = df[df['pkts_toserver'] > 0]
    if df.empty:
        return np.array([])
    X    = df.values.astype(np.float32)
    Xs   = scaler.transform(X)
    Xhat = ae.predict(Xs)
    mse  = np.mean((Xs - Xhat)**2, axis=1)
    return -mse   # convenio: menor = más anómalo

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("F3-AE — Evaluación ROC + umbrales")
print("=" * 60)

ae     = joblib.load(os.path.join(AE_DIR, 'ae_autoencoder.pkl'))
scaler = joblib.load(os.path.join(AE_DIR, 'ae_scaler.pkl'))
scores_normal = np.load(os.path.join(AE_DIR, 'ae_scores_normal.npy'))

print(f"\nHoldout normal: {len(scores_normal)} flows")
print(f"  media={scores_normal.mean():.4f}  std={scores_normal.std():.4f}")

# ── Grupo B ────────────────────────────────────────────────────────────────
gz_anom = sorted(glob.glob(os.path.join(RAW_DIR, '*_anom_*.gz')))
print(f"\n[1] Punteando Grupo B — {len(gz_anom)} archivos")

scores_anom = []
for gz in gz_anom:
    evs = parse_flows(gz, exclude_ips=NORMAL_IPS)
    sc  = score_ae(ae, scaler, evs)
    scores_anom.extend(sc.tolist())
    if len(sc):
        print(f"  {os.path.basename(gz):55s} → {len(sc):6d} flows  score={sc.mean():.4f}")

scores_anom = np.array(scores_anom)
print(f"\nTotal anómalos: {len(scores_anom)}")
print(f"  media={scores_anom.mean():.4f}  std={scores_anom.std():.4f}")

# ── ROC ────────────────────────────────────────────────────────────────────
all_scores = np.concatenate([scores_normal, scores_anom])
all_labels = np.concatenate([np.zeros(len(scores_normal)), np.ones(len(scores_anom))])

fpr, tpr, thresholds = roc_curve(all_labels, -all_scores)
auc_val = sk_auc(fpr, tpr)
print(f"\n[2] AUC-ROC: {auc_val:.4f}")

# ── τ1: índice de Youden ───────────────────────────────────────────────────
j      = tpr - fpr
idx_t1 = np.argmax(j)
tau1   = -thresholds[idx_t1]
tpr_t1 = tpr[idx_t1]
fpr_t1 = fpr[idx_t1]
print(f"    τ1 (Youden)  = {tau1:.4f}  TPR={tpr_t1*100:.2f}%  FPR={fpr_t1*100:.2f}%")

# ── τ2: FPR ≤ 2% ──────────────────────────────────────────────────────────
mask   = fpr <= 0.02
idx_t2 = np.where(mask)[0][-1] if mask.any() else 0
tau2   = -thresholds[idx_t2]
tpr_t2 = tpr[idx_t2]
fpr_t2 = fpr[idx_t2]
print(f"    τ2 (FPR≤2%)  = {tau2:.4f}  TPR={tpr_t2*100:.2f}%  FPR={fpr_t2*100:.2f}%")

# ── Precision / Recall / F1 ────────────────────────────────────────────────
pred = (all_scores <= tau1).astype(int)
TP = int(np.sum((pred == 1) & (all_labels == 1)))
FP = int(np.sum((pred == 1) & (all_labels == 0)))
FN = int(np.sum((pred == 0) & (all_labels == 1)))
prec = TP / (TP + FP + 1e-10)
rec  = TP / (TP + FN + 1e-10)
f1   = 2 * prec * rec / (prec + rec + 1e-10)
print(f"    Precision={prec*100:.2f}%  Recall={rec*100:.2f}%  F1={f1:.4f}")

# ── guardar metricas ───────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
met = os.path.join(OUT_DIR, 'ae_metricas_offline.txt')
with open(met, 'w') as f:
    f.write(f"modelo=AE\n")
    f.write(f"backend=MLPRegressor_sklearn\n")
    f.write(f"arquitectura=14-8-4-8-14_relu_adam\n")
    f.write(f"AUC={auc_val:.4f}\n")
    f.write(f"tau1={tau1:.4f}\n")
    f.write(f"tau1_TPR={tpr_t1:.4f}\n")
    f.write(f"tau1_FPR={fpr_t1:.4f}\n")
    f.write(f"tau2={tau2:.4f}\n")
    f.write(f"tau2_TPR={tpr_t2:.4f}\n")
    f.write(f"tau2_FPR={fpr_t2:.4f}\n")
    f.write(f"precision={prec:.4f}\n")
    f.write(f"recall={rec:.4f}\n")
    f.write(f"f1={f1:.4f}\n")
    f.write(f"n_train={len(scores_normal)}\n")
    f.write(f"n_anom={len(scores_anom)}\n")
print(f"\n[3] Guardado: {met}")

# ── gráfica ────────────────────────────────────────────────────────────────
try:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, 'b-', lw=2, label=f'AE (AUC={auc_val:.4f})')
    plt.scatter([fpr_t1],[tpr_t1], c='green', s=120, zorder=5,
                label=f'τ1={tau1:.4f}  TPR={tpr_t1*100:.1f}%  FPR={fpr_t1*100:.1f}%')
    plt.scatter([fpr_t2],[tpr_t2], c='red', s=120, zorder=5,
                label=f'τ2={tau2:.4f}  TPR={tpr_t2*100:.1f}%  FPR={fpr_t2*100:.1f}%')
    plt.plot([0,1],[0,1],'k--',alpha=0.4)
    plt.xlabel('FPR'); plt.ylabel('TPR')
    plt.title('Curva ROC — Autoencoder (MLPRegressor 14→8→4→8→14)')
    plt.legend(loc='lower right', fontsize=9)
    plt.tight_layout()
    png = os.path.join(OUT_DIR, 'ae_auc_roc.png')
    plt.savefig(png, dpi=150); plt.close()
    print(f"    Gráfica: {png}")
except Exception as e:
    print(f"    [aviso] matplotlib: {e}")

# ── AUC por escenario ──────────────────────────────────────────────────────
print("\n[4] AUC por escenario Grupo B:")
rep = os.path.join(OUT_DIR, 'ae_por_escenario.txt')
n_h = len(scores_normal)
with open(rep, 'w') as rp:
    rp.write("escenario,n_flows,auc\n")
    for gz in gz_anom:
        evs = parse_flows(gz, exclude_ips=NORMAL_IPS)
        sc  = score_ae(ae, scaler, evs)
        if not len(sc):
            continue
        all_s2 = np.concatenate([scores_normal, sc])
        all_l2 = np.concatenate([np.zeros(n_h), np.ones(len(sc))])
        fp2,tp2,_ = roc_curve(all_l2, -all_s2)
        auc2 = sk_auc(fp2, tp2)
        name = os.path.basename(gz)
        print(f"  {name:55s} {len(sc):6d} flows  AUC={auc2:.4f}")
        rp.write(f"{name},{len(sc)},{auc2:.4f}\n")

print(f"\nReporte: {rep}")
print("\n=== F3-AE evaluación completada ===")
