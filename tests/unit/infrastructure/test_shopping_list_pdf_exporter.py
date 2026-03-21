"""Tests for ShoppingListPdfExporter.

reportlab must be installed (`pip install reportlab`) for these tests to run.
"""
import pytest
from decimal import Decimal

from backend.domain.entities.shopping_list import ShoppingList, ShoppingListItem
from backend.domain.value_objects.money import Money
from backend.domain.value_objects.quantity import Quantity
from backend.domain.value_objects.types import ProductId
from backend.infrastructure.export.shopping_list_pdf_exporter import ShoppingListPdfExporter

reportlab = pytest.importorskip("reportlab", reason="reportlab not installed")


def _item(
    name: str = "Молоко",
    category: str = "Молочные",
    qty: float = 1.0,
    unit: str = "l",
    cost: float = 80.0,
) -> ShoppingListItem:
    return ShoppingListItem(
        product_id=ProductId(1),
        product_name=name,
        category=category,
        quantity=Quantity(qty, unit),
        cost=Money(Decimal(str(cost))),
    )


class TestShoppingListPdfExporter:
    def test_export_bytes_returns_bytes(self) -> None:
        sl = ShoppingList(items=[_item()])
        data = ShoppingListPdfExporter().export_bytes([sl])
        assert isinstance(data, bytes)

    def test_output_starts_with_pdf_magic_bytes(self) -> None:
        sl = ShoppingList(items=[_item()])
        data = ShoppingListPdfExporter().export_bytes([sl])
        assert data[:4] == b"%PDF"

    def test_empty_list_produces_valid_pdf(self) -> None:
        data = ShoppingListPdfExporter().export_bytes([ShoppingList()])
        assert data[:4] == b"%PDF"

    def test_content_type(self) -> None:
        assert ShoppingListPdfExporter().content_type() == "application/pdf"

    def test_file_extension(self) -> None:
        assert ShoppingListPdfExporter().file_extension() == "pdf"

    def test_example_bytes_is_valid_pdf(self) -> None:
        data = ShoppingListPdfExporter().example_bytes()
        assert isinstance(data, bytes)
        assert data[:4] == b"%PDF"

    def test_multiple_categories_produce_non_empty_output(self) -> None:
        sl = ShoppingList(items=[
            _item("Мука", "Сыпучие", qty=1.0, unit="kg", cost=60.0),
            _item("Молоко", "Молочные", qty=1.0, unit="l", cost=80.0),
        ])
        data = ShoppingListPdfExporter().export_bytes([sl])
        assert len(data) > 1000  # a non-trivial PDF is always well over 1 KB

    def test_item_with_recipe_quantity_produces_valid_pdf(self) -> None:
        item = ShoppingListItem(
            product_id=ProductId(1),
            product_name="Мука",
            category="Сыпучие",
            quantity=Quantity(0.2, "kg"),
            cost=Money(Decimal("16")),
            recipe_quantity=Quantity(200.0, "g"),
        )
        sl = ShoppingList(items=[item])
        data = ShoppingListPdfExporter().export_bytes([sl])
        assert data[:4] == b"%PDF"

    def test_cyrillic_font_is_embedded(self) -> None:
        """The PDF must subset-embed DejaVuSans so Cyrillic glyphs render correctly.

        When reportlab uses only the built-in Helvetica (Type1, no Cyrillic
        glyphs), it never embeds a font program — Cyrillic characters become
        question marks or boxes in any PDF viewer.

        reportlab subset-embeds TTF fonts with a random 6-letter prefix followed
        by '+FontName' (e.g. 'AAAAAA+DejaVuSans').  We verify that the embedded
        font is DejaVuSans by searching for the '+DejaVuSans' suffix in the raw
        PDF bytes.
        """
        import re

        sl = ShoppingList(items=[_item("Молоко", "Молочные")])
        data = ShoppingListPdfExporter().export_bytes([sl])
        assert re.search(rb"[A-Z]{6}\+DejaVuSans", data), (
            "PDF does not contain an embedded DejaVuSans subset. "
            "Ensure backend/infrastructure/export/fonts/DejaVuSans.ttf exists "
            "and is being registered as the Cyrillic font."
        )
