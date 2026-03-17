"""JSON file storage and search index."""

import json
import logging
import re
from pathlib import Path

from config import DATA_DIR, INDEX_PATH

logger = logging.getLogger(__name__)


class JsonStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_item(self, category: str, name: str, data: dict) -> Path:
        """Save a single item as JSON."""
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
        category_dir = self.data_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        path = category_dir / f"{safe_name}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def save_category(self, category: str, items: list[dict], name_key: str = "name") -> list[Path]:
        """Save all items in a category. Also saves _all.json aggregate."""
        paths = []
        for item in items:
            name = item.get(name_key, item.get("id", "unknown"))
            path = self.save_item(category, str(name), item)
            paths.append(path)

        # Save aggregate
        agg_path = self.data_dir / category / "_all.json"
        agg_path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        return paths

    def load_item(self, category: str, name: str) -> dict | None:
        """Load a single item."""
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)
        path = self.data_dir / category / f"{safe_name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_category(self, category: str) -> list[dict]:
        """Load all items from _all.json."""
        agg_path = self.data_dir / category / "_all.json"
        if not agg_path.exists():
            return []
        return json.loads(agg_path.read_text(encoding="utf-8"))

    def list_categories(self) -> list[str]:
        """List all categories that have data."""
        return [
            d.name for d in sorted(self.data_dir.iterdir())
            if d.is_dir() and (d / "_all.json").exists()
        ]

    def list_items(self, category: str) -> list[str]:
        """List item names in a category."""
        category_dir = self.data_dir / category
        if not category_dir.exists():
            return []
        return [
            f.stem for f in sorted(category_dir.iterdir())
            if f.suffix == ".json" and f.stem != "_all"
        ]

    def build_index(self) -> dict:
        """Build a keyword-to-path search index across all data."""
        index: dict[str, list[dict]] = {}

        for category_dir in sorted(self.data_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            agg_path = category_dir / "_all.json"
            if not agg_path.exists():
                continue

            items = json.loads(agg_path.read_text(encoding="utf-8"))
            for item in items:
                name = str(item.get("name", item.get("id", "")))
                keywords = self._extract_keywords(item)
                safe = re.sub(r'[<>:"/\\|?*]', '_', name)
                entry = {
                    "category": category,
                    "name": name,
                    "file": f"{category}/{safe}.json",
                }
                for kw in keywords:
                    kw_lower = kw.lower()
                    if kw_lower not in index:
                        index[kw_lower] = []
                    # Avoid duplicates
                    if not any(e["name"] == name and e["category"] == category for e in index[kw_lower]):
                        index[kw_lower].append(entry)

        INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Built index with {len(index)} keywords")
        return index

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search the index for matching items."""
        if not INDEX_PATH.exists():
            return []
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

        terms = query.lower().split()
        scores: dict[str, dict] = {}  # key: "category/name"

        for term in terms:
            for kw, entries in index.items():
                if term in kw:
                    for entry in entries:
                        key = f"{entry['category']}/{entry['name']}"
                        if key not in scores:
                            scores[key] = {**entry, "score": 0}
                        # Exact match scores higher
                        scores[key]["score"] += 2 if term == kw else 1

        results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _extract_keywords(self, item: dict) -> set[str]:
        """Extract searchable keywords from an item."""
        keywords = set()
        # Direct fields
        for field in ["name", "title", "description", "weaponType", "element", "substat", "region"]:
            val = item.get(field)
            if isinstance(val, str) and val:
                keywords.add(val)
                # Also add individual words for multi-word names
                for word in val.split():
                    if len(word) > 1:
                        keywords.add(word)
        # Rarity
        rarity = item.get("rarity") or item.get("stars")
        if rarity:
            keywords.add(f"{rarity}star")
        return keywords
