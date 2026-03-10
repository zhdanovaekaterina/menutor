from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId
from backend.infrastructure.database.models import MenuRow, MenuSlotRow
from backend.infrastructure.repositories.base import BaseOrmRepository


class SqliteMenuRepository(
    BaseOrmRepository[WeeklyMenu, MenuId],
    MenuRepository,
):
    _row_class = MenuRow

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_entity_id(self, entity: WeeklyMenu) -> int:
        return entity.id

    def _wrap_id(self, raw_id: int) -> MenuId:
        return MenuId(raw_id)

    def _make_new_row(self, entity: WeeklyMenu) -> MenuRow:
        row = MenuRow(name=entity.name)
        row.slots = [self._slot_to_row(s) for s in entity.slots]
        return row

    def _update_row(self, row: Any, entity: WeeklyMenu) -> None:
        row.name = entity.name
        row.slots = [self._slot_to_row(s) for s in entity.slots]

    def _row_to_entity(self, row: Any) -> WeeklyMenu:
        return WeeklyMenu(
            id=MenuId(row.id),
            name=row.name,
            slots=[
                MenuSlot(
                    day=s.day,
                    meal_type=s.meal_type,
                    recipe_id=RecipeId(s.recipe_id) if s.recipe_id is not None else None,
                    product_id=ProductId(s.product_id) if s.product_id is not None else None,
                    quantity=s.quantity,
                    unit=s.unit,
                    servings_override=s.servings_override,
                )
                for s in row.slots
            ],
        )

    @staticmethod
    def _slot_to_row(slot: MenuSlot) -> MenuSlotRow:
        return MenuSlotRow(
            day=slot.day,
            meal_type=slot.meal_type,
            recipe_id=slot.recipe_id,
            product_id=slot.product_id,
            quantity=slot.quantity,
            unit=slot.unit,
            servings_override=slot.servings_override,
        )
