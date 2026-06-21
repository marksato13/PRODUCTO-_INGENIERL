from fpdf import FPDF, XPos, YPos
import os

def N(s):
    return (str(s)
        .replace('--','--').replace(chr(0x2014),'--').replace(chr(0x2013),'-')
        .replace(chr(0x2192),'->').replace(chr(0x2190),'<-')
        .replace(chr(0x03c4),'tau').replace(chr(0x2265),'>=').replace(chr(0x2264),'<=')
        .replace(chr(0x00b7),'.').replace(chr(0x201c),'"').replace(chr(0x201d),'"')
        .replace(chr(0x2018),"'").replace(chr(0x2019),"'")
        .replace(chr(0x00e9),'e').replace(chr(0x00f3),'o').replace(chr(0x00f1),'n')
        .replace(chr(0x00fa),'u').replace(chr(0x00e1),'a').replace(chr(0x00ed),'i')
        .replace(chr(0x00c1),'A').replace(chr(0x00c9),'E').replace(chr(0x00cd),'I')
        .replace(chr(0x00d3),'O').replace(chr(0x00da),'U').replace(chr(0x00d1),'N'))

PROJ = '/home/m4rk/ppi-surikata-producto'
OUT  = PROJ + '/results/informe_final_PPI_UPeU_2026.pdf'
G    = PROJ + '/results/graficas_f6'
R    = PROJ + '/results'
E    = PROJ + '/results/eda'
GP   = PROJ + '/results/graficas_predictor'

BLU=(41,128,185); LBLU=(214,234,248)
GRN=(39,174,96);  LGRN=(213,232,212)
RED=(192,57,43);  LRED=(250,219,216)
YEL=(243,156,18); LYEL=(254,243,205)
GRY=(127,140,141); DRK=(44,62,80)
WHT=(255,255,255); LGRY=(245,245,245)
TEAL=(23,162,184)

NL = dict(new_x=XPos.LMARGIN, new_y=YPos.NEXT)
INL= dict(new_x=XPos.RIGHT,   new_y=YPos.TOP)

class PDF(FPDF):
    def normalize_text(self, txt):
        txt = N(str(txt))
        return super().normalize_text(txt)

    sec = 0
    def header(self):
        if self.page_no()==1: return
        self.set_fill_color(41,128,185); self.rect(0,0,210,8,style='F')
        self.set_xy(25,1); self.set_font('Helvetica','I',7); self.set_text_color(*WHT)
        self.cell(0,6,'Sistema de Deteccion Temprana de Anomalias en Red mediante Aprendizaje Automatico | PPI UPeU 2026',**NL)
        self.set_text_color(0,0,0)
    def footer(self):
        self.set_fill_color(*LGRY); self.rect(0,285,210,12,style='F')
        self.set_y(-12); self.set_font('Helvetica','I',8)
        self.set_text_color(*GRY)
        self.cell(0,6,f'Pagina {self.page_no()}  |  Ruben Mark Salazar Tocas · Elias Uziel Sanne Fernandez  |  UPeU 2026',align='C',**NL)
        self.set_text_color(0,0,0)

    def h1(self,txt):
        PDF.sec+=1; self.ln(5)
        self.set_fill_color(*BLU); self.set_text_color(*WHT)
        self.set_font('Helvetica','B',13)
        self.cell(0,11,f'  {PDF.sec}.  {txt}',fill=True,**NL)
        self.set_text_color(0,0,0); self.ln(4)

    def h2(self,txt):
        self.ln(4); self.set_font('Helvetica','B',11)
        self.set_text_color(*BLU); self.cell(0,8,txt,**NL)
        self.set_draw_color(*BLU)
        self.line(self.l_margin,self.get_y(),self.w-self.r_margin,self.get_y())
        self.set_draw_color(0,0,0); self.set_text_color(0,0,0); self.ln(3)

    def h3(self,txt):
        self.ln(3); self.set_font('Helvetica','B',10)
        self.set_text_color(*DRK); self.cell(0,7,txt,**NL)
        self.set_text_color(0,0,0); self.ln(1)

    def p(self,txt):
        self.set_font('Helvetica','',10)
        self.multi_cell(0,5.5,N(txt),align='J'); self.ln(2)

    def li(self,txt,color=None):
        self.set_font('Helvetica','',10)
        pw = self.w - self.l_margin - self.r_margin
        y0 = self.get_y()
        if color: self.set_text_color(*color)
        self.set_xy(self.l_margin+2, y0)
        self.cell(6,5.5,chr(149)+' ',**INL)
        self.set_xy(self.l_margin+8, y0)
        self.multi_cell(pw-8,5.5,N(txt))
        self.set_text_color(0,0,0)

    def cap(self,txt):
        self.set_font('Helvetica','I',8.5); self.set_text_color(*GRY)
        self.cell(0,5,N(txt),align='C',**NL); self.set_text_color(0,0,0); self.ln(3)

    def fig(self,path,cap,wp=0.88):
        if not os.path.exists(path): return
        pw = self.w-self.l_margin-self.r_margin
        iw = pw*wp
        if self.get_y()>self.h-self.b_margin-70: self.add_page()
        self.set_fill_color(*LGRY); self.rect(self.l_margin,self.get_y()-1,pw,2,style='F')
        self.image(path,x=(self.w-iw)/2,w=iw)
        self.cap(cap)

    def kpis(self,items):
        pw=self.w-self.l_margin-self.r_margin; cw=pw/len(items)
        y0=self.get_y()
        for i,(lbl,val,col) in enumerate(items):
            x=self.l_margin+i*cw
            self.set_fill_color(*col)
            self.rect(x,y0,cw-1,11,style='F')
            self.set_xy(x,y0+1); self.set_text_color(*WHT)
            self.set_font('Helvetica','B',12)
            self.cell(cw-1,9,val,align='C',**INL)
        self.set_xy(self.l_margin,y0+11)
        for i,(lbl,val,col) in enumerate(items):
            self.set_xy(self.l_margin+i*cw,self.get_y())
            self.set_fill_color(230,240,255); self.set_text_color(*DRK)
            self.set_font('Helvetica','',8)
            self.cell(cw-1,6,lbl,border=1,fill=True,align='C',**INL)
        self.set_text_color(0,0,0); self.set_fill_color(*WHT); self.ln(11)

    def tabla(self,hdrs,rows,widths=None,hdr_color=None):
        pw=self.w-self.l_margin-self.r_margin
        if widths is None: widths=[pw/len(hdrs)]*len(hdrs)
        hc = hdr_color or BLU
        self.set_font('Helvetica','B',9)
        self.set_fill_color(*hc); self.set_text_color(*WHT)
        for h,w in zip(hdrs,widths):
            self.cell(w,7,N(str(h)),border=1,fill=True,align='C',**INL)
        self.set_xy(self.l_margin,self.get_y()+7); self.set_text_color(0,0,0)
        for ri,row in enumerate(rows):
            if self.get_y()>self.h-self.b_margin-15: self.add_page()
            self.set_font('Helvetica','',9)
            fc = (240,248,255) if ri%2==0 else WHT
            self.set_fill_color(*fc)
            for c,w in zip(row,widths):
                self.cell(w,6,N(str(c)),border=1,fill=True,align='C',**INL)
            self.set_xy(self.l_margin,self.get_y()+6)
        self.set_fill_color(*WHT); self.ln(4)

    def box(self,txt,fc=LBLU,bc=BLU,bold_first=False):
        self.set_fill_color(*fc); self.set_draw_color(*bc)
        self.set_line_width(0.4)
        self.set_font('Helvetica','',9.5)
        self.multi_cell(0,5.5,N(txt),border=1,fill=True,align='J')
        self.set_draw_color(0,0,0); self.set_line_width(0.2); self.ln(3)

    def alert(self,txt,color=RED,bg=LRED):
        self.set_fill_color(*bg); self.set_draw_color(*color)
        self.set_font('Helvetica','B',9)
        self.multi_cell(0,6,N(txt),border=1,fill=True,align='L')
        self.set_draw_color(0,0,0); self.ln(2)

    def success(self,txt):
        self.set_fill_color(213,232,212); self.set_draw_color(*GRN)
        self.set_font('Helvetica','',9.5)
        self.multi_cell(0,5.5,N(txt),border=1,fill=True,align='J')
        self.set_draw_color(0,0,0); self.ln(2)

    def hr(self,color=GRY):
        self.set_draw_color(*color)
        self.line(self.l_margin,self.get_y(),self.w-self.r_margin,self.get_y())
        self.set_draw_color(0,0,0); self.ln(4)

    def badge(self,txt,col=GRN):
        self.set_font('Helvetica','B',8)
        self.set_fill_color(*col); self.set_text_color(*WHT)
        self.cell(0,5,N(txt),fill=True,align='C',**NL)
        self.set_text_color(0,0,0); self.ln(1)

# =============================================================================
pdf = PDF('P','mm','A4')
pdf.set_auto_page_break(True,22); pdf.set_margins(25,22,20)
pdf.add_page()

