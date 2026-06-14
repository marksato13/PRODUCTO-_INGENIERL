# F6-04: Implementaciones Adicionales y Trabajo Futuro

**Proyecto:** Sistema de Detección Temprana de Anomalías en Redes — PPI UPeU 2026  
**Estudiante:** Rubén Mark Salazar Tocas  
**Fase:** F6 — Validación y Resultados  
**Documento:** F6-04 — Implementaciones Adicionales y Trabajo Futuro  
**Fecha:** 2026-06-14

---

# BLOQUE 6 — IMPLEMENTACIONES ADICIONALES

## 6.1 Criterio de Evaluación

Para cada integración propuesta se evalúa: **¿Resuelve un problema real del sistema actual?** Solo se proponen mejoras que agregan valor medible. Se descarta lo que sería "complejidad por complejidad".

| Integración | ¿Resuelve problema real? | Prioridad | Veredito |
|---|---|---|---|
| Nuevos modelos (Ensemble IF+AE) | Sí — detecta low-and-slow APT mejor | Media | ✅ PROPONER |
| Aprendizaje incremental (River) | Sí — actualización continua sin batch | Alta | ✅ PROPONER |
| Integración Wazuh | Sí — correlación con logs host | Alta | ✅ PROPONER |
| Integración Elastic/ELK | Sí — búsqueda y auditoría avanzada | Media | ✅ PROPONER |
| Integración Grafana | Sí — dashboard web operacional | Alta | ✅ PROPONER |
| Integración SIEM genérico (CEF/LEEF) | Sí — interoperabilidad empresarial | Baja | ✅ PROPONER |
| Deep Learning LSTM | Resuelve problema que IF ya resuelve | Baja | ⚠️ Solo futuro |
| Nuevos escenarios de ataque | Sí — ampliar cobertura validada | Alta | ✅ PROPONER |

## 6.2 Nuevos Modelos — Ensemble IF + Autoencoder

### Problema que resuelve
El IF detecta anomalías por aislación estadística global. Los ataques "low-and-slow" (APT que imitan tráfico normal en velocidad pero tienen patrones de payload o secuencia anómalos) pueden tener scores IF cercanos al umbral. Un Autoencoder aprende la estructura de reconstrucción del tráfico normal; los ataques evasivos tienen mayor error de reconstrucción.

### Beneficio esperado

| Métrica | Solo IF (actual) | Ensemble IF+AE (estimado) |
|---|---|---|
| Recall general | 99.3% | 99.5–99.8% |
| Detección APT low-and-slow | ~40–60% | ~80–90% |
| Latencia adicional | 0ms | +5–15ms (CPU) o +1ms (GPU) |
| RAM adicional | 0 MB | +50–200 MB |

### Implementación propuesta

```python
# ensemble_detector.py — Fase 1 producción
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf

class EnsembleDetector:
    """
    Combina IF (anomalías globales) + Autoencoder (anomalías secuenciales)
    Score final = α × score_IF + (1−α) × score_AE
    """
    
    def __init__(self, alpha=0.7):
        self.alpha = alpha  # peso del IF (mayor = IF dominante)
        self.if_model = None
        self.ae_model = None
        self.threshold_ae = None
    
    def build_autoencoder(self, input_dim=14, encoding_dim=7):
        """Autoencoder simple: 14→7→14 con activación ReLU."""
        inputs = tf.keras.Input(shape=(input_dim,))
        encoded = tf.keras.layers.Dense(encoding_dim, activation='relu')(inputs)
        decoded = tf.keras.layers.Dense(input_dim, activation='linear')(encoded)
        self.ae_model = tf.keras.Model(inputs, decoded)
        self.ae_model.compile(optimizer='adam', loss='mse')
    
    def fit(self, X_normal):
        """Entrena IF y AE con tráfico normal."""
        # Entrenamiento IF (ya implementado)
        self.if_model = IsolationForest(n_estimators=300, contamination=0.05,
                                         random_state=42)
        self.if_model.fit(X_normal)
        
        # Entrenamiento AE
        self.build_autoencoder(input_dim=X_normal.shape[1])
        self.ae_model.fit(X_normal, X_normal, epochs=50, batch_size=32,
                         verbose=0, validation_split=0.1)
        
        # Umbral AE: percentil 95 del error de reconstrucción en datos normales
        recon = self.ae_model.predict(X_normal, verbose=0)
        errors = np.mean((X_normal - recon) ** 2, axis=1)
        self.threshold_ae = np.percentile(errors, 95)
    
    def score(self, X):
        """Score combinado: más negativo = más anómalo."""
        # IF score (normalizado a [0,1], 0=anómalo)
        if_raw = self.if_model.score_samples(X)
        if_norm = (if_raw - if_raw.min()) / (if_raw.max() - if_raw.min() + 1e-8)
        
        # AE score: error de reconstrucción normalizado (1=anómalo)
        recon = self.ae_model.predict(X, verbose=0)
        ae_errors = np.mean((X - recon) ** 2, axis=1)
        ae_norm = ae_errors / (self.threshold_ae + 1e-8)  # >1 = anómalo
        ae_score = 1 - np.clip(ae_norm, 0, 1)  # 0=anómalo, 1=normal
        
        # Ensemble: combinar (ambos en escala 0=anómalo, 1=normal)
        combined = self.alpha * if_norm + (1 - self.alpha) * ae_score
        # Convertir de vuelta a escala IF (negativo=anómalo)
        return combined - 1.0  # [−1, 0]
```

