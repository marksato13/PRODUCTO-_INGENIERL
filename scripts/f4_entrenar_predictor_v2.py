#!/usr/bin/env python3
"""
f4_entrenar_predictor_v2.py — Entrenamiento XGBoost v2 con señal combinada LIMIT+BLOCK

Lee:    results/motor_decision.log
Extrae: SOSPECHOSO (LIMIT) y ANOMALÍA (BLOCK) — formato viejo y nuevo

Features (10) — disponibles en ambos formatos del log:
    score            — IF decision function
    dest_port        — puerto objetivo
    proto_tcp        — booleano
    proto_udp        — booleano
    proto_icmp       — booleano
    hora_sin         — componente temporal
    hora_cos
    limit_count_15s  — LIMITs de esta IP en últimos 15s
    block_count_60s  — BLOCKs de esta IP en últimos 60s
    is_block         — 1=BLOCK, 0=LIMIT

Label automático:
    1 = hay otro BLOCK de la misma IP en los próximos 60s (ataque sostenido)
    0 = no hay más BLOCKs en 60s (puntual / falso positivo)

Produce:
    models/predictor_modelo_v2.pkl
    models/features_predictor_v2.txt
    results/metricas_predictor_v2.txt
"""

import re
import math
import joblib
import numpy as np
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from bisect import bisect_right

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import xgboost as xgb

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE        = Path("/home/m4rk/ppi-surikata-producto")
LOG         = BASE / "results" / "motor_decision.log"
MODEL_DIR   = BASE / "models"
RESULTS_DIR = BASE / "results"
MODEL_DIR.mkdir(exist_ok=True)

# ── Features ──────────────────────────────────────────────────────────────────
FEATURES = [
    'dest_port',
    'proto_tcp', 'proto_udp', 'proto_icmp',
    'hora_sin', 'hora_cos',
    'limit_count_15s', 'block_count_60s',
    'block_rate_60s',
    'is_block',
]
# 'score' eliminado: labels derivados de score → data leakage.
# El modelo aprende patrones comportamentales puros (9 features).

# ── Regex: captura ambos formatos (viejo y nuevo) ─────────────────────────────
# Viejo: score=FLOAT | BLOCK →
# Nuevo: score=FLOAT grado=G tipo=T byte_ratio=F pkt_rate=F | BLOCK
RE_EVENT = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| WARNING \| '
    r'(?:ANOMAL[IÍ]A|SOSPECHOSO) \| '
    r'src=(\S+) dst=(\S+) proto=(\w+[\w-]*) '
    r'score=([-\d.]+)'
    r'[^|]*\| (BLOCK|LIMIT)'
)

# ── Leer log ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("F4 — Entrenamiento XGBoost v2 (señal LIMIT+BLOCK)")
print("=" * 60)
print(f"\n[1] Leyendo {LOG} ...")

events     = []
total_lines = 0

