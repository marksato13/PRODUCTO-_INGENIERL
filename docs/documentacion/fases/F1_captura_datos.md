# F1 — Captura de Datos
**Estado: ✅ COMPLETA Y VALIDADA**  
**Período:** mayo–junio 2026 | **Resultado:** 47 capturas, 13 escenarios, 3.7 GB de tráfico real

---

## Objetivo

Registrar tráfico de red real bajo escenarios controlados (normal y anómalo) en un laboratorio virtualizado y almacenarlo como capturas brutas listas para el entrenamiento del modelo.

**Por qué esto es el fundamento de todo el sistema:** el Isolation Forest aprende exclusivamente de ejemplos de tráfico "normal". Si los datos de F1 son de baja calidad, sesgados o no representativos, ningún ajuste de hiperparámetros puede compensarlo. La validez de todo el sistema depende de que los datos de F1 sean reales, variados y bien etiquetados.

---

## Entradas → Proceso → Salidas

```
ENTRADAS
  Red física: tráfico real entre Desktop↔Servidor y Kali↔Servidor
  Herramientas: hping3, nmap, hydra, curl, wget, scp (según escenario)
  Configuración: Suricata 7.0.3 en ens35 modo promiscuo (AF-PACKET)

PROCESO
  Suricata captura todos los paquetes del segmento → genera eve.json (JSON/línea)
  Al fin de cada corrida:
    exportar_eve_por_escenario.sh → gzip -c eve.json → archivo .gz
    sudo truncate -s 0 eve.json   → vaciar para siguiente corrida
    suricatasc reopen-log-files   → Suricata rota el descriptor sin reiniciarse
    registrar_bitacora.sh         → escribe línea en bitácora

SALIDAS
  data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz  (47 archivos, 3.7 GB)
  data/normal_holdout.csv                            (13,427 flujos normales)
  docs/bitacora/bitacora_escenarios.txt              (64 entradas)
```

---

## Terminología clave

| Término | Definición |
|---|---|
| **Suricata** | Motor IDS/IPS de código abierto (v7.0.3). Captura paquetes en modo pasivo, analiza el tráfico y genera eventos estructurados en `eve.json`. No bloquea tráfico por sí mismo en F1. |
| **eve.json** | Archivo de log de Suricata en formato JSON por línea. Cada línea es un evento: `flow`, `alert`, `dns`, `http`, `stats`, etc. Es la única fuente de datos de toda la cadena de detección. |
| **Flujo (flow)** | Unidad de tráfico agregada: todos los paquetes entre un par src_ip:port ↔ dst_ip:port con el mismo protocolo, durante una sesión. Suricata los cierra por timeout (TCP FIN/RST) o expiración de idle timer. Cada flujo se convierte en una fila del dataset. |
| **ens35** | Interfaz de red del sensor (192.168.0.110) conectada al segmento de laboratorio. Configurada en **modo promiscuo**: recibe todos los paquetes del segmento, no solo los dirigidos a ella. |
| **Modo promiscuo** | La NIC acepta paquetes aunque el MAC destino no sea el suyo. Sin este modo, Suricata solo vería tráfico hacia/desde el sensor — nunca el tráfico entre Desktop↔Servidor ni Kali↔Servidor. |
| **AF-PACKET** | Modo de captura de Suricata que usa `rx_rings` en espacio de kernel, evitando copias de memoria innecesarias. Más eficiente que pcap tradicional para redes a 1 Gbps. |
| **eve.json.gz** | Compresión gzip del eve.json de una corrida. Reduce el tamaño ~10×. Formato final de almacenamiento de cada captura. Los 47 archivos suman 3.7 GB. |
| **Corrida** | Sesión de tráfico controlada de un escenario específico. Cada corrida genera un `.gz` independiente con nomenclatura `YYYYMMDD_grupo_escenario_NN`. La nomenclatura garantiza trazabilidad: cualquier resultado puede mapearse al evento exacto que lo generó. |
| **EDA** | Exploratory Data Analysis. Estudio estadístico de las 14 features para verificar su poder discriminante ANTES de entrenar el modelo. El EDA justifica que las features elegidas son válidas, no arbitrarias. |
| **Escenario** | Patrón de tráfico reproducible con herramienta, duración y objetivo definidos. La reproducibilidad es esencial para que el jurado pueda replicar cualquier corrida y obtener resultados comparables. |

---

## Topología del laboratorio

