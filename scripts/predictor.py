#!/usr/bin/env python3
"""
predictor.py — Predictor XGBoost v2 (señal combinada LIMIT+BLOCK)

Lee nuevas líneas de motor_decision.log cada INTERVALO segundos.
Por cada IP con eventos LIMIT o BLOCK recientes, predice si el ataque es sostenido.

Niveles de alerta:
  P < 0.40          → SILENCIO
  0.40 <= P < 0.70  → AVISO (dashboard amarillo)
  P >= 0.70         → ALERTA-PREDICTIVA (dashboard rojo + log WARNING)
"""

import re
import math
import time
import logging
import urllib.request
import urllib.parse
import joblib
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE      = Path('/home/m4rk/ppi-surikata-producto')
LOG       = BASE / 'results' / 'motor_decision.log'
PRED_LOG  = BASE / 'results' / 'predictor.log'
MODEL     = BASE / 'models'  / 'predictor_modelo_v2.pkl'
FEATS_F   = BASE / 'models'  / 'features_predictor_v2.txt'

# ── Config ────────────────────────────────────────────────────────────────────
THETA_ALTA  = 0.70
THETA_MEDIA = 0.40
INTERVALO   = 10        # segundos entre ciclos
DEDUP_SEG   = 300       # segundos entre alertas por la misma IP

# ── Credenciales Telegram (misma fuente que motor) ──────────────────────────
_TG_CONF   = "/home/m4rk/ppi-surikata-producto/config/telegram.conf"
TG_TOKEN   = ""
TG_CHAT_ID = ""
if __import__("os").path.exists(_TG_CONF):
    for _ln in open(_TG_CONF).read().splitlines():
        if _ln.startswith("TG_TOKEN="):    TG_TOKEN   = _ln.split("=",1)[1].strip()
        elif _ln.startswith("TG_CHAT_ID="): TG_CHAT_ID = _ln.split("=",1)[1].strip()
TG_ENABLED = bool(TG_TOKEN and TG_CHAT_ID)


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler(PRED_LOG)],
)
log = logging.getLogger('predictor')

# ── Regex: captura LIMIT y BLOCK (ambos formatos) ────────────────────────────
RE_EVENT = re.compile(
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \| WARNING \| '
    r'(?:ANOMAL[IÍ]A|SOSPECHOSO) \| '
    r'src=(\S+) dst=(\S+) proto=(\w+[\w-]*) '
    r'score=([-\d.]+)'
    r'[^|]*\| (BLOCK|LIMIT)'
)

# ── Estado por IP ─────────────────────────────────────────────────────────────
class IPState:
    __slots__ = ('limits', 'blocks', 'last_score', 'last_port',
                 'last_proto', 'last_alert_ts', 'last_event_ts')
    def __init__(self):
        self.limits        = deque()   # timestamps de LIMITs (ventana 15s)
        self.blocks        = deque()   # timestamps de BLOCKs (ventana 60s)
        self.last_score    = 0.0
        self.last_port     = 0
        self.last_proto    = 'TCP'
        self.last_alert_ts = None
        self.last_event_ts = None

ip_states  = defaultdict(IPState)
file_pos   = 0
model_mtime = 0.0
clf        = None
FEATURES   = []

