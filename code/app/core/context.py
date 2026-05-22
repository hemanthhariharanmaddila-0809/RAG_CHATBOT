import os
import json
import time
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ContextManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis connection initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis = None

    async def get_context(self, user_id: str, platform: str) -> dict:
        if not self.redis:
            return {"history": [], "last_updated": time.time()}
            
        key = f"ctx:{platform}:{user_id}"
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return {"history": [], "last_updated": time.time()}
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return {"history": [], "last_updated": time.time()}

    async def update_context(self, user_id: str, platform: str, user_msg: str, bot_reply: str) -> None:
        if not self.redis:
            return
            
        key = f"ctx:{platform}:{user_id}"
        try:
            context = await self.get_context(user_id, platform)
            history = context.get("history", [])
            
            history.append({"user": user_msg, "bot": bot_reply})
            
            # Keep last 10 exchanges maximum
            if len(history) > 10:
                history = history[-10:]
                
            new_context = {
                "history": history,
                "last_updated": time.time()
            }
            
            await self.redis.setex(key, 3600, json.dumps(new_context))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def clear_context(self, user_id: str, platform: str) -> None:
        if not self.redis:
            return
            
        key = f"ctx:{platform}:{user_id}"
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
