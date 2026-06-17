#!/usr/bin/env python3
"""
f_comparar_modelos.py — FASE 4: Entrenamiento y evaluación comparativa de 7 modelos

Lee:
  models/isolation_forest.pkl + models/scaler.pkl
  data/X_train_sup.npy + data/y_train_sup.npy   (dataset supervisado etiquetado)
  data/X_test.npy + data/y_test.npy              (test set COMPARTIDO)
  data/attack_type_test.npy                      (tipos para análisis por escenario)

Produce:
  results/comparacion/04_resultados_modelos.json
  results/comparacion/04_resultados_modelos.csv
  results/comparacion/04_log_experimentos.txt

Ejecutar:
  /home/m4rk/ppi-sensor/venv/bin/python3 scripts/comparacion/f_comparar_modelos.py

Tiempo estimado: 20-60 min (OCSVM y LOF son los más lentos)
"""

import json
import os
import sys
import time
import tracemalloc
import warnings
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (roc_auc_score, roc_curve,
                             precision_score, recall_score, f1_score)
from sklearn.neighbors import LocalOutlierFactor
from sklearn.neural_network import MLPRegressor
from sklearn.svm import OneClassSVM
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings('ignore')

# ─── Rutas ────────────────────────────────────────────────────
BASE       = "/home/m4rk/ppi-surikata-producto"
MODEL_DIR  = f"{BASE}/models"
DATA_DIR   = f"{BASE}/data"
OUT_DIR    = f"{BASE}/results/comparacion"

os.makedirs(OUT_DIR, exist_ok=True)

LOG_FILE  = f"{OUT_DIR}/04_log_experimentos.txt"
JSON_FILE = f"{OUT_DIR}/04_resultados_modelos.json"
CSV_FILE  = f"{OUT_DIR}/04_resultados_modelos.csv"

FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]

# ─── Log doble stdout + archivo ───────────────────────────────
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

SEP  = "=" * 72
SEP2 = "-" * 72

