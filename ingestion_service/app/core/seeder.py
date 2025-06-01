import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import crud, schemas
from app.models.models import Sensor
from app.services.cache_service import cache_service


logger = logging.getLogger(__name__)


class IngestionServiceSeeder:
    """Handles seeding for Ingestion Service"""

    def __init__(self):
        self.seed_data_path = Path(__file__).parent.parent.parent / "seed_data"

    async def seed_all(self, db: AsyncSession) -> None:
        """Seed all data for ingestion service"""
        try:
            logger.info("Starting ingestion service seeding...")

            # Check if seeding is needed
            if await self._is_database_populated(db):
                logger.info("Database already populated, skipping seeding")
                return

            # Seed sensors
            await self.seed_sensors(db)

            logger.info("Ingestion service seeding completed successfully")

        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            raise

    async def seed_sensors(self, db: AsyncSession) -> None:
        """Seed sensors from JSON file - idempotent operation"""
        try:
            sensors_file = self.seed_data_path / "sensors.json"
            
            if not sensors_file.exists():
                logger.warning(f"Sensors seed file not found: {sensors_file}")
                return

            with open(sensors_file, 'r') as f:
                sensors_data = json.load(f)

            seeded_count = 0
            for sensor_data in sensors_data:
                # Check if sensor already exists
                existing_sensor = await crud.sensor.get_by_device_id(
                    db, device_id=sensor_data["device_id"]
                )

                if existing_sensor:
                    logger.debug(f"Sensor {sensor_data['device_id']} already exists, skipping")
                    continue

                # Create sensor
                sensor_create = schemas.sensor.SensorCreate(
                    device_id=sensor_data["device_id"],
                    device_type=sensor_data["device_type"]
                )

                created_sensor = await crud.sensor.create(db=db, obj_in=sensor_create)

                # Cache the sensor details
                sensor_read = schemas.sensor.SensorRead.model_validate(created_sensor)
                await cache_service.set_sensor_details(sensor_read)

                seeded_count += 1
                logger.debug(f"Seeded sensor: {sensor_data['device_id']}")

            logger.info(f"Seeded {seeded_count} sensors")

        except Exception as e:
            logger.error(f"Error seeding sensors: {e}")
            raise

    async def _is_database_populated(self, db: AsyncSession) -> bool:
        """Check if database already has data to avoid re-seeding"""
        try:
            # Check if any sensors exist
            result = await db.execute(select(Sensor).limit(1))
            sensor = result.scalars().first()
            return sensor is not None
        except Exception as e:
            logger.error(f"Error checking database population: {e}")
            return False

    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """Helper method to load JSON seed data files"""
        file_path = self.seed_data_path / filename
        if not file_path.exists():
            logger.warning(f"Seed file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading seed file {filename}: {e}")
            return []


ingestion_seeder = IngestionServiceSeeder()
