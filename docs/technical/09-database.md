# Схема базы данных и миграции Alembic

---

## Обзор схемы

Menu Planner использует SQLAlchemy ORM с Alembic для управления версиями схемы. Схема поддерживает мульти-тенантность (scoping по пользователю) и сложные отношения (рецепты → ингредиенты → продукты).

### Отношения таблиц

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

## Полные определения таблиц

### Таблица Users

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

**Колонки:**
- `id` — Primary key
- `email` — Уникальный email адрес
- `nickname` — Отображаемое имя
- `password_hash` — bcrypt хеш (никогда открытый текст)
- `created_at` — Временная метка создания аккаунта

---

### Таблица Refresh Tokens

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

**Назначение:** Хранить хеши refresh токенов для ротации и отзыва токенов.

---

### Таблица Recipe Categories

```sql
CREATE TABLE recipe_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX ix_recipe_categories_name ON recipe_categories(name);
```

**Колонки:**
- `id` — Primary key
- `name` — Имя категории (например, "Завтраки", "Обеды")
- `active` — Флаг мягкого удаления

**Seed данные:**
```python
INSERT INTO recipe_categories (name, active) VALUES
  ('Завтраки', 1),
  ('Обеды', 1),
  ('Ужины', 1),
  ('Закуски', 1);
```

---

### Таблица Recipes

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

**Колонки:**
- `id` — Primary key
- `user_id` — Владелец (scoping мульти-тенантности)
- `name` — Название рецепта
- `servings` — Базовый размер порции
- `category_id` — FK категории рецепта
- `weight` — Вес готового блюда в граммах (опционально)
- `total_pieces` — Общее количество штук если штучный режим (например, 12 печенье)
- `pieces_per_portion` — Штук на одну порцию если штучный режим (например, 3)
- `created_at`, `updated_at` — Временные метки

**Ограничения:**
- Scoping пользователя: все запросы фильтруют по `user_id`
- Если `total_pieces` установлено, `pieces_per_portion` также должно быть установлено

---

### Таблица Recipe Ingredients

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

**Колонки:**
- `id` — Primary key
- `recipe_id` — FK родительского рецепта
- `product_id` — Продукт (если ингредиент это продукт)
- `sub_recipe_id` — Под-рецепт (если ингредиент это рецепт)
- `quantity_amount` — Необходимое количество
- `quantity_unit` — Единица измерения ("g", "kg", "ml", "l", "pcs", "tsp", "tbsp")
- `order` — Позиция в списке ингредиентов

**Ограничения:**
- Ровно один из `product_id` или `sub_recipe_id` установлен (XOR)
- Обнаружение циклических зависимостей на уровне приложения

---

### Таблица Cooking Steps

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

### Таблица Product Categories

```sql
CREATE TABLE product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX ix_product_categories_name ON product_categories(name);
```

**Seed данные:**
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

### Таблица Products

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

**Колонки:**
- `id` — Primary key
- `user_id` — Владелец (мульти-тенантность)
- `name` — Название продукта (например, "Мука пшеничная")
- `category_id` — FK категории
- `recipe_unit` — Единица используемая в рецептах (например, "g", "ml")
- `purchase_unit` — Единица для покупки (например, "kg", "l")
- `price_per_purchase_unit` — Цена за единицу покупки (RUB)
- `conversion_factor` — Множитель для преобразования recipe_unit → purchase_unit (например, 1000 для g→kg)
- `brand` — Опциональное имя бренда
- `supplier` — Опциональный обычный розничный торговец

**Пример:**
```
name: "Мука пшеничная"
recipe_unit: "g"
purchase_unit: "kg"
price_per_purchase_unit: 80.00
conversion_factor: 1000
# Стоимость для 200g = (200 / 1000) * 80.00 = 16.00 RUB
```

---

### Таблица Menus

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

### Таблица Menu Slots

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

