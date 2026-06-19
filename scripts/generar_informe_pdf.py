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

BLU=(41,128,185); LBLU=(214,234,248)
GRN=(39,174,96);  LGRN=(213,232,212)
RED=(192,57,43);  LRED=(250,219,216)
YEL=(243,156,18)
GRY=(127,140,141); DRK=(44,62,80)
WHT=(255,255,255)

NL = dict(new_x=XPos.LMARGIN, new_y=YPos.NEXT)
INL= dict(new_x=XPos.RIGHT,   new_y=YPos.TOP)

class PDF(FPDF):
    def normalize_text(self, txt):
        txt = N(str(txt))
        return super().normalize_text(txt)

    sec = 0
    def header(self):
        if self.page_no()==1: return
        self.set_font('Helvetica','I',8); self.set_text_color(*GRY)
        self.cell(0,7,'Aprendizaje Automatico para Deteccion de Anomalias en Red | PPI UPeU 2026',**NL)
        self.set_text_color(0,0,0)
    def footer(self):
        self.set_y(-14); self.set_font('Helvetica','I',8)
        self.set_text_color(*GRY)
        self.cell(0,8,f'Pagina {self.page_no()}',align='C',**NL)
        self.set_text_color(0,0,0)

    def h1(self,txt):
        PDF.sec+=1; self.ln(4)
        self.set_fill_color(*BLU); self.set_text_color(*WHT)
        self.set_font('Helvetica','B',14)
        self.cell(0,10,f'  {PDF.sec}.  {txt}',fill=True,**NL)
        self.set_text_color(0,0,0); self.ln(3)

    def h2(self,txt):
        self.ln(3); self.set_font('Helvetica','B',11)
        self.set_text_color(*BLU); self.cell(0,8,txt,**NL)
        self.set_draw_color(*BLU)
        self.line(self.l_margin,self.get_y(),self.w-self.r_margin,self.get_y())
        self.set_draw_color(0,0,0); self.set_text_color(0,0,0); self.ln(2)

    def h3(self,txt):
        self.ln(2); self.set_font('Helvetica','B',10)
        self.cell(0,7,txt,**NL); self.ln(1)

    def p(self,txt):
        self.set_font('Helvetica','',10)
        self.multi_cell(0,5.5,N(txt),align='J'); self.ln(1)

    def li(self,txt):
        self.set_font('Helvetica','',10)
        pw = self.w - self.l_margin - self.r_margin
        y0 = self.get_y()
        self.set_xy(self.l_margin+1, y0)
        self.cell(7,5.5,'- ',**INL)
        self.set_xy(self.l_margin+8, y0)
        self.multi_cell(pw-8,5.5,N(txt))

    def cap(self,txt):
        self.set_font('Helvetica','I',9); self.set_text_color(*GRY)
        self.cell(0,5,N(txt),**NL); self.set_text_color(0,0,0); self.ln(3)

    def fig(self,path,cap,wp=0.88):
        if not os.path.exists(path): return
        pw = self.w-self.l_margin-self.r_margin
        iw = pw*wp
        if self.get_y()>self.h-self.b_margin-70: self.add_page()
        self.image(path,x=(self.w-iw)/2,w=iw)
        self.cap(cap)

    def kpis(self,items):
        pw=self.w-self.l_margin-self.r_margin; cw=pw/len(items)
        y0=self.get_y()
        for i,(lbl,val,col) in enumerate(items):
            self.set_xy(self.l_margin+i*cw,y0)
            self.set_fill_color(*col); self.set_text_color(*WHT)
            self.set_font('Helvetica','B',13)
            self.cell(cw-1,9,val,fill=True,align='C',**INL)
        self.set_xy(self.l_margin,y0+9)
        for i,(lbl,val,col) in enumerate(items):
            self.set_xy(self.l_margin+i*cw,self.get_y())
            self.set_fill_color(240,245,255); self.set_text_color(*DRK)
            self.set_font('Helvetica','',8)
            self.cell(cw-1,6,lbl,border=1,fill=True,align='C',**INL)
        self.set_text_color(0,0,0); self.set_fill_color(*WHT); self.ln(10)

    def tabla(self,hdrs,rows,widths=None):
        pw=self.w-self.l_margin-self.r_margin
        if widths is None: widths=[pw/len(hdrs)]*len(hdrs)
        self.set_font('Helvetica','B',9)
        self.set_fill_color(*BLU); self.set_text_color(*WHT)
        for h,w in zip(hdrs,widths):
            self.cell(w,7,N(str(h)),border=1,fill=True,align='C',**INL)
        self.set_xy(self.l_margin,self.get_y()+7); self.set_text_color(0,0,0)
        for ri,row in enumerate(rows):
            if self.get_y()>self.h-self.b_margin-15: self.add_page()
            self.set_font('Helvetica','',9)
            self.set_fill_color(*(245,245,245) if ri%2==0 else WHT)
            for c,w in zip(row,widths):
                self.cell(w,6,N(str(c)),border=1,fill=True,align='C',**INL)
            self.set_xy(self.l_margin,self.get_y()+6)
        self.set_fill_color(*WHT); self.ln(3)

    def box(self,txt,fc=LBLU,bc=BLU):
        self.set_fill_color(*fc); self.set_draw_color(*bc)
        self.set_font('Helvetica','',10)
        self.multi_cell(0,5.5,N(txt),border=1,fill=True,align='J')
        self.set_draw_color(0,0,0); self.ln(3)

    def hr(self):
        self.set_draw_color(*GRY)
        self.line(self.l_margin,self.get_y(),self.w-self.r_margin,self.get_y())
        self.set_draw_color(0,0,0); self.ln(3)

