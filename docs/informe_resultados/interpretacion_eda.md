# Interpretación de Figuras y Resultados EDA

**Documento complementario al Informe de Resultados**
**PPI — Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos**
Universidad Peruana Unión · Junio 2026

---

## Contexto general del EDA

El Análisis Exploratorio de Features (EDA) se realizó sobre **401,424 flows** capturados en el laboratorio antes de entrenar el modelo. El objetivo fue verificar que las 14 features discriminan entre tráfico normal y anómalo, y entender la distribución de cada grupo para justificar la selección del Isolation Forest.

| Grupo | Tipo | Flows | Archivos | Fuente |
|---|---|---|---|---|
| A | Normal | 67,135 | 28 | Desktop 192.168.0.20 |
| B | Anómalo | 302,892 | 13 | Kali 192.168.0.100 |
| C | Mixto | 31,397 | 6 | Desktop + Kali simultáneos |

> **Resultado global:** Las 14 features superaron el test Mann-Whitney U con p < 0.001 (Grupo A vs. Grupo B), confirmando que todas son estadísticamente discriminantes.

---

## Figura 1 — Distribuciones log₁₀ de features clave por grupo

**¿Qué muestra?** Histogramas de densidad de 6 features (pkt_rate, byte_rate, duration, pkt_ratio, byte_ratio, avg_pkt_size) en escala logarítmica para los tres grupos.

**Interpretación feature por feature:**

### `pkt_rate` (paquetes por segundo)
- **Grupo A (azul):** distribución amplia, dispersa entre log₁₀=0 y log₁₀=4. Refleja la variedad del tráfico legítimo: sesiones SSH lentas (~14 pkt/s, P25) conviven con descargas intensas (~1,000 pkt/s, P75).
- **Grupo B (rojo):** pico concentrado y alto en log₁₀=3 (= 1,000 pkt/s). Los ataques de flood generan tasas de paquetes muy elevadas y uniformes — el hping3 en modo flood fuerza exactamente 1,000 pkt/s como límite de sesión.
- **Grupo C (verde):** bimodal, mezcla las dos distribuciones: pico a log₁₀=3 del tráfico anómalo y cola a la izquierda del tráfico normal.
- **Implicación:** pkt_rate es parcialmente discriminante pero insuficiente sola — el tráfico normal sostenido (A4) también puede llegar a 1,000 pkt/s.

### `byte_rate` (bytes por segundo)
- **Grupo A:** distribución amplia (P25=1,909 B/s, P75=199,226 B/s). Alta variabilidad: el HTTP en reposo envía poco, las descargas SCP envían mucho.
- **Grupo B:** pico pronunciado y estrecho en log₁₀=4.78 (= 60,000 B/s). El flood SYN envía paquetes mínimos (60 bytes cada uno) a tasa máxima.
- **Implicación:** byte_rate discrimina, pero depende del tipo de ataque. El flood ICMP puede tener byte_rate similar al tráfico normal.

### `duration` (duración del flow en segundos)
- **Grupo A:** distribución amplia entre log₁₀=−3 y log₁₀=4 (0.001 s a 10,000 s). Las sesiones SSH duran minutos; las respuestas HTTP duran milisegundos.
- **Grupo B:** distribución **extremadamente concentrada** en log₁₀=−3 a log₁₀=−1 (duración 0.001–0.1 s). Los ataques de inundación crean flows que Suricata cierra casi inmediatamente porque no completan el handshake TCP.
- **Implicación:** duration baja sola podría generar falsos positivos (las respuestas HTTP rápidas también tienen duration baja), pero en combinación con otras features es muy útil.

### `pkt_ratio` (pkts_toserver / pkts_toclient + 1)
- **Grupo A y B:** ambos picos centrados en log₁₀=0 (ratio ≈ 1). La diferencia es sutil: en tráfico normal las conversaciones son bidireccionales balanceadas; en floods TCP (SYN sin ACK) el servidor responde con RST/ACK pero en menor proporción.
- **Implicación:** pkt_ratio es la **feature menos discriminante visualmente** — las distribuciones se solapan. Sin embargo, sigue siendo estadísticamente significativa (p < 0.001) y contribuye al modelo en combinación con otras.

