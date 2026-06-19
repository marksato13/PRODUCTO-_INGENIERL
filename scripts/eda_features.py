#!/usr/bin/env python3
"""
eda_features.py — EDA descriptivo de las 14 features por Grupo (A, B, C).

Posición en el pipeline:
    F2 (capturas .gz)  →  [ESTE SCRIPT — EDA]  →  F3 (split 80/20 → IF)

Grupos:
    A — Normal   : *_normal_*.gz  (src_ip ∈ {192.168.0.20, 192.168.0.120})
    B — Anómalo  : *_anom_*.gz   (src_ip ∉ {192.168.0.20, 192.168.0.120})
    C — Mixto    : *_mixto_*.gz  (ambos filtros separados)

Salidas: results/eda/
    eda_01_distribuciones.png   — KDE 6 features continuas por grupo
    eda_02_protocolo.png        — TCP/UDP/ICMP por grupo (stacked bar)
    eda_03_boxplots.png         — Boxplots A vs B, 6 features
    eda_04_correlacion.png      — Heatmap correlación Grupo A y Grupo B
    eda_05_dest_ports.png       — Top 10 puertos destino por grupo
    eda_06_stats_tabla.png      — Tabla visual de estadísticas
    eda_stats_completas.txt     — Estadísticas en texto (media, std, mediana, skew)

Ejecutar en el sensor:
    python3 scripts/eda_features.py
"""

import os, gzip, glob, json
import numpy as np
import pandas as pd
from datetime import datetime

ROOT    = '/home/m4rk/ppi-surikata-producto'
RAW_DIR = os.path.join(ROOT, 'data/raw')
OUT_DIR = os.path.join(ROOT, 'results/eda')
os.makedirs(OUT_DIR, exist_ok=True)

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES_CONT = [
    'pkts_toserver','pkts_toclient','bytes_toserver','bytes_toclient',
    'duration','pkt_rate','byte_rate','pkt_ratio','byte_ratio','avg_pkt_size',
]
FEATURES_BIN  = ['is_tcp','is_udp','is_icmp']
FEATURES_DISC = ['dest_port']
FEATURES_ALL  = FEATURES_CONT + FEATURES_BIN + FEATURES_DISC

# ─── Extracción ───────────────────────────────────────────────────────────────
def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z','+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z','+00:00'))
        return max((t1-t0).total_seconds(), 0.001)
    except:
        return 0.001

def parse_group(paths, src_filter=None, exclude_ips=None, max_per_file=80_000):
    rows = []
    for path in paths:
        count = 0
        opener = gzip.open if path.endswith('.gz') else open
        with opener(path, 'rt', errors='ignore') as f:
            for line in f:
                if count >= max_per_file:
                    break
                try:
                    e = json.loads(line)
                    if e.get('event_type') != 'flow':
                        continue
                    src = e.get('src_ip','')
                    if src_filter  and src not in src_filter:  continue
                    if exclude_ips and src in exclude_ips:     continue
                    fl    = e.get('flow', {})
                    proto = e.get('proto','').upper()
                    dur   = flow_duration(e)
                    pts   = fl.get('pkts_toserver', 0) or 0
                    ptc   = fl.get('pkts_toclient', 0) or 0
                    bts   = fl.get('bytes_toserver',0) or 0
                    btc   = fl.get('bytes_toclient',0) or 0
                    if pts == 0: continue
                    rows.append({
                        'pkts_toserver':  pts,
                        'pkts_toclient':  ptc,
                        'bytes_toserver': bts,
                        'bytes_toclient': btc,
                        'duration':       dur,
                        'pkt_rate':      (pts+ptc)/dur,
                        'byte_rate':     (bts+btc)/dur,
                        'pkt_ratio':      pts/(ptc+1),
                        'byte_ratio':     bts/(btc+1),
                        'avg_pkt_size':  (bts+btc)/max(pts+ptc,1),
                        'is_tcp':   int(proto=='TCP'),
                        'is_udp':   int(proto=='UDP'),
                        'is_icmp':  int(proto in ('ICMP','IPV6-ICMP')),
                        'dest_port': int(e.get('dest_port',0) or 0),
                    })
                    count += 1
                except:
                    pass
    df = pd.DataFrame(rows)
    # limpiar infinitos/nan
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    return df

