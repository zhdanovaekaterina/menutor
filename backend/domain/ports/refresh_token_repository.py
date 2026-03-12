from abc import ABC, abstractmethod

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.value_objects.types import UserId


class RefreshTokenRepository(ABC):
    @abstractmethod
    def save(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    def revoke(self, token_hash: str) -> None: ...

    @abstractmethod
    def revoke_all_for_user(self, user_id: UserId) -> None: ...
