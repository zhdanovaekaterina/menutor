import io
import pathlib
from typing import Any

from backend.domain.entities.menu import WeeklyMenu

_DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

_UNIT_RU: dict[str, str] = {
    "g": "г", "kg": "кг", "ml": "мл", "l": "л",
    "pcs": "шт", "pack": "упак", "box": "кор",
    "tsp": "ч.л.", "tbsp": "ст.л.", "serv": "порц",
}


def _unit_label(unit: str) -> str:
    return _UNIT_RU.get(unit, unit)

_BUNDLED_DIR = pathlib.Path(__file__).parent / "fonts"

_REGULAR_CANDIDATES = [
    _BUNDLED_DIR / "DejaVuSans.ttf",
    pathlib.Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    pathlib.Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    pathlib.Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
]
_BOLD_CANDIDATES = [
    _BUNDLED_DIR / "DejaVuSans-Bold.ttf",
    pathlib.Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    pathlib.Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    pathlib.Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
]


def _register_fonts() -> tuple[str, str]:
    """Register Cyrillic-capable fonts and return (regular_name, bold_name)."""
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
    from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]

    regular = "Helvetica"
    bold = "Helvetica-Bold"

    for candidate in _REGULAR_CANDIDATES:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("CyrillicRegular", str(candidate)))
                regular = "CyrillicRegular"
            except Exception:
                pass
            break

    for candidate in _BOLD_CANDIDATES:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("CyrillicBold", str(candidate)))
                bold = "CyrillicBold"
            except Exception:
                pass
            break

    return regular, bold


_RECIPE_DEFAULT_COLOR = "#3B82F6"
_PRODUCT_DEFAULT_COLOR = "#10B981"


def _cell_text(
    menu: WeeklyMenu,
    day: int,
    meal_type_id: int,
    recipe_names: dict[int, str],
    product_names: dict[int, str],
    recipe_colors: dict[int, str] | None = None,
    product_colors: dict[int, str] | None = None,
) -> str:
    """Build the text content for a single grid cell."""
    slots = [
        s for s in menu.slots if s.day == day and int(s.meal_type_id) == meal_type_id
    ]
    slots.sort(key=lambda s: s.position)

    lines: list[str] = []
    for slot in slots:
        if slot.recipe_id is not None:
            rid = int(slot.recipe_id)
            name = recipe_names.get(rid, f"Рецепт #{slot.recipe_id}")
            color = (recipe_colors or {}).get(rid, _RECIPE_DEFAULT_COLOR)
            if slot.servings_override is not None:
                servings = slot.servings_override
                # Format as integer when whole number
                if servings == int(servings):
                    label = f"{name} ({int(servings)}п)"
                else:
                    label = f"{name} ({servings:g}п)"
            else:
                label = name
            lines.append(f'<font color="{color}">&#9632;</font> {label}')
        elif slot.product_id is not None:
            pid = int(slot.product_id)
            name = product_names.get(pid, f"Продукт #{slot.product_id}")
            color = (product_colors or {}).get(pid, _PRODUCT_DEFAULT_COLOR)
            if slot.quantity is not None and slot.unit is not None:
                label = f"{name} {slot.quantity:g} {_unit_label(slot.unit)}"
            else:
                label = name
            lines.append(f'<font color="{color}">&#9632;</font> {label}')

    return "<br/>".join(lines)


def _build_pdf(
    menu: WeeklyMenu,
    recipe_names: dict[int, str],
    product_names: dict[int, str],
    paper: str = "a4",
    recipe_colors: dict[int, str] | None = None,
    product_colors: dict[int, str] | None = None,
    meal_type_names: dict[int, str] | None = None,
) -> bytes:
    """Render the weekly menu as a PDF planning grid."""
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import (  # type: ignore[import-untyped]
        A3,
        A4,
        landscape,
    )
    from reportlab.lib.styles import ParagraphStyle  # type: ignore[import-untyped]
    from reportlab.lib.units import cm  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    paper_norm = paper.strip().lower()
    base_size = A3 if paper_norm == "a3" else A4
    page_size = landscape(base_size)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=menu.name,
    )

    regular, bold = _register_fonts()

    title_style = ParagraphStyle(
        "MenuTitle",
        fontName=bold,
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor("#2c5282"),
    )
    header_style = ParagraphStyle(
        "ColHeader",
        fontName=bold,
        fontSize=9,
        alignment=1,  # centre
        textColor=colors.HexColor("#2c5282"),
    )
    meal_label_style = ParagraphStyle(
        "MealLabel",
        fontName=bold,
        fontSize=9,
        textColor=colors.HexColor("#2c5282"),
    )
    cell_style = ParagraphStyle(
        "CellText",
        fontName=regular,
        fontSize=8,
        leading=11,
    )

    # --- Build ordered list of (meal_type_id, label) pairs ---
    # Use provided meal_type_names; fall back to generic label for unknown ids.
    names = meal_type_names or {}

    # Collect all unique meal_type_ids present in the menu, sorted by id for stable order
    slot_type_ids = sorted({int(s.meal_type_id) for s in menu.slots})

    # Build ordered set: ids from meal_type_names dict first (in their natural order by id),
    # then any additional ids from slots not covered by the names dict.
    known_ids = sorted(names.keys())
    extra_ids = [tid for tid in slot_type_ids if tid not in names]
    ordered_ids = known_ids + extra_ids

    # If no meal type info at all, fall back to just the ids found in slots
    if not ordered_ids:
        ordered_ids = slot_type_ids

    # --- Build table data ---
    # Header row: ["", "Пн", "Вт", ..., "Вс"]
    header_row: list[Any] = [Paragraph("", header_style)]
    for day_label in _DAYS_RU:
        header_row.append(Paragraph(day_label, header_style))

    table_data: list[list[Any]] = [header_row]

    for meal_type_id in ordered_ids:
        label = names.get(meal_type_id, f"Тип #{meal_type_id}")
        row: list[Any] = [Paragraph(label, meal_label_style)]
        for day_idx in range(7):
            text = _cell_text(
                menu, day_idx, meal_type_id,
                recipe_names, product_names, recipe_colors, product_colors,
            )
            row.append(Paragraph(text, cell_style))
        table_data.append(row)

    # --- Column widths ---
    # Available width = page width - margins
    available_w = page_size[0] - 3.0 * cm  # left + right margins
    label_col_w = 2.2 * cm
    day_col_w = (available_w - label_col_w) / 7

    col_widths = [label_col_w] + [day_col_w] * 7

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header row background
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ebf4ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
        # Meal label column (first column, data rows)
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#ebf4ff")),
        # Alternating row backgrounds for data rows
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        # Vertical alignment
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story: list[Any] = [
        Paragraph(menu.name, title_style),
        Spacer(1, 0.3 * cm),
        table,
    ]

    doc.build(story)
    return buf.getvalue()


class MenuPdfExporter:
    """Exports a weekly menu to a PDF planning grid."""

    def export_bytes(
        self,
        menu: WeeklyMenu,
        recipe_names: dict[int, str],
        product_names: dict[int, str],
        paper: str = "a4",
        recipe_colors: dict[int, str] | None = None,
        product_colors: dict[int, str] | None = None,
        meal_type_names: dict[int, str] | None = None,
    ) -> bytes:
        return _build_pdf(
            menu, recipe_names, product_names, paper,
            recipe_colors, product_colors, meal_type_names,
        )
