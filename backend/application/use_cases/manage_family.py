from dataclasses import dataclass, field

from backend.domain.entities.family_member import FamilyMember
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.value_objects.types import FamilyMemberId, UserId


@dataclass
class FamilyMemberData:
    name: str
    portion_multiplier: float = field(default=1.0)
    dietary_restrictions: str = field(default="")
    comment: str = field(default="")


class CreateFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, data: FamilyMemberData, user_id: UserId) -> FamilyMember:
        member = FamilyMember(
            id=FamilyMemberId(0),
            name=data.name,
            portion_multiplier=data.portion_multiplier,
            dietary_restrictions=data.dietary_restrictions,
            comment=data.comment,
            user_id=user_id,
        )
        return self._repo.save(member)


class EditFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(
        self, id: FamilyMemberId, data: FamilyMemberData, user_id: UserId
    ) -> FamilyMember:
        existing = self._repo.get_by_id(id)
        if existing is None or existing.user_id != user_id:
            raise EntityNotFoundError(f"Член семьи {id} не найден")
        member = FamilyMember(
            id=id,
            name=data.name,
            portion_multiplier=data.portion_multiplier,
            dietary_restrictions=data.dietary_restrictions,
            comment=data.comment,
            user_id=user_id,
        )
        return self._repo.save(member)


class DeleteFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, id: FamilyMemberId, user_id: UserId) -> None:
        existing = self._repo.get_by_id(id)
        if existing is not None and existing.user_id == user_id:
            self._repo.delete(id)


class ListFamilyMembers:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, user_id: UserId) -> list[FamilyMember]:
        return self._repo.find_all(user_id)
