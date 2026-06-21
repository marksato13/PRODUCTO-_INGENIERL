#!/usr/bin/env python3
"""
entrenar_predictor.py — Fases 0, 1 y 2 del módulo de predicción temporal.

Fase 0: Extrae dataset de gaps desde motor_decision.log
Fase 1: Compara ARIMA vs RandomForest vs XGBoost
Fase 2: Serializa el modelo ganador

Uso:
    python3 scripts/entrenar_predictor.py             # todo
    python3 scripts/entrenar_predictor.py --fase 0   # solo dataset
    python3 scripts/entrenar_predictor.py --fase 1   # solo comparación
    python3 scripts/entrenar_predictor.py --fase 2   # solo serializar
"""
import re, sys, argparse
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

BASE = Path('/home/m4rk/ppi-surikata-producto')
LOG  = BASE / 'results' / 'motor_decision.log'
OUT_CSV   = BASE / 'data'    / 'series_gap_sesiones.csv'
OUT_MODEL = BASE / 'models'  / 'predictor_modelo.pkl'
OUT_TIPO  = BASE / 'models'  / 'predictor_tipo.txt'
OUT_FEATS = BASE / 'models'  / 'features_predictor.txt'
OUT_METR  = BASE / 'results' / 'metricas_predictor.txt'
OUT_COMP  = BASE / 'results' / 'comparacion_predictores.txt'
GRAF_DIR  = BASE / 'results' / 'graficas_predictor'

GRAF_DIR.mkdir(exist_ok=True)

# ─── 3 formatos del log ──────────────────────────────────────────────────────
RE_F3 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bf=\d+ http_abuse=\d+ '
    r'bloqueados=(\d+)'
)
RE_F2 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bloqueados=(\d+) limitados=\d+\s*$'
)
RE_F1 = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=(\d+) bloqueados=(\d+)\s*$'
)
RE_BLOCK = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*WARNING.*BLOCK(?:ED)?\b'
)

def parsear_stats(linea):
    """Retorna (ts, flows, bloqueados) o None."""
    for pat in (RE_F3, RE_F2, RE_F1):
        m = pat.search(linea)
        if m:
            return pd.to_datetime(m.group(1)), int(m.group(2)), int(m.group(4))
    return None

# ─── FASE 0 — Dataset de gaps ────────────────────────────────────────────────
def fase0():
    print("=" * 60)
    print("FASE 0 — Extracción de dataset de gaps")
    print("=" * 60)

    stats_rows = []   # (ts, flows, bloqueados)
    block_ts   = []   # timestamps de BLOCK

    print(f"Parseando {LOG} …")
    with open(LOG, 'r', errors='ignore') as f:
        for linea in f:
            r = parsear_stats(linea)
            if r:
                stats_rows.append(r)
                continue
            m = RE_BLOCK.search(linea)
            if m:
                block_ts.append(pd.to_datetime(m.group(1)))

    print(f"  Stats lines    : {len(stats_rows):,}")
    print(f"  BLOCK events   : {len(block_ts):,}")

    if not stats_rows:
        print("ERROR: No se encontraron líneas de stats.")
        sys.exit(1)

    df = pd.DataFrame(stats_rows, columns=['ts', 'flows', 'bloqueados'])
    df = df.sort_values('ts').reset_index(drop=True)
    block_arr = pd.DatetimeIndex(sorted(block_ts))

    # ── Detectar reinicios (flows baja o se mantiene igual) ──────────────────
    df['reinicio'] = (df['flows'] <= df['flows'].shift(1).fillna(999999)).astype(int)
    df['sesion']   = df['reinicio'].cumsum()

    n_sesiones = df['sesion'].nunique()
    print(f"  Sesiones (reinicios+1): {n_sesiones}")

    # ── Computar gap dentro de cada sesión ───────────────────────────────────
    df['gap'] = df.groupby('sesion')['ts'].diff().dt.total_seconds()

    # Primera fila de cada sesión: sin gap válido
    df = df[df['gap'].notna()].copy()

    # Descartar gaps negativos o cero (relojes inconsistentes)
    df = df[df['gap'] > 0].copy()

    # ── Features de lag (dentro de sesión) ───────────────────────────────────
    for lag in [1, 2, 3]:
        df[f'gap_lag{lag}'] = df.groupby('sesion')['gap'].shift(lag)

    df['gap_delta'] = df['gap'] - df['gap_lag1']
    df['gap_mean5'] = df.groupby('sesion')['gap'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean()
    )
    df['gap_std5'] = df.groupby('sesion')['gap'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).std().fillna(0)
    )

    # ── Codificación temporal cíclica ─────────────────────────────────────────
    df['hora_sin'] = np.sin(2 * np.pi * df['ts'].dt.hour / 24)
    df['hora_cos'] = np.cos(2 * np.pi * df['ts'].dt.hour / 24)

    # ── Target: ¿hay un BLOCK en los próximos 60s reales? ────────────────────
    # Vectorizado: sin apply, sin loops Python → milisegundos
    print("  Calculando targets (vectorizado) …")
    VENTANA_NS = 60 * 1_000_000_000  # 60s en nanosegundos
    block_ns = np.sort(block_arr.values.astype('int64'))
    ts_ns    = df['ts'].values.astype('int64')
    lo = np.searchsorted(block_ns, ts_ns,              side='right')
    hi = np.searchsorted(block_ns, ts_ns + VENTANA_NS, side='right')
    df['target'] = (hi > lo).astype(int)

    # ── Limpiar: eliminar filas con NaN en features ───────────────────────────
    FEATURES = ['gap', 'gap_lag1', 'gap_lag2', 'gap_lag3',
                'gap_delta', 'gap_mean5', 'gap_std5',
                'bloqueados', 'hora_sin', 'hora_cos']

    df_clean = df[FEATURES + ['target', 'ts', 'sesion']].dropna().copy()

    pos = df_clean['target'].sum()
    neg = len(df_clean) - pos

    print(f"\n  Observaciones válidas : {len(df_clean):,}")
    print(f"  Positivos (ataque=1)  : {pos:,}  ({100*pos/len(df_clean):.1f}%)")
    print(f"  Negativos (normal=0)  : {neg:,}  ({100*neg/len(df_clean):.1f}%)")
    print(f"  Ratio desbalance      : 1:{neg//pos if pos else '∞'}")

    df_clean.to_csv(OUT_CSV, index=False)
    print(f"\n  Guardado: {OUT_CSV}")

    # Criterio de éxito
    if len(df_clean) < 5000:
        print("ADVERTENCIA: Menos de 5,000 obs. Revisar el log.")
    if pos < 100:
        print("ADVERTENCIA: Menos de 100 positivos. El modelo puede no aprender.")
    else:
        print("  Criterio OK ✓")

    return df_clean, FEATURES


