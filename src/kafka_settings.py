import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9094")

WATER_QUALITY_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")
WATER_QUALITY_DLQ_TOPIC = os.getenv("WATER_QUALITY_DLQ_TOPIC", "mesure.qualite.eau.dlq")
POLLUTION_ALERT_TOPIC = os.getenv("POLLUTION_ALERT_TOPIC", "alerte.pollution.detectee")

KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "urbanhub-water-quality-local")
