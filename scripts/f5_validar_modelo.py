#!/usr/bin/env python3
"""
f5_validar_modelo.py — Comparación de modelos antes de reemplazar (F5)

Evalúa el modelo actual vs un modelo candidato sobre el mismo holdout.
Útil para inspección manual antes de un reemplazo forzado.

Uso:
  python3 scripts/f5_validar_modelo.py
  python3 scripts/f5_validar_modelo.py --candidato models/predictor_modelo_v2_candidato.pkl
"""

import argparse
import glob
import gzip
import json
import os
import re
from datetime import datetime, timedelta

import numpy as np
import joblib
from sklearn.metrics import (roc_auc_score, precision_score,
                              recall_score, f1_score, confusion_matrix)

BASE      = "/home/m4rk/ppi-surikata-producto"
MODEL_DIR = f"{BASE}/models"
RESULTS   = f"{BASE}/results"

MODEL_IF      = f"{MODEL_DIR}/isolation_forest.pkl"
MODEL_SC      = f"{MODEL_DIR}/scaler.pkl"
MODEL_FEAT    = f"{MODEL_DIR}/features.csv"
MODEL_XGB     = f"{MODEL_DIR}/predictor_modelo_v2.pkl"
MODEL_XGB_FEAT = f"{MODEL_DIR}/features_predictor_v2.txt"

FEATURES_IF = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]

RE_EVENT = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| WARNING \| '
    r'(?:ANOMAL[IÍ]A|SOSPECHOSO) \| '
    r'src=(\S+) dst=(\S+) proto=(\w+[\w-]*) '
    r'score=([-\d.]+)'
    r'[^|]*\| (BLOCK|LIMIT)'
)


def print_seccion(titulo):
    print(f"\n{'─'*50}")
    print(f"  {titulo}")
    print(f"{'─'*50}")


def evaluar_if():
    """Evalúa el IF actual sobre holdout normal + anomalías."""
    print_seccion("Isolation Forest — estado actual")

    if not os.path.exists(MODEL_IF):
        print("  ✗ No existe isolation_forest.pkl")
        return

    clf    = joblib.load(MODEL_IF)
    scaler = joblib.load(MODEL_SC)

    # Holdout normal
    holdout = f"{BASE}/data/normal_holdout.csv"
    if not os.path.exists(holdout):
        print("  ✗ No existe normal_holdout.csv")
        return

    import pandas as pd
    df_norm = pd.read_csv(holdout)[FEATURES_IF].dropna()

    # Anomalías — primeros 5000 de cada archivo _anom_
    evs_anom = []
    for path in sorted(glob.glob(f"{BASE}/data/raw/*_anom_*.gz"))[:3]:
        evs_anom.extend(_parse_gz_flows(path, max_flows=2000))

    if not evs_anom:
        print("  ✗ No hay archivos _anom_*.gz para evaluar")
        return

    df_anom = _extract_features_if(evs_anom)[FEATURES_IF].dropna()

    X = np.vstack([df_norm.values, df_anom.values])
    y = np.array([0] * len(df_norm) + [1] * len(df_anom))
    scores = -clf.decision_function(scaler.transform(X))
    auc = roc_auc_score(y, scores)
    pred = clf.predict(scaler.transform(X))  # 1=normal, -1=anomalía
    y_pred_bin = (pred == -1).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, y_pred_bin).ravel()

    print(f"  AUC-ROC      : {auc:.4f}")
    print(f"  TPR (Recall) : {tp/(tp+fn):.4f}")
    print(f"  FPR          : {fp/(fp+tn):.4f}")
    print(f"  Normal hold  : {len(df_norm):,} | Anomalías: {len(df_anom):,}")


def evaluar_xgb():
    """Evalúa el XGBoost actual sobre los últimos 7 días del log."""
    print_seccion("XGBoost predictor — estado actual")

    if not os.path.exists(MODEL_XGB):
        print("  ✗ No existe predictor_modelo_v2.pkl")
        return

    clf = joblib.load(MODEL_XGB)
    log = f"{RESULTS}/motor_decision.log"
    if not os.path.exists(log):
        print(f"  ✗ No existe {log}")
        return

    desde = datetime.now() - timedelta(days=7)
    events = _parse_log(log, desde)
    print(f"  Eventos últimos 7 días: {len(events):,}")

    if len(events) < 50:
        print("  ✗ Muy pocos eventos para evaluar")
        return

    X, y = _construir_dataset(events)
    if y.sum() < 5:
        print("  ✗ Muy pocos positivos para calcular AUC")
        return

    proba = clf.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, proba)
    y_pred = (proba >= 0.5).astype(int)
    print(f"  AUC-ROC      : {auc:.4f}")
    print(f"  Precision    : {precision_score(y, y_pred, zero_division=0):.4f}")
    print(f"  Recall       : {recall_score(y, y_pred, zero_division=0):.4f}")
    print(f"  F1           : {f1_score(y, y_pred, zero_division=0):.4f}")
    print(f"  Positivos    : {int(y.sum())} / {len(y)}")


