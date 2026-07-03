-- Initialisation PostgreSQL + TimescaleDB pour UrbanHub
-- Exécuté automatiquement au premier démarrage du container

-- Extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Tables de référence
-- ============================================================

-- Capteurs (référentiel métier)
CREATE TABLE IF NOT EXISTS sensors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_id       VARCHAR(64) UNIQUE NOT NULL,
    name            VARCHAR(128) NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude       DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    point_reference VARCHAR(256) NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sensors_sensor_id ON sensors(sensor_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors(latitude, longitude) WHERE deleted_at IS NULL;

-- Utilisateurs (RBAC)
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(256) UNIQUE NOT NULL,
    name            VARCHAR(128) NOT NULL,
    role            VARCHAR(32) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMP
);

-- ============================================================
-- Série temporelle : measurements (HYPERTABLE)
-- ============================================================

CREATE TABLE IF NOT EXISTS measurements (
    id                      BIGSERIAL,
    sensor_uuid             UUID NOT NULL REFERENCES sensors(id) ON DELETE RESTRICT,
    timestamp               TIMESTAMP NOT NULL,
    ph                      DOUBLE PRECISION NOT NULL CHECK (ph BETWEEN 0 AND 14),
    turbidity_ntu           DOUBLE PRECISION NOT NULL CHECK (turbidity_ntu >= 0),
    temperature_c           DOUBLE PRECISION NOT NULL,
    level_m                 DOUBLE PRECISION NOT NULL CHECK (level_m >= 0),
    flow_m3s                DOUBLE PRECISION NOT NULL CHECK (flow_m3s >= 0),
    dissolved_oxygen_mgl    DOUBLE PRECISION NOT NULL CHECK (dissolved_oxygen_mgl >= 0),
    signal_quality          VARCHAR(16) NOT NULL DEFAULT 'GOOD'
        CHECK (signal_quality IN ('GOOD', 'DEGRADED', 'LOST')),
    firmware_version        VARCHAR(32),
    trace_id                UUID NOT NULL,
    event_id                UUID NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, id)
);

