#!/usr/bin/env python3
"""
#5 — AUC-ROC por escenario individual
Calcula AUC para cada escenario anómalo vs. tráfico normal combinado.
"""
import joblib, glob, gzip, json, os
import numpy as np
from datetime import datetime
from sklearn.metrics import roc_auc_score

MODEL_DIR  = "/home/m4rk/ppi-surikata-producto/models"
DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data/raw"
REPORT_DIR = "/home/m4rk/ppi-surikata-producto/results/reports"
NORMAL_IPS = {"192.168.0.20", "192.168.0.120"}

clf    = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")

def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e["flow"]["start"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(e["flow"]["end"].replace("Z", "+00:00"))
        return max((t1 - t0).total_seconds(), 0.001)
    except: return 0.001

def extract(e):
    flow=e.get("flow",{}); proto=e.get("proto","").upper(); dur=flow_duration(e)
    pts=flow.get("pkts_toserver",0) or 0; ptc=flow.get("pkts_toclient",0) or 0
    bts=flow.get("bytes_toserver",0) or 0; btc=flow.get("bytes_toclient",0) or 0
    return [pts,ptc,bts,btc,dur,(pts+ptc)/dur,(bts+btc)/dur,pts/(ptc+1),
            bts/(btc+1),(bts+btc)/(pts+ptc+1),int(proto=="TCP"),
            int(proto=="UDP"),int(proto in("ICMP","IPV6-ICMP")),e.get("dest_port",0) or 0]

def load_flows(path, src_filter=None, exclude_ips=None, max_flows=20000):
    rows=[]
    opener=gzip.open if path.endswith(".gz") else open
    with opener(path,"rt",errors="ignore") as f:
        for line in f:
            if len(rows)>=max_flows: break
            try:
                e=json.loads(line)
                if e.get("event_type")!="flow": continue
                src=e.get("src_ip","")
                if src_filter and src not in src_filter: continue
                if exclude_ips and src in exclude_ips: continue
                if (e.get("flow",{}).get("pkts_toserver",0) or 0)==0: continue
                rows.append(extract(e))
            except: pass
    return np.array(rows) if rows else np.empty((0,14))

# Cargar datos normales (referencia)
print("Cargando datos normales...")
normal_rows = []
for f in sorted(glob.glob(f"{DATA_DIR}/20260602_normal_*.gz")):
    r = load_flows(f, src_filter=NORMAL_IPS)
    if len(r): normal_rows.append(r)
X_normal = scaler.transform(np.vstack(normal_rows))
scores_normal = clf.score_samples(X_normal)

print(f"\n{'Escenario':<28} {'Flows_n':>7} {'Flows_a':>7} {'AUC':>6} {'Det%':>6} {'Score_med':>9}")
print("-"*68)

escenarios = [
    ("SYN Flood (B1)",    "anom_synflood"),
    ("Port Scan (B2)",    "anom_portscan"),
    ("UDP Flood (B3)",    "anom_udpflood"),
    ("ICMP Flood (B4)",   "anom_icmpflood"),
    ("HTTP Abuse (B5)",   "anom_httpabuse"),
    ("Brute Force (B6)",  "anom_bruteforce"),
    ("Mixto C1",          "mixto_http"),
    ("Mixto C2",          "mixto_ssh"),
    ("Mixto C3",          "mixto_descarga"),
]

resultados = []
for nombre, patron in escenarios:
    archivos = glob.glob(f"{DATA_DIR}/20260602_{patron}_*.gz")
    if not archivos: continue
    anom_rows = []
    for fp in archivos:
        r = load_flows(fp, exclude_ips=NORMAL_IPS)
        if len(r): anom_rows.append(r)
    if not anom_rows: continue
    X_anom = scaler.transform(np.vstack(anom_rows))
    scores_anom = clf.score_samples(X_anom)

    # Combinar para AUC: normal=0, anomalo=1
    n_n = min(len(scores_normal), 2000)
    n_a = min(len(scores_anom),   2000)
    idx_n = np.random.choice(len(scores_normal), n_n, replace=False)
    idx_a = np.random.choice(len(scores_anom),   n_a, replace=False)

    y_true  = np.concatenate([np.zeros(n_n), np.ones(n_a)])
    y_score = np.concatenate([-scores_normal[idx_n], -scores_anom[idx_a]])

    try:
        auc = roc_auc_score(y_true, y_score)
    except: auc = 0.0

    det_pct = 100*(scores_anom <= clf.offset_).sum()/len(scores_anom)
    print(f"{nombre:<28} {n_n:>7,} {n_a:>7,} {auc:>6.4f} {det_pct:>5.1f}% {scores_anom.mean():>9.4f}")
    resultados.append({"escenario": nombre, "patron": patron,
                       "flows_normal": n_n, "flows_anom": n_a,
                       "auc": round(auc, 4), "det_pct": round(det_pct, 1),
                       "score_medio": round(float(scores_anom.mean()), 4)})

# Guardar reporte
hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
lines = [
    "="*65,
    "AUC-ROC POR ESCENARIO — PPI UPeU 2026",
    f"Generado: {hoy}",
    "="*65,
    f"\n{'Escenario':<28} {'AUC':>6} {'Det%':>6} {'Score_med':>9}",
    "-"*52,
]
for r in resultados:
    marca = "OK" if r["auc"] >= 0.85 else ("~" if r["auc"] >= 0.70 else "X")
    lines.append(f"{r['escenario']:<28} {r['auc']:>6.4f} {r['det_pct']:>5.1f}% {r['score_medio']:>9.4f}  [{marca}]")

lines += [
    "",
    "AUC global (todos los escenarios): ver auc_roc_umbrales.png",
    "AUC=1.0 → discriminación perfecta | AUC=0.5 → aleatorio",
    "="*65,
]
rpt_path = f"{REPORT_DIR}/auc_por_escenario.txt"
with open(rpt_path, "w") as f:
    f.write("\n".join(lines))

print(f"\nReporte guardado: {rpt_path}")
