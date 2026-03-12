from abc import ABC, abstractmethod

from backend.domain.entities.user import User
from backend.domain.value_objects.types import UserId


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: UserId) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> User: ...
