# F6 — Diagrama Draw.io: Validación y Resultados

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

---

## Diagrama — 40 Corridas · Métricas · AUC · Gravedad · Entregables

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F6_validacion" name="F6 — Validación y Resultados">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1920" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="title" value="F6 — Validación del Sistema: 40 Corridas Controladas · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;" vertex="1" parent="1">
          <mxGeometry x="300" y="15" width="1000" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 1: SISTEMA ACTIVO F1-F5 -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="sys_bg" value="&lt;b&gt;Sistema Completo F1–F5 Activo&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="60" width="1560" height="75" as="geometry" />
        </mxCell>

        <mxCell id="s_f1" value="&lt;b&gt;F1&lt;/b&gt;&lt;br&gt;Suricata 7.0.3&lt;br&gt;ens35 · eve.json" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="10" y="30" width="150" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_f2" value="&lt;b&gt;F2&lt;/b&gt;&lt;br&gt;376,827 flows&lt;br&gt;train/val/test" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#82b366;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="180" y="30" width="150" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_f3" value="&lt;b&gt;F3&lt;/b&gt;&lt;br&gt;IF n=300 · AUC=0.9440&lt;br&gt;τ1=−0.4973 · τ2=−0.6873" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="350" y="30" width="200" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_f4" value="&lt;b&gt;F4&lt;/b&gt;&lt;br&gt;motor_decision.py&lt;br&gt;Det. SSH/HTTP · Telegram" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="570" y="30" width="200" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_f5" value="&lt;b&gt;F5&lt;/b&gt;&lt;br&gt;ipset ppi_blocked/ppi_limited&lt;br&gt;iptables DROP + hashlimit" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="790" y="30" width="220" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_tg" value="&lt;b&gt;Telegram&lt;/b&gt;&lt;br&gt;🚨⚠️🔑🌐 activo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1f5fe;strokeColor=#0277bd;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="1030" y="30" width="150" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_db" value="&lt;b&gt;Dashboard&lt;/b&gt;&lt;br&gt;:8080 SSE · terminal" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="1200" y="30" width="150" height="35" as="geometry" />
        </mxCell>
        <mxCell id="s_motor" value="&lt;b&gt;ppi-motor.service&lt;/b&gt;&lt;br&gt;Restart=on-failure · activo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="sys_bg">
          <mxGeometry x="1370" y="30" width="180" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 2: 40 CORRIDAS (4 GRUPOS) -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="corridas_bg" value="&lt;b&gt;scripts/f6_corridas.py — 40 Corridas Controladas&lt;/b&gt;&lt;br&gt;DURACION=300s por corrida · PAUSA=60s entre corridas" style="swimlane;startSize=40;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="165" width="630" height="520" as="geometry" />
        </mxCell>

        <!-- Grupo Normal -->
        <mxCell id="grp_normal" value="&lt;b&gt;Grupo Normal — Corridas 1–10&lt;/b&gt;&lt;br&gt;Solo tráfico legítimo Desktop 192.168.0.20&lt;br&gt;Rotación A1–A4 · 5 min/corrida" style="swimlane;startSize=38;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=11;" vertex="1" parent="corridas_bg">
          <mxGeometry x="10" y="48" width="606" height="95" as="geometry" />
        </mxCell>
        <mxCell id="gn_mide" value="Mide:&lt;br&gt;✓ ITL (¿Desktop bloqueado?)&lt;br&gt;✓ Disponibilidad (¿nginx responde?)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;align=left;spacingLeft=6;" vertex="1" parent="grp_normal">
          <mxGeometry x="10" y="42" width="260" height="43" as="geometry" />
        </mxCell>
        <mxCell id="gn_res" value="&lt;b&gt;resultados_normal.csv  899B&lt;/b&gt;&lt;br&gt;Disponibilidad=100% · ITL=0% · Latencia=6.6ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="grp_normal">
          <mxGeometry x="285" y="42" width="310" height="43" as="geometry" />
        </mxCell>

        <!-- Grupo Mixto -->
        <mxCell id="grp_mixto" value="&lt;b&gt;Grupo Mixto — Corridas 11–20&lt;/b&gt;&lt;br&gt;Desktop legítimo + Kali atacando simultáneamente&lt;br&gt;Rotación: synflood · portscan · udpflood · httpabuse" style="swimlane;startSize=38;fillColor=#fce4ec;strokeColor=#c62828;fontSize=11;" vertex="1" parent="corridas_bg">
          <mxGeometry x="10" y="160" width="606" height="95" as="geometry" />
        </mxCell>
        <mxCell id="gm_mide" value="Mide:&lt;br&gt;✓ TIE · Lead Time · MTTC&lt;br&gt;✓ ITL (¿Desktop afectado por error?)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;align=left;spacingLeft=6;" vertex="1" parent="grp_mixto">
          <mxGeometry x="10" y="42" width="260" height="43" as="geometry" />
        </mxCell>
        <mxCell id="gm_res" value="&lt;b&gt;resultados_mixto.csv  1.2KB&lt;/b&gt;&lt;br&gt;TIE=100% · ITL=0% · Lead Time=26s · MTTC=28s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="grp_mixto">
          <mxGeometry x="285" y="42" width="310" height="43" as="geometry" />
        </mxCell>

        <!-- Grupo Reeval -->
        <mxCell id="grp_reeval" value="&lt;b&gt;Grupo Re-evaluación — Corridas 21–30&lt;/b&gt;&lt;br&gt;Misma config que Mixto · verifica consistencia de τ1/τ2&lt;br&gt;Reproducibilidad entre sesiones" style="swimlane;startSize=38;fillColor=#fff3e0;strokeColor=#e65100;fontSize=11;" vertex="1" parent="corridas_bg">
          <mxGeometry x="10" y="272" width="606" height="95" as="geometry" />
        </mxCell>
        <mxCell id="gr_mide" value="Mide:&lt;br&gt;✓ Varianza inter-corridas&lt;br&gt;✓ Estabilidad scores τ1/τ2" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;align=left;spacingLeft=6;" vertex="1" parent="grp_reeval">
          <mxGeometry x="10" y="42" width="260" height="43" as="geometry" />
        </mxCell>
        <mxCell id="gr_res" value="&lt;b&gt;resultados_reeval.csv  1.2KB&lt;/b&gt;&lt;br&gt;Consistencia τ1/τ2 confirmada · std bajo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="grp_reeval">
          <mxGeometry x="285" y="42" width="310" height="43" as="geometry" />
        </mxCell>

        <!-- Grupo Final -->
        <mxCell id="grp_final" value="&lt;b&gt;Grupo Final — Corridas 31–40&lt;/b&gt;&lt;br&gt;Corridas definitivas del entregable PPI&lt;br&gt;Condiciones controladas · documentadas" style="swimlane;startSize=38;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=11;" vertex="1" parent="corridas_bg">
          <mxGeometry x="10" y="384" width="606" height="95" as="geometry" />
        </mxCell>
        <mxCell id="gf_mide" value="Mide:&lt;br&gt;✓ Todas las métricas&lt;br&gt;✓ Entregable oficial PPI" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;align=left;spacingLeft=6;" vertex="1" parent="grp_final">
          <mxGeometry x="10" y="42" width="260" height="43" as="geometry" />
        </mxCell>
        <mxCell id="gf_res" value="&lt;b&gt;resultados_final.csv  1.2KB&lt;/b&gt;&lt;br&gt;Corridas definitivas · todas las métricas ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="grp_final">
          <mxGeometry x="285" y="42" width="310" height="43" as="geometry" />
        </mxCell>

        <!-- resultados_f6_completo.csv -->
        <mxCell id="f6_completo" value="&lt;b&gt;resultados_f6_completo.csv  3.9KB&lt;/b&gt;&lt;br&gt;40 corridas consolidadas — ENTREGABLE PRINCIPAL" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#1565c0;strokeColor=#0d47a1;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="corridas_bg">
          <mxGeometry x="130" y="490" width="350" height="22" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 3: MÉTRICAS FINALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="metrics_bg" value="&lt;b&gt;Métricas Finales Validadas&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#c8e6c9;strokeColor=#1b5e20;fontSize=13;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="700" y="165" width="430" height="520" as="geometry" />
        </mxCell>

        <!-- Operacionales -->
        <mxCell id="met_op_title" value="OPERACIONALES (40 corridas)" style="text;html=1;fontSize=11;fontStyle=1;align=center;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="35" width="410" height="18" as="geometry" />
        </mxCell>
        <mxCell id="met_disp" value="Disponibilidad" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="58" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_disp_val" value="&lt;b&gt;100%&lt;/b&gt; ✅  (req ≥ 99%)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="56" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_itl" value="ITL (Impacto Tráfico Legítimo)" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="88" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_itl_val" value="&lt;b&gt;0%&lt;/b&gt; ✅  (req ≤ 2%)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="86" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_tie" value="TIE (Tasa Intervención Efectiva)" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="118" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_tie_val" value="&lt;b&gt;100%&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="116" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_lead" value="Lead Time" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="148" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_lead_val" value="&lt;b&gt;26 segundos&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="146" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_mttc" value="MTTC (Mean Time To Contain)" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="178" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_mttc_val" value="&lt;b&gt;28 segundos&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="176" width="175" height="24" as="geometry" />
        </mxCell>

        <!-- Pipeline -->
        <mxCell id="met_pip_title" value="PIPELINE" style="text;html=1;fontSize=11;fontStyle=1;align=center;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="215" width="410" height="18" as="geometry" />
        </mxCell>
        <mxCell id="met_lat" value="Latencia P95" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="237" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_lat_val" value="&lt;b&gt;34.8ms&lt;/b&gt; ✅  (req &lt;500ms · margen 14×)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="235" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_thr" value="Throughput" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="266" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_thr_val" value="29 flows/segundo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=11;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="264" width="175" height="24" as="geometry" />
        </mxCell>

        <!-- Modelo -->
        <mxCell id="met_mod_title" value="MODELO (test set 56,525 flows)" style="text;html=1;fontSize=11;fontStyle=1;align=center;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="305" width="410" height="18" as="geometry" />
        </mxCell>
        <mxCell id="met_auc" value="AUC-ROC" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="328" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_auc_val" value="&lt;b&gt;0.9440&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="326" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_rec" value="Recall (IF solo / con detectores)" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="357" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_rec_val" value="&lt;b&gt;87.6% / ~92–95%&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="355" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_prec" value="Precision" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="386" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_prec_val" value="&lt;b&gt;99.96%&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="384" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_f1" value="F1-Score" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="415" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_f1_val" value="&lt;b&gt;0.9338&lt;/b&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="413" width="175" height="24" as="geometry" />
        </mxCell>
        <mxCell id="met_fpr" value="FPR SSH / Transferencia" style="text;html=1;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="444" width="230" height="22" as="geometry" />
        </mxCell>
        <mxCell id="met_fpr_val" value="&lt;b&gt;0% / 0%&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="metrics_bg">
          <mxGeometry x="245" y="442" width="175" height="24" as="geometry" />
        </mxCell>

        <!-- Matriz confusión -->
        <mxCell id="conf_mat" value="TN=649(94.9%) · FP=35(5.1%)&lt;br&gt;TP=95,750(80.1%) · FN=23,792(19.9%)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e8f5e9;strokeColor=#2e7d32;fontSize=10;" vertex="1" parent="metrics_bg">
          <mxGeometry x="10" y="478" width="410" height="30" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 4: AUC POR ESCENARIO -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="auc_bg" value="&lt;b&gt;AUC y Detección por Escenario — scripts/auc_por_escenario.py&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#fafafa;strokeColor=#757575;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="715" width="1100" height="170" as="geometry" />
        </mxCell>

        <mxCell id="auc_e1" value="&lt;b&gt;B3 UDP Flood&lt;/b&gt;&lt;br&gt;AUC=0.9905 · Det=100%&lt;br&gt;Score=−0.714" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="10" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e2" value="&lt;b&gt;B4 ICMP Flood&lt;/b&gt;&lt;br&gt;AUC=0.9861 · Det=100%&lt;br&gt;Score=−0.699" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1b5e20;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="155" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e3" value="&lt;b&gt;C3 Mixto UDP&lt;/b&gt;&lt;br&gt;AUC=0.9801 · Det=99.3%&lt;br&gt;Score=−0.677" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2e7d32;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="300" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e4" value="&lt;b&gt;C1 Mixto HTTP&lt;/b&gt;&lt;br&gt;AUC=0.9737 · Det=100%&lt;br&gt;Score=−0.653" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2e7d32;strokeColor=#1b5e20;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="445" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e5" value="&lt;b&gt;B2 Port Scan&lt;/b&gt;&lt;br&gt;AUC=0.9721 · Det=99.9%&lt;br&gt;Score=−0.651" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#388e3c;strokeColor=#2e7d32;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="590" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e6" value="&lt;b&gt;B1 SYN Flood&lt;/b&gt;&lt;br&gt;AUC=0.9529 · Det=72.2%&lt;br&gt;Score=−0.606" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f9a825;strokeColor=#f57f17;fontColor=#000000;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="735" y="38" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e7" value="&lt;b&gt;C2 Mixto SSH&lt;/b&gt;&lt;br&gt;AUC=0.9277 · Det=57.1%&lt;br&gt;Score=−0.609" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fb8c00;strokeColor=#e65100;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="735" y="103" width="135" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e8" value="&lt;b&gt;B5 HTTP Abuse&lt;/b&gt;&lt;br&gt;AUC=0.8630 · Det=56.6%&lt;br&gt;→ Det.HTTP cubre resto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e65100;strokeColor=#bf360c;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="880" y="38" width="145" height="55" as="geometry" />
        </mxCell>
        <mxCell id="auc_e9" value="&lt;b&gt;B6 BruteForce SSH&lt;/b&gt;&lt;br&gt;AUC=0.6770 · Det=0.9%&lt;br&gt;→ Det.SSH cubre resto" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c62828;strokeColor=#b71c1c;fontColor=#ffffff;fontSize=10;" vertex="1" parent="auc_bg">
          <mxGeometry x="880" y="103" width="145" height="55" as="geometry" />
        </mxCell>

        <!-- Leyenda AUC -->
        <mxCell id="auc_ley" value="■ AUC &gt; 0.97 Excelente    ■ AUC 0.92–0.97 Muy bueno    ■ AUC &lt; 0.90 → Detector F4 complementa" style="text;html=1;fontSize=10;align=center;" vertex="1" parent="auc_bg">
          <mxGeometry x="10" y="138" width="1080" height="18" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 5: ESCALA DE GRAVEDAD -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="grav_bg" value="&lt;b&gt;Escala de Gravedad — clasificar_grado(score)&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#fafafa;strokeColor=#757575;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="30" y="915" width="1100" height="110" as="geometry" />
        </mxCell>

        <mxCell id="grav_n" value="&lt;b&gt;NORMAL&lt;/b&gt;&lt;br&gt;score &gt; −0.4973&lt;br&gt;→ PERMIT · sin acción&lt;br&gt;log.debug() invisible" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="grav_bg">
          <mxGeometry x="10" y="35" width="200" height="65" as="geometry" />
        </mxCell>
        <mxCell id="grav_b" value="&lt;b&gt;BAJA&lt;/b&gt;&lt;br&gt;−0.6873 &lt; score ≤ −0.4973&lt;br&gt;→ LIMIT · hashlimit 100/s&lt;br&gt;Telegram ⚠️ · log WARNING" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="grav_bg">
          <mxGeometry x="225" y="35" width="220" height="65" as="geometry" />
        </mxCell>
        <mxCell id="grav_a" value="&lt;b&gt;ALTA&lt;/b&gt;&lt;br&gt;−0.82 &lt; score ≤ −0.6873&lt;br&gt;→ BLOCK · DROP total&lt;br&gt;Telegram 🚨 · log WARNING" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffcdd2;strokeColor=#c62828;fontSize=10;" vertex="1" parent="grav_bg">
          <mxGeometry x="460" y="35" width="220" height="65" as="geometry" />
        </mxCell>
        <mxCell id="grav_c" value="&lt;b&gt;CRÍTICA&lt;/b&gt;&lt;br&gt;score ≤ −0.82  (p95 anómalos)&lt;br&gt;→ BLOCK · DROP · Escalado&lt;br&gt;Flood masivo extremo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#b71c1c;strokeColor=#7f0000;fontColor=#ffffff;fontSize=10;fontStyle=1;" vertex="1" parent="grav_bg">
          <mxGeometry x="695" y="35" width="220" height="65" as="geometry" />
        </mxCell>
        <mxCell id="grav_scores" value="Scores reales prod.: A1 HTTP−0.4277(N) · A2 SSH−0.4102(N) · B5 curl−0.5117(BAJA) · B2 scan−0.6260(BAJA) · B1 SYN−0.7214(ALTA) · B4 ICMP−0.7800(ALTA) · B3 UDP−0.8100(CRÍTICA)" style="text;html=1;fontSize=9;align=center;fontColor=#666666;" vertex="1" parent="grav_bg">
          <mxGeometry x="10" y="85" width="1080" height="18" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 6: VALIDACIÓN LIVE -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="live_bg" value="&lt;b&gt;Validaciones Live (sesión 2026-06-14/15)&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1170" y="165" width="420" height="365" as="geometry" />
        </mxCell>

        <mxCell id="live1" value="&lt;b&gt;A2+B2 simultáneos (19:41)&lt;/b&gt;&lt;br&gt;SSH Desktop: 0 FP (score=−0.434 &gt; τ1)&lt;br&gt;Port scan Kali: 1705/1705 detectados&lt;br&gt;Lead Time: 26s · BLOCK en 1er flow" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="live_bg">
          <mxGeometry x="10" y="35" width="400" height="65" as="geometry" />
        </mxCell>
        <mxCell id="live2" value="&lt;b&gt;Brute Force SSH (18:50)&lt;/b&gt;&lt;br&gt;hydra 25 intentos rápidos&lt;br&gt;ssh_intentos=15 en 60s → BLOCK&lt;br&gt;Telegram 🔑 recibido ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fce4ec;strokeColor=#c62828;fontSize=10;" vertex="1" parent="live_bg">
          <mxGeometry x="10" y="115" width="400" height="65" as="geometry" />
        </mxCell>
        <mxCell id="live3" value="&lt;b&gt;HTTP Abuse escalado (18:13)&lt;/b&gt;&lt;br&gt;55 curl → LIMIT (18:13:13)&lt;br&gt;100 req/30s → BLOCK (18:13:21)&lt;br&gt;Telegram 🌐 recibido ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff3e0;strokeColor=#e65100;fontSize=10;" vertex="1" parent="live_bg">
          <mxGeometry x="10" y="195" width="400" height="65" as="geometry" />
        </mxCell>
        <mxCell id="live4" value="&lt;b&gt;FP = 0 verificado&lt;/b&gt;&lt;br&gt;grep SOSPECHOSO|ANOMALÍA log | grep -v .100&lt;br&gt;→ 0 resultados en sesión 14-15 jun ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;" vertex="1" parent="live_bg">
          <mxGeometry x="10" y="275" width="400" height="50" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- SECCIÓN 7: ENTREGABLES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="entrega_bg" value="&lt;b&gt;Entregables Finales&lt;/b&gt;" style="swimlane;startSize=28;fillColor=#fffde7;strokeColor=#f9a825;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="1170" y="560" width="420" height="320" as="geometry" />
        </mxCell>

        <mxCell id="e_pdf" value="&lt;b&gt;reporte_validacion_final.pdf&lt;/b&gt;  7.4KB&lt;br&gt;scripts/generar_pdf_final.py&lt;br&gt;Generado: 2026-06-04 20:06&lt;br&gt;3 páginas · métricas completas&lt;br&gt;&lt;b&gt;← Entregable académico PPI&lt;/b&gt;" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="entrega_bg">
          <mxGeometry x="10" y="35" width="195" height="100" as="geometry" />
        </mxCell>
        <mxCell id="e_zip" value="&lt;b&gt;MVP_funcional.zip&lt;/b&gt;  25MB&lt;br&gt;scripts/generar_pdf_zip.py&lt;br&gt;40 archivos: scripts + modelos&lt;br&gt;+ datasets + resultados&lt;br&gt;&lt;b&gt;← Entregable técnico PPI&lt;/b&gt;" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff9c4;strokeColor=#f9a825;fontSize=10;" vertex="1" parent="entrega_bg">
          <mxGeometry x="215" y="35" width="195" height="100" as="geometry" />
        </mxCell>
        <mxCell id="e_github" value="&lt;b&gt;GitHub&lt;/b&gt;&lt;br&gt;marksato13/PRODUCTO-_INGENIERL&lt;br&gt;35+ commits · docs F1-F6&lt;br&gt;44 diagramas Mermaid&lt;br&gt;54 archivos .md" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e3f2fd;strokeColor=#1565c0;fontSize=10;" vertex="1" parent="entrega_bg">
          <mxGeometry x="10" y="145" width="195" height="85" as="geometry" />
        </mxCell>
        <mxCell id="e_log" value="&lt;b&gt;motor_decision.log&lt;/b&gt;  7.6MB&lt;br&gt;Evidencia de producción&lt;br&gt;BLOCK/LIMIT/heurísticas&lt;br&gt;con razón z-score incluida" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#f3e5f5;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="entrega_bg">
          <mxGeometry x="215" y="145" width="195" height="85" as="geometry" />
        </mxCell>
        <mxCell id="e_resumen" value="&lt;b&gt;Resultado Final&lt;/b&gt;&lt;br&gt;Sistema de detección temprana&lt;br&gt;operativo en tiempo real&lt;br&gt;Recall 92–95% · Precision 99.96%&lt;br&gt;ITL 0% · Disponibilidad 100%&lt;br&gt;Latencia P95 = 34.8ms" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1565c0;strokeColor=#0d47a1;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="entrega_bg">
          <mxGeometry x="10" y="242" width="400" height="65" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════════════ -->
        <!-- FLECHAS PRINCIPALES -->
        <!-- ══════════════════════════════════════════════════════ -->
        <mxCell id="sys_to_corridas" value="sistema activo" style="endArrow=block;endFill=1;html=1;strokeColor=#2e7d32;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="sys_bg" target="corridas_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="corridas_to_metrics" value="resultados" style="endArrow=block;endFill=1;html=1;strokeColor=#1b5e20;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="corridas_bg" target="metrics_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="corridas_to_auc" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#757575;strokeWidth=2;" edge="1" source="corridas_bg" target="auc_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="metrics_to_live" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=2;dashed=1;" edge="1" source="metrics_bg" target="live_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="metrics_to_entrega" value="genera" style="endArrow=block;endFill=1;html=1;strokeColor=#f9a825;strokeWidth=3;fontSize=11;fontStyle=1;" edge="1" source="metrics_bg" target="entrega_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
