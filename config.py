from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "db"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EDHREC_DIR = DATA_DIR / "edhrec"
RECOMMENDATIONS_DIR = PROCESSED_DIR / "commander-recommendations"

SCRYFALL_BULK_URL = "https://api.scryfall.com/bulk-data"
SCRYFALL_BULK_TYPE = "default_cards"

RAW_CARDS_PATH = RAW_DIR / "scryfall-default-cards.json"
NORMALIZED_CARDS_PATH = PROCESSED_DIR / "cards-normalized.json"
TAGGED_CARDS_PATH = PROCESSED_DIR / "cards-tagged.json"
SCORED_CARDS_PATH = PROCESSED_DIR / "cards-scored.json"
EDHREC_POPULARITY_PATH = EDHREC_DIR / "card-popularity.json"
DB_PATH = DB_DIR / "cards.db"

COMMANDER_LEGALITY = "commander"


def ensure_project_dirs() -> None:
    """Create project data directories, replacing empty placeholder files."""
    for path in (DATA_DIR, DB_DIR, RAW_DIR, PROCESSED_DIR, EDHREC_DIR, RECOMMENDATIONS_DIR):
        if path.exists() and path.is_file() and path.stat().st_size == 0:
            path.unlink()
        path.mkdir(parents=True, exist_ok=True)