```
┌─────────────────────────────────────────────────────────┐
│                 Red 192.168.0.0/24                       │
│                                                          │
│  ┌──────────────┐        ┌──────────────────────────┐   │
│  │ Win11        │        │ Ubuntu Desktop           │   │
│  │ 192.168.0.10 │        │ 192.168.0.20 ◄─ ADMIN   │   │
│  └──────────────┘        └──────────────────────────┘   │
│                                      │                   │
│  ┌──────────────┐        ┌──────────────────────────┐   │
│  │ Kali Linux   │        │ Ubuntu Sensor            │   │
│  │ 192.168.0.100│        │ 192.168.0.110            │   │
│  │ ATACANTE     │        │ Suricata 7.0.3 ens35     │   │
│  └──────────────┘        │ Motor + Modelos          │   │
│                          └──────────────────────────┘   │
│                                      │                   │
│                          ┌──────────────────────────┐   │
│                          │ Ubuntu Server            │   │
│                          │ 192.168.0.120            │   │
│                          │ nginx:80  SSH:22         │   │
│                          └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Por qué el sensor es una máquina separada del servidor:** el motor de detección corre en el sensor (192.168.0.110), no en el servidor que atiende tráfico (192.168.0.120). Esto garantiza que un fallo del motor nunca afecta la disponibilidad del servicio — los paquetes llegan al servidor independientemente. El sensor opera en modo pasivo: solo escucha, nunca interfiere con el flujo de red.

**Por qué Suricata y no Snort o Zeek:** Suricata 7 soporta AF-PACKET multihilo nativo, genera `eve.json` en formato JSON estructurado (listo para Python sin conversión), y tiene soporte activo de la comunidad OISF. Zeek también genera logs JSON pero su modelo de scripting es más complejo para pipelines de ML. Snort no genera JSON por defecto. Suricata es el estándar de facto en entornos de producción modernos.

---

## Qué se implementó

### Infraestructura de captura

| Componente | Versión / Configuración | Por qué esta elección |
|---|---|---|
| Suricata | 7.0.3 — modo pasivo, AF-PACKET en ens35 | Captura sin modificar el tráfico; AF-PACKET reduce latencia vs pcap |
| eve.json | `/var/log/suricata/eve.json` — JSON por línea | Parsing directo con Python sin librerías adicionales |
| Rotación | `exportar_eve_por_escenario.sh` + `suricatasc reopen-log-files` | Rota el archivo sin reiniciar Suricata — sin pérdida de paquetes |
| Registro | `registrar_bitacora.sh` → `docs/bitacora/bitacora_escenarios.txt` | Trazabilidad completa: hora, herramienta y archivo de cada corrida |

### Scripts de escenarios

```
scripts/capture/
├── exportar_eve_por_escenario.sh  ← exporta + rota eve.json al fin de cada corrida
├── run_A1_A4.sh                   ← ejecuta los 4 escenarios normales en secuencia
├── A1_http_normal.sh        — curl/wget → :80  (10 min)
├── A2_ssh_legitimo.sh       — ssh → :22         (8 min)
├── A3_transferencia_legitima.sh — scp/wget      (10 min)
├── A4_trafico_sostenido.sh  — curl+ssh mixto    (15 min)
├── B1_syn_flood.sh          — hping3 -S -i u5000 → :80
├── B2_port_scan.sh          — nmap -sS
├── B3_udp_flood.sh          — hping3 --udp -i u5000 → :53
├── B4_icmp_flood.sh         — hping3 -1 --flood
├── B5_acceso_repetitivo.sh  — curl bucle rápido → :80
├── B6_bruteforce.sh         — hydra -t 4 → :22
├── C1_http_syn_mixto.sh     — Desktop+Kali simultáneo
├── C2_ssh_portscan_mixto.sh
├── C3_descarga_udp_mixto.sh
└── deploy_kali.sh           ← despliega herramientas en Kali vía SSH
```

---

## Escenarios capturados

### Grupo A — Tráfico Normal (desde Desktop 192.168.0.20)

| ID | Nombre | Duración | Herramienta | Por qué este escenario |
|---|---|---|---|---|
| A1 | http_normal | 10 min | `curl`/`wget` → :80 | Define baseline HTTP: el tráfico más común en redes corporativas. Sin este escenario, el IF no aprendería que HTTP legítimo es normal |
| A2 | ssh_legitimo | 8 min | `ssh` → :22 | Define baseline SSH: los administradores usan SSH constantemente. El IF debe aprender que SSH desde 192.168.0.20 es normal aunque B6 (hydra) también use SSH |
| A3 | transferencia_legitima | 10 min | `scp`/`wget` archivos grandes | Tráfico de alta transferencia: genera flujos con `bytes_toclient` alto — sin este escenario, el IF marcaría descargas legítimas como anómalas |
| A4 | trafico_sostenido | 15 min | `curl`+`ssh` mixto | Mezcla realista: en producción, el tráfico no es de un solo tipo. Este escenario enseña al IF la variabilidad natural del tráfico normal |

> **Por qué solo Desktop como origen normal:** el modelo IF aprende de lo que es "normal" para ESTA red específica. Tráfico legítimo viene exclusivamente de 192.168.0.20 hacia 192.168.0.120. Añadir otros orígenes introduciría variabilidad no controlada que confundiría al modelo.

> **Por qué el sensor (192.168.0.110) está en la whitelist:** el sensor también genera tráfico (SSH al servidor para aplicar bloqueos, F6 corridas). Si no estuviera en la whitelist, el motor se bloquearía a sí mismo — lo que haría imposible cualquier operación remota.

### Grupo B — Tráfico Anómalo (desde Kali 192.168.0.100)

| ID | Nombre | Comando | Tipo | Por qué este ataque |
|---|---|---|---|---|
| B1 | syn_flood | `hping3 -S -p 80 -i u5000 192.168.0.120` | Volumétrico L4 | Agota el backlog de conexiones TCP. Representativo de DDoS — genera miles de half-open connections |
| B2 | port_scan | `nmap -sS 192.168.0.120` | Reconocimiento | Primer paso de cualquier intrusión (MITRE ATT&CK T1046). Genera flujos muy cortos a múltiples puertos — perfil único en IF |
| B3 | udp_flood | `hping3 --udp -p 53 -i u5000 192.168.0.120` | Volumétrico L4 | UDP no tiene estado TCP — Suricata crea un flujo independiente por cada paquete → genera el mayor volumen de eventos por corrida. Elegimos :53 (DNS) para simular amplificación UDP |
| B4 | icmp_flood | `hping3 -1 --flood 192.168.0.120` | Volumétrico L3 | Ping flood — satura el stack ICMP del servidor. Simple pero efectivo. Las features `is_icmp` y `pkt_rate` lo distinguen fácilmente del tráfico normal |
| B5 | acceso_repetitivo | `curl` en bucle rápido → :80 | Aplicación L7 | HTTP flood desde una sola IP — no es volumétrico como B1, sino por frecuencia de solicitudes. El IF lo ve como anómalo por `pkt_rate` y `byte_ratio` inusuales |
| B6 | bruteforce_ssh | `hydra -t 4 -l root -P wordlist ssh://192.168.0.120` | Credenciales | Fuerza bruta SSH (MITRE ATT&CK T1110). `hydra -t 4` usa 4 hilos paralelos — genera múltiples conexiones SSH fallidas en ráfaga. Perfil de `pkts_toserver` alto, `pkts_toclient` bajo (servidor rechaza) |