**Complejidad:** Media. Requiere TensorFlow (~200 MB), GPU recomendada para entrenamiento (no para inferencia CPU es suficiente). Estimado de implementación: 3–4 semanas.

## 6.3 Aprendizaje Incremental con River

### Problema que resuelve
El reentrenamiento batch actual requiere acumular 2000 flujos y reentrenar un IF completo (~1 segundo). Con River (librería de ML en streaming), el modelo se actualiza con cada nuevo flujo, adaptándose continuamente sin esperar lotes.

### Beneficio esperado

| Aspecto | Batch (actual) | Incremental (River) |
|---|---|---|
| Latencia de adaptación | Horas (espera lote de 2000) | Milisegundos (por flujo) |
| Costo de actualización | 1s reentrenamiento completo | <1ms por actualización |
| Gestión de concept drift | Reactiva (tras detección) | Proactiva (continua) |
| Complejidad de implementación | Ya implementado | Media (+2 semanas) |

### Implementación propuesta

```python
# incremental_detector.py
from river import anomaly, preprocessing

class IncrementalIF:
    """
    Wrapper de River HalfSpaceTrees: aproximación incremental del IF.
    Actualiza el modelo con cada nuevo flujo PERMIT.
    """
    
    def __init__(self, n_trees=25, height=15, window_size=1000):
        self.scaler = preprocessing.StandardScaler()
        self.model = anomaly.HalfSpaceTrees(
            n_trees=n_trees,
            height=height,
            window_size=window_size,
            seed=42
        )
    
    def learn_one(self, features: dict) -> float:
        """
        Actualiza el modelo con un flujo PERMIT y retorna el score.
        features: dict con las 14 features.
        """
        features_scaled = self.scaler.learn_one(features).transform_one(features)
        score = self.model.score_one(features_scaled)
        self.model.learn_one(features_scaled)
        return score  # 0=normal, 1=anómalo (invertido respecto a sklearn IF)
    
    def score_one(self, features: dict) -> float:
        """Solo score, sin actualizar."""
        features_scaled = self.scaler.transform_one(features)
        return self.model.score_one(features_scaled)
```

**Complejidad:** Baja. River es una librería Python liviana (~30 MB). Requiere modificar motor_decision.py para actualizar el modelo en cada decisión PERMIT. Estimado: 1–2 semanas.

## 6.4 Integración con Wazuh

### Problema que resuelve
Wazuh es un HIDS (Host-based IDS) que correlaciona logs del sistema operativo, autenticación y aplicaciones. Integrarlo con nuestro NIPS crea una vista unificada: cuando el IF detecta un ataque de red, Wazuh puede correlacionar si el mismo IP ya intentó autenticarse en el servidor, completando la cadena de ataque.

