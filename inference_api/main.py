from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd

from model_loader import load_model

app = FastAPI(title="Forest Cover Prediction API")

model = load_model()


# ---- request con las variables originales ----
class PredictRequest(BaseModel):
    Elevation: float
    Aspect: float
    Slope: float
    Horizontal_Distance_To_Hydrology: float
    Vertical_Distance_To_Hydrology: float
    Horizontal_Distance_To_Roadways: float
    Hillshade_9am: float
    Hillshade_Noon: float
    Hillshade_3pm: float
    Horizontal_Distance_To_Fire_Points: float
    Wilderness_Area: int
    Soil_Type: int


@app.get("/health")
def health():
    return {"status": "API running"}


def preprocess_input(data: PredictRequest):

    # convertir a dataframe
    df = pd.DataFrame([data.dict()])

    # mismas columnas categóricas del entrenamiento
    df = pd.get_dummies(
        df,
        columns=["Wilderness_Area", "Soil_Type"],
        drop_first=False
    )

    # obtener columnas esperadas por el modelo
    expected_cols = model.feature_names_in_

    # agregar columnas faltantes
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0

    # ordenar columnas
    df = df[expected_cols]

    return df


@app.post("/predict")
def predict(data: PredictRequest):

    X = preprocess_input(data)

    prediction = model.predict(X)

    return {"prediction": int(prediction[0])}