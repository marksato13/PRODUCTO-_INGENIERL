#!/usr/bin/env python3
"""
clasificador.py — Módulo de clasificación de anomalías PPI UPeU 2026
Asigna tipo, gravedad, impacto y score de riesgo (0-100) a cada decisión.

Integración: importar en motor_decision.py
  from clasificador import clasificar

Retorna dict con:
  tipo, nivel, gravedad, impacto, score_riesgo, etiqueta_soc
"""

import ipaddress

# ── Constantes de clasificación ──────────────────────────────────────────────
TAU1 = -0.4973   # PERMIT / LIMIT
TAU2 = -0.6873   # LIMIT  / BLOCK

# Niveles de anomalía
NIVEL_BAJO    = "BAJO"
NIVEL_MEDIO   = "MEDIO"
NIVEL_ALTO    = "ALTO"
NIVEL_CRITICO = "CRITICO"

# Gravedades (CVSS-like)
GRAVEDAD_BAJA     = "BAJA"      # CVSS 0.1–3.9
GRAVEDAD_MODERADA = "MODERADA"  # CVSS 4.0–6.9
GRAVEDAD_ALTA     = "ALTA"      # CVSS 7.0–8.9
GRAVEDAD_CRITICA  = "CRITICA"   # CVSS 9.0–10.0

# Tipos de impacto
IMPACTO_RECONOCIMIENTO     = "RECONOCIMIENTO"
IMPACTO_SATURACION         = "SATURACION"
IMPACTO_ACCESO_NO_AUTORIZADO = "ACCESO_NO_AUTORIZADO"
IMPACTO_INTERRUPCION       = "INTERRUPCION_SERVICIO"
IMPACTO_GENERICO           = "ANOMALIA_GENERICA"

# Puertos conocidos
PUERTO_SSH  = 22
PUERTO_HTTP = 80
PUERTO_DNS  = 53
PUERTO_HTTPS = 443


def _score_riesgo(if_score: float, accion: str, boost: int = 0) -> int:
    """
    Score de riesgo compuesto [0-100].
    S_modelo = normalización del IF score respecto a TAU1/TAU2
    S_accion = penalización por acción aplicada
    boost    = puntos adicionales por detector temporal (brute force, HTTP abuse)
    """
    # Componente del modelo (0-50): más negativo = mayor riesgo
    s_modelo = min(max((-if_score - 0.4) / 0.35 * 50, 0), 50)
    # Componente de acción (0-50)
    s_accion = 50 if accion == 'BLOCK' else (25 if accion == 'LIMIT' else 0)
    return min(int(s_modelo + s_accion + boost), 100)


