# F1 — Diagrama: Topología del Laboratorio

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
  tooltips="1" connect="1" arrows="1" fold="1" page="0"
  pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- ═══════════════════════════════════════════════════════════
         TÍTULO
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="title" value="F1 — Topología del Laboratorio  |  PPI UPeU 2026  |  Red 192.168.0.0/24"
      style="text;html=1;strokeColor=none;fillColor=#002060;fontColor=#ffffff;
             align=center;verticalAlign=middle;fontSize=15;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="100" y="20" width="1160" height="42" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         SWITCH / NUBE DE RED (centro)
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="switch" value="&lt;b&gt;Switch Virtual&lt;/b&gt;&lt;br/&gt;192.168.0.0/24&lt;br/&gt;&lt;i&gt;segmento único sin routing&lt;/i&gt;"
      style="ellipse;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#555555;
             fontColor=#333333;fontSize=11;verticalAlign=middle;"
      vertex="1" parent="1">
      <mxGeometry x="520" y="270" width="200" height="110" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         VM 1 — Win11 Cliente (.10)
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="win11" value="&lt;b&gt;Win11 Cliente&lt;/b&gt;&lt;br/&gt;192.168.0.10&lt;br/&gt;Windows 11&lt;br/&gt;Navegador · ping"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;
             fontSize=11;verticalAlign=middle;arcSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="120" width="180" height="95" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         VM 2 — Ubuntu Desktop Admin (.20)
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="desktop" value="&lt;b&gt;Ubuntu Desktop — Admin&lt;/b&gt;&lt;br/&gt;192.168.0.20  ·  Ubuntu 22.04&lt;br/&gt;curl · wget · scp · ssh&lt;br/&gt;&lt;i&gt;Origen tráfico normal (Grupos A, C)&lt;/i&gt;&lt;br/&gt;Claude Code · scripts de captura"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;
             fontSize=11;verticalAlign=middle;arcSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="370" width="210" height="115" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         VM 3 — Kali Linux Atacante (.100)
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="kali" value="&lt;b&gt;Kali Linux — Atacante&lt;/b&gt;&lt;br/&gt;192.168.0.100  ·  Kali 2024&lt;br/&gt;hping3 · nmap · hydra · sshpass&lt;br/&gt;&lt;i&gt;Origen tráfico anómalo (Grupo B)&lt;/i&gt;&lt;br/&gt;B1 SYN·B2 Scan·B3 UDP·B4 ICMP·B5 HTTP·B6 BF"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;
             fontSize=11;verticalAlign=middle;arcSize=12;"
      vertex="1" parent="1">
      <mxGeometry x="1040" y="120" width="230" height="125" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         VM 4 — Ubuntu Sensor (.110) — contenedor
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="sensor_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;
             fontSize=11;verticalAlign=top;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="310" y="510" width="290" height="270" as="geometry" />
    </mxCell>
    <mxCell id="sensor_hdr" value="&lt;b&gt;Ubuntu Sensor — IDS + Motor&lt;/b&gt;&lt;br/&gt;192.168.0.110  ·  Ubuntu 22.04"
      style="text;html=1;strokeColor=none;fillColor=#6c8ebf;fontColor=#ffffff;
             align=center;fontSize=12;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="310" y="510" width="290" height="42" as="geometry" />
    </mxCell>

    <!-- Suricata dentro del sensor -->
    <mxCell id="suricata" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&lt;br/&gt;Modo: IDS pasivo (af-packet)&lt;br/&gt;Interfaz: ens35&lt;br/&gt;Salida: /var/log/suricata/eve.json&lt;br/&gt;Servicio: suricata.service"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0050ef;strokeColor=#003399;
             fontColor=#ffffff;fontSize=10;verticalAlign=middle;arcSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="325" y="565" width="260" height="85" as="geometry" />
    </mxCell>

    <!-- Motor dentro del sensor -->
    <mxCell id="motor" value="&lt;b&gt;Motor de Decisión IF&lt;/b&gt;&lt;br/&gt;Servicio: ppi-motor.service&lt;br/&gt;Script: motor_decision.py&lt;br/&gt;Venv: sklearn 1.9.0 · Python 3.12&lt;br/&gt;Lee: eve.json + modelos + τ1/τ2"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#001dbc;strokeColor=#00008B;
             fontColor=#ffffff;fontSize=10;verticalAlign=middle;arcSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="325" y="665" width="260" height="95" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         VM 5 — Ubuntu Server (.120) — contenedor
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="server_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;
             fontSize=11;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="730" y="510" width="290" height="270" as="geometry" />
    </mxCell>
    <mxCell id="server_hdr" value="&lt;b&gt;Ubuntu Server — Servicio Objetivo&lt;/b&gt;&lt;br/&gt;192.168.0.120  ·  Ubuntu 22.04"
      style="text;html=1;strokeColor=none;fillColor=#82b366;fontColor=#ffffff;
             align=center;fontSize=12;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="730" y="510" width="290" height="42" as="geometry" />
    </mxCell>

    <!-- nginx dentro del servidor -->
    <mxCell id="nginx" value="nginx 1.24  —  puerto :80  (HTTP)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#82b366;strokeColor=#5a8a5a;
             fontColor=#ffffff;fontSize=11;verticalAlign=middle;"
      vertex="1" parent="1">
      <mxGeometry x="745" y="564" width="260" height="35" as="geometry" />
    </mxCell>

    <!-- SSH dentro del servidor -->
    <mxCell id="sshd" value="OpenSSH  —  puerto :22  (SSH)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#82b366;strokeColor=#5a8a5a;
             fontColor=#ffffff;fontSize=11;verticalAlign=middle;"
      vertex="1" parent="1">
      <mxGeometry x="745" y="606" width="260" height="35" as="geometry" />
    </mxCell>

    <!-- ipset bloqueados -->
    <mxCell id="ipset_blocked" value="ipset ppi_blocked  —  hash:ip timeout 3600s&lt;br/&gt;&lt;i&gt;→ iptables DROP (BLOCK)&lt;/i&gt;"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#b85450;strokeColor=#8a3a38;
             fontColor=#ffffff;fontSize=10;verticalAlign=middle;"
      vertex="1" parent="1">
      <mxGeometry x="745" y="648" width="260" height="45" as="geometry" />
    </mxCell>

    <!-- ipset limitados -->
    <mxCell id="ipset_limited" value="ipset ppi_limited  —  hash:ip timeout 3600s&lt;br/&gt;&lt;i&gt;→ hashlimit 100 pkt/s (LIMIT)&lt;/i&gt;"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d79b00;strokeColor=#a07000;
             fontColor=#ffffff;fontSize=10;verticalAlign=middle;"
      vertex="1" parent="1">
      <mxGeometry x="745" y="700" width="260" height="45" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         CONECTORES
    ═══════════════════════════════════════════════════════════ -->

    <!-- Win11 → Switch -->
    <mxCell id="e_win_sw" value="tráfico usuario"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0.1;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#d6b656;fontColor=#7a6000;fontSize=10;"
      edge="1" source="win11" target="switch" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Desktop → Switch -->
    <mxCell id="e_desk_sw" value="Grupos A/C: curl, wget, scp, ssh"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#82b366;fontColor=#3a6b3a;fontSize=10;fontStyle=1;"
      edge="1" source="desktop" target="switch" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Kali → Switch -->
    <mxCell id="e_kali_sw" value="Grupo B: SYN Flood, Port Scan,&lt;br/&gt;UDP/ICMP Flood, BruteForce"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=0;exitY=0.5;exitDx=0;exitDy=0;
             entryX=1;entryY=0.2;entryDx=0;entryDy=0;
             strokeColor=#b85450;fontColor=#7a0000;fontSize=10;fontStyle=1;"
      edge="1" source="kali" target="switch" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Switch → Server (tráfico destino) -->
    <mxCell id="e_sw_srv" value="todo el tráfico al servidor objetivo"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#555555;fontColor=#333333;fontSize=10;"
      edge="1" source="switch" target="server_bg" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Switch → Suricata (modo pasivo, copia del tráfico) -->
    <mxCell id="e_sw_suri" value="copia del tráfico (pasivo, ens35)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=0.35;exitY=1;exitDx=0;exitDy=0;
             entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#0050ef;fontColor=#003399;fontSize=10;
             dashed=1;dashPattern=8 4;"
      edge="1" source="switch" target="suricata" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Suricata → Motor (eve.json) -->
    <mxCell id="e_suri_motor" value="eve.json (flujos en tiempo real)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=0.5;exitY=1;exitDx=0;exitDy=0;
             entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#001dbc;fontColor=#001dbc;fontSize=10;fontStyle=1;"
      edge="1" source="suricata" target="motor" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Motor → Server (SSH ipset) -->
    <mxCell id="e_motor_srv" value="SSH → enforce.sh → ipset add/del&lt;br/&gt;BLOCK (DROP) | LIMIT (100pkt/s)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0;entryY=0.7;entryDx=0;entryDy=0;
             strokeColor=#b85450;fontColor=#7a0000;fontSize=10;fontStyle=1;
             endArrow=block;endFill=1;"
      edge="1" source="motor" target="server_bg" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Desktop → Sensor (SSH key admin) -->
    <mxCell id="e_desk_sensor" value="SSH key (BatchMode)&lt;br/&gt;admin + scripts"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=0.5;exitY=1;exitDx=0;exitDy=0;
             entryX=0;entryY=0.2;entryDx=0;entryDy=0;
             strokeColor=#009900;fontColor=#006600;fontSize=9;
             dashed=1;dashPattern=6 3;"
      edge="1" source="desktop" target="sensor_bg" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Desktop → Server (SSH key admin) -->
    <mxCell id="e_desk_server" value="SSH key (BatchMode)&lt;br/&gt;admin + verificación"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
             jettySize=auto;exitX=1;exitY=1;exitDx=0;exitDy=0;
             entryX=0;entryY=0.2;entryDx=0;entryDy=0;
             strokeColor=#009900;fontColor=#006600;fontSize=9;
             dashed=1;dashPattern=6 3;"
      edge="1" source="desktop" target="server_bg" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         LEYENDA
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="leg_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f9f9f9;strokeColor=#cccccc;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="815" width="1180" height="95" as="geometry" />
    </mxCell>
    <mxCell id="leg_title" value="&lt;b&gt;LEYENDA&lt;/b&gt;"
      style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=11;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="95" y="820" width="100" height="20" as="geometry" />
    </mxCell>

    <mxCell id="leg1" value="Tráfico normal (Grupos A/C)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="95" y="843" width="200" height="28" as="geometry" />
    </mxCell>
    <mxCell id="leg2" value="Tráfico anómalo / ataques (Grupo B)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="305" y="843" width="220" height="28" as="geometry" />
    </mxCell>
    <mxCell id="leg3" value="Sensor IDS + Motor de decisión"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="535" y="843" width="210" height="28" as="geometry" />
    </mxCell>
    <mxCell id="leg4" value="Control inline BLOCK / LIMIT (ipset)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="755" y="843" width="220" height="28" as="geometry" />
    </mxCell>
    <mxCell id="leg5" value="- - -  SSH administración (BatchMode)"
      style="text;html=1;strokeColor=#009900;fillColor=none;
             align=center;fontSize=10;fontColor=#006600;
             dashed=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="985" y="843" width="255" height="28" as="geometry" />
    </mxCell>

    <!-- ═══════════════════════════════════════════════════════════
         NOTA: WHITELIST
    ═══════════════════════════════════════════════════════════ -->
    <mxCell id="whitelist" value="&lt;b&gt;Whitelist (nunca bloquear):&lt;/b&gt;  192.168.0.1 · .20 (Desktop) · .110 (Sensor) · .120 (Server) · .130 · .140 · 127.0.0.1"
      style="text;html=1;strokeColor=#d6b656;fillColor=#fff2cc;
             align=center;fontSize=10;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="310" y="795" width="740" height="26" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```
