"""Unit tests for RecipeController — verifies use case delegation and error handling."""

from decimal import Decimal
from unittest.mock import MagicMock, call

import pytest

from backend.application.use_cases.manage_recipe import RecipeData
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError, RepositoryError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import (
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
)
from backend.presentation.controllers.recipe_controller import RecipeController


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
def list_products_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def list_categories_uc() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_recipes() -> list[Recipe]:
    return [
        Recipe(id=RecipeId(1), name="Блины", servings=4, category_id=RecipeCategoryId(1)),
        Recipe(id=RecipeId(2), name="Каша", servings=2, category_id=RecipeCategoryId(1)),
    ]


@pytest.fixture
def sample_categories() -> list[tuple[int, str]]:
    return [(1, "Завтраки"), (2, "Обеды")]


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
def controller(
    view: MagicMock,
    create_uc: MagicMock,
    edit_uc: MagicMock,
    delete_uc: MagicMock,
    list_uc: MagicMock,
    list_products_uc: MagicMock,
    list_categories_uc: MagicMock,
    sample_recipes: list[Recipe],
    sample_categories: list[tuple[int, str]],
    sample_products: list[Product],
) -> RecipeController:
    list_uc.execute.return_value = sample_recipes
    list_categories_uc.execute.return_value = sample_categories
    list_products_uc.execute.return_value = sample_products
    return RecipeController(
        view, create_uc, edit_uc, delete_uc, list_uc, list_products_uc, list_categories_uc,
    )


class TestRecipeControllerInit:
    """Tests for controller initialization."""

    def test_connects_signals(self, view: MagicMock, controller: RecipeController) -> None:
        view.create_recipe_requested.connect.assert_called_once()
        view.edit_recipe_requested.connect.assert_called_once()
        view.delete_recipe_requested.connect.assert_called_once()

    def test_refreshes_on_init(
        self,
        view: MagicMock,
        list_uc: MagicMock,
        list_categories_uc: MagicMock,
        list_products_uc: MagicMock,
        controller: RecipeController,
    ) -> None:
        list_uc.execute.assert_called_once()
        list_categories_uc.execute.assert_called_once()
        list_products_uc.execute.assert_called_once()

    def test_sets_view_data_on_init(
        self,
        view: MagicMock,
        sample_recipes: list[Recipe],
        sample_products: list[Product],
        sample_categories: list[tuple[int, str]],
        controller: RecipeController,
    ) -> None:
        view.set_recipes.assert_called_once_with(sample_recipes)
        view.set_products.assert_called_once_with(sample_products)
        view.set_categories.assert_called_once_with(sample_categories)


class TestRecipeControllerCreate:
    """Tests for recipe creation."""

    def test_create_calls_use_case(
        self, create_uc: MagicMock, controller: RecipeController,
    ) -> None:
        data = RecipeData(name="Суп", category_id=RecipeCategoryId(1), servings=4)
        controller._on_create(data)
        create_uc.execute.assert_called_once_with(data)

    def test_create_refreshes_after_success(
        self, list_uc: MagicMock, controller: RecipeController,
    ) -> None:
        data = RecipeData(name="Суп", category_id=RecipeCategoryId(1), servings=4)
        list_uc.execute.reset_mock()
        controller._on_create(data)
        list_uc.execute.assert_called_once()

    def test_create_shows_error_on_failure(
        self, create_uc: MagicMock, view: MagicMock, controller: RecipeController,
    ) -> None:
        create_uc.execute.side_effect = EntityNotFoundError("Имя пустое")
        data = RecipeData(name="", category_id=RecipeCategoryId(1), servings=4)
        controller._on_create(data)
        view.show_error.assert_called_once_with("Имя пустое")


class TestRecipeControllerEdit:
    """Tests for recipe editing."""

    def test_edit_calls_use_case(
        self, edit_uc: MagicMock, controller: RecipeController,
    ) -> None:
        data = RecipeData(name="Блины v2", category_id=RecipeCategoryId(1), servings=4)
        controller._on_edit(1, data)
        edit_uc.execute.assert_called_once_with(RecipeId(1), data)

    def test_edit_shows_error_on_failure(
        self, edit_uc: MagicMock, view: MagicMock, controller: RecipeController,
    ) -> None:
        edit_uc.execute.side_effect = EntityNotFoundError("Рецепт 99 не найден")
        data = RecipeData(name="Блины v2", category_id=RecipeCategoryId(1), servings=4)
        controller._on_edit(99, data)
        view.show_error.assert_called_once_with("Рецепт 99 не найден")


class TestRecipeControllerDelete:
    """Tests for recipe deletion."""

    def test_delete_calls_use_case(
        self, delete_uc: MagicMock, controller: RecipeController,
    ) -> None:
        controller._on_delete(1)
        delete_uc.execute.assert_called_once_with(RecipeId(1))

    def test_delete_refreshes_after_success(
        self, list_uc: MagicMock, controller: RecipeController,
    ) -> None:
        list_uc.execute.reset_mock()
        controller._on_delete(1)
        list_uc.execute.assert_called_once()

    def test_delete_shows_error_on_failure(
        self, delete_uc: MagicMock, view: MagicMock, controller: RecipeController,
    ) -> None:
        delete_uc.execute.side_effect = RepositoryError("DB error")
        controller._on_delete(1)
        view.show_error.assert_called_once_with("DB error")


class TestRecipeControllerRefresh:
    """Tests for manual refresh."""

    def test_refresh_reloads_all_data(
        self,
        list_uc: MagicMock,
        list_categories_uc: MagicMock,
        list_products_uc: MagicMock,
        controller: RecipeController,
    ) -> None:
        list_uc.execute.reset_mock()
        list_categories_uc.execute.reset_mock()
        list_products_uc.execute.reset_mock()
        controller.refresh()
        list_uc.execute.assert_called_once()
        list_categories_uc.execute.assert_called_once()
        list_products_uc.execute.assert_called_once()

    def test_refresh_shows_error_on_failure(
        self, list_uc: MagicMock, view: MagicMock, controller: RecipeController,
    ) -> None:
        list_uc.execute.side_effect = RepositoryError("DB down")
        view.show_error.reset_mock()
        controller.refresh()
        view.show_error.assert_called_once_with("DB down")
