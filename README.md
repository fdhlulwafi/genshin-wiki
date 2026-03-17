# Genshin Impact Knowledge Base API

Pre-fetched Genshin Impact data served via FastAPI. Designed as a data source for an n8n chatbot workflow.

**Live:** `genshin-wiki.fiverse.my`

## How It Works

1. **Fetch** — Collects data from [genshin-db-api](https://github.com/theBowja/genshin-db-api) and [Fandom Wiki API](https://genshin-impact.fandom.com)
2. **Store** — Saves as local JSON files with a keyword search index
3. **Serve** — FastAPI serves the data for n8n or any HTTP client

## Data Sources

| Source | Content | Items |
|--------|---------|-------|
| genshin-db-api | Characters, weapons, artifacts, materials, enemies, domains, foods, achievements | ~3,500+ |
| Fandom Wiki API | Lore, quest summaries, location descriptions | Varies |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch all data (~40 min for full fetch)
python scripts/fetch_all.py

# Or fetch a small subset for testing
python scripts/fetch_all.py --limit 5

# Start the API server
uvicorn server:app --port 8000
```

## API Endpoints

Base URL: `https://genshin-wiki.fiverse.my`

Interactive docs: `https://genshin-wiki.fiverse.my/docs`

### `GET /` — Root

Returns service info.

```bash
curl https://genshin-wiki.fiverse.my/
```

```json
{
  "service": "Genshin Impact Knowledge Base",
  "version": "1.0.0"
}
```

### `GET /health` — Health Check

Used by Docker healthcheck to verify the server is running.

```bash
curl https://genshin-wiki.fiverse.my/health
```

```json
{
  "status": "ok"
}
```

### `GET /categories` — List Categories

Returns all available data categories.

```bash
curl https://genshin-wiki.fiverse.my/categories
```

```json
["achievements", "artifacts", "characters", "domains", "enemies", "foods", "materials", "weapons"]
```

### `GET /categories/{category}` — List Items

Returns all item names within a category.

**Path parameters:**
- `category` — One of: `characters`, `weapons`, `artifacts`, `materials`, `enemies`, `domains`, `foods`, `achievements`, `lore`

```bash
curl https://genshin-wiki.fiverse.my/categories/characters
```

```json
["Albedo", "Amber", "Barbara", "Bennett", ...]
```

### `GET /categories/{category}/{name}` — Get Item Detail

Returns full data for a specific item.

**Path parameters:**
- `category` — The category name
- `name` — The item name (URL-encoded if it contains spaces)

```bash
curl https://genshin-wiki.fiverse.my/categories/characters/Hu%20Tao
```

```json
{
  "id": 10000046,
  "name": "Hu Tao",
  "title": "Fragrance in Thaw",
  "description": "The 77th Director of the Wangsheng Funeral Parlor...",
  "weaponType": "WEAPON_POLE_ARM",
  "element": "Fire",
  "rarity": 5,
  ...
}
```

### `GET /search` — Keyword Search

Searches across all data using keyword matching. Returns results ranked by relevance.

**Query parameters:**
- `q` (required) — Search query
- `limit` (optional, default: 20, max: 100) — Max results to return

```bash
curl "https://genshin-wiki.fiverse.my/search?q=pyro+polearm"
```

```json
{
  "query": "pyro polearm",
  "count": 3,
  "results": [
    {
      "category": "characters",
      "name": "Hu Tao",
      "file": "characters/Hu Tao.json",
      "score": 4
    },
    ...
  ]
}
```

### `GET /lore/{topic}` — Get Lore

Returns lore content fetched from Fandom Wiki.

**Path parameters:**
- `topic` — The lore topic name (URL-encoded if it contains spaces)

```bash
curl https://genshin-wiki.fiverse.my/lore/Mondstadt
```

```json
{
  "title": "Mondstadt",
  "page_id": 1234,
  "extract": "Mondstadt is the city of freedom...",
  "source": "fandom_wiki"
}
```

### `POST /refresh` — Refresh Data

Triggers a background re-fetch of all data from source APIs. Returns immediately.

**Query parameters:**
- `limit` (optional) — Limit items per category (for testing)

```bash
curl -X POST https://genshin-wiki.fiverse.my/refresh
```

```json
{
  "status": "refresh started"
}
```

## Scripts

```bash
python scripts/fetch_all.py              # Fetch everything
python scripts/fetch_all.py --limit 10   # Fetch 10 items per category
python scripts/fetch_all.py --skip-lore  # Skip Fandom Wiki
python scripts/fetch_category.py characters --limit 5  # Fetch one category
python scripts/build_index.py            # Rebuild search index
```

## Docker

```bash
docker build -t genshin-wiki .
docker run -p 8000:8000 -v genshin-data:/app/data genshin-wiki
```

Data persists in the `genshin-data` volume across container restarts.

After first deploy, populate data:
```bash
docker exec <container> python scripts/fetch_all.py
```

## Deployment (Dokploy)

1. Push to GitHub
2. Add as a new service in Dokploy
3. Set build type to **Dockerfile**
4. Add volume mount: name `genshin-data`, path `/app/data`
5. Add domain, set proxy to `http://localhost:80`
6. Deploy, then trigger `POST /refresh` to populate data
