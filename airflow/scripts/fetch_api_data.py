"""
fetch_api_data.py
Consulta la API externa (o simulada) y guarda los datos crudos
en la tabla forest_raw de PostgreSQL.
"""
import os
import logging
import requests
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_API_URL = os.environ.get("DATA_API_URL", "http://data_api:8080")
GROUP_ID     = os.environ.get("GROUP_ID", "10")
POSTGRES_CONN = os.environ.get(
    "POSTGRES_DATA_CONN",
    "postgresql+psycopg2://mlops:mlops@postgres_data:5432/mlops_db"
)


def fetch_and_store():
    """
    1. Llama a la API con el group_id del equipo.
    2. Guarda cada registro en forest_raw tal como viene (sin preprocesamiento).
    """

    # ── 1. Llamar a la API ────────────────────────────────────────────────────
    url = f"{DATA_API_URL}/data"
    params = {"group_id": GROUP_ID}

    logger.info(f"Consultando API: {url} con group_id={GROUP_ID}")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    batch_id = payload.get("batch_id")
    records  = payload.get("data", [])

    logger.info(f"Batch {batch_id} recibido — {len(records)} registros")

    if not records:
        logger.warning("La API no retornó registros. Abortando.")
        return

    # ── 2. Guardar en PostgreSQL ──────────────────────────────────────────────
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
            conn.execute(insert_sql, {
                "batch_id":                              batch_id,
                "elevation":                             record.get("Elevation"),
                "aspect":                                record.get("Aspect"),
                "slope":                                 record.get("Slope"),
                "horizontal_distance_to_hydrology":      record.get("Horizontal_Distance_To_Hydrology"),
                "vertical_distance_to_hydrology":        record.get("Vertical_Distance_To_Hydrology"),
                "horizontal_distance_to_roadways":       record.get("Horizontal_Distance_To_Roadways"),
                "hillshade_9am":                         record.get("Hillshade_9am"),
                "hillshade_noon":                        record.get("Hillshade_Noon"),
                "hillshade_3pm":                         record.get("Hillshade_3pm"),
                "horizontal_distance_to_fire_points":    record.get("Horizontal_Distance_To_Fire_Points"),
                "wilderness_area":                       record.get("Wilderness_Area"),
                "soil_type":                             record.get("Soil_Type"),
                "cover_type":                            record.get("Cover_Type"),
            })

    logger.info(f"{len(records)} registros guardados en forest_raw.")


if __name__ == "__main__":
    fetch_and_store()
