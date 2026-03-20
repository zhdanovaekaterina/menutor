# Инфраструктурный слой — Репозитории, Аутентификация, База данных

**Расположение файла:** `backend/infrastructure/`

Инфраструктурный слой реализует порты домена. Содержит все код, специфичный для фреймворка: SQLAlchemy ORM, хеширование пароля bcrypt, генерация JWT токенов и file I/O.

---

## Паттерн репозиториев

Репозитории реализуют порт Repository (интерфейс) из домена. Они абстрагируют доступ к данным.

### ORM модели

**Файл:** `backend/infrastructure/database/models.py`

Модели SQLAlchemy маппируют в таблицы БД. Каждая модель имеет соответствующую доменную сущность.

```python
from sqlalchemy import ForeignKey, String, Integer, DateTime, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

# ─────── Пользователи ───────────────────────────────────────────

class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    recipes: Mapped[list["RecipeRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    products: Mapped[list["ProductRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    menus: Mapped[list["MenuRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    family_members: Mapped[list["FamilyMemberRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshTokenRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# ─────── Рецепты ──────────────────────────────────────────

class RecipeRow(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    servings: Mapped[int] = mapped_column(default=1)
    category_id: Mapped[int] = mapped_column(ForeignKey("recipe_categories.id"))
    weight: Mapped[int] = mapped_column(default=0)
    total_pieces: Mapped[int | None]
    pieces_per_portion: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    user: Mapped[UserRow] = relationship(back_populates="recipes")
    category: Mapped["RecipeCategoryRow"] = relationship(back_populates="recipes")
    ingredients: Mapped[list["RecipeIngredientRow"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    steps: Mapped[list["CookingStepRow"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")

# ─────── Ингредиенты рецепта ───────────────────────────────────────────

class RecipeIngredientRow(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    sub_recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"))
    quantity_amount: Mapped[float]
    quantity_unit: Mapped[str] = mapped_column(String(50))
    order: Mapped[int] = mapped_column(default=0)

    # Отношения
    recipe: Mapped[RecipeRow] = relationship(back_populates="ingredients", foreign_keys=[recipe_id])
    product: Mapped["ProductRow"] = relationship(back_populates="recipe_ingredients")
    sub_recipe: Mapped[RecipeRow] = relationship(foreign_keys=[sub_recipe_id])
```

### Реализация репозиториев

**Файл:** `backend/infrastructure/repositories/sqlalchemy_recipe_repository.py`

Каждый репозиторий реализует соответствующий порт.

