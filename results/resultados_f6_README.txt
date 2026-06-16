================================================================
CAMPOS DEL CSV resultados_f6_completo.csv — NOTAS ACLARATORIAS
PPI — Universidad Peruana Unión 2026
================================================================

flows_normal (columna):
  Valor ACUMULATIVO total de flows procesados por el motor desde
  inicio de F6 (no por corrida individual). Para corridas 1–10
  (grupo normal) el acumulado parte de 0 porque el motor inicia
  fresco; salta a 6,500 en corrida 11 al registrar el primer
  evento WARNING (ANOMALÍA/SOSPECHOSO).

latencia_ms (columna):
  Latencia ACUMULADA de la ventana de análisis de cada corrida
  (suma de latencias de todos los flows procesados en ~316 s),
  NO la latencia por flow individual.
  La latencia por flow medida independientemente:
    Media = 34.5 ms | P95 = 34.8 ms | Umbral req. < 500 ms → CUMPLE
  Ver: results/latencia_pipeline.txt

flows_anom = 0 en corridas 12–40 (grupos mixto/reeval/final):
  Comportamiento CORRECTO. Tras la detección en corrida 11, el
  motor retiene 192.168.0.100 en el set in-memory 'bloqueados'.
  Los flows subsiguientes de esa IP se procesan a nivel DEBUG
  (no WARNING), por eso no aparecen en el conteo. La IP sigue
  bloqueada en ipset → disponibilidad = 100% confirmada.
================================================================
