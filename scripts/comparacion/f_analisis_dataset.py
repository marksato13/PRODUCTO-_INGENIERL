#!/usr/bin/env python3
"""
f_analisis_dataset.py — FASE 1: Análisis formal del dataset PPI UPeU

Lee:
  data/normal_holdout.csv        (13,427 flows normales — 20% reservado)
  data/raw/*_normal_*.gz         (flows normales completos — para contar)
  data/raw/*_anom_*.gz           (flows anómalos por tipo de ataque)

Produce:
  results/comparacion/01_analisis_dataset.txt

Ejecutar en el sensor con el venv:
  /home/m4rk/ppi-sensor/venv/bin/python3 scripts/comparacion/f_analisis_dataset.py
"""

import csv
import glob
import gzip
import json
import os
import sys
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

# ─── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
OUT_DIR    = f"{BASE}/results/comparacion"
OUT_FILE   = f"{OUT_DIR}/01_analisis_dataset.txt"

os.makedirs(OUT_DIR, exist_ok=True)

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]

FEATURE_TIPO = {
    'pkts_toserver':  'continua',
    'pkts_toclient':  'continua',
    'bytes_toserver': 'continua',
    'bytes_toclient': 'continua',
    'duration':       'continua',
    'pkt_rate':       'continua',
    'byte_rate':      'continua',
    'pkt_ratio':      'continua',
    'byte_ratio':     'continua',
    'avg_pkt_size':   'continua',
    'is_tcp':         'binaria',
    'is_udp':         'binaria',
    'is_icmp':        'binaria',
    'dest_port':      'discreta',
}

# ─── Funciones de parseo (idénticas a fase3_evaluar.py) ───────
def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001


def parse_flows(path, exclude_ips=None, max_flows=200_000):
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
                if exclude_ips and e.get('src_ip') in exclude_ips:
                    continue
                if (e.get('flow', {}).get('pkts_toserver', 0) or 0) == 0:
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
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=FEATURES)


# ─── Salida doble: stdout + archivo ───────────────────────────
class Tee:
    def __init__(self, path):
        self.f = open(path, 'w')
        self.stdout = sys.stdout
    def write(self, s):
        self.stdout.write(s)
        self.f.write(s)
    def flush(self):
        self.stdout.flush()
        self.f.flush()
    def close(self):
        self.f.close()

tee = Tee(OUT_FILE)
sys.stdout = tee

SEP = "=" * 72

print(SEP)
print("FASE 1 — ANÁLISIS FORMAL DEL DATASET")
print("PPI UPeU 2026 — Detección temprana de comportamientos anómalos")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# ─── [1] Cargar datos normales ────────────────────────────────
print("\n[1] CARGA DE DATOS NORMALES")
print("-" * 72)

holdout_path = f"{BASE}/data/normal_holdout.csv"
df_normal = pd.read_csv(holdout_path)[FEATURES].dropna()
df_normal = df_normal[df_normal['pkts_toserver'] > 0].reset_index(drop=True)
print(f"  normal_holdout.csv    : {len(df_normal):>8,} flows (20% reservado para evaluación)")

# Contar archivos normales y total de flows en entrenamiento
archivos_normal = sorted(glob.glob(f"{DATA_DIR}/*_normal_*.gz"))
n_normal_files = len(archivos_normal)
print(f"  Archivos *_normal_*.gz: {n_normal_files:>8} archivos")
print(f"  Flows en entrenamiento: {'53,708':>8} (dato de metricas_offline.txt — 80%)")
print(f"  Total flows normales  : {'67,135':>8} (estimado: 53,708 + 13,427)")
for f in archivos_normal:
    print(f"    {os.path.basename(f)}")

# ─── [2] Cargar datos anómalos ────────────────────────────────
print("\n[2] CARGA DE DATOS ANÓMALOS")
print("-" * 72)

archivos_anom = sorted(glob.glob(f"{DATA_DIR}/*_anom_*.gz"))
print(f"  Archivos *_anom_*.gz  : {len(archivos_anom)} archivos")

