Parte 2 — Pipeline de Entrenamiento y Almacenamiento de Modelo
Descripción

Esta parte del proyecto implementa el pipeline de entrenamiento de Machine Learning dentro de una arquitectura MLOps basada en contenedores.

El pipeline realiza las siguientes tareas:

1. Carga los datos del dataset Covertype en PostgreSQL.
2. Realiza el preprocesamiento de los datos.
3. Entrena un modelo Random Forest Classifier.
4. Evalúa el modelo.
5. Guarda el modelo entrenado.
6. Almacena el modelo en MinIO (Object Storage).

Esto permite simular un flujo real de producción donde los modelos se almacenan en un repositorio de artefactos.

Arquitectura

El pipeline utiliza los siguientes servicios:

PostgreSQL  →  ML Pipeline  →  MinIO
   │               │            │
   │               │            └── almacenamiento de modelos
   │               │
   │               └── entrenamiento del modelo
   │
   └── almacenamiento del dataset

Componentes:

Servicio	  -  Función
PostgreSQL	   almacenamiento del dataset
ML Pipeline	   entrenamiento del modelo
MinIO	         almacenamiento de modelos


Estructura del proyecto
P2/
│
├── docker-compose-ml.yml
│
├── postgres_init/
│   └── init.sql
│
├── ml_pipelane/
│   ├── Dockerfile
│   ├── preprocess.py
│   ├── train_model.py
│   ├── model_utils.py
│   └── requirements.txt
│
└── data/
    └── covertype.csv
    
Servicios del sistema

PostgreSQL
Se utiliza para almacenar el dataset que será utilizado para entrenar el modelo.

Tabla creada:
forest_data

Columnas principales:
Elevation
Aspect
Slope
Horizontal_Distance_To_Hydrology
Vertical_Distance_To_Hydrology
Horizontal_Distance_To_Roadways
Hillshade_9am
Hillshade_Noon
Hillshade_3pm
Horizontal_Distance_To_Fire_Points
Wilderness_Area
Soil_Type
Cover_Type

ML Pipeline
El pipeline realiza las siguientes etapas:

1. Carga de datos:
   Si la tabla forest_data está vacía, el sistema carga automáticamente: data/covertype.csv en PostgreSQL.

2. Preprocesamiento
   Se realizan las siguientes transformaciones: Conversión de variables numéricas
   Eliminación de valores nulos
   Codificación de variables categóricas (get_dummies)
   Variables categóricas:
      - Wilderness_Area
      - Soil_Type
3. Entrenamiento del modelo
   Se entrena un modelo: RandomForestClassifier
   Parámetros:
    
    n_estimators = 200
    random_state = 42
    n_jobs = -1

    División del dataset:    80% entrenamiento    20% prueba
4. Evaluación

   Se calcula:
    - Accuracy
    - Precision
    - Recall
    - F1-score
    
    Ejemplo de resultado obtenido:
    - Accuracy ≈ 0.90
5. Guardado del modelo, El modelo se guarda localmente como: model.joblib
6. Almacenamiento en MinIO
  El modelo se sube automáticamente a MinIO como artefacto de modelo.
  Bucket:
   - models
  Objeto almacenado:
   - forest_model.joblib
   - MinIO (Model Storage)
  MinIO actúa como repositorio de artefactos de Machine Learning.
  
  Configuración:
   - endpoint: minio:9000
   - user: minioadmin
   - password: minioadmin
  
  Interfaz web: http://localhost:9001

Al ingresar se puede visualizar el bucket:

models

y el modelo entrenado:

forest_model.joblib
Cómo ejecutar el pipeline
1. Levantar los contenedores

Desde la carpeta P2 ejecutar:

docker compose -f docker-compose-ml.yml up --build

Esto levantará:

PostgreSQL

MinIO

ML Pipeline

2. Ejecución automática

El pipeline realizará automáticamente:

Carga de datos en PostgreSQL

Preprocesamiento

Entrenamiento del modelo

Evaluación

Guardado del modelo

Subida a MinIO

3. Verificar el modelo en MinIO

Abrir en el navegador:

http://localhost:9001

Credenciales:

usuario: minioadmin
contraseña: minioadmin

Luego acceder al bucket:

models

y verificar el archivo:

forest_model.joblib
