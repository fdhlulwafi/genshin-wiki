"""Configuration for Genshin Impact Knowledge Base."""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INDEX_PATH = DATA_DIR / "_index.json"

# genshin-db-api
GENSHIN_DB_API_BASE = "https://genshin-db-api.vercel.app/api/v5"

CATEGORIES = [
    "characters",
    "weapons",
    "artifacts",
    "materials",
    "enemies",
    "domains",
    "foods",
    "achievements",
]

# Fandom Wiki API
FANDOM_WIKI_API = "https://genshin-impact.fandom.com/api.php"

LORE_CATEGORIES = [
    "Playable_Characters",
    "Regions",
    "Archon_Quests",
]

# Rate limiting
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.5"))  # seconds between requests
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "2.0"))  # exponential backoff multiplier

# API server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "80"))
