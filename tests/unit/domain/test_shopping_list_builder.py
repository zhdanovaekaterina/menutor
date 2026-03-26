from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import SubRecipeWeightError
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.unit_converter import UnitConverter
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    MenuId,
    ProductCategoryId,
    ProductId,
    RecipeId,
)


def _product(pid: int, recipe_unit: str = "g", purchase_unit: str = "kg",
             conversion_factor: float = 1000, price: float = 100.0) -> Product:
    return Product(
        id=ProductId(pid),
        name=f"Product{pid}",
        recipe_unit=recipe_unit,
        purchase_unit=purchase_unit,
        price_per_purchase_unit=Money(Decimal(str(price))),
        conversion_factor=conversion_factor,
    )


def _recipe(rid: int, pid: int, amount: float = 200.0,
            recipe_unit: str = "g", base_servings: int = 2) -> Recipe:
    return Recipe(
        id=RecipeId(rid),
        name=f"Recipe{rid}",
        servings=base_servings,
        ingredients=[RecipeIngredient(product_id=ProductId(pid), quantity=Quantity(amount, recipe_unit))],
    )


def _builder(recipe_repo: MagicMock, product_repo: MagicMock,
             product_category_repo: MagicMock | None = None) -> ShoppingListBuilder:
    if product_category_repo is None:
        product_category_repo = MagicMock()
        product_category_repo.find_active.return_value = []
    return ShoppingListBuilder(
        recipe_repo=recipe_repo,
        product_repo=product_repo,
        product_category_repo=product_category_repo,
        portion_calc=PortionCalculator(),
        unit_converter=UnitConverter(),
    )


# ---- single slot ----

def test_single_slot_quantity_and_cost() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # base=2 servings → 200g → 0.2 kg → 20 RUB
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    item = result.items[0]
    assert item.quantity == Quantity(0.2, "kg")
    assert item.cost == Money(Decimal("20.0"))


def test_single_slot_no_members_uses_base_servings() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # base_servings=2 used directly → 200g → 0.2 kg
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(0.2, "kg")


# ---- aggregation ----

def test_two_slots_same_ingredient_aggregated() -> None:
    r1 = _recipe(1, 1, amount=200.0, base_servings=2)
    r2 = _recipe(2, 1, amount=300.0, base_servings=2)
    product = _product(1, "g", "kg", 1000, 100.0)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: r1 if rid == RecipeId(1) else r2
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = product

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(2)),
        ],
    )
    # 200g + 300g = 500g → 0.5 kg
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(0.5, "kg")


def test_two_different_products_two_items() -> None:
    r1 = _recipe(1, 1, amount=200.0, base_servings=2)
    r2 = _recipe(2, 2, amount=400.0, base_servings=2)
    p1 = _product(1, "g", "kg", 1000, 100.0)
    p2 = _product(2, "g", "kg", 1000, 50.0)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: r1 if rid == RecipeId(1) else r2
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: p1 if pid == ProductId(1) else p2

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="dinner", recipe_id=RecipeId(2)),
        ],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 2


# ---- servings_override ----

def test_slot_servings_override_used_instead_of_base() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=100.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 5.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=4.0)],
    )
    # override=4.0 → scale_to(4.0) → 100g*(4/2)=200g
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(200.0, "g")


def test_slot_servings_override_scales_down() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=4)
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 5.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=1.0)],
    )
    # override=1.0, base=4 → factor=0.25 → 200g*0.25=50g
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(50.0, "g")


def test_slot_servings_override_fractional() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 5.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=3.0)],
    )
    # override=3.0, base=2 → factor=1.5 → 200g*1.5=300g
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(300.0, "g")


