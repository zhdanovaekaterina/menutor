"""Tests for /api/family-members router."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.domain.entities.family_member import FamilyMember
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import FamilyMemberId


def _member(id: int = 1) -> FamilyMember:
    return FamilyMember(
        id=FamilyMemberId(id),
        name="Взрослый",
        portion_multiplier=1.0,
        dietary_restrictions="без глютена",
        comment="заметка",
    )


# ---- GET /api/family-members ----


class TestListFamilyMembers:
    def test_returns_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_family_members.execute.return_value = [
            _member(1),
            _member(2),
        ]
        resp = client.get("/api/family-members")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_returns_empty_list(self, client: TestClient, container: MagicMock) -> None:
        container.list_family_members.execute.return_value = []
        resp = client.get("/api/family-members")
        assert resp.status_code == 200
        assert resp.json() == []


# ---- POST /api/family-members ----


class TestCreateFamilyMember:
    def test_creates_and_returns_201(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_family_member.execute.return_value = _member()
        body = {
            "name": "Взрослый",
            "portion_multiplier": 1.0,
            "dietary_restrictions": "без глютена",
            "comment": "заметка",
        }
        resp = client.post("/api/family-members", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Взрослый"
        assert data["portion_multiplier"] == 1.0
        assert data["dietary_restrictions"] == "без глютена"
        container.create_family_member.execute.assert_called_once()

    def test_creates_with_minimal_fields(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.create_family_member.execute.return_value = FamilyMember(
            id=FamilyMemberId(1), name="Ребёнок"
        )
        resp = client.post("/api/family-members", json={"name": "Ребёнок"})
        assert resp.status_code == 201

    def test_returns_422_on_missing_name(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.post("/api/family-members", json={})
        assert resp.status_code == 422


# ---- PUT /api/family-members/{member_id} ----


class TestUpdateFamilyMember:
    def test_updates_and_returns_member(
        self, client: TestClient, container: MagicMock
    ) -> None:
        updated = FamilyMember(
            id=FamilyMemberId(1), name="Ребёнок", portion_multiplier=0.5
        )
        container.edit_family_member.execute.return_value = updated
        body = {"name": "Ребёнок", "portion_multiplier": 0.5}
        resp = client.put("/api/family-members/1", json=body)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Ребёнок"
        assert resp.json()["portion_multiplier"] == 0.5

    def test_returns_404_when_not_found(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.edit_family_member.execute.side_effect = EntityNotFoundError(
            "Член семьи 999 не найден"
        )
        body = {"name": "Ребёнок"}
        resp = client.put("/api/family-members/999", json=body)
        assert resp.status_code == 404
        assert "не найден" in resp.json()["detail"]


# ---- DELETE /api/family-members/{member_id} ----


class TestDeleteFamilyMember:
    def test_deletes_and_returns_204(
        self, client: TestClient, container: MagicMock
    ) -> None:
        resp = client.delete("/api/family-members/1")
        assert resp.status_code == 204
        container.delete_family_member.execute.assert_called_once()
