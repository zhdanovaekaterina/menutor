"""Tests for import/export router endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult


class TestExportEntities:
    def test_export_products_csv_returns_200(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.return_value = (
            b"id,name\n1,Muka", "text/csv", "products.csv"
        )
        resp = client.get("/api/products/export/csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert 'filename="products.csv"' in resp.headers["content-disposition"]

    def test_export_products_json_returns_200(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.return_value = (
            b"[]", "application/json", "products.json"
        )
        resp = client.get("/api/products/export/json")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")

    def test_export_with_ids_passes_id_list(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.return_value = (b"data", "text/csv", "products.csv")
        client.get("/api/products/export/csv?ids=1,2")
        _, call_kwargs = container.export_entities.execute.call_args
        assert call_kwargs.get("entity_ids") == [1, 2] or \
               container.export_entities.execute.call_args[0][3] == [1, 2]

    def test_export_without_ids_passes_none(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.return_value = (b"data", "text/csv", "products.csv")
        client.get("/api/products/export/csv")
        args = container.export_entities.execute.call_args[0]
        assert args[3] is None

    def test_export_recipes_json_dispatches_correctly(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.return_value = (b"[]", "application/json", "recipes.json")
        resp = client.get("/api/recipes/export/json")
        assert resp.status_code == 200
        args = container.export_entities.execute.call_args[0]
        assert args[0] == "recipes"
        assert args[1] == "json"

    def test_export_unknown_format_returns_422(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.execute.side_effect = ImportValidationError("unsupported")
        resp = client.get("/api/products/export/xml")
        assert resp.status_code == 422


class TestExportExample:
    def test_export_example_returns_200(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.example.return_value = (
            b"id,name\n1,Example", "text/csv", "example_products.csv"
        )
        resp = client.get("/api/products/export/csv/example")
        assert resp.status_code == 200
        assert 'filename="example_products.csv"' in resp.headers["content-disposition"]

    def test_export_example_unknown_format_returns_422(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.export_entities.example.side_effect = ImportValidationError("unsupported")
        resp = client.get("/api/products/export/xml/example")
        assert resp.status_code == 422


class TestImportEntities:
    def test_import_products_csv_returns_result(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.import_entities.execute.return_value = ImportResult(
            created=2, updated=0, errors=[]
        )
        resp = client.post(
            "/api/products/import/csv",
            files={"file": ("products.csv", b"id,name\n,Test", "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["created"] == 2
        assert body["updated"] == 0
        assert body["errors"] == []

    def test_import_menus_json(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.import_entities.execute.return_value = ImportResult(
            created=1, updated=0, errors=[]
        )
        resp = client.post(
            "/api/menus/import/json",
            files={"file": ("menus.json", b"[]", "application/json")},
        )
        assert resp.status_code == 200
        args = container.import_entities.execute.call_args[0]
        assert args[0] == "menus"
        assert args[1] == "json"

    def test_import_bad_file_returns_422(
        self, client: TestClient, container: MagicMock
    ) -> None:
        container.import_entities.execute.side_effect = ImportValidationError("bad format")
        resp = client.post(
            "/api/products/import/csv",
            files={"file": ("bad.csv", b"corrupted", "text/csv")},
        )
        assert resp.status_code == 422
        assert "bad format" in resp.json()["detail"]