**Колонки:**
- `id` — Primary key
- `menu_id` — FK родительского меню
- `recipe_id` — Рецепт (если слот содержит рецепт)
- `product_id` — Продукт (если слот содержит продукт)
- `quantity_amount`, `quantity_unit` — Количество для продуктов
- `servings` — Количество порций для рецептов
- `meal_type` — "завтрак", "обед", "ужин"
- `day_of_week` — 0=Понедельник, ..., 6=Воскресенье
- `position` — Упорядочение в одном дне и типе приема пищи

---

### Таблица Family Members

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

**Колонки:**
- `id` — Primary key
- `user_id` — Владелец (мульти-тенантность)
- `name` — Имя члена семьи
- `portion_multiplier` — 1.0 = взрослый, 0.5 = ребенок, 1.5 = крупный взрослый
- `dietary_restrictions` — Свободный текст (например, "вегетарианец, аллергия на орехи")
- `comment` — Дополнительные заметки

---

## Миграции Alembic

### Настройка

```bash
# Инициализировать Alembic
alembic init alembic

# Отредактировать alembic/env.py:
# - Добавить sys.path для включения корня проекта
# - Установить target_metadata = Base.metadata
```

### Создание миграций

**Автоматическая генерация:**
```bash
alembic revision --autogenerate -m "Add weight to recipes"
```

Это создает файл с временной меткой как `alembic/versions/001_add_weight_to_recipes.py`:

```python
def upgrade() -> None:
    op.add_column('recipes', sa.Column('weight', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    op.drop_column('recipes', 'weight')
```

**Ручная миграция:**
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

### Применение миграций

```bash
# Показать текущую версию
alembic current

# Показать все ревизии
alembic history

# Применить все отложенные миграции
alembic upgrade head

# Применить N миграций
alembic upgrade +2

# Откатить одну миграцию
alembic downgrade -1

# Перейти к конкретной версии
alembic upgrade 1feb6df
```

---

## Seed данные

**Файл:** `backend/infrastructure/database/seed_defaults.py`

```python
from backend.infrastructure.database.models import Base, RecipeCategoryRow, ProductCategoryRow
from sqlalchemy import insert

def seed_defaults():
    """Вставить категории по умолчанию при первом запуске."""
    from backend.infrastructure.database import get_engine, get_session

    engine = get_engine()
    session = get_session(engine)

    try:
        # Проверить если уже seeded
        if session.query(RecipeCategoryRow).count() > 0:
            return

        # Вставить категории рецептов
        session.execute(insert(RecipeCategoryRow).values([
            {"name": "Завтраки", "active": True},
            {"name": "Обеды", "active": True},
            {"name": "Ужины", "active": True},
            {"name": "Закуски", "active": True},
        ]))

        # Вставить категории продуктов
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

Вызвать при запуске:
```python
# backend/composition/_infrastructure.py
from backend.infrastructure.database.seed_defaults import seed_defaults

def _create_infrastructure(db_url: str | None = None) -> Infrastructure:
    engine = get_engine(db_url)
    session = get_session(engine)
    seed_defaults()  # ← Идемпотентный, запускается один раз
    return Infrastructure(engine=engine, session=session, ...)
```

---

## SQLite vs PostgreSQL

### Разработка (SQLite)

```
DATABASE_URL=sqlite:///./menutor.db
```

**Преимущества:**
- Без настройки сервера
- Один файл
- Хорошо для одиночной разработки
- Достаточно быстро для MVP

**Ограничения:**
- Один писатель (нет параллелизма)
- Ограничено одной машиной

**Настройка:**
```python
from sqlalchemy import event, create_engine

engine = create_engine("sqlite:///./menutor.db")

# Включить внешние ключи
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Производство (PostgreSQL)

```
DATABASE_URL=postgresql://user:password@host:5432/menutor_db
```

**Преимущества:**
- Многопользовательский доступ с параллелизмом
- Гарантии ACID
- Репликация, резервные копии
- Enterprise ready

