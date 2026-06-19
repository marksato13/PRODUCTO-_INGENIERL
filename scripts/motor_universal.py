#!/usr/bin/env python3
"""
motor_universal.py — Motor de decisión con switching IF / AE en segundos.

Switching:
    echo "IF" > config/modelo_activo.txt && sudo systemctl restart ppi-motor-universal.service
    echo "AE" > config/modelo_activo.txt && sudo systemctl restart ppi-motor-universal.service

El MVP motor_decision.py (IF puro) NO es modificado en ningún momento.
"""
import os, sys, json, time, logging, subprocess, threading
from collections import defaultdict
from datetime import datetime
import numpy as np
import joblib

# ─── rutas ────────────────────────────────────────────────────────────────────
ROOT       = '/home/m4rk/ppi-surikata-producto'
CONFIG_F   = os.path.join(ROOT, 'config/modelo_activo.txt')
EVE_JSON   = '/var/log/suricata/eve.json'
LOG_F      = os.path.join(ROOT, 'results/motor_decision.log')
SERVER_IP  = '192.168.0.120'
TG_RELAY   = 'http://192.168.0.20:8889/telegram'

# Artefactos IF
IF_MODEL   = os.path.join(ROOT, 'models/isolation_forest.pkl')
IF_SCALER  = os.path.join(ROOT, 'models/scaler.pkl')
IF_MET     = os.path.join(ROOT, 'results/metricas_offline.txt')

# Artefactos AE
AE_MODEL   = os.path.join(ROOT, 'models/ae/ae_autoencoder.pkl')
AE_SCALER  = os.path.join(ROOT, 'models/ae/ae_scaler.pkl')
AE_MET     = os.path.join(ROOT, 'results/ae/ae_metricas_offline.txt')

WHITELIST = {
    '192.168.0.1','192.168.0.20','192.168.0.110',
    '192.168.0.120','192.168.0.130','192.168.0.140','127.0.0.1'
}

FEATURES = [
    'pkts_toserver','pkts_toclient','bytes_toserver','bytes_toclient',
    'duration','pkt_rate','byte_rate','pkt_ratio','byte_ratio',
    'avg_pkt_size','is_tcp','is_udp','is_icmp','dest_port',
]

BF_VENTANA      = 60
BF_UMBRAL_LIMIT = 5
BF_UMBRAL_BLOCK = 15
HTTP_VENTANA    = 30
HTTP_LIMIT      = 50
HTTP_BLOCK      = 100
TIMEOUT_SEC     = 300

# ─── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_F),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger('motor_universal')

# ─── leer configuración de modelo ─────────────────────────────────────────────
def leer_modelo_activo():
    try:
        with open(CONFIG_F) as f:
            return f.read().strip().upper()
    except:
        return 'IF'

# ─── adaptadores de modelo ────────────────────────────────────────────────────
class AdaptadorIF:
    """Wraps IsolationForest. score() → menor = más anómalo (rango ≈ [−1, 0])."""
    def __init__(self):
        self.model  = joblib.load(IF_MODEL)
        self.scaler = joblib.load(IF_SCALER)
        log.info("AdaptadorIF cargado: %s", IF_MODEL)

    def score(self, x14: np.ndarray) -> float:
        xs = self.scaler.transform(x14.reshape(1, -1))
        return float(self.model.score_samples(xs)[0])

class AdaptadorAE:
    """Wraps MLPRegressor Autoencoder. score() = −MSE → menor = más anómalo."""
    def __init__(self):
        self.model  = joblib.load(AE_MODEL)
        self.scaler = joblib.load(AE_SCALER)
        log.info("AdaptadorAE cargado: %s", AE_MODEL)

    def score(self, x14: np.ndarray) -> float:
        xs   = self.scaler.transform(x14.reshape(1, -1))
        xhat = self.model.predict(xs)
        mse  = float(np.mean((xs - xhat) ** 2))
        return -mse   # mismo convenio que IF

