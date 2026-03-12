"""E2E scenario tests: real DB + real use cases.

Covers the main user journey:
  Create products → Create recipe → Plan menu → Generate shopping list → Export
"""

from decimal import Decimal

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.import_export import ExportShoppingListAsText
from backend.application.use_cases.manage_family import (
    CreateFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from backend.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    ListProducts,
    ProductData,
)
from backend.application.use_cases.manage_recipe import (
    CreateRecipe,
    DeleteRecipe,
    EditRecipe,
    ListRecipes,
    RecipeData,
)
from backend.application.use_cases.plan_menu import (
    AddDishToSlot,
    ClearMenu,
    CreateMenu,
    DeleteMenu,
    ListMenus,
    LoadMenu,
)
from backend.domain.entities.menu import MenuSlot
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.unit_converter import UnitConverter
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductCategoryId, RecipeCategoryId, UserId
from backend.infrastructure.database.connection import (
    apply_schema,
    get_engine,
    seed_defaults,
)
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

TEST_USER_ID = UserId(1)

_SEED_USER_SQL = (
    "INSERT INTO users (email, nickname, hashed_password, created_at) "
    "VALUES ('test@example.com', 'tester', 'hashed', '2025-01-01 00:00:00')"
)


@pytest.fixture
def db():
    """In-memory SQLite database with schema and default data."""
    engine = get_engine("sqlite:///:memory:")
    apply_schema(engine)
    session = Session(engine)
    seed_defaults(session)
    session.execute(sa_text(_SEED_USER_SQL))
    session.commit()
    yield session
    session.close()
    engine.dispose()


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
        uid = TEST_USER_ID

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
            conversion_factor=1000,
        ), uid)
        assert flour.id != 0

        milk = create_product.execute(ProductData(
            name="Молоко", category_id=bakery_cat_id,
            recipe_unit="ml", purchase_unit="l",
            price=Money(Decimal("90")),
            conversion_factor=1000,
        ), uid)
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
        ), uid)
        assert recipe.id != 0
        assert len(recipe.ingredients) == 2

        # --- Step 4: Create family members ---
        create_member = CreateFamilyMember(repos["family"])
        create_member.execute(FamilyMemberData(name="Взрослый", portion_multiplier=1.0), uid)
        create_member.execute(FamilyMemberData(name="Ребёнок", portion_multiplier=0.5), uid)

        members = ListFamilyMembers(repos["family"]).execute(uid)
        assert len(members) == 2

        # --- Step 5: Create menu and add recipe ---
        create_menu = CreateMenu(repos["menu"])
        menu = create_menu.execute("Неделя 1", uid)
        assert menu.id != 0

        add_dish = AddDishToSlot(repos["menu"])
        slot = MenuSlot(
            day=0, meal_type="Завтрак",
            recipe_id=recipe.id, servings_override=4.0,
        )
        menu = add_dish.execute(menu.id, slot, uid)
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
        shopping_list = generate.execute(menu.id, uid)

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
        uid = TEST_USER_ID
        create_menu = CreateMenu(repos["menu"])
        load_menu = LoadMenu(repos["menu"])
        clear_menu = ClearMenu(repos["menu"])
        delete_menu = DeleteMenu(repos["menu"])
        list_menus = ListMenus(repos["menu"])

        # Create
        menu = create_menu.execute("Тестовое меню", uid)
        assert menu.name == "Тестовое меню"

        # Load
        loaded = load_menu.execute(menu.id, uid)
        assert loaded is not None
        assert loaded.name == "Тестовое меню"

        # Clear
        cleared = clear_menu.execute(menu.id, uid)
        assert cleared.slots == []

        # List
        menus = list_menus.execute(uid)
        assert any(m.id == menu.id for m in menus)

        # Delete
        delete_menu.execute(menu.id, uid)
        menus = list_menus.execute(uid)
        assert not any(m.id == menu.id for m in menus)

    def test_product_recipe_crud(self, db, repos) -> None:
        """Create, edit, list, delete products and recipes."""
        uid = TEST_USER_ID
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
        ), uid)
        assert product.name == "Сахар"

        edited = edit_prod.execute(product.id, ProductData(
            name="Сахар-песок", category_id=cat_id,
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("65")),
        ), uid)
        assert edited.name == "Сахар-песок"

        products = list_prod.execute(uid)
        assert any(p.name == "Сахар-песок" for p in products)

        delete_prod.execute(product.id, uid)
        products = list_prod.execute(uid)
        assert not any(p.id == product.id for p in products)

        # --- Recipe CRUD ---
        create_rec = CreateRecipe(repos["recipe"])
        edit_rec = EditRecipe(repos["recipe"])
        delete_rec = DeleteRecipe(repos["recipe"])
        list_rec = ListRecipes(repos["recipe"])

        recipe = create_rec.execute(RecipeData(
            name="Каша", category_id=rcat_id, servings=2,
        ), uid)
        assert recipe.name == "Каша"

        edited_r = edit_rec.execute(recipe.id, RecipeData(
            name="Овсяная каша", category_id=rcat_id, servings=3,
        ), uid)
        assert edited_r.name == "Овсяная каша"
        assert edited_r.servings == 3

        delete_rec.execute(recipe.id, uid)
        recipes = list_rec.execute(uid)
        assert not any(r.id == recipe.id for r in recipes)
