-- Unit-of-measurement catalog (weight, volume, count subtypes)
CREATE TABLE IF NOT EXISTS units (
    name       TEXT PRIMARY KEY,
    unit_group TEXT NOT NULL
);

-- Recipe category catalog
CREATE TABLE IF NOT EXISTS recipe_categories (
    name   TEXT PRIMARY KEY,
    active INTEGER NOT NULL DEFAULT 1
);

-- Product category catalog
CREATE TABLE IF NOT EXISTS product_categories (
    name   TEXT PRIMARY KEY,
    active INTEGER NOT NULL DEFAULT 1
);

-- Product / ingredient catalog
CREATE TABLE IF NOT EXISTS products (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT    NOT NULL,
    category                TEXT    NOT NULL REFERENCES product_categories(name),
    brand                   TEXT    NOT NULL DEFAULT '',
    recipe_unit             TEXT    NOT NULL REFERENCES units(name),
    purchase_unit           TEXT    NOT NULL REFERENCES units(name),
    price_per_purchase_unit REAL    NOT NULL DEFAULT 0,
    weight_per_piece_g      REAL,
    conversion_factor       REAL    NOT NULL DEFAULT 1.0
);

-- Recipe header
CREATE TABLE IF NOT EXISTS recipes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    category     TEXT    NOT NULL REFERENCES recipe_categories(name),
    dietary_tags TEXT    NOT NULL DEFAULT '[]',
    servings     INTEGER NOT NULL DEFAULT 1
);

-- Recipe ↔ product join (one row per ingredient per recipe)
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id  INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    amount     REAL    NOT NULL,
    unit       TEXT    NOT NULL REFERENCES units(name),
    PRIMARY KEY (recipe_id, product_id)
);

-- Ordered preparation steps
CREATE TABLE IF NOT EXISTS cooking_steps (
    recipe_id  INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    description TEXT   NOT NULL,
    PRIMARY KEY (recipe_id, step_order)
);

-- Family member profiles
CREATE TABLE IF NOT EXISTS family_members (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL,
    portion_multiplier   REAL    NOT NULL DEFAULT 1.0,
    dietary_restrictions TEXT    NOT NULL DEFAULT '',
    comment              TEXT    NOT NULL DEFAULT ''
);

-- Named weekly menus
CREATE TABLE IF NOT EXISTS menus (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- Menu grid: one row per (menu, day, meal_type) cell
CREATE TABLE IF NOT EXISTS menu_slots (
    menu_id          INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    day              INTEGER NOT NULL,
    meal_type        TEXT    NOT NULL,
    recipe_id        INTEGER NOT NULL REFERENCES recipes(id),
    servings_override REAL,
    PRIMARY KEY (menu_id, day, meal_type)
);
