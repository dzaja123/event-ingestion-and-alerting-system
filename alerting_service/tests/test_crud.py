import pytest
from datetime import datetime

from app.crud.alert import alert
from app.schemas.alert import AlertCreate, AlertFilter


class TestAlertCRUD:
    """Essential test cases for alert CRUD operations based on requirements."""

    async def test_create_alert(self, db_session):
        """Test creating an alert."""
        alert_data = AlertCreate(
            event_id=1,
            device_id="AA:BB:CC:DD:EE:FF",
            alert_type="unauthorized_access",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        created_alert = await alert.create(db=db_session, obj_in=alert_data)
        
        assert created_alert.event_id == 1
        assert created_alert.device_id == "AA:BB:CC:DD:EE:FF"
        assert created_alert.alert_type == "unauthorized_access"

    async def test_get_alert_by_id(self, db_session):
        """Test getting alert by ID."""
        alert_data = AlertCreate(
            event_id=1,
            device_id="AA:BB:CC:DD:EE:FF",
            alert_type="speed_violation",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        created_alert = await alert.create(db=db_session, obj_in=alert_data)
        retrieved_alert = await alert.get_by_id(db=db_session, alert_id=created_alert.id)
        
        assert retrieved_alert.id == created_alert.id
        assert retrieved_alert.alert_type == "speed_violation"

    async def test_get_alerts_by_alert_type(self, db_session):
        """Test filtering alerts by type."""
        alerts_data = [
            AlertCreate(
                event_id=1,
                device_id="AA:BB:CC:DD:EE:FF",
                alert_type="unauthorized_access",
                timestamp=datetime(2024, 12, 18, 14, 0, 0)
            ),
            AlertCreate(
                event_id=2,
                device_id="BB:CC:DD:EE:FF:AA",
                alert_type="speed_violation",
                timestamp=datetime(2024, 12, 18, 15, 0, 0)
            )
        ]
        
        for alert_data in alerts_data:
            await alert.create(db=db_session, obj_in=alert_data)
        
        filter_obj = AlertFilter(alert_type="unauthorized_access")
        unauthorized_alerts = await alert.get_multi(db=db_session, filters=filter_obj)
        
        assert len(unauthorized_alerts) == 1
        assert unauthorized_alerts[0].alert_type == "unauthorized_access"

    async def test_get_alerts_by_device_id(self, db_session):
        """Test filtering alerts by device ID."""
        device_id = "AA:BB:CC:DD:EE:FF"
        alert_data = AlertCreate(
            event_id=1,
            device_id=device_id,
            alert_type="intrusion_detection",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        await alert.create(db=db_session, obj_in=alert_data)
        
        filter_obj = AlertFilter(device_id=device_id)
        device_alerts = await alert.get_multi(db=db_session, filters=filter_obj)
        
        assert len(device_alerts) == 1
        assert device_alerts[0].device_id == device_id 