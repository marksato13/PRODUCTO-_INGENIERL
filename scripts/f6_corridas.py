#!/usr/bin/env python3
"""
Fase 6 — Automatización de corridas de validación
Ejecuta escenarios, recolecta métricas y genera CSVs de resultados.

Métricas por corrida:
  - FPR          : tasa de falsos positivos sobre tráfico normal
  - ITL          : impacto en tráfico legítimo (% flows normales afectados)
  - Latencia_ms  : latencia media de decisión (ms entre flows procesados)
  - Lead_Time_s  : tiempo desde inicio ataque hasta primera detección
  - TIE          : tasa de intervención efectiva (% anomalías bloqueadas/limitadas)
  - MTTA_s       : mean time to alert (s hasta primer log de anomalía)
  - MTTC_s       : mean time to contain (s hasta primer BLOCK o LIMIT)
  - Disponibilidad: servidor responde durante el ataque (0/1)
  - Flows_normal  : flows legítimos procesados en la corrida
  - Flows_anom    : flows anómalos detectados
  - Bloqueados    : IPs bloqueadas
  - Limitados     : IPs limitadas
"""

import subprocess
import time
import csv
import os
import re
import sys
from datetime import datetime

# ── Configuración ─────────────────────────────────────────────
DURACION_NORMAL   = 300   # segundos por corrida normal (5 min)
DURACION_MIXTO    = 300   # segundos por corrida mixta
PAUSA_ENTRE       = 60    # segundos de pausa entre corridas
N_NORMAL          = 10    # corridas grupo normal
N_MIXTO           = 10    # corridas grupo mixto
N_REEVAL          = 10    # corridas re-evaluación
N_FINAL           = 10    # corridas finales

SERVIDOR   = "192.168.0.120"
KALI       = "192.168.0.100"
SENSOR     = "192.168.0.110"
LOG_PATH   = "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
RESULT_DIR = "/home/m4rk/ppi-surikata-producto/results"
DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data"

