"""Tests for presentation.units — code↔display unit conversion."""

from src.presentation.units import UNIT_DISPLAY_OPTIONS, UNIT_RU, to_code, to_display


class TestToDisplay:
    def test_known_units(self) -> None:
        assert to_display("g") == "г"
        assert to_display("kg") == "кг"
        assert to_display("ml") == "мл"
        assert to_display("l") == "л"
        assert to_display("pcs") == "шт"
        assert to_display("pack") == "упак"
        assert to_display("box") == "кор"

    def test_unknown_unit_returns_as_is(self) -> None:
        assert to_display("oz") == "oz"
        assert to_display("") == ""


class TestToCode:
    def test_known_units(self) -> None:
        assert to_code("г") == "g"
        assert to_code("кг") == "kg"
        assert to_code("мл") == "ml"
        assert to_code("л") == "l"
        assert to_code("шт") == "pcs"
        assert to_code("упак") == "pack"
        assert to_code("кор") == "box"

    def test_unknown_display_returns_as_is(self) -> None:
        assert to_code("литры") == "литры"
        assert to_code("") == ""


class TestConstants:
    def test_unit_ru_has_all_7_units(self) -> None:
        assert len(UNIT_RU) == 7

    def test_display_options_ordered(self) -> None:
        assert UNIT_DISPLAY_OPTIONS == ["г", "кг", "мл", "л", "шт", "упак", "кор"]

    def test_roundtrip_all_units(self) -> None:
        for code, display in UNIT_RU.items():
            assert to_code(to_display(code)) == code
            assert to_display(to_code(display)) == display