> **Por qué hping3 y no scapy:** hping3 genera tráfico a velocidad de kernel sin overhead de Python. Para floods reales (miles de paquetes/segundo), scapy es 10-100× más lento. Para el EDA necesitábamos tráfico suficientemente intenso para que las features fueran discriminantes.

> **Por qué hydra y no medusa o patator:** hydra es la herramienta estándar en pentesting para SSH BF (MITRE recomienda su uso en testing). Sus 4 hilos producen el patrón de conexiones paralelas que el IF debe aprender a detectar.

### Grupo C — Mixto (Desktop + Kali simultáneos)

| ID | Componentes | Por qué este escenario es el más exigente |
|---|---|---|
| C1 | A1 (curl normal) + B1 (SYN flood) | Prueba que el IF distingue Desktop (whitelisted) de Kali en el mismo segmento. Si el sistema bloquea ambos, ITL > 0% — falla crítica |
| C2 | A2 (SSH legítimo) + B2 (port scan) | El SSH legítimo de Desktop y el port scan de Kali usan TCP. La única diferencia es el patrón de puertos destino y la IP de origen |
| C3 | A3 (descarga) + B3 (UDP flood) | Descarga legítima coexiste con flood UDP — el servidor debe seguir respondiendo a Desktop mientras dropea a Kali |

