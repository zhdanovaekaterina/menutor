from decimal import Decimal

import pytest

from src.domain.entities.family_member import FamilyMember
from src.domain.entities.product import Product
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import (
    FamilyMemberId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)


@pytest.fixture
def adult1() -> FamilyMember:
    return FamilyMember(FamilyMemberId(1), "Взрослый 1", portion_multiplier=1.0)


@pytest.fixture
def adult2() -> FamilyMember:
    return FamilyMember(FamilyMemberId(2), "Взрослый 2", portion_multiplier=1.0)


@pytest.fixture
def child() -> FamilyMember:
    return FamilyMember(FamilyMemberId(3), "Ребёнок", portion_multiplier=0.5)


@pytest.fixture
def family(adult1: FamilyMember, adult2: FamilyMember, child: FamilyMember) -> list[FamilyMember]:
    return [adult1, adult2, child]


@pytest.fixture
def flour() -> Product:
    return Product(
        id=ProductId(1),
        name="Мука",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=1000,
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
        conversion_factor=1000,
        category_id=ProductCategoryId(2),
    )


@pytest.fixture
def pancake_recipe(flour: Product, milk: Product) -> Recipe:
    return Recipe(
        id=RecipeId(1),
        name="Блины",
        servings=4,
        ingredients=[
            RecipeIngredient(flour.id, Quantity(200.0, "g")),
            RecipeIngredient(milk.id, Quantity(500.0, "ml")),
        ],
        category_id=RecipeCategoryId(1),
    )
