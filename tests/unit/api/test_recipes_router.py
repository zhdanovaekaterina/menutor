"""Tests for /api/recipes router."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId


def _recipe(id: int = 1) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Блины",
        servings=4,
        ingredients=[RecipeIngredient(ProductId(1), Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Смешать")],
        category_id=RecipeCategoryId(1),
        weight=300,
    )


# ---- GET /api/recipes ----


class TestListRecipes:
    def test_returns_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_recipes.execute.return_value = [_recipe(1), _recipe(2)]
        resp = client.get("/api/recipes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Блины"

    def test_returns_empty_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_recipes.execute.return_value = []
        resp = client.get("/api/recipes")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- GET /api/recipes/categories ----


class TestListRecipeCategories:
    def test_returns_active_categories(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.list_recipe_categories.execute.return_value = [
            ActiveCategory(1, "Завтраки"),
            ActiveCategory(2, "Обеды"),
        ]
        resp = client.get("/api/recipes/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0] == {"id": 1, "name": "Завтраки"}


# ---- GET /api/recipes/{recipe_id} ----


class TestGetRecipe:
    def test_returns_recipe(self, client: TestClient, container: MagicMock) -> None:
        container.get_recipe.execute.return_value = _recipe()
        resp = client.get("/api/recipes/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["name"] == "Блины"
        assert data["servings"] == 4
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["product_id"] == 1
        assert data["ingredients"][0]["quantity_amount"] == 200.0
        assert data["ingredients"][0]["quantity_unit"] == "g"
        assert len(data["steps"]) == 1
        assert data["steps"][0] == {"order": 1, "description": "Смешать"}
        assert data["weight"] == 300

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.get_recipe.execute.return_value = None
        resp = client.get("/api/recipes/999")
        assert resp.status_code == 404


# ---- POST /api/recipes ----


class TestCreateRecipe:
    def test_creates_and_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_recipe.execute.return_value = _recipe()
        body = {
            "name": "Блины",
            "category_id": 1,
            "servings": 4,
            "ingredients": [
                {"product_id": 1, "quantity_amount": 200.0, "quantity_unit": "g"}
            ],
            "steps": [{"order": 1, "description": "Смешать"}],
            "weight": 300,
        }
        resp = client.post("/api/recipes", json=body)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Блины"
        container.create_recipe.execute.assert_called_once()

    def test_creates_with_minimal_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_recipe.execute.return_value = Recipe(
            id=RecipeId(1), name="Каша", servings=2, category_id=RecipeCategoryId(1)
        )
        body = {"name": "Каша", "category_id": 1, "servings": 2}
        resp = client.post("/api/recipes", json=body)
        assert resp.status_code == 201

    def test_returns_422_on_missing_required_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/recipes", json={"name": "Каша"})
        assert resp.status_code == 422


# ---- PUT /api/recipes/{recipe_id} ----


class TestUpdateRecipe:
    def test_updates_and_returns_recipe(
        self, client: TestClient, container: MagicMock
    ) -> None:
        updated = Recipe(
            id=RecipeId(1),
            name="Блины v2",
            servings=6,
            category_id=RecipeCategoryId(1),
        )
        container.edit_recipe.execute.return_value = updated
        body = {"name": "Блины v2", "category_id": 1, "servings": 6}
        resp = client.put("/api/recipes/1", json=body)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Блины v2"
        assert resp.json()["servings"] == 6

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.edit_recipe.execute.side_effect = EntityNotFoundError(
            "Рецепт 999 не найден"
        )
        body = {"name": "Блины v2", "category_id": 1, "servings": 6}
        resp = client.put("/api/recipes/999", json=body)
        assert resp.status_code == 404
        assert "не найден" in resp.json()["detail"]


# ---- DELETE /api/recipes/{recipe_id} ----


class TestDeleteRecipe:
    def test_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/recipes/1")
        assert resp.status_code == 204
        container.delete_recipe.execute.assert_called_once()
