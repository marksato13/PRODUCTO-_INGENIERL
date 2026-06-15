#!/usr/bin/env python3
"""
auc_por_escenario.py — AUC-ROC desglosado por escenario individual

Lee:
  models/isolation_forest.pkl + models/scaler.pkl  (de fase3_entrenar.py)
  data/normal_holdout.csv                          (20% normal, de fase3_entrenar.py)
  data/raw/*_anom_*.gz                             (Grupo B — por escenario)
  data/raw/*_mixto_*.gz                            (Grupo C — separa por src_ip)

Produce:
  results/reports/auc_por_escenario.txt

Ejecutar en el sensor:
  python3 scripts/auc_por_escenario.py
"""

import glob
import gzip
import json
import os
from datetime import datetime

import numpy as np
import joblib
from sklearn.metrics import roc_auc_score

np.random.seed(42)

# ── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
MODEL_DIR  = f"{BASE}/models"
REPORT_DIR = f"{BASE}/results/reports"
NORMAL_IPS = {"192.168.0.20", "192.168.0.120"}

os.makedirs(REPORT_DIR, exist_ok=True)

# ── Cargar modelo ─────────────────────────────────────────────
clf    = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")

# ── Leer τ1 desde metricas_offline.txt (fuente única de verdad) ──
tau1 = clf.offset_   # fallback si no existe metricas_offline.txt
metricas_path = f"{BASE}/results/metricas_offline.txt"
if os.path.exists(metricas_path):
    with open(metricas_path) as f:
        for line in f:
            if line.strip().startswith("tau1"):
                try:
                    tau1 = float(line.split(":")[1].split("#")[0].strip())
                except Exception:
                    pass
                break
print(f"τ1 usado para Det%: {tau1:.4f}")


