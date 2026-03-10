from unittest.mock import MagicMock

from backend.application.use_cases.manage_product import ListProductCategories
from backend.application.use_cases.manage_recipe import ListRecipeCategories


def test_list_product_categories_returns_active() -> None:
    repo = MagicMock()
    repo.find_active.return_value = [(1, "Молочные"), (2, "Мясо"), (3, "Сыпучие")]

    result = ListProductCategories(repo).execute()

    repo.find_active.assert_called_once()
    assert result == [(1, "Молочные"), (2, "Мясо"), (3, "Сыпучие")]


def test_list_product_categories_empty() -> None:
    repo = MagicMock()
    repo.find_active.return_value = []

    result = ListProductCategories(repo).execute()

    assert result == []


def test_list_recipe_categories_returns_active() -> None:
    repo = MagicMock()
    repo.find_active.return_value = [(1, "Завтраки"), (2, "Обеды"), (3, "Ужины")]

    result = ListRecipeCategories(repo).execute()

    repo.find_active.assert_called_once()
    assert result == [(1, "Завтраки"), (2, "Обеды"), (3, "Ужины")]


def test_list_recipe_categories_empty() -> None:
    repo = MagicMock()
    repo.find_active.return_value = []

    result = ListRecipeCategories(repo).execute()

    assert result == []
