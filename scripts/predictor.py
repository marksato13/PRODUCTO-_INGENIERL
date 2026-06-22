#!/usr/bin/env python3
"""
predictor.py — Módulo de predicción temporal (Fase 3).
Proceso paralelo al motor. Lee motor_decision.log cada 10s,
calcula P(ataque en próximos 10s) y actúa si P >= umbral.
"""
import re, time, logging, joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import deque

BASE    = Path('/home/m4rk/ppi-surikata-producto')
LOG     = BASE / 'results' / 'motor_decision.log'
PRED_LOG= BASE / 'results' / 'predictor.log'
MODEL   = BASE / 'models'  / 'predictor_modelo.pkl'
FEATS_F = BASE / 'models'  / 'features_predictor.txt'

THETA_ALTA = 0.70
THETA_MEDIA= 0.40
INTERVALO  = 10   # segundos entre predicciones (permite anticipar al IF ~35s)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(PRED_LOG)],
)
log = logging.getLogger('predictor')

# ── Parseo del log ────────────────────────────────────────────────────────────
RE_STATS = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*'
    r'flows=(\d+) anomal[íi]as?=\d+ bf=\d+ http_abuse=\d+ '
    r'bloqueados=(\d+)'
)

def parsear_historial_stats(n=20):
    """Lee las últimas n stats lines para calcular historial de gaps."""
    try:
        with open(LOG, 'r', errors='ignore') as _f:
            _f.seek(0, 2)
            size = _f.tell()
            _f.seek(max(0, size - 512 * 1024))  # últimos 512 KB
            if size > 512 * 1024:
                _f.readline()  # descartar línea parcial
            lineas = _f.read().splitlines()
    except Exception:
        return []

    rows = []
    prev_flows = None
    for linea in lineas:
        if 'Estadísticas' not in linea and 'Estad' not in linea:
            continue
        m = RE_STATS.search(linea)
        if m:
                flows = int(m.group(2))
                # Detectar reinicio de sesión
                if prev_flows is not None and flows <= prev_flows:
                    rows = []   # nueva sesión — reiniciar historial
                prev_flows = flows
                rows.append({
                    'ts': pd.to_datetime(m.group(1)),
                    'flows': flows,
                    'bloqueados': int(m.group(3)),
                })

    return rows[-n:] if len(rows) >= 2 else []

MAX_GAP_INACTIVIDAD = 600  # 10 min sin stats → sistema inactivo, no predecir

def construir_features(historial, tiempo_desde_ultima):
    """
    Construye el vector de features a partir del historial de gaps.
    tiempo_desde_ultima: segundos desde la última stats line (gap parcial actual).
    """
    if len(historial) < 2:
        return None

    # Si el sistema lleva >10 min sin estadísticas, está inactivo — no predecir
    if tiempo_desde_ultima > MAX_GAP_INACTIVIDAD:
        return None

    # Calcular gaps entre stats consecutivas dentro de la sesión
    gaps = []
    for i in range(1, len(historial)):
        delta = (historial[i]['ts'] - historial[i-1]['ts']).total_seconds()
        if 0 < delta < 3600:
            gaps.append(delta)

    if len(gaps) < 1:
        return None

    gap_actual = tiempo_desde_ultima
    g = gaps
    # Rellenar lags faltantes con el último gap disponible
    while len(g) < 3:
        g = [g[0]] + g

    feat = {
        'gap':      gap_actual,
        'gap_lag1': g[-1],
        'gap_lag2': g[-2],
        'gap_lag3': g[-3],
        'gap_delta': gap_actual - g[-1],
        'gap_mean5': np.mean(g[-5:]),
        'gap_std5':  np.std(g[-5:]) if len(g) >= 5 else 0.0,
        'bloqueados': historial[-1]['bloqueados'],
        'hora_sin':  np.sin(2 * np.pi * datetime.now().hour / 24),
        'hora_cos':  np.cos(2 * np.pi * datetime.now().hour / 24),
    }
    return feat

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("Predictor PPI — XGBoost temporal — iniciando")
    log.info("=" * 55)

    if not MODEL.exists():
        log.error(f"Modelo no encontrado: {MODEL}")
        log.error("Ejecutar primero: python3 scripts/entrenar_predictor.py")
        return

    clf = joblib.load(MODEL)
    FEATURES = FEATS_F.read_text().strip().splitlines()
    log.info(f"Modelo cargado | features={len(FEATURES)} | θ_alta={THETA_ALTA}")

    ultima_alerta_ts = None   # para deduplicar alertas

    while True:
        try:
            # 1. Obtener historial de stats recientes
            historial = parsear_historial_stats(n=20)

            if not historial:
                log.info("Sin stats recientes — motor inactivo o log vacío")
                time.sleep(INTERVALO)
                continue

            # 2. Calcular tiempo desde última stats (gap parcial)
            ultima_stats = historial[-1]
            tiempo_desde = (datetime.now() - ultima_stats['ts'].to_pydatetime()).total_seconds()

            # 3. Construir vector de features
            feat = construir_features(historial, tiempo_desde)
            if feat is None:
                if len(historial) < 2:
                    log.info(f"Historial insuficiente ({len(historial)} stats) — esperando más datos")
                elif tiempo_desde > MAX_GAP_INACTIVIDAD:
                    log.info(f"Sistema inactivo (gap={tiempo_desde:.0f}s > {MAX_GAP_INACTIVIDAD}s) — sin prediccion")
                else:
                    log.info("Sin gaps válidos en historial — esperando")
                time.sleep(INTERVALO)
                continue

            X = np.array([[feat[f] for f in FEATURES]])

            # 4. Predicción
            p = float(clf.predict_proba(X)[0, 1])

            top_feat = max(feat, key=lambda k: abs(feat[k]) if k not in ('hora_sin','hora_cos') else 0)
            resumen  = f"P={p:.2%} | gap={feat['gap']:.0f}s lag1={feat['gap_lag1']:.0f}s delta={feat['gap_delta']:+.0f}s | top={top_feat}={feat[top_feat]:.1f}"

            # 5. Actuar según nivel
            if p >= THETA_ALTA:
                # Deduplicar: no relanzar alerta si ya se lanzó hace <5min
                ahora = datetime.now()
                if ultima_alerta_ts is None or (ahora - ultima_alerta_ts).total_seconds() > 120:  # 2 min dedup — ajustado para corridas de validación
                    log.warning(f"ALERTA-PREDICTIVA | {resumen}")
                    ultima_alerta_ts = ahora
                else:
                    log.info(f"RIESGO-ALTO (dedup) | {resumen}")
            elif p >= THETA_MEDIA:
                log.info(f"RIESGO-MEDIO | {resumen}")
            else:
                log.info(f"OK | {resumen}")

        except KeyboardInterrupt:
            log.info("Predictor detenido por usuario.")
            break
        except Exception as e:
            log.error(f"Error en ciclo: {e}")

        time.sleep(INTERVALO)

if __name__ == '__main__':
    main()