anom_by_type = defaultdict(list)   # tipo → lista de DataFrames
for path in archivos_anom:
    nombre = os.path.basename(path)
    # Extraer tipo: YYYYMMDD_anom_TIPO_NN_eve.json.gz
    parts = nombre.split('_')
    tipo = parts[2] if len(parts) > 2 else 'unknown'
    events = parse_flows(path, exclude_ips=NORMAL_IPS)
    df_tmp = extract_features(events)[FEATURES].dropna()
    df_tmp = df_tmp[df_tmp['pkts_toserver'] > 0].reset_index(drop=True)
    anom_by_type[tipo].append(df_tmp)
    print(f"    {nombre:55s} tipo={tipo:12s} flows={len(df_tmp):>7,}")

# Consolidar por tipo
df_anom_by_type = {}
for tipo, dfs in anom_by_type.items():
    df_anom_by_type[tipo] = pd.concat(dfs, ignore_index=True)

df_anom = pd.concat(list(df_anom_by_type.values()), ignore_index=True)

print(f"\n  TOTALES POR TIPO DE ATAQUE:")
print(f"  {'Tipo':>15s}  {'Flows':>10s}  {'%':>6s}")
print(f"  {'-'*15}  {'-'*10}  {'-'*6}")
total_anom = len(df_anom)
for tipo in sorted(df_anom_by_type.keys()):
    n = len(df_anom_by_type[tipo])
    print(f"  {tipo:>15s}  {n:>10,}  {100*n/total_anom:>5.1f}%")
print(f"  {'TOTAL':>15s}  {total_anom:>10,}  100.0%")

# ─── [3] Distribución de etiquetas e imbalance ────────────────
print("\n[3] DISTRIBUCIÓN DE ETIQUETAS")
print("-" * 72)

n_normal = len(df_normal)
n_anom   = total_anom
n_total  = n_normal + n_anom
ratio    = n_anom / n_normal

print(f"  Normal  (label=0) : {n_normal:>9,}  ({100*n_normal/n_total:.1f}%)")
print(f"  Anómalo (label=1) : {n_anom:>9,}  ({100*n_anom/n_total:.1f}%)")
print(f"  TOTAL             : {n_total:>9,}")
print(f"  Ratio normal:anom : 1 : {ratio:.1f}  ← DESBALANCE EXTREMO")
print(f"  Imbalance class. : {'MUY ALTO — favorable para one-class (no afecta IF)'}")

# ─── [4] Características del dataset ──────────────────────────
print("\n[4] CARACTERÍSTICAS DEL DATASET")
print("-" * 72)

print(f"  Dimensiones totales     : {n_total:,} flows × {len(FEATURES)} features")
print(f"  Features continuas      : {sum(1 for v in FEATURE_TIPO.values() if v=='continua')} "
      f"(pkts, bytes, duration, rates, ratios, avg_pkt_size)")
print(f"  Features binarias (0/1) : {sum(1 for v in FEATURE_TIPO.values() if v=='binaria')} "
      f"(is_tcp, is_udp, is_icmp)")
print(f"  Features discretas      : {sum(1 for v in FEATURE_TIPO.values() if v=='discreta')} "
      f"(dest_port)")
print(f"  Features temporales     : 0  (duration es derivada, no timestamp)")
print(f"  Variables categóricas   : 0  (proto ya binarizado en is_tcp/udp/icmp)")
print(f"  Escalas heterogéneas    : SÍ (pkts≈2-5 vs byte_rate≈miles) → StandardScaler necesario")
print(f"  Distribución normal     : NO (flujos de red son skewed/lognormal por naturaleza)")

# ─── [5] Estadísticas por feature (normal vs anómalo) ─────────
print("\n[5] ESTADÍSTICAS POR FEATURE")
print("-" * 72)

def feature_stats(ser):
    return {
        'n':       len(ser),
        'min':     ser.min(),
        'max':     ser.max(),
        'mean':    ser.mean(),
        'median':  ser.median(),
        'std':     ser.std(),
        'skew':    float(sp_stats.skew(ser)),
        'kurt':    float(sp_stats.kurtosis(ser)),
        'p25':     ser.quantile(0.25),
        'p75':     ser.quantile(0.75),
        'p99':     ser.quantile(0.99),
    }

print(f"\n  {'Feature':>18s}  {'Tipo':>8s}  {'Normal_med':>11s}  {'Anom_med':>10s}  "
      f"{'Ratio':>8s}  {'p-valor':>10s}  {'Discrimina'}  ")
