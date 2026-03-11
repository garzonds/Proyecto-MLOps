"""
DAG: data_pipeline_dag
Orquesta la ingesta de datos desde la API externa hacia PostgreSQL.

Según el enunciado:
- Cada ejecución del DAG = UNA petición a la API + almacenamiento completo.
- No se permiten múltiples peticiones en una misma ejecución.
- Se programa cada 5 minutos para capturar todos los batches.

Flujo:
  start → check_api → fetch_and_store → verify_data → end
"""

import os
import sys
import logging
from datetime import datetime, timedelta

import requests
from sqlalchemy import create_engine, text

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
DATA_API_URL  = os.environ.get("DATA_API_URL",       "http://data_api:8080")
GROUP_ID      = os.environ.get("GROUP_ID",           "10")
POSTGRES_CONN = os.environ.get("POSTGRES_DATA_CONN", "postgresql+psycopg2://mlops:mlops@postgres_data:5432/mlops_db")


# =============================================================================
# TASK 1 — Verificar que la API esté disponible
# =============================================================================
def check_api(**context):
    """Verifica que la API externa esté respondiendo antes de continuar."""
    url = f"{DATA_API_URL}/status"
    logger.info(f"Verificando API en: {url}")

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    status = response.json()
    logger.info(f"API disponible. Batch actual: {status.get('current_batch')} "
                f"| Próximo batch en: {status.get('seconds_until_next_batch')}s")

    # Pasar info al siguiente task via XCom
    context["ti"].xcom_push(key="batch_id",            value=status.get("current_batch"))
    context["ti"].xcom_push(key="seconds_until_next",  value=status.get("seconds_until_next_batch"))


# =============================================================================
# TASK 2 — Fetch y almacenamiento (UNA sola petición por ejecución)
# =============================================================================
def fetch_and_store(**context):
    """
    Realiza UNA petición a la API y guarda todos los registros en forest_raw.
    Una ejecución del DAG = una petición = un batch completo almacenado.
    """
    # Importar el script de ingesta
    sys.path.insert(0, "/opt/airflow/scripts")
    from fetch_api_data import fetch_and_store as _fetch

    _fetch()


# =============================================================================
# TASK 3 — Verificar que los datos se guardaron correctamente
# =============================================================================
def verify_data(**context):
    """Cuenta los registros en forest_raw y loggea el total acumulado."""
    engine = create_engine(POSTGRES_CONN)

    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM forest_raw")
        ).scalar()

        batch_id = context["ti"].xcom_pull(key="batch_id", task_ids="check_api")

        if batch_id:
            batch_count = conn.execute(
                text("SELECT COUNT(*) FROM forest_raw WHERE batch_id = :bid"),
                {"bid": batch_id}
            ).scalar()
            logger.info(f"Registros del batch {batch_id}: {batch_count}")

    logger.info(f"Total acumulado en forest_raw: {total}")

    if total == 0:
        raise ValueError("No hay datos en forest_raw. Algo salió mal.")

    logger.info("Verificación exitosa.")


# =============================================================================
# DEFINICIÓN DEL DAG
# =============================================================================
default_args = {
    "owner":            "integrante-1",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=1),
}

with DAG(
    dag_id="data_pipeline_dag",
    description="Ingesta de datos desde API externa hacia PostgreSQL - Grupo 10",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/5 * * * *",  # Cada 5 minutos — sincronizado con rotación de batches
    catchup=False,
    tags=["mlops", "ingesta", "grupo10"],
) as dag:

    start = EmptyOperator(task_id="start")

    t_check = PythonOperator(
        task_id="check_api",
        python_callable=check_api,
    )

    t_fetch = PythonOperator(
        task_id="fetch_and_store",
        python_callable=fetch_and_store,
    )

    t_verify = PythonOperator(
        task_id="verify_data",
        python_callable=verify_data,
    )

    end = EmptyOperator(task_id="end")

    start >> t_check >> t_fetch >> t_verify >> end
