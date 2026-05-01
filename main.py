import argparse
import json
import re
from pathlib import Path

from config import RECOMMENDATIONS_DIR, SCORED_CARDS_PATH, ensure_project_dirs
from ingestion.fetch_edhrec import fetch_popularity_for_cards, load_card_names, save_popularity
from ingestion.fetch_scryfall import fetch_bulk_cards, save_raw
from ingestion.load_db import upsert_cards
from ingestion.normalize import load_raw_cards, normalize_cards, save_normalized
from scoring.recommend import recommend_for_commander
from scoring.score import load_json, save_scored, score_cards
from tagging.tag_engine import load_cards, save_tagged, tag_cards


def parse_focus_weights(focus_values: list[str] | None) -> dict[str, float]:
    weights = {}

    for value in focus_values or []:
        if "=" in value:
            tag, raw_weight = value.split("=", 1)
            weights[tag.strip()] = float(raw_weight)
        else:
            weights[value.strip()] = 1.5

    return {tag: weight for tag, weight in weights.items() if tag and weight > 0}


def run_scryfall() -> None:
    cards = fetch_bulk_cards()
    save_raw(cards)
    print(f"Fetched {len(cards)} Scryfall cards")


def run_normalize() -> None:
    cards = normalize_cards(load_raw_cards())
    save_normalized(cards)
    print(f"Normalized {len(cards)} commander-legal cards")


def run_tag() -> None:
    cards = tag_cards(load_cards())
    save_tagged(cards)
    print(f"Tagged {len(cards)} cards")


def run_edhrec(limit: int | None) -> None:
    names = load_card_names(limit=limit)
    records = fetch_popularity_for_cards(names)
    save_popularity(records)
    print(f"Fetched EDHREC popularity for {len(records)} cards")


def run_score() -> None:
    from config import EDHREC_POPULARITY_PATH, TAGGED_CARDS_PATH

    cards = load_json(TAGGED_CARDS_PATH, [])
    popularity = load_json(EDHREC_POPULARITY_PATH, [])
    scored = score_cards(cards, popularity)
    save_scored(scored)
    print(f"Scored {len(scored)} cards")


def run_load_db() -> None:
    cards = load_json(SCORED_CARDS_PATH, [])
    upsert_cards(cards)
    print(f"Loaded {len(cards)} cards into SQLite")


def show_top(path: Path = SCORED_CARDS_PATH, limit: int = 25) -> None:
    cards = load_json(path, [])
    for card in cards[:limit]:
        tags = ", ".join(card.get("tags") or [])
        deck_count = card.get("edhrec_deck_count")
        print(
            f"{card['name']}: opportunity={card['opportunity_score']} "
            f"power={card['power_score']} efficiency={card.get('efficiency_score')} "
            f"value={card.get('cost_adjusted_value')} decks={deck_count} tags=[{tags}]"
        )


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    return cleaned or "commander"


def default_commander_output_path(commander_name: str) -> Path:
    return RECOMMENDATIONS_DIR / f"{safe_filename(commander_name)}-recommended.json"


