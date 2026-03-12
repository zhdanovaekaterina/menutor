"""Tests for /api/products router."""

from decimal import Decimal
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.product import Product
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.category import ActiveCategory
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId


def _product(id: int = 1) -> Product:
    return Product(
        id=ProductId(id),
        name="Мука",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("80")),
        brand="Макфа",
        supplier="Магнит",
        weight_per_piece_g=None,
        conversion_factor=1000.0,
        category_id=ProductCategoryId(1),
    )


# ---- GET /api/products ----


class TestListProducts:
    def test_returns_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_products.execute.return_value = [_product(1), _product(2)]
        resp = client.get("/api/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_products.execute.return_value = []
        resp = client.get("/api/products")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- GET /api/products/categories ----


class TestListProductCategories:
    def test_returns_active_categories(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.list_product_categories.execute.return_value = [
            ActiveCategory(1, "Сыпучие"),
        ]
        resp = client.get("/api/products/categories")
        assert resp.status_code == 200
        assert resp.json() == [{"id": 1, "name": "Сыпучие"}]


# ---- POST /api/products ----


class TestCreateProduct:
    def test_creates_and_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_product.execute.return_value = _product()
        body = {
            "name": "Мука",
            "category_id": 1,
            "recipe_unit": "g",
            "purchase_unit": "kg",
            "price_amount": "80",
            "brand": "Макфа",
            "supplier": "Магнит",
            "conversion_factor": 1000.0,
        }
        resp = client.post("/api/products", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Мука"
        assert data["price_amount"] == "80"
        assert data["price_currency"] == "RUB"
        container.create_product.execute.assert_called_once()

    def test_creates_with_minimal_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_product.execute.return_value = _product()
        body = {
            "name": "Мука",
            "category_id": 1,
            "recipe_unit": "g",
            "purchase_unit": "kg",
            "price_amount": "80",
        }
        resp = client.post("/api/products", json=body)
        assert resp.status_code == 201

    def test_returns_422_on_missing_required_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/products", json={"name": "Мука"})
        assert resp.status_code == 422


# ---- PUT /api/products/{product_id} ----


class TestUpdateProduct:
    def test_updates_and_returns_product(
        self, client: TestClient, container: MagicMock
    ) -> None:
        updated = Product(
            id=ProductId(1),
            name="Мука отборная",
            recipe_unit="g",
            purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("100")),
            category_id=ProductCategoryId(1),
        )
        container.edit_product.execute.return_value = updated
        body = {
            "name": "Мука отборная",
            "category_id": 1,
            "recipe_unit": "g",
            "purchase_unit": "kg",
            "price_amount": "100",
        }
        resp = client.put("/api/products/1", json=body)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Мука отборная"

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.edit_product.execute.side_effect = EntityNotFoundError(
            "Продукт 999 не найден"
        )
        body = {
            "name": "Мука",
            "category_id": 1,
            "recipe_unit": "g",
            "purchase_unit": "kg",
            "price_amount": "80",
        }
        resp = client.put("/api/products/999", json=body)
        assert resp.status_code == 404


# ---- PATCH /api/products/{product_id}/price ----


class TestUpdateProductPrice:
    def test_updates_price(self, client: TestClient, container: MagicMock) -> None:
        updated = Product(
            id=ProductId(1),
            name="Мука",
            recipe_unit="g",
            purchase_unit="kg",
            price_per_purchase_unit=Money(Decimal("120")),
            category_id=ProductCategoryId(1),
        )
        container.update_product_price.execute.return_value = updated
        resp = client.patch("/api/products/1/price", json={"amount": "120"})
        assert resp.status_code == 200
        assert resp.json()["price_amount"] == "120"

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.update_product_price.execute.side_effect = EntityNotFoundError(
            "Продукт 999 не найден"
        )
        resp = client.patch("/api/products/999/price", json={"amount": "120"})
        assert resp.status_code == 404


# ---- DELETE /api/products/{product_id} ----


class TestDeleteProduct:
    def test_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/products/1")
        assert resp.status_code == 204
        container.delete_product.execute.assert_called_once()