### Beneficio esperado
- Reducción de FN para ataques multi-vectoriales (red + host)
- Correlación automática: NIPS detecta SYN flood Y Wazuh detecta autenticación SSH fallida del mismo IP → severidad escalada
- Alertas enriquecidas con contexto del host (proceso, usuario, syscall)

### Implementación propuesta

```xml
<!-- /var/ossec/etc/rules/ppi_motor_rules.xml en el servidor Wazuh -->
<group name="ppi_motor,">

  <!-- Regla base: cualquier evento del motor PPI -->
  <rule id="100001" level="5">
    <program_name>ppi-motor</program_name>
    <description>PPI Motor: evento de detección de anomalía</description>
  </rule>

  <!-- BLOCK con severidad crítica -->
  <rule id="100002" level="12">
    <if_sid>100001</if_sid>
    <match>BLOCK</match>
    <description>PPI Motor: IP bloqueada por comportamiento anómalo</description>
  </rule>

  <!-- LIMIT con severidad media -->
  <rule id="100003" level="7">
    <if_sid>100001</if_sid>
    <match>LIMIT</match>
    <description>PPI Motor: IP limitada por comportamiento sospechoso</description>
  </rule>

  <!-- Correlación: BLOCK de red + SSH fallido en host = ataque confirmado -->
  <rule id="100010" level="15" frequency="3" timeframe="120">
    <if_matched_sid>100002</if_matched_sid>
    <if_matched_sid>5710</if_matched_sid>  <!-- Wazuh: SSH brute force -->
    <same_source_ip/>
    <description>CORR: Ataque confirmado - bloqueo de red + brute force SSH detectados</description>
    <group>ppi_correlation,attack_confirmed</group>
  </rule>

</group>
```

```python
# En motor_decision.py: enviar eventos a Wazuh via syslog
import syslog

def send_to_wazuh(src_ip: str, decision: str, score: float, trigger: str):
    """Envía evento al agente Wazuh local via syslog."""
    syslog.openlog(ident="ppi-motor", facility=syslog.LOG_LOCAL1)
    level = syslog.LOG_CRIT if decision == 'BLOCK' else syslog.LOG_WARNING
    syslog.syslog(level,
        f"decision={decision} src_ip={src_ip} score={score:.4f} trigger={trigger}")
    syslog.closelog()
```

**Complejidad:** Media. Requiere Wazuh agent en servidor (.120) y Wazuh manager en una VM adicional o servicio cloud. Estimado: 2–3 semanas.

## 6.5 Integración con Elasticsearch / ELK Stack

### Problema que resuelve
El motor_decision.log en archivo plano es suficiente para el MVP, pero no permite búsqueda, filtros, agregaciones o retención a largo plazo de forma eficiente. Elasticsearch provee almacenamiento indexado con búsqueda O(log n) y Kibana agrega capacidades de visualización sin código.

### Beneficio esperado
- Búsqueda en ~20ms sobre millones de eventos (vs. grep que escala linealmente)
- Dashboards Kibana pre-construidos sin código
- Alertas automáticas (Kibana Watcher o ElastAlert) basadas en reglas
- Retención y auditoría a largo plazo manejada automáticamente (ILM policies)

### Implementación propuesta

```ruby
# /etc/logstash/conf.d/ppi-motor.conf
input {
  file {
    path => "/home/m4rk/ppi-surikata-producto/results/motor_decision.log"
    start_position => "beginning"
    sincedb_path => "/var/lib/logstash/ppi-motor.sincedb"
    codec => plain { charset => "UTF-8" }
  }
}

filter {
  dissect {
    mapping => {
      "message" => "%{timestamp} | %{src_ip} | %{dst_ip} | %{dst_port} | %{proto} | %{score} | %{decision} | %{trigger} | %{corrida}"
    }
  }
  
  mutate {
    convert => {
      "dst_port" => "integer"
      "score" => "float"
    }
    strip => ["src_ip", "dst_ip", "proto", "decision", "trigger", "corrida"]
  }
  
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
  
  # Agregar campo de severidad
  if [decision] == "BLOCK" {
    mutate { add_field => { "severity" => "critical" "severity_num" => 3 } }
  } else if [decision] == "LIMIT" {
    mutate { add_field => { "severity" => "warning" "severity_num" => 2 } }
  } else {
    mutate { add_field => { "severity" => "info" "severity_num" => 1 } }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "ppi-motor-%{+YYYY.MM.dd}"
    template_name => "ppi-motor"
  }
  stdout { codec => rubydebug }
}
```

