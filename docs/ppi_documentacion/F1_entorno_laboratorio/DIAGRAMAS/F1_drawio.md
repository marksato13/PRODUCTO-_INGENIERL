# F1 — Diagrama Draw.io: Entorno de Laboratorio

**Instrucciones:** Abrir Draw.io → Extras → Edit Diagram → pegar el XML de abajo → OK

---

## Diagrama 1 — Topología de Red y Flujo de Captura Suricata

```xml
<mxfile host="Electron" version="24.7.17">
  <diagram id="F1_topologia" name="F1 — Topología y Captura">
    <mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- ══════════════════════════════════════════════ -->
        <!-- TÍTULO -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="title" value="F1 — Entorno de Laboratorio · PPI UPeU 2026" style="text;html=1;fontSize=16;fontStyle=1;align=center;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="400" y="20" width="700" height="35" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- NTP -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="ntp" value="&lt;b&gt;NTP&lt;/b&gt;&lt;br&gt;pool.ntp.org&lt;br&gt;America/Lima UTC−5" style="ellipse;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="660" y="70" width="180" height="70" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- SWITCH / LAN BACKBONE -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="lan_label" value="Red LAN — 192.168.0.0/24 (VMware)" style="text;html=1;fontSize=12;fontStyle=1;fontColor=#1a237e;align=center;" vertex="1" parent="1">
          <mxGeometry x="380" y="175" width="380" height="25" as="geometry" />
        </mxCell>
        <mxCell id="lan_bus" value="" style="endArrow=none;startArrow=none;html=1;strokeColor=#1565c0;strokeWidth=4;fillColor=none;" edge="1" parent="1">
          <mxGeometry x="100" y="220" width="1350" height="10" as="geometry">
            <Array as="points">
              <mxPoint x="1400" y="220" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- pfSense Gateway -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="pfsense" value="&lt;b&gt;pfSense&lt;/b&gt;&lt;br&gt;192.168.0.1&lt;br&gt;Gateway · Firewall · DHCP" style="shape=mxgraph.network.router;fillColor=#e1d5e7;strokeColor=#9673a6;html=1;fontSize=11;labelPosition=bottom;verticalLabelPosition=bottom;align=center;verticalAlign=top;" vertex="1" parent="1">
          <mxGeometry x="710" y="130" width="80" height="60" as="geometry" />
        </mxCell>
        <mxCell id="pfs_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#9673a6;strokeWidth=2;" edge="1" source="pfsense" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="750" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- DESKTOP 192.168.0.20 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="desktop" value="&lt;b&gt;Ubuntu Desktop&lt;/b&gt;&lt;br&gt;192.168.0.20&lt;br&gt;─────────────────&lt;br&gt;Admin · Claude Code&lt;br&gt;curl · wget · ssh · scp&lt;br&gt;Scripts A1–A4 · C1–C3&lt;br&gt;🔑 SSH keys → Sensor · Servidor" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="50" y="270" width="230" height="140" as="geometry" />
        </mxCell>
        <mxCell id="dt_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#6c8ebf;strokeWidth=2;" edge="1" source="desktop" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="165" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- KALI 192.168.0.100 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="kali" value="&lt;b&gt;Kali Linux&lt;/b&gt;&lt;br&gt;192.168.0.100&lt;br&gt;─────────────────&lt;br&gt;Atacante controlado&lt;br&gt;hping3 · nmap · hydra&lt;br&gt;Scripts B1–B6" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontSize=11;align=left;spacingLeft=8;" vertex="1" parent="1">
          <mxGeometry x="1260" y="270" width="230" height="130" as="geometry" />
        </mxCell>
        <mxCell id="kl_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#b85450;strokeWidth=2;" edge="1" source="kali" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="1375" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- BIGDATA 192.168.0.130 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="bigdata" value="&lt;b&gt;Ubuntu BigData&lt;/b&gt;&lt;br&gt;192.168.0.130&lt;br&gt;Almacenamiento" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="1260" y="470" width="200" height="80" as="geometry" />
        </mxCell>
        <mxCell id="bd_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#9673a6;" edge="1" source="bigdata" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="1360" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- SENSOR CONTAINER 192.168.0.110 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="sensor_bg" value="&lt;b&gt;Ubuntu Suricata — 192.168.0.110  |  Sensor IDS&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;fontStyle=1;align=left;spacingLeft=10;" vertex="1" parent="1">
          <mxGeometry x="300" y="270" width="660" height="340" as="geometry" />
        </mxCell>
        <mxCell id="sensor_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#82b366;strokeWidth=2;" edge="1" source="sensor_bg" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="630" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ens33 (gestión) -->
        <mxCell id="ens33" value="&lt;b&gt;ens33&lt;/b&gt;&lt;br&gt;192.168.0.110&lt;br&gt;Gestión SSH" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="30" y="55" width="140" height="60" as="geometry" />
        </mxCell>

        <!-- ens35 (captura) -->
        <mxCell id="ens35" value="&lt;b&gt;ens35&lt;/b&gt;&lt;br&gt;sin IP asignada&lt;br&gt;Captura promiscua" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d6b656;fontSize=10;fontStyle=1;" vertex="1" parent="sensor_bg">
          <mxGeometry x="200" y="55" width="150" height="60" as="geometry" />
        </mxCell>

        <!-- suricata.yaml -->
        <mxCell id="yaml" value="&lt;b&gt;suricata.yaml&lt;/b&gt;&lt;br&gt;af-packet: ens35&lt;br&gt;outputs: eve-log" style="shape=note;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="30" y="160" width="150" height="65" as="geometry" />
        </mxCell>

        <!-- Suricata proceso -->
        <mxCell id="suricata_proc" value="&lt;b&gt;Suricata 7.0.3&lt;/b&gt;&lt;br&gt;suricata -i ens35 -D&lt;br&gt;Demonio activo" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#82b366;strokeColor=#2e7d32;fontColor=#ffffff;fontSize=11;fontStyle=1;" vertex="1" parent="sensor_bg">
          <mxGeometry x="200" y="155" width="180" height="70" as="geometry" />
        </mxCell>

        <!-- eve.json -->
        <mxCell id="eve_json" value="&lt;b&gt;eve.json&lt;/b&gt;&lt;br&gt;/var/log/suricata/&lt;br&gt;JSON-lines · tiempo real&lt;br&gt;flow | alert | ssh | stats" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#2e7d32;fontSize=10;fontStyle=1;" vertex="1" parent="sensor_bg">
          <mxGeometry x="420" y="145" width="170" height="85" as="geometry" />
        </mxCell>

        <!-- Scripts validación -->
        <mxCell id="revisar_sh" value="&lt;b&gt;revisar_suricata.sh&lt;/b&gt;&lt;br&gt;scripts/validation/" style="shape=note;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;" vertex="1" parent="sensor_bg">
          <mxGeometry x="30" y="265" width="170" height="55" as="geometry" />
        </mxCell>

        <mxCell id="revision_txt" value="&lt;b&gt;suricata_revision.txt&lt;/b&gt;&lt;br&gt;Evidencia formal F1 ✅" style="shape=note;whiteSpace=wrap;html=1;fillColor=#c8e6c9;strokeColor=#388e3c;fontSize=10;fontStyle=1;" vertex="1" parent="sensor_bg">
          <mxGeometry x="230" y="265" width="180" height="55" as="geometry" />
        </mxCell>

        <!-- Flechas internas sensor -->
        <mxCell id="ens35_to_suri" value="captura promiscua" style="endArrow=block;endFill=1;html=1;fontSize=9;strokeColor=#d6b656;strokeWidth=2;" edge="1" source="ens35" target="suricata_proc" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="yaml_to_suri" value="configura" style="endArrow=block;endFill=1;html=1;fontSize=9;strokeColor=#666666;" edge="1" source="yaml" target="suricata_proc" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="suri_to_eve" value="escribe flow event" style="endArrow=block;endFill=1;html=1;fontSize=9;strokeColor=#2e7d32;strokeWidth=2;" edge="1" source="suricata_proc" target="eve_json" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="eve_to_revisar" value="valida" style="endArrow=open;startArrow=none;dashed=1;html=1;fontSize=9;strokeColor=#666666;" edge="1" source="eve_json" target="revisar_sh" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="revisar_to_txt" value="" style="endArrow=block;endFill=1;html=1;strokeColor=#388e3c;" edge="1" source="revisar_sh" target="revision_txt" parent="sensor_bg">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- SERVIDOR 192.168.0.120 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="srv_bg" value="&lt;b&gt;Ubuntu Server — 192.168.0.120  |  Objetivo&lt;/b&gt;" style="swimlane;startSize=30;fillColor=#ffe6cc;strokeColor=#d6b656;fontSize=12;fontStyle=1;align=left;spacingLeft=10;" vertex="1" parent="1">
          <mxGeometry x="980" y="270" width="260" height="210" as="geometry" />
        </mxCell>
        <mxCell id="srv_to_lan" value="" style="endArrow=open;startArrow=open;endFill=0;startFill=0;html=1;strokeColor=#d6b656;strokeWidth=2;" edge="1" source="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="1110" y="220" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <mxCell id="nginx" value="&lt;b&gt;nginx :80&lt;/b&gt;&lt;br&gt;/var/www/html/ ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;" vertex="1" parent="srv_bg">
          <mxGeometry x="30" y="50" width="200" height="50" as="geometry" />
        </mxCell>
        <mxCell id="sshd" value="&lt;b&gt;openssh-server :22&lt;/b&gt;&lt;br&gt;Acceso admin + brute-force ✅" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;" vertex="1" parent="srv_bg">
          <mxGeometry x="30" y="120" width="200" height="50" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- TRÁFICO ENTRE VMs -->
        <!-- ══════════════════════════════════════════════ -->
        <!-- Desktop → Servidor (normal) -->
        <mxCell id="dt_to_srv" value="A1–A4: curl · ssh · scp · wget" style="endArrow=block;endFill=1;html=1;strokeColor=#1565c0;strokeWidth=2;fontSize=10;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;" edge="1" source="desktop" target="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="340" y="315" />
              <mxPoint x="340" y="315" />
            </Array>
          </mxGeometry>
        </mxCell>

        <!-- Kali → Servidor (ataque) -->
        <mxCell id="kl_to_srv" value="B1–B6: hping3 · nmap · hydra" style="endArrow=block;endFill=1;html=1;strokeColor=#b85450;strokeWidth=2;fontSize=10;exitX=0;exitY=0.3;exitDx=0;exitDy=0;entryX=1;entryY=0.3;entryDx=0;entryDy=0;" edge="1" source="kali" target="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- Servidor → Desktop (respuestas) -->
        <mxCell id="srv_to_dt" value="HTTP 200 · SSH resp." style="endArrow=open;endFill=0;html=1;strokeColor=#82b366;strokeWidth=1;dashed=1;fontSize=9;exitX=0;exitY=0.6;exitDx=0;exitDy=0;entryX=1;entryY=0.6;entryDx=0;entryDy=0;" edge="1" source="srv_bg" target="desktop" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ens35 captura del tráfico LAN -->
        <mxCell id="lan_to_ens35" value="espeja tráfico LAN" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=2;dashed=1;fontSize=10;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="750" y="220" as="sourcePoint" />
            <mxPoint x="480" y="330" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- SSH KEYS -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="ssh_key1" value="🔑 SSH key" style="endArrow=open;endFill=0;html=1;strokeColor=#6c8ebf;dashed=1;fontSize=9;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="280" y="360" as="sourcePoint" />
            <mxPoint x="300" y="360" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="ssh_keys_label" value="ssh-copy-id → Sensor" style="text;html=1;fontSize=9;fontColor=#1565c0;" vertex="1" parent="1">
          <mxGeometry x="80" y="430" width="160" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ssh_key_dt_sensor" value="🔑 SSH key" style="endArrow=open;endFill=0;html=1;strokeColor=#6c8ebf;dashed=1;fontSize=9;exitX=0.7;exitY=1;exitDx=0;exitDy=0;" edge="1" source="desktop" target="sensor_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ssh_key_dt_srv" value="🔑 SSH key" style="endArrow=open;endFill=0;html=1;strokeColor=#6c8ebf;dashed=1;fontSize=9;" edge="1" source="desktop" target="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- NTP SYNC ARROWS -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="ntp_dt" value="NTP sync" style="endArrow=open;endFill=0;html=1;strokeColor=#d6b656;dashed=1;fontSize=9;" edge="1" source="ntp" target="desktop" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ntp_sensor" value="NTP sync" style="endArrow=open;endFill=0;html=1;strokeColor=#d6b656;dashed=1;fontSize=9;" edge="1" source="ntp" target="sensor_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ntp_srv" value="NTP sync" style="endArrow=open;endFill=0;html=1;strokeColor=#d6b656;dashed=1;fontSize=9;" edge="1" source="ntp" target="srv_bg" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="ntp_kali" value="NTP sync" style="endArrow=open;endFill=0;html=1;strokeColor=#d6b656;dashed=1;fontSize=9;" edge="1" source="ntp" target="kali" parent="1">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- CONECTOR → F2 -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="f2_conn" value="&lt;b&gt;→ F2: Captura de Tráfico&lt;/b&gt;&lt;br&gt;eve.json es la entrada&lt;br&gt;de todos los escenarios A/B/C&lt;br&gt;exportar_eve_por_escenario.sh" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;strokeWidth=3;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="440" y="650" width="260" height="80" as="geometry" />
        </mxCell>
        <mxCell id="eve_to_f2" value="input de corridas A/B/C" style="endArrow=block;endFill=1;html=1;strokeColor=#d6b656;strokeWidth=3;fontSize=10;fontStyle=1;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="600" y="613" as="sourcePoint" />
            <mxPoint x="570" y="650" as="targetPoint" />
          </mxGeometry>
        </mxCell>

        <!-- ══════════════════════════════════════════════ -->
        <!-- LEYENDA -->
        <!-- ══════════════════════════════════════════════ -->
        <mxCell id="leyenda_bg" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="30" y="660" width="260" height="100" as="geometry" />
        </mxCell>
        <mxCell id="leyenda_title" value="&lt;b&gt;Leyenda&lt;/b&gt;" style="text;html=1;fontSize=11;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="45" y="665" width="80" height="20" as="geometry" />
        </mxCell>
        <mxCell id="ley1" value="── Tráfico de red" style="text;html=1;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="45" y="685" width="160" height="18" as="geometry" />
        </mxCell>
        <mxCell id="ley2" value="- - Copia promiscua / NTP / SSH key" style="text;html=1;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="45" y="703" width="230" height="18" as="geometry" />
        </mxCell>
        <mxCell id="ley3" value="══ Flujo de datos principal → F2" style="text;html=1;fontSize=10;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="45" y="721" width="230" height="18" as="geometry" />
        </mxCell>
        <mxCell id="ley4" value="Scripts: revisar_suricata.sh · exportar_eve_por_escenario.sh" style="text;html=1;fontSize=9;fontColor=#666666;" vertex="1" parent="1">
          <mxGeometry x="45" y="739" width="240" height="18" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```