# ─── FASE 1 — Comparación ────────────────────────────────────────────────────
def fase1(df, FEATURES):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
    from xgboost import XGBClassifier
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("\n" + "=" * 60)
    print("FASE 1 — Comparación ARIMA vs RandomForest vs XGBoost")
    print("=" * 60)

    # Split temporal por posición (80/20) — evita que el cutoff por fecha
    # quede desbalanceado si los datos están concentrados en pocos días
    df_sorted = df.sort_values('ts').reset_index(drop=True)
    n80 = int(len(df_sorted) * 0.80)
    CUTOFF = df_sorted.iloc[n80]['ts']
    train = df_sorted.iloc[:n80].copy()
    test  = df_sorted.iloc[n80:].copy()

    print(f"  Split 80/20 temporal por posición:")
    print(f"  Train: filas 0–{n80-1}  → {len(train):,} obs  pos={train['target'].sum()}")
    print(f"  Test:  filas {n80}–fin   → {len(test):,} obs   pos={test['target'].sum()}")
    print(f"  Cutoff efectivo: {CUTOFF}")

    X_tr = train[FEATURES].values
    y_tr = train['target'].values
    X_te = test[FEATURES].values
    y_te = test['target'].values

    resultados = {}

    # ── ARIMA (baseline univariado sobre la serie de gaps) ────────────────────
    print("\n  [ARIMA baseline]")
    try:
        from statsmodels.tsa.arima.model import ARIMA
        from sklearn.preprocessing import MinMaxScaler
        serie = train['gap'].values
        modelo_a = ARIMA(serie, order=(3, 1, 2)).fit()
        fc = modelo_a.forecast(steps=len(test))
        # Convertir forecast a probabilidad via sigmoid sobre desviación
        mean_g, std_g = serie.mean(), serie.std()
        # Gap bajo = ataque probable → invertir
        zscore = (mean_g - fc) / (std_g + 1e-9)
        proba_arima = 1 / (1 + np.exp(-zscore))
        proba_arima = np.clip(proba_arima, 0, 1)
        auc_a = roc_auc_score(y_te, proba_arima) if y_te.sum() > 0 else 0.5
        resultados['ARIMA'] = {'auc': auc_a, 'proba': proba_arima, 'modelo': None}
        print(f"    AUC-ROC: {auc_a:.4f}")
    except Exception as e:
        print(f"    ARIMA falló: {e}")
        resultados['ARIMA'] = {'auc': 0.5, 'proba': np.full(len(y_te), 0.5), 'modelo': None}

    # ── Random Forest ─────────────────────────────────────────────────────────
    print("\n  [Random Forest]")
    clf_rf = RandomForestClassifier(
        n_estimators=300, max_depth=8,
        class_weight='balanced', random_state=42, n_jobs=-1
    )
    clf_rf.fit(X_tr, y_tr)
    p_rf  = clf_rf.predict_proba(X_te)[:, 1]
    auc_rf = roc_auc_score(y_te, p_rf) if y_te.sum() > 0 else 0.5
    # Threshold por F1
    best_f1, best_tau_rf = 0, 0.5
    for tau in np.arange(0.1, 0.9, 0.05):
        pred = (p_rf >= tau).astype(int)
        f1 = f1_score(y_te, pred, zero_division=0)
        if f1 > best_f1:
            best_f1, best_tau_rf = f1, tau
    pred_rf = (p_rf >= best_tau_rf).astype(int)
    resultados['RandomForest'] = {
        'auc': auc_rf, 'proba': p_rf, 'tau': best_tau_rf,
        'prec': precision_score(y_te, pred_rf, zero_division=0),
        'rec':  recall_score(y_te, pred_rf, zero_division=0),
        'f1':   f1_score(y_te, pred_rf, zero_division=0),
        'modelo': clf_rf
    }
    print(f"    AUC-ROC: {auc_rf:.4f}  F1@τ={best_tau_rf:.2f}: {best_f1:.4f}")

    # ── XGBoost ───────────────────────────────────────────────────────────────
    print("\n  [XGBoost]")
    ratio = float((y_tr == 0).sum()) / max((y_tr == 1).sum(), 1)
    clf_xgb = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        scale_pos_weight=ratio, subsample=0.8, colsample_bytree=0.8,
        early_stopping_rounds=20, eval_metric='auc',
        random_state=42, verbosity=0
    )
    clf_xgb.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    p_xgb = clf_xgb.predict_proba(X_te)[:, 1]
    auc_xgb = roc_auc_score(y_te, p_xgb) if y_te.sum() > 0 else 0.5
    best_f1, best_tau_xgb = 0, 0.5
    for tau in np.arange(0.1, 0.9, 0.05):
        pred = (p_xgb >= tau).astype(int)
        f1 = f1_score(y_te, pred, zero_division=0)
        if f1 > best_f1:
            best_f1, best_tau_xgb = f1, tau
    pred_xgb = (p_xgb >= best_tau_xgb).astype(int)
    resultados['XGBoost'] = {
        'auc': auc_xgb, 'proba': p_xgb, 'tau': best_tau_xgb,
        'prec': precision_score(y_te, pred_xgb, zero_division=0),
        'rec':  recall_score(y_te, pred_xgb, zero_division=0),
        'f1':   f1_score(y_te, pred_xgb, zero_division=0),
        'modelo': clf_xgb
    }
    print(f"    AUC-ROC: {auc_xgb:.4f}  F1@τ={best_tau_xgb:.2f}: {best_f1:.4f}")

    # ── Curvas ROC ────────────────────────────────────────────────────────────
    from sklearn.metrics import roc_curve
    fig, ax = plt.subplots(figsize=(7, 5))
    colores = {'ARIMA': '#888', 'RandomForest': '#2196F3', 'XGBoost': '#E53935'}
    for nombre, res in resultados.items():
        if y_te.sum() > 0:
            fpr, tpr, _ = roc_curve(y_te, res['proba'])
            ax.plot(fpr, tpr, color=colores[nombre],
                    label=f"{nombre} (AUC={res['auc']:.3f})", lw=2)
    ax.plot([0,1],[0,1],'--', color='gray', lw=1)
    ax.set_xlabel('FPR'); ax.set_ylabel('TPR')
    ax.set_title('ROC — ARIMA vs RandomForest vs XGBoost\n(Predictor temporal de ataques)')
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(GRAF_DIR / 'roc_comparacion.png', dpi=150)
    plt.close()
    print(f"\n  Gráfica ROC guardada: {GRAF_DIR / 'roc_comparacion.png'}")

    # ── Tabla resumen ─────────────────────────────────────────────────────────
    lineas = [
        "=" * 65,
        f"Comparación de modelos predictivos — {datetime.now():%Y-%m-%d}",
        f"Train: hasta {CUTOFF} ({len(train)} obs) | Test: {len(test)} obs",
        "=" * 65,
        f"{'Modelo':<16} {'AUC':>6} {'Prec':>6} {'Rec':>6} {'F1':>6} {'τ':>5}",
        "-" * 65,
    ]
    for nombre, res in resultados.items():
        tau = res.get('tau', '—')
        tau_str = f"{tau:.2f}" if isinstance(tau, float) else tau
        lineas.append(
            f"{nombre:<16} {res['auc']:>6.4f} "
            f"{res.get('prec',0):>6.4f} {res.get('rec',0):>6.4f} "
            f"{res.get('f1',0):>6.4f} {tau_str:>5}"
        )
    lineas.append("=" * 65)
    texto = '\n'.join(lineas)
    print('\n' + texto)
    OUT_COMP.write_text(texto)

    return resultados, y_te, X_te, FEATURES


