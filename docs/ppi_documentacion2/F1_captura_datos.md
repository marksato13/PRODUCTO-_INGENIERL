# F1 — Captura y Preparación de Datos
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Convertir el tráfico de red crudo en un dataset estructurado y limpio listo para entrenar el modelo de detección.

---

## Componentes

| Script | Función |
|---|---|
| Suricata 7.0.3 en ens35 | Captura flujos → eve.json |
| `scripts/parser.py` | eve.json.gz → dataset_raw.csv |
| `scripts/etiquetar_limpiar.py` | dedup, filtros IP, etiquetas normal/anómalo |
| `scripts/particionar_estadisticos.py` | split cronológico 70/15/15 |

---

## Escenarios de tráfico capturados

### Grupo A — Normal (desde Desktop 192.168.0.20)
| ID | Escenario | Duración | Herramienta |
|---|---|---|---|
| A1 | http_normal | 10 min | curl/wget → :80 |
| A2 | ssh_legitimo | 8 min | ssh → :22 |
| A3 | transferencia_legitima | 10 min | scp/wget |
| A4 | trafico_sostenido | 15 min | curl+ssh mixto |

### Grupo B — Anómalo (desde Kali 192.168.0.100)
| ID | Escenario | Herramienta |
|---|---|---|
| B1 | syn_flood | hping3 -S --flood → :80 |
| B2 | port_scan | nmap -sS |
| B3 | udp_flood | hping3 --udp --flood → :53 |
| B4 | icmp_flood | hping3 -1 --flood |
| B5 | acceso_repetitivo | curl bucle → :80 |
| B6 | bruteforce_ssh | hydra → :22 |

### Grupo C — Mixto (Desktop + Kali simultáneos)
| ID | Escenario |
|---|---|
| C1 | http_syn |
| C2 | ssh_portscan |
| C3 | descarga_udp |

---

## Features del dataset (14)

```
pkts_toserver    pkts_toclient    bytes_toserver   bytes_toclient
duration         pkt_rate         byte_rate        pkt_ratio
byte_ratio       avg_pkt_size     is_tcp           is_udp
is_icmp          dest_port
```

---

## Rutas en el sensor (192.168.0.110)

```
/home/m4rk/ppi-surikata-producto/
├── data/
│   ├── raw/          ← capturas YYYYMMDD_grupo_escenario_NN_eve.json.gz
│   ├── dataset_clean.csv
│   ├── train.csv     ← 70%
│   ├── val.csv       ← 15%
│   └── test.csv      ← 15%
└── scripts/
    ├── capture/exportar_eve_por_escenario.sh
    └── evaluation/registrar_bitacora.sh
```

---

## Métricas y resultados

- Capturas totales: 47 archivos eve.json.gz
- Split: cronológico (no aleatorio — respeta orden temporal)
- Balance del dataset: normal vs anómalo representados
- Nomenclatura: `YYYYMMDD_grupo_escenario_NN_eve.json.gz`

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] eve.json capturado correctamente por Suricata en ens35
- [x] Dataset limpio sin duplicados ni IPs de whitelist
- [x] Split cronológico 70/15/15 sin data leakage
- [x] 14 features extraídas y normalizadas
- [x] Bitácora de corridas registrada

---

## Inconsistencias conocidas / resueltas

- Suricata TCP timeout: flujos SYN flood medio-abiertos demoran ~60s en cerrar → normal para este protocolo
- eve.json se rota con `suricatasc reopen-log-files` al final de cada corrida
