import sqlite3
from collections.abc import Generator

import pytest

from src.infrastructure.database.connection import apply_schema

_SEED_SQL = """
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('g',    'weight');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('kg',   'weight');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('ml',   'volume');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('l',    'volume');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pcs',  'count_pcs');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('box',  'count_box');
INSERT OR IGNORE INTO units (name, unit_group) VALUES ('pack', 'count_pack');
INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Завтраки', 1);
INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Основные', 1);
INSERT OR IGNORE INTO recipe_categories  (name, active) VALUES ('Салаты',   1);
INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Сыпучие',  1);
INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Молочные', 1);
INSERT OR IGNORE INTO product_categories (name, active) VALUES ('Мясо',     1);
"""


@pytest.fixture
def conn() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    apply_schema(connection)
    # PRAGMA foreign_keys cannot be set inside executescript; set it separately
    connection.execute("PRAGMA foreign_keys = ON")
    # Seed required lookup data (executemany uses autocommit per statement with isolation_level=None)
    connection.executescript(_SEED_SQL)
    connection.execute("PRAGMA foreign_keys = ON")  # re-enable after executescript
    yield connection
    connection.close()
