from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.import_entities import ImportEntities
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import UserId
from backend.infrastructure.export.registry import ImportRegistry

UID = UserId(1)


def _make_use_case(
    importer: MagicMock | None = None,
    session: MagicMock | None = None,
    entity_type: str = "products",
    format: str = "csv",
) -> ImportEntities:
    registry = ImportRegistry()
    if importer:
        registry.register(entity_type, format, importer)
    return ImportEntities(registry, session or MagicMock())


def _mock_importer(result: ImportResult | None = None, raises: Exception | None = None) -> MagicMock:
    m = MagicMock()
    if raises:
        m.import_from_bytes.side_effect = raises
    else:
        m.import_from_bytes.return_value = result or ImportResult(created=1, updated=0)
    return m


def test_execute_returns_import_result() -> None:
    importer = _mock_importer(ImportResult(created=3, updated=1))
    result = _make_use_case(importer=importer).execute("products", "csv", b"data", UID)
    assert result == ImportResult(created=3, updated=1)


def test_execute_commits_session_on_success() -> None:
    session = MagicMock()
    _make_use_case(importer=_mock_importer(), session=session).execute(
        "products", "csv", b"data", UID
    )
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_execute_rollback_on_import_validation_error() -> None:
    session = MagicMock()
    importer = _mock_importer(raises=ImportValidationError("bad file"))
    uc = _make_use_case(importer=importer, session=session)
    with pytest.raises(ImportValidationError):
        uc.execute("products", "csv", b"data", UID)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_execute_rollback_on_unexpected_error() -> None:
    session = MagicMock()
    importer = _mock_importer(raises=RuntimeError("db failure"))
    uc = _make_use_case(importer=importer, session=session)
    with pytest.raises(ImportValidationError, match="Ошибка импорта"):
        uc.execute("products", "csv", b"data", UID)
    session.rollback.assert_called_once()


def test_execute_unknown_format_raises() -> None:
    session = MagicMock()
    uc = _make_use_case(session=session)
    with pytest.raises(ImportValidationError, match="xml"):
        uc.execute("products", "xml", b"data", UID)
    session.rollback.assert_not_called()
    session.commit.assert_not_called()


def test_execute_passes_data_and_user_id_to_importer() -> None:
    importer = _mock_importer()
    _make_use_case(importer=importer).execute("products", "csv", b"mydata", UID)
    importer.import_from_bytes.assert_called_once_with(b"mydata", UID)
