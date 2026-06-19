#!/usr/bin/env python3
"""
F6-AE — Comparación offline IF vs Autoencoder sobre todos los grupos A/B/C.

Métricas calculadas por escenario:
  - AUC-ROC (IF y AE)
  - Det%    @ τ1 — % flows detectados como anómalos (LIMIT+BLOCK)
  - Block%  @ τ2 — % flows bloqueados (BLOCK directo)
  - ITL%    en Grupo A — % flows normales mal clasificados como LIMIT/BLOCK

Salida:
  results/ae/comparacion/resultados_ae_comparacion.csv
  results/ae/comparacion/resumen_ae_vs_if.txt
  results/ae/graficas_comparacion/ae_01_auc_por_escenario.png
  results/ae/graficas_comparacion/ae_02_det_block_por_escenario.png
  results/ae/graficas_comparacion/ae_03_distribuciones_score.png
  results/ae/graficas_comparacion/ae_04_acuerdo_decisiones.png
  results/ae/graficas_comparacion/ae_05_panel_resumen.png

Ejecutar en el sensor:
  python3 scripts/comparacion/ae/f6_ae_comparacion.py
"""

import os, gzip, glob, json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.metrics import roc_curve, auc as sk_auc

ROOT     = '/home/m4rk/ppi-surikata-producto'
RAW_DIR  = os.path.join(ROOT, 'data/raw')
OUT_DIR  = os.path.join(ROOT, 'results/ae/comparacion')
GRF_DIR  = os.path.join(ROOT, 'results/ae/graficas_comparacion')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(GRF_DIR, exist_ok=True)

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES = [
    'pkts_toserver','pkts_toclient','bytes_toserver','bytes_toclient',
    'duration','pkt_rate','byte_rate','pkt_ratio','byte_ratio',
    'avg_pkt_size','is_tcp','is_udp','is_icmp','dest_port',
]

# ─── Cargar modelos ───────────────────────────────────────────────────────────
print("=" * 65)
print("F6-AE — Comparación offline IF vs Autoencoder")
print("=" * 65)

if_model  = joblib.load(os.path.join(ROOT, 'models/isolation_forest.pkl'))
if_scaler = joblib.load(os.path.join(ROOT, 'models/scaler.pkl'))
ae_model  = joblib.load(os.path.join(ROOT, 'models/ae/ae_autoencoder.pkl'))
ae_scaler = joblib.load(os.path.join(ROOT, 'models/ae/ae_scaler.pkl'))
print("Modelos cargados: IF + AE")

# ─── Leer umbrales ────────────────────────────────────────────────────────────
def leer_umbrales(path, def_t1, def_t2):
    t1, t2 = def_t1, def_t2
    try:
        with open(path) as f:
            for line in f:
                k, _, v = line.strip().partition('=')
                if k == 'tau1': t1 = float(v)
                if k == 'tau2': t2 = float(v)
    except:
        pass
    return t1, t2

IF_T1, IF_T2 = leer_umbrales(os.path.join(ROOT, 'results/metricas_offline.txt'), -0.4459, -0.6027)
AE_T1, AE_T2 = leer_umbrales(os.path.join(ROOT, 'results/ae/ae_metricas_offline.txt'), -0.0038, -0.0745)

print(f"IF  τ1={IF_T1:.4f}  τ2={IF_T2:.4f}")
print(f"AE  τ1={AE_T1:.4f}  τ2={AE_T2:.4f}")

# ─── Extracción de features ───────────────────────────────────────────────────
def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except:
        return 0.001

def parse_and_extract(path, src_filter=None, exclude_ips=None, max_flows=100_000):
    rows = []
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', errors='ignore') as f:
        for line in f:
            if len(rows) >= max_flows:
                break
            try:
                e = json.loads(line)
                if e.get('event_type') != 'flow':
                    continue
                src = e.get('src_ip', '')
                if src_filter and src not in src_filter:
                    continue
                if exclude_ips and src in exclude_ips:
                    continue
                fl    = e.get('flow', {})
                proto = e.get('proto', '').upper()
                dur   = flow_duration(e)
                pts   = fl.get('pkts_toserver', 0) or 0
                ptc   = fl.get('pkts_toclient', 0) or 0
                bts   = fl.get('bytes_toserver', 0) or 0
                btc   = fl.get('bytes_toclient', 0) or 0
                if pts == 0:
                    continue
                rows.append([
                    pts, ptc, bts, btc, dur,
                    (pts + ptc) / dur,
                    (bts + btc) / dur,
                    pts / (ptc + 1),
                    bts / (btc + 1),
                    (bts + btc) / max(pts + ptc, 1),
                    1.0 if proto == 'TCP'  else 0.0,
                    1.0 if proto == 'UDP'  else 0.0,
                    1.0 if proto in ('ICMP', 'IPV6-ICMP') else 0.0,
                    float(e.get('dest_port', 0) or 0),
                ])
            except:
                pass
    if not rows:
        return np.empty((0, 14), dtype=np.float32)
    X = np.array(rows, dtype=np.float32)
    # Descartar NaN/Inf
    mask = np.all(np.isfinite(X), axis=1)
    return X[mask]

