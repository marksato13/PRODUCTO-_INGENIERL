# F1 — Diagramas de Arquitectura para Draw.io

**Instrucciones de importación:**
1. Abrir [app.diagrams.net](https://app.diagrams.net) (Draw.io)
2. Menú `Extras` → `Edit Diagram` → pegar el XML de cada diagrama
3. O usar `File` → `Import from` → `Text` → pegar el XML

---

## Diagrama 1 — Arquitectura Física (Topología de Red)

> Importar este XML completo en Draw.io

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
  tooltips="1" connect="1" arrows="1" fold="1" page="1"
  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- Título -->
    <mxCell id="2" value="Arquitectura Física del Laboratorio PPI — 192.168.0.0/24"
      style="text;html=1;strokeColor=none;fillColor=none;align=center;
             verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;
             fontStyle=1;fontColor=#1565C0;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="20" width="1000" height="40" as="geometry"/>
    </mxCell>

    <!-- Contenedor: Red LAN -->
    <mxCell id="3" value="Red LAN — 192.168.0.0/24 (VMware vSwitch)"
      style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],
             [1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],
             [0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.cisco.sites.generic_building;
             sketch=0;html=1;pointerEvents=1;dashed=0;fillColor=#dae8fc;
             strokeColor=#6c8ebf;strokeWidth=2;fillColor=#f0f4ff;
             strokeColor=#4a6fa5;fontStyle=1;fontSize=13;verticalAlign=top;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="80" width="1040" height="680" as="geometry"/>
    </mxCell>

    <!-- VM pfSense Gateway -->
    <mxCell id="10" value="&lt;b&gt;pfSense&lt;/b&gt;&lt;br&gt;192.168.0.1&lt;br&gt;Gateway / Firewall&lt;br&gt;pfSense 2.7.x"
      style="shape=mxgraph.cisco.routers.router;sketch=0;html=1;
             pointerEvents=1;dashed=0;fillColor=#f5f5f5;strokeColor=#666666;
             fontColor=#333333;align=center;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="510" y="110" width="80" height="80" as="geometry"/>
    </mxCell>

    <!-- VM Ubuntu Desktop -->
    <mxCell id="20" value="&lt;b&gt;Ubuntu Desktop&lt;/b&gt;&lt;br&gt;192.168.0.20&lt;br&gt;Ubuntu 22.04 LTS&lt;br&gt;Origen tráfico NORMAL&lt;br&gt;curl · wget · ssh · scp"
      style="shape=mxgraph.cisco.computers_and_peripherals.pc;sketch=0;
             html=1;pointerEvents=1;dashed=0;fillColor=#dae8fc;
             strokeColor=#6c8ebf;fontColor=#1565C0;align=center;fontSize=10;
             fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="120" y="240" width="80" height="90" as="geometry"/>
    </mxCell>

    <!-- VM Kali Linux -->
    <mxCell id="30" value="&lt;b&gt;Kali Linux&lt;/b&gt;&lt;br&gt;192.168.0.100&lt;br&gt;Kali 2024.1&lt;br&gt;Origen tráfico ANÓMALO&lt;br&gt;hping3 · nmap · hydra"
      style="shape=mxgraph.cisco.computers_and_peripherals.pc;sketch=0;
             html=1;pointerEvents=1;dashed=0;fillColor=#f8cecc;
             strokeColor=#b85450;fontColor=#c62828;align=center;fontSize=10;
             fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="120" y="480" width="80" height="90" as="geometry"/>
    </mxCell>

    <!-- VM Suricata Sensor -->
    <mxCell id="40" value="&lt;b&gt;Ubuntu Suricata&lt;/b&gt;&lt;br&gt;192.168.0.110&lt;br&gt;Ubuntu Server 22.04&lt;br&gt;&lt;b&gt;SENSOR IDS&lt;/b&gt;&lt;br&gt;Suricata 7.0.3 · ens35&lt;br&gt;motor_decision.py&lt;br&gt;ppi-motor.service"
      style="shape=mxgraph.cisco.servers.standard_server;sketch=0;html=1;
             pointerEvents=1;dashed=0;fillColor=#d5e8d4;strokeColor=#82b366;
             fontColor=#2e7d32;align=center;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="500" y="340" width="100" height="120" as="geometry"/>
    </mxCell>

    <!-- VM Ubuntu Server -->
    <mxCell id="50" value="&lt;b&gt;Ubuntu Server&lt;/b&gt;&lt;br&gt;192.168.0.120&lt;br&gt;Ubuntu Server 22.04&lt;br&gt;&lt;b&gt;OBJETIVO&lt;/b&gt;&lt;br&gt;nginx :80 · SSH :22&lt;br&gt;ipset ppi_blocked&lt;br&gt;iptables DROP/hashlimit"
      style="shape=mxgraph.cisco.servers.standard_server;sketch=0;html=1;
             pointerEvents=1;dashed=0;fillColor=#fff2cc;strokeColor=#d6b656;
             fontColor=#7d4b00;align=center;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="860" y="340" width="100" height="130" as="geometry"/>
    </mxCell>

    <!-- VM BigData -->
    <mxCell id="60" value="&lt;b&gt;Ubuntu BigData&lt;/b&gt;&lt;br&gt;192.168.0.130&lt;br&gt;Ubuntu Server 22.04&lt;br&gt;Almacenamiento"
      style="shape=mxgraph.cisco.servers.standard_server;sketch=0;html=1;
             pointerEvents=1;dashed=0;fillColor=#e1d5e7;strokeColor=#9673a6;
             fontColor=#4a235a;align=center;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="860" y="560" width="100" height="100" as="geometry"/>
    </mxCell>

    <!-- vSwitch horizontal -->
    <mxCell id="70" value="VMware vSwitch (LAN Bridge)"
      style="shape=mxgraph.cisco.switches.workgroup_switch;sketch=0;html=1;
             pointerEvents=1;dashed=0;fillColor=#f5f5f5;strokeColor=#666666;
             fontColor=#333333;align=center;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="460" y="240" width="180" height="60" as="geometry"/>
    </mxCell>

    <!-- Conexiones al vSwitch -->
    <!-- pfSense → vSwitch -->
    <mxCell id="71" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#6c8ebf;strokeWidth=2;"
      edge="1" source="10" target="70" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Desktop → vSwitch -->
    <mxCell id="72" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#1565C0;strokeWidth=2;"
      edge="1" source="20" target="70" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Kali → vSwitch -->
    <mxCell id="73" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#c62828;strokeWidth=2;dashed=1;"
      edge="1" source="30" target="70" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- vSwitch → Sensor -->
    <mxCell id="74" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#2e7d32;strokeWidth=2;"
      edge="1" source="70" target="40" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- vSwitch → Servidor -->
    <mxCell id="75" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#d6b656;strokeWidth=2;"
      edge="1" source="70" target="50" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- vSwitch → BigData -->
    <mxCell id="76" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#9673a6;strokeWidth=1;dashed=1;"
      edge="1" source="70" target="60" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Tráfico normal: Desktop → Servidor (verde) -->
    <mxCell id="80" value="HTTP / SSH / SCP (tráfico normal)"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1565C0;
             strokeWidth=2;dashed=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0;entryY=0.3;entryDx=0;entryDy=0;
             endArrow=block;endFill=1;fontColor=#1565C0;fontSize=9;"
      edge="1" source="20" target="50" parent="1">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="330" y="285"/>
          <mxPoint x="330" y="380"/>
          <mxPoint x="860" y="380"/>
        </Array>
      </mxGeometry>
    </mxCell>

    <!-- Tráfico anómalo: Kali → Servidor (rojo) -->
    <mxCell id="81" value="SYN flood / Port Scan / UDP flood / HTTP Abuse / Brute Force"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#c62828;
             strokeWidth=2;dashed=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
             entryX=0;entryY=0.7;entryDx=0;entryDy=0;
             endArrow=block;endFill=1;fontColor=#c62828;fontSize=9;"
      edge="1" source="30" target="50" parent="1">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="330" y="525"/>
          <mxPoint x="330" y="430"/>
          <mxPoint x="860" y="430"/>
        </Array>
      </mxGeometry>
    </mxCell>

    <!-- Captura promiscua: Sensor detecta todo -->
    <mxCell id="82" value="Captura promiscua ens35&#xa;(todo el tráfico LAN)"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#2e7d32;
             strokeWidth=1;dashed=1;endArrow=open;endFill=0;
             fontColor=#2e7d32;fontSize=9;"
      edge="1" source="40" target="50" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- SSH sensor → servidor (control inline) -->
    <mxCell id="83" value="SSH: ipset add ppi_blocked/ppi_limited&#xa;(control inline)"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#e65100;
             strokeWidth=2;dashed=0;endArrow=block;endFill=1;
             fontColor=#e65100;fontSize=9;"
      edge="1" source="40" target="50" parent="1">
      <mxGeometry relative="1" as="geometry">
        <Array as="points">
          <mxPoint x="600" y="500"/>
          <mxPoint x="860" y="500"/>
        </Array>
      </mxGeometry>
    </mxCell>

    <!-- Leyenda -->
    <mxCell id="90" value="Leyenda"
      style="text;html=1;strokeColor=none;fillColor=none;align=left;
             verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=12;
             fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="690" width="80" height="20" as="geometry"/>
    </mxCell>
    <mxCell id="91" value="─── Tráfico normal (Desktop)"
      style="text;html=1;strokeColor=none;fillColor=none;align=left;
             fontColor=#1565C0;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="715" width="200" height="20" as="geometry"/>
    </mxCell>
    <mxCell id="92" value="- - - Tráfico anómalo (Kali)"
      style="text;html=1;strokeColor=none;fillColor=none;align=left;
             fontColor=#c62828;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="735" width="200" height="20" as="geometry"/>
    </mxCell>
    <mxCell id="93" value="──► Control inline SSH (BLOCK/LIMIT)"
      style="text;html=1;strokeColor=none;fillColor=none;align=left;
             fontColor=#e65100;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="755" width="230" height="20" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Diagrama 2 — Flujo Lógico del Pipeline (F1 → F6)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
  tooltips="1" connect="1" arrows="1" fold="1" page="1"
  pageScale="1" pageWidth="1654" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- Título -->
    <mxCell id="2" value="Flujo Lógico del Pipeline — PPI 2026"
      style="text;html=1;strokeColor=none;fillColor=none;align=center;
             verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;
             fontStyle=1;fontColor=#1565C0;"
      vertex="1" parent="1">
      <mxGeometry x="100" y="20" width="1400" height="40" as="geometry"/>
    </mxCell>

    <!-- F1: Suricata -->
    <mxCell id="10" value="&lt;b&gt;F1 — Suricata Sensor&lt;/b&gt;&lt;br&gt;192.168.0.110&lt;br&gt;ens35 (promiscuo)&lt;br&gt;&lt;br&gt;/etc/suricata/suricata.yaml&lt;br&gt;af-packet: ens35"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;
             strokeColor=#82b366;fontSize=11;fontColor=#2e7d32;
             verticalAlign=middle;arcSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="100" y="200" width="180" height="120" as="geometry"/>
    </mxCell>

    <!-- eve.json -->
    <mxCell id="11" value="&lt;b&gt;eve.json&lt;/b&gt;&lt;br&gt;/var/log/suricata/eve.json&lt;br&gt;136 MB activo&lt;br&gt;JSON Lines · event_type: flow"
      style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
             fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;fontColor=#7d4b00;"
      vertex="1" parent="1">
      <mxGeometry x="360" y="215" width="160" height="90" as="geometry"/>
    </mxCell>

    <!-- F4: Motor -->
    <mxCell id="20" value="&lt;b&gt;F4 — Motor de Decisión&lt;/b&gt;&lt;br&gt;motor_decision.py&lt;br&gt;&lt;br&gt;① seguir_eve() — tail -f&lt;br&gt;② Filtros de entrada&lt;br&gt;③ extract_features() → [1×14]&lt;br&gt;④ scaler.transform()&lt;br&gt;⑤ clf.score_samples() → score&lt;br&gt;⑥ explicar_anomalia() → razón&lt;br&gt;⑦ decidir(score)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;
             strokeColor=#c62828;fontSize=10;fontColor=#b71c1c;
             verticalAlign=middle;arcSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="600" y="160" width="200" height="200" as="geometry"/>
    </mxCell>

    <!-- Modelos F3 -->
    <mxCell id="21" value="&lt;b&gt;F3 — Modelos&lt;/b&gt;&lt;br&gt;isolation_forest.pkl (2.5MB)&lt;br&gt;scaler.pkl (1.4KB)&lt;br&gt;features.csv&lt;br&gt;&lt;br&gt;τ1 = -0.4973&lt;br&gt;τ2 = -0.6873"
      style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
             fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;
             fontColor=#7d4b00;"
      vertex="1" parent="1">
      <mxGeometry x="600" y="420" width="200" height="120" as="geometry"/>
    </mxCell>

    <!-- Detección temporal -->
    <mxCell id="22" value="&lt;b&gt;Detectores Temporales&lt;/b&gt;&lt;br&gt;BF SSH: ventana 60s · umbral 15&lt;br&gt;HTTP Abuse: ventana 30s · umbral 100"
      style="rhombus;whiteSpace=wrap;html=1;fillColor=#f3e5f5;
             strokeColor=#7b1fa2;fontSize=10;fontColor=#4a148c;"
      vertex="1" parent="1">
      <mxGeometry x="580" y="600" width="240" height="100" as="geometry"/>
    </mxCell>

    <!-- Decisión PERMIT -->
    <mxCell id="30" value="&lt;b&gt;PERMIT&lt;/b&gt;&lt;br&gt;score &gt; τ1&lt;br&gt;log.debug()"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;
             strokeColor=#82b366;fontSize=11;fontColor=#2e7d32;"
      vertex="1" parent="1">
      <mxGeometry x="880" y="120" width="120" height="80" as="geometry"/>
    </mxCell>

    <!-- Decisión LIMIT -->
    <mxCell id="31" value="&lt;b&gt;LIMIT&lt;/b&gt;&lt;br&gt;τ2 &lt; score ≤ τ1&lt;br&gt;ipset ppi_limited&lt;br&gt;hashlimit 100pkt/s"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;
             strokeColor=#d6b656;fontSize=11;fontColor=#7d4b00;"
      vertex="1" parent="1">
      <mxGeometry x="880" y="240" width="120" height="80" as="geometry"/>
    </mxCell>

    <!-- Decisión BLOCK -->
    <mxCell id="32" value="&lt;b&gt;BLOCK&lt;/b&gt;&lt;br&gt;score ≤ τ2&lt;br&gt;ipset ppi_blocked&lt;br&gt;iptables DROP"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;
             strokeColor=#b85450;fontSize=11;fontColor=#c62828;"
      vertex="1" parent="1">
      <mxGeometry x="880" y="360" width="120" height="80" as="geometry"/>
    </mxCell>

    <!-- F5: Servidor -->
    <mxCell id="40" value="&lt;b&gt;F5 — Control Inline&lt;/b&gt;&lt;br&gt;192.168.0.120&lt;br&gt;&lt;br&gt;ppi_blocked → DROP&lt;br&gt;ppi_limited → 100pkt/s&lt;br&gt;Timeout: 300s automático"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;
             strokeColor=#d6b656;fontSize=11;fontColor=#7d4b00;
             arcSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="1080" y="280" width="180" height="120" as="geometry"/>
    </mxCell>

    <!-- Telegram -->
    <mxCell id="50" value="&lt;b&gt;Telegram Bot&lt;/b&gt;&lt;br&gt;🚨 ANOMALÍA + score + razón&lt;br&gt;⚠️ LIMIT + score + razón&lt;br&gt;🔑 BRUTE FORCE SSH&lt;br&gt;🌐 HTTP ABUSE"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;
             strokeColor=#0277bd;fontSize=10;fontColor=#01579b;arcSize=20;"
      vertex="1" parent="1">
      <mxGeometry x="1080" y="120" width="180" height="110" as="geometry"/>
    </mxCell>

    <!-- Log -->
    <mxCell id="51" value="&lt;b&gt;motor_decision.log&lt;/b&gt;&lt;br&gt;7.6 MB&lt;br&gt;TIMESTAMP|NIVEL|TIPO|&lt;br&gt;src=IP score=X razón=[...]"
      style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
             fillColor=#f3f3f3;strokeColor=#666666;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="1080" y="440" width="180" height="90" as="geometry"/>
    </mxCell>

    <!-- Dashboard -->
    <mxCell id="52" value="&lt;b&gt;Dashboard Terminal&lt;/b&gt;&lt;br&gt;dashboard.py&lt;br&gt;Actualiza cada 3s&lt;br&gt;flows·anomalías·latencia"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;
             strokeColor=#2e7d32;fontSize=10;fontColor=#1b5e20;arcSize=20;"
      vertex="1" parent="1">
      <mxGeometry x="1080" y="560" width="180" height="80" as="geometry"/>
    </mxCell>

    <!-- Conexiones -->
    <!-- Suricata → eve.json -->
    <mxCell id="60" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#2e7d32;strokeWidth=2;endArrow=block;endFill=1;"
      edge="1" source="10" target="11" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- eve.json → Motor -->
    <mxCell id="61" value="seguir_eve()" 
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#c62828;
             strokeWidth=2;endArrow=block;endFill=1;fontSize=9;"
      edge="1" source="11" target="20" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Modelos → Motor -->
    <mxCell id="62" value="joblib.load()"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d79b00;
             strokeWidth=2;endArrow=block;endFill=1;fontSize=9;"
      edge="1" source="21" target="20" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Detectores → Motor (override) -->
    <mxCell id="63" value="override si supera umbral"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#7b1fa2;
             strokeWidth=1;dashed=1;endArrow=open;endFill=0;fontSize=9;"
      edge="1" source="22" target="20" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Motor → PERMIT -->
    <mxCell id="64" value="score &gt; -0.4973"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#2e7d32;
             strokeWidth=1;fontSize=9;"
      edge="1" source="20" target="30" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Motor → LIMIT -->
    <mxCell id="65" value="-0.6873 &lt; score ≤ -0.4973"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d6b656;
             strokeWidth=1;fontSize=9;"
      edge="1" source="20" target="31" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Motor → BLOCK -->
    <mxCell id="66" value="score ≤ -0.6873"
      style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#c62828;
             strokeWidth=1;fontSize=9;"
      edge="1" source="20" target="32" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- LIMIT/BLOCK → Servidor -->
    <mxCell id="67" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#e65100;strokeWidth=2;endArrow=block;endFill=1;"
      edge="1" source="31" target="40" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="68" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#c62828;strokeWidth=2;endArrow=block;endFill=1;"
      edge="1" source="32" target="40" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Motor → Telegram -->
    <mxCell id="69" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#0277bd;strokeWidth=1;dashed=1;endArrow=open;"
      edge="1" source="20" target="50" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Motor → Log -->
    <mxCell id="70" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#666666;strokeWidth=1;endArrow=open;"
      edge="1" source="20" target="51" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Log → Dashboard -->
    <mxCell id="71" style="edgeStyle=orthogonalEdgeStyle;html=1;
             strokeColor=#2e7d32;strokeWidth=1;dashed=1;endArrow=open;"
      edge="1" source="51" target="52" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Diagrama 3 — Clasificación de Vulnerabilidades por Capa OSI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
  tooltips="1" connect="1" arrows="1" fold="1" page="1"
  pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <mxCell id="2" value="Clasificación de Vulnerabilidades por Capa OSI — PPI 2026"
      style="text;html=1;strokeColor=none;fillColor=none;align=center;
             fontSize=15;fontStyle=1;fontColor=#1565C0;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="20" width="1040" height="30" as="geometry"/>
    </mxCell>

    <!-- Capa L3 -->
    <mxCell id="10" value="&lt;b&gt;CAPA 3 — RED&lt;/b&gt;"
      style="swimlane;fillColor=#f8cecc;strokeColor=#b85450;
             fontSize=13;fontStyle=1;fontColor=#c62828;startSize=30;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="70" width="300" height="280" as="geometry"/>
    </mxCell>
    <mxCell id="11" value="&lt;b&gt;SYN Flood&lt;/b&gt; — B1&lt;br&gt;hping3 -S -p 80 --rand-source&lt;br&gt;AUC=0.9529 · Det=72.2%&lt;br&gt;Severidad: Alta (7.5)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;
             strokeColor=#c62828;fontSize=10;"
      vertex="1" parent="10">
      <mxGeometry x="20" y="50" width="260" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="12" value="&lt;b&gt;ICMP Flood&lt;/b&gt; — B4&lt;br&gt;hping3 -1 --flood&lt;br&gt;AUC=0.9861 · Det=100%&lt;br&gt;Severidad: Media (5.8)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;
             strokeColor=#c62828;fontSize=10;"
      vertex="1" parent="10">
      <mxGeometry x="20" y="140" width="260" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="13" value="&lt;b&gt;Port Scan SYN&lt;/b&gt; — B2 (parcial L3)&lt;br&gt;nmap -sS -p 1-1024&lt;br&gt;AUC=0.9721 · Det=99.9%&lt;br&gt;Severidad: Media (4.0)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;
             strokeColor=#c62828;fontSize=10;"
      vertex="1" parent="10">
      <mxGeometry x="20" y="210" width="260" height="60" as="geometry"/>
    </mxCell>

    <!-- Capa L4 -->
    <mxCell id="20" value="&lt;b&gt;CAPA 4 — TRANSPORTE&lt;/b&gt;"
      style="swimlane;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=13;fontStyle=1;fontColor=#7d4b00;startSize=30;"
      vertex="1" parent="1">
      <mxGeometry x="420" y="70" width="300" height="210" as="geometry"/>
    </mxCell>
    <mxCell id="21" value="&lt;b&gt;UDP Flood&lt;/b&gt; — B3&lt;br&gt;hping3 --udp -p 53 --rand-source&lt;br&gt;AUC=0.9905 · Det=100%&lt;br&gt;Severidad: Alta (7.5)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;
             strokeColor=#d79b00;fontSize=10;"
      vertex="1" parent="20">
      <mxGeometry x="20" y="50" width="260" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="22" value="&lt;b&gt;Port Scan TCP&lt;/b&gt; — B2&lt;br&gt;nmap -sS (SYN half-open)&lt;br&gt;AUC=0.9721 · Det=99.9%&lt;br&gt;MITRE T1046"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;
             strokeColor=#d79b00;fontSize=10;"
      vertex="1" parent="20">
      <mxGeometry x="20" y="130" width="260" height="70" as="geometry"/>
    </mxCell>

    <!-- Capa L7 -->
    <mxCell id="30" value="&lt;b&gt;CAPA 7 — APLICACIÓN&lt;/b&gt;"
      style="swimlane;fillColor=#f3e5f5;strokeColor=#7b1fa2;
             fontSize=13;fontStyle=1;fontColor=#4a148c;startSize=30;"
      vertex="1" parent="1">
      <mxGeometry x="780" y="70" width="300" height="210" as="geometry"/>
    </mxCell>
    <mxCell id="31" value="&lt;b&gt;HTTP Abuse&lt;/b&gt; — B5&lt;br&gt;curl en bucle · :80&lt;br&gt;AUC=0.8630 · Det=56.6%+det.temp.&lt;br&gt;Severidad: Alta (7.5)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;
             strokeColor=#7b1fa2;fontSize=10;"
      vertex="1" parent="30">
      <mxGeometry x="20" y="50" width="260" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="32" value="&lt;b&gt;Brute Force SSH&lt;/b&gt; — B6&lt;br&gt;hydra -P rockyou.txt ssh://&lt;br&gt;AUC=0.6770 · Det=0.9%+det.temp.~90%&lt;br&gt;Severidad: Crítica (9.8)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;
             strokeColor=#7b1fa2;fontSize=10;"
      vertex="1" parent="30">
      <mxGeometry x="20" y="130" width="260" height="70" as="geometry"/>
    </mxCell>

    <!-- Fuera de alcance -->
    <mxCell id="40" value="&lt;b&gt;FUERA DEL ALCANCE&lt;/b&gt;"
      style="swimlane;fillColor=#f5f5f5;strokeColor=#666666;
             fontSize=13;fontStyle=1;fontColor=#333333;startSize=30;
             dashed=1;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="400" width="1020" height="130" as="geometry"/>
    </mxCell>
    <mxCell id="41" value="&lt;b&gt;Exfiltración&lt;/b&gt;&lt;br&gt;Requiere post-explotación&lt;br&gt;Necesita DPI (payload)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;
             strokeColor=#666666;fontSize=10;dashed=1;"
      vertex="1" parent="40">
      <mxGeometry x="20" y="40" width="200" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="42" value="&lt;b&gt;Movimiento Lateral&lt;/b&gt;&lt;br&gt;Requiere acceso previo&lt;br&gt;Multi-nodo (UEBA)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;
             strokeColor=#666666;fontSize=10;dashed=1;"
      vertex="1" parent="40">
      <mxGeometry x="240" y="40" width="200" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="43" value="&lt;b&gt;Slowloris / DNS Ampl.&lt;/b&gt;&lt;br&gt;Requiere servidores externos&lt;br&gt;Trabajo futuro"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;
             strokeColor=#666666;fontSize=10;dashed=1;"
      vertex="1" parent="40">
      <mxGeometry x="460" y="40" width="200" height="70" as="geometry"/>
    </mxCell>
    <mxCell id="44" value="&lt;b&gt;Ataques cifrados (TLS payload)&lt;/b&gt;&lt;br&gt;El sistema opera en L3/L4 metadata&lt;br&gt;No realiza TLS inspection"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;
             strokeColor=#666666;fontSize=10;dashed=1;"
      vertex="1" parent="40">
      <mxGeometry x="680" y="40" width="220" height="70" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Instrucciones para usar los diagramas en la tesis

### Opción A — Draw.io Online (recomendado)
1. Ir a [app.diagrams.net](https://app.diagrams.net)
2. `File` → `New` → `From Template` → en blanco
3. `Extras` → `Edit Diagram` → borrar contenido existente → pegar el XML de cada diagrama
4. `OK` → el diagrama aparece en pantalla
5. `File` → `Export As` → `PNG` (300 DPI para tesis) o `SVG` (vectorial)

### Opción B — Draw.io Desktop
1. Descargar desde [get.diagrams.net](https://get.diagrams.net)
2. `File` → `Import From` → `Text` → pegar XML
3. Exportar a PDF para insertar en tesis Word/LaTeX

### Opción C — VS Code con extensión
1. Instalar extensión `Draw.io Integration` (hediet.vscode-drawio)
2. Crear archivo con extensión `.drawio` y pegar el XML
3. El diagrama se previsualiza directamente en VS Code

### Personalización recomendada para tesis
- Exportar en PNG 300 DPI para inserción en Word
- Exportar en SVG para LaTeX (`\includegraphics{}`)
- Ajustar colores institucionales si la universidad tiene guía de estilo
- Agregar número de figura y pie de figura al insertar en el documento

---

*Archivo generado: 14 de junio 2026*
*Ruta: `/home/m4rk/Descargas/ppi_documentacion/F1_entorno_laboratorio/diagramas/F1_Arquitectura_General.drawio.md`*
