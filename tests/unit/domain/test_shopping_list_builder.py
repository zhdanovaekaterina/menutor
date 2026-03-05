from decimal import Decimal
from unittest.mock import MagicMock

from src.domain.entities.family_member import FamilyMember
from src.domain.entities.menu import MenuSlot, WeeklyMenu
from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.domain.services.portion_calculator import PortionCalculator
from src.domain.services.shopping_list_builder import ShoppingListBuilder
from src.domain.services.unit_converter import UnitConverter
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import (
    FamilyMemberId,
    MenuId,
    ProductCategoryId,
    ProductId,
    RecipeId,
)


def _product(pid: int, recipe_unit: str = "g", purchase_unit: str = "kg",
             conversion_factor: float = 0.001, price: float = 100.0) -> Product:
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
        ingredients=[RecipeIngredient(ProductId(pid), Quantity(amount, recipe_unit))],
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


def _member(mid: int, multiplier: float = 1.0) -> FamilyMember:
    return FamilyMember(FamilyMemberId(mid), f"M{mid}", portion_multiplier=multiplier)


# ---- single slot ----

def test_single_slot_quantity_and_cost() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 0.001, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # 1 adult (1.0), base=2 → total=2.0 → scale factor 1.0 → 200g → 0.2 kg → 20 RUB
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1, 1.0)])

    assert len(result.items) == 1
    item = result.items[0]
    assert item.quantity == Quantity(0.2, "kg")
    assert item.cost == Money(Decimal("20.0"))


def test_single_slot_no_members_uses_base_servings() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 0.001, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    # No members → base_servings=2 used directly → 200g → 0.2 kg
    result = _builder(recipe_repo, product_repo).build(menu, [])

    assert result.items[0].quantity == Quantity(0.2, "kg")


# ---- aggregation ----

def test_two_slots_same_ingredient_aggregated() -> None:
    r1 = _recipe(1, 1, amount=200.0, base_servings=2)
    r2 = _recipe(2, 1, amount=300.0, base_servings=2)
    product = _product(1, "g", "kg", 0.001, 100.0)

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
    # 1 adult, both recipes scaled 1:1 → 200g + 300g = 500g → 0.5 kg
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1, 1.0)])

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(0.5, "kg")


def test_two_different_products_two_items() -> None:
    r1 = _recipe(1, 1, amount=200.0, base_servings=2)
    r2 = _recipe(2, 2, amount=400.0, base_servings=2)
    p1 = _product(1, "g", "kg", 0.001, 100.0)
    p2 = _product(2, "g", "kg", 0.001, 50.0)

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
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1, 1.0)])

    assert len(result.items) == 2


# ---- family portion scaling ----

def test_family_portion_scaling() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=100.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "g", 1.0, 10.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="dinner", recipe_id=RecipeId(1))],
    )
    members = [_member(1, 1.0), _member(2, 1.0), _member(3, 0.5)]
    # total = (1+1+0.5)*2 = 5.0 servings, scale 100g → 250g, factor 1.0 → 250g
    result = _builder(recipe_repo, product_repo).build(menu, members)

    assert result.items[0].quantity == Quantity(250.0, "g")


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
    # override=4.0, members=[1.0] → total=(4*1.0)=4.0 → scale 100g*(4/2)=200g
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1, 1.0)])

    assert result.items[0].quantity == Quantity(200.0, "g")


# ---- shopping list helpers ----

def test_total_cost() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 0.001, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1))],
    )
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1)])

    assert result.total_cost() == Money(Decimal("20.0"))


def test_items_by_category() -> None:
    r1 = _recipe(1, 1, amount=200.0, recipe_unit="g", base_servings=2)
    r2 = _recipe(2, 2, amount=100.0, recipe_unit="ml", base_servings=2)
    p1 = Product(
        id=ProductId(1), name="Flour", recipe_unit="g", purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=0.001, category_id=ProductCategoryId(1),
    )
    p2 = Product(
        id=ProductId(2), name="Milk", recipe_unit="ml", purchase_unit="l",
        price_per_purchase_unit=Money(Decimal("90")),
        conversion_factor=0.001, category_id=ProductCategoryId(2),
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
    result = _builder(recipe_repo, product_repo, product_category_repo).build(menu, [_member(1)])
    by_cat = result.items_by_category()

    assert "dry" in by_cat
    assert "dairy" in by_cat
    assert len(by_cat["dry"]) == 1
    assert len(by_cat["dairy"]) == 1


# ---- standalone product slots ----

def test_standalone_product_slot_adds_quantity_directly() -> None:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 0.001, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[MenuSlot(day=0, meal_type="lunch", product_id=ProductId(1),
                        quantity=500.0, unit="g")],
    )
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1)])

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
    # Two family members shouldn't affect standalone product quantity
    result = _builder(recipe_repo, product_repo).build(
        menu, [_member(1, 1.0), _member(2, 1.0)]
    )

    assert result.items[0].quantity == Quantity(200.0, "g")


def test_product_slot_aggregates_with_recipe_ingredient() -> None:
    """A standalone product and a recipe using the same product should aggregate."""
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.return_value = _recipe(1, 1, amount=200.0, base_servings=2)
    product_repo.get_by_id.return_value = _product(1, "g", "kg", 0.001, 100.0)

    menu = WeeklyMenu(
        id=MenuId(1), name="Week",
        slots=[
            MenuSlot(day=0, meal_type="lunch", recipe_id=RecipeId(1)),
            MenuSlot(day=1, meal_type="lunch", product_id=ProductId(1),
                     quantity=300.0, unit="g"),
        ],
    )
    # Recipe: 200g (1 member, base 2 → scale 1.0) + standalone: 300g = 500g → 0.5 kg
    result = _builder(recipe_repo, product_repo).build(menu, [_member(1, 1.0)])

    assert len(result.items) == 1
    assert result.items[0].quantity == Quantity(0.5, "kg")
