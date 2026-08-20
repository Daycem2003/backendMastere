FROM python:3.11-slim

WORKDIR /app

# Dépendances système nécessaires (psycopg2, prisma binary engine)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

# Génère le client Prisma dans l'image
RUN poetry run prisma generate

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]