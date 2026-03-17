"""Fetch all Genshin Impact data from all sources."""

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


async def main(limit: int | None = None, skip_lore: bool = False):
    store = JsonStore()

    # Fetch from genshin-db-api (save each category immediately)
    async with GenshinDBFetcher() as fetcher:
        for category in CATEGORIES:
            logger.info(f"Starting category: {category}")
            items = await fetcher.fetch_category(category, limit=limit)
            store.save_category(category, items)
            logger.info(f"Saved {len(items)} {category}")

    # Fetch lore from Fandom Wiki
    if not skip_lore:
        async with FandomWikiFetcher() as fetcher:
            lore = await fetcher.fetch_lore(limit=limit)
            store.save_category("lore", lore, name_key="title")
            logger.info(f"Saved {len(lore)} lore pages")

    # Build search index
    index = store.build_index()
    logger.info(f"Index built with {len(index)} keywords")
    logger.info("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch all Genshin Impact data")
    parser.add_argument("--limit", type=int, default=None, help="Limit items per category (for testing)")
    parser.add_argument("--skip-lore", action="store_true", help="Skip Fandom Wiki lore fetch")
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, skip_lore=args.skip_lore))
