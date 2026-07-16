from __future__ import annotations

try:
    import redis
except ImportError:  # pragma: no cover - production dependencies include redis
    redis = None  # type: ignore[assignment]


class DistributedRateLimiter:
    def __init__(self, url: str) -> None:
        if redis is None:
            raise RuntimeError("redis dependency is required for distributed rate limiting")
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_seconds)
        return current <= limit

    def close(self) -> None:
        self.client.close()
