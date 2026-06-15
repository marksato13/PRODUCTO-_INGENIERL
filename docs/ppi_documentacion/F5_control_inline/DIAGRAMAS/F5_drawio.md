# F5 — Diagrama Draw.io: Control Inline e Integración

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama — Sensor → SSH → ipset/iptables → Servidor · Telegram · Dashboard

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F5_control" name="F5 — Control Inline">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="title" value="F5 — Control Inline: ipset · iptables · Telegram · Dashboard · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="300" y="15" width="1000" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SENSOR — MOTOR DE DECISIÓN -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="sensor_bg" value="&lt;b&gt;Sensor 192.168.0.110&lt;/b&gt;&lt;br&gt;motor_decision.py" style="swimlane;startSize=40;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="60" width="310" height="530" as="geometry" />
        </mxCell>

        <!-- Decisión -->
        <mxCell id="decision_node" value="&lt;b&gt;decidir(score)&lt;/b&gt;&lt;br&gt;+ detector override&lt;br&gt;→ PERMIT / LIMIT / BLOCK" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="15" y="45" width="280" height="55" as="geometry" />
        </mxCell>

        <!-- bloquear_ip() -->
        <mxCell id="bloquear_fn" value="&lt;b&gt;bloquear_ip(ip)&lt;/b&gt;&lt;br&gt;_ssh('sudo ipset add ppi_blocked&lt;br&gt;      {ip} timeout 300 -exist&lt;br&gt;      &amp;&amp; echo BLOCKED {ip}')" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="15" y="125" width="280" height="70" as="geometry" />
        </mxCell>

        <!-- limitar_ip() -->
        <mxCell id="limitar_fn" value="&lt;b&gt;limitar_ip(ip)&lt;/b&gt;&lt;br&gt;_ssh('sudo ipset add ppi_limited&lt;br&gt;      {ip} timeout 300 -exist&lt;br&gt;      &amp;&amp; echo LIMITED {ip}')" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="15" y="215" width="280" height="70" as="geometry" />
        </mxCell>

        <!-- _ssh() implementation -->
        <mxCell id="ssh_impl" value="&lt;b&gt;_ssh(cmd)&lt;/b&gt;&lt;br&gt;subprocess.run([&lt;br&gt;  'ssh',&lt;br&gt;  '-o', 'StrictHostKeyChecking=no',&lt;br&gt;  '-o', 'ConnectTimeout=5',&lt;br&gt;  'm4rk@192.168.0.120', cmd&lt;br&gt;], timeout=8)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="sensor_bg">
          <mxGeometry x="15" y="310" width="280" height="100" as="geometry" />
        </mxCell>

        <!-- In-memory sets -->
        <mxCell id="mem_sets" value="&lt;b&gt;Sets Python en memoria&lt;/b&gt;&lt;br&gt;bloqueados = set()&lt;br&gt;limitados  = set()&lt;br&gt;Si IP ya está → 'ya bloqueado'&lt;br&gt;sin SSH duplicado" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="15" y="430" width="280" height="80" as="geometry" />
        </mxCell>

        <!-- Flechas internas sensor -->
        <mxCell id="dec_to_blq" value="BLOCK" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="decision_node" target="bloquear_fn" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="dec_to_lim" value="LIMIT" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="decision_node" target="limitar_fn" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="blq_to_ssh" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#666666;strokeWidth=2;" edge="1" source="bloquear_fn" target="ssh_impl" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="lim_to_ssh" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#666666;strokeWidth=2;" edge="1" source="limitar_fn" target="ssh_impl" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ssh_to_mem" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#82b366;strokeWidth=1;dashed=1;" edge="1" source="ssh_impl" target="mem_sets" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CANAL SSH -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="ssh_tunnel" value="&lt;b&gt;Canal SSH&lt;/b&gt;&lt;br&gt;Clave pública · sin contraseña&lt;br&gt;ConnectTimeout=5s · subprocess.timeout=8s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#9e9e9e;fontSize=10;strokeDashArray=8 4;" vertex="1" parent="1">
          <mxGeometry x="360" y="340" width="230" height="65" as="geometry" />
        </mxCell>
        <mxCell id="sensor_to_tunnel" value="sudo ipset add ..." style="endArrow=block;endFill=1;html=1;strokeColor=#9e9e9e;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="sensor_bg" target="ssh_tunnel" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SERVIDOR — NETFILTER -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="srv_bg" value="&lt;b&gt;Servidor 192.168.0.120 — Netfilter (Kernel Linux)&lt;/b&gt;" style="swimlane;startSize=35;fillColor=#fff3e0;strokeColor=#e65100;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="60" width="680" height="600" as="geometry" />
        </mxCell>

        <!-- ipset ppi_blocked -->
        <mxCell id="ipset_blocked" value="&lt;b&gt;ipset ppi_blocked&lt;/b&gt;&lt;br&gt;Type: hash:ip&lt;br&gt;timeout: 300s (auto-expiry)&lt;br&gt;hashsize: 1024 · maxelem: 65536&lt;br&gt;─────────────────────&lt;br&gt;Cuando se agrega una IP:&lt;br&gt;192.168.0.100  timeout 299s ↓&lt;br&gt;...kernel countdown...&lt;br&gt;expirada → eliminada auto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="srv_bg">
          <mxGeometry x="20" y="45" width="290" height="155" as="geometry" />
        </mxCell>

        <!-- ipset ppi_limited -->
        <mxCell id="ipset_limited" value="&lt;b&gt;ipset ppi_limited&lt;/b&gt;&lt;br&gt;Type: hash:ip&lt;br&gt;timeout: 300s (auto-expiry)&lt;br&gt;hashsize: 1024 · maxelem: 65536&lt;br&gt;─────────────────────&lt;br&gt;Cuando se agrega una IP:&lt;br&gt;192.168.0.100  timeout 299s ↓&lt;br&gt;hashlimit cuenta por srcip&lt;br&gt;independiente por IP" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="srv_bg">
          <mxGeometry x="370" y="45" width="290" height="155" as="geometry" />
        </mxCell>

        <!-- iptables INPUT chain -->
        <mxCell id="ipt_chain" value="&lt;b&gt;iptables — cadena INPUT&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=11;fontStyle=1;" vertex="1" parent="srv_bg">
          <mxGeometry x="20" y="225" width="640" height="220" as="geometry" />
        </mxCell>

        <mxCell id="ipt_r1" value="&lt;b&gt;Regla 1 (línea 1 INPUT)&lt;/b&gt;&lt;br&gt;sudo iptables -I INPUT \&lt;br&gt;  -m set --match-set ppi_blocked src \&lt;br&gt;  -j DROP&lt;br&gt;─────────────────────&lt;br&gt;Efecto: TODO paquete de IP en&lt;br&gt;ppi_blocked → DROP inmediato&lt;br&gt;0 respuesta al atacante" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="ipt_chain">
          <mxGeometry x="10" y="35" width="290" height="170" as="geometry" />
        </mxCell>

        <mxCell id="ipt_r2" value="&lt;b&gt;Regla 2 (línea 2 INPUT)&lt;/b&gt;&lt;br&gt;sudo iptables -I INPUT 2 \&lt;br&gt;  -m set --match-set ppi_limited src \&lt;br&gt;  -m hashlimit \&lt;br&gt;    --hashlimit-above 100/sec \&lt;br&gt;    --hashlimit-burst 150 \&lt;br&gt;    --hashlimit-mode srcip \&lt;br&gt;  -j DROP&lt;br&gt;─────────────────────&lt;br&gt;Efecto: paquetes &gt;100/s → DROP&lt;br&gt;hasta 150 en burst → ACCEPT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="ipt_chain">
          <mxGeometry x="330" y="35" width="300" height="170" as="geometry" />
        </mxCell>

        <!-- Servicios del servidor -->
        <mxCell id="srv_nginx" value="&lt;b&gt;nginx :80&lt;/b&gt;  activo ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#d79b00;fontSize=11;" vertex="1" parent="srv_bg">
          <mxGeometry x="20" y="470" width="295" height="40" as="geometry" />
        </mxCell>
        <mxCell id="srv_sshd" value="&lt;b&gt;openssh-server :22&lt;/b&gt;  activo ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#d79b00;fontSize=11;" vertex="1" parent="srv_bg">
          <mxGeometry x="345" y="470" width="295" height="40" as="geometry" />
        </mxCell>

        <!-- Timeout diagram -->
        <mxCell id="timeout_box" value="&lt;b&gt;Timeout automático — Kernel Linux&lt;/b&gt;&lt;br&gt;T=0:   ipset add IP timeout 300&lt;br&gt;T=150: IP activa · countdown 150s&lt;br&gt;T=300: kernel elimina IP del set&lt;br&gt;T+1:   tráfico pasa de nuevo&lt;br&gt;→ motor re-detecta y re-bloquea" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="srv_bg">
          <mxGeometry x="20" y="530" width="640" height="55" as="geometry" />
        </mxCell>

        <!-- Flechas ipset → iptables -->
        <mxCell id="blocked_to_r1" value="match" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;fontSize=9;" edge="1" source="ipset_blocked" target="ipt_r1" parent="srv_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="limited_to_r2" value="match" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;fontSize=9;" edge="1" source="ipset_limited" target="ipt_r2" parent="srv_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- SSH → ipsets -->
        <mxCell id="tunnel_to_blocked" value="ipset add ppi_blocked" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="ssh_tunnel" target="ipset_blocked" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="tunnel_to_limited" value="ipset add ppi_limited" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="ssh_tunnel" target="ipset_limited" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLUJO DE TRÁFICO ENTRANTE -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="traffic_bg" value="&lt;b&gt;Tráfico entrante al servidor&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#fafafa;strokeColor=#757575;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1330" y="60" width="260" height="390" as="geometry" />
        </mxCell>

        <mxCell id="pkt_in" value="📦 Paquete&lt;br&gt;src_ip = X.X.X.X" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#9e9e9e;fontSize=11;" vertex="1" parent="traffic_bg">
          <mxGeometry x="60" y="35" width="140" height="45" as="geometry" />
        </mxCell>

        <mxCell id="chk_blocked" value="¿IP ∈&lt;br&gt;ppi_blocked?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;fontStyle=1;" vertex="1" parent="traffic_bg">
          <mxGeometry x="55" y="100" width="150" height="60" as="geometry" />
        </mxCell>

        <mxCell id="drop_blocked" value="❌ DROP&lt;br&gt;sin respuesta" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#b71c1c;strokeColor=#7f0000;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="traffic_bg">
          <mxGeometry x="155" y="108" width="95" height="45" as="geometry" />
        </mxCell>

        <mxCell id="chk_limited" value="¿IP ∈ ppi_limited&lt;br&gt;+ &gt;100 pkt/s?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;fontStyle=1;" vertex="1" parent="traffic_bg">
          <mxGeometry x="50" y="185" width="160" height="65" as="geometry" />
        </mxCell>

        <mxCell id="drop_limited" value="❌ DROP&lt;br&gt;exceso &gt;100/s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e65100;strokeColor=#bf360c;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="traffic_bg">
          <mxGeometry x="155" y="195" width="95" height="45" as="geometry" />
        </mxCell>

        <mxCell id="accept_limited" value="✅ ACCEPT&lt;br&gt;hasta 100 pkt/s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="traffic_bg">
          <mxGeometry x="60" y="278" width="140" height="40" as="geometry" />
        </mxCell>

        <mxCell id="accept_normal" value="✅ ACCEPT&lt;br&gt;sin restricción" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=11;fontStyle=1;" vertex="1" parent="traffic_bg">
          <mxGeometry x="60" y="338" width="140" height="40" as="geometry" />
        </mxCell>

        <!-- Flechas flujo tráfico -->
        <mxCell id="pkt_to_chk1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="pkt_in" target="chk_blocked" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="chk1_yes" value="SÍ" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;fontSize=9;fontStyle=1;" edge="1" source="chk_blocked" target="drop_blocked" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="chk1_no" value="NO" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;fontSize=9;" edge="1" source="chk_blocked" target="chk_limited" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="chk2_yes" value="SÍ" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;fontSize=9;fontStyle=1;" edge="1" source="chk_limited" target="drop_limited" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="chk2_no1" value="NO &gt;100/s" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=1;fontSize=9;" edge="1" source="chk_limited" target="accept_limited" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="chk2_no2" value="NO en set" style="endArrow=block;endFill=1;html=1;strokeColor=#388e3c;strokeWidth=2;fontSize=9;fontStyle=1;" edge="1" source="chk_limited" target="accept_normal" parent="traffic_bg">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="30" y="218" />
              <mxPoint x="30" y="358" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- Flecha servidor → traffic check -->
        <mxCell id="srv_to_traffic" value="paquetes&lt;br&gt;entrantes" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;fontSize=10;" edge="1" source="srv_bg" target="traffic_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- ENFORCE.SH — CONTROL MANUAL -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="enforce_bg" value="&lt;b&gt;scripts/enforce.sh — Control Manual&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="625" width="560" height="170" as="geometry" />
        </mxCell>

        <mxCell id="enf_block" value="&lt;b&gt;BLOCK&lt;/b&gt;&lt;br&gt;bash enforce.sh 192.168.0.100 BLOCK 300&lt;br&gt;→ sudo ipset add ppi_blocked IP timeout 300 -exist" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;" vertex="1" parent="enforce_bg">
          <mxGeometry x="10" y="38" width="260" height="55" as="geometry" />
        </mxCell>
        <mxCell id="enf_limit" value="&lt;b&gt;LIMIT&lt;/b&gt;&lt;br&gt;bash enforce.sh 192.168.0.100 LIMIT 300&lt;br&gt;→ sudo ipset add ppi_limited IP timeout 300 -exist" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;" vertex="1" parent="enforce_bg">
          <mxGeometry x="10" y="103" width="260" height="55" as="geometry" />
        </mxCell>
        <mxCell id="enf_unblock" value="&lt;b&gt;UNBLOCK&lt;/b&gt;&lt;br&gt;bash enforce.sh 192.168.0.100 UNBLOCK&lt;br&gt;→ sudo ipset del ppi_blocked IP 2&gt;/dev/null || true&lt;br&gt;→ sudo ipset del ppi_limited IP 2&gt;/dev/null || true" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="enforce_bg">
          <mxGeometry x="285" y="38" width="265" height="120" as="geometry" />
        </mxCell>

        <!-- enforce.sh → servidor -->
        <mxCell id="enforce_to_srv" value="ejecución manual" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=2;dashed=1;fontSize=10;" edge="1" source="enforce_bg" target="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- DASHBOARD WEB + TELEGRAM -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="notif_bg" value="&lt;b&gt;Notificaciones y Visualización&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="690" width="680" height="100" as="geometry" />
        </mxCell>

        <mxCell id="tg_out" value="&lt;b&gt;Telegram Bot&lt;/b&gt;&lt;br&gt;🚨 BLOCK · ⚠️ LIMIT&lt;br&gt;🔑 BruteForce · 🌐 HTTP&lt;br&gt;async · 300–800ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=10;" vertex="1" parent="notif_bg">
          <mxGeometry x="10" y="35" width="155" height="55" as="geometry" />
        </mxCell>
        <mxCell id="dash_web" value="&lt;b&gt;dashboard_web.py&lt;/b&gt;&lt;br&gt;http://192.168.0.110:8080&lt;br&gt;Flask + SSE · 6 vistas&lt;br&gt;auto-refresca ~150ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="notif_bg">
          <mxGeometry x="180" y="35" width="160" height="55" as="geometry" />
        </mxCell>
        <mxCell id="dash_term" value="&lt;b&gt;dashboard.py&lt;/b&gt;&lt;br&gt;Terminal · cada 3s&lt;br&gt;flows · alertas · latencia" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="notif_bg">
          <mxGeometry x="355" y="35" width="155" height="55" as="geometry" />
        </mxCell>
        <mxCell id="log_ref" value="&lt;b&gt;motor_decision.log&lt;/b&gt;&lt;br&gt;WARNING SOSPECHOSO/ANOMALÍA&lt;br&gt;razón z-score incluida" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="notif_bg">
          <mxGeometry x="525" y="30" width="145" height="60" as="geometry" />
        </mxCell>

        <!-- Sensor → Telegram -->
        <mxCell id="sensor_to_tg" value="telegram_alerta()" style="endArrow=block;endFill=1;html=1;strokeColor=#0277bd;strokeWidth=2;dashed=1;fontSize=10;exitX=0.5;exitY=1;exitDx=0;exitDy=0;" edge="1" source="sensor_bg" target="tg_out" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="sensor_to_log" value="log.warning()" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=2;dashed=1;fontSize=10;" edge="1" source="sensor_bg" target="log_ref" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="log_to_dash" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=1;dashed=1;" edge="1" source="log_ref" target="dash_web" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="log_to_dterm" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=1;dashed=1;" edge="1" source="log_ref" target="dash_term" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CICLO DE VIDA DEL BLOQUEO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="lifecycle_bg" value="&lt;b&gt;Ciclo de vida de un bloqueo&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#fffde7;strokeColor=#f9a825;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="825" width="560" height="80" as="geometry" />
        </mxCell>

        <mxCell id="lc1" value="T=0&lt;br&gt;Motor detecta&lt;br&gt;BLOCK" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=9;" vertex="1" parent="lifecycle_bg">
          <mxGeometry x="10" y="32" width="80" height="38" as="geometry" />
        </mxCell>
        <mxCell id="lc2" value="T~1s&lt;br&gt;SSH ipset add&lt;br&gt;IP timeout 300" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=9;" vertex="1" parent="lifecycle_bg">
          <mxGeometry x="105" y="32" width="95" height="38" as="geometry" />
        </mxCell>
        <mxCell id="lc3" value="T=1s–299s&lt;br&gt;Kernel: DROP&lt;br&gt;todos los pkts" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=9;" vertex="1" parent="lifecycle_bg">
          <mxGeometry x="215" y="32" width="100" height="38" as="geometry" />
        </mxCell>
        <mxCell id="lc4" value="T=300s&lt;br&gt;Kernel expira&lt;br&gt;IP del set" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=9;" vertex="1" parent="lifecycle_bg">
          <mxGeometry x="330" y="32" width="90" height="38" as="geometry" />
        </mxCell>
        <mxCell id="lc5" value="T&gt;300s&lt;br&gt;Motor re-detecta&lt;br&gt;→ re-bloquea auto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=9;" vertex="1" parent="lifecycle_bg">
          <mxGeometry x="435" y="32" width="115" height="38" as="geometry" />
        </mxCell>

        <mxCell id="lc_e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=2;" edge="1" source="lc1" target="lc2" parent="lifecycle_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="lc_e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=2;" edge="1" source="lc2" target="lc3" parent="lifecycle_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="lc_e3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=2;" edge="1" source="lc3" target="lc4" parent="lifecycle_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="lc_e4" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=2;" edge="1" source="lc4" target="lc5" parent="lifecycle_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CONECTOR → F6 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="f6_conn" value="&lt;b&gt;→ F6: Validación&lt;/b&gt;&lt;br&gt;Sistema operativo con:&lt;br&gt;ipset ppi_blocked + ppi_limited&lt;br&gt;iptables DROP + hashlimit&lt;br&gt;motor corriendo + Telegram activo&lt;br&gt;→ 40 corridas controladas&lt;br&gt;Disp=100% · ITL=0% · TIE=100%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=3;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1330" y="480" width="260" height="170" as="geometry" />
        </mxCell>
        <mxCell id="srv_to_f6" value="sistema listo" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="traffic_bg" target="f6_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- VERIFICACIÓN REAL -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="verify_bg" value="&lt;b&gt;Verificación real — sesión 2026-06-14&lt;/b&gt;&lt;br&gt;sudo iptables -L INPUT -n --line-numbers | grep ppi:&lt;br&gt;  1  DROP  all  0.0.0.0/0  match-set ppi_blocked src&lt;br&gt;  2  DROP  all  0.0.0.0/0  match-set ppi_limited src  limit: above 100/sec burst 150 mode srcip&lt;br&gt;sudo ipset list ppi_limited:&lt;br&gt;  192.168.0.100  timeout 245  ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#388e3c;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="620" y="825" width="680" height="80" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
