"""Tests for /api/product-categories and /api/recipe-categories routers."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.domain.value_objects.category import Category


def _categories() -> list[Category]:
    return [
        Category(1, "Сыпучие", True),
        Category(2, "Молочные", True),
        Category(3, "Удалённая", False),
    ]


class TestProductCategories:
    """Tests for /api/product-categories endpoints."""

    # ---- GET ----

    def test_list_returns_all(self, client: TestClient, container: MagicMock) -> None:
        container.list_all_product_categories.execute.return_value = _categories()
        resp = client.get("/api/product-categories")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0] == {"id": 1, "name": "Сыпучие", "active": True}
        assert data[2]["active"] is False

    # ---- POST ----

    def test_create_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_product_category.execute.return_value = 4
        resp = client.post("/api/product-categories", json={"name": "Напитки"})
        assert resp.status_code == 201
        assert resp.json() == {"id": 4}

    # ---- PUT ----

    def test_edit_returns_id(self, client: TestClient, container: MagicMock) -> None:
        container.edit_product_category.execute.return_value = 1
        resp = client.put("/api/product-categories/1", json={"name": "Крупы"})
        assert resp.status_code == 200
        assert resp.json() == {"id": 1}

    # ---- DELETE (soft) ----

    def test_soft_delete_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/product-categories/1")
        assert resp.status_code == 204
        container.delete_product_category.execute.assert_called_once_with(1)

    # ---- DELETE (hard) ----

    def test_hard_delete_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/product-categories/1?hard=true")
        assert resp.status_code == 204
        container.hard_delete_product_category.execute.assert_called_once_with(1)

    # ---- POST activate ----

    def test_activate_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/product-categories/3/activate")
        assert resp.status_code == 204
        container.activate_product_category.execute.assert_called_once_with(3)

    # ---- GET used ----

    def test_check_used_returns_true(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.check_product_category_used.execute.return_value = True
        resp = client.get("/api/product-categories/1/used")
        assert resp.status_code == 200
        assert resp.json() == {"used": True}

    def test_check_used_returns_false(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.check_product_category_used.execute.return_value = False
        resp = client.get("/api/product-categories/1/used")
        assert resp.json() == {"used": False}


class TestRecipeCategories:
    """Tests for /api/recipe-categories endpoints."""

    # ---- GET ----

    def test_list_returns_all(self, client: TestClient, container: MagicMock) -> None:
        container.list_all_recipe_categories.execute.return_value = [
            Category(1, "Завтраки", True),
            Category(2, "Обеды", True),
        ]
        resp = client.get("/api/recipe-categories")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    # ---- POST ----

    def test_create_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_recipe_category.execute.return_value = 3
        resp = client.post("/api/recipe-categories", json={"name": "Десерты"})
        assert resp.status_code == 201
        assert resp.json() == {"id": 3}

    # ---- PUT ----

    def test_edit_returns_id(self, client: TestClient, container: MagicMock) -> None:
        container.edit_recipe_category.execute.return_value = 1
        resp = client.put("/api/recipe-categories/1", json={"name": "Утренние"})
        assert resp.status_code == 200
        assert resp.json() == {"id": 1}

    # ---- DELETE (soft) ----

    def test_soft_delete_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/recipe-categories/1")
        assert resp.status_code == 204
        container.delete_recipe_category.execute.assert_called_once_with(1)

    # ---- DELETE (hard) ----

    def test_hard_delete_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/recipe-categories/1?hard=true")
        assert resp.status_code == 204
        container.hard_delete_recipe_category.execute.assert_called_once_with(1)

    # ---- POST activate ----

    def test_activate_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/recipe-categories/2/activate")
        assert resp.status_code == 204
        container.activate_recipe_category.execute.assert_called_once_with(2)

    # ---- GET used ----

    def test_check_used(self, client: TestClient, container: MagicMock) -> None:
        container.check_recipe_category_used.execute.return_value = False
        resp = client.get("/api/recipe-categories/1/used")
        assert resp.status_code == 200
        assert resp.json() == {"used": False}
