import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

from config import EDHREC_POPULARITY_PATH, NORMALIZED_CARDS_PATH, ensure_project_dirs

EDHREC_CARD_URL = "https://json.edhrec.com/pages/cards/{slug}.json"


def slugify_card_name(name: str) -> str:
    slug = name.lower()
    slug = slug.split("//", 1)[0].strip()
    slug = re.sub(r"['.,:!?\u2019]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return quote(slug)


def load_card_names(path: Path = NORMALIZED_CARDS_PATH, limit: int | None = None) -> list[str]:
    with path.open("r", encoding="utf-8") as file:
        cards = json.load(file)
    names = [card["name"] for card in cards]
    return names[:limit] if limit else names


def _walk_stats(value) -> tuple[int | None, float | None]:
    deck_count = None
    synergy = None

    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if lowered in {"num_decks", "deck_count", "deckcount", "total_decks", "count"} and isinstance(child, int):
                deck_count = max(deck_count or 0, child)
            if lowered in {"synergy", "synergy_score"} and isinstance(child, (int, float)):
                synergy = max(synergy or 0, float(child))

            child_count, child_synergy = _walk_stats(child)
            if child_count is not None:
                deck_count = max(deck_count or 0, child_count)
            if child_synergy is not None:
                synergy = max(synergy or 0, child_synergy)

    elif isinstance(value, list):
        for child in value:
            child_count, child_synergy = _walk_stats(child)
            if child_count is not None:
                deck_count = max(deck_count or 0, child_count)
            if child_synergy is not None:
                synergy = max(synergy or 0, child_synergy)

    return deck_count, synergy


def fetch_card_popularity(name: str) -> dict:
    url = EDHREC_CARD_URL.format(slug=slugify_card_name(name))
    response = requests.get(url, timeout=30, headers={"User-Agent": "Magic-Card-Finder/0.1"})

    if response.status_code == 404:
        return {"name": name, "edhrec_url": url, "found": False}

    response.raise_for_status()
    payload = response.json()
    deck_count, synergy = _walk_stats(payload)

    return {
        "name": name,
        "edhrec_url": url,
        "found": True,
        "deck_count": deck_count or 0,
        "max_synergy": synergy,
    }


def fetch_popularity_for_cards(names: list[str], delay_seconds: float = 0.25) -> list[dict]:
    popularity = []
    for index, name in enumerate(names, start=1):
        print(f"[{index}/{len(names)}] EDHREC {name}")
        popularity.append(fetch_card_popularity(name))
        time.sleep(delay_seconds)
    return popularity


def save_popularity(records: list[dict], path: Path = EDHREC_POPULARITY_PATH) -> None:
    ensure_project_dirs()
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


if __name__ == "__main__":
    names = load_card_names(limit=100)
    records = fetch_popularity_for_cards(names)
    save_popularity(records)
    print(f"Saved EDHREC popularity for {len(records)} cards")
