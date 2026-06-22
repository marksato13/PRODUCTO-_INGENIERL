#!/usr/bin/env python3
"""
Fase 4+5 — Motor de decisión + Control inline
Triple umbral τ1/τ2 (definidos por curva ROC):
  score > τ1  → PERMIT  (normal)
  τ2 < score ≤ τ1  → LIMIT  (sospechoso — rate limit 100 pkt/s via hashlimit)
  score ≤ τ2  → BLOCK  (anómalo — DROP via ipset)
"""

import json
import re
import ipaddress
import os
import sys
import time
import subprocess
import logging
from collections import defaultdict, deque
from datetime import datetime

import numpy as np
import joblib
import urllib.request
import urllib.parse
import threading
import queue as _queue

# ── Telegram — credenciales en config/telegram.conf (fuera de git) ────
_TG_CONF   = "/home/m4rk/ppi-surikata-producto/config/telegram.conf"
TG_TOKEN   = ""
TG_CHAT_ID = ""
if os.path.exists(_TG_CONF):
    for _ln in open(_TG_CONF).read().splitlines():
        if _ln.startswith("TG_TOKEN="):   TG_TOKEN   = _ln.split("=",1)[1].strip()
        elif _ln.startswith("TG_CHAT_ID="): TG_CHAT_ID = _ln.split("=",1)[1].strip()
TG_ENABLED = bool(TG_TOKEN and TG_CHAT_ID)

# ─────────────────────────────────────────────────────────────────────────────
EVE_PATH  = "/var/log/suricata/eve.json"
MODEL_DIR = "/home/m4rk/ppi-surikata-producto/models"
LOG_PATH  = "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
SERVIDOR  = "192.168.0.120"

# Umbrales τ1/τ2 — leídos de metricas_offline.txt (generado por fase3_evaluar.py)
_METRICAS = '/home/m4rk/ppi-surikata-producto/results/metricas_offline.txt'
TAU1, TAU2 = -0.4459, -0.6027  # valores por defecto (fase3_evaluar.py 2026-06-16, todos los datos)
if os.path.exists(_METRICAS):
    with open(_METRICAS) as _f:
        for _line in _f:
            if re.match(r"\s*tau1\s*:\s*[-\d]", _line):
                try: TAU1 = float(_line.split(':')[1].split('#')[0].strip())
                except: pass
            elif re.match(r"\s*tau2\s*:\s*[-\d]", _line):
                try: TAU2 = float(_line.split(':')[1].split('#')[0].strip())
                except: pass

WHITELIST = {"192.168.0.1", "192.168.0.20", "192.168.0.110",
             "192.168.0.120", "127.0.0.1", "192.168.0.130", "192.168.0.140"}

SET_BLOCK   = "ppi_blocked"
SET_LIMIT   = "ppi_limited"
TIMEOUT_SEC = 300   # segundos que dura el bloqueo/límite

FEATURES = [
    'pkts_toserver', 'pkts_toclient', 'bytes_toserver', 'bytes_toclient',
    'duration', 'pkt_rate', 'byte_rate', 'pkt_ratio', 'byte_ratio',
    'avg_pkt_size', 'is_tcp', 'is_udp', 'is_icmp', 'dest_port',
]

# ── Detector de Brute Force SSH (ventana temporal) ────────────
SSH_PORT          = 22
BF_VENTANA_SEG    = 60    # ventana de observación en segundos
BF_UMBRAL_LIMIT   = 5     # intentos en ventana → LIMIT
BF_UMBRAL_BLOCK   = 15    # intentos en ventana → BLOCK directo

# ── Detector de HTTP Abuse (ventana temporal) ─────────────────
HTTP_PORT          = 80
HTTP_VENTANA_SEG   = 30   # ventana de observación en segundos
HTTP_UMBRAL_LIMIT  = 50   # requests en ventana → LIMIT
HTTP_UMBRAL_BLOCK  = 100  # requests en ventana → BLOCK directo

# ─────────────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
    ]
)
log = logging.getLogger(__name__)