def save_commander_recommendations(
    commander: dict,
    recommendations: list[dict],
    output_path: Path,
    requested_name: str,
    min_power: float,
    focus_weights: dict[str, float] | None = None,
    require_focus: bool = False,
    required_tags: list[str] | None = None,
    tribe: str | None = None,
) -> None:
    ensure_project_dirs()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "requested_commander": requested_name,
        "commander": {
            "name": commander.get("name"),
            "oracle_id": commander.get("oracle_id"),
            "color_identity": commander.get("color_identity") or [],
            "tags": commander.get("tags") or [],
            "power_score": commander.get("power_score"),
            "opportunity_score": commander.get("opportunity_score"),
        },
        "filters": {
            "limit": len(recommendations),
            "min_power": min_power,
            "focus_weights": focus_weights or {},
            "require_focus": require_focus,
            "required_tags": required_tags or [],
            "tribe": tribe,
        },
        "recommendations": recommendations,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def show_commander_recommendations(
    commander_name: str,
    limit: int = 50,
    min_power: float = 0,
    output: str | None = None,
    clean: bool = False,
    focus_values: list[str] | None = None,
    require_focus: bool = False,
    required_tags: list[str] | None = None,
    tribe: str | None = None,
) -> None:
    cards = load_json(SCORED_CARDS_PATH, [])
    focus_weights = parse_focus_weights(focus_values)
    commander, recommendations = recommend_for_commander(
        cards,
        commander_name,
        limit,
        min_power,
        focus_weights,
        require_focus,
        set(required_tags or []),
        tribe,
    )
    commander_tags = ", ".join(commander.get("tags") or [])
    commander_colors = "".join(commander.get("color_identity") or []) or "colorless"
    output_path = Path(output) if output else default_commander_output_path(commander["name"])
    save_commander_recommendations(
        commander,
        recommendations,
        output_path,
        commander_name,
        min_power,
        focus_weights,
        require_focus,
        required_tags,
        tribe,
    )

    if not clean:
        print(f"Commander: {commander['name']} [{commander_colors}] tags=[{commander_tags}]")
        if focus_weights:
            focus_display = ", ".join(f"{tag}={weight:g}" for tag, weight in focus_weights.items())
            print(f"Focus: {focus_display}")
        if require_focus:
            print("Require focus: yes")
        if required_tags:
            print(f"Required tags: {', '.join(required_tags)}")
        if tribe:
            print(f"Tribal: {tribe}")
        print(f"Saved: {output_path}")
        print()

    for card in recommendations:
        if clean:
            print(card["name"])
            continue

        tags = ", ".join(card.get("tags") or [])
        print(
            f"{card['name']}: commander={card['commander_relevance_score']} "
            f"synergy={card['commander_synergy_score']} power={card['power_score']} "
            f"focus={card.get('focus_match_score')} "
            f"tribal={card.get('tribal_match_score')} "
            f"opportunity={card['opportunity_score']} value={card.get('cost_adjusted_value')} "
            f"match=({card['commander_match']}) tags=[{tags}]"
        )


def run_pipeline(skip_network: bool = False) -> None:
    ensure_project_dirs()
    if not skip_network:
        run_scryfall()
    run_normalize()
    run_tag()
    run_score()
    run_load_db()
    show_top(limit=20)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find strong, underplayed Magic cards for Commander.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("fetch-scryfall")
    subparsers.add_parser("normalize")
    subparsers.add_parser("tag")

    edhrec_parser = subparsers.add_parser("fetch-edhrec")
    edhrec_parser.add_argument("--limit", type=int, default=100, help="Limit EDHREC requests while testing.")

    subparsers.add_parser("score")
    subparsers.add_parser("load-db")
    subparsers.add_parser("top")

    commander_parser = subparsers.add_parser("commander")
    commander_parser.add_argument("name", help="Commander name to build around.")
    commander_parser.add_argument("--limit", type=int, default=50)
    commander_parser.add_argument("--min-power", type=float, default=0)
    commander_parser.add_argument("--output", help="Optional output JSON path.")
    commander_parser.add_argument("--clean", action="store_true", help="Print only recommended card names.")
    commander_parser.add_argument(
        "--focus",
        action="append",
        help="Increase or decrease a tag's importance. Examples: --focus graveyard or --focus plus_one_counters=0.5",
    )
    commander_parser.add_argument(
        "--require-focus",
        action="store_true",
        help="Only include cards that match at least one focused tag.",
    )
    commander_parser.add_argument(
        "--require-tag",
        action="append",
        help="Only include cards with this tag. Can be repeated.",
    )
    commander_parser.add_argument(
        "--tribal",
        help="Only include cards of this creature type or cards that mention/support it. Example: --tribal Goblins",
    )

    pipeline_parser = subparsers.add_parser("pipeline")
    pipeline_parser.add_argument("--skip-network", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "fetch-scryfall": run_scryfall,
        "normalize": run_normalize,
        "tag": run_tag,
        "fetch-edhrec": lambda: run_edhrec(args.limit),
        "score": run_score,
        "load-db": run_load_db,
        "top": show_top,
        "commander": lambda: show_commander_recommendations(
            args.name,
            args.limit,
            args.min_power,
            args.output,
            args.clean,
            args.focus,
            args.require_focus,
            args.require_tag,
            args.tribal,
        ),
        "pipeline": lambda: run_pipeline(args.skip_network),
    }

    if args.command is None:
        parser.print_help()
        return

    commands[args.command]()


if __name__ == "__main__":
    main()