with open(LOG, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        total_lines += 1
        m = RE_EVENT.match(line)
        if not m:
            continue
        ts_str, src_ip, dst, proto, score, action = m.groups()

        try:
            dest_port = int(dst.rsplit(':', 1)[1])
        except (IndexError, ValueError):
            dest_port = 0

        # Filtrar IPs no válidas (IPv6 largas, IPs fuera de rango del lab)
        if ':' in src_ip or src_ip.startswith('0.') or src_ip.startswith('255.'):
            continue

        ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        events.append({
            'ts':       ts,
            'ts_epoch': ts.timestamp(),
            'src_ip':   src_ip,
            'proto':    proto.upper(),
            'score':    float(score),
            'dest_port': dest_port,
            'action':   action,
        })

print(f"  Líneas totales     : {total_lines:,}")
print(f"  Eventos válidos    : {len(events):,}")

if len(events) < 1000:
    raise RuntimeError(f"Muy pocos eventos ({len(events)}) — revisar log")

# Ordenar por tiempo
events.sort(key=lambda e: e['ts_epoch'])

# Índice de BLOCKs por IP para label lookup eficiente
block_ts_by_ip = defaultdict(list)
for ev in events:
    if ev['action'] == 'BLOCK':
        block_ts_by_ip[ev['src_ip']].append(ev['ts_epoch'])

n_block = sum(1 for e in events if e['action'] == 'BLOCK')
n_limit = sum(1 for e in events if e['action'] == 'LIMIT')
print(f"\n[2] Distribución:")
print(f"  BLOCK : {n_block:,}")
print(f"  LIMIT : {n_limit:,}")
print(f"  IPs únicas con BLOCK: {len(block_ts_by_ip)}")

# ── Generar features y labels ─────────────────────────────────────────────────
print("\n[3] Generando features y labels ...")

WINDOW_LIMIT   = 15   # segundos para limit_count_15s
WINDOW_BLOCK   = 60   # segundos para block_count_60s
LABEL_HORIZON  = 60   # segundos adelante para label

limit_window = defaultdict(deque)
block_window = defaultdict(deque)

rows = []
for ev in events:
    t      = ev['ts_epoch']
    ip     = ev['src_ip']
    action = ev['action']

    # Actualizar ventanas deslizantes
    if action == 'LIMIT':
        limit_window[ip].append(t)
    if action == 'BLOCK':
        block_window[ip].append(t)

    dq_l = limit_window[ip]
    while dq_l and t - dq_l[0] > WINDOW_LIMIT:
        dq_l.popleft()

    dq_b = block_window[ip]
    while dq_b and t - dq_b[0] > WINDOW_BLOCK:
        dq_b.popleft()

    # Label: ¿hay un BLOCK de esta IP en los próximos 60s?
    future = block_ts_by_ip[ip]
    idx    = bisect_right(future, t)
    label  = 1 if idx < len(future) and future[idx] <= t + LABEL_HORIZON else 0

    hora     = ev['ts'].hour + ev['ts'].minute / 60.0
    proto    = ev['proto']

    rows.append({
        'score':           ev['score'],
        'dest_port':       ev['dest_port'],
        'proto_tcp':       int(proto == 'TCP'),
        'proto_udp':       int(proto == 'UDP'),
        'proto_icmp':      int(proto in ('ICMP', 'IPV6-ICMP')),
        'hora_sin':        math.sin(2 * math.pi * hora / 24),
        'hora_cos':        math.cos(2 * math.pi * hora / 24),
        'limit_count_15s': len(dq_l),
        'block_count_60s': len(dq_b),
        'block_rate_60s':  len(dq_b) / 60.0,
        'is_block':        int(action == 'BLOCK'),
        'label':           label,
    })

df = pd.DataFrame(rows)
pos_pct = 100 * df['label'].mean()
print(f"  Dataset : {len(df):,} filas")
print(f"  Label=1 : {df['label'].sum():,}  ({pos_pct:.1f}%)")
print(f"  Label=0 : {(df['label']==0).sum():,}  ({100-pos_pct:.1f}%)")

# ── Split aleatorio estratificado 80/20 ──────────────────────────────────────
# Estratificado para garantizar representación de ambas clases en train/test.
# Los ataques del lab se concentran en días específicos — split temporal
# pondría casi todos los positivos en test, sesgando la evaluación.
# 'score' fue removido de FEATURES para eliminar data leakage.
print("\n[4] Split aleatorio estratificado 80/20 (sin score — sin leakage) ...")

X_all = df[FEATURES].values.astype(float)
y_all = df['label'].values

X_train, X_test, y_train, y_test = train_test_split(
    X_all, y_all,
    test_size=0.20,
    random_state=42,
    stratify=y_all,
)

print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")
print(f"  Positivos train: {y_train.sum():,} ({100*y_train.mean():.1f}%)")
print(f"  Positivos test : {y_test.sum():,} ({100*y_test.mean():.1f}%)")

# ── Entrenar XGBoost ──────────────────────────────────────────────────────────
print("\n[5] Entrenando XGBoost ...")

neg = (y_train == 0).sum()
pos = (y_train == 1).sum()
spw = neg / max(pos, 1)

clf = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=spw,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1,
)
clf.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=False,
)
print("  Modelo entrenado.")

# ── Evaluar ───────────────────────────────────────────────────────────────────
print("\n[6] Evaluando ...")

proba  = clf.predict_proba(X_test)[:, 1]
auc    = roc_auc_score(y_test, proba)
y_pred = (proba >= 0.50).astype(int)
report = classification_report(y_test, y_pred, digits=4)
cm     = confusion_matrix(y_test, y_pred)

print(f"  AUC-ROC : {auc:.4f}")
print(report)

fi = pd.Series(clf.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("  Feature importance:")
for feat, imp in fi.items():
    print(f"    {feat:20s}: {imp:.4f}")

# ── Guardar ───────────────────────────────────────────────────────────────────
print("\n[7] Guardando artefactos ...")

joblib.dump(clf, MODEL_DIR / "predictor_modelo_v2.pkl")
(MODEL_DIR / "features_predictor_v2.txt").write_text('\n'.join(FEATURES) + '\n')

metricas = f"""============================================================
MÉTRICAS PREDICTOR v2 — XGBoost LIMIT+BLOCK
Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}
============================================================

DATASET
  total_eventos     : {len(df):,}
  BLOCK             : {n_block:,}
  LIMIT             : {n_limit:,}
  label_1_sostenido : {int(df['label'].sum()):,}  ({pos_pct:.1f}%)
  label_0_puntual   : {int((df['label']==0).sum()):,}  ({100-pos_pct:.1f}%)
  split_train       : {len(X_train):,}
  split_test        : {len(X_test):,}

MODELO
  algoritmo         : XGBoost (n=300, depth=4, lr=0.05)
  scale_pos_weight  : {spw:.2f}
  features          : {len(FEATURES)}

MÉTRICAS (umbral=0.50)
  AUC-ROC           : {auc:.4f}

{report}
MATRIZ CONFUSIÓN
  TN={cm[0][0]:,}  FP={cm[0][1]:,}
  FN={cm[1][0]:,}  TP={cm[1][1]:,}

FEATURE IMPORTANCE
{fi.to_string()}

UMBRALES DE ALERTA
  P < 0.40          → SILENCIO
  0.40 <= P < 0.70  → AVISO (dashboard amarillo)
  P >= 0.70         → ALERTA-PREDICTIVA (rojo + Telegram)
============================================================
"""
(RESULTS_DIR / "metricas_predictor_v2.txt").write_text(metricas)

print("  models/predictor_modelo_v2.pkl")
print("  models/features_predictor_v2.txt")
print("  results/metricas_predictor_v2.txt")
print("\n" + "=" * 60)
print(f"✓ Completado. AUC-ROC = {auc:.4f}")
print("  Siguiente: modificar scripts/predictor.py para v2")
print("=" * 60)
