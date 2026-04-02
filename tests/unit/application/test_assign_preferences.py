from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.assign_preferences import AssignPreferencesToMember
from backend.domain.entities.family_member import FamilyMember
from backend.domain.entities.preference import Preference
from backend.domain.exceptions import EntityNotFoundError, IncompatiblePreferenceModesError
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import FamilyMemberId, PreferenceId, UserId

UID = UserId(1)


def _member(pref_ids: list[int] | None = None) -> FamilyMember:
    return FamilyMember(
        id=FamilyMemberId(1),
        name="Алиса",
        user_id=UID,
        preference_ids=[PreferenceId(p) for p in (pref_ids or [])],
    )


def _pref(
    pid: int,
    ptype: PreferenceType = PreferenceType.CATEGORY_BASED,
    mode: PreferenceMode = PreferenceMode.BLOCKED,
) -> Preference:
    return Preference(
        id=PreferenceId(pid),
        name=f"Pref{pid}",
        type=ptype,
        mode=mode,
        user_id=UID,
    )


def _use_case(member: FamilyMember | None, prefs: list[Preference]) -> AssignPreferencesToMember:
    family_repo = MagicMock()
    pref_repo = MagicMock()
    family_repo.get_by_id.return_value = member
    family_repo.save.side_effect = lambda m: m
    pref_repo.find_by_ids.return_value = prefs
    return AssignPreferencesToMember(family_repo=family_repo, preference_repo=pref_repo)


def test_assign_blocked_preferences_saves_member() -> None:
    uc = _use_case(_member(), [_pref(1, mode=PreferenceMode.BLOCKED)])
    result = uc.execute(FamilyMemberId(1), [PreferenceId(1)], UID)
    assert result.preference_ids == [PreferenceId(1)]


def test_assign_allowed_preferences_saves_member() -> None:
    uc = _use_case(_member(), [_pref(1, mode=PreferenceMode.ALLOWED)])
    result = uc.execute(FamilyMemberId(1), [PreferenceId(1)], UID)
    assert result.preference_ids == [PreferenceId(1)]


def test_assign_mixed_blocked_and_allowed_raises() -> None:
    blocked = _pref(1, mode=PreferenceMode.BLOCKED)
    allowed = _pref(2, mode=PreferenceMode.ALLOWED)
    uc = _use_case(_member(), [blocked, allowed])
    with pytest.raises(IncompatiblePreferenceModesError):
        uc.execute(FamilyMemberId(1), [PreferenceId(1), PreferenceId(2)], UID)


def test_assign_allergy_plus_blocked_category_succeeds() -> None:
    allergy = _pref(1, ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED)
    blocked = _pref(2, ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED)
    uc = _use_case(_member(), [allergy, blocked])
    result = uc.execute(FamilyMemberId(1), [PreferenceId(1), PreferenceId(2)], UID)
    assert len(result.preference_ids) == 2


def test_assign_allergy_plus_allowed_raises() -> None:
    allergy = _pref(1, ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED)
    allowed = _pref(2, ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED)
    uc = _use_case(_member(), [allergy, allowed])
    with pytest.raises(IncompatiblePreferenceModesError):
        uc.execute(FamilyMemberId(1), [PreferenceId(1), PreferenceId(2)], UID)


def test_assign_empty_list_clears_preferences() -> None:
    uc = _use_case(_member([1, 2]), [])
    result = uc.execute(FamilyMemberId(1), [], UID)
    assert result.preference_ids == []


def test_assign_nonexistent_preference_raises() -> None:
    family_repo = MagicMock()
    pref_repo = MagicMock()
    family_repo.get_by_id.return_value = _member()
    # find_by_ids returns empty — the preference wasn't found
    pref_repo.find_by_ids.return_value = []
    uc = AssignPreferencesToMember(family_repo=family_repo, preference_repo=pref_repo)
    with pytest.raises(EntityNotFoundError):
        uc.execute(FamilyMemberId(1), [PreferenceId(999)], UID)


def test_assign_to_nonowned_member_raises() -> None:
    uc = _use_case(None, [])  # member not found
    with pytest.raises(EntityNotFoundError):
        uc.execute(FamilyMemberId(999), [], UID)
