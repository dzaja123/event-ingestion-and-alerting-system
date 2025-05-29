import json
import redis.asyncio as aioredis
from app.core.config import settings
from app.schemas.sensor import SensorRead


class CacheService:
    def __init__(self):
        self.redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def get_sensor_details(self, device_id: str) -> SensorRead | None:
        cache_key = f"sensor:{device_id}"
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            try:
                return SensorRead.model_validate(json.loads(cached_data))
            except Exception:
                return None
        return None

    async def set_sensor_details(self, sensor: SensorRead):
        cache_key = f"sensor:{sensor.device_id}"
        await self.redis_client.set(cache_key, sensor.model_dump_json(), ex=settings.SENSOR_CACHE_TTL_SECONDS)

    async def close(self):
        await self.redis_client.close()


cache_service = CacheService()
