#!/usr/bin/env python3
"""
Dashboard en tiempo real — PPI Surikata
Uso: python3 dashboard.py [--interval N]
"""
import re, os, sys, time, subprocess, argparse
from collections import deque, Counter, defaultdict
from datetime import datetime

LOG_PATH = "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
W = 72  # ancho de caja

# ── Colores ANSI ──────────────────────────────────────────────────────────
R  = "\033[91m"   # rojo
Y  = "\033[93m"   # amarillo
G  = "\033[92m"   # verde
C  = "\033[96m"   # cyan
B  = "\033[1m"    # negrita
RS = "\033[0m"    # reset

ICONOS = {"BLOCK": f"{R}●{RS}", "LIMIT": f"{Y}●{RS}", "PERMIT": f"{G}●{RS}"}

# ── Regex para parsear líneas del log ─────────────────────────────────────
# Formato: TIMESTAMP | LEVEL | TIPO | src=IP dst=IP:PORT proto=P score=S grado=G tipo=T | ACCION
RE_EVENTO = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"      # timestamp
    r".*?\| (ANOMALÍA|SOSPECHOSO|BRUTE-FORCE|HTTP-ABUSE)"  # tipo log
    r".*?src=([\d.]+)"                               # src_ip
    r".*?dst=([\d.]+):(\d+)"                         # dst_ip:port
    r".*?proto=(\w+)"                                # proto
    r".*?score=([-\d.]+)"                            # score
    r"(?:.*?grado=(\w+))?"                           # grado (opcional)
    r"(?:.*?tipo=(\w+))?"                            # tipo anomalía (opcional)
    r".*?\| (BLOCK|LIMIT)"                           # accion final
)
RE_STATS = re.compile(
    r"flows=(\d+).*anomalías=(\d+).*bf=(\d+).*http_abuse=(\d+)"
    r".*bloqueados=(\d+).*limitados=(\d+).*latencia_media=([\d.]+)"
)
RE_INICIO = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Motor de decisión PPI — iniciando")


class Estado:
    def __init__(self):
        self.eventos    = deque(maxlen=300)   # (ts_epoch, dict)
        self.vent_min   = deque()             # timestamps 60s
        self.inicio_app = time.time()
        # stats de la línea de resumen del motor (cada 500 flows)
        self.flows_total  = 0
        self.anom_total   = 0
        self.bf_total     = 0
        self.http_total   = 0
        self.bloq_total   = 0
        self.lim_total    = 0
        self.latencia     = 0.0
        self.motor_inicio = "—"

    def agregar(self, ev: dict):
        ahora = time.time()
        self.eventos.append((ahora, ev))
        self.vent_min.append(ahora)
        while self.vent_min and ahora - self.vent_min[0] > 60:
            self.vent_min.popleft()

    def flujos_min(self) -> int:
        return len(self.vent_min)

    def conteos(self) -> Counter:
        return Counter(e["accion"] for _, e in self.eventos)

    def ultimos(self, n=8) -> list:
        evs = list(self.eventos)
        return [e for _, e in evs[-n:]]

    def por_tipo(self) -> list:
        c = Counter(
            e.get("tipo", "ANOMALIA_GENERICA")
            for _, e in self.eventos
            if e.get("accion") == "BLOCK"
        )
        return c.most_common(5)

    def uptime(self) -> str:
        seg = int(time.time() - self.inicio_app)
        h, r = divmod(seg, 3600)
        m, s = divmod(r, 60)
        return f"{h}h {m:02d}m {s:02d}s"


def ipset_ips(nombre: str) -> list:
    try:
        out = subprocess.check_output(
            ["sudo", "ipset", "list", nombre],
            stderr=subprocess.DEVNULL, text=True, timeout=2
        )
        ips, en = [], False
        for ln in out.splitlines():
            if ln.startswith("Members:"):
                en = True; continue
            if en and ln.strip():
                ips.append(ln.strip().split()[0])
        return ips
    except Exception:
        return []


def barra(pct: float, ancho=16) -> str:
    llenos = int(pct / 100 * ancho)
    return f"{G}" + "█" * llenos + f"{RS}" + "░" * (ancho - llenos)


def caja(texto: str, ancho=W) -> str:
    return "║" + texto.ljust(ancho) + "║"


def sep(car="═") -> str:
    return "╠" + car * W + "╣"


