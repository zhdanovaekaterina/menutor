import pytest

from backend.domain.entities.family_member import FamilyMember
from backend.domain.value_objects.types import FamilyMemberId
from backend.infrastructure.repositories.sqlite_family_member_repository import (
    SqliteFamilyMemberRepository,
)


@pytest.fixture
def repo(conn: object) -> SqliteFamilyMemberRepository:
    return SqliteFamilyMemberRepository(conn)  # type: ignore[arg-type]


def _member(**kw: object) -> FamilyMember:
    defaults: dict = dict(
        id=FamilyMemberId(0),
        name="Алиса",
        portion_multiplier=1.0,
        dietary_restrictions="",
        comment="",
    )
    defaults.update(kw)
    return FamilyMember(**defaults)


def test_save_assigns_id(repo: SqliteFamilyMemberRepository) -> None:
    saved = repo.save(_member())
    assert saved.id != FamilyMemberId(0)


def test_save_and_get_by_id_roundtrip(repo: SqliteFamilyMemberRepository) -> None:
    saved = repo.save(_member(
        name="Боб", portion_multiplier=0.5,
        dietary_restrictions="без глютена", comment="школьный обед",
    ))
    retrieved = repo.get_by_id(saved.id)

    assert retrieved is not None
    assert retrieved.name == "Боб"
    assert retrieved.portion_multiplier == pytest.approx(0.5)
    assert retrieved.dietary_restrictions == "без глютена"
    assert retrieved.comment == "школьный обед"


def test_get_by_id_returns_none_when_absent(repo: SqliteFamilyMemberRepository) -> None:
    assert repo.get_by_id(FamilyMemberId(9999)) is None


def test_delete_removes_member(repo: SqliteFamilyMemberRepository) -> None:
    saved = repo.save(_member())
    repo.delete(saved.id)
    assert repo.get_by_id(saved.id) is None


def test_find_all_returns_all_members(repo: SqliteFamilyMemberRepository) -> None:
    repo.save(_member(name="Алиса"))
    repo.save(_member(name="Боб"))
    repo.save(_member(name="Ребёнок", portion_multiplier=0.5))
    assert len(repo.find_all()) == 3


def test_update_existing_member(repo: SqliteFamilyMemberRepository) -> None:
    saved = repo.save(_member(name="Алиса"))
    updated = FamilyMember(
        id=saved.id,
        name="Алиса Иванова",
        portion_multiplier=0.75,
        dietary_restrictions="вегетарианец",
        comment="обновлено",
    )
    result = repo.save(updated)
    assert result.name == "Алиса Иванова"
    assert result.portion_multiplier == pytest.approx(0.75)
