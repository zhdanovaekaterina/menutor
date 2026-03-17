from sqlalchemy.orm import Session

from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import UserId
from backend.infrastructure.export.registry import ImportRegistry


class ImportEntities:
    """Import entities from an uploaded file. All-or-nothing transaction."""

    def __init__(self, import_registry: ImportRegistry, session: Session) -> None:
        self._registry = import_registry
        self._session = session

    def execute(
        self,
        entity_type: str,
        format: str,
        data: bytes,
        user_id: UserId,
    ) -> ImportResult:
        importer = self._registry.get(entity_type, format)
        if importer is None:
            raise ImportValidationError(
                f"Формат '{format}' не поддерживается для '{entity_type}'"
            )
        try:
            result = importer.import_from_bytes(data, user_id)
            self._session.commit()
            return result
        except ImportValidationError:
            self._session.rollback()
            raise
        except Exception as e:
            self._session.rollback()
            raise ImportValidationError(f"Ошибка импорта: {e}") from e
