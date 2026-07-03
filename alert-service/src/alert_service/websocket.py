"""
WebSocket hub for real-time alert broadcasting.

Implements the Observer pattern: AlertService publishes events to the hub,
which fans them out to all connected WebSocket clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketHub:
    """
    Manages WebSocket connections and broadcasts events.

    SOLID-S: single responsibility (WebSocket fan-out only).
    SOLID-O: easy to extend with filters, per-sensor rooms, etc.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("WebSocket connected (total=%d)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(ws)
        logger.info("WebSocket disconnected (total=%d)", len(self._connections))

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Send an event to every connected client.

        Failures are caught silently so a dead client cannot break others.
        """
        message = {
            "event_type": event_type,
            "data": self._jsonify(data),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        payload = json.dumps(message, ensure_ascii=False)

        # Snapshot the connections to avoid holding the lock during sends
        async with self._lock:
            connections = list(self._connections)

        if not connections:
            return

        results = await asyncio.gather(
            *[self._safe_send(ws, payload) for ws in connections],
            return_exceptions=True,
        )
        # Count successes
        sent = sum(1 for r in results if r is True)
        logger.debug("Broadcast %s: %d/%d clients received", event_type, sent, len(connections))

    @staticmethod
    async def _safe_send(ws: WebSocket, payload: str) -> bool:
        """Send a payload, return True on success, False on failure."""
        try:
            await ws.send_text(payload)
            return True
        except Exception:
            logger.warning("WebSocket send failed, closing connection")
            try:
                await ws.close()
            except Exception:
                pass
            return False

    @staticmethod
    def _jsonify(data: dict[str, Any]) -> dict[str, Any]:
        """Convert non-JSON-serializable values (datetimes, UUIDs, enums) to strings."""
        result: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            elif hasattr(v, "value"):  # Enum
                result[k] = v.value
            elif isinstance(v, dict):
                result[k] = WebSocketHub._jsonify(v)
            elif isinstance(v, list):
                result[k] = [WebSocketHub._jsonify_item(item) for item in v]
            else:
                result[k] = v
        return result

    @staticmethod
    def _jsonify_item(item: Any) -> Any:
        """Recursively normalize a single value for JSON serialization."""
        if isinstance(item, datetime):
            return item.isoformat()
        if hasattr(item, "value"):  # Enum
            return item.value
        if isinstance(item, dict):
            return WebSocketHub._jsonify(item)
        if isinstance(item, list):
            return [WebSocketHub._jsonify_item(sub) for sub in item]
        return item


# Module-level singleton
hub = WebSocketHub()