def test_slot_no_override_uses_base_servings_factor_one() -> None:
    """When servings_override is absent, scale_to(base_servings) → factor=1, amounts unchanged."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=350.0, base_servings=4)
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 5.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # no override → scale_to(4) → factor=1.0 → 350g unchanged
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(350.0, "g")


def test_slot_override_scales_all_ingredients_proportionally() -> None:
    """All ingredients in a recipe are scaled by the same factor."""
    pid1, pid2 = ProductId(1), ProductId(2)
    p1 = _product(1, "g", "g", 1.0, 5.0)
    p2 = _product(2, "ml", "ml", 1.0, 3.0)

    recipe = Recipe(
        id=RecipeId(1), name="R", servings=2,
        ingredients=[
            RecipeIngredient(product_id=pid1, quantity=Quantity(100.0, "g")),
            RecipeIngredient(product_id=pid2, quantity=Quantity(50.0, "ml")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: p1 if pid == pid1 else p2

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=6.0)],
    )
    # override=6, base=2 → factor=3 → 100g→300g, 50ml→150ml
    result = _builder(recipe_repo, product_repo).build(menu)

    by_product = {item.product_id: item.quantity for item in result.items}
    assert by_product[pid1] == Quantity(300.0, "g")
    assert by_product[pid2] == Quantity(150.0, "ml")


# ---- shopping list helpers ----

def test_total_cost() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.total_cost() == Money(Decimal("20.0"))


def test_items_by_category() -> None:
    r1 = _recipe(1, 1, amount=200.0, recipe_unit="g", base_servings=2)
    r2 = _recipe(2, 2, amount=100.0, recipe_unit="ml", base_servings=2)
    p1 = Product(
        id=ProductId(1), name="Flour", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=1000, category_id=ProductCategoryId(1),
    )
    p2 = Product(
        id=ProductId(2), name="Milk", recipe_unit="ml", purchase_unit="l",
        price_per_purchase_unit=Money(Decimal("90")),
        conversion_factor=1000, category_id=ProductCategoryId(2),
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: r1 if rid == RecipeId(1) else r2
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: p1 if pid == ProductId(1) else p2
    product_category_repo = MagicMock()
    product_category_repo.find_active.return_value = [
        ActiveCategory(ProductCategoryId(1), "dry"),
        ActiveCategory(ProductCategoryId(2), "dairy"),
    ]

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(2)),
        ],
    )
    result = _builder(recipe_repo, product_repo, product_category_repo).build(menu)
    by_cat = result.items_by_category()

    assert "dry" in by_cat
    assert "dairy" in by_cat
    assert len(by_cat["dry"]) == 1
    assert len(by_cat["dairy"]) == 1


# ---- standalone product slots ----

def test_standalone_product_slot_adds_quantity_directly() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", product_id=ProductId(1),
                        quantity=500.0, unit="g")],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(0.5, "kg")


def test_standalone_product_no_family_scaling() -> None:
    """Standalone products specify exact amounts — no portion scaling."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 10.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", product_id=ProductId(1),
                        quantity=200.0, unit="g")],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items[0].quantity == Quantity(200.0, "g")


