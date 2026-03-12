FROM python:3.14-slim

RUN useradd --system zhdanova

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml

RUN \
    pip install --upgrade pip && \
    pip install --no-cache-dir .[dev]

RUN \
    mkdir ./.pytest_cache && \
    chown zhdanova ./.pytest_cache

USER zhdanova

CMD ["pytest", "-vs"]
