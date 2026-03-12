from dataclasses import dataclass
from datetime import datetime

from backend.domain.value_objects.types import RefreshTokenId, UserId


@dataclass
class RefreshToken:
    id: RefreshTokenId
    user_id: UserId
    token_hash: str
    expires_at: datetime
    revoked: bool = False
