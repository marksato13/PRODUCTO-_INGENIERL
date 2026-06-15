# F2 — Diagrama Draw.io: Captura de Tráfico y Pipeline de Datos

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama — Escenarios A/B/C → eve.json → Pipeline → Dataset → F3

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F2_captura" name="F2 — Captura y Pipeline Dataset">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="title" value="F2 — Captura de Tráfico y Construcción del Dataset · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="400" y="15" width="900" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- GRUPO A — NORMAL (Desktop 192.168.0.20) -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="grpA" value="&lt;b&gt;Grupo A — Normal&lt;/b&gt;&lt;br&gt;Desktop 192.168.0.20 · label=0" style="swimlane;startSize=35;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="60" width="280" height="240" as="geometry" />
        </mxCell>
        <mxCell id="a1" value="A1_http_normal.sh&lt;br&gt;curl + wget → :80 · 10 min" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="grpA">
          <mxGeometry x="15" y="45" width="250" height="35" as="geometry" />
        </mxCell>
        <mxCell id="a2" value="A2_ssh_legitimo.sh&lt;br&gt;ssh → :22 · 8 min" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="grpA">
          <mxGeometry x="15" y="90" width="250" height="35" as="geometry" />
        </mxCell>
        <mxCell id="a3" value="A3_transferencia_legitima.sh&lt;br&gt;scp + wget · 10 min" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="grpA">
          <mxGeometry x="15" y="135" width="250" height="35" as="geometry" />
        </mxCell>
        <mxCell id="a4" value="A4_trafico_sostenido.sh&lt;br&gt;curl + ssh mixto · 15 min" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="grpA">
          <mxGeometry x="15" y="180" width="250" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- GRUPO B — ANÓMALO (Kali 192.168.0.100) -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="grpB" value="&lt;b&gt;Grupo B — Anómalo&lt;/b&gt;&lt;br&gt;Kali 192.168.0.100 · label=1" style="swimlane;startSize=35;fillColor=#f8cecc;strokeColor=#b85450;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="320" width="280" height="340" as="geometry" />
        </mxCell>
        <mxCell id="b1" value="B1_syn_flood.sh · hping3 -S --flood --rand-source" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="45" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b2" value="B2_port_scan.sh · nmap -sS -p 1-1024" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="85" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b3" value="B3_udp_flood.sh · hping3 --udp --flood --rand-source" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="125" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b4" value="B4_icmp_flood.sh · hping3 -1 --flood" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="165" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b5" value="B5_acceso_repetitivo.sh · curl en bucle → :80" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="205" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b6" value="B6_bruteforce.sh · hydra -l m4rk -P rockyou.txt ssh://" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="245" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="b_wait" value="⏱ Pausa ≥ 2 min entre corridas" style="text;html=1;fontSize=9;fontColor=#b85450;fontStyle=2;align=center;" vertex="1" parent="grpB">
          <mxGeometry x="15" y="285" width="250" height="20" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- GRUPO C — MIXTO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="grpC" value="&lt;b&gt;Grupo C — Mixto&lt;/b&gt;&lt;br&gt;Desktop + Kali simultáneos · label=1" style="swimlane;startSize=35;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="680" width="280" height="165" as="geometry" />
        </mxCell>
        <mxCell id="c1" value="C1_http_syn_mixto.sh · curl + SYN flood" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="grpC">
          <mxGeometry x="15" y="45" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="c2" value="C2_ssh_portscan_mixto.sh · ssh + nmap -sS" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="grpC">
          <mxGeometry x="15" y="85" width="250" height="30" as="geometry" />
        </mxCell>
        <mxCell id="c3" value="C3_descarga_udp_mixto.sh · wget + UDP flood" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="grpC">
          <mxGeometry x="15" y="125" width="250" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SERVIDOR OBJETIVO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="servidor" value="&lt;b&gt;Servidor Objetivo&lt;/b&gt;&lt;br&gt;192.168.0.120&lt;br&gt;─────────────────&lt;br&gt;nginx :80 ✅&lt;br&gt;openssh-server :22 ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6b656;fontSize=11;fontStyle=0;" vertex="1" parent="1">
          <mxGeometry x="400" y="400" width="200" height="130" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- EVE.JSON en SENSOR -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="sensor_box" value="Sensor 192.168.0.110 · ens35 promiscua" style="text;html=1;fontSize=10;fontStyle=1;fontColor=#2e7d32;" vertex="1" parent="1">
          <mxGeometry x="390" y="570" width="280" height="20" as="geometry" />
        </mxCell>
        <mxCell id="eve" value="&lt;b&gt;eve.json&lt;/b&gt;&lt;br&gt;/var/log/suricata/&lt;br&gt;JSON-lines · tiempo real&lt;br&gt;event_type: flow" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="410" y="595" width="180" height="90" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLECHAS: SCRIPTS → SERVIDOR -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="a_to_srv" value="tráfico normal · label=0" style="endArrow=block;endFill=1;html=1;strokeColor=#6c8ebf;strokeWidth=2;fontSize=10;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;" edge="1" source="grpA" target="servidor" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="b_to_srv" value="tráfico anómalo · label=1" style="endArrow=block;endFill=1;html=1;strokeColor=#b85450;strokeWidth=2;fontSize=10;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.6;entryDx=0;entryDy=0;" edge="1" source="grpB" target="servidor" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="c_to_srv" value="mixto · label=1" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=2;fontSize=10;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.9;entryDx=0;entryDy=0;" edge="1" source="grpC" target="servidor" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Suricata captura -->
        <mxCell id="srv_to_eve" value="captura promiscua ens35" style="endArrow=block;endFill=1;html=1;strokeColor=#82b366;strokeWidth=2;dashed=1;fontSize=10;" edge="1" source="servidor" target="eve" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- EXPORTAR EVE + BITÁCORA -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="exportar_bg" value="Al finalizar cada corrida (SSH desde Desktop)" style="swimlane;startSize=25;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="660" y="560" width="280" height="160" as="geometry" />
        </mxCell>
        <mxCell id="exportar_sh" value="&lt;b&gt;exportar_eve_por_escenario.sh&lt;/b&gt;&lt;br&gt;① gzip eve.json → data/raw/ARCHIVO.gz&lt;br&gt;② truncate -s 0 eve.json&lt;br&gt;③ suricatasc reopen-log-files" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=10;" vertex="1" parent="exportar_bg">
          <mxGeometry x="10" y="30" width="260" height="60" as="geometry" />
        </mxCell>
        <mxCell id="bitacora_sh" value="&lt;b&gt;registrar_bitacora.sh&lt;/b&gt;&lt;br&gt;→ docs/bitacora/bitacora_escenarios.txt&lt;br&gt;49 entradas · trazabilidad completa" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="exportar_bg">
          <mxGeometry x="10" y="100" width="260" height="45" as="geometry" />
        </mxCell>

        <mxCell id="eve_to_export" value="gzip + truncate" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth:2;fontSize=10;" edge="1" source="eve" target="exportar_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- DATA/RAW CONTAINER -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="raw_bg" value="&lt;b&gt;data/raw/&lt;/b&gt; — 38 archivos .gz" style="swimlane;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="660" y="320" width="280" height="220" as="geometry" />
        </mxCell>
        <mxCell id="raw_n" value="📦 Normal (label=0)&lt;br&gt;20260602_normal_http_01.gz&lt;br&gt;20260602_normal_ssh_01.gz&lt;br&gt;20260604_normal_ssh_03..10.gz" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=9;" vertex="1" parent="raw_bg">
          <mxGeometry x="10" y="38" width="258" height="55" as="geometry" />
        </mxCell>
        <mxCell id="raw_a" value="📦 Anómalo (label=1)&lt;br&gt;20260602_anom_synflood_01.gz · 4.6MB&lt;br&gt;20260602_anom_portscan_01.gz · 860KB&lt;br&gt;...(B1–B6 corridas)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=9;" vertex="1" parent="raw_bg">
          <mxGeometry x="10" y="103" width="258" height="55" as="geometry" />
        </mxCell>
        <mxCell id="raw_m" value="📦 Mixto (label=1)&lt;br&gt;20260602_mixto_http_syn_01.gz · 4.2MB&lt;br&gt;mixto_ssh_portscan · mixto_descarga_udp" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=9;" vertex="1" parent="raw_bg">
          <mxGeometry x="10" y="168" width="258" height="42" as="geometry" />
        </mxCell>

        <mxCell id="export_to_raw" value="YYYYMMDD_grupo_esc_NN_eve.json.gz" style="endArrow=block;endFill=1;html=1;strokeColor=#666666;strokeWidth=2;fontSize=9;" edge="1" source="exportar_bg" target="raw_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- PIPELINE: PARSER → ETIQUETAR → PARTICIONAR -->
        <!-- ══════════════════════════════════════════════════════ -->

        <!-- parser.py -->
        <mxCell id="parser" value="&lt;b&gt;scripts/parser.py&lt;/b&gt;&lt;br&gt;Lee todos los .gz&lt;br&gt;Filtra event_type=='flow'&lt;br&gt;Label: _normal_ → 0 · resto → 1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;fontStyle=0;" vertex="1" parent="1">
          <mxGeometry x="1010" y="280" width="220" height="80" as="geometry" />
        </mxCell>
        <mxCell id="dataset_raw_file" value="&lt;b&gt;dataset_raw.csv&lt;/b&gt;&lt;br&gt;412,097 flows · 75 MB&lt;br&gt;18 columnas" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1290" y="268" width="160" height="70" as="geometry" />
        </mxCell>

        <!-- etiquetar_limpiar.py -->
        <mxCell id="etiquetar" value="&lt;b&gt;scripts/etiquetar_limpiar.py&lt;/b&gt;&lt;br&gt;Refina label por src_ip&lt;br&gt;192.168.0.20 → 0 · .100 → 1&lt;br&gt;Elimina 34 dup + 35,236 IPs inv." style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1010" y="430" width="220" height="85" as="geometry" />
        </mxCell>
        <mxCell id="dataset_clean_file" value="&lt;b&gt;dataset_clean.csv&lt;/b&gt;&lt;br&gt;376,827 flows · 69 MB&lt;br&gt;Normal:   11,669 (3.1%)&lt;br&gt;Anómalo: 365,158 (96.9%)" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1290" y="418" width="160" height="85" as="geometry" />
        </mxCell>

        <!-- particionar_estadisticos.py -->
        <mxCell id="particionar" value="&lt;b&gt;scripts/particionar_estadisticos.py&lt;/b&gt;&lt;br&gt;Partición CRONOLÓGICA 70/15/15&lt;br&gt;Sin shuffle — evita data leakage" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1010" y="590" width="220" height="75" as="geometry" />
        </mxCell>

        <!-- train / val / test -->
        <mxCell id="train_file" value="&lt;b&gt;train.csv&lt;/b&gt;&lt;br&gt;263,778 flows · 48MB&lt;br&gt;70% cronológico" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1290" y="570" width="160" height="65" as="geometry" />
        </mxCell>
        <mxCell id="val_file" value="&lt;b&gt;val.csv&lt;/b&gt;&lt;br&gt;56,524 flows · 11MB&lt;br&gt;15% cronológico" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#bbdefb;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1290" y="648" width="160" height="60" as="geometry" />
        </mxCell>
        <mxCell id="test_file" value="&lt;b&gt;test.csv&lt;/b&gt;&lt;br&gt;56,525 flows · 11MB&lt;br&gt;15% cronológico" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#ffccbc;strokeColor=#bf360c;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1290" y="718" width="160" height="60" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLECHAS PIPELINE -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="raw_to_parser" value="38 archivos .gz" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=2;fontSize=10;" edge="1" source="raw_bg" target="parser" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="parser_to_raw_csv" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth:2;" edge="1" source="parser" target="dataset_raw_file" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="raw_csv_to_etiq" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#82b366;strokeWidth=2;" edge="1" source="dataset_raw_file" target="etiquetar" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1370" y="355" />
              <mxPoint x="1120" y="355" />
              <mxPoint x="1120" y="430" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="etiq_to_clean" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#82b366;strokeWidth=2;" edge="1" source="etiquetar" target="dataset_clean_file" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="clean_to_part" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="dataset_clean_file" target="particionar" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1370" y="518" />
              <mxPoint x="1120" y="518" />
              <mxPoint x="1120" y="590" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="part_to_train" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#388e3c;strokeWidth=2;" edge="1" source="particionar" target="train_file" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="part_to_val" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=1;" edge="1" source="particionar" target="val_file" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="part_to_test" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#bf360c;strokeWidth=1;" edge="1" source="particionar" target="test_file" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CONECTOR → F3 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="f3_conn" value="&lt;b&gt;→ F3: Modelado Offline&lt;/b&gt;&lt;br&gt;fase3_isolation_forest.py&lt;br&gt;Lee data/raw/*_normal_*_01/02.gz&lt;br&gt;Filtro src_ip Desktop → &lt;b&gt;684 flows&lt;/b&gt;&lt;br&gt;&lt;br&gt;train.csv + test.csv → evaluación IF" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=3;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1510" y="540" width="260" height="130" as="geometry" />
        </mxCell>
        <mxCell id="train_to_f3" value="684 normales (corridas 01-02)" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="train_file" target="f3_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="test_to_f3" value="evaluación AUC" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=2;dashed=1;fontSize=10;" edge="1" source="test_file" target="f3_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- NOMENCLATURA -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="nomen_bg" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#999999;" vertex="1" parent="1">
          <mxGeometry x="660" y="140" width="560" height="60" as="geometry" />
        </mxCell>
        <mxCell id="nomen_title" value="&lt;b&gt;Nomenclatura de archivos:&lt;/b&gt;  YYYYMMDD _ grupo _ escenario _ NN _ eve.json.gz" style="text;html=1;fontSize=11;align=center;" vertex="1" parent="1">
          <mxGeometry x="665" y="148" width="548" height="20" as="geometry" />
        </mxCell>
        <mxCell id="nomen_ex" value="Ejemplo:  20260602_normal_http_01_eve.json.gz  ·  20260602_anom_synflood_01_eve.json.gz" style="text;html=1;fontSize=10;align=center;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="665" y="170" width="548" height="20" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- ESTADÍSTICAS DATASET -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="stats_bg" value="&lt;b&gt;Dataset Final&lt;/b&gt;&lt;br&gt;376,827 flows · 69 MB&lt;br&gt;─────────────────────&lt;br&gt;Normal (A1-A4):  11,669 · 3.1%&lt;br&gt;Anómalo (B+C): 365,158 · 96.9%&lt;br&gt;─────────────────────&lt;br&gt;Escenario mayor: C3 109,839 flows&lt;br&gt;Escenario menor: A3 29 flows" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="1510" y="310" width="220" height="155" as="geometry" />
        </mxCell>
        <mxCell id="clean_to_stats" value="" style="endArrow=open;endFill=0;html=1;strokeColor=#2e7d32;dashed=1;fontSize=9;" edge="1" source="dataset_clean_file" target="stats_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
