from dataclasses import dataclass, field
from typing import Optional
import json
import logging
import os
import redis

from iot_service.api_errors import RepositoryError

logger = logging.getLogger(__name__)


@dataclass
class Sensor:
    sensor_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    active: bool = True
    metadata: dict = field(default_factory=dict)


class SensorRepository:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._strict = os.getenv("REDIS_STRICT", "0") == "1"
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.prefix = "sensor:"
        self.index_key = "sensors:index"
        self._memory_store: dict[str, str] = {}
        self._memory_ids: set[str] = set()
        self._use_memory = False

        try:
            self.redis_client.ping()
        except Exception as exc:
            if self._strict:
                logger.warning("Redis unavailable for sensors in strict mode: %s", exc)
            else:
                logger.warning("Redis unavailable for sensors, using in-memory store: %s", exc)
                self._use_memory = True

    def _memory_payload(self, sensor: Sensor) -> str:
        return json.dumps({
            "sensor_id": sensor.sensor_id,
            "name": sensor.name,
            "location": sensor.location,
            "latitude": sensor.latitude,
            "longitude": sensor.longitude,
            "active": sensor.active,
            "metadata": sensor.metadata,
        })

    def save(self, sensor: Sensor) -> None:
        try:
            if self._use_memory:
                key = f"{self.prefix}{sensor.sensor_id}"
                self._memory_store[key] = self._memory_payload(sensor)
                self._memory_ids.add(sensor.sensor_id)
                logger.info("Sensor saved in memory: %s", sensor.sensor_id)
                return

            key = f"{self.prefix}{sensor.sensor_id}"
            payload = self._memory_payload(sensor)
            self.redis_client.set(key, payload)
            if not self.redis_client.sismember("sensors:all", sensor.sensor_id):
                self.redis_client.sadd("sensors:all", sensor.sensor_id)
            logger.info("Sensor saved: %s", sensor.sensor_id)
        except Exception as e:
            raise RepositoryError(f"Failed to save sensor: {e}") from e

    def get(self, sensor_id: str) -> Optional[Sensor]:
        try:
            if self._use_memory:
                key = f"{self.prefix}{sensor_id}"
                payload = self._memory_store.get(key)
                if payload:
                    data = json.loads(payload)
                    return Sensor(
                        sensor_id=data["sensor_id"],
                        name=data["name"],
                        location=data["location"],
                        latitude=data["latitude"],
                        longitude=data["longitude"],
                        active=data["active"],
                        metadata=data.get("metadata", {}),
                    )
                return None

            key = f"{self.prefix}{sensor_id}"
            payload = self.redis_client.get(key)
            if payload:
                data = json.loads(payload)
                return Sensor(
                    sensor_id=data["sensor_id"],
                    name=data["name"],
                    location=data["location"],
                    latitude=data["latitude"],
                    longitude=data["longitude"],
                    active=data["active"],
                    metadata=data.get("metadata", {}),
                )
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get sensor: {e}") from e

    def get_all(self) -> list[Sensor]:
        try:
            if self._use_memory:
                sensors = []
                for sensor_id in self._memory_ids:
                    sensor = self.get(sensor_id)
                    if sensor:
                        sensors.append(sensor)
                return sensors

            sensor_ids = self.redis_client.smembers("sensors:all")
            sensors = []
            for sensor_id in sensor_ids:
                sensor = self.get(sensor_id)
                if sensor:
                    sensors.append(sensor)
            return sensors
        except Exception as e:
            raise RepositoryError(f"Failed to get all sensors: {e}") from e

    def update(self, sensor_id: str, sensor: Sensor) -> bool:
        try:
            if self._use_memory:
                key = f"{self.prefix}{sensor_id}"
                if key not in self._memory_store:
                    return False
                self._memory_store[key] = self._memory_payload(sensor)
                self._memory_ids.add(sensor.sensor_id)
                return True

            key = f"{self.prefix}{sensor_id}"
            if not self.redis_client.exists(key):
                return False
            payload = json.dumps({
                "sensor_id": sensor.sensor_id,
                "name": sensor.name,
                "location": sensor.location,
                "latitude": sensor.latitude,
                "longitude": sensor.longitude,
                "active": sensor.active,
                "metadata": sensor.metadata,
            })
            self.redis_client.set(key, payload)
            logger.info("Sensor updated: %s", sensor_id)
            return True
        except Exception as e:
            raise RepositoryError(f"Failed to update sensor: {e}") from e

    def delete(self, sensor_id: str) -> bool:
        try:
            if self._use_memory:
                key = f"{self.prefix}{sensor_id}"
                if key not in self._memory_store:
                    return False
                del self._memory_store[key]
                self._memory_ids.discard(sensor_id)
                logger.info("Sensor deleted from memory: %s", sensor_id)
                return True

            key = f"{self.prefix}{sensor_id}"
            if self.redis_client.delete(key):
                self.redis_client.srem("sensors:all", sensor_id)
                logger.info("Sensor deleted: %s", sensor_id)
                return True
            return False
        except Exception as e:
            raise RepositoryError(f"Failed to delete sensor: {e}") from e

    def count(self) -> int:
        try:
            if self._use_memory:
                return len(self._memory_ids)
            return self.redis_client.scard("sensors:all")
        except Exception as e:
            raise RepositoryError(f"Failed to count sensors: {e}") from e