> **Por qué el Grupo C es crítico para la defensa:** en producción real, un atacante nunca opera en vacío — siempre hay tráfico legítimo simultáneo. El Grupo C demuestra que el sistema actúa quirúrgicamente (bloquea solo a Kali) y no como un firewall de kill-switch que corta todo el tráfico.

---

## Protocolo de una corrida completa

```bash
# 1. Verificar Suricata activo
systemctl is-active suricata

# 2. Verificar que eve.json esté en rotación limpia
wc -l /var/log/suricata/eve.json   # debe ser 0 o bajo

# 3. Ejecutar el escenario (ej: B1 SYN Flood)
FECHA=$(date +%Y%m%d); CORRIDA=01; HORA_INI=$(date +%T)
bash scripts/capture/B1_syn_flood.sh
HORA_FIN=$(date +%T)

# 4. Exportar eve.json → comprime + rota sin reiniciar Suricata
bash scripts/capture/exportar_eve_por_escenario.sh $FECHA anom synflood $CORRIDA
# → data/raw/20260602_anom_synflood_01_eve.json.gz

# 5. Registrar en bitácora (trazabilidad completa)
bash scripts/evaluation/registrar_bitacora.sh \
  anom synflood 192.168.0.100 192.168.0.120 \
  $HORA_INI $HORA_FIN "hping3 -S -i u5000" \
  "20260602_anom_synflood_01_eve.json.gz"

# 6. Esperar mínimo 2 minutos — Suricata necesita cerrar flows residuales
# Sin esta pausa, los flujos del ataque anterior contaminarían la siguiente corrida
sleep 120
```

**Por qué `suricatasc reopen-log-files` en lugar de reiniciar Suricata:** reiniciar Suricata tarda ~5 segundos y pierde todos los flujos en curso. `suricatasc reopen-log-files` cierra y reabre el descriptor de archivo en <1ms, sin perder ni un paquete. Es la única forma de rotar el log en producción sin interrupciones.

**Por qué esperar 2 minutos entre corridas:** Suricata tiene timeouts de flujo configurados (TCP: 60s idle, UDP: 30s). Si la siguiente corrida empieza antes de que expiren los flujos de la corrida anterior, eve.json tendrá eventos mezclados de dos escenarios distintos — los flujos residuales contaminarían el entrenamiento.

---

## Análisis Exploratorio de Datos (EDA)

El EDA se realizó sobre los flujos extraídos de los 47 archivos raw. Las 6 gráficas generadas están en `docs/documentacion/imagenes/F1_captura/` y son parte del informe final.

**Por qué hacer EDA antes de entrenar:** el EDA valida que las 14 features elegidas son discriminantes. Si el EDA hubiera mostrado que las features no separan normal de anómalo visualmente, habríamos necesitado rediseñarlas antes de gastar tiempo entrenando modelos.

### Hallazgos del EDA — justificación de las 14 features

| Imagen | Qué muestra | Hallazgo clave | Implicación para el modelo |
|---|---|---|---|
| `eda_01_distribuciones.png` | Histogramas de las 14 features | `bytes_toclient` tiene cola larga en ataques volumétricos (B1, B3) | El IF aprende que flujos con pocos bytes de respuesta son sospechosos (servidor no responde al flood) |
| `eda_02_protocolo.png` | % TCP / UDP / ICMP por grupo | Grupo A: 85% TCP. B3 UDP: 100% UDP. B1: 100% TCP SYN | `is_udp` e `is_tcp` son features válidas — la distribución de protocolos difiere entre grupos |
| `eda_03_boxplots.png` | Rangos normal vs anómalo | `pkt_rate` normal: μ=18 pkt/s. SYN flood: μ=8,420 pkt/s | `pkt_rate` y `byte_rate` son los features más discriminantes — separación de 467× |
| `eda_04_correlacion.png` | Correlación entre features | `pkts_toserver` y `bytes_toserver` correlación ~0.95 | Alta correlación no es problema para IF (no es lineal) — ambas features aportan información |
| `eda_05_dest_ports.png` | Puertos destino frecuentes | :80 (HTTP), :22 (SSH), :53 (UDP) dominan en ataques | `dest_port` es feature válida — los ataques apuntan a puertos específicos |
| `eda_06_stats_tabla.png` | Estadísticas completas (μ, σ, min, max) | `pkt_rate` normal μ=18, σ=12. Anómalo μ=8,420, σ=4,200 | Separación estadística clara → el IF puede construir fronteras de decisión efectivas |

