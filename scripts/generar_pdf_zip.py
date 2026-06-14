#!/usr/bin/env python3
"""
Fase 6 — Genera reporte_validacion_final.pdf y MVP_funcional.zip
"""
import os, csv, glob, zipfile, shutil
from datetime import datetime
from fpdf import FPDF

BASE   = "/home/m4rk/ppi-surikata-producto"
RESULT = f"{BASE}/results"
DATA   = f"{BASE}/data"
DOCS   = f"{BASE}/docs"

# ── Leer CSVs de corridas ─────────────────────────────────────
def leer_csv(path):
    if not os.path.exists(path): return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

normal_rows = leer_csv(f"{RESULT}/resultados_normal.csv")
mixto_rows  = leer_csv(f"{RESULT}/resultados_mixto.csv")
reeval_rows = leer_csv(f"{RESULT}/resultados_reeval.csv")
final_rows  = leer_csv(f"{RESULT}/resultados_final.csv")

def med(rows, k):
    v = []
    for r in rows:
        val = r.get(k, "")
        try:
            fv = float(val)
            if fv > 0: v.append(fv)
        except: pass
    return round(sum(v)/len(v), 2) if v else "N/A"

def pct_disp(rows):
    if not rows: return "N/A"
    return f"{sum(int(r.get('disponibilidad',1)) for r in rows)/len(rows)*100:.1f}%"

def pct_itl(rows):
    if not rows: return "N/A"
    v = [float(r.get('itl_pct',0)) for r in rows]
    return f"{sum(v)/len(v):.1f}%"

def pct_tie(rows):
    if not rows: return "N/A"
    v = []
    for r in rows:
        try: v.append(float(r.get('tie_pct',0)))
        except: pass
    return f"{sum(v)/len(v):.1f}%" if v else "N/A"

# ── PDF ───────────────────────────────────────────────────────
class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(30, 80, 140)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "PPI - Sistema de Deteccion Temprana de Anomalias de Red", fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Universidad Peruana Union 2026  |  Pagina {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def titulo(self, texto):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(220, 230, 245)
        self.cell(0, 8, texto, fill=True, ln=True)
        self.ln(2)

    def subtitulo(self, texto):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 7, texto, fill=True, ln=True)
        self.ln(1)

    def parrafo(self, texto):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, texto)
        self.ln(1)

    def tabla(self, headers, rows, col_w=None):
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(50, 100, 160)
        self.set_text_color(255, 255, 255)
        if not col_w:
            col_w = [190 // len(headers)] * len(headers)
        for h, w in zip(headers, col_w):
            self.cell(w, 7, h, border=1, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 8)
        for i, row in enumerate(rows):
            self.set_fill_color(245, 245, 245) if i % 2 == 0 else self.set_fill_color(255, 255, 255)
            for val, w in zip(row, col_w):
                self.cell(w, 6, str(val), border=1, fill=True)
            self.ln()
        self.ln(2)

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=13)
pdf.add_page()
pdf.set_font("Helvetica", "B", 16)
pdf.set_text_color(30, 80, 140)
pdf.cell(0, 12, "REPORTE DE VALIDACION FINAL", ln=True, align="C")
pdf.set_font("Helvetica", "B", 13)
pdf.cell(0, 8, "Sistema de Deteccion Temprana de Anomalias de Red", ln=True, align="C")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 6, "Universidad Peruana Union  |  PPI 2026", ln=True, align="C")
pdf.cell(0, 6, "Estudiante: Ruben Mark Salazar Tocas", ln=True, align="C")
pdf.cell(0, 6, "Asesores: Ing. Nemias Saboya Rios  |  Ing. Fernando Manuel Asin Gomez", ln=True, align="C")
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 6, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
pdf.ln(6)

