import json
from decimal import Decimal

from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId
from backend.infrastructure.export.shopping_list_json_exporter import ShoppingListJsonExporter


def _item(
    name: str = "Мука",
    category: str = "Сыпучие",
    qty: float = 1.0,
    unit: str = "kg",
    cost: float = 80.0,
    recipe_qty: float | None = None,
    recipe_unit: str = "g",
) -> ShoppingListItem:
    return ShoppingListItem(
        product_id=ProductId(1),
        product_name=name,
        category=category,
        quantity=Quantity(qty, unit),
        cost=Money(Decimal(str(cost))),
        recipe_quantity=Quantity(recipe_qty, recipe_unit) if recipe_qty is not None else None,
    )


class TestShoppingListJsonExporter:
    def _parse(self, entities: list[ShoppingList]) -> dict:  # type: ignore[type-arg]
        data = ShoppingListJsonExporter().export_bytes(entities)
        return json.loads(data.decode("utf-8"))

    def test_title_is_in_russian(self) -> None:
        result = self._parse([ShoppingList()])
        assert result["title"] == "Список покупок"

    def test_empty_list_has_no_categories(self) -> None:
        result = self._parse([ShoppingList()])
        assert result["categories"] == []

    def test_total_cost_zero_for_empty_list(self) -> None:
        result = self._parse([ShoppingList()])
        assert result["total_cost"]["amount"] == "0.00"
        assert result["total_cost"]["currency"] == "RUB"

    def test_category_grouping(self) -> None:
        sl = ShoppingList(items=[
            _item("Мука", "Сыпучие"),
            _item("Молоко", "Молочные", qty=1.0, unit="l"),
        ])
        result = self._parse([sl])
        category_names = [c["category"] for c in result["categories"]]
        assert "Сыпучие" in category_names
        assert "Молочные" in category_names

    def test_categories_sorted_alphabetically(self) -> None:
        sl = ShoppingList(items=[
            _item("Молоко", "Молочные"),
            _item("Мука", "Сыпучие"),
        ])
        result = self._parse([sl])
        category_names = [c["category"] for c in result["categories"]]
        assert category_names == sorted(category_names)

    def test_item_fields_present(self) -> None:
        sl = ShoppingList(items=[_item("Мука", "Сыпучие", qty=0.5, unit="kg", cost=40.0)])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["product_name"] == "Мука"
        assert item["purchased"] is False

    def test_buy_quantity_rounds_up(self) -> None:
        sl = ShoppingList(items=[_item(qty=1.3, unit="kg")])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["buy_quantity"]["amount"] == 2

    def test_recipe_quantity_used_when_present(self) -> None:
        sl = ShoppingList(items=[_item(qty=0.2, unit="kg", recipe_qty=200.0, recipe_unit="g")])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["recipe_quantity"]["amount"] == 200.0
        assert item["recipe_quantity"]["unit"] == "g"
        assert item["recipe_quantity"]["unit_ru"] == "г"

    def test_recipe_quantity_falls_back_to_quantity_when_none(self) -> None:
        sl = ShoppingList(items=[_item(qty=0.5, unit="l")])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["recipe_quantity"]["unit"] == "l"
        assert item["recipe_quantity"]["unit_ru"] == "л"

    def test_unit_ru_label_for_known_unit(self) -> None:
        sl = ShoppingList(items=[_item(unit="kg")])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["buy_quantity"]["unit_ru"] == "кг"

    def test_unit_ru_label_falls_back_to_code_for_unknown(self) -> None:
        from backend.infrastructure.export.shopping_list_json_exporter import _to_display
        assert _to_display("oz") == "oz"
        assert _to_display("pieces") == "pieces"

    def test_cost_formatted_to_two_decimals(self) -> None:
        sl = ShoppingList(items=[_item(cost=80.5)])
        result = self._parse([sl])
        item = result["categories"][0]["items"][0]
        assert item["cost"]["amount"] == "80.50"

    def test_total_cost_sum(self) -> None:
        sl = ShoppingList(items=[
            _item("Мука",   "Сыпучие",  cost=80.0),
            _item("Молоко", "Молочные", cost=45.0),
        ])
        result = self._parse([sl])
        assert result["total_cost"]["amount"] == "125.00"

    def test_content_type(self) -> None:
        assert ShoppingListJsonExporter().content_type() == "application/json"

    def test_file_extension(self) -> None:
        assert ShoppingListJsonExporter().file_extension() == "json"

    def test_example_bytes_is_valid_json(self) -> None:
        data = ShoppingListJsonExporter().example_bytes()
        parsed = json.loads(data.decode("utf-8"))
        assert "categories" in parsed
        assert "total_cost" in parsed

    def test_output_is_utf8_bytes(self) -> None:
        sl = ShoppingList(items=[_item("Мука", "Сыпучие")])
        data = ShoppingListJsonExporter().export_bytes([sl])
        assert isinstance(data, bytes)
        decoded = data.decode("utf-8")
        assert "Мука" in decoded
