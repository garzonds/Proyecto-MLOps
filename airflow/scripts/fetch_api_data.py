"""
fetch_api_data.py
Consulta la API del profesor (o simulada) y guarda los datos crudos
en la tabla forest_raw de PostgreSQL.

La API retorna:
{
  "group_number": 10,
  "batch_number": 3,
  "data": [["2596","51","3",...], ["2763","56","2",...]]
}

Columnas en orden:
Elevation, Aspect, Slope, Horizontal_Distance_To_Hydrology,
Vertical_Distance_To_Hydrology, Horizontal_Distance_To_Roadways,
Hillshade_9am, Hillshade_Noon, Hillshade_3pm,
Horizontal_Distance_To_Fire_Points, Wilderness_Area, Soil_Type, Cover_Type
"""
import os
import logging
import requests
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_API_URL  = os.environ.get("DATA_API_URL",       "http://data_api:8080")
GROUP_ID      = os.environ.get("GROUP_ID",           "10")
POSTGRES_CONN = os.environ.get(
    "POSTGRES_DATA_CONN",
    "postgresql+psycopg2://mlops:mlops@postgres_data:5432/mlops_db"
)

# Orden exacto de columnas que retorna la API
COLUMNS = [
    "elevation",
    "aspect",
    "slope",
    "horizontal_distance_to_hydrology",
    "vertical_distance_to_hydrology",
    "horizontal_distance_to_roadways",
    "hillshade_9am",
    "hillshade_noon",
    "hillshade_3pm",
    "horizontal_distance_to_fire_points",
    "wilderness_area",
    "soil_type",
    "cover_type",
]


def fetch_and_store():
    """
    1. Llama a la API con group_number del equipo (UNA sola petición).
    2. Parsea la respuesta (lista de listas de strings).
    3. Guarda cada fila en forest_raw sin ningún preprocesamiento.
    """

    # ── 1. Llamar a la API ────────────────────────────────────────────────────
    url = f"{DATA_API_URL}/data"
    params = {"group_number": GROUP_ID}

    logger.info(f"Consultando API: {url} con group_number={GROUP_ID}")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    payload     = response.json()
    batch_id    = payload.get("batch_number")
    rows        = payload.get("data", [])

    logger.info(f"Batch {batch_id} recibido — {len(rows)} registros")

    if not rows:
        logger.warning("La API no retornó registros. Abortando.")
        return

    # ── 2. Parsear lista de listas → lista de dicts ───────────────────────────
    records = []
    for row in rows:
        if len(row) != len(COLUMNS):
            logger.warning(f"Fila con columnas inesperadas ({len(row)}), se omite.")
            continue
        record = dict(zip(COLUMNS, row))
        record["batch_id"] = batch_id
        records.append(record)

    # ── 3. Guardar en PostgreSQL ──────────────────────────────────────────────
    engine = create_engine(POSTGRES_CONN)

    insert_sql = text("""
        INSERT INTO forest_raw (
            batch_id,
            elevation,
            aspect,
            slope,
            horizontal_distance_to_hydrology,
            vertical_distance_to_hydrology,
            horizontal_distance_to_roadways,
            hillshade_9am,
            hillshade_noon,
            hillshade_3pm,
            horizontal_distance_to_fire_points,
            wilderness_area,
            soil_type,
            cover_type
        ) VALUES (
            :batch_id,
            :elevation,
            :aspect,
            :slope,
            :horizontal_distance_to_hydrology,
            :vertical_distance_to_hydrology,
            :horizontal_distance_to_roadways,
            :hillshade_9am,
            :hillshade_noon,
            :hillshade_3pm,
            :horizontal_distance_to_fire_points,
            :wilderness_area,
            :soil_type,
            :cover_type
        )
    """)

    with engine.begin() as conn:
        for record in records:
            conn.execute(insert_sql, record)

    logger.info(f"{len(records)} registros guardados en forest_raw (batch {batch_id}).")


if __name__ == "__main__":
    fetch_and_store()