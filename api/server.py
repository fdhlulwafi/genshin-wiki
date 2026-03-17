"""FastAPI server for Genshin Impact Knowledge Base."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

from config import API_HOST, API_PORT, CATEGORIES
from storage import JsonStore

app = FastAPI(title="Genshin Impact Knowledge Base", version="1.0.0")
store = JsonStore()


@app.get("/")
async def root():
    return {"service": "Genshin Impact Knowledge Base", "version": "1.0.0"}


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
async def search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)):
    """Search across all data by keyword."""
    results = store.search(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@app.get("/lore/{topic}")
async def get_lore(topic: str):
    """Get lore content for a topic."""
    item = store.load_item("lore", topic)
    if not item:
        raise HTTPException(404, f"Lore topic '{topic}' not found")
    return item


async def _run_fetch(limit: int | None):
    """Background task to re-fetch data."""
    from scripts.fetch_all import main as fetch_main
    await fetch_main(limit=limit)


@app.post("/refresh")
async def refresh(background_tasks: BackgroundTasks, limit: int | None = None):
    """Trigger a background re-fetch of all data."""
    background_tasks.add_task(_run_fetch, limit)
    return {"status": "refresh started"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
