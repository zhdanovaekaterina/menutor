from abc import ABC, abstractmethod

from src.domain.entities.family_member import FamilyMember
from src.domain.value_objects.types import FamilyMemberId


class FamilyMemberRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: FamilyMemberId) -> FamilyMember | None: ...

    @abstractmethod
    def find_all(self) -> list[FamilyMember]: ...

    @abstractmethod
    def save(self, member: FamilyMember) -> FamilyMember: ...

    @abstractmethod
    def delete(self, id: FamilyMemberId) -> None: ...
