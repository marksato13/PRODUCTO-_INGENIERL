#!/usr/bin/env python3
"""
fase3_entrenar.py — Entrenamiento del Isolation Forest (pipeline limpio)

Lee   : data/raw/*_normal_*.gz  (Grupo A — sesión dedicada, Kali apagada)
Produce:
  models/isolation_forest.pkl   ← modelo entrenado
  models/scaler.pkl             ← StandardScaler (μ/σ de flows normales)
  models/features.csv           ← lista de 14 features en orden
  data/normal_holdout.csv       ← 20% de flows normales para fase3_evaluar.py

Ejecutar en el sensor:
  python3 scripts/fase3_entrenar.py
"""

import glob
import gzip
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

# ── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
MODEL_DIR  = f"{BASE}/models"
DATA_OUT   = f"{BASE}/data"

os.makedirs(MODEL_DIR, exist_ok=True)

# ── IPs del tráfico normal (Desktop y Servidor) ──────────────
NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

# ── 14 Features (mismo orden que motor_decision.py) ──────────
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


def parse_flows(path, src_filter=None, max_flows=100_000):
    """Lee eve.json(.gz) y devuelve solo eventos flow con src_ip en src_filter."""
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
print("FASE 3 — Entrenamiento Isolation Forest")
print("=" * 60)

# ── [1] Cargar Grupo A ────────────────────────────────────────
print("\n[1] Cargando Grupo A (normal)...")

archivos = sorted(glob.glob(f"{DATA_DIR}/*_normal_*.gz"))
if not archivos:
    raise FileNotFoundError(
        f"No se encontraron archivos *_normal_*.gz en {DATA_DIR}\n"
        "Ejecuta primero: bash scripts_f2/grupoA/run_grupo_A.sh 01"
    )

todos_eventos = []
for path in archivos:
    evs = parse_flows(path, src_filter=NORMAL_IPS)
    nombre = os.path.basename(path)
    print(f"  {nombre:55s} → {len(evs):5d} flows")
    todos_eventos.extend(evs)

df = extract_features(todos_eventos)[FEATURES].dropna()
df = df[df['pkts_toserver'] > 0].reset_index(drop=True)

print(f"\n  Total flows normales cargados: {len(df):,}")

# ── [2] Split 80/20 ──────────────────────────────────────────
print("\n[2] Split 80% entrenamiento / 20% holdout...")

df_train, df_holdout = train_test_split(
    df, test_size=0.20, random_state=42, shuffle=True
)
df_train   = df_train.reset_index(drop=True)
df_holdout = df_holdout.reset_index(drop=True)

print(f"  Entrenamiento : {len(df_train):,} flows")
print(f"  Holdout       : {len(df_holdout):,} flows  → data/normal_holdout.csv")

# ── [3] Escalar ───────────────────────────────────────────────
print("\n[3] Ajustando StandardScaler sobre el 80% de entrenamiento...")

scaler = StandardScaler()
X_train = scaler.fit_transform(df_train)

print(f"  μ (media)  : {scaler.mean_[:4].round(3).tolist()} ...")
print(f"  σ (std)    : {scaler.scale_[:4].round(3).tolist()} ...")

# ── [4] Entrenar Isolation Forest ────────────────────────────
print("\n[4] Entrenando Isolation Forest...")

clf = IsolationForest(
    n_estimators=300,
    max_samples='auto',
    contamination=0.05,
    random_state=42,
    n_jobs=-1,
)
clf.fit(X_train)

scores_train = clf.score_samples(X_train)
print(f"  Modelo entrenado.")
print(f"  Score medio (train) : {scores_train.mean():.4f} ± {scores_train.std():.4f}")
print(f"  offset_ interno     : {clf.offset_:.4f}")

# ── [5] Guardar artefactos ────────────────────────────────────
print("\n[5] Guardando artefactos...")

joblib.dump(clf,    f"{MODEL_DIR}/isolation_forest.pkl")
joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
pd.Series(FEATURES).to_csv(f"{MODEL_DIR}/features.csv", index=False, header=False)

holdout_path = f"{DATA_OUT}/normal_holdout.csv"
df_holdout.to_csv(holdout_path, index=False)

print(f"  models/isolation_forest.pkl")
print(f"  models/scaler.pkl")
print(f"  models/features.csv")
print(f"  data/normal_holdout.csv  ({len(df_holdout):,} flows)")

# ── [6] Verificación rápida ───────────────────────────────────
print("\n[6] Verificación rápida sobre holdout...")

X_holdout = scaler.transform(df_holdout)
scores_holdout = clf.score_samples(X_holdout)
preds = clf.predict(X_holdout)   # 1=normal, -1=anomalía
fp = (preds == -1).sum()
fp_pct = 100 * fp / len(preds)

print(f"  Holdout normal → FP (mal clasificados): {fp}/{len(preds)} ({fp_pct:.1f}%)")
print(f"  Score medio holdout: {scores_holdout.mean():.4f} ± {scores_holdout.std():.4f}")

print("\n" + "=" * 60)
print("✓ Entrenamiento completado.")
print(f"  Ejecutar a continuación: python3 scripts/fase3_evaluar.py")
print("=" * 60)
