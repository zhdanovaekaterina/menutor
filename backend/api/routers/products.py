from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.auth import get_current_user
from backend.api.converters import (
    active_category_to_response,
    product_to_response,
    schema_to_product_data,
)
from backend.api.deps import get_container
from backend.api.schemas.category import ActiveCategoryResponse
from backend.api.schemas.pagination import PaginatedResponse
from backend.api.schemas.product import (
    PriceUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import DuplicateNameError
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    page: int | None = Query(None, ge=1),
    search: str = Query(""),
    category_id: int | None = Query(None),
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PaginatedResponse[ProductResponse]:
    result = container.list_products.execute(
        user.id,
        ProductCategoryId(category_id) if category_id is not None else None,
        page=page,
        search=search,
    )
    return PaginatedResponse[ProductResponse](
        items=[product_to_response(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/categories", response_model=list[ActiveCategoryResponse])
def list_product_categories(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[ActiveCategoryResponse]:
    categories = container.list_product_categories.execute()
    return [active_category_to_response(c) for c in categories]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ProductResponse:
    data = schema_to_product_data(body)
    try:
        product = container.create_product.execute(data, user.id)
    except DuplicateNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return product_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    body: ProductUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ProductResponse:
    data = schema_to_product_data(body)
    product = container.edit_product.execute(ProductId(product_id), data, user.id)
    return product_to_response(product)


@router.patch("/{product_id}/price", response_model=ProductResponse)
def update_product_price(
    product_id: int,
    body: PriceUpdate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ProductResponse:
    product = container.update_product_price.execute(
        ProductId(product_id), Money(body.amount, body.currency), user.id
    )
    return product_to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_product.execute(ProductId(product_id), user.id)


@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
def batch_delete_products(
    body: list[int],
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_product.execute(
        [ProductId(pid) for pid in body], user.id
    )
