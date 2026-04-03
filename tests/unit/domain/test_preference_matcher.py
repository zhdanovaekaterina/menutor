from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.domain.entities.preference import Preference
from backend.domain.entities.product import Product
from backend.domain.entities.recipe import Recipe
from backend.domain.services.preference_matcher import PreferenceMatcher
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import (
    PreferenceId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    RecipeId,
    UserId,
)


def _product(pid: int, cat_id: int = 0) -> Product:
    return Product(
        id=ProductId(pid),
        name=f"Product{pid}",
        recipe_unit="g",
        purchase_unit="kg",
        price_per_purchase_unit=Money(Decimal("100")),
        conversion_factor=1000,
        category_id=ProductCategoryId(cat_id),
    )


def _recipe(
    rid: int,
    product_ids: list[int] | None = None,
    sub_recipe_ids: list[int] | None = None,
    category_id: int = 0,
) -> Recipe:
    ingredients = []
    for pid in (product_ids or []):
        ingredients.append(RecipeIngredient(product_id=ProductId(pid), quantity=Quantity(100, "g")))
    for sid in (sub_recipe_ids or []):
        ingredients.append(RecipeIngredient(sub_recipe_id=RecipeId(sid), quantity=Quantity(1, "serv")))
    return Recipe(
        id=RecipeId(rid), name=f"Recipe{rid}", servings=2, ingredients=ingredients,
        category_id=RecipeCategoryId(category_id),
    )


def _pref(
    pref_id: int = 1,
    ptype: PreferenceType = PreferenceType.CATEGORY_BASED,
    mode: PreferenceMode = PreferenceMode.BLOCKED,
    cat_ids: list[int] | None = None,
    prod_ids: list[int] | None = None,
    recipe_cat_ids: list[int] | None = None,
) -> Preference:
    return Preference(
        id=PreferenceId(pref_id),
        name=f"Pref{pref_id}",
        type=ptype,
        mode=mode,
        category_ids=[ProductCategoryId(c) for c in (cat_ids or [])],
        product_ids=[ProductId(p) for p in (prod_ids or [])],
        recipe_category_ids=[RecipeCategoryId(c) for c in (recipe_cat_ids or [])],
    )


def _matcher(products: dict[int, Product] | None = None, sub_recipes: dict[int, Recipe] | None = None) -> PreferenceMatcher:
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: (sub_recipes or {}).get(int(rid))
    product_repo.get_by_id.side_effect = lambda pid: (products or {}).get(int(pid))
    return PreferenceMatcher(recipe_repo=recipe_repo, product_repo=product_repo)


# --- BLOCKED mode ---

def test_blocked_recipe_with_no_ingredients_matches():
    recipe = _recipe(1)
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher()
    assert matcher.matches_preference(recipe, pref) is True


def test_blocked_recipe_without_blocked_categories_matches():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


def test_blocked_recipe_with_blocked_category_does_not_match():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=5)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


# --- ALLERGY mode ---

def test_allergy_blocked_product_does_not_match():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, prod_ids=[10])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allergy_blocked_category_does_not_match():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=5)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allergy_recipe_with_neither_blocked_matches():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, prod_ids=[99], cat_ids=[99])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


# --- ALLOWED mode ---

def test_allowed_no_ingredients_does_not_match():
    recipe = _recipe(1)
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[5])
    matcher = _matcher()
    assert matcher.matches_preference(recipe, pref) is False


def test_allowed_all_in_allowed_categories_matches():
    recipe = _recipe(1, product_ids=[10, 11])
    products = {10: _product(10, cat_id=5), 11: _product(11, cat_id=5)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


def test_allowed_ingredient_not_in_allowed_categories_does_not_match():
    recipe = _recipe(1, product_ids=[10, 11])
    products = {10: _product(10, cat_id=5), 11: _product(11, cat_id=6)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allowed_product_without_category_does_not_match():
    # BR-9: product with category_id=0 not in allowed set
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=0)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


# --- Recursive / sub-recipe ---

def test_recursive_sub_recipe_blocked_category_fails_parent():
    sub = _recipe(2, product_ids=[20])
    products = {20: _product(20, cat_id=5)}
    recipe = _recipe(1, sub_recipe_ids=[2])
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products, sub_recipes={2: sub})
    assert matcher.matches_preference(recipe, pref) is False


def test_recursive_deep_nesting_detected():
    deep = _recipe(3, product_ids=[30])
    mid = _recipe(2, sub_recipe_ids=[3])
    top = _recipe(1, sub_recipe_ids=[2])
    products = {30: _product(30, cat_id=5)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products, sub_recipes={2: mid, 3: deep})
    assert matcher.matches_preference(top, pref) is False


