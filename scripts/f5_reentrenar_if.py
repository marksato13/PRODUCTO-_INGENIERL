#!/usr/bin/env python3
"""
f5_reentrenar_if.py — Reentrenamiento semanal del Isolation Forest (F5)

Lee   : data/raw/*_normal_*.gz  (Grupo A — tráfico normal etiquetado)
Valida: data/normal_holdout.csv  (partición holdout original)
Produce (si AUC no retrocede > 0.02):
  models/isolation_forest.pkl   ← modelo actualizado
  models/scaler.pkl
  models/features.csv
  results/metricas_f5_if.txt    ← registro de la corrida

Uso:
  python3 scripts/f5_reentrenar_if.py
  python3 scripts/f5_reentrenar_if.py --forzar   # reemplaza sin comparar AUC

Cron sugerido (domingos 02:00):
  0 2 * * 0 /home/m4rk/ppi-sensor/venv/bin/python3 \
    /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_if.py \
    >> /home/m4rk/ppi-surikata-producto/results/cron_f5_if.log 2>&1
"""

import argparse
import glob
import gzip
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
MODEL_DIR  = f"{BASE}/models"
RESULTS    = f"{BASE}/results"
HOLDOUT    = f"{BASE}/data/normal_holdout.csv"

MODEL_IF   = f"{MODEL_DIR}/isolation_forest.pkl"
MODEL_SC   = f"{MODEL_DIR}/scaler.pkl"
MODEL_FEAT = f"{MODEL_DIR}/features.csv"
METRICAS   = f"{RESULTS}/metricas_f5_if.txt"

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


def auc_modelo(clf, scaler, X_normal, X_anom):
    """AUC-ROC del modelo sobre normal+anomalías del holdout."""
    X = np.vstack([X_normal, X_anom])
    y = np.array([0] * len(X_normal) + [1] * len(X_anom))
    scores = -clf.decision_function(scaler.transform(X))
    return roc_auc_score(y, scores)


def auc_modelo_existente(X_normal, X_anom):
    """Carga el modelo actual y calcula su AUC."""
    clf = joblib.load(MODEL_IF)
    scaler = joblib.load(MODEL_SC)
    return auc_modelo(clf, scaler, X_normal, X_anom), clf, scaler


# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--forzar', action='store_true',
                        help='Reemplaza el modelo aunque el AUC sea menor')
    args = parser.parse_args()

    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*60}")
    print(f"F5 — Reentrenamiento IF  [{ahora}]")
    print(f"{'='*60}")

    # ── [1] Cargar datos normales ─────────────────────────────
    print("\n[1] Cargando Grupo A (normal)...")
    archivos = sorted(glob.glob(f"{DATA_DIR}/*_normal_*.gz"))
    if not archivos:
        print("ERROR: No hay archivos *_normal_*.gz en data/raw/")
        sys.exit(1)

    todos = []
    for path in archivos:
        evs = parse_flows(path, src_filter=NORMAL_IPS)
        print(f"  {os.path.basename(path):55s} → {len(evs):5d} flows")
        todos.extend(evs)

    df = extract_features(todos)[FEATURES].dropna()
    df = df[df['pkts_toserver'] > 0].reset_index(drop=True)
    print(f"  Total: {len(df):,} flows normales")

    # ── [2] Holdout de anomalías para AUC ─────────────────────
    print("\n[2] Cargando holdout para evaluar AUC...")
    if not os.path.exists(HOLDOUT):
        print("WARNING: No existe normal_holdout.csv — se salta comparación AUC")
        auc_anterior = None
        X_normal_hold = None
        X_anom_hold   = None
    else:
        df_hold = pd.read_csv(HOLDOUT)[FEATURES].dropna()

        # Anomalías: archivos no-normales del Grupo B/C
        archivos_anom = sorted(glob.glob(f"{DATA_DIR}/*_anom_*.gz"))
        evs_anom = []
        for path in archivos_anom[:3]:  # máximo 3 archivos para validación rápida
            evs_anom.extend(parse_flows(path, max_flows=5000))

        if evs_anom:
            df_anom = extract_features(evs_anom)[FEATURES].dropna()
            X_normal_hold = df_hold.values
            X_anom_hold   = df_anom.values

            if os.path.exists(MODEL_IF) and os.path.exists(MODEL_SC):
                auc_anterior, _, _ = auc_modelo_existente(X_normal_hold, X_anom_hold)
                print(f"  AUC modelo actual   : {auc_anterior:.4f}")
            else:
                auc_anterior = None
                print("  No hay modelo previo")
        else:
            auc_anterior = None
            X_normal_hold = X_anom_hold = None
            print("  No hay archivos _anom_ para validar — se salta comparación AUC")

    # ── [3] Entrenamiento nuevo ───────────────────────────────
    print("\n[3] Entrenando nuevo Isolation Forest...")
    df_train, df_holdout_nuevo = train_test_split(
        df, test_size=0.20, random_state=42, shuffle=True
    )

    scaler_nuevo = StandardScaler()
    X_train = scaler_nuevo.fit_transform(df_train[FEATURES])

    clf_nuevo = IsolationForest(
        n_estimators=300,
        max_samples='auto',
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    clf_nuevo.fit(X_train)
    print(f"  Entrenado con {len(df_train):,} flows")

    # ── [4] Evaluar nuevo modelo ──────────────────────────────
    if X_normal_hold is not None and X_anom_hold is not None:
        auc_nuevo = auc_modelo(clf_nuevo, scaler_nuevo, X_normal_hold, X_anom_hold)
        print(f"\n[4] AUC nuevo modelo    : {auc_nuevo:.4f}")
        mejora = auc_nuevo - (auc_anterior or 0)

        if not args.forzar and auc_anterior is not None and mejora < -0.02:
            print(f"  AVISO: AUC retrocedió {-mejora:.4f} — modelo NO reemplazado")
            print("  Usa --forzar para reemplazar de todas formas")
            _guardar_metricas(ahora, auc_anterior, auc_nuevo, len(df_train), reemplazado=False)
            sys.exit(0)
    else:
        auc_nuevo = None

    # ── [5] Guardar modelo ───────────────────────────────────
    print("\n[5] Guardando modelo...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf_nuevo, MODEL_IF)
    joblib.dump(scaler_nuevo, MODEL_SC)
    pd.Series(FEATURES).to_csv(MODEL_FEAT, index=False, header=False)
    print(f"  Guardado: {MODEL_IF}")
    print(f"  Guardado: {MODEL_SC}")
    print(f"  Guardado: {MODEL_FEAT}")

    _guardar_metricas(ahora, auc_anterior, auc_nuevo, len(df_train), reemplazado=True)
    print("\n✅ Reentrenamiento IF completado — motor recargará modelo automáticamente\n")


def _guardar_metricas(ahora, auc_anterior, auc_nuevo, n_flows, reemplazado):
    os.makedirs(RESULTS, exist_ok=True)
    auc_ant_s = f"{auc_anterior:.4f}" if auc_anterior is not None else "N/A"
    auc_new_s = f"{auc_nuevo:.4f}" if auc_nuevo is not None else "N/A"
    linea = (
        f"{ahora} | flows={n_flows} | "
        f"auc_anterior={auc_ant_s} | "
        f"auc_nuevo={auc_new_s} | "
        f"reemplazado={'SI' if reemplazado else 'NO'}\n"
    )
    with open(METRICAS, 'a') as f:
        f.write(linea)
    print(f"  Métricas: {METRICAS}")


if __name__ == '__main__':
    main()
