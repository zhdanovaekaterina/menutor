from unittest.mock import MagicMock

from backend.application.use_cases.match_recipe_preferences import MatchRecipePreferences
from backend.domain.entities.preference import Preference
from backend.domain.entities.recipe import Recipe
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import PreferenceId, RecipeId, UserId

UID = UserId(1)


def _recipe(rid: int = 1) -> Recipe:
    return Recipe(id=RecipeId(rid), name=f"Recipe{rid}", servings=2, user_id=UID)


def _pref(pid: int = 1) -> Preference:
    return Preference(
        id=PreferenceId(pid),
        name=f"Pref{pid}",
        type=PreferenceType.CATEGORY_BASED,
        mode=PreferenceMode.BLOCKED,
        user_id=UID,
    )


def _use_case(
    recipe: Recipe | None,
    prefs: list[Preference],
    matched: list[Preference],
) -> MatchRecipePreferences:
    recipe_repo = MagicMock()
    pref_repo = MagicMock()
    matcher = MagicMock()
    recipe_repo.get_by_id.return_value = recipe
    pref_repo.find_all.return_value = prefs
    matcher.match_all.return_value = matched
    return MatchRecipePreferences(
        recipe_repo=recipe_repo,
        preference_repo=pref_repo,
        matcher=matcher,
    )


def test_returns_matching_preferences_for_recipe() -> None:
    pref = _pref(1)
    uc = _use_case(_recipe(), [pref], [pref])
    result = uc.execute(RecipeId(1), UID)
    assert result == [pref]


def test_nonexistent_recipe_returns_empty_list() -> None:
    uc = _use_case(None, [], [])
    result = uc.execute(RecipeId(999), UID)
    assert result == []


def test_non_owned_recipe_returns_empty_list() -> None:
    recipe = Recipe(id=RecipeId(1), name="Other", servings=2, user_id=UserId(99))
    uc = _use_case(recipe, [_pref()], [_pref()])
    result = uc.execute(RecipeId(1), UID)
    assert result == []


def test_no_preferences_returns_empty_list() -> None:
    uc = _use_case(_recipe(), [], [])
    result = uc.execute(RecipeId(1), UID)
    assert result == []
