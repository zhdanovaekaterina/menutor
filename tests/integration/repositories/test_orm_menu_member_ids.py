"""Integration tests for member_ids round-trip in OrmMenuRepository."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import (
    FamilyMemberId,
    MenuId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)
from backend.infrastructure.repositories.orm_menu_repository import OrmMenuRepository
from backend.infrastructure.repositories.orm_product_repository import OrmProductRepository
from backend.infrastructure.repositories.orm_recipe_repository import OrmRecipeRepository

from decimal import Decimal


@pytest.fixture
def menu_repo(conn: object) -> OrmMenuRepository:
    return OrmMenuRepository(conn)  # type: ignore[arg-type]


@pytest.fixture
def seeded_recipe(conn: object, user_id: UserId) -> Recipe:
    product_repo = OrmProductRepository(conn)  # type: ignore[arg-type]
    recipe_repo = OrmRecipeRepository(conn)  # type: ignore[arg-type]
    product_repo.save(Product(
        id=ProductId(0), name="Мука",
        recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")), conversion_factor=1000,
        category_id=ProductCategoryId(1), user_id=user_id,
    ))
    return recipe_repo.save(Recipe(
        id=RecipeId(0), name="Блины", servings=4,
        category_id=RecipeCategoryId(1), user_id=user_id,
    ))


def test_save_load_member_ids_round_trip(
    menu_repo: OrmMenuRepository, seeded_recipe: Recipe, user_id: UserId
) -> None:
    """Slot with member_ids=[1, 2] survives a save/load cycle."""
    menu = WeeklyMenu(MenuId(0), "Тест member_ids", slots=[
        MenuSlot(
            day=0,
            meal_type="завтрак",
            recipe_id=seeded_recipe.id,
            member_ids=[FamilyMemberId(1), FamilyMemberId(2)],
        )
    ], user_id=user_id)
    saved = menu_repo.save(menu)
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert len(retrieved.slots) == 1
    assert sorted(retrieved.slots[0].member_ids) == [FamilyMemberId(1), FamilyMemberId(2)]


def test_empty_member_ids_default(
    menu_repo: OrmMenuRepository, seeded_recipe: Recipe, user_id: UserId
) -> None:
    """Slot with no member_ids saves and loads as empty list."""
    menu = WeeklyMenu(MenuId(0), "Тест пустой member_ids", slots=[
        MenuSlot(
            day=1,
            meal_type="обед",
            recipe_id=seeded_recipe.id,
            member_ids=[],
        )
    ], user_id=user_id)
    saved = menu_repo.save(menu)
    retrieved = menu_repo.get_by_id(saved.id)

    assert retrieved is not None
    assert len(retrieved.slots) == 1
    assert retrieved.slots[0].member_ids == []


def test_existing_rows_backward_compat(
    menu_repo: OrmMenuRepository, seeded_recipe: Recipe, conn: object, user_id: UserId
) -> None:
    """Rows inserted without member_ids (using server_default) load as empty list."""
    session: Session = conn  # type: ignore[assignment]

    # Insert a menu and a slot directly via raw SQL, omitting member_ids so server_default fires
    session.execute(text("INSERT INTO menus (name, user_id) VALUES ('Старое меню', :uid)"), {"uid": int(user_id)})
    session.flush()
    menu_id_raw = session.execute(text("SELECT id FROM menus WHERE name = 'Старое меню'")).scalar()
    assert menu_id_raw is not None

    session.execute(text(
        "INSERT INTO menu_slots (menu_id, day, meal_type, recipe_id, slot_position) "
        "VALUES (:menu_id, 0, 'завтрак', :recipe_id, 0)"
    ), {"menu_id": menu_id_raw, "recipe_id": int(seeded_recipe.id)})
    session.flush()

    retrieved = menu_repo.get_by_id(MenuId(menu_id_raw))

    assert retrieved is not None
    assert len(retrieved.slots) == 1
    # member_ids column defaults to "[]" so it should deserialise as empty list
    assert retrieved.slots[0].member_ids == []