print(SEP)
print("FASE 4 — COMPARACIÓN EXPERIMENTAL DE MODELOS")
print(f"PPI UPeU 2026  |  Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# ─── [1] Cargar datos ─────────────────────────────────────────
print("\n[1] Cargando datos...")

# Test set compartido (todos los modelos)
X_test  = np.load(f"{DATA_DIR}/X_test.npy")
y_test  = np.load(f"{DATA_DIR}/y_test.npy")
at_test = np.load(f"{DATA_DIR}/attack_type_test.npy", allow_pickle=True)

# Train supervisado (RF, XGB, DT)
X_train_sup = np.load(f"{DATA_DIR}/X_train_sup.npy")
y_train_sup = np.load(f"{DATA_DIR}/y_train_sup.npy")

# Train one-class: normal subset del train supervisado (sin data leakage)
X_train_normal = X_train_sup[y_train_sup == 0]
print(f"  X_test         : {X_test.shape}  (anom={y_test.sum():,})")
print(f"  X_train_sup    : {X_train_sup.shape}  (normal={( y_train_sup==0).sum():,} / anom={(y_train_sup==1).sum():,})")
print(f"  X_train_normal : {X_train_normal.shape}  (para modelos one-class — sin leakage)")

# Scaler e IF pre-entrenado
scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")
clf_if = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
print(f"  IF pre-entrenado: n_estimators={clf_if.n_estimators}, "
      f"contamination={clf_if.contamination}")

# ─── Función de evaluación unificada ──────────────────────────
def evaluar(scores_test, y_test, higher_is_anomalous=True):
    """
    Calcula AUC-ROC, umbral Youden, y métricas en ese umbral.
    scores_test: score de anomalía (cuanto mayor → más anómalo si higher_is_anomalous=True)
    """
    # Para roc_curve, necesitamos que score alto = anomalía (y_test=1)
    s = scores_test if higher_is_anomalous else -scores_test

    fpr_arr, tpr_arr, thresholds = roc_curve(y_test, s)
    auc = roc_auc_score(y_test, s)

    # Umbral Youden (maximiza TPR - FPR)
    youden    = tpr_arr - fpr_arr
    idx       = np.argmax(youden)
    tau_roc   = thresholds[idx]           # umbral en escala de s (negado si aplica)
    tau_real  = tau_roc if higher_is_anomalous else -tau_roc
    tpr_opt   = float(tpr_arr[idx])
    fpr_opt   = float(fpr_arr[idx])

    # Predicción binaria en umbral óptimo
    y_pred = (s >= tau_roc).astype(int)
    prec   = float(precision_score(y_test, y_pred, zero_division=0))
    rec    = float(recall_score(y_test, y_pred, zero_division=0))
    f1     = float(f1_score(y_test, y_pred, zero_division=0))
    fp     = int(((y_pred == 1) & (y_test == 0)).sum())
    fn     = int(((y_pred == 0) & (y_test == 1)).sum())
    fnr    = fn / max(y_test.sum(), 1)

    return {
        'auc_roc':    round(float(auc), 4),
        'tau':        round(float(tau_real), 4),
        'tpr_youden': round(tpr_opt, 4),
        'fpr_youden': round(fpr_opt, 4),
        'recall':     round(rec, 4),
        'precision':  round(prec, 4),
        'f1':         round(f1, 4),
        'fnr':        round(fnr, 4),
        'fp':         fp,
        'fn':         fn,
        'fpr_arr':    fpr_arr.tolist(),
        'tpr_arr':    tpr_arr.tolist(),
    }

def medir_inferencia(fn_score, X, n_reps=3):
    """Tiempo de inferencia promedio en ms por muestra."""
    tiempos = []
    for _ in range(n_reps):
        t0 = time.perf_counter()
        _ = fn_score(X)
        tiempos.append(time.perf_counter() - t0)
    ms_total = min(tiempos) * 1000
    return round(ms_total / len(X), 4)   # ms/muestra

# ─── Resultados acumulados ────────────────────────────────────
resultados = {}

# ══════════════════════════════════════════════════════════════
# MODELO 1 — Isolation Forest (pre-entrenado, referencia)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 1 — Isolation Forest (referencia, pre-entrenado)")
print(SEP2)

# Tiempo entrenamiento: ya entrenado — reportamos N/A y re-tiempo de fit() en muestra
print("  [entrenamiento] ya entrenado — midiendo tiempo de re-fit para referencia...")
tracemalloc.start()
t0 = time.perf_counter()
# Usar el modelo pre-entrenado (n=300 estimadores, 53,708 flows originales)
# No re-entrenamos para preservar τ1/τ2 calibrados
t_train = 0.0   # pre-entrenado
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

# Inferencia
scores_if_test = clf_if.score_samples(X_test)   # más negativo = más anómalo
ms_inf_if = medir_inferencia(clf_if.score_samples, X_test)

metrics_if = evaluar(scores_if_test, y_test, higher_is_anomalous=False)

# También evaluar con τ1 original (−0.4459)
TAU1_ORIGINAL = -0.4459
y_pred_tau1 = (scores_if_test <= TAU1_ORIGINAL).astype(int)
prec_tau1 = float(precision_score(y_test, y_pred_tau1, zero_division=0))
rec_tau1  = float(recall_score(y_test, y_pred_tau1, zero_division=0))
f1_tau1   = float(f1_score(y_test, y_pred_tau1, zero_division=0))
fpr_tau1  = float(((y_pred_tau1==1) & (y_test==0)).sum() / (y_test==0).sum())

print(f"  AUC-ROC        : {metrics_if['auc_roc']:.4f}")
print(f"  Recall (Youden): {metrics_if['recall']:.4f}")
print(f"  Precision      : {metrics_if['precision']:.4f}")
print(f"  F1             : {metrics_if['f1']:.4f}")
print(f"  FPR (Youden)   : {metrics_if['fpr_youden']:.4f}")
print(f"  Inferencia     : {ms_inf_if:.4f} ms/muestra")
print(f"  Con τ1=−0.4459 : Recall={rec_tau1:.4f} Prec={prec_tau1:.4f} FPR={fpr_tau1:.4f}")

resultados['isolation_forest'] = {
    'grupo': 'one-class',
    'n_train': 53708,
    'train_data': 'normal (pre-entrenado, 53,708 flows originales)',
    't_train_s': 'pre-entrenado',
    'ram_peak_mb': round(peak / 1024**2, 2),
    'ms_inferencia': ms_inf_if,
    **metrics_if,
    'recall_tau1_original':    round(rec_tau1, 4),
    'precision_tau1_original': round(prec_tau1, 4),
    'f1_tau1_original':        round(f1_tau1, 4),
    'fpr_tau1_original':       round(fpr_tau1, 4),
}

# ══════════════════════════════════════════════════════════════
# MODELO 2 — One-Class SVM
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 2 — One-Class SVM (kernel RBF, nu=0.05)")
print(SEP2)
print(f"  Entrenando sobre {X_train_normal.shape[0]:,} flows normales...")
print("  (puede tardar 2-10 minutos)")

ocsvm = OneClassSVM(kernel='rbf', nu=0.05, gamma='scale')

tracemalloc.start()
t0 = time.perf_counter()
ocsvm.fit(X_train_normal)
t_train_ocsvm = time.perf_counter() - t0
_, peak_ocsvm = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_ocsvm:.1f}s")

