# Database Schema and Alembic Migrations

---

## Schema Overview

Menu Planner uses SQLAlchemy ORM with Alembic for schema versioning. The schema supports multi-tenancy (user scoping) and complex relationships (recipes → ingredients → products).

### Table Relationships

```
┌─────────────┐
│   users     │ (id, email, nickname, password_hash)
└──────┬──────┘
       │
       ├──→ recipes (user_id FK)
       │       └──→ recipe_ingredients (recipe_id FK, product_id FK, sub_recipe_id FK)
       │       └──→ cooking_steps (recipe_id FK)
       │       └──→ recipe_categories (category_id FK)
       │
       ├──→ products (user_id FK)
       │       ├──→ product_categories (category_id FK)
       │       └──→ recipe_ingredients (product_id FK)
       │
       ├──→ menus (user_id FK)
       │       └──→ menu_slots (menu_id FK, recipe_id FK, product_id FK)
       │
       ├──→ family_members (user_id FK)
       │
       └──→ refresh_tokens (user_id FK)
```

---

## Complete Table Definitions

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    nickname VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_users_email ON users(email);
```

**Columns:**
- `id` — Primary key
- `email` — Unique email address
- `nickname` — Display name
- `password_hash` — bcrypt hash (never plaintext)
- `created_at` — Account creation timestamp

---

### Refresh Tokens Table

```sql
CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN NOT NULL DEFAULT 0,

    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

**Purpose:** Store refresh token hashes for token rotation and revocation.

---

### Recipe Categories Table

```sql
CREATE TABLE recipe_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX ix_recipe_categories_name ON recipe_categories(name);
```

**Columns:**
- `id` — Primary key
- `name` — Category name (e.g., "Завтраки", "Обеды")
- `active` — Soft delete flag

**Seed data:**
```python
INSERT INTO recipe_categories (name, active) VALUES
  ('Завтраки', 1),
  ('Обеды', 1),
  ('Ужины', 1),
  ('Закуски', 1);
```

---

### Recipes Table

```sql
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    servings INTEGER NOT NULL DEFAULT 1,
    category_id INTEGER NOT NULL,
    weight INTEGER NOT NULL DEFAULT 0,
    total_pieces INTEGER,
    pieces_per_portion INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES recipe_categories(id)
);

CREATE INDEX ix_recipes_user_id ON recipes(user_id);
CREATE INDEX ix_recipes_name ON recipes(name);
CREATE INDEX ix_recipes_category_id ON recipes(category_id);
```

**Columns:**
- `id` — Primary key
- `user_id` — Owner (multi-tenancy scoping)
- `name` — Recipe name
- `servings` — Base portion size
- `category_id` — Recipe category FK
- `weight` — Finished dish weight in grams (optional)
- `total_pieces` — Total pieces if pieces-based (e.g., 12 cookies)
- `pieces_per_portion` — Pieces per serving if pieces-based (e.g., 3)
- `created_at`, `updated_at` — Timestamps

**Constraints:**
- User scoping: all queries filter by `user_id`
- If `total_pieces` is set, `pieces_per_portion` must also be set

---

### Recipe Ingredients Table

```sql
CREATE TABLE recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    product_id INTEGER,
    sub_recipe_id INTEGER,
    quantity_amount FLOAT NOT NULL,
    quantity_unit VARCHAR(50) NOT NULL,
    order INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY(sub_recipe_id) REFERENCES recipes(id) ON DELETE SET NULL
);

CREATE INDEX ix_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX ix_recipe_ingredients_product_id ON recipe_ingredients(product_id);
```

**Columns:**
- `id` — Primary key
- `recipe_id` — Parent recipe FK
- `product_id` — Product (if ingredient is a product)
- `sub_recipe_id` — Sub-recipe (if ingredient is a recipe)
- `quantity_amount` — Amount needed
- `quantity_unit` — Unit of measurement ("g", "kg", "ml", "l", "pcs", "tsp", "tbsp")
- `order` — Position in ingredient list

**Constraints:**
- Exactly one of `product_id` or `sub_recipe_id` is set (XOR)
- Detects circular dependencies at application layer

---

### Cooking Steps Table

```sql
CREATE TABLE cooking_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    description VARCHAR(1000) NOT NULL,
    order INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE INDEX ix_cooking_steps_recipe_id ON cooking_steps(recipe_id);
```

---

### Product Categories Table

```sql
CREATE TABLE product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX ix_product_categories_name ON product_categories(name);
```

**Seed data:**
```python
INSERT INTO product_categories (name, active) VALUES
  ('Сыпучие', 1),
  ('Молочные', 1),
  ('Овощи', 1),
  ('Фрукты', 1),
  ('Мясо', 1),
  ('Рыба', 1);
```

---

