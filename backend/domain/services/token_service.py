from abc import ABC, abstractmethod

from backend.domain.value_objects.types import UserId


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: UserId) -> str: ...

    @abstractmethod
    def create_refresh_token(self, user_id: UserId) -> str: ...

    @abstractmethod
    def validate_access_token(self, token: str) -> UserId | None:
        """Return UserId if token is valid, None otherwise."""
        ...

    @abstractmethod
    def get_refresh_token_hash(self, token: str) -> str:
        """Return a hash of the raw refresh token for DB storage."""
        ...
