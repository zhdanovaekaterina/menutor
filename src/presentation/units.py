"""Перевод единиц измерения: английские коды (БД) ↔ русские названия (UI)."""

UNIT_RU: dict[str, str] = {
    "g": "г",
    "kg": "кг",
    "ml": "мл",
    "l": "л",
    "pcs": "шт",
    "pack": "упак",
    "box": "кор",
}

_UNIT_EN: dict[str, str] = {v: k for k, v in UNIT_RU.items()}

# Ordered list for combo boxes
UNIT_DISPLAY_OPTIONS: list[str] = [UNIT_RU[k] for k in ("g", "kg", "ml", "l", "pcs", "pack", "box")]


def to_display(code: str) -> str:
    """Английский код → русское отображение. Неизвестные единицы возвращаются как есть."""
    return UNIT_RU.get(code, code)


def to_code(display: str) -> str:
    """Русское отображение → английский код. Неизвестные строки возвращаются как есть."""
    return _UNIT_EN.get(display, display)
