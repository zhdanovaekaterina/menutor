from dataclasses import dataclass

from backend.domain.exceptions import CircularDependencyError, NestingDepthExceededError
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.services.recipe_dependency_validator import RecipeDependencyValidator
from backend.domain.value_objects.types import RecipeId, UserId


@dataclass
class ValidationResult:
    valid: bool
    error: str | None = None


class ValidateSubRecipe:
    def __init__(
        self, repo: RecipeRepository, validator: RecipeDependencyValidator
    ) -> None:
        self._repo = repo
        self._validator = validator

    def execute(
        self,
        parent_recipe_id: RecipeId | None,
        sub_recipe_id: RecipeId,
        user_id: UserId,
    ) -> ValidationResult:
        sub = self._repo.get_by_id(sub_recipe_id)
        if sub is None or sub.user_id != user_id:
            return ValidationResult(valid=False, error="Рецепт не найден")
        if parent_recipe_id is not None:
            try:
                self._validator.validate(parent_recipe_id, [sub_recipe_id])
            except CircularDependencyError as e:
                return ValidationResult(valid=False, error=str(e))
            except NestingDepthExceededError as e:
                return ValidationResult(valid=False, error=str(e))
        return ValidationResult(valid=True)
