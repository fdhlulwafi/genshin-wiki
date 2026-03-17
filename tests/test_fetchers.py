"""Tests for fetchers and storage."""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers import GenshinDBFetcher, FandomWikiFetcher
from storage import JsonStore


@pytest.fixture
def tmp_store(tmp_path):
    return JsonStore(data_dir=tmp_path / "data")


@pytest.mark.asyncio
async def test_genshin_db_list_names():
    async with GenshinDBFetcher() as fetcher:
        names = await fetcher.list_names("characters")
    assert len(names) > 0
    assert "Hu Tao" in names


@pytest.mark.asyncio
async def test_genshin_db_get_item():
    async with GenshinDBFetcher() as fetcher:
        item = await fetcher.get_item("characters", "Hu Tao")
    assert item is not None
    assert item["name"] == "Hu Tao"
    assert "element" in item or "weaponType" in item


@pytest.mark.asyncio
async def test_genshin_db_fetch_category_with_limit():
    async with GenshinDBFetcher() as fetcher:
        items = await fetcher.fetch_category("characters", limit=3)
    assert len(items) == 3
    assert all("name" in item for item in items)


def test_store_save_and_load(tmp_store):
    data = {"name": "Hu Tao", "element": "Pyro", "rarity": 5}
    tmp_store.save_item("characters", "Hu Tao", data)

    loaded = tmp_store.load_item("characters", "Hu Tao")
    assert loaded == data


def test_store_save_category(tmp_store):
    items = [
        {"name": "Hu Tao", "element": "Pyro"},
        {"name": "Ganyu", "element": "Cryo"},
    ]
    tmp_store.save_category("characters", items)

    names = tmp_store.list_items("characters")
    assert "Hu Tao" in names
    assert "Ganyu" in names

    all_items = tmp_store.load_category("characters")
    assert len(all_items) == 2


def test_store_build_index_and_search(tmp_store):
    items = [
        {"name": "Hu Tao", "element": "Pyro", "weaponType": "Polearm", "rarity": 5},
        {"name": "Ganyu", "element": "Cryo", "weaponType": "Bow", "rarity": 5},
    ]
    tmp_store.save_category("characters", items)
    tmp_store.build_index()

    results = tmp_store.search("Hu Tao")
    assert len(results) > 0
    assert results[0]["name"] == "Hu Tao"

    results = tmp_store.search("Pyro")
    assert any(r["name"] == "Hu Tao" for r in results)


@pytest.mark.asyncio
async def test_fandom_wiki_category_members():
    async with FandomWikiFetcher() as fetcher:
        titles = await fetcher.get_category_members("Playable_Characters", limit=5)
    assert len(titles) > 0
