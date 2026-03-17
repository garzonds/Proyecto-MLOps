### Proyecto MLOps — Pipeline Completo de Machine Learning
## Descripción

Este proyecto implementa una arquitectura de Machine Learning en producción, basada en microservicios, que cubre todo el ciclo de vida del modelo:

Ingesta de datos
Procesamiento
Entrenamiento
Despliegue
Inferencia

La solución está completamente contenerizada usando Docker Compose, integrando herramientas clave del ecosistema MLOps.

## Contexto del problema

El objetivo del modelo es predecir el tipo de cobertura forestal a partir de variables cartográficas como:

Elevación
Pendiente
Distancias geográficas
Variables categóricas del terreno
Debido a la indisponibilidad de la API original, se implementó una API simulada, garantizando la continuidad del flujo de datos en batches dinámicos.

## Arquitectura del sistema

![Arquitectura General](images/architecture.png)


| Servicio           | Descripción                                     |
| ------------------ | ----------------------------------------------- |
| **Airflow**        | Orquestación del pipeline                       |
| **PostgreSQL**     | Almacenamiento de datos (raw, processed, ready) |
| **MinIO**          | Almacenamiento de modelos                       |
| **Data API**       | Simulación de fuente de datos                   |
| **ML Pipeline**    | Entrenamiento del modelo                        |
| **FastAPI**        | API de inferencia                               |
| **Docker Compose** | Orquestación de contenedores                    |


---

### Flujo de trabajo
1. Llamada a la API
2. Airflow ejecuta un DAG programado. y este realiza la peticion a la API externa (nos toco modelarla en local)
3. Los datos obtenidos se almacenan en PostgreSQL.
4. La base de datos actúa como almacenamiento inicial de datos crudos.
5. ML pipeline
6. MiniO
7. FastAPI
8. Usuario

--- 

El sistema se divide en **tres estaciones principales**.

# Estación 1 — Ingesta y Orquestación de Datos

![Estación 1](images/station1_ingestion.png)

El sistema está compuesto por los siguientes servicios:

Responsable de la extracción automatizada de datos desde la API y su almacenamiento en PostgreSQL.

## Flujo

-Airflow ejecuta un DAG programado
-Se realiza una única petición a la API por ejecución
-Se almacenan los datos en forest_raw
-Se acumulan batches de datos

## Tecnologías

-Apache Airflow
-PostgreSQL
-Docker

### Componentes principales

Carpeta:

airflow/

Archivos principales:
dags/data_pipeline_dag.py
scripts/fetch_api_data.py
Dockerfile
API externa

La API utilizada rota los datos cada **5 minutos**, por lo que cada ejecución del DAG solicita un **batch específico de datos**.

---

# Estación 2 — Pipeline de Machine Learning

Esta estación implementa el pipeline de entrenamiento del modelo de Machine Learning, encargado de transformar los datos, entrenar el modelo y almacenar el artefacto resultante en un sistema de almacenamiento desacoplado.

El pipeline se ejecuta dentro de un contenedor Docker (ml_pipeline) y forma parte del flujo MLOps del proyecto.

## Arquitectura del Sistema

El sistema está compuesto por los siguientes servicios:

![Estación 2](images/station2_ml_pipeline.png)

## Flujo del Pipeline

El pipeline es completamente automatizado:

- Lectura de datos desde  PostgreSQL
- Procesamiento de datos   
- Entrenamiento del modelo  
- Evaluación del modelo  
- Almacenamiento del modelo en MinIO  

## Modelo

Algoritmo: RandomForestClassifier

Parámetros:
n_estimators=200
random_state=42

## Evaluación

Accuracy
Precision
Recall
F1-score

## Almacenamiento

Archivo: forest_model.joblib
Bucket: models (MinIO)

## Decisiones de diseño

Separación entre datos (PostgreSQL) y modelos (MinIO)
Pipeline desacoplado del sistema de inferencia
Reproducibilidad mediante Docker

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

Esto permite simular una arquitectura completa de **Machine Learning en producción**.

---

# Flujo completo del sistema


API externa - Airflow (ingesta) - PostgreSQL - ML Pipeline (entrenamiento) - MinIO (almacenamiento del modelo) - FastAPI (inferencia) Usuario final


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

## Conclusión

Se construyó un sistema completo de MLOps que automatiza el flujo desde datos hasta predicciones en producción.
La solución es reproducible, escalable y alineada con prácticas reales de la industria.

# Autores

Proyecto desarrollado para la asignatura **MLOps**.
Arquitectura basada en microservicios para el ciclo completo de Machine Learning.
