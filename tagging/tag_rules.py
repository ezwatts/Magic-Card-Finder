import re


TAG_PATTERNS = {
    "aristocrats": [r"whenever .* dies", r"creature dies", r"each opponent loses \d+ life"],
    "activated_abilities": [r"activated abilities", r": [a-z{]", r"activate only"],
    "artifact": [r"\bartifact\b"],
    "attack_triggers": [r"whenever .* attacks", r"whenever .* attack", r"attacks, "],
    "blink": [r"exile .* return .* battlefield", r"exile .* then return", r"return .* to the battlefield under .* owner's control"],
    "card_draw": [r"\bdraws? (a|one|two|three|four|x|\d+) cards?", r"draw that many cards?"],
    "clues": [r"clue token", r"investigate"],
    "coin_flip": [r"flip a coin", r"coin flip"],
    "counters": [r"counter on", r"proliferate", r"\+1/\+1 counter", r"-1/-1 counter", r"energy counter"],
    "crimes": [r"commit a crime", r"committed a crime", r"target opponent", r"target spell an opponent controls", r"target permanent an opponent controls"],
    "creature": [r"\bcreature\b"],
    "cycling": [r"\bcycling\b"],
    "dice_rolling": [r"roll (a|one or more) d\d+", r"roll .* dice", r"die roll"],
    "discard": [r"discard"],
    "dungeon": [r"venture into the dungeon", r"initiative", r"complete a dungeon"],
    "doubling": [r"double", r"twice that many", r"additional"],
    "enchantment": [r"\benchantment\b"],
    "energy": [r"energy counter", r"\{e\}", r"pay .* energy"],
    "etb": [r"enters the battlefield", r"when .* enters", r"whenever .* enters"],
    "experience_counters": [r"experience counters?"],
    "exile": [r"\bexile\b", r"from exile", r"exiled card"],
    "extra_combat": [r"additional combat phase", r"extra combat", r"after this phase"],
    "fight": [r"\bfights?\b"],
    "flash": [r"\bflash\b", r"as though .* had flash"],
    "graveyard": [r"graveyard", r"return .* from your graveyard", r"escape", r"delirium", r"threshold"],
    "historic": [r"\bhistoric\b", r"artifact, legendary, or saga"],
    "impulse_draw": [r"exile .* top .* library", r"you may play .* exiled", r"you may cast .* exiled"],
    "landfall": [r"land enters", r"landfall", r"play an additional land"],
    "land_animation": [r"land becomes .* creature", r"lands? you control .* creatures?"],
    "land_destruction": [
        r"destroy target land",
        r"destroy target nonbasic land",
        r"destroy .* lands?",
        r"each player sacrifices .* lands?",
        r"each opponent sacrifices .* lands?",
        r"opponents? can't play lands?",
        r"lands? .* don't untap",
    ],
    "land_sacrifice": [r"sacrifice .* lands?", r"sacrifice .*: search your library .* land", r"sacrifice .*: add"],
    "land": [r"\bland\b"],
    "legendary": [r"\blegendary\b"],
    "lifegain": [r"gain \d+ life", r"whenever you gain life", r"lifelink"],
    "ltb": [r"leaves the battlefield", r"when .* leaves", r"whenever .* leaves"],
    "mana_ramp": [r"add [\{wubrgc/0-9x\}]+", r"search your library .* land", r"treasure token"],
    "mill": [r"mill", r"put .* cards .* graveyard"],
    "monarch": [r"\bmonarch\b"],
    "ninjutsu": [r"\bninjutsu\b"],
    "plus_one_counters": [r"\+1/\+1 counter"],
    "minus_one_counters": [r"-1/-1 counter"],
    "planeswalker": [r"\bplaneswalker\b"],
    "politics": [r"each opponent may", r"opponent chooses", r"council's dilemma", r"will of the council", r"tempting offer"],
    "power_matters": [r"power [0-9x]", r"power or toughness", r"greatest power", r"power among"],
    "proliferate": [r"\bproliferate\b"],
    "protection": [r"hexproof", r"indestructible", r"protection from", r"phase out", r"\bward\b"],
    "reanimator": [r"return target creature card from your graveyard", r"put .* creature card from .* graveyard onto the battlefield"],
    "recursion": [r"return .* from your graveyard", r"cast .* from your graveyard"],
    "removal": [r"destroy target", r"exile target", r"deals? \d+ damage to target", r"counter target"],
    "saga": [r"\bsaga\b"],
    "sacrifice": [r"sacrifice", r"dies"],
    "snow": [r"\bsnow\b", r"snow mana", r"snow permanent"],
    "spellslinger": [r"instant or sorcery", r"whenever you cast .* spell", r"copy target .* spell"],
    "stax": [r"can't cast", r"doesn't untap", r"players can't", r"skip", r"maximum hand size"],
    "tap_untap": [r"\btap target\b", r"\buntap\b", r"becomes tapped", r"whenever .* taps"],
    "toughness_matters": [r"toughness [0-9x]", r"power or toughness", r"greatest toughness", r"toughness rather than"],
    "treasures": [r"treasure token"],
    "tokens": [r"create .* token", r"populate"],
    "topdeck": [r"top card of your library", r"scry", r"surveil", r"look at the top", r"reveal the top"],
    "tutor": [r"search your library", r"reveal .* from your library"],
    "unblockable": [r"can't be blocked", r"unblockable"],
    "vehicle": [r"\bvehicle\b", r"\bcrew\b"],
    "voltron": [r"equipped creature", r"enchanted creature", r"aura", r"equipment"],
}

