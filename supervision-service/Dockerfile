FROM python:3.12-slim

WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ /app/src/

# Exposer le port
EXPOSE 8002

# Démarrer le service
CMD ["python", "-m", "uvicorn", "supervision_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
