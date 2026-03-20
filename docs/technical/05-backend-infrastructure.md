# Infrastructure Layer — Repositories, Auth, Database

**File location:** `backend/infrastructure/`

The Infrastructure layer implements Domain ports (abstractions). It contains all framework-specific code: SQLAlchemy ORM, bcrypt password hashing, JWT token generation, and file I/O.

---

## Repository Pattern

Repositories implement the Repository port (interface) from Domain. They abstract data access.

### ORM Models

**File:** `backend/infrastructure/database/models.py`

SQLAlchemy models map to database tables. Each model has a corresponding domain entity.

```python
from sqlalchemy import ForeignKey, String, Integer, DateTime, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

# ─────── Users ───────────────────────────────────────────

class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    recipes: Mapped[list["RecipeRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    products: Mapped[list["ProductRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    menus: Mapped[list["MenuRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    family_members: Mapped[list["FamilyMemberRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshTokenRow"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# ─────── Recipes ──────────────────────────────────────────

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

    # Relationships
    user: Mapped[UserRow] = relationship(back_populates="recipes")
    category: Mapped["RecipeCategoryRow"] = relationship(back_populates="recipes")
    ingredients: Mapped[list["RecipeIngredientRow"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    steps: Mapped[list["CookingStepRow"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")

# ─────── Recipe Ingredients ───────────────────────────────

class RecipeIngredientRow(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    sub_recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"))
    quantity_amount: Mapped[float]
    quantity_unit: Mapped[str] = mapped_column(String(50))
    order: Mapped[int] = mapped_column(default=0)

    # Relationships
    recipe: Mapped[RecipeRow] = relationship(back_populates="ingredients", foreign_keys=[recipe_id])
    product: Mapped["ProductRow"] = relationship(back_populates="recipe_ingredients")
    sub_recipe: Mapped[RecipeRow] = relationship(foreign_keys=[sub_recipe_id])

# ─────── Cooking Steps ────────────────────────────────────

class CookingStepRow(Base):
    __tablename__ = "cooking_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    description: Mapped[str] = mapped_column(String(1000))
    order: Mapped[int] = mapped_column(default=0)

    recipe: Mapped[RecipeRow] = relationship(back_populates="steps")

# ─────── Products ──────────────────────────────────────────

class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_categories.id"))
    recipe_unit: Mapped[str] = mapped_column(String(50))
    purchase_unit: Mapped[str] = mapped_column(String(50))
    price_per_purchase_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    conversion_factor: Mapped[float] = mapped_column(default=1.0)
    brand: Mapped[str] = mapped_column(String(255), default="")
    supplier: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped[UserRow] = relationship(back_populates="products")
    category: Mapped["ProductCategoryRow"] = relationship(back_populates="products")
    recipe_ingredients: Mapped[list["RecipeIngredientRow"]] = relationship(back_populates="product")

# ─────── Menus & Slots ────────────────────────────────────

class MenuRow(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[UserRow] = relationship(back_populates="menus")
    slots: Mapped[list["MenuSlotRow"]] = relationship(back_populates="menu", cascade="all, delete-orphan")

class MenuSlotRow(Base):
    __tablename__ = "menu_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id"), index=True)
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    quantity_amount: Mapped[float | None]
    quantity_unit: Mapped[str | None] = mapped_column(String(50))
    servings: Mapped[int | None]
    meal_type: Mapped[str] = mapped_column(String(50), default="обед")
    day_of_week: Mapped[int] = mapped_column(default=0)  # 0=Mon, 6=Sun
    position: Mapped[int] = mapped_column(default=0)

    menu: Mapped[MenuRow] = relationship(back_populates="slots")
    recipe: Mapped[RecipeRow | None] = relationship(foreign_keys=[recipe_id])
    product: Mapped[ProductRow | None] = relationship(foreign_keys=[product_id])
```

### Repository Implementation

**File:** `backend/infrastructure/repositories/sqlalchemy_recipe_repository.py`

Each repository implements its corresponding port.

