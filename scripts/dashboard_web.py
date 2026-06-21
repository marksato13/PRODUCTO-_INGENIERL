#!/usr/bin/env python3
"""
Dashboard Web — PPI Surikata  |  UPeU 2026
Con sidebar, SSE en tiempo real y panel de alertas sincronizado con Telegram.
Acceso: http://192.168.0.110:8080
"""
import re, os, time, json, subprocess, ipaddress
from collections import deque, Counter
from datetime import datetime, timedelta
from threading import Thread, Lock
from queue import Queue, Empty
from flask import Flask, jsonify, render_template_string, request, Response

LOG_PATH  = "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
PRED_LOG  = "/home/m4rk/ppi-surikata-producto/results/predictor.log"
SERVIDOR = "192.168.0.120"
HOST, PORT = "0.0.0.0", 8080
MAX_EVT = 3000

RE_EVENTO = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r".*?\| (?:WARNING|ERROR) \| (ANOMALÍA|SOSPECHOSO|BRUTE-FORCE|HTTP-ABUSE)"
    r".*?src=([\d.]+).*?dst=([\d.]+):(\d+).*?proto=(\w+)"
    r"(?:.*?score=([-\d.]+))?"
    r"(?:.*?grado=(\w+))?"
    r"(?:.*?tipo=(\w+))?"
    r"(?:.*?byte_ratio=([\d.]+))?"
    r"(?:.*?pkt_rate=([\d.]+))?"
    r".*?\| (BLOCK|LIMIT)"
)
RE_STATS  = re.compile(
    r"flows=(\d+).*anomal[íi]as?=(\d+).*bf=(\d+).*http_abuse=(\d+)"
    r".*bloqueados=(\d+)(?:.*limitados=(\d+))?(?:.*latencia_media=([\d.]+))?"
)
RE_INICIO = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Motor de decisión PPI — iniciando"
)
RE_PRED = re.compile(
    r"(\d{2}:\d{2}:\d{2}) \| \w+\s*\| ([\w-]+)\s*\| P=([\d.]+)%"
)

# ── Estado global ─────────────────────────────────────────────────────────────
lock = Lock()
state = {
    "eventos": deque(maxlen=MAX_EVT),
    "flows_total":0,"anom_total":0,"bf_total":0,"http_total":0,
    "latencia":0.0,"motor_inicio":"—","inicio_app":datetime.now(),
    "block_counter":0,
    "last_stats_ts": None,
    "gaps_hist": deque(maxlen=30),
}

pred_state = {
    "p": 0.0, "nivel": "OK", "ts": "—", "historial": [],
}

# ── SSE — lista de colas por cliente conectado ────────────────────────────────
sse_lock    = Lock()
sse_clients = []   # list[Queue]

def push_sse(ev: dict):
    with sse_lock:
        muertos = []
        for q in sse_clients:
            try:    q.put_nowait(ev)
            except: muertos.append(q)
        for q in muertos:
            sse_clients.remove(q)

# ── Lector de log ─────────────────────────────────────────────────────────────
def procesar_linea(linea: str, push=True):
    m = RE_EVENTO.search(linea)
    if m:
        ts_str,tl,src,dst,port,proto,score,grado,tipo,byte_ratio,pkt_rate,accion = m.groups()
        score = score or "N/A"
        try:    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except: ts = datetime.now()
        ev = {
            "ts": ts_str[11:19], "ts_dt": ts.isoformat(), "date": ts_str[:10],
            "src": src, "dst": dst, "port": port, "proto": proto,
            "score": score, "grado": grado or "—",
            "tipo": tipo or "ANOMALIA_GENERICA", "accion": accion,
            "byte_ratio": byte_ratio or "—", "pkt_rate": pkt_rate or "—",
        }
        with lock:
            state["eventos"].append((ts, ev))
            if accion == "BLOCK":
                state["block_counter"] += 1
        if push:
            push_sse(ev)
        return

    m2 = RE_STATS.search(linea)
    if m2:
        now_ts = datetime.now()
        flows_v, anom_v = int(m2.group(1)), int(m2.group(2))
        lat_v = float(m2.group(7)) if m2.group(7) else None
        with lock:
            last_ts = state["last_stats_ts"]
            gap_val = round((now_ts - last_ts).total_seconds(), 1) if last_ts else None
            state["flows_total"] = flows_v
            state["anom_total"]  = anom_v
            state["bf_total"]    = int(m2.group(3))
            state["http_total"]  = int(m2.group(4))
            if lat_v is not None: state["latencia"] = lat_v
            state["last_stats_ts"] = now_ts
            if gap_val and 0 < gap_val < 3600:
                state["gaps_hist"].append({
                    "ts": now_ts.strftime("%H:%M:%S"),
                    "gap": gap_val,
                    "flows": flows_v,
                    "anom_rate": round(anom_v / flows_v * 100, 1) if flows_v else 0,
                })
        if push and gap_val and 0 < gap_val < 3600:
            push_sse({
                "type": "stats_gap",
                "ts": now_ts.strftime("%H:%M:%S"),
                "gap": gap_val,
                "flows": flows_v,
                "anom_rate": round(anom_v / flows_v * 100, 1) if flows_v else 0,
            })
        return

    m3 = RE_INICIO.search(linea)
    if m3:
        with lock: state["motor_inicio"] = m3.group(1)[11:19]

def log_reader():
    # Cargar solo los últimos 2MB del log (evitar leer 107MB completo)
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH,"r",errors="ignore") as f:
            f.seek(0, 2); size = f.tell()
            f.seek(max(0, size - 2*1024*1024))
            if size > 2*1024*1024: f.readline()  # descartar línea parcial
            for ln in f: procesar_linea(ln, push=False)
    # Tail en tiempo real (con push SSE)
    while True:
        if not os.path.exists(LOG_PATH): time.sleep(2); continue
        try:
            with open(LOG_PATH,"r",errors="ignore") as f:
                f.seek(0,2)
                while True:
                    ln = f.readline()
                    if ln: procesar_linea(ln, push=True)
                    else:
                        try:
                            if os.path.getsize(LOG_PATH) < f.tell(): break
                        except: pass
                        time.sleep(0.1)
        except: time.sleep(2)

def predictor_reader():
    """Tailea predictor.log y empuja eventos SSE tipo predictor."""
    # Cargar historial reciente al arrancar (no esperar nuevos eventos)
    if os.path.exists(PRED_LOG):
        try:
            with open(PRED_LOG, "r", errors="ignore") as f:
                last_lines = f.readlines()[-80:]
            hist = []
            for ln in reversed(last_lines):
                m = RE_PRED.search(ln)
                if m:
                    ts, niv, p = m.group(1), m.group(2), float(m.group(3)) / 100.0
                    hist.append({"ts": ts, "nivel": niv, "p": p})
                    if len(hist) >= 20: break
            if hist:
                hist.reverse()
                with lock:
                    pred_state["historial"] = hist
                    pred_state["p"]     = hist[-1]["p"]
                    pred_state["nivel"] = hist[-1]["nivel"]
                    pred_state["ts"]    = hist[-1]["ts"]
        except: pass
    while True:
        if not os.path.exists(PRED_LOG): time.sleep(5); continue
        try:
            with open(PRED_LOG, "r", errors="ignore") as f:
                f.seek(0, 2)
                while True:
                    ln = f.readline()
                    if ln:
                        m2 = RE_PRED.search(ln)
                        if m2:
                            ts  = m2.group(1)
                            niv = m2.group(2)
                            p   = float(m2.group(3)) / 100.0
                            ev  = {"type":"predictor","ts":ts,"nivel":niv,"p":p}
                            with lock:
                                pred_state["p"]     = p
                                pred_state["nivel"] = niv
                                pred_state["ts"]    = ts
                                pred_state["historial"] = \
                                    ([{"ts":ts,"nivel":niv,"p":p}]
                                     + pred_state["historial"])[:8]
                            push_sse(ev)
                    else:
                        try:
                            if os.path.getsize(PRED_LOG) < f.tell(): break
                        except: pass
                        time.sleep(0.5)
        except: time.sleep(2)

# ── Helpers ───────────────────────────────────────────────────────────────────
def ssh_run(cmd: str) -> str:
    try:
        return subprocess.check_output(
            ["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=4",
             f"m4rk@{SERVIDOR}", cmd],
            text=True, timeout=6, stderr=subprocess.DEVNULL
        ).strip()
    except: return ""

def ipset_list(nombre: str) -> list:
    for cmds in [
        ["sudo","ipset","list",nombre],
        ["ssh","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=3",
         f"m4rk@{SERVIDOR}", f"sudo ipset list {nombre}"]
    ]:
        try:
            out = subprocess.check_output(cmds, text=True, timeout=4,
                                          stderr=subprocess.DEVNULL)
            ips,en=[],False
            for ln in out.splitlines():
                if ln.startswith("Members:"): en=True; continue
                if en and ln.strip(): ips.append(ln.strip().split()[0])
            if ips or "Members:" in out: return ips
        except: pass
    return []

def riesgo(bloq,lim,rate):
    s = min(int(min(bloq*15,60)+min(lim*5,20)+min(rate/10,20)),100)
    if s<=25: return s,"BAJO",  "#3fb950"
    if s<=50: return s,"MEDIO", "#e3b341"
    if s<=75: return s,"ALTO",  "#f0883e"
    return     s,"CRÍTICO","#f85149"

def valid_ip(ip):
    try: ipaddress.ip_address(ip); return True
    except: return False

# ── Flask ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/api/stream")
def api_stream():
    """SSE — push instantáneo de cada evento nuevo."""
    q = Queue(maxsize=60)
    with sse_lock: sse_clients.append(q)
    def generate():
        try:
            while True:
                try:
                    ev = q.get(timeout=20)
                    yield f"data: {json.dumps(ev)}\n\n"
                except Empty:
                    yield ": ping\n\n"
        finally:
            with sse_lock:
                try: sse_clients.remove(q)
                except: pass
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@app.route("/api/stats")
def api_stats():
    with lock:
        evs = list(state["eventos"])
        ft  = state["flows_total"]; bf = state["bf_total"]
        ht  = state["http_total"]; lat = state["latencia"]
        mi  = state["motor_inicio"]; ia = state["inicio_app"]
        bc  = state["block_counter"]
    ahora = datetime.now()
    c = Counter(e["accion"] for _,e in evs)
    blk=c.get("BLOCK",0); lim=c.get("LIMIT",0)
    permit=max(ft-blk-lim,0)
    rate=sum(1 for ts,_ in evs if (ahora-ts).total_seconds()<60)
    ibl=ipset_list("ppi_blocked"); ili=ipset_list("ppi_limited")
    rv,rl,rc=riesgo(len(ibl),len(ili),rate)
    up=int((ahora-ia).total_seconds())
    h,r=divmod(up,3600); m,s=divmod(r,60)
    return jsonify({
        "block":blk,"limit":lim,"permit":permit,"flows_total":ft,
        "bf_total":bf,"http_total":ht,"latencia":lat,
        "motor_inicio":mi,"uptime":f"{h}h {m:02d}m {s:02d}s",
        "ipset_blocked":ibl,"ipset_limited":ili,
        "riesgo_val":rv,"riesgo_lbl":rl,"riesgo_color":rc,
        "flujos_min":rate,"now":ahora.strftime("%Y-%m-%d %H:%M:%S"),
        "block_counter":bc, "sse_clients":len(sse_clients),
    })

