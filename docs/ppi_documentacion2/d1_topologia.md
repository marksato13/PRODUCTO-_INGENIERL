# Diagrama 1 — Topología de Red del Laboratorio
**Slide 9 del PPT**

---

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RED LOCAL  192.168.0.0/24                           │
│                                                                         │
│   ┌───────────────┐              ┌───────────────┐                      │
│   │  Win11        │              │  Kali Linux   │                      │
│   │  Cliente      │              │  Atacante     │                      │
│   │ 192.168.0.10  │              │ 192.168.0.100 │                      │
│   └───────┬───────┘              └───────┬───────┘                      │
│           │  tráfico normal              │  tráfico anómalo             │
│           │  HTTP / SSH / SCP            │  SYN flood / port scan /     │
│           │                              │  UDP flood / BF SSH          │
│           └──────────────┬───────────────┘                              │
│                          │                                              │
│                          ▼                                              │
│          ┌───────────────────────────────┐                              │
│          │   Ubuntu Sensor               │                              │
│          │   192.168.0.110               │  ◄── AQUÍ CORRE EL SISTEMA  │
│          │                               │                              │
│          │  ┌─────────────────────────┐  │                              │
│          │  │  Suricata 7.0.3         │  │                              │
│          │  │  ens35 (modo pasivo)    │  │                              │
│          │  │  → eve.json            │  │                              │
│          │  └───────────┬─────────────┘  │                              │
│          │              │                │                              │
│          │  ┌───────────▼─────────────┐  │                              │
│          │  │  motor_decision.py      │  │                              │
│          │  │  Isolation Forest       │  │                              │
│          │  │  τ1=−0.4459 τ2=−0.6027  │  │                              │
│          │  │  → PERMIT/LIMIT/BLOCK   │  │                              │
│          │  └───────────┬─────────────┘  │                              │
│          │              │                │                              │
│          │  ┌───────────▼─────────────┐  │                              │
│          │  │  dashboard_web.py :8080 │  │◄── navegador del operador   │
│          │  │  Telegram alerts        │  │◄── teléfono del operador    │
│          │  └─────────────────────────┘  │                              │
│          └───────────────┬───────────────┘                              │
│                          │  SSH + comandos ipset                        │
│                          ▼                                              │
│          ┌───────────────────────────────┐                              │
│          │   Ubuntu Servidor             │                              │
│          │   192.168.0.120               │                              │
│          │                               │                              │
│          │   nginx  :80                  │                              │
│          │   sshd   :22                  │                              │
│          │                               │                              │
│          │  ┌─────────────────────────┐  │                              │
│          │  │  iptables + ipset       │  │                              │
│          │  │  ppi_blocked  → DROP    │  │  ◄── bloqueo en kernel      │
│          │  │  ppi_limited  → LIMIT   │  │  ◄── rate 100 pkt/s         │
│          │  └─────────────────────────┘  │                              │
│          └───────────────────────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Notas para PPT / draw.io

- **Colores sugeridos:**
  - Desktop (Win11): azul claro
  - Kali (atacante): rojo
  - Sensor: verde oscuro / teal (es el core del sistema)
  - Servidor: gris azulado
  - Flechas de tráfico normal: azul
  - Flechas de tráfico anómalo: rojo con trazo discontinuo
  - Flechas de control (sensor → servidor): naranja

- **Etiquetas de flechas:**
  - Win11 → Red: "HTTP / SSH / SCP (normal)"
  - Kali → Red: "SYN flood / BF SSH / UDP flood (anómalo)"
  - Red → Sensor ens35: "todo el tráfico (modo pasivo)"
  - Sensor → Servidor: "sudo ipset add ppi_blocked <IP>"
  - Sensor → Navegador: "SSE :8080"
  - Sensor → Teléfono: "Telegram API"

- **Componentes internos del sensor a mostrar:**
  - Suricata (captura) → eve.json → Motor de decisión → IF model → acción
  - Dashboard + Telegram como salidas laterales

- **Leyenda recomendada:**
  - 🔵 Tráfico legítimo
  - 🔴 Tráfico anómalo
  - 🟠 Control inline (respuesta automática)