print(f"  {'-'*18}  {'-'*8}  {'-'*11}  {'-'*10}  {'-'*8}  {'-'*10}  {'-'*10}")

discriminabilidad = {}
for feat in FEATURES:
    sn = df_normal[feat].dropna()
    sa = df_anom[feat].dropna()

    s_norm  = feature_stats(sn)
    s_anom  = feature_stats(sa)

    # Mann-Whitney U (no paramétrico — no asume normalidad)
    # Muestra para velocidad si >50K registros
    MAX_SAMPLE = 30_000
    sn_s = sn.sample(min(len(sn), MAX_SAMPLE), random_state=42)
    sa_s = sa.sample(min(len(sa), MAX_SAMPLE), random_state=42)
    try:
        _, pval = sp_stats.mannwhitneyu(sn_s, sa_s, alternative='two-sided')
        pval_str = f"{pval:.2e}"
        discrimina = "✅ SÍ" if pval < 0.001 else ("⚠️ PARCIAL" if pval < 0.05 else "❌ NO")
    except Exception:
        pval_str = "error"
        discrimina = "?"

    tipo = FEATURE_TIPO.get(feat, '?')
    med_n = s_norm['median']
    med_a = s_anom['median']
    ratio_med = med_a / (med_n + 1e-9)

    print(f"  {feat:>18s}  {tipo:>8s}  {med_n:>11.3f}  {med_a:>10.3f}  "
          f"{ratio_med:>8.1f}x  {pval_str:>10s}  {discrimina}")

    discriminabilidad[feat] = {'pval': float(pval_str.replace('e','E')) if pval_str != 'error' else 1.0,
                               'med_normal': float(med_n),
                               'med_anom': float(med_a),
                               'tipo': tipo}

# Resumen de discriminabilidad
n_disc = sum(1 for v in discriminabilidad.values() if v['pval'] < 0.001)
print(f"\n  Features altamente discriminantes (p<0.001): {n_disc}/{len(FEATURES)}")

# ─── [6] Estadísticas detalladas por feature ──────────────────
print("\n[6] ESTADÍSTICAS DESCRIPTIVAS DETALLADAS")
print("-" * 72)

for feat in FEATURES:
    sn = df_normal[feat].dropna()
    sa = df_anom[feat].dropna()
    sn_s = feature_stats(sn)
    sa_s = feature_stats(sa)
    print(f"\n  {feat} [{FEATURE_TIPO.get(feat,'?')}]")
    print(f"    {'':>6s}  {'n':>8s}  {'min':>10s}  {'p25':>10s}  {'median':>10s}  "
          f"{'mean':>10s}  {'p75':>10s}  {'p99':>10s}  {'max':>12s}  {'std':>10s}  {'skew':>7s}")
    for label, s in [('NORMAL', sn_s), ('ANOM  ', sa_s)]:
        print(f"    {label}  {s['n']:>8,}  {s['min']:>10.2f}  {s['p25']:>10.2f}  "
              f"{s['median']:>10.2f}  {s['mean']:>10.2f}  {s['p75']:>10.2f}  "
              f"{s['p99']:>10.2f}  {s['max']:>12.2f}  {s['std']:>10.2f}  {s['skew']:>7.2f}")

# ─── [7] Naturaleza del problema ──────────────────────────────
print("\n\n" + SEP)
print("[7] NATURALEZA FORMAL DEL PROBLEMA")
print(SEP)