@app.route("/api/events")
def api_events():
    filt  = request.args.get("filter","ALL").upper()
    srch  = request.args.get("search","").strip().lower()
    limit = min(int(request.args.get("limit","80")),500)
    with lock: evs = list(state["eventos"])
    out=[]
    for _,e in reversed(evs):
        if filt!="ALL" and e["accion"]!=filt: continue
        if srch and srch not in e["src"] and srch not in (e.get("tipo","")).lower(): continue
        out.append(e)
        if len(out)>=limit: break
    return jsonify(out)

@app.route("/api/alerts")
def api_alerts():
    with lock: evs=list(state["eventos"])
    alerts=[e for _,e in reversed(evs) if e["accion"] in ("BLOCK","LIMIT")][:50]
    return jsonify(alerts)

@app.route("/api/timeline")
def api_timeline():
    with lock: evs=list(state["eventos"])
    ahora=datetime.now()
    labels,blk,lim=[],[],[]
    for h in range(23,-1,-1):
        t0=ahora.replace(minute=0,second=0,microsecond=0)-timedelta(hours=h)
        t1=t0+timedelta(hours=1)
        b=[e for ts,e in evs if t0<=ts<t1]
        labels.append(t0.strftime("%H:%M"))
        blk.append(sum(1 for e in b if e["accion"]=="BLOCK"))
        lim.append(sum(1 for e in b if e["accion"]=="LIMIT"))
    return jsonify({"labels":labels,"block":blk,"limit":lim})

@app.route("/api/tipos")
def api_tipos():
    with lock: evs=list(state["eventos"])
    c=Counter(e["tipo"] for _,e in evs if e["accion"]=="BLOCK")
    tops=c.most_common(8)
    return jsonify({"labels":[t for t,_ in tops],"data":[n for _,n in tops]})

@app.route("/api/unblock",methods=["POST"])
def api_unblock():
    ip=(request.json or {}).get("ip","").strip()
    if not valid_ip(ip): return jsonify({"ok":False,"error":"IP inválida"}),400
    ssh_run(f"sudo ipset del ppi_blocked {ip} 2>/dev/null; sudo ipset del ppi_limited {ip} 2>/dev/null")
    try:
        subprocess.run(["sudo","ipset","del","ppi_blocked",ip],capture_output=True,timeout=3)
        subprocess.run(["sudo","ipset","del","ppi_limited",ip],capture_output=True,timeout=3)
    except: pass
    return jsonify({"ok":True,"msg":f"{ip} desbloqueada"})

@app.route("/api/clear",methods=["POST"])
def api_clear():
    with lock:
        state["eventos"].clear()
        state["block_counter"] = 0
    return jsonify({"ok":True,"msg":"Alertas limpiadas"})

@app.route("/api/block",methods=["POST"])
def api_block():
    ip=(request.json or {}).get("ip","").strip()
    if not valid_ip(ip): return jsonify({"ok":False,"error":"IP inválida"}),400
    ssh_run(f"sudo ipset add ppi_blocked {ip} timeout 3600 -exist")
    return jsonify({"ok":True,"msg":f"{ip} bloqueada manualmente"})

@app.route("/api/predictor")
def api_predictor():
    with lock:
        return jsonify({
            "p": pred_state["p"],
            "nivel": pred_state["nivel"],
            "ts": pred_state["ts"],
            "historial": list(pred_state["historial"]),
        })

@app.route("/api/gaps")
def api_gaps():
    with lock:
        return jsonify(list(state["gaps_hist"]))

@app.route("/")
def index(): return render_template_string(HTML)

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PPI-Surikata | Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<style>
:root{
  --sb:56px;                          /* sidebar width */
  --sb-open:200px;
  --top:48px;
  --bg:#0d1117;--card:#161b22;--card2:#1c2128;
  --border:#30363d;--txt:#e6edf3;--muted:#8b949e;
  --red:#f85149;--yellow:#e3b341;--green:#3fb950;
  --blue:#58a6ff;--purple:#bc8cff;--orange:#f0883e;--teal:#39d353;
  --sb-bg:#0a0e17;--sb-hover:#161b22;--sb-active:#1f2937;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;
  font-size:13px;display:flex;height:100vh;overflow:hidden}

/* ── Sidebar ── */
.sidebar{
  width:var(--sb);min-width:var(--sb);background:var(--sb-bg);
  border-right:1px solid var(--border);display:flex;flex-direction:column;
  transition:width .22s ease;overflow:hidden;z-index:100;flex-shrink:0;
}
.sidebar:hover,.sidebar.open{width:var(--sb-open)}
.sb-brand{height:var(--top);display:flex;align-items:center;gap:10px;
  padding:0 16px;border-bottom:1px solid var(--border);flex-shrink:0;
  white-space:nowrap;overflow:hidden}
.sb-logo{font-size:1.1rem;font-weight:800;color:var(--blue);flex-shrink:0}
.sb-name{font-size:.78rem;font-weight:600;color:var(--txt);white-space:nowrap}
.sb-nav{flex:1;padding:8px 0;overflow:hidden}
.sb-item{
  display:flex;align-items:center;gap:12px;
  padding:11px 16px;cursor:pointer;border-left:3px solid transparent;
  transition:all .15s;white-space:nowrap;overflow:hidden;user-select:none;
}
.sb-item:hover{background:var(--sb-hover)}
.sb-item.active{background:var(--sb-active);border-left-color:var(--blue)}
.sb-item.active .sb-icon{color:var(--blue)}
.sb-icon{font-size:1.1rem;color:var(--muted);flex-shrink:0;width:24px;text-align:center}
.sb-label{font-size:.8rem;color:var(--txt);white-space:nowrap}
.sb-badge{
  margin-left:auto;background:var(--red);color:#fff;
  font-size:.62rem;font-weight:700;padding:2px 6px;
  border-radius:20px;display:none;flex-shrink:0
}
.sb-badge.show{display:block}
.sb-sep{height:1px;background:var(--border);margin:6px 10px}
.sb-bottom{padding:8px 0;border-top:1px solid var(--border)}
.sb-status{padding:10px 16px;display:flex;align-items:center;gap:10px;white-space:nowrap}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot-g{background:var(--green);animation:pulse 2s infinite}
.dot-r{background:var(--red)}
.dot-y{background:var(--yellow)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.sb-status-lbl{font-size:.72rem;color:var(--muted)}

/* ── Main area ── */
.main-wrap{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* ── Topbar ── */
.topbar{
  height:var(--top);background:var(--card);border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;gap:12px;flex-shrink:0
}
.topbar-title{font-size:.9rem;font-weight:600}
.topbar-title span{color:var(--blue)}
.topbar-right{display:flex;align-items:center;gap:14px}
#clock{font-size:.75rem;font-family:monospace;color:var(--muted)}
.chip{font-size:.7rem;padding:3px 10px;border-radius:20px;font-weight:600;
  background:var(--card2);border:1px solid var(--border);color:var(--muted)}
.chip.live{border-color:var(--green);color:var(--green)}
.sound-btn{background:none;border:1px solid var(--border);color:var(--muted);
  font-size:.72rem;padding:4px 10px;border-radius:6px;cursor:pointer;
  display:flex;align-items:center;gap:5px;transition:all .15s}
.sound-btn.on{border-color:var(--green);color:var(--green)}

/* ── Views ── */
.views{flex:1;overflow:hidden}
.view{display:none;height:100%;overflow-y:auto;padding:18px 20px}
.view.active{display:block}

/* scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}

/* ── Cards ── */
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px}
.card2{background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:12px}
.ct{font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
  color:var(--muted);margin-bottom:10px;display:flex;align-items:center;gap:6px}

/* ── Grid helpers ── */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.g8{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}
.gap{gap:14px;margin-bottom:14px}

/* ── Stat cards ── */
.stat-num{font-size:2.1rem;font-weight:800;line-height:1;margin-bottom:3px}
.stat-sub{font-size:.72rem;color:var(--muted)}
.bar-bg{background:var(--card2);border-radius:3px;height:4px;margin-top:8px}
.bar-fill{height:4px;border-radius:3px;transition:width .4s}

/* ── Colors ── */
.cr{color:var(--red)}.cy{color:var(--yellow)}.cg{color:var(--green)}
.cb{color:var(--blue)}.cm{color:var(--muted)}.co{color:var(--orange)}
.cp{color:var(--purple)}.ct-teal{color:var(--teal)}

/* ── Section header ── */
.sh{font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;
  color:var(--muted);display:flex;align-items:center;gap:8px;
  margin:16px 0 10px}
.sh::after{content:'';flex:1;height:1px;background:var(--border)}
.sh:first-child{margin-top:0}

/* ═══════════════════════════
   VISTA ALERTAS
═══════════════════════════ */
.alerts-topbar{
  display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:10px;margin-bottom:14px
}
.alerts-topbar-left{display:flex;align-items:center;gap:12px}
.alerts-title{font-size:1.1rem;font-weight:700}
.alerts-counters{display:flex;gap:8px}
.ac{padding:4px 14px;border-radius:20px;font-size:.78rem;font-weight:700;
  display:flex;align-items:center;gap:5px}
.ac-block{background:rgba(248,81,73,.15);color:var(--red);border:1px solid rgba(248,81,73,.3)}
.ac-limit{background:rgba(227,179,65,.15);color:var(--yellow);border:1px solid rgba(227,179,65,.3)}
.alerts-controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap}

/* Feed de alertas */
.alerts-feed{display:flex;flex-direction:column;gap:8px}
.alert-card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;display:flex;gap:14px;cursor:pointer;
  transition:background .15s,border-color .15s;position:relative
}
.alert-card:hover{background:var(--card2);border-color:var(--blue)}
.alert-card.BLOCK{border-left:4px solid var(--red)}
.alert-card.LIMIT{border-left:4px solid var(--yellow)}
.alert-card.new-alert{animation:alertIn .4s ease}
@keyframes alertIn{from{transform:translateY(-8px);opacity:0}to{transform:translateY(0);opacity:1}}
.alert-left{display:flex;flex-direction:column;align-items:center;gap:4px;
  min-width:46px;padding-top:2px}
.alert-icon-big{font-size:1.4rem}
.alert-ts-small{font-size:.65rem;font-family:monospace;color:var(--muted);
  text-align:center;white-space:nowrap}
