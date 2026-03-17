"""Rebuild the search index from existing data."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage import JsonStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    store = JsonStore()
    index = store.build_index()
    logger.info(f"Index built with {len(index)} keywords")
