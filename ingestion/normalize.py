import json
import re
from pathlib import Path

from config import COMMANDER_LEGALITY, NORMALIZED_CARDS_PATH, RAW_CARDS_PATH, ensure_project_dirs

MANA_VALUE_RE = re.compile(r"\{([0-9]+|[WUBRGXCS])(?:/[WUBRGPC2])?\}")


def load_raw_cards(path: Path = RAW_CARDS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def combined_oracle_text(card: dict) -> str:
    if card.get("oracle_text"):
        return card["oracle_text"]

    faces = card.get("card_faces") or []
    return "\n".join(face.get("oracle_text", "") for face in faces).strip()


def normalize_card(card: dict) -> dict | None:
    legalities = card.get("legalities", {})
    if legalities.get(COMMANDER_LEGALITY) not in {"legal", "restricted"}:
        return None

    if card.get("digital") or card.get("layout") in {"art_series", "token", "emblem"}:
        return None

    oracle_text = combined_oracle_text(card)
    if not oracle_text:
        return None

    return {
        "id": card.get("id"),
        "oracle_id": card.get("oracle_id"),
        "name": card.get("name"),
        "mana_cost": card.get("mana_cost") or "",
        "cmc": float(card.get("cmc") or 0),
        "type_line": card.get("type_line") or "",
        "oracle_text": oracle_text,
        "colors": card.get("colors") or [],
        "color_identity": card.get("color_identity") or [],
        "keywords": card.get("keywords") or [],
        "rarity": card.get("rarity"),
        "set": card.get("set"),
        "collector_number": card.get("collector_number"),
        "edhrec_rank": card.get("edhrec_rank"),
        "prices": card.get("prices") or {},
        "scryfall_uri": card.get("scryfall_uri"),
    }


def normalize_cards(cards: list[dict]) -> list[dict]:
    normalized = [normalize_card(card) for card in cards]
    deduped: dict[str, dict] = {}

    for card in normalized:
        if not card:
            continue
        key = card.get("oracle_id") or card["name"]
        existing = deduped.get(key)
        if existing is None or (card.get("edhrec_rank") or 999999) < (existing.get("edhrec_rank") or 999999):
            deduped[key] = card

    return sorted(deduped.values(), key=lambda item: item["name"])


def save_normalized(cards: list[dict], path: Path = NORMALIZED_CARDS_PATH) -> None:
    ensure_project_dirs()
    with path.open("w", encoding="utf-8") as file:
        json.dump(cards, file, indent=2)


if __name__ == "__main__":
    normalized_cards = normalize_cards(load_raw_cards())
    save_normalized(normalized_cards)
    print(f"Normalized {len(normalized_cards)} commander-legal cards")
