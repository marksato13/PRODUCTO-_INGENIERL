# F1 — Captura de Datos
**Estado: ✅ COMPLETA Y VALIDADA**

---

## Objetivo

Registrar tráfico de red real bajo escenarios controlados (normal y anómalo) y almacenarlo como capturas brutas listas para el entrenamiento del modelo.

---

## Cómo funciona

F1 es trabajo de laboratorio, no de scripts. Suricata captura pasivamente todo el tráfico y lo escribe en `eve.json`. Al finalizar cada corrida, el archivo se comprime y archiva.

```
Red → Suricata 7.0.3 (ens35, modo pasivo) → eve.json
                                                │
                               exportar_eve_por_escenario.sh
                                                │
                                    data/raw/YYYYMMDD_grupo_escenario_NN_eve.json.gz
```

**No hay scripts de parseo en esta fase.** La extracción de features ocurre en F2.

---

## Scripts de soporte de capturas

| Script | Función |
|---|---|
| `scripts/capture/exportar_eve_por_escenario.sh` | Comprime eve.json → .gz, rota el log con `suricatasc reopen-log-files` |
| `scripts/evaluation/registrar_bitacora.sh` | Escribe línea en bitácora al finalizar cada corrida |

---

## Escenarios capturados

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
| B5 | acceso_repetitivo (HTTP Abuse) | curl bucle → :80 |
| B6 | bruteforce_ssh | hydra → :22 |

### Grupo C — Mixto (Desktop + Kali simultáneos)
| ID | Escenario |
|---|---|
| C1 | http_syn |
| C2 | ssh_portscan |
| C3 | descarga_udp |

---

## Output real de F1

```
/home/m4rk/ppi-surikata-producto/data/raw/
    47 archivos .json.gz
    Ejemplos:
      20260602_normal_http_01_eve.json.gz
      20260602_anom_synflood_01_eve.json.gz
      20260616_mixto_http_synflood_01_eve.json.gz
```

**Esta es la única salida de F1.** Los archivos .gz son la entrada de F2.

---

## Criterios de aceptación — CUMPLIDOS ✅

- [x] Suricata capturando en ens35 en modo pasivo
- [x] 47 capturas almacenadas con nomenclatura correcta
- [x] Grupos A, B y C representados
- [x] eve.json rotado correctamente al finalizar cada corrida
- [x] Bitácora de corridas registrada

---

## Nota sobre la separación F1/F2

F1 termina con los archivos `.gz` en `data/raw/`. F2 comienza leyendo esos archivos para extraer features y entrenar el modelo. No hay archivos CSV intermedios entre F1 y F2.
