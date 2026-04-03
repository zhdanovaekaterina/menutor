from dataclasses import dataclass, field

from backend.application.use_cases.crud_base import load_owned
from backend.domain.entities.preference import Preference
from backend.domain.exceptions import DuplicateNameError
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.ports.preference_repository import PreferenceRepository
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import (
    PreferenceId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    UserId,
)


@dataclass
class PreferenceData:
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[ProductCategoryId] = field(default_factory=list)
    product_ids: list[ProductId] = field(default_factory=list)
    recipe_category_ids: list[RecipeCategoryId] = field(default_factory=list)


class CreatePreference:
    def __init__(self, repo: PreferenceRepository) -> None:
        self._repo = repo

    def execute(self, data: PreferenceData, user_id: UserId) -> Preference:
        existing = self._repo.find_by_name(data.name, user_id)
        if existing is not None:
            raise DuplicateNameError("предпочтение")
        preference = Preference(
            id=PreferenceId(0),
            name=data.name,
            type=data.type,
            mode=data.mode,
            category_ids=data.category_ids,
            product_ids=data.product_ids,
            recipe_category_ids=data.recipe_category_ids,
            user_id=user_id,
        )
        return self._repo.save(preference)


class UpdatePreference:
    def __init__(self, repo: PreferenceRepository) -> None:
        self._repo = repo

    def execute(
        self, preference_id: PreferenceId, data: PreferenceData, user_id: UserId
    ) -> Preference:
        load_owned(self._repo, preference_id, user_id, "Предпочтение")
        existing = self._repo.find_by_name(data.name, user_id)
        if existing is not None and existing.id != preference_id:
            raise DuplicateNameError("предпочтение")
        preference = Preference(
            id=preference_id,
            name=data.name,
            type=data.type,
            mode=data.mode,
            category_ids=data.category_ids,
            product_ids=data.product_ids,
            recipe_category_ids=data.recipe_category_ids,
            user_id=user_id,
        )
        return self._repo.save(preference)


class DeletePreference:
    def __init__(
        self,
        preference_repo: PreferenceRepository,
        family_repo: FamilyMemberRepository,
    ) -> None:
        self._preference_repo = preference_repo
        self._family_repo = family_repo

    def execute(self, preference_id: PreferenceId, user_id: UserId) -> None:
        existing = self._preference_repo.get_by_id(preference_id)
        if existing is None or existing.user_id != user_id:
            return  # silently ignore

        members = self._family_repo.find_all(user_id)
        for member in members:
            if preference_id in member.preference_ids:
                member.preference_ids.remove(preference_id)
                self._family_repo.save(member)

        self._preference_repo.delete([preference_id])