```python
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.types import RecipeId, RecipeCategoryId, UserId

class SqlalchemyRecipeRepository(RecipeRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, recipe_id: RecipeId, user_id: UserId) -> Recipe | None:
        """Fetch recipe by ID, scoped to user."""
        row = self.session.query(RecipeRow).filter(
            RecipeRow.id == int(recipe_id),
            RecipeRow.user_id == int(user_id),
        ).first()

        return recipe_row_to_domain(row) if row else None

    def list_by_user(self, user_id: UserId) -> list[Recipe]:
        """List all user's recipes."""
        rows = self.session.query(RecipeRow).filter(
            RecipeRow.user_id == int(user_id)
        ).order_by(RecipeRow.name).all()

        return [recipe_row_to_domain(row) for row in rows]

    def list_by_category(
        self, user_id: UserId, category_id: RecipeCategoryId
    ) -> list[Recipe]:
        """List recipes in category."""
        rows = self.session.query(RecipeRow).filter(
            RecipeRow.user_id == int(user_id),
            RecipeRow.category_id == int(category_id),
        ).order_by(RecipeRow.name).all()

        return [recipe_row_to_domain(row) for row in rows]

    def save(self, recipe: Recipe) -> RecipeId:
        """Create or update recipe."""
        if int(recipe.id) == 0:
            # Insert
            row = recipe_domain_to_row(recipe)
            self.session.add(row)
        else:
            # Update
            row = self.session.query(RecipeRow).filter(
                RecipeRow.id == int(recipe.id),
                RecipeRow.user_id == int(recipe.user_id),
            ).first()
            if not row:
                raise RepositoryError(f"Recipe {recipe.id} not found")

            # Update fields
            row.name = recipe.name
            row.servings = recipe.servings
            row.category_id = int(recipe.category_id)
            row.weight = recipe.weight
            row.total_pieces = recipe.total_pieces
            row.pieces_per_portion = recipe.pieces_per_portion
            row.updated_at = datetime.utcnow()

            # Update ingredients and steps (cascade delete)
            self.session.query(RecipeIngredientRow).filter(
                RecipeIngredientRow.recipe_id == int(recipe.id)
            ).delete()
            self.session.query(CookingStepRow).filter(
                CookingStepRow.recipe_id == int(recipe.id)
            ).delete()

            # Re-add
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

        self.session.flush()  # Get ID without commit
        return RecipeId(row.id)

    def delete(self, recipe_id: RecipeId, user_id: UserId) -> None:
        """Soft or hard delete recipe."""
        row = self.session.query(RecipeRow).filter(
            RecipeRow.id == int(recipe_id),
            RecipeRow.user_id == int(user_id),
        ).first()

        if not row:
            raise RepositoryError(f"Recipe {recipe_id} not found")

        self.session.delete(row)
```

### Converters (Row ↔ Domain)

**File:** `backend/infrastructure/repositories/mappers.py`

Convert between ORM rows and domain entities.

```python
def recipe_row_to_domain(row: RecipeRow) -> Recipe:
    """Map SQLAlchemy RecipeRow to domain Recipe."""
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
    """Map domain Recipe to SQLAlchemy RecipeRow."""
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

## Authentication Services

### BcryptPasswordHasher

**File:** `backend/infrastructure/auth/bcrypt_password_hasher.py`

Implements `PasswordHasher` port from domain.

```python
import bcrypt
from backend.domain.services.password_hasher import PasswordHasher

class BcryptPasswordHasher(PasswordHasher):
    """Hash and verify passwords using bcrypt."""

    def hash_password(self, password: str) -> str:
        """Generate bcrypt hash with salt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))
```

**Example:**
```python
hasher = BcryptPasswordHasher()
hash = hasher.hash_password("secret123")  # "$2b$12$..."
is_valid = hasher.verify_password("secret123", hash)  # True
is_invalid = hasher.verify_password("wrong", hash)  # False
```

### JwtTokenService

**File:** `backend/infrastructure/auth/jwt_token_service.py`

Implements `TokenService` port from domain. Creates and validates JWTs.

```python
import os
from datetime import datetime, timedelta, UTC
import jwt
from backend.domain.services.token_service import TokenService
from backend.domain.exceptions import AuthenticationError
from backend.domain.value_objects.types import UserId

class JwtTokenService(TokenService):
    """Create and validate JWT tokens."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, user_id: UserId, expires_in_minutes: int = 30) -> str:
        """
        Create short-lived access token.

        Payload:
            user_id: User ID
            exp: Expiration time
            type: "access"
            iat: Issued at
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
        """Create long-lived refresh token."""
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
        Validate JWT and return payload.

        Raises:
            AuthenticationError: Invalid or expired token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")
```

**Example:**
```python
service = JwtTokenService(secret_key="my-secret-key")

# Create tokens
access = service.create_access_token(UserId(1), expires_in_minutes=30)
refresh = service.create_refresh_token(UserId(1), expires_in_days=30)

# Validate
payload = service.validate_token(access)  # {"user_id": 1, "type": "access", ...}

# Expired token
old_token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
service.validate_token(old_token)  # Raises AuthenticationError
```

---

## Database Setup

### SQLAlchemy Engine & Session

**File:** `backend/infrastructure/database/__init__.py`

```python
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

def get_engine(db_url: str | None = None) -> Engine:
    """
    Create SQLAlchemy engine.

    Defaults to SQLite in dev, accepts PostgreSQL URL.

    Example URLs:
        sqlite:///./menutor.db          # File-based SQLite
        sqlite:///:memory:              # In-memory (for tests)
        postgresql://user:pass@host/db  # PostgreSQL
    """
    url = db_url or os.environ.get("DATABASE_URL", "sqlite:///./menutor.db")

    if url.startswith("sqlite"):
        # SQLite-specific setup
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # For :memory:
            echo=False,
        )

        # Enable foreign keys
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
    """Create SQLAlchemy session."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal()
