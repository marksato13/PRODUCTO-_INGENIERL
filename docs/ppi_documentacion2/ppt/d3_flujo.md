# Diagrama 3 — Flujo de Decisión del Motor
**Slide 10 del PPT**

---

## draw.io XML

> Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxfile host="app.diagrams.net" modified="2026-06-22" version="21.0.0">
  <diagram id="d3-flujo" name="Flujo de Decisión">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="1600" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- START -->
        <mxCell id="start" value="&lt;b&gt;Nuevo evento eve.json&lt;/b&gt;&lt;br&gt;flujo TCP / UDP / ICMP detectado por Suricata" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="300" y="30" width="400" height="60" as="geometry"/>
        </mxCell>

        <!-- D1 Whitelist -->
        <mxCell id="d_wl" value="¿IP origen&lt;br&gt;en whitelist?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="325" y="140" width="350" height="100" as="geometry"/>
        </mxCell>

        <!-- PERMIT whitelist -->
        <mxCell id="permit_wl" value="✅  PERMIT&lt;br&gt;log DEBUG&lt;br&gt;sin acción" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="750" y="155" width="170" height="70" as="geometry"/>
        </mxCell>

        <!-- Extract features -->
        <mxCell id="feat" value="Extraer 14 features&lt;br&gt;pkts_to{server,client} · bytes_to{server,client}&lt;br&gt;duration · pkt_rate · byte_rate · pkt_ratio&lt;br&gt;byte_ratio · avg_pkt_size · is_{tcp,udp,icmp} · dest_port" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="250" y="295" width="500" height="80" as="geometry"/>
        </mxCell>

        <!-- StandardScaler -->
        <mxCell id="scaler" value="StandardScaler.transform()&lt;br&gt;(ajustado sobre 80% flujos normales de entrenamiento)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="280" y="425" width="440" height="60" as="geometry"/>
        </mxCell>

        <!-- IF -->
        <mxCell id="iforest" value="&lt;b&gt;IsolationForest.score_samples()&lt;/b&gt;&lt;br&gt;n=300 árboles  ·  score ∈ [−1, 0]&lt;br&gt;Latencia P95 = 34.8ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#647687;strokeColor=#314354;fontColor=#ffffff;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="280" y="535" width="440" height="80" as="geometry"/>
        </mxCell>

        <!-- Decision band visual -->
        <mxCell id="band_block" value="BLOCK" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontColor=#b85450;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="665" width="200" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="band_limit" value="LIMIT" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#b46504;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="300" y="665" width="200" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="band_permit" value="PERMIT" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="500" y="665" width="200" height="40" as="geometry"/>
        </mxCell>
        <mxCell id="band_tau2" value="τ2 = −0.6027" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rotatable=0;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="280" y="645" width="120" height="20" as="geometry"/>
        </mxCell>
        <mxCell id="band_tau1" value="τ1 = −0.4459" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rotatable=0;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="480" y="645" width="120" height="20" as="geometry"/>
        </mxCell>

        <!-- D2 tau1 -->
        <mxCell id="d_t1" value="score &gt; τ1&lt;br&gt;(−0.4459)?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="325" y="755" width="350" height="90" as="geometry"/>
        </mxCell>

        <!-- PERMIT score -->
        <mxCell id="permit_sc" value="✅  PERMIT&lt;br&gt;log DEBUG&lt;br&gt;sin acción" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="750" y="770" width="170" height="65" as="geometry"/>
        </mxCell>

        <!-- D3 tau2 -->
        <mxCell id="d_t2" value="score &gt; τ2&lt;br&gt;(−0.6027)?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#b46504;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="325" y="905" width="350" height="90" as="geometry"/>
        </mxCell>

        <!-- LIMIT -->
        <mxCell id="limit_sc" value="⚠️  LIMIT&lt;br&gt;hashlimit 100 pkt/s&lt;br&gt;ipset ppi_limited" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#b46504;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="750" y="920" width="180" height="70" as="geometry"/>
        </mxCell>

        <!-- BLOCK -->
        <mxCell id="block_sc" value="🚫  BLOCK&lt;br&gt;ipset DROP (kernel)&lt;br&gt;ipset ppi_blocked" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontColor=#b85450;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="325" y="1055" width="350" height="70" as="geometry"/>
        </mxCell>

        <!-- Heuristicos -->
        <mxCell id="heur" value="&lt;b&gt;Detectores heurísticos (paralelo al IF):&lt;/b&gt;&lt;br&gt;BF-SSH:   ≥ 5 intentos/60s → LIMIT&lt;br&gt;              ≥ 15 intentos/60s → BLOCK&lt;br&gt;HTTP-Abuse: ≥ 50 req/30s → LIMIT&lt;br&gt;              ≥ 100 req/30s → BLOCK" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontColor=#b46504;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="30" y="890" width="260" height="110" as="geometry"/>
        </mxCell>

        <!-- Bloqueo progresivo -->
        <mxCell id="prog" value="&lt;b&gt;Bloqueo progresivo&lt;/b&gt;&lt;br&gt;block_counts.json (por IP)&lt;br&gt;&lt;br&gt;bloqueo #1 → timeout 300s (5 min)&lt;br&gt;bloqueo #2 → timeout 1800s (30 min)&lt;br&gt;bloqueo #3 → timeout 0 (PERMANENTE ∞)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontColor=#b85450;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="250" y="1185" width="500" height="90" as="geometry"/>
        </mxCell>

        <!-- Enforcement -->
        <mxCell id="enf" value="Enforcement&lt;br&gt;SSH → m4rk@192.168.0.120&lt;br&gt;sudo ipset add ppi_blocked &lt;IP&gt; [timeout N]&lt;br&gt;sudo ipset add ppi_limited &lt;IP&gt; [timeout N]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="250" y="1335" width="500" height="80" as="geometry"/>
        </mxCell>

        <!-- Notificación -->
        <mxCell id="notif" value="Notificación&lt;br&gt;motor_decision.log  ·  Dashboard SSE :8080  ·  Telegram (dedup 300s/IP)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="250" y="1475" width="500" height="65" as="geometry"/>
        </mxCell>

        <!-- ARROWS main flow -->
        <mxCell id="a01" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="start" target="d_wl" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_wl_yes" value="SÍ" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;fontColor=#2d6a0b;fontStyle=1;" edge="1" source="d_wl" target="permit_wl" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_wl_no" value="NO" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;fontColor=#b85450;fontStyle=1;" edge="1" source="d_wl" target="feat" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_feat_sc" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="feat" target="scaler" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_sc_if" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="scaler" target="iforest" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_if_t1" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="iforest" target="d_t1" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_t1_yes" value="SÍ" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;fontColor=#2d6a0b;fontStyle=1;" edge="1" source="d_t1" target="permit_sc" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_t1_no" value="NO" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;fontColor=#b85450;fontStyle=1;" edge="1" source="d_t1" target="d_t2" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_t2_yes" value="SÍ" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d6b656;fontColor=#b46504;fontStyle=1;" edge="1" source="d_t2" target="limit_sc" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_t2_no" value="NO" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;fontColor=#b85450;fontStyle=1;" edge="1" source="d_t2" target="block_sc" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_heur_limit" value="override" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d79b00;dashed=1;fontColor=#d79b00;fontSize=9;" edge="1" source="heur" target="limit_sc" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_heur_block" value="override" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;dashed=1;fontColor=#b85450;fontSize=9;" edge="1" source="heur" target="block_sc" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_block_prog" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;" edge="1" source="block_sc" target="prog" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_limit_enf" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d6b656;" edge="1" source="limit_sc" target="enf" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_prog_enf" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;" edge="1" source="prog" target="enf" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a_enf_notif" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;" edge="1" source="enf" target="notif" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## Línea de decisión (τ1 / τ2)

```
Score IF     −1.0          −0.6027         −0.4459          0.0
              │──────────────┼───────────────┼───────────────│
              │   BLOCK 🚫  │    LIMIT ⚠️   │   PERMIT ✅   │
              │  DROP kernel │  100 pkt/s    │  sin acción   │
              │  τ2=FPR≤2%  │               │  τ1=Youden    │
              │  TPR=18.3%  │               │  TPR=99.4%    │
```
