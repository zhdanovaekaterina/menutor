from fastapi import APIRouter, Depends, Response, status

from backend.api.auth import get_current_user
from backend.api.converters import (
    saved_shopping_list_to_meta,
    saved_shopping_list_to_response,
    schema_to_saved_shopping_list_item_data,
)
from backend.api.deps import get_container
from backend.api.schemas.meal_summary import GenerateFilteredShoppingListRequest
from backend.api.schemas.shopping_list import (
    RenameSavedShoppingListRequest,
    SavedShoppingListMetaResponse,
    SavedShoppingListResponse,
    UpdateSavedShoppingListRequest,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import (
    MenuId,
    SavedShoppingListId,
    SavedShoppingListItemId,
)

router = APIRouter(tags=["shopping-list"])


# ── Generate and auto-save from menu ──────────────────────────────


@router.post(
    "/menus/{menu_id}/shopping-list",
    response_model=SavedShoppingListResponse,
)
def generate_shopping_list(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.generate_and_save_shopping_list.execute(MenuId(menu_id), user.id)
    return saved_shopping_list_to_response(saved)


@router.post(
    "/menus/{menu_id}/shopping-list/filtered",
    response_model=SavedShoppingListResponse,
)
def generate_filtered_shopping_list(
    menu_id: int,
    body: GenerateFilteredShoppingListRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.generate_filtered_shopping_list.execute(
        MenuId(menu_id), user.id, set(body.slot_indices)
    )
    return saved_shopping_list_to_response(saved)


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


@router.post("/menus/{menu_id}/shopping-list/export/json")
def export_shopping_list_json(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    data, content_type, filename = container.export_shopping_list.execute(
        MenuId(menu_id), user.id, "json"
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/menus/{menu_id}/shopping-list/export/pdf")
def export_shopping_list_pdf(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> Response:
    data, content_type, filename = container.export_shopping_list.execute(
        MenuId(menu_id), user.id, "pdf"
    )
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Saved Shopping Lists CRUD ──────────────────────────────────────


@router.get("/shopping-lists", response_model=list[SavedShoppingListMetaResponse])
def list_saved_shopping_lists(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[SavedShoppingListMetaResponse]:
    lists = container.list_saved_shopping_lists.execute(user.id)
    return [saved_shopping_list_to_meta(sl) for sl in lists]


@router.post(
    "/shopping-lists",
    response_model=SavedShoppingListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_shopping_list(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.create_saved_shopping_list.execute(user.id)
    return saved_shopping_list_to_response(saved)


@router.get("/shopping-lists/{list_id}", response_model=SavedShoppingListResponse)
def get_saved_shopping_list(
    list_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.get_saved_shopping_list.execute(
        SavedShoppingListId(list_id), user.id
    )
    return saved_shopping_list_to_response(saved)


@router.put("/shopping-lists/{list_id}", response_model=SavedShoppingListResponse)
def update_saved_shopping_list(
    list_id: int,
    body: UpdateSavedShoppingListRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    items_data = [schema_to_saved_shopping_list_item_data(item) for item in body.items]
    saved = container.update_saved_shopping_list.execute(
        SavedShoppingListId(list_id), body.name, items_data, user.id
    )
    return saved_shopping_list_to_response(saved)


@router.patch("/shopping-lists/{list_id}", response_model=SavedShoppingListResponse)
def rename_saved_shopping_list(
    list_id: int,
    body: RenameSavedShoppingListRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.rename_saved_shopping_list.execute(
        SavedShoppingListId(list_id), body.name, user.id
    )
    return saved_shopping_list_to_response(saved)


@router.delete("/shopping-lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_shopping_list(
    list_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_saved_shopping_list.execute(
        SavedShoppingListId(list_id), user.id
    )


@router.post(
    "/shopping-lists/{list_id}/copy",
    response_model=SavedShoppingListResponse,
    status_code=status.HTTP_201_CREATED,
)
def copy_saved_shopping_list(
    list_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.copy_saved_shopping_list.execute(
        SavedShoppingListId(list_id), user.id
    )
    return saved_shopping_list_to_response(saved)


@router.post(
    "/shopping-lists/{list_id}/items/{item_id}/toggle-purchased",
    response_model=SavedShoppingListResponse,
)
def toggle_item_purchased(
    list_id: int,
    item_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> SavedShoppingListResponse:
    saved = container.toggle_item_purchased.execute(
        SavedShoppingListId(list_id),
        SavedShoppingListItemId(item_id),
        user.id,
    )
    return saved_shopping_list_to_response(saved)