### `byte_ratio` (bytes_toserver / bytes_toclient + 1)
- **Grupo A:** pico muy estrecho y alto en log₁₀=0 (ratio ≈ 1). El tráfico legítimo es simétrico: el servidor responde con volumen similar al que recibe.
- **Grupo B:** pico pronunciado en log₁₀=1.78 (ratio ≈ 60). Los ataques de inundación envían muchos bytes al servidor pero **reciben respuesta mínima o nula** — el servidor descarta los paquetes de flood o responde con RST mínimo.
- **Es la diferencia más visible de toda la Figura 1:** las dos distribuciones están casi completamente separadas. Mediana A=0.96, mediana B=60.00, ratio=**62.8×**.
- **Implicación:** byte_ratio es el principal discriminador del modelo. Un valor > 5 es señal fuerte de anomalía.

### `avg_pkt_size` (tamaño promedio de paquete en bytes)
- **Grupo A:** pico en log₁₀=2.13 (≈ 134 bytes). HTTP/SSH tiene paquetes de tamaño moderado con payload de datos.
- **Grupo B:** pico en log₁₀=1.78 (≈ 60 bytes). Los paquetes de flood son mínimos — solo cabecera IP+TCP sin payload útil. El tamaño 60 bytes es el mínimo de un paquete TCP/IP.
- **Implicación:** avg_pkt_size bajo combinado con byte_ratio alto es un patrón muy característico de los ataques de inundación.

---

## Figura 2 — Boxplots Grupo A vs. Grupo B en escala log₁₀

**¿Qué muestra?** Cajas de cuartiles (Q1–Q3), medianas y outliers para 6 features, comparando directamente Grupo A (azul) vs. Grupo B (rojo/salmón).

**Interpretación boxplot por boxplot:**

### `pkt_rate`
- **A:** caja amplia (IQR grande), mediana=327 pkt/s — el tráfico normal varía mucho.
- **B:** caja pequeña y concentrada, mediana=1,000 pkt/s — los ataques de flood tienen tasa constante (límite del hping3).
- **Lectura:** la caja B está más arriba y es mucho más estrecha que A. A tiene más outliers superiores (transferencias intensas ocasionales).

### `byte_rate`
- **A:** caja muy amplia (IQR = 1,909 a 199,226 B/s), mediana=40,543 B/s.
- **B:** caja más estrecha con mediana=60,000 B/s pero varios outliers superiores (ataques como UDP flood a alta velocidad alcanzan 1.6 MB/s).
- **Lectura:** las medianas se solapan — byte_rate sola no basta, pero su combinación con byte_ratio sí discrimina.

### `duration`
- **A:** caja amplia entre log₁₀=−2.4 y 0 (0.004 s a 1 s), con cola larga hacia arriba (sesiones SSH largas).
- **B:** caja extremadamente compacta en log₁₀=−3 (≈ 0 s), mediana=0.00 s. Los flows de flood son prácticamente instantáneos.
- **Lectura:** esta es la diferencia de caja **más visible** del boxplot después de byte_ratio — duration discrimina muy bien.

### `pkt_ratio`
- **A:** mediana=1.17, caja pequeña y centrada en 0.
- **B:** mediana=1.00, caja igualmente pequeña.
- **Lectura:** cajas muy parecidas, casi imposible distinguir visualmente. Confirma que pkt_ratio es la feature menos discriminante, pero pasa el test estadístico (p < 0.001) porque hay diferencias en los extremos.

### `byte_ratio` ← **la más importante**
- **A (azul):** caja diminuta centrada en log₁₀=−0.02 (ratio≈1). El IQR de A va de 0.94 a 1.37 — la gran mayoría del tráfico normal tiene ratio casi exactamente 1.
- **B (rojo/salmón):** caja **muy grande** que abarca log₁₀=0.3 a 1.78 (ratio 2 a 60). La mediana es log₁₀=1.78 (ratio=60). El cuartil inferior (Q1) de B ya supera la mediana de A.
- **Lectura:** esta es la diferencia de cajas más contrastante de todo el gráfico. La caja B no se solapa con la caja A — hay separación clara en los cuartiles. Esto justifica por qué byte_ratio tiene el mayor peso en el modelo Isolation Forest.

### `avg_pkt_size`
- **A:** mediana=134.75 bytes, distribución algo más ancha.
- **B:** mediana=60.00 bytes, caja estrecha — casi todos los paquetes de flood pesan exactamente 60 bytes.
- **Lectura:** A está notablemente más arriba que B. La diferencia es clara pero no tan extrema como byte_ratio.