**Complejidad:** Alta. ELK stack requiere ~4 GB RAM mínimo. Para el laboratorio actual (7.8 GB), sería una VM adicional o servicio cloud (Elastic Cloud). Estimado: 3–4 semanas con VM adicional.

## 6.6 Integración con Grafana

### Problema que resuelve
El dashboard.py actual es un script terminal. Grafana provee dashboards web, alertas, acceso multi-usuario y paneles prediseñados — sin código de frontend.

### Beneficio esperado
- Dashboard accesible vía browser desde cualquier dispositivo en la red
- Alertas PagerDuty/Telegram nativos sin código adicional
- Panels de series de tiempo con zoom, correlación visual
- Multi-usuario con roles (admin, analista, auditor)

### Implementación propuesta

```yaml
# docker-compose-grafana.yml (alternativa ligera al ELK completo)
version: '3.8'
services:
  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    environment:
      INFLUXDB_DB: ppi_metrics
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: ppi_secure_2026
    volumes:
      - influxdb_data:/var/lib/influxdb2
  
  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ppi_grafana_2026
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - influxdb

volumes:
  influxdb_data:
  grafana_data:
```

```python
# metrics_shipper.py — envía motor_decision.log a InfluxDB
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import tailer

client = InfluxDBClient(url="http://localhost:8086", token="ppi_token_2026", org="ppi")
write_api = client.write_api(write_options=SYNCHRONOUS)

for line in tailer.follow(open('/home/m4rk/ppi-surikata-producto/results/motor_decision.log')):
    # Parsear línea y enviar métrica
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 7:
        point = (Point("motor_decision")
                 .tag("decision", parts[6])
                 .tag("proto", parts[4])
                 .field("score", float(parts[5]) if parts[5] != 'N/A' else 0.0)
                 .field("dst_port", int(parts[3]))
                 .tag("src_ip", parts[1]))
        write_api.write(bucket="ppi_metrics", record=point)
```

**Complejidad:** Media-Baja. Docker Compose simplifica el despliegue. InfluxDB + Grafana juntos usan ~1.2 GB RAM. Factible en el sensor actual (7.8 GB). Estimado: 1–2 semanas.

## 6.7 Nuevos Escenarios de Ataque

### Problema que resuelve
Las 40 corridas de F6 validan 6 tipos de ataque. Ampliar la cobertura fortalece la evidencia de generalización.

### Escenarios propuestos

| ID | Escenario | Herramienta | Categoría MITRE | Prioridad |
|---|---|---|---|---|
| B7 | DNS Amplification | dig + iptables spoofing | T1498.002 | Alta |
| B8 | Slowloris (HTTP DoS lento) | slowloris.py | T1499.001 | Alta |
| B9 | XMAS Scan | nmap -sX | T1046 | Media |
| B10 | FIN Scan | nmap -sF | T1046 | Media |
| B11 | ARP Spoofing | arpspoof | T1557.002 | Media |
| B12 | HTTPS Flood (TLS) | wrk --https | T1499.002 | Baja |

**Impacto esperado:** Con B7–B10 (los más importantes), el recall estimado sobre ataques ampliados sería 98.5–99% (algunos ataques lento como Slowloris requieren ventana de tiempo más larga para acumular evidencia). Estimado: 1 semana para implementar los 4 escenarios prioritarios.

---

# BLOQUE 7 — TRABAJO FUTURO

## 7.1 Corto Plazo (0 – 6 meses)

### Objetivo general
Consolidar el MVP en un sistema robusto y llevarlo a la primera exposición en entorno real (Fase 1 del roadmap).

