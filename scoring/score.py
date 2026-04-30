import json
import math
import re
from pathlib import Path

from config import EDHREC_POPULARITY_PATH, SCORED_CARDS_PATH, TAGGED_CARDS_PATH, ensure_project_dirs
from tagging.tag_rules import TAG_SYNERGIES

TAG_POWER_WEIGHTS = {
    "activated_abilities": 5,
    "card_draw": 12,
    "mana_ramp": 12,
    "removal": 10,
    "tutor": 14,
    "protection": 8,
    "recursion": 9,
    "tokens": 7,
    "graveyard": 7,
    "sacrifice": 7,
    "aristocrats": 7,
    "doubling": 10,
    "stax": 11,
    "spellslinger": 6,
    "counters": 5,
    "blink": 6,
    "landfall": 6,
    "discard": 4,
    "lifegain": 3,
    "mill": 3,
    "voltron": 4,
    "artifact": 2,
    "attack_triggers": 6,
    "clues": 5,
    "coin_flip": 1,
    "crimes": 4,
    "creature": 1,
    "cycling": 4,
    "dice_rolling": 1,
    "dungeon": 3,
    "enchantment": 2,
    "energy": 5,
    "etb": 7,
    "exile": 5,
    "extra_combat": 12,
    "fight": 5,
    "flash": 5,
    "historic": 4,
    "impulse_draw": 8,
    "land": 2,
    "land_animation": 4,
    "legendary": 2,
    "monarch": 8,
    "ninjutsu": 5,
    "plus_one_counters": 5,
    "minus_one_counters": 4,
    "planeswalker": 3,
    "politics": 2,
    "power_matters": 3,
    "proliferate": 7,
    "reanimator": 10,
    "saga": 3,
    "snow": 2,
    "tap_untap": 6,
    "toughness_matters": 3,
    "treasures": 8,
    "topdeck": 6,
    "unblockable": 4,
    "vehicle": 3,
}

KEYWORD_WEIGHTS = {
    "Flying": 1,
    "Haste": 2,
    "Hexproof": 4,
    "Indestructible": 5,
    "Lifelink": 2,
    "Menace": 1,
    "Trample": 1,
    "Vigilance": 1,
    "Ward": 2,
}

PREMIUM_TAGS = {
    "card_draw",
    "mana_ramp",
    "removal",
    "tutor",
    "recursion",
    "protection",
    "stax",
    "doubling",
    "extra_combat",
    "reanimator",
    "monarch",
    "impulse_draw",
}