# ─── FASE 2 — Decisión y serialización ───────────────────────────────────────
def fase2(resultados, y_te, X_te, FEATURES):
    import joblib
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("\n" + "=" * 60)
    print("FASE 2 — Decisión del modelo de producción")
    print("=" * 60)

    auc_rf  = resultados['RandomForest']['auc']
    auc_xgb = resultados['XGBoost']['auc']

    if auc_xgb > auc_rf + 0.02:
        ganador, tipo = resultados['XGBoost'], 'XGBoost'
    else:
        ganador, tipo = resultados['RandomForest'], 'RandomForest'

    print(f"  XGBoost AUC: {auc_xgb:.4f}")
    print(f"  RF AUC:      {auc_rf:.4f}")
    print(f"  Ganador:     {tipo}  (diferencia={auc_xgb-auc_rf:+.4f}pp)")

    # Serializar
    joblib.dump(ganador['modelo'], OUT_MODEL)
    OUT_TIPO.write_text(tipo)
    OUT_FEATS.write_text('\n'.join(FEATURES))

    # Métricas finales
    metr = (
        f"Modelo: {tipo}\n"
        f"AUC-ROC:     {ganador['auc']:.4f}\n"
        f"Precision@τ: {ganador.get('prec',0):.4f}\n"
        f"Recall@τ:    {ganador.get('rec',0):.4f}\n"
        f"F1@τ:        {ganador.get('f1',0):.4f}\n"
        f"Umbral τ:    {ganador.get('tau',0.5):.4f}\n"
        f"Features:    {', '.join(FEATURES)}\n"
        f"Generado:    {datetime.now():%Y-%m-%d %H:%M}\n"
    )
    OUT_METR.write_text(metr)
    print(f"\n{metr}")

    # SHAP (solo si XGBoost ganó — RF SHAP es más lento)
    if tipo == 'XGBoost':
        print("  Generando SHAP plot …")
        try:
            import shap
            explainer = shap.TreeExplainer(ganador['modelo'])
            shap_vals = explainer.shap_values(X_te[:500])
            fig, ax = plt.subplots(figsize=(8, 5))
            shap.summary_plot(shap_vals, X_te[:500],
                              feature_names=FEATURES,
                              show=False, plot_type='bar')
            plt.tight_layout()
            plt.savefig(GRAF_DIR / 'shap_predictor.png', dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  SHAP guardado: {GRAF_DIR / 'shap_predictor.png'}")
        except Exception as e:
            print(f"  SHAP falló (no crítico): {e}")

    print(f"\n  Modelos guardados:")
    print(f"    {OUT_MODEL}")
    print(f"    {OUT_TIPO}  → '{tipo}'")
    print(f"    {OUT_FEATS}")
    print(f"    {OUT_METR}")


# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fase', type=int, choices=[0, 1, 2], default=None)
    args = parser.parse_args()

    if args.fase is None or args.fase == 0:
        df, FEATURES = fase0()
    else:
        if not OUT_CSV.exists():
            print(f"ERROR: {OUT_CSV} no existe. Ejecuta --fase 0 primero.")
            sys.exit(1)
        df = pd.read_csv(OUT_CSV, parse_dates=['ts'])
        FEATURES = ['gap','gap_lag1','gap_lag2','gap_lag3',
                    'gap_delta','gap_mean5','gap_std5',
                    'bloqueados','hora_sin','hora_cos']

    if args.fase is None or args.fase == 1:
        resultados, y_te, X_te, FEATURES = fase1(df, FEATURES)
    
    if args.fase is None or args.fase == 2:
        if args.fase == 2:
            # cargar resultados desde archivos si solo se corre fase 2
            print("Para --fase 2 aislada, ejecutar fases 0 y 1 primero.")
            sys.exit(1)
        fase2(resultados, y_te, X_te, FEATURES)

    print("\n✓ Completado.")
