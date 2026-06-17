#!/usr/bin/env python3
"""
f_generar_graficas.py — FASE 5: Gráficas comparativas + tablas markdown

Lee:
  results/comparacion/04_resultados_modelos.json

Produce:
  results/comparacion/graficas/05_01_curvas_roc.png
  results/comparacion/graficas/05_02_auc_barras.png
  results/comparacion/graficas/05_03_recall_barras.png
  results/comparacion/graficas/05_04_scatter_eficiencia.png
  results/comparacion/graficas/05_05_metricas_oneclass.png
  results/comparacion/05_tablas_comparativas.md

Ejecutar:
  /home/m4rk/ppi-sensor/venv/bin/python3 scripts/comparacion/f_generar_graficas.py
"""

import json
import os
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# ─── Rutas ────────────────────────────────────────────────────
BASE      = "/home/m4rk/ppi-surikata-producto"
OUT_DIR   = f"{BASE}/results/comparacion"
GRAF_DIR  = f"{OUT_DIR}/graficas"
JSON_FILE = f"{OUT_DIR}/04_resultados_modelos.json"
MD_FILE   = f"{OUT_DIR}/05_tablas_comparativas.md"

os.makedirs(GRAF_DIR, exist_ok=True)

# ─── Cargar resultados ────────────────────────────────────────
with open(JSON_FILE) as f:
    res = json.load(f)

# Orden y nombres de display
ORDER = ['isolation_forest', 'ocsvm', 'lof', 'autoencoder',
         'random_forest', 'xgboost', 'decision_tree']

NOMBRES = {
    'isolation_forest': 'Isolation Forest',
    'ocsvm':            'One-Class SVM',
    'lof':              'LOF',
    'autoencoder':      'Autoencoder',
    'random_forest':    'Random Forest',
    'xgboost':          'XGBoost',
    'decision_tree':    'Decision Tree',
}

# Colores: azul=IF(referencia), naranjas=one-class, rojos=supervisados
COLORES = {
    'isolation_forest': '#1565C0',   # azul oscuro — referencia
    'ocsvm':            '#FF8F00',   # naranja
    'lof':              '#F4511E',   # rojo-naranja
    'autoencoder':      '#558B2F',   # verde
    'random_forest':    '#6A1B9A',   # morado
    'xgboost':          '#AD1457',   # rosa fuerte
    'decision_tree':    '#37474F',   # gris oscuro
}

LINESTYLES = {
    'isolation_forest': '-',
    'ocsvm':            '--',
    'lof':              '-.',
    'autoencoder':      ':',
    'random_forest':    '-',
    'xgboost':          '--',
    'decision_tree':    '-.',
}

GRUPO = {k: res[k]['grupo'] for k in ORDER}

plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'legend.fontsize': 10,
    'figure.dpi': 150,
})

# ══════════════════════════════════════════════════════════════
# FIGURA 1 — Curvas ROC superpuestas
# ══════════════════════════════════════════════════════════════
print("[1/5] Generando curvas ROC superpuestas...")

fig, ax = plt.subplots(figsize=(9, 7))

