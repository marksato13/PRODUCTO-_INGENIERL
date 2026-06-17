# Overview — Pipeline F1→F6

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1422" dy="762" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- TÍTULO -->
    <mxCell id="2" value="&lt;b&gt;PPI — Pipeline Completo F1→F6&lt;/b&gt;&lt;br&gt;Sistema de Detección Temprana de Anomalías de Red — Universidad Peruana Unión 2026" style="text;html=1;align=center;fontSize=16;fontStyle=1;strokeColor=none;fillColor=none;" vertex="1" parent="1">
      <mxGeometry x="200" y="15" width="1250" height="50" as="geometry" />
    </mxCell>

    <!-- ═══════════════ SECCIÓN OFFLINE (F1-F3) ═══════════════ -->
    <mxCell id="3" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;opacity=30;" vertex="1" parent="1">
      <mxGeometry x="10" y="75" width="1630" height="320" as="geometry" />
    </mxCell>
    <mxCell id="4" value="OFFLINE — F1 Captura de Tráfico  |  F2 Preparación de Datos  |  F3 Entrenamiento del Modelo Isolation Forest" style="text;html=1;align=left;fontStyle=1;fontSize=11;strokeColor=none;fillColor=none;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="20" y="80" width="800" height="20" as="geometry" />
    </mxCell>

    <!-- ── LAB TOPOLOGY ── -->
    <mxCell id="5" value="&lt;b&gt;Laboratorio&lt;/b&gt;" style="swimlane;startSize=25;fillColor=#f5f5f5;strokeColor=#666;fontColor=#333;fontSize=10;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="20" y="105" width="170" height="278" as="geometry" />
    </mxCell>
    <mxCell id="6" value="&lt;b&gt;Win11&lt;/b&gt; 192.168.0.10&lt;br&gt;Cliente HTTP/SSH" style="rounded=1;fillColor=#f5f5f5;strokeColor=#666;fontSize=9;" vertex="1" parent="5">
      <mxGeometry x="10" y="30" width="150" height="45" as="geometry" />
    </mxCell>
    <mxCell id="7" value="&lt;b&gt;Desktop&lt;/b&gt; 192.168.0.20&lt;br&gt;Tráfico normal + Relay Tg" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="5">
      <mxGeometry x="10" y="90" width="150" height="50" as="geometry" />
    </mxCell>
    <mxCell id="8" value="&lt;b&gt;Kali Linux&lt;/b&gt; 192.168.0.100&lt;br&gt;SYN Flood, PortScan, BF, UDP..." style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;" vertex="1" parent="5">
      <mxGeometry x="10" y="158" width="150" height="50" as="geometry" />
    </mxCell>
    <mxCell id="9" value="&lt;b&gt;Server&lt;/b&gt; 192.168.0.120&lt;br&gt;nginx:80 / SSH:22" style="rounded=1;fillColor=#647687;strokeColor=#314354;fontColor=#fff;fontSize=9;" vertex="1" parent="5">
      <mxGeometry x="10" y="222" width="150" height="45" as="geometry" />
    </mxCell>

    <!-- ── F1 SURICATA ── -->
    <mxCell id="10" value="&lt;b&gt;F1 — Captura de Tráfico&lt;/b&gt;" style="text;html=1;align=center;fontStyle=1;fontSize=10;strokeColor=none;fillColor=none;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="205" y="105" width="195" height="20" as="geometry" />
    </mxCell>
    <mxCell id="11" value="&lt;b&gt;Sensor 192.168.0.110&lt;/b&gt;" style="rounded=1;fillColor=#647687;strokeColor=#314354;fontColor=#fff;fontSize=10;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="205" y="128" width="195" height="35" as="geometry" />
    </mxCell>
    <mxCell id="12" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&lt;br&gt;ens35 — modo promiscuo&lt;br&gt;Análisis de flujos TCP/UDP/ICMP&lt;br&gt;Protocolo IDS en línea" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="205" y="175" width="195" height="75" as="geometry" />
    </mxCell>
    <mxCell id="13" value="&lt;b&gt;/var/log/suricata/eve.json&lt;/b&gt;&lt;br&gt;Eventos tipo: flow&lt;br&gt;Rotar al fin de cada corrida" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="205" y="263" width="195" height="80" as="geometry" />
    </mxCell>

    <!-- ── F2 DATA PREP ── -->
    <mxCell id="14" value="&lt;b&gt;F2 — Preparación de Datos&lt;/b&gt;" style="text;html=1;align=center;fontStyle=1;fontSize=10;strokeColor=none;fillColor=none;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="420" y="105" width="265" height="20" as="geometry" />
    </mxCell>
    <mxCell id="15" value="&lt;b&gt;parser.py&lt;/b&gt;&lt;br&gt;eve.json.gz → dataset_raw.csv&lt;br&gt;Extrae campos de flujos" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="420" y="128" width="265" height="60" as="geometry" />
    </mxCell>
    <mxCell id="16" value="&lt;b&gt;etiquetar_limpiar.py&lt;/b&gt;&lt;br&gt;Dedup, filtros IP, etiqueta normal/anomalía&lt;br&gt;→ dataset_clean.csv" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="420" y="203" width="265" height="60" as="geometry" />
    </mxCell>
    <mxCell id="17" value="&lt;b&gt;particionar_estadisticos.py&lt;/b&gt;&lt;br&gt;Split cronológico 70/15/15&lt;br&gt;→ train.csv / val.csv / test.csv" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="420" y="278" width="265" height="60" as="geometry" />
    </mxCell>

    <!-- ── F3 MODEL ── -->
    <mxCell id="18" value="&lt;b&gt;F3 — Entrenamiento Isolation Forest&lt;/b&gt;" style="text;html=1;align=center;fontStyle=1;fontSize=10;strokeColor=none;fillColor=none;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="705" y="105" width="390" height="20" as="geometry" />
    </mxCell>
    <mxCell id="19" value="&lt;b&gt;fase3_isolation_forest.py&lt;/b&gt;&lt;br&gt;IsolationForest(n_estimators=300,&lt;br&gt;contamination=0.05, random_state=42)&lt;br&gt;sklearn 1.9.0 — NO supervisado" style="rounded=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="705" y="128" width="230" height="80" as="geometry" />
    </mxCell>
    <mxCell id="20" value="&lt;b&gt;isolation_forest.pkl&lt;/b&gt;&lt;br&gt;&lt;b&gt;scaler.pkl&lt;/b&gt; (StandardScaler)&lt;br&gt;features.csv — 14 features" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="705" y="225" width="230" height="80" as="geometry" />
    </mxCell>
    <mxCell id="21" value="&lt;b&gt;auc_roc_umbrales.py&lt;/b&gt;&lt;br&gt;Curva ROC sobre test.csv&lt;br&gt;Youden J + FPR≤2%" style="rounded=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="955" y="128" width="210" height="70" as="geometry" />
    </mxCell>
    <mxCell id="22" value="&lt;b&gt;τ1 = −0.4459&lt;/b&gt; → PERMIT (Youden)&lt;br&gt;&lt;b&gt;τ2 = −0.6027&lt;/b&gt; → BLOCK (FPR≤2%)&lt;br&gt;metricas_offline.txt&lt;br&gt;AUC-ROC entrenamiento: 0.8998" style="rounded=1;fillColor=#FFD966;strokeColor=#d6b656;fontSize=9;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="955" y="218" width="210" height="80" as="geometry" />
    </mxCell>

    <!-- ── OFFLINE EDGES ── -->
    <!-- Lab flows → eve.json -->
    <mxCell id="23" value="flows red" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;strokeColor=#b85450;" edge="1" source="8" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="24" value="" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#82b366;" edge="1" source="7" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Suricata → eve.json -->
    <mxCell id="25" value="escribe" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="12" target="13" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- eve.json → parser -->
    <mxCell id="26" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="13" target="15" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- F2 chain -->
    <mxCell id="27" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="15" target="16" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="28" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="16" target="17" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- F2 → F3 -->
    <mxCell id="29" value="train.csv" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="17" target="19" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- F3 chain -->
    <mxCell id="30" value="guarda" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="19" target="20" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="31" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="20" target="21" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="32" value="deriva τ" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="21" target="22" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ═══════════════ SECCIÓN ONLINE (F4-F5) ═══════════════ -->
    <mxCell id="33" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;opacity=20;" vertex="1" parent="1">
      <mxGeometry x="10" y="415" width="1630" height="230" as="geometry" />
    </mxCell>
    <mxCell id="34" value="ONLINE (Tiempo Real) — F4 Motor de Decisión  |  F5 Control Inline sobre iptables/ipset" style="text;html=1;align=left;fontStyle=1;fontSize=11;strokeColor=none;fillColor=none;fontColor=#6F0000;" vertex="1" parent="1">
      <mxGeometry x="20" y="420" width="800" height="20" as="geometry" />
    </mxCell>

    <!-- eve.json LIVE -->
    <mxCell id="35" value="&lt;b&gt;eve.json (live)&lt;/b&gt;&lt;br&gt;tail -f&lt;br&gt;poll 0.1s" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="20" y="445" width="130" height="75" as="geometry" />
    </mxCell>

    <!-- Whitelist check -->
    <mxCell id="36" value="Whitelist?&lt;br&gt;.20 .110 .120...&lt;br&gt;→ skip PERMIT" style="rhombus;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="168" y="440" width="135" height="80" as="geometry" />
    </mxCell>

    <!-- 14 features -->
    <mxCell id="37" value="&lt;b&gt;14 Features&lt;/b&gt;&lt;br&gt;pkts_to/from, bytes_to/from&lt;br&gt;duration, pkt_rate, byte_rate&lt;br&gt;ratios, is_tcp/udp/icmp, port" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=8;" vertex="1" parent="1">
      <mxGeometry x="320" y="440" width="170" height="75" as="geometry" />
    </mxCell>

    <!-- scaler -->
    <mxCell id="38" value="scaler.transform()&lt;br&gt;StandardScaler" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="508" y="455" width="130" height="50" as="geometry" />
    </mxCell>

    <!-- IF score -->
    <mxCell id="39" value="&lt;b&gt;IF.score_samples()&lt;/b&gt;&lt;br&gt;score ∈ [−1, 0]&lt;br&gt;P95 latencia: 34.8ms" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="655" y="445" width="155" height="65" as="geometry" />
    </mxCell>

    <!-- Decision -->
    <mxCell id="40" value="&lt;b&gt;DECISIÓN&lt;/b&gt;&lt;br&gt;score &gt; τ1 → PERMIT&lt;br&gt;τ2 &lt; score ≤ τ1 → LIMIT&lt;br&gt;score ≤ τ2 → BLOCK" style="rounded=1;fillColor=#FF8000;strokeColor=#CC5500;fontColor=#ffffff;fontSize=9;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="828" y="435" width="175" height="80" as="geometry" />
    </mxCell>

    <!-- Heuristics -->
    <mxCell id="41" value="&lt;b&gt;BF-SSH Heurístico&lt;/b&gt;&lt;br&gt;≥5 intentos/60s → LIMIT&lt;br&gt;≥15 intentos/60s → BLOCK&lt;br&gt;(independiente del IF)" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=8;" vertex="1" parent="1">
      <mxGeometry x="508" y="540" width="170" height="65" as="geometry" />
    </mxCell>
    <mxCell id="42" value="&lt;b&gt;HTTP-ABUSE Heurístico&lt;/b&gt;&lt;br&gt;≥50 req/30s → LIMIT&lt;br&gt;≥100 req/30s → BLOCK&lt;br&gt;(independiente del IF)" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=8;" vertex="1" parent="1">
      <mxGeometry x="693" y="540" width="175" height="65" as="geometry" />
    </mxCell>

    <!-- F5 ipsets -->
    <mxCell id="43" value="&lt;b&gt;ppi_blocked&lt;/b&gt;&lt;br&gt;ipset hash:ip&lt;br&gt;timeout 300s&lt;br&gt;→ iptables DROP (pkt)" style="rounded=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1025" y="435" width="170" height="70" as="geometry" />
    </mxCell>
    <mxCell id="44" value="&lt;b&gt;ppi_limited&lt;/b&gt;&lt;br&gt;ipset hash:ip&lt;br&gt;timeout 300s&lt;br&gt;→ hashlimit 100 pkt/s" style="rounded=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1025" y="525" width="170" height="70" as="geometry" />
    </mxCell>
    <mxCell id="45" value="&lt;b&gt;Server 192.168.0.120&lt;/b&gt;&lt;br&gt;nginx:80 / SSH:22&lt;br&gt;iptables FORWARD chain&lt;br&gt;enforce.sh" style="rounded=1;fillColor=#647687;strokeColor=#314354;fontColor=#fff;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1215" y="460" width="185" height="80" as="geometry" />
    </mxCell>

    <!-- ONLINE EDGES -->
    <!-- eve live → whitelist -->
    <mxCell id="46" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="35" target="36" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- whitelist → features (not whitelisted) -->
    <mxCell id="47" value="no" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="36" target="37" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- features → scaler → IF → decision -->
    <mxCell id="48" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="37" target="38" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="49" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="38" target="39" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="50" value="score" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="39" target="40" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- τ1/τ2 → decision (config load, dashed) -->
    <mxCell id="51" value="carga τ1/τ2 al inicio" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;dashed=1;strokeColor=#d6b656;" edge="1" source="22" target="40" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- model pkl loaded by IF step -->
    <mxCell id="52" value="carga modelo" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;dashed=1;strokeColor=#d6b656;" edge="1" source="20" target="39" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- heuristics → decision -->
    <mxCell id="53" value="" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;" edge="1" source="41" target="40" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="54" value="" style="edgeStyle=orthogonalEdgeStyle;strokeColor=#b85450;" edge="1" source="42" target="40" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- decision → ipsets -->
    <mxCell id="55" value="BLOCK" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;strokeColor=#b85450;" edge="1" source="40" target="43" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="56" value="LIMIT" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;strokeColor=#FF8000;" edge="1" source="40" target="44" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- ipsets → server -->
    <mxCell id="57" value="DROP" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="43" target="45" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="58" value="LIMIT pkt" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;" edge="1" source="44" target="45" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- eve.json offline → eve.json live (mismo archivo) -->
    <mxCell id="59" value="mismo archivo" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;dashed=1;strokeColor=#888;" edge="1" source="13" target="35" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ═══════════════ SECCIÓN F6 + NOTIFICACIONES ═══════════════ -->
    <mxCell id="60" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;opacity=25;" vertex="1" parent="1">
      <mxGeometry x="10" y="665" width="1630" height="195" as="geometry" />
    </mxCell>
    <mxCell id="61" value="VALIDACIÓN F6 — 40 Corridas Batch  |  NOTIFICACIONES en Tiempo Real" style="text;html=1;align=left;fontStyle=1;fontSize=11;strokeColor=none;fillColor=none;fontColor=#003300;" vertex="1" parent="1">
      <mxGeometry x="20" y="670" width="700" height="20" as="geometry" />
    </mxCell>

    <!-- F6 blocks -->
    <mxCell id="62" value="&lt;b&gt;F6 — Validación Batch&lt;/b&gt;&lt;br&gt;f6_corridas.py&lt;br&gt;auc_por_escenario.py&lt;br&gt;40 corridas: A1-A4, B1-B6, C1-C3" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="20" y="695" width="200" height="75" as="geometry" />
    </mxCell>
    <mxCell id="63" value="resultados_f6_completo.csv&lt;br&gt;graficas_f6/ (7 PNG 300 DPI)&lt;br&gt;auc_por_escenario.png" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="235" y="695" width="170" height="75" as="geometry" />
    </mxCell>
    <mxCell id="64" value="&lt;b&gt;Métricas Finales Validadas&lt;/b&gt;&lt;br&gt;AUC-ROC: 0.8998 | Recall: 99.40%&lt;br&gt;Precision: 99.54% | F1: 0.9947&lt;br&gt;Latencia P95: 34.8ms | ITL: 0%&lt;br&gt;Disponibilidad: 100%" style="rounded=1;fillColor=#00897B;strokeColor=#00695C;fontColor=#ffffff;fontSize=9;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="420" y="690" width="235" height="85" as="geometry" />
    </mxCell>

    <!-- Notifications -->
    <mxCell id="65" value="&lt;b&gt;Dashboard Terminal&lt;/b&gt;&lt;br&gt;dashboard.py&lt;br&gt;stats motor cada 3s&lt;br&gt;(sensor)" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="680" y="695" width="155" height="75" as="geometry" />
    </mxCell>
    <mxCell id="66" value="&lt;b&gt;Dashboard Web&lt;/b&gt;&lt;br&gt;dashboard_web.py&lt;br&gt;Flask + SSE&lt;br&gt;http://sensor:8080" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="850" y="695" width="155" height="75" as="geometry" />
    </mxCell>
    <mxCell id="67" value="&lt;b&gt;Relay Telegram&lt;/b&gt;&lt;br&gt;telegram_relay.py&lt;br&gt;Desktop :8889&lt;br&gt;(sensor sin internet)" style="rounded=1;fillColor=#2AABEE;strokeColor=#1a7bbf;fontColor=#ffffff;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1020" y="695" width="155" height="75" as="geometry" />
    </mxCell>
    <mxCell id="68" value="&lt;b&gt;api.telegram.org&lt;/b&gt;&lt;br&gt;🚨 Alerta en celular&lt;br&gt;Token: 8677152686:..." style="rounded=1;fillColor=#1a7bbf;strokeColor=#1565C0;fontColor=#ffffff;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1190" y="695" width="155" height="75" as="geometry" />
    </mxCell>

    <!-- F6 + NOTIFICATIONS EDGES -->
    <mxCell id="69" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="62" target="63" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="70" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="63" target="64" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- motor logs → dashboards -->
    <mxCell id="71" value="motor_decision.log" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;dashed=1;" edge="1" source="40" target="65" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="72" value="" style="edgeStyle=orthogonalEdgeStyle;dashed=1;" edge="1" source="40" target="66" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- motor → relay telegram -->
    <mxCell id="73" value="POST JSON alerta" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;strokeColor=#2AABEE;" edge="1" source="40" target="67" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- relay → telegram API -->
    <mxCell id="74" value="HTTPS forward" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;strokeColor=#1a7bbf;" edge="1" source="67" target="68" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- F6 uses motor log data -->
    <mxCell id="75" value="corridas batch" style="edgeStyle=orthogonalEdgeStyle;fontSize=8;dashed=1;" edge="1" source="40" target="62" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ═══════════════ LEYENDA ═══════════════ -->
    <mxCell id="76" value="&lt;b&gt;Leyenda&lt;/b&gt;" style="text;html=1;fontStyle=1;fontSize=10;strokeColor=none;fillColor=none;" vertex="1" parent="1">
      <mxGeometry x="1430" y="80" width="80" height="20" as="geometry" />
    </mxCell>
    <mxCell id="77" value="F1 Captura" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="105" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="78" value="F2 Preparación de datos" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="145" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="79" value="F3 Modelo (Isolation Forest)" style="rounded=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="185" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="80" value="F4 Motor de decisión (online)" style="rounded=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="225" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="81" value="F5 Control inline (ipset/iptables)" style="rounded=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="265" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="82" value="F6 Validación + métricas" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="305" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="83" value="Telegram (notificación)" style="rounded=1;fillColor=#2AABEE;strokeColor=#1a7bbf;fontColor=#fff;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="345" width="195" height="30" as="geometry" />
    </mxCell>
    <mxCell id="84" value="Whitelist (nunca bloquear)" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=9;" vertex="1" parent="1">
      <mxGeometry x="1430" y="385" width="195" height="30" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```
