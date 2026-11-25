# ML API: clasificación de flores Iris

## 1. Descripción

API REST construida con FastAPI que sirve un modelo Random Forest de scikit-learn ya entrenado. La API no entrena ni modifica el modelo: lo carga una vez al iniciar y lo mantiene en memoria.

## 2. Objetivo

Recibir por HTTP las cuatro medidas de una flor y devolver su especie (*setosa*, *versicolor* o *virginica*) con la probabilidad de cada una.

| Método y ruta | Función | Respuestas |
|---|---|---|
| `GET /health` | Indica si el servicio está preparado para predecir | 200, 503 |
| `GET /health/live` | Indica solo si el proceso está activo | 200 |
| `POST /predict` | Clasifica una flor; requiere API Key | 200, 401, 413, 422, 500, 503 |

El código 400 no se usa: no hay reglas de negocio aparte de la validación de entrada, que responde 422 (también si el JSON está mal formado).

## 3. Requisitos previos

- Python 3.13 para la ejecución local.
- Docker con Docker Compose para la ejecución en contenedor.

## 4. Estructura de carpetas

```text
ml-api/
├── app/
│   ├── __main__.py               # Punto de entrada: python -m app
│   ├── main.py                   # Creación de la aplicación y ciclo de vida
│   ├── api/
│   │   ├── dependencies.py       # Inyección del servicio
│   │   ├── errors.py             # Traducción de errores a HTTP
│   │   ├── security.py           # API Key y límite de tamaño
│   │   └── routes/               # health.py y prediction.py
│   ├── core/                     # config.py y logging.py
│   ├── schemas/                  # Contratos Pydantic
│   ├── services/
│   │   └── prediction_service.py # Carga del modelo e inferencia
│   └── models/model.joblib
├── tests/
├── Dockerfile
├── compose.yaml
├── requirements.txt              # Ejecución
└── requirements-dev.txt          # Ejecución y pruebas
```

Las rutas solo tratan HTTP y la inferencia está en el servicio, que no depende de FastAPI.

## 5. Instalación local

Desde la carpeta `ml-api`, en PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

En Linux o macOS:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Si no tiene Python 3.13 pero sí conda:

```powershell
conda create -n ml-api python=3.13
conda activate ml-api
python -m pip install -r requirements-dev.txt
```

## 6. Variables de entorno

Solo `API_KEY` es obligatoria: sin ella, la API no arranca. Copie el ejemplo y genere una clave.

PowerShell:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Bash:

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Pegue el resultado en `.env`, después de `API_KEY=`.

| Variable | Valor predeterminado | Uso |
|---|---|---|
| `API_KEY` | Ninguno (obligatoria) | Clave de acceso, mínimo 32 caracteres |
| `MAX_BODY_BYTES` | 10240 | Tamaño máximo del cuerpo, en bytes |
| `APP_NAME` | API de clasificación de Iris | Nombre mostrado |
| `API_VERSION` | 1.0.0 | Versión de la API |
| `ENVIRONMENT` | `development` (`production` en la imagen) | `production` deshabilita Swagger |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `HOST` | `127.0.0.1` (`0.0.0.0` en la imagen) | Interfaz de escucha |
| `PORT` | 8000 (8080 en la imagen) | Puerto de escucha |
| `MODEL_PATH` | `app/models/model.joblib` | Ruta del modelo |
| `MODEL_SHA256` | Huella del modelo incluido | Integridad del modelo |
| `CORS_ALLOWED_ORIGINS` | `[]` | Lista JSON de orígenes autorizados |
| `BIND_ADDRESS` | `0.0.0.0` | Interfaz publicada por Docker Compose |
| `HOST_PORT` | 8000 | Puerto publicado por Docker Compose |

## 7. Modelo

- **Ubicación:** `app/models/model.joblib` (Joblib, 167.745 bytes).
- **Tipo:** `RandomForestClassifier` de 100 árboles, guardado con scikit-learn 1.6.1.
- **Preprocesamiento:** ninguno. El artefacto es el clasificador, sin `Pipeline`.
- **Origen:** notebook `clase-45.ipynb`, con el dataset Iris y `train_test_split(test_size=0.20, random_state=42, stratify=y)`.
- **Exactitud en prueba:** 0,9 (30 observaciones).

El modelo se entrenó con matrices NumPy, por lo que el archivo no guarda nombres de columnas. El orden y los nombres proceden de `load_iris`:

