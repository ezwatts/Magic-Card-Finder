import json
from pathlib import Path

from config import NORMALIZED_CARDS_PATH, TAGGED_CARDS_PATH, ensure_project_dirs
from tagging.tag_rules import tag_card


def load_cards(path: Path = NORMALIZED_CARDS_PATH):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def tag_cards(cards):
    tagged = []

    for card in cards:
        oracle = card.get("oracle_text", "")
        if not oracle:
            continue

        tags = tag_card(oracle, card.get("type_line", ""), card.get("keywords", []))
        tagged_card = dict(card)
        tagged_card["tags"] = tags

        tagged.append(tagged_card)

    return tagged


def save_tagged(cards, path: Path = TAGGED_CARDS_PATH):
    ensure_project_dirs()
    with path.open("w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)


if __name__ == "__main__":
    cards = load_cards()
    tagged = tag_cards(cards)
    save_tagged(tagged)

    print(f"Tagged {len(tagged)} cards")