# ─── Cargar datos ─────────────────────────────────────────────────────────────
print("="*65)
print("EDA — Análisis Exploratorio de Features por Grupo")
print("="*65)

gz_A = sorted(glob.glob(os.path.join(RAW_DIR, '*_normal_*.gz')))
gz_B = sorted(glob.glob(os.path.join(RAW_DIR, '*_anom_*.gz')))
gz_C = sorted(glob.glob(os.path.join(RAW_DIR, '*_mixto_*.gz')))

print(f"\n[1] Cargando archivos...")
print(f"  Grupo A (normal):  {len(gz_A)} archivos")
print(f"  Grupo B (anómalo): {len(gz_B)} archivos")
print(f"  Grupo C (mixto):   {len(gz_C)} archivos")

dfA = parse_group(gz_A, src_filter=NORMAL_IPS)
print(f"  GA: {len(dfA):,} flows cargados")

dfB = parse_group(gz_B, exclude_ips=NORMAL_IPS, max_per_file=40_000)
print(f"  GB: {len(dfB):,} flows cargados")

dfC_norm = parse_group(gz_C, src_filter=NORMAL_IPS, max_per_file=5_000)
dfC_anom = parse_group(gz_C, exclude_ips=NORMAL_IPS, max_per_file=5_000)
dfC = pd.concat([dfC_norm, dfC_anom], ignore_index=True)
print(f"  GC: {len(dfC):,} flows cargados ({len(dfC_norm):,} normal + {len(dfC_anom):,} anómalo)")

# Sample para gráficas (stats se calculan sobre datos completos de A y B)
SAMPLE_N = 15_000
dfA_s = dfA.sample(min(SAMPLE_N, len(dfA)), random_state=42)
dfB_s = dfB.sample(min(SAMPLE_N, len(dfB)), random_state=42)
dfC_s = dfC.sample(min(SAMPLE_N, len(dfC)), random_state=42)
print(f"\n  Samples para gráficas: A={len(dfA_s):,}  B={len(dfB_s):,}  C={len(dfC_s):,}")

# ─── Estadísticas en texto ────────────────────────────────────────────────────
print("\n[2] Calculando estadísticas descriptivas...")

