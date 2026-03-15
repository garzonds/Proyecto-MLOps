"""
Simulación local de la API del profesor.
Mismo contrato que http://10.43.101.94:8080

Endpoints:
- GET /data?group_number=10
- GET /restart_data_generation?group_number=10
- GET /status
"""
import random
import time
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

MIN_UPDATE_TIME = 300  # 5 minutos — igual que la API del profesor

app = FastAPI(
    title="Proyecto MLOps - Data API (Simulación Local)",
    version="1.0.0",
    description="Simulación local de la API del profesor. Mismo contrato que http://10.43.101.94:8080",
)

# ── Modelos ───────────────────────────────────────────────────────────────────
class BatchResponse(BaseModel):
    group_number: int = Field(..., description="Número de grupo solicitado")
    batch_number: int = Field(..., description="Índice del batch servido")
    data: List[List[str]] = Field(..., description="Filas del dataset en formato string")


# ── Generación de datos sintéticos ────────────────────────────────────────────
WILDERNESS_AREAS = ["Rawah", "Neota", "Comanche", "Cache"]
SOIL_TYPES = [f"C{7700 + i}" for i in range(1, 41)]
COVER_TYPES = list(range(1, 8))
TOTAL_RECORDS = 5000
BATCH_SIZE = TOTAL_RECORDS // 10


def generate_dataset(seed: int = 42) -> List[List[str]]:
    random.seed(seed)
    dataset = []
    for _ in range(TOTAL_RECORDS):
        row = [
            str(round(random.uniform(1859, 3858), 2)),
            str(round(random.uniform(0, 360), 2)),
            str(round(random.uniform(0, 66), 2)),
            str(round(random.uniform(0, 1397), 2)),
            str(round(random.uniform(-173, 601), 2)),
            str(round(random.uniform(0, 7117), 2)),
            str(random.randint(0, 255)),
            str(random.randint(0, 255)),
            str(random.randint(0, 255)),
            str(round(random.uniform(0, 7173), 2)),
            random.choice(WILDERNESS_AREAS),
            random.choice(SOIL_TYPES),
            str(random.choice(COVER_TYPES)),
        ]
        dataset.append(row)
    return dataset


DATASET = generate_dataset()


def get_batch_data(batch_number: int) -> List[List[str]]:
    start = batch_number * BATCH_SIZE
    end = start + BATCH_SIZE
    batch = DATASET[start:end]
    sample_size = BATCH_SIZE // 10
    return random.sample(batch, min(sample_size, len(batch)))


# ── Estado por grupo: [timestamp, batch_actual] ───────────────────────────────
timestamps = {str(g): [0, -1] for g in range(1, 12)}


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"Proyecto MLOps": "Data API - Simulación Local"}


@app.get("/data", response_model=BatchResponse, tags=["data"])
async def read_data(
    group_number: int = Query(..., ge=1, le=11, description="Número de grupo (1-10)", example=10)
):
    if group_number < 1 or group_number > 11:
        raise HTTPException(status_code=400, detail="Número de grupo inválido")

    if timestamps[str(group_number)][1] >= 11:
        raise HTTPException(
            status_code=400,
            detail="Ya se recolectó toda la información mínima necesaria"
        )

    current_time = time.time()
    last_update_time = timestamps[str(group_number)][0]

    if current_time - last_update_time > MIN_UPDATE_TIME:
        timestamps[str(group_number)][0] = current_time
        timestamps[str(group_number)][1] += 2 if timestamps[str(group_number)][1] == -1 else 1

    batch_number = timestamps[str(group_number)][1]
    data = get_batch_data(batch_number)

    return {
        "group_number": group_number,
        "batch_number": batch_number,
        "data": data,
    }


@app.get("/restart_data_generation", tags=["admin"])
async def restart_data(
    group_number: int = Query(..., ge=1, le=11, description="Número de grupo a reiniciar", example=10)
):
    if group_number < 1 or group_number > 11:
        raise HTTPException(status_code=400, detail="Número de grupo inválido")

    timestamps[str(group_number)][0] = 0
    timestamps[str(group_number)][1] = -1
    return {"ok": True, "group_number": group_number, "message": "Reiniciado correctamente"}


@app.get("/status", tags=["info"])
async def status():
    result = {}
    current_time = time.time()
    for g in range(1, 11):
        last = timestamps[str(g)][0]
        seconds_remaining = max(0, MIN_UPDATE_TIME - (current_time - last))
        result[f"group_{g}"] = {
            "current_batch": timestamps[str(g)][1],
            "seconds_until_next_batch": round(seconds_remaining),
        }
    return result