# ─────────────────────────────────────────────────────────────────────────────
pdf = PDF('P','mm','A4')
pdf.set_auto_page_break(True,20); pdf.set_margins(25,22,20)
pdf.add_page()

# ── PORTADA ──────────────────────────────────────────────────────────────────
pdf.set_fill_color(*BLU); pdf.rect(0,0,210,44,style='F')
pdf.set_fill_color(*DRK); pdf.rect(0,44,210,7,style='F')
pdf.set_xy(25,10); pdf.set_font('Helvetica','B',16); pdf.set_text_color(*WHT)
pdf.cell(0,8,'UNIVERSIDAD PERUANA UNION',align='C',**NL)
pdf.set_xy(25,19); pdf.set_font('Helvetica','',11)
pdf.cell(0,7,'Facultad de Ingenieria y Arquitectura',align='C',**NL)
pdf.set_xy(25,27); pdf.set_font('Helvetica','I',10)
pdf.cell(0,7,'Escuela Profesional de Ingenieria de Sistemas',align='C',**NL)
pdf.set_text_color(0,0,0); pdf.ln(28)

pdf.set_font('Helvetica','B',9); pdf.set_text_color(*GRY)
pdf.cell(0,6,'PROYECTO PRODUCTIVO DE INVESTIGACION (PPI)',align='C',**NL)
pdf.ln(4); pdf.set_font('Helvetica','B',17); pdf.set_text_color(*DRK)
pdf.multi_cell(0,9,'Sistema de Deteccion Temprana de Comportamientos Anomalos en Redes de Datos',align='C')
pdf.ln(2); pdf.set_font('Helvetica','B',12); pdf.set_text_color(*BLU)
pdf.multi_cell(0,7,'mediante Aprendizaje Automatico y un Mecanismo de Control en Tiempo Real',align='C')
pdf.set_text_color(0,0,0); pdf.ln(8); pdf.hr()

for lbl,val in [('Estudiante 1:','Ruben Mark Salazar Tocas'),
                ('Estudiante 2:','Elias Uziel Sanne Fernandez'),
                ('Asesor 1:','Ing. Nemias Saboya Rios'),
                ('Asesor 2:','Ing. Fernando Manuel Asin Gomez'),
                ('Universidad:','Universidad Peruana Union (UPeU)'),
                ('Fecha:','Junio 2026'),
                ('Estado:','F1-F6 completadas y validadas — Repositorio: github.com/marksato13/PRODUCTO-_INGENIERL')]:
    pdf.set_font('Helvetica','B',10); pdf.cell(48,7,lbl,**INL)
    pdf.set_font('Helvetica','',10); pdf.cell(0,7,val,**NL)
pdf.ln(6); pdf.hr()

pdf.set_font('Helvetica','B',10); pdf.set_text_color(*BLU)
pdf.cell(0,7,'Resumen',**NL); pdf.set_text_color(0,0,0)
pdf.set_font('Helvetica','',10)
pdf.multi_cell(0,5.5,'Este trabajo presenta el diseno, implementacion y validacion de un sistema de deteccion temprana de comportamientos anomalos en redes de datos para entornos universitarios. Se utiliza el algoritmo Isolation Forest (IF) entrenado sobre flujos de red capturados por Suricata 7.0.3, combinado con detectores heuristicos para ataques de fuerza bruta SSH y abuso HTTP. El motor de decision procesa flujos en tiempo real con latencia P95=34.8 ms y aplica control inline mediante ipset/iptables. La validacion con 40 corridas demostro Disponibilidad=100%, ITL=0%, Lead Time=61.92 s y AUC-ROC=0.8998.',align='J')
pdf.ln(5)
pdf.kpis([('Disponibilidad','100%',GRN),('ITL','0%',GRN),('AUC-ROC','0.8998',BLU),('Latencia P95','34.8ms',BLU),('Lead Time','61.9s',YEL),('Corridas','40/40',GRN)])

