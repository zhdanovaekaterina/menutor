"""Infrastructure layer objects — DB, repos, auth services, exporters."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.domain.services.password_hasher import PasswordHasher
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.unit_converter import UnitConverter
from backend.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from backend.infrastructure.auth.jwt_token_service import JwtTokenService
from backend.infrastructure.database.connection import (
    apply_schema,
    get_engine,
    seed_defaults,
)
from backend.infrastructure.export.csv_exporter import ShoppingListCsvExporter
from backend.infrastructure.export.text_exporter import ShoppingListTextExporter
from backend.infrastructure.repositories.sqlalchemy_family_member_repository import (
    SqlAlchemyFamilyMemberRepository,
)
from backend.infrastructure.repositories.sqlalchemy_menu_repository import (
    SqlAlchemyMenuRepository,
)
from backend.infrastructure.repositories.sqlalchemy_product_category_repository import (
    SqlAlchemyProductCategoryRepository,
)
from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SqlAlchemyProductRepository,
)
from backend.infrastructure.repositories.sqlalchemy_recipe_category_repository import (
    SqlAlchemyRecipeCategoryRepository,
)
from backend.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SqlAlchemyRecipeRepository,
)
from backend.infrastructure.repositories.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from backend.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


@dataclass
class _Infrastructure:
    """Holds all infrastructure objects created during startup."""

    engine: Any
    session: Session
    user_repo: SqlAlchemyUserRepository
    refresh_token_repo: SqlAlchemyRefreshTokenRepository
    password_hasher: PasswordHasher
    token_service: JwtTokenService
    recipe_repo: SqlAlchemyRecipeRepository
    product_repo: SqlAlchemyProductRepository
    menu_repo: SqlAlchemyMenuRepository
    family_repo: SqlAlchemyFamilyMemberRepository
    product_category_repo: SqlAlchemyProductCategoryRepository
    recipe_category_repo: SqlAlchemyRecipeCategoryRepository
    text_exporter: ShoppingListTextExporter
    csv_exporter: ShoppingListCsvExporter
    builder: ShoppingListBuilder


def _create_infrastructure(db_url: str | None) -> _Infrastructure:
    """Build all infrastructure-layer objects: DB, repos, services."""
    if db_url is None:
        _env_path = Path(__file__).resolve().parents[2] / ".config" / ".env"
        load_dotenv(_env_path)
        db_url = os.environ.get("DATABASE_URL", "sqlite:///data/menutor.db")

    engine = get_engine(db_url)
    apply_schema(engine)
    session = Session(engine)
    seed_defaults(session)

    recipe_repo = SqlAlchemyRecipeRepository(session)
    product_repo = SqlAlchemyProductRepository(session)
    product_category_repo = SqlAlchemyProductCategoryRepository(session)

    return _Infrastructure(
        engine=engine,
        session=session,
        user_repo=SqlAlchemyUserRepository(session),
        refresh_token_repo=SqlAlchemyRefreshTokenRepository(session),
        password_hasher=BcryptPasswordHasher(),
        token_service=JwtTokenService(
            os.environ.get(
                "JWT_SECRET_KEY",
                "change-me-in-production-use-a-long-random-string!",
            )
        ),
        recipe_repo=recipe_repo,
        product_repo=product_repo,
        menu_repo=SqlAlchemyMenuRepository(session),
        family_repo=SqlAlchemyFamilyMemberRepository(session),
        product_category_repo=product_category_repo,
        recipe_category_repo=SqlAlchemyRecipeCategoryRepository(session),
        text_exporter=ShoppingListTextExporter(),
        csv_exporter=ShoppingListCsvExporter(),
        builder=ShoppingListBuilder(
            recipe_repo=recipe_repo,
            product_repo=product_repo,
            product_category_repo=product_category_repo,
            portion_calc=PortionCalculator(),
            unit_converter=UnitConverter(),
        ),
    )
