from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.domain.exceptions import ImportValidationError
from backend.domain.value_objects.types import MenuId, UserId
from backend.infrastructure.export.registry import ExportRegistry


class ExportShoppingList:
    """Export a shopping list for a given menu as a downloadable file."""

    def __init__(
        self,
        export_registry: ExportRegistry,
        generate_shopping_list: GenerateShoppingList,
    ) -> None:
        self._registry = export_registry
        self._generate = generate_shopping_list

    def execute(
        self,
        menu_id: MenuId,
        user_id: UserId,
        format: str,
    ) -> tuple[bytes, str, str]:
        exporter = self._registry.get("shopping_list", format)
        if exporter is None:
            raise ImportValidationError(
                f"Формат '{format}' не поддерживается для списка покупок"
            )
        shopping_list = self._generate.execute(menu_id, user_id)
        data = exporter.export_bytes([shopping_list])
        filename = f"shopping_list.{exporter.file_extension()}"
        return data, exporter.content_type(), filename
