"""Composition Root — единственное место, где сходятся все слои приложения.

Никакой другой модуль не должен импортировать отсюда.
main.py создаёт ApplicationContainer и передаёт его в MainWindow.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from backend.application.use_cases.auth import (
    GetCurrentUser,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    RegisterUser,
)
from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from backend.application.use_cases.manage_category import (
    ActivateCategory,
    CheckProductCategoryUsed,
    CheckRecipeCategoryUsed,
    CreateProductCategory,
    CreateRecipeCategory,
    DeleteProductCategory,
    DeleteRecipeCategory,
    EditProductCategory,
    EditRecipeCategory,
    HardDeleteCategory,
    ListAllProductCategories,
    ListAllRecipeCategories,
)
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
    RemoveItemFromSlot,
    SaveMenu,
)
from backend.domain.services.password_hasher import PasswordHasher
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.unit_converter import UnitConverter
from sqlalchemy.orm import Session

from backend.infrastructure.database.connection import (
    apply_schema,
    get_engine,
    seed_defaults,
)
from backend.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from backend.infrastructure.auth.jwt_token_service import JwtTokenService
from backend.infrastructure.export.csv_exporter import ShoppingListCsvExporter
from backend.infrastructure.export.text_exporter import ShoppingListTextExporter
from backend.infrastructure.repositories.sqlite_family_member_repository import (
    SqliteFamilyMemberRepository,
)
from backend.infrastructure.repositories.sqlite_menu_repository import SqliteMenuRepository
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


class ApplicationContainer:
    """Граф зависимостей всего приложения. Создаётся один раз в main()."""

    def __init__(self, db_url: str | None = None) -> None:
        # ── Infrastructure ────────────────────────────────────────────
        if db_url is None:
            _env_path = Path(__file__).resolve().parents[1] / ".config" / ".env"
            load_dotenv(_env_path)
            db_url = os.environ.get("DATABASE_URL", "sqlite:///data/menutor.db")
        engine = get_engine(db_url)
        apply_schema(engine)
        session = Session(engine)
        seed_defaults(session)

        user_repo = SqliteUserRepository(session)
        refresh_token_repo = SqliteRefreshTokenRepository(session)

        jwt_secret = os.environ.get(
            "JWT_SECRET_KEY", "change-me-in-production-use-a-long-random-string!"
        )
        password_hasher: PasswordHasher = BcryptPasswordHasher()
        token_service = JwtTokenService(jwt_secret)

        recipe_repo = SqliteRecipeRepository(session)
        product_repo = SqliteProductRepository(session)
        menu_repo = SqliteMenuRepository(session)
        family_repo = SqliteFamilyMemberRepository(session)
        product_category_repo = SqliteProductCategoryRepository(session)
        recipe_category_repo = SqliteRecipeCategoryRepository(session)

        text_exporter = ShoppingListTextExporter()
        csv_exporter = ShoppingListCsvExporter()

        # ── Domain Services ───────────────────────────────────────────
        unit_converter = UnitConverter()
        portion_calc = PortionCalculator()
        builder = ShoppingListBuilder(
            recipe_repo=recipe_repo,
            product_repo=product_repo,
            product_category_repo=product_category_repo,
            portion_calc=portion_calc,
            unit_converter=unit_converter,
        )

        # ── Application — Auth ──────────────────────────────────────────
        self.register_user = RegisterUser(user_repo, password_hasher)
        self.login_user = LoginUser(
            user_repo, password_hasher, token_service, refresh_token_repo
        )
        self.refresh_access_token = RefreshAccessToken(
            token_service, refresh_token_repo, user_repo
        )
        self.get_current_user = GetCurrentUser(token_service, user_repo)
        self.logout_user = LogoutUser(token_service, refresh_token_repo)

        # Expose for PATCH /auth/me
        self.password_hasher = password_hasher
        self.user_repo = user_repo

        # ── Application — Recipes ─────────────────────────────────────
        self.create_recipe = CreateRecipe(recipe_repo)
        self.edit_recipe = EditRecipe(recipe_repo)
        self.delete_recipe = DeleteRecipe(recipe_repo)
        self.get_recipe = GetRecipe(recipe_repo)
        self.list_recipes = ListRecipes(recipe_repo)
        self.list_recipe_categories = ListRecipeCategories(recipe_category_repo)

        # ── Application — Products ────────────────────────────────────
        self.create_product = CreateProduct(product_repo)
        self.edit_product = EditProduct(product_repo)
        self.delete_product = DeleteProduct(product_repo)
        self.update_product_price = UpdateProductPrice(product_repo)
        self.list_products = ListProducts(product_repo)
        self.list_product_categories = ListProductCategories(product_category_repo)

        # ── Application — Menu ────────────────────────────────────────
        self.create_menu = CreateMenu(menu_repo)
        self.save_menu = SaveMenu(menu_repo)
        self.load_menu = LoadMenu(menu_repo)
        self.delete_menu = DeleteMenu(menu_repo)
        self.list_menus = ListMenus(menu_repo)
        self.add_dish_to_slot = AddDishToSlot(menu_repo)
        self.remove_item_from_slot = RemoveItemFromSlot(menu_repo)
        self.clear_menu = ClearMenu(menu_repo)

        # ── Application — Categories ──────────────────────────────────
        self.list_all_product_categories = ListAllProductCategories(
            product_category_repo
        )
        self.create_product_category = CreateProductCategory(product_category_repo)
        self.edit_product_category = EditProductCategory(product_category_repo)
        self.delete_product_category = DeleteProductCategory(product_category_repo)
        self.hard_delete_product_category = HardDeleteCategory(product_category_repo)
        self.activate_product_category = ActivateCategory(product_category_repo)
        self.check_product_category_used = CheckProductCategoryUsed(
            product_category_repo
        )

        self.list_all_recipe_categories = ListAllRecipeCategories(
            recipe_category_repo
        )
        self.create_recipe_category = CreateRecipeCategory(recipe_category_repo)
        self.edit_recipe_category = EditRecipeCategory(recipe_category_repo)
        self.delete_recipe_category = DeleteRecipeCategory(recipe_category_repo)
        self.hard_delete_recipe_category = HardDeleteCategory(recipe_category_repo)
        self.activate_recipe_category = ActivateCategory(recipe_category_repo)
        self.check_recipe_category_used = CheckRecipeCategoryUsed(
            recipe_category_repo
        )

        # ── Application — Family ──────────────────────────────────────
        self.create_family_member = CreateFamilyMember(family_repo)
        self.edit_family_member = EditFamilyMember(family_repo)
        self.delete_family_member = DeleteFamilyMember(family_repo)
        self.list_family_members = ListFamilyMembers(family_repo)

        # ── Application — Shopping List ───────────────────────────────
        self.generate_shopping_list = GenerateShoppingList(
            menu_repo=menu_repo,
            builder=builder,
        )
        self.export_shopping_list_as_text = ExportShoppingListAsText(text_exporter)
        self.export_shopping_list_as_csv = ExportShoppingListAsCsv(csv_exporter)

        # Keep engine and session alive for the process lifetime
        self._engine = engine
        self._session = session