### Products Table

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL,
    recipe_unit VARCHAR(50) NOT NULL,
    purchase_unit VARCHAR(50) NOT NULL,
    price_per_purchase_unit DECIMAL(10, 2) NOT NULL,
    conversion_factor FLOAT NOT NULL DEFAULT 1.0,
    brand VARCHAR(255) DEFAULT '',
    supplier VARCHAR(255) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES product_categories(id)
);

CREATE INDEX ix_products_user_id ON products(user_id);
CREATE INDEX ix_products_name ON products(name);
CREATE INDEX ix_products_category_id ON products(category_id);
```

**Columns:**
- `id` — Primary key
- `user_id` — Owner (multi-tenancy)
- `name` — Product name (e.g., "Мука пшеничная")
- `category_id` — Category FK
- `recipe_unit` — Unit used in recipes (e.g., "g", "ml")
- `purchase_unit` — Unit for buying (e.g., "kg", "l")
- `price_per_purchase_unit` — Price per purchase unit (RUB)
- `conversion_factor` — Multiplier to convert recipe_unit → purchase_unit (e.g., 1000 for g→kg)
- `brand` — Optional brand name
- `supplier` — Optional typical retailer

**Example:**
```
name: "Мука пшеничная"
recipe_unit: "g"
purchase_unit: "kg"
price_per_purchase_unit: 80.00
conversion_factor: 1000
# Cost for 200g = (200 / 1000) * 80.00 = 16.00 RUB
```

---

### Menus Table

```sql
CREATE TABLE menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_menus_user_id ON menus(user_id);
```

---

### Menu Slots Table

```sql
CREATE TABLE menu_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL,
    recipe_id INTEGER,
    product_id INTEGER,
    quantity_amount FLOAT,
    quantity_unit VARCHAR(50),
    servings INTEGER,
    meal_type VARCHAR(50) NOT NULL DEFAULT 'обед',
    day_of_week INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY(menu_id) REFERENCES menus(id) ON DELETE CASCADE,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE SET NULL,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE INDEX ix_menu_slots_menu_id ON menu_slots(menu_id);
CREATE INDEX ix_menu_slots_recipe_id ON menu_slots(recipe_id);
```

**Columns:**
- `id` — Primary key
- `menu_id` — Parent menu FK
- `recipe_id` — Recipe (if slot contains recipe)
- `product_id` — Product (if slot contains product)
- `quantity_amount`, `quantity_unit` — Quantity for products
- `servings` — Number of servings for recipes
- `meal_type` — "завтрак", "обед", "ужин"
- `day_of_week` — 0=Monday, ..., 6=Sunday
- `position` — Ordering within same (day, meal_type)

---

### Family Members Table

```sql
CREATE TABLE family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    portion_multiplier FLOAT NOT NULL DEFAULT 1.0,
    dietary_restrictions VARCHAR(1000) DEFAULT '',
    comment VARCHAR(1000) DEFAULT '',

    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_family_members_user_id ON family_members(user_id);
```

**Columns:**
- `id` — Primary key
- `user_id` — Owner (multi-tenancy)
- `name` — Family member name
- `portion_multiplier` — 1.0 = adult, 0.5 = child, 1.5 = large adult
- `dietary_restrictions` — Free-form text (e.g., "vegetarian, nut allergy")
- `comment` — Additional notes

---

## Alembic Migrations

### Setup

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic/env.py:
# - Add sys.path to include project root
# - Set target_metadata = Base.metadata
```

### Creating Migrations

**Auto-generate:**
```bash
alembic revision --autogenerate -m "Add weight to recipes"
```

This creates a timestamped file like `alembic/versions/001_add_weight_to_recipes.py`:

```python
def upgrade() -> None:
    op.add_column('recipes', sa.Column('weight', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('recipes', 'weight')
```

**Manual migration:**
```python
def upgrade() -> None:
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['recipe_categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_recipes_user_id', 'user_id'),
    )

def downgrade() -> None:
    op.drop_table('recipes')
```

### Applying Migrations

```bash
# Show current version
alembic current

# Show all revisions
alembic history

# Apply all pending migrations
alembic upgrade head

# Apply N migrations
alembic upgrade +2

# Downgrade one migration
alembic downgrade -1

# Jump to specific version
alembic upgrade 1feb6df
```

---

## Seed Data

**File:** `backend/infrastructure/database/seed_defaults.py`

```python
from backend.infrastructure.database.models import Base, RecipeCategoryRow, ProductCategoryRow
from sqlalchemy import insert

def seed_defaults():
    """Insert default categories on first run."""
    from backend.infrastructure.database import get_engine, get_session

    engine = get_engine()
    session = get_session(engine)

    try:
        # Check if already seeded
        if session.query(RecipeCategoryRow).count() > 0:
            return

        # Insert recipe categories
        session.execute(insert(RecipeCategoryRow).values([
            {"name": "Завтраки", "active": True},
            {"name": "Обеды", "active": True},
            {"name": "Ужины", "active": True},
            {"name": "Закуски", "active": True},
        ]))

        # Insert product categories
        session.execute(insert(ProductCategoryRow).values([
            {"name": "Сыпучие", "active": True},
            {"name": "Молочные", "active": True},
            {"name": "Овощи", "active": True},
            {"name": "Фрукты", "active": True},
            {"name": "Мясо", "active": True},
            {"name": "Рыба", "active": True},
        ]))

        session.commit()
    finally:
        session.close()
```