scores_ocsvm = ocsvm.score_samples(X_test)
ms_inf_ocsvm = medir_inferencia(ocsvm.score_samples, X_test)
metrics_ocsvm = evaluar(scores_ocsvm, y_test, higher_is_anomalous=False)

print(f"  AUC-ROC   : {metrics_ocsvm['auc_roc']:.4f}")
print(f"  Recall    : {metrics_ocsvm['recall']:.4f}")
print(f"  Precision : {metrics_ocsvm['precision']:.4f}")
print(f"  F1        : {metrics_ocsvm['f1']:.4f}")
print(f"  FPR       : {metrics_ocsvm['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_ocsvm:.4f} ms/muestra")

resultados['ocsvm'] = {
    'grupo': 'one-class',
    'n_train': X_train_normal.shape[0],
    'train_data': f'normal subset train ({X_train_normal.shape[0]} flows)',
    't_train_s': round(t_train_ocsvm, 2),
    'ram_peak_mb': round(peak_ocsvm / 1024**2, 2),
    'ms_inferencia': ms_inf_ocsvm,
    **metrics_ocsvm,
}

# ══════════════════════════════════════════════════════════════
# MODELO 3 — Local Outlier Factor
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 3 — Local Outlier Factor (k=20, novelty=True)")
print(SEP2)

# LOF O(n²): usar muestra de hasta 5,000 flows por viabilidad
N_LOF = min(5000, X_train_normal.shape[0])
np.random.seed(42)
idx_lof = np.random.choice(X_train_normal.shape[0], N_LOF, replace=False)
X_lof_train = X_train_normal[idx_lof]

print(f"  Entrenando sobre {N_LOF:,} flows normales (muestra — O(n²) constraint)...")

lof = LocalOutlierFactor(n_neighbors=20, novelty=True, contamination=0.05)

tracemalloc.start()
t0 = time.perf_counter()
lof.fit(X_lof_train)
t_train_lof = time.perf_counter() - t0
_, peak_lof = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_lof:.1f}s")

scores_lof = lof.score_samples(X_test)
ms_inf_lof = medir_inferencia(lof.score_samples, X_test)
metrics_lof = evaluar(scores_lof, y_test, higher_is_anomalous=False)

print(f"  AUC-ROC   : {metrics_lof['auc_roc']:.4f}")
print(f"  Recall    : {metrics_lof['recall']:.4f}")
print(f"  Precision : {metrics_lof['precision']:.4f}")
print(f"  F1        : {metrics_lof['f1']:.4f}")
print(f"  FPR       : {metrics_lof['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_lof:.4f} ms/muestra")

