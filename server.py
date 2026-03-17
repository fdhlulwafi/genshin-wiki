"""FastAPI server for Genshin Impact Knowledge Base."""

import time

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

from config import CATEGORIES
from storage import JsonStore

app = FastAPI(title="Genshin Impact Knowledge Base", version="1.0.0")
store = JsonStore()

# Refresh state
refresh_state = {
    "running": False,
    "started_at": None,
    "completed_at": None,
    "current_category": None,
    "error": None,
}


@app.get("/")
async def root():
    return {"service": "Genshin Impact Knowledge Base", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/categories")
async def list_categories():
    """List all available categories."""
    return store.list_categories()


@app.get("/categories/{category}")
async def list_items(category: str):
    """List all items in a category."""
    items = store.list_items(category)
    if not items:
        raise HTTPException(404, f"Category '{category}' not found or empty")
    return items


@app.get("/categories/{category}/{name}")
async def get_item(category: str, name: str):
    """Get full data for a specific item."""
    item = store.load_item(category, name)
    if not item:
        raise HTTPException(404, f"Item '{name}' not found in '{category}'")
    return item


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    full: bool = Query(False, description="Include full item data in results"),
):
    """Search across all data by keyword. Use full=true to include complete item data."""
    results = store.search(q, limit=limit)
    if full:
        for result in results:
            data = store.load_item(result["category"], result["name"])
            if data:
                result["data"] = data
    return {"query": q, "count": len(results), "results": results}


@app.get("/lore/{topic}")
async def get_lore(topic: str):
    """Get lore content for a topic."""
    item = store.load_item("lore", topic)
    if not item:
        raise HTTPException(404, f"Lore topic '{topic}' not found")
    return item


async def _run_fetch(category: str | None, limit: int | None):
    """Background task to re-fetch data."""
    refresh_state["running"] = True
    refresh_state["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    refresh_state["completed_at"] = None
    refresh_state["error"] = None

    try:
        if category == "lore":
            from fetchers import FandomWikiFetcher
            async with FandomWikiFetcher() as fetcher:
                items = await fetcher.fetch_lore(limit=limit)
                store.save_category("lore", items, name_key="title")
        elif category:
            from fetchers import GenshinDBFetcher
            async with GenshinDBFetcher() as fetcher:
                items = await fetcher.fetch_category(category, limit=limit)
                store.save_category(category, items)
        else:
            from scripts.fetch_all import main as fetch_main
            await fetch_main(limit=limit)

        # Rebuild index
        store.build_index()
        refresh_state["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    except Exception as e:
        refresh_state["error"] = str(e)
    finally:
        refresh_state["running"] = False


@app.post("/refresh")
async def refresh(background_tasks: BackgroundTasks, category: str | None = None, limit: int | None = None):
    """Trigger a background re-fetch. Optionally specify a single category."""
    if refresh_state["running"]:
        return {"status": "already running", "started_at": refresh_state["started_at"]}
    background_tasks.add_task(_run_fetch, category, limit)
    target = category or "all"
    return {"status": "refresh started", "target": target}


@app.get("/refresh/status")
async def refresh_status():
    """Check the status of data fetching."""
    categories = store.list_categories()
    item_counts = {}
    for cat in categories:
        item_counts[cat] = len(store.list_items(cat))

    return {
        "running": refresh_state["running"],
        "started_at": refresh_state["started_at"],
        "completed_at": refresh_state["completed_at"],
        "error": refresh_state["error"],
        "categories_fetched": len(categories),
        "item_counts": item_counts,
        "total_items": sum(item_counts.values()),
    }