def score_if(X):
    if len(X) == 0:
        return np.array([])
    Xs = if_scaler.transform(X)
    return if_model.score_samples(Xs)

def score_ae(X):
    if len(X) == 0:
        return np.array([])
    Xs   = ae_scaler.transform(X)
    Xhat = ae_model.predict(Xs)
    return -np.mean((Xs - Xhat) ** 2, axis=1)

def decision(scores, t1, t2):
    """Retorna array con 'PERMIT'/'LIMIT'/'BLOCK' por flow."""
    d = np.where(scores > t1, 'PERMIT',
        np.where(scores > t2, 'LIMIT', 'BLOCK'))
    return d

# ─────────────────────────────────────────────────────────────────────────────
# GRUPO A — Normal: medir ITL (falsos positivos sobre tráfico legítimo)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "─" * 65)
print("[1] GRUPO A — Normal (ITL: falsos positivos en tráfico legítimo)")
print("─" * 65)

gz_normal = sorted(glob.glob(os.path.join(RAW_DIR, '*_normal_*.gz')))
normal_rows = []

for gz in gz_normal:
    X = parse_and_extract(gz, src_filter=NORMAL_IPS)
    if len(X) == 0:
        continue
    sif = score_if(X)
    sae = score_ae(X)
    n   = len(X)
    itl_if = float(np.mean(sif <= IF_T1)) * 100
    itl_ae = float(np.mean(sae <= AE_T1)) * 100
    blk_if = float(np.mean(sif <= IF_T2)) * 100
    blk_ae = float(np.mean(sae <= AE_T2)) * 100
    name = os.path.basename(gz)
    normal_rows.append({
        'archivo': name, 'grupo': 'A',
        'n_flows': n,
        'itl_if': round(itl_if, 2), 'itl_ae': round(itl_ae, 2),
        'blk_if': round(blk_if, 2), 'blk_ae': round(blk_ae, 2),
    })
    print(f"  {name:55s} {n:6d} flows  ITL_IF={itl_if:.1f}%  ITL_AE={itl_ae:.1f}%")

df_normal = pd.DataFrame(normal_rows)
total_if = df_normal['itl_if'].mean() if len(df_normal) else 0
total_ae = df_normal['itl_ae'].mean() if len(df_normal) else 0
print(f"\n  ITL medio  IF={total_if:.2f}%   AE={total_ae:.2f}%")

# ─────────────────────────────────────────────────────────────────────────────
# GRUPO B — Anómalo: AUC, Det%, Block% por escenario
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "─" * 65)
print("[2] GRUPO B — Anómalo (AUC, Det%, Block% por escenario)")
print("─" * 65)

gz_anom = sorted(glob.glob(os.path.join(RAW_DIR, '*_anom_*.gz')))

# Cargar scores normales del holdout (ya calculados en entrenamiento)
scores_normal_ae = np.load(os.path.join(ROOT, 'models/ae/ae_scores_normal.npy'))

# Para IF: regenerar scores del holdout normal (X_holdout_s ya guardado)
X_holdout_s = np.load(os.path.join(ROOT, 'models/ae/ae_holdout_scaled.npy'))
# IF usa su propio scaler, necesitamos X en espacio original
# Invertir scaler del AE para obtener X original, luego aplicar scaler del IF
X_holdout_orig = ae_scaler.inverse_transform(X_holdout_s)
scores_normal_if = score_if(X_holdout_orig.astype(np.float32))