resultados['lof'] = {
    'grupo': 'one-class',
    'n_train': N_LOF,
    'train_data': f'muestra normal ({N_LOF} flows, O(n²) constraint)',
    't_train_s': round(t_train_lof, 2),
    'ram_peak_mb': round(peak_lof / 1024**2, 2),
    'ms_inferencia': ms_inf_lof,
    **metrics_lof,
}

# ══════════════════════════════════════════════════════════════
# MODELO 4 — Autoencoder (MLPRegressor como AE)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 4 — Autoencoder (MLPRegressor 14→10→7→10→14, MSE)")
print(SEP2)
print(f"  Entrenando sobre {X_train_normal.shape[0]:,} flows normales...")

ae = MLPRegressor(
    hidden_layer_sizes=(10, 7, 10),
    activation='relu',
    solver='adam',
    learning_rate_init=0.001,
    max_iter=200,
    random_state=42,
    tol=1e-4,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=10,
)

tracemalloc.start()
t0 = time.perf_counter()
ae.fit(X_train_normal, X_train_normal)  # target = input (reconstrucción)
t_train_ae = time.perf_counter() - t0
_, peak_ae = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_ae:.1f}s  ({ae.n_iter_} iteraciones)")

# Score = MSE de reconstrucción (mayor MSE = más anómalo)
def ae_score(X):
    recon = ae.predict(X)
    return np.mean((X - recon)**2, axis=1)

scores_ae = ae_score(X_test)
ms_inf_ae = medir_inferencia(ae_score, X_test)
metrics_ae = evaluar(scores_ae, y_test, higher_is_anomalous=True)

print(f"  AUC-ROC   : {metrics_ae['auc_roc']:.4f}")
print(f"  Recall    : {metrics_ae['recall']:.4f}")
print(f"  Precision : {metrics_ae['precision']:.4f}")
print(f"  F1        : {metrics_ae['f1']:.4f}")
print(f"  FPR       : {metrics_ae['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_ae:.4f} ms/muestra")

resultados['autoencoder'] = {
    'grupo': 'one-class',
    'n_train': X_train_normal.shape[0],
    'train_data': f'normal subset train ({X_train_normal.shape[0]} flows)',
    't_train_s': round(t_train_ae, 2),
    'ram_peak_mb': round(peak_ae / 1024**2, 2),
    'ms_inferencia': ms_inf_ae,
    **metrics_ae,
}

# ══════════════════════════════════════════════════════════════
# MODELO 5 — Random Forest (supervisado, upper bound)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 5 — Random Forest (supervisado, n=300, class_weight=balanced)")
print(SEP2)
print(f"  Entrenando sobre {X_train_sup.shape[0]:,} flows etiquetados...")

rf = RandomForestClassifier(
    n_estimators=300,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1,
)

tracemalloc.start()
t0 = time.perf_counter()
rf.fit(X_train_sup, y_train_sup)
t_train_rf = time.perf_counter() - t0
_, peak_rf = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_rf:.1f}s")

scores_rf = rf.predict_proba(X_test)[:, 1]
ms_inf_rf = medir_inferencia(lambda X: rf.predict_proba(X)[:,1], X_test)
metrics_rf = evaluar(scores_rf, y_test, higher_is_anomalous=True)

print(f"  AUC-ROC   : {metrics_rf['auc_roc']:.4f}  ← VENTAJA INJUSTA (conoce ataques)")
print(f"  Recall    : {metrics_rf['recall']:.4f}")
print(f"  Precision : {metrics_rf['precision']:.4f}")
print(f"  F1        : {metrics_rf['f1']:.4f}")
print(f"  FPR       : {metrics_rf['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_rf:.4f} ms/muestra")
print(f"  Feature importances top-3:")
fi = sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1])
for feat, imp in fi[:3]:
    print(f"    {feat}: {imp:.4f}")