# ── Cola Telegram no-bloqueante ───────────────────────────────
_tg_queue = _queue.Queue(maxsize=100)

def _tg_worker():
    while True:
        msg = _tg_queue.get()
        if TG_ENABLED:
            try:
                url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                data = json.dumps({"chat_id": TG_CHAT_ID, "text": msg}).encode()
                req  = urllib.request.Request(url, data=data,
                           headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=10)
            except Exception as ex:
                log.warning(f"Telegram ERROR: {ex}")
        _tg_queue.task_done()

threading.Thread(target=_tg_worker, daemon=True, name="tg-sender").start()

TG_DEDUP_SEG = 300          # misma IP no genera 2 alertas en menos de 5 min
_last_tg_alert: dict = {}   # ip → timestamp última alerta enviada

TAU_AVISO    = -0.35   # score medio < TAU_AVISO → pre-alerta de tendencia
AVISO_MIN_FL = 10      # flows mínimos por IP para activar la pre-alerta
_score_hist: dict = {} # ip → deque(maxlen=AVISO_MIN_FL) de scores

def telegram_alerta(mensaje: str):
    if not TG_ENABLED:
        return
    try:
        _tg_queue.put_nowait(mensaje)
    except _queue.Full:
        log.warning("Telegram queue llena — alerta descartada")

def telegram_alerta_ip(ip: str, mensaje: str):
    """Como telegram_alerta pero suprime si la misma IP fue notificada < TG_DEDUP_SEG."""
    ahora = time.time()
    if ahora - _last_tg_alert.get(ip, 0) < TG_DEDUP_SEG:
        log.debug(f"Telegram dedup: {ip} — alerta suprimida (ventana {TG_DEDUP_SEG}s)")
        return
    _last_tg_alert[ip] = ahora
    telegram_alerta(mensaje)


def es_ip_bloqueable(ip: str) -> bool:
    try:
        obj = ipaddress.ip_address(ip)
        return not (obj.is_unspecified or obj.is_multicast or obj.is_reserved
                    or obj == ipaddress.ip_address('255.255.255.255')
                    or str(obj).endswith('.255'))
    except ValueError:
        return False


def load_model():
    clf    = joblib.load(f"{MODEL_DIR}/isolation_forest.pkl")
    scaler = joblib.load(f"{MODEL_DIR}/scaler.pkl")
    log.info(f"Modelo cargado | umbral_base={clf.offset_:.4f} | τ1={TAU1} | τ2={TAU2}")
    return clf, scaler


def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e['flow']['start'].replace('Z', '+00:00'))
        t1 = datetime.fromisoformat(e['flow']['end'].replace('Z', '+00:00'))
        return max((t1 - t0).total_seconds(), 0.001)
    except Exception:
        return 0.001


def extract_features(e):
    flow  = e.get('flow', {})
    proto = e.get('proto', '').upper()
    dur   = flow_duration(e)
    pts   = flow.get('pkts_toserver',  0) or 0
    ptc   = flow.get('pkts_toclient',  0) or 0
    bts   = flow.get('bytes_toserver', 0) or 0
    btc   = flow.get('bytes_toclient', 0) or 0
    return np.array([[
        pts, ptc, bts, btc, dur,
        (pts + ptc) / dur,
        (bts + btc) / dur,
        pts / (ptc + 1),
        bts / (btc + 1),
        (bts + btc) / (pts + ptc + 1),
        int(proto == 'TCP'),
        int(proto == 'UDP'),
        int(proto in ('ICMP', 'IPV6-ICMP')),
        e.get('dest_port', 0) or 0,
    ]], dtype=float)


def _ssh(cmd):
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5',
         f'm4rk@{SERVIDOR}', cmd],
        capture_output=True, text=True, timeout=8
    )
    return (result.stdout + result.stderr).strip()


def bloquear_ip(ip):
    try:
        out = _ssh(
            f'sudo ipset add {SET_BLOCK} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
            f'&& echo "BLOCKED {ip}"'
        )
        return out
    except Exception as ex:
        return f"ERROR: {ex}"


