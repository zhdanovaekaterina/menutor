"""Unit tests for Product domain entity — compute_purchase and purchase_cost methods."""

from decimal import Decimal

import pytest

from src.domain.entities.product import Product
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.types import ProductCategoryId, ProductId


@pytest.fixture
def flour() -> Product:
    return Product(
        id=ProductId(1),
        name="Мука",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=0.001,
        category_id=ProductCategoryId(1),
    )


@pytest.fixture
def milk() -> Product:
    return Product(
        id=ProductId(2),
        name="Молоко",
        recipe_unit="ml",
        purchase_unit="l",
        price_per_purchase_unit=Money(Decimal("90")),
        conversion_factor=0.001,
        category_id=ProductCategoryId(2),
    )


@pytest.fixture
def eggs() -> Product:
    """Product with 1:1 conversion factor (pcs → pcs)."""
    return Product(
        id=ProductId(3),
        name="Яйца",
        recipe_unit="pcs",
        purchase_unit="pcs",
        price_per_purchase_unit=Money(Decimal("12")),
        conversion_factor=1.0,
    )


class TestComputePurchase:
    def test_grams_to_kg(self, flour: Product) -> None:
        purchase_qty, cost = flour.compute_purchase(200.0)
        assert purchase_qty.amount == pytest.approx(0.2)
        assert purchase_qty.unit == "kg"
        assert cost == Money(Decimal("80")) * 0.2

    def test_ml_to_l(self, milk: Product) -> None:
        purchase_qty, cost = milk.compute_purchase(500.0)
        assert purchase_qty.amount == pytest.approx(0.5)
        assert purchase_qty.unit == "l"
        assert cost == Money(Decimal("90")) * 0.5

    def test_identity_conversion(self, eggs: Product) -> None:
        purchase_qty, cost = eggs.compute_purchase(10.0)
        assert purchase_qty.amount == pytest.approx(10.0)
        assert purchase_qty.unit == "pcs"
        assert cost == Money(Decimal("12")) * 10.0

    def test_zero_amount(self, flour: Product) -> None:
        purchase_qty, cost = flour.compute_purchase(0.0)
        assert purchase_qty.amount == pytest.approx(0.0)
        assert cost == Money(Decimal("80")) * 0.0


class TestPurchaseCost:
    def test_cost_for_purchase_amount(self, flour: Product) -> None:
        cost = flour.purchase_cost(0.5)
        assert cost == Money(Decimal("80")) * 0.5

    def test_cost_for_zero(self, flour: Product) -> None:
        cost = flour.purchase_cost(0.0)
        assert cost == Money(Decimal("80")) * 0.0

    def test_cost_for_whole_unit(self, milk: Product) -> None:
        cost = milk.purchase_cost(1.0)
        assert cost == Money(Decimal("90")) * 1.0
