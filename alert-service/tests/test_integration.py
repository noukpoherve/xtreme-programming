import pytest
from unittest.mock import AsyncMock

from alert_service.service import AlertService
from alert_service.state_config import SensorState
from alert_service.models import SensorStateView


@pytest.mark.asyncio
async def test_restore_states_from_db():
    # Arrange
    mock_transition_repo = AsyncMock()
    mock_transition_repo.get_current_states.return_value = {
        "uuid-1": SensorStateView(
            sensor_id="SEINE-RESTORE-001",
            state=SensorState.CRITICAL,
            anomaly_count=4,
        )
    }

    service = AlertService(transition_repo=mock_transition_repo)

    # Act
    await service.restore_states_from_db()

    # Assert
    registry = service.registry
    processor = registry.get("SEINE-RESTORE-001")
    assert processor.state == SensorState.CRITICAL
    assert processor.anomaly_count == 4