CARD_TYPE_COST_TOLERANCE = {
    "Instant": 0.15,
    "Sorcery": 0.05,
    "Artifact": 0.35,
    "Creature": 0.45,
    "Enchantment": 0.45,
    "Planeswalker": 0.3,
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def popularity_by_name(records: list[dict]) -> dict[str, dict]:
    return {record["name"]: record for record in records}


def synergy_score(tags: list[str]) -> float:
    tag_set = set(tags)
    score = 0

    for tag in tag_set:
        related = TAG_SYNERGIES.get(tag, set())
        score += len(tag_set & related) * 6

    return min(score, 30)


def card_type_tolerance(type_line: str) -> float:
    for card_type, tolerance in CARD_TYPE_COST_TOLERANCE.items():
        if card_type in type_line:
            return tolerance
    return 0


def effect_score(card: dict) -> float:
    tags = card.get("tags", [])
    text = card.get("oracle_text", "").lower()
    score = sum(TAG_POWER_WEIGHTS.get(tag, 0) for tag in tags)

    if re.search(r"draw (two|three|four|x) cards?", text):
        score += 7
    if re.search(r"each opponent|each player|all opponents", text):
        score += 5
    if re.search(r"without paying (its|their) mana cost", text):
        score += 10
    if re.search(r"you may cast|play .* from your graveyard", text):
        score += 5
    if re.search(r"at the beginning of .* upkeep|whenever .* cast|whenever .* enters", text):
        score += 4
    if re.search(r"activate only once each turn|this ability triggers only once", text):
        score -= 5
    if re.search(r"as an additional cost|sacrifice .*:", text):
        score -= 3

    return max(0, score)


def cost_adjusted_value(card: dict) -> float:
    cmc = float(card.get("cmc") or 0)
    raw_effect = effect_score(card)
    tolerance = card_type_tolerance(card.get("type_line", ""))

    if cmc <= 0:
        return min(25, raw_effect * 1.25)

    adjusted_cost = max(1, cmc - tolerance)
    return round(raw_effect / (adjusted_cost ** 0.85), 2)


def mana_efficiency_score(card: dict) -> float:
    cmc = float(card.get("cmc") or 0)
    tags = set(card.get("tags", []))
    value = cost_adjusted_value(card)
    premium_count = len(tags & PREMIUM_TAGS)

    if cmc <= 0:
        base = 8
    elif cmc <= 2:
        base = 12
    elif cmc <= 4:
        base = 7
    elif cmc <= 6:
        base = 0
    else:
        base = -8

    if value >= 18:
        base += 10
    elif value >= 12:
        base += 5
    elif value < 6 and cmc >= 4:
        base -= 10
    elif value < 4:
        base -= 6

    if premium_count == 0 and cmc >= 5:
        base -= 7

    return max(-20, min(base, 25))


def baseline_power_score(card: dict) -> float:
    tags = card.get("tags", [])
    tag_score = min(45, effect_score(card) * 0.75)
    keyword_score = sum(KEYWORD_WEIGHTS.get(keyword, 0) for keyword in card.get("keywords", []))
    efficiency = mana_efficiency_score(card)
    value = cost_adjusted_value(card)
    rank_bonus = 0

    edhrec_rank = card.get("edhrec_rank")
    if isinstance(edhrec_rank, int) and edhrec_rank > 0:
        rank_bonus = max(0, 12 - math.log10(edhrec_rank) * 4)

    synergy_cap = 22 if value >= 10 else 10
    synergy = min(synergy_score(tags), synergy_cap)
    score = 22 + tag_score + keyword_score + synergy + efficiency + rank_bonus
    return round(max(0, min(score, 100)), 2)


def opportunity_score(power_score: float, deck_count: int | None) -> float:
    popularity_penalty = math.log10((deck_count or 0) + 1) * 10
    return round(max(0, power_score - popularity_penalty), 2)


def score_cards(cards: list[dict], popularity: list[dict] | None = None) -> list[dict]:
    popularity_lookup = popularity_by_name(popularity or [])
    scored = []

    for card in cards:
        popularity_record = popularity_lookup.get(card["name"], {})
        deck_count = popularity_record.get("deck_count")
        power = baseline_power_score(card)

        enriched = dict(card)
        enriched["edhrec_deck_count"] = deck_count
        enriched["edhrec_found"] = popularity_record.get("found")
        enriched["effect_score"] = round(effect_score(card), 2)
        enriched["cost_adjusted_value"] = cost_adjusted_value(card)
        enriched["efficiency_score"] = mana_efficiency_score(card)
        enriched["power_score"] = power
        enriched["opportunity_score"] = opportunity_score(power, deck_count)
        scored.append(enriched)

    return sorted(scored, key=lambda item: (item["opportunity_score"], item["power_score"]), reverse=True)


def save_scored(cards: list[dict], path: Path = SCORED_CARDS_PATH) -> None:
    ensure_project_dirs()
    with path.open("w", encoding="utf-8") as file:
        json.dump(cards, file, indent=2)


if __name__ == "__main__":
    tagged_cards = load_json(TAGGED_CARDS_PATH, [])
    popularity_records = load_json(EDHREC_POPULARITY_PATH, [])
    scored_cards = score_cards(tagged_cards, popularity_records)
    save_scored(scored_cards)
    print(f"Scored {len(scored_cards)} cards")
