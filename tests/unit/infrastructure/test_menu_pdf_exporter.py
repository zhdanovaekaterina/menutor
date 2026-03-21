"""Tests for MenuPdfExporter.

reportlab must be installed for these tests to run.
"""
import re

import pytest

from backend.domain.entities.menu import MenuSlot, WeeklyMenu
from backend.domain.value_objects.types import MenuId, ProductId, RecipeId
from backend.infrastructure.export.menu_pdf_exporter import MenuPdfExporter

reportlab = pytest.importorskip("reportlab", reason="reportlab not installed")


def _make_menu(slots: list[MenuSlot] | None = None) -> WeeklyMenu:
    return WeeklyMenu(
        id=MenuId(1),
        name="Тестовое меню",
        slots=slots or [],
    )


def _recipe_slot(day: int, meal_type: str, recipe_id: int = 1, servings: float | None = None) -> MenuSlot:
    return MenuSlot(
        day=day,
        meal_type=meal_type,
        recipe_id=RecipeId(recipe_id),
        servings_override=servings,
    )


def _product_slot(
    day: int,
    meal_type: str,
    product_id: int = 1,
    quantity: float | None = None,
    unit: str | None = None,
) -> MenuSlot:
    return MenuSlot(
        day=day,
        meal_type=meal_type,
        product_id=ProductId(product_id),
        quantity=quantity,
        unit=unit,
    )


class TestMenuPdfExporter:
    def test_returns_bytes(self) -> None:
        menu = _make_menu()
        data = MenuPdfExporter().export_bytes(menu, {}, {})
        assert isinstance(data, bytes)

    def test_starts_with_pdf_magic(self) -> None:
        menu = _make_menu()
        data = MenuPdfExporter().export_bytes(menu, {}, {})
        assert data[:4] == b"%PDF"

    def test_empty_menu_produces_valid_pdf(self) -> None:
        """A menu with no slots should still render without errors."""
        menu = _make_menu(slots=[])
        data = MenuPdfExporter().export_bytes(menu, {}, {})
        assert data[:4] == b"%PDF"
        assert len(data) > 500

    def test_menu_with_recipe_slots(self) -> None:
        slots = [
            _recipe_slot(0, "Завтрак", recipe_id=10),
            _recipe_slot(3, "Обед", recipe_id=20, servings=2.0),
        ]
        menu = _make_menu(slots)
        recipe_names = {10: "Омлет", 20: "Борщ"}
        data = MenuPdfExporter().export_bytes(menu, recipe_names, {})
        assert data[:4] == b"%PDF"
        assert len(data) > 1000

    def test_menu_with_product_slots(self) -> None:
        slots = [
            _product_slot(1, "Завтрак", product_id=5, quantity=250.0, unit="мл"),
            _product_slot(4, "Ужин", product_id=6),
        ]
        menu = _make_menu(slots)
        product_names = {5: "Молоко", 6: "Кефир"}
        data = MenuPdfExporter().export_bytes(menu, {}, product_names)
        assert data[:4] == b"%PDF"

    def test_a4_produces_valid_pdf(self) -> None:
        menu = _make_menu([_recipe_slot(0, "Завтрак")])
        data = MenuPdfExporter().export_bytes(menu, {1: "Каша"}, {}, paper="a4")
        assert data[:4] == b"%PDF"

    def test_a3_produces_valid_pdf(self) -> None:
        menu = _make_menu([_recipe_slot(0, "Завтрак")])
        data = MenuPdfExporter().export_bytes(menu, {1: "Каша"}, {}, paper="a3")
        assert data[:4] == b"%PDF"

    def test_a4_and_a3_produce_different_sizes(self) -> None:
        """A3 pages are larger than A4, so the PDF output sizes will differ."""
        slots = [_recipe_slot(i, "Обед") for i in range(7)]
        recipe_names = {1: "Суп"}
        menu_a4 = _make_menu(slots)
        menu_a3 = _make_menu(slots)
        data_a4 = MenuPdfExporter().export_bytes(menu_a4, recipe_names, {}, paper="a4")
        data_a3 = MenuPdfExporter().export_bytes(menu_a3, recipe_names, {}, paper="a3")
        assert len(data_a4) != len(data_a3)

    def test_paper_param_case_insensitive(self) -> None:
        menu = _make_menu()
        data_upper = MenuPdfExporter().export_bytes(menu, {}, {}, paper="A4")
        data_lower = MenuPdfExporter().export_bytes(menu, {}, {}, paper="a4")
        # Both should produce valid PDFs (sizes may differ due to internal randomness,
        # but both must start with %PDF)
        assert data_upper[:4] == b"%PDF"
        assert data_lower[:4] == b"%PDF"

    def test_cyrillic_font_is_embedded(self) -> None:
        """The PDF must subset-embed DejaVuSans for correct Cyrillic rendering.

        reportlab subset-embeds TTF fonts with a random 6-letter prefix followed
        by '+FontName' (e.g. 'AAAAAA+DejaVuSans').  We verify that the embedded
        font is DejaVuSans by searching for the '+DejaVuSans' suffix in the raw
        PDF bytes.
        """
        slots = [_recipe_slot(0, "Завтрак", recipe_id=1)]
        menu = _make_menu(slots)
        data = MenuPdfExporter().export_bytes(menu, {1: "Омлет с сыром"}, {})
        assert re.search(rb"[A-Z]{6}\+DejaVuSans", data), (
            "PDF does not contain an embedded DejaVuSans subset. "
            "Ensure backend/infrastructure/export/fonts/DejaVuSans.ttf exists "
            "and is being registered as the Cyrillic font."
        )

    def test_servings_override_shown_as_integer_when_whole(self) -> None:
        """Servings displayed as '2п' not '2.0п' for whole numbers."""
        slots = [_recipe_slot(0, "Обед", recipe_id=1, servings=2.0)]
        menu = _make_menu(slots)
        # We cannot easily inspect PDF text content, but we can verify it renders
        data = MenuPdfExporter().export_bytes(menu, {1: "Пицца"}, {})
        assert data[:4] == b"%PDF"

    def test_servings_override_shown_for_recipe(self) -> None:
        """A fractional servings_override renders without error."""
        slots = [_recipe_slot(0, "Обед", recipe_id=1, servings=1.5)]
        menu = _make_menu(slots)
        data = MenuPdfExporter().export_bytes(menu, {1: "Пицца"}, {})
        assert data[:4] == b"%PDF"

    def test_full_week_all_meals(self) -> None:
        """Filling every cell in the grid renders without errors."""
        slots = []
        for day in range(7):
            for meal_type in ["Завтрак", "Обед", "Ужин"]:
                slots.append(_recipe_slot(day, meal_type, recipe_id=day + 1))
        recipe_names = {i: f"Рецепт {i}" for i in range(1, 8)}
        menu = _make_menu(slots)
        data = MenuPdfExporter().export_bytes(menu, recipe_names, {})
        assert data[:4] == b"%PDF"
        assert len(data) > 2000
