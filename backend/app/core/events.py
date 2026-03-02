"""Redis pub/sub broadcaster — decouples Celery workers from WebSocket connections."""
import json
from collections.abc import AsyncGenerator
from typing import Any

from app.core.redis_client import get_redis

ACTIVITY_CHANNEL = "polsia:activity"


async def publish_activity(event: dict[str, Any]) -> None:
    redis = await get_redis()
    await redis.publish(ACTIVITY_CHANNEL, json.dumps(event))


async def subscribe_activity() -> AsyncGenerator[dict[str, Any], None]:
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(ACTIVITY_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(ACTIVITY_CHANNEL)
        await pubsub.aclose()
