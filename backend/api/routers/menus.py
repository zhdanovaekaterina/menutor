from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.converters import menu_to_response
from backend.api.deps import get_container
from backend.api.schemas.menu import (
    MenuCreate,
    MenuResponse,
    MenuSlotSchema,
    RemoveItemRequest,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.menu import MenuSlot
from backend.domain.exceptions import EntityNotFoundError
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId

router = APIRouter(prefix="/menus", tags=["menus"])


def _schema_to_slot(s: MenuSlotSchema) -> MenuSlot:
    return MenuSlot(
        day=s.day,
        meal_type=s.meal_type,
        recipe_id=RecipeId(s.recipe_id) if s.recipe_id is not None else None,
        product_id=ProductId(s.product_id) if s.product_id is not None else None,
        quantity=s.quantity,
        unit=s.unit,
        servings_override=s.servings_override,
    )


@router.get("", response_model=list[MenuResponse])
def list_menus(
    container: ApplicationContainer = Depends(get_container),
) -> list[MenuResponse]:
    menus = container.list_menus.execute()
    return [menu_to_response(m) for m in menus]


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_menu(
    body: MenuCreate,
    container: ApplicationContainer = Depends(get_container),
) -> MenuResponse:
    menu = container.create_menu.execute(body.name)
    return menu_to_response(menu)


@router.get("/{menu_id}", response_model=MenuResponse)
def get_menu(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> MenuResponse:
    menu = container.load_menu.execute(MenuId(menu_id))
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
) -> None:
    container.delete_menu.execute(MenuId(menu_id))


@router.post("/{menu_id}/slots", response_model=MenuResponse)
def add_slot(
    menu_id: int,
    body: MenuSlotSchema,
    container: ApplicationContainer = Depends(get_container),
) -> MenuResponse:
    slot = _schema_to_slot(body)
    try:
        menu = container.add_dish_to_slot.execute(MenuId(menu_id), slot)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return menu_to_response(menu)


@router.delete("/{menu_id}/slots", response_model=MenuResponse)
def remove_slot(
    menu_id: int,
    body: RemoveItemRequest,
    container: ApplicationContainer = Depends(get_container),
) -> MenuResponse:
    try:
        menu = container.remove_item_from_slot.execute(
            menu_id=MenuId(menu_id),
            day=body.day,
            meal_type=body.meal_type,
            recipe_id=RecipeId(body.recipe_id) if body.recipe_id is not None else None,
            product_id=(
                ProductId(body.product_id) if body.product_id is not None else None
            ),
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return menu_to_response(menu)


@router.post("/{menu_id}/clear", response_model=MenuResponse)
def clear_menu(
    menu_id: int,
    container: ApplicationContainer = Depends(get_container),
) -> MenuResponse:
    try:
        menu = container.clear_menu.execute(MenuId(menu_id))
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return menu_to_response(menu)
