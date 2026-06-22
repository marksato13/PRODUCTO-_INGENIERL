# Diagrama 2 — Pipeline en 6 Fases
**Slide 5 del PPT**

---

## Versión horizontal (para slide ancho)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│    F1    │     │    F2    │     │    F3    │     │    F4    │     │    F5    │     │    F6    │
│ Captura  │────▶│  Datos   │────▶│  Modelo  │────▶│  Motor   │────▶│ Aprend.  │────▶│ Validac. │
│          │     │          │     │          │     │          │     │ Continuo │     │          │
│ Suricata │     │ Dataset  │     │Isolation │     │Decisión  │     │XGBoost   │     │40 corridas│
│ eve.json │     │ 14 feat  │     │ Forest   │     │en tiempo │     │diario    │     │lab real  │
│          │     │ limpio   │     │AUC=0.900 │     │real      │     │IF semana │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │                │
  47 capturas     667K flujos       τ1=−0.446        PERMIT           hot-reload       Disp=100%
  9 escenarios    etiquetados       τ2=−0.603        LIMIT            sin reinicio     ITL=0%
  .json.gz        dataset_clean     AUC-ROC          BLOCK            automático       Lead=62s
```

---

## Versión vertical con detalle (para slide o informe)

```
                    ╔══════════════════════════════════╗
                    ║           F1 — CAPTURA           ║
                    ║  Suricata 7.0.3 · ens35 pasivo   ║
                    ║  9 escenarios (A/B/C) · 47 .gz   ║
                    ╚══════════════════╦═══════════════╝
                                       ║
                                  eve.json.gz
                                       ║
                    ╔══════════════════▼═══════════════╗
                    ║       F2 — PROCESAMIENTO          ║
                    ║  14 features por flujo            ║
                    ║  Etiquetado normal / anómalo      ║
                    ║  Split cronológico 70 / 15 / 15   ║
                    ╚══════════════════╦═══════════════╝
                                       ║
                              train.csv / test.csv
                                       ║
                    ╔══════════════════▼═══════════════╗
                    ║       F3 — MODELO IF              ║
                    ║  IsolationForest n=300            ║
                    ║  AUC=0.8998                       ║
                    ║  τ1=−0.4459  τ2=−0.6027          ║
                    ╚══════════════════╦═══════════════╝
                                       ║
                         isolation_forest.pkl
                         metricas_offline.txt
                                       ║
               ╔═══════════════════════▼══════════════════╗
               ║           F4 — MOTOR DE DECISIÓN         ║
               ║  tail eve.json → 14 features → IF score  ║
               ║  PERMIT / LIMIT / BLOCK                  ║
               ║  BF-SSH · HTTP-Abuse · Bloqueo prog.     ║
               ║  Dashboard :8080 · Telegram alerts       ║
               ╚═══════════════╦══════════════════════════╝
                               ║
               ╔═══════════════▼══════════════════════════╗
               ║           F5 — APRENDIZAJE CONTINUO      ║
               ║  IF: semanal (dom 02:00)                 ║
               ║  XGBoost: diario (03:00)                 ║
               ║  Guarda si AUC no retrocede              ║
               ║  hot-reload sin reiniciar servicio       ║
               ╚═══════════════╦══════════════════════════╝
                               ║
               ╔═══════════════▼══════════════════════════╗
               ║           F6 — VALIDACIÓN                ║
               ║  40 corridas · 9 escenarios              ║
               ║  Disponibilidad 100% · ITL 0%            ║
               ║  Latencia P95 = 34.8ms                   ║
               ╚══════════════════════════════════════════╝
```

---

## Notas para PPT / draw.io

- **Colores sugeridos:**
  - F1: gris (captura pasiva)
  - F2: azul claro (datos)
  - F3: azul oscuro (modelo entrenado)
  - F4: verde (producción / tiempo real) ← el más importante visualmente
  - F5: teal (aprendizaje continuo)
  - F6: amarillo/dorado (validación)

- **Íconos sugeridos por fase:**
  - F1: 📡 antena / sensor
  - F2: 📊 tabla / CSV
  - F3: 🤖 modelo / árbol
  - F4: ⚡ rayo / tiempo real
  - F5: 🔄 ciclo / flecha circular
  - F6: ✅ check / escudo

- **En la versión horizontal:** usar flechas gruesas entre cajas y texto pequeño debajo de cada caja con el output principal

- **Énfasis visual:** F4 debe ser la caja más grande o con borde más grueso — es el core del producto
