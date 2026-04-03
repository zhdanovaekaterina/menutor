from abc import ABC, abstractmethod

from backend.domain.entities.preference import Preference
from backend.domain.value_objects.types import PreferenceId, UserId


class PreferenceRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: PreferenceId) -> Preference | None: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[Preference]: ...

    @abstractmethod
    def find_by_ids(self, ids: list[PreferenceId], user_id: UserId) -> list[Preference]: ...

    @abstractmethod
    def find_by_name(self, name: str, user_id: UserId) -> Preference | None: ...

    @abstractmethod
    def save(self, preference: Preference) -> Preference: ...

    @abstractmethod
    def delete(self, ids: list[PreferenceId]) -> None: ...
