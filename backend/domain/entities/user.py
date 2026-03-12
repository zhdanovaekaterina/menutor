from dataclasses import dataclass, field
from datetime import UTC, datetime

from backend.domain.value_objects.types import UserId


@dataclass
class User:
    id: UserId
    email: str
    nickname: str
    hashed_password: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
