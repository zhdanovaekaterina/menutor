"""Wire import/export use cases."""

from typing import Any

from backend.application.use_cases.export_entities import ExportEntities
from backend.application.use_cases.export_shopping_list import ExportShoppingList
from backend.application.use_cases.import_entities import ImportEntities
from backend.composition._infrastructure import _Infrastructure
from backend.infrastructure.export.menu_json_exporter import MenuJsonExporter
from backend.infrastructure.export.product_csv_exporter import ProductCsvExporter
from backend.infrastructure.export.product_json_exporter import ProductJsonExporter
from backend.infrastructure.export.recipe_csv_exporter import RecipeCsvExporter
from backend.infrastructure.export.recipe_json_exporter import RecipeJsonExporter
from backend.infrastructure.export.registry import ExportRegistry, ImportRegistry
from backend.infrastructure.import_.menu_json_importer import MenuJsonImporter
from backend.infrastructure.import_.product_csv_importer import ProductCsvImporter
from backend.infrastructure.import_.product_json_importer import ProductJsonImporter
from backend.infrastructure.import_.recipe_csv_importer import RecipeCsvImporter
from backend.infrastructure.import_.recipe_json_importer import RecipeJsonImporter


def _wire_import_export(
    infra: _Infrastructure,
    generate_shopping_list: Any,
) -> dict[str, Any]:
    export_registry = ExportRegistry()
    export_registry.register("products", "csv", ProductCsvExporter())
    export_registry.register("products", "json", ProductJsonExporter())
    export_registry.register("recipes", "csv", RecipeCsvExporter())
    export_registry.register("recipes", "json", RecipeJsonExporter())
    export_registry.register(
        "recipes", "json_compact", RecipeJsonExporter(compact=True)
    )
    export_registry.register("menus", "json", MenuJsonExporter())
    export_registry.register("shopping_list", "txt", infra.text_exporter)
    export_registry.register("shopping_list", "csv", infra.csv_exporter)

    import_registry = ImportRegistry()
    import_registry.register("products", "csv", ProductCsvImporter(infra.product_repo))
    import_registry.register(
        "products", "json", ProductJsonImporter(infra.product_repo)
    )
    import_registry.register("recipes", "csv", RecipeCsvImporter(infra.recipe_repo))
    import_registry.register("recipes", "json", RecipeJsonImporter(infra.recipe_repo))
    import_registry.register("menus", "json", MenuJsonImporter(infra.menu_repo))

    return {
        "export_entities": ExportEntities(
            export_registry,
            infra.product_repo,
            infra.recipe_repo,
            infra.menu_repo,
        ),
        "import_entities": ImportEntities(import_registry, infra.session),
        "export_shopping_list": ExportShoppingList(
            export_registry, generate_shopping_list
        ),
    }