# ── 1. INTRODUCCION ───────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Introduccion')
pdf.p('Las redes universitarias estan expuestas a ataques como inundaciones SYN, escaneos de puertos, ataques de fuerza bruta y abuso de servicios web. La deteccion tardia puede comprometer la disponibilidad de servicios criticos.')
pdf.p('Este PPI propone un sistema basado en Isolation Forest que opera sobre flujos Suricata, aplicando acciones PERMIT/LIMIT/BLOCK directamente en el kernel Linux mediante ipset/iptables, sin intervencion humana.')
pdf.h2('Objetivos Especificos')
for o in ['Configurar laboratorio virtualizado de 5 nodos para pruebas controladas.',
          'Capturar y etiquetar trafico de red en 9 escenarios reproducibles (A/B/C).',
          'Entrenar Isolation Forest (n=300) y derivar umbrales tau1/tau2 via curva ROC.',
          'Implementar motor de decision en tiempo real con latencia P95<500ms.',
          'Aplicar control inline via ipset/iptables: PERMIT, LIMIT y BLOCK.',
          'Validar con 40 corridas midiendo Disponibilidad, ITL y Lead Time.']:
    pdf.li(o)

# ── 2. METODOLOGIA ────────────────────────────────────────────────────────────
pdf.h1('Metodologia — Pipeline de 6 Fases')
pdf.p('El sistema se desarrolla en 6 fases secuenciales donde cada fase consume artefactos de la anterior.')
pdf.tabla(['Fase','Nombre','Descripcion'],
    [('F1','Entorno Laboratorio','5 VMs, red 192.168.0.0/24, Suricata 7.0.3'),
     ('F2','Captura Trafico','47 archivos eve.json.gz: 28 normal (4 escenarios x multiples corridas) + 13 anom + 6 mixto'),
     ('F3','Modelado Offline','Isolation Forest n=300, 14 features, curva ROC, tau1/tau2'),
     ('F4','Motor Decision','tail eve.json, extraccion features, scoring IF, accion'),
     ('F5','Control Inline','ipset/iptables en servidor, enforce.sh, dashboard web :8080'),
     ('F6','Validacion','40 corridas, 4 grupos, Disponibilidad/ITL/Lead Time/AUC')],
    [18,40,120])

# ── 3. F1 ────────────────────────────────────────────────────────────────────
pdf.h1('F1 — Entorno de Laboratorio')
pdf.tabla(['VM','IP','SO','Rol'],
    [('Win11 Cliente','192.168.0.10','Windows 11','Trafico cliente HTTP/SSH'),
     ('Ubuntu Desktop','192.168.0.20','Ubuntu 22.04','Admin, trafico normal A1-A4'),
     ('Kali Linux','192.168.0.100','Kali 2024','Ataques B1-B6: hping3,nmap,hydra'),
     ('Ubuntu Sensor','192.168.0.110','Ubuntu 22.04','Suricata 7.0.3, motor_decision.py'),
     ('Ubuntu Server','192.168.0.120','Ubuntu 22.04','nginx:80, SSH:22, ipset/iptables')],
    [40,36,30,72])
for item in ['Suricata 7.0.3: captura pasiva en interfaz ens35, salida EVE JSON.',
             'ppi-motor.service: systemd, reinicio automatico en fallo.',
             'SSH keys: Desktop->Sensor y Desktop->Server (BatchMode, sin contrasena).',
             'Whitelist: 192.168.0.1, .20, .110, .120, .130, .140, 127.0.0.1.']:
    pdf.li(item)

# ── 4. F2 ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F2 — Captura de Trafico')
pdf.tabla(['Tipo','Escenarios','Archivos raw','Flows aprox.'],
    [('Normal (Grupo A)','http, ssh, transferencia, sostenido','28 archivos (multiples corridas)','67,135 flows'),
     ('Anomalo (Grupo B)','syn_flood, port_scan, udp_flood, icmp_flood, http_abuse, bruteforce','13 archivos (2 fechas + extra BF)','598,285 flows'),
     ('Mixto (Grupo C)','http_syn, ssh_portscan, descarga_udp','6 archivos (3 de jun-02, 3 de jun-16)','variable')],
    [28,66,50,28])