def test_cyclic_sub_recipe_no_infinite_loop():
    # Recipe 1 -> sub_recipe 2, repo returns recipe 1 again for sub 2 (cycle)
    recipe1 = _recipe(1, sub_recipe_ids=[2])
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    # sub_recipe 2 has same id as sub 2 but points back to recipe 1
    recipe2 = _recipe(2, sub_recipe_ids=[1])
    recipe_repo.get_by_id.side_effect = lambda rid: {1: recipe1, 2: recipe2}.get(int(rid))
    product_repo.get_by_id.return_value = None
    matcher = PreferenceMatcher(recipe_repo=recipe_repo, product_repo=product_repo)
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    # Should return True (no products found due to cycle guard)
    result = matcher.matches_preference(recipe1, pref)
    assert result is True


def test_match_all_returns_correct_subset():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=5)}
    pref_match = _pref(1, ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[5])
    pref_no_match = _pref(2, ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[5])
    matcher = _matcher(products=products)
    result = matcher.match_all(recipe, [pref_match, pref_no_match])
    assert result == [pref_match]


def test_empty_blocked_preference_matches_all_recipes():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=5)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


def test_empty_allowed_preference_matches_no_recipes():
    # BR-11: ALLOWED with no categories and recipe has products
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=5)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[])
    matcher = _matcher(products=products)
    # product has category 5, but allowed set is empty, so category 5 is not allowed
    assert matcher.matches_preference(recipe, pref) is False


def test_allergy_product_blocked_but_category_not():
    recipe = _recipe(1, product_ids=[10])
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, prod_ids=[10], cat_ids=[])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


# --- Recipe category: BLOCKED mode ---

def test_blocked_recipe_with_blocked_recipe_category_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, recipe_cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_blocked_recipe_category_ok_product_category_blocked_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=3)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[3], recipe_cat_ids=[9])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_blocked_recipe_category_blocked_product_category_ok_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[9], recipe_cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_blocked_both_category_types_ok_matches():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, cat_ids=[9], recipe_cat_ids=[9])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


# --- Recipe category: ALLERGY mode ---

def test_allergy_blocked_recipe_category_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=7)
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, recipe_cat_ids=[7])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allergy_recipe_category_not_blocked_matches():
    recipe = _recipe(1, product_ids=[10], category_id=7)
    products = {10: _product(10, cat_id=2)}
    pref = _pref(ptype=PreferenceType.ALLERGY, mode=PreferenceMode.BLOCKED, recipe_cat_ids=[99])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


# --- Recipe category: ALLOWED mode ---

def test_allowed_recipe_category_in_allowed_list_matches():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=3)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[3], recipe_cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


def test_allowed_recipe_category_not_in_allowed_list_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=3)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, cat_ids=[3], recipe_cat_ids=[9])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allowed_uncategorized_recipe_does_not_match():
    recipe = _recipe(1, product_ids=[10], category_id=0)
    products = {10: _product(10, cat_id=3)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, recipe_cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is False


def test_allowed_only_recipe_categories_no_product_categories_matches():
    recipe = _recipe(1, product_ids=[10], category_id=5)
    products = {10: _product(10, cat_id=3)}
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, recipe_cat_ids=[5])
    matcher = _matcher(products=products)
    assert matcher.matches_preference(recipe, pref) is True


# --- Recipe category: sub-recipe recursion ---

def test_blocked_sub_recipe_category_fails_parent():
    sub = _recipe(2, product_ids=[20], category_id=8)
    products = {20: _product(20, cat_id=2)}
    recipe = _recipe(1, sub_recipe_ids=[2])
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, recipe_cat_ids=[8])
    matcher = _matcher(products=products, sub_recipes={2: sub})
    assert matcher.matches_preference(recipe, pref) is False


def test_allowed_sub_recipe_category_not_in_allowed_fails():
    sub = _recipe(2, product_ids=[20], category_id=8)
    products = {20: _product(20, cat_id=3)}
    recipe = _recipe(1, sub_recipe_ids=[2], category_id=5)
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.ALLOWED, recipe_cat_ids=[5])
    matcher = _matcher(products=products, sub_recipes={2: sub})
    assert matcher.matches_preference(recipe, pref) is False


def test_cyclic_recipe_categories_no_infinite_loop():
    recipe1 = _recipe(1, sub_recipe_ids=[2], category_id=3)
    recipe2 = _recipe(2, sub_recipe_ids=[1], category_id=4)
    recipe_repo = MagicMock()
    product_repo = MagicMock()
    recipe_repo.get_by_id.side_effect = lambda rid: {1: recipe1, 2: recipe2}.get(int(rid))
    product_repo.get_by_id.return_value = None
    matcher = PreferenceMatcher(recipe_repo=recipe_repo, product_repo=product_repo)
    pref = _pref(ptype=PreferenceType.CATEGORY_BASED, mode=PreferenceMode.BLOCKED, recipe_cat_ids=[99])
    result = matcher.matches_preference(recipe1, pref)
    assert result is True  # categories 3 and 4 are not in blocked set [99]
