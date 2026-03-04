import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str = "data/menutor.db") -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create all tables (idempotent). Enables foreign-key enforcement afterwards."""
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    # executescript issues an implicit COMMIT which can reset per-connection PRAGMAs;
    # re-enable foreign keys explicitly after it returns.
    conn.execute("PRAGMA foreign_keys = ON")


def seed_defaults(conn: sqlite3.Connection) -> None:
    """Populate lookup tables with default unit and category values."""
    conn.executemany(
        "INSERT OR IGNORE INTO units (name, unit_group) VALUES (?, ?)",
        [
            ("g",    "weight"),
            ("kg",   "weight"),
            ("ml",   "volume"),
            ("l",    "volume"),
            ("pcs",  "count_pcs"),
            ("box",  "count_box"),
            ("pack", "count_pack"),
        ],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO recipe_categories (name, active) VALUES (?, 1)",
        [("Завтраки",), ("Обеды",), ("Ужины",), ("Основные",), ("Салаты",), ("Десерты",)],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO product_categories (name, active) VALUES (?, 1)",
        [("Сыпучие",), ("Молочные",), ("Мясо",), ("Овощи",),
         ("Фрукты",), ("Консервы",), ("Напитки",), ("Прочее",)],
    )
    conn.commit()
