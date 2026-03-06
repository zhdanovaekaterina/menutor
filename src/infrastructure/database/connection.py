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


def _migrate_menu_slots(conn: sqlite3.Connection) -> None:
    """Migrate old menu_slots (composite PK, no product_id) to new schema."""
    info = conn.execute("PRAGMA table_info(menu_slots)").fetchall()
    columns = {row[1] for row in info}
    if "product_id" in columns:
        return  # already migrated
    # Old schema detected — recreate table
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS _menu_slots_backup (
            menu_id INTEGER, day INTEGER, meal_type TEXT,
            recipe_id INTEGER, servings_override REAL
        );
        INSERT INTO _menu_slots_backup SELECT menu_id, day, meal_type, recipe_id, servings_override FROM menu_slots;
        DROP TABLE menu_slots;
    """)


def _migrate_products_supplier(conn: sqlite3.Connection) -> None:
    """Add supplier column to products if missing."""
    info = conn.execute("PRAGMA table_info(products)").fetchall()
    columns = {row[1] for row in info}
    if "supplier" not in columns:
        conn.execute("ALTER TABLE products ADD COLUMN supplier TEXT NOT NULL DEFAULT ''")
        conn.commit()


def _migrate_recipes_weight(conn: sqlite3.Connection) -> None:
    """Add weight column to recipes if missing."""
    info = conn.execute("PRAGMA table_info(recipes)").fetchall()
    columns = {row[1] for row in info}
    if "weight" not in columns:
        conn.execute("ALTER TABLE recipes ADD COLUMN weight INTEGER NOT NULL DEFAULT 0")
        conn.commit()


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create all tables (idempotent). Enables foreign-key enforcement afterwards."""
    # Migrate old menu_slots if it exists
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "menu_slots" in tables:
        _migrate_menu_slots(conn)
    if "products" in tables:
        _migrate_products_supplier(conn)
    if "recipes" in tables:
        _migrate_recipes_weight(conn)

    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))

    # Restore backed-up data if migration happened
    if "menu_slots" in tables:
        backup_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_menu_slots_backup'"
        ).fetchone()
        if backup_exists:
            conn.executescript("""
                INSERT INTO menu_slots (menu_id, day, meal_type, recipe_id, servings_override)
                    SELECT menu_id, day, meal_type, recipe_id, servings_override
                    FROM _menu_slots_backup;
                DROP TABLE _menu_slots_backup;
            """)

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
