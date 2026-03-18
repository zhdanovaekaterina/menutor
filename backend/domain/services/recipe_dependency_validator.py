from backend.domain.entities.recipe import Recipe
from backend.domain.exceptions import CircularDependencyError, NestingDepthExceededError
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.types import RecipeId

MAX_NESTING_DEPTH = 5


class RecipeDependencyValidator:
    """Validates sub-recipe references for cycles and depth limits."""

    def __init__(self, recipe_repo: RecipeRepository) -> None:
        self._repo = recipe_repo

    def validate(
        self,
        recipe_id: RecipeId,
        sub_recipe_ids: list[RecipeId],
    ) -> None:
        for sub_id in sub_recipe_ids:
            visited: set[RecipeId] = {recipe_id}
            self._dfs(sub_id, visited, depth=1)

    def _dfs(
        self,
        current_id: RecipeId,
        visited: set[RecipeId],
        depth: int,
    ) -> None:
        if current_id in visited:
            raise CircularDependencyError(
                f"Циклическая зависимость: рецепт {current_id} уже "
                f"присутствует в цепочке зависимостей"
            )
        if depth > MAX_NESTING_DEPTH:
            raise NestingDepthExceededError(
                f"Превышена максимальная глубина вложенности ({MAX_NESTING_DEPTH})"
            )
        recipe = self._repo.get_by_id(current_id)
        if recipe is None:
            return
        visited.add(current_id)
        for ing in recipe.ingredients:
            if ing.is_sub_recipe:
                assert ing.sub_recipe_id is not None
                self._dfs(ing.sub_recipe_id, visited, depth + 1)
        visited.discard(current_id)  # backtrack

    def compute_depth(self, recipe_id: RecipeId) -> int:
        recipe = self._repo.get_by_id(recipe_id)
        if recipe is None:
            return 0
        return self._compute_depth_recursive(recipe, set(), 0)

    def _compute_depth_recursive(
        self, recipe: Recipe, visited: set[RecipeId], current_depth: int
    ) -> int:
        max_depth = current_depth
        for ing in recipe.ingredients:
            if ing.is_sub_recipe and ing.sub_recipe_id not in visited:
                assert ing.sub_recipe_id is not None
                sub = self._repo.get_by_id(ing.sub_recipe_id)
                if sub is not None:
                    visited.add(ing.sub_recipe_id)
                    d = self._compute_depth_recursive(sub, visited, current_depth + 1)
                    max_depth = max(max_depth, d)
                    visited.discard(ing.sub_recipe_id)
        return max_depth