def clasificar(
    e: dict,
    if_score: float,
    accion: str,
    dest_port: int,
    proto: str,
    detector: str = None,   # 'BRUTE_FORCE' | 'HTTP_ABUSE' | None
    bf_intentos: int = 0,
    http_requests: int = 0,
) -> dict:
    """
    Clasifica un flow anómalo y retorna su perfil completo.

    Parámetros:
        e           : evento EVE JSON original
        if_score    : anomaly score del Isolation Forest
        accion      : 'PERMIT' | 'LIMIT' | 'BLOCK'
        dest_port   : puerto destino del flow
        proto       : protocolo ('TCP' | 'UDP' | 'ICMP')
        detector    : 'BRUTE_FORCE' | 'HTTP_ABUSE' | None (solo modelo)
        bf_intentos : intentos SSH en ventana (para brute force)
        http_requests: requests HTTP en ventana (para HTTP abuse)

    Retorna dict con: tipo, nivel, gravedad, impacto, score_riesgo,
                      cvss_base, mitre_id, etiqueta_soc, descripcion
    """
    proto_up = proto.upper() if proto else ''
    flow = e.get('flow', {})
    pts  = flow.get('pkts_toserver', 0) or 0
    ptc  = flow.get('pkts_toclient', 0) or 0
    bts  = flow.get('bytes_toserver', 0) or 0
    btc  = flow.get('bytes_toclient', 0) or 0

    # ── Regla 1: Brute Force SSH (detector temporal tiene prioridad) ──────────
    if detector == 'BRUTE_FORCE' or (dest_port == PUERTO_SSH and bf_intentos >= 5):
        nivel    = NIVEL_CRITICO if bf_intentos >= 15 else NIVEL_ALTO
        gravedad = GRAVEDAD_CRITICA
        return {
            'tipo':        'BRUTE_FORCE_SSH',
            'nivel':       nivel,
            'gravedad':    gravedad,
            'impacto':     IMPACTO_ACCESO_NO_AUTORIZADO,
            'score_riesgo': _score_riesgo(if_score, accion, boost=40),
            'cvss_base':   9.8,
            'mitre_id':    'T1110 — Brute Force / T1110.001 — Password Guessing',
            'mitre_ta':    'TA0006 — Credential Access',
            'etiqueta_soc': f'BF-SSH | {bf_intentos} intentos/60s | {accion}',
            'descripcion': f'Intento sistemático de credenciales SSH: {bf_intentos} intentos en ventana 60s',
        }

    # ── Regla 2: HTTP Abuse (detector temporal) ───────────────────────────────
    if detector == 'HTTP_ABUSE' or (dest_port == PUERTO_HTTP and http_requests >= 50):
        nivel = NIVEL_CRITICO if http_requests >= 100 else NIVEL_ALTO
        return {
            'tipo':        'HTTP_ABUSE',
            'nivel':       nivel,
            'gravedad':    GRAVEDAD_ALTA,
            'impacto':     IMPACTO_INTERRUPCION,
            'score_riesgo': _score_riesgo(if_score, accion, boost=30),
            'cvss_base':   7.5,
            'mitre_id':    'T1498.002 — Reflection Amplification (App Layer)',
            'mitre_ta':    'TA0040 — Impact',
            'etiqueta_soc': f'HTTP-ABUSE | {http_requests} req/30s | {accion}',
            'descripcion': f'Abuso de capa de aplicación HTTP: {http_requests} requests en 30s',
        }

    # ── Regla 3: ICMP Flood ────────────────────────────────────────────────────
    if proto_up in ('ICMP', 'IPV6-ICMP'):
        return {
            'tipo':        'ICMP_FLOOD',
            'nivel':       NIVEL_MEDIO,
            'gravedad':    GRAVEDAD_MODERADA,
            'impacto':     IMPACTO_SATURACION,
            'score_riesgo': _score_riesgo(if_score, accion),
            'cvss_base':   5.8,
            'mitre_id':    'T1498 — Network Denial of Service',
            'mitre_ta':    'TA0040 — Impact',
            'etiqueta_soc': f'ICMP-FLOOD | score={if_score:.4f} | {accion}',
            'descripcion': 'Inundación ICMP: saturación de buffer de red con echo requests',
        }

    # ── Regla 4: UDP Flood (dest_port=53 o UDP genérico de alto volumen) ──────
    if proto_up == 'UDP':
        nivel = NIVEL_ALTO if if_score <= TAU2 else NIVEL_MEDIO
        return {
            'tipo':        'UDP_FLOOD',
            'nivel':       nivel,
            'gravedad':    GRAVEDAD_ALTA,
            'impacto':     IMPACTO_SATURACION,
            'score_riesgo': _score_riesgo(if_score, accion),
            'cvss_base':   7.5,
            'mitre_id':    'T1498.001 — Direct Network Flood (UDP)',
            'mitre_ta':    'TA0040 — Impact',
            'etiqueta_soc': f'UDP-FLOOD | port={dest_port} | score={if_score:.4f} | {accion}',
            'descripcion': f'Inundación UDP puerto {dest_port}: saturación de ancho de banda',
        }

    # ── Regla 5: Port Scan (TCP, bajo bytes, alto variedad de puertos) ─────────
    # Heurística: flows muy cortos TCP con few bytes = scan probe
    dur = flow.get('end', '') == flow.get('start', '')  # duración ~0
    es_scan = (proto_up == 'TCP'
               and bts < 200       # pocos bytes enviados
               and btc < 200       # pocos bytes recibidos
               and pts <= 3)       # muy pocos paquetes (SYN/SYN-ACK/RST)

    if es_scan:
        return {
            'tipo':        'PORT_SCAN',
            'nivel':       NIVEL_MEDIO,
            'gravedad':    GRAVEDAD_MODERADA,
            'impacto':     IMPACTO_RECONOCIMIENTO,
            'score_riesgo': _score_riesgo(if_score, accion),
            'cvss_base':   4.0,
            'mitre_id':    'T1046 — Network Service Discovery',
            'mitre_ta':    'TA0007 — Discovery',
            'etiqueta_soc': f'PORT-SCAN | dst:{dest_port} | score={if_score:.4f} | {accion}',
            'descripcion': f'Reconocimiento activo: sondeo TCP puerto {dest_port} (pkts={pts}, bytes={bts}B)',
        }

    # ── Regla 6: SYN Flood (TCP, alto pkt_ratio, alto volumen) ───────────────
    dur_val = max(
        (lambda f: float(f) if f else 0.001)(
            str(e.get('flow', {}).get('end', ''))[:0]),
        0.001
    )
    pkt_rate_est = (pts + ptc) / max(dur_val, 0.001) if dur_val > 0 else 1000
    es_syn = (proto_up == 'TCP'
              and pts > ptc        # asimétrico (server no responde)
              and bts > 0          # hay bytes enviados
              and if_score <= TAU1)

    if es_syn or (proto_up == 'TCP' and if_score <= TAU2):
        nivel = NIVEL_CRITICO if if_score <= TAU2 else NIVEL_ALTO
        return {
            'tipo':        'SYN_FLOOD',
            'nivel':       nivel,
            'gravedad':    GRAVEDAD_ALTA,
            'impacto':     IMPACTO_SATURACION,
            'score_riesgo': _score_riesgo(if_score, accion),
            'cvss_base':   7.5,
            'mitre_id':    'T1498.001 — Direct Network Flood (SYN)',
            'mitre_ta':    'TA0040 — Impact',
            'etiqueta_soc': f'SYN-FLOOD | score={if_score:.4f} | {accion}',
            'descripcion': f'Inundación SYN TCP: agotamiento tabla de conexiones (score={if_score:.4f})',
        }

    # ── Regla 7: Anomalía genérica (no identificada específicamente) ──────────
    nivel    = NIVEL_ALTO    if if_score <= TAU2 else NIVEL_MEDIO
    gravedad = GRAVEDAD_ALTA if if_score <= TAU2 else GRAVEDAD_MODERADA
    return {
        'tipo':        'GENERIC_ANOMALY',
        'nivel':       nivel,
        'gravedad':    gravedad,
        'impacto':     IMPACTO_GENERICO,
        'score_riesgo': _score_riesgo(if_score, accion),
        'cvss_base':   5.0,
        'mitre_id':    'T1498 — Network Denial of Service',
        'mitre_ta':    'TA0040 — Impact',
        'etiqueta_soc': f'ANOMALY | proto={proto_up} | score={if_score:.4f} | {accion}',
        'descripcion': f'Anomalía estadística no clasificada: score={if_score:.4f}, proto={proto_up}',
    }