# ── PORTADA ───────────────────────────────────────────────────────────────────
pdf.set_fill_color(*BLU); pdf.rect(0,0,210,50,style='F')
pdf.set_fill_color(*DRK); pdf.rect(0,50,210,8,style='F')
pdf.set_xy(25,8); pdf.set_font('Helvetica','B',17); pdf.set_text_color(*WHT)
pdf.cell(0,9,'UNIVERSIDAD PERUANA UNION',align='C',**NL)
pdf.set_xy(25,18); pdf.set_font('Helvetica','',12)
pdf.cell(0,7,'Facultad de Ingenieria y Arquitectura',align='C',**NL)
pdf.set_xy(25,26); pdf.set_font('Helvetica','I',10)
pdf.cell(0,7,'Escuela Profesional de Ingenieria de Sistemas',align='C',**NL)
pdf.set_text_color(0,0,0); pdf.ln(40)

pdf.set_font('Helvetica','B',9); pdf.set_text_color(*GRY)
pdf.cell(0,6,'PROYECTO PRODUCTIVO DE INVESTIGACION (PPI) — INFORME FINAL',align='C',**NL)
pdf.ln(5); pdf.set_font('Helvetica','B',16); pdf.set_text_color(*DRK)
pdf.multi_cell(0,9,'Deteccion Temprana de Comportamientos Anomalos en Redes de Datos',align='C')
pdf.ln(2); pdf.set_font('Helvetica','B',12); pdf.set_text_color(*BLU)
pdf.multi_cell(0,8,'mediante Aprendizaje Automatico y un Mecanismo de Control en Tiempo Real',align='C')
pdf.set_text_color(0,0,0); pdf.ln(10); pdf.hr()

for lbl,val in [
    ('Estudiante 1:','Ruben Mark Salazar Tocas'),
    ('Estudiante 2:','Elias Uziel Sanne Fernandez'),
    ('Asesor 1:','Ing. Nemias Saboya Rios'),
    ('Asesor 2:','Ing. Fernando Manuel Asin Gomez'),
    ('Universidad:','Universidad Peruana Union (UPeU) — Lima, Peru'),
    ('Fecha:','Junio 2026'),
    ('Repositorio:','github.com/marksato13/PRODUCTO-_INGENIERL'),
    ('Estado:','F1-F6 completadas y validadas')]:
    pdf.set_font('Helvetica','B',10); pdf.cell(42,7,lbl,**INL)
    pdf.set_font('Helvetica','',10); pdf.cell(0,7,val,**NL)
pdf.ln(7); pdf.hr()

pdf.set_font('Helvetica','B',10); pdf.set_text_color(*BLU)
pdf.cell(0,7,'Resumen Ejecutivo',**NL); pdf.set_text_color(0,0,0)
pdf.set_font('Helvetica','',10)
pdf.multi_cell(0,5.5,'Este PPI disena, implementa y valida un sistema de deteccion temprana de comportamientos anomalos en redes de datos para entornos universitarios. El sistema utiliza el algoritmo Isolation Forest (IF) entrenado exclusivamente con trafico normal capturado por Suricata 7.0.3 sobre 14 features de flujos de red. Un motor de decision en tiempo real (motor_decision.py) procesa cada flow con latencia P95=34.8 ms y aplica control inline mediante ipset/iptables (PERMIT/LIMIT/BLOCK). La validacion con 40 corridas demostro Disponibilidad=100%, ITL=0% (ningun trafico legitimo afectado) y Lead Time de deteccion=61.92 s. El experimento comparativo evaluo 7 modelos; IF fue seleccionado como modelo de produccion por sus 40 corridas validadas en vivo y rendimiento certificado.',align='J')
pdf.ln(5)
pdf.kpis([('Disponibilidad','100%',GRN),('ITL','0%',GRN),('AUC-ROC','0.8998',BLU),('Latencia P95','34.8 ms',BLU),('Lead Time','61.9 s',YEL),('Corridas OK','40/40',GRN)])

# ── 1. INTRODUCCION ───────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Introduccion y Motivacion')
pdf.p('Las redes universitarias concentran servicios criticos (plataformas academicas, repositorios, laboratorios remotos) y son objetivos frecuentes de ataques automatizados: inundaciones SYN, escaneos de puertos, fuerza bruta SSH y abuso de servicios web. La deteccion tardia — tipicamente horas o dias — permite al atacante completar su objetivo antes de cualquier respuesta.')
pdf.p('Este PPI propone un sistema de deteccion y contencion inline que actua en tiempo real: Suricata 7.0.3 captura flujos de red, el algoritmo Isolation Forest puntua cada flujo en <35 ms, y la accion (PERMIT/LIMIT/BLOCK) se aplica directamente en el kernel Linux mediante ipset/iptables sin intervencion humana.')
pdf.h2('Objetivos especificos')
for o in [
    'F1: Configurar laboratorio virtualizado de 5 nodos con topologia realista (Cliente, Admin, Atacante, Sensor, Servidor).',
    'F2: Capturar 47 archivos eve.json.gz en 13 escenarios — tráfico normal (4 tipos), ataques (6 tipos, 2 fechas) y mixtos (3 tipos).',
    'F3: Entrenar Isolation Forest (n=300, 14 features) y derivar umbrales tau1/tau2 via curva ROC sobre datos no vistos.',
    'F4: Implementar motor de decision en tiempo real (latencia P95<500ms) con detectores heuristicos para BruteForce y HTTP Abuse.',
    'F5: Integrar control inline via ipset/iptables con dashboard web en tiempo real (Flask+SSE).',
    'F6: Validar con 40 corridas midiendo Disponibilidad, ITL, Lead Time, Latencia y AUC-ROC.']:
    pdf.li(o)
pdf.h2('Alcance y limitaciones')
pdf.p('El sistema opera en red LAN universitaria (192.168.0.0/24). El modelo IF fue entrenado en laboratorio controlado — su reentrenamiento con datos de produccion real es la siguiente fase natural. Las acciones BLOCK/LIMIT se aplican en el sensor, no en el router de borde.')

# ── 2. METODOLOGIA PIPELINE ───────────────────────────────────────────────────
pdf.h1('Metodologia — Pipeline de 6 Fases')
pdf.p('El sistema se articula en 6 fases donde cada una produce artefactos que consume la siguiente. El pipeline es determinista y reproducible: ejecutar los 6 scripts en secuencia recalibra el sistema con nuevos datos.')
pdf.tabla(['Fase','Script principal','Entrada','Salida principal'],
    [('F1','— (configuracion)','VMs VMware','5 nodos, Suricata activo, SSH keys'),
     ('F2','exportar_eve_por_escenario.sh','eve.json (Suricata)','47 archivos .gz en data/raw/'),
     ('F3a','fase3_entrenar.py','*_normal_*.gz','isolation_forest.pkl, scaler.pkl, normal_holdout.csv'),
     ('F3b','fase3_evaluar.py','holdout.csv + *_anom_*.gz','metricas_offline.txt, auc_roc.png'),
     ('F3c','auc_por_escenario.py','*_anom_*.gz','AUC por archivo de captura'),
     ('F4+F5','motor_decision.py','eve.json (tail -f)','motor_decision.log, acciones ipset'),
     ('F5','dashboard_web.py','motor_decision.log','Dashboard web :8080 (SSE)'),
     ('F6','f6_corridas.py','scripts de escenario','resultados_f6_completo.csv, 7 graficas PNG')],
    [14,42,50,62])
pdf.box('Principio one-class: el modelo aprende UNICAMENTE el perfil del trafico normal (Grupo A). Cualquier desviacion significativa es tratada como anomalia. No se usan etiquetas de ataque en el entrenamiento — esto permite detectar ataques futuros desconocidos [Liu 2008, Chandola 2009].')

# ── 3. F1 — ENTORNO ───────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F1 — Entorno de Laboratorio')
pdf.p('El laboratorio simula una red universitaria real con roles diferenciados: un cliente Windows, una maquina de administracion/generacion de trafico normal, un atacante Kali Linux, un sensor de red con Suricata y un servidor de servicios.')
pdf.tabla(['VM','IP','Sistema Operativo','Rol en el PPI','Herramientas clave'],
    [('Win11 Cliente','192.168.0.10','Windows 11','Simula usuario final','Navegador, RDP'),
     ('Ubuntu Desktop','192.168.0.20','Ubuntu 22.04 LTS','Admin + origen trafico normal','curl, wget, scp, ssh, Python 3'),
     ('Kali Linux','192.168.0.100','Kali 2024','Origen de ataques controlados','hping3, nmap, hydra, sshpass'),
     ('Ubuntu Sensor','192.168.0.110','Ubuntu 22.04 LTS','Captura + deteccion + control','Suricata 7.0.3, Python venv, ipset, iptables'),
     ('Ubuntu Server','192.168.0.120','Ubuntu 22.04 LTS','Objetivo de servicio','nginx 1.18 (:80), OpenSSH (:22), ipset')],
    [22,30,28,40,48])
pdf.h3('Configuracion de red y seguridad')
for item in [
    'Red interna: 192.168.0.0/24. Suricata captura pasivamente en ens35 (modo af-packet, promiscuo).',
    'SSH keys configuradas Desktop->Sensor y Desktop->Server (BatchMode=yes, sin contrasena interactiva).',
    'Whitelist de IPs protegidas (nunca bloqueadas): 192.168.0.1, .20, .110, .120, .130, .140, 127.0.0.1.',
    'ppi-motor.service: systemd unit con reinicio automatico en fallo (Restart=always, RestartSec=5s).',
    'venv Python en sensor (/home/m4rk/ppi-sensor/venv) — sklearn 1.9.0 fijado para reproducibilidad.']:
    pdf.li(item)
