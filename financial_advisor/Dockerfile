FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
RUN pip install --no-cache-dir --upgrade setuptools>=80.10.2 wheel>=0.46.2

COPY pyproject.toml ./
COPY src/ ./src/

RUN uv pip install --system -e .

ENV PYTHONPATH=/app/src

CMD ["fa-extract"]
