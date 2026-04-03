"""Tests for /api/preferences router and /api/recipes/{id}/matching-preferences."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.preference import Preference
from backend.domain.exceptions import DuplicateNameError, EntityNotFoundError
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import PreferenceId, UserId


def _pref(id: int = 1, name: str = "Веган") -> Preference:
    return Preference(
        id=PreferenceId(id),
        name=name,
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        category_ids=[],
        product_ids=[],
        recipe_category_ids=[],
        user_id=UserId(1),
    )


_BODY = {
    "name": "Веган",
    "type": "CATEGORY_BASED",
    "mode": "BLOCKED",
    "category_ids": [],
    "product_ids": [],
    "recipe_category_ids": [],
}


# ---- GET /api/preferences ----

class TestListPreferences:
    def test_returns_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_preferences.execute.return_value = [_pref(1), _pref(2)]
        resp = client.get("/api/preferences")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_preferences.execute.return_value = []
        resp = client.get("/api/preferences")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- GET /api/preferences/{id} ----

class TestGetPreference:
    def test_returns_preference(self, client: TestClient, container: MagicMock) -> None:
        container.get_preference.execute.return_value = _pref(1)
        resp = client.get("/api/preferences/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1
        assert resp.json()["name"] == "Веган"

    def test_not_found_returns_404(self, client: TestClient, container: MagicMock) -> None:
        container.get_preference.execute.return_value = None
        resp = client.get("/api/preferences/999")
        assert resp.status_code == 404


# ---- POST /api/preferences ----

class TestCreatePreference:
    def test_creates_and_returns_201(self, client: TestClient, container: MagicMock) -> None:
        container.create_preference.execute.return_value = _pref()
        resp = client.post("/api/preferences", json=_BODY)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Веган"
        container.create_preference.execute.assert_called_once()

    def test_duplicate_name_returns_422(self, client: TestClient, container: MagicMock) -> None:
        container.create_preference.execute.side_effect = DuplicateNameError("предпочтение")
        resp = client.post("/api/preferences", json=_BODY)
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client: TestClient, container: MagicMock) -> None:
        body = {**_BODY}
        del body["name"]
        resp = client.post("/api/preferences", json=body)
        assert resp.status_code == 422


# ---- PUT /api/preferences/{id} ----

class TestUpdatePreference:
    def test_updates_and_returns_200(self, client: TestClient, container: MagicMock) -> None:
        container.update_preference.execute.return_value = _pref(1, "Обновлено")
        resp = client.put("/api/preferences/1", json={**_BODY, "name": "Обновлено"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Обновлено"

    def test_not_found_returns_404(self, client: TestClient, container: MagicMock) -> None:
        container.update_preference.execute.side_effect = EntityNotFoundError("not found")
        resp = client.put("/api/preferences/999", json=_BODY)
        assert resp.status_code == 404


# ---- DELETE /api/preferences/{id} ----

class TestDeletePreference:
    def test_deletes_returns_204(self, client: TestClient, container: MagicMock) -> None:
        resp = client.delete("/api/preferences/1")
        assert resp.status_code == 204
        container.delete_preference.execute.assert_called_once()


# ---- recipe_category_ids field ----

class TestRecipeCategoryIds:
    def test_create_with_recipe_category_ids_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        from backend.domain.value_objects.types import RecipeCategoryId
        pref = _pref()
        pref.recipe_category_ids = [RecipeCategoryId(1), RecipeCategoryId(2)]
        container.create_preference.execute.return_value = pref
        body = {**_BODY, "recipe_category_ids": [1, 2]}
        resp = client.post("/api/preferences", json=body)
        assert resp.status_code == 201
        assert resp.json()["recipe_category_ids"] == [1, 2]

    def test_response_includes_recipe_category_ids(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.list_preferences.execute.return_value = [_pref()]
        resp = client.get("/api/preferences")
        assert resp.status_code == 200
        assert "recipe_category_ids" in resp.json()[0]
        assert resp.json()[0]["recipe_category_ids"] == []


# ---- GET /api/recipes/{id}/matching-preferences ----

class TestMatchingPreferences:
    def test_returns_matched_preferences(self, client: TestClient, container: MagicMock) -> None:
        container.match_recipe_preferences.execute.return_value = [_pref(1), _pref(2)]
        resp = client.get("/api/recipes/1/matching-preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "preferences" in data
        assert len(data["preferences"]) == 2

    def test_nonexistent_recipe_returns_empty(self, client: TestClient, container: MagicMock) -> None:
        container.match_recipe_preferences.execute.return_value = []
        resp = client.get("/api/recipes/999/matching-preferences")
        assert resp.status_code == 200
        assert resp.json()["preferences"] == []
