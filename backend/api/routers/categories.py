"""Маршруты для управления категориями продуктов и рецептов.

Разделены на два суб-роутера:
  /product-categories — категории продуктов
  /recipe-categories  — категории рецептов
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.converters import category_to_response
from backend.api.deps import get_container
from backend.api.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUsedResponse,
)
from backend.composition_root import ApplicationContainer

router = APIRouter(tags=["categories"])


# ── Product Categories ─────────────────────────────────────────────


@router.get("/product-categories", response_model=list[CategoryResponse])
def list_product_categories(
    container: ApplicationContainer = Depends(get_container),
) -> list[CategoryResponse]:
    categories = container.list_all_product_categories.execute()
    return [category_to_response(c) for c in categories]


@router.post(
    "/product-categories",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
def create_product_category(
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, int]:
    category_id = container.create_product_category.execute(body.name)
    return {"id": category_id}


@router.put("/product-categories/{category_id}", response_model=dict[str, int])
def edit_product_category(
    category_id: int,
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, int]:
    result_id = container.edit_product_category.execute(category_id, body.name)
    return {"id": result_id}


@router.delete(
    "/product-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_product_category(
    category_id: int,
    hard: bool = False,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    if hard:
        container.hard_delete_product_category.execute(category_id)
    else:
        container.delete_product_category.execute(category_id)


@router.post(
    "/product-categories/{category_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def activate_product_category(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    container.activate_product_category.execute(category_id)


@router.get(
    "/product-categories/{category_id}/used", response_model=CategoryUsedResponse
)
def check_product_category_used(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> CategoryUsedResponse:
    used = container.check_product_category_used.execute(category_id)
    return CategoryUsedResponse(used=used)


# ── Recipe Categories ──────────────────────────────────────────────


@router.get("/recipe-categories", response_model=list[CategoryResponse])
def list_recipe_categories(
    container: ApplicationContainer = Depends(get_container),
) -> list[CategoryResponse]:
    categories = container.list_all_recipe_categories.execute()
    return [category_to_response(c) for c in categories]


@router.post(
    "/recipe-categories",
    response_model=dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
def create_recipe_category(
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, int]:
    category_id = container.create_recipe_category.execute(body.name)
    return {"id": category_id}


@router.put("/recipe-categories/{category_id}", response_model=dict[str, int])
def edit_recipe_category(
    category_id: int,
    body: CategoryCreate,
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, int]:
    result_id = container.edit_recipe_category.execute(category_id, body.name)
    return {"id": result_id}


@router.delete(
    "/recipe-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_recipe_category(
    category_id: int,
    hard: bool = False,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    if hard:
        container.hard_delete_recipe_category.execute(category_id)
    else:
        container.delete_recipe_category.execute(category_id)


@router.post(
    "/recipe-categories/{category_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def activate_recipe_category(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    container.activate_recipe_category.execute(category_id)


@router.get(
    "/recipe-categories/{category_id}/used", response_model=CategoryUsedResponse
)
def check_recipe_category_used(
    category_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> CategoryUsedResponse:
    used = container.check_recipe_category_used.execute(category_id)
    return CategoryUsedResponse(used=used)
