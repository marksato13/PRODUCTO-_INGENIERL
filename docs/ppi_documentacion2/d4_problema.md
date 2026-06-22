# Diagrama 4 — Situación Problemática y Objetivos
**Slides 2 y 4 del PPT**

---

## draw.io XML

> Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxfile host="app.diagrams.net" modified="2026-06-22" version="21.0.0">
  <diagram id="d4-problema" name="Problema y Objetivos">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- ═══════════════════════════════════════════ -->
        <!-- SECCIÓN 1: ANTES vs DESPUÉS               -->
        <!-- ═══════════════════════════════════════════ -->

        <!-- Título sección 1 -->
        <mxCell id="t1" value="PROBLEMA: Detección tardía de amenazas en redes corporativas" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="15" width="1400" height="40" as="geometry"/>
        </mxCell>

        <!-- ANTES background -->
        <mxCell id="antes_bg" value="SIN ESTE SISTEMA" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontColor=#b85450;fontSize=15;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="60" y="70" width="680" height="500" as="geometry"/>
        </mxCell>

        <!-- Antes T+0 -->
        <mxCell id="a_t0" value="T + 0&lt;br&gt;&lt;b&gt;Atacante inicia SYN flood / BF SSH&lt;/b&gt;&lt;br&gt;Kali 192.168.0.100 → Servidor :80 / :22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="100" y="120" width="600" height="70" as="geometry"/>
        </mxCell>
        <!-- Antes T+? -->
        <mxCell id="a_t1" value="T + ??? minutos&lt;br&gt;&lt;b&gt;Servidor se degrada / cae&lt;/b&gt;&lt;br&gt;nginx sin respuesta · SSH bloqueado&lt;br&gt;IDS por firma: &quot;no conozco este patrón — ignoro&quot;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="100" y="220" width="600" height="80" as="geometry"/>
        </mxCell>
        <!-- Antes T+días -->
        <mxCell id="a_t2" value="T + horas o días&lt;br&gt;&lt;b&gt;Admin llega a la oficina o recibe reporte&lt;/b&gt;&lt;br&gt;&quot;reviso los logs... ya era tarde&quot;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="100" y="330" width="600" height="70" as="geometry"/>
        </mxCell>
        <!-- 207 días -->
        <mxCell id="ibm" value="207 días" style="text;html=1;strokeColor=#b85450;fillColor=#ffffff;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=1;fontSize=42;fontStyle=1;fontColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="170" y="425" width="460" height="90" as="geometry"/>
        </mxCell>
        <mxCell id="ibm_sub" value="tiempo promedio de detección (IBM Cost of a Data Breach 2023)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=11;fontColor=#b85450;" vertex="1" parent="1">
          <mxGeometry x="120" y="520" width="560" height="30" as="geometry"/>
        </mxCell>

        <!-- DESPUÉS background -->
        <mxCell id="desp_bg" value="CON ESTE SISTEMA" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=15;fontStyle=1;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="860" y="70" width="680" height="500" as="geometry"/>
        </mxCell>

        <!-- Después T+0 -->
        <mxCell id="d_t0" value="T + 0&lt;br&gt;&lt;b&gt;Atacante inicia SYN flood / BF SSH&lt;/b&gt;&lt;br&gt;Kali 192.168.0.100 → Servidor :80 / :22" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="900" y="120" width="600" height="70" as="geometry"/>
        </mxCell>
        <!-- T+53s -->
        <mxCell id="d_t53" value="T + 53s&lt;br&gt;&lt;b&gt;Motor detecta: SOSPECHOSO&lt;/b&gt;&lt;br&gt;score = −0.48 · BF-SSH: 5 intentos/60s&lt;br&gt;⚠️ LIMIT — hashlimit 100 pkt/s aplicado" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontColor=#b46504;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="900" y="220" width="600" height="80" as="geometry"/>
        </mxCell>
        <!-- T+60s BLOCK -->
        <mxCell id="d_t60" value="T + 60s&lt;br&gt;&lt;b&gt;Motor confirma: ANOMALÍA&lt;/b&gt;&lt;br&gt;BF-SSH: 15 intentos/60s alcanzados&lt;br&gt;🚫 BLOCK — ipset DROP (kernel)&lt;br&gt;bloqueo #1: timeout 300s" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontColor=#b85450;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="900" y="330" width="600" height="90" as="geometry"/>
        </mxCell>
        <!-- T+60s Telegram -->
        <mxCell id="d_tel" value="T + 60s  📱  Telegram al operador&lt;br&gt;T + 60s  🖥  Dashboard: IP bloqueada&lt;br&gt;&lt;b&gt;Sin intervención humana&lt;/b&gt; ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="900" y="450" width="600" height="80" as="geometry"/>
        </mxCell>

        <!-- VS separador -->
        <mxCell id="vs" value="VS" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=36;fontStyle=1;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="745" y="270" width="110" height="80" as="geometry"/>
        </mxCell>

        <!-- Flecha ANTES -->
        <mxCell id="ea1" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;strokeWidth=2;" edge="1" source="a_t0" target="a_t1" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ea2" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;strokeWidth=2;" edge="1" source="a_t1" target="a_t2" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ea3" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;strokeWidth=2;" edge="1" source="a_t2" target="ibm" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <!-- Flecha DESPUÉS -->
        <mxCell id="ed1" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;strokeWidth=2;" edge="1" source="d_t0" target="d_t53" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ed2" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d6b656;strokeWidth=2;" edge="1" source="d_t53" target="d_t60" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="ed3" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#b85450;strokeWidth=2;" edge="1" source="d_t60" target="d_tel" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

        <!-- ═══════════════════════════════════════════ -->
        <!-- SECCIÓN 2: ÁRBOL DE OBJETIVOS             -->
        <!-- ═══════════════════════════════════════════ -->

        <!-- Título sección 2 -->
        <mxCell id="t2" value="ÁRBOL DE OBJETIVOS" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="595" width="1400" height="40" as="geometry"/>
        </mxCell>

        <!-- OG -->
        <mxCell id="og" value="&lt;b&gt;OBJETIVO GENERAL&lt;/b&gt;&lt;br&gt;Desarrollar un sistema de detección temprana y control inline&lt;br&gt;de comportamientos anómalos en redes de datos,&lt;br&gt;con respuesta automática en tiempo real (P95 &lt; 500ms)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#647687;strokeColor=#314354;fontColor=#ffffff;fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="500" y="645" width="600" height="90" as="geometry"/>
        </mxCell>

        <!-- OE1 -->
        <mxCell id="oe1" value="&lt;b&gt;OE 1&lt;/b&gt;&lt;br&gt;Pipeline de captura&lt;br&gt;y procesamiento&lt;br&gt;de tráfico real&lt;br&gt;&lt;hr/&gt;F1 + F2&lt;br&gt;47 capturas&lt;br&gt;14 features&lt;br&gt;667K flujos&lt;br&gt;etiquetados" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="100" y="790" width="250" height="230" as="geometry"/>
        </mxCell>

        <!-- OE2 -->
        <mxCell id="oe2" value="&lt;b&gt;OE 2&lt;/b&gt;&lt;br&gt;Modelo de detección&lt;br&gt;AUC-ROC ≥ 0.80&lt;br&gt;con datos reales&lt;br&gt;&lt;hr/&gt;F3&lt;br&gt;AUC = 0.8998 ✅&lt;br&gt;Precision = 99.54%&lt;br&gt;Recall = 99.40%&lt;br&gt;F1 = 0.9947" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#647687;strokeColor=#314354;fontColor=#ffffff;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="675" y="790" width="250" height="230" as="geometry"/>
        </mxCell>

        <!-- OE3 -->
        <mxCell id="oe3" value="&lt;b&gt;OE 3&lt;/b&gt;&lt;br&gt;Motor de decisión +&lt;br&gt;validación 40 corridas&lt;br&gt;&lt;hr/&gt;F4 + F5 + F6&lt;br&gt;Disp. = 100% ✅&lt;br&gt;ITL = 0% ✅&lt;br&gt;P95 = 34.8ms ✅&lt;br&gt;Lead ≈ 62s ✅&lt;br&gt;XGBoost AUC=0.9992 ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontColor=#2d6a0b;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1250" y="790" width="250" height="230" as="geometry"/>
        </mxCell>

        <!-- Líneas OG→OE -->
        <mxCell id="og_oe1" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=2;" edge="1" source="og" target="oe1" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="og_oe2" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#647687;strokeWidth=2;" edge="1" source="og" target="oe2" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="og_oe3" value="" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;strokeWidth=2;" edge="1" source="og" target="oe3" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## Notas de uso

- **Slide 2** → usar solo la sección ANTES/DESPUÉS (parte superior del diagrama)
- **Slide 4** → usar solo el árbol de objetivos (parte inferior)
- En draw.io puedes seleccionar un grupo de celdas y exportar solo esa sección como PNG
- Los números reales del DESPUÉS (T+53s LIMIT, T+60s BLOCK) fueron validados en la sesión de pruebas en vivo del 2026-06-22
