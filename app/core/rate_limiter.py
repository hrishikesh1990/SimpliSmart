from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
import time
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict


class RateLimiter:

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_task = None

    async def cleanup(self):
        while True:
            current_time = datetime.utcnow()
            for ip, timestamps in list(self.requests.items()):
                self.requests[ip] = [
                    ts for ts in timestamps
                    if current_time - ts < timedelta(minutes=1)
                ]
                if not self.requests[ip]:
                    del self.requests[ip]
            await asyncio.sleep(60)

    async def start_cleanup(self):
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self.cleanup())

    async def check_rate_limit(self, request: Request):
        if not self._cleanup_task:
            await self.start_cleanup()

        client_ip = request.client.host
        current_time = datetime.utcnow()

        # Remove timestamps older than 1 minute
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if current_time - ts < timedelta(minutes=1)
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Rate limit exceeded")

        self.requests[client_ip].append(current_time)


rate_limiter = RateLimiter()
