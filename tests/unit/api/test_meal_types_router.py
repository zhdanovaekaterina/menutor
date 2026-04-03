"""Tests for /api/meal-types router."""

from datetime import time
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.meal_type import MealType
from backend.domain.exceptions import DuplicateNameError, EntityNotFoundError, MealTypeLimitError, SystemMealTypeDeletionError
from backend.domain.value_objects.types import MealTypeId, UserId


def _meal_type(
    id: int = 1,
    name: str = "Завтрак",
    meal_time: time = time(8, 0),
    is_system: bool = True,
    sort_order: int = 0,
) -> MealType:
    return MealType(
        id=MealTypeId(id),
        user_id=UserId(1),
        name=name,
        time=meal_time,
        is_system=is_system,
        sort_order=sort_order,
    )


# ---- GET /api/meal-types ----


class TestListMealTypes:
    def test_list_meal_types(self, client: TestClient, container: MagicMock) -> None:
        container.list_meal_types.execute.return_value = [
            _meal_type(1, "Завтрак", time(8, 0), is_system=True, sort_order=0),
            _meal_type(2, "Обед", time(13, 0), is_system=True, sort_order=1),
        ]
        resp = client.get("/api/meal-types")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Завтрак"
        assert data[0]["time"] == "08:00"
        assert data[0]["is_system"] is True
        assert data[0]["sort_order"] == 0

    def test_list_meal_types_empty(self, client: TestClient, container: MagicMock) -> None:
        container.list_meal_types.execute.return_value = []
        resp = client.get("/api/meal-types")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- POST /api/meal-types ----


class TestCreateMealType:
    def test_create_meal_type_success(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_meal_type.execute.return_value = _meal_type(
            4, "Полдник", time(16, 0), is_system=False, sort_order=3
        )
        resp = client.post("/api/meal-types", json={"name": "Полдник", "time": "16:00"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 4
        assert data["name"] == "Полдник"
        assert data["time"] == "16:00"
        assert data["is_system"] is False

    def test_create_meal_type_invalid_time(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/meal-types", json={"name": "Поздно", "time": "25:00"})
        assert resp.status_code == 422

    def test_create_meal_type_invalid_time_format(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/meal-types", json={"name": "Поздно", "time": "8:00"})
        assert resp.status_code == 422

    def test_create_meal_type_empty_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/meal-types", json={"name": "", "time": "08:00"})
        assert resp.status_code == 422

    def test_create_meal_type_duplicate(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_meal_type.execute.side_effect = DuplicateNameError(
            "тип приема пищи"
        )
        resp = client.post("/api/meal-types", json={"name": "Завтрак", "time": "08:00"})
        assert resp.status_code == 422

    def test_create_meal_type_limit(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_meal_type.execute.side_effect = MealTypeLimitError(
            "Достигнут лимит типов приемов пищи (10 пользовательских)"
        )
        resp = client.post("/api/meal-types", json={"name": "Новый", "time": "22:00"})
        assert resp.status_code == 422
        assert "лимит" in resp.json()["detail"].lower()


# ---- PUT /api/meal-types/{id} ----


class TestUpdateMealType:
    def test_update_meal_type_success(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.update_meal_type.execute.return_value = _meal_type(
            4, "Поздний перекус", time(21, 0), is_system=False, sort_order=3
        )
        resp = client.put(
            "/api/meal-types/4", json={"name": "Поздний перекус", "time": "21:00"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Поздний перекус"
        assert data["time"] == "21:00"

    def test_update_meal_type_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.update_meal_type.execute.side_effect = EntityNotFoundError(
            "Тип приема пищи 999 не найден"
        )
        resp = client.put(
            "/api/meal-types/999", json={"name": "Нечто", "time": "10:00"}
        )
        assert resp.status_code == 404

    def test_update_meal_type_duplicate_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.update_meal_type.execute.side_effect = DuplicateNameError(
            "тип приема пищи"
        )
        resp = client.put(
            "/api/meal-types/4", json={"name": "Завтрак", "time": "08:30"}
        )
        assert resp.status_code == 422


# ---- DELETE /api/meal-types/{id} ----


class TestDeleteMealType:
    def test_delete_meal_type_success(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_meal_type.execute.return_value = None
        resp = client.delete("/api/meal-types/4")
        assert resp.status_code == 204
        container.delete_meal_type.execute.assert_called_once()

    def test_delete_system_type(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_meal_type.execute.side_effect = SystemMealTypeDeletionError(
            "Системные типы приемов пищи нельзя удалить"
        )
        resp = client.delete("/api/meal-types/1")
        assert resp.status_code == 403
        assert "системные" in resp.json()["detail"].lower()

    def test_delete_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.delete_meal_type.execute.side_effect = EntityNotFoundError(
            "Тип приема пищи 999 не найден"
        )
        resp = client.delete("/api/meal-types/999")
        assert resp.status_code == 404


# ---- GET /api/meal-types/{id}/usage ----


class TestCheckMealTypeUsage:
    def test_check_usage_empty(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.check_meal_type_usage.execute.return_value = []
        resp = client.get("/api/meal-types/1/usage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type_id"] == 1
        assert data["menus"] == []
        assert data["count"] == 0

    def test_check_usage_with_menus(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.check_meal_type_usage.execute.return_value = [
            (10, "Меню на неделю"),
            (11, "Праздничное меню"),
        ]
        resp = client.get("/api/meal-types/2/usage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type_id"] == 2
        assert data["count"] == 2
        assert len(data["menus"]) == 2
        assert data["menus"][0]["id"] == 10
        assert data["menus"][0]["name"] == "Меню на неделю"

    def test_check_usage_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.check_meal_type_usage.execute.side_effect = EntityNotFoundError(
            "Тип приема пищи 999 не найден"
        )
        resp = client.get("/api/meal-types/999/usage")
        assert resp.status_code == 404


# ---- Authorization ----


class TestUnauthorized:
    def test_unauthorized_list(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.get("/api/meal-types")
        assert resp.status_code == 401

    def test_unauthorized_create(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.post(
            "/api/meal-types", json={"name": "Завтрак", "time": "08:00"}
        )
        assert resp.status_code == 401

    def test_unauthorized_delete(
        self, unauth_client: TestClient, container: MagicMock
    ) -> None:
        resp = unauth_client.delete("/api/meal-types/1")
        assert resp.status_code == 401
