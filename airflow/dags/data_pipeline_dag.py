"""
DAG: data_pipeline_dag
Pipeline MLOps del proyecto:
start -> fetch_and_store -> verify_data -> train_model -> end

Reglas del enunciado:
- Cada ejecución del DAG = UNA petición a la API + almacenamiento completo.
- No se permiten múltiples peticiones en una misma ejecución.
- Se programa cada 5 minutos para capturar batches.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
DATA_API_URL = os.environ.get("DATA_API_URL", "http://data_api:8080")
GROUP_ID = os.environ.get("GROUP_ID", "10")
POSTGRES_CONN = os.environ.get(
    "POSTGRES_DATA_CONN",
    "postgresql+psycopg2://mlops:mlops@postgres_data:5432/mlops_db"
)

# Carpeta reutilizable con train_model.py, preprocess.py, model_utils.py
ML_PIPELINE_PATH = "/opt/airflow/ml_pipeline"

# Carpeta donde está fetch_api_data.py
SCRIPTS_PATH = "/opt/airflow/scripts"


# =============================================================================
# TASK 1 — Fetch y almacenamiento (UNA sola petición por ejecución)
# =============================================================================
def fetch_and_store(**context):
    """
    Realiza UNA petición a la API y guarda registros en forest_raw.
    Si no se obtiene batch_id, falla explícitamente.
    """
    if SCRIPTS_PATH not in sys.path:
        sys.path.insert(0, SCRIPTS_PATH)

    from fetch_api_data import fetch_and_store as _fetch

    logger.info(
        f"Iniciando fetch_and_store con DATA_API_URL={DATA_API_URL} y GROUP_ID={GROUP_ID}"
    )

    batch_id = _fetch()

    if batch_id is None:
        raise ValueError(
            "No se obtuvo batch_id desde la API. "
            "No se insertaron datos en forest_raw."
        )

    context["ti"].xcom_push(key="batch_id", value=batch_id)
    logger.info(f"Batch almacenado correctamente: {batch_id}")


# =============================================================================
# TASK 2 — Verificar que los datos se guardaron correctamente
# =============================================================================
def verify_data(**context):
    """
    Verifica que forest_raw tenga datos y, si existe batch_id,
    cuenta cuántos registros quedaron asociados a ese batch.
    """
    engine = create_engine(POSTGRES_CONN)

    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM forest_raw")
        ).scalar()

        batch_id = context["ti"].xcom_pull(
            key="batch_id",
            task_ids="fetch_and_store"
        )

        logger.info(f"Total acumulado en forest_raw: {total}")

        if total == 0:
            raise ValueError("No hay datos en forest_raw. Algo salió mal.")

        # Validación específica por batch_id, si existe la columna y hubo batch
        if batch_id is not None:
            try:
                batch_count = conn.execute(
                    text("SELECT COUNT(*) FROM forest_raw WHERE batch_id = :bid"),
                    {"bid": batch_id}
                ).scalar()

                logger.info(f"Registros del batch {batch_id}: {batch_count}")

                if batch_count == 0:
                    raise ValueError(
                        f"El batch {batch_id} no dejó registros en forest_raw."
                    )
            except Exception as e:
                logger.warning(
                    "No se pudo validar por batch_id en forest_raw. "
                    f"Se continúa con la validación general. Detalle: {e}"
                )

    logger.info("Verificación exitosa.")


# =============================================================================
# TASK 3 — Entrenamiento y almacenamiento del modelo en MinIO
# =============================================================================
def train_model_task(**context):
    """
    Reutiliza train_model.py desde /opt/airflow/ml_pipeline.
    Ese script debe encargarse de:
    - leer desde PostgreSQL
    - preprocesar
    - entrenar modelo
    - subir modelo a MinIO
    """
    if ML_PIPELINE_PATH not in sys.path:
        sys.path.insert(0, ML_PIPELINE_PATH)

    from train_model import train

    logger.info("Iniciando entrenamiento del modelo usando ml_pipeline/train_model.py ...")
    train()
    logger.info("Entrenamiento finalizado y modelo enviado a MinIO.")


# =============================================================================
# DEFINICIÓN DEL DAG
# =============================================================================
default_args = {
    "owner": "integrante-1",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="data_pipeline_dag",
    description="Pipeline MLOps - ingesta, verificación y entrenamiento - Grupo 10",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/5 * * * *",
    catchup=False,
    tags=["mlops", "ingesta", "grupo10", "training"],
) as dag:

    start = EmptyOperator(task_id="start")

    t_fetch = PythonOperator(
        task_id="fetch_and_store",
        python_callable=fetch_and_store,
    )

    t_verify = PythonOperator(
        task_id="verify_data",
        python_callable=verify_data,
    )

    t_train = PythonOperator(
        task_id="train_model",
        python_callable=train_model_task,
    )

    end = EmptyOperator(task_id="end")

    start >> t_fetch >> t_verify >> t_train >> end