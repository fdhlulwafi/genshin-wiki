# Genshin Impact Knowledge Base API

Pre-fetched Genshin Impact data served via FastAPI. Designed as a data source for an n8n chatbot workflow.

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
uvicorn api.server:app --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/categories` | List all categories |
| `GET` | `/categories/{category}` | List items in a category |
| `GET` | `/categories/{category}/{name}` | Get item detail |
| `GET` | `/search?q=...` | Keyword search across all data |
| `GET` | `/lore/{topic}` | Get lore content |
| `POST` | `/refresh` | Trigger background re-fetch |

### Example

```bash
curl http://localhost:8000/search?q=hu+tao
curl http://localhost:8000/categories/characters/Hu%20Tao
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
3. Set build type to Dockerfile
4. Add volume mount: `/app/data`
5. Deploy, then trigger `POST /refresh` to populate data
