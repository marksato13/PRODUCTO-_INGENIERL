# F4 — Diagrama: Motor de Decisión en Tiempo Real

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="900" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="100" value="F4 — Motor de Decisión en Tiempo Real · PPI UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="300" y="20" width="700" height="40" as="geometry"/></mxCell>
    <!-- Entrada -->
    <mxCell id="2" value="eve.json&#xa;(tail -f en tiempo real)&#xa;/var/log/suricata/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="40" y="360" width="140" height="80" as="geometry"/></mxCell>
    <!-- Parser flow -->
    <mxCell id="3" value="Parsear flow&#xa;type=flow&#xa;→ extraer campos" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1"><mxGeometry x="250" y="360" width="140" height="70" as="geometry"/></mxCell>
    <!-- Features -->
    <mxCell id="4" value="Extracción&#xa;14 features&#xa;(pkts, bytes, rates,&#xa;ratios, flags, port)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1"><mxGeometry x="460" y="340" width="140" height="90" as="geometry"/></mxCell>
    <!-- Scaler -->
    <mxCell id="5" value="StandardScaler&#xa;transform(x)&#xa;scaler.pkl" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1"><mxGeometry x="670" y="360" width="130" height="70" as="geometry"/></mxCell>
    <!-- IF Score -->
    <mxCell id="6" value="IsolationForest&#xa;score_samples(x)&#xa;isolation_forest.pkl&#xa;→ score ∈ [−1, 0]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="870" y="340" width="150" height="90" as="geometry"/></mxCell>
    <!-- Whitelist check -->
    <mxCell id="7" value="¿IP en whitelist?&#xa;{.20, .110, .120, ...}" style="rhombus;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="1090" y="340" width="140" height="90" as="geometry"/></mxCell>
    <!-- Ignorar -->
    <mxCell id="8" value="IGNORAR&#xa;(no acción)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1"><mxGeometry x="1090" y="220" width="130" height="60" as="geometry"/></mxCell>
    <!-- Decision tree -->
    <mxCell id="9" value="score > τ1 (−0.4650)?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;" vertex="1" parent="1"><mxGeometry x="1090" y="480" width="150" height="80" as="geometry"/></mxCell>
    <mxCell id="10" value="PERMIT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="1320" y="480" width="100" height="50" as="geometry"/></mxCell>
    <mxCell id="11" value="score > τ2 (−0.6118)?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="1"><mxGeometry x="1090" y="610" width="150" height="80" as="geometry"/></mxCell>
    <mxCell id="12" value="LIMIT&#xa;hashlimit 100pkt/s&#xa;ipset ppi_limited" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="1320" y="610" width="120" height="70" as="geometry"/></mxCell>
    <mxCell id="13" value="BLOCK&#xa;DROP&#xa;ipset ppi_blocked" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="1090" y="750" width="150" height="70" as="geometry"/></mxCell>
    <!-- Detectores heurísticos -->
    <mxCell id="14" value="&lt;b&gt;Detector SSH BruteForce&lt;/b&gt;&#xa;15 intentos/60s → BLOCK&#xa;5 intentos/60s → LIMIT&#xa;Puerto: TCP/22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;align=left;" vertex="1" parent="1"><mxGeometry x="250" y="160" width="180" height="90" as="geometry"/></mxCell>
    <mxCell id="15" value="&lt;b&gt;Detector HTTP Abuse&lt;/b&gt;&#xa;100 req/30s → BLOCK&#xa;50 req/30s → LIMIT&#xa;Puerto: TCP/80" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;align=left;" vertex="1" parent="1"><mxGeometry x="460" y="160" width="180" height="90" as="geometry"/></mxCell>
    <!-- Log -->
    <mxCell id="16" value="motor_decision.log&#xa;results/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;fontSize=10;" vertex="1" parent="1"><mxGeometry x="670" y="160" width="130" height="60" as="geometry"/></mxCell>
    <!-- Latencia -->
    <mxCell id="17" value="Latencia P95: 34.8 ms&#xa;Throughput: 29 flows/s&#xa;Requisito &lt;500 ms: CUMPLE" style="text;html=1;align=left;fontSize=10;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1"><mxGeometry x="40" y="560" width="200" height="60" as="geometry"/></mxCell>
    <!-- Flechas -->
    <mxCell id="30" edge="1" source="2" target="3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="31" edge="1" source="3" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="32" edge="1" source="4" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="33" edge="1" source="5" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="34" edge="1" source="6" target="7" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="35" value="Sí" edge="1" source="7" target="8" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="36" value="No" edge="1" source="7" target="9" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="37" value="Sí" edge="1" source="9" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="38" value="No" edge="1" source="9" target="11" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="39" value="Sí" edge="1" source="11" target="12" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="40" value="No" edge="1" source="11" target="13" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
