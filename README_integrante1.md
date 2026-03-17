# README — Integrante 1: Ingesta de Datos

## Descripcion

Este modulo implementa la capa de ingesta de datos del proyecto MLOps. Su responsabilidad es recolectar datos desde una API externa, procesarlos y almacenarlos en PostgreSQL para que el pipeline de entrenamiento (Integrante 2) pueda consumirlos.

El flujo completo es:

```
API externa (data_api) --> Airflow DAG --> PostgreSQL (forest_raw)
```

---

## Servicios del docker-compose

El archivo `docker-compose.yml` levanta los siguientes servicios. Cada uno tiene una responsabilidad especifica dentro del sistema:

**postgres_airflow**
Base de datos PostgreSQL dedicada exclusivamente a los metadatos internos de Airflow (DAGs, runs, XComs, variables). No almacena datos del proyecto.

**postgres_data**
Base de datos PostgreSQL donde se almacenan los datos del proyecto en tres etapas: `forest_raw` (datos crudos de la API), `forest_processed` (datos con encoding y limpieza) y `forest_ready` (datos escalados y listos para entrenamiento). El esquema se inicializa automaticamente con `postgres/init.sql`.

**minio**
Almacenamiento de objetos compatible con S3. Se utiliza para guardar los modelos entrenados. Expone la API en el puerto 9000 y la interfaz grafica en el puerto 9001.

**airflow-init**
Contenedor de inicializacion que crea la base de datos de Airflow y el usuario administrador. Se ejecuta una sola vez y termina.

**airflow-webserver**
Interfaz grafica de Airflow. Disponible en `http://localhost:8080`. Permite activar, pausar y monitorear los DAGs.

**airflow-scheduler**
Componente de Airflow que ejecuta los DAGs segun su programacion. Corre en segundo plano de forma continua.

**data_api**
Simulacion local de la API del profesor. Sirve porciones aleatorias del dataset Covertype dividido en 11 batches. Expone el puerto 8081 en el host. Esta API se despliega localmente pero Airflow se conecta a ella como si fuera una maquina externa (ver seccion de conexion externa mas adelante).

**ml_pipeline**
Servicio del Integrante 2. Consume los datos de `forest_raw`, entrena el modelo y lo guarda en MinIO.

**inference_api**
Servicio del Integrante 3. API FastAPI que carga el modelo desde MinIO y realiza predicciones.

---

## Estructura de archivos

```
airflow/
    dags/
        data_pipeline_dag.py    <- DAG de orquestacion
    scripts/
        fetch_api_data.py       <- Script de ingesta
    Dockerfile
data_api/
    main.py                     <- API local del dataset
    Dockerfile
    data/
        covertype.csv           <- Dataset completo (581,012 filas)
postgres/
    init.sql                    <- Esquema de las tablas
docker-compose.yml
```

---

## Conexion a la API como maquina externa

El enunciado exige que la conexion a la API de datos se realice como si fuera una maquina externa, es decir, no por la red interna de Docker sino via internet o localhost.

Para cumplir este requisito se usa el DNS especial `host.docker.internal`, que permite a cualquier contenedor Docker acceder al host (la maquina donde corre Docker) como si fuera una IP externa:

```
Airflow (contenedor)
    --> http://host.docker.internal:8081
        --> host Windows/Mac
            --> puerto 8081
                --> contenedor data_api
```

Esto esta configurado en `docker-compose.yml` dentro de la seccion `x-airflow-common`:

```yaml
DATA_API_URL: http://host.docker.internal:8081  # Simular red externa
```

Si se usa la API del profesor en lugar de la local, cambiar esta variable por:

```yaml
DATA_API_URL: http://10.43.101.94:8080
```

---

## Configuracion del tiempo de actualizacion de batches

La API local rota el batch de datos cada cierto tiempo configurable. Este tiempo se controla con la variable `MIN_UPDATE_TIME` en `data_api/main.py`:

```python
MIN_UPDATE_TIME = 60  # segundos
```

| Escenario | Valor recomendado |
|-----------|-------------------|
| Pruebas locales | 60 segundos |
| API del profesor | 300 segundos (5 minutos) |

Cuando se cambia `MIN_UPDATE_TIME`, tambien se debe actualizar el `schedule_interval` del DAG en `airflow/dags/data_pipeline_dag.py` para que esten sincronizados:

```python
# Pruebas locales (cada 1 minuto)
schedule_interval="*/1 * * * *"

# API del profesor (cada 5 minutos)
schedule_interval="*/5 * * * *"
```

---

## DAG: data_pipeline_dag

El DAG orquesta el proceso completo de ingesta. Cada ejecucion realiza exactamente UNA peticion a la API y almacena los registros recibidos en PostgreSQL. No se permiten multiples peticiones por ejecucion.

Flujo de tareas:

```
start --> fetch_and_store --> verify_data --> end
```

**fetch_and_store**: Llama a la API, convierte los tipos de datos (strings a float/int segun corresponda) y guarda las filas en `forest_raw`. Si el batch ya existe en la base de datos, omite la insercion para evitar duplicados. Si la API retorna 400 (todos los batches recolectados), termina sin error.

**verify_data**: Verifica que los datos se guardaron correctamente contando los registros en `forest_raw` y loggeando el total acumulado.

---

## Como correr

### Requisitos previos

- Docker Desktop instalado y corriendo
- El archivo `covertype.csv` en `data_api/data/`

### Levantar todos los servicios

```bash
docker-compose up --build -d
```

### Verificar que todo esta corriendo

```bash
docker-compose ps
```

Todos los servicios deben mostrar `running` o `healthy`.

### Probar la API local

```bash
curl "http://localhost:8081/data?group_number=10"
```

### Reiniciar el conteo de batches

Si se quiere volver a recolectar desde el batch 1:

```bash
curl "http://localhost:8081/restart_data_generation?group_number=10"
```

### Activar el DAG

1. Abrir `http://localhost:8080` (usuario: `admin`, contrasena: `admin`)
2. Activar el toggle del DAG `data_pipeline_dag`
3. Disparar manualmente con el boton Trigger DAG

### Verificar datos en PostgreSQL

```bash
docker exec -it postgres_data psql -U mlops -d mlops_db \
  -c "SELECT batch_id, COUNT(*) as registros FROM forest_raw GROUP BY batch_id ORDER BY batch_id;"
```

### Pausar el DAG cuando se tengan los 10 batches

```bash
docker exec -it airflow_scheduler airflow dags pause data_pipeline_dag
```

---

## Interfaces graficas

| Servicio | URL | Usuario | Contrasena |
|----------|-----|---------|------------|
| Airflow | http://localhost:8080 | admin | admin |
| MinIO | http://localhost:9001 | minioadmin | minioadmin |
| Data API (Swagger) | http://localhost:8081/docs | - | - |

---

## Evidencia de funcionamiento

Agregar capturas de pantalla de:

1. Vista Grid del DAG en Airflow mostrando runs en verde
2. Vista Graph del DAG mostrando el flujo de tareas
3. Logs del task `fetch_and_store` mostrando registros guardados
4. Resultado de la consulta a PostgreSQL con los 10 batches recolectados
5. docker-compose ps mostrando todos los servicios corriendo
