# F2 — Diagrama: Pipeline de Captura de Tráfico

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML → OK

```xml
<mxGraphModel dx="1400" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="800" math="0" shadow="0">
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <!-- Título -->
    <mxCell id="100" value="F2 — Pipeline de Captura de Tráfico · PPI UPeU 2026" style="text;html=1;align=center;fontStyle=1;fontSize=13;" vertex="1" parent="1"><mxGeometry x="350" y="20" width="700" height="40" as="geometry"/></mxCell>
    <!-- Fuentes de tráfico -->
    <mxCell id="2" value="&lt;b&gt;Grupo A — Normal&lt;/b&gt;&#xa;Desktop 192.168.0.20&#xa;A1 http_normal (curl :80, 10 min)&#xa;A2 ssh_legitimo (ssh :22, 8 min)&#xa;A3 transferencia (scp/wget, 10 min)&#xa;A4 trafico_sostenido (mixto, 15 min)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="40" y="120" width="210" height="120" as="geometry"/></mxCell>
    <mxCell id="3" value="&lt;b&gt;Grupo B — Anómalo&lt;/b&gt;&#xa;Kali 192.168.0.100&#xa;B1 syn_flood (hping3 -S, :80)&#xa;B2 port_scan (nmap -sS 1-1024)&#xa;B3 udp_flood (hping3 --udp, :53)&#xa;B4 icmp_flood (hping3 -1)&#xa;B5 http_abuse (curl bucle, :80)&#xa;B6 bruteforce (hydra, :22)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="40" y="280" width="210" height="160" as="geometry"/></mxCell>
    <mxCell id="4" value="&lt;b&gt;Grupo C — Mixto&lt;/b&gt;&#xa;Desktop + Kali simultáneos&#xa;C1 http_normal + syn_flood&#xa;C2 ssh_legitimo + port_scan&#xa;C3 transferencia + udp_flood" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;align=left;fontSize=10;" vertex="1" parent="1"><mxGeometry x="40" y="480" width="210" height="110" as="geometry"/></mxCell>
    <!-- Suricata -->
    <mxCell id="5" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&#xa;sensor 192.168.0.110&#xa;ens35 — captura pasiva&#xa;Salida: /var/log/suricata/eve.json&#xa;Formato: EVE JSON (flows)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="340" y="300" width="180" height="110" as="geometry"/></mxCell>
    <!-- eve.json.gz -->
    <mxCell id="6" value="&lt;b&gt;eve.json.gz&lt;/b&gt;&#xa;51 archivos raw&#xa;data/raw/&#xa;YYYYMMDD_grupo_escenario_NN" style="shape=document;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666;fontSize=10;" vertex="1" parent="1"><mxGeometry x="610" y="300" width="150" height="90" as="geometry"/></mxCell>
    <!-- Scripts F2 -->
    <mxCell id="7" value="parser.py&#xa;eve.json.gz → dataset_raw.csv&#xa;Extrae flows tipo netflow" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="1"><mxGeometry x="850" y="160" width="170" height="70" as="geometry"/></mxCell>
    <mxCell id="8" value="etiquetar_limpiar.py&#xa;raw → labeled → clean&#xa;label=0 normal, label=1 anómalo&#xa;dedup + filtros IP" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="1"><mxGeometry x="850" y="280" width="170" height="80" as="geometry"/></mxCell>
    <mxCell id="9" value="particionar_estadisticos.py&#xa;clean → train/val/test&#xa;Split 70/15/15 cronológico&#xa;(no aleatorio — evita leakage)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;" vertex="1" parent="1"><mxGeometry x="850" y="410" width="170" height="80" as="geometry"/></mxCell>
    <!-- Salidas finales -->
    <mxCell id="10" value="train.csv&#xa;val.csv&#xa;test.csv&#xa;data/" style="shape=document;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="1110" y="330" width="130" height="90" as="geometry"/></mxCell>
    <!-- exportar_eve -->
    <mxCell id="11" value="exportar_eve_por_escenario.sh&#xa;gzip + truncate + reopen-log" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=10;" vertex="1" parent="1"><mxGeometry x="600" y="160" width="170" height="60" as="geometry"/></mxCell>
    <!-- Flechas -->
    <mxCell id="20" edge="1" source="2" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="21" edge="1" source="3" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="22" edge="1" source="4" target="5" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="23" edge="1" source="5" target="11" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="24" edge="1" source="11" target="6" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="25" edge="1" source="6" target="7" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="26" edge="1" source="7" target="8" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="27" edge="1" source="8" target="9" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="28" edge="1" source="9" target="10" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>
```
