# src/book2anki/core/utils.py
import time
from collections import deque
import asyncio

class AsyncRateLimiter:
    """Shared rate limiter using token bucket algorithm"""
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.timestamps = deque()

    async def wait(self):
        while True:
            now = time.monotonic()
            while self.timestamps and self.timestamps[0] <= now - self.period:
                self.timestamps.popleft()
            if len(self.timestamps) < self.max_calls:
                break
            sleep_time = self.period - (now - self.timestamps[0])
            await asyncio.sleep(sleep_time)
        self.timestamps.append(now)
