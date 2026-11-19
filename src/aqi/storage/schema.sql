
CREATE TABLE IF NOT EXISTS air_quality_observations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source TEXT NOT NULL DEFAULT 'openaq',

    source_location_id BIGINT NOT NULL,
    sensor_id BIGINT NOT NULL,

    parameter TEXT NOT NULL
        CHECK (parameter = 'pm25'),

    value DOUBLE PRECISION NOT NULL
        CHECK (value >= 0),

    unit TEXT NOT NULL,

    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    flags JSONB NOT NULL DEFAULT '[]'::jsonb,

    raw_file TEXT,
    ingestion_run_id TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_observation_period
        CHECK (period_end > period_start),

    CONSTRAINT valid_latitude
        CHECK (
            latitude IS NULL
            OR latitude BETWEEN -90 AND 90
        ),

    CONSTRAINT valid_longitude
        CHECK (
            longitude IS NULL
            OR longitude BETWEEN -180 AND 180
        ),

    CONSTRAINT unique_sensor_observation
        UNIQUE (source, sensor_id, period_end)
);


CREATE INDEX IF NOT EXISTS idx_observations_period_end
    ON air_quality_observations (period_end);


CREATE INDEX IF NOT EXISTS idx_observations_location
    ON air_quality_observations (source_location_id);