pdf.tabla(['Escenario','Origen','Herramienta','Detalle'],
    [('http_normal','Desktop 192.168.0.20','curl, wget','GET :80 con pausas 5-10s'),
     ('ssh_legitimo','Desktop 192.168.0.20','ssh, scp','Sesion interactiva :22'),
     ('transferencia','Desktop 192.168.0.20','scp, wget','Descarga archivos grandes'),
     ('sostenido','Desktop 192.168.0.20','curl+ssh mixto','Trafico combinado 15min'),
     ('syn_flood','Kali 192.168.0.100','hping3 -S -p 80','SYN sin completar handshake'),
     ('port_scan','Kali 192.168.0.100','nmap -sS 1-1024','Escaneo sigiloso puertos'),
     ('udp_flood','Kali 192.168.0.100','hping3 --udp :53','Inundacion UDP puerto 53'),
     ('icmp_flood','Kali 192.168.0.100','hping3 -1 --flood','Ping flood sin limite'),
     ('http_abuse','Kali 192.168.0.100','curl bucle continuo','100+ req/30s a :80'),
     ('bruteforce','Kali 192.168.0.100','hydra/sshpass :22','Intentos contrasena SSH'),
     ('mixto_http_syn','Desktop+Kali','curl+hping3','Normal+SYN flood simultaneo'),
     ('mixto_ssh_scan','Desktop+Kali','ssh+nmap','Normal+escaneo simultaneo'),
     ('mixto_descarga_udp','Desktop+Kali','scp+hping3','Normal+UDP flood simultaneo')],
    [28,36,36,78])
pdf.tabla(['Artefacto','Flows','Descripcion'],
    [('normal_holdout.csv','13,427 (20% aleatorio)','Reservado para evaluacion offline en fase3_evaluar.py'),
     ('data/raw/*_normal_*.gz','67,135 totales','Fuente directa — 28 archivos de 4 escenarios y multiples corridas'),
     ('data/raw/*_anom_*.gz','598,285','Fuente directa — 13 archivos (BF x3, HTTP x2, ICMP x2, PS x2, SYN x2, UDP x2)'),
     ('data/raw/*_mixto_*.gz','variable','Fuente directa — 6 archivos (3 de jun-02, 3 de jun-16)')],[50,28,100])
pdf.box('Split 80/20 ALEATORIO (random_state=42, shuffle=True): el 80% de los flows normales entrena el modelo, el 20% restante queda como holdout para evaluar FP/FPR sobre datos normales nunca vistos. No existe particion 70/15/15 — esa era la diseno anterior eliminado porque IF no supervisado no necesita validacion con etiquetas.')


# ── 4b. EDA — ANALISIS EXPLORATORIO ─────────────────────────────────────────
pdf.add_page(); pdf.h1('Analisis Exploratorio de Datos (EDA)')
pdf.p('Se analizaron 651,993 flows capturados en los Grupos A (normal), B (anomalo) y C (mixto). El objetivo fue confirmar que las 14 features seleccionadas discriminan estadisticamente entre trafico normal y anomalo, justificando su uso como entrada al modelo Isolation Forest.')
pdf.tabla(['Feature','Mann-Whitney p','Separacion','Conclusion'],
    [('byte_ratio','< 0.001','ALTA','62x diferencia: normal=0.96 vs anomalo=60.0'),
     ('pkt_rate','< 0.001','ALTA','Anomalo 25x mas rapido: normal=800 vs anom=20,000pkt/s'),
     ('bytes_toserver','< 0.001','ALTA','Floods generan muchos mas bytes hacia servidor'),
     ('duration','< 0.001','MEDIA','Flows anomalos mas cortos en general (floods)'),
     ('dest_port','< 0.001','MEDIA','Puerto 80 predomina en ataques HTTP, escaneos'),
     ('is_tcp','< 0.001','MEDIA','Ataques TCP (SYN flood, scan) mas frecuentes'),
     ('is_udp','< 0.001','MEDIA','UDP flood genera muchos flows UDP cortos'),
     ('todas','< 0.001','—','14/14 features significativas (test Mann-Whitney U)')],
    [30,26,20,96])
pdf.p('Nota: test Mann-Whitney U no parametrico — no asume normalidad. p<0.001 en todas las features confirma discriminabilidad estadistica.')
pdf.fig(E+'/eda_01_distribuciones.png','Figura EDA-1 — Distribucion de las 14 features: normal (azul) vs anomalo (naranja)',0.95)
pdf.fig(E+'/eda_02_protocolo.png','Figura EDA-2 — Distribucion por protocolo (TCP/UDP/ICMP) en tráfico normal vs anomalo',0.90)
pdf.add_page()
pdf.fig(E+'/eda_03_boxplots.png','Figura EDA-3 — Boxplots de features clave: alta separacion en byte_ratio y pkt_rate',0.95)
pdf.fig(E+'/eda_04_correlacion.png','Figura EDA-4 — Matriz de correlacion entre las 14 features (Spearman)',0.90)
pdf.add_page()
pdf.fig(E+'/eda_05_dest_ports.png','Figura EDA-5 — Top puertos destino en trafico normal y anomalo',0.90)
pdf.fig(E+'/eda_06_stats_tabla.png','Figura EDA-6 — Tabla de estadisticas descriptivas con p-valores Mann-Whitney',0.95)

