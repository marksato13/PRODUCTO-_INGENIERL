# F1 — Diagrama: Topología de Red del Laboratorio

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <!-- Switch / Red 192.168.0.x -->
    <mxCell id="10" value="Switch&#xa;192.168.0.x" style="shape=mxgraph.cisco.switches.workgroup_switch;sketch=0;html=1;pointerEvents=1;dashed=0;fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;" vertex="1" parent="1"><mxGeometry x="500" y="340" width="60" height="50" as="geometry"/></mxCell>
    <!-- Win11 Cliente -->
    <mxCell id="2" value="&lt;b&gt;Win11 Cliente&lt;/b&gt;&#xa;192.168.0.10&#xa;Genera tráfico cliente" style="shape=mxgraph.cisco.computers_and_peripherals.pc;sketch=0;html=1;pointerEvents=1;dashed=0;fillColor=#036897;strokeColor=#ffffff;strokeWidth=2;verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;" vertex="1" parent="1"><mxGeometry x="120" y="160" width="60" height="50" as="geometry"/></mxCell>
    <!-- Ubuntu Desktop Admin -->
    <mxCell id="3" value="&lt;b&gt;Ubuntu Desktop&lt;/b&gt;&#xa;192.168.0.20 [ADMIN]&#xa;Tráfico normal A1-A4&#xa;Claude Code corre aquí" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="320" y="140" width="160" height="80" as="geometry"/></mxCell>
    <!-- Kali Linux -->
    <mxCell id="4" value="&lt;b&gt;Kali Linux&lt;/b&gt;&#xa;192.168.0.100&#xa;Ataques B1-B6&#xa;hping3 / nmap / hydra" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="120" y="420" width="160" height="80" as="geometry"/></mxCell>
    <!-- Ubuntu Sensor -->
    <mxCell id="5" value="&lt;b&gt;Ubuntu Sensor&lt;/b&gt;&#xa;192.168.0.110&#xa;Suricata 7.0.3 (ens35)&#xa;motor_decision.py&#xa;/var/log/suricata/eve.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="600" y="160" width="180" height="100" as="geometry"/></mxCell>
    <!-- Ubuntu Server -->
    <mxCell id="6" value="&lt;b&gt;Ubuntu Server&lt;/b&gt;&#xa;192.168.0.120&#xa;nginx :80 / SSH :22&#xa;ipset ppi_blocked&#xa;iptables DROP/LIMIT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="600" y="420" width="180" height="100" as="geometry"/></mxCell>
    <!-- Conexiones al switch -->
    <mxCell id="20" edge="1" source="2" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="21" edge="1" source="3" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="22" edge="1" source="4" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="23" edge="1" source="5" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="24" edge="1" source="6" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <!-- SSH keys -->
    <mxCell id="30" value="SSH keys" style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#82b366;" edge="1" source="3" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="31" value="SSH keys" style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#82b366;" edge="1" source="3" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <!-- Suricata captura -->
    <mxCell id="32" value="captura ens35" style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#d6b656;" edge="1" source="5" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <!-- Titulo -->
    <mxCell id="40" value="F1 — Topología del Laboratorio PPI · UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="300" y="40" width="500" height="40" as="geometry"/></mxCell>
    <!-- Leyenda -->
    <mxCell id="41" value="🔴 Fuente de ataques  🟡 Sensor/Motor  🔵 Servicio objetivo  🟢 Admin" style="text;html=1;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="60" y="580" width="600" height="30" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