stats_path = os.path.join(OUT_DIR, 'eda_stats_completas.txt')
with open(stats_path, 'w') as f:
    f.write("="*80 + "\n")
    f.write("EDA — ESTADÍSTICAS DESCRIPTIVAS POR GRUPO Y FEATURE\n")
    f.write(f"PPI UPeU 2026 | Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"Grupo A: {len(dfA):,} flows | Grupo B: {len(dfB):,} flows | Grupo C: {len(dfC):,} flows\n")
    f.write("="*80 + "\n\n")

    for feat in FEATURES_CONT:
        f.write(f"{'─'*60}\n{feat}\n{'─'*60}\n")
        f.write(f"{'Grupo':>8} {'n':>8} {'min':>10} {'P25':>10} {'mediana':>10} "
                f"{'media':>12} {'P75':>10} {'P99':>12} {'max':>12} {'std':>12} {'skew':>8}\n")
        for lbl, df in [('A-Normal', dfA), ('B-Anóm', dfB), ('C-Mixto', dfC)]:
            s = df[feat]
            f.write(f"{lbl:>8} {len(s):>8,} {s.min():>10.2f} {s.quantile(.25):>10.2f} "
                    f"{s.median():>10.2f} {s.mean():>12.2f} {s.quantile(.75):>10.2f} "
                    f"{s.quantile(.99):>12.2f} {s.max():>12.2f} {s.std():>12.2f} {s.skew():>8.2f}\n")
        f.write("\n")

    f.write("="*80 + "\n")
    f.write("PROTOCOLO POR GRUPO\n")
    f.write("="*80 + "\n")
    for lbl, df in [('A-Normal', dfA), ('B-Anóm', dfB), ('C-Mixto', dfC)]:
        n = len(df)
        tcp  = df['is_tcp'].sum()
        udp  = df['is_udp'].sum()
        icmp = df['is_icmp'].sum()
        f.write(f"  {lbl}: TCP={tcp/n*100:.1f}%  UDP={udp/n*100:.1f}%  ICMP={icmp/n*100:.1f}%\n")

print(f"  Guardado: {stats_path}")

# ─── Gráficas ─────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    CLR_A = '#1f77b4'   # azul
    CLR_B = '#d62728'   # rojo
    CLR_C = '#2ca02c'   # verde
    ALPHA = 0.70

    print("\n[3] Generando gráficas...")

    # ── Gráfica 1: Distribuciones KDE por grupo ──────────────────────────────
    feat_labels = {
        'pkt_rate':     'pkt_rate (pkt/s)',
        'byte_rate':    'byte_rate (B/s)',
        'duration':     'duration (s)',
        'pkt_ratio':    'pkt_ratio (toserver/toclient+1)',
        'byte_ratio':   'byte_ratio (bytes_toserver/toclient+1)',
        'avg_pkt_size': 'avg_pkt_size (B/pkt)',
    }
    feats_plot = list(feat_labels.keys())

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle('Distribuciones de Features por Grupo — Grupo A (Normal) vs B (Anómalo) vs C (Mixto)',
                 fontweight='bold', fontsize=12)

    for ax, feat in zip(axes.flat, feats_plot):
        for df, color, label in [(dfA_s, CLR_A, 'A-Normal'), (dfB_s, CLR_B, 'B-Anómalo'), (dfC_s, CLR_C, 'C-Mixto')]:
            vals = df[feat].values
            vals = vals[vals > 0]
            if len(vals) < 10:
                continue
            log_vals = np.log10(vals + 1e-9)
            ax.hist(log_vals, bins=60, density=True, color=color,
                    alpha=0.45, label=label, histtype='stepfilled')
            ax.hist(log_vals, bins=60, density=True, color=color,
                    alpha=0.9, histtype='step', lw=1.5)
        ax.set_title(feat_labels[feat], fontsize=9, fontweight='bold')
        ax.set_xlabel('log₁₀(valor)', fontsize=8)
        ax.set_ylabel('Densidad', fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_01_distribuciones.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    # ── Gráfica 2: Protocolo por grupo ────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))

    groups  = ['A — Normal', 'B — Anómalo', 'C — Mixto']
    dfs     = [dfA, dfB, dfC]   # stats de protocolo en datos completos
    tcp_pct  = [df['is_tcp'].mean()*100 for df in dfs]
    udp_pct  = [df['is_udp'].mean()*100 for df in dfs]
    icmp_pct = [df['is_icmp'].mean()*100 for df in dfs]
    other_pct = [100 - t - u - i for t,u,i in zip(tcp_pct, udp_pct, icmp_pct)]

    x = np.arange(len(groups))
    w = 0.5
    bottom = np.zeros(len(groups))
    for vals, color, label in [
        (tcp_pct,   '#1f77b4', 'TCP'),
        (udp_pct,   '#ff7f0e', 'UDP'),
        (icmp_pct,  '#2ca02c', 'ICMP'),
        (other_pct, '#aec7e8', 'Otro'),
    ]:
        vals = np.array(vals)
        ax.bar(x, vals, w, bottom=bottom, label=label, alpha=0.87)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v > 3:
                ax.text(i, b + v/2, f'{v:.1f}%', ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white')
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=11)
    ax.set_ylabel('Porcentaje de flows (%)', fontsize=10)
    ax.set_title('Distribución de Protocolo por Grupo\n(TCP · UDP · ICMP)', fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(0, 108)
    ax.grid(axis='y', alpha=0.3)

    # Agregar n= debajo de cada barra
    for i, (lbl, df) in enumerate(zip(groups, dfs)):
        ax.text(i, -7, f'n={len(df):,}', ha='center', va='top', fontsize=8, color='gray')

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_02_protocolo.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    # ── Gráfica 3: Boxplots A vs B ────────────────────────────────────────────
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('Boxplots A (Normal) vs B (Anómalo) — escala log₁₀', fontweight='bold', fontsize=12)

    for ax, feat in zip(axes.flat, feats_plot):
        data = []
        labels_box = []
        for df, lbl in [(dfA_s, 'A\nNormal'), (dfB_s, 'B\nAnómalo')]:
            vals = df[feat].values
            vals = vals[vals > 0]
            data.append(np.log10(vals + 1e-9))
            labels_box.append(lbl)

        bp = ax.boxplot(data, labels=labels_box, patch_artist=True,
                        medianprops={'color':'black','lw':2},
                        flierprops={'marker':'.','markersize':1,'alpha':0.3},
                        whiskerprops={'lw':1.2},
                        boxprops={'lw':1.2})
        for patch, color in zip(bp['boxes'], [CLR_A, CLR_B]):
            patch.set_facecolor(color)
            patch.set_alpha(0.65)

        # Mediana real en el título
        med_a = dfA[feat].median()
        med_b = dfB[feat].median()
        ax.set_title(f'{feat}\nmed_A={med_a:.2f}  med_B={med_b:.2f}', fontsize=8, fontweight='bold')
        ax.set_ylabel('log₁₀(valor)', fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_03_boxplots.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    # ── Gráfica 4: Heatmap correlación ────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle('Correlación de Pearson entre Features\nGrupo A (Normal) vs Grupo B (Anómalo)',
                 fontweight='bold', fontsize=12)

    feat_short = ['pkts_srv','pkts_cli','bytes_srv','bytes_cli',
                  'dur','pkt_rt','byte_rt','pkt_ra','byte_ra',
                  'avg_pkt','tcp','udp','icmp','port']

    for ax, df, lbl, cmap in [(ax1, dfA_s, 'Grupo A — Normal', 'Blues'),
                               (ax2, dfB_s, 'Grupo B — Anómalo', 'Reds')]:
        corr = df[FEATURES_ALL].corr()
        corr.columns = feat_short
        corr.index   = feat_short
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap='RdBu_r', aspect='auto')
        ax.set_xticks(range(14)); ax.set_yticks(range(14))
        ax.set_xticklabels(feat_short, rotation=45, ha='right', fontsize=7)
        ax.set_yticklabels(feat_short, fontsize=7)
        for i in range(14):
            for j in range(14):
                v = corr.values[i,j]
                ax.text(j, i, f'{v:.1f}', ha='center', va='center',
                        fontsize=5.5, color='black' if abs(v)<0.7 else 'white')
        ax.set_title(lbl, fontweight='bold', fontsize=10)
        plt.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_04_correlacion.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    # ── Gráfica 5: Top 10 puertos destino ─────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Top 10 Puertos Destino por Grupo', fontweight='bold', fontsize=12)

    port_labels = {22:'SSH', 80:'HTTP', 443:'HTTPS', 8080:'HTTP-alt',
                   53:'DNS', 0:'ICMP', 3306:'MySQL', 21:'FTP', 25:'SMTP', 3389:'RDP'}

    for ax, df, lbl, color in [
        (axes[0], dfA_s, 'A — Normal',  CLR_A),
        (axes[1], dfB_s, 'B — Anómalo', CLR_B),
        (axes[2], dfC_s, 'C — Mixto',   CLR_C),
    ]:
        top = df['dest_port'].value_counts().head(10)
        ports = [str(p) + f'\n({port_labels.get(p,"")})' if p in port_labels else str(p)
                 for p in top.index]
        ax.barh(range(len(top)), top.values, color=color, alpha=0.8)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(ports, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel('Número de flows', fontsize=9)
        ax.set_title(lbl, fontweight='bold', fontsize=10)
        ax.grid(axis='x', alpha=0.3)
        # Agregar valores
        for i, v in enumerate(top.values):
            ax.text(v * 1.01, i, f'{v:,}', va='center', fontsize=7)

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_05_dest_ports.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    # ── Gráfica 6: Tabla estadísticas ─────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis('off')

    col_labels = ['Feature', 'A media', 'A mediana', 'A skew', 'B media', 'B mediana', 'B skew', 'Ratio med', 'Discrimina']
    table_data = []
    for feat in FEATURES_CONT:
        med_a = dfA[feat].median()
        med_b = dfB[feat].median()
        ratio = med_b / med_a if med_a > 0 else float('inf')
        table_data.append([
            feat,
            f'{dfA[feat].mean():.2f}',
            f'{med_a:.2f}',
            f'{dfA[feat].skew():.1f}',
            f'{dfB[feat].mean():.2f}',
            f'{med_b:.2f}',
            f'{dfB[feat].skew():.1f}',
            f'{ratio:.1f}×',
            '✅',
        ])

    tbl = ax.table(cellText=table_data, colLabels=col_labels,
                   loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.9)

    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(color='white', fontweight='bold')
        elif col == 0:
            cell.set_facecolor('#eaf0fb')
            cell.set_text_props(fontweight='bold')
        elif col in (7,):
            val = table_data[row-1][7] if row > 0 else ''
            try:
                v = float(val.replace('×',''))
                if v > 10:
                    cell.set_facecolor('#fde8e8')
                elif v < 0.3:
                    cell.set_facecolor('#fde8e8')
            except:
                pass
        elif row % 2 == 0:
            cell.set_facecolor('#f8f9fa')

    ax.set_title('Estadísticas Descriptivas — Grupo A (Normal) vs Grupo B (Anómalo)\n'
                 'PPI UPeU 2026 — 14 features × Mann-Whitney p<0.001',
                 fontweight='bold', fontsize=11, pad=20)

    plt.tight_layout()
    p = os.path.join(OUT_DIR, 'eda_06_stats_tabla.png')
    plt.savefig(p, dpi=150)
    plt.close()
    print(f"  ✓ {p}")

    print(f"\n[4] Todas las gráficas en: {OUT_DIR}/")

except Exception as e:
    import traceback
    print(f"\n[ERROR] matplotlib: {e}")
    traceback.print_exc()

# ─── Resumen final en consola ─────────────────────────────────────────────────
print("\n" + "="*65)
print("RESUMEN EDA")
print("="*65)
print(f"  Grupo A (Normal):  {len(dfA):>8,} flows | {len(gz_A)} archivos")
print(f"  Grupo B (Anómalo): {len(dfB):>8,} flows | {len(gz_B)} archivos")
print(f"  Grupo C (Mixto):   {len(dfC):>8,} flows | {len(gz_C)} archivos")
print(f"\n  Feature más discriminante: byte_ratio")
print(f"    A mediana = {dfA['byte_ratio'].median():.3f}")
print(f"    B mediana = {dfB['byte_ratio'].median():.3f}")
print(f"    Ratio     = {dfB['byte_ratio'].median()/dfA['byte_ratio'].median():.1f}×")
print(f"\n  Protocolo Grupo A: TCP={dfA['is_tcp'].mean()*100:.1f}%  UDP={dfA['is_udp'].mean()*100:.1f}%  ICMP={dfA['is_icmp'].mean()*100:.1f}%")
print(f"  Protocolo Grupo B: TCP={dfB['is_tcp'].mean()*100:.1f}%  UDP={dfB['is_udp'].mean()*100:.1f}%  ICMP={dfB['is_icmp'].mean()*100:.1f}%")
print("\n=== EDA completado ===")