---

## Figura 3 — Distribución de protocolos por grupo

**¿Qué muestra?** Barras apiladas con el porcentaje de flows TCP, UDP e ICMP en cada grupo.

**Interpretación:**

### Grupo A — Normal (n=67,135)
- **TCP: 99.6%** — el tráfico legítimo en esta red es casi exclusivamente TCP. HTTP (:80, :8080) y SSH (:22) son los servicios del servidor. No hay servicios UDP relevantes (no hay DNS propio, no hay streaming).
- **UDP: 0.4%** — mínimo residual. Puede ser tráfico de resolución DNS, NTP u otros servicios de sistema.
- **ICMP: ~0%** — sin pings ni mensajes de control en el tráfico normal de usuario.

### Grupo B — Anómalo (n=302,892)
- **TCP: 59.4%** — sigue siendo mayoría porque SYN flood (B1), port scan TCP (B2) y brute force SSH (B6) usan TCP.
- **UDP: 21.9%** — udp_flood (B3, hping3 --udp al puerto :53) genera un volumen alto de flows UDP.
- **ICMP: 18.7%** — icmp_flood (B4, hping3 -1 --flood) genera miles de flows ICMP que Suricata registra individualmente.
- **Interpretación clave:** la **diversidad de protocolos** es un indicador de anomalía. Un sensor que ve de repente 20% UDP y 19% ICMP en su tráfico (vs. el 0% habitual) debe elevar la sospecha inmediatamente.

### Grupo C — Mixto (n=31,397)
- **TCP: 96.8%** — dominado por el tráfico normal del Desktop. El tráfico anómalo (SYN flood, port scan) también aporta TCP, pero el volumen del normal es mayor en este grupo.
- **UDP+ICMP: ~3.2%** — aportes pequeños del componente anómalo.
- **Implicación:** en el escenario C (mixto) las features de protocolo solas no bastan — el componente anómalo queda "enmascarado" por el tráfico normal. Aquí el motor necesita el score IF sobre flows individuales, no estadísticas agregadas de protocolo.

**Implicación para el modelo:**
Las features `is_tcp`, `is_udp`, `is_icmp` funcionan mejor en escenarios B puros. En escenarios C el motor debe apoyarse principalmente en byte_ratio y pkt_rate de cada flow individual.

---

## Figura 4 — Heatmap de correlación Pearson (14×14)

**¿Qué muestra?** Dos matrices de correlación Pearson: izquierda = Grupo A (Normal), derecha = Grupo B (Anómalo). Colores: rojo oscuro = correlación positiva fuerte (r≈1), azul oscuro = correlación negativa fuerte (r≈−1), blanco = sin correlación (r≈0).

**Interpretación Grupo A (Normal) — izquierda:**

- **Bloque de volumen (pkts_toserver, pkts_toclient, bytes_toserver, bytes_toclient):** correlación positiva muy alta (r > 0.9, cuadrado rojo oscuro en la esquina superior izquierda). En tráfico legítimo HTTP/SSH, si el cliente envía muchos paquetes, el servidor también responde con muchos — la comunicación es bidireccional y proporcional.
- **pkt_rate y byte_rate:** correlacionados con las features de volumen (r ≈ 0.6–0.8). A mayor volumen total, mayor tasa.
- **byte_ratio y pkt_ratio:** correlación **negativa** con bytes_toclient (cuadrado azul). Si el servidor responde mucho (bytes_toclient alto), el ratio bytes_toserver/bytes_toclient cae — lógico.
- **duration:** correlación positiva moderada con las features de volumen. Los flows más largos acumulan más bytes.
- **is_tcp, is_udp, is_icmp:** prácticamente sin correlación con el resto (valores cercanos a 0, color blanco). El tipo de protocolo no predice el volumen en tráfico normal.
- **dest_port:** sin correlación significativa con el resto.

**Interpretación Grupo B (Anómalo) — derecha:**

