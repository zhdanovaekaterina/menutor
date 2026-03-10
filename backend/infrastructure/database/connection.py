from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session

from backend.infrastructure.database.models import Base


def get_engine(db_path: str = "data/menutor.db") -> Engine:
    if db_path != ":memory:":
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")

    @event.listens_for(engine, "connect")
    def _enable_fk(conn, _record):  # type: ignore[no-untyped-def]
        conn.execute("PRAGMA foreign_keys = ON")

    return engine


def _migrate_menu_slots(conn) -> None:  # type: ignore[no-untyped-def]
    """Migrate old menu_slots (no product_id) to new schema."""
    info = conn.execute(text("PRAGMA table_info(menu_slots)")).fetchall()
    columns = {row[1] for row in info}
    if "product_id" in columns:
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS _menu_slots_backup (
            menu_id INTEGER, day INTEGER, meal_type TEXT,
            recipe_id INTEGER, servings_override REAL
        )
    """))
    conn.execute(text(
        "INSERT INTO _menu_slots_backup "
        "SELECT menu_id, day, meal_type, recipe_id, servings_override FROM menu_slots"
    ))
    conn.execute(text("DROP TABLE menu_slots"))
    conn.commit()


def _migrate_products_supplier(conn) -> None:  # type: ignore[no-untyped-def]
    info = conn.execute(text("PRAGMA table_info(products)")).fetchall()
    if "supplier" not in {row[1] for row in info}:
        conn.execute(text(
            "ALTER TABLE products ADD COLUMN supplier TEXT NOT NULL DEFAULT ''"
        ))
        conn.commit()


def _migrate_recipes_weight(conn) -> None:  # type: ignore[no-untyped-def]
    info = conn.execute(text("PRAGMA table_info(recipes)")).fetchall()
    if "weight" not in {row[1] for row in info}:
        conn.execute(text(
            "ALTER TABLE recipes ADD COLUMN weight INTEGER NOT NULL DEFAULT 0"
        ))
        conn.commit()


def apply_schema(engine: Engine) -> None:
    """Create all tables (idempotent). Runs legacy migrations first."""
    with engine.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        had_menu_slots = "menu_slots" in tables
        if had_menu_slots:
            _migrate_menu_slots(conn)
        if "products" in tables:
            _migrate_products_supplier(conn)
        if "recipes" in tables:
            _migrate_recipes_weight(conn)

    Base.metadata.create_all(engine)

    # Restore backed-up menu_slots data if migration happened
    if had_menu_slots:
        with engine.connect() as conn:
            backup_exists = conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='_menu_slots_backup'"
                )
            ).fetchone()
            if backup_exists:
                conn.execute(text(
                    "INSERT INTO menu_slots "
                    "(menu_id, day, meal_type, recipe_id, servings_override) "
                    "SELECT menu_id, day, meal_type, recipe_id, servings_override "
                    "FROM _menu_slots_backup"
                ))
                conn.execute(text("DROP TABLE _menu_slots_backup"))
                conn.commit()


def seed_defaults(session: Session) -> None:
    """Populate lookup tables with default unit and category values."""
    session.execute(
        text("INSERT OR IGNORE INTO units (name, unit_group) VALUES (:n, :g)"),
        [
            {"n": "g",    "g": "weight"},
            {"n": "kg",   "g": "weight"},
            {"n": "ml",   "g": "volume"},
            {"n": "l",    "g": "volume"},
            {"n": "pcs",  "g": "count_pcs"},
            {"n": "box",  "g": "count_box"},
            {"n": "pack", "g": "count_pack"},
        ],
    )
    session.execute(
        text(
            "INSERT OR IGNORE INTO recipe_categories (name, active) VALUES (:n, 1)"
        ),
        [
            {"n": "Завтраки"}, {"n": "Обеды"}, {"n": "Ужины"},
            {"n": "Основные"}, {"n": "Салаты"}, {"n": "Десерты"},
        ],
    )
    session.execute(
        text(
            "INSERT OR IGNORE INTO product_categories (name, active) VALUES (:n, 1)"
        ),
        [
            {"n": "Сыпучие"}, {"n": "Молочные"}, {"n": "Мясо"}, {"n": "Овощи"},
            {"n": "Фрукты"}, {"n": "Консервы"}, {"n": "Напитки"}, {"n": "Прочее"},
        ],
    )
    session.commit()
