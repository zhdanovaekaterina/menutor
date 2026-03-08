from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.manage_product import (
    CreateProduct,
    DeleteProduct,
    EditProduct,
    GetProduct,
    ListProducts,
    ProductData,
    UpdateProductPrice,
)
from src.domain.entities.product import Product
from src.domain.value_objects.money import Money
from src.domain.value_objects.types import ProductCategoryId, ProductId


def _data(**kwargs) -> ProductData:
    defaults = dict(
        name="Мука",
        category_id=ProductCategoryId(1),
        recipe_unit="g",
        purchase_unit="kg",
        price=Money(Decimal("80")),
        brand="",
        weight_per_piece_g=None,
        conversion_factor=0.001,
    )
    defaults.update(kwargs)
    return ProductData(**defaults)


def _saved_product(id: int = 1) -> Product:
    return Product(
        id=ProductId(id),
        name="Мука",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        conversion_factor=0.001,
        category_id=ProductCategoryId(1),
    )


# ---- CreateProduct ----

def test_create_product_calls_save() -> None:
    repo = MagicMock()
    repo.save.return_value = _saved_product()

    result = CreateProduct(repo).execute(_data())

    repo.save.assert_called_once()
    assert result == _saved_product()


def test_create_product_builds_entity_correctly() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda p: p

    result = CreateProduct(repo).execute(_data(name="Сахар", conversion_factor=0.001))

    assert result.name == "Сахар"
    assert result.conversion_factor == 0.001


# ---- EditProduct ----

def test_edit_product_updates_fields() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_product()
    repo.save.side_effect = lambda p: p

    result = EditProduct(repo).execute(ProductId(1), _data(name="Сахар"))

    assert result.name == "Сахар"
    assert result.id == ProductId(1)


def test_edit_product_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найден"):
        EditProduct(repo).execute(ProductId(999), _data())


# ---- DeleteProduct ----

def test_delete_product_calls_repo_delete() -> None:
    repo = MagicMock()

    DeleteProduct(repo).execute(ProductId(1))

    repo.delete.assert_called_once_with(ProductId(1))


# ---- UpdateProductPrice ----

def test_update_price_changes_price_and_saves() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_product()
    repo.save.side_effect = lambda p: p
    new_price = Money(Decimal("120"))

    result = UpdateProductPrice(repo).execute(ProductId(1), new_price)

    assert result.price_per_purchase_unit == new_price
    repo.save.assert_called_once()


def test_update_price_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найден"):
        UpdateProductPrice(repo).execute(ProductId(999), Money(Decimal("100")))


# ---- GetProduct / ListProducts ----

def test_get_product_returns_entity() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved_product()
    assert GetProduct(repo).execute(ProductId(1)) == _saved_product()


def test_list_products_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_saved_product(1), _saved_product(2)]
    assert len(ListProducts(repo).execute()) == 2
