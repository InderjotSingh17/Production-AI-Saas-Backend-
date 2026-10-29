import hashlib
from redis.exceptions import RedisError
from app.services.redis_client import redis_client
CACHE_TTL_SECONDS = 300

def _cache_key(prompt: str) -> str:
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"ai_response_cache:{prompt_hash}"


def get_cached_response(prompt: str) -> str | None:
    try:
        return redis_client.get(_cache_key(prompt))
    except RedisError:
        return None


def cache_response(prompt: str, response: str) -> None:
    try:
        redis_client.setex(
            _cache_key(prompt),
            CACHE_TTL_SECONDS,
            response,
        )
    except RedisError:
        pass