pdf.h3('Comandos de verificacion del entorno')
pdf.box('# Verificar conectividad\nssh m4rk@192.168.0.110 "echo OK sensor"\nssh m4rk@192.168.0.120 "echo OK servidor"\n\n# Estado del motor\nsudo systemctl status ppi-motor.service\n\n# Dashboard terminal (sensor)\npython3 scripts/dashboard.py\n\n# Dashboard web (browser en Desktop)\n# http://192.168.0.110:8080')

# ── 4. F2 — CAPTURA ───────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F2 — Captura de Trafico por Grupos')
pdf.p('Se capturaron 47 archivos eve.json.gz organizados en tres grupos con proposito metodologico diferente. Cada escenario se ejecuto en multiples corridas para garantizar representatividad estadistica.')
pdf.tabla(['Grupo','Archivos','Flows totales','Proposito en el pipeline'],
    [('A — Normal','28 archivos (.gz)','67,135 flows','Entrenamiento del modelo IF (80%) + holdout evaluacion (20%)'),
     ('B — Anomalo','13 archivos (.gz)','598,285 flows','Evaluacion offline: AUC-ROC, umbrales tau1/tau2, metricas'),
     ('C — Mixto','6 archivos (.gz)','variable','Evaluacion realista: trafico normal + ataque simultaneos')],
    [22,28,28,90])
pdf.h3('Escenarios por tipo y herramienta')
pdf.tabla(['Escenario','Grupo','Origen','Herramienta','Descripcion del trafico generado'],
    [('http_normal','A','Desktop :20','curl, wget','GET al nginx:80 con pausa 5-10s. Simula navegacion normal.'),
     ('ssh_legitimo','A','Desktop :20','ssh, scp','Sesion SSH interactiva + transferencia de archivos.'),
     ('transferencia','A','Desktop :20','scp, wget','Descarga de archivos 1-100MB al servidor.'),
     ('sostenido','A','Desktop :20','curl+ssh mixto','Combinacion de HTTP y SSH durante 15 minutos.'),
     ('syn_flood','B','Kali :100','hping3 -S -p 80','SYN sin completar handshake. Genera flows de 1 pkt, 0 bytes_toclient.'),
     ('port_scan','B','Kali :100','nmap -sS 1-1024','Escaneo sigiloso. Un SYN por puerto, rara respuesta. Alto pkt_rate.'),
     ('udp_flood','B','Kali :100','hping3 --udp :53','Inundacion UDP. Flows sin estado. byte_ratio elevado.'),
     ('icmp_flood','B','Kali :100','hping3 -1 --flood','Ping flood. is_icmp=1, duration corta, pkt_rate muy alto.'),
     ('http_abuse','B','Kali :100','curl bucle','100+ GET/30s. Activa detector heuristico HTTP_ABUSE.'),
     ('bruteforce','B','Kali :100','hydra, sshpass','15+ intentos SSH/60s. Activa detector BruteForce.'),
     ('mixto_http_syn','C','Desktop+Kali','curl + hping3','Trafico normal + SYN flood simultaneos.'),
     ('mixto_ssh_scan','C','Desktop+Kali','ssh + nmap','SSH legitimo + escaneo de puertos simultaneos.'),
     ('mixto_trans_udp','C','Desktop+Kali','scp + hping3','Descarga de archivos + UDP flood simultaneos.')],
    [28,14,24,26,76])
pdf.h3('Split 80/20 para entrenamiento del modelo')
pdf.tabla(['Artefacto producido','Flows','Descripcion y uso en pipeline'],
    [('normal_holdout.csv (20%)','13,427 flows','Reservado ANTES de entrenar. Usado en fase3_evaluar.py para medir FPR real sobre datos normales no vistos.'),
     ('X_train (80% interno)','53,708 flows','Entra a IsolationForest.fit(). El scaler se ajusta SOLO sobre este conjunto (sin data leakage).')],
    [40,22,106])
pdf.box('Split 80/20 ALEATORIO con semilla fija (train_test_split, test_size=0.20, random_state=42, shuffle=True). La semilla garantiza reproducibilidad exacta. No se usa split cronologico porque IF no supervisado no tiene riesgo de data leakage temporal — aprende solo el perfil de normalidad, no eventos especificos.')

# ── 5. EDA ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Analisis Exploratorio de Datos (EDA)')
pdf.p('Se analizaron 651,993 flows del conjunto completo (A+B+C) para confirmar que las 14 features seleccionadas discriminan estadisticamente entre trafico normal y anomalo. El test estadistico utilizado es Mann-Whitney U — no parametrico, no asume normalidad.')
pdf.h3('Resultado: 14/14 features significativas (p < 0.001)')
pdf.tabla(['Feature','Tipo','p-valor','Separacion','Ejemplo discriminativo'],
    [('byte_ratio','Ratio','< 0.001','MUY ALTA','Normal: mediana=0.96 | Anomalo: mediana=60.0 (SYN flood: 0 bytes toclient)'),
     ('pkt_rate','Tasa','< 0.001','MUY ALTA','Normal: ~800 pkt/s | SYN flood: 20,000+ pkt/s'),
     ('bytes_toserver','Volumen','< 0.001','ALTA','Floods envian muchos bytes al servidor sin respuesta proporcional'),
     ('duration','Temporal','< 0.001','ALTA','SYN/UDP floods: duration < 0.01s | SSH normal: > 30s'),
     ('pkt_ratio','Ratio','< 0.001','ALTA','Floods: muchos pkts_toserver, pocos toclient'),
     ('dest_port','Puerto','< 0.001','MEDIA','Puerto 80 dom. en HTTP abuse; puertos 1-1024 en port scan'),
     ('pkt_toclient','Volumen','< 0.001','MEDIA','Respuesta nula en floods (servidor no puede contestar)'),
     ('is_tcp','Flag','< 0.001','MEDIA','SYN flood, port scan: is_tcp=1 con byte_ratio anomalo'),
     ('is_udp','Flag','< 0.001','MEDIA','UDP flood: is_udp=1 con duracion minima'),
     ('is_icmp','Flag','< 0.001','MEDIA','ICMP flood: is_icmp=1, pkt_rate muy alto'),
     ('avg_pkt_size','Tamano','< 0.001','MEDIA','Floods: paquetes minimos (40-64B) vs normal (200-1500B)'),
     ('byte_rate','Tasa','< 0.001','MEDIA','Tasa de bytes total: floods = muy alto unidireccional'),
     ('pkts_toserver','Volumen','< 0.001','MEDIA','Floods: pkts_toserver >> pkts_toclient'),
     ('bytes_toclient','Volumen','< 0.001','BAJA','Floods: bytes_toclient=0 frecuentemente')],
    [26,18,18,20,86])
pdf.fig(E+'/eda_01_distribuciones.png','Figura 1 — Distribuciones de las 14 features: normal (azul) vs anomalo (naranja). Separacion visible en byte_ratio y pkt_rate.',0.95)
pdf.fig(E+'/eda_02_protocolo.png','Figura 2 — Distribucion por protocolo: ataques concentran TCP (SYN/scan) y UDP (floods) vs trafico normal mas variado.',0.88)
pdf.add_page()
pdf.fig(E+'/eda_03_boxplots.png','Figura 3 — Boxplots de features clave. byte_ratio: normal IQR=0.5-2.0 vs anomalo IQR=0.1-120. Separacion de mas de 60x en la mediana.',0.95)
pdf.fig(E+'/eda_04_correlacion.png','Figura 4 — Correlacion de Spearman entre las 14 features. Alta correlacion pkts<->bytes (esperada). byte_ratio y pkt_rate son features independientes clave.',0.88)
pdf.add_page()
pdf.fig(E+'/eda_05_dest_ports.png','Figura 5 — Top puertos destino. Anomalo: concentracion en :80 (HTTP abuse, SYN flood) y escaneo 1-1024 (port scan). Normal: :80, :22 sin repeticion masiva.',0.88)
pdf.fig(E+'/eda_06_stats_tabla.png','Figura 6 — Estadisticas descriptivas completas con p-valores Mann-Whitney U. Todas las features: p < 0.001 (nivel alpha = 0.05 superado en 5 ordenes de magnitud).',0.95)

# ── 6. F3 — MODELADO ─────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F3 — Modelado Offline: Isolation Forest')
pdf.h3('Algoritmo: Isolation Forest')
pdf.p('Isolation Forest [Liu et al. 2008] es un algoritmo de deteccion de anomalias no supervisado. Su principio: los puntos anomalos son mas faciles de aislar aleatoriamente que los normales. El modelo construye n_estimators=300 arboles de aislamiento. Para cada flujo nuevo, el score es el promedio de pasos necesarios para aislarlo:')
pdf.box('score cercano a 0  => facil de aislar => ANOMALIA\nscore cercano a -1 => dificil de aislar => NORMAL\n\nEjemplo SYN Flood: pkts_toserver=1, bytes_toclient=0, duration=0.001s, pkt_rate=10000\n  => El arbol lo aísla en 2-3 pasos => score=-0.65 => BLOCK\n\nEjemplo HTTP normal: pkts_toserver=4, bytes_toclient=1200, duration=0.8s, pkt_rate=5\n  => El arbol necesita 20+ pasos => score=-0.38 => PERMIT')
pdf.h3('Parametros del modelo (fase3_entrenar.py)')
pdf.tabla(['Parametro','Valor','Justificacion'],
    [('n_estimators','300','Convergencia del AUC a partir de n=100 [Liu 2008]. 300 garantiza estabilidad.'),
     ('contamination','0.05','Prior de anomalias en entrenamiento. No afecta score, solo offset interno.'),
     ('max_samples','auto','= min(256, n_train). Balance entre sesgo y varianza por arbol.'),
     ('random_state','42','Reproducibilidad exacta del modelo y del split 80/20.'),
     ('n_jobs','-1','Paralelo en todos los cores disponibles del sensor.')],
    [26,18,124])
