import pytest

from src.domain.value_objects.quantity import Quantity


def test_add_same_unit() -> None:
    result = Quantity(100.0, "g") + Quantity(200.0, "g")
    assert result == Quantity(300.0, "g")


def test_add_with_auto_conversion_g_plus_kg() -> None:
    result = Quantity(500.0, "g") + Quantity(1.0, "kg")
    assert result == Quantity(1500.0, "g")


def test_add_kg_plus_g() -> None:
    result = Quantity(1.0, "kg") + Quantity(500.0, "g")
    assert result == Quantity(1.5, "kg")


def test_add_ml_plus_l() -> None:
    result = Quantity(500.0, "ml") + Quantity(0.5, "l")
    assert result == Quantity(1000.0, "ml")


def test_convert_g_to_kg() -> None:
    result = Quantity(1000.0, "g").convert_to("kg")
    assert result == Quantity(1.0, "kg")


def test_convert_kg_to_g() -> None:
    result = Quantity(2.5, "kg").convert_to("g")
    assert result == Quantity(2500.0, "g")


def test_convert_l_to_ml() -> None:
    result = Quantity(1.5, "l").convert_to("ml")
    assert result == Quantity(1500.0, "ml")


def test_convert_same_unit_returns_equal_object() -> None:
    q = Quantity(500.0, "g")
    assert q.convert_to("g") == q


def test_cross_group_conversion_raises() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        Quantity(100.0, "g").convert_to("ml")


def test_add_incompatible_units_raises() -> None:
    with pytest.raises(ValueError):
        _ = Quantity(100.0, "g") + Quantity(100.0, "ml")


def test_unknown_unit_at_construction_raises() -> None:
    with pytest.raises(ValueError, match="Unknown unit"):
        Quantity(1.0, "furlongs")


def test_quantity_is_immutable() -> None:
    q = Quantity(100.0, "g")
    with pytest.raises(Exception):
        q.amount = 200.0  # type: ignore[misc]


def test_count_units_no_conversion_between_types() -> None:
    with pytest.raises(ValueError):
        Quantity(1.0, "pcs").convert_to("box")


def test_add_count_same_unit() -> None:
    result = Quantity(3.0, "pcs") + Quantity(2.0, "pcs")
    assert result == Quantity(5.0, "pcs")