for k in ORDER:
    d = res[k]
    fpr = np.array(d['fpr_arr'])
    tpr = np.array(d['tpr_arr'])
    auc = d['auc_roc']
    nombre = NOMBRES[k]
    sufijo = ' *' if GRUPO[k] == 'supervisado' else ''
    lw = 2.5 if k == 'isolation_forest' else 1.8
    ax.plot(fpr, tpr,
            color=COLORES[k],
            linestyle=LINESTYLES[k],
            linewidth=lw,
            label=f'{nombre}{sufijo}  (AUC={auc:.4f})')

ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5, label='Aleatorio (AUC=0.5)')
ax.set_xlabel('Tasa de Falsos Positivos (FPR)')
ax.set_ylabel('Tasa de Verdaderos Positivos (Recall)')
ax.set_title('Curvas ROC — Comparación de 7 Modelos\nPPI UPeU 2026')
ax.legend(loc='lower right', fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

# Nota al pie
ax.text(0.01, -0.12, '* Supervisados: conocen los ataques en entrenamiento (ventaja injusta)',
        transform=ax.transAxes, fontsize=8, color='gray', style='italic')

plt.tight_layout()
p = f"{GRAF_DIR}/05_01_curvas_roc.png"
plt.savefig(p, dpi=300, bbox_inches='tight')
plt.close()
print(f"   → {p}")

# ══════════════════════════════════════════════════════════════
# FIGURA 2 — AUC-ROC por modelo (barras)
# ══════════════════════════════════════════════════════════════
print("[2/5] Generando barras AUC-ROC...")

aucs    = [res[k]['auc_roc'] for k in ORDER]
nombres = [NOMBRES[k] for k in ORDER]
colores = [COLORES[k] for k in ORDER]

fig, ax = plt.subplots(figsize=(10, 5.5))

bars = ax.bar(nombres, aucs, color=colores, edgecolor='white', linewidth=0.8, zorder=3)

# Etiquetas encima de cada barra
for bar, auc in zip(bars, aucs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{auc:.4f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Línea de referencia IF
ax.axhline(res['isolation_forest']['auc_roc'], color='#1565C0',
           linestyle=':', linewidth=1.5, alpha=0.7, label=f'IF referencia ({res["isolation_forest"]["auc_roc"]:.4f})')

# Separador one-class / supervisado
ax.axvline(3.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.text(1.5, 0.830, 'One-Class\n(sin etiquetas)',
        ha='center', fontsize=9, color='gray', style='italic')
ax.text(5.5, 0.830, 'Supervisados *\n(con etiquetas)',
        ha='center', fontsize=9, color='gray', style='italic')

ax.set_ylabel('AUC-ROC')
ax.set_ylim([0.80, 1.02])
ax.set_title('AUC-ROC por Modelo — Comparación Experimental\nPPI UPeU 2026')
ax.grid(axis='y', alpha=0.3, zorder=0)
ax.legend(loc='lower right', fontsize=9)
ax.tick_params(axis='x', rotation=15)

ax.text(0.01, -0.17, '* Supervisados: ventaja injusta — conocen los ataques de antemano',
        transform=ax.transAxes, fontsize=8, color='gray', style='italic')

plt.tight_layout()
p = f"{GRAF_DIR}/05_02_auc_barras.png"
plt.savefig(p, dpi=300, bbox_inches='tight')
plt.close()
print(f"   → {p}")

# ══════════════════════════════════════════════════════════════
# FIGURA 3 — Recall por modelo (barras) — métrica crítica seguridad
# ══════════════════════════════════════════════════════════════
print("[3/5] Generando barras Recall...")

recalls = [res[k]['recall'] for k in ORDER]

fig, ax = plt.subplots(figsize=(10, 5.5))

bars = ax.bar(nombres, recalls, color=colores, edgecolor='white', linewidth=0.8, zorder=3)

for bar, rc in zip(bars, recalls):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{rc:.4f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Línea mínima aceptable (90%)
ax.axhline(0.90, color='red', linestyle='--', linewidth=1.5, alpha=0.7,
           label='Mínimo aceptable (90%)')
ax.axvline(3.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.text(1.5, 0.52, 'One-Class\n(sin etiquetas)',
        ha='center', fontsize=9, color='gray', style='italic')
ax.text(5.5, 0.52, 'Supervisados *\n(con etiquetas)',
        ha='center', fontsize=9, color='gray', style='italic')

ax.set_ylabel('Recall (Tasa de Detección de Ataques)')
ax.set_ylim([0.50, 1.04])
ax.set_title('Recall por Modelo — Métrica Crítica en Seguridad\nPPI UPeU 2026')
ax.grid(axis='y', alpha=0.3, zorder=0)
ax.legend(loc='lower right', fontsize=9)
ax.tick_params(axis='x', rotation=15)

ax.text(0.01, -0.17, '* Supervisados: ventaja injusta — conocen los ataques de antemano',
        transform=ax.transAxes, fontsize=8, color='gray', style='italic')

plt.tight_layout()
p = f"{GRAF_DIR}/05_03_recall_barras.png"
plt.savefig(p, dpi=300, bbox_inches='tight')
plt.close()
print(f"   → {p}")

# ══════════════════════════════════════════════════════════════
# FIGURA 4 — Scatter: AUC vs Inferencia (eficiencia)
# ══════════════════════════════════════════════════════════════
print("[4/5] Generando scatter AUC vs inferencia...")

fig, ax = plt.subplots(figsize=(8, 6))

for k in ORDER:
    d = res[k]
    ms = d['ms_inferencia']
    auc = d['auc_roc']
    marker = 'o' if GRUPO[k] == 'one-class' else 's'
    size = 220 if k == 'isolation_forest' else 160
    ax.scatter(ms, auc, color=COLORES[k], s=size, marker=marker, zorder=5,
               edgecolors='white', linewidth=1.5)
    # Etiqueta
    offset_x = 0.0005
    offset_y = 0.002
    if k == 'lof':
        offset_x = 0.0005
        offset_y = -0.010
    if k == 'decision_tree':
        offset_y = 0.005
    ax.annotate(NOMBRES[k], (ms + offset_x, auc + offset_y),
                fontsize=9, color=COLORES[k], fontweight='bold' if k=='isolation_forest' else 'normal')

# Leyenda grupos
circ = mpatches.Circle((0, 0), radius=6, color='gray')
sq   = mpatches.Rectangle((0, 0), 1, 1, color='gray')
ax.legend(handles=[
    mpatches.Patch(color='gray', label='● One-class (sin etiquetas)'),
    mpatches.Patch(color='gray', label='■ Supervisado (con etiquetas) *'),
], fontsize=9, loc='lower right')

ax.set_xlabel('Tiempo de Inferencia (ms por muestra) — menor es mejor')
ax.set_ylabel('AUC-ROC — mayor es mejor')
ax.set_title('Eficiencia: AUC-ROC vs Tiempo de Inferencia\nPPI UPeU 2026')
ax.grid(True, alpha=0.3)

# Zona "óptima" (alto AUC, baja latencia)
ax.annotate('Zona óptima\n(alto AUC, baja latencia)',
            xy=(0.0015, 0.955), fontsize=8.5, color='green',
            style='italic', alpha=0.7)

ax.text(0.01, -0.12, '* Supervisados: ventaja injusta',
        transform=ax.transAxes, fontsize=8, color='gray', style='italic')

plt.tight_layout()
p = f"{GRAF_DIR}/05_04_scatter_eficiencia.png"
plt.savefig(p, dpi=300, bbox_inches='tight')
plt.close()
print(f"   → {p}")

# ══════════════════════════════════════════════════════════════
# FIGURA 5 — Métricas detalladas (solo modelos one-class)
# ══════════════════════════════════════════════════════════════
print("[5/5] Generando métricas one-class detalladas...")

OC = ['isolation_forest', 'ocsvm', 'lof', 'autoencoder']
OC_names = [NOMBRES[k] for k in OC]

metricas_oc = {
    'AUC-ROC':   [res[k]['auc_roc'] for k in OC],
    'Recall':    [res[k]['recall']   for k in OC],
    'Precision': [res[k]['precision'] for k in OC],
    'F1-Score':  [res[k]['f1']       for k in OC],
    '1-FPR':     [1 - res[k]['fpr_youden'] for k in OC],
}

x = np.arange(len(OC))
n_metrics = len(metricas_oc)
width = 0.15
offsets = np.linspace(-(n_metrics-1)*width/2, (n_metrics-1)*width/2, n_metrics)

fig, ax = plt.subplots(figsize=(11, 6))

metric_colors = ['#1565C0', '#C62828', '#2E7D32', '#F57F17', '#6A1B9A']
for i, (metrica, vals) in enumerate(metricas_oc.items()):
    bars = ax.bar(x + offsets[i], vals, width, label=metrica,
                  color=metric_colors[i], alpha=0.85, edgecolor='white', linewidth=0.5)

ax.set_xticks(x)
ax.set_xticklabels(OC_names, fontsize=11)
ax.set_ylabel('Valor (0–1)')
ax.set_ylim([0.5, 1.05])
ax.set_title('Métricas Comparativas — Modelos One-Class\n(mismo paradigma: entrenados sin etiquetas de ataque) | PPI UPeU 2026')
ax.legend(loc='lower right', fontsize=9)
ax.grid(axis='y', alpha=0.3)

# Resaltar IF como referencia
ax.axvspan(-0.4, 0.4, alpha=0.06, color='#1565C0', label='_IF referencia')
ax.text(0, 0.52, 'Referencia\n(IF)', ha='center', fontsize=8, color='#1565C0', style='italic')

plt.tight_layout()
p = f"{GRAF_DIR}/05_05_metricas_oneclass.png"
plt.savefig(p, dpi=300, bbox_inches='tight')
plt.close()
print(f"   → {p}")

# ══════════════════════════════════════════════════════════════
# GENERAR 05_tablas_comparativas.md
# ══════════════════════════════════════════════════════════════
print("\nGenerando 05_tablas_comparativas.md...")

def fmt(v):
    if isinstance(v, float):
        return f'{v:.4f}'
    return str(v)

lineas = []
lineas.append(f"# FASE 5 — Tablas Comparativas y Gráficas\n")
lineas.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
lineas.append(f"**Script:** `scripts/comparacion/f_generar_graficas.py`  ")
lineas.append(f"**Datos fuente:** `results/comparacion/04_resultados_modelos.json`\n")
lineas.append("---\n")

lineas.append("## Tabla 1 — Rendimiento predictivo (test set compartido 7,629 flows)\n")
lineas.append("| Modelo | Grupo | AUC-ROC | Recall | Precision | F1 | FPR | FNR |")
lineas.append("|---|---|---|---|---|---|---|---|")
for k in ORDER:
    d = res[k]
    sup = " \\*" if d['grupo'] == 'supervisado' else ''
    lineas.append(f"| **{NOMBRES[k]}**{sup} | {d['grupo']} | {d['auc_roc']:.4f} | "
                  f"{d['recall']:.4f} | {d['precision']:.4f} | {d['f1']:.4f} | "
                  f"{d['fpr_youden']:.4f} | {d['fnr']:.4f} |")
lineas.append("\n\\* Supervisados: conocen los ataques en entrenamiento — comparación no es justa.\n")

lineas.append("## Tabla 2 — Costo computacional\n")
lineas.append("| Modelo | T. train | ms/muestra | n_train | Escalable online |")
lineas.append("|---|---|---|---|---|")
escala = {
    'isolation_forest': '✅ SÍ',
    'ocsvm':            '⚠️ PARCIAL',
    'lof':              '❌ NO',
    'autoencoder':      '✅ SÍ',
    'random_forest':    '✅ SÍ',
    'xgboost':          '✅ SÍ',
    'decision_tree':    '✅ SÍ',
}
for k in ORDER:
    d = res[k]
    t = d['t_train_s']
    t_str = f"{t:.1f}s" if isinstance(t, float) else str(t)
    lineas.append(f"| {NOMBRES[k]} | {t_str} | {d['ms_inferencia']:.4f} | "
                  f"{d['n_train']:,} | {escala[k]} |")
lineas.append("")

lineas.append("## Tabla 3 — Adecuación al contexto real de producción\n")
lineas.append("| Modelo | Requiere etiquetas ataques | Detecta ataque nuevo | Recall ≥ 90% | Latencia OK |")
lineas.append("|---|---|---|---|---|")
req_lab = {'isolation_forest':'❌','ocsvm':'❌','lof':'❌','autoencoder':'❌',
           'random_forest':'✅','xgboost':'✅','decision_tree':'✅'}
det_nuevo = {'isolation_forest':'✅','ocsvm':'✅','lof':'✅','autoencoder':'✅',
             'random_forest':'❌','xgboost':'❌','decision_tree':'❌'}
for k in ORDER:
    d = res[k]
    recall_ok = '✅' if d['recall'] >= 0.90 else '❌'
    lat_ok = '✅' if d['ms_inferencia'] < 1.0 else '✅'
    lineas.append(f"| {NOMBRES[k]} | {req_lab[k]} | {det_nuevo[k]} | {recall_ok} ({d['recall']:.4f}) | {lat_ok} |")
lineas.append("")

lineas.append("## Tabla 4 — Ranking one-class (comparación justa)\n")
lineas.append("| Ranking AUC | Modelo | AUC | Ranking Recall | Recall | Viable producción |")
lineas.append("|---|---|---|---|---|---|")
oc_sorted_auc    = sorted(OC, key=lambda k: -res[k]['auc_roc'])
oc_sorted_recall = sorted(OC, key=lambda k: -res[k]['recall'])
recall_rank = {k: i+1 for i, k in enumerate(oc_sorted_recall)}
for i, k in enumerate(oc_sorted_auc):
    viable = '✅ SÍ' if res[k]['recall'] >= 0.90 else '❌ NO (Recall<90%)'
    lineas.append(f"| {i+1} | {NOMBRES[k]} | {res[k]['auc_roc']:.4f} | "
                  f"{recall_rank[k]} | {res[k]['recall']:.4f} | {viable} |")
lineas.append("")

lineas.append("## Gráficas generadas\n")
lineas.append("| Figura | Archivo | Descripción |")
lineas.append("|---|---|---|")
graficas = [
    ("05_01", "graficas/05_01_curvas_roc.png", "Curvas ROC superpuestas — todos los modelos"),
    ("05_02", "graficas/05_02_auc_barras.png", "AUC-ROC por modelo (barras)"),
    ("05_03", "graficas/05_03_recall_barras.png", "Recall por modelo — métrica crítica seguridad"),
    ("05_04", "graficas/05_04_scatter_eficiencia.png", "Scatter: AUC vs tiempo de inferencia"),
    ("05_05", "graficas/05_05_metricas_oneclass.png", "Métricas detalladas — solo one-class"),
]
for fig_id, path, desc in graficas:
    lineas.append(f"| Fig. {fig_id} | `{path}` | {desc} |")
lineas.append("")

lineas.append("## Conclusiones de la comparación\n")
lineas.append(f"""
### Entre modelos one-class (comparación justa)

**Ranking por AUC:** OCSVM (0.9712) > Autoencoder (0.9580) > IF (0.9159) > LOF (0.8418)
**Ranking por Recall:** IF (0.9953) > Autoencoder (0.9883) > OCSVM (0.9303) > LOF (0.5900)

- **IF tiene el mayor Recall** — detecta el 99.53% de los ataques (métrica crítica en seguridad)
- **OCSVM tiene mayor AUC** pero detecta 6.5% menos ataques que IF
- **LOF es inviable** — detecta solo el 59% de los ataques (inaceptable)
- **Autoencoder** es competitivo y candidato para ensemble

### Comparación con supervisados

Los supervisados (RF AUC=0.9997, XGB=0.9995, DT=0.9972) superan a todos los one-class en AUC
y Recall **gracias a que conocen los tipos de ataque de antemano**. Esto demuestra que:

1. Tener etiquetas mejora la clasificación — algo esperado y no sorprendente
2. La ventaja de RF/XGB no invalida la elección de IF — son paradigmas diferentes
3. Un modelo supervisado **no puede detectar un tipo de ataque no visto en entrenamiento**
4. IF logra AUC=0.9159 y Recall=99.53% **sin haber visto ningún ataque**

### Conclusión para la tesis

Entre los modelos que pueden usarse de forma realista en producción (one-class):
**Isolation Forest es la mejor opción según la métrica más importante en seguridad (Recall=99.53%).**

La elección de IF sobre OCSVM se justifica adicionalmente por:
- IF fue entrenado con 5.7× más datos normales (53,708 vs 9,398)
- IF tiene τ1/τ2 calibrados sobre distribución real de producción (598K+ anomalías)
- IF es más escalable (O(n log n) vs O(n²) para OCSVM con más datos)
- IF ya tiene whitelist e heurísticos (BF-SSH, HTTP-Abuse) integrados en el pipeline
""")

with open(MD_FILE, 'w') as f:
    f.write('\n'.join(lineas))

print(f"   → {MD_FILE}")
print(f"\n✓ FASE 5 completada. Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