pdf.h3('Umbrales de decision tau1 y tau2 (derivados por curva ROC)')
pdf.tabla(['Umbral','Valor','Criterio de derivacion','TPR','FPR','Accion del motor'],
    [('tau1','-0.4459','Indice de Youden: max(TPR - FPR) en la curva ROC [Youden 1950]','99.40%','20.47%','score > tau1  => PERMIT'),
     ('tau2','-0.6027','FPR <= 2%: punto de maxima TPR con FPR controlado','18.27%','2.00%','score > tau2  => LIMIT')],
    [14,18,72,16,16,32])
pdf.p('Nota sobre FPR=20.47%: segun Buczak & Guven [2016], los IDS basados en anomalias tipicamente operan con FPR 10-30% a maxima TPR. Este valor se mitiga en produccion con la whitelist de IPs internas. Reducir tau1 para bajar FPR haría escapar SYN floods con score ~ -0.49.')
pdf.kpis([('AUC-ROC','0.8998',BLU),('Precision','99.54%',GRN),('Recall','99.40%',GRN),('F1','0.9947',GRN),('T.train','< 10 s',YEL)])
pdf.fig(R+'/auc_roc.png','Figura 7 — Curva ROC del modelo IF (AUC=0.8998). tau1 marcado con Youden index, tau2 con FPR<=2%.',0.75)
pdf.fig(R+'/isolation_forest_resultado.png','Figura 8 — Distribucion de scores IF: normal (azul, media=-0.40) vs anomalo (rojo, media=-0.54). Separacion de 0.14 puntos.',0.75)
pdf.h3('AUC por escenario — comparacion IF vs Autoencoder')
pdf.tabla(['Archivo captura (Grupo B)','Flows','AUC Isolation Forest','AUC Autoencoder'],
    [('bruteforce 02-jun','2,061','0.9727','0.9649'),
     ('http_abuse 02-jun','13,889','0.9545','0.9516'),
     ('icmp_flood 02-jun','23,460','0.9160','0.9966'),
     ('port_scan 02-jun','3,258','0.8351','0.9901'),
     ('syn_flood 02-jun','95,393','0.8815','0.9517'),
     ('udp_flood 02-jun','18,168','0.9579','0.9881'),
     ('bruteforce 03-jun','100,000','0.8252','0.9863'),
     ('bruteforce 15-jun','4,824','0.9728','0.9036'),
     ('http_abuse 15-jun','36,902','0.9749','0.9111'),
     ('icmp_flood 15-jun','100,000','0.8955','0.9996'),
     ('port_scan 15-jun','100,000','0.9508','0.9918'),
     ('syn_flood 15-jun','330','0.9515','0.8287'),
     ('udp_flood 15-jun','100,000','0.9623','0.9883'),
     ('MEDIA (13 escenarios)','598,285','0.9270','0.9579')],
    [42,18,34,34])

# ── 7. F4 — MOTOR ────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F4 — Motor de Decision en Tiempo Real')
pdf.p('El motor (motor_decision.py, ~620 lineas) es el nucleo del sistema. Corre como servicio systemd (ppi-motor.service) en el sensor. Lee eve.json en tiempo real usando seguir_eve() — equivalente a tail -f con deteccion de rotacion — y procesa cada flow independientemente.')
pdf.h3('Pipeline de procesamiento por flow (orden exacto de ejecucion)')
pdf.tabla(['Paso','Funcion','Descripcion'],
    [('1','seguir_eve()','Lee nueva linea de eve.json. Filtra: solo event_type=flow.'),
     ('2','Filtro whitelist','Si src_ip esta en WHITELIST => IGNORAR. IPs internas nunca bloqueadas.'),
     ('3','extract_features()','Calcula 14 features del flow. Aplica scaler.transform() (sin fit — previene data leakage).'),
     ('4','clf.score_samples()','Isolation Forest puntua el flow. score en (-1, 0). Actualiza _score_hist (deque 10 ultimos).'),
     ('5','detectar_http_abuse()','Contador de flows TCP:80 por IP en ventana 30s. >=50 => LIMIT, >=100 => BLOCK.'),
     ('6','detectar_brute_force()','Contador de intentos TCP:22 por IP en ventana 60s. >=5 => LIMIT, >=15 => BLOCK.'),
     ('7','Pre-alerta tendencia','Si score_medio (media de 10) < TAU_AVISO(-0.35) y flow actual es PERMIT: log TENDENCIA.'),
     ('8','decidir(score)','score > tau1(-0.4459): PERMIT | score > tau2(-0.6027): LIMIT | else: BLOCK.'),
     ('9','bloquear/limitar_ip()','SSH al servidor: sudo ipset add ppi_blocked/ppi_limited <IP> timeout 300.'),
     ('10','telegram_alerta_ip()','Envia alerta Telegram (dedup 300s por IP). Incluye score, byte_ratio, pkt_rate.')],
    [10,36,122])
pdf.h3('Constantes y umbrales del motor')
pdf.tabla(['Constante','Valor','Significado'],
    [('TAU1','-0.4459','Umbral PERMIT/LIMIT (Youden index)'),
     ('TAU2','-0.6027','Umbral LIMIT/BLOCK (FPR<=2%)'),
     ('TAU_AVISO','-0.35','Umbral pre-alerta de tendencia (score_medio deque 10)'),
     ('AVISO_MIN_FL','10','Minimo de flows en _score_hist para disparar pre-alerta'),
     ('HTTP_PORT','80','Puerto monitoreado por detector HTTP_ABUSE'),
     ('SSH_PORT','22','Puerto monitoreado por detector BruteForce'),
     ('HTTP_VENTANA_SEG','30','Ventana temporal para contar requests HTTP'),
     ('HTTP_UMBRAL_LIMIT','50','Requests/30s que activan LIMIT'),
     ('HTTP_UMBRAL_BLOCK','100','Requests/30s que activan BLOCK'),
     ('BF_VENTANA_SEG','60','Ventana temporal para contar intentos SSH'),
     ('BF_UMBRAL_LIMIT','5','Intentos/60s que activan LIMIT'),
     ('BF_UMBRAL_BLOCK','15','Intentos/60s que activan BLOCK'),
     ('TG_DEDUP_SEG','300','Segundos minimos entre alertas Telegram por la misma IP')],
    [30,20,118])
pdf.h3('Flujo de decision — ejemplo SYN Flood detectado')
pdf.box('EVENTO eve.json recibido:\n  src=192.168.0.100  dst=192.168.0.120:80  proto=TCP\n  pkts_toserver=1  bytes_toserver=44  bytes_toclient=0  duration=0.001s\n\nPASO 3 — Features extraidas:\n  pkt_rate=1000.0  byte_ratio=44.0  bytes_toclient=0  is_tcp=1  dest_port=80\n\nPASO 4 — Score IF: -0.6155  (< tau2=-0.6027 => decision: BLOCK)\n\nPASO 5 — HTTP_ABUSE: sin contador activo aun\nPASO 6 — BruteForce: port!=22, skip\n\nPASO 8 — decidir(-0.6155): BLOCK\nPASO 9 — _ssh("sudo ipset add ppi_blocked 192.168.0.100 timeout 300")\n\nLOG: WARNING | ANOMALIA | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP\n     score=-0.6155 grado=ALTA tipo=HTTP_ABUSE | BLOCK -> BLOCKED 192.168.0.100')
pdf.kpis([('Latencia media','34.5 ms',BLU),('Latencia P95','34.8 ms',BLU),('Throughput','29 flows/s',GRN),('Requisito','>= 500 ms',GRN)])
pdf.fig(G+'/f6_06_latencia_pipeline.png','Figura 9 — Distribucion de latencia del pipeline sobre 1000 flows medidos. P50=33ms, P95=34.8ms, max<50ms.',0.90)

# ── 8. F5 — CONTROL INLINE ───────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F5 — Control Inline, Pruebas de Integracion y Dashboard')
pdf.h3('Mecanismo de control con ipset/iptables')
pdf.p('El motor aplica las acciones BLOCK y LIMIT directamente en el kernel Linux del servidor (192.168.0.120) via SSH. No existe un proxy o capa intermedia — la accion tarda < 5ms adicionales al tiempo de decision.')
pdf.tabla(['Tipo','Set ipset','Regla iptables en servidor','Efecto en la red'],
    [('BLOCK','ppi_blocked (hash:ip, timeout=300s)','iptables -A INPUT -m set --match-set ppi_blocked src -j DROP','DROP total. Paquetes descartados silenciosamente. Timeout 300s (5 min), renovable.'),
     ('LIMIT','ppi_limited (hash:ip, timeout=300s)','iptables -A INPUT -m set --match-set ppi_limited src -m hashlimit --hashlimit-above 100/sec --hashlimit-mode srcip -j DROP','Rate limit a 100 pkt/s. Trafico legitimo pasa, ataque se degrada. Timeout 300s.'),
     ('UNBLOCK','Ninguno','ipset del ppi_blocked <IP>; ipset del ppi_limited <IP>','Restaura acceso completo inmediatamente.')],
    [14,40,70,44])