```python
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.types import RecipeId, RecipeCategoryId, UserId

class SqlalchemyRecipeRepository(RecipeRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        """Получить рецепт по ID, ограниченный пользователем."""
        row = self.session.query(RecipeRow).filter(
            RecipeRow.id == int(recipe_id),
            RecipeRow.user_id == int(user_id),
        ).first()

        return recipe_row_to_domain(row) if row else None

    def list_by_user(self, user_id: UserId) -> list[Recipe]:
        """Вывести все рецепты пользователя."""
        rows = self.session.query(RecipeRow).filter(
            RecipeRow.user_id == int(user_id)
        ).order_by(RecipeRow.name).all()

        return [recipe_row_to_domain(row) for row in rows]

    def list_by_category(
        self, user_id: UserId, category_id: RecipeCategoryId
    ) -> list[Recipe]:
        """Вывести рецепты в категории."""
        rows = self.session.query(RecipeRow).filter(
            RecipeRow.user_id == int(user_id),
            RecipeRow.category_id == int(category_id),
        ).order_by(RecipeRow.name).all()

        return [recipe_row_to_domain(row) for row in rows]

    def save(self, recipe: Recipe) -> RecipeId:
        """Создать или обновить рецепт."""
        if int(recipe.id) == 0:
            # Вставить
            row = recipe_domain_to_row(recipe)
            self.session.add(row)
        else:
            # Обновить
            row = self.session.query(RecipeRow).filter(
                RecipeRow.id == int(recipe.id),
                RecipeRow.user_id == int(recipe.user_id),
            ).first()
            if not row:
                raise RepositoryError(f"Рецепт {recipe.id} не найден")

            # Обновить поля
            row.name = recipe.name
            row.servings = recipe.servings
            row.category_id = int(recipe.category_id)
            row.weight = recipe.weight
            row.total_pieces = recipe.total_pieces
            row.pieces_per_portion = recipe.pieces_per_portion
            row.updated_at = datetime.utcnow()

            # Обновить ингредиенты и шаги (каскадное удаление)
            self.session.query(RecipeIngredientRow).filter(
                RecipeIngredientRow.recipe_id == int(recipe.id)
            ).delete()
            self.session.query(CookingStepRow).filter(
                CookingStepRow.recipe_id == int(recipe.id)
            ).delete()

            # Переиспользовать
            for ing in recipe.ingredients:
                ing_row = RecipeIngredientRow(
                    recipe_id=int(recipe.id),
                    product_id=int(ing.product_id),
                    sub_recipe_id=int(ing.sub_recipe_id) if ing.sub_recipe_id else None,
                    quantity_amount=ing.quantity.amount,
                    quantity_unit=ing.quantity.unit,
                    order=ing.order,
                )
                row.ingredients.append(ing_row)

            for step in recipe.steps:
                step_row = CookingStepRow(
                    recipe_id=int(recipe.id),
                    description=step.description,
                    order=step.order,
                )
                row.steps.append(step_row)

        self.session.flush()  # Получить ID без коммита
        return RecipeId(row.id)

    def delete(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Мягкое или жесткое удаление рецепта."""
        row = self.session.query(RecipeRow).filter(
            RecipeRow.id == int(recipe_id),
            RecipeRow.user_id == int(user_id),
        ).first()

        if not row:
            raise RepositoryError(f"Рецепт {recipe_id} не найден")

        self.session.delete(row)
```

### Конвертеры (Row ↔ Domain)

**Файл:** `backend/infrastructure/repositories/mappers.py`

Преобразовать между ORM строками и доменными сущностями.

```python
def recipe_row_to_domain(row: RecipeRow) -> Recipe:
    """Маппировать SQLAlchemy RecipeRow в доменный Recipe."""
    ingredients = [
        RecipeIngredient(
            product_id=ProductId(ing_row.product_id),
            sub_recipe_id=RecipeId(ing_row.sub_recipe_id) if ing_row.sub_recipe_id else None,
            quantity=Quantity(ing_row.quantity_amount, ing_row.quantity_unit),
            order=ing_row.order,
        )
        for ing_row in row.ingredients
    ]

    steps = [
        CookingStep(
            description=step_row.description,
            order=step_row.order,
        )
        for step_row in row.steps
    ]

    return Recipe(
        id=RecipeId(row.id),
        name=row.name,
        servings=row.servings,
        ingredients=ingredients,
        steps=steps,
        category_id=RecipeCategoryId(row.category_id),
        weight=row.weight,
        user_id=UserId(row.user_id),
        total_pieces=row.total_pieces,
        pieces_per_portion=row.pieces_per_portion,
    )

def recipe_domain_to_row(recipe: Recipe) -> RecipeRow:
    """Маппировать доменный Recipe в SQLAlchemy RecipeRow."""
    return RecipeRow(
        id=int(recipe.id) if int(recipe.id) != 0 else None,
        name=recipe.name,
        servings=recipe.servings,
        category_id=int(recipe.category_id),
        weight=recipe.weight,
        user_id=int(recipe.user_id),
        total_pieces=recipe.total_pieces,
        pieces_per_portion=recipe.pieces_per_portion,
    )
```

---

## Сервисы аутентификации

### BcryptPasswordHasher

**Файл:** `backend/infrastructure/auth/bcrypt_password_hasher.py`

Реализует порт `PasswordHasher` из домена.

```python
import bcrypt
from backend.domain.services.password_hasher import PasswordHasher

class BcryptPasswordHasher(PasswordHasher):
    """Хешировать и проверять пароли используя bcrypt."""

    def hash_password(self, password: str) -> str:
        """Генерировать bcrypt хеш с солью."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hash: str) -> bool:
        """Проверить пароль против хеша."""
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))
```

