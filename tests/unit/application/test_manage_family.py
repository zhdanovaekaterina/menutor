from unittest.mock import MagicMock

import pytest

from src.application.use_cases.manage_family import (
    CreateFamilyMember,
    DeleteFamilyMember,
    EditFamilyMember,
    FamilyMemberData,
    ListFamilyMembers,
)
from src.domain.entities.family_member import FamilyMember
from src.domain.value_objects.types import FamilyMemberId


def _data(**kwargs) -> FamilyMemberData:
    defaults = dict(name="Алиса", portion_multiplier=1.0,
                    dietary_restrictions="", comment="")
    defaults.update(kwargs)
    return FamilyMemberData(**defaults)


def _saved(id: int = 1) -> FamilyMember:
    return FamilyMember(FamilyMemberId(id), "Алиса", portion_multiplier=1.0)


# ---- CreateFamilyMember ----

def test_create_member_calls_save() -> None:
    repo = MagicMock()
    repo.save.return_value = _saved()

    result = CreateFamilyMember(repo).execute(_data())

    repo.save.assert_called_once()
    assert result == _saved()


def test_create_member_builds_entity_correctly() -> None:
    repo = MagicMock()
    repo.save.side_effect = lambda m: m

    result = CreateFamilyMember(repo).execute(_data(name="Боб", portion_multiplier=0.5))

    assert result.name == "Боб"
    assert result.portion_multiplier == 0.5


# ---- EditFamilyMember ----

def test_edit_member_updates_fields() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _saved()
    repo.save.side_effect = lambda m: m

    result = EditFamilyMember(repo).execute(FamilyMemberId(1), _data(name="Новое имя"))

    assert result.name == "Новое имя"
    assert result.id == FamilyMemberId(1)


def test_edit_member_raises_when_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="не найден"):
        EditFamilyMember(repo).execute(FamilyMemberId(999), _data())


# ---- DeleteFamilyMember ----

def test_delete_member_calls_repo_delete() -> None:
    repo = MagicMock()

    DeleteFamilyMember(repo).execute(FamilyMemberId(1))

    repo.delete.assert_called_once_with(FamilyMemberId(1))


# ---- ListFamilyMembers ----

def test_list_members_returns_all() -> None:
    repo = MagicMock()
    repo.find_all.return_value = [_saved(1), _saved(2)]

    assert len(ListFamilyMembers(repo).execute()) == 2
