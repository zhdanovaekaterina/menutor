from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from backend.api.auth import get_current_user
from backend.api.converters import (
    active_category_to_response,
    recipe_to_response,
    schema_to_recipe_data,
)
from backend.api.deps import get_container
from backend.api.schemas.category import ActiveCategoryResponse
from backend.api.schemas.recipe import (
    FlattenedProductResponse,
    RecipeCreate,
    RecipeResponse,
    RecipeUpdate,
    ValidateSubRecipeRequest,
    ValidateSubRecipeResponse,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import RecipeCategoryId, RecipeId, UserId

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _make_name_lookup(container: ApplicationContainer, user_id: UserId):  # type: ignore[return]
    def lookup(rid: RecipeId) -> str | None:
        r = container.get_recipe.execute(rid, user_id)
        return r.name if r is not None else None
    return lookup


@router.get("", response_model=list[RecipeResponse])
def list_recipes(
    category_id: int | None = Query(None),
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[RecipeResponse]:
    recipes = container.list_recipes.execute(
        user.id, RecipeCategoryId(category_id) if category_id is not None else None
    )
    lookup = _make_name_lookup(container, user.id)
    return [recipe_to_response(r, lookup) for r in recipes]


@router.get("/categories", response_model=list[ActiveCategoryResponse])
def list_recipe_categories(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[ActiveCategoryResponse]:
    categories = container.list_recipe_categories.execute()
    return [active_category_to_response(c) for c in categories]


# MUST be registered before /{recipe_id} routes
@router.post("/validate-sub-recipe", response_model=ValidateSubRecipeResponse)
def validate_sub_recipe(
    body: ValidateSubRecipeRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ValidateSubRecipeResponse:
    result = container.validate_sub_recipe.execute(
        RecipeId(body.parent_recipe_id) if body.parent_recipe_id else None,
        RecipeId(body.sub_recipe_id),
        user.id,
    )
    return ValidateSubRecipeResponse(valid=result.valid, error=result.error)


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
    return recipe_to_response(recipe, _make_name_lookup(container, user.id))


@router.get("/{recipe_id}/flattened-products", response_model=list[FlattenedProductResponse])
def get_flattened_products(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[FlattenedProductResponse]:
    items = container.flatten_recipe_products.execute(RecipeId(recipe_id), user.id)
    return [
        FlattenedProductResponse(
            product_id=int(item.product_id),
            product_name=item.product_name,
            quantity_amount=item.quantity.amount,
            quantity_unit=item.quantity.unit,
        )
        for item in items
    ]


@router.get("/{recipe_id}/dependents")
def get_recipe_dependents(
    recipe_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[dict]:
    parents = container.delete_recipe.check_dependents(RecipeId(recipe_id), user.id)
    return [{"id": int(r.id), "name": r.name} for r in parents]


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    body: RecipeCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> RecipeResponse:
    data = schema_to_recipe_data(body)
    recipe = container.create_recipe.execute(data, user.id)
    return recipe_to_response(recipe, _make_name_lookup(container, user.id))


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    body: RecipeUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> RecipeResponse:
    data = schema_to_recipe_data(body)
    recipe = container.edit_recipe.execute(RecipeId(recipe_id), data, user.id)
    return recipe_to_response(recipe, _make_name_lookup(container, user.id))


@router.delete("/{recipe_id}", response_model=None)
def delete_recipe(
    recipe_id: int,
    check_dependents: bool = Query(False),
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response | JSONResponse:
    if check_dependents:
        parents = container.delete_recipe.check_dependents(RecipeId(recipe_id), user.id)
        if parents:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "detail": "Рецепт используется в других рецептах",
                    "dependents": [{"id": int(r.id), "name": r.name} for r in parents],
                },
            )
    container.delete_recipe.execute(RecipeId(recipe_id), user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def batch_delete_recipes(
    body: list[int],
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_recipe.execute(
        [RecipeId(rid) for rid in body], user.id
    )
