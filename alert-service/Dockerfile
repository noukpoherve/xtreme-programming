FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "alert_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