# ─── leer umbrales ────────────────────────────────────────────────────────────
def leer_umbrales(met_path):
    tau1, tau2 = -0.4459, -0.6027   # defaults IF
    try:
        with open(met_path) as f:
            for line in f:
                k, _, v = line.strip().partition('=')
                if k == 'tau1': tau1 = float(v)
                if k == 'tau2': tau2 = float(v)
    except Exception as e:
        log.warning("No se pudo leer umbrales de %s: %s", met_path, e)
    return tau1, tau2

# ─── extracción de features ───────────────────────────────────────────────────
def flow_duration(ev):
    try:
        fl = ev.get('flow', {})
        fmt = '%Y-%m-%dT%H:%M:%S.%f%z'
        t0  = datetime.strptime(fl['start'], fmt)
        t1  = datetime.strptime(fl['end'],   fmt)
        return max((t1 - t0).total_seconds(), 0.001)
    except:
        return 0.001

def extraer_features(ev):
    fl    = ev.get('flow', {})
    proto = ev.get('proto', '').upper()
    dur   = flow_duration(ev)
    pts   = fl.get('pkts_toserver',  0) or 0
    ptc   = fl.get('pkts_toclient',  0) or 0
    bts   = fl.get('bytes_toserver', 0) or 0
    btc   = fl.get('bytes_toclient', 0) or 0
    row = np.array([
        pts, ptc, bts, btc, dur,
        (pts + ptc) / dur,
        (bts + btc) / dur,
        pts / (ptc + 1),
        bts / (btc + 1),
        (bts + btc) / max(pts + ptc, 1),
        1.0 if proto == 'TCP'  else 0.0,
        1.0 if proto == 'UDP'  else 0.0,
        1.0 if proto in ('ICMP','IPV6-ICMP') else 0.0,
        float(ev.get('dest_port', 0) or 0),
    ], dtype=np.float64)
    if np.any(np.isnan(row)) or np.any(np.isinf(row)):
        return None
    return row

# ─── heurísticos ─────────────────────────────────────────────────────────────
def clasificar_grado(score, tau1, tau2):
    if score > tau1:
        return 'NORMAL'
    if score > tau2:
        return 'BAJA'
    if score > tau2 - 0.2:
        return 'ALTA'
    return 'CRITICA'

# ─── control ipset ────────────────────────────────────────────────────────────
def ssh_enforce(ip, accion, timeout=TIMEOUT_SEC):
    cmd = (f'ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no '
           f'm4rk@{SERVER_IP} '
           f'"bash /home/m4rk/ppi-surikata-producto/scripts/enforce.sh '
           f'{ip} {accion} {timeout}"')
    subprocess.Popen(cmd, shell=True)

# ─── Telegram (no bloqueante) ─────────────────────────────────────────────────
import queue, requests
tg_queue   = queue.Queue(maxsize=100)
tg_running = True

def tg_worker():
    while tg_running:
        try:
            msg = tg_queue.get(timeout=1)
            try:
                requests.post(TG_RELAY, json={'text': msg}, timeout=3)
            except:
                pass
        except queue.Empty:
            pass

tg_thread = threading.Thread(target=tg_worker, daemon=True)
tg_thread.start()

def tg_send(msg):
    try:
        tg_queue.put_nowait(msg)
    except queue.Full:
        pass

