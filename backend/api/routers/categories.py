"""Маршруты для управления категориями продуктов и рецептов.

Разделены на два суб-роутера:
  /product-categories — категории продуктов
  /recipe-categories  — категории рецептов
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.converters import category_to_response
from backend.api.deps import get_container
from backend.api.schemas.category import (
    CategoryCreate,
    CategoryMoveDeleteRequest,
    CategoryResponse,
    CategoryUsedResponse,
)
from backend.application.use_cases.manage_category import CategoryBundle
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import AppError

router = APIRouter(tags=["categories"])


def _bundle(container: ApplicationContainer, type: str) -> CategoryBundle:
    return container.product_categories if type == "product" else container.recipe_categories


# ── Product Categories ─────────────────────────────────────────────


@router.get("/product-categories", response_model=list[CategoryResponse])
def list_product_categories(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    return [category_to_response(c) for c in _bundle(container, "product").list_all.execute()]


@router.post(
    "/product-categories",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
def create_product_category(
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    return {"id": _bundle(container, "product").create.execute(body.name)}


@router.put("/product-categories/{category_id}", response_model=dict[str, int])
def edit_product_category(
    category_id: int,
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    return {"id": _bundle(container, "product").edit.execute(category_id, body.name)}


@router.delete(
    "/product-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_product_category(
    category_id: int,
    hard: bool = False,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    b = _bundle(container, "product")
    (b.hard_delete if hard else b.delete).execute(category_id)


@router.post(
    "/product-categories/{category_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def activate_product_category(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    _bundle(container, "product").activate.execute(category_id)


@router.get(
    "/product-categories/{category_id}/used", response_model=CategoryUsedResponse
)
def check_product_category_used(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> CategoryUsedResponse:
    return CategoryUsedResponse(used=_bundle(container, "product").check_used.execute(category_id))


@router.post(
    "/product-categories/{category_id}/move-and-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def move_and_delete_product_category(
    category_id: int,
    body: CategoryMoveDeleteRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    try:
        _bundle(container, "product").move_and_delete.execute(category_id, body.target_category_id)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


# ── Recipe Categories ──────────────────────────────────────────────


@router.get("/recipe-categories", response_model=list[CategoryResponse])
def list_recipe_categories(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    return [category_to_response(c) for c in _bundle(container, "recipe").list_all.execute()]


@router.post(
    "/recipe-categories",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
def create_recipe_category(
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    return {"id": _bundle(container, "recipe").create.execute(body.name)}


@router.put("/recipe-categories/{category_id}", response_model=dict[str, int])
def edit_recipe_category(
    category_id: int,
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    return {"id": _bundle(container, "recipe").edit.execute(category_id, body.name)}


@router.delete(
    "/recipe-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_recipe_category(
    category_id: int,
    hard: bool = False,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    b = _bundle(container, "recipe")
    (b.hard_delete if hard else b.delete).execute(category_id)


@router.post(
    "/recipe-categories/{category_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def activate_recipe_category(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    _bundle(container, "recipe").activate.execute(category_id)


@router.get(
    "/recipe-categories/{category_id}/used", response_model=CategoryUsedResponse
)
def check_recipe_category_used(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> CategoryUsedResponse:
    return CategoryUsedResponse(used=_bundle(container, "recipe").check_used.execute(category_id))


@router.post(
    "/recipe-categories/{category_id}/move-and-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def move_and_delete_recipe_category(
    category_id: int,
    body: CategoryMoveDeleteRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    try:
        _bundle(container, "recipe").move_and_delete.execute(category_id, body.target_category_id)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
