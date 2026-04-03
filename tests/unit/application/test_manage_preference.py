from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.manage_preference import (
    CreatePreference,
    DeletePreference,
    PreferenceData,
    UpdatePreference,
)
from backend.application.use_cases.crud_base import GetEntity, ListEntities
from backend.domain.entities.preference import Preference
from backend.domain.exceptions import DuplicateNameError, EntityNotFoundError
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import PreferenceId, RecipeCategoryId, UserId

UID = UserId(1)


def _pref(id: int = 1, name: str = "Веган") -> Preference:
    return Preference(
        id=PreferenceId(id),
        name=name,
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        user_id=UID,
    )


def _data(name: str = "Веган") -> PreferenceData:
    return PreferenceData(
        name=name,
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
    )


# ---- CreatePreference ----

def test_create_preference_saves_and_returns() -> None:
    repo = MagicMock()
    repo.find_by_name.return_value = None
    repo.save.return_value = _pref()

    result = CreatePreference(repo).execute(_data(), UID)

    repo.save.assert_called_once()
    assert result == _pref()


def test_create_preference_duplicate_name_raises() -> None:
    repo = MagicMock()
    repo.find_by_name.return_value = _pref()

    with pytest.raises(DuplicateNameError):
        CreatePreference(repo).execute(_data(), UID)


# ---- UpdatePreference ----

def test_update_preference_saves_with_updated_fields() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _pref(id=1)
    repo.find_by_name.return_value = None
    repo.save.return_value = _pref(id=1, name="Вегетарианское")

    result = UpdatePreference(repo).execute(PreferenceId(1), _data("Вегетарианское"), UID)

    repo.save.assert_called_once()
    assert result.name == "Вегетарианское"


def test_update_preference_not_owned_raises() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None  # not found => not owned

    with pytest.raises(EntityNotFoundError):
        UpdatePreference(repo).execute(PreferenceId(999), _data(), UID)


def test_update_preference_duplicate_name_different_id_raises() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _pref(id=1)
    repo.find_by_name.return_value = _pref(id=2, name="Веган")  # different id, same name

    with pytest.raises(DuplicateNameError):
        UpdatePreference(repo).execute(PreferenceId(1), _data("Веган"), UID)


def test_update_preference_same_name_same_id_succeeds() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _pref(id=1)
    repo.find_by_name.return_value = _pref(id=1, name="Веган")  # same id
    repo.save.return_value = _pref(id=1)

    result = UpdatePreference(repo).execute(PreferenceId(1), _data("Веган"), UID)

    repo.save.assert_called_once()
    assert result is not None


# ---- DeletePreference ----

def test_delete_preference_unlinks_from_members_and_deletes() -> None:
    from backend.domain.entities.family_member import FamilyMember
    from backend.domain.value_objects.types import FamilyMemberId

    pref_repo = MagicMock()
    family_repo = MagicMock()
    pref_repo.get_by_id.return_value = _pref(id=1)

    member = FamilyMember(
        id=FamilyMemberId(10),
        name="Боб",
        preference_ids=[PreferenceId(1), PreferenceId(2)],
        user_id=UID,
    )
    family_repo.find_all.return_value = [member]
    family_repo.save.return_value = member

    DeletePreference(pref_repo, family_repo).execute(PreferenceId(1), UID)

    family_repo.save.assert_called_once()
    pref_repo.delete.assert_called_once_with([PreferenceId(1)])


def test_delete_preference_not_owned_does_nothing() -> None:
    pref_repo = MagicMock()
    family_repo = MagicMock()
    pref_repo.get_by_id.return_value = None  # not found

    DeletePreference(pref_repo, family_repo).execute(PreferenceId(999), UID)

    pref_repo.delete.assert_not_called()
    family_repo.find_all.assert_not_called()


# ---- GetEntity / ListEntities (used as GetPreference / ListPreferences) ----

def test_get_preference_returns_owned() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _pref(id=1)

    result = GetEntity(repo).execute(PreferenceId(1), UID)

    assert result == _pref(id=1)


def test_get_preference_returns_none_for_non_owned() -> None:
    repo = MagicMock()
    other_uid = UserId(99)
    pref = _pref(id=1)
    pref_with_other_user = Preference(
        id=PreferenceId(1),
        name="Веган",
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        user_id=other_uid,
    )
    repo.get_by_id.return_value = pref_with_other_user

    result = GetEntity(repo).execute(PreferenceId(1), UID)

    assert result is None


def test_list_preferences_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_pref(1), _pref(2)]

    result = ListEntities(repo).execute(UID)

    assert len(result) == 2


def test_create_preference_with_recipe_category_ids() -> None:
    repo = MagicMock()
    repo.find_by_name.return_value = None
    saved = _pref()
    saved.recipe_category_ids = [RecipeCategoryId(3)]
    repo.save.return_value = saved

    data = PreferenceData(
        name="Веган",
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        recipe_category_ids=[RecipeCategoryId(3)],
    )
    CreatePreference(repo).execute(data, UID)

    call_arg: Preference = repo.save.call_args[0][0]
    assert call_arg.recipe_category_ids == [RecipeCategoryId(3)]


def test_update_preference_with_recipe_category_ids() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _pref(id=1)
    repo.find_by_name.return_value = None
    saved = _pref(id=1)
    saved.recipe_category_ids = [RecipeCategoryId(5)]
    repo.save.return_value = saved

    data = PreferenceData(
        name="Веган",
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        recipe_category_ids=[RecipeCategoryId(5)],
    )
    UpdatePreference(repo).execute(PreferenceId(1), data, UID)

    call_arg: Preference = repo.save.call_args[0][0]
    assert call_arg.recipe_category_ids == [RecipeCategoryId(5)]