| Orden | Campo JSON | Nombre en `load_iris` | Rango de entrenamiento (cm) |
|---|---|---|---|
| 1 | `sepal_length_cm` | sepal length (cm) | 4,3 a 7,9 |
| 2 | `sepal_width_cm` | sepal width (cm) | 2,0 a 4,4 |
| 3 | `petal_length_cm` | petal length (cm) | 1,1 a 6,9 |
| 4 | `petal_width_cm` | petal width (cm) | 0,1 a 2,5 |

Clases: 0 = setosa, 1 = versicolor, 2 = virginica.

Hay dos validaciones distintas:

- **Técnica (422):** campos obligatorios, sin campos desconocidos, números finitos, mayores que 0 y de 30 cm como máximo. Los textos y booleanos no se convierten a número.
- **De dominio:** un valor fuera del rango de entrenamiento se predice, pero aparece en `out_of_range_features`, porque el resultado es menos fiable.

Al iniciar se comprueban la huella SHA-256 (antes de deserializar), la versión de scikit-learn, el tipo, el número de características y las clases. Si algo falla, el proceso sigue activo, pero `/health` y `/predict` responden 503.

## 8. Ejecución de FastAPI

```powershell
python -m app
```

La API queda en <http://127.0.0.1:8000>. Con recarga automática durante el desarrollo:

```powershell
uvicorn app.main:create_app --factory --reload
```

## 9. Documentación Swagger

Con `ENVIRONMENT=development`:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

Para probar `/predict` desde Swagger, pulse **Authorize** e introduzca la API Key.

## 10. Construcción de la imagen Docker

```powershell
docker build -t ml-api:local .
```

La imagen parte de `python:3.13.18-slim-trixie`, incluye el modelo y se ejecuta con un usuario sin privilegios.

## 11. Ejecución del contenedor

```powershell
$env:API_KEY = "su-api-key"
docker run --rm -p 127.0.0.1:8000:8080 -e API_KEY -e ENVIRONMENT=development ml-api:local
```

Sin `ENVIRONMENT=development`, Swagger queda deshabilitado.

## 12. Ejecución con Docker Compose

```powershell
docker compose up --build -d --wait
docker compose logs -f api
docker compose down
```

El servicio se publica en `0.0.0.0`, por lo que otros equipos de la red pueden usarlo en `http://IP-DEL-EQUIPO:8000` si el firewall lo permite. `/predict` exige API Key, pero HTTP no la cifra: en redes que no sean de confianza, defina `BIND_ADDRESS=127.0.0.1` para limitar el servicio a este equipo. Puede cambiar el puerto con `HOST_PORT`.

Compose usa su red predeterminada y solo toma de `.env` las variables `API_KEY`, `MAX_BODY_BYTES`, `BIND_ADDRESS`, `HOST_PORT`, `ENVIRONMENT`, `LOG_LEVEL` y `CORS_ALLOWED_ORIGINS`.

## 13. Ejemplos

Sustituya `su-api-key` por la clave de su archivo `.env`.

PowerShell:

```powershell
$flor = @{
    sepal_length_cm = 6.0
    sepal_width_cm  = 2.7
    petal_length_cm = 5.1
    petal_width_cm  = 1.6
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/predict `
    -Headers @{ 'X-API-Key' = 'su-api-key' } `
    -ContentType 'application/json' -Body $flor
```

Bash:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'X-API-Key: su-api-key' \
  -H 'Content-Type: application/json' \
  -d '{"sepal_length_cm": 6.0, "sepal_width_cm": 2.7, "petal_length_cm": 5.1, "petal_width_cm": 1.6}'
