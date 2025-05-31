import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alert_processor import alert_processor
from app.schemas.alert import AlertCreate


class TestAlertProcessor:
    """Essential test cases for the 3 core alert criteria from requirements."""

    async def test_process_unauthorized_access_event(self, db_session, sample_access_event, mock_cache_service):
        """Test unauthorized access detection (user_id not in authorized list)."""
        mock_cache_service.is_user_authorized.return_value = False
        
        result = await alert_processor.process_event(sample_access_event, db_session)
        
        assert result is not None
        assert isinstance(result, AlertCreate)
        assert result.alert_type == "unauthorized_access"
        assert result.event_id == sample_access_event.id
        assert result.device_id == sample_access_event.device_id

    async def test_process_authorized_access_event(self, db_session, sample_authorized_access_event, mock_cache_service):
        """Test authorized access event (should not trigger alert)."""
        mock_cache_service.is_user_authorized.return_value = True
        
        result = await alert_processor.process_event(sample_authorized_access_event, db_session)
        assert result is None

    async def test_process_speed_violation_event(self, db_session, sample_speed_event):
        """Test speed violation detection (speed > 90 km/h)."""
        result = await alert_processor.process_event(sample_speed_event, db_session)
        
        assert result is not None
        assert isinstance(result, AlertCreate)
        assert result.alert_type == "speed_violation"
        assert result.event_id == sample_speed_event.id
        assert result.device_id == sample_speed_event.device_id

    async def test_process_safe_speed_event(self, db_session, sample_safe_speed_event):
        """Test safe speed event (should not trigger alert)."""
        result = await alert_processor.process_event(sample_safe_speed_event, db_session)
        assert result is None

    async def test_process_intrusion_event(self, db_session, sample_intrusion_event):
        """Test intrusion detection (restricted area + after hours)."""
        result = await alert_processor.process_event(sample_intrusion_event, db_session)
        
        assert result is not None
        assert isinstance(result, AlertCreate)
        assert result.alert_type == "intrusion_detection"
        assert result.event_id == sample_intrusion_event.id
        assert result.device_id == sample_intrusion_event.device_id

    async def test_process_safe_motion_event(self, db_session, sample_safe_motion_event):
        """Test safe motion event (should not trigger alert)."""
        result = await alert_processor.process_event(sample_safe_motion_event, db_session)
        assert result is None

    def test_is_restricted_area(self):
        """Test restricted area detection logic."""
        processor = alert_processor
        
        assert processor._is_restricted_area("Restricted Area") is True
        assert processor._is_restricted_area("Secure Zone") is True
        assert processor._is_restricted_area("Open Area") is False
        assert processor._is_restricted_area("Public Zone") is False

    def test_is_after_hours(self):
        """Test after hours detection logic (18:00 - 05:59)."""
        processor = alert_processor
        
        assert processor._is_after_hours(datetime(2024, 12, 18, 22, 0, 0)) is True
        assert processor._is_after_hours(datetime(2024, 12, 18, 2, 0, 0)) is True
        assert processor._is_after_hours(datetime(2024, 12, 18, 12, 0, 0)) is False
        assert processor._is_after_hours(datetime(2024, 12, 18, 17, 0, 0)) is False 