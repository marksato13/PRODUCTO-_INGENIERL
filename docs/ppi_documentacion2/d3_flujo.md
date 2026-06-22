# Diagrama 3 — Flujo de Decisión del Motor
**Slide 10 del PPT**

---

## Versión principal (flujo completo)

```
┌─────────────────────────────────────────────────────────┐
│                    eve.json (Suricata)                   │
│              nuevo evento de flujo TCP/UDP/ICMP          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  ¿IP en whitelist?    │
              │  (192.168.0.20, .110, │
              │   .120, .1, 127.0.0.1)│
              └─────────┬─────────────┘
                        │
              ┌─────────┴──────────┐
              │ SÍ                 │ NO
              ▼                    ▼
           PERMIT            Extraer 14 features
        (sin acción)         pkts / bytes / rates
                             proto / puerto / dur
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   StandardScaler      │
                        │   → normalizar        │
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Isolation Forest    │
                        │   n=300 árboles       │
                        │   score ∈ [−1, 0]     │
                        └───────────┬───────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
             score > −0.4459  −0.6027 < score   score ≤ −0.6027
                 (> τ1)        ≤ −0.4459            (≤ τ2)
                    │          (entre τ2 y τ1)       │
                    ▼               ▼               ▼
                 PERMIT           LIMIT           BLOCK
              ✅ log DEBUG    ⚠️ log WARNING   🚫 log WARNING
              sin acción      hashlimit         ipset DROP
                              100 pkt/s         kernel level
                                    │               │
                                    └───────┬───────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │   Detectores heurísticos    │
                              │                             │
                              │  BF-SSH:                    │
                              │   ≥ 5 intentos/60s → LIMIT  │
                              │   ≥ 15 intentos/60s → BLOCK │
                              │                             │
                              │  HTTP-Abuse:                │
                              │   ≥ 50 req/30s → LIMIT      │
                              │   ≥ 100 req/30s → BLOCK     │
                              └─────────────┬──────────────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │   Bloqueo progresivo        │
                              │                             │
                              │  bloqueo #1 → timeout 300s  │
                              │  bloqueo #2 → timeout 1800s │
                              │  bloqueo #3 → timeout 0 (∞) │
                              └─────────────┬──────────────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │   Enforcement               │
                              │                             │
                              │  SSH → servidor 192.168.0.120│
                              │  sudo ipset add ppi_blocked  │
                              │  sudo ipset add ppi_limited  │
                              └─────────────┬──────────────┘
                                            │
                              ┌─────────────▼──────────────┐
                              │   Notificación              │
                              │                             │
                              │  motor_decision.log         │
                              │  Dashboard SSE :8080        │
                              │  Telegram (async, dedup 5m) │
                              └────────────────────────────┘
```

---

## Versión simplificada (para slide, más visual)

```
 Suricata
 eve.json
    │
    ▼
┌──────────────┐
│  ¿whitelist? │──SÍ──▶ PERMIT ✅
└──────┬───────┘
       │ NO
       ▼
┌──────────────┐
│ 14 features  │
│  + IF score  │
└──────┬───────┘
       │
       ├──── score > −0.4459 ──▶  PERMIT ✅  (tráfico normal)
       │
       ├──── −0.6027 < score ──▶  LIMIT ⚠️   (hashlimit 100 pkt/s)
       │     ≤ −0.4459               └── + heurísticos BF/HTTP
       │
       └──── score ≤ −0.6027 ──▶  BLOCK 🚫  (ipset DROP kernel)
                                      └── bloqueo progresivo
                                          #1=5min #2=30min #3=∞

                     BLOCK ──▶ Telegram 📱 + Dashboard 🖥️
```

---

## Visualización de la línea de decisión (para slide 10)

```
Score IF         −1.0          −0.6027         −0.4459          0.0
                  │─────────────────┼───────────────┼──────────────│
                  │                 │               │              │
                  │◄── BLOCK ──────►│◄─── LIMIT ───►│◄── PERMIT ──►│
                  │   DROP kernel   │  100 pkt/s    │  sin acción  │
                  │   🚫 rojo       │  ⚠️ amarillo  │  ✅ verde    │
                  │                 │               │              │
                  │   τ2=−0.6027    │               │ τ1=−0.4459   │
                  │   FPR=2%        │               │ Youden index │
                  │   TPR=18.3%     │               │ TPR=99.4%    │
```

---

## Notas para PPT / draw.io

- **Versión recomendada para slide:** la simplificada (centro de la página) + la línea de decisión abajo
- **Colores de las zonas:**
  - PERMIT: fondo verde suave
  - LIMIT: fondo amarillo / naranja suave
  - BLOCK: fondo rojo suave
- **La línea de decisión** es muy visual — se puede poner como banda horizontal de colores degradados de rojo a verde
- **Enfatizar:** los detectores heurísticos BF-SSH y HTTP-Abuse actúan SIN esperar el score IF — son paralelos
- **El bloqueo progresivo** se puede mostrar como un badge que se incrementa: [1] → [2] → [∞]
