#!/usr/bin/env python3
"""
Fase 3 — Modelado offline: Isolation Forest para detección de anomalías de red
Dataset: eventos flow de Suricata eve.json (Grupo A normal, Grupo B anómalo)
"""

import json
import gzip
import glob
import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data/raw"
MODEL_DIR  = "/home/m4rk/ppi-surikata-producto/models"
RESULT_DIR = "/home/m4rk/ppi-surikata-producto/results"

os.makedirs(MODEL_DIR,  exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}   # Desktop y Servidor
ANOM_IPS   = {'192.168.0.100'}                    # Kali

def parse_flows(path, max_flows=50_000, src_filter=None):
    """Lee un eve.json(.gz) y devuelve solo eventos de tipo 'flow'.
    src_filter: set de IPs permitidas en src_ip (None = sin filtro).
    Evita contaminación: el eve.json acumula TODO el tráfico, incluyendo
    escenarios anómalos que se ejecutaron después de los normales."""
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


def flow_duration(e):
    """Duración del flow en segundos (mínimo 0.001)."""
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001


def extract_features(events):
    """Construye DataFrame de features por flow."""
    rows = []
    for e in events:
        flow  = e.get('flow', {})
        proto = e.get('proto', '').upper()
        dur   = flow_duration(e)

        pts  = flow.get('pkts_toserver',  0) or 0
        ptc  = flow.get('pkts_toclient',  0) or 0
        bts  = flow.get('bytes_toserver', 0) or 0
        btc  = flow.get('bytes_toclient', 0) or 0

        rows.append({
            'pkts_toserver':  pts,
            'pkts_toclient':  ptc,
            'bytes_toserver': bts,
            'bytes_toclient': btc,
            'duration':       dur,
            'pkt_rate':       (pts + ptc) / dur,
            'byte_rate':      (bts + btc) / dur,
            'pkt_ratio':      pts / (ptc + 1),        # asimetría de paquetes
            'byte_ratio':     bts / (btc + 1),        # asimetría de bytes
            'avg_pkt_size':   (bts + btc) / (pts + ptc + 1),
            'is_tcp':         int(proto == 'TCP'),
            'is_udp':         int(proto == 'UDP'),
            'is_icmp':        int(proto in ('ICMP', 'IPV6-ICMP')),
            'dest_port':      e.get('dest_port', 0) or 0,
        })
    return pd.DataFrame(rows)


FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]


# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("FASE 3 — Isolation Forest  |  PPI Detección de Anomalías")
print("=" * 60)

# ── 1. Cargar datos ───────────────────────────────────────────
print("\n[1] Cargando datos...")

# Agrupar archivos normales por escenario (http, ssh, transferencia, sostenido)
# para luego balancear — evita que HTTP domine el entrenamiento.
MAX_POR_ESCENARIO = 500   # cap por tipo de tráfico normal

from collections import defaultdict
normal_por_escenario = defaultdict(list)
for f in sorted(glob.glob(f"{DATA_DIR}/20260602_normal_*_eve.json.gz")):
    nombre = os.path.basename(f)
    # extraer escenario: normal_<escenario>_NN_eve.json.gz
    escenario = nombre.split('_')[2]
    evs = parse_flows(f, src_filter=NORMAL_IPS)
    print(f"    {nombre:50s} → {len(evs):5d} flows  [{escenario}]")
    normal_por_escenario[escenario].extend(evs)

normal_events = []
print(f"\n    Datos normales por escenario:")
for escenario, evs in sorted(normal_por_escenario.items()):
    print(f"      {escenario:<20s}: {len(evs):5d} flows")
    normal_events.extend(evs)

anom_events = []
for f in sorted(glob.glob(f"{DATA_DIR}/20260602_anom_*_eve.json.gz")):
    # Sin filtro src: floods con --rand-source y respuestas ICMP tienen src≠Kali
    evs = parse_flows(f, src_filter=None)
    # Excluir explícitamente flows de Desktop (tráfico normal que quedó en el eve.json)
    evs = [e for e in evs if e.get('src_ip') not in NORMAL_IPS]
    print(f"    {os.path.basename(f):50s} → {len(evs):5d} flows")
    anom_events.extend(evs)

df_n = extract_features(normal_events)[FEATURES].dropna()
df_a = extract_features(anom_events)[FEATURES].dropna()

# Filtrar flows vacíos (sin paquetes al servidor — ruido de gestión)
df_n = df_n[df_n['pkts_toserver'] > 0].reset_index(drop=True)
df_a = df_a[df_a['pkts_toserver'] > 0].reset_index(drop=True)

print(f"\n    Flows normales listos : {len(df_n):,}")
print(f"    Flows anómalos listos : {len(df_a):,}")

# ── 2. Escalado ───────────────────────────────────────────────
print("\n[2] Escalando features...")
scaler = StandardScaler()
X_n = scaler.fit_transform(df_n)
X_a = scaler.transform(df_a)

# ── 3. Entrenamiento ──────────────────────────────────────────
print("\n[3] Entrenando Isolation Forest...")
clf = IsolationForest(
    n_estimators=300,
    max_samples='auto',
    contamination=0.05,   # ~5% de ruido esperado en tráfico normal
    random_state=42,
    n_jobs=-1,
)
clf.fit(X_n)
print("    Modelo entrenado.")

# ── 4. Predicciones y métricas ────────────────────────────────
print("\n[4] Evaluando...")
pred_n = clf.predict(X_n)   # 1 = normal, -1 = anomalía
pred_a = clf.predict(X_a)