**Las 14 features elegidas** (`pkts_toserver`, `pkts_toclient`, `bytes_toserver`, `bytes_toclient`, `duration`, `pkt_rate`, `byte_rate`, `pkt_ratio`, `byte_ratio`, `avg_pkt_size`, `is_tcp`, `is_udp`, `is_icmp`, `dest_port`) son todas extraíbles directamente de los eventos `flow` de Suricata sin procesamiento adicional. Esto garantiza que el modelo puede funcionar en tiempo real sin latencia de transformación.

> Ver imágenes completas: `docs/documentacion/imagenes/F1_captura/`

---

## Dataset generado

```
data/
├── raw/                           ← 47 archivos .json.gz (3.7 GB total)
│   ├── 20260602_normal_http_01_eve.json.gz
│   ├── 20260602_anom_synflood_01_eve.json.gz
│   └── ... (45 archivos más)
└── normal_holdout.csv             ← 13,427 flujos normales (generado en F2)

docs/bitacora/
└── bitacora_escenarios.txt        ← 64 entradas registradas
```

**Por qué solo 47 capturas y no cientos:** en un laboratorio virtualizado con 5 VMs, la variabilidad del tráfico está acotada — más corridas del mismo escenario producirían flujos casi idénticos. 47 capturas cubren todos los escenarios (A1-A4, B1-B6, C1-C3) con múltiples repeticiones en diferentes fechas (02-jun al 15-jun), garantizando variabilidad temporal suficiente.

**Por qué la nomenclatura `YYYYMMDD_grupo_escenario_NN`:** permite trazabilidad completa. Si durante la defensa el jurado pregunta por qué un flujo específico tiene score X, podemos localizar el archivo exact, la corrida exacta y la entrada de bitácora correspondiente. Sin nomenclatura estructurada, los 47 archivos serían indistinguibles.

---

## Criterios de aceptación — CUMPLIDOS ✅

| CA | Criterio | Resultado | Argumento |
|---|---|---|---|
| CA-F1-01 | Suricata captura en ens35 modo pasivo | ✅ Activo — 500MB eve.json | Verificable con `systemctl is-active suricata` + `ls -lh /var/log/suricata/eve.json` |
| CA-F1-02 | Mínimo 9 escenarios distintos capturados | ✅ 13 escenarios (A1-A4, B1-B6, C1-C3) | 44% más de lo requerido — mayor diversidad de entrenamiento |
| CA-F1-03 | ≥ 1 corrida por escenario archivada en `.gz` | ✅ 47 capturas | Promedio 3.6 corridas por escenario — variabilidad temporal garantizada |
| CA-F1-04 | Nomenclatura `YYYYMMDD_grupo_escenario_NN` | ✅ Todas las capturas | Verificable con `ls data/raw/` |
| CA-F1-05 | Bitácora con timestamp por corrida | ✅ 64 entradas | Trazabilidad completa: `cat docs/bitacora/bitacora_escenarios.txt` |
| CA-F1-06 | eve.json rotado correctamente post-corrida | ✅ `suricatasc reopen-log-files` | Sin reinicio de Suricata = sin pérdida de paquetes entre corridas |

---

## Argumento de defensa

> "F1 no es solo 'capturar tráfico'. Diseñamos 13 escenarios que representan el espectro completo de una red corporativa: 4 escenarios de uso legítimo con variedad (HTTP, SSH, transferencia, tráfico mixto) y 6 vectores de ataque alineados con MITRE ATT&CK — reconocimiento (B2), ataques volumétricos L3/L4 (B1, B3, B4), abuso de aplicación (B5) y credenciales (B6). Los escenarios mixtos del Grupo C son especialmente valiosos porque validan la precisión quirúrgica del sistema: el IF bloquea a Kali sin tocar a Desktop, incluso cuando ambos están activos simultáneamente en el mismo segmento.
>
> El EDA confirma que la elección de las 14 features no fue arbitraria: la tasa de paquetes en SYN flood (μ=8,420 pkt/s) es 467 veces mayor que en tráfico normal (μ=18 pkt/s). La separación es tan clara estadísticamente que el IF puede construir fronteras de decisión con AUC=0.8998 sin necesidad de etiquetas.
>
> Elegimos Suricata 7.0.3 sobre alternativas (Snort, Zeek) por su soporte nativo de AF-PACKET y salida JSON estructurada directamente consumible por Python — sin capas de conversión que introduzcan latencia. La arquitectura de sensor separado garantiza que el motor de detección nunca afecta la disponibilidad del servicio que protege."