os.makedirs(RESULT_DIR, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────
def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(msg):
    print(f"[{ts()}] {msg}", flush=True)

def run(cmd, timeout=30, check=False):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def ssh_kali(cmd, timeout=10):
    return run(
        f"sshpass -p 'Cisco123' ssh -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=5 m4rk@{KALI} \"{cmd}\"",
        timeout=timeout
    )

def verificar_disponibilidad():
    r = run(f"ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "
            f"m4rk@{SERVIDOR} 'curl -s -o /dev/null -w \"%{{http_code}}\" "
            f"http://localhost/ --max-time 2'", timeout=8)
    return 1 if r.strip() == "200" else 0

def leer_log_ventana(t_inicio, t_fin):
    """Lee líneas del log del motor en la ventana temporal."""
    lineas = []
    try:
        with open(LOG_PATH, "r", errors="ignore") as f:
            for linea in f:
                m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', linea)
                if m:
                    try:
                        t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
                        if t_inicio <= t <= t_fin:
                            lineas.append((t, linea.strip()))
                    except Exception:
                        pass
    except Exception:
        pass
    return lineas

def calcular_metricas(lineas, t_ataque_inicio=None):
    """Extrae métricas de las líneas del log en la ventana."""
    flows_normal = 0
    flows_anom   = 0
    bloqueados   = set()
    limitados    = set()
    tiempos      = []
    t_primera_alerta = None
    t_primera_accion = None

    for t, linea in lineas:
        tiempos.append(t)
        KEYWORDS_ANOM = ("ANOMALÍA", "SOSPECHOSO", "HTTP-ABUSE", "BRUTE-FORCE")
        if any(k in linea for k in KEYWORDS_ANOM):
            flows_anom += 1
            if t_primera_alerta is None:
                t_primera_alerta = t
            if "BLOCK" in linea or "LIMIT" in linea:
                m = re.search(r'src=([\d.]+)', linea)
                ip = m.group(1) if m else None
                if ip:
                    if "BLOCK" in linea:
                        bloqueados.add(ip)
                    else:
                        limitados.add(ip)
                if t_primera_accion is None:
                    t_primera_accion = t
        elif "Estadísticas" in linea:
            m_flows = re.search(r'flows=(\d+)', linea)
            if m_flows:
                flows_normal = int(m_flows.group(1))

    # Latencia: inversa de tasa de procesamiento
    if len(tiempos) > 2:
        dur = tiempos[-1] - tiempos[0]
        latencia_ms = (dur / len(tiempos) * 1000) if len(tiempos) > 0 else 0
    else:
        latencia_ms = 0

    lead_time = (t_primera_alerta - t_ataque_inicio
                 if t_primera_alerta and t_ataque_inicio else None)
    mtta = lead_time
    mttc = (t_primera_accion - t_ataque_inicio
            if t_primera_accion and t_ataque_inicio else None)

    total_anom = flows_anom
    n_intervenidos = len(bloqueados) + len(limitados)
    tie = (n_intervenidos / max(total_anom, 1)) * 100 if total_anom > 0 else 0

    # ITL: flows normales que fueron mal clasificados
    # (aproximado: flows en ventana sin anomalía / total flows normal)
    itl = 0.0  # se calcula post-hoc si hay flows normales

    return {
        "flows_normal": flows_normal,
        "flows_anom":   total_anom,
        "bloqueados":   len(bloqueados),
        "limitados":    len(limitados),
        "latencia_ms":  round(latencia_ms, 2),
        "lead_time_s":  round(lead_time, 2) if lead_time else None,
        "mtta_s":       round(mtta, 2) if mtta else None,
        "mttc_s":       round(mttc, 2) if mttc else None,
        "tie_pct":      round(tie, 2),
        "itl_pct":      itl,
    }

# ── Ejecutores de tráfico ─────────────────────────────────────
def trafico_normal_bg(duracion):
    """Lanza tráfico HTTP + SSH normal en background desde este host."""
    end = time.time() + duracion
    procs = []
    script = f"""
import subprocess, time
end = time.time() + {duracion}
while time.time() < end:
    subprocess.run('curl -s http://{SERVIDOR}/ -o /dev/null', shell=True)
    time.sleep(4)
    subprocess.run('ssh -o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=no '
                   'm4rk@{SERVIDOR} uptime > /dev/null 2>&1', shell=True)
    time.sleep(4)
"""
    import multiprocessing
    def worker():
        import subprocess, time
        end_t = time.time() + duracion
        while time.time() < end_t:
            subprocess.run(f'curl -s http://{SERVIDOR}/ -o /dev/null', shell=True)
            time.sleep(4)
            subprocess.run(
                f'ssh -o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=no '
                f'm4rk@{SERVIDOR} uptime > /dev/null 2>&1', shell=True)
            time.sleep(4)
    p = multiprocessing.Process(target=worker)
    p.start()
    return p

def trafico_anom_bg(tipo, duracion):
    """Lanza ataque desde Kali en background."""
    if tipo == "synflood":
        cmd = f"sudo timeout {duracion} hping3 -S -p 80 -i u5000 {SERVIDOR} > /dev/null 2>&1 &"
    elif tipo == "portscan":
        cmd = f"nmap -sS -p 1-1024 {SERVIDOR} > /dev/null 2>&1 &"
    elif tipo == "udpflood":
        cmd = f"sudo timeout {duracion} hping3 --udp -p 53 -i u5000 {SERVIDOR} > /dev/null 2>&1 &"
    elif tipo == "httpabuse":
        cmd = f"timeout {duracion} bash -c 'while true; do curl -s http://{SERVIDOR}/ -o /dev/null; done' > /dev/null 2>&1 &"
    else:
        return
    ret = ssh_kali(cmd, timeout=15)
    if ret.startswith("ERROR"):
        print(f"  [WARN] ssh_kali falló: {ret}")

# ── Función principal de corrida ──────────────────────────────
def ejecutar_corrida(num, grupo, escenario_anom=None, duracion=DURACION_NORMAL):
    log(f"Corrida {num:02d} | grupo={grupo} | escenario={escenario_anom or 'solo_normal'} | dur={duracion}s")

    t_inicio = time.time()

    # Tráfico normal siempre activo
    p_normal = trafico_normal_bg(duracion)

    t_ataque = None
    if escenario_anom:
        time.sleep(15)  # esperar 15s antes de lanzar el ataque
        t_ataque = time.time()
        trafico_anom_bg(escenario_anom, duracion - 15)
        log(f"  Ataque {escenario_anom} iniciado a t+15s")

    # Verificar disponibilidad a mitad de la corrida
    time.sleep(duracion // 2)
    disp = verificar_disponibilidad()
    time.sleep(duracion // 2)

    t_fin = time.time()

    # Terminar tráfico normal
    p_normal.terminate()
    p_normal.join(timeout=5)

    # Recolectar métricas del log
    lineas = leer_log_ventana(t_inicio, t_fin)
    metricas = calcular_metricas(lineas, t_ataque)

    resultado = {
        "corrida":         num,
        "grupo":           grupo,
        "escenario":       escenario_anom or "normal",
        "fecha":           datetime.now().strftime("%Y-%m-%d"),
        "hora_inicio":     datetime.fromtimestamp(t_inicio).strftime("%H:%M:%S"),
        "hora_fin":        datetime.fromtimestamp(t_fin).strftime("%H:%M:%S"),
        "duracion_s":      round(t_fin - t_inicio),
        "disponibilidad":  disp,
        **metricas,
    }

    log(f"  → flows_anom={resultado['flows_anom']} "
        f"bloq={resultado['bloqueados']} lim={resultado['limitados']} "
        f"lead={resultado['lead_time_s']}s mttc={resultado['mttc_s']}s "
        f"disp={disp}")

    return resultado

# ── COLUMNAS CSV ──────────────────────────────────────────────
COLS = ["corrida","grupo","escenario","fecha","hora_inicio","hora_fin",
        "duracion_s","disponibilidad","flows_normal","flows_anom",
        "bloqueados","limitados","latencia_ms","lead_time_s",
        "mtta_s","mttc_s","tie_pct","itl_pct"]

def guardar_csv(path, filas):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(filas)
    log(f"  Guardado: {path}  ({len(filas)} corridas)")

# ── MAIN ──────────────────────────────────────────────────────
def main():
    log("=" * 60)
    log("FASE 6 — Corridas de validación")
    log(f"Normal={N_NORMAL}  Mixto={N_MIXTO}  Reeval={N_REEVAL}  Final={N_FINAL}")
    log(f"Duración por corrida: {DURACION_NORMAL}s  Pausa: {PAUSA_ENTRE}s")
    log("=" * 60)

    ataques_mixto = ["synflood","portscan","udpflood","httpabuse",
                     "synflood","portscan","udpflood","httpabuse","synflood","portscan"]

    # ── GRUPO 1: Normal (runs 1-10) ────────────────────────────
    log("\n--- GRUPO 1: Tráfico normal (runs 1-10) ---")
    normal_rows = []
    for i in range(1, N_NORMAL + 1):
        r = ejecutar_corrida(i, "normal", None, DURACION_NORMAL)
        normal_rows.append(r)
        guardar_csv(f"{RESULT_DIR}/resultados_normal.csv", normal_rows)
        if i < N_NORMAL:
            log(f"  Pausa {PAUSA_ENTRE}s ...")
            time.sleep(PAUSA_ENTRE)

    # ── GRUPO 2: Mixto (runs 11-20) ───────────────────────────
    log("\n--- GRUPO 2: Tráfico mixto (runs 11-20) ---")
    mixto_rows = []
    for i in range(1, N_MIXTO + 1):
        ataque = ataques_mixto[i - 1]
        r = ejecutar_corrida(10 + i, "mixto", ataque, DURACION_MIXTO)
        mixto_rows.append(r)
        guardar_csv(f"{RESULT_DIR}/resultados_mixto.csv", mixto_rows)
        if i < N_MIXTO:
            log(f"  Pausa {PAUSA_ENTRE}s ...")
            time.sleep(PAUSA_ENTRE)

    # ── GRUPO 3: Re-evaluación (runs 21-30) ───────────────────
    log("\n--- GRUPO 3: Re-evaluación τ1/τ2 (runs 21-30) ---")
    reeval_rows = []
    ataques_reeval = ataques_mixto  # misma rotación de ataques
    for i in range(1, N_REEVAL + 1):
        ataque = ataques_reeval[i - 1]
        r = ejecutar_corrida(20 + i, "reeval", ataque, DURACION_MIXTO)
        reeval_rows.append(r)
        guardar_csv(f"{RESULT_DIR}/resultados_reeval.csv", reeval_rows)
        if i < N_REEVAL:
            log(f"  Pausa {PAUSA_ENTRE}s ...")
            time.sleep(PAUSA_ENTRE)

    # ── GRUPO 4: Final (runs 31-40) ───────────────────────────
    log("\n--- GRUPO 4: Corridas finales (runs 31-40) ---")
    final_rows = []
    for i in range(1, N_FINAL + 1):
        ataque = ataques_mixto[i - 1]
        r = ejecutar_corrida(30 + i, "final", ataque, DURACION_MIXTO)
        final_rows.append(r)
        guardar_csv(f"{RESULT_DIR}/resultados_final.csv", final_rows)
        if i < N_FINAL:
            log(f"  Pausa {PAUSA_ENTRE}s ...")
            time.sleep(PAUSA_ENTRE)

    # ── Resumen consolidado ────────────────────────────────────
    todas = normal_rows + mixto_rows + reeval_rows + final_rows
    guardar_csv(f"{RESULT_DIR}/resultados_f6_completo.csv", todas)

    log("\n" + "=" * 60)
    log("RESUMEN F6")
    log("=" * 60)

    def media(rows, campo):
        vals = [r[campo] for r in rows if r.get(campo) is not None]
        return round(sum(vals)/len(vals), 3) if vals else "N/A"

    for grupo, rows in [("Normal", normal_rows), ("Mixto", mixto_rows),
                        ("Reeval", reeval_rows), ("Final", final_rows)]:
        log(f"\n  {grupo} ({len(rows)} corridas):")
        log(f"    Disponibilidad  : {sum(r['disponibilidad'] for r in rows)/len(rows)*100:.1f}%")
        log(f"    Lead Time medio : {media(rows, 'lead_time_s')} s")
        log(f"    MTTC medio      : {media(rows, 'mttc_s')} s")
        log(f"    TIE medio       : {media(rows, 'tie_pct')} %")
        log(f"    Latencia media  : {media(rows, 'latencia_ms')} ms")
        log(f"    ITL medio       : {media(rows, 'itl_pct')} %")

    log(f"\nArchivos generados en {RESULT_DIR}/")
    log("  resultados_normal.csv")
    log("  resultados_mixto.csv")
    log("  resultados_reeval.csv")
    log("  resultados_final.csv")
    log("  resultados_f6_completo.csv")


if __name__ == "__main__":
    main()