```

### Alembic Migrations

**File:** `backend/infrastructure/database/migrations/env.py`

Alembic configuration for automatic schema updates.

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
from backend.infrastructure.database.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
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
    """Run migrations in online mode."""
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

### Migration Workflow

```bash
# Auto-detect changes
alembic revision --autogenerate -m "Add weight to recipes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Example migration:**

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
    # ... more tables

def downgrade() -> None:
    op.drop_table('recipes')
    op.drop_table('users')
    # ...
```

---

## Exporters (Strategy Pattern)

**File:** `backend/infrastructure/export/`

Interchangeable export algorithms.

```python
from abc import ABC, abstractmethod
from backend.domain.entities.shopping_list import ShoppingList

class ShoppingListExporter(ABC):
    @abstractmethod
    def export(self, shopping_list: ShoppingList) -> str:
        pass

class CsvExporter(ShoppingListExporter):
    """Export shopping list as CSV."""

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
    """Export shopping list as JSON."""

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

### Exporter Registry

```python
class ExporterRegistry:
    def __init__(self):
        self._exporters: dict[str, ShoppingListExporter] = {}

    def register(self, format_name: str, exporter: ShoppingListExporter) -> None:
        self._exporters[format_name] = exporter

    def get(self, format_name: str) -> ShoppingListExporter:
        if format_name not in self._exporters:
            raise ValueError(f"Unknown exporter: {format_name}")
        return self._exporters[format_name]

# Usage
registry = ExporterRegistry()
registry.register("csv", CsvExporter())
registry.register("json", JsonExporter())

csv_exporter = registry.get("csv")
csv_output = csv_exporter.export(shopping_list)
```

---

## Multi-Database Support

### SQLite (Development)

```
DATABASE_URL=sqlite:///./menutor.db
```

- File-based
- No server setup needed
- Good for single-user dev

### PostgreSQL (Production)

```
DATABASE_URL=postgresql://username:password@host:5432/menutor_db
```

- Multi-user, concurrent access
- ACID guarantees
- Better for scale

Both work identically through SQLAlchemy layer. No code changes needed.

---

## Testing with In-Memory Database

**Pattern:** Use SQLite `:memory:` for fast tests.

```python
# tests/conftest.py

@pytest.fixture
def db_session():
    """In-memory SQLite database for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def recipe_repo(db_session):
    """Recipe repository with test DB."""
    return SqlalchemyRecipeRepository(db_session)

def test_save_recipe(recipe_repo):
    recipe = Recipe(...)
    recipe_id = recipe_repo.save(recipe)
    assert recipe_id is not None

    loaded = recipe_repo.get_by_id(recipe_id, UserId(1))
    assert loaded.name == recipe.name
```

---

## Summary

The Infrastructure layer:
- **Implements** all Domain ports (repositories, auth, exporters)
- **Manages** database schema via SQLAlchemy + Alembic
- **Handles** password hashing and JWT generation
- **Supports** multiple databases (SQLite, PostgreSQL)
- **Is testable** via dependency injection

Key patterns:
- **Repository:** Abstract data access
- **ORM Mapper:** Convert rows ↔ domain entities
- **Strategy:** Interchangeable exporters
- **Service:** Stateless auth operations

---

**Next:** See [backend-api.md](06-backend-api.md) for HTTP layer details.