Call on startup:
```python
# backend/composition/_infrastructure.py
from backend.infrastructure.database.seed_defaults import seed_defaults

def _create_infrastructure(db_url: str | None = None) -> Infrastructure:
    engine = get_engine(db_url)
    session = get_session(engine)
    seed_defaults()  # ← Idempotent, runs once
    return Infrastructure(engine=engine, session=session, ...)
```

---

## SQLite vs PostgreSQL

### Development (SQLite)

```
DATABASE_URL=sqlite:///./menutor.db
```

**Advantages:**
- No server setup
- Single file
- Good for solo dev
- Fast enough for MVP

**Limitations:**
- Single writer (no concurrency)
- Limited to one machine

**Setup:**
```python
from sqlalchemy import event, create_engine

engine = create_engine("sqlite:///./menutor.db")

# Enable foreign keys
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Production (PostgreSQL)

```
DATABASE_URL=postgresql://user:password@host:5432/menutor_db
```

**Advantages:**
- Multi-user, concurrent access
- ACID guarantees
- Replication, backups
- Enterprise ready

**Setup:**
```bash
# Create database
createdb menutor_db

# Run migrations
PGPASSWORD=password psql -h localhost -U user menutor_db < schema.sql

# Or with Alembic
alembic upgrade head
```

**Connection string:**
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/menutor_db"
```

**No code changes needed** — SQLAlchemy handles both seamlessly.

---

## Indexes

Strategic indexes for common queries:

| Table | Column(s) | Purpose |
|-------|-----------|---------|
| `users` | `email` | Login lookup |
| `recipes` | `user_id` | List user's recipes |
| `recipes` | `name` | Search recipes |
| `products` | `user_id` | List user's products |
| `products` | `name` | Search products |
| `recipe_ingredients` | `recipe_id` | Fetch ingredients |
| `menu_slots` | `menu_id` | Fetch slots |
| `family_members` | `user_id` | List family members |
| `refresh_tokens` | `user_id` | Find user's tokens |

```sql
-- Query optimization example
EXPLAIN QUERY PLAN
SELECT * FROM recipes WHERE user_id = 1 AND name LIKE '%блины%';

-- Should show: SEARCH recipes USING INDEX ix_recipes_user_id
```

---

## Constraints & Integrity

### Foreign Key Constraints

```sql
-- Cascade delete: removing user deletes all their recipes
FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE

-- Set null: removing category doesn't delete recipes
FOREIGN KEY(category_id) REFERENCES recipe_categories(id) ON DELETE RESTRICT
```

### Unique Constraints

```sql
-- Email must be unique
CREATE UNIQUE INDEX ix_users_email ON users(email);

-- Token hashes must be unique
CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

### Check Constraints

```sql
-- Enforced at application layer (SQLAlchemy validation)
-- Example: servings >= 1
-- Example: total_pieces >= pieces_per_portion
```

---

## Backup & Recovery

### SQLite Backup

```bash
# Simple file copy
cp menutor.db menutor.db.backup

# Or use sqlite3 CLI
sqlite3 menutor.db ".backup '/path/to/menutor.db.backup'"

# Restore
sqlite3 menutor.db ".restore '/path/to/menutor.db.backup'"
```

### PostgreSQL Backup

```bash
# Full backup
pg_dump -U user -h localhost menutor_db > menutor_backup.sql

# Restore
psql -U user -h localhost menutor_db < menutor_backup.sql

# Binary backup (faster)
pg_dump -U user -h localhost -Fc menutor_db > menutor_backup.dump
pg_restore -U user -h localhost menutor_db < menutor_backup.dump
```

---

## Summary

**Database architecture:**
- **Multi-tenancy:** All data scoped by `user_id`
- **Relationships:** Recipes → Ingredients → Products, Menus → Slots
- **Nested recipes:** Sub-recipe IDs in ingredient table
- **Type safety:** Quantity amounts + units stored separately
- **Soft deletes:** Categories have `active` flag

**Migrations:**
- **Alembic:** Version-controlled schema changes
- **Auto-generate:** `alembic revision --autogenerate`
- **Idempotent:** Safe to run multiple times
- **Reversible:** Downgrade with `alembic downgrade`

**Data integrity:**
- **Foreign keys:** Enforced cascade delete
- **Indexes:** Strategic on `user_id`, names, FKs
- **Constraints:** Unique emails, XOR ingredient types

---

**Complete technical documentation is now ready.**

All 9 documents provide comprehensive coverage of the Menu Planner architecture, from high-level overview to low-level database schema.
