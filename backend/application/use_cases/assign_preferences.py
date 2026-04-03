from backend.domain.entities.family_member import FamilyMember
from backend.domain.exceptions import (
    EntityNotFoundError,
    IncompatiblePreferenceModesError,
)
from backend.domain.ports.family_member_repository import FamilyMemberRepository
from backend.domain.ports.preference_repository import PreferenceRepository
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import FamilyMemberId, PreferenceId, UserId


class AssignPreferencesToMember:
    """Replaces all preference assignments on a family member.

    Validates BR-3: all preferences must share the same effective mode
    (all BLOCKED-family or all ALLOWED-family).
    """

    def __init__(
        self,
        family_repo: FamilyMemberRepository,
        preference_repo: PreferenceRepository,
    ) -> None:
        self._family_repo = family_repo
        self._preference_repo = preference_repo

    def execute(
        self,
        member_id: FamilyMemberId,
        preference_ids: list[PreferenceId],
        user_id: UserId,
    ) -> FamilyMember:
        member = self._family_repo.get_by_id(member_id)
        if member is None or member.user_id != user_id:
            raise EntityNotFoundError(f"Член семьи {member_id} не найден")

        if preference_ids:
            preferences = self._preference_repo.find_by_ids(preference_ids, user_id)
            found_ids = {p.id for p in preferences}
            for pid in preference_ids:
                if pid not in found_ids:
                    raise EntityNotFoundError(f"Предпочтение {pid} не найдено")
            self._validate_mode_compatibility(preferences)

        member.preference_ids = preference_ids
        return self._family_repo.save(member)

    @staticmethod
    def _validate_mode_compatibility(preferences: list) -> None:
        """Ensure all preferences have compatible modes (BR-3)."""
        has_blocked = False
        has_allowed = False
        for p in preferences:
            effective_mode = (
                PreferenceMode.BLOCKED
                if p.type == PreferenceType.ALLERGY
                else p.mode
            )
            if effective_mode == PreferenceMode.BLOCKED:
                has_blocked = True
            else:
                has_allowed = True
        if has_blocked and has_allowed:
            raise IncompatiblePreferenceModesError(
                "Нельзя назначить одному члену семьи предпочтения "
                "с режимами BLOCKED и ALLOWED одновременно"
            )
