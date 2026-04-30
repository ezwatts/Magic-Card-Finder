# Magic Card Finder

Find Commander cards that look powerful for a specific strategy or commander, but may be underplayed on EDHREC.

The project builds a local card database from Scryfall, adds heuristic strategy tags, optionally imports EDHREC popularity data, then ranks cards by power, efficiency, commander relevance, and underplayed opportunity.

## Setup

```powershell
pip install -r requirements.txt
```

Use Python 3.11+ if possible.

## Build the local data

Scryfall and EDHREC data are generated locally and are intentionally not committed to git.

```powershell
python main.py fetch-scryfall
python main.py normalize
python main.py tag
python main.py fetch-edhrec --limit 100
python main.py score
python main.py load-db
```

You can also run the non-EDHREC pipeline after Scryfall has been fetched:

```powershell
python main.py pipeline --skip-network
```

Increase the EDHREC limit once the small test run works:

```powershell
python main.py fetch-edhrec --limit 1000
python main.py score
python main.py load-db
```

If tag logic changes, refresh generated scores with:

```powershell
python main.py tag
python main.py score
```

## Commands

Show hidden-gem style results:

```powershell
python main.py top
```

Find recommendations for a commander:

```powershell
python main.py commander "Muldrotha"
```

Commander recommendations default to 50 cards. You can override that and filter by minimum power:

```powershell
python main.py commander "Winter, Misanthropic Guide" --limit 25 --min-power 50
```

Print only card names:

```powershell
python main.py commander "Winter, Misanthropic Guide" --clean
```

This still writes a detailed commander-specific JSON report under:

```text
data/processed/commander-recommendations/
```

You can choose a custom output path:

```powershell
python main.py commander "Muldrotha" --output "data/processed/Muldrotha recommended.json"
```

## Scoring

Cards are scored with several fields:

- `power_score`: overall strength estimate.
- `effect_score`: estimated value of the card text.
- `cost_adjusted_value`: how much useful effect the card provides relative to mana value.
- `efficiency_score`: bonus or penalty for cheap/high-impact versus clunky/low-impact cards.
- `opportunity_score`: power score reduced by EDHREC popularity.
- `commander_relevance_score`: commander-specific blend of power, opportunity, efficiency, shared tags, and synergistic tags.

## Tags And Synergies

The tagger recognizes broad themes such as:

```text
artifact, creature, enchantment, instant, land, legendary, planeswalker, saga, sorcery, vehicle
card_draw, mana_ramp, removal, tutor, protection, stax
graveyard, recursion, reanimator, sacrifice, aristocrats
blink, etb, tokens, treasures, clues
counters, plus_one_counters, minus_one_counters, energy, proliferate
topdeck, impulse_draw, exile, cycling, snow
attack_triggers, extra_combat, unblockable, ninjutsu, voltron
monarch, politics, tap_untap, fight, flash, dungeon, crimes
```

Commander recommendations use explicit synergy relationships, for example:

```text
blink <-> etb
sacrifice <-> graveyard / recursion / aristocrats
tokens <-> sacrifice / counters / doubling
artifact <-> treasures / clues / sacrifice
saga <-> enchantment / historic / proliferate
ninjutsu <-> unblockable / attack_triggers
energy <-> counters / proliferate / doubling
```

## Generated Files

The generated data can be large and is ignored by git:

```text
data/raw/
data/processed/
data/edhrec/
db/*.db
```

Friends who clone the repo should generate these files locally by running the setup commands above.
