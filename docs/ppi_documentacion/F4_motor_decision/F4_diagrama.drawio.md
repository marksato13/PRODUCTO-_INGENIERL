# F4 — Diagrama: Motor de Decision

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- TÍTULO -->
    <mxCell id="2" value="F4 — Motor de Decisión en Tiempo Real (motor_decision.py)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=20;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="20" width="1520" height="45" as="geometry" />
    </mxCell>

    <!-- ===== SECCIÓN STARTUP (fila superior) ===== -->
    <mxCell id="3" value="&lt;b&gt;Al arrancar ppi-motor.service&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="73" width="300" height="22" as="geometry" />
    </mxCell>

    <!-- metricas_offline.txt -->
    <mxCell id="4" value="&lt;b&gt;metricas_offline.txt&lt;/b&gt;&lt;br&gt;Lee τ1 = −0.4459&lt;br&gt;Lee τ2 = −0.6027" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF8000;strokeColor=#CC5500;fontSize=11;fontColor=#FFFFFF;" vertex="1" parent="1">
      <mxGeometry x="60" y="98" width="210" height="75" as="geometry" />
    </mxCell>

    <!-- Models group -->
    <mxCell id="5" value="isolation_forest.pkl&lt;br&gt;scaler.pkl&lt;br&gt;features.csv&lt;br&gt;&lt;i&gt;(cargados en memoria)&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="295" y="98" width="195" height="75" as="geometry" />
    </mxCell>

    <!-- systemd service -->
    <mxCell id="6" value="ppi-motor.service&lt;br&gt;&lt;i&gt;systemd — auto-restart&lt;/i&gt;&lt;br&gt;WorkingDirectory=/home/m4rk/ppi-surikata-producto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;fontColor=#333333;" vertex="1" parent="1">
      <mxGeometry x="515" y="98" width="225" height="75" as="geometry" />
    </mxCell>

    <!-- WHITELIST label -->
    <mxCell id="7" value="&lt;b&gt;WHITELIST&lt;/b&gt; (hardcoded)&lt;br&gt;.1 .20 .110 .120 .130 .140 127.0.0.1&lt;br&gt;&lt;i&gt;nunca se bloquean&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e6f3ff;strokeColor=#4488aa;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="760" y="98" width="245" height="75" as="geometry" />
    </mxCell>

    <!-- ===== INPUT: eve.json ===== -->
    <mxCell id="8" value="&lt;b&gt;/var/log/suricata/eve.json&lt;/b&gt;&lt;br&gt;tail -f (línea a línea)&lt;br&gt;&lt;br&gt;Suricata 7.0.3&lt;br&gt;ens35 — sensor .110" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="60" y="240" width="200" height="130" as="geometry" />
    </mxCell>

    <!-- ===== MOTOR_DECISION.PY — caja principal ===== -->
    <mxCell id="9" value="&lt;b&gt;motor_decision.py — bucle principal&lt;/b&gt;&lt;br&gt;&lt;br&gt;Para cada línea de eve.json:&lt;br&gt;  1. Parsear JSON → solo event_type = &apos;flow&apos;&lt;br&gt;  2. Extraer 14 features (pkts, bytes, duration, rates...)&lt;br&gt;  3. Verificar ip_origen ∈ WHITELIST → IGNORAR si aplica&lt;br&gt;  4. X_scaled = scaler.transform(features)&lt;br&gt;  5. score = IF.score_samples(X_scaled)  [rango: −1 a 0]&lt;br&gt;&lt;br&gt;  ─── Decisión triple ───&lt;br&gt;  score &gt; τ1 (−0.4459) → &lt;b&gt;PERMIT&lt;/b&gt;   (log DEBUG, sin acción)&lt;br&gt;  τ2 &lt; score ≤ τ1      → &lt;b&gt;LIMIT&lt;/b&gt;    (log WARNING + enforce.sh)&lt;br&gt;  score ≤ τ2 (−0.6027) → &lt;b&gt;BLOCK&lt;/b&gt;    (log WARNING + enforce.sh)&lt;br&gt;&lt;br&gt;  Estadísticas cada 500 flows → motor_decision.log" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=10;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="315" y="225" width="455" height="290" as="geometry" />
    </mxCell>

    <!-- ===== DECISIONES SALIDA ===== -->
    <mxCell id="10" value="&lt;b&gt;PERMIT&lt;/b&gt;&lt;br&gt;Tráfico normal&lt;br&gt;score &gt; −0.4459&lt;br&gt;log DEBUG" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="830" y="240" width="155" height="80" as="geometry" />
    </mxCell>
    <mxCell id="11" value="&lt;b&gt;LIMIT&lt;/b&gt;&lt;br&gt;Sospechoso&lt;br&gt;−0.6027 &lt; score ≤ −0.4459&lt;br&gt;hashlimit 100 pkt/s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=11;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="830" y="340" width="155" height="80" as="geometry" />
    </mxCell>
    <mxCell id="12" value="&lt;b&gt;BLOCK&lt;/b&gt;&lt;br&gt;Anómalo confirmado&lt;br&gt;score ≤ −0.6027&lt;br&gt;iptables DROP" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="830" y="440" width="155" height="80" as="geometry" />
    </mxCell>

    <!-- ===== ENFORCE.SH ===== -->
    <mxCell id="13" value="&lt;b&gt;enforce.sh&lt;/b&gt;&lt;br&gt;SSH → m4rk@192.168.0.120&lt;br&gt;sudo ipset add/del&lt;br&gt;timeout: 300s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1045" y="355" width="185" height="85" as="geometry" />
    </mxCell>

    <!-- ===== SERVIDOR 192.168.0.120 (contenedor) ===== -->
    <mxCell id="14" value="&lt;b&gt;Servidor 192.168.0.120&lt;/b&gt;&lt;br&gt;nginx:80 | SSH:22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
      <mxGeometry x="1290" y="230" width="275" height="260" as="geometry" />
    </mxCell>
    <!-- ipset ppi_limited -->
    <mxCell id="15" value="&lt;b&gt;ipset ppi_limited&lt;/b&gt;&lt;br&gt;hashlimit 100 pkt/s&lt;br&gt;(timeout 300s)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1310" y="270" width="235" height="75" as="geometry" />
    </mxCell>
    <!-- ipset ppi_blocked -->
    <mxCell id="16" value="&lt;b&gt;ipset ppi_blocked&lt;/b&gt;&lt;br&gt;iptables DROP&lt;br&gt;(timeout 300s)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1310" y="375" width="235" height="75" as="geometry" />
    </mxCell>

    <!-- ===== DETECTORES HEURÍSTICOS ===== -->
    <mxCell id="17" value="&lt;b&gt;Detectores heurísticos&lt;/b&gt; (paralelo al score IF)&lt;br&gt;&lt;br&gt;SSH Brute Force (TCP/22):&lt;br&gt;  ventana 60s | ≥5 intentos → LIMIT | ≥15 → BLOCK&lt;br&gt;&lt;br&gt;HTTP Abuse (TCP/80):&lt;br&gt;  ventana 30s | ≥50 req → LIMIT | ≥100 → BLOCK&lt;br&gt;&lt;br&gt;&lt;i&gt;Detectan ataques con score IF moderado&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;align=left;spacingLeft=8;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="315" y="575" width="390" height="145" as="geometry" />
    </mxCell>

    <!-- ===== MOTOR LOG ===== -->
    <mxCell id="18" value="&lt;b&gt;motor_decision.log&lt;/b&gt;&lt;br&gt;&lt;br&gt;PERMIT → DEBUG&lt;br&gt;LIMIT/BLOCK → WARNING&lt;br&gt;Stats cada 500 flows → INFO" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="760" y="585" width="200" height="120" as="geometry" />
    </mxCell>

    <!-- ===== DASHBOARDS ===== -->
    <mxCell id="19" value="&lt;b&gt;dashboard.py&lt;/b&gt;&lt;br&gt;Terminal — cada 3s&lt;br&gt;stats en tiempo real" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1015" y="585" width="170" height="80" as="geometry" />
    </mxCell>
    <mxCell id="20" value="&lt;b&gt;dashboard_web.py&lt;/b&gt;&lt;br&gt;Flask+SSE :8080&lt;br&gt;http://192.168.0.110:8080" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1200" y="585" width="185" height="80" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: metricas → motor (startup) ===== -->
    <mxCell id="21" value="τ1/τ2 al inicio" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.15;entryY=0;entryDx=0;entryDy=0;strokeColor=#CC5500;strokeWidth=2;fontSize=10;fontColor=#CC5500;" edge="1" source="4" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: models → motor (startup) ===== -->
    <mxCell id="22" value="modelos en memoria" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.35;entryY=0;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontColor=#8B6914;" edge="1" source="5" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: systemd → motor ===== -->
    <mxCell id="23" value="inicia" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.55;entryY=0;entryDx=0;entryDy=0;dashed=1;strokeColor=#666666;fontSize=10;" edge="1" source="6" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: WHITELIST → motor ===== -->
    <mxCell id="24" value="consulta" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.75;entryY=0;entryDx=0;entryDy=0;dashed=1;strokeColor=#4488aa;fontSize=10;fontColor=#4488aa;" edge="1" source="7" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: eve.json → motor ===== -->
    <mxCell id="25" value="flujos JSON" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.25;entryDx=0;entryDy=0;strokeColor=#6c8ebf;strokeWidth=2;fontSize=10;" edge="1" source="8" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: motor → PERMIT ===== -->
    <mxCell id="26" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.25;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#82b366;strokeWidth=2;" edge="1" source="9" target="10" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: motor → LIMIT ===== -->
    <mxCell id="27" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.55;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#d6790a;strokeWidth=2;" edge="1" source="9" target="11" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: motor → BLOCK ===== -->
    <mxCell id="28" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.8;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;" edge="1" source="9" target="12" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: LIMIT → enforce.sh ===== -->
    <mxCell id="29" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;strokeColor=#d6790a;strokeWidth=2;" edge="1" source="11" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: BLOCK → enforce.sh ===== -->
    <mxCell id="30" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.7;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;" edge="1" source="12" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: enforce.sh → ipset ppi_limited ===== -->
    <mxCell id="31" value="ipset add ppi_limited" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#d6790a;fontSize=10;" edge="1" source="13" target="15" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: enforce.sh → ipset ppi_blocked ===== -->
    <mxCell id="32" value="ipset add ppi_blocked" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.7;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#b85450;fontSize=10;" edge="1" source="13" target="16" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: heurísticos → enforce.sh ===== -->
    <mxCell id="33" value="override cuando aplica" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=1;entryDx=0;entryDy=0;strokeColor=#9673a6;strokeWidth=2;fontSize=10;" edge="1" source="17" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: motor → log ===== -->
    <mxCell id="34" value="escribe decisiones" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#d6b656;fontSize=10;" edge="1" source="9" target="18" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: log → dashboard.py ===== -->
    <mxCell id="35" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="18" target="19" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== CONECTOR: log → dashboard_web ===== -->
    <mxCell id="36" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.6;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="18" target="20" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== FLECHA A F6 ===== -->
    <mxCell id="37" value="→ F6: f6_corridas.py&lt;br&gt;lee motor_decision.log&lt;br&gt;para validación" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#003366;strokeColor=#001a33;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="1015" y="695" width="185" height="65" as="geometry" />
    </mxCell>
    <mxCell id="38" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;" edge="1" source="18" target="37" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== LEYENDA ===== -->
    <mxCell id="39" value="Leyenda" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="790" width="80" height="25" as="geometry" />
    </mxCell>
    <mxCell id="40" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="60" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="41" value="Scripts Python" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="83" y="822" width="120" height="18" as="geometry" />
    </mxCell>
    <mxCell id="42" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF8000;strokeColor=#CC5500;" vertex="1" parent="1">
      <mxGeometry x="215" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="43" value="Fuente única de verdad" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="238" y="822" width="145" height="18" as="geometry" />
    </mxCell>
    <mxCell id="44" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="395" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="45" value="PERMIT / dashboards" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="418" y="822" width="140" height="18" as="geometry" />
    </mxCell>
    <mxCell id="46" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;" vertex="1" parent="1">
      <mxGeometry x="570" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="47" value="LIMIT (hashlimit)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="593" y="822" width="120" height="18" as="geometry" />
    </mxCell>
    <mxCell id="48" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="725" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="49" value="BLOCK (DROP)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="748" y="822" width="110" height="18" as="geometry" />
    </mxCell>
    <mxCell id="50" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
      <mxGeometry x="870" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="51" value="Detectores heurísticos" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="893" y="822" width="145" height="18" as="geometry" />
    </mxCell>
    <mxCell id="52" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="1050" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="53" value="Artefactos / logs" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="1073" y="822" width="120" height="18" as="geometry" />
    </mxCell>

  
    <!-- ===== TELEGRAM NOTIFICATION CHANNEL ===== -->
    <mxCell id="54" value="CANAL DE ALERTAS TELEGRAM" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=12;fontStyle=1;fontColor=#1a6085;" vertex="1" parent="1">
      <mxGeometry x="1340" y="420" width="200" height="30" as="geometry" />
    </mxCell>

    <mxCell id="55" value="&lt;b&gt;telegram_alerta(msg)&lt;/b&gt;&lt;br&gt;&lt;br&gt;_tg_queue (no bloquea)&lt;br&gt;Thread _tg_worker&lt;br&gt;POST JSON al relay" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2AABEE;strokeColor=#1a8abc;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="1340" y="460" width="200" height="90" as="geometry" />
    </mxCell>

    <mxCell id="56" value="&lt;b&gt;telegram_relay.py&lt;/b&gt;&lt;br&gt;Desktop 192.168.0.20&lt;br&gt;Puerto :8889&lt;br&gt;&lt;br&gt;POST /telegram&lt;br&gt;→ api.telegram.org" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
      <mxGeometry x="1340" y="570" width="200" height="105" as="geometry" />
    </mxCell>

    <mxCell id="57" value="&lt;b&gt;Bot Telegram&lt;/b&gt;&lt;br&gt;api.telegram.org&lt;br&gt;&lt;br&gt;🚨 BLOCK → operador&lt;br&gt;⚠️ LIMIT → operador" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2AABEE;strokeColor=#1a8abc;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="1340" y="695" width="200" height="90" as="geometry" />
    </mxCell>

    <!-- Conector: motor → telegram_alerta -->
    <mxCell id="58" value="LIMIT/BLOCK" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#2AABEE;strokeWidth=2;fontColor=#2AABEE;fontSize=9;fontStyle=1;" edge="1" source="9" target="55" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: telegram_alerta → relay -->
    <mxCell id="59" value="HTTP POST" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=1.5;dashed=1;fontSize=9;" edge="1" source="55" target="56" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: relay → Telegram API -->
    <mxCell id="60" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=1.5;dashed=1;fontSize=9;" edge="1" source="56" target="57" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Leyenda Telegram -->
    <mxCell id="61" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2AABEE;strokeColor=#1a8abc;" vertex="1" parent="1">
      <mxGeometry x="1215" y="822" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="62" value="Telegram / Bot" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="1238" y="822" width="120" height="18" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```
