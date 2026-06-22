#!/usr/bin/env bash
# F5 — Valida reentrenamiento automático (cron + métricas post-retrain)
PROJECT="/home/m4rk/ppi-surikata-producto"
echo "=== F5: APRENDIZAJE CONTINUO (reentrenamiento) ==="
echo ""

# Cron job configurado
if crontab -l 2>/dev/null | grep -q "f5_reentrenar"; then
    echo "  ✅ PASS  Cron job F5 configurado:"
    crontab -l | grep "f5_reentrenar" | sed 's/^/    /'
else
    echo "  ❌ FAIL  No hay cron job para reentrenamiento"
    echo "  → Para añadir: crontab -e y agregar:"
    echo "    0 3 * * * cd $PROJECT && /home/m4rk/ppi-sensor/venv/bin/python3 scripts/f5_reentrenar_if.py"
fi

echo ""

# Métricas post-retrain IF
if [ -f "$PROJECT/results/metricas_f5_if.txt" ]; then
    echo "  ✅ PASS  metricas_f5_if.txt existe"
    echo "  Última entrada:"
    tail -5 "$PROJECT/results/metricas_f5_if.txt" | sed 's/^/    /'
else
    echo "  ⚠️   metricas_f5_if.txt no existe (aún no se ejecutó F5)"
fi

echo ""

# Métricas post-retrain XGBoost
if [ -f "$PROJECT/results/metricas_f5_xgboost.txt" ]; then
    echo "  ✅ PASS  metricas_f5_xgboost.txt existe"
    tail -3 "$PROJECT/results/metricas_f5_xgboost.txt" | sed 's/^/    /'
else
    echo "  ⚠️   metricas_f5_xgboost.txt no existe"
fi

echo ""

# Log de cron XGBoost
if [ -f "$PROJECT/results/cron_f5_xgb.log" ]; then
    echo "  Últimas 3 líneas de cron_f5_xgb.log:"
    tail -3 "$PROJECT/results/cron_f5_xgb.log" | sed 's/^/    /'
fi

# Validar que modelos tienen fecha reciente
echo ""
echo "  Fechas de los modelos actuales:"
ls -lh "$PROJECT/models/isolation_forest.pkl" "$PROJECT/models/predictor_modelo_v2.pkl" 2>/dev/null \
    | awk '{print "    " $6, $7, $8, $9}'