def formato_log(clasificacion: dict, src_ip: str, dst: str) -> str:
    """Genera línea de log enriquecida con clasificación."""
    c = clasificacion
    return (
        f"tipo={c['tipo']} | nivel={c['nivel']} | gravedad={c['gravedad']} | "
        f"impacto={c['impacto']} | riesgo={c['score_riesgo']}/100 | "
        f"mitre={c['mitre_id'].split('—')[0].strip()} | "
        f"src={src_ip} dst={dst} | {c['etiqueta_soc']}"
    )


def formato_telegram(clasificacion: dict, src_ip: str, accion: str, hora: str) -> str:
    """Genera mensaje Telegram enriquecido con clasificación."""
    c  = clasificacion
    emoji = {
        'PORT_SCAN':    '🔍',
        'SYN_FLOOD':    '🌊',
        'UDP_FLOOD':    '💧',
        'ICMP_FLOOD':   '📡',
        'HTTP_ABUSE':   '🌐',
        'BRUTE_FORCE_SSH': '🔑',
        'GENERIC_ANOMALY': '⚠️',
    }.get(c['tipo'], '🚨')

    nivel_emoji = {
        'BAJO': '🟢', 'MEDIO': '🟡', 'ALTO': '🟠', 'CRITICO': '🔴'
    }.get(c['nivel'], '⚫')

    return (
        f"{emoji} PPI ALERTA — {c['tipo']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Accion   : {accion}\n"
        f"IP       : {src_ip}\n"
        f"Gravedad : {nivel_emoji} {c['gravedad']}\n"
        f"Nivel    : {c['nivel']}\n"
        f"Impacto  : {c['impacto']}\n"
        f"Riesgo   : {c['score_riesgo']}/100\n"
        f"MITRE    : {c['mitre_id'].split('—')[0].strip()}\n"
        f"Detalle  : {c['descripcion']}\n"
        f"Hora     : {hora}"
    )