# ── 5. F3 ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F3 — Modelado Offline con Isolation Forest')
pdf.tabla(['Feature','Descripcion','Tipo'],
    [('pkts_toserver','Paquetes al servidor','Volumen'),
     ('pkts_toclient','Paquetes del servidor','Volumen'),
     ('bytes_toserver','Bytes al servidor','Volumen'),
     ('bytes_toclient','Bytes del servidor','Volumen'),
     ('duration','Duracion del flow (s)','Temporalidad'),
     ('pkt_rate','Paquetes por segundo','Tasa'),
     ('byte_rate','Bytes por segundo','Tasa'),
     ('pkt_ratio','pkts_toserver/pkts_toclient','Ratio'),
     ('byte_ratio','bytes_toserver/bytes_toclient','Ratio'),
     ('avg_pkt_size','Tamano medio paquete (B)','Tamano'),
     ('is_tcp','1 si TCP','Flag'),('is_udp','1 si UDP','Flag'),
     ('is_icmp','1 si ICMP','Flag'),('dest_port','Puerto destino','Puerto')],
    [38,100,30])
pdf.tabla(['Umbral','Valor','Criterio','TPR','FPR'],
    [('tau1 (PERMIT/LIMIT)','-0.4459','Youden index max (TPR-FPR optimo)','99.40%','20.47%'),
     ('tau2 (LIMIT/BLOCK)', '-0.6027','FPR <= 2% con maximo TPR',         '18.27%', '2.00%')],
    [40,20,76,16,16])
pdf.kpis([('AUC-ROC','0.8998',BLU),('Precision','99.54%',GRN),('Recall','99.40%',GRN),('F1','0.9947',GRN)])
pdf.fig(R+'/auc_roc.png','Figura 1 — Curva ROC del modelo Isolation Forest (AUC=0.8998)',0.72)
pdf.fig(R+'/isolation_forest_resultado.png','Figura 2 — Distribucion de scores IF: normal (azul) vs anomalo (rojo)',0.72)
pdf.fig(R+'/sensibilidad/sensibilidad_n_flows.png','Figura 3 — AUC vs n_estimators (estable a partir de n=200)',0.72)
pdf.tabla(['Archivo raw (captura)','Flows','AUC-IF','AUC-AE'],
    [('BruteForce 02-jun','2,061','0.9727','0.9649'),
     ('HTTP Abuse 02-jun','13,889','0.9545','0.9516'),
     ('ICMP Flood 02-jun','23,460','0.9160','0.9966'),
     ('Port Scan 02-jun','3,258','0.8351','0.9901'),
     ('SYN Flood 02-jun','95,393','0.8815','0.9517'),
     ('UDP Flood 02-jun','18,168','0.9579','0.9881'),
     ('BruteForce 03-jun','100,000','0.8252','0.9863'),
     ('BruteForce 15-jun','4,824','0.9728','0.9036'),
     ('HTTP Abuse 15-jun','36,902','0.9749','0.9111'),
     ('ICMP Flood 15-jun','100,000','0.8955','0.9996'),
     ('Port Scan 15-jun','100,000','0.9508','0.9918'),
     ('SYN Flood 15-jun','330','0.9515','0.8287'),
     ('UDP Flood 15-jun','100,000','0.9623','0.9883'),
     ('AUC medio (IF=0.9270 / AE=0.9579)','598,285','0.9270','0.9579')],
    [48,20,18,18])
pdf.p('Nota: AUC-IF = AUC del Isolation Forest de produccion. AUC-AE = Autoencoder del experimento comparativo. IF elegido sobre AE por validacion F6 (40 corridas, disponibilidad=100%, ITL=0%).')

# ── 6. F4 ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F4 — Motor de Decision en Tiempo Real')
pdf.box('Logica por flow:\n  1. IP en whitelist -> IGNORAR\n  2. score > tau1 (-0.4459) -> PERMIT (normal)\n  3. score > tau2 (-0.6027) -> LIMIT (hashlimit 100pkt/s, ipset ppi_limited)\n  4. score <= tau2 -> BLOCK (DROP, ipset ppi_blocked)\n\nDetectores heuristicos en paralelo:\n  SSH BruteForce: >=15 intentos/60s -> BLOCK (>=5 -> LIMIT)\n  HTTP Abuse:     >=100 req/30s -> BLOCK (>=50 -> LIMIT)')
pdf.kpis([('Latencia media','34.5 ms',BLU),('Latencia P95','34.8 ms',BLU),('Throughput','29 flows/s',GRN),('Requisito','<500 ms',GRN)])
pdf.fig(G+'/f6_06_latencia_pipeline.png','Figura 4 — Distribucion de latencia del pipeline (1000 flows medidos)',0.90)

