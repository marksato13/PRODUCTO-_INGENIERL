# Informe de Resultados — Sistema de Detección Temprana de Comportamientos Anómalos en Redes de Datos

**Universidad Peruana Unión — Proyecto de Investigación (PPI)**
**Estudiante:** Rubén Mark Salazar Tocas
**Asesores:** Ing. Nemias Saboya Rios · Ing. Fernando Manuel Asin Gomez
**Fecha:** Junio 2026

---

## 1. Resumen Ejecutivo

Se diseñó, implementó y validó un sistema de detección temprana de comportamientos anómalos en redes de datos universitarias, basado en el algoritmo **Isolation Forest** entrenado sobre 14 features extraídas de flows de red capturados con **Suricata 7.0.3**. El sistema opera en modo inline sobre el sensor de red, emitiendo decisiones de control de tráfico (**PERMIT / LIMIT / BLOCK**) en tiempo real mediante `iptables/ipset`.

### Métricas finales del sistema

| Métrica | Valor obtenido | Requisito |
|---|---|---|
| AUC-ROC | **0.8998** | ≥ 0.85 |
| Precisión | **99.54 %** | — |
| Recall (TPR @ τ1) | **99.40 %** | — |
| F1-Score | **0.9947** | — |
| Latencia P95 (pipeline completo) | **34.8 ms** | < 500 ms |
| Interrupción de Tráfico Legítimo (ITL) | **0 %** | — |
| Disponibilidad del motor | **100 %** | — |
| Corridas de validación F6 completadas | **40 / 40** | — |

El sistema **cumple todos los requisitos definidos** para el PPI. La latencia de decisión es 14× inferior al límite establecido y no se registró ninguna interrupción de tráfico legítimo durante las 40 corridas de validación.