# ── Telegram ──────────────────────────────────────────────────────────────────
def telegram_alerta(ip: str, p: float, action: str):
    if not TG_ENABLED:
        return
    try:
        msg  = f"[PREDICTOR] Ataque sostenido | IP={ip} | P={p:.0%} | ultimo={action}"
        url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        import json as _json
        data = _json.dumps({"chat_id": TG_CHAT_ID, "text": msg}).encode()
        req  = urllib.request.Request(url, data=data,
                   headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass   # no bloquear el ciclo si Telegram falla

# ── Cargar / recargar modelo ──────────────────────────────────────────────────
def cargar_modelo():
    global clf, FEATURES, model_mtime
    if not MODEL.exists():
        log.error(f"Modelo no encontrado: {MODEL}")
        log.error("Ejecutar: python3 scripts/f4_entrenar_predictor_v2.py")
        return False
    clf        = joblib.load(MODEL)
    FEATURES   = FEATS_F.read_text().strip().splitlines()
    model_mtime = MODEL.stat().st_mtime
    log.info(f"Modelo cargado | features={len(FEATURES)} | θ_alta={THETA_ALTA} | θ_media={THETA_MEDIA}")
    return True

def check_hot_reload():
    global clf, FEATURES, model_mtime
    try:
        mtime = MODEL.stat().st_mtime
        if mtime != model_mtime:
            clf        = joblib.load(MODEL)
            FEATURES   = FEATS_F.read_text().strip().splitlines()
            model_mtime = mtime
            log.info("Modelo recargado (hot-reload)")
    except Exception:
        pass

# ── Leer nuevas líneas del log ────────────────────────────────────────────────
def leer_nuevos_eventos():
    global file_pos
    nuevos = []
    try:
        with open(LOG, 'r', encoding='utf-8', errors='ignore') as f:
            # Detectar rotación: si el archivo es más pequeño que la posición guardada
            f.seek(0, 2)
            size = f.tell()
            if size < file_pos:
                file_pos = 0
                log.info("Rotación de log detectada — reiniciando posición")

            f.seek(file_pos)
            for line in f:
                m = RE_EVENT.match(line)
                if not m:
                    continue
                ts_str, src_ip, dst, proto, score, action = m.groups()
                if ':' in src_ip or src_ip.startswith('0.') or src_ip.startswith('255.'):
                    continue
                try:
                    dest_port = int(dst.rsplit(':', 1)[1])
                except (IndexError, ValueError):
                    dest_port = 0
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                nuevos.append({
                    'ts':       ts,
                    'ts_epoch': ts.timestamp(),
                    'src_ip':   src_ip,
                    'proto':    proto.upper(),
                    'score':    float(score),
                    'dest_port': dest_port,
                    'action':   action,
                })
            file_pos = f.tell()
    except Exception as e:
        log.error(f"Error leyendo log: {e}")
    return nuevos

# ── Construir features para una IP ───────────────────────────────────────────
def construir_features(state: IPState, t: float) -> np.ndarray:
    # Limpiar ventanas
    while state.limits and t - state.limits[0] > 15:
        state.limits.popleft()
    while state.blocks and t - state.blocks[0] > 60:
        state.blocks.popleft()

    proto = state.last_proto
    hora  = datetime.fromtimestamp(t)
    h     = hora.hour + hora.minute / 60.0

    block_count = len(state.blocks)
    block_rate = block_count / 60.0  # bloqueos por segundo en ventana 60s
    
    return np.array([[
        state.last_port,
        int(proto == 'TCP'),
        int(proto == 'UDP'),
        int(proto in ('ICMP', 'IPV6-ICMP')),
        math.sin(2 * math.pi * h / 24),
        math.cos(2 * math.pi * h / 24),
        len(state.limits),
        len(state.blocks),
        block_rate,
        int(state.last_score <= -0.6027),   # is_block (score <= τ2)
    ]])

# ── Ciclo principal ───────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("Predictor PPI v2 — XGBoost LIMIT+BLOCK — iniciando")
    log.info("=" * 55)

    if not cargar_modelo():
        return

    ips_con_eventos = set()   # IPs con eventos en este ciclo

    while True:
        try:
            check_hot_reload()

            # 1. Leer nuevos eventos del log
            nuevos = leer_nuevos_eventos()

            ips_con_eventos.clear()

            # 2. Actualizar estado por IP
            for ev in nuevos:
                ip    = ev['src_ip']
                t     = ev['ts_epoch']
                state = ip_states[ip]

                state.last_score    = ev['score']
                state.last_port     = ev['dest_port']
                state.last_proto    = ev['proto']
                state.last_event_ts = t

                if ev['action'] == 'LIMIT':
                    state.limits.append(t)
                else:
                    state.blocks.append(t)

                ips_con_eventos.add(ip)

            # 3. Predecir por cada IP activa
            if not ips_con_eventos:
                time.sleep(INTERVALO)
                continue

            ahora = datetime.now()
            for ip in ips_con_eventos:
                state = ip_states[ip]
                t     = state.last_event_ts

                X = construir_features(state, t)
                p = float(clf.predict_proba(X)[0, 1])

                lc  = len(state.limits)
                bc  = len(state.blocks)
                tag = f"src={ip} P={p:.2%} score={state.last_score:.4f} limits_15s={lc} blocks_60s={bc}"

                # Regla determinista CA-F4-02: ataque gradual con >= 5 LIMITs
                _dedup_det = (
                    state.last_alert_ts is None or
                    (ahora - state.last_alert_ts).total_seconds() > DEDUP_SEG
                )
                if lc >= 5 and _dedup_det and p < THETA_ALTA:
                    log.warning(f"AVISO-DETERMINISTA | limit_count={lc}>=5 | {tag}")
                    state.last_alert_ts = ahora
                    telegram_alerta(ip, p, "LIMIT-ACUM")

                if p >= THETA_ALTA:
                    # Deduplicar por IP
                    dedup_ok = (
                        state.last_alert_ts is None or
                        (ahora - state.last_alert_ts).total_seconds() > DEDUP_SEG
                    )
                    if dedup_ok:
                        log.warning(f"ALERTA-PREDICTIVA | {tag}")
                        state.last_alert_ts = ahora
                        telegram_alerta(ip, p, ev['action'])
                    else:
                        log.info(f"ALERTA-PREDICTIVA (dedup) | {tag}")

                elif p >= THETA_MEDIA:
                    log.info(f"AVISO | {tag}")

                else:
                    log.info(f"OK | {tag}")

        except KeyboardInterrupt:
            log.info("Predictor detenido por usuario.")
            break
        except Exception as e:
            log.error(f"Error en ciclo: {e}")

        time.sleep(INTERVALO)

if __name__ == '__main__':
    main()
