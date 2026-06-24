# Diagrama 1 — Topología de Red del Laboratorio
**Slide 9 del PPT**

---

## draw.io XML

> Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxfile host="app.diagrams.net" modified="2026-06-22" version="21.0.0">
  <diagram id="d1-topologia" name="Topología de Red">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- Fondo red local -->
        <mxCell id="net" value="RED LOCAL  192.168.0.0 / 24" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;fontSize=16;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="10" y="10" width="1580" height="970" as="geometry"/>
        </mxCell>
        <!-- Win11 -->
        <mxCell id="win11" value="&lt;b&gt;Win11&lt;/b&gt;&lt;br&gt;Cliente&lt;br&gt;&lt;font color=&apos;#6c8ebf&apos;&gt;192.168.0.10&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="60" y="70" width="170" height="90" as="geometry"/>
        </mxCell>
        <!-- Desktop Admin -->
        <mxCell id="desktop" value="&lt;b&gt;Ubuntu Desktop&lt;/b&gt;&lt;br&gt;Admin / 192.168.0.20&lt;br&gt;&lt;i&gt;Claude Code corre aquí&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="710" y="70" width="180" height="90" as="geometry"/>
        </mxCell>
        <!-- Kali -->
        <mxCell id="kali" value="&lt;b&gt;Kali Linux&lt;/b&gt;&lt;br&gt;Atacante&lt;br&gt;&lt;font color=&apos;#b85450&apos;&gt;192.168.0.100&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="1360" y="70" width="170" height="90" as="geometry"/>
        </mxCell>
        <!-- Sensor container -->
        <mxCell id="sensor" value="&lt;b&gt;Ubuntu Sensor  ·  192.168.0.110  ·  NÚCLEO DEL SISTEMA&lt;/b&gt;" style="swimlane;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=13;fontStyle=1;startSize=38;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="260" y="240" width="780" height="370" as="geometry"/>
        </mxCell>
        <!-- Suricata -->
        <mxCell id="suricata" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&lt;br&gt;ens35 · modo pasivo&lt;br&gt;→ /var/log/suricata/eve.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="20" y="55" width="220" height="75" as="geometry"/>
        </mxCell>
        <!-- Motor -->
        <mxCell id="motor" value="&lt;b&gt;motor_decision.py&lt;/b&gt;&lt;br&gt;Isolation Forest n=300&lt;br&gt;τ1=−0.4459  ·  τ2=−0.6027&lt;br&gt;→ PERMIT / LIMIT / BLOCK&lt;br&gt;+ heurísticos BF-SSH y HTTP-Abuse&lt;br&gt;+ bloqueo progresivo #1/#2/#3" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="20" y="155" width="220" height="120" as="geometry"/>
        </mxCell>
        <!-- Dashboard -->
        <mxCell id="dash" value="&lt;b&gt;dashboard_web.py  :8080&lt;/b&gt;&lt;br&gt;Flask + SSE (&lt;150ms)  ·  Telegram (async, dedup 5min)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="20" y="300" width="220" height="55" as="geometry"/>
        </mxCell>
        <!-- Models -->
        <mxCell id="models" value="&lt;b&gt;models/&lt;/b&gt;&lt;br&gt;isolation_forest.pkl&lt;br&gt;predictor_modelo_v2.pkl (XGBoost)&lt;br&gt;scaler.pkl  ·  features.csv" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="295" y="55" width="220" height="90" as="geometry"/>
        </mxCell>
        <!-- Results -->
        <mxCell id="results" value="&lt;b&gt;results/&lt;/b&gt;&lt;br&gt;motor_decision.log&lt;br&gt;metricas_offline.txt (τ1/τ2)&lt;br&gt;block_counts.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="295" y="170" width="220" height="85" as="geometry"/>
        </mxCell>
        <!-- enforce.sh -->
        <mxCell id="enforce" value="&lt;b&gt;enforce.sh&lt;/b&gt;&lt;br&gt;Control manual&lt;br&gt;BLOCK / LIMIT / UNBLOCK [timeout]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="sensor">
          <mxGeometry x="545" y="55" width="210" height="75" as="geometry"/>
        </mxCell>
        <!-- Internal arrows sensor -->
        <mxCell id="ie1" value="eve.json" style="edgeStyle=orthogonalEdgeStyle;html=1;fontSize=9;" edge="1" source="suricata" target="motor" parent="sensor">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ie2" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;fontSize=9;" edge="1" source="motor" target="dash" parent="sensor">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ie3" value="load pkl" style="edgeStyle=orthogonalEdgeStyle;html=1;fontSize=9;dashed=1;" edge="1" source="models" target="motor" parent="sensor">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <!-- Servidor container -->
        <mxCell id="servidor" value="&lt;b&gt;Ubuntu Servidor  ·  192.168.0.120&lt;/b&gt;" style="swimlane;fillColor=#e1d5e7;strokeColor=#9673a6;fontColor=#4c1d70;fontSize=13;fontStyle=1;startSize=35;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="260" y="700" width="780" height="170" as="geometry"/>
        </mxCell>
        <!-- nginx -->
        <mxCell id="nginx" value="&lt;b&gt;Servicios&lt;/b&gt;&lt;br&gt;nginx  :80&lt;br&gt;sshd   :22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;" vertex="1" parent="servidor">
          <mxGeometry x="20" y="48" width="180" height="100" as="geometry"/>
        </mxCell>
        <!-- iptables -->
        <mxCell id="iptables" value="&lt;b&gt;iptables + ipset&lt;/b&gt;&lt;br&gt;ppi_blocked  →  DROP (kernel)  🚫&lt;br&gt;ppi_limited   →  hashlimit 100 pkt/s  ⚠️&lt;br&gt;Whitelist: .1 .20 .110 .120 127.0.0.1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="servidor">
          <mxGeometry x="240" y="48" width="520" height="100" as="geometry"/>
        </mxCell>
        <!-- Navegador -->
        <mxCell id="browser" value="&lt;b&gt;Navegador&lt;/b&gt;&lt;br&gt;Dashboard :8080&lt;br&gt;SSE real-time" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1100" y="350" width="150" height="80" as="geometry"/>
        </mxCell>
        <!-- Telegram -->
        <mxCell id="telegram" value="&lt;b&gt;Telegram 📱&lt;/b&gt;&lt;br&gt;Alertas BLOCK&lt;br&gt;async · dedup 5min" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1100" y="470" width="150" height="80" as="geometry"/>
        </mxCell>
        <!-- Flechas externas -->
        <mxCell id="e1" value="HTTP / SSH / SCP (tráfico normal)" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=2;fontColor=#6c8ebf;fontSize=10;" edge="1" source="win11" target="sensor" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e2" value="SYN flood · BF SSH · UDP flood · portscan (anómalo)" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;strokeWidth=2;dashed=1;fontColor=#b85450;fontSize=10;" edge="1" source="kali" target="sensor" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e3" value="SSH admin" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#9673a6;dashed=1;fontColor=#9673a6;fontSize=10;" edge="1" source="desktop" target="sensor" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e4" value="SSH + sudo ipset add ppi_blocked / ppi_limited" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d79b00;strokeWidth=2;fontColor=#d79b00;fontSize=10;" edge="1" source="motor" target="servidor" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e5" value="SSE :8080" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;fontSize=10;" edge="1" source="dash" target="browser" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="e6" value="Telegram API" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;fontSize=10;" edge="1" source="dash" target="telegram" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## Leyenda de colores

| Color | Elemento |
|---|---|
| Azul | Win11, tráfico normal, navegador |
| Rojo (discontinuo) | Kali, tráfico anómalo, iptables/bloqueo |
| Verde | Sensor (núcleo), dashboard, Telegram |
| Naranja | Comando de control (SSH → ipset) |
| Amarillo | Archivos de modelos y resultados |
| Púrpura | Desktop admin, Servidor |