scores_n = clf.score_samples(X_n)
scores_a = clf.score_samples(X_a)

tn = (pred_n ==  1).sum()
fp = (pred_n == -1).sum()
tp = (pred_a == -1).sum()
fn = (pred_a ==  1).sum()

precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
fpr       = fp / (fp + tn) if (fp + tn) > 0 else 0.0

print(f"\n{'='*60}")
print(f"  RESULTADOS")
print(f"{'='*60}")
print(f"  Normal  → clasificado normal   (TN): {tn:6,}  ({100*tn/(tn+fp):.1f}%)")
print(f"  Normal  → clasificado anomalía (FP): {fp:6,}  ({100*fp/(tn+fp):.1f}%)")
print(f"  Anómalo → clasificado anomalía (TP): {tp:6,}  ({100*tp/(tp+fn):.1f}%)")
print(f"  Anómalo → clasificado normal   (FN): {fn:6,}  ({100*fn/(tp+fn):.1f}%)")
print(f"\n  Precisión         : {precision:.4f}")
print(f"  Recall (Detección): {recall:.4f}")
print(f"  F1-Score          : {f1:.4f}")
print(f"  Tasa Falsos Pos.  : {fpr:.4f}")
print(f"\n  Score medio normal : {scores_n.mean():.4f}  (±{scores_n.std():.4f})")
print(f"  Score medio anómalo: {scores_a.mean():.4f}  (±{scores_a.std():.4f})")
print(f"  Umbral decisión    : {clf.offset_:.4f}")
print(f"{'='*60}")

# ── 5. Guardar modelo ─────────────────────────────────────────
print("\n[5] Guardando modelo...")
joblib.dump(clf,    f"{MODEL_DIR}/isolation_forest.pkl")
joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
pd.Series(FEATURES).to_csv(f"{MODEL_DIR}/features.csv", index=False, header=False)
print(f"    Guardado en {MODEL_DIR}/")

# ── 6. Visualizaciones ────────────────────────────────────────
print("\n[6] Generando gráficos...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Isolation Forest — Detección de Anomalías de Red\nPPI UPeU 2026", fontsize=13, fontweight='bold')

# 6a. Distribución de anomaly scores
ax = axes[0, 0]
ax.hist(scores_n, bins=60, alpha=0.65, color='steelblue',
        label=f'Normal (n={len(scores_n):,})', density=True)
ax.hist(scores_a, bins=60, alpha=0.65, color='crimson',
        label=f'Anómalo (n={len(scores_a):,})', density=True)
ax.axvline(clf.offset_, color='black', linestyle='--', linewidth=1.5, label=f'Umbral ({clf.offset_:.3f})')
ax.set_xlabel('Anomaly Score')
ax.set_ylabel('Densidad')
ax.set_title('Distribución de Anomaly Scores')
ax.legend(fontsize=8)

# 6b. Packet rate vs bytes_toserver
ax = axes[0, 1]
ax.scatter(df_n['pkt_rate'].clip(0, 1000), df_n['bytes_toserver'].clip(0, 100_000),
           c='steelblue', alpha=0.2, s=4, label='Normal')
ax.scatter(df_a['pkt_rate'].clip(0, 1000), df_a['bytes_toserver'].clip(0, 100_000),
           c='crimson', alpha=0.2, s=4, label='Anómalo')
ax.set_xlabel('Packet Rate (pkt/s)')
ax.set_ylabel('Bytes to Server')
ax.set_title('Packet Rate vs Bytes to Server')
ax.legend(fontsize=8)

# 6c. Duración del flow
ax = axes[1, 0]
ax.hist(df_n['duration'].clip(0, 60), bins=50, alpha=0.65, color='steelblue',
        label='Normal', density=True)
ax.hist(df_a['duration'].clip(0, 60), bins=50, alpha=0.65, color='crimson',
        label='Anómalo', density=True)
ax.set_xlabel('Duración del flow (s, clipped 60s)')
ax.set_ylabel('Densidad')
ax.set_title('Distribución de Duración del Flow')
ax.legend(fontsize=8)

# 6d. Métricas resumen
ax = axes[1, 1]
ax.axis('off')
tabla = [
    ['Métrica', 'Valor'],
    ['Precisión',           f'{precision:.4f}'],
    ['Recall (Detección)',  f'{recall:.4f}'],
    ['F1-Score',            f'{f1:.4f}'],
    ['Tasa Falsos Positivos', f'{fpr:.4f}'],
    ['TP (anomalías detectadas)', str(tp)],
    ['FN (anomalías perdidas)',   str(fn)],
    ['FP (falsas alarmas)',       str(fp)],
    ['TN (normal correcto)',      str(tn)],
    ['Score umbral',             f'{clf.offset_:.4f}'],
    ['n_estimators',             str(clf.n_estimators)],
    ['contamination',            str(clf.contamination)],
]
t = ax.table(cellText=tabla[1:], colLabels=tabla[0],
             loc='center', cellLoc='left')
t.auto_set_font_size(False)
t.set_fontsize(9)
t.scale(1.2, 1.4)
ax.set_title('Resumen de Métricas', fontweight='bold')

plt.tight_layout()
out_png = f"{RESULT_DIR}/isolation_forest_resultado.png"
plt.savefig(out_png, dpi=150, bbox_inches='tight')
print(f"    Gráfico: {out_png}")

print("\n✓ Fase 3 completada.")
