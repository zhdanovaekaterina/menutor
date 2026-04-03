from backend.domain.entities.preference import Preference
from backend.domain.ports.preference_repository import PreferenceRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.preference_matcher import PreferenceMatcher
from backend.domain.value_objects.types import RecipeId, UserId


class MatchRecipePreferences:
    """Returns all user preferences that a given recipe satisfies."""

    def __init__(
        self,
        recipe_repo: RecipeRepository,
        preference_repo: PreferenceRepository,
        matcher: PreferenceMatcher,
    ) -> None:
        self._recipe_repo = recipe_repo
        self._preference_repo = preference_repo
        self._matcher = matcher

    def execute(self, recipe_id: RecipeId, user_id: UserId) -> list[Preference]:
        recipe = self._recipe_repo.get_by_id(recipe_id)
        if recipe is None or recipe.user_id != user_id:
            return []
        all_prefs = self._preference_repo.find_all(user_id)
        return self._matcher.match_all(recipe, all_prefs)
