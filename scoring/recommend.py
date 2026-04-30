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
        return sorted(contains_matches, key=lambda card: len(card["name"]))[0]

    close = get_close_matches(target, by_name.keys(), n=1, cutoff=0.65)
    if close:
        return by_name[close[0]]

    raise ValueError(f"Could not find commander named {name!r}")


def is_color_legal(card: dict, commander: dict) -> bool:
    commander_identity = set(commander.get("color_identity") or [])
    card_identity = set(card.get("color_identity") or [])
    return card_identity <= commander_identity


def commander_synergy_score(card: dict, commander: dict) -> float:
    card_tags = set(card.get("tags") or [])
    commander_tags = set(commander.get("tags") or [])

    direct_overlap = card_tags & commander_tags
    connected_tags = set()

    for commander_tag in commander_tags:
        connected_tags |= TAG_SYNERGIES.get(commander_tag, set())

    indirect_overlap = card_tags & connected_tags
    support_tags = card_tags & {"card_draw", "mana_ramp", "removal", "protection", "tutor"}

    strategic_direct = direct_overlap - STRUCTURAL_TAGS
    structural_direct = direct_overlap & STRUCTURAL_TAGS
    strategic_indirect = indirect_overlap - STRUCTURAL_TAGS
    structural_indirect = indirect_overlap & STRUCTURAL_TAGS

    return min(
        45,
        len(strategic_direct) * 10
        + len(structural_direct) * 3
        + len(strategic_indirect) * 7
        + len(structural_indirect) * 2
        + len(support_tags) * 2,
    )


def commander_relevance_score(card: dict, commander: dict) -> float:
    synergy = commander_synergy_score(card, commander)
    power = float(card.get("power_score") or 0)
    opportunity = float(card.get("opportunity_score") or 0)
    efficiency = float(card.get("efficiency_score") or 0)

    return round((power * 0.42) + (opportunity * 0.28) + (synergy * 0.25) + (efficiency * 0.05), 2)


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

        synergy = commander_synergy_score(card, commander)
        if synergy <= 0 and float(card.get("power_score") or 0) < 70:
            continue

        enriched = dict(card)
        enriched["commander_synergy_score"] = synergy
        enriched["commander_relevance_score"] = commander_relevance_score(card, commander)
        enriched["commander_match"] = explain_match(card, commander)
        recommendations.append(enriched)

    recommendations.sort(
        key=lambda card: (
            card["commander_relevance_score"],
            card["commander_synergy_score"],
            card.get("opportunity_score") or 0,
        ),
        reverse=True,
    )

    return commander, recommendations[:limit]
