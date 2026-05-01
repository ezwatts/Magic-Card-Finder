import re
from difflib import get_close_matches

from tagging.tag_rules import TAG_SYNERGIES

STRUCTURAL_TAGS = {
    "artifact",
    "battle",
    "creature",
    "enchantment",
    "instant",
    "land",
    "legendary",
    "planeswalker",
    "saga",
    "sorcery",
    "vehicle",
}


def normalize_name(name: str) -> str:
    return " ".join(name.casefold().split())


def find_card(cards: list[dict], name: str) -> dict:
    target = normalize_name(name)
    by_name = {normalize_name(card["name"]): card for card in cards}

    if target in by_name:
        return by_name[target]

    contains_matches = [
        card
        for card in cards
        if target in normalize_name(card["name"]) or normalize_name(card["name"]) in target
    ]
    if contains_matches:
        return sorted(
            contains_matches,
            key=lambda card: (
                "Legendary" not in card.get("type_line", ""),
                "Creature" not in card.get("type_line", "") and "Planeswalker" not in card.get("type_line", ""),
                len(card["name"]),
            ),
        )[0]

    close = get_close_matches(target, by_name.keys(), n=1, cutoff=0.65)
    if close:
        return by_name[close[0]]

    raise ValueError(f"Could not find commander named {name!r}")


def is_color_legal(card: dict, commander: dict) -> bool:
    commander_identity = set(commander.get("color_identity") or [])
    card_identity = set(card.get("color_identity") or [])
    return card_identity <= commander_identity


def normalize_tribe(tribe: str | None) -> str | None:
    if not tribe:
        return None

    normalized = tribe.strip().casefold()
    if normalized.endswith("ies"):
        return f"{normalized[:-3]}y"
    if normalized.endswith("s") and not normalized.endswith("ss"):
        return normalized[:-1]
    return normalized


def tribe_forms(tribe: str) -> set[str]:
    forms = {tribe}
    if tribe.endswith("y"):
        forms.add(f"{tribe[:-1]}ies")
    else:
        forms.add(f"{tribe}s")
    return forms


def contains_tribe(value: str, tribe: str) -> bool:
    forms = "|".join(re.escape(form) for form in tribe_forms(tribe))
    return bool(re.search(rf"\b({forms})\b", value.casefold()))


def tribal_match_score(card: dict, tribe: str | None = None) -> float:
    normalized_tribe = normalize_tribe(tribe)
    if not normalized_tribe:
        return 0

    type_line = card.get("type_line", "")
    oracle_text = card.get("oracle_text", "")
    text = oracle_text.casefold()
    score = 0

    if contains_tribe(type_line, normalized_tribe):
        score += 18
    if contains_tribe(oracle_text, normalized_tribe):
        score += 14

    forms = "|".join(re.escape(form) for form in tribe_forms(normalized_tribe))
    lord_patterns = [
        rf"\b({forms})\b you control get \+\d+/\+\d+",
        rf"other \b({forms})\b you control get \+\d+/\+\d+",
        rf"\b({forms})\b you control have",
        rf"other \b({forms})\b you control have",
        rf"\b({forms})\b spells? you cast cost",
        rf"whenever .* \b({forms})\b .* enters",
        rf"whenever .* \b({forms})\b .* attacks",
        rf"create .* \b({forms})\b .* token",
        rf"search your library .* \b({forms})\b",
        rf"return .* \b({forms})\b .* from your graveyard",
    ]

    if any(re.search(pattern, text) for pattern in lord_patterns):
        score += 24

    return score


def tag_focus_multiplier(tag: str, focus_weights: dict[str, float] | None = None) -> float:
    if not focus_weights:
        return 1
    return focus_weights.get(tag, 1)


def weighted_tag_score(tags: set[str], base_points: float, focus_weights: dict[str, float] | None = None) -> float:
    return sum(base_points * tag_focus_multiplier(tag, focus_weights) for tag in tags)


def focus_match_score(card: dict, focus_weights: dict[str, float] | None = None) -> float:
    if not focus_weights:
        return 0

    card_tags = set(card.get("tags") or [])
    return round(sum(12 * weight for tag, weight in focus_weights.items() if tag in card_tags), 2)


