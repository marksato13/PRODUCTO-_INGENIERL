#!/usr/bin/env python3
"""Genera reporte_validacion_final.pdf con métricas actualizadas."""
import os, csv
from datetime import datetime
from fpdf import FPDF

BASE   = '/home/m4rk/ppi-surikata-producto'
RESULT = f'{BASE}/results'

def leer_csv(path):
    if not os.path.exists(path): return []
    with open(path, newline='') as f: return list(csv.DictReader(f))

normal_rows = leer_csv(f'{RESULT}/resultados_normal.csv')
mixto_rows  = leer_csv(f'{RESULT}/resultados_mixto.csv')
reeval_rows = leer_csv(f'{RESULT}/resultados_reeval.csv')
final_rows  = leer_csv(f'{RESULT}/resultados_final.csv')

def pct_disp(rows):
    if not rows: return 'N/A'
    return f"{sum(int(r.get('disponibilidad',1)) for r in rows)/len(rows)*100:.1f}%"

def pct_tie(rows):
    v = []
    for r in rows:
        try: v.append(float(r.get('tie_pct', 0)))
        except: pass
    return f"{sum(v)/len(v):.1f}%" if v else 'N/A'


class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(30, 80, 140)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'PPI - Sistema de Deteccion Temprana de Anomalias de Red',
                  fill=True, new_x='LMARGIN', new_y='NEXT')
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-13)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Universidad Peruana Union 2026  |  Pagina {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def titulo(self, t):
        self.set_font('Helvetica', 'B', 13)
        self.set_fill_color(220, 230, 245)
        self.cell(0, 8, t, fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def parrafo(self, t):
        self.set_font('Helvetica', '', 9)
        self.multi_cell(0, 5, t)
        self.ln(1)

    def tabla(self, headers, rows, col_w=None):
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(50, 100, 160)
        self.set_text_color(255, 255, 255)
        if not col_w:
            col_w = [190 // len(headers)] * len(headers)
        for h, w in zip(headers, col_w):
            self.cell(w, 7, h, border=1, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 8)
        for i, row in enumerate(rows):
            self.set_fill_color(245, 245, 245) if i % 2 == 0 else self.set_fill_color(255, 255, 255)
            for val, w in zip(row, col_w):
                self.cell(w, 6, str(val), border=1, fill=True)
            self.ln()
        self.ln(2)


pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=13)
pdf.add_page()

# Portada
pdf.set_font('Helvetica', 'B', 16)
pdf.set_text_color(30, 80, 140)
pdf.cell(0, 12, 'REPORTE DE VALIDACION FINAL', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_font('Helvetica', 'B', 13)
pdf.cell(0, 8, 'Sistema de Deteccion Temprana de Anomalias de Red',
         new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_font('Helvetica', '', 10)
pdf.set_text_color(80, 80, 80)
for linea in ['Universidad Peruana Union  |  PPI 2026',
              'Estudiante: Ruben Mark Salazar Tocas',
              'Asesores: Ing. Nemias Saboya Rios  |  Ing. Fernando Manuel Asin Gomez',
              f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}']:
    pdf.cell(0, 6, linea, new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_text_color(0, 0, 0)
pdf.ln(6)

# 1. Descripcion
pdf.titulo('1. DESCRIPCION DEL SISTEMA')
pdf.parrafo(
    'Sistema de deteccion temprana de comportamientos anomalos en redes de datos '
    'implementado en laboratorio controlado. Usa Isolation Forest para clasificacion '
    'no supervisada de flujos Suricata 7.0.3, con detectores temporales de Brute Force '
    'SSH y HTTP Abuse, control inline PERMIT/LIMIT/BLOCK via ipset/iptables, y '
    'notificaciones Telegram en tiempo real.')
pdf.tabla(
    ['VM', 'IP', 'Rol'],
    [['Ubuntu Desktop',   '192.168.0.20',  'Cliente / origen trafico normal'],
     ['Kali Linux',       '192.168.0.100', 'Origen trafico anomalo controlado'],
     ['Ubuntu Suricata',  '192.168.0.110', 'Sensor (Suricata 7.0.3, ens35)'],
     ['Ubuntu Server',    '192.168.0.120', 'Objetivo (nginx:80, SSH:22)']],
    [48, 38, 104])

# 2. Modelo
pdf.titulo('2. CONFIGURACION DEL MODELO')
pdf.tabla(
    ['Parametro', 'Valor', 'Descripcion'],
    [['Algoritmo',           'Isolation Forest', 'Deteccion anomalias no supervisada'],
     ['n_estimators',        '300',              'Arboles en el ensemble'],
     ['contamination',       '0.05',             'Fraccion esperada de ruido en datos normales'],
     ['Features',            '14',               'pkts, bytes, duracion, tasas, protocolo, puerto'],
     ['Umbral base',         '-0.5481',          'clf.offset_ (contamination=0.05)'],
     ['tau1 (PERMIT/LIMIT)', '-0.4973',          'Youden index maximo (TPR=91%, FPR=9.5%)'],
     ['tau2 (LIMIT/BLOCK)',  '-0.6873',          'FPR<=2% con maximo TPR (TPR=40.6%)'],
     ['AUC-ROC global',      '0.9440',           'Capacidad discriminativa del modelo']],
    [38, 30, 122])

# 3. Detectores temporales
pdf.titulo('3. DETECTORES TEMPORALES (MEJORAS v2)')
pdf.tabla(
    ['Detector', 'Ventana', 'Umbral LIMIT', 'Umbral BLOCK', 'Validado en vivo'],
    [['Brute Force SSH', '60s', '5 intentos',  '15 intentos', 'Si - BLOCK 15/60s OK'],
     ['HTTP Abuse HTTP', '30s', '50 requests', '100 requests','Si - BLOCK 100/30s + Telegram OK']],
    [42, 18, 28, 28, 74])
pdf.parrafo('Efecto: recall Brute Force 1%->~90%. HTTP Abuse 31%->~80%. Recall global estimado: 92-95%.')

# 4. Metricas globales
pdf.titulo('4. METRICAS GLOBALES DEL MODELO')
pdf.tabla(
    ['Metrica', 'Modelo base', 'Con detectores', 'Interpretacion'],
    [['Recall',            '87.6%',   '~92-95%', 'Porcentaje de ataques detectados'],
     ['Precision',         '99.96%',  '99.96%',  'Casi sin falsas alarmas'],
     ['F1-Score',          '0.9338',  '>0.94',   'Balance precision-recall'],
     ['FP Rate (normal)',  '5.1%',    '5.1%',    'Trafico normal mal clasificado'],
     ['FP SSH',            '0%',      '0%',      'SSH legitimo: cero falsas alarmas'],
     ['FP Transferencia',  '0%',      '0%',      'Transferencia archivos: cero FP'],
     ['AUC-ROC',           '0.9440',  '0.9440',  '94.4% discriminacion correcta'],
     ['Latencia P95',      'N/A',     '34.8 ms', 'Muy por debajo del limite 500ms']],
    [48, 28, 28, 86])

# 5. AUC por escenario
pdf.titulo('5. AUC-ROC POR ESCENARIO INDIVIDUAL')
pdf.tabla(
    ['Escenario', 'AUC', 'Deteccion', 'Score medio', 'Estado'],
    [['UDP Flood (B3)',        '0.9905', '100%',  '-0.714', 'Excelente'],
     ['ICMP Flood (B4)',       '0.9861', '100%',  '-0.700', 'Excelente'],
     ['Mixto C3 (desc+UDP)',   '0.9801', '99.3%', '-0.677', 'Excelente'],
     ['Mixto C1 (HTTP+SYN)',   '0.9737', '100%',  '-0.653', 'Excelente'],
     ['Port Scan (B2)',        '0.9721', '99.9%', '-0.651', 'Excelente'],
     ['SYN Flood (B1)',        '0.9529', '72.2%', '-0.606', 'Muy bueno'],
     ['Mixto C2 (SSH+scan)',   '0.9277', '57.1%', '-0.609', 'Muy bueno'],
     ['HTTP Abuse (B5)',       '0.8630', '56.6%', '-0.589', 'Bueno + det.temporal'],
     ['Brute Force (B6)',      '0.6770', '0.9%',  '-0.438', 'Limitado + det.temporal']],
    [52, 16, 22, 26, 74])

# 6. Validacion F6
pdf.titulo('6. RESULTADOS FASE 6 - 40 CORRIDAS')
pdf.tabla(
    ['Grupo', 'Corridas', 'Disponibilidad', 'TIE', 'ITL', 'Latencia'],
    [['Normal (1-10)',  '10', pct_disp(normal_rows), 'N/A',              '0%', '6.6 ms'],
     ['Mixto (11-20)',  '10', pct_disp(mixto_rows),  pct_tie(mixto_rows),  '0%', '6.6 ms'],
     ['Reeval (21-30)', '10', pct_disp(reeval_rows), pct_tie(reeval_rows), '0%', '6.6 ms'],
     ['Final (31-40)',  '10', pct_disp(final_rows),  pct_tie(final_rows),  '0%', '6.6 ms']],
    [38, 22, 35, 28, 24, 43])
pdf.parrafo('Lead Time real: ~26s. MTTC: ~28s. Disponibilidad 100% en las 40 corridas.')

# 7. Validacion en vivo
pdf.titulo('7. VALIDACIONES EN VIVO')
pdf.tabla(
    ['Escenario', 'Resultado'],
    [['SSH legitimo + Port scan',  '0 FP en SSH  |  1705/1705 portscan detectados'],
     ['HTTP Abuse - curl en bucle','100 req/30s -> BLOCK + alerta Telegram OK'],
     ['Brute Force - 25 intentos', '15 intentos/60s -> BLOCK + alerta Telegram OK'],
     ['SYN Flood IPs random',      'IPs spoofadas -> LIMIT (score -0.65) OK'],
     ['Accion LIMIT validada',     'SOSPECHOSO score -0.51, hashlimit 100pkt/s OK']],
    [90, 100])

# 8. Limitaciones
pdf.titulo('8. LIMITACIONES DOCUMENTADAS')
pdf.parrafo(
    'a) Brute Force SSH (B6) modelo base ~1%: resuelto con detector temporal '
    '(ventana 60s, 15 intentos -> BLOCK directo).\n\n'
    'b) HTTP Abuse lento (B5) modelo base ~31%: mejorado con detector temporal '
    '(ventana 30s, 100 requests -> BLOCK directo).\n\n'
    'c) Lead Time automatico muestra artefacto negativo por timeout de flow Suricata '
    '(~30s). Lead Time real medido en vivo: ~26s.\n\n'
    'd) El eve.json acumula todo el trafico historico. Solucion: filtro src_ip en '
    'entrenamiento + fix de rotacion en motor (deteccion automatica de logrotate).')

# 9. Conclusion
pdf.titulo('9. CONCLUSION')
pdf.parrafo(
    'El sistema detecta el 87.6% de los ataques (modelo base) y hasta ~92-95% con '
    'detectores temporales, con precision del 99.96%, latencia P95 de 34.8ms '
    '(< 500ms requerido), disponibilidad 100% y cero impacto en trafico legitimo. '
    'El motor procesa flujos Suricata en tiempo real aplicando acciones PERMIT/LIMIT/BLOCK '
    'via ipset/iptables y envia notificaciones Telegram. Las 6 fases del PPI estan '
    'completadas con funcionamiento demostrado en 40 corridas de validacion en '
    'entorno de laboratorio controlado.')

out = f'{RESULT}/reporte_validacion_final.pdf'
pdf.output(out)
print(f'PDF generado: {out}')
print(f'Tamanio: {os.path.getsize(out)/1024:.1f} KB')
