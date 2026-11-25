# Python más reciente con soporte en scikit-learn 1.6.1, la versión del modelo
# (no publica paquetes para 3.14 ni posteriores).
FROM python:3.13.18-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8080

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser

# El código y el modelo quedan propiedad de root: el proceso solo puede leerlos.
COPY app ./app

USER 10001

EXPOSE 8080

# `python -m app` lee HOST y PORT; Cloud Run define PORT en ejecución.
CMD ["python", "-m", "app"]