# ── 7. F5 ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F5 — Control Inline e Integracion')
pdf.tabla(['Set ipset','Regla iptables','Efecto'],
    [('ppi_blocked','INPUT -m set --match-set ppi_blocked src -j DROP','DROP completo, timeout=300s'),
     ('ppi_limited','INPUT -m set --match-set ppi_limited src --hashlimit-above 100/sec -j DROP','Limite 100pkt/s, timeout=300s')],
    [28,100,50])
pdf.tabla(['Componente','Interfaz','Descripcion'],
    [('dashboard.py','Terminal ANSI','Estadisticas tiempo real, refresca cada 3s'),
     ('dashboard_web.py','HTTP :8080 Flask+SSE','Push instantaneo al navegador'),
     ('/api/stats','GET JSON','Flows, anomalias, bloqueados, latencia media'),
     ('/api/stream','GET SSE','Eventos push sin recargar pagina'),
     ('/api/block|unblock','POST JSON','Control manual desde interfaz web')],[35,32,111])
pdf.tabla(['Prueba T3-T5','Resultado'],
    [('enforce.sh BLOCK','PASS: IP en ppi_blocked timeout=59s'),
     ('enforce.sh LIMIT','PASS: IP en ppi_limited timeout=59s'),
     ('enforce.sh UNBLOCK','PASS: Removida de ambos sets'),
     ('Auto-expiry 5s','PASS: Expirado correctamente'),
     ('GET / HTTP','PASS: HTTP 200 en 17ms'),
     ('SSE /api/stream','PASS: Streaming activo, 1 cliente'),
     ('POST /api/block','PASS: {"ok":true}')],[60,118])


# ── 7b. EXPERIMENTO COMPARATIVO ──────────────────────────────────────────────
pdf.add_page(); pdf.h1('Experimento Comparativo — Seleccion de Modelo')
pdf.p('Antes de fijar Isolation Forest como modelo de produccion, se evaluaron 7 modelos sobre el mismo conjunto de 611,712 flows (normal_holdout + todos los archivos anomalos).')
pdf.tabla(['Modelo','Paradigma','AUC-ROC','Recall','FPR','T.train'],
    [('Isolation Forest','one-class','0.8998','99.40%','20.47%','< 10 s'),
     ('Autoencoder (AE)','one-class','0.9103','99.42%','25.68%','115.6 s'),
     ('One-Class SVM','one-class','0.9712','93.03%','8.02%','0.6 s'),
     ('LOF','one-class','0.8418','59.00%','5.19%','0.3 s'),
     ('Random Forest (*)','supervisado','0.9997','99.86%','0.40%','9.8 s'),
     ('XGBoost (*)','supervisado','0.9995','99.86%','0.42%','77.8 s'),
     ('Decision Tree (*)','supervisado','0.9972','99.75%','0.52%','0.1 s')],
    [38,24,20,18,16,22])
pdf.p('(*) Supervisados requieren etiquetas de ataque en entrenamiento — no replicables en produccion real donde ataques futuros son desconocidos.')
pdf.h3('Por que se elige Isolation Forest sobre Autoencoder (AUC mayor)')
pdf.tabla(['Criterio','IF','AE','Ganador'],
    [('AUC-ROC global','0.8998','0.9103','AE (+1.16%)'),
     ('Recall @ tau1','99.40%','99.42%','Empate'),
     ('FPR @ tau1 (menor = mejor)','20.47%','25.68%','IF mejor'),
     ('Block% @ tau2','18.27%','54.62%','AE (3x mas BLOCK)'),
     ('Corridas F6 validadas en vivo','40/40','0 corridas','IF certificado'),
     ('Disponibilidad F6','100%','No medida','IF certificado'),
     ('ITL en F6','0%','No medida','IF certificado'),
     ('Tiempo de entrenamiento','< 10 s','115.6 s','IF 12x mas rapido'),
     ('Tamano modelo serializado','2.5 MB','16 KB','AE mas ligero')],
    [56,18,18,40])
pdf.box('Razon de seleccion: IF tiene 40 corridas validadas en produccion real con Disponibilidad=100% e ITL=0%. El AE solo fue evaluado offline. En un sistema IPS que toma acciones reales (DROP, LIMIT) sobre trafico de produccion, la validacion en vivo es el criterio determinante. El AE queda documentado como mejora futura con mayor Block% (54.6% vs 18.3%).')

