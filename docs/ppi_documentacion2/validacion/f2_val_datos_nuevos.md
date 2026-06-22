# V6 — Validación con Datos Normales Nuevos (Generalización)

**Criterios:** CA-16  
**Tiempo estimado:** 15-20 minutos (captura) + 5 min (análisis)  
**Propósito:** Verificar que el IF no sobreajustó al período de captura original

---

## Por qué esta validación existe

El holdout actual (13,427 flujos normales) proviene del **mismo período de captura** que el entrenamiento (80% de los mismos datos). Aunque es un conjunto separado, comparte la distribución temporal.

Esta validación genera tráfico normal **nuevo, en diferente sesión/horario**, pasa los flujos por el modelo IF, y verifica que el FPR se mantiene dentro del rango esperado (≤ 30%). Si el FPR sube mucho, indica que el modelo sobreajustó a patrones temporales específicos de las corridas originales.

**CA-16:** FPR en nueva data normal ≤ 0.30

---

## Cómo ejecutar — opción A (captura real nueva)

### Paso 1: Capturar nueva sesión de tráfico normal

Elige un escenario A que no haya sido el más frecuente (recomendado A3 — transferencia):

```bash
# En Desktop (192.168.0.20) — Duración: 10 minutos
for i in $(seq 1 40); do
  wget -q -O /dev/null http://192.168.0.120/index.html
  sleep 15
done
```

O tráfico SSH mixto:
```bash
for i in $(seq 1 20); do
  ssh -o BatchMode=yes m4rk@192.168.0.120 "ls /var/log/ | wc -l" 2>/dev/null
  sleep 25
done
```

### Paso 2: Exportar flujos de eve.json a CSV

```bash
# En sensor (192.168.0.110) — después de la captura
cd /home/m4rk/ppi-surikata-producto
source /home/m4rk/ppi-sensor/venv/bin/activate

python3 - << 'EOF'
import json, pandas as pd, numpy as np
from datetime import datetime

FEATURES = ['pkts_toserver','pkts_toclient','bytes_toserver','bytes_toclient',
            'duration','pkt_rate','byte_rate','pkt_ratio','byte_ratio',
            'avg_pkt_size','is_tcp','is_udp','is_icmp','dest_port']

rows = []
with open('/var/log/suricata/eve.json') as f:
    for line in f:
        try:
            ev = json.loads(line)
            if ev.get('event_type') != 'flow': continue
            fl = ev.get('flow', {})
            dur = fl.get('age', 0)
            ps = ev.get('pkts_toserver', 0)
            pc = ev.get('pkts_toclient', 0)
            bs = ev.get('bytes_toserver', 0)
            bc = ev.get('bytes_toclient', 0)
            tp = int(ev.get('proto','').upper() == 'TCP')
            ud = int(ev.get('proto','').upper() == 'UDP')
            ic = int(ev.get('proto','').upper() == 'ICMP')
            dp = ev.get('dest_port', 0)
            rows.append([ps, pc, bs, bc, dur,
                         ps/max(dur,1), bs/max(dur,1),
                         ps/max(ps+pc,1), bs/max(bs+bc,1),
                         (bs+bc)/max(ps+pc,1),
                         tp, ud, ic, dp])
        except: pass

df = pd.DataFrame(rows, columns=FEATURES)
df.to_csv('/tmp/nueva_data_normal.csv', index=False)
print(f"Flujos extraídos: {len(df)}")
EOF
```

### Paso 3: Evaluar con el modelo IF

```bash
python3 - << 'EOF'
import pandas as pd, pickle, numpy as np

df = pd.read_csv('/tmp/nueva_data_normal.csv')

with open('models/scaler.pkl','rb') as f: scaler = pickle.load(f)
with open('models/isolation_forest.pkl','rb') as f: iforest = pickle.load(f)

X = scaler.transform(df)
scores = iforest.decision_function(X)

TAU1 = -0.4459
TAU2 = -0.6027

n_permit = (scores > TAU1).sum()
n_limit  = ((scores > TAU2) & (scores <= TAU1)).sum()
n_block  = (scores <= TAU2).sum()
total = len(scores)

fpr_efectivo = (n_limit + n_block) / total

print(f"\n=== VALIDACIÓN V6 — Nueva data normal ===")
print(f"Total flujos:  {total}")
print(f"PERMIT (normal):  {n_permit}  ({n_permit/total:.1%})")
print(f"LIMIT (FP suave): {n_limit}   ({n_limit/total:.1%})")
print(f"BLOCK (FP fuerte):{n_block}   ({n_block/total:.1%})")
print(f"\nFPR efectivo: {fpr_efectivo:.4f} ({fpr_efectivo:.1%})")
print(f"Criterio CA-16: ≤ 0.30")
print(f"RESULTADO: {'✅ PASS' if fpr_efectivo <= 0.30 else '❌ FAIL'}")
print(f"\nScore medio: {scores.mean():.4f} ± {scores.std():.4f}")
print(f"(Esperado tráfico normal: -0.3965 ± 0.0753)")
EOF
```

---

## Cómo ejecutar — opción B (reusar eve.json capturado en diferente horario)

Si ya tienes un `.gz` de corridas normales recientes en `data/raw/`:

```bash
# Listar capturas normales disponibles
ls /home/m4rk/ppi-surikata-producto/data/raw/ | grep normal

# Descomprimir una y evaluar
gunzip -c data/raw/YYYYMMDD_normal_http_NN_eve.json.gz > /tmp/test_eve.json
# Luego reemplazar el path en el Paso 3 arriba
```

---

## Interpretación de resultados

| FPR obtenido | Interpretación |
|---|---|
| < 20% | Modelo más conservador que en entrenamiento — muy bien |
| 20-25% | Esperado — consistente con τ1 teórico (CA-16 ✅ PASS) |
| 25-30% | Ligero drift temporal — aceptable (CA-16 ✅ PASS) |
| > 30% | Drift significativo — considerar reentrenamiento (CA-16 ❌ FAIL) |

**Nota:** El FPR teórico de τ1 es 20.47% sobre datos de entrenamiento. En datos nuevos se espera un valor similar. Si supera 30%, activar F5 (reentrenamiento incremental con la nueva captura).
