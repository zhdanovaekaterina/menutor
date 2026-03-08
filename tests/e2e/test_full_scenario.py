"""E2E scenario tests: real DB + real use cases, mocked views.

Covers the main user journey:
  Create products → Create recipe → Plan menu → Generate shopping list → Export
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.generate_shopping_list import GenerateShoppingList
from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.application.use_cases.manage_category import (
    CreateProductCategory,
    CreateRecipeCategory,
    ListAllProductCategories,
    ListAllRecipeCategories,
)
from src.application.use_cases.manage_family import (
    CreateFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from src.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProductCategories,
    ListProducts,
    ProductData,
)
from src.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    ListRecipeCategories,
    ListRecipes,
    RecipeData,
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
from src.domain.entities.menu import MenuSlot
from src.domain.services.portion_calculator import PortionCalculator
from src.domain.services.shopping_list_builder import ShoppingListBuilder
from src.domain.services.unit_converter import UnitConverter
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import ProductCategoryId, RecipeCategoryId, RecipeId
from src.infrastructure.database.connection import apply_schema, get_connection, seed_defaults
from src.infrastructure.export.text_exporter import ShoppingListTextExporter
from src.infrastructure.repositories.sqlite_family_member_repository import (
    SqliteFamilyMemberRepository,
)
from src.infrastructure.repositories.sqlite_menu_repository import SqliteMenuRepository
from src.infrastructure.repositories.sqlite_product_category_repository import (
    SqliteProductCategoryRepository,
)
from src.infrastructure.repositories.sqlite_product_repository import SqliteProductRepository
from src.infrastructure.repositories.sqlite_recipe_category_repository import (
    SqliteRecipeCategoryRepository,
)
from src.infrastructure.repositories.sqlite_recipe_repository import SqliteRecipeRepository
from src.presentation.controllers.menu_planner_controller import MenuPlannerController
from src.presentation.controllers.product_controller import ProductController
from src.presentation.controllers.recipe_controller import RecipeController
from src.presentation.controllers.shopping_list_controller import ShoppingListController


@pytest.fixture
def db():
    """In-memory SQLite database with schema and default data."""
    conn = get_connection(":memory:")
    apply_schema(conn)
    seed_defaults(conn)
    yield conn
    conn.close()


@pytest.fixture
def repos(db):
    """All repository instances backed by the in-memory DB."""
    return {
        "recipe": SqliteRecipeRepository(db),
        "product": SqliteProductRepository(db),
        "menu": SqliteMenuRepository(db),
        "family": SqliteFamilyMemberRepository(db),
        "product_cat": SqliteProductCategoryRepository(db),
        "recipe_cat": SqliteRecipeCategoryRepository(db),
    }


class TestFullUserScenario:
    """Scenario: Create products, create recipe, plan menu, generate shopping list."""

    def test_recipe_to_shopping_list_pipeline(self, db, repos) -> None:
        # --- Step 1: Get default categories ---
        product_cats = repos["product_cat"].find_active()
        assert len(product_cats) > 0
        bakery_cat_id = ProductCategoryId(product_cats[0][0])

        recipe_cats = repos["recipe_cat"].find_active()
        assert len(recipe_cats) > 0
        breakfast_cat_id = RecipeCategoryId(recipe_cats[0][0])

        # --- Step 2: Create products ---
        create_product = CreateProduct(repos["product"])

        flour = create_product.execute(ProductData(
            name="Мука", category_id=bakery_cat_id,
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("80")),
            conversion_factor=0.001,
        ))
        assert flour.id != 0

        milk = create_product.execute(ProductData(
            name="Молоко", category_id=bakery_cat_id,
            recipe_unit="ml", purchase_unit="l",
            price=Money(Decimal("90")),
            conversion_factor=0.001,
        ))
        assert milk.id != 0

        # --- Step 3: Create recipe with ingredients ---
        create_recipe = CreateRecipe(repos["recipe"])
        recipe = create_recipe.execute(RecipeData(
            name="Блины",
            category_id=breakfast_cat_id,
            servings=4,
            ingredients=[
                RecipeIngredient(flour.id, Quantity(200.0, "g")),
                RecipeIngredient(milk.id, Quantity(500.0, "ml")),
            ],
        ))
        assert recipe.id != 0
        assert len(recipe.ingredients) == 2

        # --- Step 4: Create family members ---
        create_member = CreateFamilyMember(repos["family"])
        create_member.execute(FamilyMemberData(name="Взрослый", portion_multiplier=1.0))
        create_member.execute(FamilyMemberData(name="Ребёнок", portion_multiplier=0.5))

        members = ListFamilyMembers(repos["family"]).execute()
        assert len(members) == 2

        # --- Step 5: Create menu and add recipe ---
        create_menu = CreateMenu(repos["menu"])
        menu = create_menu.execute("Неделя 1")
        assert menu.id != 0

        add_dish = AddDishToSlot(repos["menu"])
        slot = MenuSlot(
            day=0, meal_type="Завтрак",
            recipe_id=recipe.id, servings_override=4.0,
        )
        menu = add_dish.execute(menu.id, slot)
        assert len(menu.slots) == 1

        # --- Step 6: Generate shopping list ---
        builder = ShoppingListBuilder(
            recipe_repo=repos["recipe"],
            product_repo=repos["product"],
            product_category_repo=repos["product_cat"],
            portion_calc=PortionCalculator(),
            unit_converter=UnitConverter(),
        )
        generate = GenerateShoppingList(repos["menu"], builder)
        shopping_list = generate.execute(menu.id)

        assert len(shopping_list.items) == 2
        names = {item.product_name for item in shopping_list.items}
        assert "Мука" in names
        assert "Молоко" in names

        # --- Step 7: Export as text ---
        text_exporter = ShoppingListTextExporter()
        export_text = ExportShoppingListAsText(text_exporter)
        text = export_text.execute(shopping_list)
        assert "Мука" in text
        assert "Молоко" in text

    def test_menu_crud_lifecycle(self, db, repos) -> None:
        """Create → Load → Clear → Delete menu."""
        create_menu = CreateMenu(repos["menu"])
        load_menu = LoadMenu(repos["menu"])
        clear_menu = ClearMenu(repos["menu"])
        delete_menu = DeleteMenu(repos["menu"])
        list_menus = ListMenus(repos["menu"])

        # Create
        menu = create_menu.execute("Тестовое меню")
        assert menu.name == "Тестовое меню"

        # Load
        loaded = load_menu.execute(menu.id)
        assert loaded is not None
        assert loaded.name == "Тестовое меню"

        # Clear
        cleared = clear_menu.execute(menu.id)
        assert cleared.slots == []

        # List
        menus = list_menus.execute()
        assert any(m.id == menu.id for m in menus)

        # Delete
        delete_menu.execute(menu.id)
        menus = list_menus.execute()
        assert not any(m.id == menu.id for m in menus)

    def test_product_recipe_crud(self, db, repos) -> None:
        """Create, edit, list, delete products and recipes."""
        product_cats = repos["product_cat"].find_active()
        cat_id = ProductCategoryId(product_cats[0][0])

        recipe_cats = repos["recipe_cat"].find_active()
        rcat_id = RecipeCategoryId(recipe_cats[0][0])

        # --- Product CRUD ---
        create_prod = CreateProduct(repos["product"])
        edit_prod = EditProduct(repos["product"])
        delete_prod = DeleteProduct(repos["product"])
        list_prod = ListProducts(repos["product"])

        product = create_prod.execute(ProductData(
            name="Сахар", category_id=cat_id,
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("60")),
        ))
        assert product.name == "Сахар"

        from src.application.use_cases.manage_product import ProductData as PD
        edited = edit_prod.execute(product.id, PD(
            name="Сахар-песок", category_id=cat_id,
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("65")),
        ))
        assert edited.name == "Сахар-песок"

        products = list_prod.execute()
        assert any(p.name == "Сахар-песок" for p in products)

        delete_prod.execute(product.id)
        products = list_prod.execute()
        assert not any(p.id == product.id for p in products)

        # --- Recipe CRUD ---
        create_rec = CreateRecipe(repos["recipe"])
        edit_rec = EditRecipe(repos["recipe"])
        delete_rec = DeleteRecipe(repos["recipe"])
        list_rec = ListRecipes(repos["recipe"])

        recipe = create_rec.execute(RecipeData(
            name="Каша", category_id=rcat_id, servings=2,
        ))
        assert recipe.name == "Каша"

        edited_r = edit_rec.execute(recipe.id, RecipeData(
            name="Овсяная каша", category_id=rcat_id, servings=3,
        ))
        assert edited_r.name == "Овсяная каша"
        assert edited_r.servings == 3

        delete_rec.execute(recipe.id)
        recipes = list_rec.execute()
        assert not any(r.id == recipe.id for r in recipes)

    def test_controller_with_real_use_cases(self, db, repos) -> None:
        """Verify ProductController works with real use cases (mocked view only)."""
        view = MagicMock()
        view._model = MagicMock()

        product_cats = repos["product_cat"].find_active()
        cat_id = ProductCategoryId(product_cats[0][0])

        create_uc = CreateProduct(repos["product"])
        edit_uc = EditProduct(repos["product"])
        delete_uc = DeleteProduct(repos["product"])
        list_uc = ListProducts(repos["product"])
        list_cat_uc = ListProductCategories(repos["product_cat"])

        ctrl = ProductController(view, create_uc, edit_uc, delete_uc, list_uc, list_cat_uc)

        # View should have been populated on init
        view.set_products.assert_called_once()
        view.set_categories.assert_called_once()

        # Create a product via controller
        data = ProductData(
            name="Яйца", category_id=cat_id,
            recipe_unit="pcs", purchase_unit="pcs",
            price=Money(Decimal("120")),
        )
        ctrl._on_create(data)

        # List should now have the product
        products = list_uc.execute()
        assert any(p.name == "Яйца" for p in products)

    def test_menu_planner_with_real_use_cases(self, db, repos) -> None:
        """Verify MenuPlannerController works end-to-end with real DB."""
        view = MagicMock()
        callback = MagicMock()

        # Create recipe + product first
        product_cats = repos["product_cat"].find_active()
        cat_id = ProductCategoryId(product_cats[0][0])
        recipe_cats = repos["recipe_cat"].find_active()
        rcat_id = RecipeCategoryId(recipe_cats[0][0])

        product = CreateProduct(repos["product"]).execute(ProductData(
            name="Рис", category_id=cat_id,
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("100")),
            conversion_factor=0.001,
        ))
        recipe = CreateRecipe(repos["recipe"]).execute(RecipeData(
            name="Плов", category_id=rcat_id, servings=4,
            ingredients=[RecipeIngredient(product.id, Quantity(300.0, "g"))],
        ))

        builder = ShoppingListBuilder(
            recipe_repo=repos["recipe"],
            product_repo=repos["product"],
            product_category_repo=repos["product_cat"],
            portion_calc=PortionCalculator(),
            unit_converter=UnitConverter(),
        )

        ctrl = MenuPlannerController(
            view=view,
            create_menu_uc=CreateMenu(repos["menu"]),
            save_menu_uc=SaveMenu(repos["menu"]),
            load_menu_uc=LoadMenu(repos["menu"]),
            delete_menu_uc=DeleteMenu(repos["menu"]),
            list_menus_uc=ListMenus(repos["menu"]),
            add_dish_uc=AddDishToSlot(repos["menu"]),
            remove_item_uc=RemoveItemFromSlot(repos["menu"]),
            clear_menu_uc=ClearMenu(repos["menu"]),
            list_recipes_uc=ListRecipes(repos["recipe"]),
            list_products_uc=ListProducts(repos["product"]),
            list_family_uc=ListFamilyMembers(repos["family"]),
            generate_shopping_list_uc=GenerateShoppingList(repos["menu"], builder),
            on_shopping_list_generated=callback,
        )

        # Create menu
        ctrl._on_new_menu("Тестовая неделя")
        assert ctrl._current_menu is not None

        # Add recipe to slot
        ctrl._on_slot_updated(0, "Обед", "recipe", recipe.id, 4.0, "")

        # Generate shopping list
        ctrl._on_generate()
        callback.assert_called_once()
        sl = callback.call_args[0][0]
        assert len(sl.items) > 0
        assert any(item.product_name == "Рис" for item in sl.items)
