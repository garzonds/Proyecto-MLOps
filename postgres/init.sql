-- ============================================================
-- Inicialización de la base de datos de datos del proyecto
-- Tres etapas: raw, processed, ready
-- ============================================================

-- Datos crudos tal como vienen de la API
CREATE TABLE IF NOT EXISTS forest_raw (
    id                              SERIAL PRIMARY KEY,
    batch_id                        INTEGER,
    elevation                       FLOAT,
    aspect                          FLOAT,
    slope                           FLOAT,
    horizontal_distance_to_hydrology FLOAT,
    vertical_distance_to_hydrology  FLOAT,
    horizontal_distance_to_roadways FLOAT,
    hillshade_9am                   FLOAT,
    hillshade_noon                  FLOAT,
    hillshade_3pm                   FLOAT,
    horizontal_distance_to_fire_points FLOAT,
    wilderness_area                 VARCHAR(50),
    soil_type                       VARCHAR(50),
    cover_type                      INTEGER,
    ingested_at                     TIMESTAMP DEFAULT NOW()
);

-- Datos procesados (encoding, limpieza)
CREATE TABLE IF NOT EXISTS forest_processed (
    id                              SERIAL PRIMARY KEY,
    elevation                       FLOAT,
    aspect                          FLOAT,
    slope                           FLOAT,
    horizontal_distance_to_hydrology FLOAT,
    vertical_distance_to_hydrology  FLOAT,
    horizontal_distance_to_roadways FLOAT,
    hillshade_9am                   FLOAT,
    hillshade_noon                  FLOAT,
    hillshade_3pm                   FLOAT,
    horizontal_distance_to_fire_points FLOAT,
    wilderness_area_rawah           INTEGER,
    wilderness_area_neota           INTEGER,
    wilderness_area_comanche        INTEGER,
    wilderness_area_cache           INTEGER,
    soil_type_encoded               INTEGER,
    cover_type                      INTEGER,
    processed_at                    TIMESTAMP DEFAULT NOW()
);

-- Datos listos para entrenamiento (escalados y balanceados)
CREATE TABLE IF NOT EXISTS forest_ready (
    id                              SERIAL PRIMARY KEY,
    features                        JSONB,
    label                           INTEGER,
    created_at                      TIMESTAMP DEFAULT NOW()
);
