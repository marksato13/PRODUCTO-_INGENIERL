# F8 — Dashboard de Monitoreo en Tiempo Real
## Estado: ✅ COMPLETA

## Objetivo
Visibilidad operacional completa del sistema mediante interfaz web en tiempo real.

## Componentes
- Servidor Flask en puerto 8080
- Server-Sent Events (SSE) para push al navegador
- Servicio: ppi-dashboard.service (restart=always, venv)
- Acceso: http://192.168.0.110:8080

## Paneles
| Panel | Fuente | Actualización |
|---|---|---|
| Gauge P(ataque) | predictor.log | Cada 2s (SSE) |
| Feed ALERTA/BLOCK/LIMIT | motor_decision.log | Tiempo real (SSE) |
| Tabla IPs bloqueadas | ipset + motor log | Cada 30s (cache) |
| Estadísticas motor | motor_decision.log | Tiempo real (SSE) |

## Criterios de aceptación
- [x] CA-F8-01: Dashboard accesible en http://192.168.0.110:8080
- [x] CA-F8-02: Gauge muestra P(ataque) actualizado por ciclo del predictor
- [x] CA-F8-03: Feed muestra eventos en tiempo real sin polling del cliente
- [x] CA-F8-04: Tabla bloqueados refleja estado real del ipset
- [x] CA-F8-05: Servicio reinicia automáticamente si cae
- [ ] CA-F8-06: Gauge sube ANTES que BLOCK en tabla (requiere F7 v2 completa)

## Nota
CA-F8-06 depende de F7. El código del dashboard NO requiere cambios.
Cuando F7 esté lista, el gauge subirá en T≈2s y BLOCK aparecerá en T≈5s.
