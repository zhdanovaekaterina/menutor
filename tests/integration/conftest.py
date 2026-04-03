from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from backend.domain.value_objects.types import UserId
from backend.infrastructure.database.connection import apply_schema

_SEED_SQL = [
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('g',    'weight')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('kg',   'weight')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('ml',   'volume')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('l',    'volume')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pcs',  'count_pcs')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('box',  'count_box')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pack', 'count_pack')",
    "INSERT OR IGNORE INTO units (name, unit_group) VALUES ('serv', 'servings')",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Завтраки', 1)",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Основные', 1)",
    "INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Салаты',   1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Сыпучие',  1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Молочные', 1)",
    "INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Мясо',     1)",
]

_SEED_USER_SQL = (
    "INSERT INTO users (email, nickname, hashed_password, created_at) "
    "VALUES ('test@example.com', 'tester', 'hashed', '2025-01-01 00:00:00')"
)

# Three system meal types for user_id=1 (ids 1=Завтрак, 2=Обед, 3=Ужин)
_SEED_MEAL_TYPES_SQL = [
    "INSERT OR IGNORE INTO meal_types (id, user_id, name, time, is_system, sort_order) VALUES (1, 1, 'Завтрак', '08:00', 1, 0)",
    "INSERT OR IGNORE INTO meal_types (id, user_id, name, time, is_system, sort_order) VALUES (2, 1, 'Обед', '13:00', 1, 1)",
    "INSERT OR IGNORE INTO meal_types (id, user_id, name, time, is_system, sort_order) VALUES (3, 1, 'Ужин', '18:00', 1, 2)",
]

TEST_USER_ID = UserId(1)


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
    session.execute(text(_SEED_USER_SQL))
    for stmt in _SEED_MEAL_TYPES_SQL:
        session.execute(text(stmt))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def user_id() -> UserId:
    return TEST_USER_ID