pdf.h3('enforce.sh — Control manual')
pdf.p('El script enforce.sh permite control manual independiente del motor para administracion o respuesta a incidentes:')
pdf.box('# Bloquear IP manualmente (timeout 60s)\nbash scripts/enforce.sh 192.168.0.100 BLOCK 60\n\n# Limitar IP (hashlimit 100pkt/s)\nbash scripts/enforce.sh 192.168.0.100 LIMIT 60\n\n# Desbloquear inmediatamente\nbash scripts/enforce.sh 192.168.0.100 UNBLOCK\n\n# Nota: enforce.sh actua SOLO sobre ipset. El motor NO llama a enforce.sh\n# — el motor llama directamente a bloquear_ip() -> _ssh("sudo ipset add...")')
pdf.h3('Pruebas de integracion T3-T5 (todas aprobadas)')
pdf.tabla(['Prueba','Descripcion','Resultado obtenido'],
    [('T3.1 — BLOCK manual','enforce.sh BLOCK + verificar ipset list','PASS: IP en ppi_blocked, timeout=300s activo'),
     ('T3.2 — LIMIT manual','enforce.sh LIMIT + ping flood + medir pkt/s','PASS: trafico limitado a <100pkt/s medido con tcpdump'),
     ('T3.3 — UNBLOCK','enforce.sh UNBLOCK + ping desde IP bloqueada','PASS: ping responde inmediatamente tras UNBLOCK'),
     ('T3.4 — Auto-expiry','BLOCK con timeout=5s + esperar 6s + ping','PASS: acceso restaurado automaticamente'),
     ('T4.1 — Dashboard web','GET http://192.168.0.110:8080/ desde Desktop','PASS: HTTP 200, pagina carga en 17ms'),
     ('T4.2 — SSE stream','EventSource /api/stream en DevTools','PASS: eventos push recibidos, sin polling'),
     ('T4.3 — API stats','GET /api/stats (JSON)','PASS: {flows, anomalias, bloqueados, latencia_media}'),
     ('T4.4 — API block','POST /api/block {"ip":"192.168.0.100"}','PASS: {"ok":true}, IP bloqueada via API web'),
     ('T5.1 — Motor restart','systemctl restart ppi-motor + flujo ataque','PASS: motor carga modelo y retoma deteccion en <8s')],
    [28,62,78])
pdf.h3('Dashboard web — componentes')
pdf.tabla(['Componente','Ruta','Tipo','Descripcion'],
    [('Panel principal','/ (GET)','HTML','KPIs en tiempo real: flows/min, anomalias, bloqueados, latencia'),
     ('Stream eventos','/ (SSE)','EventSource','Eventos push cada deteccion. Sin recargar pagina.'),
     ('API estadisticas','/api/stats (GET)','JSON','flows, anomalias, bf, http_abuse, bloqueados, limitados, latencia_media'),
     ('API stream','/api/stream (GET)','SSE','Mismo stream del panel, accesible por clientes externos'),
     ('API control','/api/block y /api/unblock (POST)','JSON','Control manual de IPs desde la interfaz web')],
    [26,30,18,94])

# ── 9. EXPERIMENTO COMPARATIVO ────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Experimento Comparativo — Seleccion de Modelo')
pdf.p('Previo a la validacion F6, se implementaron y evaluaron 7 modelos sobre el mismo conjunto de 611,712 flows (normal_holdout + todos los archivos anomalos del Grupo B). El objetivo fue justificar la eleccion de Isolation Forest como modelo de produccion.')
pdf.h3('Tabla 1 — Rendimiento predictivo (evaluacion offline uniforme)')
pdf.tabla(['Modelo','Paradigma','AUC-ROC','Recall','Precision','FPR','T.train','Escalable'],
    [('Isolation Forest','one-class','0.8998','99.40%','99.54%','20.47%','< 10 s','Si'),
     ('Autoencoder (AE)','one-class','0.9103','99.42%','99.42%','25.68%','115.6 s','Si'),
     ('One-Class SVM','one-class','0.9712','93.03%','91.20%','8.02%','0.6 s','Parcial'),
     ('LOF','one-class','0.8418','59.00%','91.04%','5.19%','0.3 s','No'),
     ('Random Forest (*)','supervisado','0.9997','99.86%','99.56%','0.40%','9.8 s','Si'),
     ('XGBoost (*)','supervisado','0.9995','99.86%','99.53%','0.42%','77.8 s','Si'),
     ('Decision Tree (*)','supervisado','0.9972','99.75%','99.42%','0.52%','0.1 s','Si')],
    [34,20,18,16,18,16,18,16])
pdf.p('(*) Modelos supervisados requieren etiquetas de ataque en entrenamiento. No son comparacion justa ni replicables en produccion real donde los ataques futuros son desconocidos.')
pdf.h3('Tabla 2 — Por que IF sobre AE (modelo con mayor AUC)')
pdf.tabla(['Criterio de seleccion','Isolation Forest','Autoencoder','Ventaja'],
    [('AUC-ROC global','0.8998','0.9103','AE +1.16%'),
     ('Recall @ tau1','99.40%','99.42%','Empate'),
     ('FPR @ tau1','20.47%','25.68%','IF mejor (5.21pp menos FP)'),
     ('Block% directo @ tau2','18.27%','54.62%','AE bloquea 3x mas directamente'),
     ('ITL Grupo C (trafico mixto)','9.8-100%','8.6-77.2%','IF conserva mas trafico legitimo'),
     ('Corridas F6 en vivo','40/40 validadas','0 corridas','IF UNICO certificado en produccion'),
     ('Disponibilidad F6','100% (40 corridas)','No medida','IF certificado'),
     ('ITL en F6 real','0% (40 corridas)','No medida','IF certificado'),
     ('Lead Time F6','61.92 s medido','No medido','IF certificado'),
     ('Tiempo de entrenamiento','< 10 s','115.6 s','IF 12x mas rapido'),
     ('Tamano modelo .pkl','2.5 MB','16 KB','AE mas ligero')],
    [56,30,28,54])
pdf.box('RAZON DE SELECCION: En un sistema IPS que aplica acciones reales (DROP de paquetes, rate-limit) sobre trafico de produccion, la validacion en vivo con disponibilidad certificada es el criterio determinante. IF es el UNICO modelo con 40 corridas de validacion formal (Disponibilidad=100%, ITL=0%). El AE solo fue evaluado offline — su comportamiento bajo carga real con trafico mixto no esta certificado. El AE queda documentado como propuesta de mejora futura: mayor Block% (54.6% vs 18.3%) sugiere mejor discriminacion en la zona de alta anomalia.')

# ── 10. F6 — VALIDACION ──────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F6 — Validacion del Sistema (40 Corridas)')
pdf.p('La validacion se ejecuto con f6_corridas.py en el sensor (192.168.0.110) el 2026-06-16. Todas las corridas duraron 300-317 segundos. Durante los grupos Mixto/Reeval/Final, el atacante Kali lanza el ataque 15 segundos despues de iniciada la corrida.')
pdf.h3('Grupos de corridas y metodologia')
pdf.tabla(['Grupo','Corridas','Escenario','Metodologia','Hipotesis validada'],
    [('Normal','1-10','Solo trafico Desktop normal (curl+ssh)','Motor activo, Kali inactiva','FP=0: ninguna IP normal bloqueada (ITL=0%, flows_anom=0)'),
     ('Mixto','11-20','Normal + ataque simultaneo desde Kali','Traficos coexistentes, rotacion syn/portscan/udp/http cada corrida','Sistema detecta ataque (corrida 11) sin afectar trafico normal'),
     ('Reeval','21-30','Normal + ataque, IP Kali ya bloqueada','Kali sigue atacando pero ipset la bloquea antes de que llege al servidor','IP contenida: flows_anom=0, servidor disponible, latencia estable'),
     ('Final','31-40','Normal + ataque, confirmacion de contencion','4 tipos de ataque ciclicos: syn/portscan/udp/http','Disponibilidad=100%, ITL=0% en todas las corridas de confirmacion')],
    [16,16,42,52,42])
