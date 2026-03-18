from decimal import Decimal
from unittest.mock import MagicMock

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.services.shopping_list_builder import ShoppingListBuilder
from backend.domain.services.unit_converter import UnitConverter
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
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
        (ProductCategoryId(1), "dry"), (ProductCategoryId(2), "dairy"),
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
