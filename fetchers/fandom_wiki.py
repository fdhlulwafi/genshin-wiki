"""Fetcher for Genshin Impact Fandom Wiki via MediaWiki API."""

import logging
import re

from tqdm import tqdm

from config import FANDOM_WIKI_API, LORE_CATEGORIES
from fetchers.base import BaseFetcher

logger = logging.getLogger(__name__)


class FandomWikiFetcher(BaseFetcher):
    def __init__(self):
        super().__init__(FANDOM_WIKI_API)

    async def get_category_members(self, category: str, limit: int = 500) -> list[str]:
        """Get page titles in a wiki category."""
        titles = []
        cmcontinue = None

        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": str(min(limit - len(titles), 50)),
                "cmtype": "page",
                "format": "json",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            data = await self.get("", params=params)
            if not data:
                break

            members = data.get("query", {}).get("categorymembers", [])
            titles.extend(m["title"] for m in members)

            cont = data.get("continue", {}).get("cmcontinue")
            if not cont or len(titles) >= limit:
                break
            cmcontinue = cont

        return titles[:limit]

    async def get_page_extract(self, title: str) -> dict | None:
        """Get plain-text extract of a wiki page."""
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": "true",
            "exsectionformat": "plain",
            "format": "json",
        }
        data = await self.get("", params=params)
        if not data:
            return None

        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return None
            extract = page.get("extract", "")
            # Clean up excessive whitespace
            extract = re.sub(r"\n{3,}", "\n\n", extract)
            return {
                "title": page.get("title", title),
                "page_id": int(page_id),
                "extract": extract,
                "source": "fandom_wiki",
            }
        return None

    async def fetch_lore(self, categories: list[str] | None = None, limit: int | None = None) -> list[dict]:
        """Fetch lore pages from wiki categories."""
        categories = categories or LORE_CATEGORIES
        all_titles = set()

        for cat in categories:
            titles = await self.get_category_members(cat)
            all_titles.update(titles)
            logger.info(f"Category '{cat}': {len(titles)} pages")

        if limit:
            all_titles = set(list(all_titles)[:limit])

        results = []
        for title in tqdm(sorted(all_titles), desc="Fetching lore", unit="page"):
            page = await self.get_page_extract(title)
            if page and page["extract"]:
                results.append(page)
            else:
                logger.warning(f"No content for: {title}")

        return results
