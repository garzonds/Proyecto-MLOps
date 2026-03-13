from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

from model_loader import load_model

app = FastAPI(title="Forest Cover Prediction API")

model = load_model()


class PredictRequest(BaseModel):
    features: list[float]


@app.get("/health")
def health():
    return {"status": "API running"}


@app.post("/predict")
def predict(data: PredictRequest):

    X = np.array(data.features).reshape(1, -1)

    prediction = model.predict(X)

    return {"prediction": int(prediction[0])}