# ─── seguir eve.json ──────────────────────────────────────────────────────────
def seguir_eve(path):
    with open(path, 'r', errors='ignore') as f:
        f.seek(0, 2)
        while True:
            if os.path.getsize(path) < f.tell():
                f.seek(0)
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    modelo_activo = leer_modelo_activo()
    log.info("=" * 60)
    log.info("motor_universal.py — modelo activo: %s", modelo_activo)
    log.info("=" * 60)

    if modelo_activo == 'AE':
        adaptador  = AdaptadorAE()
        tau1, tau2 = leer_umbrales(AE_MET)
    else:
        adaptador  = AdaptadorIF()
        tau1, tau2 = leer_umbrales(IF_MET)

    log.info("Umbrales: tau1=%.4f  tau2=%.4f", tau1, tau2)

    bloqueados  = set()
    limitados   = set()
    ssh_intentos  = defaultdict(list)
    http_requests = defaultdict(list)

    stats = {'total': 0, 'permit': 0, 'limit': 0, 'block': 0, 'whitelist': 0}

    log.info("Leyendo eve.json: %s", EVE_JSON)

    for raw in seguir_eve(EVE_JSON):
        try:
            ev = json.loads(raw)
        except:
            continue

        if ev.get('event_type') != 'flow':
            continue

        src = ev.get('src_ip', '')
        if src in WHITELIST:
            stats['whitelist'] += 1
            continue

        stats['total'] += 1
        now  = time.time()
        accion_final = 'PERMIT'

        # ── heurístico brute-force SSH ────────────────────────────────────
        if ev.get('dest_port') == 22 and ev.get('proto','').upper() == 'TCP':
            ssh_intentos[src].append(now)
            ssh_intentos[src] = [t for t in ssh_intentos[src] if now - t < BF_VENTANA]
            n_bf = len(ssh_intentos[src])
            if n_bf >= BF_UMBRAL_BLOCK:
                accion_final = 'BLOCK'
            elif n_bf >= BF_UMBRAL_LIMIT:
                accion_final = 'LIMIT'

        # ── heurístico HTTP abuse ─────────────────────────────────────────
        if ev.get('dest_port') in (80, 8080) and ev.get('proto','').upper() == 'TCP':
            http_requests[src].append(now)
            http_requests[src] = [t for t in http_requests[src] if now - t < HTTP_VENTANA]
            n_http = len(http_requests[src])
            if n_http >= HTTP_BLOCK:
                accion_final = 'BLOCK'
            elif n_http >= HTTP_LIMIT:
                if accion_final != 'BLOCK':
                    accion_final = 'LIMIT'

        # ── modelo de detección ───────────────────────────────────────────
        feats = extraer_features(ev)
        if feats is not None:
            score = adaptador.score(feats)
            grado = clasificar_grado(score, tau1, tau2)

            if grado in ('ALTA', 'CRITICA') and accion_final == 'PERMIT':
                accion_final = 'BLOCK' if grado == 'CRITICA' else 'LIMIT'
            elif grado == 'BAJA' and accion_final == 'PERMIT':
                accion_final = 'LIMIT'

            if accion_final in ('LIMIT', 'BLOCK'):
                log.warning(
                    "EVENTO modelo=%s src=%s score=%.4f grado=%s accion=%s",
                    modelo_activo, src, score, grado, accion_final
                )
        else:
            score, grado = 0.0, 'NORMAL'

        # ── aplicar acción ────────────────────────────────────────────────
        if accion_final == 'BLOCK' and src not in bloqueados:
            bloqueados.add(src)
            limitados.discard(src)
            ssh_enforce(src, 'BLOCK')
            stats['block'] += 1
            msg = f"🔴 BLOCK [{modelo_activo}] {src} score={score:.4f} grado={grado}"
            log.warning(msg)
            tg_send(msg)

        elif accion_final == 'LIMIT' and src not in bloqueados and src not in limitados:
            limitados.add(src)
            ssh_enforce(src, 'LIMIT')
            stats['limit'] += 1
            msg = f"🟡 LIMIT [{modelo_activo}] {src} score={score:.4f} grado={grado}"
            log.warning(msg)
            tg_send(msg)

        else:
            if accion_final == 'PERMIT':
                stats['permit'] += 1
            log.debug("PERMIT [%s] %s score=%.4f", modelo_activo, src, score)

        # ── stats cada 500 flows ──────────────────────────────────────────
        if stats['total'] % 500 == 0:
            log.info(
                "STATS modelo=%s total=%d permit=%d limit=%d block=%d whitelist=%d",
                modelo_activo,
                stats['total'], stats['permit'], stats['limit'],
                stats['block'],  stats['whitelist']
            )

if __name__ == '__main__':
    main()
