import json

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.exceptions import ImportValidationError, InvalidEntityError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId


class MenuJsonImporter:
    def __init__(self, repo: MenuRepository) -> None:
        self._repo = repo

    def import_from_bytes(self, data: bytes, user_id: UserId) -> ImportResult:
        if not data.strip():
            return ImportResult(created=0, updated=0)

        try:
            rows = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ImportValidationError(f"Некорректный JSON: {e}") from e

        if not isinstance(rows, list):
            raise ImportValidationError("JSON должен быть массивом объектов")

        created = updated = 0
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise ImportValidationError(f"Элемент {i}: ожидается объект")
            if not str(row.get("name", "")).strip():
                raise ImportValidationError(f"Элемент {i}: поле 'name' не может быть пустым")

            try:
                slots = [
                    MenuSlot(
                        day=int(s["day"]),
                        meal_type=str(s["meal_type"]),
                        recipe_id=RecipeId(int(s["recipe_id"])) if s.get("recipe_id") is not None else None,
                        product_id=ProductId(int(s["product_id"])) if s.get("product_id") is not None else None,
                        quantity=float(s["quantity"]) if s.get("quantity") is not None else None,
                        unit=str(s["unit"]) if s.get("unit") is not None else None,
                        servings_override=float(s["servings_override"]) if s.get("servings_override") is not None else None,
                        position=int(s.get("position") or 0),
                    )
                    for s in (row.get("slots") or [])
                ]
            except InvalidEntityError as e:
                raise ImportValidationError(f"Элемент {i}: некорректный слот: {e}") from e
            except Exception as e:
                raise ImportValidationError(f"Элемент {i}: ошибка разбора слотов: {e}") from e

            raw_id = int(row.get("id") or 0)
            existing = self._repo.get_by_id(MenuId(raw_id)) if raw_id > 0 else None
            if existing is not None and existing.user_id == user_id:
                entity_id = existing.id
                updated += 1
            else:
                entity_id = MenuId(0)
                created += 1

            menu = WeeklyMenu(
                id=entity_id,
                name=str(row["name"]).strip(),
                slots=slots,
                user_id=user_id,
            )
            self._repo.save(menu)

        return ImportResult(created=created, updated=updated)

    def supported_extensions(self) -> list[str]:
        return ["json"]