def _parse_gz_flows(path, max_flows=5000):
    events = []
    with gzip.open(path, 'rt', errors='ignore') as f:
        for line in f:
            if len(events) >= max_flows:
                break
            try:
                e = json.loads(line)
                if e.get('event_type') == 'flow':
                    events.append(e)
            except Exception:
                pass
    return events


def _extract_features_if(events):
    import pandas as pd
    from datetime import datetime as dt
    rows = []
    for e in events:
        flow  = e.get('flow', {})
        proto = e.get('proto', '').upper()
        try:
            t0 = dt.fromisoformat(flow['start'].replace('Z', '+00:00'))
            t1 = dt.fromisoformat(flow['end'].replace('Z', '+00:00'))
            dur = max((t1 - t0).total_seconds(), 0.001)
        except Exception:
            dur = 0.001
        pts = flow.get('pkts_toserver', 0) or 0
        ptc = flow.get('pkts_toclient', 0) or 0
        bts = flow.get('bytes_toserver', 0) or 0
        btc = flow.get('bytes_toclient', 0) or 0
        rows.append({
            'pkts_toserver': pts, 'pkts_toclient': ptc,
            'bytes_toserver': bts, 'bytes_toclient': btc,
            'duration': dur,
            'pkt_rate': (pts+ptc)/dur, 'byte_rate': (bts+btc)/dur,
            'pkt_ratio': pts/(ptc+1), 'byte_ratio': bts/(btc+1),
            'avg_pkt_size': (bts+btc)/(pts+ptc+1),
            'is_tcp': int(proto=='TCP'), 'is_udp': int(proto=='UDP'),
            'is_icmp': int(proto in ('ICMP','IPV6-ICMP')),
            'dest_port': e.get('dest_port', 0) or 0,
        })
    return pd.DataFrame(rows)


def _parse_log(path, desde):
    import math
    events = []
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            m = RE_EVENT.search(line)
            if not m:
                continue
            ts_str, src, dst, proto, score_s, decision = m.groups()
            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            if ts < desde:
                continue
            dst_parts = dst.rsplit(':', 1)
            dest_port = int(dst_parts[1]) if len(dst_parts)==2 and dst_parts[1].isdigit() else 0
            events.append({
                'ts': ts, 'src': src, 'proto': proto.upper(),
                'score': float(score_s), 'dest_port': dest_port,
                'decision': decision,
            })
    return events


def _construir_dataset(events):
    import bisect, math
    from collections import deque
    TAU2 = -0.6027
    block_ts_por_ip = {}
    for ev in events:
        if ev['decision'] == 'BLOCK':
            block_ts_por_ip.setdefault(ev['src'], []).append(ev['ts'])

    limit_wins, block_wins = {}, {}
    rows_X, rows_y = [], []

    for ev in events:
        src = ev['src']
        t   = ev['ts']
        h   = t.hour + t.minute / 60.0

        lw = limit_wins.setdefault(src, deque())
        bw = block_wins.setdefault(src, deque())
        cutoff_15 = t - timedelta(seconds=15)
        cutoff_60 = t - timedelta(seconds=60)
        while lw and lw[0] < cutoff_15:
            lw.popleft()
        while bw and bw[0] < cutoff_60:
            bw.popleft()
        if ev['decision'] == 'LIMIT':
            lw.append(t)
        else:
            bw.append(t)

        futuros = block_ts_por_ip.get(src, [])
        t_futura = t + timedelta(seconds=60)
        idx = bisect.bisect_right(futuros, t)
        label = 1 if idx < len(futuros) and futuros[idx] <= t_futura else 0

        proto_u = ev['proto']
        rows_X.append([
            ev['score'], ev['dest_port'],
            int(proto_u=='TCP'), int(proto_u=='UDP'),
            int(proto_u in ('ICMP','IPV6-ICMP')),
            math.sin(2*math.pi*h/24), math.cos(2*math.pi*h/24),
            len(lw), len(bw),
            int(ev['score'] <= TAU2),
        ])
        rows_y.append(label)

    return np.array(rows_X, dtype=np.float32), np.array(rows_y, dtype=np.int32)


def main():
    print(f"\n{'='*60}")
    print(f"F5 — Validación de modelos  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print(f"{'='*60}")

    evaluar_if()
    evaluar_xgb()

    # Historial de reentrenamientos
    print_seccion("Historial F5")
    for log_path in [
        f"{RESULTS}/metricas_f5_if.txt",
        f"{RESULTS}/metricas_f5_xgboost.txt",
    ]:
        nombre = os.path.basename(log_path)
        if os.path.exists(log_path):
            print(f"\n  {nombre}:")
            with open(log_path) as f:
                for line in f:
                    print(f"    {line.rstrip()}")
        else:
            print(f"\n  {nombre}: (sin registros)")

    print()


if __name__ == '__main__':
    main()
