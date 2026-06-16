# F5 — Diagrama: Control Inline e Integración

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="800" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="100" value="F5 — Control Inline e Integración · PPI UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="300" y="20" width="700" height="40" as="geometry"/></mxCell>
    <!-- Motor en sensor -->
    <mxCell id="2" value="&lt;b&gt;motor_decision.py&lt;/b&gt;&#xa;Sensor 192.168.0.110&#xa;systemd: ppi-motor.service&#xa;τ1=−0.4650 τ2=−0.6118" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="80" y="300" width="200" height="100" as="geometry"/></mxCell>
    <!-- SSH al servidor -->
    <mxCell id="3" value="SSH&#xa;(BatchMode, keys)" style="shape=mxgraph.cisco.connections.generic_connection;whiteSpace=wrap;html=1;fillColor=#666;strokeColor=#ffffff;" vertex="1" parent="1"><mxGeometry x="340" y="330" width="80" height="40" as="geometry"/></mxCell>
    <!-- ipset en servidor -->
    <mxCell id="4" value="&lt;b&gt;ipset — Servidor 192.168.0.120&lt;/b&gt;&#xa;ppi_blocked (hash:ip, timeout=300s)&#xa;ppi_limited (hash:ip, timeout=300s)&#xa;NOPASSWD sudo para m4rk" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="480" y="280" width="240" height="100" as="geometry"/></mxCell>
    <!-- iptables -->
    <mxCell id="5" value="&lt;b&gt;iptables INPUT — Servidor&lt;/b&gt;&#xa;Línea 1: -m set --match-set ppi_blocked src -j DROP&#xa;Línea 2: -m set --match-set ppi_limited src&#xa;         --hashlimit 100/s burst 150 -j ACCEPT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="480" y="440" width="310" height="90" as="geometry"/></mxCell>
    <!-- enforce.sh -->
    <mxCell id="6" value="&lt;b&gt;enforce.sh&lt;/b&gt;&#xa;Control manual&#xa;BLOCK / LIMIT / UNBLOCK&#xa;SSH → servidor → ipset" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="80" y="500" width="170" height="90" as="geometry"/></mxCell>
    <!-- Dashboard terminal -->
    <mxCell id="7" value="dashboard.py&#xa;Terminal (ANSI)&#xa;Lee motor_decision.log&#xa;Actualiza cada 3s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="1"><mxGeometry x="80" y="160" width="160" height="80" as="geometry"/></mxCell>
    <!-- Dashboard web -->
    <mxCell id="8" value="dashboard_web.py&#xa;Flask + SSE&#xa;http://192.168.0.110:8080&#xa;/api/stats /api/alerts&#xa;/api/stream (SSE)&#xa;/api/block /api/unblock" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="1"><mxGeometry x="280" y="140" width="180" height="110" as="geometry"/></mxCell>
    <!-- Browser -->
    <mxCell id="9" value="Navegador&#xa;Desktop 192.168.0.20" style="shape=mxgraph.cisco.computers_and_peripherals.pc;sketch=0;html=1;pointerEvents=1;dashed=0;fillColor=#036897;strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;" vertex="1" parent="1"><mxGeometry x="540" y="140" width="60" height="50" as="geometry"/></mxCell>
    <!-- Kali bloqueada -->
    <mxCell id="10" value="Kali 192.168.0.100&#xa;[BLOQUEADA]&#xa;Paquetes → DROP en servidor" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=3;" vertex="1" parent="1"><mxGeometry x="830" y="300" width="180" height="80" as="geometry"/></mxCell>
    <!-- Flechas -->
    <mxCell id="20" value="BLOCK/LIMIT" edge="1" source="2" target="3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="21" edge="1" source="3" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="22" edge="1" source="4" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="23" value="Lee log" edge="1" source="7" target="2" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="24" value="Lee log" edge="1" source="8" target="2" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="25" value="HTTP" edge="1" source="9" target="8" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="26" value="SSH→ipset" edge="1" source="6" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="27" value="DROP" edge="1" source="5" target="10" style="strokeColor=#b85450;dashed=1;" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
