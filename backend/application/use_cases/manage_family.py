from dataclasses import dataclass, field
from typing import Any

from backend.application.use_cases.crud_base import (
    CreateEntity,
    DeleteEntity,
    EditEntity,
    ListEntities,
)
from backend.domain.entities.family_member import FamilyMember
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.value_objects.types import FamilyMemberId, PreferenceId, UserId


@dataclass
class FamilyMemberData:
    name: str
    portion_multiplier: float = field(default=1.0)
    comment: str = field(default="")
    preference_ids: list[PreferenceId] = field(default_factory=list)


def _build_member(
    id: FamilyMemberId, data: FamilyMemberData, user_id: UserId,
) -> FamilyMember:
    return FamilyMember(
        id=id,
        name=data.name,
        portion_multiplier=data.portion_multiplier,
        comment=data.comment,
        user_id=user_id,
        preference_ids=data.preference_ids,
    )


class CreateFamilyMember(CreateEntity):
    def __init__(self, repo: FamilyMemberRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, data: Any, user_id: UserId) -> FamilyMember:
        return _build_member(FamilyMemberId(0), data, user_id)


class EditFamilyMember(EditEntity):
    _label = "Член семьи"

    def __init__(self, repo: FamilyMemberRepository) -> None:
        super().__init__(repo)

    def _build_entity(self, id: Any, data: Any, user_id: UserId) -> FamilyMember:
        return _build_member(id, data, user_id)


DeleteFamilyMember = DeleteEntity
ListFamilyMembers = ListEntities