**Пример:**
```python
hasher = BcryptPasswordHasher()
hash = hasher.hash_password("secret123")  # "$2b$12$..."
is_valid = hasher.verify_password("secret123", hash)  # True
is_invalid = hasher.verify_password("wrong", hash)  # False
```

### JwtTokenService

**Файл:** `backend/infrastructure/auth/jwt_token_service.py`

Реализует порт `TokenService` из домена. Создает и валидирует JWT.

```python
import os
from datetime import datetime, timedelta, UTC
import jwt
from backend.domain.services.token_service import TokenService
from backend.domain.exceptions import AuthenticationError
from backend.domain.value_objects.types import UserId

class JwtTokenService(TokenService):
    """Создать и валидировать JWT токены."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: UserId, expires_in_minutes: int = 30) -> str:
        """
        Создать короткоживущий токен доступа.

        Полезная нагрузка:
            user_id: ID пользователя
            exp: Время истечения
            type: "access"
            iat: Выданный в
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=expires_in_minutes)

        payload = {
            "user_id": int(user_id),
            "exp": expires_at,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, user_id: UserId, expires_in_days: int = 30) -> str:
        """Создать долгоживущий refresh токен."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=expires_in_days)

        payload = {
            "user_id": int(user_id),
            "exp": expires_at,
            "iat": now,
            "type": "refresh",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def validate_token(self, token: str) -> dict:
        """
        Валидировать JWT и вернуть полезную нагрузку.

        Выбрасывает:
            AuthenticationError: Неверный или истекший токен
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Токен истек")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Неверный токен: {e}")
```

**Пример:**
```python
service = JwtTokenService(secret_key="my-secret-key")

# Создать токены
access = service.create_access_token(UserId(1), expires_in_minutes=30)
refresh = service.create_refresh_token(UserId(1), expires_in_days=30)

# Валидировать
payload = service.validate_token(access)  # {"user_id": 1, "type": "access", ...}

# Истекший токен
old_token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
service.validate_token(old_token)  # Выбрасывает AuthenticationError
```

---

## Настройка БД

### SQLAlchemy engine & session

**Файл:** `backend/infrastructure/database/__init__.py`

```python
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

def get_engine(db_url: str | None = None) -> Engine:
    """
    Создать SQLAlchemy engine.

    По умолчанию SQLite в dev, принимает URL PostgreSQL.

    Примеры URL:
        sqlite:///./menutor.db          # SQLite на основе файла
        sqlite:///:memory:              # В памяти (для тестов)
        postgresql://user:pass@host/db  # PostgreSQL
    """
    url = db_url or os.environ.get("DATABASE_URL", "sqlite:///./menutor.db")

    if url.startswith("sqlite"):
        # Настройка специфичная для SQLite
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Для :memory:
            echo=False,
        )

        # Включить внешние ключи
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL
        engine = create_engine(url, echo=False)

    return engine

def get_session(engine: Engine) -> Session:
    """Создать SQLAlchemy сессию."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal()
```

### Миграции Alembic

**Файл:** `backend/infrastructure/database/migrations/env.py`

Конфигурация Alembic для автоматических обновлений схемы.

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.infrastructure.database.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Запустить миграции в режиме offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Запустить миграции в режиме online."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### Рабочий процесс миграций

```bash
# Автоопределение изменений
alembic revision --autogenerate -m "Добавить вес к рецептам"

# Применить миграции
alembic upgrade head

# Откатить
alembic downgrade -1
```

**Пример миграции:**

```python
# backend/infrastructure/database/migrations/versions/001_initial_schema.py

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('nickname', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_users_email', 'email'),
    )

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
    # ... еще таблицы

def downgrade() -> None:
    op.drop_table('recipes')
    op.drop_table('users')
    # ...
```

---

## Экспортеры (паттерн Strategy)

**Файл:** `backend/infrastructure/export/`

Взаимозаменяемые алгоритмы экспорта.

