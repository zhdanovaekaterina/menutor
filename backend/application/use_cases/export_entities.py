from typing import Any

from backend.domain.exceptions import ImportValidationError
from backend.domain.ports.menu_repository import MenuRepository
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.ports.recipe_repository import RecipeRepository
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId, UserId
from backend.infrastructure.export.registry import ExportRegistry


class ExportEntities:
    """Export a user's entities by type and format.

    Returns (bytes, content_type, filename).
    """

    def __init__(
        self,
        export_registry: ExportRegistry,
        product_repo: ProductRepository,
        recipe_repo: RecipeRepository,
        menu_repo: MenuRepository,
    ) -> None:
        self._registry = export_registry
        self._product_repo = product_repo
        self._recipe_repo = recipe_repo
        self._menu_repo = menu_repo

    def execute(
        self,
        entity_type: str,
        format: str,
        user_id: UserId,
        entity_ids: list[int] | None = None,
    ) -> tuple[bytes, str, str]:
        exporter = self._registry.get(entity_type, format)
        if exporter is None:
            raise ImportValidationError(
                f"Формат '{format}' не поддерживается для '{entity_type}'"
            )
        entities = self._load_entities(entity_type, user_id, entity_ids)
        data = exporter.export_bytes(entities)
        filename = f"{entity_type}.{exporter.file_extension()}"
        return data, exporter.content_type(), filename

    def example(self, entity_type: str, format: str) -> tuple[bytes, str, str]:
        exporter = self._registry.get(entity_type, format)
        if exporter is None:
            raise ImportValidationError(
                f"Формат '{format}' не поддерживается для '{entity_type}'"
            )
        filename = f"example_{entity_type}.{exporter.file_extension()}"
        return exporter.example_bytes(), exporter.content_type(), filename

    def _load_entities(
        self,
        entity_type: str,
        user_id: UserId,
        entity_ids: list[int] | None,
    ) -> list[Any]:
        if entity_type == "products":
            all_entities = self._product_repo.find_all(user_id)
            if entity_ids is not None:
                id_set = set(entity_ids)
                return [e for e in all_entities if e.id in id_set]
            return all_entities

        if entity_type == "recipes":
            all_entities = self._recipe_repo.find_all(user_id)
            if entity_ids is not None:
                id_set = set(entity_ids)
                return [e for e in all_entities if e.id in id_set]
            return all_entities

        if entity_type == "menus":
            all_entities = self._menu_repo.find_all(user_id)
            if entity_ids is not None:
                id_set = set(entity_ids)
                return [e for e in all_entities if e.id in id_set]
            return all_entities

        raise ImportValidationError(f"Неизвестный тип сущности: '{entity_type}'")
