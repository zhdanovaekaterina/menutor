import io
from typing import Any

from backend.domain.entities.shopping_list import ShoppingList

_UNIT_RU: dict[str, str] = {
    "g": "г", "kg": "кг", "ml": "мл", "l": "л",
    "pcs": "шт", "pack": "упак", "box": "кор",
    "tsp": "ч.л.", "tbsp": "ст.л.",
}


def _to_display(code: str) -> str:
    return _UNIT_RU.get(code, code)


def _build_pdf(shopping_list: ShoppingList) -> bytes:
    """Render a shopping list as a PDF using reportlab."""
    import pathlib

    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import (  # type: ignore[import-untyped]
        ParagraphStyle,
        getSampleStyleSheet,
    )
    from reportlab.lib.units import cm  # type: ignore[import-untyped]
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Список покупок",
    )

    # Register a Unicode-capable font for Cyrillic support.
    # We first try the fonts bundled with this package (DejaVuSans), which
    # guarantees correct rendering without any system font dependency.
    # System-level DejaVu / Liberation paths are kept as a secondary fallback.
    _BUNDLED_DIR = pathlib.Path(__file__).parent / "fonts"

    _CYRILLIC_FONT = "Helvetica"
    _CYRILLIC_FONT_BOLD = "Helvetica-Bold"

    regular_candidates = [
        _BUNDLED_DIR / "DejaVuSans.ttf",
        pathlib.Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        pathlib.Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        pathlib.Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for candidate in regular_candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("CyrillicRegular", str(candidate)))
                _CYRILLIC_FONT = "CyrillicRegular"
            except Exception:
                pass
            break

    bold_candidates = [
        _BUNDLED_DIR / "DejaVuSans-Bold.ttf",
        pathlib.Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        pathlib.Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        pathlib.Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    for candidate in bold_candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("CyrillicBold", str(candidate)))
                _CYRILLIC_FONT_BOLD = "CyrillicBold"
            except Exception:
                pass
            break

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleRu",
        parent=styles["Title"],
        fontName=_CYRILLIC_FONT_BOLD,
        fontSize=18,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "HeadingRu",
        parent=styles["Heading2"],
        fontName=_CYRILLIC_FONT_BOLD,
        fontSize=13,
        textColor=colors.HexColor("#2c5282"),
        spaceBefore=10,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "NormalRu",
        parent=styles["Normal"],
        fontName=_CYRILLIC_FONT,
        fontSize=10,
    )
    total_style = ParagraphStyle(
        "TotalRu",
        parent=styles["Normal"],
        fontName=_CYRILLIC_FONT_BOLD,
        fontSize=11,
        spaceBefore=10,
    )

    story: list[Any] = []
    story.append(Paragraph("Список покупок", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c5282")))
    story.append(Spacer(1, 0.3 * cm))

    for category, items in sorted(shopping_list.items_by_category().items()):
        story.append(Paragraph(category, heading_style))

        table_data = [
            [
                Paragraph("<b>Товар</b>", normal_style),
                Paragraph("<b>Кол-во по рецепту</b>", normal_style),
                Paragraph("<b>Купить</b>", normal_style),
                Paragraph("<b>Стоимость</b>", normal_style),
            ]
        ]
        for item in items:
            rq = item.recipe_quantity if item.recipe_quantity is not None else item.quantity
            bq = item.buy_quantity
            recipe_str = f"{rq.amount:g} {_to_display(rq.unit)}"
            buy_str = f"{bq.amount:g} {_to_display(bq.unit)}"
            cost_str = f"{item.cost.amount:.2f} руб"
            table_data.append([
                Paragraph(item.product_name, normal_style),
                Paragraph(recipe_str, normal_style),
                Paragraph(buy_str, normal_style),
                Paragraph(cost_str, normal_style),
            ])

        col_widths = [7 * cm, 4 * cm, 3 * cm, 3 * cm]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ebf4ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * cm))

    total = shopping_list.total_cost()
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c5282")))
    story.append(
        Paragraph(f"Итого: {total.amount:.2f} руб", total_style)
    )

    doc.build(story)
    return buf.getvalue()


class ShoppingListPdfExporter:
    """Exports a shopping list to PDF using reportlab."""

    def export_bytes(self, entities: list[Any]) -> bytes:
        shopping_list: ShoppingList = entities[0]
        return _build_pdf(shopping_list)

    def example_bytes(self) -> bytes:
        from decimal import Decimal

        from backend.domain.entities.shopping_list import ShoppingListItem
        from backend.domain.value_objects.money import Money
        from backend.domain.value_objects.quantity import Quantity
        from backend.domain.value_objects.types import ProductId

        example_list = ShoppingList(
            items=[
                ShoppingListItem(
                    product_id=ProductId(1),
                    product_name="Молоко",
                    category="Молочные",
                    quantity=Quantity(1.0, "l"),
                    cost=Money(Decimal("80.00")),
                )
            ]
        )
        return _build_pdf(example_list)

    def content_type(self) -> str:
        return "application/pdf"

    def file_extension(self) -> str:
        return "pdf"
