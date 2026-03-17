"""Fetch a single category of Genshin Impact data."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CATEGORIES
from fetchers import FandomWikiFetcher, GenshinDBFetcher
from storage import JsonStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main(category: str, limit: int | None = None):
    store = JsonStore()

    if category == "lore":
        async with FandomWikiFetcher() as fetcher:
            items = await fetcher.fetch_lore(limit=limit)
            store.save_category("lore", items, name_key="title")
    elif category in CATEGORIES:
        async with GenshinDBFetcher() as fetcher:
            items = await fetcher.fetch_category(category, limit=limit)
            store.save_category(category, items)
    else:
        logger.error(f"Unknown category: {category}. Valid: {CATEGORIES + ['lore']}")
        return

    logger.info(f"Saved {len(items)} {category}")

    # Rebuild index
    index = store.build_index()
    logger.info(f"Index rebuilt with {len(index)} keywords")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a single category")
    parser.add_argument("category", choices=CATEGORIES + ["lore"])
    parser.add_argument("--limit", type=int, default=None, help="Limit items (for testing)")
    args = parser.parse_args()
    asyncio.run(main(args.category, limit=args.limit))
