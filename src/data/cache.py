"""Redis 缓存操作。"""
import redis

from config.settings import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """获取 Redis 客户端（单例）。"""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True, protocol=2)
    return _client


def cache_get(key: str) -> str | None:
    """读取缓存。"""
    return get_redis().get(key)


def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    """写入缓存，默认 1 小时过期。"""
    return get_redis().set(key, value, ex=ttl)
