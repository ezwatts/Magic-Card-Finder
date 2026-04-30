import json
from pathlib import Path

import requests

from config import RAW_CARDS_PATH, SCRYFALL_BULK_TYPE, SCRYFALL_BULK_URL, ensure_project_dirs


def get_bulk_download_uri(bulk_type: str = SCRYFALL_BULK_TYPE) -> str:
    response = requests.get(SCRYFALL_BULK_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()

    for item in payload.get("data", []):
        if item.get("type") == bulk_type:
            return item["download_uri"]

    available = ", ".join(item.get("type", "?") for item in payload.get("data", []))
    raise ValueError(f"Could not find Scryfall bulk type {bulk_type!r}. Available: {available}")


def fetch_bulk_cards(bulk_type: str = SCRYFALL_BULK_TYPE) -> list[dict]:
    download_uri = get_bulk_download_uri(bulk_type)
    response = requests.get(download_uri, timeout=120)
    response.raise_for_status()
    return response.json()


def save_raw(cards: list[dict], path: Path = RAW_CARDS_PATH) -> None:
    ensure_project_dirs()
    with path.open("w", encoding="utf-8") as file:
        json.dump(cards, file)


if __name__ == "__main__":
    cards = fetch_bulk_cards()
    save_raw(cards)
    print(f"Fetched {len(cards)} cards")