def test_product_slot_aggregates_with_recipe_ingredient() -> None:
    """A standalone product and a recipe using the same product should aggregate."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="lunch", product_id=ProductId(1),
                     quantity=300.0, unit="g"),
        ],
    )
    # Recipe: 200g (base 2 → scale 1.0) + standalone: 300g = 500g → 0.5 kg
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(0.5, "kg")


# ---- unit conversion error resilience ----

def test_incompatible_recipe_unit_skips_product() -> None:
    """When recipe ingredient unit is incompatible with product.recipe_unit, item is skipped."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    # ingredient is in 'g', but product expects 'pcs' — incompatible groups
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, recipe_unit="g", base_servings=2)
    product_repo.get_by_id.return_value = _product(1, recipe_unit="pcs", purchase_unit="pcs",
                                                    conversion_factor=1, price=5.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items == []


def test_standalone_slot_unknown_unit_skipped() -> None:
    """Standalone slot with an unknown unit string is skipped without raising."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 1000, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", product_id=ProductId(1),
                        quantity=500.0, unit="unknown_unit")],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items == []


def test_incompatible_aggregation_keeps_first_occurrence() -> None:
    """Same product in two recipes with incompatible units — first value kept, second skipped."""
    # Recipe 1 uses product 1 in 'g', recipe 2 uses product 1 in 'pcs'
    r1 = Recipe(
        id=RecipeId(1), name="R1", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
    )
    r2 = Recipe(
        id=RecipeId(2), name="R2", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(3.0, "pcs"))],
    )
    product = _product(1, recipe_unit="g", purchase_unit="g", conversion_factor=1, price=1.0)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: r1 if rid == RecipeId(1) else r2
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = product

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(2)),
        ],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # Only the first occurrence (200g) is kept; the 'pcs' ingredient is skipped
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(200.0, "g")


# ---- sub-recipe flattening ----

def test_sub_recipe_flattened_to_products() -> None:
    """Recipe A has sub-recipe B (2 serv of B). B has 200g tomatoes at base 4 servings.
    Expected: shopping list shows 100g tomatoes (200g * 2/4)."""
    tomato = _product(1, "g", "g", 1.0, 5.0)

    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(2.0, "serv"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: recipe_a if rid == RecipeId(1) else recipe_b
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = tomato

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(100.0, "g")


def test_sub_recipe_products_aggregated_with_parent() -> None:
    """Parent has 100g tomatoes directly + sub-recipe that also has 50g tomatoes → 150g total."""
    tomato = _product(1, "g", "g", 1.0, 5.0)

    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(50.0, "g"))],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g")),
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: recipe_a if rid == RecipeId(1) else recipe_b
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = tomato

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(150.0, "g")


def test_nested_sub_recipe_flattened() -> None:
    """A→B→C: all flatten to leaf products."""
    pepper = _product(1, "g", "g", 1.0, 5.0)

    recipe_c = Recipe(
        id=RecipeId(3), name="C", servings=2,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g"))],
    )
    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(3), quantity=Quantity(2.0, "serv"))],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv"))],
    )

    def get_by_id(rid: RecipeId) -> Recipe | None:
        return {RecipeId(1): recipe_a, RecipeId(2): recipe_b, RecipeId(3): recipe_c}.get(rid)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = get_by_id
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = pepper

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    # A: 1 serv of B, B base=1 → sub_scale=1.0; B: 2 serv of C, C base=2 → sub_scale=1.0; C: 100g*1.0=100g
    assert result.items[0].quantity == Quantity(100.0, "g")


def test_sub_recipe_scales_with_servings_override() -> None:
    """Menu slot overrides parent servings; sub-recipe products scale accordingly."""
    onion = _product(1, "g", "g", 1.0, 2.0)

    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g"))],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: recipe_a if rid == RecipeId(1) else recipe_b
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = onion

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1), servings_override=3.0)],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # Parent scaled x3; 1 serv of B x3 → 3 serv of B (base 1) → 300g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(300.0, "g")


def test_sub_recipe_standalone_and_nested_aggregate() -> None:
    """Same recipe as standalone slot AND as sub-ingredient; products aggregate."""
    carrot = _product(1, "g", "g", 1.0, 3.0)

    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(80.0, "g"))],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv"))],
    )

    def get_by_id(rid: RecipeId) -> Recipe | None:
        return {RecipeId(1): recipe_a, RecipeId(2): recipe_b}.get(rid)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = get_by_id
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = carrot

    # Slot 1: recipe B directly (80g), Slot 2: recipe A which includes B (80g) → total 160g
    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(2)),
            MenuSlot(day=1, meal_type="dinner", recipe_id=RecipeId(1)),
        ],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(160.0, "g")


def test_sub_recipe_empty_ingredients_contributes_nothing() -> None:
    """Sub-recipe with empty ingredients adds 0 products."""
    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1, ingredients=[],
    )
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: recipe_a if rid == RecipeId(1) else recipe_b
    product_repo = MagicMock()

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert result.items == []


def test_sub_recipe_cycle_defensive_guard() -> None:
    """If a cycle exists in stored data, builder does not infinite-loop."""
    # A uses B, B uses A — cycle in persisted data
    recipe_a = Recipe(
        id=RecipeId(1), name="A", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv"))],
    )
    recipe_b = Recipe(
        id=RecipeId(2), name="B", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(1), quantity=Quantity(1.0, "serv"))],
    )

    def get_by_id(rid: RecipeId) -> Recipe | None:
        return {RecipeId(1): recipe_a, RecipeId(2): recipe_b}.get(rid)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = get_by_id
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = None

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # Must terminate, not loop forever
    result = _builder(recipe_repo, product_repo).build(menu)
    assert result.items == []


# ---- weight-based sub-recipe scaling ----


def test_sub_recipe_weight_based_scaling_grams() -> None:
    """250g of a 1000g sub-recipe → scale=0.25; flour 500g → 125g, tomato 4pcs → 1pcs."""
    flour = _product(1, "g", "g", 1.0, 5.0)
    tomato = _product(2, "pcs", "pcs", 1.0, 3.0)

    # Sub-recipe: weight=1000g, servings=4; contains 500g flour and 4 pcs tomato
    sub_recipe = Recipe(
        id=RecipeId(2), name="Соус", servings=4, weight=1000,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(500.0, "g")),
            RecipeIngredient(product_id=ProductId(2), quantity=Quantity(4.0, "pcs")),
        ],
    )
    # Parent recipe uses 250g of the sub-recipe (weight-based)
    parent_recipe = Recipe(
        id=RecipeId(1), name="Паста", servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(250.0, "g")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = (
        lambda pid: flour if pid == ProductId(1) else tomato
    )

    result = _builder(recipe_repo, product_repo).flatten_recipe_products(parent_recipe)

    # scale = 250 / 1000 = 0.25
    assert result[ProductId(1)] == Quantity(125.0, "g")   # 500 * 0.25
    assert result[ProductId(2)] == Quantity(1.0, "pcs")   # 4 * 0.25


def test_sub_recipe_weight_based_scaling_kg_unit() -> None:
    """0.5 kg of a 1000g sub-recipe → scale=0.5; 200g flour → 100g."""
    flour = _product(1, "g", "g", 1.0, 5.0)

    sub_recipe = Recipe(
        id=RecipeId(2), name="Тесто", servings=2, weight=1000,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g")),
        ],
    )
    parent_recipe = Recipe(
        id=RecipeId(1), name="Пирог", servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(0.5, "kg")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    result = _builder(recipe_repo, product_repo).flatten_recipe_products(parent_recipe)

    # 0.5 kg → 500g; scale = 500 / 1000 = 0.5; flour = 200 * 0.5 = 100g
    assert result[ProductId(1)] == Quantity(100.0, "g")


def test_sub_recipe_weight_based_raises_when_weight_zero() -> None:
    """SubRecipeWeightError raised when weight unit used and sub-recipe weight is 0."""
    sub_recipe = Recipe(
        id=RecipeId(2), name="Начинка", servings=2, weight=0,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g")),
        ],
    )
    parent_recipe = Recipe(
        id=RecipeId(1), name="Пирог", servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(300.0, "g")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()

    builder = _builder(recipe_repo, product_repo)
    with pytest.raises(SubRecipeWeightError):
        builder.flatten_recipe_products(parent_recipe)


def test_sub_recipe_servings_based_scaling_unchanged() -> None:
    """Servings-based scaling (serv unit) continues to work as before."""
    onion = _product(1, "g", "g", 1.0, 2.0)

    sub_recipe = Recipe(
        id=RecipeId(2), name="Зажарка", servings=2,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g")),
        ],
    )
    parent_recipe = Recipe(
        id=RecipeId(1), name="Суп", servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = onion

    result = _builder(recipe_repo, product_repo).flatten_recipe_products(parent_recipe)

    # 1 serv of a 2-serv recipe → scale = 0.5; onion = 100 * 0.5 = 50g
    assert result[ProductId(1)] == Quantity(50.0, "g")


# ---- pieces-mode recipes ----


def _pieces_recipe(
    rid: int,
    pid: int,
    amount: float = 500.0,
    unit: str = "g",
    base_servings: int = 4,
    total_pieces: int = 10,
    pieces_per_portion: int = 2,
) -> Recipe:
    return Recipe(
        id=RecipeId(rid),
        name=f"PiecesRecipe{rid}",
        servings=base_servings,
        total_pieces=total_pieces,
        pieces_per_portion=pieces_per_portion,
        ingredients=[RecipeIngredient(product_id=ProductId(pid), quantity=Quantity(amount, unit))],
    )


# 1. pieces recipe (10 pcs, flour 500g), slot servings_override=2.5, pieces_per_portion=2
#    → pcs = max(1, round(2.5 * 2)) = 5, scale = 5/10 = 0.5 → 250g flour
def test_pieces_mode_recipe_scale_factor() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    recipe = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=2.5)],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(250.0, "g")


# 2. pieces recipe, pieces_override=15, total_pieces=10 → scale=1.5
def test_pieces_mode_with_pieces_override() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    recipe = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        pieces_override=15)],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # scale = 15/10 = 1.5; 500g * 1.5 = 750g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(750.0, "g")


# 3. two slots of same pieces recipe → pieces sum (FR-17)
def test_pieces_mode_two_slots_aggregated() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    recipe = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            # slot1: pieces_override=5 → scale=0.5 → 250g
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1), pieces_override=5),
            # slot2: pieces_override=5 → scale=0.5 → 250g
            MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(1), pieces_override=5),
        ],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # aggregated: 250g + 250g = 500g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(500.0, "g")


# 4. one pieces + one normal recipe in same menu
def test_pieces_mode_and_normal_in_same_menu() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    sugar = _product(2, "g", "g", 1.0, 3.0)

    pieces_r = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)
    # normal recipe: 2 servings, 200g sugar, scale_factor=1 → 200g
    normal_r = Recipe(
        id=RecipeId(2),
        name="Normal",
        servings=2,
        ingredients=[RecipeIngredient(product_id=ProductId(2), quantity=Quantity(200.0, "g"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: pieces_r if rid == RecipeId(1) else normal_r
    )
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = (
        lambda pid: flour if pid == ProductId(1) else sugar
    )

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            # pieces: pieces_override=5 → scale=0.5 → 250g flour
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1), pieces_override=5),
            # normal: no override → scale=1.0 → 200g sugar
            MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(2)),
        ],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    assert len(result.items) == 2
    by_product = {item.product_id: item.quantity for item in result.items}
    assert by_product[ProductId(1)] == Quantity(250.0, "g")
    assert by_product[ProductId(2)] == Quantity(200.0, "g")


# 5. minimum one piece: 0.1 * 2 = 0.2 → round=0 → max(1,0)=1
def test_pieces_mode_minimum_one_piece() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    # total_pieces=10, pieces_per_portion=2, amount=500g
    recipe = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        # servings_override=0.1 → pcs = max(1, round(0.1*2)) = max(1, round(0.2)) = max(1,0) = 1
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=0.1)],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # scale = 1/10 = 0.1; 500g * 0.1 = 50g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(50.0, "g")


# 6. rounding: 2.1 * 2 = 4.2 → round=4
def test_pieces_mode_rounding() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)
    recipe = _pieces_recipe(1, 1, amount=500.0, total_pieces=10, pieces_per_portion=2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        # servings_override=2.1 → pcs = max(1, round(2.1*2)) = max(1, round(4.2)) = 4
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1),
                        servings_override=2.1)],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # scale = 4/10 = 0.4; 500g * 0.4 = 200g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(200.0, "g")


# 7. normal parent with pieces sub-recipe
def test_nested_pieces_recipe_in_normal_parent() -> None:
    flour = _product(1, "g", "g", 1.0, 5.0)

    # pieces sub-recipe: total_pieces=10, pieces_per_portion=2, 500g flour, servings=4
    sub_recipe = Recipe(
        id=RecipeId(2),
        name="PiecesSub",
        servings=4,
        total_pieces=10,
        pieces_per_portion=2,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(500.0, "g"))],
    )
    # normal parent: 1 serving, uses 3 serv of sub-recipe
    parent_recipe = Recipe(
        id=RecipeId(1),
        name="Parent",
        servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(3.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu)

    # parent: scale_factor=1.0 (1 serv / 1 serv)
    # sub-recipe ingredient: scaled_amount = 3.0 * 1.0 = 3.0 serv
    # sub_recipe.is_pieces_mode=True: pcs = max(1, round(3.0 * 2)) = 6
    # sub_scale = 6 / 10 = 0.6
    # flour: 500g * 0.6 = 300g
    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(300.0, "g")


# ---- build_filtered ----

def test_build_filtered_uses_only_selected_slots() -> None:
    product1 = _product(1)
    product2 = _product(2)
    recipe1 = _recipe(1, 1, amount=200.0, base_servings=2)
    recipe2 = _recipe(2, 2, amount=300.0, base_servings=3)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: {RecipeId(1): recipe1, RecipeId(2): recipe2}.get(rid)
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: {ProductId(1): product1, ProductId(2): product2}.get(pid)

    builder_obj = _builder(recipe_repo, product_repo)
    menu = WeeklyMenu(MenuId(1), "Test", [
        MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),   # index 0
        MenuSlot(day=1, meal_type="lunch", recipe_id=RecipeId(2)),   # index 1
        MenuSlot(day=2, meal_type="dinner", recipe_id=RecipeId(1)),  # index 2
    ])

    result = builder_obj.build_filtered(menu, {0, 2})
    product_ids = {item.product_id for item in result.items}
    assert ProductId(1) in product_ids
    assert ProductId(2) not in product_ids


def test_build_filtered_empty_indices_returns_empty_list() -> None:
    recipe1 = _recipe(1, 1, amount=200.0, base_servings=2)
    product1 = _product(1)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe1
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = product1

    builder_obj = _builder(recipe_repo, product_repo)
    menu = WeeklyMenu(MenuId(1), "Test", [
        MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
    ])

    result = builder_obj.build_filtered(menu, set())
    assert result.items == []


def test_build_filtered_all_indices_matches_build() -> None:
    recipe1 = _recipe(1, 1, amount=200.0, base_servings=2)
    recipe2 = _recipe(2, 2, amount=400.0, base_servings=2)
    product1 = _product(1)
    product2 = _product(2)

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: {RecipeId(1): recipe1, RecipeId(2): recipe2}.get(rid)
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: {ProductId(1): product1, ProductId(2): product2}.get(pid)

    builder_obj = _builder(recipe_repo, product_repo)
    menu = WeeklyMenu(MenuId(1), "Test", [
        MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
        MenuSlot(day=1, meal_type="dinner", recipe_id=RecipeId(2)),
    ])

    full_result = builder_obj.build(menu)
    filtered_result = builder_obj.build_filtered(menu, {0, 1})

    full_ids = {item.product_id for item in full_result.items}
    filtered_ids = {item.product_id for item in filtered_result.items}
    assert full_ids == filtered_ids


# ---- resolve_recipe_ingredients_tree ----

from backend.domain.services.shopping_list_builder import IngredientNode  # noqa: E402


def test_resolve_recipe_ingredients_tree_simple() -> None:
    """2 product ingredients, scale_factor=2.0 → doubled amounts."""
    pid1, pid2 = ProductId(1), ProductId(2)
    p1 = _product(1, "g", "g", 1.0, 5.0)
    p2 = _product(2, "ml", "ml", 1.0, 3.0)

    recipe = Recipe(
        id=RecipeId(1), name="R", servings=2,
        ingredients=[
            RecipeIngredient(product_id=pid1, quantity=Quantity(100.0, "g")),
            RecipeIngredient(product_id=pid2, quantity=Quantity(50.0, "ml")),
        ],
    )

    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: p1 if pid == pid1 else p2

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(recipe, 2.0)

    assert len(nodes) == 2
    node_by_pid = {n.product_id: n for n in nodes}
    assert node_by_pid[pid1].quantity_amount == 200.0
    assert node_by_pid[pid1].quantity_unit == "g"
    assert node_by_pid[pid2].quantity_amount == 100.0
    assert node_by_pid[pid2].quantity_unit == "ml"


def test_resolve_recipe_ingredients_tree_with_sub_recipe() -> None:
    """1 product + 1 sub-recipe ingredient → product node + sub-recipe node with children."""
    flour = _product(1, "g", "g", 1.0, 5.0)

    sub_recipe = Recipe(
        id=RecipeId(2), name="Соус", servings=2,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
    )
    parent_recipe = Recipe(
        id=RecipeId(1), name="Паста", servings=1,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(50.0, "g")),
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(1.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = flour

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(parent_recipe, 1.0)

    assert len(nodes) == 2
    product_nodes = [n for n in nodes if n.product_id is not None]
    sub_nodes = [n for n in nodes if n.sub_recipe_id is not None]

    assert len(product_nodes) == 1
    assert product_nodes[0].quantity_amount == 50.0

    assert len(sub_nodes) == 1
    assert sub_nodes[0].sub_recipe_name == "Соус"
    assert len(sub_nodes[0].children) == 1
    assert sub_nodes[0].children[0].product_id == ProductId(1)


def test_resolve_recipe_ingredients_tree_missing_product() -> None:
    """Product not in repo → 'Продукт не найден' fallback in product_name."""
    recipe = Recipe(
        id=RecipeId(1), name="R", servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(99), quantity=Quantity(100.0, "g"))],
    )

    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = None  # product not found

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(recipe, 1.0)

    assert len(nodes) == 1
    assert "Продукт не найден" in nodes[0].product_name
    assert "99" in nodes[0].product_name


def test_resolve_recipe_ingredients_tree_missing_sub_recipe() -> None:
    """Sub-recipe not in repo → node with sub_recipe_id set and no children."""
    recipe = Recipe(
        id=RecipeId(1), name="R", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(99), quantity=Quantity(1.0, "serv"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = None  # sub-recipe not found
    product_repo = MagicMock()

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(recipe, 1.0)

    assert len(nodes) == 1
    node = nodes[0]
    assert node.sub_recipe_id == RecipeId(99)
    assert node.children == []


def test_resolve_recipe_ingredients_tree_cycle_guard() -> None:
    """Recipe referencing itself produces empty result without infinite recursion."""
    recipe = Recipe(
        id=RecipeId(1), name="Self-ref", servings=1,
        ingredients=[RecipeIngredient(sub_recipe_id=RecipeId(1), quantity=Quantity(1.0, "serv"))],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    product_repo = MagicMock()

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(recipe, 1.0)

    # The sub-recipe ingredient resolves to empty (cycle guard) → one sub-recipe node with no children
    assert len(nodes) == 1
    assert nodes[0].sub_recipe_id == RecipeId(1)
    assert nodes[0].children == []


def test_resolve_recipe_ingredients_tree_zero_weight_sub_recipe() -> None:
    """Sub-recipe with weight=0 referenced by weight → node with empty children list."""
    sub_recipe = Recipe(
        id=RecipeId(2), name="Начинка", servings=2, weight=0,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(100.0, "g")),
        ],
    )
    parent_recipe = Recipe(
        id=RecipeId(1), name="Пирог", servings=1,
        ingredients=[
            RecipeIngredient(sub_recipe_id=RecipeId(2), quantity=Quantity(300.0, "g")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = (
        lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    )
    product_repo = MagicMock()

    builder_obj = _builder(recipe_repo, product_repo)
    nodes = builder_obj.resolve_recipe_ingredients_tree(parent_recipe, 1.0)

    assert len(nodes) == 1
    node = nodes[0]
    assert node.sub_recipe_id == RecipeId(2)
    assert node.sub_recipe_name == "Начинка"
    assert node.children == []


# ---- build_filtered with excluded_sub_recipe_ids ----


def test_build_filtered_excludes_sub_recipe_ids() -> None:
    """Sub-recipe whose ID is in excluded_sub_recipe_ids should not contribute products."""
    sub_product = _product(2)  # only in sub-recipe
    top_product = _product(1)  # only in top-level recipe

    sub_recipe = Recipe(
        id=RecipeId(10),
        name="Соус",
        servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(2), quantity=Quantity(100.0, "g"))],
    )
    parent_recipe = Recipe(
        id=RecipeId(1),
        name="Паста",
        servings=1,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g")),
            RecipeIngredient(sub_recipe_id=RecipeId(10), quantity=Quantity(1.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: {ProductId(1): top_product, ProductId(2): sub_product}.get(pid)

    builder_obj = _builder(recipe_repo, product_repo)
    menu = WeeklyMenu(MenuId(1), "Test", [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1)),
    ])

    result = builder_obj.build_filtered(menu, {0}, excluded_sub_recipe_ids={RecipeId(10)})

    product_ids = {item.product_id for item in result.items}
    assert ProductId(1) in product_ids       # top-level ingredient present
    assert ProductId(2) not in product_ids   # sub-recipe ingredient excluded


def test_build_filtered_excluded_sub_recipe_ids_empty_set_includes_all() -> None:
    """Passing an empty excluded_sub_recipe_ids set should include all products."""
    sub_product = _product(2)
    top_product = _product(1)

    sub_recipe = Recipe(
        id=RecipeId(10),
        name="Соус",
        servings=1,
        ingredients=[RecipeIngredient(product_id=ProductId(2), quantity=Quantity(100.0, "g"))],
    )
    parent_recipe = Recipe(
        id=RecipeId(1),
        name="Паста",
        servings=1,
        ingredients=[
            RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g")),
            RecipeIngredient(sub_recipe_id=RecipeId(10), quantity=Quantity(1.0, "serv")),
        ],
    )

    recipe_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: parent_recipe if rid == RecipeId(1) else sub_recipe
    product_repo = MagicMock()
    product_repo.get_by_id.side_effect = lambda pid: {ProductId(1): top_product, ProductId(2): sub_product}.get(pid)

    builder_obj = _builder(recipe_repo, product_repo)
    menu = WeeklyMenu(MenuId(1), "Test", [
        MenuSlot(day=0, meal_type="обед", recipe_id=RecipeId(1)),
    ])

    result = builder_obj.build_filtered(menu, {0}, excluded_sub_recipe_ids=set())

    product_ids = {item.product_id for item in result.items}
    assert ProductId(1) in product_ids   # top-level ingredient present
    assert ProductId(2) in product_ids   # sub-recipe ingredient also present