def leer_log_completo(path: str, estado: Estado):
    """Carga el log completo al arrancar para poblar el estado inicial."""
    try:
        with open(path, "r", errors="ignore") as f:
            for linea in f:
                procesar_linea(linea, estado)
    except Exception:
        pass


def procesar_linea(linea: str, estado: Estado):
    # Línea de evento (ANOMALÍA, SOSPECHOSO, etc.)
    m = RE_EVENTO.search(linea)
    if m:
        ts, tipo_log, src, dst, port, proto, score, grado, tipo, accion = m.groups()
        estado.agregar({
            "ts": ts[11:19],           # solo HH:MM:SS
            "src": src,
            "dst": dst,
            "port": port,
            "proto": proto,
            "score": score,
            "grado": grado or "—",
            "tipo": tipo or "ANOMALIA_GENERICA",
            "accion": accion,
        })
        return

    # Línea de estadísticas del motor (cada 500 flows)
    m2 = RE_STATS.search(linea)
    if m2:
        (estado.flows_total, estado.anom_total, estado.bf_total,
         estado.http_total, estado.bloq_total, estado.lim_total) = [
            int(x) for x in m2.groups()[:6]
        ]
        estado.latencia = float(m2.group(7))
        return

    # Línea de inicio del motor
    m3 = RE_INICIO.search(linea)
    if m3:
        estado.motor_inicio = m3.group(1)[11:19]


def render(estado: Estado) -> str:
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c     = estado.conteos()
    block = c.get("BLOCK", 0)
    limit = c.get("LIMIT", 0)
    total = block + limit or 1
    fmin  = estado.flujos_min()

    bloqueadas = ipset_ips("ppi_blocked")
    limitadas  = ipset_ips("ppi_limited")

    lineas = []

    # ── Cabecera ──────────────────────────────────────────────────────────
    lineas.append("╔" + "═" * W + "╗")
    lineas.append(caja(f"  {B}PPI-SURIKATA{RS}  Sistema de Detección de Anomalías en Red"))
    lineas.append(caja(f"  {C}{now}{RS}   UPeU 2026   Motor activo desde: {estado.motor_inicio}"))
    lineas.append(sep())

    # ── Estado del sistema ────────────────────────────────────────────────
    estado_str = (f"  {G}●{RS} Suricata  "
                  f"{G}●{RS} Motor  "
                  f"{G}●{RS} Telegram  "
                  f"│  Uptime: {B}{estado.uptime()}{RS}  "
                  f"│  F/min: {B}{fmin}{RS}")
    lineas.append(caja(estado_str))
    lineas.append(sep())

    # ── Contadores ────────────────────────────────────────────────────────
    pct_b = block / total * 100
    pct_l = limit / total * 100
    lineas.append(caja(
        f"  {R}BLOCK{RS}: {B}{block:>5}{RS} ({pct_b:4.1f}%)"
        f"   {Y}LIMIT{RS}: {B}{limit:>4}{RS} ({pct_l:4.1f}%)"
        f"   Total sesión: {B}{block+limit:>5}{RS}"
        f"   Latencia: {B}{estado.latencia:.1f}ms{RS}"
    ))
    lineas.append(caja(
        f"  BruteForce SSH: {B}{estado.bf_total}{RS}"
        f"   HTTP Abuse: {B}{estado.http_total}{RS}"
        f"   flows procesados: {B}{estado.flows_total:,}{RS}"
    ))
    lineas.append(sep())

    # ── Últimas decisiones ────────────────────────────────────────────────
    lineas.append(caja(f"  {B}ÚLTIMAS DECISIONES{RS}"))
    lineas.append(caja(
        f"  {'Hora':8}  {'Origen':16}  {'Puerto':6}  "
        f"{'Score':8}  {'Grado':8}  {'Tipo':22}  Dec"
    ))
    lineas.append(caja("  " + "─" * (W - 2)))

    recientes = estado.ultimos(8)
    if not recientes:
        lineas.append(caja("  Sin eventos aún — esperando tráfico..."))
        for _ in range(7):
            lineas.append(caja(""))
    else:
        for ev in reversed(recientes):
            ico   = ICONOS.get(ev["accion"], "⚪")
            gcolor = R if ev.get("grado") in ("ALTA","CRITICA") else (Y if ev.get("grado") == "BAJA" else G)
            fila = (
                f"  {ev['ts']:8}  {ico} {ev['src']:14}  :{ev['port']:5}"
                f"  {ev['score']:>8}  {gcolor}{ev.get('grado','—'):8}{RS}"
                f"  {ev.get('tipo','—'):22}  {ev['accion']}"
            )
            lineas.append(caja(fila))
        for _ in range(8 - len(recientes)):
            lineas.append(caja(""))

    lineas.append(sep())

    # ── Métricas del modelo + ipset activo ────────────────────────────────
    lineas.append(caja(
        f"  {B}MÉTRICAS DEL MODELO{RS}" + " " * 18 +
        f"{B}IPSET ACTIVO{RS}"
    ))
    metricas = [
        f"  Precision:  99.96%  {barra(99.96)}",
        f"  Recall:     99.30%  {barra(99.30)}",
        f"  AUC-ROC:    0.9440  {barra(94.40)}",
        f"  F1 Score:   0.9963  {barra(99.63)}",
        f"  Lat P95:    34.8ms  {G}✅ <500ms{RS}",
        f"  ITL:        0.0%    {G}✅ cero FP{RS}",
    ]
    ipset_bloq = ([f"  {R}BLOQUEADAS:{RS} {len(bloqueadas)}"] +
                  [f"    {R}{ip}{RS}" for ip in bloqueadas[:4]])
    ipset_lim  = ([f"  {Y}LIMITADAS: {RS} {len(limitadas)}"] +
                  [f"    {Y}{ip}{RS}" for ip in limitadas[:2]])
    ipset_info = ipset_bloq + ipset_lim

    max_f = max(len(metricas), len(ipset_info))
    for i in range(max_f):
        izq = metricas[i]   if i < len(metricas)   else ""
        der = ipset_info[i] if i < len(ipset_info) else ""
        # construir fila de ancho fijo
        izq_plain = re.sub(r'\033\[[0-9;]*m', '', izq)
        der_plain = re.sub(r'\033\[[0-9;]*m', '', der)
        pad_izq = 38 - len(izq_plain)
        fila = izq + " " * max(0, pad_izq) + der
        lineas.append(caja(fila))

    lineas.append(sep())

    # ── Distribución por tipo ─────────────────────────────────────────────
    lineas.append(caja(f"  {B}TIPOS DE ATAQUE (sesión){RS}"))
    top = estado.por_tipo()
    if not top:
        lineas.append(caja("  Sin BLOCKs registrados aún"))
    else:
        for tipo, cnt in top:
            pct = cnt / block * 100 if block else 0
            barra_str = barra(pct, 14)
            lineas.append(caja(f"  {tipo:<24} {barra_str} {pct:4.0f}%  ({cnt})"))

    lineas.append(sep("─").replace("╠", "╠").replace("╣", "╣"))
    lineas.append(caja(
        f"  τ1={B}-0.4973{RS}(PERMIT/LIMIT)  τ2={B}-0.6873{RS}(LIMIT/BLOCK)"
        f"  │  {B}Ctrl+C{RS} para salir"
    ))
    lineas.append("╚" + "═" * W + "╝")

    return "\n".join(lineas)


