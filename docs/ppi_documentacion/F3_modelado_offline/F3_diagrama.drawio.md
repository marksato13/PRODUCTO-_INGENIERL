# F3 — Diagrama: Modelado Offline con Isolation Forest

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="800" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="100" value="F3 — Modelado Offline · Isolation Forest · PPI UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="300" y="20" width="700" height="40" as="geometry"/></mxCell>
    <!-- Entrada -->
    <mxCell id="2" value="train.csv&#xa;53,708 flows normales&#xa;data/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="60" y="300" width="140" height="80" as="geometry"/></mxCell>
    <!-- Preprocesamiento -->
    <mxCell id="3" value="&lt;b&gt;Extracción de 14 Features&lt;/b&gt;&#xa;pkts_toserver, pkts_toclient&#xa;bytes_toserver, bytes_toclient&#xa;duration, pkt_rate, byte_rate&#xa;pkt_ratio, byte_ratio, avg_pkt_size&#xa;is_tcp, is_udp, is_icmp, dest_port" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="270" y="260" width="200" height="140" as="geometry"/></mxCell>
    <!-- StandardScaler -->
    <mxCell id="4" value="StandardScaler&#xa;fit_transform(train)&#xa;→ scaler.pkl" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1"><mxGeometry x="550" y="300" width="150" height="70" as="geometry"/></mxCell>
    <!-- IsolationForest -->
    <mxCell id="5" value="&lt;b&gt;IsolationForest&lt;/b&gt;&#xa;n_estimators = 300&#xa;contamination = 0.05&#xa;random_state = 42&#xa;fit(X_train_scaled)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="780" y="260" width="170" height="110" as="geometry"/></mxCell>
    <!-- Modelos guardados -->
    <mxCell id="6" value="isolation_forest.pkl&#xa;scaler.pkl&#xa;features.csv (14)&#xa;models/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;fontSize=10;" vertex="1" parent="1"><mxGeometry x="1030" y="280" width="140" height="90" as="geometry"/></mxCell>
    <!-- Evaluacion -->
    <mxCell id="7" value="fase3_evaluar.py&#xa;score_samples(X_test)&#xa;→ scores negativos" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="550" y="460" width="150" height="70" as="geometry"/></mxCell>
    <!-- Curva ROC -->
    <mxCell id="8" value="auc_roc_umbrales.py&#xa;Curva ROC&#xa;AUC = 0.8955" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="780" y="460" width="150" height="70" as="geometry"/></mxCell>
    <!-- Umbrales -->
    <mxCell id="9" value="&lt;b&gt;Umbrales τ1 / τ2&lt;/b&gt;&#xa;τ1 = −0.4650 (Youden)&#xa;τ2 = −0.6118 (FPR≤2%)&#xa;→ metricas_offline.txt" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=10;" vertex="1" parent="1"><mxGeometry x="1020" y="450" width="170" height="90" as="geometry"/></mxCell>
    <!-- Script principal -->
    <mxCell id="10" value="fase3_isolation_forest.py" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=3;" vertex="1" parent="1"><mxGeometry x="550" y="180" width="200" height="40" as="geometry"/></mxCell>
    <!-- Flechas -->
    <mxCell id="20" edge="1" source="2" target="3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="21" edge="1" source="3" target="4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="22" edge="1" source="4" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="23" edge="1" source="5" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="24" edge="1" source="4" target="7" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="25" edge="1" source="7" target="8" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="26" edge="1" source="8" target="9" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
