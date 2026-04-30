import re


TAG_PATTERNS = {
    "aristocrats": [r"whenever .* dies", r"creature dies", r"each opponent loses \d+ life"],
    "blink": [r"exile .* return .* battlefield", r"leaves the battlefield", r"enters the battlefield"],
    "card_draw": [r"draw (a|two|three|x) cards?", r"draw that many cards?"],
    "counters": [r"\+1/\+1 counter", r"proliferate", r"counter on"],
    "discard": [r"discard"],
    "doubling": [r"double", r"twice that many", r"additional"],
    "graveyard": [r"graveyard", r"return .* from your graveyard", r"escape", r"delirium", r"threshold"],
    "landfall": [r"land enters", r"landfall", r"play an additional land"],
    "lifegain": [r"gain \d+ life", r"whenever you gain life", r"lifelink"],
    "mana_ramp": [r"add [\{wubrgc/0-9x\}]+", r"search your library .* land", r"treasure token"],
    "mill": [r"mill", r"put .* cards .* graveyard"],
    "protection": [r"hexproof", r"indestructible", r"protection from", r"phase out"],
    "recursion": [r"return .* from your graveyard", r"cast .* from your graveyard"],
    "removal": [r"destroy target", r"exile target", r"deals? \d+ damage to target", r"counter target"],
    "sacrifice": [r"sacrifice", r"dies"],
    "spellslinger": [r"instant or sorcery", r"whenever you cast .* spell", r"copy target .* spell"],
    "stax": [r"can't cast", r"doesn't untap", r"players can't", r"skip"],
    "tokens": [r"create .* token", r"populate"],
    "tutor": [r"search your library", r"reveal .* from your library"],
    "voltron": [r"equipped creature", r"enchanted creature", r"aura", r"equipment"],
}

TAG_SYNERGIES = {
    "aristocrats": {"sacrifice", "tokens", "recursion"},
    "blink": {"card_draw", "removal", "tokens"},
    "counters": {"doubling", "tokens", "protection"},
    "discard": {"graveyard", "recursion"},
    "graveyard": {"discard", "mill", "recursion", "sacrifice"},
    "landfall": {"mana_ramp", "tokens"},
    "lifegain": {"card_draw", "tokens"},
    "sacrifice": {"aristocrats", "tokens", "recursion", "graveyard"},
    "spellslinger": {"card_draw", "removal", "tokens"},
    "tokens": {"aristocrats", "counters", "doubling", "sacrifice"},
    "voltron": {"protection", "card_draw"},
}


def tag_card(text: str, type_line: str = "", keywords: list[str] | None = None) -> list[str]:
    haystack = f"{text}\n{type_line}\n{' '.join(keywords or [])}".lower()
    tags = set()

    for tag, patterns in TAG_PATTERNS.items():
        if any(re.search(pattern, haystack) for pattern in patterns):
            tags.add(tag)

    return sorted(tags)
