"""Base fetcher with retry and rate limiting."""

import asyncio
import logging

import httpx

from config import MAX_RETRIES, REQUEST_DELAY, RETRY_BACKOFF

logger = logging.getLogger(__name__)


class BaseFetcher:
    def __init__(self, base_url: str, delay: float = REQUEST_DELAY):
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *exc):
        if self.client:
            await self.client.aclose()

    async def get(self, path: str, params: dict | None = None) -> dict | list | None:
        """GET with retry + exponential backoff."""
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        for attempt in range(MAX_RETRIES):
            try:
                await asyncio.sleep(self.delay)
                resp = await self.client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                wait = RETRY_BACKOFF ** attempt
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {url}: {e}. Retrying in {wait}s")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"All retries exhausted for {url}")
                    return None