**Настройка:**
```bash
# Создать базу данных
createdb menutor_db

# Запустить миграции
PGPASSWORD=password psql -h localhost -U user menutor_db < schema.sql

# Или с Alembic
alembic upgrade head
```

**Строка подключения:**
```python
DATABASE_URL = "postgresql://user:password@localhost:5432/menutor_db"
```

**Изменения кода не требуются** — SQLAlchemy обрабатывает обе базы без изменений.

---

## Индексы

Стратегические индексы для обычных запросов:

| Таблица | Колонка(и) | Назначение |
|-------|-----------|---------|
| `users` | `email` | Поиск при логине |
| `recipes` | `user_id` | Список рецептов пользователя |
| `recipes` | `name` | Поиск рецептов |
| `products` | `user_id` | Список продуктов пользователя |
| `products` | `name` | Поиск продуктов |
| `recipe_ingredients` | `recipe_id` | Получить ингредиенты |
| `menu_slots` | `menu_id` | Получить слоты |
| `family_members` | `user_id` | Список членов семьи |
| `refresh_tokens` | `user_id` | Найти токены пользователя |

```sql
-- Пример оптимизации запроса
EXPLAIN QUERY PLAN
SELECT * FROM recipes WHERE user_id = 1 AND name LIKE '%блины%';

-- Должно показать: SEARCH recipes USING INDEX ix_recipes_user_id
```

---

## Ограничения и целостность

### Ограничения внешних ключей

```sql
-- Cascade delete: удаление пользователя удаляет все их рецепты
FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE

-- Set null: удаление категории не удаляет рецепты
FOREIGN KEY(category_id) REFERENCES recipe_categories(id) ON DELETE RESTRICT
```

### Уникальные ограничения

```sql
-- Email должен быть уникальным
CREATE UNIQUE INDEX ix_users_email ON users(email);

-- Хеши токенов должны быть уникальными
CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

### Check ограничения

```sql
-- Проверяется на уровне приложения (валидация SQLAlchemy)
-- Пример: servings >= 1
-- Пример: total_pieces >= pieces_per_portion
```

---

## Резервная копия и восстановление

### Резервная копия SQLite

```bash
# Простое копирование файла
cp menutor.db menutor.db.backup

# Или используя sqlite3 CLI
sqlite3 menutor.db ".backup '/path/to/menutor.db.backup'"

# Восстановление
sqlite3 menutor.db ".restore '/path/to/menutor.db.backup'"
```

### Резервная копия PostgreSQL

```bash
# Полная резервная копия
pg_dump -U user -h localhost menutor_db > menutor_backup.sql

# Восстановление
psql -U user -h localhost menutor_db < menutor_backup.sql

# Бинарная резервная копия (быстрее)
pg_dump -U user -h localhost -Fc menutor_db > menutor_backup.dump
pg_restore -U user -h localhost menutor_db < menutor_backup.dump
```

---

## Резюме

**Архитектура базы данных:**
- **Мульти-тенантность:** Все данные scoped по `user_id`
- **Отношения:** Рецепты → Ингредиенты → Продукты, Меню → Слоты
- **Вложенные рецепты:** Sub-recipe IDs в таблице ингредиентов
- **Type safety:** Количество и единицы хранятся отдельно
- **Мягкие удаления:** Категории имеют флаг `active`

**Миграции:**
- **Alembic:** Версионированные изменения схемы
- **Автоматическая генерация:** `alembic revision --autogenerate`
- **Идемпотентные:** Безопасно запускать несколько раз
- **Reversible:** Откатить с `alembic downgrade`

**Целостность данных:**
- **Внешние ключи:** Enforced cascade delete
- **Индексы:** Стратегические по `user_id`, именам, FKs
- **Ограничения:** Уникальные emails, XOR типы ингредиентов

---

**Полная техническая документация теперь готова.**

Все 9 документов обеспечивают всестороннее покрытие архитектуры Menu Planner, от высокоуровневого обзора до низкоуровневой схемы базы данных.