- **La estructura cambia completamente:** el bloque rojo del Grupo A desaparece. pkts_toclient y bytes_toclient están cercanos a 0 en los ataques de flood (el servidor no responde o responde mínimo), lo que **rompe la correlación** entre toserver y toclient.
- **pkts_toserver y bytes_toserver:** siguen correlacionados entre sí (r > 0.7) porque el atacante manda paquetes de tamaño fijo (60 bytes).
- **byte_ratio:** muestra ahora correlación positiva con pkts_toserver y bytes_toserver (más envíos = mayor ratio), y correlación negativa muy fuerte con bytes_toclient (si el servidor no responde, el ratio sube). Este patrón es **opuesto** al Grupo A.
- **pkt_rate:** correlación positiva con pkts_toserver — en flood el rate sube con el volumen enviado.
- **is_udp e is_icmp:** en B sí tienen correlación con algunas features de volumen (los floods UDP e ICMP tienen patrones de volumen específicos).

**Implicación para el modelo:**
El Isolation Forest aprende implícitamente que en tráfico normal existe alta correlación entre bytes_toserver y bytes_toclient. Cuando llega un flow de flood donde bytes_toclient ≈ 0 y bytes_toserver > 0, el IF lo identifica como "difícil de aislar" (score bajo) porque viola la estructura de correlaciones aprendida.

---

## Figura 5 — Top-10 puertos de destino por grupo

**¿Qué muestra?** Barras horizontales con los 10 puertos de destino más frecuentes en cada grupo, ordenados por número de flows.

**Interpretación:**

### Grupo A — Normal
- **Puerto 8080 (11,134 flows):** el servidor objetivo tiene nginx también en :8080 (HTTP alternativo). La mayoría de los scripts de escenario A1/A4 usaron `curl http://192.168.0.120:8080` por defecto.
- **Puerto 22 (508 flows):** tráfico SSH legítimo (escenarios A2 y A4).
- **Puerto 80 (261 flows):** HTTP estándar, menor proporción que 8080.
- **Resto de puertos (< 60 flows cada uno):** puertos efímeros del lado cliente que Suricata captura como destino en algunos flows. Muy baja frecuencia.
- **Concentración:** los 3 primeros puertos concentran el 98.5% de los flows. El tráfico normal es **altamente predecible y concentrado** en los servicios conocidos.

### Grupo B — Anómalo
- **Puerto 80 (8,030 flows):** SYN flood (B1) y HTTP abuse (B5) van a :80. Es el puerto más atacado.
- **Puerto 53 (3,199 flows):** UDP flood (B3) apuntaba al puerto DNS :53 del servidor. Suricata captura cada datagrama UDP como un flow independiente.
- **Puerto 0 (2,847 flows):** el ICMP flood (B4) no usa puerto de transporte, pero Suricata asigna dest_port=0 para los flows ICMP. Estos 2,847 flows corresponden al icmp_flood.
- **Puerto 22 (433 flows):** brute force SSH (B6) con hydra.
- **Resto (< 15 flows cada uno):** puertos aleatorios del port scan (B2 — nmap -sS escanea múltiples puertos pero con muy pocos paquetes por puerto).
- **Distribución:** más dispersa que A, pero los 4 primeros puertos concentran el 97% del tráfico. Los ataques son predecibles en sus puertos objetivo.

### Grupo C — Mixto
- **Puerto 80 (5,102 flows):** dominante — aportes del HTTP normal (Desktop) más el SYN flood (Kali).
- **Puerto 22 (2,358 flows):** SSH legítimo (Desktop) en escenarios C2.
- **Puerto 8080 (2,161 flows):** HTTP normal del Desktop hacia el puerto alternativo.
- **Puerto 53 (323 flows):** UDP flood del componente anómalo.
- **Puerto 0 — ICMP (119 flows):** aportes del flood ICMP.
- **Implicación:** en C el puerto destino ya no discrimina — tanto el :80 normal como el :80 del SYN flood aparecen mezclados. El motor debe usar las features de volumen y ratio, no solo el puerto.

**Implicación para el modelo:**
`dest_port` como feature numérica contribuye al Isolation Forest de forma limitada — el puerto :80 aparece en tráfico normal y anómalo. Su valor real está en combinación: dest_port=80 + byte_ratio=60 es muy diferente a dest_port=80 + byte_ratio=1.

---

## Figura 6 — Estadísticas descriptivas de las 14 features por grupo

**¿Qué muestra?** Tabla resumen con media, mediana, skewness (asimetría), ratio de medianas (B/A) y una indicación de discriminabilidad para cada feature. Las celdas en rosa/salmón destacan los ratios extremos.