def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e["flow"]["start"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(e["flow"]["end"].replace("Z", "+00:00"))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001


def extract(e):
    flow  = e.get("flow", {})
    proto = e.get("proto", "").upper()
    dur   = flow_duration(e)
    pts   = flow.get("pkts_toserver",  0) or 0
    ptc   = flow.get("pkts_toclient",  0) or 0
    bts   = flow.get("bytes_toserver", 0) or 0
    btc   = flow.get("bytes_toclient", 0) or 0
    return [
        pts, ptc, bts, btc, dur,
        (pts + ptc) / dur,
        (bts + btc) / dur,
        pts / (ptc + 1),
        bts / (btc + 1),
        (bts + btc) / (pts + ptc + 1),
        int(proto == "TCP"),
        int(proto == "UDP"),
        int(proto in ("ICMP", "IPV6-ICMP")),
        e.get("dest_port", 0) or 0,
    ]


def load_flows(path, src_filter=None, exclude_ips=None, max_flows=20_000):
    rows = []
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", errors="ignore") as f:
        for line in f:
            if len(rows) >= max_flows:
                break
            try:
                e = json.loads(line)
                if e.get("event_type") != "flow":
                    continue
                src = e.get("src_ip", "")
                if src_filter and src not in src_filter:
                    continue
                if exclude_ips and src in exclude_ips:
                    continue
                if (e.get("flow", {}).get("pkts_toserver", 0) or 0) == 0:
                    continue
                rows.append(extract(e))
            except Exception:
                pass
    return np.array(rows) if rows else np.empty((0, 14))


# ── Cargar referencia normal ──────────────────────────────────
print("\nCargando datos normales de referencia...")

# Prioridad 1: normal_holdout.csv (separación limpia 80/20)
holdout_path = f"{BASE}/data/normal_holdout.csv"
if os.path.exists(holdout_path):
    import pandas as pd
    df_h = pd.read_csv(holdout_path)
    cols = df_h.columns.tolist()
    X_normal_ref = scaler.transform(df_h[cols].values)
    scores_normal = clf.score_samples(X_normal_ref)
    print(f"  Fuente: normal_holdout.csv ({len(scores_normal):,} flows)")
else:
    # Fallback: leer .gz normales directamente
    normal_rows = []
    for f in sorted(glob.glob(f"{DATA_DIR}/*_normal_*.gz")):
        r = load_flows(f, src_filter=NORMAL_IPS)
        if len(r):
            normal_rows.append(r)
    if not normal_rows:
        raise FileNotFoundError(
            "No se encontró normal_holdout.csv ni archivos *_normal_*.gz\n"
            "Ejecuta primero: fase3_entrenar.py"
        )
    X_normal_ref = scaler.transform(np.vstack(normal_rows))
    scores_normal = clf.score_samples(X_normal_ref)
    print(f"  Fuente: *_normal_*.gz ({len(scores_normal):,} flows)")


# ── Escenarios a evaluar ──────────────────────────────────────
# patrón: fragmento del nombre del archivo entre FECHA_ y _NN_eve.json.gz
escenarios = [
    # Grupo B — ataques puros (Desktop quieto)
    ("SYN Flood     (B1)", "anom_synflood"),
    ("Port Scan     (B2)", "anom_portscan"),
    ("UDP Flood     (B3)", "anom_udpflood"),
    ("ICMP Flood    (B4)", "anom_icmpflood"),
    ("HTTP Abuse    (B5)", "anom_httpabuse"),
    ("Brute Force   (B6)", "anom_bruteforce"),
    # Grupo C — mixto (se extraen solo flujos de ataque con exclude_ips)
    ("Mixto HTTP+SYN  (C1)", "mixto_http_synflood"),
    ("Mixto SSH+Scan  (C2)", "mixto_ssh_portscan"),
    ("Mixto Trf+UDP   (C3)", "mixto_transfer_udpflood"),
]

print(f"\n{'Escenario':<28} {'Flows_n':>7} {'Flows_a':>7} "
      f"{'AUC':>6} {'Det%':>6} {'Score_med':>9}")
print("-" * 68)

resultados = []
for nombre, patron in escenarios:
    archivos = sorted(glob.glob(f"{DATA_DIR}/*_{patron}_*.gz"))
    if not archivos:
        print(f"{nombre:<28} {'—':>7} {'—':>7} {'N/A':>6} {'—':>6} {'—':>9}  [sin datos]")
        continue

    anom_rows = []
    for fp in archivos:
        r = load_flows(fp, exclude_ips=NORMAL_IPS)
        if len(r):
            anom_rows.append(r)
    if not anom_rows:
        print(f"{nombre:<28} {'—':>7} {'—':>7} {'N/A':>6} {'—':>6} {'—':>9}  [sin flows]")
        continue

    X_anom      = scaler.transform(np.vstack(anom_rows))
    scores_anom = clf.score_samples(X_anom)

    # Muestra balanceada para AUC (evita sesgo por tamaño de dataset)
    n_n = min(len(scores_normal), 2_000)
    n_a = min(len(scores_anom),   2_000)
    idx_n = np.random.choice(len(scores_normal), n_n, replace=False)
    idx_a = np.random.choice(len(scores_anom),   n_a, replace=False)

    y_true  = np.concatenate([np.zeros(n_n), np.ones(n_a)])
    y_score = np.concatenate([-scores_normal[idx_n], -scores_anom[idx_a]])

    try:
        auc = roc_auc_score(y_true, y_score)
    except Exception:
        auc = 0.0

    # Det%: % de flows anómalos con score ≤ τ1 (clasificados como LIMIT o BLOCK)
    det_pct = 100 * (scores_anom <= tau1).sum() / len(scores_anom)

    marca = "OK" if auc >= 0.85 else ("~" if auc >= 0.70 else "X")
    print(f"{nombre:<28} {n_n:>7,} {n_a:>7,} {auc:>6.4f} "
          f"{det_pct:>5.1f}% {scores_anom.mean():>9.4f}  [{marca}]")

    resultados.append({
        "escenario":   nombre.strip(),
        "patron":      patron,
        "flows_normal": n_n,
        "flows_anom":  n_a,
        "auc":         round(auc, 4),
        "det_pct":     round(det_pct, 1),
        "score_medio": round(float(scores_anom.mean()), 4),
    })


# ── Guardar reporte ───────────────────────────────────────────
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

lines = [
    "=" * 65,
    "AUC-ROC POR ESCENARIO — PPI UPeU 2026",
    f"Generado : {timestamp}",
    f"τ1 usado : {tau1:.4f}  (PERMIT/LIMIT — fuente: metricas_offline.txt)",
    "=" * 65,
    "",
    f"{'Escenario':<28} {'AUC':>6} {'Det%':>6} {'Score_med':>9}",
    "-" * 52,
]

for r in resultados:
    marca = "OK" if r["auc"] >= 0.85 else ("~" if r["auc"] >= 0.70 else "X")
    lines.append(
        f"{r['escenario']:<28} {r['auc']:>6.4f} "
        f"{r['det_pct']:>5.1f}% {r['score_medio']:>9.4f}  [{marca}]"
    )

lines += [
    "",
    "AUC=1.0 → discriminación perfecta | AUC=0.5 → aleatorio",
    "Det% = flows anómalos con score ≤ τ1 (LIMIT o BLOCK)",
    "[OK] AUC≥0.85  [~] 0.70≤AUC<0.85  [X] AUC<0.70",
    "Curva ROC global: results/auc_roc.png",
    "=" * 65,
]

rpt_path = f"{REPORT_DIR}/auc_por_escenario.txt"
with open(rpt_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"\nReporte guardado: {rpt_path}")