def limitar_ip(ip):
    try:
        out = _ssh(
            f'sudo ipset add {SET_LIMIT} {ip} timeout {TIMEOUT_SEC} -exist 2>&1 '
            f'&& echo "LIMITED {ip}"'
        )
        return out
    except Exception as ex:
        return f"ERROR: {ex}"


def inicializar_servidor():
    try:
        # ── ipset BLOCK (DROP total) ───────────────────────────
        _ssh(f'sudo ipset create {SET_BLOCK} hash:ip timeout {TIMEOUT_SEC} 2>/dev/null || true')
        _ssh(
            f'sudo iptables -C INPUT -m set --match-set {SET_BLOCK} src -j DROP 2>/dev/null '
            f'|| sudo iptables -I INPUT -m set --match-set {SET_BLOCK} src -j DROP'
        )

        # ── ipset LIMIT (rate limit 100 pkt/s via hashlimit) ──
        _ssh(f'sudo ipset create {SET_LIMIT} hash:ip timeout {TIMEOUT_SEC} 2>/dev/null || true')
        # Regla hashlimit: DROP paquetes de ppi_limited que excedan 100/s
        _ssh(
            f'sudo iptables -C INPUT -m set --match-set {SET_LIMIT} src '
            f'-m hashlimit --hashlimit-name ppi_limit --hashlimit-above 100/sec '
            f'--hashlimit-mode srcip --hashlimit-burst 150 -j DROP 2>/dev/null '
            f'|| sudo iptables -I INPUT 2 -m set --match-set {SET_LIMIT} src '
            f'-m hashlimit --hashlimit-name ppi_limit --hashlimit-above 100/sec '
            f'--hashlimit-mode srcip --hashlimit-burst 150 -j DROP'
        )

        log.info(
            f"Servidor init: OK | BLOCK=ipset+DROP | "
            f"LIMIT=ipset+hashlimit(100pkt/s) | τ1={TAU1} τ2={TAU2}"
        )
    except Exception as ex:
        log.warning(f"No se pudo inicializar servidor: {ex}")


# ─────────────────────────────────────────────────────────────────────────────
def seguir_eve(path):
    """Sigue eve.json como tail -f, detectando rotación/truncado."""
    f = open(path, 'r', errors='ignore')
    f.seek(0, 2)
    while True:
        line = f.readline()
        if line:
            yield line
        else:
            # Detectar rotación: si el tamaño del archivo es menor que la posición actual
            try:
                pos_actual   = f.tell()
                size_archivo = os.path.getsize(path)
                if size_archivo < pos_actual:
                    log.info("eve.json rotado/truncado — reabriendo desde el inicio")
                    f.close()
                    f = open(path, 'r', errors='ignore')
                    f.seek(0, 2)
            except Exception:
                pass
            time.sleep(0.2)


def decidir(score):
    """Devuelve 'PERMIT', 'LIMIT' o 'BLOCK' según τ1/τ2."""
    if score > TAU1:
        return 'PERMIT'
    elif score > TAU2:
        return 'LIMIT'
    else:
        return 'BLOCK'




def clasificar_grado(score: float) -> str:
    """Convierte score IF a grado cualitativo NORMAL/BAJA/ALTA/CRITICA."""
    if score > TAU1:     return "NORMAL"
    elif score > TAU2:   return "BAJA"
    elif score > -0.82:  return "ALTA"
    else:                return "CRITICA"


