"""Tests for /api/menus router."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.application.paginated_result import PaginatedResult
from backend.application.use_cases.generate_meal_summary import (
    MealOccurrence,
    MealSummaryProduct,
    MealSummaryRecipe,
    MealSummaryResponse,
)
from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.services.shopping_list_builder import IngredientNode
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId


def _menu(id: int = 1, slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(id=MenuId(id), name="Неделя 1", slots=slots or [])


def _slot_recipe(pieces_override: int | None = None) -> MenuSlot:
    return MenuSlot(day=0, meal_type="Завтрак", recipe_id=RecipeId(1), pieces_override=pieces_override)


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


# ---- POST /api/menus/{menu_id}/slots/move ----


class TestMoveSlot:
    def test_moves_slot(self, client: TestClient, container: MagicMock) -> None:
        container.move_slot_in_menu.execute.return_value = _menu(
            slots=[MenuSlot(day=1, meal_type="Обед", recipe_id=RecipeId(1), position=0)]
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
        assert resp.json()["slots"][0]["day"] == 1
        assert resp.json()["slots"][0]["meal_type"] == "Обед"
        container.move_slot_in_menu.execute.assert_called_once()

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.move_slot_in_menu.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        body = {
            "day": 0,
            "meal_type": "Завтрак",
            "recipe_id": 1,
            "to_day": 1,
            "to_meal_type": "Обед",
            "to_position": 0,
        }
        resp = client.post("/api/menus/999/slots/move", json=body)
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


# ---- pieces_override in slots ----


class TestPiecesOverride:
    def test_add_slot_with_pieces_override(self, client: TestClient, container: MagicMock) -> None:
        """POST /menus/{id}/slots с pieces_override."""
        container.add_dish_to_slot.execute.return_value = _menu(1, [_slot_recipe(pieces_override=5)])
        resp = client.post("/api/menus/1/slots", json={
            "day": 0, "meal_type": "Завтрак", "recipe_id": 1, "pieces_override": 5,
        })
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert slot["pieces_override"] == 5

    def test_add_slot_without_pieces_override(self, client: TestClient, container: MagicMock) -> None:
        """POST /menus/{id}/slots без pieces_override -- null в ответе."""
        container.add_dish_to_slot.execute.return_value = _menu(1, [_slot_recipe()])
        resp = client.post("/api/menus/1/slots", json={
            "day": 0, "meal_type": "Завтрак", "recipe_id": 1,
        })
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert slot["pieces_override"] is None

    def test_get_menu_includes_pieces_override(self, client: TestClient, container: MagicMock) -> None:
        """GET /menus/{id} возвращает pieces_override."""
        container.load_menu.execute.return_value = _menu(1, [_slot_recipe(pieces_override=8)])
        resp = client.get("/api/menus/1")
        assert resp.status_code == 200
        slot = resp.json()["slots"][0]
        assert slot["pieces_override"] == 8


# ---- POST /api/menus/{menu_id}/export/pdf ----


class TestExportMenuPdf:
    def test_returns_pdf_for_ascii_menu_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.load_menu.execute.return_value = _menu(3)
        container.list_recipes.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        container.list_products.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        resp = client.post("/api/menus/3/export/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_returns_pdf_for_cyrillic_menu_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """Cyrillic menu name must not trigger a UnicodeEncodeError (HTTP headers are Latin-1)."""
        from backend.domain.value_objects.types import MenuId

        cyrillic_menu = WeeklyMenu(id=MenuId(3), name="Тест меню", slots=[_slot_recipe()])
        container.load_menu.execute.return_value = cyrillic_menu
        container.list_recipes.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        container.list_products.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        resp = client.post("/api/menus/3/export/pdf")
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"
        cd = resp.headers["content-disposition"]
        assert "filename*=UTF-8''" in cd
        assert "%D0" in cd  # percent-encoded Cyrillic bytes present

    def test_returns_404_when_menu_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.load_menu.execute.return_value = None
        resp = client.post("/api/menus/999/export/pdf")
        assert resp.status_code == 404

    def test_content_disposition_has_ascii_fallback(
        self, client: TestClient, container: MagicMock
    ) -> None:
        """Content-Disposition must include a plain ASCII filename= fallback."""
        container.load_menu.execute.return_value = _menu(1)
        container.list_recipes.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        container.list_products.execute.return_value = PaginatedResult(items=[], total=0, page=1, page_size=0)
        resp = client.post("/api/menus/1/export/pdf")
        assert resp.status_code == 200
        cd = resp.headers["content-disposition"]
        assert 'filename="' in cd
        assert "filename*=UTF-8''" in cd


# ---- GET /api/menus/{menu_id}/summary ----


def _meal_summary(
    menu_id: int = 1,
    with_ingredients: bool = False,
) -> MealSummaryResponse:
    ingredients = []
    if with_ingredients:
        child = IngredientNode(
            product_id=ProductId(10),
            product_name="Молоко",
            quantity_amount=200.0,
            quantity_unit="ml",
        )
        ingredients = [
            IngredientNode(
                product_id=None,
                product_name="",
                quantity_amount=1.0,
                quantity_unit="serv",
                sub_recipe_id=RecipeId(5),
                sub_recipe_name="Соус",
                children=[child],
            )
        ]
    return MealSummaryResponse(
        menu_id=MenuId(menu_id),
        menu_name="Неделя 1",
        recipes=[
            MealSummaryRecipe(
                recipe_id=RecipeId(1),
                recipe_name="Блины",
                occurrences=[
                    MealOccurrence(
                        day=0,
                        meal_type="Завтрак",
                        servings=4.0,
                        pieces_override=None,
                        slot_index=0,
                    )
                ],
                total_servings=4.0,
                pieces_info=None,
                ingredients=ingredients,
            )
        ],
        products=[
            MealSummaryProduct(
                product_id=ProductId(2),
                product_name="Молоко",
                occurrences=[{"day": 1, "meal_type": "Перекус", "quantity": 0.5, "unit": "l", "slot_index": 1}],
                total_quantity=0.5,
                unit="l",
            )
        ],
    )


class TestGetMealSummary:
    def test_get_meal_summary_success(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_meal_summary.execute.return_value = _meal_summary()
        resp = client.get("/api/menus/1/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["menu_id"] == 1
        assert data["menu_name"] == "Неделя 1"
        assert isinstance(data["recipes"], list)
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["recipe_name"] == "Блины"
        assert data["recipes"][0]["total_servings"] == 4.0
        assert isinstance(data["products"], list)
        assert len(data["products"]) == 1
        assert data["products"][0]["product_name"] == "Молоко"

    def test_get_meal_summary_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_meal_summary.execute.side_effect = EntityNotFoundError(
            "Меню 999 не найдено"
        )
        resp = client.get("/api/menus/999/summary")
        assert resp.status_code == 404
        assert "не найдено" in resp.json()["detail"]

    def test_get_meal_summary_includes_ingredients_tree(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.generate_meal_summary.execute.return_value = _meal_summary(
            with_ingredients=True
        )
        resp = client.get("/api/menus/1/summary")
        assert resp.status_code == 200
        data = resp.json()
        recipe = data["recipes"][0]
        assert len(recipe["ingredients"]) == 1
        ing = recipe["ingredients"][0]
        assert ing["sub_recipe_id"] == 5
        assert ing["sub_recipe_name"] == "Соус"
        assert len(ing["sub_ingredients"]) == 1
        child = ing["sub_ingredients"][0]
        assert child["product_id"] == 10
        assert child["product_name"] == "Молоко"