if __name__ == '__main__':
    # Test de clasificación con eventos simulados
    print("="*60)
    print("TEST DEL CLASIFICADOR — PPI UPeU 2026")
    print("="*60)

    casos = [
        dict(desc="Port Scan B2",   proto='TCP', port=443, score=-0.651, accion='LIMIT',
             e={'flow':{'pkts_toserver':1,'pkts_toclient':0,'bytes_toserver':60,'bytes_toclient':0,'start':'2026-06-02T04:09:02+0000','end':'2026-06-02T04:09:02+0000'}}),
        dict(desc="SYN Flood B1",   proto='TCP', port=80,  score=-0.676, accion='BLOCK',
             e={'flow':{'pkts_toserver':8,'pkts_toclient':2,'bytes_toserver':480,'bytes_toclient':120,'start':'2026-06-02T03:12:25+0000','end':'2026-06-02T03:12:25+0000'}}),
        dict(desc="UDP Flood B3",   proto='UDP', port=53,  score=-0.714, accion='BLOCK',
             e={'flow':{'pkts_toserver':6,'pkts_toclient':0,'bytes_toserver':360,'bytes_toclient':0,'start':'2026-06-02T04:09:29+0000','end':'2026-06-02T04:09:29+0000'}}),
        dict(desc="ICMP Flood B4",  proto='ICMP',port=0,   score=-0.691, accion='BLOCK',
             e={'flow':{'pkts_toserver':4,'pkts_toclient':0,'bytes_toserver':120,'bytes_toclient':0,'start':'2026-06-02T04:13:41+0000','end':'2026-06-02T04:13:41+0000'}}),
        dict(desc="HTTP Abuse B5",  proto='TCP', port=80,  score=-0.502, accion='LIMIT',
             e={'flow':{'pkts_toserver':4,'pkts_toclient':3,'bytes_toserver':400,'bytes_toclient':555,'start':'2026-06-04T15:10:00+0000','end':'2026-06-04T15:10:00+0000'}},
             detector='HTTP_ABUSE', http_requests=100),
        dict(desc="Brute Force B6", proto='TCP', port=22,  score=-0.435, accion='BLOCK',
             e={'flow':{'pkts_toserver':3,'pkts_toclient':2,'bytes_toserver':300,'bytes_toclient':200,'start':'2026-06-03T18:50:03+0000','end':'2026-06-03T18:50:03+0000'}},
             detector='BRUTE_FORCE', bf_intentos=15),
    ]

    for caso in casos:
        c = clasificar(
            e=caso['e'],
            if_score=caso['score'],
            accion=caso['accion'],
            dest_port=caso['port'],
            proto=caso['proto'],
            detector=caso.get('detector'),
            bf_intentos=caso.get('bf_intentos', 0),
            http_requests=caso.get('http_requests', 0),
        )
        print(f"\n  [{caso['desc']}]")
        print(f"    tipo={c['tipo']} | nivel={c['nivel']} | gravedad={c['gravedad']}")
        print(f"    impacto={c['impacto']} | riesgo={c['score_riesgo']}/100")
        print(f"    mitre={c['mitre_id']}")
        print(f"    log: {formato_log(c, '192.168.0.100', '192.168.0.120:'+str(caso['port']))}")
        print(f"\n    TELEGRAM:")
        for line in formato_telegram(c, '192.168.0.100', caso['accion'], '2026-06-14 04:30:00').split('\n'):
            print(f"      {line}")
