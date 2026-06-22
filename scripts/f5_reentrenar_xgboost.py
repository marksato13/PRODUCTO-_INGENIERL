#!/usr/bin/env python3
"""
f5_reentrenar_xgboost.py — Reentrenamiento nocturno del predictor XGBoost (F5)

Lee   : results/motor_decision.log  (últimas 24h de eventos LIMIT+BLOCK)
Valida: AUC-ROC sobre split estratificado 20%
Produce (si AUC >= 0.70 y no retrocede > 0.05):
  models/predictor_modelo_v2.pkl        ← modelo actualizado
  models/features_predictor_v2.txt
  results/metricas_f5_xgboost.txt       ← registro de la corrida

predictor.py detecta el cambio de mtime y recarga automáticamente sin reiniciar.

Uso:
  python3 scripts/f5_reentrenar_xgboost.py
  python3 scripts/f5_reentrenar_xgboost.py --horas 48   # ventana más amplia
  python3 scripts/f5_reentrenar_xgboost.py --forzar     # reemplaza sin comparar AUC

Cron sugerido (diario 03:00):
  0 3 * * * /home/m4rk/ppi-sensor/venv/bin/python3 \
    /home/m4rk/ppi-surikata-producto/scripts/f5_reentrenar_xgboost.py \
    >> /home/m4rk/ppi-surikata-producto/results/cron_f5_xgb.log 2>&1
"""

import argparse
import bisect
import math
import os
import re
import sys
from collections import deque
from datetime import datetime, timedelta

import numpy as np
import joblib
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

BASE      = "/home/m4rk/ppi-surikata-producto"
LOG       = f"{BASE}/results/motor_decision.log"
MODEL_DIR = f"{BASE}/models"
RESULTS   = f"{BASE}/results"

MODEL_OUT  = f"{MODEL_DIR}/predictor_modelo_v2.pkl"
FEAT_OUT   = f"{MODEL_DIR}/features_predictor_v2.txt"
METRICAS   = f"{RESULTS}/metricas_f5_xgboost.txt"
METRICAS_V2 = f"{RESULTS}/metricas_predictor_v2.txt"

FEATURES = [
    'score', 'dest_port',
    'proto_tcp', 'proto_udp', 'proto_icmp',
    'hora_sin', 'hora_cos',
    'limit_count_15s', 'block_count_60s',
    'is_block',
]

RE_EVENT = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| WARNING \| '
    r'(?:ANOMAL[IÍ]A|SOSPECHOSO) \| '
    r'src=(\S+) dst=(\S+) proto=(\w+[\w-]*) '
    r'score=([-\d.]+)'
    r'[^|]*\| (BLOCK|LIMIT)'
)

TAU2 = -0.6027  # umbral BLOCK


def parse_log(path, desde_ts):
    """Lee eventos LIMIT/BLOCK del log desde `desde_ts` en adelante."""
    events = []
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            m = RE_EVENT.search(line)
            if not m:
                continue
            ts_str, src, dst, proto, score_s, decision = m.groups()
            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            if ts < desde_ts:
                continue
            dst_parts = dst.rsplit(':', 1)
            dest_port = int(dst_parts[1]) if len(dst_parts) == 2 and dst_parts[1].isdigit() else 0
            proto = proto.upper()
            events.append({
                'ts': ts,
                'src': src,
                'proto': proto,
                'score': float(score_s),
                'dest_port': dest_port,
                'decision': decision,
            })
    return events


def construir_dataset(events):
    """Genera filas de features + label automático para cada evento."""
    if not events:
        return np.empty((0, len(FEATURES))), np.array([])

    # timestamps de BLOCKs por IP para labeling eficiente
    block_ts_por_ip = {}
    for ev in events:
        if ev['decision'] == 'BLOCK':
            block_ts_por_ip.setdefault(ev['src'], []).append(ev['ts'])

    # ventanas deslizantes per-IP
    limit_wins = {}  # src → deque de timestamps (15s)
    block_wins = {}  # src → deque de timestamps (60s)

    rows_X, rows_y = [], []

    for ev in events:
        src = ev['src']
        t   = ev['ts']
        h   = t.hour + t.minute / 60.0

        # actualizar ventanas
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

        # label: ¿hay BLOCK de misma IP en próximos 60s?
        futuros = block_ts_por_ip.get(src, [])
        t_futura = t + timedelta(seconds=60)
        idx = bisect.bisect_right(futuros, t)
        label = 1 if idx < len(futuros) and futuros[idx] <= t_futura else 0

        proto_u = ev['proto']
        rows_X.append([
            ev['score'],
            ev['dest_port'],
            int(proto_u == 'TCP'),
            int(proto_u == 'UDP'),
            int(proto_u in ('ICMP', 'IPV6-ICMP')),
            math.sin(2 * math.pi * h / 24),
            math.cos(2 * math.pi * h / 24),
            len(lw),
            len(bw),
            int(ev['score'] <= TAU2),
        ])
        rows_y.append(label)

    return np.array(rows_X, dtype=np.float32), np.array(rows_y, dtype=np.int32)


def auc_modelo_actual(X_test, y_test):
    """Carga el modelo actual y calcula AUC sobre los datos de test."""
    if not os.path.exists(MODEL_OUT):
        return None
    clf = joblib.load(MODEL_OUT)
    proba = clf.predict_proba(X_test)[:, 1]
    return roc_auc_score(y_test, proba)


# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--horas', type=int, default=24,
                        help='Ventana de log a usar (default: 24h)')
    parser.add_argument('--forzar', action='store_true',
                        help='Reemplaza el modelo aunque el AUC sea menor')
    args = parser.parse_args()

    ahora = datetime.now()
    ahora_str = ahora.strftime('%Y-%m-%d %H:%M:%S')
    desde = ahora - timedelta(hours=args.horas)

    print(f"\n{'='*60}")
    print(f"F5 — Reentrenamiento XGBoost  [{ahora_str}]")
    print(f"{'='*60}")
    print(f"Ventana: últimas {args.horas}h  (desde {desde.strftime('%Y-%m-%d %H:%M')})")

    # ── [1] Leer log ──────────────────────────────────────────
    print(f"\n[1] Leyendo {LOG} ...")
    if not os.path.exists(LOG):
        print(f"ERROR: No existe {LOG}")
        sys.exit(1)

    events = parse_log(LOG, desde)
    print(f"  Eventos LIMIT+BLOCK en ventana: {len(events):,}")

    if len(events) < 100:
        print("  AVISO: Muy pocos eventos (<100) — amplia la ventana con --horas")
        sys.exit(0)

    # ── [2] Construir dataset ─────────────────────────────────
    print("\n[2] Construyendo features + labels automáticos...")
    X, y = construir_dataset(events)
    pos = int(y.sum())
    neg = len(y) - pos
    print(f"  Total: {len(X):,} | Positivos: {pos} ({100*pos/len(y):.1f}%) | Negativos: {neg}")

    if pos < 10:
        print("  AVISO: Muy pocos positivos (<10) — el modelo no puede generalizarse")
        print("  Ejecuta escenarios de ataque antes de reentrenar")
        sys.exit(0)

    # ── [3] Split estratificado ───────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # ── [4] AUC del modelo actual sobre estos datos ───────────
    auc_anterior = None
    if os.path.exists(MODEL_OUT):
        try:
            auc_anterior = auc_modelo_actual(X_test, y_test)
            print(f"\n[3] AUC modelo actual en ventana: {auc_anterior:.4f}")
        except Exception as e:
            print(f"\n[3] No se pudo evaluar modelo actual: {e}")

    # ── [5] Entrenar nuevo modelo ─────────────────────────────
    print("\n[4] Entrenando XGBoost...")
    spw = max(1, neg // max(pos, 1))

    clf_nuevo = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=spw,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1,
    )
    clf_nuevo.fit(X_train, y_train)

    # ── [6] Evaluar ───────────────────────────────────────────
    proba_test = clf_nuevo.predict_proba(X_test)[:, 1]
    auc_nuevo = roc_auc_score(y_test, proba_test)
    y_pred = (proba_test >= 0.5).astype(int)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)

    print(f"  AUC nuevo     : {auc_nuevo:.4f}")
    print(f"  Precision     : {prec:.4f}")
    print(f"  Recall        : {rec:.4f}")
    print(f"  F1            : {f1:.4f}")

    # ── [7] Decidir si reemplazar ─────────────────────────────
    if not args.forzar:
        if auc_nuevo < 0.70:
            print(f"\n  AVISO: AUC={auc_nuevo:.4f} < 0.70 — modelo NO reemplazado")
            _guardar_metricas(ahora_str, args.horas, len(events), auc_anterior, auc_nuevo, prec, rec, reemplazado=False)
            sys.exit(0)
        if auc_anterior is not None and (auc_nuevo - auc_anterior) < -0.05:
            print(f"\n  AVISO: AUC retrocedió {auc_anterior - auc_nuevo:.4f} — modelo NO reemplazado")
            print("  Usa --forzar para reemplazar de todas formas")
            _guardar_metricas(ahora_str, args.horas, len(events), auc_anterior, auc_nuevo, prec, rec, reemplazado=False)
            sys.exit(0)

    # ── [8] Guardar ───────────────────────────────────────────
    print("\n[5] Guardando modelo (predictor.py recargará automáticamente)...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf_nuevo, MODEL_OUT)
    with open(FEAT_OUT, 'w') as f:
        f.write('\n'.join(FEATURES) + '\n')
    print(f"  Guardado: {MODEL_OUT}")

    _guardar_metricas(ahora_str, args.horas, len(events), auc_anterior, auc_nuevo, prec, rec, reemplazado=True)
    print("\n✅ Reentrenamiento XGBoost completado\n")


def _guardar_metricas(ahora, horas, n_events, auc_ant, auc_nuevo, prec, rec, reemplazado):
    os.makedirs(RESULTS, exist_ok=True)
    auc_ant_s = f"{auc_ant:.4f}" if auc_ant is not None else "N/A"
    linea = (
        f"{ahora} | horas={horas} | events={n_events} | "
        f"auc_anterior={auc_ant_s} | "
        f"auc_nuevo={auc_nuevo:.4f} | "
        f"precision={prec:.4f} | recall={rec:.4f} | "
        f"reemplazado={'SI' if reemplazado else 'NO'}\n"
    )
    with open(METRICAS, 'a') as f:
        f.write(linea)
    print(f"  Métricas: {METRICAS}")


if __name__ == '__main__':
    main()
