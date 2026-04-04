"""Tests for RecipeCostCalculator domain service."""

from decimal import Decimal

from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.services.recipe_cost_calculator import RecipeCostCalculator
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductCategoryId, ProductId, RecipeCategoryId, RecipeId


def _product(
    id: int,
    price: Decimal = Decimal("100"),
    recipe_unit: str = "g",
    purchase_unit: str = "kg",
    conversion_factor: float = 1000.0,
) -> Product:
    return Product(
        id=ProductId(id),
        name=f"Product {id}",
        recipe_unit=recipe_unit,
        purchase_unit=purchase_unit,
        price_per_purchase_unit=Money(price),
        conversion_factor=conversion_factor,
        category_id=ProductCategoryId(1),
    )


def _recipe(
    servings: int = 4,
    total_pieces: int | None = None,
    pieces_per_portion: int | None = None,
) -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Test",
        servings=servings,
        category_id=RecipeCategoryId(1),
        total_pieces=total_pieces,
        pieces_per_portion=pieces_per_portion,
    )


class TestRecipeCostCalculator:
    def setup_method(self) -> None:
        self.calc = RecipeCostCalculator()

    def test_empty_products_returns_none(self) -> None:
        result = self.calc.calculate(_recipe(), {}, {})
        assert result.cost_per_portion is None
        assert result.is_partial is False

    def test_single_product_cost(self) -> None:
        """200g of flour at 100 RUB/kg -> 0.2kg -> 20 RUB total, 5 RUB/portion (4 servings)."""
        product = _product(1, Decimal("100"), "g", "kg", 1000.0)
        flat = {ProductId(1): Quantity(200.0, "g")}
        lookup = {ProductId(1): product}
        result = self.calc.calculate(_recipe(servings=4), flat, lookup)
        assert result.cost_per_portion == Decimal("5.00")
        assert result.total_cost == Decimal("20.00")
        assert result.currency == "RUB"
        assert result.is_partial is False

    def test_zero_price_marks_partial(self) -> None:
        product = _product(1, Decimal("0"))
        flat = {ProductId(1): Quantity(200.0, "g")}
        lookup = {ProductId(1): product}
        result = self.calc.calculate(_recipe(), flat, lookup)
        assert result.is_partial is True
        assert result.cost_per_portion is not None  # still calculated (as 0)

    def test_missing_product_marks_partial(self) -> None:
        flat = {ProductId(1): Quantity(200.0, "g")}
        lookup: dict = {}
        result = self.calc.calculate(_recipe(), flat, lookup)
        assert result.is_partial is True

    def test_pieces_mode_cost(self) -> None:
        """12 pieces, 3 per portion -> 4 servings. Total cost / 4."""
        product = _product(1, Decimal("100"), "g", "kg", 1000.0)
        flat = {ProductId(1): Quantity(1200.0, "g")}
        lookup = {ProductId(1): product}
        recipe = _recipe(servings=12, total_pieces=12, pieces_per_portion=3)
        result = self.calc.calculate(recipe, flat, lookup)
        # 1200g -> 1.2kg -> 120 RUB / 4 portions = 30 RUB
        assert result.cost_per_portion == Decimal("30.00")
        assert result.computed_servings == 4

    def test_multiple_products(self) -> None:
        p1 = _product(1, Decimal("100"), "g", "kg", 1000.0)
        p2 = _product(2, Decimal("80"), "ml", "l", 1000.0)
        flat = {ProductId(1): Quantity(500.0, "g"), ProductId(2): Quantity(400.0, "ml")}
        lookup = {ProductId(1): p1, ProductId(2): p2}
        result = self.calc.calculate(_recipe(servings=4), flat, lookup)
        # p1: 500g -> 0.5kg -> 50 RUB; p2: 400ml -> 0.4L -> 32 RUB; total 82 RUB / 4 = 20.50
        assert result.cost_per_portion == Decimal("20.50")

    def test_ingredient_costs_breakdown(self) -> None:
        product = _product(1, Decimal("100"), "g", "kg", 1000.0)
        flat = {ProductId(1): Quantity(200.0, "g")}
        lookup = {ProductId(1): product}
        result = self.calc.calculate(_recipe(servings=4), flat, lookup)
        assert len(result.ingredient_costs) == 1
        ic = result.ingredient_costs[0]
        assert ic.product_name == "Product 1"
        assert ic.has_price is True
        assert ic.cost is not None
        assert ic.cost.amount == Decimal("20.00")  # 200g -> 0.2kg -> 20 RUB
