import requests
import json
from datetime import datetime, timezone
from typing import Dict, List
import time


class TestIoTSystem:
    """End-to-end tests for IoT Event Ingestion and Alerting System"""

    def test_01_setup_sensors(self, session: requests.Session, api_config: Dict, test_sensors: List[Dict]):
        """Test creating sensors in the system"""
        ingestion_url = api_config["ingestion_base_url"]

        for sensor in test_sensors:
            response = session.post(
                f"{ingestion_url}/sensors",
                json=sensor,
                timeout=api_config["timeout"]
            )
            # Accept both successful creation and sensor already exists
            if response.status_code in [200, 201]:
                print(f"Created sensor: {sensor['device_id']} ({sensor['device_type']})")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"Sensor already exists: {sensor['device_id']} ({sensor['device_type']})")
            else:
                assert False, f"Failed to create sensor {sensor['device_id']}: {response.text}"

    def test_02_setup_authorized_users(self, session: requests.Session, api_config: Dict, authorized_users: List[str]):
        """Test creating authorized users in the system"""
        alerting_url = api_config["alerting_base_url"]

        for user_id in authorized_users:
            user_data = {"user_id": user_id}
            response = session.post(
                f"{alerting_url}/authorized-users",
                json=user_data,
                timeout=api_config["timeout"]
            )
            # Accept both successful creation and user already exists
            if response.status_code in [200, 201]:
                print(f"Created authorized user: {user_id}")
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"Authorized user already exists: {user_id}")
            else:
                assert False, f"Failed to create user {user_id}: {response.text}"

    def test_03_access_control_unauthorized_alert(self, session: requests.Session, api_config: Dict):
        """Test access control event that should trigger an alert (unauthorized user)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Send unauthorized access event
        event_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "access_attempt",
            "user_id": "unauthorized_user"
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent unauthorized access event")

        # Check if alert was generated
        response = session.get(
            f"{alerting_url}/alerts",
            params={"event_type": "access_attempt"},
            timeout=api_config["timeout"]
        )
        assert response.status_code == 200, f"Failed to retrieve alerts: {response.text}"

        alerts = response.json()
        unauthorized_alerts = [
            alert for alert in alerts 
            if alert.get("alert_type") == "unauthorized_access" and 
               alert.get("device_id") == "AA:BB:CC:DD:EE:FF"
        ]
        assert len(unauthorized_alerts) > 0, "Expected unauthorized access alert was not generated"
        print("Unauthorized access alert generated successfully")

    def test_04_access_control_authorized_no_alert(self, session: requests.Session, api_config: Dict):
        """Test access control event that should NOT trigger an alert (authorized user)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Get initial alert count
        response = session.get(f"{alerting_url}/alerts", timeout=api_config["timeout"])
        initial_alert_count = len(response.json()) if response.status_code == 200 else 0

        # Send authorized access event
        event_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "access_attempt",
            "user_id": "authorized_user"
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent authorized access event")

        # Verify no new alerts were generated
        response = session.get(f"{alerting_url}/alerts", timeout=api_config["timeout"])
        current_alert_count = len(response.json()) if response.status_code == 200 else 0

        assert current_alert_count == initial_alert_count, "No alert should be generated for authorized access"
        print("No alert generated for authorized user (correct behavior)")
    
    def test_05_speed_violation_alert(self, session: requests.Session, api_config: Dict):
        """Test radar speed event that should trigger an alert (speed > 90 km/h)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Send speed violation event
        event_data = {
            "device_id": "11:22:33:44:55:66",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "speed_violation",
            "speed_kmh": 120,
            "location": "Zone A"
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent speed violation event (120 km/h)")

        # Check if alert was generated
        response = session.get(
            f"{alerting_url}/alerts",
            params={"event_type": "speed_violation"},
            timeout=api_config["timeout"]
        )
        assert response.status_code == 200, f"Failed to retrieve alerts: {response.text}"

        alerts = response.json()
        speed_alerts = [
            alert for alert in alerts 
            if alert.get("alert_type") == "speed_violation" and 
               alert.get("device_id") == "11:22:33:44:55:66"
        ]
        assert len(speed_alerts) > 0, "Expected speed violation alert was not generated"
        print("Speed violation alert generated successfully")

    def test_06_speed_normal_no_alert(self, session: requests.Session, api_config: Dict):
        """Test radar speed event that should NOT trigger an alert (speed <= 90 km/h)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Get initial alert count
        response = session.get(f"{alerting_url}/alerts", timeout=api_config["timeout"])

        # Send normal speed event
        event_data = {
            "device_id": "11:22:33:44:55:66",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "speed_violation",
            "speed_kmh": 70,
            "location": "Zone A"
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent normal speed event (70 km/h)")

        # Verify no new speed violation alerts were generated
        response = session.get(
            f"{alerting_url}/alerts",
            params={"event_type": "speed_violation"},
            timeout=api_config["timeout"]
        )
        speed_alerts = response.json() if response.status_code == 200 else []
        recent_speed_alerts = [
            alert for alert in speed_alerts
            if alert.get("device_id") == "11:22:33:44:55:66" and
               "70" in str(alert.get("details", {}))
        ]

        assert len(recent_speed_alerts) == 0, "No alert should be generated for normal speed"
        print("No alert generated for normal speed (correct behavior)")

    def test_07_intrusion_detection_alert(self, session: requests.Session, api_config: Dict, test_images: Dict):
        """Test intrusion detection event that should trigger an alert (restricted area)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Send intrusion detection event
        after_hours_time = datetime.now(timezone.utc).replace(hour=20, minute=0, second=0, microsecond=0)
        event_data = {
            "device_id": "77:88:99:AA:BB:CC",
            "timestamp": after_hours_time.isoformat(),
            "event_type": "motion_detected",
            "zone": "Restricted Area",
            "confidence": 0.95,
            "photo_base64": test_images["alert_image"]
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent intrusion detection event (Restricted Area)")

        # Wait for alert processing
        time.sleep(3)

        # Check if alert was generated
        response = session.get(
            f"{alerting_url}/alerts",
            params={"alert_type": "intrusion_detection"},
            timeout=api_config["timeout"]
        )
        assert response.status_code == 200, f"Failed to retrieve alerts: {response.text}"

        alerts = response.json()
        intrusion_alerts = [
            alert for alert in alerts 
            if alert.get("alert_type") == "intrusion_detection" and 
               alert.get("device_id") == "77:88:99:AA:BB:CC"
        ]
        assert len(intrusion_alerts) > 0, "Expected intrusion detection alert was not generated"

        # Validate the latest alert and photo storage
        latest_alert = intrusion_alerts[-1]
        print(f"Alert structure: {json.dumps(latest_alert, indent=2)}")

        # Validate photo is stored directly
        assert "photo_base64" in latest_alert, "Alert should have photo_base64 field"
        assert latest_alert["photo_base64"] == test_images["alert_image"], "Stored photo should match sent photo"

        print("Intrusion detection alert generated successfully with photo")
        print(f"Photo size: {len(latest_alert['photo_base64'])} characters")

    def test_08_intrusion_detection_open_area_no_alert(self, session: requests.Session, api_config: Dict, test_images: Dict):
        """Test intrusion detection event that should NOT trigger an alert (open area)"""
        ingestion_url = api_config["ingestion_base_url"]
        alerting_url = api_config["alerting_base_url"]

        # Get current intrusion alert count
        response = session.get(
            f"{alerting_url}/alerts",
            params={"alert_type": "intrusion_detection"},
            timeout=api_config["timeout"]
        )
        initial_intrusion_count = len(response.json()) if response.status_code == 200 else 0

        # Send motion detection in open area
        event_data = {
            "device_id": "77:88:99:AA:BB:CC",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "motion_detected",
            "zone": "Open Area",
            "confidence": 0.80,
            "photo_base64": test_images["no_alert_image"]
        }

        response = session.post(
            f"{ingestion_url}/events",
            json=event_data,
            timeout=api_config["timeout"]
        )
        assert response.status_code in [200, 201], f"Failed to create event: {response.text}"
        print("Sent motion detection event (Open Area)")

        # Verify no new intrusion alerts were generated for open area
        response = session.get(
            f"{alerting_url}/alerts",
            params={"alert_type": "intrusion_detection"},
            timeout=api_config["timeout"]
        )
        current_intrusion_count = len(response.json()) if response.status_code == 200 else 0

        # Check if any new intrusion alerts were created
        if current_intrusion_count > initial_intrusion_count:
            # Check if the new alerts are actually for Open Area
            intrusion_alerts = response.json()
            recent_alerts = intrusion_alerts[initial_intrusion_count:]
            open_area_alerts = [
                alert for alert in recent_alerts
                if "Open Area" in str(alert)
            ]
            assert len(open_area_alerts) == 0, f"No alert should be generated for motion in open area, but found: {open_area_alerts}"

        print("No alert generated for open area motion (correct behavior)")

    def test_09_retrieve_events(self, session: requests.Session, api_config: Dict):
        """Test retrieving stored events with filters"""
        ingestion_url = api_config["ingestion_base_url"]

        # Get all events
        response = session.get(f"{ingestion_url}/events", timeout=api_config["timeout"])
        assert response.status_code == 200, f"Failed to retrieve events: {response.text}"

        all_events = response.json()
        assert len(all_events) > 0, "Should have stored events from previous tests"
        print(f"Retrieved {len(all_events)} total events")

        # Test filtering by event type
        response = session.get(
            f"{ingestion_url}/events",
            params={"event_type": "access_attempt"},
            timeout=api_config["timeout"]
        )
        assert response.status_code == 200, f"Failed to retrieve filtered events: {response.text}"
        access_events = response.json()
        print(f"Retrieved {len(access_events)} access attempt events")

        # Test filtering by device type
        response = session.get(
            f"{ingestion_url}/events",
            params={"device_type": "radar"},
            timeout=api_config["timeout"]
        )
        assert response.status_code == 200, f"Failed to retrieve device-filtered events: {response.text}"
        radar_events = response.json()
        print(f"Retrieved {len(radar_events)} radar events")

    def test_10_retrieve_alerts_summary(self, session: requests.Session, api_config: Dict):
        """Test retrieving all alerts and validate the complete flow"""
        alerting_url = api_config["alerting_base_url"]

        # Get all alerts
        response = session.get(f"{alerting_url}/alerts", timeout=api_config["timeout"])
        assert response.status_code == 200, f"Failed to retrieve alerts: {response.text}"

        all_alerts = response.json()
        print(f"Retrieved {len(all_alerts)} total alerts")

        # Validate we have the expected alert types
        alert_types = [alert.get("alert_type") for alert in all_alerts]

        assert "unauthorized_access" in alert_types, "Missing unauthorized access alert"
        assert "speed_violation" in alert_types, "Missing speed violation alert"
        assert "intrusion_detection" in alert_types, "Missing intrusion detection alert"
