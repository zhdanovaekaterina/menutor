"""Unit tests for GenerateMealSummary use case."""

from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.generate_meal_summary import (
    GenerateMealSummary,
    MealSummaryResponse,
)
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId

from decimal import Decimal

UID = UserId(1)
OTHER_UID = UserId(2)


def _uc(
    menu_repo: MagicMock,
    recipe_repo: MagicMock,
    product_repo: MagicMock,
    builder: MagicMock,
) -> GenerateMealSummary:
    return GenerateMealSummary(menu_repo, recipe_repo, product_repo, builder)


def _make_recipe(
    recipe_id: int = 1,
    name: str = "Борщ",
    servings: int = 4,
    total_pieces: int | None = None,
    pieces_per_portion: int | None = None,
) -> Recipe:
    return Recipe(
        id=RecipeId(recipe_id),
        name=name,
        servings=servings,
        total_pieces=total_pieces,
        pieces_per_portion=pieces_per_portion,
    )


def _make_product(product_id: int = 10, name: str = "Молоко") -> Product:
    return Product(
        id=ProductId(product_id),
        name=name,
        recipe_unit="ml",
        purchase_unit="l",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=1000.0,
        user_id=UID,
    )


def test_execute_returns_summary_for_valid_menu() -> None:
    recipe = _make_recipe(recipe_id=1, name="Борщ", servings=4)
    product = _make_product(product_id=10, name="Молоко")

    slots = [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1)),
        MenuSlot(day=1, meal_type="ужин", product_id=ProductId(10), quantity=500.0, unit="ml"),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя 1", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = product
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert isinstance(result, MealSummaryResponse)
    assert result.menu_id == MenuId(1)
    assert result.menu_name == "Неделя 1"
    assert len(result.recipes) == 1
    assert len(result.products) == 1
    assert result.recipes[0].recipe_name == "Борщ"
    assert result.products[0].product_name == "Молоко"


def test_execute_raises_when_menu_not_found() -> None:
    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = None
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(999), UID)


def test_execute_raises_when_wrong_user() -> None:
    menu = WeeklyMenu(MenuId(1), "Неделя", [], user_id=OTHER_UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    with pytest.raises(EntityNotFoundError, match="не найдено"):
        _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)


def test_execute_aggregates_same_recipe_occurrences() -> None:
    recipe = _make_recipe(recipe_id=1, name="Плов", servings=4)

    slots = [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1), servings_override=2.0),
        MenuSlot(day=3, meal_type="ужин", recipe_id=RecipeId(1), servings_override=3.0),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert len(result.recipes) == 1
    summary = result.recipes[0]
    assert len(summary.occurrences) == 2
    assert summary.total_servings == pytest.approx(5.0)


def test_execute_respects_servings_override() -> None:
    recipe = _make_recipe(recipe_id=1, name="Суп", servings=4)

    slot = MenuSlot(day=2, meal_type="обед", recipe_id=RecipeId(1), servings_override=6.0)
    menu = WeeklyMenu(MenuId(1), "Неделя", [slot], user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert len(result.recipes) == 1
    occ = result.recipes[0].occurrences[0]
    assert occ.servings == pytest.approx(6.0)


def test_execute_handles_pieces_mode() -> None:
    # Recipe: 12 pieces total, 3 pieces per portion => 4 servings
    recipe = _make_recipe(
        recipe_id=1, name="Печенье", servings=4,
        total_pieces=12, pieces_per_portion=3,
    )

    slot = MenuSlot(day=0, meal_type="завтрак", recipe_id=RecipeId(1), pieces_override=6)
    menu = WeeklyMenu(MenuId(1), "Неделя", [slot], user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert len(result.recipes) == 1
    summary = result.recipes[0]
    assert summary.pieces_info is not None
    assert summary.pieces_info["pieces_per_portion"] == 3
    # 6 pieces_override / 3 per portion = 2.0 servings
    assert summary.total_servings == pytest.approx(2.0)
    assert summary.pieces_info["total_pieces"] == 6
    occ = summary.occurrences[0]
    assert occ.pieces_override == 6


def test_execute_skips_missing_recipe() -> None:
    slots = [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(99)),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = None  # recipe not found
    product_repo = MagicMock()
    builder = MagicMock()

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert result.recipes == []


def test_execute_skips_missing_product() -> None:
    slots = [
        MenuSlot(day=0, meal_type="завтрак", product_id=ProductId(99), quantity=200.0, unit="ml"),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = None  # product not found
    builder = MagicMock()

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert result.products == []


def test_execute_empty_menu() -> None:
    menu = WeeklyMenu(MenuId(1), "Пустая неделя", [], user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    builder = MagicMock()

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert result.recipes == []
    assert result.products == []


def test_execute_includes_slot_index_in_occurrences() -> None:
    recipe = _make_recipe(recipe_id=1, name="Каша", servings=2)

    slots = [
        MenuSlot(day=0, meal_type="завтрак", recipe_id=RecipeId(1)),
        MenuSlot(day=1, meal_type="завтрак", recipe_id=RecipeId(1)),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert len(result.recipes) == 1
    occurrences = result.recipes[0].occurrences
    assert len(occurrences) == 2
    assert occurrences[0].slot_index == 0
    assert occurrences[1].slot_index == 1


def test_execute_calls_builder_for_each_unique_recipe() -> None:
    recipe_a = _make_recipe(recipe_id=1, name="Борщ", servings=4)
    recipe_b = _make_recipe(recipe_id=2, name="Пельмени", servings=3)

    slots = [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1)),
        MenuSlot(day=1, meal_type="обед", recipe_id=RecipeId(2)),
    ]
    menu = WeeklyMenu(MenuId(1), "Неделя", slots, user_id=UID)

    menu_repo = MagicMock()
    menu_repo.get_by_id.return_value = menu
    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: recipe_a if rid == RecipeId(1) else recipe_b
    product_repo = MagicMock()
    builder = MagicMock()
    builder.resolve_recipe_ingredients_tree.return_value = []

    result = _uc(menu_repo, recipe_repo, product_repo, builder).execute(MenuId(1), UID)

    assert len(result.recipes) == 2
    assert builder.resolve_recipe_ingredients_tree.call_count == 2
