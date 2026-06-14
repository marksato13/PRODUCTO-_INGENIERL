#!/usr/bin/env python3
"""
Fase 2 — Etiquetado y limpieza del dataset
dataset_raw.csv → dataset_labeled.csv → dataset_clean.csv

Etiquetado:
  - Reconfirma label usando src_ip: flujos de Desktop (192.168.0.20) → label=0
  - Flujos de Kali (192.168.0.100) o IPs random → label=1
  - Flujos ambiguos (src_ip en ambas zonas) → se resuelve por escenario

Limpieza:
  - Elimina duplicados por flow_id
  - Elimina flows con pkts_toserver=0
  - Elimina IPs inválidas (broadcast, multicast, 0.0.0.0)
  - Valida tipos de dato
  - Reporta estadísticos finales
"""

import csv
import os
import ipaddress
from collections import defaultdict

DATA_DIR  = "/home/m4rk/ppi-surikata-producto/data"
RAW_CSV   = f"{DATA_DIR}/dataset_raw.csv"
LABEL_CSV = f"{DATA_DIR}/dataset_labeled.csv"
CLEAN_CSV = f"{DATA_DIR}/dataset_clean.csv"

NORMAL_IPS = {"192.168.0.20", "192.168.0.120"}
KALI_IP    = "192.168.0.100"


def es_ip_valida(ip):
    try:
        obj = ipaddress.ip_address(ip)
        return not (obj.is_unspecified or obj.is_multicast or obj.is_reserved
                    or str(obj).endswith(".255")
                    or obj == ipaddress.ip_address("255.255.255.255"))
    except ValueError:
        return False


def reetiqueta(row):
    """Refina label usando src_ip real del flow."""
    src = row["src_ip"]
    escenario = row["escenario"]

    # Flujo iniciado por Desktop → siempre normal
    if src in NORMAL_IPS and "normal" in escenario:
        return "0"
    # Flujo iniciado por Kali → siempre anómalo
    if src == KALI_IP:
        return "1"
    # IPs random en floods (synflood/udpflood/icmpflood con --rand-source)
    if "anom" in escenario or "mixto" in escenario:
        return "1"
    # Desktop en escenarios mixtos → normal (tráfico legítimo del mixto)
    if src in NORMAL_IPS and "mixto" in escenario:
        return "0"
    # Fallback al label original
    return row["label"]


# ── PASO 1: dataset_labeled.csv ──────────────────────────────
print("=" * 60)
print("PASO 1 — Etiquetado refinado → dataset_labeled.csv")
print("=" * 60)

total_raw = 0
label_cambiados = 0

with open(RAW_CSV, "r", encoding="utf-8") as fin, \
     open(LABEL_CSV, "w", newline="", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)
    campos = reader.fieldnames
    writer = csv.DictWriter(fout, fieldnames=campos)
    writer.writeheader()

    for row in reader:
        total_raw += 1
        nuevo_label = reetiqueta(row)
        if nuevo_label != row["label"]:
            label_cambiados += 1
        row["label"] = nuevo_label
        writer.writerow(row)

print(f"  Total filas procesadas : {total_raw:,}")
print(f"  Labels refinados       : {label_cambiados:,}")
print(f"  Guardado en            : {LABEL_CSV}")
print()

# ── PASO 2: dataset_clean.csv ────────────────────────────────
print("=" * 60)
print("PASO 2 — Limpieza → dataset_clean.csv")
print("=" * 60)

seen_ids    = set()
stats = defaultdict(int)

with open(LABEL_CSV, "r", encoding="utf-8") as fin, \
     open(CLEAN_CSV, "w", newline="", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()

    for row in reader:
        stats["total"] += 1

        # 1. Eliminar duplicados por flow_id
        fid = row.get("flow_id", "")
        if fid and fid in seen_ids:
            stats["dup_flowid"] += 1
            continue
        if fid:
            seen_ids.add(fid)

        # 2. Eliminar flows sin paquetes al servidor
        try:
            if int(row.get("pkts_toserver", 0) or 0) == 0:
                stats["pkts_cero"] += 1
                continue
        except ValueError:
            stats["tipo_invalido"] += 1
            continue

        # 3. Eliminar IPs inválidas (broadcast, multicast, 0.0.0.0)
        src = row.get("src_ip", "")
        dst = row.get("dest_ip", "")
        if not es_ip_valida(src) or not es_ip_valida(dst):
            stats["ip_invalida"] += 1
            continue

        # 4. Validar campos numéricos
        try:
            float(row.get("bytes_toserver", 0) or 0)
            float(row.get("bytes_toclient", 0) or 0)
            float(row.get("duration", 0) or 0)
        except (ValueError, TypeError):
            stats["tipo_invalido"] += 1
            continue

        # 5. Eliminar timestamps vacíos
        if not row.get("timestamp") or not row.get("flow_start"):
            stats["timestamp_vacio"] += 1
            continue

        stats["conservados"] += 1
        lbl = int(row.get("label", 0))
        if lbl == 0:
            stats["label_0"] += 1
        else:
            stats["label_1"] += 1

        writer.writerow(row)

# ── Estadísticos finales ──────────────────────────────────────
print(f"  Filas entrada          : {stats['total']:>10,}")
print(f"  Duplicados eliminados  : {stats['dup_flowid']:>10,}")
print(f"  pkts_toserver=0        : {stats['pkts_cero']:>10,}")
print(f"  IPs invalidas          : {stats['ip_invalida']:>10,}")
print(f"  Tipo invalido          : {stats['tipo_invalido']:>10,}")
print(f"  Timestamp vacio        : {stats['timestamp_vacio']:>10,}")
print(f"  ─────────────────────────────────────")
print(f"  Filas conservadas      : {stats['conservados']:>10,}")
print()
print(f"  Label=0 (normal)       : {stats['label_0']:>10,}  ({100*stats['label_0']/max(stats['conservados'],1):.1f}%)")
print(f"  Label=1 (anomalo)      : {stats['label_1']:>10,}  ({100*stats['label_1']/max(stats['conservados'],1):.1f}%)")
print()

# ── Estadísticos por escenario ────────────────────────────────
print("  Distribución por escenario:")
print(f"  {'Escenario':<30} {'Flows':>8} {'Label':>6}")
print(f"  {'-'*46}")

escenario_stats = defaultdict(lambda: [0, 0])
with open(CLEAN_CSV, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        esc = row["escenario"]
        lbl = int(row["label"])
        escenario_stats[esc][lbl] += 1

for esc in sorted(escenario_stats.keys()):
    n0, n1 = escenario_stats[esc]
    total_esc = n0 + n1
    lbl_str = "0 (normal)" if n0 > n1 else "1 (anom)"
    print(f"  {esc:<30} {total_esc:>8,}  {lbl_str}")

print()
print(f"  Guardado en: {CLEAN_CSV}")
print("=" * 60)
