from minio import Minio
import os
import io
import joblib
import time


def load_model():

    print("Inicializando cliente MinIO...")

    client = Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=False
    )

    bucket = os.getenv("MINIO_BUCKET", "models")

    # Nombre del modelo generado por ml_pipeline
    model_name = "forest_model.joblib"

    print(f"Intentando cargar modelo '{model_name}' desde bucket '{bucket}'")

    # Esperar hasta que el modelo exista
    while True:
        try:
            response = client.get_object(bucket, model_name)
            print("Modelo encontrado en MinIO")
            break
        except Exception as e:
            print("Modelo aún no disponible. Esperando 5 segundos...")
            time.sleep(5)

    try:
        model_bytes = io.BytesIO(response.read())
        model = joblib.load(model_bytes)
        print("Modelo cargado correctamente")
    finally:
        response.close()
        response.release_conn()

    return model