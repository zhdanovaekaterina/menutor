"""Composition Root — единственное место, где сходятся все слои приложения.

Никакой другой модуль не должен импортировать отсюда.
main.py создаёт ApplicationContainer и передаёт его в MainWindow.
"""

from src.application.use_cases.generate_shopping_list import GenerateShoppingList
from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    ListFamilyMembers,
)
from src.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProductCategories,
    ListProducts,
    UpdateProductPrice,
)
from src.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    GetRecipe,
    ListRecipeCategories,
    ListRecipes,
)
from src.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
    RemoveItemFromSlot,
    SaveMenu,
)
from src.domain.services.portion_calculator import PortionCalculator
from src.domain.services.shopping_list_builder import ShoppingListBuilder
from src.domain.services.unit_converter import UnitConverter
from src.infrastructure.database.connection import (
    apply_schema,
    get_connection,
    seed_defaults,
)
from src.infrastructure.export.csv_exporter import ShoppingListCsvExporter
from src.infrastructure.export.text_exporter import ShoppingListTextExporter
from src.infrastructure.repositories.sqlite_family_member_repository import (
    SqliteFamilyMemberRepository,
)
from src.infrastructure.repositories.sqlite_menu_repository import SqliteMenuRepository
from src.infrastructure.repositories.sqlite_product_category_repository import (
    SqliteProductCategoryRepository,
)
from src.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)
from src.infrastructure.repositories.sqlite_recipe_category_repository import (
    SqliteRecipeCategoryRepository,
)
from src.infrastructure.repositories.sqlite_recipe_repository import (
    SqliteRecipeRepository,
)


class ApplicationContainer:
    """Граф зависимостей всего приложения. Создаётся один раз в main()."""

    def __init__(self, db_path: str = "data/menutor.db") -> None:
        # ── Infrastructure ────────────────────────────────────────────
        conn = get_connection(db_path)
        apply_schema(conn)
        seed_defaults(conn)

        recipe_repo = SqliteRecipeRepository(conn)
        product_repo = SqliteProductRepository(conn)
        menu_repo = SqliteMenuRepository(conn)
        family_repo = SqliteFamilyMemberRepository(conn)
        product_category_repo = SqliteProductCategoryRepository(conn)
        recipe_category_repo = SqliteRecipeCategoryRepository(conn)

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

        # Keep connection alive for the process lifetime
        self._conn = conn