print(f"  Holdout normal IF: {len(scores_normal_if)} flows  media={scores_normal_if.mean():.4f}")
print(f"  Holdout normal AE: {len(scores_normal_ae)} flows  media={scores_normal_ae.mean():.4f}")

anom_rows = []
for gz in gz_anom:
    X = parse_and_extract(gz, exclude_ips=NORMAL_IPS)
    if len(X) == 0:
        continue
    sif = score_if(X)
    sae = score_ae(X)
    n   = len(X)
    nh  = len(scores_normal_if)

    # AUC-IF
    all_s_if = np.concatenate([scores_normal_if, sif])
    all_l    = np.concatenate([np.zeros(nh), np.ones(n)])
    fpr_if, tpr_if, _ = roc_curve(all_l, -all_s_if)
    auc_if = sk_auc(fpr_if, tpr_if)

    # AUC-AE
    all_s_ae = np.concatenate([scores_normal_ae, sae])
    fpr_ae, tpr_ae, _ = roc_curve(all_l, -all_s_ae)
    auc_ae = sk_auc(fpr_ae, tpr_ae)

    # Det% y Block%
    det_if  = float(np.mean(sif <= IF_T1)) * 100
    det_ae  = float(np.mean(sae <= AE_T1)) * 100
    blk_if  = float(np.mean(sif <= IF_T2)) * 100
    blk_ae  = float(np.mean(sae <= AE_T2)) * 100

    # Acuerdo de decisiones
    d_if = decision(sif, IF_T1, IF_T2)
    d_ae = decision(sae, AE_T1, AE_T2)
    ambos_blk  = int(np.sum((d_if == 'BLOCK')  & (d_ae == 'BLOCK')))
    ambos_lim  = int(np.sum((d_if == 'LIMIT')  & (d_ae == 'LIMIT')))
    ambos_per  = int(np.sum((d_if == 'PERMIT') & (d_ae == 'PERMIT')))
    solo_if    = int(np.sum((d_if != 'PERMIT') & (d_ae == 'PERMIT')))
    solo_ae    = int(np.sum((d_ae != 'PERMIT') & (d_if == 'PERMIT')))

    # Etiqueta corta de escenario
    base = os.path.basename(gz)
    parts = base.split('_')
    try:
        escenario = parts[2] + '_' + parts[3]
    except:
        escenario = base[:20]

    name = base
    anom_rows.append({
        'archivo': name, 'escenario': escenario, 'grupo': 'B',
        'n_flows': n,
        'auc_if': round(auc_if, 4), 'auc_ae': round(auc_ae, 4),
        'det_if': round(det_if, 2), 'det_ae': round(det_ae, 2),
        'blk_if': round(blk_if, 2), 'blk_ae': round(blk_ae, 2),
        'ambos_block': ambos_blk, 'ambos_limit': ambos_lim,
        'ambos_permit': ambos_per,
        'solo_if': solo_if, 'solo_ae': solo_ae,
    })
    print(f"  {name:55s}  AUC_IF={auc_if:.4f}  AUC_AE={auc_ae:.4f}  "
          f"Det_IF={det_if:.1f}%  Det_AE={det_ae:.1f}%")

df_anom = pd.DataFrame(anom_rows)

# ─────────────────────────────────────────────────────────────────────────────
# GRUPO C — Mixto: separar por src_ip
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "─" * 65)
print("[3] GRUPO C — Mixto (normal + anómalo simultáneo)")
print("─" * 65)

gz_mixto = sorted(glob.glob(os.path.join(RAW_DIR, '*_mixto_*.gz')))
mixto_rows = []

for gz in gz_mixto:
    X_norm = parse_and_extract(gz, src_filter=NORMAL_IPS)
    X_anom = parse_and_extract(gz, exclude_ips=NORMAL_IPS)
    name = os.path.basename(gz)
    row = {'archivo': name, 'grupo': 'C', 'n_normal': len(X_norm), 'n_anom': len(X_anom)}

    if len(X_norm) > 0:
        sif = score_if(X_norm)
        sae = score_ae(X_norm)
        row['itl_if'] = round(float(np.mean(sif <= IF_T1)) * 100, 2)
        row['itl_ae'] = round(float(np.mean(sae <= AE_T1)) * 100, 2)
    else:
        row['itl_if'] = row['itl_ae'] = 0.0

    if len(X_anom) > 0:
        sif = score_if(X_anom)
        sae = score_ae(X_anom)
        row['det_if'] = round(float(np.mean(sif <= IF_T1)) * 100, 2)
        row['det_ae'] = round(float(np.mean(sae <= AE_T1)) * 100, 2)
        row['blk_if'] = round(float(np.mean(sif <= IF_T2)) * 100, 2)
        row['blk_ae'] = round(float(np.mean(sae <= AE_T2)) * 100, 2)
    else:
        row['det_if'] = row['det_ae'] = row['blk_if'] = row['blk_ae'] = 0.0

    mixto_rows.append(row)
    print(f"  {name:50s}  ITL_IF={row['itl_if']:.1f}%  ITL_AE={row['itl_ae']:.1f}%  "
          f"Det_IF={row.get('det_if', 0):.1f}%  Det_AE={row.get('det_ae', 0):.1f}%")

