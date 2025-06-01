import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx

from app import crud, schemas
from app.models.models import AuthorizedUser
from app.services.cache_service import cache_service
from app.core.config import settings


logger = logging.getLogger(__name__)


class AlertingServiceSeeder:
    """Handles seeding for Alerting Service"""
    
    def __init__(self):
        self.seed_data_path = Path(__file__).parent.parent.parent / "seed_data"
    
    async def seed_all(self, db: AsyncSession) -> None:
        """Seed all data for alerting service"""
        try:
            logger.info("Starting alerting service seeding...")
            
            # Check if seeding is needed
            if await self._is_database_populated(db):
                logger.info("Database already populated, skipping seeding")
                return
            
            # Seed authorized users
            await self.seed_authorized_users(db)
            
            # sync sensor data from ingestion service
            await self.sync_sensor_cache()
            
            logger.info("Alerting service seeding completed successfully")
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            raise

    async def seed_authorized_users(self, db: AsyncSession) -> None:
        """Seed authorized users from JSON file - idempotent operation"""
        try:
            users_file = self.seed_data_path / "authorized_users.json"
            
            if not users_file.exists():
                logger.warning(f"Authorized users seed file not found: {users_file}")
                return
            
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            seeded_count = 0
            for user_data in users_data:
                # Check if user already exists
                existing_user = await crud.authorized_user.get_by_user_id(
                    db, user_id=user_data["user_id"]
                )
                
                if existing_user:
                    logger.debug(f"User {user_data['user_id']} already exists, skipping")
                    continue
                
                # Create authorized user
                user_create = schemas.authorized_user.AuthorizedUserCreate(
                    user_id=user_data["user_id"],
                    description=user_data.get("description")
                )
                
                created_user = await crud.authorized_user.create(db=db, obj_in=user_create)
                
                # Add to cache
                await cache_service.add_authorized_user(user_data["user_id"])
                
                seeded_count += 1
                logger.debug(f"Seeded authorized user: {user_data['user_id']}")
            
            # Update cache with all authorized users
            all_users = await crud.authorized_user.get_all(db)
            user_ids = {user.user_id for user in all_users}
            await cache_service.set_authorized_users(user_ids)
            
            logger.info(f"Seeded {seeded_count} authorized users")
            
        except Exception as e:
            logger.error(f"Error seeding authorized users: {e}")
            raise

    async def sync_sensor_cache(self) -> None:
        """Sync sensor data from Ingestion Service via API for caching"""
        try:
            # Only attempt if ingestion service URL is configured
            ingestion_url = getattr(settings, 'INGESTION_SERVICE_URL', None)
            if not ingestion_url:
                logger.info("Ingestion service URL not configured, skipping sensor cache sync")
                return
            
            logger.info("Syncing sensor data from Ingestion Service...")
            
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                try:
                    response = await client.get(f"{ingestion_url}/api/v1/sensors")
                    
                    if response.status_code == 200:
                        sensors = response.json()
                        
                        # Cache sensor data for alerting service use
                        for sensor in sensors:
                            await cache_service.redis_client.hset(
                                "sensors_registry",
                                sensor["device_id"],
                                json.dumps({
                                    "device_id": sensor["device_id"],
                                    "device_type": sensor["device_type"]
                                })
                            )
                        
                        logger.info(f"Synced {len(sensors)} sensors to alerting service cache")
                    else:
                        logger.warning(f"Failed to fetch sensors from ingestion service: {response.status_code}")
                        
                except httpx.ConnectError:
                    logger.warning("Could not connect to ingestion service for sensor sync")
                except httpx.TimeoutException:
                    logger.warning("Timeout while syncing sensors from ingestion service")
                    
        except Exception as e:
            logger.error(f"Error syncing sensor cache: {e}")
    
    async def _is_database_populated(self, db: AsyncSession) -> bool:
        """Check if database already has data to avoid re-seeding"""
        try:
            # Check if any authorized users exist
            result = await db.execute(select(AuthorizedUser).limit(1))
            user = result.scalars().first()
            return user is not None
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


alerting_seeder = AlertingServiceSeeder()
