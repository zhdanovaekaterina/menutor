from typing import Protocol

from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import UserId


class EntityImporter(Protocol):
    """Parses bytes and upserts entities."""

    def import_from_bytes(self, data: bytes, user_id: UserId) -> ImportResult: ...
    def supported_extensions(self) -> list[str]: ...
