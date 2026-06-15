# F4 — Diagrama Draw.io: Motor de Decisión

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama — Pipeline Completo: eve.json → Filtros → IF → Detectores → Decisión → Acciones

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F4_motor" name="F4 — Motor de Decisión">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1400" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="title" value="F4 — Motor de Decisión: motor_decision.py (547 líneas) · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="300" y="15" width="1000" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 1: ARRANQUE DEL SISTEMA -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="boot_bg" value="&lt;b&gt;1. Arranque — ppi-motor.service (systemd)&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="60" width="1350" height="120" as="geometry" />
        </mxCell>

        <mxCell id="svc" value="&lt;b&gt;ppi-motor.service&lt;/b&gt;&lt;br&gt;Requires=suricata.service&lt;br&gt;WorkingDir=/home/m4rk/ppi-surikata-producto&lt;br&gt;Restart=on-failure · RestartSec=10" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="boot_bg">
          <mxGeometry x="10" y="38" width="240" height="70" as="geometry" />
        </mxCell>
        <mxCell id="load_model" value="&lt;b&gt;load_model()&lt;/b&gt;&lt;br&gt;joblib.load(isolation_forest.pkl)&lt;br&gt;joblib.load(scaler.pkl)&lt;br&gt;TAU1=−0.4973 · TAU2=−0.6873" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="boot_bg">
          <mxGeometry x="270" y="38" width="240" height="70" as="geometry" />
        </mxCell>
        <mxCell id="init_srv" value="&lt;b&gt;inicializar_servidor()&lt;/b&gt;&lt;br&gt;SSH → 192.168.0.120&lt;br&gt;① ipset create ppi_blocked/ppi_limited&lt;br&gt;② iptables DROP + hashlimit" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="boot_bg">
          <mxGeometry x="530" y="38" width="250" height="70" as="geometry" />
        </mxCell>
        <mxCell id="tg_thread" value="&lt;b&gt;threading.Thread&lt;/b&gt;&lt;br&gt;target=_tg_worker · daemon=True&lt;br&gt;Cola asyncrónica Telegram&lt;br&gt;Queue(maxsize=100)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=10;" vertex="1" parent="boot_bg">
          <mxGeometry x="800" y="38" width="240" height="70" as="geometry" />
        </mxCell>
        <mxCell id="loop_start" value="&lt;b&gt;seguir_eve()&lt;/b&gt;&lt;br&gt;f.seek(0,2) → tail -f&lt;br&gt;poll cada 0.2s&lt;br&gt;detecta rotación/truncado" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="boot_bg">
          <mxGeometry x="1060" y="38" width="220" height="70" as="geometry" />
        </mxCell>

        <mxCell id="boot_e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;" edge="1" source="svc" target="load_model" parent="boot_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="boot_e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;" edge="1" source="load_model" target="init_srv" parent="boot_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="boot_e3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;" edge="1" source="init_srv" target="tg_thread" parent="boot_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="boot_e4" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;" edge="1" source="tg_thread" target="loop_start" parent="boot_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- EVE.JSON -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="eve_cyl" value="&lt;b&gt;eve.json&lt;/b&gt;&lt;br&gt;/var/log/suricata/&lt;br&gt;readline() por línea" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="170" y="220" width="150" height="75" as="geometry" />
        </mxCell>
        <mxCell id="eve_to_loop" value="cada flow event" style="endArrow=block;endFill=1;html=1;strokeColor=#82b366;strokeWidth=2;fontSize=10;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="245" y="295" as="sourcePoint" />
            <mxPoint x="245" y="335" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="boot_to_eve" value="inicia loop" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;fontSize=10;" edge="1" source="loop_start" target="eve_cyl" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 2: FILTROS (5 capas) -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="filters_bg" value="&lt;b&gt;2. Filtros de Entrada (5 capas en orden)&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#f5f5f5;strokeColor=#757575;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="330" width="870" height="110" as="geometry" />
        </mxCell>

        <mxCell id="f1" value="① event_type&lt;br&gt;== 'flow'" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eeeeee;strokeColor=#757575;fontSize=10;" vertex="1" parent="filters_bg">
          <mxGeometry x="10" y="38" width="130" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f2" value="② ':' not in&lt;br&gt;src_ip&lt;br&gt;(solo IPv4)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eeeeee;strokeColor=#757575;fontSize=10;" vertex="1" parent="filters_bg">
          <mxGeometry x="160" y="38" width="130" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f3" value="③ src_ip ∉&lt;br&gt;WHITELIST&lt;br&gt;{.1 .20 .110 .120 .130...}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eeeeee;strokeColor=#757575;fontSize=10;" vertex="1" parent="filters_bg">
          <mxGeometry x="310" y="38" width="160" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f4" value="④ es_ip_bloqueable()&lt;br&gt;¬0.0.0.0 ¬255.255.255.255&lt;br&gt;¬multicast ¬*.255" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eeeeee;strokeColor=#757575;fontSize=10;" vertex="1" parent="filters_bg">
          <mxGeometry x="490" y="38" width="175" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f5" value="⑤ pkts_toserver&lt;br&gt;&gt; 0&lt;br&gt;(flow válido)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="filters_bg">
          <mxGeometry x="685" y="38" width="130" height="55" as="geometry" />
        </mxCell>

        <mxCell id="fe1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="f1" target="f2" parent="filters_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="fe2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="f2" target="f3" parent="filters_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="fe3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="f3" target="f4" parent="filters_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="fe4" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="f4" target="f5" parent="filters_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Descartado -->
        <mxCell id="descartado" value="❌ Descartado — sin acción" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b85450;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="930" y="360" width="180" height="40" as="geometry" />
        </mxCell>
        <mxCell id="f_to_disc" value="falla algún filtro" style="endArrow=block;endFill=1;html=1;strokeColor=#b85450;strokeWidth=1;dashed=1;fontSize=9;" edge="1" source="filters_bg" target="descartado" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 3: PIPELINE CLASIFICACIÓN -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="pipe_bg" value="&lt;b&gt;3. Pipeline de Clasificación IF&lt;/b&gt;  ·  Latencia P95 = 34.8ms" style="swimlane;startSize=30;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="475" width="870" height="110" as="geometry" />
        </mxCell>

        <mxCell id="p_extract" value="&lt;b&gt;extract_features(e)&lt;/b&gt;&lt;br&gt;numpy array [1×14]&lt;br&gt;14 features del flow" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=10;" vertex="1" parent="pipe_bg">
          <mxGeometry x="10" y="38" width="190" height="60" as="geometry" />
        </mxCell>
        <mxCell id="p_scale" value="&lt;b&gt;scaler.transform(X)&lt;/b&gt;&lt;br&gt;(X − μ_normal) / σ_normal&lt;br&gt;centra respecto al perfil normal" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=10;" vertex="1" parent="pipe_bg">
          <mxGeometry x="225" y="38" width="210" height="60" as="geometry" />
        </mxCell>
        <mxCell id="p_score" value="&lt;b&gt;clf.score_samples(X)[0]&lt;/b&gt;&lt;br&gt;score ∈ (−1, 0)&lt;br&gt;más negativo = más anómalo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00796b;strokeColor=#004d40;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="pipe_bg">
          <mxGeometry x="460" y="38" width="210" height="60" as="geometry" />
        </mxCell>
        <mxCell id="p_grado" value="&lt;b&gt;clasificar_grado(score)&lt;/b&gt;&lt;br&gt;NORMAL / BAJA / ALTA / CRÍTICA" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=10;" vertex="1" parent="pipe_bg">
          <mxGeometry x="695" y="38" width="165" height="60" as="geometry" />
        </mxCell>

        <mxCell id="pe1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth=2;" edge="1" source="p_extract" target="p_scale" parent="pipe_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="pe2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth=2;" edge="1" source="p_scale" target="p_score" parent="pipe_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="pe3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth=2;" edge="1" source="p_score" target="p_grado" parent="pipe_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 4: DETECTORES + EXPLAINABILITY (PARALELO) -->
        <!-- ══════════════════════════════════════════════════════ -->

        <!-- Detector SSH -->
        <mxCell id="det_ssh" value="&lt;b&gt;detectar_brute_force()&lt;/b&gt;&lt;br&gt;dest_port == 22&lt;br&gt;ssh_intentos[ip].append(ts)&lt;br&gt;purga ts &lt; ahora − 60s&lt;br&gt;n ≥ 15 → BLOCK&lt;br&gt;n ≥ 5  → LIMIT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="30" y="625" width="200" height="115" as="geometry" />
        </mxCell>

        <!-- Detector HTTP -->
        <mxCell id="det_http" value="&lt;b&gt;detectar_http_abuse()&lt;/b&gt;&lt;br&gt;dest_port == 80&lt;br&gt;http_requests[ip].append(ts)&lt;br&gt;purga ts &lt; ahora − 30s&lt;br&gt;n ≥ 100 → BLOCK&lt;br&gt;n ≥ 50  → LIMIT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="250" y="625" width="200" height="115" as="geometry" />
        </mxCell>

        <!-- Explainability -->
        <mxCell id="explain" value="&lt;b&gt;explicar_anomalia()&lt;/b&gt;&lt;br&gt;Solo en LIMIT y BLOCK&lt;br&gt;z = (X_raw − μ) / σ&lt;br&gt;Top-3 features por |z|&lt;br&gt;Ej: pkt_rate:z=+45.2 |&lt;br&gt;    pkts_to:z=+38.7 | ..." style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="470" y="625" width="210" height="115" as="geometry" />
        </mxCell>

        <!-- Grado zonas -->
        <mxCell id="grado_zones" value="&lt;b&gt;Grados de anomalía&lt;/b&gt;&lt;br&gt;NORMAL  : score &gt; −0.4973&lt;br&gt;BAJA    : score &gt; −0.6873&lt;br&gt;ALTA    : score &gt; −0.82&lt;br&gt;CRÍTICA : score ≤ −0.82" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="700" y="625" width="200" height="115" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 5: LÓGICA DE DECISIÓN -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="dec_check1" value="¿Detector heurístico&lt;br&gt;activó BLOCK/LIMIT?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="785" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="dec_score1" value="¿score &gt; τ1&lt;br&gt;= −0.4973?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="380" y="785" width="170" height="80" as="geometry" />
        </mxCell>
        <mxCell id="dec_score2" value="¿score &gt; τ2&lt;br&gt;= −0.6873?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="620" y="785" width="170" height="80" as="geometry" />
        </mxCell>

        <!-- Flechas decisión -->
        <mxCell id="de1" value="SÍ → override" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;fontSize=9;" edge="1" source="dec_check1" target="dec_score1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="200" y="900" />
              <mxPoint x="465" y="900" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="de1b" value="NO" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=2;fontSize=9;" edge="1" source="dec_check1" target="dec_score1" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="de2" value="NO" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=2;fontSize=9;" edge="1" source="dec_score1" target="dec_score2" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 6: ACCIONES -->
        <!-- ══════════════════════════════════════════════════════ -->

        <!-- PERMIT -->
        <mxCell id="act_permit" value="&lt;b&gt;PERMIT&lt;/b&gt;&lt;br&gt;log.debug() — invisible&lt;br&gt;sin acción en ipset" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="330" y="920" width="200" height="70" as="geometry" />
        </mxCell>
        <mxCell id="score1_permit" value="SÍ" style="endArrow=block;endFill=1;html=1;strokeColor=#388e3c;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="dec_score1" target="act_permit" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- LIMIT -->
        <mxCell id="act_limit" value="&lt;b&gt;LIMIT&lt;/b&gt;&lt;br&gt;ipset add ppi_limited (SSH al srv)&lt;br&gt;hashlimit 100 pkt/s · timeout 300s&lt;br&gt;log.warning('SOSPECHOSO|...')&lt;br&gt;Telegram ⚠️ + razón z-score" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="580" y="920" width="250" height="85" as="geometry" />
        </mxCell>
        <mxCell id="score2_limit" value="SÍ" style="endArrow=block;endFill=1;html=1;strokeColor=#d79b00;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="dec_score2" target="act_limit" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- BLOCK -->
        <mxCell id="act_block" value="&lt;b&gt;BLOCK&lt;/b&gt;&lt;br&gt;ipset add ppi_blocked (SSH al srv)&lt;br&gt;iptables DROP · timeout 300s&lt;br&gt;log.warning('ANOMALÍA|...')&lt;br&gt;Telegram 🚨 + razón z-score" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="860" y="920" width="250" height="85" as="geometry" />
        </mxCell>
        <mxCell id="score2_block" value="NO" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="dec_score2" target="act_block" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ya bloqueado / ya limitado -->
        <mxCell id="ya_bloq" value="src_ip ∈ bloqueados (set Python)&lt;br&gt;→ 'ya bloqueado' · sin SSH" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=9;dashed=1;" vertex="1" parent="1">
          <mxGeometry x="860" y="830" width="200" height="45" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 7: SALIDAS -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="out_bg" value="&lt;b&gt;7. Salidas y Notificaciones&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1150" y="330" width="290" height="590" as="geometry" />
        </mxCell>

        <mxCell id="out_log" value="&lt;b&gt;motor_decision.log&lt;/b&gt;  7.6 MB&lt;br&gt;─────────────────────&lt;br&gt;PERMIT → log.debug() [invisible]&lt;br&gt;─────────────────────&lt;br&gt;LIMIT: WARNING | SOSPECHOSO |&lt;br&gt;  score=-0.53 | razón=[...]&lt;br&gt;─────────────────────&lt;br&gt;BLOCK: WARNING | ANOMALÍA |&lt;br&gt;  score=-0.72 | razón=[...]&lt;br&gt;  → BLOCKED 192.168.0.100&lt;br&gt;─────────────────────&lt;br&gt;STATS cada 500 flows:&lt;br&gt;  flows · anomalías · latencia" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=9;align=left;spacingLeft=6;" vertex="1" parent="out_bg">
          <mxGeometry x="10" y="38" width="268" height="155" as="geometry" />
        </mxCell>

        <mxCell id="out_tg" value="&lt;b&gt;Telegram Bot&lt;/b&gt;  async queue&lt;br&gt;─────────────────────&lt;br&gt;🚨 BLOCK: IP · Score · Razón&lt;br&gt;⚠️ LIMIT: IP · Score&lt;br&gt;🔑 BRUTE FORCE (n/60s)&lt;br&gt;🌐 HTTP ABUSE (n/30s)&lt;br&gt;─────────────────────&lt;br&gt;chat_id=8512353253&lt;br&gt;300–800ms async" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=9;align=left;spacingLeft=6;" vertex="1" parent="out_bg">
          <mxGeometry x="10" y="205" width="268" height="130" as="geometry" />
        </mxCell>

        <mxCell id="out_dash_web" value="&lt;b&gt;dashboard_web.py&lt;/b&gt;&lt;br&gt;Flask + SSE · :8080&lt;br&gt;ppi-dashboard.service&lt;br&gt;6 vistas: alertas · control&lt;br&gt;análisis · ipset · sistema" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=9;align=left;spacingLeft=6;" vertex="1" parent="out_bg">
          <mxGeometry x="10" y="350" width="268" height="90" as="geometry" />
        </mxCell>

        <mxCell id="out_dash_term" value="&lt;b&gt;dashboard.py&lt;/b&gt;  terminal&lt;br&gt;Lee motor_decision.log · cada 3s&lt;br&gt;flows · alertas · bloqueados · latencia" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=9;align=left;spacingLeft=6;" vertex="1" parent="out_bg">
          <mxGeometry x="10" y="455" width="268" height="60" as="geometry" />
        </mxCell>

        <mxCell id="out_stats" value="&lt;b&gt;Estadísticas internas cada 500 flows&lt;/b&gt;&lt;br&gt;total_flows · total_anom · total_bf&lt;br&gt;bloqueados · limitados · latencia_media" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=9;" vertex="1" parent="out_bg">
          <mxGeometry x="10" y="528" width="268" height="50" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CONECTOR → F5 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="f5_conn" value="&lt;b&gt;→ F5: Control Inline&lt;/b&gt;&lt;br&gt;bloquear_ip():&lt;br&gt;  _ssh('sudo ipset add ppi_blocked IP timeout 300 -exist')&lt;br&gt;limitar_ip():&lt;br&gt;  _ssh('sudo ipset add ppi_limited IP timeout 300 -exist')&lt;br&gt;&lt;br&gt;Servidor 192.168.0.120&lt;br&gt;Canal SSH sin contraseña · ConnectTimeout=5s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=3;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1150" y="60" width="290" height="175" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLECHAS VERTICALES PRINCIPALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="main_f1" value="flow event JSON" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="eve_cyl" target="filters_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f2" value="flow válido" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="filters_bg" target="pipe_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f3" value="score" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="pipe_bg" target="det_ssh" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f3b" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=3;" edge="1" source="pipe_bg" target="det_http" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f3c" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#0277bd;strokeWidth=2;" edge="1" source="pipe_bg" target="explain" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f4a" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="det_ssh" target="dec_check1" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f4b" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="det_http" target="dec_check1" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f4c" value="razón" style="endArrow=block;endFill=1;html=1;strokeColor=#0277bd;strokeWidth=2;dashed=1;fontSize=9;" edge="1" source="explain" target="act_limit" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="main_f4d" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#0277bd;strokeWidth=2;dashed=1;" edge="1" source="explain" target="act_block" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Salidas → log -->
        <mxCell id="act_to_log1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=1;dashed=1;" edge="1" source="act_limit" target="out_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="act_to_log2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=1;dashed=1;" edge="1" source="act_block" target="out_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- BLOCK/LIMIT → F5 -->
        <mxCell id="block_to_f5" value="SSH ipset add ppi_blocked" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="act_block" target="f5_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="limit_to_f5" value="SSH ipset add ppi_limited" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="act_limit" target="f5_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
