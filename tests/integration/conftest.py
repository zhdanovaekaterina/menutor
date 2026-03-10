from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from backend.infrastructure.database.connection import apply_schema

_SEED_SQL = [
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('g',    'weight')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('kg',   'weight')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('ml',   'volume')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('l',    'volume')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pcs',  'count_pcs')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('box',  'count_box')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pack', 'count_pack')",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Завтраки', 1)",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Основные', 1)",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Салаты',   1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Сыпучие',  1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Молочные', 1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Мясо',     1)",
]


@pytest.fixture
def conn() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record):  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    apply_schema(engine)
    session = Session(engine)
    for stmt in _SEED_SQL:
        session.execute(text(stmt))
    session.commit()
    yield session
    session.close()
    engine.dispose()