pdf.h3('Detalle corrida 11 — Unico evento de deteccion (SYN Flood)')
pdf.box('TIMELINE CORRIDA 11 (2026-06-16, 10:16:43 a 10:21:59, 316 segundos):\n\n  t=  0s  Inicio corrida. Desktop genera curl/ssh normal al servidor.\n  t= 15s  Kali lanza: hping3 -S -p 80 -i u5000 192.168.0.120\n           Suricata comienza a registrar flows de SYN sin ACK.\n\n  t= 62s  MOTOR DETECTA:\n           SOSPECHOSO | src=192.168.0.100 dst=192.168.0.120:80 proto=TCP\n           score=-0.5045 grado=BAJA tipo=BAJA_ANOMALIA | LIMIT\n           => SSH al servidor: ipset add ppi_limited 192.168.0.100\n\n  t= 63s  MOTOR ESCALA:\n           HTTP-ABUSE | src=192.168.0.100 requests=100/30s | BLOCK\n           => SSH al servidor: ipset add ppi_blocked 192.168.0.100\n\n  t=  0-316s  nginx responde HTTP 200 durante TODO el ataque (disponibilidad=1)\n  t=316s  Fin corrida. ITL=0.0% (ningun flow normal afectado).\n\n  Lead Time = 61.92 s  |  MTTA = 61.92 s  |  MTTC = 61.92 s\n  TIE = 100%  |  flows_anom = 2  |  bloqueados = 1  |  limitados = 1')
pdf.h3('Resultados completos por corrida — 40 corridas')
pdf.tabla(['C#','Grupo','Escenario','Hora','Dur.','Disp.','flows_N','flows_A','Bloq.','Lat.ms','Lead_s'],
    [('1','normal','normal','09:17','300s','1','0','0','0','0','—'),
     ('2','normal','normal','09:23','300s','1','0','0','0','0','—'),
     ('3','normal','normal','09:29','300s','1','0','0','0','0','—'),
     ('4','normal','normal','09:35','300s','1','0','0','0','0','—'),
     ('5','normal','normal','09:41','300s','1','0','0','0','0','—'),
     ('6','normal','normal','09:47','300s','1','0','0','0','0','—'),
     ('7','normal','normal','09:53','300s','1','0','0','0','0','—'),
     ('8','normal','normal','09:59','300s','1','0','0','0','0','—'),
     ('9','normal','normal','10:05','300s','1','0','0','0','0','—'),
     ('10','normal','normal','10:11','300s','1','0','0','0','0','—'),
     ('11','mixto','synflood','10:16','316s','1','6,500','2','1','15,400','61.92'),
     ('12','mixto','portscan','10:23','316s','1','17,000','0','0','16,778','—'),
     ('13','mixto','udpflood','10:29','316s','1','27,500','0','0','16,882','—'),
     ('14','mixto','httpabuse','10:35','316s','1','38,000','0','0','17,294','—'),
     ('15','mixto','synflood','10:41','316s','1','48,500','0','0','17,000','—'),
     ('16','mixto','portscan','10:48','316s','1','59,000','0','0','16,611','—'),
     ('17','mixto','udpflood','10:54','316s','1','70,000','0','0','16,444','—'),
     ('18','mixto','httpabuse','11:00','316s','1','81,000','0','0','16,778','—'),
     ('19','mixto','synflood','11:07','316s','1','91,500','0','0','16,444','—'),
     ('20','mixto','portscan','11:13','316s','1','102,500','0','0','16,333','—'),
     ('21','reeval','synflood','11:18','316s','1','111,500','0','0','16,444','—'),
     ('22','reeval','portscan','11:24','316s','1','122,500','0','0','16,500','—'),
     ('23','reeval','udpflood','11:31','316s','1','133,000','0','0','16,611','—'),
     ('24','reeval','httpabuse','11:37','316s','1','143,500','0','0','17,176','—'),
     ('25','reeval','synflood','11:43','316s','1','154,000','0','0','16,824','—'),
     ('26','reeval','portscan','11:50','316s','1','165,000','0','0','16,833','—'),
     ('27','reeval','udpflood','11:56','316s','1','175,500','0','0','16,889','—'),
     ('28','reeval','httpabuse','12:02','316s','1','185,500','0','0','17,294','—'),
     ('29','reeval','synflood','12:08','316s','1','196,500','0','0','16,444','—'),
     ('30','reeval','portscan','12:15','316s','1','207,500','0','0','16,278','—'),
     ('31','final','synflood','12:20','316s','1','216,500','0','0','16,444','—'),
     ('32','final','portscan','12:26','316s','1','227,500','0','0','16,333','—'),
     ('33','final','udpflood','12:33','316s','1','238,500','0','0','16,278','—'),
     ('34','final','httpabuse','12:39','317s','1','249,000','0','0','16,889','—'),
     ('35','final','synflood','12:45','316s','1','259,500','0','0','16,588','—'),
     ('36','final','portscan','12:52','316s','1','270,500','0','0','16,611','—'),
     ('37','final','udpflood','12:58','316s','1','281,000','0','0','16,778','—'),
     ('38','final','httpabuse','13:04','316s','1','291,500','0','0','17,294','—'),
     ('39','final','synflood','13:10','316s','1','302,000','0','0','17,000','—'),
     ('40','final','portscan','13:17','316s','1','312,500','0','0','16,833','—')],
    [8,14,20,14,14,10,16,14,10,16,14])
pdf.p('Nota: flows_N = acumulado total procesado desde inicio de F6. Corridas 12-40: flows_anom=0 porque la IP 192.168.0.100 permanece bloqueada en ipset tras corrida 11 — el servidor rechaza sus paquetes antes de que generen flows completos en Suricata.')

# ── 11. RESULTADOS ────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Resultados Principales y Discusion')
pdf.kpis([('Disponibilidad','100%',GRN),('ITL Global','0%',GRN),('Lead Time','61.9 s',BLU),('Latencia P95','34.8 ms',BLU),('AUC-ROC','0.8998',BLU),('F1-Score','0.9947',GRN)])
pdf.h3('Resultado 1 — Disponibilidad 100% en las 40 corridas')
pdf.p('El servidor nginx (192.168.0.120:80) respondio HTTP 200 en todas las corridas incluyendo la corrida 11 durante el SYN Flood activo. La accion BLOCK (ipset DROP) se ejecuto en t=63s, conteniendo el ataque antes de que pudiera saturar los recursos del servidor.')
pdf.fig(G+'/f6_01_disponibilidad.png','Figura 10 — Disponibilidad binaria en las 40 corridas. 40/40 = 100%. Requisito >= 99% CUMPLE.',0.90)
pdf.h3('Resultado 2 — ITL=0% (impacto en trafico legitimo nulo)')
pdf.p('Ninguna IP de trafico normal (Desktop 192.168.0.20) fue bloqueada o limitada en ninguna de las 40 corridas. Esto valida el funcionamiento correcto de la whitelist y confirma que el FPR del modelo no impacta operacionalmente al estar las IPs internas protegidas.')
pdf.fig(G+'/f6_04_itl.png','Figura 11 — ITL=0% en las 40 corridas. Ninguna corrida reporto impacto en trafico legitimo. Requisito ITL=0% CUMPLE.',0.90)
pdf.add_page()
pdf.h3('Resultado 3 — Deteccion en corrida 11 (Lead Time = 61.92 s)')
pdf.p('Solo la corrida 11 genero flows_anom=2 (el SYN flood). El sistema detecto en t=62s (LIMIT) y escalo en t=63s (BLOCK). Las corridas 12-40 muestran flows_anom=0 porque la IP de Kali permanecio bloqueada en ipset (timeout 300s renovado por el motor).')
pdf.fig(G+'/f6_02_flows_anomalos.png','Figura 12 — Flows anomalos por corrida. Solo corrida 11 muestra flows_anom=2. El resto: 0 (IP contenida).',0.90)
pdf.fig(G+'/f6_03_timeline_deteccion.png','Figura 13 — Timeline de corrida 11: LIMIT en t=62s, BLOCK en t=63s. Servidor disponible en todo momento.',0.90)
pdf.add_page()
pdf.h3('Resultado 4 — Latencia del pipeline P95=34.8 ms')
pdf.p('La latencia de decision (extract_features + scaler.transform + clf.score_samples + decision) se midio sobre 1000 flows reales. P50=33ms, P95=34.8ms, maximo < 50ms. El requisito de < 500ms se cumple con margen de seguridad de 14x.')
pdf.fig(G+'/f6_05_flujos_acumulados.png','Figura 14 — Flujos acumulados procesados: 0 a 312,500 al finalizar la corrida 40. Motor estable durante 7+ horas.',0.88)
pdf.h3('Resultado 5 — Comparacion de cumplimiento de requisitos')
pdf.tabla(['Requisito','Metrica','Objetivo','Obtenido','Estado','Margen'],
    [('Latencia pipeline','P95','< 500 ms','34.8 ms','CUMPLE','14.4x mejor'),
     ('Disponibilidad servicio','Promedio 40 corridas','>= 99%','100% (40/40)','CUMPLE','+1pp'),
     ('Impacto trafico legitimo','ITL en 40 corridas','= 0%','0% (40/40)','CUMPLE','exacto'),
     ('Precision deteccion','@ umbral tau1','>= 95%','99.54%','CUMPLE','+4.54pp'),
     ('Recall deteccion','@ umbral tau1','>= 80%','99.40%','CUMPLE','+19.40pp'),
     ('AUC-ROC modelo','Curva ROC completa','>= 0.85','0.8998','CUMPLE','+0.05pp'),
     ('Lead Time deteccion','Corrida 11 SYN flood','< 120 s','61.92 s','CUMPLE','48.1% del limite'),
     ('Flows procesados','Total corridas 1-40','>= 10,000','312,500','CUMPLE','31x objetivo')],
    [40,34,22,22,18,32])
pdf.fig(G+'/f6_07_panel_resumen.png','Figura 15 — Panel resumen F6: todas las metricas clave en las 40 corridas. Verde=CUMPLE en todos los indicadores.',0.95)

