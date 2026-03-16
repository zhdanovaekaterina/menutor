"""Composition Root — единственное место, где сходятся все слои приложения.

Никакой другой модуль не должен импортировать отсюда.
main.py создаёт ApplicationContainer и передаёт его в MainWindow.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from backend.application.use_cases.auth import (
    ChangePassword,
    GetCurrentUser,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    RegisterUser,
    UpdateProfile,
)
from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from backend.application.use_cases.manage_category import CategoryBundle
from backend.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    ListFamilyMembers,
)
from backend.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProductCategories,
    ListProducts,
    UpdateProductPrice,
)
from backend.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    GetRecipe,
    ListRecipeCategories,
    ListRecipes,
)
from backend.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    MoveSlotInMenu,
    RemoveItemFromSlot,
    SaveMenu,
)
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
from backend.infrastructure.export.text_exporter import ShoppingListTextExporter
from backend.infrastructure.repositories.sqlite_family_member_repository import (
    SqliteFamilyMemberRepository,
)
from backend.infrastructure.repositories.sqlite_menu_repository import (
    SqliteMenuRepository,
)
from backend.infrastructure.repositories.sqlite_product_category_repository import (
    SqliteProductCategoryRepository,
)
from backend.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)
from backend.infrastructure.repositories.sqlite_recipe_category_repository import (
    SqliteRecipeCategoryRepository,
)
from backend.infrastructure.repositories.sqlite_recipe_repository import (
    SqliteRecipeRepository,
)
from backend.infrastructure.repositories.sqlite_refresh_token_repository import (
    SqliteRefreshTokenRepository,
)
from backend.infrastructure.repositories.sqlite_user_repository import (
    SqliteUserRepository,
)


@dataclass
class _Infrastructure:
    """Holds all infrastructure objects created during startup."""

    engine: Any
    session: Session
    user_repo: SqliteUserRepository
    refresh_token_repo: SqliteRefreshTokenRepository
    password_hasher: PasswordHasher
    token_service: JwtTokenService
    recipe_repo: SqliteRecipeRepository
    product_repo: SqliteProductRepository
    menu_repo: SqliteMenuRepository
    family_repo: SqliteFamilyMemberRepository
    product_category_repo: SqliteProductCategoryRepository
    recipe_category_repo: SqliteRecipeCategoryRepository
    text_exporter: ShoppingListTextExporter
    csv_exporter: ShoppingListCsvExporter
    builder: ShoppingListBuilder


def _create_infrastructure(db_url: str | None) -> _Infrastructure:
    """Build all infrastructure-layer objects: DB, repos, services."""
    if db_url is None:
        _env_path = Path(__file__).resolve().parents[1] / ".config" / ".env"
        load_dotenv(_env_path)
        db_url = os.environ.get("DATABASE_URL", "sqlite:///data/menutor.db")

    engine = get_engine(db_url)
    apply_schema(engine)
    session = Session(engine)
    seed_defaults(session)

    recipe_repo = SqliteRecipeRepository(session)
    product_repo = SqliteProductRepository(session)
    product_category_repo = SqliteProductCategoryRepository(session)

    return _Infrastructure(
        engine=engine,
        session=session,
        user_repo=SqliteUserRepository(session),
        refresh_token_repo=SqliteRefreshTokenRepository(session),
        password_hasher=BcryptPasswordHasher(),
        token_service=JwtTokenService(
            os.environ.get(
                "JWT_SECRET_KEY",
                "change-me-in-production-use-a-long-random-string!",
            )
        ),
        recipe_repo=recipe_repo,
        product_repo=product_repo,
        menu_repo=SqliteMenuRepository(session),
        family_repo=SqliteFamilyMemberRepository(session),
        product_category_repo=product_category_repo,
        recipe_category_repo=SqliteRecipeCategoryRepository(session),
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


class ApplicationContainer:
    """Граф зависимостей всего приложения. Создаётся один раз в main()."""

    def __init__(self, db_url: str | None = None) -> None:
        infra = _create_infrastructure(db_url)

        # ── Auth ─────────────────────────────────────────────────────
        self.register_user = RegisterUser(
            infra.user_repo, infra.password_hasher, infra.family_repo
        )
        self.login_user = LoginUser(
            infra.user_repo, infra.password_hasher,
            infra.token_service, infra.refresh_token_repo,
        )
        self.refresh_access_token = RefreshAccessToken(
            infra.token_service, infra.refresh_token_repo, infra.user_repo
        )
        self.get_current_user = GetCurrentUser(
            infra.token_service, infra.user_repo
        )
        self.logout_user = LogoutUser(
            infra.token_service, infra.refresh_token_repo
        )
        self.change_password = ChangePassword(
            infra.user_repo, infra.password_hasher
        )
        self.update_profile = UpdateProfile(
            infra.user_repo, infra.password_hasher
        )

        # ── Recipes ──────────────────────────────────────────────────
        self.create_recipe = CreateRecipe(infra.recipe_repo)
        self.edit_recipe = EditRecipe(infra.recipe_repo)
        self.delete_recipe = DeleteRecipe(infra.recipe_repo)
        self.get_recipe = GetRecipe(infra.recipe_repo)
        self.list_recipes = ListRecipes(infra.recipe_repo)
        self.list_recipe_categories = ListRecipeCategories(
            infra.recipe_category_repo
        )

        # ── Products ─────────────────────────────────────────────────
        self.create_product = CreateProduct(infra.product_repo)
        self.edit_product = EditProduct(infra.product_repo)
        self.delete_product = DeleteProduct(infra.product_repo)
        self.update_product_price = UpdateProductPrice(infra.product_repo)
        self.list_products = ListProducts(infra.product_repo)
        self.list_product_categories = ListProductCategories(
            infra.product_category_repo
        )

        # ── Menu ─────────────────────────────────────────────────────
        self.create_menu = CreateMenu(infra.menu_repo)
        self.save_menu = SaveMenu(infra.menu_repo)
        self.load_menu = LoadMenu(infra.menu_repo)
        self.delete_menu = DeleteMenu(infra.menu_repo)
        self.list_menus = ListMenus(infra.menu_repo)
        self.add_dish_to_slot = AddDishToSlot(infra.menu_repo)
        self.move_slot_in_menu = MoveSlotInMenu(infra.menu_repo)
        self.remove_item_from_slot = RemoveItemFromSlot(infra.menu_repo)
        self.clear_menu = ClearMenu(infra.menu_repo)

        # ── Categories ───────────────────────────────────────────────
        self.product_categories = CategoryBundle(infra.product_category_repo)
        self.recipe_categories = CategoryBundle(infra.recipe_category_repo)

        # ── Family ───────────────────────────────────────────────────
        self.create_family_member = CreateFamilyMember(infra.family_repo)
        self.edit_family_member = EditFamilyMember(infra.family_repo)
        self.delete_family_member = DeleteFamilyMember(infra.family_repo)
        self.list_family_members = ListFamilyMembers(infra.family_repo)

        # ── Shopping List ────────────────────────────────────────────
        self.generate_shopping_list = GenerateShoppingList(
            menu_repo=infra.menu_repo, builder=infra.builder,
        )
        self.export_shopping_list_as_text = ExportShoppingListAsText(
            infra.text_exporter
        )
        self.export_shopping_list_as_csv = ExportShoppingListAsCsv(
            infra.csv_exporter
        )

        self._engine = infra.engine
        self._session = infra.session
