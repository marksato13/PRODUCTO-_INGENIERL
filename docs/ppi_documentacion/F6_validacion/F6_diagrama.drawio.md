# F6 — Diagrama: Validacion 40 Corridas

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- TÍTULO -->
    <mxCell id="2" value="F6 — Validación del Sistema Completo: 40 Corridas con Motor ACTIVO" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=20;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="20" width="1520" height="45" as="geometry" />
    </mxCell>

    <!-- PRE-REQUISITO BANNER -->
    <mxCell id="3" value="&lt;b&gt;Pre-requisito:&lt;/b&gt;  ppi-motor.service ACTIVO | isolation_forest.pkl + scaler.pkl cargados | τ1=−0.4459 y τ2=−0.6027 leídos de metricas_offline.txt | ipsets ppi_blocked/ppi_limited inicializados en servidor .120" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF8000;strokeColor=#CC5500;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="73" width="1520" height="50" as="geometry" />
    </mxCell>

    <!-- F6_CORRIDAS.PY -->
    <mxCell id="4" value="&lt;b&gt;f6_corridas.py&lt;/b&gt;&lt;br&gt;&lt;br&gt;Orquesta 40 corridas en 4 grupos&lt;br&gt;300s/corrida | 60s pausa entre corridas&lt;br&gt;~4 horas duración total&lt;br&gt;Lee motor_decision.log para métricas" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="60" y="140" width="310" height="110" as="geometry" />
    </mxCell>

    <!-- CONFIG NOTE -->
    <mxCell id="5" value="Por corrida:&lt;br&gt;• Desktop genera tráfico HTTP/SSH (todos los grupos)&lt;br&gt;• Kali lanza SYN Flood SOLO en corrida 11&lt;br&gt;• Motor procesa flows en tiempo real&lt;br&gt;• f6_corridas.py espera 300s y lee el log" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;align=left;spacingLeft=8;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="395" y="140" width="340" height="110" as="geometry" />
    </mxCell>

    <!-- MOTOR_DECISION.LOG (durante F6) -->
    <mxCell id="6" value="motor_decision.log&lt;br&gt;&lt;i&gt;escrito en tiempo real&lt;br&gt;por el motor activo&lt;/i&gt;&lt;br&gt;leído por f6_corridas.py" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="765" y="140" width="195" height="110" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- GRUPO NORMAL — Corridas 1-10 -->
    <!-- ============================================================ -->
    <mxCell id="7" value="&lt;b&gt;GRUPO NORMAL&lt;/b&gt;&lt;br&gt;Corridas 1–10&lt;br&gt;&lt;br&gt;Solo Desktop (.20) genera tráfico&lt;br&gt;HTTP/SSH legítimo → nginx/SSH&lt;br&gt;&lt;br&gt;Motor: solo flujos PERMIT&lt;br&gt;flows_anom = 0&lt;br&gt;bloqueados = 0&lt;br&gt;disponibilidad = 1 (100%)&lt;br&gt;itl_pct = 0%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
      <mxGeometry x="60" y="285" width="310" height="255" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- GRUPO MIXTO — Corridas 11-20 -->
    <!-- ============================================================ -->
    <mxCell id="8" value="&lt;b&gt;GRUPO MIXTO&lt;/b&gt;&lt;br&gt;Corridas 11–20" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFE0B2;strokeColor=#E65100;fontSize=12;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
      <mxGeometry x="390" y="285" width="340" height="255" as="geometry" />
    </mxCell>

    <!-- Corrida 11 — DETECCIÓN (destacada) -->
    <mxCell id="9" value="&lt;b&gt;Corrida 11 — SYN Flood (DETECCIÓN)&lt;/b&gt;&lt;br&gt;Kali lanza hping3 -S --flood → :80&lt;br&gt;t=0s inicio ataque&lt;br&gt;t=61.92s → LIMIT → BLOCK&lt;br&gt;&lt;b&gt;Lead Time = 61.92 s&lt;/b&gt; (timeout Suricata TCP)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="400" y="340" width="320" height="100" as="geometry" />
    </mxCell>

    <!-- Corridas 12-20 -->
    <mxCell id="10" value="Corridas 12–20:&lt;br&gt;&lt;i&gt;flows_anom=0 (CORRECTO)&lt;/i&gt;&lt;br&gt;IP .100 retenida en set&lt;br&gt;&lt;b&gt;bloqueados&lt;/b&gt; en memoria del motor&lt;br&gt;→ log a nivel DEBUG, no WARNING&lt;br&gt;disponibilidad=1 en todas" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#E65100;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="400" y="450" width="320" height="80" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- GRUPO REEVAL — Corridas 21-30 -->
    <!-- ============================================================ -->
    <mxCell id="11" value="&lt;b&gt;GRUPO REEVAL&lt;/b&gt;&lt;br&gt;Corridas 21–30&lt;br&gt;&lt;br&gt;Kali sigue bloqueada en&lt;br&gt;memoria IF (sin reiniciar motor)&lt;br&gt;&lt;br&gt;Re-evaluación de contención&lt;br&gt;flows_anom = 0&lt;br&gt;bloqueados = 1 (Kali .100)&lt;br&gt;disponibilidad = 1&lt;br&gt;itl_pct = 0%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
      <mxGeometry x="750" y="285" width="310" height="255" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- GRUPO FINAL — Corridas 31-40 -->
    <!-- ============================================================ -->
    <mxCell id="12" value="&lt;b&gt;GRUPO FINAL&lt;/b&gt;&lt;br&gt;Corridas 31–40&lt;br&gt;&lt;br&gt;Confirmación de contención total&lt;br&gt;Kali permanece bloqueada&lt;br&gt;&lt;br&gt;flows_anom = 0&lt;br&gt;disponibilidad = 1&lt;br&gt;itl_pct = 0%&lt;br&gt;&lt;br&gt;40/40 corridas exitosas ✓" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#003366;fontSize=11;verticalAlign=top;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="1080" y="285" width="310" height="255" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- CONECTORES F6_CORRIDAS → GRUPOS -->
    <!-- ============================================================ -->
    <mxCell id="13" value="corridas 1-10" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;strokeColor=#82b366;strokeWidth=2;fontSize=10;fontColor=#82b366;" edge="1" source="4" target="7" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="14" value="corrida 11" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.7;exitY=1;exitDx=0;exitDy=0;entryX=0.3;entryY=0;entryDx=0;entryDy=0;strokeColor=#E65100;strokeWidth=2;fontSize=10;fontColor=#E65100;" edge="1" source="4" target="8" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="15" value="corridas 21-30" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#9673a6;strokeWidth=2;fontSize=10;fontColor=#9673a6;" edge="1" source="4" target="11" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="16" value="corridas 31-40" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.7;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#003366;strokeWidth=2;fontSize=10;fontColor=#003366;" edge="1" source="4" target="12" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- CONECTOR: f6_corridas → log -->
    <mxCell id="17" value="lee cada 300s" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.15;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontColor=#8B6914;" edge="1" source="4" target="6" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- OUTPUTS -->
    <!-- ============================================================ -->
    <!-- resultados_f6_completo.csv -->
    <mxCell id="18" value="&lt;b&gt;resultados_f6_completo.csv&lt;/b&gt;&lt;br&gt;41 líneas (header + 40 corridas)&lt;br&gt;Columnas: corrida, grupo, disponibilidad,&lt;br&gt;flows_anom, bloqueados, lead_time_s, itl_pct..." style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="60" y="575" width="310" height="100" as="geometry" />
    </mxCell>

    <!-- generar_graficas_f6.py -->
    <mxCell id="19" value="&lt;b&gt;generar_graficas_f6.py&lt;/b&gt;&lt;br&gt;&lt;br&gt;Lee resultados_f6_completo.csv&lt;br&gt;Genera 7 figuras matplotlib 300 DPI" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="400" y="585" width="250" height="80" as="geometry" />
    </mxCell>

    <!-- 7 PNGs -->
    <mxCell id="20" value="&lt;b&gt;7 figuras PNG 300 DPI&lt;/b&gt;&lt;br&gt;f6_01 Disponibilidad (40 barras verdes)&lt;br&gt;f6_02 Flows anómalos (corrida 11)&lt;br&gt;f6_03 Timeline detección SYN Flood&lt;br&gt;f6_04 ITL=0% todas las corridas&lt;br&gt;f6_05 Flujos normales acumulados&lt;br&gt;f6_06 Latencia pipeline (34-39ms)&lt;br&gt;f6_07 Panel ejecutivo 2×3" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;align=left;spacingLeft=6;" vertex="1" parent="1">
      <mxGeometry x="675" y="565" width="285" height="135" as="geometry" />
    </mxCell>

    <!-- CONECTORES outputs -->
    <mxCell id="21" value="escribe" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.3;entryY=0;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;fontSize=10;" edge="1" source="6" target="18" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="22" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#6c8ebf;" edge="1" source="18" target="19" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="23" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="19" target="20" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- MÉTRICAS FINALES -->
    <!-- ============================================================ -->
    <mxCell id="24" value="&lt;b&gt;RESULTADOS FINALES VALIDADOS (F6 — 2026-06-16)&lt;/b&gt;&lt;br&gt;&lt;br&gt;Disponibilidad: &lt;b&gt;100%&lt;/b&gt; (40/40 corridas) ✓  |  ITL global: &lt;b&gt;0%&lt;/b&gt; ✓  |  Lead Time detección SYN Flood: &lt;b&gt;61.92 s&lt;/b&gt; (req. &lt; 120 s) ✓&lt;br&gt;Latencia P95 por flow: &lt;b&gt;34.8 ms&lt;/b&gt; (req. &lt; 500 ms) ✓  |  AUC-ROC: &lt;b&gt;0.8998&lt;/b&gt; (req. ≥ 0.85) ✓  |  Corridas exitosas: &lt;b&gt;40/40&lt;/b&gt; ✓" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#003366;strokeColor=#001a33;fontSize=13;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="720" width="1380" height="90" as="geometry" />
    </mxCell>

    <!-- NOTA LEAD TIME -->
    <mxCell id="25" value="&lt;i&gt;Lead Time 61.92s = timeout Suricata para flows TCP half-open (~60s)&lt;br&gt;El motor actúa en 34ms al recibir el evento — la espera es del sensor IDS&lt;/i&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;fontColor=#666666;fontStyle=2;" vertex="1" parent="1">
      <mxGeometry x="60" y="818" width="600" height="35" as="geometry" />
    </mxCell>

    <!-- ============================================================ -->
    <!-- LEYENDA -->
    <!-- ============================================================ -->
    <mxCell id="26" value="Leyenda" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="860" width="80" height="22" as="geometry" />
    </mxCell>
    <mxCell id="27" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="60" y="888" width="16" height="16" as="geometry" />
    </mxCell>
    <mxCell id="28" value="Grupo Normal (solo tráfico legítimo)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="81" y="888" width="220" height="16" as="geometry" />
    </mxCell>
    <mxCell id="29" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFE0B2;strokeColor=#E65100;" vertex="1" parent="1">
      <mxGeometry x="315" y="888" width="16" height="16" as="geometry" />
    </mxCell>
    <mxCell id="30" value="Grupo Mixto (ataque en corrida 11)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="336" y="888" width="210" height="16" as="geometry" />
    </mxCell>
    <mxCell id="31" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="560" y="888" width="16" height="16" as="geometry" />
    </mxCell>
    <mxCell id="32" value="Corrida 11 — detección SYN Flood" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="581" y="888" width="205" height="16" as="geometry" />
    </mxCell>
    <mxCell id="33" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
      <mxGeometry x="800" y="888" width="16" height="16" as="geometry" />
    </mxCell>
    <mxCell id="34" value="Grupo Reeval (contención en memoria)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="821" y="888" width="215" height="16" as="geometry" />
    </mxCell>
    <mxCell id="35" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="1050" y="888" width="16" height="16" as="geometry" />
    </mxCell>
    <mxCell id="36" value="Grupo Final (confirmación total)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="1071" y="888" width="190" height="16" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```