# 1. Descripcion
pdf.titulo("1. DESCRIPCION DEL SISTEMA")
pdf.parrafo(
    "Sistema de deteccion temprana de comportamientos anomalos en redes de datos "
    "implementado en un entorno de laboratorio controlado. Utiliza Isolation Forest "
    "para clasificacion no supervisada de flujos de red capturados por Suricata 7.0.3, "
    "con control inline mediante ipset/iptables con triple accion: PERMIT, LIMIT y BLOCK."
)

pdf.subtitulo("Topologia del laboratorio")
pdf.tabla(
    ["VM", "IP", "Rol"],
    [["Ubuntu Desktop", "192.168.0.20", "Cliente / origen trafico normal"],
     ["Kali Linux",     "192.168.0.100","Origen trafico anomalo controlado"],
     ["Ubuntu Suricata","192.168.0.110","Sensor (Suricata 7.0.3, ens35)"],
     ["Ubuntu Server",  "192.168.0.120","Objetivo (nginx:80, SSH:22)"]],
    [48, 38, 104]
)

# 2. Modelo
pdf.titulo("2. CONFIGURACION DEL MODELO")
pdf.tabla(
    ["Parametro", "Valor", "Descripcion"],
    [["Algoritmo",    "Isolation Forest", "Deteccion de anomalias no supervisada"],
     ["n_estimators", "300",              "Arboles en el ensemble"],
     ["contamination","0.05",             "Fraccion esperada de ruido en datos normales"],
     ["Features",     "14",               "pkts, bytes, duracion, tasas, protocolo, puerto"],
     ["Umbral base",  "-0.5481",          "clf.offset_ (contamination=0.05)"],
     ["tau1 (LIMIT)", "-0.4973",          "Umbral PERMIT/LIMIT  (Youden, TPR=91%)"],
     ["tau2 (BLOCK)", "-0.6873",          "Umbral LIMIT/BLOCK   (FPR<=2%, TPR=40.6%)"],
     ["AUC-ROC",      "0.9440",           "Capacidad discriminativa del modelo"]],
    [38, 30, 122]
)

# 3. Metricas globales
pdf.titulo("3. METRICAS GLOBALES DEL MODELO")
pdf.tabla(
    ["Metrica", "Valor", "Interpretacion"],
    [["Precision",        "99.96%", "Casi sin falsas alarmas al declarar anomalia"],
     ["Recall",           "80.4%",  "80.4% de ataques detectados"],
     ["F1-Score",         "0.8912", "Balance precision-recall"],
     ["Tasa FP (normal)", "5.1%",   "Porcentaje de trafico normal mal clasificado"],
     ["FP SSH",           "0%",     "SSH legitimo: cero falsas alarmas"],
     ["FP Transferencia", "0%",     "Transferencia de archivos: cero falsas alarmas"],
     ["AUC-ROC",          "0.9440", "94.4% probabilidad discriminacion correcta"]],
    [50, 30, 110]
)

# 4. Deteccion por escenario
pdf.titulo("4. DETECCION POR ESCENARIO")
pdf.tabla(
    ["Escenario", "Grupo", "Flows", "Resultado", "Score medio"],
    [["HTTP Normal (A1)",       "Normal",  "345",   "FP=4.6%  OK", "-0.4277"],
     ["SSH Legitimo (A2)",      "Normal",  "58",    "FP=0%    OK", "-0.4102"],
     ["Transferencia (A3)",     "Normal",  "29",    "FP=0%    OK", "-0.4484"],
     ["Trafico Sostenido (A4)", "Normal",  "252",   "FP=7.5%  ~",  "-0.4252"],
     ["SYN Flood (B1)",         "Anomalo", "50000", "Det=87.9% OK","-0.6383"],
     ["Port Scan (B2)",         "Anomalo", "3258",  "Det=99.9% OK","-0.6508"],
     ["UDP Flood (B3)",         "Anomalo", "18168", "Det=100%  OK","-0.7142"],
     ["ICMP Flood (B4)",        "Anomalo", "23460", "Det=100%  OK","-0.6982"],
     ["HTTP Abuse (B5)",        "Anomalo", "22595", "Det=30.7% ~", "-0.5133"],
     ["Brute Force (B6)",       "Anomalo", "2061",  "Det=0.9%  X", "-0.4376"]],
    [52, 22, 22, 32, 30]
)

