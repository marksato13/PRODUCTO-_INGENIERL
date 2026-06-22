# Diagrama 2 — Pipeline en 6 Fases
**Slide 5 del PPT**

---

## draw.io XML

> Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxfile host="app.diagrams.net" modified="2026-06-22" version="21.0.0">
  <diagram id="d2-pipeline" name="Pipeline 6 Fases">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="700" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- F1 CAPTURA -->
        <mxCell id="f1" value="&lt;b&gt;&lt;font style=&apos;font-size:14px;&apos;&gt;F1&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;CAPTURA&lt;/b&gt;&lt;br&gt;&lt;hr/&gt;Suricata 7.0.3&lt;br&gt;ens35 · modo pasivo&lt;br&gt;&lt;br&gt;9 escenarios (A/B/C)&lt;br&gt;47 capturas .json.gz&lt;br&gt;&lt;br&gt;capture/exportar_eve&lt;br&gt;_por_escenario.sh&lt;br&gt;&lt;br&gt;&lt;font color=&apos;#666666&apos;&gt;Output:&lt;/font&gt;&lt;br&gt;eve.json.gz" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="20" y="60" width="230" height="560" as="geometry"/>
        </mxCell>

        <!-- F2 PROCESAMIENTO -->
        <mxCell id="f2" value="&lt;b&gt;&lt;font style=&apos;font-size:14px;&apos;&gt;F2&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;PROCESAMIENTO&lt;/b&gt;&lt;br&gt;&lt;hr/&gt;fase3_entrenar.py&lt;br&gt;(preproceso datos)&lt;br&gt;&lt;br&gt;14 features por flujo&lt;br&gt;pkts · bytes · rates&lt;br&gt;proto · puerto · dur&lt;br&gt;&lt;br&gt;Flujos normales:&lt;br&gt;53,708 (desktop .20)&lt;br&gt;&lt;br&gt;Flujos anómalos:&lt;br&gt;598,285 etiquetados&lt;br&gt;&lt;br&gt;&lt;font color=&apos;#6c8ebf&apos;&gt;Output:&lt;/font&gt;&lt;br&gt;normal_holdout.csv&lt;br&gt;(20% holdout = 13,427)&lt;br&gt;dataset_comparacion.csv" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="290" y="60" width="230" height="560" as="geometry"/>
        </mxCell>

        <!-- F3 MODELO IF -->
        <mxCell id="f3" value="&lt;b&gt;&lt;font style=&apos;font-size:14px;&apos;&gt;F3&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;MODELO IF&lt;/b&gt;&lt;br&gt;&lt;hr/&gt;fase3_entrenar.py&lt;br&gt;fase3_evaluar.py&lt;br&gt;&lt;br&gt;IsolationForest&lt;br&gt;n=300, contam=0.05&lt;br&gt;&lt;br&gt;Split &lt;b&gt;80/20 aleatorio&lt;/b&gt;&lt;br&gt;(shuffle=True)&lt;br&gt;&lt;br&gt;AUC-ROC = 0.8998&lt;br&gt;Precision = 99.54%&lt;br&gt;Recall = 99.40%&lt;br&gt;F1 = 0.9947&lt;br&gt;&lt;br&gt;τ1 = −0.4459 (Youden)&lt;br&gt;τ2 = −0.6027 (FPR≤2%)&lt;br&gt;&lt;br&gt;&lt;font color=&apos;#314354&apos;&gt;Output:&lt;/font&gt;&lt;br&gt;isolation_forest.pkl&lt;br&gt;scaler.pkl&lt;br&gt;metricas_offline.txt" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#647687;strokeColor=#314354;fontColor=#ffffff;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="560" y="60" width="230" height="560" as="geometry"/>
        </mxCell>

        <!-- F4 MOTOR (destacado) -->
        <mxCell id="f4" value="&lt;b&gt;&lt;font style=&apos;font-size:16px;&apos;&gt;F4 + F5a&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;MOTOR DE DECISIÓN&lt;/b&gt;&lt;br&gt;&lt;font color=&apos;#ffffff&apos;&gt;CORE DEL SISTEMA&lt;/font&gt;&lt;br&gt;&lt;hr/&gt;motor_decision.py&lt;br&gt;&lt;br&gt;tail eve.json&lt;br&gt;→ 14 features&lt;br&gt;→ IF score&lt;br&gt;&lt;br&gt;score &gt; τ1 → &lt;b&gt;PERMIT&lt;/b&gt; ✅&lt;br&gt;τ2 &lt; score ≤ τ1 → &lt;b&gt;LIMIT&lt;/b&gt; ⚠️&lt;br&gt;score ≤ τ2 → &lt;b&gt;BLOCK&lt;/b&gt; 🚫&lt;br&gt;&lt;br&gt;BF-SSH: 5→LIMIT 15→BLOCK&lt;br&gt;HTTP: 50→LIMIT 100→BLOCK&lt;br&gt;&lt;br&gt;Bloqueo progresivo:&lt;br&gt;#1=5min · #2=30min · #3=∞&lt;br&gt;&lt;br&gt;→ Dashboard SSE :8080&lt;br&gt;→ Telegram (async)&lt;br&gt;&lt;br&gt;SSH → ipset add&lt;br&gt;ppi_blocked / ppi_limited" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#82b366;strokeColor=#2d6a0b;fontColor=#ffffff;fontSize=11;verticalAlign=top;strokeWidth=3;" vertex="1" parent="1">
          <mxGeometry x="830" y="30" width="260" height="600" as="geometry"/>
        </mxCell>

        <!-- F5 APRENDIZAJE CONTINUO -->
        <mxCell id="f5" value="&lt;b&gt;&lt;font style=&apos;font-size:14px;&apos;&gt;F5b&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;APRENDIZAJE&lt;br&gt;CONTINUO&lt;/b&gt;&lt;br&gt;&lt;hr/&gt;f5_reentrenar_if.py&lt;br&gt;f5_reentrenar_xgboost.py&lt;br&gt;&lt;br&gt;XGBoost v2:&lt;br&gt;diario (03:00)&lt;br&gt;9 features comport.&lt;br&gt;AUC = 0.9992&lt;br&gt;Split 80/20 estrat.&lt;br&gt;&lt;br&gt;IF: semanal (dom 02:00)&lt;br&gt;&lt;br&gt;hot-reload sin reinicio&lt;br&gt;Guarda solo si&lt;br&gt;AUC no retrocede&lt;br&gt;&lt;br&gt;&lt;font color=&apos;#2d6a0b&apos;&gt;Output:&lt;/font&gt;&lt;br&gt;predictor_modelo_v2.pkl&lt;br&gt;isolation_forest.pkl" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="1140" y="60" width="230" height="560" as="geometry"/>
        </mxCell>

        <!-- F6 VALIDACION -->
        <mxCell id="f6" value="&lt;b&gt;&lt;font style=&apos;font-size:14px;&apos;&gt;F6&lt;/font&gt;&lt;/b&gt;&lt;br&gt;&lt;b&gt;VALIDACIÓN&lt;/b&gt;&lt;br&gt;&lt;hr/&gt;f6_corridas.py&lt;br&gt;auc_por_escenario.py&lt;br&gt;generar_graficas_f6.py&lt;br&gt;&lt;br&gt;40 corridas · 4 grupos × 10&lt;br&gt;5 min/corrida · ataque T+15s&lt;br&gt;&lt;br&gt;Disponibilidad = 100%&lt;br&gt;ITL = 0%&lt;br&gt;Latencia P95 = 34.8ms&lt;br&gt;(req &lt; 500ms ✓)&lt;br&gt;&lt;br&gt;Lead Time ≈ 62s&lt;br&gt;(SYN Flood)&lt;br&gt;&lt;br&gt;Grupos: Normal · Mixto · Reeval · Final&lt;br&gt;Ataques: synflood · portscan · udpflood · httpabuse&lt;br&gt;CA-16 FPR datos nuevos = 0.0% ✅&lt;br&gt;&lt;br&gt;&lt;font color=&apos;#b85450&apos;&gt;Output:&lt;/font&gt;&lt;br&gt;resultados_f6_completo.csv&lt;br&gt;graficas_f6/ (7 PNG 300DPI)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="1420" y="60" width="230" height="560" as="geometry"/>
        </mxCell>

        <!-- Flechas entre fases -->
        <mxCell id="a12" value="47 archivos .gz" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#666666;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="f1" target="f2" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a23" value="normal_holdout.csv" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#6c8ebf;strokeWidth=2;fontSize=10;fontStyle=1;" edge="1" source="f2" target="f3" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a34" value="isolation_forest.pkl&lt;br&gt;metricas_offline.txt" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#647687;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#314354;" edge="1" source="f3" target="f4" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a45" value="motor_decision.log" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#2d6a0b;" edge="1" source="f4" target="f5" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        <mxCell id="a54" value="hot-reload pkl" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#82b366;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#2d6a0b;dashed=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;" edge="1" source="f5" target="f4" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="1255" y="680"/>
              <mxPoint x="960" y="680"/>
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="a46" value="resultados_f6_completo.csv" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#d6b656;strokeWidth=2;fontSize=10;fontStyle=1;fontColor=#b46504;" edge="1" source="f4" target="f6" parent="1">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## Correcciones respecto a versión anterior

| Incorrecto (v. anterior) | Correcto (implementado) |
|---|---|
| Split cronológico 70/15/15 | **Split 80/20 aleatorio** (IF) / **estratificado** (XGBoost) |
| train.csv / val.csv / test.csv | `normal_holdout.csv` (20%) + `dataset_comparacion.csv` |
| parser.py / etiquetar_limpiar.py | No existen — se usa `fase3_entrenar.py` |
| particionar_estadisticos.py | No existe |
| fase3_isolation_forest.py | No existe → `fase3_entrenar.py` + `fase3_evaluar.py` |
| auc_roc_umbrales.py | No existe → incluido en `fase3_evaluar.py` |
| XGBoost no mencionado | **F5b**: `f5_reentrenar_xgboost.py`, 9 features, AUC=0.9992 |

---

## Notas de actualización (2026-06-22)

- Verificado contra código real en sensor 192.168.0.110
- ipset/iptables corre en servidor 192.168.0.120 (enforcement vía SSH)
- Telegram: API directa (api.telegram.org), sin relay
- Predictor ciclo: 10 segundos (INTERVALO=10)
- F6: 4 grupos × 10 corridas = 40, 300s cada una, ataque a T+15s
