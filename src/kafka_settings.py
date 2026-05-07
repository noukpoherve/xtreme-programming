import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")

WATER_QUALITY_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "urbanhub-water-quality-local")
KAFKA_CONSUMER_TIMEOUT_SECONDS = int(os.getenv("KAFKA_CONSUMER_TIMEOUT_SECONDS", "30"))