def commander_synergy_score(
    card: dict,
    commander: dict,
    focus_weights: dict[str, float] | None = None,
) -> float:
    card_tags = set(card.get("tags") or [])
    commander_tags = set(commander.get("tags") or [])

    direct_overlap = card_tags & commander_tags
    connected_tags = set()

    for commander_tag in commander_tags:
        connected_tags |= TAG_SYNERGIES.get(commander_tag, set())

    indirect_overlap = card_tags & connected_tags
    support_tags = card_tags & {"card_draw", "mana_ramp", "removal", "protection", "tutor"}
    focused_tags = card_tags & set(focus_weights or {})

    strategic_direct = direct_overlap - STRUCTURAL_TAGS
    structural_direct = direct_overlap & STRUCTURAL_TAGS
    strategic_indirect = indirect_overlap - STRUCTURAL_TAGS
    structural_indirect = indirect_overlap & STRUCTURAL_TAGS

    score = (
        weighted_tag_score(strategic_direct, 10, focus_weights)
        + weighted_tag_score(structural_direct, 3, focus_weights)
        + weighted_tag_score(strategic_indirect, 7, focus_weights)
        + weighted_tag_score(structural_indirect, 2, focus_weights)
        + weighted_tag_score(support_tags, 2, focus_weights)
        + weighted_tag_score(focused_tags, 8, focus_weights)
    )

    return min(60 if focus_weights else 45, score)


def commander_relevance_score(
    card: dict,
    commander: dict,
    focus_weights: dict[str, float] | None = None,
    tribe: str | None = None,
) -> float:
    synergy = commander_synergy_score(card, commander, focus_weights)
    power = float(card.get("power_score") or 0)
    opportunity = float(card.get("opportunity_score") or 0)
    efficiency = float(card.get("efficiency_score") or 0)
    focus_score = focus_match_score(card, focus_weights)
    tribe_score = tribal_match_score(card, tribe)

    return round(
        (power * 0.38)
        + (opportunity * 0.23)
        + (synergy * 0.24)
        + (efficiency * 0.05)
        + focus_score
        + tribe_score,
        2,
    )


def explain_match(card: dict, commander: dict) -> str:
    card_tags = set(card.get("tags") or [])
    commander_tags = set(commander.get("tags") or [])
    direct = sorted(card_tags & commander_tags)

    connected_tags = set()
    for commander_tag in commander_tags:
        connected_tags |= TAG_SYNERGIES.get(commander_tag, set())

    indirect = sorted((card_tags & connected_tags) - set(direct))
    parts = []

    if direct:
        parts.append(f"shared: {', '.join(direct)}")
    if indirect:
        parts.append(f"supports: {', '.join(indirect)}")
    if not parts:
        parts.append("generic power/support")

    return "; ".join(parts)


def recommend_for_commander(
    cards: list[dict],
    commander_name: str,
    limit: int = 25,
    min_power: float = 0,
    focus_weights: dict[str, float] | None = None,
    require_focus: bool = False,
    required_tags: set[str] | None = None,
    tribe: str | None = None,
) -> tuple[dict, list[dict]]:
    commander = find_card(cards, commander_name)
    recommendations = []

    for card in cards:
        if card.get("oracle_id") == commander.get("oracle_id"):
            continue
        if not is_color_legal(card, commander):
            continue
        if float(card.get("power_score") or 0) < min_power:
            continue
        card_tags = set(card.get("tags") or [])
        if required_tags and not required_tags <= card_tags:
            continue
        tribe_score = tribal_match_score(card, tribe)
        if tribe and tribe_score <= 0:
            continue

        synergy = commander_synergy_score(card, commander, focus_weights)
        focused_match = bool(card_tags & set(focus_weights or {}))
        if require_focus and not focused_match:
            continue
        if synergy <= 0 and float(card.get("power_score") or 0) < 70 and not focused_match:
            continue

        enriched = dict(card)
        enriched["commander_synergy_score"] = synergy
        enriched["focus_match_score"] = focus_match_score(card, focus_weights)
        enriched["tribal_match_score"] = tribe_score
        enriched["commander_relevance_score"] = commander_relevance_score(card, commander, focus_weights, tribe)
        enriched["commander_match"] = explain_match(card, commander)
        recommendations.append(enriched)

    recommendations.sort(
        key=lambda card: (
            card["commander_relevance_score"],
            card.get("tribal_match_score") or 0,
            card.get("focus_match_score") or 0,
            card["commander_synergy_score"],
            card.get("opportunity_score") or 0,
        ),
        reverse=True,
    )

    return commander, recommendations[:limit]
