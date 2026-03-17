"""
fetch_api_data.py
Consulta la API del profesor (o simulada) y guarda los datos crudos
en la tabla forest_raw de PostgreSQL.

La API retorna todos los valores como strings:
{
  "group_number": 10,
  "batch_number": 3,
  "data": [["2596","51","3",...,"Comanche","C7722","2"], ...]
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

DATA_API_URL = os.environ.get("DATA_API_URL", "http://host.docker.internal:8081")
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
    "wilderness_area",   # VARCHAR — ej: "Comanche", "Rawah"
    "soil_type",         # VARCHAR — ej: "C7722"
    "cover_type",        # INTEGER — ej: "2"
]

# Columnas numéricas y su tipo destino
FLOAT_COLS = {
    "elevation", "aspect", "slope",
    "horizontal_distance_to_hydrology",
    "vertical_distance_to_hydrology",
    "horizontal_distance_to_roadways",
    "hillshade_9am", "hillshade_noon", "hillshade_3pm",
    "horizontal_distance_to_fire_points",
}
INT_COLS = {"cover_type"}
# wilderness_area y soil_type se dejan como VARCHAR (no se convierten)


def parse_row(raw_row: list):
    """
    Convierte una fila de strings a los tipos correctos para forest_raw.
    Retorna None si la fila tiene errores irrecuperables.
    """
    if len(raw_row) != len(COLUMNS):
        logger.warning(f"Fila con {len(raw_row)} columnas (esperadas {len(COLUMNS)}), se omite.")
        return None

    record = {}
    for col, val in zip(COLUMNS, raw_row):
        try:
            if col in FLOAT_COLS:
                record[col] = float(val)
            elif col in INT_COLS:
                record[col] = int(float(val))  # float primero por si viene "2.0"
            else:
                record[col] = str(val).strip()  # wilderness_area, soil_type
        except (ValueError, TypeError) as e:
            logger.warning(f"Error convirtiendo columna '{col}' valor '{val}': {e}. Se omite fila.")
            return None

    return record


def fetch_and_store():
    """
    1. Llama a la API con group_number del equipo (UNA sola petición).
    2. Maneja el error 400 cuando ya se recolectaron todos los batches.
    3. Verifica duplicados por batch_id antes de insertar.
    4. Convierte tipos y guarda cada fila en forest_raw.
    Retorna el batch_id insertado, o None si no se insertó nada.
    """

    # ── 1. Llamar a la API ────────────────────────────────────────────────────
    url = f"{DATA_API_URL}/data"
    params = {"group_number": GROUP_ID}

    logger.info(f"Consultando API: {url} con group_number={GROUP_ID}")
    response = requests.get(url, params=params, timeout=30)

    # ── Manejar límite de batches (400) ───────────────────────────────────────
    if response.status_code == 400:
        detail = response.json().get("detail", "")
        if "mínima necesaria" in detail or "minima necesaria" in detail:
            logger.warning("Ya se recolectaron todos los batches disponibles. "
                           "Usa /restart_data_generation para reiniciar.")
            return None
        else:
            logger.error(f"Error 400 inesperado: {detail}")
            raise ValueError(f"Error 400 de la API: {detail}")

    response.raise_for_status()

    payload  = response.json()
    batch_id = payload.get("batch_number")
    rows     = payload.get("data", [])

    logger.info(f"Batch {batch_id} recibido — {len(rows)} registros")

    if not rows:
        logger.warning("La API no retornó registros. Abortando.")
        return None

    # ── 2. Verificar duplicados ───────────────────────────────────────────────
    engine = create_engine(POSTGRES_CONN)

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT COUNT(*) FROM forest_raw WHERE batch_id = :bid"),
            {"bid": batch_id}
        ).scalar()

    if existing > 0:
        logger.warning(f"Batch {batch_id} ya existe en DB ({existing} registros). "
                       "Saltando inserción.")
        return batch_id

    # ── 3. Parsear y convertir tipos ──────────────────────────────────────────
    records = []
    skipped = 0
    for raw_row in rows:
        record = parse_row(raw_row)
        if record is None:
            skipped += 1
            continue
        record["batch_id"] = batch_id
        records.append(record)

    if skipped > 0:
        logger.warning(f"{skipped} filas omitidas por errores de tipo.")

    if not records:
        logger.error("Ningún registro válido después de parsear. Abortando.")
        return None

    # ── 4. Guardar en PostgreSQL ──────────────────────────────────────────────
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
    return batch_id


if __name__ == "__main__":
    fetch_and_store()