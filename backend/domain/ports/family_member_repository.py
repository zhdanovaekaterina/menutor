from abc import ABC, abstractmethod

from backend.domain.entities.family_member import FamilyMember
from backend.domain.value_objects.types import FamilyMemberId, UserId


class FamilyMemberRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: FamilyMemberId) -> FamilyMember | None: ...

    @abstractmethod
    def find_all(self, user_id: UserId) -> list[FamilyMember]: ...

    @abstractmethod
    def save(self, member: FamilyMember) -> FamilyMember: ...

    @abstractmethod
    def delete(self, id: FamilyMemberId) -> None: ...
