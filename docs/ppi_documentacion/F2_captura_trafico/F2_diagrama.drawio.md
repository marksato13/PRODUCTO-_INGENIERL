# F2 — Diagrama: Pipeline de Captura y Preprocesamiento

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
  tooltips="1" connect="1" arrows="1" fold="1" page="0"
  pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- ══════════════════════════════════════════════════════════
         TÍTULO
    ══════════════════════════════════════════════════════════ -->
    <mxCell id="title" value="F2 — Pipeline de Captura y Preprocesamiento de Tráfico  |  PPI UPeU 2026"
      style="text;html=1;strokeColor=none;fillColor=#002060;fontColor=#ffffff;
             align=center;verticalAlign=middle;fontSize=14;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="60" y="15" width="1330" height="40" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         ZONA 1 — CAPTURA (fondo azul claro)
    ══════════════════════════════════════════════════════════ -->
    <mxCell id="zona1_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f1ff;strokeColor=#6c8ebf;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="55" y="62" width="1340" height="370" as="geometry" />
    </mxCell>
    <mxCell id="zona1_lbl" value="FASE DE CAPTURA"
      style="text;html=1;strokeColor=none;fillColor=#6c8ebf;fontColor=#ffffff;
             align=left;fontSize=12;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="55" y="62" width="200" height="28" as="geometry" />
    </mxCell>

    <!-- Desktop .20 -->
    <mxCell id="desktop" value="&lt;b&gt;Desktop (.20)&lt;/b&gt;&lt;br/&gt;Ubuntu 22.04&lt;br/&gt;curl · wget · scp · ssh&lt;br/&gt;&lt;i&gt;Grupos A y C (normal)&lt;/i&gt;"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="95" width="180" height="95" as="geometry" />
    </mxCell>

    <!-- Kali .100 -->
    <mxCell id="kali" value="&lt;b&gt;Kali (.100)&lt;/b&gt;&lt;br/&gt;Kali 2024&lt;br/&gt;hping3 · nmap · hydra&lt;br/&gt;&lt;i&gt;Grupos B y C (anómalo)&lt;/i&gt;"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="80" y="228" width="180" height="95" as="geometry" />
    </mxCell>

    <!-- Switch -->
    <mxCell id="switch" value="&lt;b&gt;Switch Virtual&lt;/b&gt;&lt;br/&gt;192.168.0.0/24"
      style="ellipse;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#555555;
             fontColor=#333333;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="320" y="155" width="165" height="80" as="geometry" />
    </mxCell>

    <!-- Server .120 -->
    <mxCell id="server" value="&lt;b&gt;Server (.120)&lt;/b&gt;&lt;br/&gt;nginx:80 · SSH:22&lt;br/&gt;&lt;i&gt;destino del tráfico&lt;/i&gt;"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="555" y="165" width="175" height="75" as="geometry" />
    </mxCell>

    <!-- Suricata (sensor) -->
    <mxCell id="suricata" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt; (sensor .110)&lt;br/&gt;Modo: IDS pasivo (af-packet)&lt;br/&gt;Interfaz: ens35&lt;br/&gt;Captura: todos los flows de la red&lt;br/&gt;Servicio: suricata.service"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0050ef;strokeColor=#003399;
             fontColor=#ffffff;fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="790" y="100" width="245" height="115" as="geometry" />
    </mxCell>

    <!-- eve.json (archivo live) -->
    <mxCell id="eve_json" value="&lt;b&gt;/var/log/suricata/eve.json&lt;/b&gt;&lt;br/&gt;EVE JSON en tiempo real&lt;br/&gt;event_type: flow · alert · http · ssh"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="800" y="265" width="225" height="75" as="geometry" />
    </mxCell>

    <!-- exportar_eve_por_escenario.sh -->
    <mxCell id="exportar_sh" value="&lt;b&gt;exportar_eve_por_escenario.sh&lt;/b&gt;&lt;br/&gt;1. gzip -c eve.json → .gz&lt;br/&gt;2. truncate -s 0 eve.json&lt;br/&gt;3. suricatasc reopen-log-files"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="1085" y="98" width="250" height="85" as="geometry" />
    </mxCell>

    <!-- registrar_bitacora.sh -->
    <mxCell id="registrar_sh" value="&lt;b&gt;registrar_bitacora.sh&lt;/b&gt;&lt;br/&gt;Agrega línea al log de corridas&lt;br/&gt;(fecha | grupo | escenario | IPs | horas)"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="1085" y="205" width="250" height="70" as="geometry" />
    </mxCell>

    <!-- data/raw (51 archivos .gz) -->
    <mxCell id="data_raw" value="&lt;b&gt;data/raw/&lt;/b&gt;&lt;br/&gt;51 archivos .eve.json.gz&lt;br/&gt;YYYYMMDD_grupo_escenario_NN_*.gz&lt;br/&gt;28 normales · 13 anóm · 10 mixtos"
      style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
             fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="1085" y="295" width="250" height="90" as="geometry" />
    </mxCell>

    <!-- bitacora -->
    <mxCell id="bitacora" value="&lt;b&gt;bitacora_escenarios.txt&lt;/b&gt;&lt;br/&gt;51 líneas de registro&lt;br/&gt;&lt;i&gt;docs/bitacora/&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="1085" y="402" width="250" height="70" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         ZONA 2 — PROCESAMIENTO (fondo verde claro)
    ══════════════════════════════════════════════════════════ -->
    <mxCell id="zona2_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8ffe8;strokeColor=#82b366;fontSize=11;"
      vertex="1" parent="1">
      <mxGeometry x="55" y="455" width="1340" height="360" as="geometry" />
    </mxCell>
    <mxCell id="zona2_lbl" value="FASE DE PROCESAMIENTO"
      style="text;html=1;strokeColor=none;fillColor=#82b366;fontColor=#ffffff;
             align=left;fontSize=12;fontStyle=1;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="55" y="455" width="240" height="28" as="geometry" />
    </mxCell>

    <!-- data/raw entrada (referencia en zona 2) -->
    <mxCell id="data_raw_ref" value="&lt;b&gt;data/raw/*.eve.json.gz&lt;/b&gt;&lt;br/&gt;51 capturas comprimidas&lt;br/&gt;(entrada al pipeline)"
      style="shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;
             fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="75" y="490" width="210" height="80" as="geometry" />
    </mxCell>

    <!-- parser.py -->
    <mxCell id="parser_py" value="&lt;b&gt;parser.py&lt;/b&gt;&lt;br/&gt;Lee cada .gz (event_type=flow)&lt;br/&gt;Extrae 14 features por flujo&lt;br/&gt;Rellena 0 si campo ausente"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="355" y="490" width="205" height="90" as="geometry" />
    </mxCell>

    <!-- dataset_raw.csv -->
    <mxCell id="raw_csv" value="&lt;b&gt;dataset_raw.csv&lt;/b&gt;&lt;br/&gt;&gt; 800,000 filas&lt;br/&gt;Sin limpiar · con duplicados&lt;br/&gt;data/"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="630" y="490" width="205" height="90" as="geometry" />
    </mxCell>

    <!-- etiquetar_limpiar.py -->
    <mxCell id="etiquetar_py" value="&lt;b&gt;etiquetar_limpiar.py&lt;/b&gt;&lt;br/&gt;1. Label: .100→1 · .20→0&lt;br/&gt;2. Filtro whitelist IPs&lt;br/&gt;3. Dedup por flow_id&lt;br/&gt;4. Drop NaN"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="905" y="480" width="215" height="110" as="geometry" />
    </mxCell>

    <!-- dataset_clean.csv -->
    <mxCell id="clean_csv" value="&lt;b&gt;dataset_clean.csv&lt;/b&gt;&lt;br/&gt;~665,420 flows limpios&lt;br/&gt;label=0 · label=1&lt;br/&gt;14 features · sin NaN&lt;br/&gt;data/"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="1190" y="480" width="185" height="110" as="geometry" />
    </mxCell>

    <!-- particionar_estadisticos.py -->
    <mxCell id="particionar_py" value="&lt;b&gt;particionar_estadisticos.py&lt;/b&gt;&lt;br/&gt;Split cronológico (no aleatorio)&lt;br/&gt;70% train · 15% val · 15% test"
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;
             fontSize=10;verticalAlign=middle;arcSize=8;"
      vertex="1" parent="1">
      <mxGeometry x="1190" y="630" width="185" height="80" as="geometry" />
    </mxCell>

    <!-- train.csv -->
    <mxCell id="train_csv" value="&lt;b&gt;train.csv&lt;/b&gt;&lt;br/&gt;53,708 flows&lt;br/&gt;Solo label=0 (normal)&lt;br/&gt;&lt;i&gt;→ IF entrenamiento (F3)&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="920" y="735" width="180" height="70" as="geometry" />
    </mxCell>

    <!-- val.csv -->
    <mxCell id="val_csv" value="&lt;b&gt;val.csv&lt;/b&gt;&lt;br/&gt;~99,800 flows&lt;br/&gt;label=0 y label=1&lt;br/&gt;&lt;i&gt;→ ajuste de parámetros (F3)&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="1115" y="735" width="180" height="70" as="geometry" />
    </mxCell>

    <!-- test.csv -->
    <mxCell id="test_csv" value="&lt;b&gt;test.csv&lt;/b&gt;&lt;br/&gt;~99,700 flows&lt;br/&gt;Solo label=1 (anómalo)&lt;br/&gt;&lt;i&gt;→ evaluación AUC (F3)&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="1310" y="735" width="180" height="70" as="geometry" />
    </mxCell>

    <!-- normal_holdout.csv (extra output) -->
    <mxCell id="holdout_csv" value="&lt;b&gt;normal_holdout.csv&lt;/b&gt;&lt;br/&gt;13,427 flows (label=0)&lt;br/&gt;&lt;i&gt;→ medir FPR en F3&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="1115" y="780" width="180" height="65" as="geometry" />
    </mxCell>

    <!-- features.csv -->
    <mxCell id="features_csv" value="&lt;b&gt;models/features.csv&lt;/b&gt;&lt;br/&gt;14 nombres de columnas&lt;br/&gt;&lt;i&gt;→ validación en motor (F4)&lt;/i&gt;"
      style="shape=mxgraph.flowchart.document;whiteSpace=wrap;html=1;
             fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;fontStyle=1;"
      vertex="1" parent="1">
      <mxGeometry x="630" y="625" width="205" height="70" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         CONECTORES — ZONA CAPTURA
    ══════════════════════════════════════════════════════════ -->

    <!-- Desktop → Switch (normal) -->
    <mxCell id="e1" value="Grupos A/C&lt;br/&gt;(curl, scp, ssh)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.35;entryDx=0;entryDy=0;
             strokeColor=#82b366;fontColor=#3a6b3a;fontSize=10;fontStyle=1;"
      edge="1" source="desktop" target="switch" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Kali → Switch (anómalo) -->
    <mxCell id="e2" value="Grupo B&lt;br/&gt;(flood, scan, BF)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.65;entryDx=0;entryDy=0;
             strokeColor=#b85450;fontColor=#7a0000;fontSize=10;fontStyle=1;"
      edge="1" source="kali" target="switch" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Switch → Server -->
    <mxCell id="e3" value="tráfico al objetivo"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#555555;fontSize=10;"
      edge="1" source="switch" target="server" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Switch → Suricata (pasivo, dashed) -->
    <mxCell id="e4" value="copia pasiva (ens35)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.2;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;
             strokeColor=#0050ef;fontColor=#003399;fontSize=10;
             dashed=1;dashPattern=8 4;"
      edge="1" source="switch" target="suricata" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Suricata → eve.json -->
    <mxCell id="e5" value="escribe flows"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#0050ef;fontColor=#003399;fontSize=10;"
      edge="1" source="suricata" target="eve_json" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- eve.json → exportar.sh -->
    <mxCell id="e6" value="fin de escenario&lt;br/&gt;(vía SSH desde Desktop)"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#d79b00;fontColor=#7a5000;fontSize=10;"
      edge="1" source="eve_json" target="exportar_sh" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- exportar.sh → data/raw -->
    <mxCell id="e7" value=".gz generado"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#6c8ebf;fontSize=10;"
      edge="1" source="exportar_sh" target="data_raw" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- exportar.sh → registrar.sh (paralelo) -->
    <mxCell id="e8" value=""
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#d79b00;fontSize=10;"
      edge="1" source="exportar_sh" target="registrar_sh" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- registrar.sh → bitacora -->
    <mxCell id="e9" value="append"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#d6b656;fontSize=10;"
      edge="1" source="registrar_sh" target="bitacora" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         CONECTOR ENTRE ZONAS (data/raw → data/raw_ref)
    ══════════════════════════════════════════════════════════ -->
    <mxCell id="e_cross" value="datos comprimidos&lt;br/&gt;pasan al procesamiento"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#6c8ebf;fontColor=#003399;fontSize=10;fontStyle=1;
             endArrow=block;endFill=1;strokeWidth=2;"
      edge="1" source="data_raw" target="data_raw_ref" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         CONECTORES — ZONA PROCESAMIENTO
    ══════════════════════════════════════════════════════════ -->

    <!-- data_raw_ref → parser.py -->
    <mxCell id="e10" value="lee .gz"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#d79b00;fontColor=#7a5000;fontSize=10;"
      edge="1" source="data_raw_ref" target="parser_py" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- parser.py → dataset_raw.csv -->
    <mxCell id="e11" value="14 features&lt;br/&gt;por flow"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#6c8ebf;fontColor=#003399;fontSize=10;"
      edge="1" source="parser_py" target="raw_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- parser.py → features.csv (salida secundaria) -->
    <mxCell id="e_feat" value="genera lista&lt;br/&gt;de features"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#d6b656;fontColor=#7a5000;fontSize=10;dashed=1;"
      edge="1" source="parser_py" target="features_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- dataset_raw.csv → etiquetar.py -->
    <mxCell id="e12" value="label · dedup&lt;br/&gt;filtros IP"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#d79b00;fontColor=#7a5000;fontSize=10;"
      edge="1" source="raw_csv" target="etiquetar_py" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- etiquetar.py → dataset_clean.csv -->
    <mxCell id="e13" value="665K flows&lt;br/&gt;limpios"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#82b366;fontColor=#3a6b3a;fontSize=10;"
      edge="1" source="etiquetar_py" target="clean_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- dataset_clean.csv → particionar.py -->
    <mxCell id="e14" value="70/15/15&lt;br/&gt;cronológico"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#82b366;fontColor=#3a6b3a;fontSize=10;"
      edge="1" source="clean_csv" target="particionar_py" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- particionar.py → train.csv -->
    <mxCell id="e15" value="70%&lt;br/&gt;normal"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#82b366;fontColor=#3a6b3a;fontSize=10;"
      edge="1" source="particionar_py" target="train_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- particionar.py → val.csv -->
    <mxCell id="e16" value="15%&lt;br/&gt;mixto"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#6c8ebf;fontColor=#003399;fontSize=10;"
      edge="1" source="particionar_py" target="val_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- particionar.py → test.csv -->
    <mxCell id="e17" value="15%&lt;br/&gt;anómalo"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=1;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
             strokeColor=#b85450;fontColor=#7a0000;fontSize=10;"
      edge="1" source="particionar_py" target="test_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- train.csv → normal_holdout (nota) -->
    <mxCell id="e_holdout" value="20% reservado&lt;br/&gt;para FPR"
      style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
             exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
             strokeColor=#d6b656;fontColor=#7a5000;fontSize=10;dashed=1;"
      edge="1" source="train_csv" target="holdout_csv" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ══════════════════════════════════════════════════════════
         LEYENDA
    ══════════════════════════════════════════════════════════ -->
    <mxCell id="leg_bg" value=""
      style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f9f9f9;strokeColor=#cccccc;"
      vertex="1" parent="1">
      <mxGeometry x="55" y="830" width="1340" height="65" as="geometry" />
    </mxCell>
    <mxCell id="leg1" value="Tráfico normal (label=0)"
      style="rounded=1;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="70" y="845" width="185" height="38" as="geometry" />
    </mxCell>
    <mxCell id="leg2" value="Tráfico anómalo (label=1)"
      style="rounded=1;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="265" y="845" width="185" height="38" as="geometry" />
    </mxCell>
    <mxCell id="leg3" value="Scripts bash de automatización"
      style="rounded=1;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="460" y="845" width="210" height="38" as="geometry" />
    </mxCell>
    <mxCell id="leg4" value="Archivos de datos generados"
      style="rounded=1;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="680" y="845" width="210" height="38" as="geometry" />
    </mxCell>
    <mxCell id="leg5" value="Dataset final (salida de F2 → entrada F3)"
      style="rounded=1;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=10;"
      vertex="1" parent="1">
      <mxGeometry x="900" y="845" width="255" height="38" as="geometry" />
    </mxCell>
    <mxCell id="leg6" value="- - -  Salida secundaria / referencia"
      style="text;html=1;strokeColor=#d6b656;fillColor=#fff2cc;
             align=center;fontSize=10;fontColor=#7a5000;rounded=1;"
      vertex="1" parent="1">
      <mxGeometry x="1165" y="845" width="215" height="38" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```
