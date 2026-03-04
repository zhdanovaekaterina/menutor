from src.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from src.domain.entities.shopping_list import ShoppingList
from src.presentation.views.shopping_list_view import ShoppingListView


class ShoppingListController:
    """Соединяет ShoppingListView с use cases экспорта."""

    def __init__(
        self,
        view: ShoppingListView,
        export_text_uc: ExportShoppingListAsText,
        export_csv_uc: ExportShoppingListAsCsv,
    ) -> None:
        self._view = view
        self._export_text_uc = export_text_uc
        self._export_csv_uc = export_csv_uc
        self._shopping_list: ShoppingList | None = None

        view.export_text_requested.connect(self._on_export_text)
        view.export_csv_requested.connect(self._on_export_csv)

    def set_shopping_list(self, shopping_list: ShoppingList) -> None:
        self._shopping_list = shopping_list
        self._view.set_shopping_list(shopping_list)

    def _on_export_text(self) -> None:
        if self._shopping_list is None:
            return
        try:
            text = self._export_text_uc.execute(self._shopping_list)
            self._view.show_text_export(text)
        except Exception as exc:
            self._view.show_error(str(exc))

    def _on_export_csv(self, filepath: str) -> None:
        if self._shopping_list is None:
            return
        try:
            self._export_csv_uc.execute(self._shopping_list, filepath)
        except Exception as exc:
            self._view.show_error(str(exc))