# ── 8. F6 ────────────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('F6 — Validacion del Sistema (40 Corridas)')
pdf.tabla(['Grupo','Corridas','Descripcion','Resultado esperado'],
    [('Normal','1-10','Solo trafico Desktop normal','flows_anom=0, disp=1, itl=0'),
     ('Mixto','11-20','Normal + Ataques alternados','Corrida 11: deteccion Lead=61.9s'),
     ('Reeval','21-30','Re-evaluacion con IP bloqueada','flows_anom=0 (IP contenida)'),
     ('Final','31-40','Confirmacion de contencion','disp=1, itl=0 en todas')],
    [20,18,68,72])
pdf.box('Corrida 11 — SYN Flood (evento de deteccion):\n  t= 0s  inicio de corrida\n  t=15s  ataque hping3 -S -p 80 desde Kali 192.168.0.100\n  t=62s  SOSPECHOSO | src=192.168.0.100 score=-0.5045 | LIMIT\n  t=63s  HTTP-ABUSE | requests=100/30s | BLOCK -> BLOCKED 192.168.0.100\n  t=300s fin corrida | nginx HTTP 200 todo el tiempo | ITL=0%',LBLU,BLU)
pdf.tabla(['Grupo','Disponibilidad','Lead Time','ITL','flows_anom'],
    [('Normal (1-10)','100%','N/A','0%','0'),
     ('Mixto (11-20)','100%','61.92s','0%','2 (corrida 11)'),
     ('Reeval (21-30)','100%','N/A','0%','0 (IP contenida)'),
     ('Final (31-40)','100%','N/A','0%','0 (IP contenida)')],[38,30,26,18,65])

# ── 9. RESULTADOS ─────────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Resultados y Discusion')
pdf.kpis([('Disponibilidad','100%',GRN),('ITL Global','0%',GRN),('Lead Time','61.9s',BLU),('Latencia P95','34.8ms',BLU),('AUC-ROC','0.8998',BLU),('Corridas OK','40/40',GRN)])
pdf.fig(G+'/f6_07_panel_resumen.png','Figura 5 — Panel resumen F6: metricas clave en las 40 corridas',0.95)
pdf.add_page()
pdf.fig(G+'/f6_01_disponibilidad.png','Figura 6 — Disponibilidad 100% en las 40 corridas',0.90)
pdf.fig(G+'/f6_02_flows_anomalos.png','Figura 7 — Flujos anomalos detectados: solo corrida 11',0.90)
pdf.add_page()
pdf.fig(G+'/f6_03_timeline_deteccion.png','Figura 8 — Timeline corrida 11: LIMIT t=62s, BLOCK t=63s',0.90)
pdf.fig(G+'/f6_04_itl.png','Figura 9 — ITL=0% en las 40 corridas (trafico legitimo nunca interrumpido)',0.90)
pdf.add_page()
pdf.fig(G+'/f6_05_flujos_acumulados.png','Figura 10 — Flujos acumulados procesados: 0 a 312,500',0.88)
pdf.p('Tres indicadores criticos se cumplieron simultaneamente en las 40 corridas:')
for item in ['Disponibilidad=100%: servidor HTTP 200 durante todos los ataques activos.',
             'ITL=0%: ningun host legitimo fue limitado ni bloqueado en ninguna corrida.',
             'Latencia P95=34.8ms: 14x por debajo del requisito de 500ms.']:
    pdf.li(item)

# ── 10. CONCLUSIONES ─────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Conclusiones')
for tit,txt in [
    ('Deteccion efectiva','AUC-ROC=0.8998, recall=99.40%, precision=99.54%. Los detectores heuristicos elevan el recall efectivo a ~100% para bruteforce y http abuse.'),
    ('Latencia en tiempo real','Pipeline P95=34.8ms, throughput=29 flows/s. Cumple el requisito de 500ms por un factor de 14.'),
    ('Sin impacto en trafico legitimo','ITL=0% en 40 corridas. La whitelist previene auto-bloqueo de infraestructura critica.'),
    ('Disponibilidad garantizada','nginx HTTP 200 durante todos los ataques. ipset bloquea al atacante antes de saturar el servidor.'),
    ('Pipeline reproducible','6 scripts deterministas que pueden recalibrarse con nuevos datos ejecutando la cadena completa.')]:
    pdf.h3(tit); pdf.p(txt)
