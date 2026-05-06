FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --no-dev

COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV ALERT_REDIS_HOST=redis
ENV ALERT_KAFKA_BOOTSTRAP_SERVERS=kafka:9092

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "alert_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
