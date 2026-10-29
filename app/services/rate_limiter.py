
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.services.redis_client import redis_client


CHECK_LIMITS_SCRIPT = """
local minute_count = tonumber(redis.call('GET', KEYS[1]) or '0')
local daily_count = tonumber(redis.call('GET', KEYS[2]) or '0')

if minute_count >= tonumber(ARGV[1]) then
    return {0, redis.call('TTL', KEYS[1])}
end

if daily_count >= tonumber(ARGV[2]) then
    return {1, 0}
end

minute_count = redis.call('INCR', KEYS[1])
if minute_count == 1 then
    redis.call('EXPIRE', KEYS[1], 60)
end

daily_count = redis.call('INCR', KEYS[2])
if daily_count == 1 then
    redis.call('EXPIRE', KEYS[2], 172800)
end

return {2, 0}
"""


def enforce_rate_limit(user_id: int | str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = redis_client.eval(
        CHECK_LIMITS_SCRIPT,
        2,
        f"rate_limit:ai:{user_id}",
        f"ai_daily_requests:{user_id}:{today}",
        settings.AI_REQUESTS_PER_MINUTE,
        settings.AI_REQUESTS_PER_DAY,
    )

    status = int(result[0])

    if status == 0:
        retry_after = max(int(result[1]), 1)
        raise HTTPException(
            status_code=429,
            detail="Too many AI requests. Try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )

    if status == 1:
        raise HTTPException(
            status_code=429,
            detail="Daily AI request limit reached.",
        )
