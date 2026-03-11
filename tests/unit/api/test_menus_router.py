"""Tests for /api/menus router."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId


def _menu(id: int = 1, slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(id=MenuId(id), name="Неделя 1", slots=slots or [])


def _slot_recipe() -> MenuSlot:
    return MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(1))


def _slot_product() -> MenuSlot:
    return MenuSlot(
        day=1, meal_type="Перекус", product_id=ProductId(5), quantity=2.0, unit="pcs"
    )


# ---- GET /api/menus ----


class TestListMenus:
    def test_returns_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_menus.execute.return_value = [_menu(1), _menu(2)]
        resp = client.get("/api/menus")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_menus.execute.return_value = []
        resp = client.get("/api/menus")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- POST /api/menus ----


class TestCreateMenu:
    def test_creates_and_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_menu.execute.return_value = _menu()
        resp = client.post("/api/menus", json={"name": "Неделя 1"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Неделя 1"
        assert resp.json()["slots"] == []

    def test_returns_422_on_missing_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/menus", json={})
        assert resp.status_code == 422


# ---- GET /api/menus/{menu_id} ----


class TestGetMenu:
    def test_returns_menu_with_slots(
        self, client: TestClient, container: MagicMock
    ) -> None:
        menu = _menu(slots=[_slot_recipe(), _slot_product()])
        container.load_menu.execute.return_value = menu
        resp = client.get("/api/menus/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert len(data["slots"]) == 2
        assert data["slots"][0]["recipe_id"] == 1
        assert data["slots"][0]["product_id"] is None
        assert data["slots"][1]["product_id"] == 5
        assert data["slots"][1]["recipe_id"] is None

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.load_menu.execute.return_value = None
        resp = client.get("/api/menus/999")
        assert resp.status_code == 404


# ---- DELETE /api/menus/{menu_id} ----


class TestDeleteMenu:
    def test_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/menus/1")
        assert resp.status_code == 204
        container.delete_menu.execute.assert_called_once()


# ---- POST /api/menus/{menu_id}/slots ----


class TestAddSlot:
    def test_adds_recipe_slot(self, client: TestClient, container: MagicMock) -> None:
        container.add_dish_to_slot.execute.return_value = _menu(
            slots=[_slot_recipe()]
        )
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        assert len(resp.json()["slots"]) == 1

    def test_adds_product_slot(self, client: TestClient, container: MagicMock) -> None:
        container.add_dish_to_slot.execute.return_value = _menu(
            slots=[_slot_product()]
        )
        body = {
            "day": 1,
            "meal_type": "Перекус",
            "product_id": 5,
            "quantity": 2.0,
            "unit": "pcs",
        }
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 200

    def test_returns_422_when_both_ids_set(
        self, client: TestClient, container: MagicMock
    ) -> None:
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1, "product_id": 2}
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 422

    def test_returns_422_when_no_ids_set(
        self, client: TestClient, container: MagicMock
    ) -> None:
        body = {"day": 0, "meal_type": "Завтрак"}
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 422

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.add_dish_to_slot.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.post("/api/menus/999/slots", json=body)
        assert resp.status_code == 404


# ---- DELETE /api/menus/{menu_id}/slots ----


class TestRemoveSlot:
    def test_removes_slot(self, client: TestClient, container: MagicMock) -> None:
        container.remove_item_from_slot.execute.return_value = _menu()
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.request("DELETE", "/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        container.remove_item_from_slot.execute.assert_called_once()

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.remove_item_from_slot.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.request("DELETE", "/api/menus/999/slots", json=body)
        assert resp.status_code == 404


# ---- POST /api/menus/{menu_id}/clear ----


class TestClearMenu:
    def test_clears_and_returns_empty_slots(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.clear_menu.execute.return_value = _menu()
        resp = client.post("/api/menus/1/clear")
        assert resp.status_code == 200
        assert resp.json()["slots"] == []

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.clear_menu.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.post("/api/menus/999/clear")
        assert resp.status_code == 404
