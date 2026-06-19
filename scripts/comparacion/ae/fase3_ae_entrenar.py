#!/usr/bin/env python3
"""
F3-AE — Entrenar Autoencoder (MLPRegressor sklearn 14→8→4→8→14).
Mismos filtros que fase3_entrenar.py del IF:
  - NORMAL_IPS = {192.168.0.20, 192.168.0.120}
  - max_flows=100_000 por archivo
  - dropna + pkts_toserver > 0
  - split 80/20 random_state=42
Salida: models/ae/ae_autoencoder.pkl  +  models/ae/ae_scaler.pkl
"""
import os, gzip, json, glob, time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split

ROOT    = '/home/m4rk/ppi-surikata-producto'
RAW_DIR = os.path.join(ROOT, 'data/raw')
OUT_DIR = os.path.join(ROOT, 'models/ae')

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

def parse_flows(path, src_filter=None, max_flows=100_000):
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
                if src_filter and e.get('src_ip') not in src_filter:
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

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("F3-AE — Entrenamiento Autoencoder (MLPRegressor sklearn)")
print("=" * 60)
t0 = time.time()

# ── cargar Grupo A ────────────────────────────────────────────────────────────
archivos = sorted(glob.glob(os.path.join(RAW_DIR, '*_normal_*.gz')))
print(f"\n[1] Cargando Grupo A — {len(archivos)} archivos")

todos = []
for path in archivos:
    evs = parse_flows(path, src_filter=NORMAL_IPS)
    print(f"  {os.path.basename(path):55s} → {len(evs):5d} flows")
    todos.extend(evs)

df = extract_features(todos)[FEATURES].dropna()
df = df[df['pkts_toserver'] > 0].reset_index(drop=True)
X  = df.values.astype(np.float32)
print(f"\nX total tras filtros: {X.shape}")

# ── split 80/20 idéntico al IF ─────────────────────────────────────────────
X_train, X_holdout = train_test_split(X, test_size=0.20, random_state=42, shuffle=True)
print(f"X_train: {X_train.shape}   X_holdout: {X_holdout.shape}")

# ── StandardScaler (fit solo en 80%) ──────────────────────────────────────
scaler     = StandardScaler()
X_train_s  = scaler.fit_transform(X_train)
X_holdout_s = scaler.transform(X_holdout)

# ── Autoencoder: MLPRegressor 14→8→4→8→14 ────────────────────────────────
print("\n[2] Entrenando Autoencoder (14→8→4→8→14, relu, adam, max_iter=500)...")
ae = MLPRegressor(
    hidden_layer_sizes=(8, 4, 8),
    activation='relu',
    solver='adam',
    max_iter=500,
    random_state=42,
    n_iter_no_change=20,
    tol=1e-4,
    verbose=False,
)
ae.fit(X_train_s, X_train_s)
print(f"  Iteraciones convergidas: {ae.n_iter_}")
print(f"  Loss final (MSE train):  {ae.loss_:.6f}")

# ── scores normales en holdout ─────────────────────────────────────────────
X_hat          = ae.predict(X_holdout_s)
mse_holdout    = np.mean((X_holdout_s - X_hat)**2, axis=1)
scores_normal  = -mse_holdout   # convenio IF: menor = más anómalo
print(f"\n[3] Scores holdout normal ({len(scores_normal)} flows):")
print(f"    media={scores_normal.mean():.4f}  std={scores_normal.std():.4f}  "
      f"min={scores_normal.min():.4f}  max={scores_normal.max():.4f}")

# ── guardar ────────────────────────────────────────────────────────────────
os.makedirs(OUT_DIR, exist_ok=True)
joblib.dump(ae,     os.path.join(OUT_DIR, 'ae_autoencoder.pkl'))
joblib.dump(scaler, os.path.join(OUT_DIR, 'ae_scaler.pkl'))
np.save(os.path.join(OUT_DIR, 'ae_scores_normal.npy'), scores_normal)
np.save(os.path.join(OUT_DIR, 'ae_holdout_scaled.npy'), X_holdout_s)

elapsed = time.time() - t0
print(f"\nTiempo total: {elapsed:.1f}s")
print(f"Guardado en {OUT_DIR}/:")
print("  ae_autoencoder.pkl  ae_scaler.pkl")
print("  ae_scores_normal.npy  ae_holdout_scaled.npy")
print("\nSiguiente: python3 scripts/comparacion/ae/fase3_ae_evaluar.py")