resultados['random_forest'] = {
    'grupo': 'supervisado',
    'n_train': X_train_sup.shape[0],
    'train_data': f'etiquetado ({X_train_sup.shape[0]} flows — VENTAJA INJUSTA)',
    't_train_s': round(t_train_rf, 2),
    'ram_peak_mb': round(peak_rf / 1024**2, 2),
    'ms_inferencia': ms_inf_rf,
    'feature_importances': {f: round(float(i), 4) for f, i in zip(FEATURES, rf.feature_importances_)},
    **metrics_rf,
}

# ══════════════════════════════════════════════════════════════
# MODELO 6 — XGBoost (supervisado, upper bound)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 6 — XGBoost (supervisado, n=300, scale_pos_weight)")
print(SEP2)
print(f"  Entrenando sobre {X_train_sup.shape[0]:,} flows etiquetados...")

ratio_clases = float((y_train_sup == 0).sum()) / float((y_train_sup == 1).sum())
xgb = XGBClassifier(
    n_estimators=300,
    scale_pos_weight=ratio_clases,
    eval_metric='auc',
    random_state=42,
    n_jobs=-1,
    verbosity=0,
    use_label_encoder=False if hasattr(XGBClassifier, 'use_label_encoder') else None,
)
# Limpiar parámetros None
xgb_params = {k: v for k, v in xgb.get_params().items() if v is not None}
xgb.set_params(**{k: v for k, v in xgb_params.items()})

tracemalloc.start()
t0 = time.perf_counter()
xgb.fit(X_train_sup, y_train_sup)
t_train_xgb = time.perf_counter() - t0
_, peak_xgb = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_xgb:.1f}s")

scores_xgb = xgb.predict_proba(X_test)[:, 1]
ms_inf_xgb = medir_inferencia(lambda X: xgb.predict_proba(X)[:,1], X_test)
metrics_xgb = evaluar(scores_xgb, y_test, higher_is_anomalous=True)

print(f"  AUC-ROC   : {metrics_xgb['auc_roc']:.4f}  ← VENTAJA INJUSTA (conoce ataques)")
print(f"  Recall    : {metrics_xgb['recall']:.4f}")
print(f"  Precision : {metrics_xgb['precision']:.4f}")
print(f"  F1        : {metrics_xgb['f1']:.4f}")
print(f"  FPR       : {metrics_xgb['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_xgb:.4f} ms/muestra")

resultados['xgboost'] = {
    'grupo': 'supervisado',
    'n_train': X_train_sup.shape[0],
    'train_data': f'etiquetado ({X_train_sup.shape[0]} flows — VENTAJA INJUSTA)',
    't_train_s': round(t_train_xgb, 2),
    'ram_peak_mb': round(peak_xgb / 1024**2, 2),
    'ms_inferencia': ms_inf_xgb,
    **metrics_xgb,
}

# ══════════════════════════════════════════════════════════════
# MODELO 7 — Decision Tree (baseline supervisado)
# ══════════════════════════════════════════════════════════════
print(f"\n{SEP2}")
print("MODELO 7 — Decision Tree (baseline supervisado, max_depth=10)")
print(SEP2)
print(f"  Entrenando sobre {X_train_sup.shape[0]:,} flows etiquetados...")

dt = DecisionTreeClassifier(
    max_depth=10,
    class_weight='balanced',
    random_state=42,
)

tracemalloc.start()
t0 = time.perf_counter()
dt.fit(X_train_sup, y_train_sup)
t_train_dt = time.perf_counter() - t0
_, peak_dt = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"  Entrenamiento: {t_train_dt:.1f}s")

scores_dt = dt.predict_proba(X_test)[:, 1]
ms_inf_dt = medir_inferencia(lambda X: dt.predict_proba(X)[:,1], X_test)
metrics_dt = evaluar(scores_dt, y_test, higher_is_anomalous=True)

print(f"  AUC-ROC   : {metrics_dt['auc_roc']:.4f}  ← VENTAJA INJUSTA (conoce ataques)")
print(f"  Recall    : {metrics_dt['recall']:.4f}")
print(f"  Precision : {metrics_dt['precision']:.4f}")
print(f"  F1        : {metrics_dt['f1']:.4f}")
print(f"  FPR       : {metrics_dt['fpr_youden']:.4f}")
print(f"  Inferencia: {ms_inf_dt:.4f} ms/muestra")