-- Convert to hypertable BEFORE creating unique index on event_id
SELECT create_hypertable('measurements', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Idempotence: unique on event_id (must include timestamp for TimescaleDB)
CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_event_id
    ON measurements (timestamp, event_id);

CREATE INDEX IF NOT EXISTS idx_measurements_sensor_time
    ON measurements (sensor_uuid, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_trace
    ON measurements (trace_id);

-- Politique de rétention : 90 jours pour les données brutes
SELECT add_retention_policy('measurements', INTERVAL '90 days', if_not_exists => TRUE);

-- ============================================================
-- Continuous aggregates (downsample)
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_hourly
WITH (timescaledb.continuous) AS
SELECT
    sensor_uuid,
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(ph) AS ph_avg,
    MIN(ph) AS ph_min,
    MAX(ph) AS ph_max,
    AVG(turbidity_ntu) AS turbidity_avg,
    MIN(turbidity_ntu) AS turbidity_min,
    MAX(turbidity_ntu) AS turbidity_max,
    AVG(temperature_c) AS temp_avg,
    AVG(dissolved_oxygen_mgl) AS oxygen_avg,
    COUNT(*) AS sample_count
FROM measurements
GROUP BY sensor_uuid, bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('measurements_hourly',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_daily
WITH (timescaledb.continuous) AS
SELECT
    sensor_uuid,
    time_bucket('1 day', timestamp) AS bucket,
    AVG(ph) AS ph_avg,
    MIN(ph) AS ph_min,
    MAX(ph) AS ph_max,
    AVG(turbidity_ntu) AS turbidity_avg,
    MIN(turbidity_ntu) AS turbidity_min,
    MAX(turbidity_ntu) AS turbidity_max,
    COUNT(*) AS sample_count,
    COUNT(*) FILTER (WHERE ph < 6.5 OR ph > 8.5) AS ph_anomaly_count,
    COUNT(*) FILTER (WHERE turbidity_ntu > 10) AS turbidity_anomaly_count
FROM measurements
GROUP BY sensor_uuid, bucket
WITH NO DATA;

SELECT add_continuous_aggregate_policy('measurements_daily',
    start_offset => INTERVAL '30 days',
    end_offset   => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- ============================================================
-- Transitions d'état (machine à états)
-- ============================================================

CREATE TABLE IF NOT EXISTS state_transitions (
    id                          BIGSERIAL PRIMARY KEY,
    sensor_uuid                 UUID NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    timestamp                   TIMESTAMP NOT NULL DEFAULT NOW(),
    previous_state              VARCHAR(16) NOT NULL CHECK (previous_state IN ('NORMAL', 'WARNING', 'CRITICAL')),
    new_state                   VARCHAR(16) NOT NULL CHECK (new_state IN ('NORMAL', 'WARNING', 'CRITICAL')),
    anomaly_count_at_transition INTEGER NOT NULL CHECK (anomaly_count_at_transition >= 0),
    anomaly_type                VARCHAR(32),
    trace_id                    UUID NOT NULL,
    created_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_state_transitions_sensor_time
    ON state_transitions (sensor_uuid, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_state_transitions_new_state
    ON state_transitions (new_state, timestamp DESC);

-- ============================================================
-- Alertes
-- ============================================================

CREATE TABLE IF NOT EXISTS alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_uuid         UUID NOT NULL REFERENCES sensors(id) ON DELETE RESTRICT,
    severity            VARCHAR(16) NOT NULL CHECK (severity IN ('WARNING', 'CRITICAL')),
    alert_type          VARCHAR(64) NOT NULL DEFAULT 'state_transition',
    message             TEXT NOT NULL,
    trace_id            UUID NOT NULL,
    status              VARCHAR(16) NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'ACK', 'RESOLVED', 'CLOSED')),
    opened_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at     TIMESTAMP,
    resolved_at         TIMESTAMP,
    acknowledged_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    resolution_comment  TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_sensor_opened
    ON alerts (sensor_uuid, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity
    ON alerts (status, severity, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_trace
    ON alerts (trace_id);

-- ============================================================
-- Audit log
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(64) NOT NULL,
    resource_type   VARCHAR(64) NOT NULL,
    resource_id     UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user_time
    ON audit_log (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource
    ON audit_log (resource_type, resource_id, created_at DESC);

-- ============================================================
-- Vues utiles
-- ============================================================

CREATE OR REPLACE VIEW current_sensor_state AS
SELECT
    s.id AS sensor_uuid,
    s.sensor_id,
    s.name,
    s.latitude,
    s.longitude,
    s.point_reference,
    -- Statut calculé depuis la dernière transition
    COALESCE(
        (SELECT new_state FROM state_transitions st
         WHERE st.sensor_uuid = s.id
         ORDER BY timestamp DESC LIMIT 1),
        'NORMAL'
    ) AS state,
    COALESCE(
        (SELECT anomaly_count_at_transition FROM state_transitions st
         WHERE st.sensor_uuid = s.id
         ORDER BY timestamp DESC LIMIT 1),
        0
    ) AS anomaly_count,
    (SELECT MAX(timestamp) FROM state_transitions st WHERE st.sensor_uuid = s.id) AS last_transition_at
FROM sensors s
WHERE s.deleted_at IS NULL;

-- ============================================================
-- Seed : 12 capteurs de la Seine
-- ============================================================

INSERT INTO sensors (sensor_id, name, latitude, longitude, point_reference, metadata) VALUES
    ('SEINE-VITRY-001',       'Vitry-sur-Seine',         48.7876, 2.3926, 'Station amont Paris',     '{"description": "Amont de Paris - zone industrielle", "pollution_probability": 0.02}'),
    ('SEINE-CHARENTON-002',    'Charenton-le-Pont',       48.8207, 2.4151, 'Confluence Marne/Seine',  '{"description": "Confluence Marne/Seine", "pollution_probability": 0.03}'),
    ('SEINE-BERCY-003',        'Bercy',                   48.8359, 2.3823, 'Quai de Bercy',           '{"description": "Quai de Bercy - trafic fluvial", "pollution_probability": 0.04}'),
    ('SEINE-AUSTERLITZ-004',   'Pont d''Austerlitz',      48.8447, 2.3655, 'Pont d''Austerlitz',      '{"description": "Zone urbaine dense", "pollution_probability": 0.05, "pollution_type": "turbidity"}'),
    ('SEINE-ILES-LOUVRE-005',  'Île de la Cité',          48.8530, 2.3470, 'Île de la Cité',          '{"description": "Cœur de Paris - bateaux-mouches", "pollution_probability": 0.06}'),
    ('SEINE-CONCORDE-006',     'Pont de la Concorde',     48.8637, 2.3017, 'Pont de la Concorde',     '{"description": "Haut lieu touristique", "pollution_probability": 0.07}'),
    ('SEINE-ALMA-007',         'Pont de l''Alma',         48.8637, 2.3017, 'Pont de l''Alma',         '{"description": "Zouave et crue de la Seine", "pollution_probability": 0.08}'),
    ('SEINE-TOUR-EIFFEL-008',  'Tour Eiffel',             48.8584, 2.2945, 'Tour Eiffel',             '{"description": "Zone touristique majeure", "pollution_probability": 0.10, "pollution_type": "turbidity"}'),
    ('SEINE-IENA-009',         'Pont d''Iéna',            48.8597, 2.2923, 'Pont d''Iéna',            '{"description": "Aval immédiat Tour Eiffel", "pollution_probability": 0.12}'),
    ('SEINE-BILLANCOURT-010',  'Boulogne-Billancourt',    48.8412, 2.2528, 'Boulogne-Billancourt',    '{"description": "Aval - rejets industriels", "pollution_probability": 0.15}'),
    ('SEINE-SURESNES-011',     'Suresnes',                48.8714, 2.2286, 'Suresnes',                '{"description": "Boucle de Gennevilliers", "pollution_probability": 0.18}'),
    ('SEINE-COLOMBES-012',     'Colombes',                48.9135, 2.2546, 'Colombes',                '{"description": "Rejets STEP + industries", "pollution_probability": 0.20}')
ON CONFLICT (sensor_id) DO NOTHING;

-- Utilisateur admin par défaut
INSERT INTO users (email, name, role)
VALUES ('admin@urbanhub.local', 'Admin UrbanHub', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Confirmation
DO $$
BEGIN
    RAISE NOTICE '✅ UrbanHub DB initialized: % sensors, % users',
        (SELECT COUNT(*) FROM sensors),
        (SELECT COUNT(*) FROM users);
END $$;