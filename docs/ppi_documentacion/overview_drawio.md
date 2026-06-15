# Overview — Diagrama Draw.io: Pipeline Completo F1 → F6

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama General — Sistema de Detección Temprana PPI UPeU 2026

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="overview_ppi" name="Overview — Pipeline F1-F6">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- TÍTULO Y SUBTÍTULO -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="titulo" value="Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos" style="text;html=1;fontSize=18;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="100" y="15" width="1700" height="28" as="geometry" />
        </mxCell>
        <mxCell id="subtitulo" value="Universidad Peruana Unión · PPI 2026 · Rubén Mark Salazar Tocas · Ing. Nemias Saboya · Ing. Fernando Asin" style="text;html=1;fontSize=11;align=center;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="100" y="43" width="1700" height="18" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- RED LAN — TOPOLOGÍA -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="lan_bg" value="Red LAN 192.168.0.0/24 — VMware" style="swimlane;startSize=25;fillColor=#eceff1;strokeColor=#607d8b;fontSize=11;fontStyle=1;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="30" y="80" width="330" height="430" as="geometry" />
        </mxCell>

        <mxCell id="pfsense" value="&lt;b&gt;pfSense&lt;/b&gt;&lt;br&gt;192.168.0.1&lt;br&gt;Gateway · Firewall" style="shape=mxgraph.network.router;fillColor=#e1d5e7;strokeColor=#9673a6;html=1;fontSize=10;labelPosition=right;align=left;verticalLabelPosition=middle;verticalAlign=middle;" vertex="1" parent="lan_bg">
          <mxGeometry x="120" y="35" width="60" height="45" as="geometry" />
        </mxCell>

        <mxCell id="desktop_vm" value="&lt;b&gt;Desktop 192.168.0.20&lt;/b&gt;&lt;br&gt;Administrador · Claude Code&lt;br&gt;Scripts A1–A4 · C1–C3&lt;br&gt;curl · ssh · scp · wget" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="lan_bg">
          <mxGeometry x="10" y="115" width="195" height="70" as="geometry" />
        </mxCell>

        <mxCell id="kali_vm" value="&lt;b&gt;Kali 192.168.0.100&lt;/b&gt;&lt;br&gt;Atacante controlado&lt;br&gt;hping3 · nmap · hydra&lt;br&gt;Scripts B1–B6" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="lan_bg">
          <mxGeometry x="10" y="205" width="195" height="70" as="geometry" />
        </mxCell>

        <mxCell id="sensor_vm" value="&lt;b&gt;Sensor 192.168.0.110&lt;/b&gt;&lt;br&gt;Suricata 7.0.3 · ens35&lt;br&gt;motor_decision.py&lt;br&gt;ppi-motor.service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;fontStyle=1;" vertex="1" parent="lan_bg">
          <mxGeometry x="120" y="295" width="195" height="70" as="geometry" />
        </mxCell>

        <mxCell id="server_vm" value="&lt;b&gt;Servidor 192.168.0.120&lt;/b&gt;&lt;br&gt;nginx :80 · sshd :22&lt;br&gt;ipset ppi_blocked/ppi_limited&lt;br&gt;iptables DROP + hashlimit" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="lan_bg">
          <mxGeometry x="10" y="340" width="195" height="70" as="geometry" />
        </mxCell>

        <!-- LAN connections -->
        <mxCell id="pfs_dt" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#607d8b;" edge="1" source="pfsense" target="desktop_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="pfs_kl" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#607d8b;" edge="1" source="pfsense" target="kali_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="pfs_sn" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#607d8b;" edge="1" source="pfsense" target="sensor_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="pfs_sv" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#607d8b;" edge="1" source="pfsense" target="server_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="dt_srv_traf" value="A: normal" style="endArrow=block;endFill=1;html=1;strokeColor=#6c8ebf;strokeWidth=2;fontSize=9;" edge="1" source="desktop_vm" target="server_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="kl_srv_traf" value="B: ataque" style="endArrow=block;endFill=1;html=1;strokeColor=#b85450;strokeWidth=2;fontSize=9;" edge="1" source="kali_vm" target="server_vm" parent="lan_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F1 — ENTORNO -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f1_bg" value="&lt;b&gt;F1 — Entorno de Laboratorio&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="390" y="80" width="220" height="180" as="geometry" />
        </mxCell>

        <mxCell id="f1_suri" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&lt;br&gt;ens35 — promiscua&lt;br&gt;DPI por flow&lt;br&gt;af-packet: ens35" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="f1_bg">
          <mxGeometry x="10" y="38" width="198" height="60" as="geometry" />
        </mxCell>
        <mxCell id="f1_eve" value="&lt;b&gt;eve.json&lt;/b&gt;&lt;br&gt;/var/log/suricata/&lt;br&gt;JSON-lines · flow events" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#bbdefb;strokeColor=#1565c0;fontSize=10;fontStyle=1;" vertex="1" parent="f1_bg">
          <mxGeometry x="35" y="110" width="148" height="60" as="geometry" />
        </mxCell>
        <mxCell id="f1_suri_to_eve" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=2;" edge="1" source="f1_suri" target="f1_eve" parent="f1_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F2 — CAPTURA -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f2_bg" value="&lt;b&gt;F2 — Captura y Dataset&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="390" y="290" width="220" height="260" as="geometry" />
        </mxCell>

        <mxCell id="f2_esc" value="13 escenarios A/B/C&lt;br&gt;38 corridas · 49 bitácora&lt;br&gt;exportar_eve.sh" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="f2_bg">
          <mxGeometry x="10" y="38" width="198" height="50" as="geometry" />
        </mxCell>
        <mxCell id="f2_raw" value="data/raw/ · 38 .gz&lt;br&gt;YYYYMMDD_grupo_esc_NN.gz" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="f2_bg">
          <mxGeometry x="10" y="98" width="198" height="38" as="geometry" />
        </mxCell>
        <mxCell id="f2_pipe" value="parser.py → 412K flows&lt;br&gt;etiquetar_limpiar.py → 377K&lt;br&gt;particionar → 70/15/15" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="f2_bg">
          <mxGeometry x="10" y="146" width="198" height="50" as="geometry" />
        </mxCell>
        <mxCell id="f2_out" value="&lt;b&gt;train/val/test.csv&lt;/b&gt;&lt;br&gt;376,827 flows · 69MB" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#2e7d32;fontSize=10;fontStyle=1;" vertex="1" parent="f2_bg">
          <mxGeometry x="35" y="206" width="148" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f2e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=1;" edge="1" source="f2_esc" target="f2_raw" parent="f2_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f2e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=1;" edge="1" source="f2_raw" target="f2_pipe" parent="f2_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f2e3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth:2;" edge="1" source="f2_pipe" target="f2_out" parent="f2_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F3 — MODELO -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f3_bg" value="&lt;b&gt;F3 — Isolation Forest&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fff3e0;strokeColor=#e65100;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="640" y="80" width="260" height="470" as="geometry" />
        </mxCell>

        <mxCell id="f3_input" value="684 flows normales&lt;br&gt;corridas 01-02 · src_ip Desktop&lt;br&gt;filtro doble" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="38" width="238" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f3_feats" value="14 Features por flow&lt;br&gt;pkts · bytes · duration&lt;br&gt;pkt_rate · byte_rate · ratios&lt;br&gt;is_tcp · is_udp · is_icmp · port" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="95" width="238" height="65" as="geometry" />
        </mxCell>
        <mxCell id="f3_scaler" value="&lt;b&gt;StandardScaler&lt;/b&gt;&lt;br&gt;fit solo en normales&lt;br&gt;→ scaler.pkl  1.4KB" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="172" width="238" height="50" as="geometry" />
        </mxCell>
        <mxCell id="f3_if" value="&lt;b&gt;IsolationForest&lt;/b&gt;&lt;br&gt;n_estimators=300 · contam=0.05&lt;br&gt;AUC=0.9440 · Recall=87.6%&lt;br&gt;→ isolation_forest.pkl  2.5MB" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#9673a6;strokeColor=#6a1b9a;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="234" width="238" height="65" as="geometry" />
        </mxCell>
        <mxCell id="f3_tau" value="&lt;b&gt;τ1 = −0.4973&lt;/b&gt;  PERMIT/LIMIT&lt;br&gt;Youden: TPR=91% FPR=9.5%&lt;br&gt;&lt;b&gt;τ2 = −0.6873&lt;/b&gt;  LIMIT/BLOCK&lt;br&gt;FPR≤2%: TPR=40.6%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;fontStyle=1;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="312" width="238" height="65" as="geometry" />
        </mxCell>
        <mxCell id="f3_recal" value="v1: 2026-06-02 (binario)&lt;br&gt;v2: 2026-06-04 (triple) ← prod." style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=9;dashed=1;" vertex="1" parent="f3_bg">
          <mxGeometry x="10" y="390" width="238" height="35" as="geometry" />
        </mxCell>
        <mxCell id="f3e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=1;" edge="1" source="f3_input" target="f3_feats" parent="f3_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f3e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=1;" edge="1" source="f3_feats" target="f3_scaler" parent="f3_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f3e3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="f3_scaler" target="f3_if" parent="f3_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f3e4" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth:2;" edge="1" source="f3_if" target="f3_tau" parent="f3_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F4 — MOTOR DE DECISIÓN -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f4_bg" value="&lt;b&gt;F4 — Motor de Decisión&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fce4ec;strokeColor=#c62828;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="930" y="80" width="280" height="470" as="geometry" />
        </mxCell>

        <mxCell id="f4_eve" value="seguir_eve()&lt;br&gt;tail -f eve.json · rotación" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="38" width="258" height="35" as="geometry" />
        </mxCell>
        <mxCell id="f4_fil" value="5 Filtros: event_type · IPv4&lt;br&gt;WHITELIST · es_ip_bloqueable · pkts&gt;0" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="83" width="258" height="40" as="geometry" />
        </mxCell>
        <mxCell id="f4_pipe" value="extract_features() → [1×14]&lt;br&gt;scaler.transform()&lt;br&gt;clf.score_samples() → score" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c62828;strokeColor=#7f0000;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="133" width="258" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f4_det" value="Det. SSH: 5→LIMIT / 15→BLOCK / 60s&lt;br&gt;Det. HTTP: 50→LIMIT / 100→BLOCK / 30s&lt;br&gt;explicar_anomalia(): Top-3 z-scores" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="200" width="258" height="55" as="geometry" />
        </mxCell>
        <mxCell id="f4_dec_permit" value="PERMIT&lt;br&gt;log.debug()" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="275" width="75" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f4_dec_limit" value="LIMIT&lt;br&gt;WARNING&lt;br&gt;Telegram ⚠️" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;fontStyle=1;" vertex="1" parent="f4_bg">
          <mxGeometry x="95" y="275" width="80" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f4_dec_block" value="BLOCK&lt;br&gt;WARNING&lt;br&gt;Telegram 🚨" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;fontStyle=1;" vertex="1" parent="f4_bg">
          <mxGeometry x="185" y="275" width="75" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f4_log" value="&lt;b&gt;motor_decision.log&lt;/b&gt;  7.6MB&lt;br&gt;P95=34.8ms · Throughput=29 flows/s" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="f4_bg">
          <mxGeometry x="35" y="335" width="205" height="45" as="geometry" />
        </mxCell>
        <mxCell id="f4_svc" value="ppi-motor.service · Restart=on-failure" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=9;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="393" width="258" height="28" as="geometry" />
        </mxCell>
        <mxCell id="f4_grado" value="NORMAL / BAJA / ALTA / CRÍTICA" style="text;html=1;fontSize=9;align=center;fontColor=#666666;" vertex="1" parent="f4_bg">
          <mxGeometry x="10" y="430" width="258" height="18" as="geometry" />
        </mxCell>

        <mxCell id="f4e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=1;" edge="1" source="f4_eve" target="f4_fil" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=2;" edge="1" source="f4_fil" target="f4_pipe" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4e3" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth:1;" edge="1" source="f4_pipe" target="f4_det" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4e4a" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#388e3c;strokeWidth=1;" edge="1" source="f4_det" target="f4_dec_permit" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4e4b" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=1;" edge="1" source="f4_det" target="f4_dec_limit" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4e4c" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;" edge="1" source="f4_det" target="f4_dec_block" parent="f4_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F5 — CONTROL INLINE -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f5_bg" value="&lt;b&gt;F5 — Control Inline&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1240" y="80" width="270" height="320" as="geometry" />
        </mxCell>

        <mxCell id="f5_ssh" value="SSH → 192.168.0.120&lt;br&gt;bloquear_ip() / limitar_ip()&lt;br&gt;subprocess · ConnectTimeout=5s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="f5_bg">
          <mxGeometry x="10" y="38" width="248" height="50" as="geometry" />
        </mxCell>
        <mxCell id="f5_blocked" value="&lt;b&gt;ipset ppi_blocked&lt;/b&gt;&lt;br&gt;hash:ip · timeout 300s&lt;br&gt;→ iptables DROP total" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#b71c1c;fontSize=10;fontStyle=1;" vertex="1" parent="f5_bg">
          <mxGeometry x="10" y="100" width="113" height="65" as="geometry" />
        </mxCell>
        <mxCell id="f5_limited" value="&lt;b&gt;ipset ppi_limited&lt;/b&gt;&lt;br&gt;hash:ip · timeout 300s&lt;br&gt;→ hashlimit 100/s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;fontStyle=1;" vertex="1" parent="f5_bg">
          <mxGeometry x="133" y="100" width="125" height="65" as="geometry" />
        </mxCell>
        <mxCell id="f5_enforce" value="enforce.sh&lt;br&gt;BLOCK · LIMIT · UNBLOCK manual" style="shape=note;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="f5_bg">
          <mxGeometry x="10" y="180" width="248" height="40" as="geometry" />
        </mxCell>
        <mxCell id="f5_timeout" value="Timeout 300s automático (kernel)&lt;br&gt;Motor re-detecta y re-bloquea" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="f5_bg">
          <mxGeometry x="10" y="233" width="248" height="38" as="geometry" />
        </mxCell>
        <mxCell id="f5_dashboard" value="dashboard_web.py :8080 · Flask+SSE&lt;br&gt;dashboard.py · terminal cada 3s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=10;" vertex="1" parent="f5_bg">
          <mxGeometry x="10" y="278" width="248" height="35" as="geometry" />
        </mxCell>
        <mxCell id="f5e1" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#b71c1c;strokeWidth=2;" edge="1" source="f5_ssh" target="f5_blocked" parent="f5_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f5e2" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="f5_ssh" target="f5_limited" parent="f5_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- F6 — VALIDACIÓN -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="f6_bg" value="&lt;b&gt;F6 — Validación&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fffde7;strokeColor=#f9a825;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1540" y="80" width="340" height="470" as="geometry" />
        </mxCell>

        <mxCell id="f6_script" value="&lt;b&gt;f6_corridas.py&lt;/b&gt;&lt;br&gt;40 corridas · 4 grupos × 10&lt;br&gt;300s/corrida · 60s pausa" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fffde7;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="38" width="318" height="50" as="geometry" />
        </mxCell>

        <!-- Métricas -->
        <mxCell id="f6_m1" value="Disponibilidad = &lt;b&gt;100%&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="100" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m2" value="ITL (Impacto Tráfico Legítimo) = &lt;b&gt;0%&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="130" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m3" value="TIE (Tasa Intervención Efectiva) = &lt;b&gt;100%&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="160" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m4" value="Lead Time = &lt;b&gt;26s&lt;/b&gt; · MTTC = &lt;b&gt;28s&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="190" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m5" value="Latencia P95 = &lt;b&gt;34.8ms&lt;/b&gt; ✅  (&lt;500ms · 14× margen)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="220" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m6" value="AUC=0.9440 · Recall=92–95% · Precision=99.96%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2e7d32;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="250" width="318" height="24" as="geometry" />
        </mxCell>
        <mxCell id="f6_m7" value="FPR SSH=0% · FPR Transferencia=0% ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2e7d32;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="280" width="318" height="24" as="geometry" />
        </mxCell>

        <!-- Entregables -->
        <mxCell id="f6_pdf" value="&lt;b&gt;reporte_validacion_final.pdf&lt;/b&gt;  7.4KB" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="320" width="148" height="40" as="geometry" />
        </mxCell>
        <mxCell id="f6_zip" value="&lt;b&gt;MVP_funcional.zip&lt;/b&gt;  25MB" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="170" y="320" width="148" height="40" as="geometry" />
        </mxCell>
        <mxCell id="f6_csv" value="resultados_f6_completo.csv  3.9KB" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fffde7;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="f6_bg">
          <mxGeometry x="60" y="374" width="200" height="38" as="geometry" />
        </mxCell>
        <mxCell id="f6_github" value="GitHub: marksato13/PRODUCTO-_INGENIERL&lt;br&gt;35+ commits · 54 docs · 44 diagramas" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=9;" vertex="1" parent="f6_bg">
          <mxGeometry x="10" y="425" width="318" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- TELEGRAM + DASHBOARD (abajo) -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="tg_box" value="&lt;b&gt;📱 Telegram Bot&lt;/b&gt;&lt;br&gt;🚨 BLOCK · ⚠️ LIMIT&lt;br&gt;🔑 BruteForce · 🌐 HTTP&lt;br&gt;Cola async daemon&lt;br&gt;300–800ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="930" y="590" width="200" height="100" as="geometry" />
        </mxCell>
        <mxCell id="dash_box" value="&lt;b&gt;🖥️ Dashboard Web&lt;/b&gt;&lt;br&gt;http://192.168.0.110:8080&lt;br&gt;Flask + SSE · 6 vistas&lt;br&gt;Auto-refresca ~150ms&lt;br&gt;ppi-dashboard.service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1150" y="590" width="210" height="100" as="geometry" />
        </mxCell>
        <mxCell id="dash_term_box" value="&lt;b&gt;📟 Terminal&lt;/b&gt;&lt;br&gt;dashboard.py · cada 3s&lt;br&gt;flows · alertas · latencia" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1380" y="590" width="180" height="100" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- FLECHAS ENTRE FASES (FLUJO PRINCIPAL) -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- LAN → F1 -->
        <mxCell id="lan_to_f1" value="tráfico LAN" style="endArrow=block;endFill=1;html=1;strokeColor=#607d8b;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="lan_bg" target="f1_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F1 → F2 -->
        <mxCell id="f1_to_f2" value="eve.json" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="f1_bg" target="f2_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F2 → F3 -->
        <mxCell id="f2_to_f3" value="684 flows&lt;br&gt;normales" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="f2_bg" target="f3_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F3 → F4 -->
        <mxCell id="f3_to_f4" value="*.pkl&lt;br&gt;τ1 · τ2" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="f3_bg" target="f4_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- eve.json → F4 (runtime) -->
        <mxCell id="eve_to_f4" value="seguir_eve()\ntiempo real" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth:2;dashed=1;fontSize=9;" edge="1" source="f1_bg" target="f4_bg" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="500" y="200" />
              <mxPoint x="500" y="660" />
              <mxPoint x="1070" y="660" />
              <mxPoint x="1070" y="200" />
            </Array>
          </mxGeometry>
        </mxCell>
        <!-- F4 → F5 -->
        <mxCell id="f4_to_f5" value="BLOCK/LIMIT&lt;br&gt;SSH ipset add" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="f4_bg" target="f5_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F5 → F6 -->
        <mxCell id="f5_to_f6" value="sistema&lt;br&gt;operativo" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="f5_bg" target="f6_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F4 → Telegram -->
        <mxCell id="f4_to_tg" value="telegram_alerta()" style="endArrow=block;endFill=1;html=1;strokeColor=#0277bd;strokeWidth=2;dashed=1;fontSize=9;" edge="1" source="f4_bg" target="tg_box" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F4 → Dashboard -->
        <mxCell id="f4_to_dash" value="motor_decision.log" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=2;dashed=1;fontSize=9;" edge="1" source="f4_bg" target="dash_box" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="f4_to_dterm" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=1;dashed=1;" edge="1" source="f4_bg" target="dash_term_box" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <!-- F5 → Server paquetes -->
        <mxCell id="f5_to_srv" value="ipset DROP&lt;br&gt;hashlimit" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth:2;fontSize=9;" edge="1" source="f5_bg" target="server_vm" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════════════════ -->
        <!-- LEYENDA FASES -->
        <!-- ══════════════════════════════════════════════════════════════════ -->
        <mxCell id="leyenda_bg" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#9e9e9e;" vertex="1" parent="1">
          <mxGeometry x="30" y="560" width="870" height="55" as="geometry" />
        </mxCell>
        <mxCell id="ley_f1" value="■ F1 Entorno" style="text;html=1;fontSize=11;fontColor=#1565c0;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="45" y="572" width="110" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_f2" value="■ F2 Captura" style="text;html=1;fontSize=11;fontColor=#2e7d32;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="160" y="572" width="110" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_f3" value="■ F3 Modelo IF" style="text;html=1;fontSize=11;fontColor=#e65100;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="280" y="572" width="120" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_f4" value="■ F4 Motor" style="text;html=1;fontSize=11;fontColor=#c62828;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="410" y="572" width="100" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_f5" value="■ F5 Control Inline" style="text;html=1;fontSize=11;fontColor=#9673a6;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="520" y="572" width="150" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_f6" value="■ F6 Validación" style="text;html=1;fontSize=11;fontColor=#f9a825;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="680" y="572" width="130" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley_lines" value="── Flujo principal datos    - - Flujo runtime/async" style="text;html=1;fontSize=10;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="45" y="592" width="840" height="18" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
