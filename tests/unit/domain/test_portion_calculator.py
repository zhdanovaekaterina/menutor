from backend.domain.entities.family_member import FamilyMember
from backend.domain.services.portion_calculator import PortionCalculator
from backend.domain.value_objects.types import FamilyMemberId


def _member(id: int, multiplier: float) -> FamilyMember:
    return FamilyMember(FamilyMemberId(id), f"Member{id}", portion_multiplier=multiplier)


def test_single_adult_full_portion() -> None:
    calc = PortionCalculator()
    assert calc.total_servings(4, [_member(1, 1.0)]) == 4.0


def test_single_child_half_portion() -> None:
    calc = PortionCalculator()
    assert calc.total_servings(4, [_member(1, 0.5)]) == 2.0


def test_family_of_three() -> None:
    calc = PortionCalculator()
    members = [_member(1, 1.0), _member(2, 1.0), _member(3, 0.5)]
    # (1.0 + 1.0 + 0.5) * 2 = 5.0
    assert calc.total_servings(2, members) == 5.0


def test_empty_members_returns_zero() -> None:
    calc = PortionCalculator()
    assert calc.total_servings(4, []) == 0.0


def test_effective_servings_on_member() -> None:
    member = _member(1, 0.75)
    assert member.effective_servings(4) == 3.0
