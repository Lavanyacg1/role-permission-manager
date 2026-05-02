import os
import json
import hashlib
import logging
import redis

logger = logging.getLogger(__name__)

CACHE_TTL = 15 * 60

def get_redis_client():
    try:
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None

def make_cache_key(endpoint: str, data: dict) -> str:
    raw = f"{endpoint}:{json.dumps(data, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()

def get_cached(key: str):
    client = get_redis_client()
    if client is None:
        return None
    try:
        value = client.get(key)
        if value:
            logger.info(f"Cache HIT for key: {key[:16]}...")
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        return None

def set_cached(key: str, value: dict):
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, CACHE_TTL, json.dumps(value))
        logger.info(f"Cache SET for key: {key[:16]}...")
    except Exception as e:
        logger.warning(f"Cache set error: {e}")