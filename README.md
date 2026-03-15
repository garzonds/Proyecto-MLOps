
# Proyecto MLOps — Pipeline Completo de Machine Learning

Este proyecto implementa un **flujo completo de MLOps** dividido en tres microservicios independientes que trabajan juntos dentro de un entorno orquestado con **Docker Compose**.

El objetivo es simular un flujo real de producción donde:

- Los datos se **extraen desde una API externa**
- Se **procesan y entrenan modelos de Machine Learning**
- El modelo entrenado se **expone mediante una API de inferencia**

Arquitectura general del sistema:

![Arquitectura General](images/architecture.png)

El sistema se divide en **tres estaciones principales**.

---

# Estación 1 — Ingesta y Orquestación de Datos

![Estación 1](images/station1_ingestion.png)

Esta estación se encarga de la **extracción programada de datos desde una API externa y su almacenamiento en una base de datos relacional**.

El proceso es orquestado mediante **Apache Airflow**, permitiendo automatizar la ejecución del pipeline.

### Flujo de trabajo

1. Airflow ejecuta un DAG programado.
2. El DAG realiza una petición a la API externa.
3. Los datos obtenidos se almacenan en PostgreSQL.
4. La base de datos actúa como almacenamiento inicial de datos crudos.

### Componentes principales

Carpeta:


airflow/


Archivos principales:


dags/data_pipeline_dag.py
scripts/fetch_api_data.py
Dockerfile


### Tecnologías utilizadas

- Apache Airflow
- Docker
- PostgreSQL
- API externa

La API utilizada rota los datos cada **5 minutos**, por lo que cada ejecución del DAG solicita un **batch específico de datos**.

---

# Estación 2 — Pipeline de Machine Learning

![Estación 2](images/station2_ml_pipeline.png)

Esta estación corresponde al **pipeline de entrenamiento del modelo de Machine Learning**.

Aquí se realiza la transformación de datos, entrenamiento del modelo y almacenamiento del artefacto resultante.

### Flujo de trabajo

1. El pipeline lee los datos desde PostgreSQL.
2. Se realiza el preprocesamiento de los datos.
3. Se entrena el modelo de Machine Learning.
4. El modelo entrenado se serializa.
5. El modelo se almacena en **MinIO (Object Storage)**.

### Componentes principales

Carpeta:


ml_pipeline/


Archivos principales:


preprocess.py
train_model.py
model_utils.py
Dockerfile


### Procesamiento de datos

El pipeline realiza:

- limpieza de datos
- conversión de variables numéricas
- codificación de variables categóricas

Variables categóricas:


Wilderness_Area
Soil_Type


### Entrenamiento del modelo

Se entrena un modelo:


RandomForestClassifier


División del dataset:


80% entrenamiento
20% prueba


Evaluación mediante:

- Accuracy
- Precision
- Recall
- F1-score

### Almacenamiento del modelo

El modelo entrenado se guarda como:


forest_model.joblib


y se almacena en **MinIO** dentro del bucket:


models


Esto permite mantener los modelos como **artefactos independientes del entorno de entrenamiento**.

---

# Estación 3 — API de Inferencia

![Estación 3](images/station3_inference.png)

Esta estación se encarga de **servir predicciones utilizando el modelo entrenado**.

El modelo se carga desde MinIO y se expone a través de una **API REST implementada con FastAPI**.

### Flujo de trabajo

1. El servicio descarga el modelo desde MinIO.
2. El modelo se carga en memoria.
3. La API recibe variables de entrada.
4. Se genera una predicción en tiempo real.

### Componentes principales

Carpeta:


inference_api/


Archivos principales:


main.py
model_loader.py
Dockerfile


### API REST

Endpoint principal:


POST /predict


Entrada esperada:

Variables cartográficas como:

- Elevation
- Slope
- Soil_Type
- Hillshade
- Distancias geográficas

Salida:


Predicción de Cover Type (clase 1 a 7)


---

# Integración del sistema

Todos los servicios se ejecutan dentro de un entorno unificado utilizando:


docker-compose.yml


Servicios incluidos:

- Airflow
- PostgreSQL
- ML Pipeline
- MinIO
- API de inferencia

Esto permite simular una arquitectura completa de **Machine Learning en producción**.

---

# Flujo completo del sistema


API externa
↓
Airflow (ingesta)
↓
PostgreSQL
↓
ML Pipeline (entrenamiento)
↓
MinIO (almacenamiento del modelo)
↓
FastAPI (inferencia)
↓
Usuario final


---

# Tecnologías utilizadas

- Python
- Docker
- Docker Compose
- Apache Airflow
- PostgreSQL
- MinIO
- FastAPI
- Scikit-learn

---

# Autores

Proyecto desarrollado para la asignatura **MLOps**.

Arquitectura basada en microservicios para el ciclo completo de Machine Learning.
