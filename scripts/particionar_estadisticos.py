#!/usr/bin/env python3
"""
Fase 2 — Partición temporal y estadísticos del dataset
dataset_clean.csv → train.csv / val.csv / test.csv + resumen_estadistico.txt

Partición cronológica (sin mezcla temporal):
  70% train | 15% val | 15% test
  Se mantiene orden temporal para evitar fuga de datos.
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data"
CLEAN_CSV  = f"{DATA_DIR}/dataset_clean.csv"
TRAIN_CSV  = f"{DATA_DIR}/train.csv"
VAL_CSV    = f"{DATA_DIR}/val.csv"
TEST_CSV   = f"{DATA_DIR}/test.csv"
REPORT_TXT = f"{DATA_DIR}/resumen_estadistico.txt"

TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
# test = 1 - train - val = 0.15

# ── Leer y ordenar cronológicamente ──────────────────────────
print("Leyendo dataset_clean.csv ...")
filas = []
with open(CLEAN_CSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    campos = reader.fieldnames
    for row in reader:
        filas.append(row)

# Ordenar por timestamp
filas.sort(key=lambda r: r.get("timestamp", ""))
N = len(filas)
print(f"  Total flows: {N:,}")

# ── Partición ────────────────────────────────────────────────
n_train = int(N * TRAIN_RATIO)
n_val   = int(N * VAL_RATIO)
n_test  = N - n_train - n_val

train_rows = filas[:n_train]
val_rows   = filas[n_train:n_train + n_val]
test_rows  = filas[n_train + n_val:]

def escribir_csv(path, rows, campos):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(rows)

escribir_csv(TRAIN_CSV, train_rows, campos)
escribir_csv(VAL_CSV,   val_rows,   campos)
escribir_csv(TEST_CSV,  test_rows,  campos)

def contar_labels(rows):
    c = defaultdict(int)
    for r in rows:
        c[int(r["label"])] += 1
    return c

tc = contar_labels(train_rows)
vc = contar_labels(val_rows)
sc = contar_labels(test_rows)

print(f"\n  Train : {len(train_rows):>7,}  (label0={tc[0]:,}  label1={tc[1]:,})")
print(f"  Val   : {len(val_rows):>7,}  (label0={vc[0]:,}  label1={vc[1]:,})")
print(f"  Test  : {len(test_rows):>7,}  (label0={sc[0]:,}  label1={sc[1]:,})")

# ── Estadísticos globales ────────────────────────────────────
def stats_campo(rows, campo):
    vals = []
    for r in rows:
        try:
            v = float(r.get(campo, 0) or 0)
            vals.append(v)
        except (ValueError, TypeError):
            pass
    if not vals:
        return 0, 0, 0, 0, 0
    vals.sort()
    n = len(vals)
    media = sum(vals) / n
    var   = sum((x - media)**2 for x in vals) / n
    std   = var ** 0.5
    return min(vals), vals[n//4], media, vals[3*n//4], max(vals)

campos_num = ["bytes_toserver", "bytes_toclient", "pkts_toserver",
              "pkts_toclient", "duration"]

# Estadísticos por label
stats_por_label = {}
for lbl in [0, 1]:
    subset = [r for r in filas if int(r["label"]) == lbl]
    stats_por_label[lbl] = {}
    for c in campos_num:
        stats_por_label[lbl][c] = stats_campo(subset, c)

# Distribución de protocolos
proto_count = defaultdict(int)
for r in filas:
    proto_count[r.get("proto", "?")] += 1

# Distribución por escenario
esc_count = defaultdict(lambda: [0, 0])
for r in filas:
    esc = r.get("escenario", "?")
    lbl = int(r.get("label", 0))
    esc_count[esc][lbl] += 1

# ── Generar resumen_estadistico.txt ──────────────────────────
hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
sep = "=" * 65

lines = [
    sep,
    "RESUMEN ESTADÍSTICO DEL DATASET — FASE 2",
    "Sistema de Detección Temprana de Anomalías de Red",
    "PPI — Universidad Peruana Unión 2026",
    f"Generado: {hoy}",
    sep, "",
    "1. COMPOSICIÓN GENERAL",
    "-" * 40,
    f"   Archivo fuente  : dataset_clean.csv",
    f"   Total flows     : {N:,}",
    f"   Label=0 Normal  : {sum(1 for r in filas if r['label']=='0'):,}  ({100*sum(1 for r in filas if r['label']=='0')/N:.1f}%)",
    f"   Label=1 Anomalo : {sum(1 for r in filas if r['label']=='1'):,}  ({100*sum(1 for r in filas if r['label']=='1')/N:.1f}%)",
    "",
    "2. PARTICIÓN TEMPORAL (70/15/15)",
    "-" * 40,
    f"   {'Conjunto':<10} {'Flows':>8} {'Normal':>8} {'Anomalo':>8} {'%Normal':>8}",
    f"   {'-'*46}",
    f"   {'Train':<10} {len(train_rows):>8,} {tc[0]:>8,} {tc[1]:>8,} {100*tc[0]/len(train_rows):>7.1f}%",
    f"   {'Val':<10} {len(val_rows):>8,} {vc[0]:>8,} {vc[1]:>8,} {100*vc[0]/len(val_rows):>7.1f}%",
    f"   {'Test':<10} {len(test_rows):>8,} {sc[0]:>8,} {sc[1]:>8,} {100*sc[0]/len(test_rows):>7.1f}%",
    "",
    "3. DISTRIBUCIÓN DE PROTOCOLOS",
    "-" * 40,
]
for proto, cnt in sorted(proto_count.items(), key=lambda x: -x[1]):
    lines.append(f"   {proto:<10} : {cnt:>8,}  ({100*cnt/N:.1f}%)")

lines += [
    "",
    "4. DISTRIBUCIÓN POR ESCENARIO",
    "-" * 65,
    f"   {'Escenario':<30} {'Total':>8} {'Normal':>8} {'Anomalo':>8}",
    f"   {'-'*56}",
]
for esc in sorted(esc_count.keys()):
    n0, n1 = esc_count[esc]
    lines.append(f"   {esc:<30} {n0+n1:>8,} {n0:>8,} {n1:>8,}")

lines += [
    "",
    "5. ESTADÍSTICOS POR CLASE Y FEATURE",
    "-" * 65,
]
for lbl, nombre in [(0, "NORMAL (label=0)"), (1, "ANOMALO (label=1)")]:
    lines.append(f"   {nombre}")
    lines.append(f"   {'Feature':<22} {'Min':>10} {'Q1':>10} {'Media':>10} {'Q3':>10} {'Max':>10}")
    lines.append(f"   {'-'*62}")
    for c in campos_num:
        mn, q1, med, q3, mx = stats_por_label[lbl][c]
        lines.append(f"   {c:<22} {mn:>10.2f} {q1:>10.2f} {med:>10.2f} {q3:>10.2f} {mx:>10.2f}")
    lines.append("")

lines += [
    "6. VENTANA TEMPORAL",
    "-" * 40,
    f"   Primer timestamp : {filas[0].get('timestamp','')[:19]}",
    f"   Ultimo timestamp : {filas[-1].get('timestamp','')[:19]}",
    "",
    sep,
]

texto = "\n".join(lines)
with open(REPORT_TXT, "w") as f:
    f.write(texto)

print()
print(texto)
print(f"\nArchivos generados:")
print(f"  {TRAIN_CSV}")
print(f"  {VAL_CSV}")
print(f"  {TEST_CSV}")
print(f"  {REPORT_TXT}")