.alert-center{flex:1;min-width:0}
.alert-row1{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
.alert-ip{font-size:.95rem;font-weight:700;font-family:monospace}
.alert-arrow{color:var(--muted);font-size:.8rem}
.alert-dst{font-size:.8rem;font-family:monospace;color:var(--muted)}
.alert-row2{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
.alert-tipo-big{font-size:.85rem;font-weight:600}
.alert-score{font-family:monospace;font-size:.8rem;color:var(--muted)}
.alert-gravedad{font-size:.72rem;color:var(--muted);font-style:italic}
.alert-right{display:flex;flex-direction:column;gap:6px;align-items:flex-end;
  min-width:80px;flex-shrink:0}
.btn-sm{font-size:.72rem;padding:4px 10px;border-radius:6px;cursor:pointer;
  border:1px solid var(--border);background:none;color:var(--muted);
  transition:all .15s;white-space:nowrap}
.btn-sm:hover{color:var(--txt);border-color:var(--txt)}
.btn-unblock{border-color:var(--green);color:var(--green)}
.btn-unblock:hover{background:rgba(63,185,80,.1)}
.alert-new-dot{position:absolute;top:10px;right:10px;width:7px;height:7px;
  border-radius:50%;background:var(--blue);animation:pulse 1.5s infinite}

/* filtros */
.flt-btn{background:var(--card2);border:1px solid var(--border);color:var(--muted);
  font-size:.75rem;padding:5px 14px;border-radius:20px;cursor:pointer;transition:all .15s}
.flt-btn:hover,.flt-btn.active{border-color:var(--blue);color:var(--blue)}
.flt-btn.a-block.active{border-color:var(--red);color:var(--red);background:rgba(248,81,73,.1)}
.flt-btn.a-limit.active{border-color:var(--yellow);color:var(--yellow);background:rgba(227,179,65,.1)}
.flt-btn.a-critica.active{border-color:var(--orange);color:var(--orange)}

/* ── Badges ── */
.bdg{font-size:.67rem;padding:2px 8px;border-radius:20px;font-weight:700;white-space:nowrap}
.bdg-BLOCK{background:rgba(248,81,73,.18);color:var(--red);border:1px solid rgba(248,81,73,.3)}
.bdg-LIMIT{background:rgba(227,179,65,.15);color:var(--yellow);border:1px solid rgba(227,179,65,.25)}
.bdg-PERMIT{background:rgba(63,185,80,.12);color:var(--green);border:1px solid rgba(63,185,80,.2)}
.bdg-CRITICA{background:rgba(248,81,73,.18);color:var(--red)}
.bdg-ALTA{background:rgba(240,136,62,.18);color:var(--orange)}
.bdg-BAJA{background:rgba(227,179,65,.15);color:var(--yellow)}
.bdg-NORMAL{background:rgba(63,185,80,.12);color:var(--green)}

/* ── Table ── */
.tbl-wrap{overflow-x:auto;max-height:420px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:.79rem}
thead{position:sticky;top:0;z-index:1}
thead th{background:var(--card2);color:var(--muted);font-weight:600;
  border-bottom:1px solid var(--border);padding:8px 10px;text-align:left;
  font-size:.67rem;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}
tbody tr{border-bottom:1px solid #21262d;cursor:pointer;transition:background .12s}
tbody tr:hover{background:var(--card2)}
tbody td{padding:6px 10px;vertical-align:middle}
.mono{font-family:monospace;font-size:.79rem}

/* ── Controles tabla ── */
.tbl-ctrl{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.srch{background:var(--card2);border:1px solid var(--border);color:var(--txt);
  font-size:.78rem;padding:5px 12px;border-radius:6px;outline:none;width:200px}
.srch:focus{border-color:var(--blue)}
.btn-exp{background:none;border:1px solid var(--border);color:var(--muted);
  font-size:.72rem;padding:5px 12px;border-radius:6px;cursor:pointer;
  display:flex;align-items:center;gap:4px}
.btn-exp:hover{border-color:var(--green);color:var(--green)}

/* ── ipset pills ── */
.ip-pill{display:inline-flex;align-items:center;gap:5px;font-family:monospace;
  font-size:.78rem;padding:4px 10px;border-radius:6px;margin:3px}
.ip-bl{background:rgba(248,81,73,.1);color:var(--red);border:1px solid rgba(248,81,73,.25)}
.ip-lm{background:rgba(227,179,65,.1);color:var(--yellow);border:1px solid rgba(227,179,65,.25)}
.unbl-btn{background:none;border:none;cursor:pointer;color:var(--muted);
  font-size:.72rem;padding:0 3px;transition:color .15s}
.unbl-btn:hover{color:var(--green)}

/* ── Charts ── */
.ch-wrap{position:relative;height:200px}
.ch-wrap-lg{position:relative;height:260px}

/* ── Metrics ── */
.mcard{background:var(--card2);border:1px solid var(--border);border-radius:8px;
  padding:12px;text-align:center}
.mv{font-size:1.45rem;font-weight:700;margin-bottom:3px}
.ml{font-size:.62rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.mb{background:var(--bg);border-radius:3px;height:4px;margin-top:7px}
.mb-f{height:4px;border-radius:3px}

/* ── Modal ── */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9000;
  display:none;align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal-box{background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:22px;max-width:460px;width:90%;box-shadow:0 8px 40px rgba(0,0,0,.6)}
.modal-hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.modal-t{font-weight:700}
.modal-x{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem}
.dr{display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border)}
.dk{color:var(--muted);font-size:.76rem;min-width:110px}
.dv{font-family:monospace;font-size:.8rem}

/* ── Toasts ── */
.toast-c{position:fixed;bottom:20px;right:20px;z-index:9999;
  display:flex;flex-direction:column;gap:8px;max-width:300px}
.toast{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;box-shadow:0 4px 24px rgba(0,0,0,.6);
  animation:toastIn .3s ease;display:flex;gap:10px;cursor:pointer}
.toast.bl-t{border-left:4px solid var(--red)}
.toast.lm-t{border-left:4px solid var(--yellow)}
@keyframes toastIn{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes toastOut{to{transform:translateY(20px);opacity:0}}
.t-icon{font-size:1.1rem;margin-top:1px}
.t-body{flex:1}
.t-title{font-weight:700;font-size:.8rem;margin-bottom:2px}
.t-msg{font-size:.72rem;color:var(--muted);font-family:monospace}

/* ── Manual block ── */
.manual-row{display:flex;gap:6px;margin-top:12px;
  padding-top:12px;border-top:1px solid var(--border)}
.manual-ip{flex:1;background:var(--card2);border:1px solid var(--border);
  color:var(--txt);padding:6px 10px;border-radius:6px;font-size:.78rem;outline:none}
.manual-ip:focus{border-color:var(--blue)}
.btn-blk-m{background:rgba(248,81,73,.15);border:1px solid var(--red);
  color:var(--red);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:.75rem}
</style>
</head>
<body>

<!-- ═══════════════ SIDEBAR ═══════════════ -->
<aside class="sidebar" id="sidebar">
  <div class="sb-brand">
    <span class="sb-logo">PPI</span>
    <span class="sb-name">Surikata IPS</span>
  </div>
  <nav class="sb-nav">
    <div class="sb-item active" onclick="goView('dashboard',this)">
      <i class="bi bi-speedometer2 sb-icon"></i>
      <span class="sb-label">Dashboard</span>
    </div>
    <div class="sb-item" onclick="goView('alertas',this)">
      <i class="bi bi-bell-fill sb-icon cr"></i>
      <span class="sb-label">Alertas</span>
      <span class="sb-badge" id="sb-badge">0</span>
    </div>
    <div class="sb-item" onclick="goView('detecciones',this)">
      <i class="bi bi-list-ul sb-icon"></i>
      <span class="sb-label">Detecciones</span>
    </div>
    <div class="sb-item" onclick="goView('analisis',this)">
      <i class="bi bi-graph-up sb-icon cb"></i>
      <span class="sb-label">Análisis</span>
    </div>
    <div class="sb-item" onclick="goView('predictor',this)">
      <i class="bi bi-lightning-charge-fill sb-icon" style="color:var(--yellow)"></i>
      <span class="sb-label">Predictor</span>
      <span class="sb-badge" id="sb-pred-badge"></span>
    </div>
    <div class="sb-item" onclick="goView('control',this)">
      <i class="bi bi-shield-fill sb-icon cy"></i>
      <span class="sb-label">Control ipset</span>
    </div>
    <div class="sb-sep"></div>
    <div class="sb-item" onclick="goView('sistema',this)">
      <i class="bi bi-cpu sb-icon cm"></i>
      <span class="sb-label">Sistema</span>
    </div>
  </nav>
  <div class="sb-bottom">
    <div class="sb-status">
      <span class="dot dot-g" id="sb-motor-dot"></span>
      <span class="sb-status-lbl">Motor activo</span>
    </div>
    <div class="sb-status">
      <span class="dot dot-g" id="sb-sse-dot"></span>
      <span class="sb-status-lbl">SSE conectado</span>
    </div>
  </div>
</aside>

<!-- ═══════════════ MAIN ═══════════════ -->
<div class="main-wrap">

  <!-- Topbar -->
  <div class="topbar">
    <span class="topbar-title"><span>PPI</span>-Surikata — Detección Temprana de Anomalías · UPeU 2026</span>
    <div class="topbar-right">
      <span class="chip live" id="sse-chip"><i class="bi bi-circle-fill" style="font-size:.45rem"></i> EN VIVO</span>
      <button class="sound-btn" id="sound-btn" onclick="toggleSound()">
        <i class="bi bi-volume-mute-fill"></i><span id="sound-lbl">Sonido</span>
      </button>
      <span id="clock"></span>
      <span class="chip" id="uptime-chip">—</span>
    </div>
  </div>

  <!-- Views -->
  <div class="views">

    <!-- ═══ VISTA: DASHBOARD ═══ -->
    <div class="view active" id="view-dashboard">
      <div class="sh"><i class="bi bi-speedometer2"></i>Vista General</div>
      <div class="g4 gap">
        <div class="card">
          <div class="ct"><i class="bi bi-shield-x cr"></i>BLOCK</div>
          <div class="stat-num cr" id="s-block">—</div>
          <div class="stat-sub" id="s-block-pct">—</div>
          <div class="bar-bg"><div class="bar-fill" id="bar-block" style="background:var(--red);width:0%"></div></div>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-shield-exclamation cy"></i>LIMIT</div>
          <div class="stat-num cy" id="s-limit">—</div>
          <div class="stat-sub" id="s-limit-pct">—</div>
          <div class="bar-bg"><div class="bar-fill" id="bar-limit" style="background:var(--yellow);width:0%"></div></div>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-shield-check cg"></i>PERMIT</div>
          <div class="stat-num cg" id="s-permit">—</div>
          <div class="stat-sub" id="s-permit-pct">—</div>
          <div class="bar-bg"><div class="bar-fill" id="bar-permit" style="background:var(--green);width:0%"></div></div>
        </div>
        <div class="card" style="text-align:center">
          <div class="ct" style="justify-content:center"><i class="bi bi-exclamation-triangle"></i>Nivel de Riesgo</div>
          <div class="stat-num" id="risk-num" style="color:var(--green)">—</div>
          <div style="font-size:.8rem;font-weight:700;letter-spacing:.1em" id="risk-lbl" style="color:var(--green)">—</div>
          <div class="bar-bg"><div class="bar-fill" id="risk-bar" style="width:0%"></div></div>
          <div style="margin-top:8px;font-size:.72rem;color:var(--muted)">
            F/min: <b id="s-fmin">—</b> &nbsp;|&nbsp; Lat: <b id="s-lat2" class="cg">—</b>
          </div>
        </div>
      </div>

      <div class="g4 gap">
        <div class="card2 text-center">
          <div class="ct" style="justify-content:center;margin-bottom:6px"><i class="bi bi-activity cb"></i>Flows total</div>
          <div style="font-size:1.6rem;font-weight:700;color:var(--blue)" id="s-flows">—</div>
        </div>
        <div class="card2 text-center">
          <div class="ct" style="justify-content:center;margin-bottom:6px"><i class="bi bi-key-fill co"></i>Brute Force SSH</div>
          <div style="font-size:1.6rem;font-weight:700;color:var(--orange)" id="s-bf">—</div>
        </div>
        <div class="card2 text-center">
          <div class="ct" style="justify-content:center;margin-bottom:6px"><i class="bi bi-globe cp"></i>HTTP Abuse</div>
          <div style="font-size:1.6rem;font-weight:700;color:var(--purple)" id="s-http">—</div>
        </div>
        <div class="card2 text-center">
          <div class="ct" style="justify-content:center;margin-bottom:6px"><i class="bi bi-stopwatch ct-teal"></i>Latencia media</div>
          <div style="font-size:1.6rem;font-weight:700;color:var(--teal)" id="s-lat">—</div>
        </div>
      </div>


      <div class="sh" style="margin-top:20px"><i class="bi bi-lightning-charge-fill" style="color:var(--yellow)"></i>&nbsp;Predictor XGBoost — Probabilidad de Ataque (próximos 60s)</div>
      <div class="g2 gap">
        <div class="card" style="text-align:center">
          <div class="ct" style="justify-content:center;margin-bottom:10px"><i class="bi bi-graph-up-arrow" style="color:var(--yellow)"></i>&nbsp;P(ataque en 60s)</div>
          <div id="pred-valor" style="font-size:2.8rem;font-weight:700;color:var(--green);transition:color .4s">—%</div>
          <div style="margin:10px 4px 4px"><div style="height:10px;border-radius:5px;background:var(--card2)"><div id="pred-barra" style="height:100%;border-radius:5px;width:0%;background:var(--green);transition:width .6s,background .4s"></div></div></div>
          <div style="display:flex;justify-content:center;gap:24px;margin-top:8px;font-size:.82rem">
            <span id="pred-nivel" style="font-weight:700;color:var(--green)">OK</span>
            <span id="pred-ts" style="color:var(--muted)">—</span>
          </div>
          <div style="margin-top:10px;font-size:.7rem;color:var(--muted)">θ<sub>alta</sub>=70% &nbsp;·&nbsp; θ<sub>media</sub>=40% &nbsp;·&nbsp; ciclo=60s</div>
        </div>
        <div class="card">
          <div class="ct" style="margin-bottom:8px"><i class="bi bi-clock-history" style="color:var(--yellow)"></i>&nbsp;Historial de predicciones</div>
          <div id="pred-historial" style="font-family:monospace;font-size:.78rem;line-height:1.9"></div>
          <div style="margin-top:10px;font-size:.68rem;color:var(--muted)">AUC-ROC=0.58 &nbsp;·&nbsp; 11,376 obs &nbsp;·&nbsp; split 80/20 temporal</div>
        </div>
      </div>

      <div class="g2 gap">
        <div class="card">
          <div class="ct"><i class="bi bi-bar-chart-fill"></i>Eventos por hora — últimas 24h</div>
          <div class="ch-wrap"><canvas id="chartLine"></canvas></div>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-pie-chart-fill"></i>Distribución por tipo de ataque</div>
          <div class="ch-wrap"><canvas id="chartDona"></canvas></div>
        </div>
      </div>

      <div class="sh"><i class="bi bi-cpu"></i>Métricas del Modelo — Isolation Forest</div>
      <div class="g8 gap">
        <div class="mcard"><div class="ml">Precision</div><div class="mv cg">99.54%</div>
          <div class="mb"><div class="mb-f" style="width:99.54%;background:var(--green)"></div></div></div>
        <div class="mcard"><div class="ml">Recall</div><div class="mv cy">99.40%</div>
          <div class="mb"><div class="mb-f" style="width:99.40%;background:var(--yellow)"></div></div></div>
        <div class="mcard"><div class="ml">F1 Score</div><div class="mv cp">0.9947</div>
          <div class="mb"><div class="mb-f" style="width:99.47%;background:var(--purple)"></div></div></div>
        <div class="mcard"><div class="ml">AUC-ROC</div><div class="mv cb">0.8998</div>
          <div class="mb"><div class="mb-f" style="width:89.98%;background:var(--blue)"></div></div></div>
        <div class="mcard"><div class="ml">Lat. P95</div><div class="mv cg">34.8ms</div>
          <div style="font-size:.62rem;color:var(--muted);margin-top:3px">req &lt;500ms ✓</div></div>
        <div class="mcard"><div class="ml">ITL</div><div class="mv cg">0%</div>
          <div style="font-size:.62rem;color:var(--muted);margin-top:3px">F6 · whitelist activa</div></div>
        <div class="mcard"><div class="ml">Corridas F6</div><div class="mv cb">40</div>
          <div style="font-size:.62rem;color:var(--muted);margin-top:3px">40/40 disponibilidad</div></div>
        <div class="mcard"><div class="ml">Umbrales</div>
          <div style="font-size:.8rem;font-weight:700;font-family:monospace;line-height:1.7">
            <span class="cy">τ1=-0.4459</span><br><span class="cr">τ2=-0.6027</span>
          </div></div>
      </div>
    </div><!-- /dashboard -->

    <!-- ═══ VISTA: ALERTAS ═══ -->
    <div class="view" id="view-alertas">

      <div class="alerts-topbar">
        <div class="alerts-topbar-left">
          <div class="alerts-title"><i class="bi bi-bell-fill cr"></i> &nbsp;Alertas en Tiempo Real</div>
          <div class="alerts-counters">
            <span class="ac ac-block"><i class="bi bi-shield-x"></i> BLOCK: <b id="al-block-cnt">0</b></span>
            <span class="ac ac-limit"><i class="bi bi-shield-exclamation"></i> LIMIT: <b id="al-limit-cnt">0</b></span>
          </div>
        </div>
        <div class="alerts-controls">
          <button class="flt-btn active"    id="af-all"     onclick="setAlertFilter('ALL',this)">Todos</button>
          <button class="flt-btn a-block"   id="af-block"   onclick="setAlertFilter('BLOCK',this)">BLOCK</button>
          <button class="flt-btn a-limit"   id="af-limit"   onclick="setAlertFilter('LIMIT',this)">LIMIT</button>
          <button class="flt-btn a-critica" id="af-critica" onclick="setAlertFilter('CRITICA',this)">CRÍTICA</button>
          <button class="sound-btn" id="al-sound-btn" onclick="toggleSound()" style="margin-left:4px">
            <i class="bi bi-volume-mute-fill"></i> Sonido
          </button>
          <button class="flt-btn" onclick="clearAlerts()" style="border-color:var(--red);color:var(--red)"><i class="bi bi-trash3"></i> Limpiar todo</button>
        </div>
      </div>

      <!-- Ticker de última alerta -->
      <div style="background:rgba(248,81,73,.06);border:1px solid rgba(248,81,73,.2);
        border-radius:8px;padding:8px 14px;margin-bottom:12px;
        display:flex;align-items:center;gap:10px;font-size:.78rem" id="last-alert-bar">
        <span style="color:var(--muted)"><i class="bi bi-clock"></i> Última alerta:</span>
        <span id="last-alert-txt" style="font-family:monospace;color:var(--red)">Sin alertas aún</span>
      </div>

      <!-- Feed -->
      <div class="alerts-feed" id="alerts-feed">
        <div style="text-align:center;padding:60px 0;color:var(--muted)">
          <i class="bi bi-shield-check" style="font-size:3rem;color:var(--green);display:block;margin-bottom:12px"></i>
          Sin alertas — sistema normal
        </div>
      </div>
    </div><!-- /alertas -->

    <!-- ═══ VISTA: DETECCIONES ═══ -->
    <div class="view" id="view-detecciones">
      <div class="sh"><i class="bi bi-table"></i>Detecciones — Historial Completo</div>
      <div class="card">
        <div class="tbl-ctrl">
          <button class="flt-btn active" id="tf-all"   onclick="setTblFilter('ALL',this)">Todos</button>
          <button class="flt-btn a-block" id="tf-block" onclick="setTblFilter('BLOCK',this)"><i class="bi bi-x-circle cr"></i> BLOCK</button>
          <button class="flt-btn a-limit" id="tf-limit" onclick="setTblFilter('LIMIT',this)"><i class="bi bi-dash-circle cy"></i> LIMIT</button>
          <input class="srch" id="tbl-srch" placeholder="🔍 IP o tipo..." oninput="renderTbl()">
          <button class="btn-exp" onclick="exportCSV()"><i class="bi bi-download"></i> Exportar CSV</button>
          <span style="margin-left:auto;font-size:.72rem;color:var(--muted)" id="tbl-cnt"></span>
        </div>
        <div class="tbl-wrap">
          <table>
            <thead><tr>
              <th>Hora</th><th>IP Origen</th><th>Destino:Puerto</th>
              <th>Proto</th><th>Score IF</th><th>Grado</th><th>Tipo Ataque</th><th>Decisión</th>
            </tr></thead>
            <tbody id="tbl-body">
              <tr><td colspan="8" style="text-align:center;padding:30px;color:var(--muted)">Cargando...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div><!-- /detecciones -->

    <!-- ═══ VISTA: ANÁLISIS ═══ -->
    <div class="view" id="view-analisis">
      <div class="sh"><i class="bi bi-graph-up"></i>Análisis Temporal</div>
      <div class="card gap">
        <div class="ct"><i class="bi bi-bar-chart-fill"></i>Eventos BLOCK y LIMIT por hora — últimas 24h</div>
        <div class="ch-wrap-lg"><canvas id="chartLine2"></canvas></div>
      </div>
      <div class="g2 gap">
        <div class="card">
          <div class="ct"><i class="bi bi-pie-chart-fill"></i>Distribución por tipo de ataque</div>
          <div class="ch-wrap-lg"><canvas id="chartDona2"></canvas></div>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-bar-chart-line"></i>Top IPs detectadas</div>
          <div style="padding:8px 0;font-size:.8rem;color:var(--muted)" id="top-ips-list">Sin datos aún</div>
        </div>
      </div>
    </div><!-- /analisis -->

    <!-- ═══ VISTA: PREDICTOR ═══ -->
    <div class="view" id="view-predictor">
      <div class="sh"><i class="bi bi-lightning-charge-fill" style="color:var(--yellow)"></i>Módulo Predictor XGBoost — Tiempo Real</div>

      <!-- KPIs superiores -->
      <div class="g4 gap">
        <div class="card" style="text-align:center;grid-column:span 1">
          <div class="ct" style="justify-content:center"><i class="bi bi-graph-up-arrow cy"></i>P(ataque/60s)</div>
          <div id="pg-valor" style="font-size:3.2rem;font-weight:800;color:var(--green);transition:color .4s;line-height:1">—%</div>
          <div style="margin:10px 6px 4px">
            <div style="height:12px;border-radius:6px;background:var(--card2);position:relative">
              <div id="pg-barra" style="height:100%;border-radius:6px;width:0%;background:var(--green);transition:width .6s,background .4s"></div>
              <div style="position:absolute;left:40%;top:0;height:100%;width:1px;background:rgba(227,179,65,.5)"></div>
              <div style="position:absolute;left:70%;top:0;height:100%;width:1px;background:rgba(248,81,73,.5)"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.62rem;color:var(--muted);margin-top:3px">
              <span>0%</span><span class="cy">40%</span><span class="cr">70%</span><span>100%</span>
            </div>
          </div>
          <div id="pg-nivel" style="font-weight:700;font-size:.9rem;color:var(--green);margin-top:4px">OK</div>
          <div style="font-size:.68rem;color:var(--muted);margin-top:6px">
            θ<sub>alta</sub>=70% · θ<sub>media</sub>=40% · ciclo=60s
          </div>
        </div>
        <div class="card" style="grid-column:span 1">
          <div class="ct"><i class="bi bi-cpu cb"></i>Estado del modelo</div>
          <div style="font-size:.82rem;line-height:2">
            <div><span class="cm">Algoritmo:</span> <b>XGBoost (temporal)</b></div>
            <div><span class="cm">AUC-ROC:</span> <b class="cy">0.58</b> <span class="cm" style="font-size:.72rem">(test set 98.5% positivo)</span></div>
            <div><span class="cm">Features:</span> <b>10</b> (gap, lag1-3, mean5, std5…)</div>
            <div><span class="cm">Training:</span> <b>11,376 obs</b> · split 80/20</div>
            <div><span class="cm">Servicio:</span> <b class="cg">ppi-predictor.service</b></div>
          </div>
        </div>
        <div class="card" style="grid-column:span 2">
          <div class="ct"><i class="bi bi-info-circle"></i>Señal predictiva — cómo funciona</div>
          <div style="font-size:.8rem;line-height:1.8;color:var(--muted)">
            El motor escribe estadísticas cada <b style="color:var(--txt)">500 flows</b>.
            El tiempo entre dos líneas consecutivas (<b style="color:var(--yellow)">gap</b>) refleja la tasa de tráfico.
            Un gap corto = tráfico intenso = posible ataque.
          </div>
          <div style="display:flex;gap:12px;margin-top:10px">
            <div style="flex:1;text-align:center;background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.3);border-radius:8px;padding:8px">
              <div style="font-size:1.3rem;font-weight:700;color:var(--green)">~174s</div>
              <div style="font-size:.7rem;color:var(--muted)">Gap normal</div>
            </div>
            <div style="flex:1;text-align:center;background:rgba(227,179,65,.1);border:1px solid rgba(227,179,65,.3);border-radius:8px;padding:8px">
              <div style="font-size:1.3rem;font-weight:700;color:var(--yellow)">~60s</div>
              <div style="font-size:.7rem;color:var(--muted)">Moderado</div>
            </div>
            <div style="flex:1;text-align:center;background:rgba(248,81,73,.1);border:1px solid rgba(248,81,73,.3);border-radius:8px;padding:8px">
              <div style="font-size:1.3rem;font-weight:700;color:var(--red)">~17s</div>
              <div style="font-size:.7rem;color:var(--muted)">Ataque (10×)</div>
            </div>
            <div style="flex:1;text-align:center;background:rgba(88,166,255,.1);border:1px solid rgba(88,166,255,.3);border-radius:8px;padding:8px">
              <div style="font-size:1.3rem;font-weight:700;color:var(--blue)">MAX_GAP</div>
              <div style="font-size:.7rem;color:var(--muted)">&gt;600s → sin pred.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Gráficas -->
      <div class="g2 gap">
        <div class="card">
          <div class="ct"><i class="bi bi-graph-up-arrow cy"></i>P(ataque) en tiempo real — últimas 20 predicciones</div>
          <div class="ch-wrap-lg"><canvas id="chartPred"></canvas></div>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-activity cb"></i>Gap entre estadísticas (seg) — tasa de tráfico</div>
          <div class="ch-wrap-lg"><canvas id="chartGap"></canvas></div>
          <div style="display:flex;gap:16px;margin-top:6px;font-size:.68rem">
            <span style="color:var(--red)">━ 60s umbral</span>
            <span style="color:var(--green)">━ 174s normal</span>
            <span style="color:var(--muted)">gap bajo → tráfico intenso</span>
          </div>
        </div>
      </div>

      <!-- Feed predicciones -->
      <div class="sh"><i class="bi bi-clock-history"></i>Historial de predicciones</div>
      <div class="card">
        <div id="pred-feed" style="font-family:monospace;font-size:.8rem;line-height:2;max-height:220px;overflow-y:auto">
          <span class="cm">Esperando predicciones...</span>
        </div>
      </div>
    </div><!-- /predictor -->

    <!-- ═══ VISTA: CONTROL IPSET ═══ -->
    <div class="view" id="view-control">
      <div class="sh"><i class="bi bi-shield-fill"></i>Control Inline — ipset</div>
      <div class="g2 gap">
        <div class="card">
          <div class="ct cr"><i class="bi bi-x-circle-fill"></i>ppi_blocked — DROP total</div>
          <div id="ctrl-blocked"><span class="cm">Sin IPs bloqueadas</span></div>
          <div class="manual-row">
            <input class="manual-ip" id="m-ip" placeholder="IP a bloquear (ej: 192.168.0.100)">
            <button class="btn-blk-m" onclick="manualBlock()"><i class="bi bi-ban"></i> Bloquear</button>
          </div>
        </div>
        <div class="card">
          <div class="ct cy"><i class="bi bi-dash-circle-fill"></i>ppi_limited — hashlimit 100 pkt/s</div>
          <div id="ctrl-limited"><span class="cm">Sin IPs limitadas</span></div>
        </div>
      </div>
      <div class="sh"><i class="bi bi-clock-history"></i>Últimas IPs detectadas</div>
      <div class="card">
        <div id="ctrl-recent" style="display:flex;flex-wrap:wrap;gap:6px">
          <span class="cm" style="font-size:.8rem">Sin eventos recientes</span>
        </div>
      </div>
    </div><!-- /control -->

    <!-- ═══ VISTA: SISTEMA ═══ -->
    <div class="view" id="view-sistema">
      <div class="sh"><i class="bi bi-cpu"></i>Información del Sistema</div>
      <div class="g2 gap">
        <div class="card">
          <div class="ct"><i class="bi bi-hdd-network"></i>Arquitectura del Laboratorio</div>
          <table style="width:100%;font-size:.8rem;border-collapse:collapse">
            <tr><td class="cm" style="padding:6px 0;width:150px">Desktop (Admin)</td><td class="mono">192.168.0.20 — tráfico normal</td></tr>
            <tr><td class="cm" style="padding:6px 0">Kali (Atacante)</td><td class="mono">192.168.0.100 — tráfico anómalo</td></tr>
            <tr><td class="cm" style="padding:6px 0">Sensor Suricata</td><td class="mono">192.168.0.110 — captura + motor</td></tr>
            <tr><td class="cm" style="padding:6px 0">Servidor nginx</td><td class="mono">192.168.0.120 — :80 / :22</td></tr>
            <tr><td class="cm" style="padding:6px 0">Control inline</td><td class="mono">ipset + iptables (kernel)</td></tr>
            <tr><td class="cm" style="padding:6px 0">Motor inicio</td><td class="mono cg" id="sys-motor">—</td></tr>
            <tr><td class="cm" style="padding:6px 0">Uptime dashboard</td><td class="mono" id="sys-uptime">—</td></tr>
            <tr><td class="cm" style="padding:6px 0">Clientes SSE</td><td class="mono cb" id="sys-sse">—</td></tr>
          </table>
        </div>
        <div class="card">
          <div class="ct"><i class="bi bi-braces"></i>Isolation Forest — Configuración</div>
          <table style="width:100%;font-size:.8rem;border-collapse:collapse">
            <tr><td class="cm" style="padding:6px 0;width:160px">Algoritmo</td><td class="mono">Isolation Forest</td></tr>
            <tr><td class="cm" style="padding:6px 0">scikit-learn</td><td class="mono">1.9.0</td></tr>
            <tr><td class="cm" style="padding:6px 0">n_estimators</td><td class="mono">300 árboles</td></tr>
            <tr><td class="cm" style="padding:6px 0">contamination</td><td class="mono">0.05</td></tr>
            <tr><td class="cm" style="padding:6px 0">Entrenamiento</td><td class="mono">53,708 flujos normales (Grupo A 80%)</td></tr>
            <tr><td class="cm" style="padding:6px 0">Dataset total</td><td class="mono">401,424 flujos · 47 archivos</td></tr>
            <tr><td class="cm" style="padding:6px 0">Features</td><td class="mono">14 (pkts, bytes, rates, proto)</td></tr>
            <tr><td class="cm" style="padding:6px 0">Modelo (.pkl)</td><td class="mono">2.4 MB en RAM</td></tr>
          </table>
        </div>
      </div>
      <div class="sh"><i class="bi bi-info-circle"></i>Cómo funciona la sincronización</div>
      <div class="card">
        <div style="font-size:.82rem;line-height:1.8;color:var(--muted)">
          <p>El motor (<code style="color:var(--txt)">motor_decision.py</code>) escribe cada decisión al log <b>simultáneamente</b> con el envío a Telegram.</p>
          <p>Este dashboard usa <b style="color:var(--blue)">Server-Sent Events (SSE)</b>: el lector de log detecta la nueva línea en ~150ms y la empuja al browser sin polling.</p>
          <p>Resultado: <b style="color:var(--green)">la alerta aparece aquí antes que el mensaje de Telegram</b> llega al teléfono (Telegram tiene ~300-800ms de latencia de red).</p>
          <div style="margin-top:12px;padding:10px 14px;background:var(--card2);border-radius:8px;font-size:.78rem">
            <b>Flujo de tiempo:</b><br>
            Motor detecta anomalía → escribe log + llama Telegram async<br>
            &nbsp;&nbsp;├ Log reader detecta línea: <b class="cg">~150ms</b> → SSE push → alerta en dashboard<br>
            &nbsp;&nbsp;└ Telegram API entrega: <b class="cy">~300-800ms</b> → notificación en teléfono
          </div>
        </div>
      </div>
    </div><!-- /sistema -->

  </div><!-- /views -->
</div><!-- /main-wrap -->

<!-- Modal -->
<div class="modal-bg" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal-box">
    <div class="modal-hd">
      <span class="modal-t" id="modal-t">Detalle</span>
      <button class="modal-x" onclick="closeModal()"><i class="bi bi-x-lg"></i></button>
    </div>
    <div id="modal-body"></div>
    <div id="modal-actions" style="margin-top:14px;display:flex;gap:8px"></div>
  </div>
</div>

<!-- Toasts -->
<div class="toast-c" id="toast-c"></div>

<script>
// ═══════════════════════════════════════════════
// CONSTANTES Y ESTADO
// ═══════════════════════════════════════════════
const TIPO_IC = {
  SYN_FLOOD:'bi-lightning-fill',      UDP_FLOOD:'bi-broadcast',
  ICMP_FLOOD:'bi-reception-4',        PORT_SCAN:'bi-search',
  HTTP_ABUSE:'bi-globe',              BRUTE_FORCE_SSH:'bi-key-fill',
  ANOMALIA_GENERICA:'bi-question-circle', BAJA_ANOMALIA:'bi-info-circle'
};
const GRAVEDAD = {
  SYN_FLOOD:'Caída del servicio HTTP/TCP',
  UDP_FLOOD:'Saturación del ancho de banda',
  ICMP_FLOOD:'Saturación de red + pérdida conectividad',
  PORT_SCAN:'Reconocimiento — preparación de ataque',
  HTTP_ABUSE:'Agotamiento de conexiones del servidor web',
  BRUTE_FORCE_SSH:'Riesgo de acceso no autorizado al servidor',
  ANOMALIA_GENERICA:'Comportamiento desconocido — requiere evaluación',
  BAJA_ANOMALIA:'Desviación leve, sin impacto inmediato'
};

let soundOn    = false;
let alertFilt  = 'ALL';
let tblFilt    = 'ALL';
let allEvents  = [];
let alertsData = [];
let unreadCnt  = 0;
let sseOk      = false;

const AudioCtx = window.AudioContext || window.webkitAudioContext;
function beep(f=880,d=.12,v=.35){
  if(!soundOn) return;
  try{
    const ac=new AudioCtx(),o=ac.createOscillator(),g=ac.createGain();
    o.connect(g);g.connect(ac.destination);
    o.frequency.value=f;
    g.gain.setValueAtTime(v,ac.currentTime);
    g.gain.exponentialRampToValueAtTime(.001,ac.currentTime+d);
    o.start();o.stop(ac.currentTime+d);
  }catch(e){}
}

// ═══════════════════════════════════════════════
// SIDEBAR / NAVEGACIÓN
// ═══════════════════════════════════════════════
function goView(name, el){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.sb-item').forEach(i=>i.classList.remove('active'));
  document.getElementById('view-'+name).classList.add('active');
  if(el) el.classList.add('active');
  if(name==='alertas'){ unreadCnt=0; updateBadge(); }
  if(name==='analisis') refreshCharts2();
  if(name==='detecciones') renderTbl();
  if(name==='control') refreshControl();
  if(name==='predictor'){ initPredictorCharts(); loadPredictorData(); }
}

// ═══════════════════════════════════════════════
function actualizarPredictor(ev) {
  const p   = Math.round(ev.p * 100);
  const col = p>=70?"var(--red)":p>=40?"var(--yellow)":"var(--green)";
  const lbl = (ev.nivel||"").replace(/[-_]/g,' ').trim() || (p>=70?"ALERTA":p>=40?"RIESGO MEDIO":"OK");
  const ts  = ev.ts||"—";

  // Panel dashboard principal
  const ve=document.getElementById("pred-valor");
  const be=document.getElementById("pred-barra");
  const ne=document.getElementById("pred-nivel");
  const te=document.getElementById("pred-ts");
  const he=document.getElementById("pred-historial");
  if(ve){ve.textContent=p+"%";ve.style.color=col;}
  if(be){be.style.width=p+"%";be.style.background=col;}
  if(ne){ne.textContent=lbl;ne.style.color=col;}
  if(te){te.textContent=ts;}
  if(he){
    const row=`<div style="color:${col}">${ts} &nbsp; ${p}% &nbsp; ${lbl}</div>`;
    he.innerHTML=row+he.innerHTML.split("<div").slice(0,7).join("<div");
  }

  // Gauge vista Predictor
  const pg=document.getElementById("pg-valor");
  const pb=document.getElementById("pg-barra");
  const pn=document.getElementById("pg-nivel");
  if(pg){pg.textContent=p+"%";pg.style.color=col;}
  if(pb){pb.style.width=p+"%";pb.style.background=col;}
  if(pn){pn.textContent=lbl;pn.style.color=col;}

  // Chart P% (vista predictor)
  if(chartPred){
    chartPred.data.labels.push(ts);
    chartPred.data.datasets[0].data.push(p);
    if(chartPred.data.labels.length>20){
      chartPred.data.labels.shift();
      chartPred.data.datasets[0].data.shift();
    }
    chartPred.update('none');
  }

  // Feed predicciones
  const feed=document.getElementById("pred-feed");
  if(feed){
    if(feed.querySelector('.cm')) feed.innerHTML='';
    const row=document.createElement('div');
    row.style.cssText=`color:${col};border-bottom:1px solid var(--border);padding:2px 0`;
    row.textContent=`${ts}  P=${p}%  ${lbl}`;
    feed.insertBefore(row, feed.firstChild);
    while(feed.children.length>15) feed.removeChild(feed.lastChild);
  }

  // Badge sidebar predictor si está en alerta
  const badge=document.getElementById("sb-pred-badge");
  if(badge){
    if(p>=70){badge.textContent="!";badge.classList.add("show");}
    else badge.classList.remove("show");
  }
}

function actualizarGap(ev){
  if(!chartGap) return;
  const col = ev.gap<60?"var(--red)":ev.gap<120?"var(--yellow)":"var(--green)";
  chartGap.data.labels.push(ev.ts);
  chartGap.data.datasets[0].data.push(ev.gap);
  chartGap.data.datasets[0].pointBackgroundColor = chartGap.data.datasets[0].pointBackgroundColor||[];
  if(Array.isArray(chartGap.data.datasets[0].pointBackgroundColor))
    chartGap.data.datasets[0].pointBackgroundColor.push(col);
  if(chartGap.data.labels.length>20){
    chartGap.data.labels.shift();
    chartGap.data.datasets[0].data.shift();
    if(Array.isArray(chartGap.data.datasets[0].pointBackgroundColor))
      chartGap.data.datasets[0].pointBackgroundColor.shift();
  }
  chartGap.update('none');
}

// SSE — RECEPCIÓN INSTANTÁNEA
// ═══════════════════════════════════════════════
function initSSE(){
  const es = new EventSource('/api/stream');

  es.onopen = ()=>{
    sseOk=true;
    document.getElementById('sse-chip').innerHTML='<i class="bi bi-circle-fill" style="font-size:.45rem"></i> EN VIVO';
    document.getElementById('sse-chip').className='chip live';
    document.getElementById('sb-sse-dot').className='dot dot-g';
  };

  es.onmessage = (e)=>{
    const ev = JSON.parse(e.data);
    if(ev.type==='predictor'){actualizarPredictor(ev);return;}
    if(ev.type==='stats_gap'){actualizarGap(ev);return;}

    // 1. Guardar en allEvents
    allEvents.unshift(ev);
    if(allEvents.length>500) allEvents.pop();

    // 2. Agregar al feed de alertas (BLOCK y LIMIT)
    if(ev.accion==='BLOCK'||ev.accion==='LIMIT'){
      alertsData.unshift(ev);
      if(alertsData.length>100) alertsData.pop();

      // Feed de alertas (si estamos en esa vista, insertar al tope)
      const feed = document.getElementById('view-alertas');
      if(feed.classList.contains('active')){
        prependAlert(ev);
      } else {
        unreadCnt++;
        updateBadge();
      }

      // Ticker última alerta
      document.getElementById('last-alert-txt').textContent =
        `${ev.ts} | ${ev.accion} | ${ev.src} → :${ev.port} | ${(ev.tipo||'').replace(/_/g,' ')} | Score: ${ev.score}`;

      // Toast
      showToast(ev);

      // Beep
      if(ev.accion==='BLOCK') beep(880,.18,.4);
      else beep(440,.1,.2);

      // Actualizar contadores alertas
      updateAlertCounters();
    }

    // 3. Actualizar tabla si estamos en detecciones
    const dv = document.getElementById('view-detecciones');
    if(dv.classList.contains('active')) renderTbl();
  };

  es.onerror = ()=>{
    sseOk=false;
    document.getElementById('sse-chip').innerHTML='<i class="bi bi-circle-fill" style="font-size:.45rem;color:var(--red)"></i> RECONECTANDO';
    document.getElementById('sse-chip').className='chip';
    document.getElementById('sb-sse-dot').className='dot dot-r';
    setTimeout(initSSE, 3000);
    es.close();
  };
}

// ═══════════════════════════════════════════════
// PANEL DE ALERTAS
// ═══════════════════════════════════════════════
function alertCard(ev, isNew=false){
  const ic    = TIPO_IC[ev.tipo]||'bi-shield-x';
  const color = ev.accion==='BLOCK'?'var(--red)':'var(--yellow)';
  const grd   = ev.grado && ev.grado!=='—' ? ev.grado : 'NORMAL';
  const grav  = GRAVEDAD[ev.tipo]||'—';
  const showUnbl = ev.accion==='BLOCK';
  return `<div class="alert-card ${ev.accion}${isNew?' new-alert':''}" onclick='openModal(${JSON.stringify(ev)})'>
    ${isNew?'<span class="alert-new-dot"></span>':''}
    <div class="alert-left">
      <i class="bi ${ic} alert-icon-big" style="color:${color}"></i>
      <span class="alert-ts-small">${ev.ts}</span>
      <span class="bdg bdg-${ev.accion}" style="font-size:.62rem">${ev.accion}</span>
    </div>
    <div class="alert-center">
      <div class="alert-row1">
        <span class="alert-ip" style="color:${color}">${ev.src}</span>
        <span class="alert-arrow"><i class="bi bi-arrow-right"></i></span>
        <span class="alert-dst">${ev.dst}:${ev.port} / ${ev.proto}</span>
        <span class="bdg bdg-${grd}">${grd}</span>
      </div>
      <div class="alert-row2">
        <i class="bi ${ic}" style="color:${color}"></i>
        <span class="alert-tipo-big" style="color:${color}">${(ev.tipo||'—').replace(/_/g,' ')}</span>
        <span class="alert-score">Score: <b>${ev.score}</b></span>
        ${ev.byte_ratio!=='—'?`<span class="alert-score" style="color:var(--muted)">br: <b>${parseFloat(ev.byte_ratio).toFixed(1)}</b></span>`:''}
      </div>
      <div class="alert-gravedad"><i class="bi bi-info-circle"></i> ${grav}</div>
    </div>
    <div class="alert-right">
      ${showUnbl?`<button class="btn-sm btn-unblock" onclick="event.stopPropagation();unblockIP('${ev.src}')"><i class="bi bi-unlock"></i> Desbloquear</button>`:''}
      <button class="btn-sm" onclick="event.stopPropagation();openModal(${JSON.stringify(ev)})"><i class="bi bi-eye"></i> Detalle</button>
    </div>
  </div>`;
}

function prependAlert(ev){
  const feed = document.getElementById('alerts-feed');
  // Remover "sin alertas" si existe
  if(feed.querySelector('.bi-shield-check')) feed.innerHTML='';
  const div = document.createElement('div');
  div.innerHTML = alertCard(ev, true);
  feed.insertBefore(div.firstElementChild, feed.firstChild);
  // Máximo 50 cards
  while(feed.children.length > 50) feed.removeChild(feed.lastChild);
  setTimeout(()=>{
    const dot = feed.querySelector('.alert-new-dot');
    if(dot) dot.remove();
  }, 4000);
}

function renderAlertsFeed(){
  let data = alertsData;
  if(alertFilt==='BLOCK')   data=data.filter(e=>e.accion==='BLOCK');
  if(alertFilt==='LIMIT')   data=data.filter(e=>e.accion==='LIMIT');
  if(alertFilt==='CRITICA') data=data.filter(e=>e.grado==='CRITICA');
  const feed = document.getElementById('alerts-feed');
  if(!data.length){
    feed.innerHTML='<div style="text-align:center;padding:60px 0;color:var(--muted)"><i class="bi bi-shield-check" style="font-size:3rem;color:var(--green);display:block;margin-bottom:12px"></i>Sin alertas con este filtro</div>';
    return;
  }
  feed.innerHTML = data.map(e=>alertCard(e)).join('');
}

function setAlertFilter(f, btn){
  alertFilt=f;
  document.querySelectorAll('#view-alertas .flt-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderAlertsFeed();
}

async function clearAlerts(){
  await fetch('/api/clear',{method:'POST'});
  alertsData=[];
  allEvents=[];
  unreadCnt=0;
  updateBadge();
  updateAlertCounters();
  document.getElementById('alerts-feed').innerHTML=
    '<div style="text-align:center;padding:60px 0;color:var(--muted)"><i class="bi bi-shield-check" style="font-size:3rem;color:var(--green);display:block;margin-bottom:12px"></i>Alertas limpiadas — esperando nuevos eventos</div>';
  document.getElementById('last-alert-txt').textContent='Sin alertas aún';
  document.getElementById('al-block-cnt').textContent='0';
  document.getElementById('al-limit-cnt').textContent='0';
  // limpiar tabla detecciones también
  document.getElementById('tbl-body').innerHTML=
    '<tr><td colspan="8" style="text-align:center;padding:30px;color:var(--muted)">Sin eventos</td></tr>';
  notify('✅ Alertas limpiadas','cg');
}

function updateAlertCounters(){
  const blk=alertsData.filter(e=>e.accion==='BLOCK').length;
  const lim=alertsData.filter(e=>e.accion==='LIMIT').length;
  document.getElementById('al-block-cnt').textContent=blk;
  document.getElementById('al-limit-cnt').textContent=lim;
}

function updateBadge(){
  const b=document.getElementById('sb-badge');
  if(unreadCnt>0){ b.textContent=unreadCnt>99?'99+':unreadCnt; b.classList.add('show'); }
  else { b.classList.remove('show'); }
}

// ═══════════════════════════════════════════════
// TABLA DETECCIONES
// ═══════════════════════════════════════════════
function setTblFilter(f, btn){
  tblFilt=f;
  document.querySelectorAll('#view-detecciones .flt-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  renderTbl();
}

function renderTbl(){
  const srch = document.getElementById('tbl-srch')?.value.trim().toLowerCase()||'';
  let rows = allEvents.filter(e=>{
    if(tblFilt!=='ALL' && e.accion!==tblFilt) return false;
    if(srch && !e.src.includes(srch) && !(e.tipo||'').toLowerCase().includes(srch)) return false;
    return true;
  });
  document.getElementById('tbl-cnt').textContent=rows.length+' eventos';
  if(!rows.length){
    document.getElementById('tbl-body').innerHTML=
      '<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--muted)">Sin resultados</td></tr>';
    return;
  }
  document.getElementById('tbl-body').innerHTML=rows.slice(0,200).map(e=>{
    const grd=e.grado&&e.grado!=='—'?e.grado:'NORMAL';
    const ic=TIPO_IC[e.tipo]||'bi-question-circle';
    const bc=e.accion==='BLOCK'?'var(--red)':e.accion==='LIMIT'?'var(--yellow)':'var(--green)';
    return `<tr onclick='openModal(${JSON.stringify(e)})'>
      <td class="mono cm">${e.ts}</td>
      <td class="mono" style="color:${bc};font-weight:600">${e.src}</td>
      <td class="mono cm">${e.dst}:${e.port}</td>
      <td><span class="bdg" style="background:rgba(139,148,158,.1);color:var(--muted);border:1px solid var(--border)">${e.proto}</span></td>
      <td class="mono cm">${e.score}</td>
      <td><span class="bdg bdg-${grd}">${grd}</span></td>
      <td style="white-space:nowrap"><i class="bi ${ic}" style="color:${bc}"></i> ${(e.tipo||'—').replace(/_/g,' ')}</td>
      <td><span class="bdg bdg-${e.accion}">${e.accion}</span></td>
    </tr>`;
  }).join('');
}

function exportCSV(){
  const rows=allEvents.filter(e=>{
    if(tblFilt!=='ALL'&&e.accion!==tblFilt) return false;
    return true;
  });
  const h='Hora,IP_Origen,Destino,Puerto,Proto,Score,Grado,Tipo,Decision\n';
  const csv=h+rows.map(e=>
    `${e.ts_dt||e.ts},${e.src},${e.dst},${e.port},${e.proto},${e.score},${e.grado||''},${e.tipo||''},${e.accion}`
  ).join('\n');
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download=`ppi_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
}

// ═══════════════════════════════════════════════
// CONTROL IPSET
// ═══════════════════════════════════════════════
function refreshControl(){
  fetch('/api/stats').then(r=>r.json()).then(s=>{
    const bl=s.ipset_blocked;
    document.getElementById('ctrl-blocked').innerHTML=bl.length
      ? bl.map(ip=>`<span class="ip-pill ip-bl">
          <i class="bi bi-x-circle"></i>${ip}
          <button class="unbl-btn" onclick="unblockIP('${ip}')" title="Desbloquear"><i class="bi bi-unlock"></i></button>
        </span>`).join('')
      : '<span class="cm">Sin IPs bloqueadas</span>';
    const li=s.ipset_limited;
    document.getElementById('ctrl-limited').innerHTML=li.length
      ? li.map(ip=>`<span class="ip-pill ip-lm">
          <i class="bi bi-dash-circle"></i>${ip}
          <button class="unbl-btn" onclick="unblockIP('${ip}')" title="Desbloquear"><i class="bi bi-unlock"></i></button>
        </span>`).join('')
      : '<span class="cm">Sin IPs limitadas</span>';
  }).catch(()=>{});

  // IPs recientes del feed
  const recientes=[...new Set(alertsData.slice(0,20).map(e=>e.src))];
  document.getElementById('ctrl-recent').innerHTML=recientes.length
    ? recientes.map(ip=>`<span class="ip-pill" style="background:var(--card2);border:1px solid var(--border);color:var(--txt)">
        <i class="bi bi-person-fill cm"></i>${ip}
        <button class="unbl-btn" onclick="manualBlockIP('${ip}')" title="Bloquear">
          <i class="bi bi-ban cr"></i>
        </button>
      </span>`).join('')
    : '<span class="cm" style="font-size:.8rem">Sin eventos recientes</span>';
}

async function unblockIP(ip){
  closeModal();
  const r=await fetch('/api/unblock',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({ip})});
  const d=await r.json();
  notify(d.ok?`✅ ${ip} desbloqueada`:`❌ Error al desbloquear`, d.ok?'cg':'cr');
  refreshControl();
}

async function manualBlock(){
  const ip=document.getElementById('m-ip').value.trim();
  if(!ip){notify('Ingresa una IP','cy');return;}
  await manualBlockIP(ip);
  document.getElementById('m-ip').value='';
}

async function manualBlockIP(ip){
  const r=await fetch('/api/block',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({ip})});
  const d=await r.json();
  notify(d.ok?`🔴 ${ip} bloqueada`:`❌ Error`, d.ok?'cr':'cy');
  refreshControl();
}

function notify(msg,cls){
  const d=document.createElement('div');
  d.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:9999;'+
    'background:var(--card);border:1px solid var(--border);border-radius:8px;'+
    'padding:10px 20px;font-size:.82rem;box-shadow:0 4px 24px rgba(0,0,0,.6);white-space:nowrap';
  d.className=cls; d.textContent=msg;
  document.body.appendChild(d);
  setTimeout(()=>d.remove(),3000);
}

// ═══════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════
function openModal(ev){
  const grd=ev.grado&&ev.grado!=='—'?ev.grado:'—';
  const rows=[
    ['Decisión',`<span class="bdg bdg-${ev.accion}">${ev.accion}</span>`],
    ['Grado',`<span class="bdg bdg-${grd}">${grd}</span>`],
    ['Tipo',(ev.tipo||'—').replace(/_/g,' ')],
    ['Timestamp',ev.ts_dt||ev.ts],
    ['IP Origen',`<span class="mono cr">${ev.src}</span>`],
    ['IP Destino',`<span class="mono">${ev.dst}</span>`],
    ['Puerto / Proto',`:${ev.port} / ${ev.proto}`],
    ['Score IF',`<span class="mono">${ev.score}</span>`],
    ...(ev.byte_ratio&&ev.byte_ratio!=='—'?[['byte_ratio',`<span class="mono">${parseFloat(ev.byte_ratio).toFixed(2)}</span> <span style="color:var(--muted);font-size:.8em">(normal ≈ 0.95)</span>`]]:[]),
    ...(ev.pkt_rate&&ev.pkt_rate!=='—'?[['pkt_rate',`<span class="mono">${parseFloat(ev.pkt_rate).toFixed(1)}</span> pkt/s`]]:[]),
    ['Gravedad',GRAVEDAD[ev.tipo]||'—'],
  ];
  document.getElementById('modal-t').textContent=`${ev.accion} — ${(ev.tipo||'').replace(/_/g,' ')}`;
  document.getElementById('modal-body').innerHTML=
    rows.map(([k,v])=>`<div class="dr"><span class="dk">${k}</span><span class="dv">${v}</span></div>`).join('');
  document.getElementById('modal-actions').innerHTML=
    ev.accion==='BLOCK'
      ?`<button onclick="unblockIP('${ev.src}')" style="background:rgba(63,185,80,.15);border:1px solid var(--green);
          color:var(--green);padding:7px 16px;border-radius:6px;cursor:pointer;font-size:.8rem">
          <i class="bi bi-unlock"></i> Desbloquear ${ev.src}</button>`:'';
  document.getElementById('modal').classList.add('show');
}
function closeModal(){document.getElementById('modal').classList.remove('show')}

// ═══════════════════════════════════════════════
// TOASTS
// ═══════════════════════════════════════════════
function showToast(ev){
  const c=document.getElementById('toast-c');
  const ic=ev.accion==='BLOCK'?'🔴':'🟡';
  const cls=ev.accion==='BLOCK'?'bl-t':'lm-t';
  const d=document.createElement('div');
  d.className=`toast ${cls}`;
  d.innerHTML=`
    <div class="t-icon">${ic}</div>
    <div class="t-body">
      <div class="t-title">${ev.accion} · ${(ev.tipo||'').replace(/_/g,' ')}</div>
      <div class="t-msg">${ev.src} → :${ev.port} · ${ev.grado} · ${ev.score}</div>
    </div>`;
  d.onclick=()=>{ goView('alertas',document.querySelector('.sb-item:nth-child(2)')); d.remove(); };
  c.appendChild(d);
  while(c.children.length>4) c.firstChild.remove();
  setTimeout(()=>{ d.style.animation='toastOut .3s ease forwards'; setTimeout(()=>d.remove(),300); },5000);
}

// ═══════════════════════════════════════════════
// SONIDO
// ═══════════════════════════════════════════════
function toggleSound(){
  soundOn=!soundOn;
  ['sound-btn','al-sound-btn'].forEach(id=>{
    const b=document.getElementById(id);
    if(!b) return;
    b.className='sound-btn'+(soundOn?' on':'');
    b.innerHTML=soundOn
      ?'<i class="bi bi-volume-up-fill"></i> Sonido ON'
      :'<i class="bi bi-volume-mute-fill"></i> Sonido';
  });
  if(soundOn) beep(660,.1,.3);
}

// ═══════════════════════════════════════════════
// STATS POLLING (para datos agregados)
// ═══════════════════════════════════════════════
async function fetchStats(){
  try{
    const r=await fetch('/api/stats');
    const s=await r.json();
    const tot=(s.block+s.limit+s.permit)||1;
    const p=v=>(v/tot*100).toFixed(1);

    // dashboard view
    document.getElementById('s-block').textContent   = s.block.toLocaleString();
    document.getElementById('s-limit').textContent   = s.limit.toLocaleString();
    document.getElementById('s-permit').textContent  = s.permit.toLocaleString();
    document.getElementById('s-block-pct').textContent  = p(s.block)+'% del total';
    document.getElementById('s-limit-pct').textContent  = p(s.limit)+'% del total';
    document.getElementById('s-permit-pct').textContent = p(s.permit)+'% del total';
    document.getElementById('bar-block').style.width  = p(s.block)+'%';
    document.getElementById('bar-limit').style.width  = p(s.limit)+'%';
    document.getElementById('bar-permit').style.width = p(s.permit)+'%';
    document.getElementById('s-flows').textContent = s.flows_total.toLocaleString();
    document.getElementById('s-bf').textContent    = s.bf_total;
    document.getElementById('s-http').textContent  = s.http_total;
    document.getElementById('s-lat').textContent   = s.latencia.toFixed(1)+'ms';
    document.getElementById('s-lat2').textContent  = s.latencia.toFixed(1)+'ms';
    document.getElementById('s-fmin').textContent  = s.flujos_min;
    document.getElementById('uptime-chip').textContent = s.uptime;

    const rc = s.riesgo_color;
    document.getElementById('risk-num').textContent    = s.riesgo_val+'%';
    document.getElementById('risk-num').style.color    = rc;
    document.getElementById('risk-lbl').textContent    = s.riesgo_lbl;
    document.getElementById('risk-lbl').style.color    = rc;
    document.getElementById('risk-bar').style.width    = s.riesgo_val+'%';
    document.getElementById('risk-bar').style.background = rc;

    // control view ipset
    const ctrl=document.getElementById('view-control');
    if(ctrl.classList.contains('active')) refreshControl();

    // sistema view
    document.getElementById('sys-motor').textContent  = s.motor_inicio;
    document.getElementById('sys-uptime').textContent = s.uptime;
    document.getElementById('sys-sse').textContent    = s.sse_clients+' cliente(s)';

  }catch(e){}
}

// ═══════════════════════════════════════════════
// GRÁFICOS
// ═══════════════════════════════════════════════
const BASE={responsive:true,maintainAspectRatio:false,
  plugins:{legend:{labels:{color:'#8b949e',font:{size:10},boxWidth:12}}}};
const TIPO_COLORS=['rgba(248,81,73,.85)','rgba(240,136,62,.85)','rgba(227,179,65,.85)',
  'rgba(88,166,255,.85)','rgba(188,140,255,.85)','rgba(63,185,80,.85)','rgba(57,211,83,.7)'];

const chartLine = new Chart(document.getElementById('chartLine').getContext('2d'),{
  type:'bar',data:{labels:[],datasets:[
    {label:'BLOCK',data:[],backgroundColor:'rgba(248,81,73,.8)',stack:'s'},
    {label:'LIMIT',data:[],backgroundColor:'rgba(227,179,65,.7)',stack:'s'},
  ]},options:{...BASE,scales:{
    x:{ticks:{color:'#8b949e',font:{size:9},maxRotation:45},grid:{color:'#21262d'}},
    y:{ticks:{color:'#8b949e',font:{size:9}},grid:{color:'#21262d'},beginAtZero:true}
  },plugins:{...BASE.plugins,tooltip:{mode:'index',intersect:false}}}
});

const chartDona = new Chart(document.getElementById('chartDona').getContext('2d'),{
  type:'doughnut',data:{labels:[],datasets:[{data:[],borderColor:'#161b22',
    borderWidth:2,backgroundColor:TIPO_COLORS}]},
  options:{...BASE,cutout:'55%',plugins:{...BASE.plugins,
    legend:{position:'bottom',labels:{color:'#8b949e',font:{size:9},boxWidth:10}}}}
});

// Gráficos vista predictor
let chartPred = null, chartGap = null;

function initPredictorCharts(){
  if(chartPred) return;
  const threshOpts = (yMax)=>({
    annotation:{annotations:{
      l1:{type:'line',yMin:70,yMax:70,borderColor:'rgba(248,81,73,.5)',borderWidth:1,borderDash:[4,4]},
      l2:{type:'line',yMin:40,yMax:40,borderColor:'rgba(227,179,65,.5)',borderWidth:1,borderDash:[4,4]},
    }}
  });
  chartPred = new Chart(document.getElementById('chartPred').getContext('2d'),{
    type:'line',
    data:{labels:[],datasets:[{
      label:'P(ataque) %',
      data:[],
      borderColor:'rgba(227,179,65,.9)',
      backgroundColor:'rgba(227,179,65,.12)',
      pointBackgroundColor:'rgba(248,81,73,.9)',
      pointRadius:4,fill:true,tension:0.3,
    }]},
    options:{...BASE,
      scales:{
        x:{ticks:{color:'#8b949e',font:{size:9},maxRotation:45},grid:{color:'#21262d'}},
        y:{min:0,max:100,ticks:{color:'#8b949e',font:{size:9},callback:v=>v+'%'},grid:{color:'#21262d'}},
      },
      plugins:{...BASE.plugins,
        annotation:{annotations:{
          alta:{type:'line',yMin:70,yMax:70,borderColor:'rgba(248,81,73,.6)',borderWidth:1,borderDash:[5,3],
            label:{content:'ALERTA 70%',display:true,position:'end',color:'rgba(248,81,73,.8)',font:{size:9}}},
          media:{type:'line',yMin:40,yMax:40,borderColor:'rgba(227,179,65,.6)',borderWidth:1,borderDash:[5,3],
            label:{content:'RIESGO 40%',display:true,position:'end',color:'rgba(227,179,65,.8)',font:{size:9}}},
        }}
      }
    }
  });
  chartGap = new Chart(document.getElementById('chartGap').getContext('2d'),{
    type:'line',
    data:{labels:[],datasets:[{
      label:'Gap (seg)',
      data:[],
      borderColor:'rgba(88,166,255,.9)',
      backgroundColor:'rgba(88,166,255,.1)',
      pointRadius:4,fill:true,tension:0.3,
    }]},
    options:{...BASE,
      scales:{
        x:{ticks:{color:'#8b949e',font:{size:9},maxRotation:45},grid:{color:'#21262d'}},
        y:{min:0,ticks:{color:'#8b949e',font:{size:9},callback:v=>v+'s'},grid:{color:'#21262d'}},
      },
      plugins:{...BASE.plugins,
        annotation:{annotations:{
          ataque:{type:'line',yMin:60,yMax:60,borderColor:'rgba(248,81,73,.6)',borderWidth:1,borderDash:[5,3],
            label:{content:'60s umbral',display:true,position:'end',color:'rgba(248,81,73,.8)',font:{size:9}}},
          normal:{type:'line',yMin:174,yMax:174,borderColor:'rgba(63,185,80,.5)',borderWidth:1,borderDash:[5,3],
            label:{content:'174s normal',display:true,position:'end',color:'rgba(63,185,80,.7)',font:{size:9}}},
        }}
      }
    }
  });
}

async function loadPredictorData(){
  try{
    const [pr,gp]=await Promise.all([
      fetch('/api/predictor').then(r=>r.json()),
      fetch('/api/gaps').then(r=>r.json()),
    ]);
    // Poblar gauge con el último valor
    if(pr.p!==undefined) actualizarPredictor({p:pr.p,nivel:pr.nivel,ts:pr.ts});
    // Poblar chart P% con historial
    if(pr.historial && pr.historial.length && chartPred){
      chartPred.data.labels=pr.historial.map(h=>h.ts);
      chartPred.data.datasets[0].data=pr.historial.map(h=>Math.round(h.p*100));
      chartPred.update('none');
    }
    // Poblar chart gap con historial
    if(gp.length && chartGap){
      chartGap.data.labels=gp.map(g=>g.ts);
      chartGap.data.datasets[0].data=gp.map(g=>g.gap);
      chartGap.update('none');
    }
    // Feed predicciones
    const feed=document.getElementById('pred-feed');
    if(feed && pr.historial && pr.historial.length){
      feed.innerHTML='';
      [...pr.historial].reverse().forEach(h=>{
        const p=Math.round(h.p*100);
        const col=p>=70?"var(--red)":p>=40?"var(--yellow)":"var(--green)";
        const row=document.createElement('div');
        row.style.cssText=`color:${col};border-bottom:1px solid var(--border);padding:2px 0`;
        row.textContent=`${h.ts}  P=${p}%  ${h.nivel||''}`;
        feed.appendChild(row);
      });
    }
  }catch(e){}
}

// Gráficos vista análisis
let chartLine2,chartDona2;
function initAnalysisCharts(){
  if(chartLine2) return;
  chartLine2=new Chart(document.getElementById('chartLine2').getContext('2d'),{
    type:'bar',data:{labels:[],datasets:[
      {label:'BLOCK',data:[],backgroundColor:'rgba(248,81,73,.8)',stack:'s'},
      {label:'LIMIT',data:[],backgroundColor:'rgba(227,179,65,.7)',stack:'s'},
    ]},options:{...BASE,scales:{
      x:{ticks:{color:'#8b949e',font:{size:9},maxRotation:45},grid:{color:'#21262d'}},
      y:{ticks:{color:'#8b949e',font:{size:9}},grid:{color:'#21262d'},beginAtZero:true}
    },plugins:{...BASE.plugins,tooltip:{mode:'index',intersect:false}}}
  });
  chartDona2=new Chart(document.getElementById('chartDona2').getContext('2d'),{
    type:'doughnut',data:{labels:[],datasets:[{data:[],borderColor:'#161b22',
      borderWidth:2,backgroundColor:TIPO_COLORS}]},
    options:{...BASE,cutout:'55%',plugins:{...BASE.plugins,
      legend:{position:'bottom',labels:{color:'#8b949e',font:{size:9},boxWidth:10}}}}
  });
  // chartMetrics eliminado — datos eran hardcoded e incorrectos
  // se reemplazó por lista de top IPs en el panel de análisis
}

async function refreshCharts(){
  try{
    const [tl,tp]=await Promise.all([
      fetch('/api/timeline').then(r=>r.json()),
      fetch('/api/tipos').then(r=>r.json())
    ]);
    [chartLine,chartLine2].forEach(c=>{
      if(!c) return;
      c.data.labels=tl.labels;
      c.data.datasets[0].data=tl.block;
      c.data.datasets[1].data=tl.limit;
      c.update('none');
    });
    [chartDona,chartDona2].forEach(c=>{
      if(!c) return;
      c.data.labels=tp.labels.map(l=>l.replace(/_/g,' '));
      c.data.datasets[0].data=tp.data;
      c.update('none');
    });
    // Top IPs
    const topMap={};
    allEvents.forEach(e=>{topMap[e.src]=(topMap[e.src]||0)+1;});
    const topSorted=Object.entries(topMap).sort((a,b)=>b[1]-a[1]).slice(0,8);
    const tipEl=document.getElementById('top-ips-list');
    if(tipEl) tipEl.innerHTML=topSorted.length
      ? topSorted.map(([ip,cnt])=>`<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border)"><span class="mono cr">${ip}</span><span class="bdg bdg-BLOCK">${cnt} eventos</span></div>`).join('')
      : '<span class="cm">Sin datos aún</span>';
  }catch(e){}
}

function refreshCharts2(){
  initAnalysisCharts();
  refreshCharts();
}

// ═══════════════════════════════════════════════
// CARGA INICIAL DE ALERTAS (historial del log)
// ═══════════════════════════════════════════════
async function loadInitialAlerts(){
  try{
    const r=await fetch('/api/alerts');
    const data=await r.json();
    alertsData=data;
    allEvents=data; // seed de events también
    updateAlertCounters();
    if(data.length){
      document.getElementById('last-alert-txt').textContent=
        `${data[0].ts} | ${data[0].accion} | ${data[0].src} | ${(data[0].tipo||'').replace(/_/g,' ')}`;
    }
  }catch(e){}
}

async function loadInitialEvents(){
  try{
    const r=await fetch('/api/events?limit=200');
    const data=await r.json();
    allEvents=data;
    renderTbl();
  }catch(e){}
}

// ═══════════════════════════════════════════════
// RELOJ
// ═══════════════════════════════════════════════
function tick(){
  document.getElementById('clock').textContent=
    new Date().toLocaleString('es-PE',{hour12:false,
      year:'numeric',month:'2-digit',day:'2-digit',
      hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

// ═══════════════════════════════════════════════
// ARRANQUE
// ═══════════════════════════════════════════════
tick();
initSSE();
loadInitialAlerts();
loadInitialEvents();
fetchStats();
refreshCharts();

setInterval(tick,        1000);
setInterval(fetchStats,  4000);
setInterval(refreshCharts,12000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    Thread(target=log_reader,       daemon=True).start()
    Thread(target=predictor_reader, daemon=True).start()
    print(f"Dashboard → http://192.168.0.110:{PORT}")
    print(f"SSE en tiempo real activo | Log: {LOG_PATH}")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