```

Respuesta 200:

```json
{
  "class_id": 1,
  "class_name": "versicolor",
  "probabilities": {"setosa": 0.0, "versicolor": 0.66, "virginica": 0.34},
  "out_of_range_features": []
}
```

Respuesta 401, sin API Key o con una incorrecta:

```json
{"detail": "API Key ausente o inválida"}
```

Respuesta 422, con un texto en lugar de un número y sin `petal_width_cm`:

```json
{
  "detail": [
    {"type": "float_type", "loc": ["body", "sepal_length_cm"], "msg": "Input should be a valid number"},
    {"type": "missing", "loc": ["body", "petal_width_cm"], "msg": "Field required"}
  ]
}
```

Respuesta 503 de `/predict`, cuando el modelo no se pudo cargar:

```json
{"detail": "Servicio de inferencia no disponible"}
```

Respuesta 200 de `/health`:

```json
{"status": "ok", "model_loaded": true}
```

## 14. Pruebas

```powershell
python -m pytest -v
```

Las pruebas usan el modelo real, no lo entrenan y no requieren red. Una de ellas compara las 150 observaciones de Iris entre el modelo y la API.

## 15. Problemas frecuentes y seguridad

### Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| La API no arranca y el log menciona `api_key` | Falta `API_KEY` o tiene menos de 32 caracteres. |
| Compose indica «Defina API_KEY» | Cree `.env` como se explica en la sección 6. |
| `/predict` responde 401 | Falta la cabecera `X-API-Key` o la clave no coincide. |
| `/predict` responde 413 | El cuerpo supera `MAX_BODY_BYTES`. |
| `/health` responde 503 | El modelo no se cargó. El log indica el motivo. |
| «La huella SHA-256 del modelo no coincide» | El archivo cambió. Si el cambio es legítimo, actualice `MODEL_SHA256`. |
| «Modelo corrupto o incompatible» | Suele ser otra versión de scikit-learn. Instale `requirements.txt` en un entorno limpio. |
| `pip` intenta compilar scikit-learn o falla al instalarlo | La versión de Python es 3.14 o posterior. Use 3.13. |
| `/docs` responde 404 | `ENVIRONMENT` es `production`. |
| El puerto está ocupado | Cambie `PORT` en local o `HOST_PORT` en Compose. |
| «Acceso denegado» en `pytest-of-<usuario>` (Windows) | Ejecute `python -m pytest --basetemp .pytest_tmp`. |

Para obtener la huella de un modelo nuevo en PowerShell:

```powershell
(Get-FileHash app\models\model.joblib -Algorithm SHA256).Hash.ToLower()
```

Un modelo con otras características, clases o rangos también exige actualizar `schemas/prediction.py` y las constantes de `services/prediction_service.py`.

### Seguridad

- `/predict` exige una API Key en la cabecera `X-API-Key`. `/health` y `/health/live` son públicos.
- **HTTP no cifra la clave.** Fuera de una red de confianza, use HTTPS mediante un proxy inverso o Cloud Run.
- La clave es compartida: no distingue usuarios ni permisos. Si se filtra, genere otra y reinicie el servicio.
- Compose pasa la clave como variable de entorno: quien pueda usar Docker en el equipo puede leerla.
- La API no limita la cantidad de solicitudes. Antes de publicarla en Internet, añada esa limitación en un proxy o gateway.
- El cuerpo de las solicitudes está limitado a 10 KB de forma predeterminada.
- Cargar un archivo Joblib o Pickle puede ejecutar código. Use solo modelos de origen confiable; la huella detecta cambios, pero no prueba que el original sea seguro.
- CORS está deshabilitado de forma predeterminada. No use `*` en producción.
- Los logs no incluyen el cuerpo de las solicitudes y los errores no devuelven trazas.
- No guarde secretos en el código ni en la imagen. `.env` está excluido de Git y de Docker.

## Despliegue en Google Cloud Run

El contenedor escucha en `0.0.0.0`, respeta `PORT`, envía los logs a stdout, incluye el modelo y no necesita almacenamiento persistente. Los pasos siguientes son orientativos: **este proyecto no se ha desplegado en Google Cloud**.

Sustituya `PROYECTO`, `REGION` y `CUENTA_DE_SERVICIO`:

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com --project PROYECTO

gcloud artifacts repositories create ml-api --repository-format=docker --location=REGION --project PROYECTO

gcloud builds submit --tag REGION-docker.pkg.dev/PROYECTO/ml-api/ml-api:1.0.0 --project PROYECTO

# El secreto se lee de un archivo local que no debe versionarse ni llevar salto de línea final.
gcloud secrets create ml-api-key --data-file=api-key.txt --project PROYECTO

gcloud secrets add-iam-policy-binding ml-api-key --project PROYECTO \
  --member=serviceAccount:CUENTA_DE_SERVICIO --role=roles/secretmanager.secretAccessor

gcloud run deploy ml-api \
  --image REGION-docker.pkg.dev/PROYECTO/ml-api/ml-api:1.0.0 \
  --region REGION --project PROYECTO \
  --service-account CUENTA_DE_SERVICIO \
  --no-allow-unauthenticated \
  --set-secrets API_KEY=ml-api-key:latest \
  --memory 512Mi --max-instances 2 \
  --startup-probe httpGet.path=/health,httpGet.port=8080,periodSeconds=5,failureThreshold=6
```

- `--no-allow-unauthenticated` exige una identidad autorizada por IAM, además de la API Key.
- `--set-secrets` entrega la API Key desde Secret Manager, fuera de la imagen.
- La sonda sobre `/health` es importante: la sonda TCP predeterminada daría por válida una instancia que no pudo cargar el modelo.
- `--max-instances` acota el costo.
