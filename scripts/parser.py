#!/usr/bin/env python3
"""
Fase 2 — Parser EVE JSON → dataset_raw.csv
Lee todos los archivos eve.json(.gz) de data/raw/, filtra eventos 'flow',
extrae columnas estándar y asigna label según nombre de archivo.
label=0: tráfico normal | label=1: tráfico anómalo o mixto
"""

import json
import gzip
import glob
import csv
import os
from datetime import datetime, timezone

DATA_DIR   = "/home/m4rk/ppi-surikata-producto/data/raw"
OUTPUT_CSV = "/home/m4rk/ppi-surikata-producto/data/dataset_raw.csv"

COLUMNAS = [
    "timestamp", "flow_id", "src_ip", "src_port",
    "dest_ip", "dest_port", "proto", "app_proto",
    "bytes_toserver", "bytes_toclient",
    "pkts_toserver", "pkts_toclient",
    "flow_start", "flow_end", "duration",
    "escenario", "corrida", "label"
]


def inferir_label(nombre_archivo):
    """0 = normal, 1 = anómalo o mixto."""
    n = nombre_archivo.lower()
    if "_normal_" in n:
        return 0
    return 1


def inferir_escenario(nombre_archivo):
    """Extrae grupo_escenario del nombre: YYYYMMDD_grupo_escenario_NN_eve.json.gz"""
    partes = nombre_archivo.replace("_eve.json.gz", "").replace("_eve.json", "").split("_")
    if len(partes) >= 4:
        return f"{partes[1]}_{partes[2]}"
    return "desconocido"


def inferir_corrida(nombre_archivo):
    partes = nombre_archivo.replace("_eve.json.gz", "").replace("_eve.json", "").split("_")
    if len(partes) >= 4:
        return partes[3]
    return "01"


def flow_duration(e):
    try:
        t0 = datetime.fromisoformat(e["flow"]["start"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(e["flow"]["end"].replace("Z", "+00:00"))
        return round(max((t1 - t0).total_seconds(), 0.0), 3)
    except Exception:
        return 0.0


def parsear_archivo(path):
    nombre = os.path.basename(path)
    label  = inferir_label(nombre)
    escenario = inferir_escenario(nombre)
    corrida   = inferir_corrida(nombre)

    registros = []
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", errors="ignore") as f:
        for line in f:
            try:
                e = json.loads(line.strip())
            except Exception:
                continue

            if e.get("event_type") != "flow":
                continue

            flow = e.get("flow", {})
            dur  = flow_duration(e)

            registros.append({
                "timestamp":      e.get("timestamp", ""),
                "flow_id":        e.get("flow_id", ""),
                "src_ip":         e.get("src_ip", ""),
                "src_port":       e.get("src_port", ""),
                "dest_ip":        e.get("dest_ip", ""),
                "dest_port":      e.get("dest_port", ""),
                "proto":          e.get("proto", ""),
                "app_proto":      e.get("app_proto", ""),
                "bytes_toserver": flow.get("bytes_toserver", 0) or 0,
                "bytes_toclient": flow.get("bytes_toclient", 0) or 0,
                "pkts_toserver":  flow.get("pkts_toserver", 0) or 0,
                "pkts_toclient":  flow.get("pkts_toclient", 0) or 0,
                "flow_start":     flow.get("start", ""),
                "flow_end":       flow.get("end", ""),
                "duration":       dur,
                "escenario":      escenario,
                "corrida":        corrida,
                "label":          label,
            })
    return registros


def main():
    archivos = sorted(
        glob.glob(f"{DATA_DIR}/*.gz") +
        glob.glob(f"{DATA_DIR}/*.json")
    )
    # Excluir mixto del dataset_raw (se incluye en labeled separado)
    archivos = [a for a in archivos if not a.endswith("eve.json") or "raw" not in a]

    print(f"Archivos encontrados: {len(archivos)}")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    total = 0
    cont_normal = 0
    cont_anom   = 0

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=COLUMNAS)
        writer.writeheader()

        for path in archivos:
            nombre = os.path.basename(path)
            registros = parsear_archivo(path)
            writer.writerows(registros)

            n = len(registros)
            lbl = inferir_label(nombre)
            total += n
            if lbl == 0:
                cont_normal += n
            else:
                cont_anom += n

            print(f"  {nombre:<52} → {n:6d} flows  label={lbl}")

    print()
    print("=" * 60)
    print(f"  dataset_raw.csv generado: {OUTPUT_CSV}")
    print(f"  Total flows     : {total:,}")
    print(f"  Flows normales  : {cont_normal:,}  ({100*cont_normal/total:.1f}%)")
    print(f"  Flows anomalos  : {cont_anom:,}  ({100*cont_anom/total:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
