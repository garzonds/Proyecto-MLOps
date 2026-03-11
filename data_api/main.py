"""
Simulación local de la API del profesor.
Expone el mismo contrato que http://10.43.101.94:8080
- GET /data?group_id=10  → retorna un batch aleatorio de datos
- Cambia de batch cada 5 minutos (10 batches en total)
"""
import time
import random
import threading
from datetime import datetime
from fastapi import FastAPI, Query
import pandas as pd
import numpy as np

app = FastAPI(title="Data API - Simulación Local")

# ── Estado global del batch ───────────────────────────────────────────────────
BATCH_DURATION = 300  # 5 minutos en segundos
N_BATCHES = 10
BATCH_SIZE = 500      # registros por batch

state = {
    "current_batch": 1,
    "last_change": time.time(),
}

WILDERNESS_AREAS = ["Rawah", "Neota", "Comanche", "Cache"]
SOIL_TYPES = [f"Type_{i}" for i in range(1, 41)]
COVER_TYPES = list(range(1, 8))


def generate_batch(batch_id: int, n: int = BATCH_SIZE) -> list:
    """Genera datos sintéticos similares al dataset Forest Cover."""
    random.seed(batch_id * 42)
    np.random.seed(batch_id * 42)

    records = []
    for _ in range(n):
        records.append({
            "batch_id": batch_id,
            "Elevation": round(random.uniform(1859, 3858), 2),
            "Aspect": round(random.uniform(0, 360), 2),
            "Slope": round(random.uniform(0, 66), 2),
            "Horizontal_Distance_To_Hydrology": round(random.uniform(0, 1397), 2),
            "Vertical_Distance_To_Hydrology": round(random.uniform(-173, 601), 2),
            "Horizontal_Distance_To_Roadways": round(random.uniform(0, 7117), 2),
            "Hillshade_9am": random.randint(0, 255),
            "Hillshade_Noon": random.randint(0, 255),
            "Hillshade_3pm": random.randint(0, 255),
            "Horizontal_Distance_To_Fire_Points": round(random.uniform(0, 7173), 2),
            "Wilderness_Area": random.choice(WILDERNESS_AREAS),
            "Soil_Type": random.choice(SOIL_TYPES),
            "Cover_Type": random.choice(COVER_TYPES),
        })
    return records


def batch_rotator():
    """Hilo que rota el batch cada 5 minutos."""
    while True:
        time.sleep(BATCH_DURATION)
        state["current_batch"] = (state["current_batch"] % N_BATCHES) + 1
        state["last_change"] = time.time()
        print(f"[{datetime.now()}] Batch rotado → {state['current_batch']}")


# Iniciar rotador en hilo separado
threading.Thread(target=batch_rotator, daemon=True).start()


@app.get("/data")
def get_data(group_id: int = Query(..., description="Número de grupo")):
    """
    Retorna una muestra aleatoria del batch actual.
    Mismo contrato que la API del profesor.
    """
    batch_id = state["current_batch"]
    batch_data = generate_batch(batch_id)

    # Muestra aleatoria de ~50 registros por petición
    sample_size = random.randint(40, 60)
    sample = random.sample(batch_data, min(sample_size, len(batch_data)))

    seconds_remaining = BATCH_DURATION - (time.time() - state["last_change"])

    return {
        "group_id": group_id,
        "batch_id": batch_id,
        "records": len(sample),
        "seconds_until_next_batch": round(seconds_remaining),
        "data": sample,
    }


@app.get("/status")
def status():
    seconds_remaining = BATCH_DURATION - (time.time() - state["last_change"])
    return {
        "current_batch": state["current_batch"],
        "seconds_until_next_batch": round(seconds_remaining),
        "total_batches": N_BATCHES,
    }
