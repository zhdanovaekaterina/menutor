"""Tests for shopping list generation, export, and saved-list endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.saved_shopping_list import (
    SavedShoppingList,
    SavedShoppingListItem,
)
from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import (
    ProductId,
    SavedShoppingListId,
    SavedShoppingListItemId,
    UserId,
)

_CREATED_AT = datetime(2026, 3, 21, 10, 0, 0, tzinfo=UTC)
_UPDATED_AT = datetime(2026, 3, 21, 10, 5, 0, tzinfo=UTC)


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


def _shopping_list_with_decimal_quantity() -> ShoppingList:
    return ShoppingList(
        items=[
            ShoppingListItem(
                product_id=ProductId(1),
                product_name="Масло",
                category="Молочные",
                quantity=Quantity(1.3, "l"),
                cost=Money(Decimal("200")),
                purchased=False,
            ),
        ]
    )


def _saved_item(
    item_id: int = 1,
    product_id: int | None = 1,
    product_name: str = "Мука",
    category: str = "Сыпучие",
    purchased: bool = False,
) -> SavedShoppingListItem:
    return SavedShoppingListItem(
        id=SavedShoppingListItemId(item_id),
        product_id=ProductId(product_id) if product_id is not None else None,
        product_name=product_name,
        category=category,
        quantity=Quantity(0.2, "kg"),
        buy_quantity=Quantity(1.0, "kg"),
        buy_quantity_overridden=False,
        cost=Money(Decimal("50")),
        purchased=purchased,
        recipe_quantity=Quantity(200.0, "g"),
        item_order=0,
    )


def _saved_list(
    list_id: int = 1,
    name: str = "Список 10:00 21.03.2026",
    items: list[SavedShoppingListItem] | None = None,
    source_menu_id: int | None = None,
) -> SavedShoppingList:
    return SavedShoppingList(
        id=SavedShoppingListId(list_id),
        user_id=UserId(1),
        name=name,
        items=items if items is not None else [_saved_item()],
        source_menu_id=None,
        created_at=_CREATED_AT,
        updated_at=_UPDATED_AT,
    )


# ---- POST /api/menus/{menu_id}/shopping-list ----


class TestGenerateShoppingList:
    def test_generates_and_returns_saved_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_and_save_shopping_list.execute.return_value = _saved_list(
            name="Создано из меню «Неделя» 10:00 21.03.2026",
            items=[_saved_item()],
        )
        resp = client.post("/api/menus/1/shopping-list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert "меню" in data["name"].lower() or "список" in data["name"].lower()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Мука"
        assert "total_cost" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_and_save_shopping_list.execute.side_effect = (
            EntityNotFoundError("Меню 999 не найдено")
        )
        resp = client.post("/api/menus/999/shopping-list")
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.post("/api/menus/1/shopping-list")
        assert resp.status_code == 401


# ---- POST /api/menus/{menu_id}/shopping-list/export/text ----


class TestExportShoppingListText:
    def test_exports_as_plain_text(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            "Мука — 0.2 кг\nМолоко — 0.5 л".encode("utf-8"),
            "text/plain; charset=utf-8",
            "shopping_list.txt",
        )
        resp = client.post("/api/menus/1/shopping-list/export/text")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/shopping-list/export/text")
        assert resp.status_code == 404


# ---- POST /api/menus/{menu_id}/shopping-list/export/json ----


class TestExportShoppingListJson:
    def test_exports_as_json(
        self, client: TestClient, container: MagicMock
    ) -> None:
        payload = '{"title": "Список покупок"}'.encode("utf-8")
        container.export_shopping_list.execute.return_value = (
            payload,
            "application/json",
            "shopping_list.json",
        )
        resp = client.post("/api/menus/1/shopping-list/export/json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]

    def test_content_disposition_header(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            b"{}",
            "application/json",
            "shopping_list.json",
        )
        resp = client.post("/api/menus/1/shopping-list/export/json")
        assert "shopping_list.json" in resp.headers["content-disposition"]

    def test_calls_use_case_with_json_format(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            b"{}",
            "application/json",
            "shopping_list.json",
        )
        client.post("/api/menus/5/shopping-list/export/json")
        container.export_shopping_list.execute.assert_called_once()
        args = container.export_shopping_list.execute.call_args
        assert args[0][2] == "json"

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/shopping-list/export/json")
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]


# ---- POST /api/menus/{menu_id}/shopping-list/export/pdf ----


class TestExportShoppingListPdf:
    def test_exports_as_pdf(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            b"%PDF-1.4 fake",
            "application/pdf",
            "shopping_list.pdf",
        )
        resp = client.post("/api/menus/1/shopping-list/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_content_disposition_header(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            b"%PDF-1.4 fake",
            "application/pdf",
            "shopping_list.pdf",
        )
        resp = client.post("/api/menus/1/shopping-list/export/pdf")
        assert "shopping_list.pdf" in resp.headers["content-disposition"]

    def test_calls_use_case_with_pdf_format(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.return_value = (
            b"%PDF-1.4 fake",
            "application/pdf",
            "shopping_list.pdf",
        )
        client.post("/api/menus/3/shopping-list/export/pdf")
        container.export_shopping_list.execute.assert_called_once()
        args = container.export_shopping_list.execute.call_args
        assert args[0][2] == "pdf"

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_shopping_list.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/shopping-list/export/pdf")
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]


# ---- GET /api/shopping-lists ----


class TestListSavedShoppingLists:
    def test_returns_meta_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.list_saved_shopping_lists.execute.return_value = [
            _saved_list(1, "Список А"),
            _saved_list(2, "Список Б"),
        ]
        resp = client.get("/api/shopping-lists")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Список А"
        # meta should NOT contain items
        assert "items" not in data[0]
        assert "total_cost" not in data[0]

    def test_returns_empty_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.list_saved_shopping_lists.execute.return_value = []
        resp = client.get("/api/shopping-lists")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.get("/api/shopping-lists")
        assert resp.status_code == 401


# ---- POST /api/shopping-lists ----


class TestCreateSavedShoppingList:
    def test_creates_empty_list_with_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_saved_shopping_list.execute.return_value = _saved_list(
            items=[]
        )
        resp = client.post("/api/shopping-lists")
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 1
        assert data["items"] == []
        assert "total_cost" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.post("/api/shopping-lists")
        assert resp.status_code == 401


# ---- GET /api/shopping-lists/{list_id} ----


class TestGetSavedShoppingList:
    def test_returns_full_list_with_items(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.get_saved_shopping_list.execute.return_value = _saved_list()
        resp = client.get("/api/shopping-lists/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Мука"
        assert "buy_quantity_overridden" in data["items"][0]
        assert "item_order" in data["items"][0]

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.get_saved_shopping_list.execute.side_effect = EntityNotFoundError(
            "Список покупок 999 не найден"
        )
        resp = client.get("/api/shopping-lists/999")
        assert resp.status_code == 404
        assert "не найден" in resp.json()["detail"]

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.get("/api/shopping-lists/1")
        assert resp.status_code == 401


# ---- PUT /api/shopping-lists/{list_id} ----


class TestUpdateSavedShoppingList:
    def _update_body(self) -> dict:
        return {
            "name": "Обновленный список",
            "items": [
                {
                    "product_id": 1,
                    "product_name": "Масло",
                    "category": "Молочные",
                    "quantity_amount": 0.5,
                    "quantity_unit": "kg",
                    "buy_quantity_amount": 1.0,
                    "buy_quantity_unit": "kg",
                    "buy_quantity_overridden": False,
                    "cost_amount": 100.0,
                    "cost_currency": "RUB",
                    "purchased": False,
                    "recipe_quantity_amount": None,
                    "recipe_quantity_unit": None,
                    "item_order": 0,
                }
            ],
        }

    def test_updates_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        updated = _saved_list(name="Обновленный список")
        container.update_saved_shopping_list.execute.return_value = updated
        resp = client.put("/api/shopping-lists/1", json=self._update_body())
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Обновленный список"

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.update_saved_shopping_list.execute.side_effect = EntityNotFoundError(
            "Список покупок 999 не найден"
        )
        resp = client.put("/api/shopping-lists/999", json=self._update_body())
        assert resp.status_code == 404

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.put("/api/shopping-lists/1", json=self._update_body())
        assert resp.status_code == 401


# ---- PATCH /api/shopping-lists/{list_id} ----


class TestRenameSavedShoppingList:
    def test_renames_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        renamed = _saved_list(name="Новое название")
        container.rename_saved_shopping_list.execute.return_value = renamed
        resp = client.patch("/api/shopping-lists/1", json={"name": "Новое название"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Новое название"

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.rename_saved_shopping_list.execute.side_effect = EntityNotFoundError(
            "Список покупок 999 не найден"
        )
        resp = client.patch(
            "/api/shopping-lists/999", json={"name": "Неважно"}
        )
        assert resp.status_code == 404

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.patch("/api/shopping-lists/1", json={"name": "Новое"})
        assert resp.status_code == 401


# ---- DELETE /api/shopping-lists/{list_id} ----


class TestDeleteSavedShoppingList:
    def test_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_saved_shopping_list.execute.return_value = None
        resp = client.delete("/api/shopping-lists/1")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_calls_use_case_with_correct_id(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_saved_shopping_list.execute.return_value = None
        client.delete("/api/shopping-lists/7")
        container.delete_saved_shopping_list.execute.assert_called_once()

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.delete("/api/shopping-lists/1")
        assert resp.status_code == 401


# ---- POST /api/shopping-lists/{list_id}/copy ----


class TestCopySavedShoppingList:
    def test_copies_list_with_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        copy = _saved_list(2, "Список А (копия)")
        container.copy_saved_shopping_list.execute.return_value = copy
        resp = client.post("/api/shopping-lists/1/copy")
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 2
        assert "копия" in data["name"]

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.copy_saved_shopping_list.execute.side_effect = EntityNotFoundError(
            "Список покупок 999 не найден"
        )
        resp = client.post("/api/shopping-lists/999/copy")
        assert resp.status_code == 404

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.post("/api/shopping-lists/1/copy")
        assert resp.status_code == 401


# ---- POST /api/shopping-lists/{list_id}/items/{item_id}/toggle-purchased ----


class TestToggleItemPurchased:
    def test_toggles_purchased_and_returns_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        toggled = _saved_list(items=[_saved_item(purchased=True)])
        container.toggle_item_purchased.execute.return_value = toggled
        resp = client.post("/api/shopping-lists/1/items/1/toggle-purchased")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["purchased"] is True

    def test_returns_404_when_list_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.toggle_item_purchased.execute.side_effect = EntityNotFoundError(
            "Список покупок 999 не найден"
        )
        resp = client.post("/api/shopping-lists/999/items/1/toggle-purchased")
        assert resp.status_code == 404

    def test_returns_404_when_item_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.toggle_item_purchased.execute.side_effect = EntityNotFoundError(
            "Позиция 99 не найдена в списке 1"
        )
        resp = client.post("/api/shopping-lists/1/items/99/toggle-purchased")
        assert resp.status_code == 404
        assert "не найден" in resp.json()["detail"]

    def test_requires_auth(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.post("/api/shopping-lists/1/items/1/toggle-purchased")
        assert resp.status_code == 401


# ---- POST /api/menus/{menu_id}/shopping-list/filtered ----


class TestGenerateFilteredShoppingList:
    def test_generate_filtered_shopping_list_success(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_filtered_shopping_list.execute.return_value = _saved_list(
            name="Создано из меню «Неделя» 10:00 21.03.2026",
            items=[_saved_item()],
        )
        resp = client.post(
            "/api/menus/1/shopping-list/filtered",
            json={"slot_indices": [0, 2]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert len(data["items"]) == 1
        assert "total_cost" in data
        # verify execute was called with the correct slot indices set
        call_args = container.generate_filtered_shopping_list.execute.call_args
        assert call_args is not None
        assert call_args[0][2] == {0, 2}

    def test_generate_filtered_shopping_list_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_filtered_shopping_list.execute.side_effect = (
            EntityNotFoundError("Меню 999 не найдено")
        )
        resp = client.post(
            "/api/menus/999/shopping-list/filtered",
            json={"slot_indices": [0]},
        )
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]

    def test_generate_filtered_shopping_list_empty_indices(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_filtered_shopping_list.execute.return_value = _saved_list(
            items=[],
        )
        resp = client.post(
            "/api/menus/1/shopping-list/filtered",
            json={"slot_indices": []},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        call_args = container.generate_filtered_shopping_list.execute.call_args
        assert call_args is not None
        assert call_args[0][2] == set()

    def test_generate_filtered_shopping_list_with_exclusions(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_filtered_shopping_list.execute.return_value = _saved_list(
            items=[_saved_item()],
        )
        resp = client.post(
            "/api/menus/1/shopping-list/filtered",
            json={"slot_indices": [0], "excluded_sub_recipe_ids": [5, 6]},
        )
        assert resp.status_code == 200
        call_args = container.generate_filtered_shopping_list.execute.call_args
        assert call_args is not None
        # slot_indices at positional index 2, excluded_sub_recipe_ids at index 3
        assert call_args[0][2] == {0}
        assert call_args[0][3] == {5, 6}