pdf.tabla(['Requisito','Objetivo','Obtenido','Estado'],
    [('Latencia P95','< 500 ms','34.8 ms','CUMPLE'),
     ('Disponibilidad','>= 99%','100% (40/40)','CUMPLE'),
     ('ITL','= 0%','0% (40/40)','CUMPLE'),
     ('AUC-ROC','>= 0.85','0.8998','CUMPLE'),
     ('Lead Time','< 120 s','61.92 s','CUMPLE'),
     ('Precision','>= 95%','99.54%','CUMPLE'),
     ('Recall','>= 80%','99.40%','CUMPLE'),
     ('Flows procesados','>= 10,000','312,500','CUMPLE')],[40,28,32,28])

# ── 11. REFERENCIAS ───────────────────────────────────────────────────────────
pdf.add_page(); pdf.h1('Referencias Bibliograficas')
for i,(a,t,p,y) in enumerate([
    ('Liu, F.T., Ting, K.M., Zhou, Z.H.','Isolation Forest','IEEE ICDM pp.413-422','2008'),
    ('Liu, F.T., Ting, K.M., Zhou, Z.H.','Isolation-Based Anomaly Detection','ACM TKDD 6(1)','2012'),
    ('Chandola, V., Banerjee, A., Kumar, V.','Anomaly Detection: A Survey','ACM Comput. Surv. 41(3)','2009'),
    ('Scarfone, K., Mell, P.','Guide to Intrusion Detection (IDPS), NIST SP 800-94','NIST','2007'),
    ('Garcia-Teodoro, P. et al.','Anomaly-based network intrusion detection: techniques, systems','Computers & Security 28','2009'),
    ('Fawcett, T.','An Introduction to ROC Analysis','Pattern Recognition Letters 27(8)','2006'),
    ('Mann, H.B., Whitney, D.R.','On a Test of Whether One of Two Random Variables is Stochastically Larger','Ann. Math. Stat. 18(1)','1947'),
    ('Youden, W.J.','Index for Rating Diagnostic Tests','Cancer 3(1) pp.32-35','1950'),
    ('Pedregosa, F. et al.','Scikit-learn: Machine Learning in Python','JMLR 12 pp.2825-2830','2011'),
    ('Powers, D.M.W.','Evaluation: Precision, Recall, F-Measure to ROC','JMLT 2(1)','2011'),
    ('Buczak, A.L., Guven, E.','Survey of ML Methods for Cyber Security IDS','IEEE Comm. Surveys 18(2)','2016'),
    ('OISF','Suricata 7.0 User Guide — Flow Timeouts','Open Information Security Foundation','2023'),
    ('Sommer, R., Paxson, V.','Outside the Closed World: On ML for Network IDS','IEEE S&P pp.305-316','2010')],1):
    pdf.set_font('Helvetica','B',9); pdf.cell(8,5.5,f'[{i}]',**INL)
    pdf.set_font('Helvetica','',9)
    pdf.multi_cell(0,5.5,f'{a} ({y}). {t}. {p}.'); pdf.ln(1)

# ── ANEXO ──────────────────────────────────────────────────────────────────
pdf.add_page()
pdf.set_fill_color(*GRY); pdf.set_text_color(*WHT)
pdf.set_font('Helvetica','B',13)
pdf.cell(0,10,'  Anexo A — Estructura del Repositorio',fill=True,**NL)
pdf.set_text_color(0,0,0); pdf.ln(3)
pdf.p('Repositorio: https://github.com/marksato13/PRODUCTO-_INGENIERL\nSensor: /home/m4rk/ppi-surikata-producto/')
pdf.tabla(['Artefacto','Descripcion'],
    [('scripts/motor_decision.py','Motor de decision en tiempo real (F4+F5)'),
     ('scripts/f6_corridas.py','Orquestador de 40 corridas (F6)'),
     ('scripts/enforce.sh','Control manual BLOCK/LIMIT/UNBLOCK via SSH->ipset'),
     ('scripts/dashboard_web.py','Dashboard Flask+SSE en :8080'),
     ('scripts/fase3_isolation_forest.py','Entrenamiento IF'),
     ('scripts/fase3_evaluar.py','Evaluacion, ROC, umbrales tau1/tau2'),
     ('models/isolation_forest.pkl','Modelo IF serializado'),
     ('models/scaler.pkl','StandardScaler fit sobre train.csv'),
     ('results/metricas_offline.txt','Umbrales canonicos tau1=-0.4459 tau2=-0.6027'),
     ('results/resultados_f6_completo.csv','40 corridas x 18 metricas'),
     ('results/graficas_f6/','7 figuras PNG 300 DPI para informe'),
     ('docs/ppi_documentacion/','13 archivos: 2 por fase (diagrama+spec)')],[80,98])

pdf.output(OUT)
print(f'OK: {OUT}')
import os; print(f'Tamano: {os.path.getsize(OUT)//1024} KB')
