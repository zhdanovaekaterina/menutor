from fastapi import APIRouter, Depends
from fastapi.responses import Response

from backend.api.auth import get_current_user
from backend.api.converters import shopping_list_to_response
from backend.api.deps import get_container
from backend.api.schemas.shopping_list import ShoppingListResponse
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
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
    shopping_list = container.generate_shopping_list.execute(
        MenuId(menu_id), user.id
    )
    return shopping_list_to_response(shopping_list)


@router.post("/menus/{menu_id}/shopping-list/export/text")
def export_shopping_list_text(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    data, content_type, filename = container.export_shopping_list.execute(
        MenuId(menu_id), user.id, "txt"
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/menus/{menu_id}/shopping-list/export/csv")
def export_shopping_list_csv(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    data, content_type, filename = container.export_shopping_list.execute(
        MenuId(menu_id), user.id, "csv"
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
