import json
import redis.asyncio as aioredis
from app.core.config import settings
from typing import Set
import logging

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def get_authorized_users(self) -> Set[str]:
        """Get cached set of authorized user IDs"""
        try:
            cached_users = await self.redis_client.smembers("authorized_users")
            return set(cached_users) if cached_users else set()
        except Exception as e:
            logger.error(f"Error getting authorized users from cache: {e}")
            return set()

    async def set_authorized_users(self, user_ids: Set[str]):
        """Cache the set of authorized user IDs"""
        try:
            # Clear existing set and add new user IDs
            await self.redis_client.delete("authorized_users")
            if user_ids:
                await self.redis_client.sadd("authorized_users", *user_ids)
                await self.redis_client.expire("authorized_users", settings.AUTHORIZED_USERS_CACHE_TTL)
        except Exception as e:
            logger.error(f"Error setting authorized users in cache: {e}")

    async def add_authorized_user(self, user_id: str):
        """Add a single authorized user to the cache"""
        try:
            await self.redis_client.sadd("authorized_users", user_id)
            await self.redis_client.expire("authorized_users", settings.AUTHORIZED_USERS_CACHE_TTL)
        except Exception as e:
            logger.error(f"Error adding authorized user to cache: {e}")

    async def is_user_authorized(self, user_id: str) -> bool:
        """Check if user is in the authorized cache"""
        try:
            return await self.redis_client.sismember("authorized_users", user_id)
        except Exception as e:
            logger.error(f"Error checking user authorization in cache: {e}")
            return False

    async def close(self):
        await self.redis_client.close()


cache_service = CacheService() 