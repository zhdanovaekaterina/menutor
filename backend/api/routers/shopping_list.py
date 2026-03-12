from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from backend.api.auth import get_current_user
from backend.api.converters import shopping_list_to_response
from backend.api.deps import get_container
from backend.api.schemas.shopping_list import ShoppingListResponse
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import MenuId

router = APIRouter(tags=["shopping-list"])


@router.post(
    "/menus/{menu_id}/shopping-list", response_model=ShoppingListResponse
)
def generate_shopping_list(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> ShoppingListResponse:
    try:
        shopping_list = container.generate_shopping_list.execute(
            MenuId(menu_id), user.id
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return shopping_list_to_response(shopping_list)


@router.post("/menus/{menu_id}/shopping-list/export/text")
def export_shopping_list_text(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> PlainTextResponse:
    try:
        shopping_list = container.generate_shopping_list.execute(
            MenuId(menu_id), user.id
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    text = container.export_shopping_list_as_text.execute(shopping_list)
    return PlainTextResponse(content=text)
