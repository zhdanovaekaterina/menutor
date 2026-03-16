from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.converters import (
    active_category_to_response,
    recipe_to_response,
    schema_to_recipe_data,
)
from backend.api.deps import get_container
from backend.api.schemas.category import ActiveCategoryResponse
from backend.api.schemas.recipe import RecipeCreate, RecipeResponse, RecipeUpdate
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import RecipeId

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(user.id)
    return [recipe_to_response(r) for r in recipes]


@router.get("/categories", response_model=list[ActiveCategoryResponse])
def list_recipe_categories(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[ActiveCategoryResponse]:
    categories = container.list_recipe_categories.execute()
    return [active_category_to_response(c) for c in categories]


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> RecipeResponse:
    recipe = container.get_recipe.execute(RecipeId(recipe_id), user.id)
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
    user: User = Depends(get_current_user),
) -> RecipeResponse:
    data = schema_to_recipe_data(body)
    recipe = container.create_recipe.execute(data, user.id)
    return recipe_to_response(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> RecipeResponse:
    data = schema_to_recipe_data(body)
    recipe = container.edit_recipe.execute(RecipeId(recipe_id), data, user.id)
    return recipe_to_response(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_recipe.execute(RecipeId(recipe_id), user.id)


@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def batch_delete_recipes(
    body: list[int],
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_recipe.execute(
        [RecipeId(rid) for rid in body], user.id
    )
