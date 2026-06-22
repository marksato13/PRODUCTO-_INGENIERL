import sys, re

metrics_file = sys.argv[1]
vals = {}
with open(metrics_file) as f:
    for line in f:
        m = re.match(r'\s*([\w_-]+)\s*:\s*(-?[\d]+\.[\d]+)', line)
        if m:
            try:
                vals[m.group(1)] = float(m.group(2))
            except ValueError:
                pass

checks = [
    ("CA-1", "AUC-ROC",   "AUC-ROC",   "≥ 0.85", lambda v: v >= 0.85),
    ("CA-2", "tau1_tpr",  "TPR@τ1",    "≥ 0.95", lambda v: v >= 0.95),
    ("CA-3", "tau1_fpr",  "FPR@τ1",    "≤ 0.25", lambda v: v <= 0.25),
    ("CA-4", "precision", "Precision", "≥ 0.95", lambda v: v >= 0.95),
]

ok = 0
print()
for ca, key, label, crit, fn in checks:
    v = vals.get(key)
    if v is None:
        print(f"  ⚠️  {ca} {label}: clave '{key}' no encontrada")
        continue
    passed = fn(v)
    mark = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {mark}  {ca} {label}: {v:.4f}  (criterio: {crit})")
    if passed:
        ok += 1

print(f"\n  Resultado: {ok}/4 criterios PASS")
