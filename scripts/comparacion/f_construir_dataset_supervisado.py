#!/usr/bin/env python3
"""
f_construir_dataset_supervisado.py — FASE 3: Construcción del dataset etiquetado

Lee:
  data/normal_holdout.csv          (13,427 flows normales)
  data/raw/*_anom_*.gz             (flows anómalos por tipo)
  models/scaler.pkl                (StandardScaler entrenado sobre datos normales)

Produce:
  data/dataset_comparacion.csv     (dataset completo etiquetado)
  data/X_train_sup.npy             (70% — features train supervisados, escaladas)
  data/X_test.npy                  (30% — features test COMPARTIDO todos los modelos)
  data/y_train_sup.npy             (70% — etiquetas train supervisados)
  data/y_test.npy                  (30% — etiquetas test compartidas)
  data/attack_type_test.npy        (tipo de ataque para análisis por escenario)
  results/comparacion/03_dataset_supervisado.txt  (reporte)

Diseño:
  Normal   (label=0): 13,427 flows de normal_holdout.csv
  Anómalo  (label=1): 2,000 flows por tipo × 6 tipos = 12,000 flows (muestra estratificada)
  Total:              ~25,427 flows | Split: 70% train / 30% test (estratificado)

  El mismo scaler.pkl (entrenado sobre normales) se aplica a TODOS los modelos
  para consistencia y porque replica el pipeline de producción real.

Ejecutar:
  /home/m4rk/ppi-sensor/venv/bin/python3 scripts/comparacion/f_construir_dataset_supervisado.py
"""

import glob
import gzip
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

# ─── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
DATA_DIR   = f"{BASE}/data/raw"
DATA_OUT   = f"{BASE}/data"
MODEL_DIR  = f"{BASE}/models"
OUT_DIR    = f"{BASE}/results/comparacion"
LOG_FILE   = f"{OUT_DIR}/03_dataset_supervisado.txt"

os.makedirs(OUT_DIR, exist_ok=True)

NORMAL_IPS = {'192.168.0.20', '192.168.0.120'}

FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]

SAMPLE_PER_TYPE = 2000  # flows anómalos por tipo de ataque
RANDOM_STATE    = 42
TEST_SIZE       = 0.30

# ─── Log doble ────────────────────────────────────────────────
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

tee = Tee(LOG_FILE)
sys.stdout = tee

SEP = "=" * 72
print(SEP)
print("FASE 3 — CONSTRUCCIÓN DEL DATASET SUPERVISADO")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# ─── Funciones de parseo ──────────────────────────────────────
def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001

def parse_flows(path, exclude_ips=None, max_flows=300_000):
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

# ─── [1] Cargar scaler ────────────────────────────────────────
print("\n[1] Cargando scaler.pkl...")
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")
print(f"  Scaler cargado — media features: {scaler.mean_[:3].round(2)} ...")

# ─── [2] Cargar flows normales ────────────────────────────────
print("\n[2] Cargando flows normales (data/normal_holdout.csv)...")
df_normal = pd.read_csv(f"{DATA_OUT}/normal_holdout.csv")[FEATURES].dropna()
df_normal = df_normal[df_normal['pkts_toserver'] > 0].reset_index(drop=True)
df_normal['label']       = 0
df_normal['attack_type'] = 'normal'
print(f"  Flows normales: {len(df_normal):,}")

# ─── [3] Cargar y muestrear flows anómalos ────────────────────
print(f"\n[3] Cargando flows anómalos (muestra {SAMPLE_PER_TYPE} por tipo)...")

archivos_anom = sorted(glob.glob(f"{DATA_DIR}/*_anom_*.gz"))
from collections import defaultdict
dfs_por_tipo = defaultdict(list)

for path in archivos_anom:
    nombre = os.path.basename(path)
    parts  = nombre.split('_')
    tipo   = parts[2] if len(parts) > 2 else 'unknown'
    events = parse_flows(path, exclude_ips=NORMAL_IPS)
    df_tmp = extract_features(events)[FEATURES].dropna()
    df_tmp = df_tmp[df_tmp['pkts_toserver'] > 0].reset_index(drop=True)
    dfs_por_tipo[tipo].append(df_tmp)
    print(f"  {nombre:55s} tipo={tipo:12s} flows_leidos={len(df_tmp):>7,}")

print(f"\n  Muestreo estratificado ({SAMPLE_PER_TYPE} por tipo):")
dfs_anom = []
resumen_tipos = {}
for tipo in sorted(dfs_por_tipo.keys()):
    df_tipo = pd.concat(dfs_por_tipo[tipo], ignore_index=True)
    n_total = len(df_tipo)
    n_sample = min(SAMPLE_PER_TYPE, n_total)
    df_muestra = df_tipo.sample(n=n_sample, random_state=RANDOM_STATE).reset_index(drop=True)
    df_muestra['label']       = 1
    df_muestra['attack_type'] = tipo
    dfs_anom.append(df_muestra)
    resumen_tipos[tipo] = {'total': n_total, 'muestra': n_sample}
    print(f"    {tipo:>15s}: {n_total:>8,} disponibles → {n_sample:>5,} seleccionados")

df_anom = pd.concat(dfs_anom, ignore_index=True)
print(f"\n  Total anómalos en dataset: {len(df_anom):,}")

