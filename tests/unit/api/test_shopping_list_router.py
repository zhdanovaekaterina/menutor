"""Tests for shopping list generation and export endpoints."""

from decimal import Decimal
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId


def _shopping_list() -> ShoppingList:
    return ShoppingList(
        items=[
            ShoppingListItem(
                product_id=ProductId(1),
                product_name="Мука",
                category="Сыпучие",
                quantity=Quantity(0.2, "kg"),
                cost=Money(Decimal("16")),
                purchased=False,
                recipe_quantity=Quantity(200.0, "g"),
            ),
            ShoppingListItem(
                product_id=ProductId(2),
                product_name="Молоко",
                category="Молочные",
                quantity=Quantity(0.5, "l"),
                cost=Money(Decimal("45")),
                purchased=False,
            ),
        ]
    )


# ---- POST /api/menus/{menu_id}/shopping-list ----


class TestGenerateShoppingList:
    def test_generates_and_returns_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.return_value = _shopping_list()
        resp = client.post("/api/menus/1/shopping-list")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["product_name"] == "Мука"
        assert data["items"][0]["quantity"] == {"amount": 0.2, "unit": "kg"}
        assert data["items"][0]["cost"] == {"amount": "16", "currency": "RUB"}
        assert data["items"][0]["recipe_quantity"] == {"amount": 200.0, "unit": "g"}
        assert data["items"][1]["recipe_quantity"] is None

    def test_returns_total_cost(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.return_value = _shopping_list()
        resp = client.post("/api/menus/1/shopping-list")
        data = resp.json()
        assert data["total_cost"] == {"amount": "61", "currency": "RUB"}

    def test_returns_empty_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.return_value = ShoppingList()
        resp = client.post("/api/menus/1/shopping-list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_cost"] == {"amount": "0", "currency": "RUB"}

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/shopping-list")
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]


# ---- POST /api/menus/{menu_id}/shopping-list/export/text ----


class TestExportShoppingListText:
    def test_exports_as_plain_text(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.return_value = _shopping_list()
        container.export_shopping_list_as_text.execute.return_value = (
            "Мука — 0.2 кг\nМолоко — 0.5 л"
        )
        resp = client.post("/api/menus/1/shopping-list/export/text")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"
        assert "Мука" in resp.text

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_shopping_list.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/shopping-list/export/text")
        assert resp.status_code == 404
