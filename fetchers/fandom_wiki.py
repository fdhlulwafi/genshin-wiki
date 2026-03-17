"""Fetcher for Genshin Impact Fandom Wiki via MediaWiki API."""

import logging
import re

from tqdm import tqdm

from config import FANDOM_WIKI_API, LORE_CATEGORIES
from fetchers.base import BaseFetcher

logger = logging.getLogger(__name__)


def clean_wikitext(text: str) -> str:
    """Convert wikitext to clean plain text."""
    # Remove nested templates (up to 3 levels deep)
    for _ in range(3):
        text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    # Remove file/image/category links
    text = re.sub(r'\[\[File:[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[Category:[^\]]*\]\]', '', text)
    # Convert wiki links [[Page|text]] to just text
    text = re.sub(r'\[\[[^|\]]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # Remove ref tags and contents
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean headers (== Title == -> Title)
    text = re.sub(r'={2,}\s*([^=]+?)\s*={2,}', r'\n\1\n', text)
    # Remove bold/italic markup
    text = re.sub(r"'{2,}", '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


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

    async def get_page_content(self, title: str) -> dict | None:
        """Get page content via action=parse (wikitext), cleaned to plain text."""
        params = {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
        }
        data = await self.get("", params=params)
        if not data or "parse" not in data:
            return None

        wikitext = data["parse"].get("wikitext", {}).get("*", "")

        # Follow redirects
        if wikitext.startswith("#REDIRECT"):
            redirect_match = re.search(r'\[\[([^\]]+)\]\]', wikitext)
            if redirect_match:
                return await self.get_page_content(redirect_match.group(1))
            return None

        cleaned = clean_wikitext(wikitext)
        if not cleaned or len(cleaned) < 50:
            return None

        return {
            "title": data["parse"].get("title", title),
            "page_id": data["parse"].get("pageid", 0),
            "extract": cleaned,
            "source": "fandom_wiki",
        }

    async def fetch_lore(self, categories: list[str] | None = None, limit: int | None = None) -> list[dict]:
        """Fetch lore pages from wiki categories."""
        categories = categories or LORE_CATEGORIES
        all_titles = set()

        for cat in categories:
            titles = await self.get_category_members(cat)
            all_titles.update(titles)
            logger.info(f"Category '{cat}': {len(titles)} pages")

        # For character pages, also fetch their /Profile subpage
        profile_titles = set()
        for title in all_titles:
            profile_titles.add(f"{title}/Profile")
        all_titles.update(profile_titles)

        if limit:
            all_titles = set(list(all_titles)[:limit])

        results = []
        for title in tqdm(sorted(all_titles), desc="Fetching lore", unit="page"):
            page = await self.get_page_content(title)
            if page:
                results.append(page)
            else:
                logger.debug(f"No content for: {title}")

        logger.info(f"Fetched {len(results)} lore pages")
        return results