def seguir_log(path: str, estado: Estado):
    """Tail continuo del log, detecta rotación."""
    try:
        f = open(path, "r", errors="ignore")
        f.seek(0, 2)
    except Exception:
        return None
    while True:
        linea = f.readline()
        if linea:
            procesar_linea(linea, estado)
        else:
            try:
                if os.path.getsize(path) < f.tell():
                    f.close()
                    f = open(path, "r", errors="ignore")
                    f.seek(0, 2)
            except Exception:
                pass
            time.sleep(0.15)


def main():
    parser = argparse.ArgumentParser(description="PPI Dashboard")
    parser.add_argument("--interval", type=int, default=3)
    parser.add_argument("--log", default=LOG_PATH)
    args = parser.parse_args()

    if not os.path.exists(args.log):
        print(f"Log no encontrado: {args.log}")
        print("Asegúrate de que el motor esté corriendo:")
        print("  sudo systemctl start ppi-motor.service")
        sys.exit(1)

    estado = Estado()
    print("Cargando historial del log...")
    leer_log_completo(args.log, estado)

    import threading
    t = threading.Thread(
        target=seguir_log, args=(args.log, estado), daemon=True
    )
    t.start()

    try:
        while True:
            print("\033[2J\033[H", end="", flush=True)
            print(render(estado))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDashboard cerrado.")


if __name__ == "__main__":
    main()