df_mixto = pd.DataFrame(mixto_rows)

# ─────────────────────────────────────────────────────────────────────────────
# GUARDAR CSV Y RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
csv_path = os.path.join(OUT_DIR, 'resultados_ae_comparacion.csv')
df_anom.to_csv(csv_path, index=False)
print(f"\n[4] CSV guardado: {csv_path}")

res_path = os.path.join(OUT_DIR, 'resumen_ae_vs_if.txt')
with open(res_path, 'w') as f:
    f.write("=" * 65 + "\n")
    f.write("RESUMEN COMPARATIVO  IF vs AE — PPI UPeU 2026\n")
    f.write("=" * 65 + "\n\n")

    f.write("UMBRALES\n")
    f.write(f"  IF  τ1={IF_T1:.4f}  τ2={IF_T2:.4f}\n")
    f.write(f"  AE  τ1={AE_T1:.4f}  τ2={AE_T2:.4f}\n\n")

    f.write("GRUPO A — ITL (falsos positivos en tráfico normal)\n")
    f.write(f"  ITL medio IF  = {total_if:.2f}%\n")
    f.write(f"  ITL medio AE  = {total_ae:.2f}%\n\n")

    f.write("GRUPO B — Detección (tráfico anómalo)\n")
    if len(df_anom):
        f.write(f"  AUC-ROC medio  IF = {df_anom['auc_if'].mean():.4f}\n")
        f.write(f"  AUC-ROC medio  AE = {df_anom['auc_ae'].mean():.4f}\n")
        f.write(f"  Det%  @ τ1  IF = {df_anom['det_if'].mean():.2f}%\n")
        f.write(f"  Det%  @ τ1  AE = {df_anom['det_ae'].mean():.2f}%\n")
        f.write(f"  Block% @ τ2 IF = {df_anom['blk_if'].mean():.2f}%\n")
        f.write(f"  Block% @ τ2 AE = {df_anom['blk_ae'].mean():.2f}%\n\n")
        f.write("  AUC por escenario:\n")
        for _, row in df_anom.iterrows():
            f.write(f"    {row['archivo']:55s}  AUC_IF={row['auc_if']:.4f}  AUC_AE={row['auc_ae']:.4f}\n")

    f.write("\nGRUPO C — Mixto (Normal+Anómalo simultáneo)\n")
    for _, row in df_mixto.iterrows():
        f.write(f"  {row['archivo']:50s}  ITL_IF={row['itl_if']:.1f}%  ITL_AE={row['itl_ae']:.1f}%  "
                f"Det_IF={row.get('det_if', 0):.1f}%  Det_AE={row.get('det_ae', 0):.1f}%\n")

print(f"    Resumen: {res_path}")

# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICAS
# ─────────────────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    CLR_IF = '#1f77b4'   # azul
    CLR_AE = '#d62728'   # rojo

    # ── Gráfica 1: AUC por escenario ────────────────────────────────────────
    if len(df_anom):
        fig, ax = plt.subplots(figsize=(12, 5))
        labels = [os.path.basename(r['archivo']).replace('_eve.json.gz', '')
                  .replace('20260602_anom_', '').replace('20260603_anom_', '')
                  .replace('20260615_anom_', '')
                  for _, r in df_anom.iterrows()]
        x  = np.arange(len(labels))
        w  = 0.35
        ax.bar(x - w/2, df_anom['auc_if'], w, label=f'IF  (μ={df_anom["auc_if"].mean():.4f})',
               color=CLR_IF, alpha=0.85)
        ax.bar(x + w/2, df_anom['auc_ae'], w, label=f'AE  (μ={df_anom["auc_ae"].mean():.4f})',
               color=CLR_AE, alpha=0.85)
        ax.axhline(0.80, ls='--', color='gray', lw=1, label='Mínimo requerido (0.80)')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)
        ax.set_ylabel('AUC-ROC')
        ax.set_title('AUC-ROC por Escenario — IF vs Autoencoder', fontweight='bold')
        ax.set_ylim(0.6, 1.02)
        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        p = os.path.join(GRF_DIR, 'ae_01_auc_por_escenario.png')
        plt.savefig(p, dpi=150)
        plt.close()
        print(f"\n[5] Gráfica 1: {p}")

    # ── Gráfica 2: Det% y Block% por escenario ──────────────────────────────
    if len(df_anom):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        labels = [r['escenario'].replace('01', '').rstrip('_')
                  for _, r in df_anom.iterrows()]
        x = np.arange(len(labels))
        w = 0.35

        ax1.bar(x - w/2, df_anom['det_if'], w, label='IF', color=CLR_IF, alpha=0.85)
        ax1.bar(x + w/2, df_anom['det_ae'], w, label='AE', color=CLR_AE, alpha=0.85)
        ax1.set_title('Det% @ τ1 (LIMIT+BLOCK)\nFlows anómalos detectados', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)
        ax1.set_ylabel('%')
        ax1.set_ylim(0, 110)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        ax2.bar(x - w/2, df_anom['blk_if'], w, label='IF', color=CLR_IF, alpha=0.85)
        ax2.bar(x + w/2, df_anom['blk_ae'], w, label='AE', color=CLR_AE, alpha=0.85)
        ax2.set_title('Block% @ τ2 (FPR≤2%)\nFlows anómalos bloqueados', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)
        ax2.set_ylabel('%')
        ax2.set_ylim(0, 110)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        plt.suptitle('Tasas de Detección y Bloqueo — IF vs Autoencoder', fontweight='bold')
        plt.tight_layout()
        p = os.path.join(GRF_DIR, 'ae_02_det_block_por_escenario.png')
        plt.savefig(p, dpi=150)
        plt.close()
        print(f"    Gráfica 2: {p}")

    # ── Gráfica 3: Distribuciones de score ──────────────────────────────────
    # Cargar un archivo normal y uno anómalo para mostrar las distribuciones
    gz_n_sample = gz_normal[:3] if gz_normal else []
    gz_a_sample = gz_anom[:3] if gz_anom else []

    Xn_all, Xa_all = [], []
    for gz in gz_n_sample:
        X = parse_and_extract(gz, src_filter=NORMAL_IPS, max_flows=10000)
        if len(X): Xn_all.append(X)
    for gz in gz_a_sample:
        X = parse_and_extract(gz, exclude_ips=NORMAL_IPS, max_flows=10000)
        if len(X): Xa_all.append(X)

    if Xn_all and Xa_all:
        Xn = np.vstack(Xn_all)
        Xa = np.vstack(Xa_all)
        sn_if = score_if(Xn); sa_if = score_if(Xa)
        sn_ae = score_ae(Xn); sa_ae = score_ae(Xa)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        ax = axes[0]
        ax.hist(sn_if, bins=80, density=True, alpha=0.65, color='steelblue', label='Normal')
        ax.hist(sa_if, bins=80, density=True, alpha=0.65, color='tomato', label='Anómalo')
        ax.axvline(IF_T1, color='green', ls='--', lw=1.5, label=f'τ1={IF_T1:.3f}')
        ax.axvline(IF_T2, color='red', ls='--', lw=1.5, label=f'τ2={IF_T2:.3f}')
        ax.set_title('Isolation Forest — score_samples(X)', fontweight='bold')
        ax.set_xlabel('Score IF'); ax.set_ylabel('Densidad')
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

        ax = axes[1]
        ax.hist(sn_ae, bins=80, density=True, alpha=0.65, color='steelblue', label='Normal')
        ax.hist(sa_ae, bins=80, density=True, alpha=0.65, color='tomato', label='Anómalo')
        ax.axvline(AE_T1, color='green', ls='--', lw=1.5, label=f'τ1={AE_T1:.3f}')
        ax.axvline(AE_T2, color='red', ls='--', lw=1.5, label=f'τ2={AE_T2:.3f}')
        ax.set_title('Autoencoder — −MSE(X, X̂)', fontweight='bold')
        ax.set_xlabel('Score AE'); ax.set_ylabel('Densidad')
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

        plt.suptitle('Distribución de Scores — Normal vs Anómalo', fontweight='bold')
        plt.tight_layout()
        p = os.path.join(GRF_DIR, 'ae_03_distribuciones_score.png')
        plt.savefig(p, dpi=150)
        plt.close()
        print(f"    Gráfica 3: {p}")

    # ── Gráfica 4: Acuerdo de decisiones (Grupo B) ──────────────────────────
    if len(df_anom):
        # Stacked bar: ambos_block, solo_if, solo_ae, ambos_permit
        n_esc = len(df_anom)
        labels = [r['escenario'].replace('01', '').rstrip('_')
                  for _, r in df_anom.iterrows()]
        x = np.arange(n_esc)

        total = df_anom['n_flows'].values
        p_ambos_blk  = df_anom['ambos_block'].values  / total * 100
        p_ambos_lim  = df_anom['ambos_limit'].values  / total * 100
        p_solo_if    = df_anom['solo_if'].values       / total * 100
        p_solo_ae    = df_anom['solo_ae'].values       / total * 100
        p_ambos_per  = df_anom['ambos_permit'].values  / total * 100

        fig, ax = plt.subplots(figsize=(13, 5))
        bottom = np.zeros(n_esc)
        for vals, color, label in [
            (p_ambos_blk, '#d62728', 'Ambos BLOCK'),
            (p_ambos_lim, '#ff7f0e', 'Ambos LIMIT'),
            (p_solo_if,   '#1f77b4', 'Solo IF detecta'),
            (p_solo_ae,   '#9467bd', 'Solo AE detecta'),
            (p_ambos_per, '#aec7e8', 'Ambos PERMIT (FP)'),
        ]:
            ax.bar(x, vals, bottom=bottom, label=label, color=color, alpha=0.88)
            bottom += vals

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)
        ax.set_ylabel('% de flows')
        ax.set_title('Acuerdo de Decisiones por Escenario — IF vs AE', fontweight='bold')
        ax.legend(loc='lower right', fontsize=8, ncol=2)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 105)
        plt.tight_layout()
        p = os.path.join(GRF_DIR, 'ae_04_acuerdo_decisiones.png')
        plt.savefig(p, dpi=150)
        plt.close()
        print(f"    Gráfica 4: {p}")

    # ── Gráfica 5: Panel resumen ─────────────────────────────────────────────
    if len(df_anom):
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))
        fig.suptitle('Panel Resumen — IF vs Autoencoder\nPPI UPeU 2026',
                     fontweight='bold', fontsize=13)

        # 5a: AUC medio por grupo de escenario
        ax = axes[0, 0]
        escenarios_uniq = sorted(set('_'.join(r['escenario'].split('_')[:2])
                                     for _, r in df_anom.iterrows()))
        auc_if_grp, auc_ae_grp = [], []
        for esc in escenarios_uniq:
            sub = df_anom[df_anom['escenario'].str.startswith(esc.split('_')[0])]
            auc_if_grp.append(sub['auc_if'].mean())
            auc_ae_grp.append(sub['auc_ae'].mean())
        x = np.arange(len(escenarios_uniq)); w = 0.35
        ax.bar(x - w/2, auc_if_grp, w, color=CLR_IF, alpha=0.85, label='IF')
        ax.bar(x + w/2, auc_ae_grp, w, color=CLR_AE, alpha=0.85, label='AE')
        ax.axhline(0.80, ls='--', color='gray', lw=1)
        ax.set_xticks(x); ax.set_xticklabels(escenarios_uniq, rotation=25, ha='right', fontsize=8)
        ax.set_ylim(0.5, 1.05); ax.set_title('AUC-ROC por tipo de ataque'); ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        # 5b: Tabla resumen de métricas globales
        ax = axes[0, 1]
        ax.axis('off')
        metricas = [
            ['Métrica', 'IF', 'AE'],
            ['AUC-ROC (μ)', f"{df_anom['auc_if'].mean():.4f}", f"{df_anom['auc_ae'].mean():.4f}"],
            ['Det% @ τ1 (μ)', f"{df_anom['det_if'].mean():.1f}%", f"{df_anom['det_ae'].mean():.1f}%"],
            ['Block% @ τ2 (μ)', f"{df_anom['blk_if'].mean():.1f}%", f"{df_anom['blk_ae'].mean():.1f}%"],
            ['ITL% Grupo A (μ)', f"{total_if:.2f}%", f"{total_ae:.2f}%"],
            ['τ1 (Youden)', f"{IF_T1:.4f}", f"{AE_T1:.4f}"],
            ['τ2 (FPR≤2%)', f"{IF_T2:.4f}", f"{AE_T2:.4f}"],
        ]
        tbl = ax.table(cellText=metricas[1:], colLabels=metricas[0],
                       loc='center', cellLoc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(10)
        tbl.scale(1.2, 1.8)
        for (row, col), cell in tbl.get_celld().items():
            if row == 0:
                cell.set_facecolor('#2c3e50')
                cell.set_text_props(color='white', fontweight='bold')
            elif col == 1:
                cell.set_facecolor('#d6e4f0')
            elif col == 2:
                cell.set_facecolor('#fde8e8')
        ax.set_title('Métricas Globales Comparativas', pad=10)

        # 5c: Block% por escenario (ambos modelos)
        ax = axes[1, 0]
        labels_s = [r['escenario'].replace('01', '').rstrip('_')
                    for _, r in df_anom.iterrows()]
        x = np.arange(len(labels_s)); w = 0.35
        ax.bar(x - w/2, df_anom['blk_if'], w, color=CLR_IF, alpha=0.85, label='IF')
        ax.bar(x + w/2, df_anom['blk_ae'], w, color=CLR_AE, alpha=0.85, label='AE')
        ax.set_xticks(x); ax.set_xticklabels(labels_s, rotation=30, ha='right', fontsize=7)
        ax.set_ylabel('%'); ax.set_ylim(0, 110)
        ax.set_title('Block% @ τ2 por escenario\n(FPR ≤ 2%)'); ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        # 5d: Scatter AUC_IF vs AUC_AE por escenario
        ax = axes[1, 1]
        ax.scatter(df_anom['auc_if'], df_anom['auc_ae'], c='#2ecc71', s=100, zorder=5, edgecolors='black', lw=0.5)
        for _, row in df_anom.iterrows():
            lbl = row['escenario'].split('_')[0]
            ax.annotate(lbl, (row['auc_if'], row['auc_ae']),
                        textcoords='offset points', xytext=(4, 3), fontsize=7)
        mn, mx = 0.6, 1.02
        ax.plot([mn, mx], [mn, mx], 'k--', lw=1, alpha=0.5, label='AUC_IF = AUC_AE')
        ax.set_xlim(mn, mx); ax.set_ylim(mn, mx)
        ax.set_xlabel('AUC Isolation Forest'); ax.set_ylabel('AUC Autoencoder')
        ax.set_title('AUC_AE vs AUC_IF por escenario\n(puntos sobre la diagonal → AE gana)')
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax.fill_between([mn, mx], [mn, mx], [mx, mx], alpha=0.06, color='red',
                        label='AE mejor')

        plt.tight_layout()
        p = os.path.join(GRF_DIR, 'ae_05_panel_resumen.png')
        plt.savefig(p, dpi=150)
        plt.close()
        print(f"    Gráfica 5: {p}")

    print("\n[6] Todas las gráficas guardadas en:", GRF_DIR)

except Exception as e:
    print(f"\n[AVISO] matplotlib: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# IMPRESIÓN FINAL DE RESUMEN
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("RESUMEN FINAL")
print("=" * 65)
if len(df_anom):
    print(f"  Grupo A  — ITL:     IF={total_if:.2f}%   AE={total_ae:.2f}%")
    print(f"  Grupo B  — AUC-ROC: IF={df_anom['auc_if'].mean():.4f}  AE={df_anom['auc_ae'].mean():.4f}  (ΔAE={df_anom['auc_ae'].mean()-df_anom['auc_if'].mean():+.4f})")
    print(f"  Grupo B  — Det% τ1: IF={df_anom['det_if'].mean():.1f}%  AE={df_anom['det_ae'].mean():.1f}%")
    print(f"  Grupo B  — Blk% τ2: IF={df_anom['blk_if'].mean():.1f}%  AE={df_anom['blk_ae'].mean():.1f}%  ← ventaja clave del AE")
print("=" * 65)
print("\n=== F6-AE comparación completada ===")
