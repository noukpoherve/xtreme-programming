import json
import logging
import os
from typing import Optional

import redis

from alert_service.api_errors import RepositoryError
from alert_service.models import AlertPayload

logger = logging.getLogger(__name__)


class AlertRepository:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._strict = os.getenv("REDIS_STRICT", "0") == "1"
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.prefix = "alert:"
        self.index_key = "alerts:index"
        self._memory_store: dict[str, str] = {}
        self._memory_index: list[str] = []
        self._use_memory = False

        try:
            self.redis_client.ping()
        except Exception as exc:
            if self._strict:
                logger.warning("Redis unavailable for alerts in strict mode: %s", exc)
            else:
                logger.warning("Redis unavailable for alerts, using in-memory store: %s", exc)
                self._use_memory = True

    def _memory_get(self, alert_id: str) -> Optional[AlertPayload]:
        payload = self._memory_store.get(f"{self.prefix}{alert_id}")
        if payload:
            return AlertPayload.model_validate_json(payload)
        return None

    def _memory_save(self, alert: AlertPayload) -> None:
        key = f"{self.prefix}{alert.alert_id}"
        is_new = key not in self._memory_store
        self._memory_store[key] = alert.model_dump_json()
        if is_new and alert.alert_id not in self._memory_index:
            self._memory_index.insert(0, alert.alert_id)

    def _memory_delete(self, alert_id: str) -> bool:
        key = f"{self.prefix}{alert_id}"
        if key not in self._memory_store:
            return False
        del self._memory_store[key]
        self._memory_index = [stored_id for stored_id in self._memory_index if stored_id != alert_id]
        return True

    async def save(self, alert: AlertPayload) -> None:
        try:
            if self._use_memory:
                self._memory_save(alert)
                logger.info("Alert saved in memory: %s", alert.alert_id)
                return

            key = f"{self.prefix}{alert.alert_id}"
            payload = alert.model_dump_json()
            is_new = not self.redis_client.exists(key)
            self.redis_client.set(key, payload)
            if is_new:
                self.redis_client.lpush(self.index_key, alert.alert_id)
            logger.info("Alert saved: %s", alert.alert_id)
        except Exception as e:
            raise RepositoryError(f"Failed to save alert: {e}") from e

    async def get(self, alert_id: str) -> Optional[AlertPayload]:
        try:
            if self._use_memory:
                return self._memory_get(alert_id)

            key = f"{self.prefix}{alert_id}"
            payload = self.redis_client.get(key)
            if payload:
                return AlertPayload.model_validate_json(payload)
            return None
        except Exception as e:
            raise RepositoryError(f"Failed to get alert: {e}") from e

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[AlertPayload]:
        try:
            if self._use_memory:
                alert_ids = self._memory_index[offset : offset + limit]
            else:
                alert_ids = self.redis_client.lrange(
                    self.index_key, offset, offset + limit - 1
                )
            alerts = []
            for alert_id in alert_ids:
                alert = await self.get(alert_id)
                if alert:
                    alerts.append(alert)
            return alerts
        except Exception as e:
            raise RepositoryError(f"Failed to get all alerts: {e}") from e

    async def get_by_sensor(self, sensor_id: str) -> list[AlertPayload]:
        try:
            if self._use_memory:
                alert_ids = list(self._memory_index)
            else:
                alert_ids = self.redis_client.lrange(self.index_key, 0, -1)
            alerts = []
            for alert_id in alert_ids:
                alert = await self.get(alert_id)
                if alert and alert.sensor_id == sensor_id:
                    alerts.append(alert)
            return alerts
        except Exception as e:
            raise RepositoryError(f"Failed to get alerts by sensor: {e}") from e

    async def update(self, alert_id: str, alert: AlertPayload) -> bool:
        try:
            if self._use_memory:
                key = f"{self.prefix}{alert_id}"
                if key not in self._memory_store:
                    return False
                self._memory_store[key] = alert.model_dump_json()
                return True

            key = f"{self.prefix}{alert_id}"
            if not self.redis_client.exists(key):
                return False
            payload = alert.model_dump_json()
            self.redis_client.set(key, payload)
            logger.info("Alert updated: %s", alert_id)
            return True
        except Exception as e:
            raise RepositoryError(f"Failed to update alert: {e}") from e

    async def delete(self, alert_id: str) -> bool:
        try:
            if self._use_memory:
                deleted = self._memory_delete(alert_id)
                if deleted:
                    logger.info("Alert deleted from memory: %s", alert_id)
                return deleted

            key = f"{self.prefix}{alert_id}"
            if self.redis_client.delete(key):
                self.redis_client.lrem(self.index_key, 1, alert_id)
                logger.info("Alert deleted: %s", alert_id)
                return True
            return False
        except Exception as e:
            raise RepositoryError(f"Failed to delete alert: {e}") from e

    async def count(self) -> int:
        try:
            if self._use_memory:
                return len(self._memory_index)
            return self.redis_client.llen(self.index_key)
        except Exception as e:
            raise RepositoryError(f"Failed to count alerts: {e}") from e
