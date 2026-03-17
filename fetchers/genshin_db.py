"""Fetcher for genshin-db-api (https://genshin-db-api.vercel.app)."""

import logging

from tqdm import tqdm

from config import CATEGORIES, GENSHIN_DB_API_BASE
from fetchers.base import BaseFetcher

logger = logging.getLogger(__name__)


class GenshinDBFetcher(BaseFetcher):
    def __init__(self):
        super().__init__(GENSHIN_DB_API_BASE)

    async def list_names(self, category: str) -> list[str]:
        """Get all item names for a category."""
        data = await self.get(category, params={"query": "names", "matchCategories": "true"})
        if not data or not isinstance(data, list):
            logger.error(f"Failed to get names for {category}")
            return []
        return data

    async def get_item(self, category: str, name: str) -> dict | None:
        """Get full data for a single item."""
        data = await self.get(category, params={"query": name})
        if not data or not isinstance(data, dict):
            return None
        return data

    async def fetch_category(self, category: str, limit: int | None = None) -> list[dict]:
        """Fetch all items in a category. Returns list of item data dicts."""
        names = await self.list_names(category)
        if limit:
            names = names[:limit]

        items = []
        desc = f"Fetching {category}"
        for name in tqdm(names, desc=desc, unit="item"):
            item = await self.get_item(category, name)
            if item:
                items.append(item)
            else:
                logger.warning(f"Failed to fetch {category}/{name}")
        return items

    async def fetch_all(self, categories: list[str] | None = None, limit: int | None = None) -> dict[str, list[dict]]:
        """Fetch all categories. Returns {category: [items]}."""
        categories = categories or CATEGORIES
        result = {}
        for category in categories:
            logger.info(f"Starting category: {category}")
            result[category] = await self.fetch_category(category, limit=limit)
            logger.info(f"Completed {category}: {len(result[category])} items")
        return result
