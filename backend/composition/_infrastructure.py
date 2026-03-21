"""Infrastructure layer objects — DB, repos, auth services, exporters."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.domain.services.password_hasher import PasswordHasher
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.unit_converter import UnitConverter
from backend.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from backend.infrastructure.auth.jwt_token_service import JwtTokenService
from backend.infrastructure.database.connection import (
    apply_schema,
    get_engine,
    seed_defaults,
)
from backend.infrastructure.export.csv_exporter import ShoppingListCsvExporter
from backend.infrastructure.export.shopping_list_json_exporter import (
    ShoppingListJsonExporter,
)
from backend.infrastructure.export.shopping_list_pdf_exporter import (
    ShoppingListPdfExporter,
)
from backend.infrastructure.export.text_exporter import ShoppingListTextExporter
from backend.infrastructure.repositories.orm_family_member_repository import (
    OrmFamilyMemberRepository,
)
from backend.infrastructure.repositories.orm_menu_repository import (
    OrmMenuRepository,
)
from backend.infrastructure.repositories.orm_product_category_repository import (
    OrmProductCategoryRepository,
)
from backend.infrastructure.repositories.orm_product_repository import (
    OrmProductRepository,
)
from backend.infrastructure.repositories.orm_recipe_category_repository import (
    OrmRecipeCategoryRepository,
)
from backend.infrastructure.repositories.orm_recipe_repository import (
    OrmRecipeRepository,
)
from backend.infrastructure.repositories.orm_refresh_token_repository import (
    OrmRefreshTokenRepository,
)
from backend.infrastructure.repositories.orm_user_repository import (
    OrmUserRepository,
)


@dataclass
class _Infrastructure:
    """Holds all infrastructure objects created during startup."""

    engine: Any
    session: Session
    user_repo: OrmUserRepository
    refresh_token_repo: OrmRefreshTokenRepository
    password_hasher: PasswordHasher
    token_service: JwtTokenService
    recipe_repo: OrmRecipeRepository
    product_repo: OrmProductRepository
    menu_repo: OrmMenuRepository
    family_repo: OrmFamilyMemberRepository
    product_category_repo: OrmProductCategoryRepository
    recipe_category_repo: OrmRecipeCategoryRepository
    text_exporter: ShoppingListTextExporter
    csv_exporter: ShoppingListCsvExporter
    json_exporter: ShoppingListJsonExporter
    pdf_exporter: ShoppingListPdfExporter
    builder: ShoppingListBuilder


_TEST_JWT_SECRET = "test-only-secret-do-not-use-in-production"


def _get_jwt_secret(db_url: str) -> str:
    """Return JWT secret key, raising if not configured for non-SQLite databases."""
    secret = os.environ.get("JWT_SECRET_KEY")
    if secret:
        return secret
    if db_url.startswith("sqlite"):
        return _TEST_JWT_SECRET
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required for non-SQLite databases. "
        "Set it in .config/.env or your environment."
    )


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

    recipe_repo = OrmRecipeRepository(session)
    product_repo = OrmProductRepository(session)
    product_category_repo = OrmProductCategoryRepository(session)

    return _Infrastructure(
        engine=engine,
        session=session,
        user_repo=OrmUserRepository(session),
        refresh_token_repo=OrmRefreshTokenRepository(session),
        password_hasher=BcryptPasswordHasher(),
        token_service=JwtTokenService(_get_jwt_secret(db_url)),
        recipe_repo=recipe_repo,
        product_repo=product_repo,
        menu_repo=OrmMenuRepository(session),
        family_repo=OrmFamilyMemberRepository(session),
        product_category_repo=product_category_repo,
        recipe_category_repo=OrmRecipeCategoryRepository(session),
        text_exporter=ShoppingListTextExporter(),
        csv_exporter=ShoppingListCsvExporter(),
        json_exporter=ShoppingListJsonExporter(),
        pdf_exporter=ShoppingListPdfExporter(),
        builder=ShoppingListBuilder(
            recipe_repo=recipe_repo,
            product_repo=product_repo,
            product_category_repo=product_category_repo,
            portion_calc=PortionCalculator(),
            unit_converter=UnitConverter(),
        ),
    )