**Interpretación fila por fila:**

| Feature | A mediana | B mediana | Ratio | Interpretación |
|---|---|---|---|---|
| `pkts_toserver` | 7 | 1 | 0.1× | B envía **menos** paquetes al servidor (floods son ráfagas cortas), pero muy rápido |
| `pkts_toclient` | 5 | 0 | 0.0× | El servidor prácticamente **no responde** en los ataques de flood — señal fuerte |
| `bytes_toserver` | 790 | 60 | 0.1× | B envía paquetes mínimos (60 bytes = cabecera TCP sin payload) |
| `bytes_toclient` | 826 | 0 | 0.0× | **Sin respuesta del servidor** — bytes_toclient≈0 es marca de flood |
| `duration` | 0.04 s | 0.00 s | 0.0× | Flows de flood duran milisegundos (no completan handshake) |
| `pkt_rate` | 327 pkt/s | 1,000 pkt/s | 3.1× | Tasa 3× mayor en ataques — discriminante pero con solapamiento |
| `byte_rate` | 40,543 B/s | 60,000 B/s | 1.5× | Diferencia menor — los floods son rápidos pero con paquetes mínimos |
| `pkt_ratio` | 1.17 | 1.00 | 0.9× | Casi idéntico — la **menos discriminante** de las 14 features |
| **`byte_ratio`** | **0.96** | **60.00** | **62.8×** | **Feature más discriminante** — resaltada en el gráfico (rosa intenso) |
| `avg_pkt_size` | 134.75 | 60.00 | 0.4× | Paquetes anómalos son mini (solo cabecera), los normales tienen payload |

**Columna "Discrimina":** todas las 14 features muestran el checkmark (✓ o similar), confirmando p < 0.001 en el test Mann-Whitney U. Ninguna feature fue descartada.

**Skewness (asimetría):**
- Grupo A tiene skewness extremadamente alta en casi todas las features (≥ 166–259). Esto indica distribuciones con cola muy larga a la derecha — la mayoría de flows normales son "pequeños" pero hay outliers grandes (transferencias intensas, sesiones largas).
- Grupo B tiene skewness de 2–36 — más moderada. Los ataques de flood son más uniformes en sus valores.
- Esta diferencia de skewness es otra razón por la que Isolation Forest funciona bien aquí: el algoritmo aísla los puntos en las colas largas, y el tráfico normal tiene muchos puntos en esas colas (por eso FPR=20.47%).

**Implicación crítica — FPR del modelo:**
El FPR=20.47% se explica directamente por esta tabla. Los flows legítimos con valores extremos (transferencias grandes → bytes_toserver alto → byte_ratio alto) quedan en la zona de puntuación baja del IF. La whitelist de IPs internas mitiga este efecto: aunque el motor les asigne score bajo, no los bloquea.

---

## Síntesis: Jerarquía de features discriminantes

Ordenadas por poder de discriminación (de mayor a menor):

1. **`byte_ratio`** — 62.8× de diferencia entre medianas. Primer discriminador sin ambigüedad.
2. **`pkts_toclient` / `bytes_toclient`** — valor 0 en floods es señal casi definitiva de ataque.
3. **`duration`** — 0.00 s en B vs. 0.04 s en A. Flows de flood no completan handshake.
4. **`avg_pkt_size`** — 60 bytes en B (mínimo TCP) vs. 134 bytes en A (con payload).
5. **`pkt_rate`** — 3.1× mayor en B, pero con solapamiento en tráfico normal sostenido.
6. **`byte_rate`** — 1.5× mayor en B, con solapamiento considerable.
7. **`is_udp` / `is_icmp`** — 0% en A, 21.9% / 18.7% en B. Discrimina por tipo de escenario.
8. **`pkt_ratio`** — 0.9× (casi idéntico). Menos útil de forma individual.

El Isolation Forest aprovecha **la combinación** de todas estas señales: un flow con byte_ratio=60 + pkts_toclient=0 + duration=0.001 s obtendrá un score muy bajo (< −0.60) con alta confianza, independientemente de cómo se comporten las features menos discriminantes.

---

*Documento generado el 2026-06-19 como complemento al informe de resultados.*
*Fuente de datos: `results/eda/eda_stats_completas.txt` y `results/eda/*.png`*