def clasificar_tipo(e: dict, score: float, decision: str,
                    ssh_intentos: dict, http_requests: dict) -> str:
    """Infiere el tipo de anomalía desde features del flujo."""
    if decision == "PERMIT":
        return "NORMAL"
    proto     = e.get("proto", "").upper()
    dest_port = e.get("dest_port", 0) or 0
    flow      = e.get("flow", {})
    pts  = flow.get("pkts_toserver", 0) or 0
    ptc  = flow.get("pkts_toclient", 0) or 0
    btc  = flow.get("bytes_toclient", 0) or 0
    dur  = max(flow_duration(e), 0.001)
    pkt_rate = (pts + ptc) / dur
    src_ip   = e.get("src_ip", "")

    if dest_port == SSH_PORT and proto == "TCP":
        ahora = time.time()
        rec = [t for t in ssh_intentos.get(src_ip, []) if ahora - t < BF_VENTANA_SEG]
        if len(rec) >= BF_UMBRAL_LIMIT:
            return "BRUTE_FORCE_SSH"
    if dest_port == HTTP_PORT and proto == "TCP":
        ahora = time.time()
        rec = [t for t in http_requests.get(src_ip, []) if ahora - t < HTTP_VENTANA_SEG]
        if len(rec) >= HTTP_UMBRAL_LIMIT:
            return "HTTP_ABUSE"
    if decision == "LIMIT":
        return "BAJA_ANOMALIA"
    if proto in ("ICMP", "IPV6-ICMP") and pkt_rate > 300:
        return "ICMP_FLOOD"
    if proto == "UDP" and pkt_rate > 500:
        return "UDP_FLOOD"
    if proto == "TCP" and pkt_rate > 2000 and dur < 2.0 and btc < 100:
        return "SYN_FLOOD"
    if dest_port == HTTP_PORT and proto == "TCP" and pkt_rate > 200:
        return "HTTP_ABUSE"
    if dest_port == SSH_PORT and proto == "TCP":
        return "BRUTE_FORCE_SSH"
    return "ANOMALIA_GENERICA"

def detectar_http_abuse(ip, dest_port, ts_flow, http_requests):
    """
    Detector temporal de HTTP abuse.
    Cuenta requests HTTP por IP en ventana de 30s.
    Retorna ('BLOCK', n) o ('LIMIT', n) si supera umbral, None si normal.
    """
    if dest_port != HTTP_PORT:
        return None

    ahora = ts_flow if ts_flow else time.time()
    ventana_inicio = ahora - HTTP_VENTANA_SEG
    http_requests[ip].append(ahora)
    http_requests[ip] = [t for t in http_requests[ip] if t >= ventana_inicio]
    n = len(http_requests[ip])
    if n >= HTTP_UMBRAL_BLOCK:
        return ('BLOCK', n)
    elif n >= HTTP_UMBRAL_LIMIT:
        return ('LIMIT', n)
    return None


def detectar_brute_force(ip, dest_port, ts_flow, ssh_intentos):
    """
    Detector temporal de brute force SSH.
    Registra cada intento SSH y evalúa la tasa en la ventana.
    Retorna ('BLOCK', n) o ('LIMIT', n) si supera umbral, None si normal.
    """
    if dest_port != SSH_PORT:
        return None

    ahora = ts_flow if ts_flow else time.time()
    ventana_inicio = ahora - BF_VENTANA_SEG

    # Añadir timestamp del intento actual
    ssh_intentos[ip].append(ahora)

    # Purgar intentos fuera de la ventana
    ssh_intentos[ip] = [t for t in ssh_intentos[ip] if t >= ventana_inicio]

    n = len(ssh_intentos[ip])
    if n >= BF_UMBRAL_BLOCK:
        return ('BLOCK', n)
    elif n >= BF_UMBRAL_LIMIT:
        return ('LIMIT', n)
    return None


