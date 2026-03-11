from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.converters import active_category_to_response, recipe_to_response
from backend.api.deps import get_container
from backend.api.schemas.category import ActiveCategoryResponse
from backend.api.schemas.recipe import RecipeCreate, RecipeResponse, RecipeUpdate
from backend.application.use_cases.manage_recipe import RecipeData
from backend.composition_root import ApplicationContainer
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.cooking_step import CookingStep
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.recipe_ingredient import RecipeIngredient
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _to_recipe_data(body: RecipeCreate | RecipeUpdate) -> RecipeData:
    return RecipeData(
        name=body.name,
        category_id=RecipeCategoryId(body.category_id),
        servings=body.servings,
        ingredients=[
            RecipeIngredient(
                product_id=ing.product_id,
                quantity=Quantity(ing.quantity_amount, ing.quantity_unit),
            )
            for ing in body.ingredients
        ],
        steps=[
            CookingStep(order=s.order, description=s.description)
            for s in body.steps
        ],
        weight=body.weight,
    )


@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    container: ApplicationContainer = Depends(get_container),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute()
    return [recipe_to_response(r) for r in recipes]


@router.get("/categories", response_model=list[ActiveCategoryResponse])
def list_recipe_categories(
    container: ApplicationContainer = Depends(get_container),
) -> list[ActiveCategoryResponse]:
    categories = container.list_recipe_categories.execute()
    return [active_category_to_response(c) for c in categories]


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    recipe = container.get_recipe.execute(RecipeId(recipe_id))
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецепт {recipe_id} не найден",
        )
    return recipe_to_response(recipe)


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    body: RecipeCreate,
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    data = _to_recipe_data(body)
    recipe = container.create_recipe.execute(data)
    return recipe_to_response(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    container: ApplicationContainer = Depends(get_container),
) -> RecipeResponse:
    data = _to_recipe_data(body)
    try:
        recipe = container.edit_recipe.execute(RecipeId(recipe_id), data)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return recipe_to_response(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    container.delete_recipe.execute(RecipeId(recipe_id))
