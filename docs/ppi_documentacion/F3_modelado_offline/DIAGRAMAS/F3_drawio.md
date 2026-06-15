# F3 — Diagrama Draw.io: Modelado Offline · Isolation Forest

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama — 684 flows → Features → Scaler → IF → τ1/τ2 → Artefactos → F4

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F3_modelado" name="F3 — Isolation Forest Training">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="title" value="F3 — Modelado Offline: Isolation Forest · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="350" y="15" width="900" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 1. INPUT: DATOS DE ENTRENAMIENTO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="input_bg" value="&lt;b&gt;1. Datos de Entrenamiento&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="60" width="260" height="340" as="geometry" />
        </mxCell>

        <mxCell id="raw_filter" value="&lt;b&gt;Filtro doble&lt;/b&gt;&lt;br&gt;① Solo corridas _01_ y _02_&lt;br&gt;② src_ip ∈ {192.168.0.20,&lt;br&gt;          192.168.0.120}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="38" width="240" height="65" as="geometry" />
        </mxCell>

        <mxCell id="flow_http" value="normal_http_01/02 → 345 flows" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="118" width="240" height="28" as="geometry" />
        </mxCell>
        <mxCell id="flow_sos" value="normal_sostenido_01/02 → 252 flows" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="155" width="240" height="28" as="geometry" />
        </mxCell>
        <mxCell id="flow_ssh" value="normal_ssh_01/02 → 58 flows (8.5%)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="192" width="240" height="28" as="geometry" />
        </mxCell>
        <mxCell id="flow_tfr" value="normal_transferencia_01/02 → 29 flows" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="229" width="240" height="28" as="geometry" />
        </mxCell>

        <mxCell id="total_flows" value="&lt;b&gt;TOTAL: 684 flows normales puros&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1565c0;strokeColor=#0d47a1;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="input_bg">
          <mxGeometry x="10" y="276" width="240" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 2. FEATURE ENGINEERING -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="fe_bg" value="&lt;b&gt;2. Feature Engineering — extract_features()&lt;/b&gt;&lt;br&gt;14 features por flow" style="swimlane;startSize=45;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="330" y="60" width="310" height="340" as="geometry" />
        </mxCell>

        <mxCell id="feat_vol" value="&lt;b&gt;Volumétricas (4)&lt;/b&gt;&lt;br&gt;pkts_toserver · pkts_toclient&lt;br&gt;bytes_toserver · bytes_toclient" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="fe_bg">
          <mxGeometry x="10" y="55" width="288" height="50" as="geometry" />
        </mxCell>
        <mxCell id="feat_tmp" value="&lt;b&gt;Temporal (1)&lt;/b&gt;&lt;br&gt;duration = end − start  (mín. 0.001s)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="fe_bg">
          <mxGeometry x="10" y="115" width="288" height="40" as="geometry" />
        </mxCell>
        <mxCell id="feat_der" value="&lt;b&gt;Derivadas (5)&lt;/b&gt;&lt;br&gt;pkt_rate = (pts+ptc)/dur&lt;br&gt;byte_rate = (bts+btc)/dur&lt;br&gt;pkt_ratio = pts/(ptc+1)&lt;br&gt;byte_ratio = bts/(btc+1)&lt;br&gt;avg_pkt_size = (bts+btc)/(pts+ptc+1)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="fe_bg">
          <mxGeometry x="10" y="165" width="288" height="80" as="geometry" />
        </mxCell>
        <mxCell id="feat_bin" value="&lt;b&gt;Binarias (3)&lt;/b&gt;  is_tcp · is_udp · is_icmp" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="fe_bg">
          <mxGeometry x="10" y="255" width="288" height="30" as="geometry" />
        </mxCell>
        <mxCell id="feat_dst" value="&lt;b&gt;Discreta (1)&lt;/b&gt;  dest_port" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="fe_bg">
          <mxGeometry x="10" y="295" width="288" height="28" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 3. STANDARD SCALER -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="scaler_bg" value="&lt;b&gt;3. StandardScaler&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fff3e0;strokeColor=#e65100;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="685" y="60" width="250" height="200" as="geometry" />
        </mxCell>
        <mxCell id="scaler_fit" value="&lt;b&gt;scaler.fit(X_normal_684)&lt;/b&gt;&lt;br&gt;Calcula μ y σ SOLO de flows normales&lt;br&gt;mean_  = media de cada feature&lt;br&gt;scale_ = desviación estándar" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="scaler_bg">
          <mxGeometry x="10" y="38" width="230" height="65" as="geometry" />
        </mxCell>
        <mxCell id="scaler_transform" value="X_scaled = (X − μ) / σ&lt;br&gt;Anómalos → z-scores extremos" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe0b2;strokeColor=#e65100;fontSize=10;" vertex="1" parent="scaler_bg">
          <mxGeometry x="10" y="113" width="230" height="40" as="geometry" />
        </mxCell>
        <mxCell id="scaler_pkl" value="&lt;b&gt;scaler.pkl  1.4 KB&lt;/b&gt;" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;fontStyle=1;" vertex="1" parent="scaler_bg">
          <mxGeometry x="60" y="158" width="130" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 4. ISOLATION FOREST -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="if_bg" value="&lt;b&gt;4. Isolation Forest&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="685" y="290" width="250" height="260" as="geometry" />
        </mxCell>
        <mxCell id="if_params" value="&lt;b&gt;Hiperparámetros&lt;/b&gt;&lt;br&gt;n_estimators  = 300&lt;br&gt;contamination = 0.05&lt;br&gt;max_samples   = 'auto' (256)&lt;br&gt;random_state  = 42&lt;br&gt;n_jobs        = −1 (4 cores)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="if_bg">
          <mxGeometry x="10" y="38" width="230" height="90" as="geometry" />
        </mxCell>
        <mxCell id="if_algo" value="300 árboles aleatorios&lt;br&gt;Submuestra 256 flows/árbol&lt;br&gt;Score: más negativo = más anómalo&lt;br&gt;score ∈ (−1, 0)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1bee7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="if_bg">
          <mxGeometry x="10" y="138" width="230" height="60" as="geometry" />
        </mxCell>
        <mxCell id="if_pkl" value="&lt;b&gt;isolation_forest.pkl  2.5 MB&lt;/b&gt;&lt;br&gt;Born: 2026-06-02 · Mod: 2026-06-04" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#9673a6;strokeColor=#6a1b9a;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="if_bg">
          <mxGeometry x="30" y="205" width="190" height="45" as="geometry" />
        </mxCell>

        <!-- features.csv -->
        <mxCell id="feat_csv" value="&lt;b&gt;features.csv  152B&lt;/b&gt;&lt;br&gt;14 features en orden" style="shape=note;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="685" y="570" width="170" height="50" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 5. EVALUACIÓN: ROC + UMBRALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="eval_bg" value="&lt;b&gt;5. Evaluación — auc_roc_umbrales.py&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fce4ec;strokeColor=#c62828;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="990" y="60" width="310" height="340" as="geometry" />
        </mxCell>
        <mxCell id="eval_set" value="&lt;b&gt;Eval set balanceado 50/50&lt;/b&gt;&lt;br&gt;11,669 normales + 11,669 anómalos&lt;br&gt;= 23,338 flows de test.csv" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="eval_bg">
          <mxGeometry x="10" y="38" width="290" height="50" as="geometry" />
        </mxCell>
        <mxCell id="scores_dist" value="Distribución de scores:&lt;br&gt;Normal:   μ = −0.4262  σ = 0.0646&lt;br&gt;Anómalo:  μ = −0.6548  σ = 0.0808&lt;br&gt;Separación Δ = &lt;b&gt;0.229&lt;/b&gt; unidades" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="eval_bg">
          <mxGeometry x="10" y="98" width="290" height="60" as="geometry" />
        </mxCell>
        <mxCell id="auc_val" value="Curva ROC · &lt;b&gt;AUC = 0.9440&lt;/b&gt;&lt;br&gt;auc_roc_umbrales.png" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#b71c1c;strokeColor=#7f0000;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="eval_bg">
          <mxGeometry x="60" y="168" width="190" height="40" as="geometry" />
        </mxCell>
        <mxCell id="tau1_box" value="&lt;b&gt;τ1 = −0.4973&lt;/b&gt;&lt;br&gt;Youden: max(TPR−FPR)&lt;br&gt;TPR = 91.0%  FPR = 9.5%&lt;br&gt;→ PERMIT / LIMIT" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;fontStyle=1;" vertex="1" parent="eval_bg">
          <mxGeometry x="10" y="220" width="140" height="70" as="geometry" />
        </mxCell>
        <mxCell id="tau2_box" value="&lt;b&gt;τ2 = −0.6873&lt;/b&gt;&lt;br&gt;FPR ≤ 2% · max TPR&lt;br&gt;TPR = 40.6%  FPR = 1.8%&lt;br&gt;→ LIMIT / BLOCK" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#c62828;fontSize=10;fontStyle=1;" vertex="1" parent="eval_bg">
          <mxGeometry x="160" y="220" width="140" height="70" as="geometry" />
        </mxCell>
        <mxCell id="decision_zones" value="score &gt; −0.4973 → &lt;b&gt;PERMIT&lt;/b&gt;&lt;br&gt;−0.6873 &lt; score ≤ −0.4973 → &lt;b&gt;LIMIT&lt;/b&gt;&lt;br&gt;score ≤ −0.6873 → &lt;b&gt;BLOCK&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f57f17;fontSize=10;fontStyle=1;" vertex="1" parent="eval_bg">
          <mxGeometry x="10" y="300" width="290" height="28" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- 6. ARTEFACTOS FINALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="artifacts_bg" value="&lt;b&gt;6. Artefactos de Producción&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#e0f2f1;strokeColor=#00796b;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1360" y="60" width="250" height="340" as="geometry" />
        </mxCell>
        <mxCell id="art_if" value="&lt;b&gt;isolation_forest.pkl&lt;/b&gt;&lt;br&gt;2.5 MB · Mod: 2026-06-04 14:41" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#9673a6;strokeColor=#6a1b9a;fontColor=#ffffff;fontSize=10;" vertex="1" parent="artifacts_bg">
          <mxGeometry x="20" y="38" width="210" height="50" as="geometry" />
        </mxCell>
        <mxCell id="art_scaler" value="&lt;b&gt;scaler.pkl&lt;/b&gt;  1.4 KB" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="artifacts_bg">
          <mxGeometry x="20" y="100" width="210" height="40" as="geometry" />
        </mxCell>
        <mxCell id="art_feat" value="&lt;b&gt;features.csv&lt;/b&gt;  152 B" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="artifacts_bg">
          <mxGeometry x="20" y="152" width="210" height="35" as="geometry" />
        </mxCell>
        <mxCell id="art_umbrales" value="&lt;b&gt;umbrales_finales.txt&lt;/b&gt;  1.9 KB&lt;br&gt;τ1=−0.4973 · τ2=−0.6873&lt;br&gt;BF SSH: 5/15 por 60s&lt;br&gt;HTTP: 50/100 por 30s" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f57f17;fontSize=10;" vertex="1" parent="artifacts_bg">
          <mxGeometry x="20" y="198" width="210" height="70" as="geometry" />
        </mxCell>
        <mxCell id="art_metrics" value="&lt;b&gt;reporte_metricas_v1.txt&lt;/b&gt;&lt;br&gt;Recall=87.6% · Prec=99.96%&lt;br&gt;F1=0.9338 · AUC=0.9440" style="shape=note;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="artifacts_bg">
          <mxGeometry x="20" y="280" width="210" height="50" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- AUC POR ESCENARIO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="auc_bg" value="&lt;b&gt;AUC por Escenario — auc_por_escenario.py&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fafafa;strokeColor=#757575;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="440" width="620" height="190" as="geometry" />
        </mxCell>
        <mxCell id="auc_excel" value="✅ Excelente (AUC &gt; 0.97)&lt;br&gt;B3 UDP Flood  0.9905  Det=100%&lt;br&gt;B4 ICMP Flood 0.9861  Det=100%&lt;br&gt;C3 Mixto UDP  0.9801  Det=99.3%&lt;br&gt;C1 Mixto HTTP 0.9737  Det=100%&lt;br&gt;B2 Port Scan  0.9721  Det=99.9%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="auc_bg">
          <mxGeometry x="10" y="38" width="190" height="140" as="geometry" />
        </mxCell>
        <mxCell id="auc_good" value="⚡ Muy bueno (AUC 0.92–0.97)&lt;br&gt;B1 SYN Flood  0.9529  Det=72.2%&lt;br&gt;C2 Mixto SSH  0.9277  Det=57.1%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="auc_bg">
          <mxGeometry x="215" y="38" width="185" height="75" as="geometry" />
        </mxCell>
        <mxCell id="auc_comp" value="⚠️ Complementado en F4&lt;br&gt;B5 HTTP Abuse  0.8630  Det=56.6%&lt;br&gt;  → detector HTTP 50/100 req/30s&lt;br&gt;B6 BruteForce  0.6770  Det=0.9%&lt;br&gt;  → detector SSH 5/15 int/60s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;align=left;spacingLeft=8;" vertex="1" parent="auc_bg">
          <mxGeometry x="415" y="38" width="195" height="110" as="geometry" />
        </mxCell>
        <mxCell id="auc_recall" value="Recall IF solo: 80.4%   →   Con detectores F4: ~92–95%" style="text;html=1;fontSize=11;fontStyle=1;align=center;fontColor=#c62828;" vertex="1" parent="auc_bg">
          <mxGeometry x="10" y="158" width="600" height="22" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- RECALIBRACIÓN v1 → v2 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="recal_bg" value="&lt;b&gt;Recalibración del Modelo: v1 → v2&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fffde7;strokeColor=#f9a825;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="660" width="890" height="130" as="geometry" />
        </mxCell>
        <mxCell id="v1_box" value="&lt;b&gt;Versión 1&lt;/b&gt;&lt;br&gt;2026-06-02 01:42&lt;br&gt;(Born: isolation_forest.pkl)&lt;br&gt;Umbral: clf.offset_ = −0.5481&lt;br&gt;Lógica: BINARIA&lt;br&gt;(PERMIT / BLOCK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="recal_bg">
          <mxGeometry x="10" y="38" width="190" height="80" as="geometry" />
        </mxCell>
        <mxCell id="recal_why" value="Análisis de sesgo SSH:&lt;br&gt;• Corridas 03-10 → 65% SSH&lt;br&gt;• Modelo aprende SSH = normal&lt;br&gt;• det(B6) cae a 0%&lt;br&gt;&lt;br&gt;Sensibilidad N vs AUC:&lt;br&gt;• AUC estable desde N=200&lt;br&gt;• N=684 punto óptimo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="recal_bg">
          <mxGeometry x="220" y="38" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="recal_arrow" value="aplica filtro&lt;br&gt;doble + ROC" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=3;fontSize=9;fontStyle=1;" edge="1" parent="recal_bg">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="430" y="78" as="sourcePoint" />
            <mxPoint x="490" y="78" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="v2_box" value="&lt;b&gt;Versión 2 ← EN PRODUCCIÓN&lt;/b&gt;&lt;br&gt;2026-06-04 14:41&lt;br&gt;(Modify: isolation_forest.pkl)&lt;br&gt;τ1 = −0.4973 · τ2 = −0.6873&lt;br&gt;Lógica: TRIPLE&lt;br&gt;(PERMIT / LIMIT / BLOCK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;fontStyle=1;" vertex="1" parent="recal_bg">
          <mxGeometry x="500" y="38" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="recal_gain" value="✅ Grado: NORMAL / BAJA / ALTA / CRÍTICA&lt;br&gt;✅ Detectores SSH + HTTP complementan IF&lt;br&gt;✅ Recall combinado: ~92–95%" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="recal_bg">
          <mxGeometry x="715" y="38" width="165" height="80" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- CONECTOR → F4 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="f4_conn" value="&lt;b&gt;→ F4: Motor de Decisión&lt;/b&gt;&lt;br&gt;joblib.load(isolation_forest.pkl)&lt;br&gt;joblib.load(scaler.pkl)&lt;br&gt;TAU1 = −0.4973  (hardcoded)&lt;br&gt;TAU2 = −0.6873  (hardcoded)&lt;br&gt;features.csv → orden columnas" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=3;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1360" y="430" width="250" height="140" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLECHAS PRINCIPALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="input_to_fe" value="684 flows" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="input_bg" target="fe_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="fe_to_scaler" value="vector [1×14]" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="fe_bg" target="scaler_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="scaler_to_if" value="X_scaled" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="scaler_bg" target="if_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="if_to_eval" value="score_samples()" style="endArrow=block;endFill=1;html=1;strokeColor=#c62828;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="if_bg" target="eval_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="eval_to_arts" value="τ1 · τ2 · AUC" style="endArrow=block;endFill=1;html=1;strokeColor=#00796b;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="eval_bg" target="artifacts_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="if_to_arts" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#9673a6;strokeWidth=2;" edge="1" source="if_bg" target="art_if" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="scaler_to_arts" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#e65100;strokeWidth=2;" edge="1" source="scaler_bg" target="art_scaler" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="arts_to_f4" value="carga al&lt;br&gt;iniciar motor" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" source="artifacts_bg" target="f4_conn" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="feat_csv_to_arts" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#666666;strokeWidth:1;dashed=1;" edge="1" source="feat_csv" target="art_feat" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
