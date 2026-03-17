import os
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_COLUMN = "cover_type"  # minúsculas — coincide con forest_raw


def get_postgres_engine():
    """
    Crea la conexión a PostgreSQL usando variables de entorno.
    Compatible con Docker Compose.
    """
    db_host = os.getenv("POSTGRES_HOST", "postgres_data")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "mlops_db")
    db_user = os.getenv("POSTGRES_USER", "mlops")
    db_password = os.getenv("POSTGRES_PASSWORD", "mlops")

    connection_string = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    print(f"Conectando a PostgreSQL en {db_host}:{db_port}/{db_name} con usuario {db_user}")

    engine = create_engine(connection_string)
    return engine


def load_data(table_name="forest_raw"):
    """
    Carga los datos desde la tabla forest_raw de PostgreSQL.
    Esta tabla es llenada por Airflow (Integrante 1).
    """
    engine = get_postgres_engine()

    query = f"SELECT * FROM {table_name};"
    df = pd.read_sql(query, engine)

    print(f"Datos cargados desde PostgreSQL ({table_name}): {df.shape}")
    return df


def preprocess_data(df: pd.DataFrame):
    """
    Limpieza y preparación del dataset para entrenamiento.
    Las columnas vienen en minúsculas desde forest_raw.
    """
    df = df.copy()

    # Eliminar columnas de metadatos que no son features
    cols_to_drop = ["id", "batch_id", "ingested_at"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # Columnas numéricas
    numeric_cols = [
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
        "cover_type",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Columnas categóricas
    categorical_cols = [
        "wilderness_area",
        "soil_type"
    ]

    df = df.dropna(subset=numeric_cols + categorical_cols)

    # One-hot encoding de variables categóricas
    df = pd.get_dummies(
        df,
        columns=categorical_cols,
        drop_first=False
    )

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN].astype(int)

    print(f"Dataset final:")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")

    return X, y, df
