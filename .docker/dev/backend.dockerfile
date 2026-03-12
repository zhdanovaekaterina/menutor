FROM python:3.14-slim

RUN \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --system zhdanova

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml

RUN \
    pip install --upgrade pip && \
    pip install --no-cache-dir .

USER zhdanova

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
