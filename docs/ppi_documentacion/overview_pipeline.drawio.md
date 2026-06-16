# Overview — Pipeline completo F1 → F6

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="600" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="700" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="2" value="F1&#xa;Entorno&#xa;Laboratorio" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="40" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="3" value="F2&#xa;Captura&#xa;Tráfico" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="260" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="4" value="F3&#xa;Modelado&#xa;Offline (IF)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="480" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="5" value="F4&#xa;Motor de&#xa;Decisión" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="700" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="6" value="F5&#xa;Control&#xa;Inline" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="920" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="7" value="F6&#xa;Validación&#xa;(40 corridas)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="1140" y="280" width="160" height="80" as="geometry"/></mxCell>
    <mxCell id="8" edge="1" source="2" target="3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="9" edge="1" source="3" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="10" edge="1" source="4" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="11" edge="1" source="5" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="12" edge="1" source="6" target="7" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="13" value="eve.json.gz&#xa;(51 archivos)" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;" vertex="1" parent="1"><mxGeometry x="310" y="160" width="120" height="60" as="geometry"/></mxCell>
    <mxCell id="14" value="train/val/test.csv&#xa;isolation_forest.pkl" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;" vertex="1" parent="1"><mxGeometry x="490" y="160" width="150" height="60" as="geometry"/></mxCell>
    <mxCell id="15" value="τ1=−0.4650&#xa;τ2=−0.6118" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;" vertex="1" parent="1"><mxGeometry x="710" y="160" width="120" height="60" as="geometry"/></mxCell>
    <mxCell id="16" value="resultados_f6_completo.csv&#xa;7 gráficas PNG" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;" vertex="1" parent="1"><mxGeometry x="1130" y="160" width="170" height="60" as="geometry"/></mxCell>
    <mxCell id="17" value="PPI — Universidad Peruana Unión 2026&#xa;Sistema de Detección Temprana de Anomalías en Redes" style="text;html=1;align=center;fontStyle=1;fontSize=14;" vertex="1" parent="1"><mxGeometry x="350" y="40" width="700" height="60" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
