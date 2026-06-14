# FASE 1 — Entorno de Laboratorio

**Proyecto:** Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos  
**Institución:** Universidad Peruana Unión — PPI 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez  
**Fecha de cierre:** 10 de mayo 2026  

---

## Objetivo de la fase

Desplegar y configurar el entorno de laboratorio virtualizado que sirve como plataforma de experimentación para el sistema de detección. Esto incluye la creación de las máquinas virtuales, la configuración de la red, la instalación del sensor Suricata y la validación de que el flujo de captura de tráfico funciona correctamente.

---

## 1. Topología de red implementada

Se desplegaron 7 máquinas virtuales en VMware sobre la red `192.168.0.0/24` con IPs estáticas:

| VM | IP | Sistema Operativo | Rol |
|---|---|---|---|
| pfSense | 192.168.0.1 | pfSense | Gateway / firewall de laboratorio |
| Win11 | 192.168.0.10 | Windows 11 | Cliente adicional |
| Ubuntu Desktop | **192.168.0.20** | Ubuntu 22.04 Desktop | Origen de tráfico normal · Claude Code |
| Kali Linux | **192.168.0.100** | Kali Linux 2024 | Origen de tráfico anómalo controlado |
| Ubuntu Suricata | **192.168.0.110** | Ubuntu Server 22.04 | **Sensor principal** (Suricata) |
| Ubuntu Server | **192.168.0.120** | Ubuntu Server 22.04 | Objetivo: nginx (80) + SSH (22) |
| Ubuntu BigData | 192.168.0.130 | Ubuntu Server 22.04 | Almacenamiento de datos |

Las VMs en negrita son las que participan activamente en los escenarios de captura.

**Verificación de conectividad:** Se confirmó ping exitoso entre todas las VMs antes de cerrar la fase.

**Usuario en todas las VMs:** `m4rk`  
**Autenticación SSH:** claves configuradas desde Desktop → Sensor y Desktop → Server.

---

## 2. Instalación de Suricata

### Versión instalada
```
Suricata 7.0.3 RELEASE
```

### Ubicación
Instalado en el sensor: `192.168.0.110`

### Comando de ejecución (modo demonio)
```bash
suricata -i ens35 -D
```

### Interfaz de captura configurada

En `/etc/suricata/suricata.yaml`:

```yaml
af-packet:
  - interface: ens35    # Interfaz que monitorea la LAN del laboratorio
```

La interfaz `ens35` es la que conecta el sensor a la red `192.168.0.0/24`, permitiendo la captura promiscua de todo el tráfico entre las VMs.

### Verificación del servicio activo

```bash
ssh m4rk@192.168.0.110 "systemctl is-active suricata"
# Salida: active

ssh m4rk@192.168.0.110 "ps aux | grep suricata"
# Salida: root  suricata -i ens35 -D
```

---

## 3. Configuración del output EVE JSON

Suricata genera eventos en formato JSON en el archivo:

```
/var/log/suricata/eve.json
```

Este archivo es el punto de entrada del pipeline de detección. Se configuró para emitir eventos de tipo `flow` con los campos mínimos necesarios para el modelo:

| Campo | Descripción |
|---|---|
| `timestamp` | Momento del cierre del flow |
| `flow_id` | Identificador único del flow |
| `event_type` | Tipo de evento (`flow`, `alert`, `ssh`, etc.) |
| `src_ip` / `dest_ip` | IPs origen y destino |
| `src_port` / `dest_port` | Puertos origen y destino |
| `proto` | Protocolo (TCP, UDP, ICMP) |
| `flow.pkts_toserver` / `flow.pkts_toclient` | Conteo de paquetes |
| `flow.bytes_toserver` / `flow.bytes_toclient` | Bytes transferidos |
| `flow.start` / `flow.end` | Timestamps de inicio y fin del flow |

**Ejemplo real de evento flow capturado:**
```json
{
  "timestamp": "2026-06-02T04:09:02+0000",
  "flow_id": 188776050051964,
  "in_iface": "ens35",
  "event_type": "flow",
  "src_ip": "192.168.0.100",
  "src_port": 42112,
  "dest_ip": "192.168.0.120",
  "dest_port": 80,
  "proto": "TCP",
  "app_proto": "http",
  "flow": {
    "pkts_toserver": 6,
    "pkts_toclient": 4,
    "bytes_toserver": 492,
    "bytes_toclient": 555,
    "start": "2026-06-02T04:09:02+0000",
    "end": "2026-06-02T04:09:02+0000"
  }
}
```

---

## 4. Validación formal de Suricata

Se ejecutó el script de validación `revisar_suricata.sh` el **10 de mayo de 2026**, generando el archivo de evidencia formal.

### Script de validación

**Ubicación:** `scripts/validation/revisar_suricata.sh`

El script verifica automáticamente:
1. Que Suricata esté corriendo (`systemctl is-active`)
2. La versión instalada (`suricata -V`)
3. El proceso activo (`ps aux | grep suricata`)
4. La interfaz de red configurada (`ip a`)
5. La existencia y contenido de `eve.json`
6. Que haya eventos de tipo `flow` disponibles
7. Que haya eventos de tipo `stats` (validación del sensor)

### Evidencia generada

**Ubicación:** `scripts/validation/suricata_revision.txt`

Extracto del contenido:
```
REVISION SURICATA
Fecha: dom 10 may 2026 02:20:57 UTC

===== suricata -V =====
This is Suricata version 7.0.3 RELEASE

===== ps aux | grep suricata =====
root  suricata -i ens35 -D

===== Verificación eve.json =====
Archivo existe: /var/log/suricata/eve.json ✓
Eventos flow presentes ✓
Eventos stats presentes ✓
Interfaz de captura: ens35 ✓
```

---

## 5. Servicios del servidor objetivo (192.168.0.120)

Para que los escenarios de captura tuviesen tráfico realista, se configuraron los siguientes servicios en el servidor:

### nginx (puerto 80)
```
/var/www/html/
├── index.html
├── info.html
├── health.html
└── files/
    ├── manual.txt
    ├── sample.csv
    └── archivo_grande.bin
```

### OpenSSH (puerto 22)
Servicio SSH estándar activo, usado tanto para tráfico legítimo (escenarios A2) como objetivo de brute force (escenario B6).

---

## 6. Criterios de cierre de F1

| Criterio | Estado |
|---|---|
| VMs operativas en VMware | ✅ |
| Red LAN configurada con IPs fijas | ✅ |
| Conectividad ping entre todas las VMs | ✅ |
| Suricata 7.0.3 instalado en 192.168.0.110 | ✅ |
| Interfaz ens35 configurada como captura | ✅ |
| eve.json generando eventos flow | ✅ |
| Campos mínimos validados en eve.json | ✅ |
| Script de validación ejecutado y evidencia guardada | ✅ |
| nginx y SSH activos en servidor objetivo | ✅ |

**F1 CERRADA ✅ — 10 de mayo 2026**

---

## Archivos de referencia

| Archivo | Ruta en el sensor | Descripción |
|---|---|---|
| `revisar_suricata.sh` | `scripts/validation/revisar_suricata.sh` | Script de validación automatizada |
| `suricata_revision.txt` | `scripts/validation/suricata_revision.txt` | **Evidencia formal F1** |
| `suricata.yaml` | `/etc/suricata/suricata.yaml` | Configuración activa de Suricata |
| `eve.json` | `/var/log/suricata/eve.json` | Output en tiempo real del sensor |

> **Nota:** Todos los archivos residen en el sensor `192.168.0.110` bajo el directorio base  
> `/home/m4rk/ppi-surikata-producto/`
