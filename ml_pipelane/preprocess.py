import os
import pandas as pd
from sqlalchemy import create_engine, text

TARGET_COLUMN = "Cover_Type"
CSV_PATH = "/data/covertype.csv"


def get_postgres_engine():
    db_host = os.getenv("POSTGRES_HOST", "postgres")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "mlops")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    connection_string = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    return create_engine(connection_string)


def seed_table_if_empty(table_name="forest_data"):
    engine = get_postgres_engine()

    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
        row_count = result.scalar()

    if row_count == 0:
        print(f"Tabla {table_name} vacía. Cargando datos desde {CSV_PATH} ...")
        df_csv = pd.read_csv(CSV_PATH)
        df_csv.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Se cargaron {len(df_csv)} filas en {table_name}.")
    else:
        print(f"Tabla {table_name} ya tiene {row_count} filas. No se recarga.")


def load_data(table_name="forest_data"):
    seed_table_if_empty(table_name)

    engine = get_postgres_engine()
    query = f"SELECT * FROM {table_name};"
    df = pd.read_sql(query, engine)
    return df


def preprocess_data(df: pd.DataFrame):
    df = df.copy()

    numeric_cols = [
        "Elevation",
        "Aspect",
        "Slope",
        "Horizontal_Distance_To_Hydrology",
        "Vertical_Distance_To_Hydrology",
        "Horizontal_Distance_To_Roadways",
        "Hillshade_9am",
        "Hillshade_Noon",
        "Hillshade_3pm",
        "Horizontal_Distance_To_Fire_Points",
        "Cover_Type",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    categorical_cols = ["Wilderness_Area", "Soil_Type"]

    df = df.dropna(subset=numeric_cols + categorical_cols)

    df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN].astype(int)

    return X, y, df
