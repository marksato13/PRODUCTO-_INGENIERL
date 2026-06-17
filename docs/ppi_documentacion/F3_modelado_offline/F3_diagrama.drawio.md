# F3 — Diagrama: Modelado Offline

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Título -->
    <mxCell id="2" value="F3 — Modelado Offline: Isolation Forest (no supervisado)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=20;fontStyle=1;fontColor=#003366;" vertex="1" parent="1">
      <mxGeometry x="60" y="20" width="1520" height="45" as="geometry" />
    </mxCell>

    <!-- ===== GRUPO A ===== -->
    <mxCell id="3" value="&lt;b&gt;GRUPO A — Normal Puro&lt;/b&gt;&lt;br&gt;data/raw/*_normal_*.gz&lt;br&gt;&lt;br&gt;28 archivos&lt;br&gt;(Kali APAGADA)&lt;br&gt;67,135 flows totales" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="60" y="80" width="195" height="130" as="geometry" />
    </mxCell>

    <!-- ===== FASE3_ENTRENAR.PY ===== -->
    <mxCell id="4" value="&lt;b&gt;fase3_entrenar.py&lt;/b&gt;&lt;br&gt;&lt;br&gt;1. Lee *_normal_*.gz (glob date-agnostic)&lt;br&gt;2. Filtra src_ip en {Desktop .20, Servidor .120}&lt;br&gt;3. Split 80/20 aleatorio (random_state=42, shuffle=True)&lt;br&gt;4. StandardScaler.fit_transform(80% de flows)&lt;br&gt;5. IsolationForest(n_estimators=300, contamination=0.05).fit()" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="315" y="70" width="435" height="160" as="geometry" />
    </mxCell>

    <!-- Conector: Grupo A → entrenar -->
    <mxCell id="5" value="67,135 flows" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#82b366;strokeWidth=2;fontSize=10;fontColor=#82b366;" edge="1" source="3" target="4" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== ANOTACIÓN SPLIT ===== -->
    <mxCell id="6" value="80% → 53,708 flows (entrenamiento)&lt;br&gt;20% → 13,427 flows (holdout — nunca visto por IF)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=10;fontColor=#333333;" vertex="1" parent="1">
      <mxGeometry x="315" y="248" width="320" height="45" as="geometry" />
    </mxCell>
    <mxCell id="7" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.3;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;dashed=1;strokeColor=#999999;" edge="1" source="4" target="6" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== ARTEFACTOS DE ENTRENAR ===== -->
    <!-- isolation_forest.pkl -->
    <mxCell id="8" value="isolation_forest.pkl&lt;br&gt;~2.5 MB&lt;br&gt;sklearn 1.9.0" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="315" y="320" width="135" height="80" as="geometry" />
    </mxCell>
    <!-- scaler.pkl -->
    <mxCell id="9" value="scaler.pkl&lt;br&gt;StandardScaler&lt;br&gt;fit solo en 80%" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="460" y="320" width="135" height="80" as="geometry" />
    </mxCell>
    <!-- features.csv -->
    <mxCell id="10" value="features.csv&lt;br&gt;14 columnas&lt;br&gt;(orden exacto)" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="605" y="320" width="135" height="80" as="geometry" />
    </mxCell>
    <!-- normal_holdout.csv -->
    <mxCell id="11" value="normal_holdout.csv&lt;br&gt;13,427 flows&lt;br&gt;&lt;i&gt;nunca visto por IF&lt;/i&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;fontStyle=2;" vertex="1" parent="1">
      <mxGeometry x="755" y="320" width="150" height="80" as="geometry" />
    </mxCell>

    <!-- Conector: entrenar → pkl -->
    <mxCell id="12" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.18;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="4" target="8" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: entrenar → scaler -->
    <mxCell id="13" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.38;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="4" target="9" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: entrenar → features -->
    <mxCell id="14" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.6;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" source="4" target="10" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: entrenar → holdout -->
    <mxCell id="15" value="20%" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.82;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontColor=#8B6914;" edge="1" source="4" target="11" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== GRUPO B ===== -->
    <mxCell id="16" value="&lt;b&gt;GRUPO B — Ataque Puro&lt;/b&gt;&lt;br&gt;data/raw/*_anom_*.gz&lt;br&gt;&lt;br&gt;13 archivos&lt;br&gt;(Desktop QUIETO)&lt;br&gt;598,285 flows totales" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="60" y="360" width="195" height="130" as="geometry" />
    </mxCell>

    <!-- ===== FASE3_EVALUAR.PY ===== -->
    <mxCell id="17" value="&lt;b&gt;fase3_evaluar.py&lt;/b&gt;&lt;br&gt;&lt;br&gt;1. Carga isolation_forest.pkl + scaler.pkl&lt;br&gt;2. Score sobre normal_holdout.csv → scores normales&lt;br&gt;3. Score sobre *_anom_*.gz → scores anómalos&lt;br&gt;4. Construye curva ROC (label binario, score continuo)&lt;br&gt;5. AUC = área bajo la curva&lt;br&gt;6. τ1 = argmax(TPR − FPR)  [Youden index]&lt;br&gt;7. τ2 = max TPR donde FPR ≤ 2%&lt;br&gt;8. Escribe metricas_offline.txt" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="990" y="290" width="430" height="210" as="geometry" />
    </mxCell>

    <!-- Conector: holdout → evaluar -->
    <mxCell id="18" value="referencia normal" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.2;entryDx=0;entryDy=0;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontColor=#8B6914;" edge="1" source="11" target="17" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: Grupo B → evaluar -->
    <mxCell id="19" value="ataques para ROC" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.55;entryDx=0;entryDy=0;strokeColor=#b85450;strokeWidth=2;fontSize=10;fontColor=#b85450;" edge="1" source="16" target="17" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: pkl → evaluar -->
    <mxCell id="20" value="modelo" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.85;entryDx=0;entryDy=0;strokeColor=#d6b656;fontSize=10;fontColor=#8B6914;" edge="1" source="8" target="17" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== SALIDAS DE EVALUAR ===== -->
    <!-- metricas_offline.txt — FUENTE ÚNICA -->
    <mxCell id="21" value="&lt;b&gt;metricas_offline.txt&lt;/b&gt;&lt;br&gt;★ FUENTE ÚNICA DE VERDAD ★&lt;br&gt;&lt;br&gt;AUC-ROC: 0.8998&lt;br&gt;τ1: −0.4459  (Youden — PERMIT/LIMIT)&lt;br&gt;τ2: −0.6027  (FPR≤2% — LIMIT/BLOCK)&lt;br&gt;Precision: 99.54% | Recall: 99.40% | F1: 0.9947" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF8000;strokeColor=#CC5500;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="990" y="555" width="290" height="140" as="geometry" />
    </mxCell>
    <!-- auc_roc.png -->
    <mxCell id="22" value="auc_roc.png&lt;br&gt;Curva ROC con&lt;br&gt;τ1 y τ2 marcados" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="1320" y="555" width="150" height="80" as="geometry" />
    </mxCell>

    <!-- Conector: evaluar → metricas -->
    <mxCell id="23" value="escribe" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.3;exitY=1;exitDx=0;exitDy=0;entryX=0.3;entryY=0;entryDx=0;entryDy=0;strokeWidth=2;strokeColor=#CC5500;" edge="1" source="17" target="21" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: evaluar → auc_roc.png -->
    <mxCell id="24" value="genera" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.85;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontSize=10;" edge="1" source="17" target="22" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== FLECHA A F4 ===== -->
    <mxCell id="25" value="→ F4: motor_decision.py&lt;br&gt;lee τ1/τ2 al arrancar" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#003366;strokeColor=#001a33;fontSize=11;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="990" y="745" width="220" height="55" as="geometry" />
    </mxCell>
    <mxCell id="26" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;strokeWidth=2;strokeColor=#FF8000;" edge="1" source="21" target="25" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== GRUPO C ===== -->
    <mxCell id="27" value="&lt;b&gt;GRUPO C — Mixto&lt;/b&gt;&lt;br&gt;data/raw/*_mixto_*.gz&lt;br&gt;&lt;br&gt;6 archivos&lt;br&gt;(motor DETENIDO)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="60" y="560" width="195" height="110" as="geometry" />
    </mxCell>

    <!-- ===== AUC_POR_ESCENARIO.PY ===== -->
    <mxCell id="28" value="&lt;b&gt;auc_por_escenario.py&lt;/b&gt;&lt;br&gt;&lt;br&gt;AUC individual por escenario&lt;br&gt;B1-B6 y C1-C3&lt;br&gt;(no modifica metricas_offline.txt)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;verticalAlign=middle;" vertex="1" parent="1">
      <mxGeometry x="315" y="558" width="290" height="115" as="geometry" />
    </mxCell>

    <!-- Conector: Grupo B → auc_por_escenario -->
    <mxCell id="29" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;strokeColor=#b85450;" edge="1" source="16" target="28" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: Grupo C → auc_por_escenario -->
    <mxCell id="30" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.7;entryDx=0;entryDy=0;strokeColor=#9673a6;" edge="1" source="27" target="28" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <!-- Conector: pkl → auc_por_escenario -->
    <mxCell id="31" value="modelo" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;strokeColor=#d6b656;fontSize=10;fontColor=#8B6914;" edge="1" source="8" target="28" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- auc_por_escenario.txt -->
    <mxCell id="32" value="auc_por_escenario.txt&lt;br&gt;&lt;br&gt;B1 SYN Flood: 0.8342&lt;br&gt;B2 Port Scan: 0.9722&lt;br&gt;B3 UDP Flood: 0.9537&lt;br&gt;B4 ICMP Flood: 0.8961&lt;br&gt;B5 HTTP Abuse: 0.9670&lt;br&gt;B6 BruteForce: 0.8658&lt;br&gt;C1-C3 mixto..." style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="640" y="555" width="185" height="175" as="geometry" />
    </mxCell>

    <!-- Conector: auc_por_escenario → txt -->
    <mxCell id="33" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;" edge="1" source="28" target="32" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ===== NOTA METODOLÓGICA ===== -->
    <mxCell id="34" value="Nota: F3 lee los .gz directamente con gzip.open()&lt;br&gt;NO existen CSVs intermedios (dataset_raw, train, val, test)&lt;br&gt;Ver: docs/METODOLOGIA_PIPELINE_COMPARATIVA.md" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6790a;fontSize=10;fontStyle=2;align=left;spacingLeft=8;" vertex="1" parent="1">
      <mxGeometry x="315" y="440" width="620" height="60" as="geometry" />
    </mxCell>

    <!-- ===== LEYENDA ===== -->
    <mxCell id="35" value="Leyenda" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontStyle=1;" vertex="1" parent="1">
      <mxGeometry x="60" y="800" width="80" height="25" as="geometry" />
    </mxCell>
    <mxCell id="36" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="60" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="37" value="Grupo A (normal puro)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="83" y="830" width="140" height="18" as="geometry" />
    </mxCell>
    <mxCell id="38" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="240" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="39" value="Grupo B (ataques puros)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="263" y="830" width="145" height="18" as="geometry" />
    </mxCell>
    <mxCell id="40" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" vertex="1" parent="1">
      <mxGeometry x="420" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="41" value="Grupo C (mixto controlado)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="443" y="830" width="155" height="18" as="geometry" />
    </mxCell>
    <mxCell id="42" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="610" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="43" value="Scripts Python" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="633" y="830" width="110" height="18" as="geometry" />
    </mxCell>
    <mxCell id="44" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="755" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="45" value="Artefactos (pkl / csv / png)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="778" y="830" width="165" height="18" as="geometry" />
    </mxCell>
    <mxCell id="46" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FF8000;strokeColor=#CC5500;" vertex="1" parent="1">
      <mxGeometry x="955" y="830" width="18" height="18" as="geometry" />
    </mxCell>
    <mxCell id="47" value="Fuente única de verdad (metricas_offline.txt)" style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="978" y="830" width="270" height="18" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```