TAG_SYNERGIES = {
    "aristocrats": {"sacrifice", "tokens", "recursion"},
    "artifact": {"historic", "treasures", "clues", "sacrifice", "recursion"},
    "attack_triggers": {"extra_combat", "unblockable", "voltron", "ninjutsu"},
    "blink": {"etb", "ltb", "card_draw", "removal", "tokens"},
    "card_draw": {"cycling", "monarch", "impulse_draw", "topdeck"},
    "clues": {"artifact", "tokens", "sacrifice", "card_draw"},
    "counters": {"doubling", "tokens", "protection", "proliferate", "experience_counters"},
    "creature": {"blink", "etb", "sacrifice", "recursion", "tokens"},
    "crimes": {"removal", "discard", "spellslinger"},
    "cycling": {"graveyard", "card_draw", "discard", "recursion"},
    "discard": {"graveyard", "recursion", "reanimator"},
    "doubling": {"counters", "plus_one_counters", "minus_one_counters", "energy", "experience_counters", "tokens"},
    "enchantment": {"saga", "constellation", "recursion"},
    "energy": {"counters", "doubling", "proliferate"},
    "etb": {"blink", "recursion", "creature", "artifact", "enchantment"},
    "experience_counters": {"counters", "proliferate", "doubling"},
    "exile": {"impulse_draw", "removal", "recursion"},
    "extra_combat": {"attack_triggers", "voltron", "tokens"},
    "fight": {"power_matters", "removal"},
    "graveyard": {"discard", "mill", "recursion", "sacrifice", "cycling"},
    "historic": {"artifact", "legendary", "saga"},
    "impulse_draw": {"exile", "topdeck", "spellslinger", "card_draw"},
    "landfall": {"mana_ramp", "tokens"},
    "land": {"landfall", "mana_ramp", "land_animation", "land_destruction", "land_sacrifice"},
    "land_destruction": {"land", "stax", "removal", "recursion", "graveyard"},
    "land_sacrifice": {"land", "sacrifice", "graveyard", "recursion", "landfall", "mana_ramp"},
    "legendary": {"historic", "voltron"},
    "lifegain": {"card_draw", "tokens"},
    "ltb": {"blink", "sacrifice", "recursion"},
    "monarch": {"politics", "card_draw", "unblockable", "attack_triggers"},
    "ninjutsu": {"unblockable", "attack_triggers"},
    "plus_one_counters": {"counters", "doubling", "proliferate", "tokens"},
    "minus_one_counters": {"counters", "proliferate", "doubling", "removal"},
    "planeswalker": {"proliferate", "doubling", "protection"},
    "power_matters": {"fight", "plus_one_counters", "voltron", "tokens"},
    "proliferate": {"counters", "experience_counters", "plus_one_counters", "minus_one_counters", "energy", "planeswalker", "saga"},
    "recursion": {"etb", "ltb", "graveyard", "sacrifice"},
    "removal": {"crimes", "fight", "spellslinger"},
    "saga": {"enchantment", "historic", "proliferate", "blink"},
    "sacrifice": {"aristocrats", "tokens", "recursion", "graveyard", "artifact", "ltb", "land_sacrifice"},
    "snow": {"land", "mana_ramp"},
    "spellslinger": {"card_draw", "removal", "tokens"},
    "stax": {"land_destruction", "tap_untap", "removal"},
    "tap_untap": {"activated_abilities", "mana_ramp", "vehicle"},
    "toughness_matters": {"plus_one_counters", "tokens", "protection"},
    "treasures": {"artifact", "tokens", "sacrifice", "mana_ramp"},
    "tokens": {"aristocrats", "counters", "doubling", "sacrifice", "artifact", "treasures", "clues"},
    "topdeck": {"card_draw", "impulse_draw", "miracle"},
    "unblockable": {"ninjutsu", "attack_triggers", "voltron"},
    "vehicle": {"artifact", "tap_untap", "creature"},
    "voltron": {"protection", "card_draw"},
}

TYPE_TAGS = {
    "artifact": "Artifact",
    "battle": "Battle",
    "creature": "Creature",
    "enchantment": "Enchantment",
    "instant": "Instant",
    "land": "Land",
    "legendary": "Legendary",
    "planeswalker": "Planeswalker",
    "saga": "Saga",
    "sorcery": "Sorcery",
    "vehicle": "Vehicle",
}

KEYWORD_TAGS = {
    "cycling": "cycling",
    "flash": "flash",
    "ninjutsu": "ninjutsu",
    "crew": "vehicle",
}


def tag_card(text: str, type_line: str = "", keywords: list[str] | None = None) -> list[str]:
    haystack = f"{text}\n{type_line}\n{' '.join(keywords or [])}".lower()
    tags = set()

    for tag, type_name in TYPE_TAGS.items():
        if type_name.lower() in type_line.lower():
            tags.add(tag)

    for keyword in keywords or []:
        keyword_tag = KEYWORD_TAGS.get(keyword.lower())
        if keyword_tag:
            tags.add(keyword_tag)

    for tag, patterns in TAG_PATTERNS.items():
        if any(re.search(pattern, haystack) for pattern in patterns):
            tags.add(tag)

    if tags & {"plus_one_counters", "minus_one_counters", "energy", "experience_counters", "proliferate"}:
        tags.add("counters")
    if tags & {"clues", "treasures"}:
        tags.add("tokens")
        tags.add("artifact")
    if "saga" in tags:
        tags.add("enchantment")
    if "vehicle" in tags:
        tags.add("artifact")

    return sorted(tags)