def main():
    log.info("=" * 60)
    log.info("Motor de decisión PPI — iniciando")
    log.info("=" * 60)

    clf, scaler = load_model()
    inicializar_servidor()

    bloqueados    = set()
    limitados     = set()
    _block_repeat_ts = {}
    ssh_intentos  = defaultdict(list)   # ip → [timestamps] brute force SSH
    http_requests = defaultdict(list)   # ip → [timestamps] HTTP abuse
    total_flows   = 0
    total_anom    = 0
    total_bf      = 0
    total_http_ab = 0
    latencias_ms  = []                  # para calcular latencia media
    _kdrops_prev  = None                # kernel_drops última lectura stats
    _kdrops_ts    = time.time()         # timestamp de esa lectura
    _kdrops_alert_ts = 0.0             # cooldown alertas kernel_drops (600s)

    log.info(f"Monitoreando {EVE_PATH} ...")
    log.info(f"Brute Force SSH : ventana={BF_VENTANA_SEG}s "
             f"umbral_limit={BF_UMBRAL_LIMIT} umbral_block={BF_UMBRAL_BLOCK}")
    log.info(f"HTTP Abuse      : ventana={HTTP_VENTANA_SEG}s "
             f"umbral_limit={HTTP_UMBRAL_LIMIT} umbral_block={HTTP_UMBRAL_BLOCK}")

    for line in seguir_eve(EVE_PATH):
        try:
            e = json.loads(line.strip())
        except Exception:
            continue

        if e.get('event_type') == 'stats':
            _kd = e.get('stats', {}).get('capture', {}).get('kernel_drops', None)
            if _kd is not None and _kdrops_prev is not None:
                ahora = time.time()
                dt    = max(ahora - _kdrops_ts, 1)
                tasa  = (_kd - _kdrops_prev) / dt * 60  # drops/min
                if tasa > 100_000 and ahora - _kdrops_alert_ts > 600:
                    msg = (f'[MOTOR] ALERTA saturacion Suricata '
                           f'kernel_drops={_kd:,} tasa={tasa:,.0f}/min '
                           f'— motor podria quedar ciego')
                    log.warning(msg)
                    telegram_alerta(msg)
                    _kdrops_alert_ts = ahora
            if _kd is not None:
                _kdrops_prev = _kd
                _kdrops_ts   = time.time()
            continue
        if e.get('event_type') != 'flow':
            continue

        src_ip = e.get('src_ip', '')
        if not src_ip or ':' in src_ip or src_ip in WHITELIST:
            continue
        if not es_ip_bloqueable(src_ip):
            continue
        if (e.get('flow', {}).get('pkts_toserver', 0) or 0) == 0:
            continue

        total_flows += 1

        try:
            t_proc_ini = time.time()
            X     = scaler.transform(extract_features(e))
            score = clf.score_samples(X)[0]
            latencia_ms = (time.time() - t_proc_ini) * 1000
        except Exception as ex:
            log.debug(f"Feature error: {ex}")
            continue

        dest_ip   = e.get('dest_ip', '?')
        dest_port = e.get('dest_port', 0) or 0
        proto     = e.get('proto', '?')

        # features clave para alertas (calculadas del dict e, no del scaler)
        _fl  = e.get('flow', {})
        _bts = _fl.get('bytes_toserver', 0) or 0
        _btc = _fl.get('bytes_toclient',  0) or 0
        _pts = _fl.get('pkts_toserver',   0) or 0
        _ptc = _fl.get('pkts_toclient',   0) or 0
        _dur = max(flow_duration(e), 0.001)
        byte_ratio = _bts / (_btc + 1)
        pkt_rate   = (_pts + _ptc) / _dur

        # ts_flow: timestamp del flow para detectores temporales
        try:
            ts_flow = datetime.fromisoformat(
                e.get('timestamp', '').replace('Z', '+00:00')).timestamp()
        except Exception:
            ts_flow = time.time()

        # flag para contar anomalía UNA sola vez por flow (evitar doble conteo)
        _flow_anomaly = False

        # ── Detector de HTTP Abuse (override temporal) ────────
        http_ab = detectar_http_abuse(src_ip, dest_port, ts_flow, http_requests)
        if http_ab:
            hab_accion, hab_n = http_ab
            _flow_anomaly = True
            total_http_ab += 1
            if hab_accion == 'BLOCK' and src_ip not in bloqueados:
                bloqueados.add(src_ip)
                limitados.discard(src_ip)
                resp = bloquear_ip(src_ip)
                log.warning(
                    f"HTTP-ABUSE | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} requests={hab_n}/{HTTP_VENTANA_SEG}s | BLOCK → {resp}"
                )
                telegram_alerta_ip(src_ip,
                    f"🚨 PPI ALERTA — HTTP ABUSE\n"
                    f"Accion  : BLOCK (DROP)\n"
                    f"IP      : {src_ip}\n"
                    f"Proto   : {proto}  Puerto: {dest_port}\n"
                    f"Requests: {hab_n}/{HTTP_VENTANA_SEG}s\n"
                    f"Score   : {score:.4f}\n"
                    f"Hora    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            elif hab_accion == 'LIMIT' and src_ip not in limitados and src_ip not in bloqueados:
                limitados.add(src_ip)
                resp = limitar_ip(src_ip)
                log.warning(
                    f"HTTP-ABUSE | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} requests={hab_n}/{HTTP_VENTANA_SEG}s | LIMIT → {resp}"
                )
                telegram_alerta_ip(src_ip,
                    f"⚠️ PPI ALERTA — HTTP ABUSE\n"
                    f"Accion : LIMIT (100pkt/s)\nIP     : {src_ip}\nPuerto : {dest_port}\n"
                    f"Requests: {hab_n}/{HTTP_VENTANA_SEG}s\nHora   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

        # ── Detector de Brute Force SSH (override temporal) ───
        bf = detectar_brute_force(src_ip, dest_port, ts_flow, ssh_intentos)
        if bf:
            bf_accion, bf_n = bf
            _flow_anomaly = True
            total_bf += 1
            if bf_accion == 'BLOCK' and src_ip not in bloqueados:
                bloqueados.add(src_ip)
                limitados.discard(src_ip)
                resp = bloquear_ip(src_ip)
                log.warning(
                    f"BRUTE-FORCE | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} intentos={bf_n}/{BF_VENTANA_SEG}s | BLOCK → {resp}"
                )
                telegram_alerta_ip(src_ip,
                    f"🚨 PPI ALERTA — BRUTE FORCE SSH\n"
                    f"Accion : BLOCK\nIP     : {src_ip}\nPuerto : {dest_port}\n"
                    f"Intentos: {bf_n}/{BF_VENTANA_SEG}s\nHora   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            elif bf_accion == 'LIMIT' and src_ip not in limitados and src_ip not in bloqueados:
                limitados.add(src_ip)
                resp = limitar_ip(src_ip)
                log.warning(
                    f"BRUTE-FORCE | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} intentos={bf_n}/{BF_VENTANA_SEG}s | LIMIT → {resp}"
                )
                telegram_alerta_ip(src_ip,
                    f"⚠️ PPI ALERTA — BRUTE FORCE SSH\n"
                    f"Accion : LIMIT\nIP     : {src_ip}\nPuerto : {dest_port}\n"
                    f"Intentos: {bf_n}/{BF_VENTANA_SEG}s\nHora   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            # Continuar al análisis de score igual (no skip)

        # ── Pre-alerta de tendencia (score medio < TAU_AVISO, aún PERMIT) ───
        if src_ip not in _score_hist:
            _score_hist[src_ip] = deque(maxlen=AVISO_MIN_FL)
        _score_hist[src_ip].append(score)
        if (len(_score_hist[src_ip]) == AVISO_MIN_FL
                and score > TAU1):   # solo si aún es PERMIT
            media_score = sum(_score_hist[src_ip]) / AVISO_MIN_FL
            if media_score < TAU_AVISO:
                telegram_alerta_ip(src_ip,
                    f"👀 PPI AVISO — TENDENCIA ANÓMALA\n"
                    f"IP           : {src_ip}\n"
                    f"Score medio  : {media_score:.4f} (últimos {AVISO_MIN_FL} flows)\n"
                    f"Umbral aviso : {TAU_AVISO}\n"
                    f"byte_ratio   : {byte_ratio:.2f}  (normal ≈ 0.95)\n"
                    f"Hora         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                log.info(
                    f"TENDENCIA | src={src_ip} score_medio={media_score:.4f} "
                    f"byte_ratio={byte_ratio:.2f} | AVISO"
                )

        accion = decidir(score)
        grado  = clasificar_grado(score)
        tipo   = clasificar_tipo(e, score, accion, ssh_intentos, http_requests)

        if accion == 'BLOCK':
            _flow_anomaly = True
            if src_ip not in bloqueados:
                bloqueados.add(src_ip)
                if src_ip in limitados:
                    limitados.discard(src_ip)
                    _ssh(f'sudo ipset del {SET_LIMIT} {src_ip} 2>/dev/null || true')
                resp = bloquear_ip(src_ip)
                log.warning(
                    f"ANOMALÍA | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} score={score:.4f} grado={grado} tipo={tipo} "
                    f"byte_ratio={byte_ratio:.2f} pkt_rate={pkt_rate:.1f} | BLOCK"
                )
                telegram_alerta_ip(src_ip,
                    f"🚨 PPI ALERTA — {tipo}\n"
                    f"Accion  : BLOCK (DROP)\n"
                    f"IP      : {src_ip}\n"
                    f"Proto   : {proto}  Puerto: {dest_port}\n"
                    f"Score   : {score:.4f}  Grado: {grado}\n"
                    f"byte_ratio: {byte_ratio:.2f}  (normal ≈ 0.95)\n"
                    f"pkt_rate  : {pkt_rate:,.1f} pkt/s\n"
                    f"Hora    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                # IP ya en ipset: loguear decisión con rate-limit 5s por IP
                import time as _time
                _ahora = _time.time()
                if _block_repeat_ts.get(src_ip, 0) + 5.0 <= _ahora:
                    _block_repeat_ts[src_ip] = _ahora
                    log.warning(
                        f"ANOMALÍA | src={src_ip} dst={dest_ip}:{dest_port} "
                        f"proto={proto} score={score:.4f} grado={grado} tipo={tipo} "
                        f"byte_ratio={byte_ratio:.2f} pkt_rate={pkt_rate:.1f} | BLOCK"
                    )

        elif accion == 'LIMIT':
            _flow_anomaly = True
            if src_ip not in limitados and src_ip not in bloqueados:
                limitados.add(src_ip)
                resp = limitar_ip(src_ip)
                log.warning(
                    f"SOSPECHOSO | src={src_ip} dst={dest_ip}:{dest_port} "
                    f"proto={proto} score={score:.4f} grado={grado} tipo={tipo} "
                    f"byte_ratio={byte_ratio:.2f} pkt_rate={pkt_rate:.1f} | LIMIT"
                )
                telegram_alerta_ip(src_ip,
                    f"⚠️ PPI ALERTA — {tipo}\n"
                    f"Accion  : LIMIT (100 pkt/s)\n"
                    f"IP      : {src_ip}\n"
                    f"Proto   : {proto}  Puerto: {dest_port}\n"
                    f"Score   : {score:.4f}  Grado: {grado}\n"
                    f"byte_ratio: {byte_ratio:.2f}  (normal ≈ 0.95)\n"
                    f"pkt_rate  : {pkt_rate:,.1f} pkt/s\n"
                    f"Hora    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                log.debug(
                    f"LIMIT | src={src_ip} score={score:.4f} tipo={tipo} | ya en ipset — skip enforcement"
                )

        else:  # PERMIT
            log.debug(
                f"normal | src={src_ip} dst={dest_ip}:{dest_port} "
                f"proto={proto} score={score:.4f} | PERMIT"
            )

        # conteo único de anomalía por flow (fix M1 doble conteo)
        if _flow_anomaly:
            total_anom += 1

        latencias_ms.append(latencia_ms)

        # Purgar _score_hist cada 10,000 flows para evitar memory leak
        if total_flows % 10_000 == 0 and _score_hist:
            _score_hist.clear()
            _last_tg_alert.clear()

        if total_flows % 500 == 0:
            lat_med = sum(latencias_ms) / len(latencias_ms) if latencias_ms else 0
            latencias_ms.clear()
            log.info(
                f"Estadísticas | flows={total_flows} anomalías={total_anom} "
                f"bf={total_bf} http_abuse={total_http_ab} "
                f"bloqueados={len(bloqueados)} limitados={len(limitados)} "
                f"latencia_media={lat_med:.2f}ms"
            )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.info("Motor detenido por usuario.")
