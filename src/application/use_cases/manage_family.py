from dataclasses import dataclass, field

from src.domain.entities.family_member import FamilyMember
from src.domain.ports.family_member_repository import FamilyMemberRepository
from src.domain.value_objects.types import FamilyMemberId


@dataclass
class FamilyMemberData:
    name: str
    portion_multiplier: float = field(default=1.0)
    dietary_restrictions: str = field(default="")
    comment: str = field(default="")


class CreateFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, data: FamilyMemberData) -> FamilyMember:
        member = FamilyMember(
            id=FamilyMemberId(0),
            name=data.name,
            portion_multiplier=data.portion_multiplier,
            dietary_restrictions=data.dietary_restrictions,
            comment=data.comment,
        )
        return self._repo.save(member)


class EditFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, id: FamilyMemberId, data: FamilyMemberData) -> FamilyMember:
        if self._repo.get_by_id(id) is None:
            raise ValueError(f"Член семьи {id} не найден")
        member = FamilyMember(
            id=id,
            name=data.name,
            portion_multiplier=data.portion_multiplier,
            dietary_restrictions=data.dietary_restrictions,
            comment=data.comment,
        )
        return self._repo.save(member)


class DeleteFamilyMember:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self, id: FamilyMemberId) -> None:
        self._repo.delete(id)


class ListFamilyMembers:
    def __init__(self, repo: FamilyMemberRepository) -> None:
        self._repo = repo

    def execute(self) -> list[FamilyMember]:
        return self._repo.find_all()
