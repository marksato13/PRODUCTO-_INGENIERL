import sys, re

metrics_file = sys.argv[1]
text = open(metrics_file).read()

auc_m  = re.search(r'AUC-ROC\s*:\s*([\d.]+)', text)
fp_m   = re.search(r'FP=(\d+)', text)
fn_m   = re.search(r'FN=(\d+)', text)
tp_m   = re.search(r'TP=(\d+)', text)

if not all([auc_m, fp_m, fn_m]):
    print("  ❌ No se pudieron leer AUC/FP/FN del archivo")
    sys.exit(1)

auc     = float(auc_m.group(1))
fp      = int(fp_m.group(1))
fn      = int(fn_m.group(1))
errores = fp + fn

ca11 = auc >= 0.95
ca12 = errores <= 30

print()
print(f"  {'✅ PASS' if ca11 else '❌ FAIL'}  CA-11 AUC-ROC: {auc:.4f}  (criterio: ≥ 0.95)")
print(f"  {'✅ PASS' if ca12 else '❌ FAIL'}  CA-12 FP+FN:   {errores} ({fp} FP + {fn} FN)  (criterio: ≤ 30)")
print(f"\n  Resultado: {sum([ca11, ca12])}/2 criterios PASS")