| Tarea | Descripción | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|---|
| CP-01 | Modo MONITOR (log-only, sin bloqueo) | Permite Fase 1 sin riesgo | 3 días | CRÍTICA |
| CP-02 | Dashboard web con Grafana + InfluxDB | Operación sin terminal | 1–2 semanas | ALTA |
| CP-03 | Script de instalación automatizado | Onboarding en nueva red real | 1 semana | ALTA |
| CP-04 | Nuevos escenarios B7–B10 | Validación extendida | 1 semana | ALTA |
| CP-05 | Aprendizaje incremental (River) | Adaptación continua | 2 semanas | MEDIA |
| CP-06 | API REST de gestión (FastAPI) | Gestión sin SSH | 1 semana | MEDIA |
| CP-07 | Tests automáticos pytest | Prevenir regresiones | 1 semana | MEDIA |
| CP-08 | Publicación preprint (Zenodo/arXiv) | Visibilidad académica | 2 semanas | BAJA |
| CP-09 | Piloto en laboratorio UPeU (red real) | Validación Fase 1 | 4–6 semanas | ALTA |
| CP-10 | Enriquecer alertas Telegram con GeoIP | Contexto al operador | 3 días | BAJA |

### Hitos de Corto Plazo

```
Mes 1: CP-01 (modo MONITOR) + CP-07 (tests) + CP-02 (Grafana inicio)
Mes 2: CP-02 (Grafana completo) + CP-03 (instalador) + CP-04 (nuevos escenarios)
Mes 3: CP-05 (River incremental) + CP-06 (API REST) + inicio CP-09 (piloto UPeU)
Mes 4–6: CP-09 (30 días MONITOR en red real) + evaluación datos reales
         → Si 30 días exitosos: activar LIMIT en Fase 1
```

## 7.2 Mediano Plazo (6 – 12 meses)

### Objetivo general
Evolución del sistema hacia producción parcial y madurez operacional. Integración con el ecosistema de seguridad universitario.

| Tarea | Descripción | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|---|
| MP-01 | Integración Wazuh HIDS | Correlación red+host | 3 semanas | ALTA |
| MP-02 | Integración Elasticsearch/ELK | Búsqueda y auditoría | 4 semanas | ALTA |
| MP-03 | Reentrenamiento automático mensual | Modelo siempre actualizado | 1 semana | ALTA |
| MP-04 | HA (High Availability) sensor | Eliminar SPOF | 2 semanas | ALTA |
| MP-05 | Análisis tráfico cifrado (TLS metadata) | Cobertura HTTPS | 3 semanas | MEDIA |
| MP-06 | Ensemble IF + Autoencoder | Detección APT evasivo | 4 semanas | MEDIA |
| MP-07 | Nuevos datasets (CIC-IDS 2023) | Comparación con benchmark | 2 semanas | MEDIA |
| MP-08 | Integración threat intel (OTX, MISP) | Contexto IOC | 2 semanas | MEDIA |
| MP-09 | Scoring por reputación IP | Capa adicional de contexto | 1 semana | BAJA |
| MP-10 | Publicación en congreso (LACNIC/CNIC) | Difusión académica | 4 semanas | ALTA |

### Nuevos Datasets para Mediano Plazo

| Dataset | Descripción | Utilidad |
|---|---|---|
| CIC-IDS 2023 (UNB) | Tráfico moderno con IoT y cloud | Comparar AUC en benchmark público |
| UNSW-NB15 | 9 tipos de ataque, 49 features | Validar generalización del IF |
| CAIDA DDOS 2007 | Tráfico de DDoS real a gran escala | Validar escalabilidad del sistema |
| UPeU Network Logs | Tráfico real universitario (capturar en CP-09) | Dataset propio de producción |

## 7.3 Largo Plazo (1 – 3 años)

### Objetivo general
Sistema maduro en producción universitaria, con investigación continua y potencial publicación como contribución al estado del arte regional.

