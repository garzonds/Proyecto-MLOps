FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pandas \
    scikit-learn \
    psycopg2-binary \
    sqlalchemy \
    minio

COPY . .

CMD ["python", "train_model.py"]