import pytest
from datetime import datetime, timezone

from alert_service.models import AlertPayload, Localisation
from alert_service.service import AlertService


@pytest.fixture
def service():
    return AlertService()


@pytest.fixture
def sample_payload():
    return AlertPayload(
        alert_id="alert-123",
        event_id="event-123",
        capteur_id="SEINE-001",
        timestamp=datetime.now(timezone.utc),
        severity="CRITICAL",
        type="ph_critique",
        message="pH trop bas",
        localisation=Localisation(
            latitude=48.8637,
            longitude=2.3017,
            point_reference="Pont Alma",
        ),
        trace_id="trace-123",
        metadata={"ph": 5.2},
    )


@pytest.mark.asyncio
async def test_process_alert_created(service, sample_payload):
    result = await service.process_alert(sample_payload)
    assert result["status"] == "CREATED"
    assert result["alert_id"] == "alert-123"
