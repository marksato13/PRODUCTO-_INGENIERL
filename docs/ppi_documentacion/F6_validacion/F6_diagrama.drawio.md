# F6 — Diagrama: Validación del Sistema (40 Corridas)

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="900" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="100" value="F6 — Validación del Sistema · 40 Corridas · PPI UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="300" y="20" width="700" height="40" as="geometry"/></mxCell>
    <!-- f6_corridas.py -->
    <mxCell id="2" value="&lt;b&gt;f6_corridas.py&lt;/b&gt;&#xa;Orquestador de 40 corridas&#xa;SSH a Kali para lanzar ataques&#xa;Lee motor_decision.log&#xa;Calcula métricas por corrida" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="80" y="300" width="200" height="110" as="geometry"/></mxCell>
    <!-- 4 grupos -->
    <mxCell id="3" value="&lt;b&gt;Grupo Normal (1–10)&lt;/b&gt;&#xa;Tráfico normal Desktop&#xa;Verifica: ITL=0%, Disp=100%&#xa;Esperado: flows_anom=0" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="1"><mxGeometry x="360" y="120" width="180" height="90" as="geometry"/></mxCell>
    <mxCell id="4" value="&lt;b&gt;Grupo Mixto (11–20)&lt;/b&gt;&#xa;Normal + Ataques alternados&#xa;Corrida 11: primera detección&#xa;Lead Time = 61.92s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;" vertex="1" parent="1"><mxGeometry x="360" y="250" width="180" height="90" as="geometry"/></mxCell>
    <mxCell id="5" value="&lt;b&gt;Grupo Reeval (21–30)&lt;/b&gt;&#xa;Re-evaluación con IP bloqueada&#xa;Motor retiene en memoria&#xa;flows_anom=0 (correcto)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;" vertex="1" parent="1"><mxGeometry x="360" y="380" width="180" height="90" as="geometry"/></mxCell>
    <mxCell id="6" value="&lt;b&gt;Grupo Final (31–40)&lt;/b&gt;&#xa;Confirmación de contención&#xa;IP atacante bloqueada todo el tiempo&#xa;Disp=100% confirmada" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="360" y="510" width="180" height="90" as="geometry"/></mxCell>
    <!-- CSVs -->
    <mxCell id="7" value="resultados_f6_completo.csv&#xa;40 corridas × 18 campos&#xa;results/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;fontSize=10;" vertex="1" parent="1"><mxGeometry x="620" y="310" width="160" height="80" as="geometry"/></mxCell>
    <!-- Graficas -->
    <mxCell id="8" value="generar_graficas_f6.py&#xa;7 figuras PNG 300 DPI&#xa;results/graficas_f6/" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="620" y="460" width="160" height="70" as="geometry"/></mxCell>
    <!-- Métricas finales -->
    <mxCell id="9" value="&lt;b&gt;MÉTRICAS FINALES&lt;/b&gt;&#xa;Disponibilidad: 100% (40/40)&#xa;ITL: 0% (40/40)&#xa;Lead Time: 61.92 s (corrida 11)&#xa;Flows procesados: 312,500&#xa;Latencia P95: 34.8 ms&#xa;AUC-ROC: 0.8955" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="870" y="280" width="210" height="150" as="geometry"/></mxCell>
    <!-- Timeline corrida 11 -->
    <mxCell id="10" value="Corrida 11 — SYN Flood&#xa;t=0s: inicio corrida&#xa;t=15s: ataque inicia&#xa;t=61.9s: SOSPECHOSO → LIMIT&#xa;t=62.5s: HTTP-ABUSE → BLOCK&#xa;t=300s: fin corrida&#xa;Disp=100% todo el tiempo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;align=left;" vertex="1" parent="1"><mxGeometry x="620" y="160" width="210" height="120" as="geometry"/></mxCell>
    <!-- Flechas -->
    <mxCell id="20" edge="1" source="2" target="3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="21" edge="1" source="2" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="22" edge="1" source="2" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="23" edge="1" source="2" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="24" edge="1" source="2" target="7" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="25" edge="1" source="7" target="8" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="26" edge="1" source="7" target="9" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="27" edge="1" source="4" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
