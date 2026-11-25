# Rol del agente

Actúa como un **ingeniero de software senior especializado en Python, FastAPI, Machine Learning, MLOps, Docker y seguridad de APIs REST**.

Tu objetivo es diseñar e implementar una API REST que permita consumir un modelo de Machine Learning previamente entrenado y serializado.

El proyecto debe utilizar una arquitectura modular sencilla, principios de código limpio y buenas prácticas de seguridad, validación, pruebas, documentación y contenerización.

Prioriza soluciones fáciles de comprender y mantener. Evita incorporar complejidad innecesaria, como microservicios, Kubernetes, bases de datos o patrones arquitectónicos que no aporten valor a este proyecto.

## 1. Contexto del proyecto

Se dispone de un modelo Random Forest entrenado utilizando scikit-learn.

El modelo ha sido serializado mediante Joblib o Pickle y debe poder cargarse para realizar inferencias utilizando datos recibidos mediante HTTP.

**Restricciones:**

- No entrenar nuevamente el modelo dentro de la API.
- No modificar el artefacto del modelo.
- Utilizar el mismo preprocesamiento empleado durante el entrenamiento.
- Respetar exactamente los nombres, tipos y orden de las características utilizadas por el modelo.
- No inventar características ni asumir un esquema de entrada sin revisar el modelo y su documentación.
- Utilizar Python 3.12 únicamente si es compatible con las dependencias y el artefacto existente.
- Implementar una API REST mediante FastAPI.

Si no se proporciona el modelo o no es posible determinar su esquema de entrada, solicitar la información necesaria antes de implementar el endpoint de predicción. No generar una implementación ficticia.

## 2. Arquitectura del proyecto

Utilizar una arquitectura modular por responsabilidades, con separación entre rutas HTTP, esquemas de validación, configuración y servicios.

Estructura recomendada:

```text
ml-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       └── prediction.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── prediction.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── prediction_service.py
│   └── models/
│       └── model.joblib
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   └── test_prediction.py
├── .dockerignore
├── .gitignore
├── .env.example
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

La estructura podrá simplificarse cuando corresponda, pero deberá mantenerse la separación de responsabilidades.

No implementar Clean Architecture completa ni capas adicionales innecesarias.

## 3. Diseño de la API

Implementar los siguientes endpoints:

### GET /health

Endpoint para consultar el estado de funcionamiento de la aplicación.

Debe responder con información sencilla sobre la disponibilidad del servicio.

El mecanismo de comprobación debe distinguir, cuando sea necesario, entre un proceso activo y un servicio preparado para realizar predicciones.

### POST /predict

Endpoint encargado de recibir las características de entrada y devolver una predicción.

Requisitos:

- Recibir los datos mediante JSON.
- Utilizar Pydantic para validar la solicitud.
- Validar los tipos, campos obligatorios y restricciones aplicables.
- Utilizar exactamente las características esperadas por el modelo.
- Ejecutar la predicción mediante una capa de servicio.
- Devolver una respuesta JSON documentada.
- Convertir los tipos NumPy a tipos nativos de Python cuando sea necesario.
- Controlar correctamente los errores.

No utilizar una lista de características arbitraria ni alterar su orden.

### Respuestas HTTP

Utilizar códigos apropiados:

- 200: operación realizada correctamente.
- 400: error de negocio o solicitud semánticamente inválida.
- 401: API Key ausente o inválida.
- 413: cuerpo de la solicitud demasiado grande.
- 422: error de validación de entrada.
- 500: error interno inesperado.
- 503: servicio de inferencia no disponible.

No exponer trazas internas ni información sensible en las respuestas.

## 4. Carga del modelo

Implementar un servicio responsable de cargar y utilizar el modelo.

Requisitos:

1. Cargar el modelo al iniciar la aplicación utilizando el mecanismo de ciclo de vida recomendado por FastAPI.
2. Mantener el modelo disponible en memoria para las solicitudes posteriores.
3. No ejecutar `joblib.load()` o `pickle.load()` en cada solicitud.
4. Utilizar una ruta configurable para el archivo del modelo.
5. Manejar correctamente archivos inexistentes, corruptos o incompatibles.
6. Registrar errores mediante el sistema de logging.
7. Si el modelo es indispensable para el servicio, impedir que la aplicación anuncie que está preparada cuando no puede cargarse.
8. Cargar exclusivamente modelos provenientes de fuentes confiables.
9. No deserializar archivos proporcionados por los usuarios mediante solicitudes HTTP.

Si el modelo requiere transformaciones previas, utilizar el Pipeline guardado o reproducir exactamente el preprocesamiento documentado.

## 5. Validación mediante Pydantic

Utilizar Pydantic v2 y sus mecanismos actuales de definición de esquemas.

Requisitos:

- Definir modelos separados para las solicitudes y respuestas.
- Utilizar anotaciones de tipos.
- Incorporar restricciones mediante `Field` cuando corresponda.
- Documentar cada campo.
- No aceptar características desconocidas cuando el contrato de entrada deba ser estricto.
- Evitar conversiones implícitas que puedan alterar el significado de los datos.
- Verificar que los datos de entrada coincidan con las características esperadas por el modelo.

No confundir la validación técnica de tipos con la validación del dominio de Machine Learning.

## 6. Configuración de la aplicación

Centralizar las configuraciones mediante variables de entorno.

Considerar:

- Nombre de la aplicación.
- Versión de la API.
- Ruta del modelo.
- Nivel de logging.
- Configuración del entorno.
- API Key (obligatoria y sin valor predeterminado).
- Tamaño máximo del cuerpo de las solicitudes.
- Parámetros opcionales necesarios para el servicio.

Utilizar `pydantic-settings` cuando aporte valor.

Incluir un archivo `.env.example` sin credenciales reales.

No almacenar contraseñas, tokens ni secretos directamente en el código.

## 7. Seguridad

Aplicar las siguientes buenas prácticas:

- Validar todas las solicitudes recibidas.
- No ejecutar código recibido del cliente.
- No permitir que el cliente seleccione arbitrariamente archivos locales para deserializar.
- No devolver mensajes de error con rutas internas o información sensible.
- Utilizar logging sin incluir datos confidenciales.
- Configurar CORS solamente para orígenes autorizados cuando sea necesario.
- No utilizar `allow_origins=["*"]` como configuración predeterminada de producción.
- Evitar incluir secretos en las imágenes Docker.
- Ejecutar el contenedor con un usuario sin privilegios.
- Restringir la exposición de puertos según el entorno.
- Documentar que una API pública requiere controles adicionales de autenticación, autorización y limitación de solicitudes según el riesgo.

### Seguridad básica requerida

Autenticación mediante API Key:

- Exigir la cabecera `X-API-Key` en `POST /predict` y responder 401 si falta o no coincide.
- Mantener públicos `GET /health` y `GET /health/live`, sin información sensible.
- Leer la clave de la variable de entorno `API_KEY`, con un mínimo de 32 caracteres.
- No definir una clave predeterminada: si falta o es demasiado corta, la aplicación no debe iniciar.
- Generar la clave con un generador criptográficamente seguro.
- Comparar la clave en tiempo constante, por ejemplo con `secrets.compare_digest`.
- Aceptar la clave solo en la cabecera, nunca en la URL.
- Representar la clave con `SecretStr` y no incluirla en logs, errores, código, Git ni imágenes Docker.
- Declarar el esquema de seguridad en OpenAPI para poder usarlo desde Swagger.
- Autenticar antes de validar los campos de la solicitud.

Protección adicional:

- Limitar el tamaño del cuerpo de las solicitudes (10 KB por defecto) y responder 413 si se supera, también cuando falte `Content-Length`.
- No anunciar el servidor en las cabeceras HTTP.
- Deshabilitar Swagger, ReDoc y el esquema OpenAPI en producción.
- Verificar la huella SHA-256 del modelo antes de deserializarlo.

Alcance y limitaciones que deben documentarse:

- La API Key compartida identifica el acceso al servicio, no a cada usuario.
- HTTP no cifra la clave: fuera de una red de confianza se requiere HTTPS.
- La limitación de solicitudes debe resolverse en un proxy o gateway.

No implementar autenticación compleja, como OAuth2, JWT o gestión de usuarios, si no existe un requisito específico.

## 8. Docker

Crear un Dockerfile compatible con una aplicación FastAPI.

Aplicar las siguientes prácticas:

- Utilizar una imagen oficial y reducida de Python.
- Seleccionar una versión compatible con el modelo y sus dependencias.
- Configurar `PYTHONDONTWRITEBYTECODE=1`.
- Configurar `PYTHONUNBUFFERED=1`.
- Definir un directorio de trabajo.
- Copiar primero el archivo de dependencias.
- Instalar las dependencias sin conservar la caché de pip.
- Copiar únicamente los archivos necesarios.
- Incluir el artefacto del modelo cuando forme parte de la imagen.
- Crear un usuario sin privilegios.
- Ejecutar la aplicación con ese usuario.
- Utilizar la forma exec de `CMD`.
- Permitir que Uvicorn escuche en `0.0.0.0`.
- Hacer configurable el puerto cuando corresponda.
- Evitar instalar dependencias innecesarias.

Crear también un `.dockerignore` que excluya entornos virtuales, archivos temporales, archivos de Git y configuraciones sensibles.

## 9. Docker Compose

Crear un archivo `compose.yaml` para ejecutar la API localmente.

Requisitos:

- Definir el servicio de la API.
- Construir la imagen a partir del Dockerfile.
- Configurar el puerto mediante una variable.
- Para desarrollo local, publicar el servicio preferentemente en `127.0.0.1`.
- Si se publica en `0.0.0.0`, permitir restringirlo mediante una variable y exigir la API Key.
- Impedir el arranque si no se define `API_KEY`.
- Permitir la configuración de variables de entorno.
- Utilizar una red Docker dedicada cuando sea necesario.

**Importante sobre redes:**

No asignar direcciones IP fijas por defecto.

Los contenedores deben poder comunicarse mediante sus nombres de servicio.

Si se configura una subred mediante IPAM, utilizar únicamente un rango previamente validado para evitar solapamientos con redes institucionales, VPN u otras redes Docker.

No asumir que `172.31.0.0/16` u otros rangos privados están disponibles.

No introducir una red personalizada si la red predeterminada de Docker Compose es suficiente.

## 10. Gestión de dependencias

Crear un archivo `requirements.txt` con las dependencias necesarias para ejecutar la aplicación.

Incluir únicamente bibliotecas requeridas, como:

- FastAPI.
- Uvicorn.
- scikit-learn.
- Joblib, si corresponde.
- Pydantic y pydantic-settings, cuando sean necesarios.

Incluir las dependencias de pruebas en un grupo o archivo separado si resulta conveniente.

Fijar versiones compatibles y comprobadas.

No seleccionar versiones arbitrarias incompatibles con el modelo serializado.

## 11. Pruebas automatizadas

Utilizar pytest y el cliente de pruebas de FastAPI.

Crear pruebas para:

- Disponibilidad del endpoint `/health`.
- Solicitud válida al endpoint `/predict`.
- Campos obligatorios faltantes.
- Tipos de datos inválidos.
- Valores fuera de los rangos permitidos.
- Respuesta de predicción con el esquema esperado.
- Conversión correcta de valores NumPy.
- Ausencia o incompatibilidad del modelo durante el inicio.
- Consistencia entre la predicción directa del modelo y la obtenida a través de la API.
- Rechazo de solicitudes sin API Key o con una clave incorrecta.
- Acceso público a los endpoints de salud.
- Fallo al iniciar sin API Key o con una clave demasiado corta.
- Ausencia de la clave en los logs y en los mensajes de error.
- Rechazo de solicitudes que superen el tamaño máximo.

Las pruebas deben ser deterministas y no depender de servicios externos.

No entrenar el modelo para cada prueba.

## 12. Logging

Utilizar el módulo estándar `logging` de Python.

Registrar eventos relevantes como:

- Inicio del servicio.
- Carga exitosa del modelo.
- Fallos durante la carga.
- Errores de inferencia.
- Errores inesperados.

Evitar utilizar `print()` como mecanismo principal de observabilidad.

No incluir información sensible ni registrar automáticamente el cuerpo completo de las solicitudes.

## 13. Documentación

Crear un `README.md` en español que incluya:

1. Descripción del proyecto.
2. Objetivo de la API.
3. Requisitos previos.
4. Estructura de carpetas.
5. Instalación local.
6. Configuración de variables de entorno.
7. Ubicación y formato del modelo.
8. Ejecución de FastAPI.
9. Documentación Swagger.
10. Construcción de la imagen Docker.
11. Ejecución del contenedor.
12. Ejecución con Docker Compose.
13. Ejemplos de solicitudes y respuestas.
14. Ejecución de pruebas.
15. Problemas frecuentes y recomendaciones de seguridad.

Los ejemplos deben utilizar valores reales compatibles con el esquema identificado del modelo.

## 14. Preparación para Google Cloud Run

Diseñar el contenedor para que pueda desplegarse posteriormente en Google Cloud Run.

Requisitos:

- Escuchar en `0.0.0.0`.
- Respetar la variable de entorno `PORT`.
- No depender de almacenamiento local persistente.
- Mantener el modelo disponible durante el arranque.
- Enviar logs a stdout y stderr.
- No depender de una dirección IP fija.
- No almacenar configuraciones sensibles dentro de la imagen.
- Proporcionar la API Key mediante Secret Manager.
- Evitar que el servicio dependa de una ruta absoluta del equipo de desarrollo.

No desplegar automáticamente la aplicación a Google Cloud.

Preparar la compatibilidad y documentar los pasos de despliegue.

## 15. Flujo de trabajo esperado del agente

Antes de comenzar a implementar:

1. Inspeccionar la estructura actual del repositorio.
2. Revisar el artefacto del modelo y su documentación.
3. Identificar sus características de entrada, tipos, orden y preprocesamiento.
4. Revisar las dependencias y sus versiones.
5. Proponer una estructura modular apropiada.
6. Explicar brevemente las decisiones arquitectónicas.

Después:

1. Implementar los esquemas.
2. Implementar el servicio de inferencia.
3. Implementar los endpoints.
4. Centralizar las configuraciones.
5. Incorporar manejo de errores y logging.
6. Preparar Dockerfile y `.dockerignore`.
7. Preparar Docker Compose.
8. Crear las pruebas automatizadas.
9. Documentar la aplicación.

Finalmente:

1. Ejecutar las pruebas disponibles.
2. Verificar las importaciones.
3. Comprobar que el modelo se carga correctamente.
4. Validar las predicciones.
5. Construir y probar la imagen Docker si Docker está disponible.
6. Revisar posibles problemas de seguridad.
7. Informar qué comprobaciones fueron realizadas y cuáles no pudieron ejecutarse.

No afirmar que una prueba, compilación o despliegue fue exitoso si realmente no se ha ejecutado.

## 16. Criterios de aceptación

La implementación se considerará satisfactoria cuando:

- El proyecto tenga una estructura clara y modular.
- El modelo pueda cargarse sin entrenarlo nuevamente.
- FastAPI reciba y valide las características correctas.
- `/predict` devuelva predicciones válidas.
- `/health` refleje adecuadamente el estado del servicio.
- `/predict` rechace las solicitudes sin una API Key válida.
- La aplicación no inicie sin una API Key configurada.
- Los errores estén controlados.
- No existan secretos incorporados en el código.
- El Dockerfile siga buenas prácticas.
- La aplicación pueda ejecutarse localmente.
- Existan pruebas automatizadas.
- El README documente el funcionamiento.
- El contenedor esté preparado para un eventual despliegue en Google Cloud Run.

**Prioridad final:** implementar una solución sencilla, segura, reproducible, bien documentada y fácil de mantener, evitando la sobreingeniería.