# 5. F6 Corridas
pdf.titulo("5. RESULTADOS FASE 6 - 40 CORRIDAS")
pdf.tabla(
    ["Grupo", "Corridas", "Disponibilidad", "TIE", "ITL", "Latencia"],
    [["Normal (1-10)",   "10", pct_disp(normal_rows), "N/A",           pct_itl(normal_rows), "6.6 ms"],
     ["Mixto (11-20)",   "10", pct_disp(mixto_rows),  pct_tie(mixto_rows),  "0%", "6.6 ms*"],
     ["Reeval (21-30)",  "10", pct_disp(reeval_rows), pct_tie(reeval_rows), "0%", "6.6 ms*"],
     ["Final (31-40)",   "10", pct_disp(final_rows),  pct_tie(final_rows),  "0%", "6.6 ms*"]],
    [38, 22, 35, 28, 24, 43]
)
pdf.parrafo("* Latencia del motor de decision medida en sesion de validacion en vivo (A2+B2, 2026-06-02 19:41).")
pdf.parrafo("Lead Time real: ~26s (tiempo desde inicio ataque hasta primera deteccion, medido en sesion B2).")
pdf.parrafo("MTTC real: ~28s (tiempo hasta primera accion BLOCK/LIMIT aplicada).")

# 6. Validacion en vivo
pdf.titulo("6. VALIDACION EN VIVO")
pdf.subtitulo("Escenario: A2 SSH legitimo + B2 Port scan simultaneos (2026-06-02 19:41-19:50)")
pdf.tabla(
    ["Prueba", "Resultado"],
    [["SSH legitimo (192.168.0.20)",     "0 falsas alarmas  OK"],
     ["Port scan Kali (192.168.0.100)",  "1705/1705 flows detectados  OK"],
     ["Bloqueo automatico",              "1er flow -> BLOCK inmediato  OK"],
     ["Score SSH normal",                "-0.434 (sobre umbral tau1)"],
     ["Score port scan",                 "-0.655 (bajo umbral tau2)"],
     ["Separacion de scores",            "0.221 unidades"],
     ["Accion LIMIT validada (B5)",      "HTTP abuse -> SOSPECHOSO|LIMIT -> 100 pkt/s  OK"]],
    [90, 100]
)

# 7. Limitaciones
pdf.titulo("7. LIMITACIONES CONOCIDAS")
pdf.parrafo(
    "a) Brute Force SSH (B6) - Deteccion ~1%: Los flujos SSH individuales son "
    "indistinguibles de SSH legitimo en el espacio de 14 features a nivel de flow. "
    "Requiere features temporales (tasa de intentos fallidos en ventana de tiempo).\n\n"
    "b) HTTP Abuse lento (B5) - Deteccion ~31%: Los ataques HTTP lentos imitan "
    "patrones de trafico normal. Requiere analisis de secuencia de requests o "
    "features de sesion HTTP.\n\n"
    "c) Lead Time medicion: El calculo automatizado muestra artefacto negativo por "
    "el timeout de flow de Suricata (~30s). Lead Time real medido en vivo: ~26s."
)

# 8. Conclusion
pdf.titulo("8. CONCLUSION")
pdf.parrafo(
    "El sistema detecta el 80.4% de los ataques de red evaluados con una precision "
    "del 99.96%, procesando flujos Suricata en tiempo real y aplicando bloqueo o "
    "limitacion de trafico automaticamente mediante ipset/iptables. La tasa de "
    "falsas alarmas es del 5.1%, con 0% de FP en trafico SSH legitimo y "
    "transferencia de archivos. El sistema opera con disponibilidad del 100% en "
    "las 40 corridas de validacion, ITL=0% (sin impacto en trafico legitimo) y "
    "TIE~100% (toda anomalia detectada recibe accion). Las 6 fases del PPI han "
    "sido completadas con funcionamiento demostrado en entorno de laboratorio controlado."
)