| Tarea | Descripción | Horizonte | Prerrequisito |
|---|---|---|---|
| LP-01 | Producción completa en red UPeU | 12–18 meses | MP-04 (HA) + MP-01 (Wazuh) |
| LP-02 | Multi-sensor (campus distribuido) | 18–24 meses | LP-01 + Kafka implementado |
| LP-03 | Federated Learning inter-institucional | 24–36 meses | LP-02 + acuerdos institucionales |
| LP-04 | UEBA (User and Entity Behavior Analytics) | 18–30 meses | ELK + Wazuh integrados |
| LP-05 | Respuesta automática adaptativa (τ dinámico) | 24–36 meses | MLOps maduro + supervisión SOC |
| LP-06 | Certificación ISO 27001 del proceso | 30–36 meses | 18 meses operación estable |
| LP-07 | Paper en revista indexada (Scopus/SCI) | 18–24 meses | Dataset + resultados producción |
| LP-08 | Tesis doctoral (extensión del PPI) | 36+ meses | Paper publicado + LP-01 |

### Nuevos Modelos para Largo Plazo

| Modelo | Ventaja sobre IF actual | Prerequisito | AUC estimado |
|---|---|---|---|
| Isolation Forest + Autoencoder (Ensemble) | Detecta APT evasivo | GPU en sensor | +0.02–0.04 AUC |
| Graph Neural Network (GNN) | Detecta ataques basados en relaciones entre IPs | Dataset etiquetado + GPU | +0.03–0.05 AUC |
| LSTM Autoencoder | Captura secuencias temporales de ataques graduales | GPU obligatoria, etiquetas | +0.04–0.06 AUC |
| Federated IF | Combina modelos de múltiples instituciones sin compartir datos | Acuerdo multi-institución | +0.01–0.03 AUC |
| One-Class SVM con kernel RBF | Alternativa a IF para baseline pequeño | Sin GPU, pero O(n²) | ~0.91 AUC estimado |

### Visión de Producción Real (3 años)

```
ARQUITECTURA OBJETIVO — 3 AÑOS

Internet
    │
[Firewall Perimetral] ← certificado ISO 27001
    │
[TAP Óptico / SPAN Port Troncal]
    │
[Sensor Primario] ←── [Sensor Backup] (HA activo-pasivo)
    │                          │
    └──────────────────────────┘
                │
         [Motor IF v3.x]
         (Ensemble IF+AE+LSTM)
         (River incremental)
         (Kafka multi-sensor)
                │
    ┌───────────┴────────────┐
    ▼                         ▼
[Elasticsearch]         [InfluxDB]
    │                         │
[Kibana SIEM]            [Grafana]
    │                         │
[Wazuh Integration]    [Alertas PagerDuty]
    │
[SOC Dashboard]
    │
[Informe Ejecutivo CISO]

Métricas objetivo a 3 años:
  Recall:    > 99.5%
  Precision: > 99.9%
  AUC:       > 0.96
  Latencia P95: < 50ms
  Uptime:    99.9% (HA)
  ITL:       0%
```

## 7.4 Roadmap de Publicaciones Académicas

| # | Tipo | Título tentativo | Venue | Horizonte |
|---|---|---|---|---|
| P1 | Preprint | "Anomaly Detection in University Networks Using Isolation Forest and Suricata Inline Control" | Zenodo / arXiv cs.CR | Mes 3 |
| P2 | Conferencia | "Real-time Network Anomaly Detection: MVP Implementation and Validation" | LACNIC Security Track | 12 meses |
| P3 | Artículo | "Adaptive Isolation Forest for Zero-Day Attack Detection in Resource-Constrained Environments" | Computers & Security (Elsevier) | 24 meses |
| P4 | Tesis doctoral | Extensión completa del sistema con Federated Learning | UPeU / Universidad asociada | 36+ meses |

---

## Resumen de Impacto Esperado

| Horizonte | Hito clave | Impacto |
|---|---|---|
| 6 meses | Piloto en red UPeU con modo MONITOR | Validación en tráfico real |
| 12 meses | Producción parcial (1 VLAN) con LIMIT activo + Wazuh | Sistema operacional real |
| 18 meses | Producción completa + ELK + HA | SOC operativo |
| 24 meses | Multi-sensor campus + paper publicado | Contribución al estado del arte |
| 36 meses | Federated Learning + ISO 27001 | Sistema de clase empresarial |

---

*Documento generado: 2026-06-14*  
*Basado en arquitectura validada: 40 corridas F6 | AUC=0.9440 | Recall=99.3% | ITL=0%*
