from dataclasses import dataclass, field

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId


@dataclass
class Recipe:
    id: RecipeId
    name: str
    servings: int
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    steps: list[CookingStep] = field(default_factory=list)
    category_id: RecipeCategoryId = field(default=RecipeCategoryId(0))
    weight: int = 0
    user_id: UserId = field(default=UserId(0))
    total_pieces: int | None = None
    pieces_per_portion: int | None = None

    def __post_init__(self) -> None:
        has_total = self.total_pieces is not None
        has_per = self.pieces_per_portion is not None
        if has_total != has_per:
            raise InvalidEntityError(
                "total_pieces и pieces_per_portion должны быть заданы вместе или оба None"
            )
        if has_total and has_per:
            assert self.total_pieces is not None
            assert self.pieces_per_portion is not None
            if self.total_pieces < 1:
                raise InvalidEntityError("total_pieces должно быть >= 1")
            if self.pieces_per_portion < 1:
                raise InvalidEntityError("pieces_per_portion должно быть >= 1")
            if self.pieces_per_portion > self.total_pieces:
                raise InvalidEntityError(
                    "pieces_per_portion не может быть больше total_pieces"
                )

    @property
    def is_pieces_mode(self) -> bool:
        return self.total_pieces is not None and self.pieces_per_portion is not None

    @property
    def computed_servings(self) -> int:
        if self.is_pieces_mode:
            assert self.total_pieces is not None
            assert self.pieces_per_portion is not None
            return self.total_pieces // self.pieces_per_portion
        return self.servings

    def scale_to(self, target_servings: float) -> "Recipe":
        factor = target_servings / self.servings
        scaled_ingredients = [
            RecipeIngredient(
                product_id=ing.product_id,
                sub_recipe_id=ing.sub_recipe_id,
                quantity=Quantity(ing.quantity.amount * factor, ing.quantity.unit),
                order=ing.order,
            )
            for ing in self.ingredients
        ]
        new_total_pieces: int | None = None
        if self.is_pieces_mode:
            assert self.total_pieces is not None
            new_total_pieces = max(1, round(self.total_pieces * factor))
        return Recipe(
            id=self.id,
            name=self.name,
            servings=round(target_servings),
            ingredients=scaled_ingredients,
            steps=list(self.steps),
            category_id=self.category_id,
            weight=self.weight,
            user_id=self.user_id,
            total_pieces=new_total_pieces,
            pieces_per_portion=self.pieces_per_portion,
        )
