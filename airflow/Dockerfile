FROM apache/airflow:2.6.3

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    pandas \
    scikit-learn \
    numpy \
    sqlalchemy \
    psycopg2-binary \
    minio \
    joblib