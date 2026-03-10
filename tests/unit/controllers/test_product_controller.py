"""Unit tests for ProductController — verifies use case delegation and error handling."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.manage_product import ProductData
from backend.domain.entities.product import Product
from backend.domain.exceptions import EntityNotFoundError, RepositoryError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId
from backend.presentation.controllers.product_controller import ProductController


@pytest.fixture
def view() -> MagicMock:
    return MagicMock()


@pytest.fixture
def create_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def edit_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def delete_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_categories_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_products() -> list[Product]:
    return [
        Product(
            id=ProductId(1), name="Мука",
            recipe_unit="g", purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("80")),
            category_id=ProductCategoryId(1),
        ),
    ]


@pytest.fixture
def sample_categories() -> list[tuple[int, str]]:
    return [(1, "Бакалея"), (2, "Молочные")]


@pytest.fixture
def controller(
    view: MagicMock,
    create_uc: MagicMock,
    edit_uc: MagicMock,
    delete_uc: MagicMock,
    list_uc: MagicMock,
    list_categories_uc: MagicMock,
    sample_products: list[Product],
    sample_categories: list[tuple[int, str]],
) -> ProductController:
    list_uc.execute.return_value = sample_products
    list_categories_uc.execute.return_value = sample_categories
    return ProductController(view, create_uc, edit_uc, delete_uc, list_uc, list_categories_uc)


class TestProductControllerInit:
    def test_connects_signals(self, view: MagicMock, controller: ProductController) -> None:
        view.create_product_requested.connect.assert_called_once()
        view.edit_product_requested.connect.assert_called_once()
        view.delete_product_requested.connect.assert_called_once()

    def test_sets_view_data_on_init(
        self,
        view: MagicMock,
        sample_products: list[Product],
        sample_categories: list[tuple[int, str]],
        controller: ProductController,
    ) -> None:
        view.set_products.assert_called_once_with(sample_products)
        view.set_categories.assert_called_once_with(sample_categories)


class TestProductControllerCreate:
    def test_create_delegates_to_use_case(
        self, create_uc: MagicMock, controller: ProductController,
    ) -> None:
        data = ProductData(
            name="Сахар", category_id=ProductCategoryId(1),
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("60")),
        )
        controller._on_create(data)
        create_uc.execute.assert_called_once_with(data)

    def test_create_shows_error_on_failure(
        self, create_uc: MagicMock, view: MagicMock, controller: ProductController,
    ) -> None:
        create_uc.execute.side_effect = EntityNotFoundError("Дубликат")
        data = ProductData(
            name="Мука", category_id=ProductCategoryId(1),
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("80")),
        )
        controller._on_create(data)
        view.show_error.assert_called_once_with("Дубликат")


class TestProductControllerEdit:
    def test_edit_delegates_to_use_case(
        self, edit_uc: MagicMock, controller: ProductController,
    ) -> None:
        data = ProductData(
            name="Мука в/с", category_id=ProductCategoryId(1),
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("90")),
        )
        controller._on_edit(1, data)
        edit_uc.execute.assert_called_once_with(ProductId(1), data)

    def test_edit_shows_error_on_not_found(
        self, edit_uc: MagicMock, view: MagicMock, controller: ProductController,
    ) -> None:
        edit_uc.execute.side_effect = EntityNotFoundError("Продукт 99 не найден")
        data = ProductData(
            name="X", category_id=ProductCategoryId(1),
            recipe_unit="g", purchase_unit="kg",
            price=Money(Decimal("1")),
        )
        controller._on_edit(99, data)
        view.show_error.assert_called_once_with("Продукт 99 не найден")


class TestProductControllerDelete:
    def test_delete_delegates_to_use_case(
        self, delete_uc: MagicMock, controller: ProductController,
    ) -> None:
        controller._on_delete(1)
        delete_uc.execute.assert_called_once_with(ProductId(1))

    def test_delete_refreshes_view(
        self, list_uc: MagicMock, controller: ProductController,
    ) -> None:
        list_uc.execute.reset_mock()
        controller._on_delete(1)
        list_uc.execute.assert_called_once()

    def test_delete_shows_error_on_failure(
        self, delete_uc: MagicMock, view: MagicMock, controller: ProductController,
    ) -> None:
        delete_uc.execute.side_effect = RepositoryError("FK constraint")
        controller._on_delete(1)
        view.show_error.assert_called_once_with("FK constraint")