# ── 12. MODULO PREDICTOR TEMPORAL — XGBOOST ──────────────────────────────────
pdf.add_page(); pdf.h1('Modulo Predictor Temporal -- XGBoost')
pdf.p('El modulo predictor complementa al Isolation Forest con capacidad de anticipacion: mientras IF reacciona flow a flow (decision en ~34.8 ms por flow), el predictor estima la probabilidad P(ataque en los proximos 60s) basandose en el ritmo al que el motor acumula flows. Los dos motores corren en paralelo; el predictor no interfiere con la latencia del motor principal.')

pdf.h2('Sennal predictiva -- gap entre estadisticas del motor')
pdf.p('El motor_decision.py escribe una linea de estadisticas cada 500 flows procesados. El tiempo entre dos lineas consecutivas (gap) refleja la tasa de trafico: bajo ataque intenso (ab -n 3000 -c 150), 500 flows llegan en ~17s; con trafico normal del Desktop, el mismo umbral tarda ~174s. Esta diferencia de 10x es la sennal central del predictor.')
pdf.tabla(['Estado de red','Gap tipico entre stats','Flujos/min estimados','Interpretacion'],
    [('Normal (Desktop whitelisted)','~174 segundos','~173','Actividad baja — sin ataque'),
     ('Calentamiento moderado (ab c=20)','~60 segundos','~500','Actividad media'),
     ('Ataque intenso (ab -n 3000 c=150)','~17 segundos','~1,760','Alta intensidad -- ALERTA inminente')],
    [52,36,32,50])

pdf.h2('Comparacion de modelos -- seleccion de XGBoost')
pdf.p('Se evaluaron tres modelos temporales sobre 11,376 observaciones extraidas de motor_decision.log (split 80/20 cronologico por posicion de fila; corte en 2026-06-18 18:19). XGBoost obtuvo el mejor AUC-ROC y fue seleccionado para produccion.')
pdf.tabla(['Modelo','AUC-ROC test','Observaciones de seleccion'],
    [('ARIMA (univariado)','0.50','Solo usa gap actual -- equivale a azar; no captura lags'),
     ('Random Forest','0.48','Inferior a ARIMA con este tamano de conjunto y desbalance'),
     ('XGBoost (ELEGIDO)','0.58','Mejor AUC; scale_pos_weight corrige desbalance; early stopping evita overfitting')],
    [40,26,104])
pdf.box('Nota sobre AUC=0.58: el conjunto de test proviene de sesiones de ataque continuas en laboratorio (98.5% muestras positivas). El AUC bajo refleja la dificultad de discriminar DENTRO de una sesion de ataque ya activa, no la capacidad de detectar el inicio del ataque. Las corridas de validacion P4-P5 demuestran deteccion efectiva (P=81-83%) en condiciones reales.')
pdf.fig(GP+'/roc_comparacion.png','Figura 16 -- Curvas ROC comparativas: ARIMA (AUC=0.50), Random Forest (0.48), XGBoost (0.58). Test set contiene 98.5% muestras positivas (sesiones de ataque continuo en laboratorio).',0.75)

pdf.h2('Features del modelo predictor (11 features)')
pdf.tabla(['Feature','Descripcion','Normal / Ataque'],
    [('gap','Seg. desde ultima linea de estadisticas','~174s / ~17s'),
     ('gap_lag1','Gap de la estadistica anterior','~174s / ~17s'),
     ('gap_lag2 / lag3','Gaps de 2 y 3 estadisticas atras','~174s / ~17s'),
     ('gap_mean5','Promedio de los 5 gaps mas recientes','alto / bajo'),
     ('gap_std5','Desv. estandar de los 5 gaps','variable / baja (ataque estable)'),
     ('delta_gap','Cambio: gap - gap_lag1','~0 / negativo al inicio del ataque'),
     ('delta_gap2','Cambio de segundo orden del gap','~0 / oscilante'),
     ('anom_rate','Fraccion de anomalias en ventana del motor','baja / alta'),
     ('block_rate','Fraccion de IPs bloqueadas actualmente','0 / creciente'),
     ('time_of_day','Hora del dia en horas decimales','— / —')],
    [28,88,54])

pdf.add_page()
pdf.h2('Umbrales de decision del predictor')
pdf.tabla(['Nivel','Condicion','Salida en log','Accion recomendada'],
    [('OK','P < 0.40','INFO OK','Sin accion -- trafico normal'),
     ('RIESGO-MEDIO','0.40 <= P < 0.70','INFO RIESGO-MEDIO','Observacion -- posible anomalia'),
     ('ALERTA-PREDICTIVA','P >= 0.70','WARNING ALERTA-PREDICTIVA','Ataque inminente anticipado -- verificar motor IF')],
    [34,28,42,66])
pdf.box('Deduplicacion: si la ultima ALERTA fue hace menos de 5 minutos, el predictor registra RIESGO-ALTO (dedup) en lugar de nueva ALERTA. Evita spam de alertas durante ataques sostenidos. El dashboard web muestra el nivel de riesgo en tiempo real via SSE.')

pdf.h2('Corridas de validacion del predictor (P4-P10)')
pdf.tabla(['Corrida','Tipo','Resultado','P%','Feature top','Observacion'],
    [('P4','Ataque','ALERTA-PREDICTIVA (VP)','81.43%','gap=23s','Deteccion a 02:43:49, ~2 min tras inicio ataque'),
     ('P5','Ataque','ALERTA-PREDICTIVA (VP)','83.46%','gap_mean5=62.4','Deteccion a 02:48:49, ~2 min tras inicio ataque'),
     ('P6','Normal','FP residual post-ataque','83.09%','lag1=17s','lag1 de P5 en memoria del proceso -- artefacto de sesion'),
     ('P7','Normal','Sin alerta (VN)','--','--','Correcto: historial limpio tras reinicio servicio'),
     ('P8','Normal','Sin alerta (VN)','--','--','Correcto: historial limpio tras reinicio servicio'),
     ('P9','Normal','Sin alerta (VN)','--','--','Correcto: historial limpio tras reinicio servicio'),
     ('P10','Normal','Sin alerta (VN)','--','--','Correcto: historial limpio tras reinicio servicio')],
    [14,16,34,12,28,66])
pdf.kpis([('TPR (ataques)','2/2 = 100%',GRN),('FPR (normal+reinicio)','0/4 = 0%',GRN),('P media ataque','82.4%',BLU),('AUC predictor','0.58',YEL)])
pdf.box('P6 (falso positivo): ocurre SOLO cuando el proceso predictor retiene en memoria el lag1=17s del ataque anterior. Mitigacion implementada: reinicio de ppi-predictor.service entre corridas. En produccion: cooldown automatico de 5-10 min tras evento BLOCK, o reinicio del servicio al limpiar ipset.')
pdf.fig(GP+'/shap_predictor.png','Figura 17 -- Importancia SHAP del predictor XGBoost: gap y gap_lag1 son los predictores dominantes, confirmando que el ritmo de llegada de flows es la sennal central del modulo predictor.',0.75)

pdf.h2('Arquitectura de integracion -- flujo completo')
pdf.box('Suricata (eve.json) --> motor_decision.py: IF score por flow [34.8ms] --> PERMIT / LIMIT / BLOCK + stats_line/500flows --> predictor.py: gap features [<1ms] --> P(ataque/60s) --> ALERTA-PREDICTIVA en predictor.log + SSE dashboard_web.py. Los dos motores son procesos independientes (ppi-motor.service y ppi-predictor.service). IF actua sobre cada flow individual; el predictor actua sobre la tasa agregada. Sin interferencia de latencia.')
pdf.tabla(['Componente','Servicio systemd','Latencia','Sennal de entrada','Salida'],
    [('Isolation Forest','ppi-motor.service','~34.8 ms/flow','Cada flow de eve.json','PERMIT/LIMIT/BLOCK + stats/500 flows'),
     ('Predictor XGBoost','ppi-predictor.service','< 1 ms','Gap entre stats lines','ALERTA-PREDICTIVA si P >= 0.70'),
     ('Dashboard web','ppi-dashboard.service','SSE en tiempo real','motor.log + predictor.log','Panel HTTP :8080 con gauge de riesgo')],
    [34,34,20,46,36])

