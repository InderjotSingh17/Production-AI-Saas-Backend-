
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.services.redis_client import redis_client


def daily_token_key(user_id: int | str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"ai_daily_tokens:{user_id}:{today}"


def enforce_daily_token_budget(user_id: int | str) -> None:
    used = int(redis_client.get(daily_token_key(user_id)) or 0)

    if used >= settings.AI_DAILY_TOKEN_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Daily AI token budget reached.",
        )


def record_token_usage(user_id: int | str, tokens: int) -> None:
    if tokens <= 0:
        return

    key = daily_token_key(user_id)
    redis_client.incrby(key, tokens)
    redis_client.expire(key, 48 * 60 * 60)
