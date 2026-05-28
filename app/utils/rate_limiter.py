"""Async token bucket rate limiter."""

import asyncio
import time


class AsyncTokenBucket:
    def __init__(self, max_tokens: int, refill_per_minute: int):
        self.tokens = float(max_tokens)
        self.max_tokens = max_tokens
        self.refill_rate = refill_per_minute / 60.0
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def acquire(self) -> None:
        async with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return
            wait_seconds = (1 - self.tokens) / self.refill_rate
            await asyncio.sleep(wait_seconds)
            self._refill()
            self.tokens -= 1


serpapi_limiter = AsyncTokenBucket(max_tokens=100, refill_per_minute=100)
hf_limiter = AsyncTokenBucket(max_tokens=30, refill_per_minute=30)