# ── 13. CONCLUSIONES ─────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Conclusiones')
pdf.h3('1. Sistema de deteccion temprana funcional y validado')
pdf.p('Se implemento un sistema end-to-end que va desde la captura con Suricata hasta el control inline con ipset/iptables. La validacion con 40 corridas demostro que el sistema cumple simultaneamente los tres indicadores criticos: Disponibilidad=100%, ITL=0%, Latencia P95=34.8ms.')
pdf.h3('2. Isolation Forest eficaz en paradigma one-class')
pdf.p('El modelo IF (AUC=0.8998, Recall=99.40%, F1=0.9947) fue entrenado EXCLUSIVAMENTE con trafico normal — sin necesidad de muestras etiquetadas de ataques. Esto es fundamental para entornos reales donde los ataques futuros son desconocidos [Liu 2008, Chandola 2009]. Los detectores heuristicos (HTTP_ABUSE, BruteForce) complementan el IF elevando el recall efectivo a ~100% para esos tipos especificos.')
pdf.h3('3. Lead Time de 61.92 s — estructura del sistema y oportunidades de mejora')
pdf.p('El Lead Time esta determinado principalmente por el timeout TCP de Suricata (~60s): el motor no puede decidir hasta que el flow TCP se cierra. Los detectores heuristicos actuan sobre eventos individuales (no esperan cierre del flow), logrando deteccion mas rapida para BruteForce y HTTP_ABUSE. Como mejora futura: analisis de paquetes individuales (sin esperar flow) reduciria el lead time a < 5s.')
pdf.h3('4. Pipeline reproducible y escalable')
pdf.p('Los 6 scripts (F2-F6) son deterministas con semillas fijas. El sistema puede recalibrarse con nuevos datos ejecutando la cadena completa. sklearn 1.9.0 esta fijado en el venv del sensor para garantizar reproducibilidad exacta del modelo.')
pdf.h3('5. Justificacion metodologica vs alternativas')
pdf.p('El experimento comparativo evaluo 7 modelos. IF fue elegido sobre AE (AUC superior 0.9103) porque es el UNICO modelo validado en produccion real con 40 corridas certificadas. El AE queda como propuesta de mejora futura con mayor capacidad de bloqueo directo (54.6% vs 18.3% en Block%).')
pdf.tabla(['Requisito','Objetivo','Obtenido','Estado'],
    [('Latencia P95','< 500 ms','34.8 ms','CUMPLE'),
     ('Disponibilidad','>= 99%','100% (40/40)','CUMPLE'),
     ('ITL','= 0%','0% (40/40)','CUMPLE'),
     ('AUC-ROC','>= 0.85','0.8998','CUMPLE'),
     ('Lead Time','< 120 s','61.92 s','CUMPLE'),
     ('Precision','>= 95%','99.54%','CUMPLE'),
     ('Recall','>= 80%','99.40%','CUMPLE'),
     ('Flows procesados','>= 10,000','312,500','CUMPLE')],[44,28,30,26])

# ── 13. REFERENCIAS ──────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Referencias Bibliograficas')
refs = [
    ('Liu, F.T., Ting, K.M., Zhou, Z.H.','Isolation Forest','Proc. 8th IEEE Int. Conf. on Data Mining (ICDM 2008), pp. 413-422','2008','10.1109/ICDM.2008.17'),
    ('Liu, F.T., Ting, K.M., Zhou, Z.H.','Isolation-Based Anomaly Detection','ACM Trans. Knowledge Discovery from Data (TKDD), 6(1), Art. 3','2012','10.1145/2133360.2133363'),
    ('Chandola, V., Banerjee, A., Kumar, V.','Anomaly Detection: A Survey','ACM Computing Surveys, 41(3), Art. 15. (>15,000 citas)','2009','10.1145/1541880.1541882'),
    ('Scarfone, K., Mell, P.','Guide to Intrusion Detection and Prevention Systems (IDPS), NIST SP 800-94','National Institute of Standards and Technology','2007','csrc.nist.gov/publications/detail/sp/800-94/final'),
    ('Garcia-Teodoro, P. et al.','Anomaly-based network intrusion detection: Techniques, systems and challenges','Computers & Security, 28(1-2), pp. 18-28','2009','10.1016/j.cose.2008.08.003'),
    ('Fawcett, T.','An Introduction to ROC Analysis','Pattern Recognition Letters, 27(8), pp. 861-874','2006','10.1016/j.patrec.2005.10.010'),
    ('Mann, H.B., Whitney, D.R.','On a Test of Whether One of Two Random Variables is Stochastically Larger Than the Other','Annals of Mathematical Statistics, 18(1), pp. 50-60','1947','10.1214/aoms/1177730491'),
    ('Youden, W.J.','Index for Rating Diagnostic Tests','Cancer, 3(1), pp. 32-35','1950','10.1002/1097-0142(1950)3:1<32::AID-CNCR2820030106>3.0.CO;2-3'),
    ('Pedregosa, F. et al.','Scikit-learn: Machine Learning in Python','J. Machine Learning Research (JMLR), 12, pp. 2825-2830','2011','scikit-learn.org'),
    ('Powers, D.M.W.','Evaluation: From Precision, Recall and F-Measure to ROC, Informedness, Markedness','J. Machine Learning Technologies, 2(1), pp. 37-63','2011','hdl.handle.net/2328/27165'),
    ('Buczak, A.L., Guven, E.','A Survey of Data Mining and ML Methods for Cyber Security Intrusion Detection','IEEE Comm. Surveys & Tutorials, 18(2), pp. 1153-1176','2016','10.1109/COMST.2015.2494502'),
    ('OISF','Suricata 7.0 User Guide — Flow Timeouts Configuration','Open Information Security Foundation','2023','docs.suricata.io/en/latest/configuration/suricata-yaml.html'),
    ('Sommer, R., Paxson, V.','Outside the Closed World: On Using Machine Learning for Network Intrusion Detection','IEEE Symposium on Security and Privacy, pp. 305-316','2010','10.1109/SP.2010.25'),
]
for i,(a,t,p,y,doi) in enumerate(refs,1):
    if pdf.get_y() > pdf.h - pdf.b_margin - 25: pdf.add_page()
    pdf.set_font('Helvetica','B',9); pdf.set_text_color(*BLU)
    pdf.cell(10,5.5,f'[{i}]',**INL)
    pdf.set_text_color(*DRK)
    pdf.set_font('Helvetica','B',9)
    pdf.multi_cell(0,5.5,N(f'{a} ({y}). {t}.'))
    pdf.set_font('Helvetica','',8.5); pdf.set_text_color(*GRY)
    pdf.set_x(pdf.l_margin+10)
    pdf.multi_cell(0,5,N(f'{p}. DOI/URL: {doi}'))
    pdf.set_text_color(0,0,0); pdf.ln(2)

# ── ANEXO A ──────────────────────────────────────────────────────────────────
pdf.add_page()
pdf.set_fill_color(*DRK); pdf.set_text_color(*WHT)
pdf.set_font('Helvetica','B',13)
pdf.cell(0,11,'  Anexo A — Estructura del Repositorio y Artefactos',fill=True,**NL)
pdf.set_text_color(0,0,0); pdf.ln(4)
pdf.p('Repositorio: https://github.com/marksato13/PRODUCTO-_INGENIERL\nUbicacion en sensor: /home/m4rk/ppi-surikata-producto/')
pdf.tabla(['Artefacto / Ruta','Fase','Descripcion'],
    [('scripts/fase3_entrenar.py','F3','Entrena IF sobre *_normal_*.gz. Produce isolation_forest.pkl, scaler.pkl, normal_holdout.csv'),
     ('scripts/fase3_evaluar.py','F3','Evalua sobre holdout+anom. Produce metricas_offline.txt, auc_roc.png'),
     ('scripts/auc_por_escenario.py','F3','AUC-ROC individual por cada archivo .gz del Grupo B'),
     ('scripts/motor_decision.py','F4+F5','Motor tiempo real (~620 lineas). Tail eve.json, IF scoring, ipset control, Telegram, dashboard SSE'),
     ('scripts/enforce.sh','F5','Control manual BLOCK/LIMIT/UNBLOCK. Independiente del motor.'),
     ('scripts/dashboard_web.py','F5','Servidor Flask+SSE en :8080. Panel web, /api/stats, /api/stream, /api/block'),
     ('scripts/f6_corridas.py','F6','Orquestador 40 corridas: lanza escenarios, mide metricas, genera CSV y graficas'),
     ('scripts/generar_graficas_f6.py','F6','Genera 7 figuras PNG 300 DPI desde resultados_f6_completo.csv'),
     ('models/isolation_forest.pkl','F3','Modelo IF serializado. sklearn 1.9.0. n=300, contamination=0.05'),
     ('models/scaler.pkl','F3','StandardScaler fit sobre el 80% de flows normales (53,708 flows)'),
     ('models/features.csv','F3','Lista de 14 features en orden exacto — sincronizadas entre entrenar y motor'),
     ('data/normal_holdout.csv','F3','20% de flows normales (13,427). Nunca visto por el modelo durante fit().'),
     ('data/raw/*.gz','F2','47 archivos eve.json.gz: 28 normal, 13 anom, 6 mixto'),
     ('results/metricas_offline.txt','F3','Fuente canonica: AUC=0.8998, tau1=-0.4459, tau2=-0.6027, Precision, Recall, F1'),
     ('results/resultados_f6_completo.csv','F6','40 corridas x 18 metricas: disponibilidad, flows, lead_time, latencia, ITL...'),
     ('results/graficas_f6/ (7 PNG)','F6','f6_01 a f6_07: disponibilidad, flows_anom, timeline, ITL, acumulados, latencia, panel'),
     ('results/eda/ (6 PNG)','EDA','eda_01 a eda_06: distribuciones, protocolo, boxplots, correlacion, puertos, stats (300 DPI)'),
     ('results/ae/comparacion/','Comp.','Resultados IF vs AE por escenario. resumen_ae_vs_if.txt con AUC por archivo.'),
     ('docs/ppi_documentacion/','Todas','13 archivos MD: 2 por fase (diagrama drawio + especificacion tecnica)'),
     ('docs/respuestas_asesor/','Defensa','06_REFERENCIAS_FORMALES.md, 07_DEFENSA_PREGUNTAS_FORMALES.md (14 preguntas)')],
    [62,14,92])

pdf.output(OUT)
print(f'OK: {OUT}')
import os; print(f'Tamano: {os.path.getsize(OUT)//1024} KB')
