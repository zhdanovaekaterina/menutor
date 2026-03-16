import json
from decimal import Decimal, InvalidOperation

from backend.domain.entities.product import Product
from backend.domain.exceptions import ImportValidationError
from backend.domain.ports.product_repository import ProductRepository
from backend.domain.value_objects.import_result import ImportResult
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.types import ProductCategoryId, ProductId, UserId

_REQUIRED = {"name", "category_id", "recipe_unit", "purchase_unit", "price_amount"}


class ProductJsonImporter:
    def __init__(self, repo: ProductRepository) -> None:
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

            missing = _REQUIRED - set(row.keys())
            if missing:
                raise ImportValidationError(
                    f"Элемент {i}: отсутствуют обязательные поля: {', '.join(sorted(missing))}"
                )
            if not str(row.get("name", "")).strip():
                raise ImportValidationError(f"Элемент {i}: поле 'name' не может быть пустым")

            try:
                price_amount = Decimal(str(row["price_amount"]))
            except InvalidOperation:
                raise ImportValidationError(f"Элемент {i}: некорректное значение 'price_amount'")

            try:
                category_id = int(row["category_id"])
            except (ValueError, TypeError):
                raise ImportValidationError(f"Элемент {i}: некорректное значение 'category_id'")

            try:
                conversion_factor = float(row.get("conversion_factor") or 1.0)
            except (ValueError, TypeError):
                raise ImportValidationError(f"Элемент {i}: некорректное значение 'conversion_factor'")

            raw_id = int(row.get("id") or 0)
            existing = self._repo.get_by_id(ProductId(raw_id)) if raw_id > 0 else None
            if existing is not None and existing.user_id == user_id:
                entity_id = existing.id
                updated += 1
            else:
                entity_id = ProductId(0)
                created += 1

            product = Product(
                id=entity_id,
                name=str(row["name"]).strip(),
                recipe_unit=str(row["recipe_unit"]).strip(),
                purchase_unit=str(row["purchase_unit"]).strip(),
                price_per_purchase_unit=Money(
                    price_amount,
                    str(row.get("price_currency") or "RUB").strip(),
                ),
                brand=str(row.get("brand") or "").strip(),
                supplier=str(row.get("supplier") or "").strip(),
                conversion_factor=conversion_factor,
                category_id=ProductCategoryId(category_id),
                user_id=user_id,
            )
            self._repo.save(product)

        return ImportResult(created=created, updated=updated)

    def supported_extensions(self) -> list[str]:
        return ["json"]
