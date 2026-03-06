from dataclasses import dataclass, field

from src.domain.value_objects.cooking_step import CookingStep
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.types import RecipeCategoryId, RecipeId


@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    category_id: RecipeCategoryId = field(default=RecipeCategoryId(0))
    weight: int = 0

    def scale_to(self, target_servings: float) -> "Recipe":
        factor = target_servings / self.servings
        scaled_ingredients = [
            RecipeIngredient(
                product_id=ing.product_id,
                quantity=Quantity(ing.quantity.amount * factor, ing.quantity.unit),
            )
            for ing in self.ingredients
        ]
        return Recipe(
            id=self.id,
            name=self.name,
            servings=round(target_servings),
            ingredients=scaled_ingredients,
            steps=list(self.steps),
            category_id=self.category_id,
            weight=self.weight,
        )
