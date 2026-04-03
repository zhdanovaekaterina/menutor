from datetime import time
from unittest.mock import MagicMock

import pytest

from backend.application.use_cases.manage_meal_type import (
    CheckMealTypeUsage,
    CreateMealType,
    CreateSystemMealTypes,
    DeleteMealType,
    ListMealTypes,
    MealTypeData,
    UpdateMealType,
)
from backend.domain.entities.meal_type import MealType
from backend.domain.exceptions import (
    DuplicateNameError,
    EntityNotFoundError,
    MealTypeLimitError,
    SystemMealTypeDeletionError,
)
from backend.domain.value_objects.types import MealTypeId, UserId


USER_ID = UserId(1)


def _mt(id: int, name: str, t: time = time(8, 0), is_system: bool = False, sort_order: int = 0) -> MealType:
    return MealType(
        id=MealTypeId(id),
        user_id=USER_ID,
        name=name,
        time=t,
        is_system=is_system,
        sort_order=sort_order,
    )


def _mock_repo(**kwargs: object) -> MagicMock:
    repo = MagicMock()
    repo.get_by_id.return_value = kwargs.get("get_by_id", None)
    repo.find_all.return_value = kwargs.get("find_all", [])
    repo.find_by_name.return_value = kwargs.get("find_by_name", None)
    repo.count_custom.return_value = kwargs.get("count_custom", 0)
    repo.save.side_effect = lambda mt: mt
    repo.get_usage.return_value = kwargs.get("get_usage", [])
    return repo


# ─── CreateMealType ───────────────────────────────────────────────────────────

def test_create_meal_type_success() -> None:
    repo = _mock_repo()
    result = CreateMealType(repo).execute(MealTypeData("Полдник", time(15, 0)), USER_ID)
    assert result.name == "Полдник"
    assert result.is_system is False
    repo.save.assert_called_once()


def test_create_meal_type_empty_name() -> None:
    repo = _mock_repo()
    with pytest.raises(ValueError, match="от 1 до 50"):
        CreateMealType(repo).execute(MealTypeData("", time(15, 0)), USER_ID)


def test_create_meal_type_long_name() -> None:
    repo = _mock_repo()
    with pytest.raises(ValueError, match="от 1 до 50"):
        CreateMealType(repo).execute(MealTypeData("А" * 51, time(15, 0)), USER_ID)


def test_create_meal_type_duplicate_name() -> None:
    existing = _mt(1, "Полдник")
    repo = _mock_repo(find_by_name=existing)
    with pytest.raises(DuplicateNameError):
        CreateMealType(repo).execute(MealTypeData("Полдник", time(15, 0)), USER_ID)


def test_create_meal_type_limit_reached() -> None:
    repo = _mock_repo(count_custom=10)
    with pytest.raises(MealTypeLimitError):
        CreateMealType(repo).execute(MealTypeData("Новый", time(15, 0)), USER_ID)


def test_create_meal_type_sort_order_increments() -> None:
    existing_types = [_mt(1, "Завтрак", sort_order=0), _mt(2, "Обед", sort_order=1)]
    repo = _mock_repo(find_all=existing_types)
    result = CreateMealType(repo).execute(MealTypeData("Полдник", time(15, 0)), USER_ID)
    assert result.sort_order == 2


# ─── UpdateMealType ───────────────────────────────────────────────────────────

def test_update_meal_type_success() -> None:
    mt = _mt(1, "Старое", time(8, 0))
    repo = _mock_repo(get_by_id=mt)
    result = UpdateMealType(repo).execute(MealTypeId(1), MealTypeData("Новое", time(9, 0)), USER_ID)
    assert result.name == "Новое"
    assert result.time == time(9, 0)


def test_update_meal_type_duplicate_name() -> None:
    mt = _mt(1, "Завтрак")
    other = _mt(2, "Обед")
    repo = _mock_repo(get_by_id=mt, find_by_name=other)
    with pytest.raises(DuplicateNameError):
        UpdateMealType(repo).execute(MealTypeId(1), MealTypeData("Обед", time(13, 0)), USER_ID)


def test_update_meal_type_same_name_same_id() -> None:
    mt = _mt(1, "Завтрак")
    repo = _mock_repo(get_by_id=mt, find_by_name=mt)
    result = UpdateMealType(repo).execute(MealTypeId(1), MealTypeData("Завтрак", time(9, 0)), USER_ID)
    assert result.name == "Завтрак"


def test_update_system_type_name() -> None:
    mt = _mt(1, "Завтрак", is_system=True)
    repo = _mock_repo(get_by_id=mt)
    result = UpdateMealType(repo).execute(MealTypeId(1), MealTypeData("Утро", time(8, 0)), USER_ID)
    assert result.name == "Утро"


def test_update_system_type_time() -> None:
    mt = _mt(1, "Завтрак", is_system=True)
    repo = _mock_repo(get_by_id=mt)
    result = UpdateMealType(repo).execute(MealTypeId(1), MealTypeData("Завтрак", time(7, 30)), USER_ID)
    assert result.time == time(7, 30)


# ─── DeleteMealType ───────────────────────────────────────────────────────────

def test_delete_custom_type() -> None:
    mt = _mt(5, "Полдник")
    repo = _mock_repo(get_by_id=mt)
    DeleteMealType(repo).execute(MealTypeId(5), USER_ID)
    repo.delete.assert_called_once_with([MealTypeId(5)])


def test_delete_system_type() -> None:
    mt = _mt(1, "Завтрак", is_system=True)
    repo = _mock_repo(get_by_id=mt)
    with pytest.raises(SystemMealTypeDeletionError):
        DeleteMealType(repo).execute(MealTypeId(1), USER_ID)


def test_delete_nonexistent() -> None:
    repo = _mock_repo(get_by_id=None)
    with pytest.raises(EntityNotFoundError):
        DeleteMealType(repo).execute(MealTypeId(99), USER_ID)


# ─── ListMealTypes ────────────────────────────────────────────────────────────

def test_list_meal_types_sorted_by_time() -> None:
    types = [
        _mt(3, "Ужин", time(18, 0), sort_order=2),
        _mt(1, "Завтрак", time(8, 0), sort_order=0),
        _mt(2, "Обед", time(13, 0), sort_order=1),
    ]
    repo = _mock_repo(find_all=types)
    result = ListMealTypes(repo).execute(USER_ID)
    assert [t.name for t in result] == ["Завтрак", "Обед", "Ужин"]


# ─── CheckMealTypeUsage ───────────────────────────────────────────────────────

def test_check_usage_no_menus() -> None:
    mt = _mt(1, "Завтрак")
    repo = _mock_repo(get_by_id=mt, get_usage=[])
    result = CheckMealTypeUsage(repo).execute(MealTypeId(1), USER_ID)
    assert result == []


def test_check_usage_with_menus() -> None:
    mt = _mt(1, "Завтрак")
    repo = _mock_repo(get_by_id=mt, get_usage=[(10, "Меню 1"), (11, "Меню 2")])
    result = CheckMealTypeUsage(repo).execute(MealTypeId(1), USER_ID)
    assert len(result) == 2
    assert result[0] == (10, "Меню 1")


# ─── CreateSystemMealTypes ────────────────────────────────────────────────────

def test_create_system_meal_types() -> None:
    repo = _mock_repo()
    result = CreateSystemMealTypes(repo).execute(USER_ID)
    assert len(result) == 3
    names = [mt.name for mt in result]
    assert "Завтрак" in names
    assert "Обед" in names
    assert "Ужин" in names
    for mt in result:
        assert mt.is_system is True
