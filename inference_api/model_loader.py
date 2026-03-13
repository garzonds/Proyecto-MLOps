from minio import Minio
import pickle
import io
import os

def load_model():

    client = Minio(
        os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=False
    )

    bucket = "models"
    model_name = "model.pkl"

    response = client.get_object(bucket, model_name)

    model_bytes = io.BytesIO(response.read())

    model = pickle.load(model_bytes)

    return model