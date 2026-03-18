"""Wire shopping list use cases."""

from typing import Any

from backend.application.use_cases.export_shopping_list import ExportShoppingList
from backend.application.use_cases.generate_shopping_list import GenerateShoppingList
from backend.application.use_cases.import_export import (
    ExportShoppingListAsCsv,
    ExportShoppingListAsText,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_shopping(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "generate_shopping_list": GenerateShoppingList(
            menu_repo=infra.menu_repo,
            builder=infra.builder,
        ),
        "export_shopping_list_as_text": ExportShoppingListAsText(infra.text_exporter),
        "export_shopping_list_as_csv": ExportShoppingListAsCsv(infra.csv_exporter),
    }