out_pdf = f"{RESULT}/reporte_validacion_final.pdf"
pdf.output(out_pdf)
print(f"PDF generado: {out_pdf}")

# ── ZIP MVP ───────────────────────────────────────────────────
zip_path = f"{RESULT}/MVP_funcional.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    def add(src, arc):
        if os.path.exists(src):
            zf.write(src, arc)

    # Scripts
    for f in glob.glob(f"{BASE}/scripts/*.py"):
        zf.write(f, f"MVP/scripts/{os.path.basename(f)}")
    for f in glob.glob(f"{BASE}/scripts/capture/*.sh"):
        zf.write(f, f"MVP/scripts/capture/{os.path.basename(f)}")
    for f in glob.glob(f"{BASE}/scripts/evaluation/*.sh"):
        zf.write(f, f"MVP/scripts/evaluation/{os.path.basename(f)}")

    # Modelo
    add(f"{BASE}/models/isolation_forest.pkl", "MVP/models/isolation_forest.pkl")
    add(f"{BASE}/models/scaler.pkl",            "MVP/models/scaler.pkl")
    add(f"{BASE}/models/features.csv",          "MVP/models/features.csv")

    # Datasets (solo CSVs pequeños, no raw gz)
    for f in [f"{DATA}/dataset_clean.csv", f"{DATA}/resumen_estadistico.txt",
              f"{DATA}/train.csv", f"{DATA}/val.csv", f"{DATA}/test.csv"]:
        if os.path.exists(f):
            zf.write(f, f"MVP/data/{os.path.basename(f)}")

    # Resultados y reportes
    for f in glob.glob(f"{RESULT}/reports/*.txt"):
        zf.write(f, f"MVP/results/reports/{os.path.basename(f)}")
    for f in glob.glob(f"{RESULT}/figures/*.png"):
        zf.write(f, f"MVP/results/figures/{os.path.basename(f)}")
    for f in glob.glob(f"{RESULT}/tables/*.csv"):
        zf.write(f, f"MVP/results/tables/{os.path.basename(f)}")
    for f in glob.glob(f"{RESULT}/resultados_*.csv"):
        zf.write(f, f"MVP/results/{os.path.basename(f)}")
    add(out_pdf, "MVP/results/reporte_validacion_final.pdf")

    # Documentacion
    add(f"{DOCS}/plan_captura.txt",   "MVP/docs/plan_captura.txt")
    add(f"{DOCS}/guion_ataques.txt",  "MVP/docs/guion_ataques.txt")
    add(f"{DOCS}/bitacora/bitacora_escenarios.txt", "MVP/docs/bitacora_escenarios.txt")

    # README
    readme = f"""MVP — Sistema de Deteccion Temprana de Anomalias de Red
PPI Universidad Peruana Union 2026
Estudiante: Ruben Mark Salazar Tocas

Estructura:
  scripts/          Scripts de captura, entrenamiento y motor de decision
  models/           Modelo Isolation Forest entrenado + scaler
  data/             Datasets procesados (clean, train, val, test)
  results/          Reportes, figuras, tablas y CSVs de corridas F6
  docs/             Documentacion del proyecto

Para ejecutar el motor de decision:
  python3 scripts/motor_decision.py

Requiere: Python 3.10+, scikit-learn, numpy, joblib, ipset, iptables
"""
    zf.writestr("MVP/README.txt", readme)

print(f"ZIP generado: {zip_path}")
size_mb = os.path.getsize(zip_path) / 1024 / 1024
print(f"Tamanio: {size_mb:.1f} MB")
print(f"\nArchivos en el ZIP:")
with zipfile.ZipFile(zip_path) as z:
    for info in z.infolist():
        print(f"  {info.filename}  ({info.file_size//1024} KB)")
