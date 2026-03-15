import os
import joblib
from minio import Minio


def get_minio_client():
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
    joblib.dump(model, model_path)
    return model_path


def upload_model_to_minio(model_path, bucket_name="models", object_name="forest_model.joblib"):
    client = get_minio_client()

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    client.fput_object(bucket_name, object_name, model_path)

    return {
        "bucket": bucket_name,
        "object_name": object_name,
        "model_path": model_path,
    }
