"""Tests for recipe cost endpoints."""

from decimal import Decimal
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.application.paginated_result import PAGE_SIZE, PaginatedResult
from backend.domain.entities.recipe import Recipe
from backend.domain.services.recipe_cost_calculator import RecipeCostResult
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId


def _recipe(id: int = 1) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Борщ",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Варить")],
        category_id=RecipeCategoryId(1),
        weight=2400,
    )


def _cost_result(
    cost: Decimal | None = Decimal("85.30"),
    partial: bool = False,
) -> RecipeCostResult:
    return RecipeCostResult(
        cost_per_portion=cost,
        total_cost=cost * 4 if cost else None,
        currency="RUB" if cost else None,
        is_partial=partial,
        computed_servings=4,
        ingredient_costs=[],
    )


class TestListRecipesWithCost:
    def test_includes_cost_fields(self, client: TestClient, container: MagicMock) -> None:
        container.list_recipes.execute.return_value = PaginatedResult(
            items=[_recipe(1)], total=1, page=1, page_size=PAGE_SIZE,
        )
        container.calculate_recipe_cost.execute.return_value = _cost_result()
        resp = client.get("/api/recipes", params={"page": 1})
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["cost_per_portion"] == 85.30
        assert item["cost_currency"] == "RUB"
        assert item["cost_is_partial"] is False

    def test_null_cost_when_no_ingredients(self, client: TestClient, container: MagicMock) -> None:
        container.list_recipes.execute.return_value = PaginatedResult(
            items=[_recipe(1)], total=1, page=1, page_size=PAGE_SIZE,
        )
        container.calculate_recipe_cost.execute.return_value = _cost_result(cost=None)
        resp = client.get("/api/recipes", params={"page": 1})
        item = resp.json()["items"][0]
        assert item["cost_per_portion"] is None

    def test_partial_cost_flag(self, client: TestClient, container: MagicMock) -> None:
        container.list_recipes.execute.return_value = PaginatedResult(
            items=[_recipe(1)], total=1, page=1, page_size=PAGE_SIZE,
        )
        container.calculate_recipe_cost.execute.return_value = _cost_result(partial=True)
        resp = client.get("/api/recipes", params={"page": 1})
        item = resp.json()["items"][0]
        assert item["cost_is_partial"] is True


class TestGetRecipeWithCost:
    def test_includes_cost_fields(self, client: TestClient, container: MagicMock) -> None:
        container.get_recipe.execute.return_value = _recipe(1)
        container.calculate_recipe_cost.execute.return_value = _cost_result()
        resp = client.get("/api/recipes/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cost_per_portion"] == 85.30
        assert data["cost_currency"] == "RUB"
        assert data["cost_is_partial"] is False

    def test_null_cost_on_missing_recipe_cost(self, client: TestClient, container: MagicMock) -> None:
        container.get_recipe.execute.return_value = _recipe(1)
        container.calculate_recipe_cost.execute.return_value = _cost_result(cost=None)
        resp = client.get("/api/recipes/1")
        assert resp.json()["cost_per_portion"] is None


class TestCostPreview:
    def test_returns_cost_preview(self, client: TestClient, container: MagicMock) -> None:
        container.preview_recipe_cost.execute.return_value = _cost_result()
        resp = client.post("/api/recipes/cost-preview", json={
            "ingredients": [{"product_id": 1, "quantity_amount": 200, "quantity_unit": "g"}],
            "servings": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["cost_per_portion"] == 85.30
        assert data["cost_currency"] == "RUB"
        assert data["computed_servings"] == 4

    def test_null_cost_preview(self, client: TestClient, container: MagicMock) -> None:
        container.preview_recipe_cost.execute.return_value = _cost_result(cost=None)
        resp = client.post("/api/recipes/cost-preview", json={
            "ingredients": [{"product_id": 1, "quantity_amount": 200, "quantity_unit": "g"}],
            "servings": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["cost_per_portion"] is None


class TestCreateUpdateRecipeWithCost:
    def test_create_includes_cost(self, client: TestClient, container: MagicMock) -> None:
        container.create_recipe.execute.return_value = _recipe(1)
        container.calculate_recipe_cost.execute.return_value = _cost_result()
        resp = client.post("/api/recipes", json={
            "name": "Борщ", "category_id": 1, "servings": 4, "weight": 0,
        })
        assert resp.status_code == 201
        assert resp.json()["cost_per_portion"] == 85.30

    def test_update_includes_cost(self, client: TestClient, container: MagicMock) -> None:
        container.edit_recipe.execute.return_value = _recipe(1)
        container.calculate_recipe_cost.execute.return_value = _cost_result()
        resp = client.put("/api/recipes/1", json={
            "name": "Борщ", "category_id": 1, "servings": 4, "weight": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["cost_per_portion"] == 85.30
