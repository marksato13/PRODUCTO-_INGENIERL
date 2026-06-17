# F5 — Diagrama: Control Inline

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- TÍTULO -->
    <mxCell id="2" value="F5 — Control Inline: enforce.sh + ipset/iptables en Servidor" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=20;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="20" width="1520" height="45" as="geometry" />
    </mxCell>

    <!-- ===== LLAMADAS AUTOMÁTICAS ===== -->
    <mxCell id="3" value="&lt;b&gt;motor_decision.py&lt;/b&gt;&lt;br&gt;&lt;i&gt;Enforcement automático&lt;/i&gt;&lt;br&gt;&lt;br&gt;Cuando score ≤ τ1 (LIMIT)&lt;br&gt;o score ≤ τ2 (BLOCK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="60" y="80" width="215" height="95" as="geometry" />
    </mxCell>

    <!-- ===== CONTROL MANUAL ===== -->
    <mxCell id="4" value="&lt;b&gt;Control manual (CLI)&lt;/b&gt;&lt;br&gt;&lt;i&gt;desde Sensor o Desktop&lt;/i&gt;&lt;br&gt;&lt;br&gt;bash enforce.sh &lt;ip&gt; BLOCK 300&lt;br&gt;bash enforce.sh &lt;ip&gt; LIMIT 300&lt;br&gt;bash enforce.sh &lt;ip&gt; UNBLOCK" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
      <mxGeometry x="60" y="210" width="215" height="105" as="geometry" />
    </mxCell>

    <!-- ===== ENFORCE.SH ===== -->
    <mxCell id="5" value="&lt;b&gt;enforce.sh&lt;/b&gt;&lt;br&gt;&lt;br&gt;BLOCK  → ipset add ppi_blocked &lt;ip&gt; timeout &lt;t&gt;&lt;br&gt;LIMIT  → ipset add ppi_limited &lt;ip&gt; timeout &lt;t&gt;&lt;br&gt;UNBLOCK → ipset del de ambos sets&lt;br&gt;&lt;br&gt;SSH: m4rk@192.168.0.120&lt;br&gt;sudo NOPASSWD: /usr/sbin/ipset" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="340" y="135" width="255" height="155" as="geometry" />
    </mxCell>

    <!-- Conector: motor → enforce.sh -->
    <mxCell id="6" value="BLOCK / LIMIT" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.25;entryDx=0;entryDy=0;strokeColor=#6c8ebf;strokeWidth=2;fontSize=10;" edge="1" source="3" target="5" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: CLI → enforce.sh -->
    <mxCell id="7" value="BLOCK/LIMIT/UNBLOCK" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.75;entryDx=0;entryDy=0;strokeColor=#666666;strokeWidth=2;fontSize=10;" edge="1" source="4" target="5" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== SERVIDOR 192.168.0.120 (contenedor) ===== -->
    <mxCell id="8" value="&lt;b&gt;Servidor 192.168.0.120&lt;/b&gt;  —  nginx:80 | SSH:22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#444444;fontSize=13;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
      <mxGeometry x="665" y="75" width="760" height="440" as="geometry" />
    </mxCell>

    <!-- iptables INPUT chain header -->
    <mxCell id="9" value="&lt;b&gt;iptables INPUT chain (en orden):&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="685" y="110" width="400" height="25" as="geometry" />
    </mxCell>

    <!-- Regla 1: ppi_blocked → DROP -->
    <mxCell id="10" value="Regla 1: &lt;b&gt;-m set --match-set ppi_blocked src -j DROP&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="685" y="143" width="410" height="40" as="geometry" />
    </mxCell>

    <!-- Regla 2: ppi_limited → hashlimit -->
    <mxCell id="11" value="Regla 2: &lt;b&gt;-m set --match-set ppi_limited src --hashlimit-above 100/sec -j DROP&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="685" y="195" width="410" height="40" as="geometry" />
    </mxCell>

    <!-- ipset ppi_blocked -->
    <mxCell id="12" value="&lt;b&gt;ipset ppi_blocked&lt;/b&gt;&lt;br&gt;hash:ip timeout 300&lt;br&gt;&lt;br&gt;→ iptables DROP&lt;br&gt;(descarta todo paquete)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1120" y="130" width="210" height="105" as="geometry" />
    </mxCell>

    <!-- ipset ppi_limited -->
    <mxCell id="13" value="&lt;b&gt;ipset ppi_limited&lt;/b&gt;&lt;br&gt;hash:ip timeout 300&lt;br&gt;&lt;br&gt;→ hashlimit 100 pkt/s&lt;br&gt;(paquetes excedentes: DROP)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1120" y="255" width="210" height="105" as="geometry" />
    </mxCell>

    <!-- Conector: regla 1 → ipset ppi_blocked -->
    <mxCell id="14" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;" edge="1" source="10" target="12" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: regla 2 → ipset ppi_limited -->
    <mxCell id="15" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;strokeColor=#d6790a;strokeWidth=2;" edge="1" source="11" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Timeout auto-expiry -->
    <mxCell id="16" value="&lt;b&gt;Auto-expiry:&lt;/b&gt; timeout=300s → la IP sale del ipset automáticamente&lt;br&gt;(sin reiniciar el motor ni ejecutar UNBLOCK manualmente)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffde7;strokeColor=#f0a500;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="685" y="260" width="410" height="55" as="geometry" />
    </mxCell>

    <!-- NOPASSWD sudoers -->
    <mxCell id="17" value="&lt;b&gt;sudoers:&lt;/b&gt; m4rk ALL=(ALL) NOPASSWD: /usr/sbin/ipset, /usr/sbin/iptables" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="685" y="330" width="620" height="40" as="geometry" />
    </mxCell>

    <!-- Servicios del servidor -->
    <mxCell id="18" value="&lt;b&gt;Servicios en el servidor:&lt;/b&gt; nginx (puerto 80) | OpenSSH (puerto 22)&lt;br&gt;Tráfico NO bloqueado llega con normalidad a estos servicios" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="685" y="385" width="720" height="55" as="geometry" />
    </mxCell>

    <!-- ===== FLECHA SSH enforce.sh → servidor ===== -->
    <mxCell id="19" value="SSH BatchMode&lt;br&gt;sudo ipset add/del" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#003366;strokeWidth=3;fontSize=11;fontStyle=1;fontColor=#003366;" edge="1" source="5" target="8" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== FLUJO DE TRÁFICO (sección inferior) ===== -->
    <mxCell id="20" value="&lt;b&gt;Flujo de tráfico de red entrante al servidor:&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="545" width="500" height="25" as="geometry" />
    </mxCell>

    <!-- Desktop .20 (WHITELIST) -->
    <mxCell id="21" value="&lt;b&gt;Desktop 192.168.0.20&lt;/b&gt;&lt;br&gt;WHITELIST — nunca bloqueado&lt;br&gt;&lt;i&gt;no está en ppi_blocked ni ppi_limited&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="60" y="578" width="230" height="75" as="geometry" />
    </mxCell>

    <!-- Kali .100 -->
    <mxCell id="22" value="&lt;b&gt;Kali 192.168.0.100&lt;/b&gt;&lt;br&gt;IP atacante&lt;br&gt;&lt;i&gt;añadida por motor o manualmente&lt;/i&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="60" y="680" width="230" height="75" as="geometry" />
    </mxCell>

    <!-- iptables check box -->
    <mxCell id="23" value="&lt;b&gt;iptables INPUT&lt;/b&gt;&lt;br&gt;(kernel del servidor)&lt;br&gt;&lt;br&gt;¿src ∈ ppi_blocked? → DROP&lt;br&gt;¿src ∈ ppi_limited? → hashlimit&lt;br&gt;Else → ACCEPT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e6e6e6;strokeColor=#444444;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="355" y="598" width="225" height="130" as="geometry" />
    </mxCell>

    <!-- ACCEPT -->
    <mxCell id="24" value="&lt;b&gt;ACCEPT&lt;/b&gt;&lt;br&gt;Llega a nginx / SSH" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="655" y="578" width="150" height="60" as="geometry" />
    </mxCell>

    <!-- LIMIT / hashlimit -->
    <mxCell id="25" value="&lt;b&gt;hashlimit&lt;/b&gt;&lt;br&gt;≤100 pkt/s pasan&lt;br&gt;resto: DROP" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="655" y="658" width="150" height="70" as="geometry" />
    </mxCell>

    <!-- DROP -->
    <mxCell id="26" value="&lt;b&gt;DROP&lt;/b&gt;&lt;br&gt;Paquetes descartados&lt;br&gt;por el kernel" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="655" y="748" width="150" height="70" as="geometry" />
    </mxCell>

    <!-- Conector: Desktop → iptables -->
    <mxCell id="27" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.2;entryDx=0;entryDy=0;strokeColor=#82b366;strokeWidth=2;" edge="1" source="21" target="23" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: Kali → iptables -->
    <mxCell id="28" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.8;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;" edge="1" source="22" target="23" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: iptables → ACCEPT -->
    <mxCell id="29" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.25;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#82b366;strokeWidth=2;" edge="1" source="23" target="24" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: iptables → hashlimit -->
    <mxCell id="30" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.55;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#d6790a;strokeWidth=2;" edge="1" source="23" target="25" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: iptables → DROP -->
    <mxCell id="31" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.85;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;" edge="1" source="23" target="26" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== DASHBOARD TERMINAL ===== -->
    <mxCell id="32" value="&lt;b&gt;dashboard.py&lt;/b&gt;&lt;br&gt;Terminal ANSI — cada 3s&lt;br&gt;Flows, anomalías, bloqueados,&lt;br&gt;limitados, latencia media" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="880" y="560" width="200" height="95" as="geometry" />
    </mxCell>

    <!-- ===== DASHBOARD WEB ===== -->
    <mxCell id="33" value="&lt;b&gt;dashboard_web.py :8080&lt;/b&gt;&lt;br&gt;Flask + Server-Sent Events&lt;br&gt;&lt;br&gt;GET /api/stats   → métricas JSON&lt;br&gt;GET /api/stream  → SSE push&lt;br&gt;GET /api/alerts  → historial&lt;br&gt;POST /api/block  → bloquear IP&lt;br&gt;POST /api/unblock → liberar IP&lt;br&gt;&lt;br&gt;http://192.168.0.110:8080" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
      <mxGeometry x="1100" y="530" width="240" height="185" as="geometry" />
    </mxCell>

    <!-- motor_decision.log -->
    <mxCell id="34" value="motor_decision.log&lt;br&gt;(leído por dashboards)" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="665" y="555" width="175" height="70" as="geometry" />
    </mxCell>

    <!-- Conector: log → dashboard terminal -->
    <mxCell id="35" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" source="34" target="32" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: log → dashboard web -->
    <mxCell id="36" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.6;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;" edge="1" source="34" target="33" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Dashboard web → POST block → enforce.sh -->
    <mxCell id="37" value="POST /api/block → enforce.sh" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;dashed=1;strokeColor=#82b366;fontSize=10;" edge="1" source="33" target="5" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== LEYENDA ===== -->
    <mxCell id="38" value="Leyenda" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="875" width="80" height="25" as="geometry" />
    </mxCell>
    <mxCell id="39" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="60" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="40" value="BLOCK / DROP (iptables)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="83" y="907" width="155" height="18" as="geometry" />
    </mxCell>
    <mxCell id="41" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;" vertex="1" parent="1">
      <mxGeometry x="250" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="42" value="LIMIT / hashlimit 100 pkt/s" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="273" y="907" width="165" height="18" as="geometry" />
    </mxCell>
    <mxCell id="43" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="450" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="44" value="ACCEPT / WHITELIST / Dashboard" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="473" y="907" width="195" height="18" as="geometry" />
    </mxCell>
    <mxCell id="45" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="680" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="46" value="Scripts Python / Bash" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="703" y="907" width="135" height="18" as="geometry" />
    </mxCell>
    <mxCell id="47" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffde7;strokeColor=#f0a500;" vertex="1" parent="1">
      <mxGeometry x="850" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="48" value="Auto-expiry (timeout 300s)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="873" y="907" width="170" height="18" as="geometry" />
    </mxCell>

  
    <!-- ===== TELEGRAM RELAY (canal de notificación) ===== -->
    <mxCell id="49" value="ALERTAS TELEGRAM" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=12;fontStyle=1;fontColor=#1a6085;" vertex="1" parent="1">
      <mxGeometry x="1140" y="730" width="240" height="30" as="geometry" />
    </mxCell>

    <mxCell id="50" value="&lt;b&gt;telegram_relay.py&lt;/b&gt;&lt;br&gt;Desktop 192.168.0.20 : 8889&lt;br&gt;&lt;br&gt;Recibe POST del motor (sensor)&lt;br&gt;Reenvía a api.telegram.org&lt;br&gt;&lt;br&gt;(Sensor sin internet → relay LAN)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
      <mxGeometry x="1140" y="770" width="240" height="110" as="geometry" />
    </mxCell>

    <mxCell id="51" value="&lt;b&gt;api.telegram.org&lt;/b&gt;&lt;br&gt;&lt;br&gt;🚨 BLOCK alert → operador&lt;br&gt;⚠️ LIMIT alert → operador&lt;br&gt;Latencia entrega: &amp;lt; 3s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2AABEE;strokeColor=#1a8abc;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="1140" y="900" width="240" height="90" as="geometry" />
    </mxCell>

    <!-- Conector: motor_decision.log → relay (representando salida de alertas del motor) -->
    <mxCell id="52" value="telegram_alerta()&lt;br&gt;LIMIT/BLOCK" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#2AABEE;strokeWidth=2;fontColor=#2AABEE;fontSize=9;fontStyle=1;" edge="1" source="34" target="50" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Conector: relay → Telegram API -->
    <mxCell id="53" value="HTTPS POST" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=1.5;dashed=1;fontSize=9;" edge="1" source="50" target="51" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Leyenda -->
    <mxCell id="54" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2AABEE;strokeColor=#1a8abc;" vertex="1" parent="1">
      <mxGeometry x="680" y="907" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="55" value="Telegram / Relay" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="703" y="907" width="130" height="18" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```
