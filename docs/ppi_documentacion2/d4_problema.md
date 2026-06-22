# Diagrama 4 — Situación Problemática
**Slide 2 del PPT (gancho inicial)**

---

## Versión línea de tiempo (para slide 2)

```
                      ATAQUE EN CURSO — NADIE LO SABE
                      ─────────────────────────────────

  02:00 AM          03:00 AM          08:00 AM          ??? días después
     │                 │                 │                    │
     ▼                 ▼                 ▼                    ▼
┌─────────┐       ┌─────────┐       ┌─────────┐        ┌─────────────┐
│ Atacante│       │Servidor │       │  TI     │        │  Respuesta  │
│ inicia  │──────▶│ empieza │──────▶│ llega   │───────▶│  reactiva   │
│SYN flood│       │a fallar │       │ a la    │        │             │
│         │       │         │       │ oficina │        │ demasiado   │
└─────────┘       └─────────┘       └─────────┘        │   tarde     │
                                         │              └─────────────┘
                                    "reviso logs"
                                    "ya era tarde"


        ◄────────────────────────────────────────────────────────────►
                              207 días
                  (tiempo promedio de detección — IBM 2023)
```

---

## Versión comparativa ANTES / DESPUÉS (para argumentar la solución)

```
        SIN ESTE SISTEMA              CON ESTE SISTEMA
        ─────────────────             ─────────────────

  T+0   Atacante inicia flood    T+0   Atacante inicia flood
        │                               │
  T+??  IDS por firma:           T+53s  Motor detecta: SOSPECHOSO
        "no conozco este                │  score=−0.4832 → LIMIT
         patrón — ignoro"               │
        │                        T+60s  Motor confirma: ANOMALÍA
  T+??  Admin recibe reporte             🚫 BLOCK — ipset DROP
        días o semanas después          │
        │                        T+60s  📱 Telegram: alerta al operador
  T+??  Acción manual:                  │
        "agregar regla al        T+60s  🖥️  Dashboard: IP bloqueada
         firewall"                       │
        │                        T+300s Bloqueo expira — si reincide:
  Daño: servicio caído                   BLOCK#2 30min → BLOCK#3 ∞
        datos comprometidos
        reputación afectada              ✅ Sin intervención humana
```

---

## Diagrama árbol de objetivos (Slide 4)

```
                    ┌─────────────────────────────────────────────┐
                    │            OBJETIVO GENERAL                  │
                    │                                             │
                    │  Desarrollar un sistema de detección        │
                    │  temprana y control inline de               │
                    │  comportamientos anómalos en redes,         │
                    │  con respuesta automática en tiempo real     │
                    └────────────────┬────────────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │       OE1        │  │       OE2        │  │       OE3        │
   │                  │  │                  │  │                  │
   │  Pipeline de     │  │  Modelo de       │  │  Motor de        │
   │  captura y       │  │  detección       │  │  decisión +      │
   │  procesamiento   │  │  AUC-ROC ≥ 0.80  │  │  validación      │
   │  de tráfico real │  │  con datos reales│  │  40 corridas     │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
          │                      │                      │
   F1 + F2                    F2 + F3             F3 + F4 + F5 + F6
   47 capturas             AUC = 0.8998           Disp. 100% ITL 0%
   14 features             Prec = 99.54%          P95 = 34.8ms
   667K flujos             Rec  = 99.40%          Lead = 62s
```

---

## Notas para PPT / draw.io

**Diagrama slide 2 (gancho):**
- Usar línea de tiempo horizontal con íconos grandes
- La cifra "207 días" en rojo, grande, centrada — es el impacto
- Fondo oscuro, texto blanco — efecto dramático

**Diagrama comparativo ANTES/DESPUÉS:**
- Dos columnas lado a lado
- Columna izquierda: fondo gris / rojo suave
- Columna derecha: fondo verde suave
- Las marcas de tiempo T+60s en la columna derecha resaltan la rapidez

**Árbol de objetivos (slide 4):**
- OG arriba en azul oscuro
- OE1, OE2, OE3 en azul medio, mismo tamaño
- Resultados debajo de cada OE en texto pequeño gris
- Conectar con líneas limpias
