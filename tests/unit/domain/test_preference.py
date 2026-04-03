import pytest

from backend.domain.entities.preference import Preference
from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import PreferenceId, ProductCategoryId, ProductId, RecipeCategoryId, UserId


def _pref(**kwargs) -> Preference:
    defaults = dict(
        id=PreferenceId(1),
        name="Вегетарианское",
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
    )
    defaults.update(kwargs)
    return Preference(**defaults)


def test_valid_category_based_blocked():
    pref = _pref(type=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED)
    assert pref.name == "Вегетарианское"
    assert pref.type == PreferenceType.CATEGORY_BASED
    assert pref.mode == PreferenceMode.BLOCKED


def test_valid_category_based_allowed():
    pref = _pref(type=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED)
    assert pref.mode == PreferenceMode.ALLOWED


def test_valid_allergy():
    pref = _pref(type=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED)
    assert pref.type == PreferenceType.ALLERGY
    assert pref.mode == PreferenceMode.BLOCKED


def test_allergy_with_allowed_raises():
    with pytest.raises(InvalidEntityError, match="BLOCKED"):
        _pref(type=PreferenceType.ALLERGY, mode=PreferenceMode.ALLOWED)


def test_empty_name_raises():
    with pytest.raises(InvalidEntityError):
        _pref(name="")


def test_whitespace_name_raises():
    with pytest.raises(InvalidEntityError):
        _pref(name="   ")


def test_category_based_with_product_ids_raises():
    with pytest.raises(InvalidEntityError):
        _pref(
            type=PreferenceType.CATEGORY_BASED,
            product_ids=[ProductId(1)],
        )


def test_allergy_with_product_ids_is_valid():
    pref = _pref(type=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, product_ids=[ProductId(1)])
    assert pref.product_ids == [ProductId(1)]


def test_allergy_with_category_ids_is_valid():
    pref = _pref(type=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, category_ids=[ProductCategoryId(1)])
    assert pref.category_ids == [ProductCategoryId(1)]


def test_allergy_with_both_ids_is_valid():
    pref = _pref(
        type=PreferenceType.ALLERGY,
        mode=PreferenceMode.BLOCKED,
        category_ids=[ProductCategoryId(1)],
        product_ids=[ProductId(2)],
    )
    assert pref.category_ids == [ProductCategoryId(1)]
    assert pref.product_ids == [ProductId(2)]


def test_empty_ids_is_valid():
    pref = _pref(category_ids=[], product_ids=[])
    assert pref.category_ids == []
    assert pref.product_ids == []


def test_category_based_with_recipe_category_ids_is_valid():
    pref = _pref(
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        recipe_category_ids=[RecipeCategoryId(3)],
    )
    assert pref.recipe_category_ids == [RecipeCategoryId(3)]


def test_allergy_with_recipe_category_ids_is_valid():
    pref = _pref(
        type=PreferenceType.ALLERGY,
        mode=PreferenceMode.BLOCKED,
        recipe_category_ids=[RecipeCategoryId(5)],
    )
    assert pref.recipe_category_ids == [RecipeCategoryId(5)]


def test_empty_recipe_category_ids_is_valid():
    pref = _pref(recipe_category_ids=[])
    assert pref.recipe_category_ids == []


def test_recipe_category_ids_default_is_empty():
    pref = _pref()
    assert pref.recipe_category_ids == []
