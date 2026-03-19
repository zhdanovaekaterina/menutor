"""Tests for /api/recipes router."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.application.use_cases.flatten_recipe_products import FlattenedProduct
from backend.application.use_cases.preview_flattened_products import IngredientData
from backend.application.use_cases.validate_sub_recipe import ValidationResult
from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import EntityNotFoundError, SubRecipeWeightError
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import ProductId, RecipeCategoryId, RecipeId


def _recipe(id: int = 1, total_pieces: int | None = None, pieces_per_portion: int | None = None) -> Recipe:
    return Recipe(
        id=RecipeId(id),
        name="Блины",
        servings=4,
        ingredients=[RecipeIngredient(product_id=ProductId(1), quantity=Quantity(200.0, "g"))],
        steps=[CookingStep(1, "Смешать")],
        category_id=RecipeCategoryId(1),
        weight=300,
        total_pieces=total_pieces,
        pieces_per_portion=pieces_per_portion,
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


class TestBatchDeleteRecipes:
    def test_batch_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/recipes/batch-delete", json=[1, 2, 3])
        assert resp.status_code == 204
        container.delete_recipe.execute.assert_called_once()
        args = container.delete_recipe.execute.call_args
        assert args[0][0] == [RecipeId(1), RecipeId(2), RecipeId(3)]

    def test_batch_delete_empty_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/recipes/batch-delete", json=[])
        assert resp.status_code == 204


# ---- POST /api/recipes with sub-recipe ingredient ----


class TestCreateRecipeWithSubRecipeIngredient:
    def test_create_recipe_with_sub_recipe_ingredient(
        self, client: TestClient, container: MagicMock
    ) -> None:
        sub_recipe = Recipe(
            id=RecipeId(5),
            name="Соус",
            servings=4,
            ingredients=[],
            steps=[],
            category_id=RecipeCategoryId(1),
        )
        result_recipe = Recipe(
            id=RecipeId(10),
            name="Паста",
            servings=2,
            ingredients=[
                RecipeIngredient(sub_recipe_id=RecipeId(5), quantity=Quantity(1.0, "serv"))
            ],
            steps=[],
            category_id=RecipeCategoryId(1),
        )
        container.create_recipe.execute.return_value = result_recipe
        # get_recipe is called by _make_name_lookup for sub-recipe ingredient
        container.get_recipe.execute.return_value = sub_recipe

        body = {
            "name": "Паста",
            "category_id": 1,
            "servings": 2,
            "ingredients": [
                {"sub_recipe_id": 5, "quantity_amount": 1.0, "quantity_unit": "serv"}
            ],
            "steps": [],
            "weight": 0,
        }
        resp = client.post("/api/recipes", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Паста"
        ing = data["ingredients"][0]
        assert ing["sub_recipe_id"] == 5
        assert ing["product_id"] is None

    def test_backward_compat_product_only_request(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """Old format without sub_recipe_id field still works."""
        container.create_recipe.execute.return_value = _recipe()
        body = {
            "name": "Блины",
            "category_id": 1,
            "servings": 4,
            "ingredients": [
                {"product_id": 1, "quantity_amount": 200.0, "quantity_unit": "g"}
            ],
            "steps": [],
            "weight": 300,
        }
        resp = client.post("/api/recipes", json=body)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Блины"


# ---- GET /api/recipes/{id} includes sub_recipe_name ----


class TestGetRecipeIncludesSubRecipeName:
    def test_get_recipe_includes_sub_recipe_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        sauce = Recipe(
            id=RecipeId(5),
            name="Соус",
            servings=2,
            ingredients=[],
            steps=[],
            category_id=RecipeCategoryId(1),
        )
        pasta = Recipe(
            id=RecipeId(1),
            name="Паста",
            servings=2,
            ingredients=[
                RecipeIngredient(sub_recipe_id=RecipeId(5), quantity=Quantity(1.0, "serv"))
            ],
            steps=[],
            category_id=RecipeCategoryId(1),
        )
        # get_recipe is called first for the main recipe, then again via lookup
        container.get_recipe.execute.side_effect = [pasta, sauce]

        resp = client.get("/api/recipes/1")
        assert resp.status_code == 200
        data = resp.json()
        ing = data["ingredients"][0]
        assert ing["sub_recipe_id"] == 5
        assert ing["sub_recipe_name"] == "Соус"
        assert ing["product_id"] is None


# ---- POST /api/recipes/validate-sub-recipe ----


class TestValidateSubRecipe:
    def test_validate_sub_recipe_valid(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.validate_sub_recipe.execute.return_value = ValidationResult(valid=True)
        body = {"parent_recipe_id": 1, "sub_recipe_id": 2}
        resp = client.post("/api/recipes/validate-sub-recipe", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["error"] is None

    def test_validate_sub_recipe_circular(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.validate_sub_recipe.execute.return_value = ValidationResult(
            valid=False, error="Циклическая зависимость"
        )
        body = {"parent_recipe_id": 1, "sub_recipe_id": 1}
        resp = client.post("/api/recipes/validate-sub-recipe", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["error"] == "Циклическая зависимость"


# ---- GET /api/recipes/{recipe_id}/flattened-products ----


class TestGetFlattenedProducts:
    def test_get_flattened_products(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.flatten_recipe_products.execute.return_value = [
            FlattenedProduct(
                product_id=ProductId(1),
                product_name="Мука",
                quantity=Quantity(200.0, "g"),
            ),
            FlattenedProduct(
                product_id=ProductId(2),
                product_name="Молоко",
                quantity=Quantity(500.0, "ml"),
            ),
        ]
        resp = client.get("/api/recipes/1/flattened-products")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["product_id"] == 1
        assert data[0]["product_name"] == "Мука"
        assert data[0]["quantity_amount"] == 200.0
        assert data[0]["quantity_unit"] == "g"
        assert data[1]["product_id"] == 2


# ---- GET /api/recipes/{recipe_id}/dependents ----


class TestGetRecipeDependents:
    def test_get_dependents_returns_parents(
        self, client: TestClient, container: MagicMock
    ) -> None:
        parent = Recipe(
            id=RecipeId(10),
            name="Борщ",
            servings=4,
            category_id=RecipeCategoryId(1),
        )
        container.delete_recipe.check_dependents.return_value = [parent]
        resp = client.get("/api/recipes/5/dependents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == 10
        assert data[0]["name"] == "Борщ"

    def test_get_dependents_empty(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_recipe.check_dependents.return_value = []
        resp = client.get("/api/recipes/5/dependents")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- POST /api/recipes/{recipe_id}/flattened-products-preview ----


class TestPreviewFlattenedProducts:
    def test_returns_flattened_products_for_given_ingredients(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.preview_flattened_products.execute.return_value = [
            FlattenedProduct(
                product_id=ProductId(1),
                product_name="Мука",
                quantity=Quantity(200.0, "g"),
            ),
            FlattenedProduct(
                product_id=ProductId(2),
                product_name="Молоко",
                quantity=Quantity(500.0, "ml"),
            ),
        ]
        body = {
            "ingredients": [
                {"product_id": 1, "sub_recipe_id": None, "quantity_amount": 200.0, "quantity_unit": "g"},
                {"sub_recipe_id": 5, "product_id": None, "quantity_amount": 1.0, "quantity_unit": "serv"},
            ]
        }
        resp = client.post("/api/recipes/1/flattened-products-preview", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["product_id"] == 1
        assert data[0]["product_name"] == "Мука"
        assert data[0]["quantity_amount"] == 200.0
        assert data[0]["quantity_unit"] == "g"
        assert data[1]["product_id"] == 2
        assert data[1]["product_name"] == "Молоко"

    def test_passes_ingredient_data_to_use_case(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.preview_flattened_products.execute.return_value = []
        body = {
            "ingredients": [
                {"product_id": 3, "sub_recipe_id": None, "quantity_amount": 100.0, "quantity_unit": "g"},
            ]
        }
        resp = client.post("/api/recipes/7/flattened-products-preview", json=body)
        assert resp.status_code == 200
        container.preview_flattened_products.execute.assert_called_once()
        call_args = container.preview_flattened_products.execute.call_args
        recipe_id_arg = call_args[0][0]
        ingredients_arg = call_args[0][2]
        assert int(recipe_id_arg) == 7
        assert len(ingredients_arg) == 1
        assert isinstance(ingredients_arg[0], IngredientData)
        assert ingredients_arg[0].product_id == 3
        assert ingredients_arg[0].quantity_amount == 100.0
        assert ingredients_arg[0].quantity_unit == "g"

    def test_returns_empty_list_when_no_ingredients(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.preview_flattened_products.execute.return_value = []
        body = {"ingredients": []}
        resp = client.post("/api/recipes/1/flattened-products-preview", json=body)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_422_on_missing_body(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/recipes/1/flattened-products-preview", json={})
        assert resp.status_code == 422

    def test_returns_422_when_sub_recipe_weight_error(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.preview_flattened_products.execute.side_effect = SubRecipeWeightError(
            "Рецепт «Соус» имеет нулевой вес. Укажите вес рецепта или используйте порции."
        )
        body = {
            "ingredients": [
                {"sub_recipe_id": 5, "product_id": None, "quantity_amount": 250.0, "quantity_unit": "g"},
            ]
        }
        resp = client.post("/api/recipes/1/flattened-products-preview", json=body)
        assert resp.status_code == 422
        assert "нулевой вес" in resp.json()["detail"]


# ---- DELETE /api/recipes/{recipe_id} with check_dependents ----


class TestDeleteWithCheckDependents:
    def test_delete_with_check_dependents_returns_409(
        self, client: TestClient, container: MagicMock
    ) -> None:
        parent = Recipe(
            id=RecipeId(10),
            name="Борщ",
            servings=4,
            category_id=RecipeCategoryId(1),
        )
        container.delete_recipe.check_dependents.return_value = [parent]
        resp = client.delete("/api/recipes/5?check_dependents=true")
        assert resp.status_code == 409
        data = resp.json()
        assert "dependents" in data
        assert data["dependents"][0]["id"] == 10
        # execute was NOT called since we returned early
        container.delete_recipe.execute.assert_not_called()

    def test_delete_with_check_dependents_no_deps_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_recipe.check_dependents.return_value = []
        resp = client.delete("/api/recipes/5?check_dependents=true")
        assert resp.status_code == 204
        container.delete_recipe.execute.assert_called_once()


# ---- Pieces mode fields ----


class TestPiecesMode:
    def test_create_pieces_recipe(self, client: TestClient, container: MagicMock) -> None:
        """POST /recipes с total_pieces и pieces_per_portion."""
        container.create_recipe.execute.return_value = _recipe(1, total_pieces=10, pieces_per_portion=2)
        resp = client.post("/api/recipes", json={
            "name": "Котлеты", "category_id": 1, "servings": 5,
            "total_pieces": 10, "pieces_per_portion": 2,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_pieces"] == 10
        assert data["pieces_per_portion"] == 2

    def test_create_normal_recipe_pieces_null(self, client: TestClient, container: MagicMock) -> None:
        """POST /recipes без штучных полей -- поля null в ответе."""
        container.create_recipe.execute.return_value = _recipe(1)
        resp = client.post("/api/recipes", json={
            "name": "Борщ", "category_id": 1, "servings": 4,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_pieces"] is None
        assert data["pieces_per_portion"] is None

    def test_get_pieces_recipe(self, client: TestClient, container: MagicMock) -> None:
        """GET /recipes/{id} возвращает штучные поля."""
        container.get_recipe.execute.return_value = _recipe(1, total_pieces=10, pieces_per_portion=2)
        resp = client.get("/api/recipes/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_pieces"] == 10
        assert data["pieces_per_portion"] == 2

    def test_list_recipes_includes_pieces_fields(self, client: TestClient, container: MagicMock) -> None:
        """GET /recipes включает штучные поля."""
        container.list_recipes.execute.return_value = [
            _recipe(1, total_pieces=10, pieces_per_portion=2),
            _recipe(2),
        ]
        resp = client.get("/api/recipes")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["total_pieces"] == 10
        assert data[1]["total_pieces"] is None
