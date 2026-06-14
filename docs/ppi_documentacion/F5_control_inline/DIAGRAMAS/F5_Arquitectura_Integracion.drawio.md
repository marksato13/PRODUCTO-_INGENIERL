# F5 — Diagramas de Arquitectura (Draw.io)

**Instrucciones de uso:**
1. Abrir [app.diagrams.net](https://app.diagrams.net)
2. Menú → Extras → Edit Diagram (Ctrl+Shift+X)
3. Pegar el XML del diagrama deseado
4. Click "Close" para renderizar

---

## Diagrama 1 — Arquitectura Física (Topología de Red)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- TÍTULO -->
    <mxCell id="2" value="PPI-UPeU 2026 — Arquitectura Física de Red"
            style="text;html=1;strokeColor=none;fillColor=none;align=center;
                   verticalAlign=middle;whiteSpace=wrap;rounded=0;
                   fontSize=16;fontStyle=1"
            vertex="1" parent="1">
      <mxGeometry x="200" y="20" width="770" height="40" as="geometry"/>
    </mxCell>

    <!-- RED 192.168.0.0/24 -->
    <mxCell id="3" value="Red de Laboratorio&#xa;192.168.0.0/24"
            style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],
                   [1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],
                   [0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
                   shape=mxgraph.cisco.sites.generic_building;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#dae8fc;strokeColor=#6c8ebf;
                   fontSize=12;fontStyle=1;verticalLabelPosition=bottom;
                   verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="540" y="280" width="60" height="60" as="geometry"/>
    </mxCell>

    <!-- SWITCH -->
    <mxCell id="4" value="Switch&#xa;192.168.0.1&#xa;(Port Mirror)"
            style="shape=mxgraph.cisco.switches.workgroup_switch;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#fff2cc;strokeColor=#d6b656;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="520" y="340" width="100" height="60" as="geometry"/>
    </mxCell>

    <!-- Win11 CLIENTE -->
    <mxCell id="5" value="Win11 Cliente&#xa;192.168.0.10&#xa;Tráfico normal"
            style="shape=mxgraph.cisco.computers_and_peripherals.pc;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="100" y="200" width="80" height="60" as="geometry"/>
    </mxCell>

    <!-- Ubuntu Desktop ADMIN -->
    <mxCell id="6" value="Ubuntu Desktop&#xa;192.168.0.20&#xa;Admin / Scripts A1-A4&#xa;[Claude Code]"
            style="shape=mxgraph.cisco.computers_and_peripherals.workstation;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="280" y="200" width="80" height="60" as="geometry"/>
    </mxCell>

    <!-- Kali ATACANTE -->
    <mxCell id="7" value="Kali Linux&#xa;192.168.0.100&#xa;Atacante&#xa;Scripts B1-B6"
            style="shape=mxgraph.cisco.computers_and_peripherals.pc;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#f8cecc;strokeColor=#b85450;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="700" y="200" width="80" height="60" as="geometry"/>
    </mxCell>

    <!-- Suricata SENSOR -->
    <mxCell id="8" value="Ubuntu Suricata&#xa;192.168.0.110&#xa;SENSOR&#xa;ens35 (promiscuo)&#xa;Suricata 7.0.3&#xa;motor_decision.py&#xa;ipset/iptables"
            style="shape=mxgraph.cisco.servers.standard_server;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;
                   fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="460" y="480" width="80" height="80" as="geometry"/>
    </mxCell>

    <!-- Ubuntu SERVER -->
    <mxCell id="9" value="Ubuntu Server&#xa;192.168.0.120&#xa;nginx :80&#xa;OpenSSH :22&#xa;[Servicio]"
            style="shape=mxgraph.cisco.servers.standard_server;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#dae8fc;strokeColor=#6c8ebf;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="660" y="480" width="80" height="80" as="geometry"/>
    </mxCell>

    <!-- Telegram -->
    <mxCell id="10" value="Telegram Bot&#xa;(Alertas BLOCK/LIMIT)&#xa;🔴 Notificación push"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;
                   fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="480" width="140" height="60" as="geometry"/>
    </mxCell>

    <!-- Dashboard -->
    <mxCell id="11" value="Dashboard&#xa;dashboard.py&#xa;(terminal / Grafana)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;
                   fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="580" width="140" height="60" as="geometry"/>
    </mxCell>

    <!-- Analista SOC -->
    <mxCell id="12" value="Analista SOC&#xa;(monitoreo + respuesta)"
            style="shape=mxgraph.cisco.computers_and_peripherals.pc_man;
                   sketch=0;html=1;pointerEvents=1;dashed=0;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalLabelPosition=bottom;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="100" y="680" width="60" height="80" as="geometry"/>
    </mxCell>

    <!-- CONEXIONES: hosts al switch -->
    <mxCell id="20" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="5" target="4" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="21" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="6" target="4" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="22" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="7" target="4" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Switch al servidor -->
    <mxCell id="23" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="4" target="9" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Switch al sensor (port mirror) -->
    <mxCell id="24" value="port mirror"
            style="edgeStyle=orthogonalEdgeStyle;dashed=1;
                   endArrow=open;endFill=0;strokeColor=#FF8000;"
            edge="1" source="4" target="8" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Sensor al servidor (control inline) -->
    <mxCell id="25" value="ipset BLOCK&#xa;(DROP kernel)"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;
                   fontColor=#b85450;dashed=1;"
            edge="1" source="8" target="9" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Sensor al Telegram -->
    <mxCell id="26" value="Alertas&#xa;async"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#9673a6;"
            edge="1" source="8" target="10" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Sensor al Dashboard -->
    <mxCell id="27" value="motor_decision.log"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#d6b656;"
            edge="1" source="8" target="11" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- SOC a Telegram/Dashboard -->
    <mxCell id="28" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="10" target="12" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="29" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="11" target="12" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Diagrama 2 — Arquitectura Lógica (Flujo de Datos y Decisiones)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- TÍTULO -->
    <mxCell id="2" value="PPI-UPeU 2026 — Arquitectura Lógica (Flujo de Datos)"
            style="text;html=1;strokeColor=none;fillColor=none;align=center;
                   verticalAlign=middle;whiteSpace=wrap;rounded=0;
                   fontSize=14;fontStyle=1"
            vertex="1" parent="1">
      <mxGeometry x="150" y="20" width="870" height="30" as="geometry"/>
    </mxCell>

    <!-- PASO 1: TRÁFICO -->
    <mxCell id="10" value="1. Tráfico de Red&#xa;(paquetes raw)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="100" width="150" height="60" as="geometry"/>
    </mxCell>

    <!-- PASO 2: SURICATA -->
    <mxCell id="11" value="2. Suricata 7.0.3&#xa;ens35 (promiscuo)&#xa;Genera eventos flow"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="220" width="150" height="70" as="geometry"/>
    </mxCell>

    <!-- PASO 3: EVE.JSON -->
    <mxCell id="12" value="3. eve.json&#xa;{event_type:flow,&#xa; src_ip, bytes,&#xa; pkts, duration}"
            style="shape=document;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="360" width="150" height="70" as="geometry"/>
    </mxCell>

    <!-- PASO 4: PARSE + FEATURES -->
    <mxCell id="13" value="4. Data Engineering&#xa;parse_flow()&#xa;derive_features()&#xa;→ 14 features"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;"
            vertex="1" parent="1">
      <mxGeometry x="300" y="360" width="160" height="70" as="geometry"/>
    </mxCell>

    <!-- PASO 5: SCALER -->
    <mxCell id="14" value="5. StandardScaler&#xa;transform(X)&#xa;Z-score normaliz."
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;"
            vertex="1" parent="1">
      <mxGeometry x="510" y="360" width="150" height="70" as="geometry"/>
    </mxCell>

    <!-- PASO 6: ISOLATION FOREST -->
    <mxCell id="15" value="6. Isolation Forest&#xa;score_samples(X_sc)&#xa;score ∈ [-1, 0]"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=11;fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="710" y="360" width="150" height="70" as="geometry"/>
    </mxCell>

    <!-- PASO 7: CLASIFICACIÓN -->
    <mxCell id="16" value="7. Clasificación&#xa;τ1 = -0.4973&#xa;τ2 = -0.6873"
            style="rhombus;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;"
            vertex="1" parent="1">
      <mxGeometry x="710" y="500" width="150" height="100" as="geometry"/>
    </mxCell>

    <!-- OUTPUTS -->
    <mxCell id="17" value="PERMIT&#xa;score > τ1&#xa;(-0.4973)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=11;fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="560" y="650" width="100" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="18" value="LIMIT&#xa;τ2 &lt; score ≤ τ1&#xa;hashlimit 100p/s"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;
                   fontSize=11;fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="720" y="650" width="120" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="19" value="BLOCK&#xa;score ≤ τ2&#xa;(-0.6873) DROP"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#f8cecc;strokeColor=#b85450;
                   fontSize=11;fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="900" y="650" width="100" height="60" as="geometry"/>
    </mxCell>

    <!-- EFECTOS -->
    <mxCell id="30" value="Log acumulado&#xa;→ Reentrenamiento"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="560" y="770" width="110" height="50" as="geometry"/>
    </mxCell>

    <mxCell id="31" value="ipset ppi_limited&#xa;Telegram (amarillo)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="710" y="770" width="130" height="50" as="geometry"/>
    </mxCell>

    <mxCell id="32" value="ipset ppi_blocked&#xa;Telegram (rojo)&#xa;SIEM alert"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="890" y="770" width="120" height="50" as="geometry"/>
    </mxCell>

    <!-- WHITELIST (bypass) -->
    <mxCell id="33" value="WHITELIST&#xa;.20/.110/.120&#xa;127.0.0.1"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   dashed=1;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="300" y="500" width="110" height="60" as="geometry"/>
    </mxCell>

    <!-- HEURÍSTICAS -->
    <mxCell id="34" value="Detectores&#xa;Heurísticos&#xa;SSH BF / HTTP Abuse"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   dashed=1;fontSize=10;"
            vertex="1" parent="1">
      <mxGeometry x="460" y="500" width="130" height="60" as="geometry"/>
    </mxCell>

    <!-- ARISTAS -->
    <mxCell id="40" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="10" target="11" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="41" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="11" target="12" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="42" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="12" target="13" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="43" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="13" target="14" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="44" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="14" target="15" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="45" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="15" target="16" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Clasificador a outputs -->
    <mxCell id="46" value="score &gt; τ1"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#82b366;fontColor=#82b366;"
            edge="1" source="16" target="17" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="47" value="τ2 &lt; s ≤ τ1"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#d6b656;fontColor=#d6b656;"
            edge="1" source="16" target="18" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="48" value="score ≤ τ2"
            style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;fontColor=#b85450;"
            edge="1" source="16" target="19" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Outputs a efectos -->
    <mxCell id="49" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#9673a6;"
            edge="1" source="17" target="30" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="50" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#d6b656;"
            edge="1" source="18" target="31" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="51" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;"
            edge="1" source="19" target="32" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <!-- Whitelist bypass -->
    <mxCell id="52" value="whitelist?&#xa;→ PERMIT"
            style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#82b366;"
            edge="1" source="13" target="33" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Diagrama 3 — Arquitectura de Despliegue (Componentes en el Sensor)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- TÍTULO -->
    <mxCell id="2" value="PPI-UPeU 2026 — Arquitectura de Despliegue (Sensor 192.168.0.110)"
            style="text;html=1;strokeColor=none;fillColor=none;align=center;
                   verticalAlign=middle;whiteSpace=wrap;rounded=0;
                   fontSize=14;fontStyle=1"
            vertex="1" parent="1">
      <mxGeometry x="100" y="20" width="970" height="30" as="geometry"/>
    </mxCell>

    <!-- VM SENSOR (contenedor) -->
    <mxCell id="3" value="Ubuntu Server 22.04 LTS — 192.168.0.110&#xa;Intel Xeon Bronze 3204 / 4 cores / 7.8 GB RAM"
            style="swimlane;startSize=40;fillColor=#f5f5f5;strokeColor=#666666;
                   fontColor=#333333;fontSize=12;fontStyle=1;"
            vertex="1" parent="1">
      <mxGeometry x="80" y="80" width="1000" height="700" as="geometry"/>
    </mxCell>

    <!-- CAPA OS / KERNEL -->
    <mxCell id="4" value="KERNEL Linux 6.x — Netfilter (iptables + ipset)"
            style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="3">
      <mxGeometry x="20" y="60" width="960" height="120" as="geometry"/>
    </mxCell>

    <mxCell id="5" value="ipset ppi_blocked&#xa;(DROP)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
            vertex="1" parent="4">
      <mxGeometry x="100" y="40" width="130" height="50" as="geometry"/>
    </mxCell>

    <mxCell id="6" value="ipset ppi_limited&#xa;(LIMIT 100p/s)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
            vertex="1" parent="4">
      <mxGeometry x="280" y="40" width="130" height="50" as="geometry"/>
    </mxCell>

    <mxCell id="7" value="iptables FORWARD chain&#xa;DROP ppi_blocked&#xa;LIMIT ppi_limited"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;"
            vertex="1" parent="4">
      <mxGeometry x="460" y="30" width="160" height="65" as="geometry"/>
    </mxCell>

    <!-- CAPA SURICATA -->
    <mxCell id="8" value="Suricata 7.0.3 (systemd service)"
            style="swimlane;startSize=30;fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="3">
      <mxGeometry x="20" y="200" width="460" height="120" as="geometry"/>
    </mxCell>

    <mxCell id="9" value="ens35&#xa;(promiscuous)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;"
            vertex="1" parent="8">
      <mxGeometry x="30" y="40" width="100" height="50" as="geometry"/>
    </mxCell>

    <mxCell id="10" value="/var/log/suricata/&#xa;eve.json"
            style="shape=document;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
            vertex="1" parent="8">
      <mxGeometry x="300" y="35" width="120" height="55" as="geometry"/>
    </mxCell>

    <!-- CAPA PYTHON / MOTOR -->
    <mxCell id="11" value="Python 3.11 — ppi-sensor venv (scikit-learn 1.8.0)"
            style="swimlane;startSize=30;fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="3">
      <mxGeometry x="20" y="340" width="960" height="200" as="geometry"/>
    </mxCell>

    <mxCell id="12" value="motor_decision.py&#xa;(daemon — systemd)&#xa;tail -f eve.json"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="11">
      <mxGeometry x="30" y="40" width="150" height="65" as="geometry"/>
    </mxCell>

    <mxCell id="13" value="derive_features()&#xa;14 features&#xa;from raw fields"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;"
            vertex="1" parent="11">
      <mxGeometry x="220" y="40" width="120" height="65" as="geometry"/>
    </mxCell>

    <mxCell id="14" value="scaler.pkl&#xa;transform(X)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
            vertex="1" parent="11">
      <mxGeometry x="380" y="40" width="110" height="65" as="geometry"/>
    </mxCell>

    <mxCell id="15" value="isolation_forest.pkl&#xa;score_samples()&#xa;n=300 árboles"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="11">
      <mxGeometry x="530" y="40" width="140" height="65" as="geometry"/>
    </mxCell>

    <mxCell id="16" value="Clasificador&#xa;τ1/τ2&#xa;PERMIT/LIMIT/BLOCK"
            style="rhombus;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;"
            vertex="1" parent="11">
      <mxGeometry x="710" y="30" width="120" height="85" as="geometry"/>
    </mxCell>

    <mxCell id="17" value="enforce.sh&#xa;ipset add/del"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
            vertex="1" parent="11">
      <mxGeometry x="870" y="40" width="70" height="65" as="geometry"/>
    </mxCell>

    <!-- CAPA ALMACENAMIENTO -->
    <mxCell id="18" value="Almacenamiento — /home/m4rk/ppi-surikata-produto/"
            style="swimlane;startSize=30;fillColor=#e1d5e7;strokeColor=#9673a6;
                   fontSize=10;fontStyle=1;"
            vertex="1" parent="3">
      <mxGeometry x="20" y="560" width="960" height="110" as="geometry"/>
    </mxCell>

    <mxCell id="19" value="models/&#xa;isolation_forest.pkl&#xa;scaler.pkl"
            style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;"
            vertex="1" parent="18">
      <mxGeometry x="30" y="30" width="130" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="20" value="data/&#xa;train/val/test.csv&#xa;normal_flows_nuevos"
            style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;"
            vertex="1" parent="18">
      <mxGeometry x="210" y="30" width="130" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="21" value="results/&#xa;motor_decision.log&#xa;umbrales_finales.txt"
            style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;"
            vertex="1" parent="18">
      <mxGeometry x="390" y="30" width="130" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="22" value="docs/bitacora/&#xa;bitacora_escenarios.txt&#xa;(40 corridas F6)"
            style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;"
            vertex="1" parent="18">
      <mxGeometry x="570" y="30" width="130" height="60" as="geometry"/>
    </mxCell>

    <mxCell id="23" value="dashboard.py&#xa;motor_decision.log&#xa;refresh 3s"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;"
            vertex="1" parent="18">
      <mxGeometry x="750" y="30" width="120" height="60" as="geometry"/>
    </mxCell>

    <!-- ARISTAS internas -->
    <mxCell id="40" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="9" target="10" parent="8">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="41" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="10" target="12" parent="3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="42" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="12" target="13" parent="11">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="43" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="13" target="14" parent="11">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="44" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="14" target="15" parent="11">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="45" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="15" target="16" parent="11">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="46" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="16" target="17" parent="11">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="47" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;"
            edge="1" source="17" target="5" parent="3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Diagrama 4 — Arquitectura de Integración (Componentes e Interfaces)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <!-- TÍTULO -->
    <mxCell id="2" value="PPI-UPeU 2026 — Arquitectura de Integración (Interfaces entre Componentes)"
            style="text;html=1;strokeColor=none;fillColor=none;align=center;
                   verticalAlign=middle;whiteSpace=wrap;rounded=0;
                   fontSize=14;fontStyle=1"
            vertex="1" parent="1">
      <mxGeometry x="100" y="15" width="970" height="30" as="geometry"/>
    </mxCell>

    <!-- SURICATA -->
    <mxCell id="10" value="Suricata 7.0.3&#xa;——————————&#xa;IN:  paquetes raw (ens35)&#xa;OUT: eve.json (JSON lines)&#xa;——————————&#xa;Protocolo: file append&#xa;Formato: {event_type:flow,...}"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="60" y="80" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- DATA ENGINEERING -->
    <mxCell id="11" value="Data Engineering&#xa;——————————&#xa;IN:  línea JSON eve.json&#xa;OUT: ndarray (1, 14) float64&#xa;——————————&#xa;parse_flow(): 9 campos raw&#xa;derive_features(): 14 feat&#xa;fillna(0): sin NaN"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="310" y="80" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- SCALER -->
    <mxCell id="12" value="StandardScaler&#xa;——————————&#xa;IN:  ndarray (1, 14) raw&#xa;OUT: ndarray (1, 14) scaled&#xa;——————————&#xa;Fit: 684 flows normales&#xa;Transform: Z-score&#xa;Archivo: scaler.pkl (4KB)"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="560" y="80" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- ISOLATION FOREST -->
    <mxCell id="13" value="Isolation Forest&#xa;——————————&#xa;IN:  ndarray (1, 14) scaled&#xa;OUT: score float ∈ [-1, 0]&#xa;——————————&#xa;n_estimators=300&#xa;contamination=0.05&#xa;Archivo: .pkl 2.4MB&#xa;Latencia: 8–15ms"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#ffe6cc;strokeColor=#d79b00;
                   fontSize=10;fontStyle=1;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="810" y="80" width="200" height="170" as="geometry"/>
    </mxCell>

    <!-- CLASIFICADOR -->
    <mxCell id="14" value="Clasificador τ1/τ2&#xa;——————————&#xa;IN:  score float&#xa;OUT: {PERMIT,LIMIT,BLOCK}&#xa;——————————&#xa;τ1=-0.4973 (Youden)&#xa;τ2=-0.6873 (FPR≤2%)&#xa;+ Whitelist check&#xa;+ Heurística SSH/HTTP"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="560" y="310" width="200" height="170" as="geometry"/>
    </mxCell>

    <!-- ENFORCE -->
    <mxCell id="15" value="enforce.sh + ipset&#xa;——————————&#xa;IN:  IP + action + timeout&#xa;OUT: regla kernel activa&#xa;——————————&#xa;ipset add ppi_blocked IP&#xa;ipset add ppi_limited IP&#xa;iptables: DROP / LIMIT&#xa;Latencia kernel: &lt;1ms"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#f8cecc;strokeColor=#b85450;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="810" y="310" width="200" height="170" as="geometry"/>
    </mxCell>

    <!-- LOGGER -->
    <mxCell id="16" value="motor_decision.log&#xa;——————————&#xa;IN:  decisión + metadatos&#xa;OUT: línea structured log&#xa;——————————&#xa;TS | ACT | IP | SCORE&#xa;| PORT | LAT | DETECTOR&#xa;Rotación: logrotate diario"
            style="shape=document;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="310" y="310" width="200" height="170" as="geometry"/>
    </mxCell>

    <!-- TELEGRAM -->
    <mxCell id="17" value="Telegram Bot&#xa;——————————&#xa;IN:  IP + action + score&#xa;OUT: push notification&#xa;——————————&#xa;python-telegram-bot&#xa;Async (no bloquea motor)&#xa;Rate limit: 1msg/5s/IP&#xa;Latencia: 100–500ms"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#e1d5e7;strokeColor=#9673a6;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="810" y="550" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- DASHBOARD -->
    <mxCell id="18" value="dashboard.py&#xa;——————————&#xa;IN:  motor_decision.log&#xa;OUT: tabla ASCII terminal&#xa;——————————&#xa;Refresh: 3 segundos&#xa;Muestra: top IPs, latencia&#xa;           PERMIT/LIMIT/BLOCK&#xa;Extensible a Grafana"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#fff2cc;strokeColor=#d6b656;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="560" y="550" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- RETRAIN -->
    <mxCell id="19" value="batch_retrain.py&#xa;——————————&#xa;IN:  normal_flows_nuevos.csv&#xa;OUT: isolation_forest_vN.pkl&#xa;——————————&#xa;Trigger: ≥2,000 flows&#xa;4 Gates calidad&#xa;Deploy: symlink hot-reload&#xa;Rollback: automático"
            style="rounded=1;whiteSpace=wrap;html=1;
                   fillColor=#d5e8d4;strokeColor=#82b366;
                   fontSize=10;verticalAlign=top;"
            vertex="1" parent="1">
      <mxGeometry x="60" y="550" width="200" height="150" as="geometry"/>
    </mxCell>

    <!-- ARISTAS con etiquetas de interfaz -->
    <mxCell id="30" value="file tail&#xa;eve.json"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#d79b00;"
            edge="1" source="10" target="11" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="31" value="ndarray&#xa;(1,14) raw"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#82b366;"
            edge="1" source="11" target="12" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="32" value="ndarray&#xa;(1,14) scaled"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#82b366;"
            edge="1" source="12" target="13" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="33" value="score&#xa;float"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#d6b656;"
            edge="1" source="13" target="14" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="34" value="IP+action&#xa;+timeout"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#b85450;"
            edge="1" source="14" target="15" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="35" value="decisión&#xa;+metadatos"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#9673a6;"
            edge="1" source="14" target="16" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="36" value="BLOCK/LIMIT&#xa;async"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#9673a6;"
            edge="1" source="14" target="17" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="37" value="read log&#xa;cada 3s"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#d6b656;"
            edge="1" source="16" target="18" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="38" value="flows PERMIT&#xa;acumulados"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#82b366;dashed=1;"
            edge="1" source="16" target="19" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

    <mxCell id="39" value="nuevo modelo&#xa;hot-reload"
            style="edgeStyle=orthogonalEdgeStyle;fontSize=9;
                   strokeColor=#82b366;dashed=1;"
            edge="1" source="19" target="13" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## Notas de uso

- Los diagramas usan formas estándar de Draw.io (mxGraph) — no requieren plugins adicionales
- Para exportar como PNG/SVG: File → Export As desde la interfaz de Draw.io
- Para editar la topología de red en Diagrama 1, actualizar las IPs en los `value=""` de cada nodo
- Las líneas discontinuas (`dashed=1`) representan flujos futuros o propuestos
- Los colores siguen el código: Verde=#d5e8d4 (normal), Naranja=#ffe6cc (sensor/proceso), Rojo=#f8cecc (bloqueo), Amarillo=#fff2cc (control/umbral), Morado=#e1d5e7 (almacenamiento/notificación)
