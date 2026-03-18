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
from backend.application.use_cases.export_entities import ExportEntities
from backend.application.use_cases.export_shopping_list import ExportShoppingList
from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.import_entities import ImportEntities
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
from backend.infrastructure.export.menu_json_exporter import MenuJsonExporter
from backend.infrastructure.export.product_csv_exporter import ProductCsvExporter
from backend.infrastructure.export.product_json_exporter import ProductJsonExporter
from backend.infrastructure.export.recipe_csv_exporter import RecipeCsvExporter
from backend.infrastructure.export.recipe_json_exporter import RecipeJsonExporter
from backend.infrastructure.export.registry import ExportRegistry, ImportRegistry
from backend.infrastructure.export.text_exporter import ShoppingListTextExporter
from backend.infrastructure.import_.menu_json_importer import MenuJsonImporter
from backend.infrastructure.import_.product_csv_importer import ProductCsvImporter
from backend.infrastructure.import_.product_json_importer import ProductJsonImporter
from backend.infrastructure.import_.recipe_csv_importer import RecipeCsvImporter
from backend.infrastructure.import_.recipe_json_importer import RecipeJsonImporter
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
        _env_path = Path(__file__).resolve().parents[1] / ".config" / ".env"
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

        # ── Import/Export ────────────────────────────────────────────
        export_registry = ExportRegistry()
        export_registry.register("products", "csv", ProductCsvExporter())
        export_registry.register("products", "json", ProductJsonExporter())
        export_registry.register("recipes", "csv", RecipeCsvExporter())
        export_registry.register("recipes", "json", RecipeJsonExporter())
        export_registry.register("recipes", "json_compact", RecipeJsonExporter(compact=True))
        export_registry.register("menus", "json", MenuJsonExporter())
        export_registry.register("shopping_list", "txt", infra.text_exporter)
        export_registry.register("shopping_list", "csv", infra.csv_exporter)

        import_registry = ImportRegistry()
        import_registry.register("products", "csv", ProductCsvImporter(infra.product_repo))
        import_registry.register("products", "json", ProductJsonImporter(infra.product_repo))
        import_registry.register("recipes", "csv", RecipeCsvImporter(infra.recipe_repo))
        import_registry.register("recipes", "json", RecipeJsonImporter(infra.recipe_repo))
        import_registry.register("menus", "json", MenuJsonImporter(infra.menu_repo))

        self.export_entities = ExportEntities(
            export_registry, infra.product_repo, infra.recipe_repo, infra.menu_repo,
        )
        self.import_entities = ImportEntities(import_registry, infra.session)
        self.export_shopping_list = ExportShoppingList(
            export_registry, self.generate_shopping_list,
        )

        self._engine = infra.engine
        self._session = infra.session
