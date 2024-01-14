FROM python:3.9.18-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y wget  # for health check

COPY poetry.lock pyproject.toml ./
RUN python -m pip install --no-cache-dir poetry==1.6.1 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

COPY . .

CMD ["poetry", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
