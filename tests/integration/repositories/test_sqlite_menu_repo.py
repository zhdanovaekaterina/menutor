from decimal import Decimal

import pytest

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import (
    MenuId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from backend.infrastructure.repositories.sqlite_menu_repository import SqliteMenuRepository
from backend.infrastructure.repositories.sqlite_product_repository import (
    SqliteProductRepository,
)
from backend.infrastructure.repositories.sqlite_recipe_repository import (
    SqliteRecipeRepository,
)


@pytest.fixture
def menu_repo(conn: object) -> SqliteMenuRepository:
    return SqliteMenuRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def seeded_recipe(conn: object) -> Recipe:
    """Insert product + recipe directly; returns recipe with real DB id."""
    product_repo = SqliteProductRepository(conn)  # type: ignore[arg-type]
    recipe_repo = SqliteRecipeRepository(conn)  # type: ignore[arg-type]
    p = product_repo.save(Product(
        id=ProductId(0), name="Мука",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")), conversion_factor=1000,
        category_id=ProductCategoryId(1),
    ))
    return recipe_repo.save(Recipe(id=RecipeId(0), name="Блины", servings=4,
                                   category_id=RecipeCategoryId(1)))


@pytest.fixture
def seeded_product(conn: object) -> Product:
    """Insert a product; returns product with real DB id."""
    product_repo = SqliteProductRepository(conn)  # type: ignore[arg-type]
    return product_repo.save(Product(
        id=ProductId(0), name="Молоко",
        recipe_unit="ml", purchase_unit="l",
        price_per_purchase_unit=Money(Decimal("90")), conversion_factor=1000,
        category_id=ProductCategoryId(1),
    ))


def _empty_menu(name: str = "Неделя") -> WeeklyMenu:
    return WeeklyMenu(MenuId(0), name, slots=[])


def test_save_assigns_id(menu_repo: SqliteMenuRepository) -> None:
    saved = menu_repo.save(_empty_menu())
    assert saved.id != MenuId(0)


def test_save_and_get_by_id_empty_menu(menu_repo: SqliteMenuRepository) -> None:
    saved = menu_repo.save(_empty_menu("Моё меню"))
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Моё меню"
    assert retrieved.slots == []


def test_save_and_get_with_recipe_slots(menu_repo: SqliteMenuRepository,
                                  seeded_recipe: Recipe) -> None:
    menu = WeeklyMenu(MenuId(0), "С блюдами", slots=[
        MenuSlot(day=0, meal_type="завтрак", recipe_id=seeded_recipe.id),
        MenuSlot(day=1, meal_type="обед",    recipe_id=seeded_recipe.id,
                 servings_override=3.0),
    ])
    saved = menu_repo.save(menu)
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert len(retrieved.slots) == 2
    slot_map = {s.meal_type: s for s in retrieved.slots}
    assert slot_map["завтрак"].day == 0
    assert slot_map["завтрак"].recipe_id == seeded_recipe.id
    assert slot_map["завтрак"].product_id is None
    assert slot_map["обед"].servings_override == pytest.approx(3.0)


def test_save_and_get_with_product_slot(menu_repo: SqliteMenuRepository,
                                        seeded_product: Product) -> None:
    menu = WeeklyMenu(MenuId(0), "С продуктом", slots=[
        MenuSlot(day=2, meal_type="ужин", product_id=seeded_product.id,
                 quantity=500.0, unit="ml"),
    ])
    saved = menu_repo.save(menu)
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert len(retrieved.slots) == 1
    slot = retrieved.slots[0]
    assert slot.product_id == seeded_product.id
    assert slot.recipe_id is None
    assert slot.quantity == pytest.approx(500.0)
    assert slot.unit == "ml"


def test_save_multiple_items_same_cell(menu_repo: SqliteMenuRepository,
                                       seeded_recipe: Recipe,
                                       seeded_product: Product) -> None:
    """Multiple items in the same (day, meal_type) should all be saved."""
    menu = WeeklyMenu(MenuId(0), "Мульти", slots=[
        MenuSlot(day=0, meal_type="завтрак", recipe_id=seeded_recipe.id),
        MenuSlot(day=0, meal_type="завтрак", product_id=seeded_product.id,
                 quantity=200.0, unit="ml"),
    ])
    saved = menu_repo.save(menu)
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert len(retrieved.slots) == 2
    types = {("recipe" if s.recipe_id else "product") for s in retrieved.slots}
    assert types == {"recipe", "product"}


def test_get_by_id_returns_none_when_absent(menu_repo: SqliteMenuRepository) -> None:
    assert menu_repo.get_by_id(MenuId(9999)) is None


def test_delete_removes_menu(menu_repo: SqliteMenuRepository) -> None:
    saved = menu_repo.save(_empty_menu())
    menu_repo.delete(saved.id)
    assert menu_repo.get_by_id(saved.id) is None


def test_delete_cascades_to_slots(menu_repo: SqliteMenuRepository,
                                   seeded_recipe: Recipe,
                                   conn: object) -> None:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    session: Session = conn  # type: ignore[assignment]
    menu = WeeklyMenu(MenuId(0), "Тест", slots=[
        MenuSlot(0, "завтрак", recipe_id=seeded_recipe.id)
    ])
    saved = menu_repo.save(menu)
    menu_repo.delete(saved.id)

    count = session.execute(
        text("SELECT COUNT(*) FROM menu_slots WHERE menu_id = :id"),
        {"id": saved.id},
    ).scalar()
    assert count == 0


def test_find_all(menu_repo: SqliteMenuRepository) -> None:
    menu_repo.save(_empty_menu("Неделя 1"))
    menu_repo.save(_empty_menu("Неделя 2"))
    assert len(menu_repo.find_all()) == 2


def test_save_updates_existing_menu_and_replaces_slots(
    menu_repo: SqliteMenuRepository, seeded_recipe: Recipe
) -> None:
    saved = menu_repo.save(WeeklyMenu(MenuId(0), "Исходное", slots=[
        MenuSlot(0, "завтрак", recipe_id=seeded_recipe.id),
    ]))
    # Update: rename + change slots
    updated = menu_repo.save(WeeklyMenu(saved.id, "Обновлённое", slots=[
        MenuSlot(3, "ужин", recipe_id=seeded_recipe.id),
    ]))
    assert updated.name == "Обновлённое"
    assert len(updated.slots) == 1
    assert updated.slots[0].day == 3