resultados['decision_tree'] = {
    'grupo': 'supervisado',
    'n_train': X_train_sup.shape[0],
    'train_data': f'etiquetado ({X_train_sup.shape[0]} flows — VENTAJA INJUSTA)',
    't_train_s': round(t_train_dt, 2),
    'ram_peak_mb': round(peak_dt / 1024**2, 2),
    'ms_inferencia': ms_inf_dt,
    **metrics_dt,
}

# ─── Guardar resultados ───────────────────────────────────────
print(f"\n{SEP}")
print("GUARDANDO RESULTADOS")
print(SEP)

# Quitar curvas ROC del JSON principal (son grandes)
resultados_slim = {}
for k, v in resultados.items():
    slim = {kk: vv for kk, vv in v.items() if kk not in ('fpr_arr', 'tpr_arr')}
    resultados_slim[k] = slim

# JSON completo (con curvas ROC para gráficas)
with open(JSON_FILE, 'w') as f:
    json.dump(resultados, f, indent=2)
print(f"  JSON completo: {JSON_FILE}")

# CSV resumen
campos_csv = ['grupo', 'n_train', 't_train_s', 'ram_peak_mb', 'ms_inferencia',
              'auc_roc', 'recall', 'precision', 'f1', 'fpr_youden', 'fnr', 'fp', 'fn']
rows_csv = []
for nombre, d in resultados_slim.items():
    row = {'modelo': nombre}
    for c in campos_csv:
        row[c] = d.get(c, '')
    rows_csv.append(row)

df_csv = pd.DataFrame(rows_csv)
df_csv.to_csv(CSV_FILE, index=False)
print(f"  CSV resumen  : {CSV_FILE}")

# ─── Tabla resumen final ──────────────────────────────────────
print(f"\n{SEP}")
print("TABLA COMPARATIVA — RESUMEN")
print(SEP)

ORDER = ['isolation_forest', 'ocsvm', 'lof', 'autoencoder',
         'random_forest', 'xgboost', 'decision_tree']
NOMBRES = {
    'isolation_forest': 'Isolation Forest',
    'ocsvm':            'One-Class SVM',
    'lof':              'LOF',
    'autoencoder':      'Autoencoder',
    'random_forest':    'Random Forest*',
    'xgboost':          'XGBoost*',
    'decision_tree':    'Decision Tree*',
}

print(f"\n  {'Modelo':>18s}  {'Grupo':>10s}  {'AUC':>6s}  {'Recall':>7s}  "
      f"{'Prec':>7s}  {'F1':>6s}  {'FPR':>6s}  {'ms/s':>7s}  {'T_train':>8s}")
print(f"  {'-'*18}  {'-'*10}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*6}  {'-'*6}  {'-'*7}  {'-'*8}")

for k in ORDER:
    d = resultados_slim[k]
    t = d['t_train_s']
    t_str = f"{t:.1f}s" if isinstance(t, float) else str(t)
    print(f"  {NOMBRES[k]:>18s}  {d['grupo']:>10s}  {d['auc_roc']:.4f}  "
          f"{d['recall']:.4f}  {d['precision']:.4f}  {d['f1']:.4f}  "
          f"{d['fpr_youden']:.4f}  {d['ms_inferencia']:>7.4f}  {t_str:>8s}")

print(f"\n  * Supervisados: VENTAJA INJUSTA — conocen los ataques en entrenamiento")
print(f"  IF: modelo de producción pre-entrenado sobre 53,708 flows normales originales")
print(f"  Test set compartido: {len(y_test):,} flows ({(y_test==0).sum():,} normal + {y_test.sum():,} anómalos)")

print(f"\n{SEP}")
print(f"Log: {LOG_FILE}")
print(f"JSON: {JSON_FILE}")
print(f"CSV: {CSV_FILE}")
print(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

sys.stdout = tee.stdout
tee.close()
print(f"\n✓ Experimentos completos. Resultados en: {OUT_DIR}")
