"""Tests for member_ids support in /api/menus endpoints."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.value_objects.types import FamilyMemberId, MenuId, RecipeId


def _menu(id: int = 1, slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(id=MenuId(id), name="Неделя 1", slots=slots or [])


def _slot_with_members(member_ids: list[int], recipe_id: int = 1) -> MenuSlot:
    return MenuSlot(
        day=0,
        meal_type="Завтрак",
        recipe_id=RecipeId(recipe_id),
        member_ids=[FamilyMemberId(m) for m in member_ids],
    )


class TestAddSlotWithMemberIds:
    def test_add_slot_with_member_ids(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """POST /menus/{id}/slots with member_ids passes them through and returns them."""
        container.add_dish_to_slot.execute.return_value = _menu(
            slots=[_slot_with_members([1, 2])]
        )
        body = {
            "day": 0,
            "meal_type": "Завтрак",
            "recipe_id": 1,
            "member_ids": [1, 2],
        }
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert sorted(slot["member_ids"]) == [1, 2]

    def test_add_slot_without_member_ids(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """POST without member_ids — response slot has member_ids: []."""
        container.add_dish_to_slot.execute.return_value = _menu(
            slots=[_slot_with_members([])]
        )
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.post("/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert slot["member_ids"] == []


class TestGetMenuIncludesMemberIds:
    def test_get_menu_includes_member_ids(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """GET /menus/{id} response slots include member_ids field."""
        container.load_menu.execute.return_value = _menu(
            slots=[_slot_with_members([3, 5])]
        )
        resp = client.get("/api/menus/1")
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert "member_ids" in slot
        assert sorted(slot["member_ids"]) == [3, 5]


class TestRemoveSlotWithPosition:
    def test_remove_slot_with_position(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """DELETE /menus/{id}/slots with position field passes it to use case."""
        container.remove_item_from_slot.execute.return_value = _menu()
        body = {
            "day": 0,
            "meal_type": "Завтрак",
            "recipe_id": 1,
            "position": 2,
        }
        resp = client.request("DELETE", "/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        _, kwargs = container.remove_item_from_slot.execute.call_args
        assert kwargs.get("position") == 2

    def test_remove_slot_without_position(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """DELETE without position field — use case receives position=None."""
        container.remove_item_from_slot.execute.return_value = _menu()
        body = {"day": 0, "meal_type": "Завтрак", "recipe_id": 1}
        resp = client.request("DELETE", "/api/menus/1/slots", json=body)
        assert resp.status_code == 200
        _, kwargs = container.remove_item_from_slot.execute.call_args
        assert kwargs.get("position") is None


class TestMoveSlotWithPosition:
    def test_move_slot_with_position(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """POST /menus/{id}/slots/move with position field passes it to use case."""
        container.move_slot_in_menu.execute.return_value = _menu(
            slots=[MenuSlot(day=1, meal_type="Обед", recipe_id=RecipeId(1))]
        )
        body = {
            "day": 0,
            "meal_type": "Завтрак",
            "recipe_id": 1,
            "to_day": 1,
            "to_meal_type": "Обед",
            "to_position": 0,
            "position": 1,
        }
        resp = client.post("/api/menus/1/slots/move", json=body)
        assert resp.status_code == 200
        _, kwargs = container.move_slot_in_menu.execute.call_args
        assert kwargs.get("position") == 1

    def test_move_slot_without_position(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """POST move without position — use case receives position=None."""
        container.move_slot_in_menu.execute.return_value = _menu(
            slots=[MenuSlot(day=1, meal_type="Обед", recipe_id=RecipeId(1))]
        )
        body = {
            "day": 0,
            "meal_type": "Завтрак",
            "recipe_id": 1,
            "to_day": 1,
            "to_meal_type": "Обед",
            "to_position": 0,
        }
        resp = client.post("/api/menus/1/slots/move", json=body)
        assert resp.status_code == 200
        _, kwargs = container.move_slot_in_menu.execute.call_args
        assert kwargs.get("position") is None


class TestCopyMenuPreservesMemberIds:
    def test_copy_menu_preserves_member_ids(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """POST /menus/{id}/copy — response slots include member_ids."""
        container.copy_menu.execute.return_value = WeeklyMenu(
            id=MenuId(2),
            name="Копия: Неделя 1",
            slots=[_slot_with_members([1, 2])],
        )
        resp = client.post("/api/menus/1/copy")
        assert resp.status_code == 201
        slot = resp.json()["slots"][0]
        assert sorted(slot["member_ids"]) == [1, 2]