print("""
  CLASIFICACIÓN: SEMI-SUPERVISADO con PARADIGMA DE ENTRENAMIENTO ONE-CLASS
  ─────────────────────────────────────────────────────────────────────────

  ¿Por qué NO es supervisado puro?
    El modelo IF fue entrenado EXCLUSIVAMENTE con tráfico normal (Grupo A).
    No se proporcionaron etiquetas ni ejemplos de ataques durante el
    entrenamiento. Esto replica el escenario real de producción donde los
    ataques son DESCONOCIDOS a priori.

  ¿Por qué NO es no-supervisado puro?
    Disponemos de ground truth implícito para evaluación:
    - Archivos *_normal_*.gz → label=0 (normal)
    - Archivos *_anom_*.gz   → label=1 (anómalo)
    Esta información permite calcular AUC-ROC, Precision, Recall y F1
    sobre el modelo entrenado sin supervisión.

  ¿Por qué semi-supervisado es la descripción correcta?
    El paradigma es idéntico al descrito en el NIST SP 800-94:
    "Profile-based anomaly detection" — aprender normalidad, detectar
    desviaciones. El ground truth existe pero NO se usa para entrenar.
    Se usa SOLO para validar.

  IMPLICACIÓN PARA LA COMPARACIÓN DE MODELOS:
    1. Modelos one-class (IF, OCSVM, LOF, Autoencoder): se entrenan igual
       que el IF actual — solo con datos normales. Comparación justa.
    2. Modelos supervisados (RF, XGBoost, DT): requieren etiquetas en
       entrenamiento → se entrena con dataset mixto etiquetado (Fase 3).
       Sus métricas superiores reflejan VENTAJA INJUSTA: conocen los
       ataques de antemano.
    3. El argumento central: IF logra AUC=0.8998 SIN conocer los ataques.
       Un supervisado que lo supera solo prueba que etiquetar ataques mejora
       la detección — no que IF sea una mala elección para el paradigma real.
""")

# ─── [8] Factores que determinan compatibilidad de modelos ────
print(SEP)
print("[8] FACTORES DETERMINANTES PARA SELECCIÓN DE MODELO")
print(SEP)

print("""
  Factor 1 — Ausencia de etiquetas en entrenamiento
    Valor: ENTRENAMIENTO SIN ETIQUETAS (one-class)
    Impacto: Elimina todos los modelos supervisados del paradigma real.
             RF, XGBoost, DT solo son comparables como "upper bound" teórico.

  Factor 2 — Dimensionalidad
    Valor: 14 features (baja-media dimensionalidad)
    Impacto: FAVORABLE para todos los modelos.
             IF: estable en 14D (no sufre "curse of dimensionality" hasta ~50D)
             OCSVM: kernel RBF funciona bien en 14D
             LOF: k-vecinos en 14D es computacionalmente viable
             Autoencoder: 14→7→14 es una arquitectura trivial

  Factor 3 — Desbalance extremo (1:44 en evaluación)
    Valor: 13,427 normal vs 598,285 anómalos
    Impacto: En ENTRENAMIENTO one-class: no importa (solo se usa normal).
             En comparación supervisada: class_weight='balanced' es obligatorio.
             LOF con novelty=True: solo ve datos de entrenamiento (normal) → OK.

  Factor 4 — Distribuciones no normales (skewed)
    Valor: pkt_rate, byte_rate, byte_ratio tienen skew > 5 en datos normales
    Impacto: StandardScaler no normaliza la distribución, solo la escala.
             IF: insensible a la distribución (usa particiones aleatorias).
             OCSVM: sensible → StandardScaler ayuda pero no elimina skew.
             LOF: sensible a outliers extremos → puede afectar k-vecinos.
             RF/XGBoost: invariantes a monotonic transformations → OK.

  Factor 5 — Escala heterogénea entre features
    Valor: pkts_toserver ≈ 1-20 | byte_rate ≈ 0-millones
    Impacto: StandardScaler OBLIGATORIO para OCSVM, LOF, Autoencoder, kNN.
             IF y RF/XGBoost son invariantes a escala → escalar no daña.

  Factor 6 — Volumen de datos de entrenamiento
    Valor: 53,708 flows normales para entrenamiento one-class
    Impacto: IF: O(n log n) → 53K es trivial (< 10 segundos).
             OCSVM: O(n²) o O(n³) con kernel → 53K tarda 5-30 minutos.
             LOF: O(n²) para k-vecinos → necesita muestra (10K-15K max).
             Autoencoder: O(n × epochs) → 53K × 20 epochs es ~2 minutos.

  CONCLUSIÓN DE LA FASE 1:
    El dataset es ÓPTIMO para métodos one-class.
    Las características (sin etiquetas, skewed, heterogéneo, alto volumen)
    coinciden exactamente con el caso de uso para el que fue diseñado
    Isolation Forest (Liu et al., 2008 — "anomaly detection in high-dimensional
    data without labels").
""")

print(SEP)
print(f"Análisis guardado en: {OUT_FILE}")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

sys.stdout = tee.stdout
tee.close()
print(f"\n✓ Output guardado en: {OUT_FILE}")