# ─── [4] Combinar y estadísticas ─────────────────────────────
print("\n[4] Combinando dataset...")
df_all = pd.concat([df_normal, df_anom], ignore_index=True)
df_all = df_all.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

n_total  = len(df_all)
n_norm   = (df_all['label'] == 0).sum()
n_anom   = (df_all['label'] == 1).sum()
ratio    = n_anom / n_norm

print(f"\n  {'Clase':>10s}  {'Flows':>8s}  {'%':>6s}")
print(f"  {'-'*10}  {'-'*8}  {'-'*6}")
print(f"  {'Normal':>10s}  {n_norm:>8,}  {100*n_norm/n_total:>5.1f}%")
print(f"  {'Anómalo':>10s}  {n_anom:>8,}  {100*n_anom/n_total:>5.1f}%")
print(f"  {'TOTAL':>10s}  {n_total:>8,}  100.0%")
print(f"  Ratio: 1:{ratio:.2f} ({('CASI BALANCEADO' if ratio < 2 else 'DESBALANCEADO')})")

# ─── [5] Guardar dataset_comparacion.csv ─────────────────────
print("\n[5] Guardando data/dataset_comparacion.csv...")
csv_path = f"{DATA_OUT}/dataset_comparacion.csv"
df_all.to_csv(csv_path, index=False)
print(f"  Guardado: {csv_path} ({n_total:,} filas × {len(df_all.columns)} columnas)")

# ─── [6] Split 70/30 estratificado ───────────────────────────
print(f"\n[6] Split estratificado {int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}...")

X = df_all[FEATURES].values
y = df_all['label'].values
at = df_all['attack_type'].values

X_train_raw, X_test_raw, y_train, y_test, at_train, at_test = train_test_split(
    X, y, at,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y
)

print(f"  Train: {len(y_train):,} flows  ({(y_train==0).sum():,} normal / {(y_train==1).sum():,} anómalos)")
print(f"  Test : {len(y_test):,}  flows  ({(y_test==0).sum():,} normal / {(y_test==1).sum():,} anómalos)")

# ─── [7] Escalar con scaler.pkl existente ────────────────────
print("\n[7] Escalando features (scaler.pkl entrenado sobre datos normales)...")
X_train_scaled = scaler.transform(X_train_raw)
X_test_scaled  = scaler.transform(X_test_raw)
print(f"  X_train_scaled: {X_train_scaled.shape}  mean={X_train_scaled.mean():.3f}")
print(f"  X_test_scaled : {X_test_scaled.shape}   mean={X_test_scaled.mean():.3f}")

# ─── [8] Guardar arrays numpy ─────────────────────────────────
print("\n[8] Guardando arrays numpy...")

paths = {
    'X_train_sup':       X_train_scaled,
    'X_test':            X_test_scaled,
    'y_train_sup':       y_train,
    'y_test':            y_test,
    'attack_type_test':  at_test,
    # También guardar sin escalar para referencia
    'X_train_sup_raw':   X_train_raw,
    'X_test_raw':        X_test_raw,
}

for name, arr in paths.items():
    p = f"{DATA_OUT}/{name}.npy"
    np.save(p, arr)
    print(f"  {name:>20s}.npy  shape={arr.shape}")

# ─── [9] Verificación de distribución en test ────────────────
print("\n[9] Distribución en el TEST SET (compartido para todos los modelos)...")
print(f"\n  {'Tipo':>15s}  {'n':>6s}  {'label':>6s}")
print(f"  {'-'*15}  {'-'*6}  {'-'*6}")
tipos_test, counts_test = np.unique(at_test, return_counts=True)
for t, c in zip(tipos_test, counts_test):
    lbl = '0' if t == 'normal' else '1'
    print(f"  {t:>15s}  {c:>6,}  {lbl:>6s}")

# ─── [10] Resumen final ───────────────────────────────────────
print(f"\n{SEP}")
print("RESUMEN DATASET SUPERVISADO")
print(SEP)
print(f"""
  Archivo principal : data/dataset_comparacion.csv
  Total flows       : {n_total:,} ({n_norm:,} normal + {n_anom:,} anómalos)
  Ratio             : 1:{ratio:.2f}
  Tipos de ataque   : {', '.join(sorted(resumen_tipos.keys()))}

  Arrays para modelos (en data/):
    X_train_sup.npy   : {X_train_scaled.shape} — features train supervisados (escaladas)
    X_test.npy        : {X_test_scaled.shape}  — features TEST compartido (escaladas)
    y_train_sup.npy   : {y_train.shape}         — etiquetas train
    y_test.npy        : {y_test.shape}           — etiquetas test
    attack_type_test  : {at_test.shape}          — tipo ataque (análisis por escenario)

  Scaler usado: models/scaler.pkl (entrenado sobre 53,708 flows normales)
  Split: {int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)} estratificado (random_state={RANDOM_STATE})

  INSTRUCCIÓN PARA FASE 4:
    - Modelos ONE-CLASS : entrenan con 53,708 flows normales originales
                          evalúan sobre X_test.npy + y_test.npy
    - Modelos SUPERVISADOS: entrenan con X_train_sup.npy + y_train_sup.npy
                             evalúan sobre X_test.npy + y_test.npy (MISMO test set)
""")

print(f"Output: {LOG_FILE}")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

sys.stdout = tee.stdout
tee.close()
print(f"\n✓ Output guardado en: {LOG_FILE}")
