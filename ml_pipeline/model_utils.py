import os
import joblib
from minio import Minio
from minio.error import S3Error


def get_minio_client():
    """
    Crea el cliente de conexión a MinIO usando variables de entorno
    compatibles con Docker Compose.
    """

    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

    client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )

    return client


def save_model_local(model, model_path="model.joblib"):
    """
    Guarda el modelo entrenado localmente dentro del contenedor.
    """
    joblib.dump(model, model_path)
    print(f"Modelo guardado localmente en: {model_path}")
    return model_path


def upload_model_to_minio(model_path, bucket_name="models", object_name="forest_model.joblib"):
    """
    Sube el modelo entrenado a MinIO.
    Si el bucket no existe, lo crea automáticamente.
    """

    client = get_minio_client()

    try:
        # verificar si el bucket existe
        if not client.bucket_exists(bucket_name):
            print(f"Bucket '{bucket_name}' no existe. Creándolo...")
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' creado correctamente.")
        else:
            print(f"Bucket '{bucket_name}' ya existe.")

        # subir el modelo
        print(f"Subiendo modelo a MinIO: {object_name}")
        client.fput_object(
            bucket_name,
            object_name,
            model_path
        )

        print("Modelo subido correctamente a MinIO.")

        return {
            "bucket": bucket_name,
            "object_name": object_name,
            "model_path": model_path,
        }

    except S3Error as e:
        print("Error al subir el modelo a MinIO:")
        print(e)
        raise