```python
from abc import ABC, abstractmethod
from backend.domain.entities.shopping_list import ShoppingList

class ShoppingListExporter(ABC):
    @abstractmethod
    def export(self, shopping_list: ShoppingList) -> str:
        pass

class CsvExporter(ShoppingListExporter):
    """Экспортировать список покупок как CSV."""

    def export(self, shopping_list: ShoppingList) -> str:
        lines = ["Продукт,Категория,Количество,Цена,Сумма"]

        current_category = None
        for item in shopping_list.items:
            if item.category_id != current_category:
                lines.append(f"\n{item.category_name},,,")
                current_category = item.category_id

            lines.append(
                f"{item.name},,{item.quantity.amount} {item.quantity.unit},"
                f"{item.price_per_unit.amount},{item.total_cost.amount}"
            )

        lines.append(f"\nИтого,,,{shopping_list.total_cost.amount}")
        return "\n".join(lines)

class JsonExporter(ShoppingListExporter):
    """Экспортировать список покупок как JSON."""

    def export(self, shopping_list: ShoppingList) -> str:
        data = {
            "items": [
                {
                    "product_id": int(item.product_id),
                    "name": item.name,
                    "quantity": {
                        "amount": item.quantity.amount,
                        "unit": item.quantity.unit,
                    },
                    "price_per_unit": float(item.price_per_unit.amount),
                    "total_cost": float(item.total_cost.amount),
                }
                for item in shopping_list.items
            ],
            "total_cost": float(shopping_list.total_cost.amount),
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
```

### Реестр экспортёров

```python
class ExporterRegistry:
    def __init__(self):
        self._exporters: dict[str, ShoppingListExporter] = {}

    def register(self, format_name: str, exporter: ShoppingListExporter) -> None:
        self._exporters[format_name] = exporter

    def get(self, format_name: str) -> ShoppingListExporter:
        if format_name not in self._exporters:
            raise ValueError(f"Неизвестный экспортёр: {format_name}")
        return self._exporters[format_name]

# Использование
registry = ExporterRegistry()
registry.register("csv", CsvExporter())
registry.register("json", JsonExporter())

csv_exporter = registry.get("csv")
csv_output = csv_exporter.export(shopping_list)
```

---

## Поддержка нескольких БД

### SQLite (разработка)

```
DATABASE_URL=sqlite:///./menutor.db
```

- На основе файла
- Не требует настройки сервера
- Хорошо для dev одного пользователя

### PostgreSQL (продакшен)

```
DATABASE_URL=postgresql://username:password@host:5432/menutor_db
```

- Многопользовательский, параллельный доступ
- Гарантии ACID
- Лучше для масштабирования

Обе работают идентично через слой SQLAlchemy. Изменения кода не требуются.

---

## Тестирование с БД в памяти

**Паттерн:** Используйте SQLite `:memory:` для быстрых тестов.

```python
# tests/conftest.py

@pytest.fixture
def db_session():
    """БД SQLite в памяти для тестов."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def recipe_repo(db_session):
    """Репозиторий рецептов с тестовой БД."""
    return SqlalchemyRecipeRepository(db_session)

def test_save_recipe(recipe_repo):
    recipe = Recipe(...)
    recipe_id = recipe_repo.save(recipe)
    assert recipe_id is not None

    loaded = recipe_repo.get_by_id(recipe_id, UserId(1))
    assert loaded.name == recipe.name
```

---

## Резюме

Инфраструктурный слой:
- **Реализует** все порты домена (репозитории, аутентификация, экспортеры)
- **Управляет** схемой БД через SQLAlchemy + Alembic
- **Обрабатывает** хеширование пароля и генерацию JWT
- **Поддерживает** несколько БД (SQLite, PostgreSQL)
- **Тестируемо** через внедрение зависимостей

Ключевые паттерны:
- **Repository:** Абстрактный доступ к данным
- **ORM маппер:** Преобразование строк ↔ доменные сущности
- **Strategy:** Взаимозаменяемые экспортеры
- **Service:** Логика без состояния для аутентификации

---

**Далее:** См. [backend-api.md](06-backend-api.md) для деталей HTTP слоя.
