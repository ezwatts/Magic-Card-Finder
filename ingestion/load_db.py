import json
import sqlite3
from pathlib import Path

from config import DB_PATH, SCORED_CARDS_PATH, ensure_project_dirs


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    ensure_project_dirs()
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            oracle_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mana_cost TEXT,
            cmc REAL,
            type_line TEXT,
            oracle_text TEXT,
            color_identity TEXT,
            tags TEXT,
            edhrec_rank INTEGER,
            edhrec_deck_count INTEGER,
            effect_score REAL,
            cost_adjusted_value REAL,
            efficiency_score REAL,
            power_score REAL,
            opportunity_score REAL,
            scryfall_uri TEXT
        )
        """
    )
    existing_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(cards)").fetchall()
    }
    for column_name, column_type in {
        "effect_score": "REAL",
        "cost_adjusted_value": "REAL",
        "efficiency_score": "REAL",
    }.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE cards ADD COLUMN {column_name} {column_type}")
    return connection


def load_scored_cards(path: Path = SCORED_CARDS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def upsert_cards(cards: list[dict], db_path: Path = DB_PATH) -> None:
    connection = init_db(db_path)
    rows = [
        (
            card.get("oracle_id"),
            card.get("name"),
            card.get("mana_cost"),
            card.get("cmc"),
            card.get("type_line"),
            card.get("oracle_text"),
            json.dumps(card.get("color_identity") or []),
            json.dumps(card.get("tags") or []),
            card.get("edhrec_rank"),
            card.get("edhrec_deck_count"),
            card.get("effect_score"),
            card.get("cost_adjusted_value"),
            card.get("efficiency_score"),
            card.get("power_score"),
            card.get("opportunity_score"),
            card.get("scryfall_uri"),
        )
        for card in cards
        if card.get("oracle_id")
    ]

    connection.executemany(
        """
        INSERT INTO cards (
            oracle_id, name, mana_cost, cmc, type_line, oracle_text, color_identity,
            tags, edhrec_rank, edhrec_deck_count, effect_score, cost_adjusted_value,
            efficiency_score, power_score, opportunity_score, scryfall_uri
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(oracle_id) DO UPDATE SET
            name=excluded.name,
            mana_cost=excluded.mana_cost,
            cmc=excluded.cmc,
            type_line=excluded.type_line,
            oracle_text=excluded.oracle_text,
            color_identity=excluded.color_identity,
            tags=excluded.tags,
            edhrec_rank=excluded.edhrec_rank,
            edhrec_deck_count=excluded.edhrec_deck_count,
            effect_score=excluded.effect_score,
            cost_adjusted_value=excluded.cost_adjusted_value,
            efficiency_score=excluded.efficiency_score,
            power_score=excluded.power_score,
            opportunity_score=excluded.opportunity_score,
            scryfall_uri=excluded.scryfall_uri
        """,
        rows,
    )
    connection.commit()
    connection.close()


if __name__ == "__main__":
    cards = load_scored_cards()
    upsert_cards(cards)
    print(f"Loaded {len(cards)} cards into {DB_PATH}")
