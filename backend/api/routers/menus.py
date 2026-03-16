from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.converters import menu_to_response, schema_to_menu_slot
from backend.api.deps import get_container
from backend.api.schemas.menu import (
    MenuCreate,
    MenuResponse,
    MenuSlotSchema,
    MoveSlotRequest,
    RemoveItemRequest,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("", response_model=list[MenuResponse])
def list_menus(
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> list[MenuResponse]:
    menus = container.list_menus.execute(user.id)
    return [menu_to_response(m) for m in menus]


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    body: MenuCreate,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    menu = container.create_menu.execute(body.name, user.id)
    return menu_to_response(menu)


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    menu = container.load_menu.execute(MenuId(menu_id), user.id)
    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Меню {menu_id} не найдено",
        )
    return menu_to_response(menu)


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> None:
    container.delete_menu.execute(MenuId(menu_id), user.id)


@router.post("/{menu_id}/slots", response_model=MenuResponse)
def add_slot(
    menu_id: int,
    body: MenuSlotSchema,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    slot = schema_to_menu_slot(body)
    menu = container.add_dish_to_slot.execute(MenuId(menu_id), slot, user.id)
    return menu_to_response(menu)


@router.post("/{menu_id}/slots/move", response_model=MenuResponse)
def move_slot(
    menu_id: int,
    body: MoveSlotRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    menu = container.move_slot_in_menu.execute(
        menu_id=MenuId(menu_id),
        day=body.day,
        meal_type=body.meal_type,
        user_id=user.id,
        to_day=body.to_day,
        to_meal_type=body.to_meal_type,
        to_position=body.to_position,
        recipe_id=RecipeId(body.recipe_id) if body.recipe_id is not None else None,
        product_id=(
            ProductId(body.product_id) if body.product_id is not None else None
        ),
    )
    return menu_to_response(menu)


@router.delete("/{menu_id}/slots", response_model=MenuResponse)
def remove_slot(
    menu_id: int,
    body: RemoveItemRequest,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    menu = container.remove_item_from_slot.execute(
        menu_id=MenuId(menu_id),
        day=body.day,
        meal_type=body.meal_type,
        user_id=user.id,
        recipe_id=RecipeId(body.recipe_id) if body.recipe_id is not None else None,
        product_id=(
            ProductId(body.product_id) if body.product_id is not None else None
        ),
    )
    return menu_to_response(menu)


@router.post("/{menu_id}/clear", response_model=MenuResponse)
def clear_menu(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
    user: User = Depends(get_current_user),
) -> MenuResponse:
    menu = container.clear_menu.execute(MenuId(menu_id), user.id)
    return menu_to_response(menu)
