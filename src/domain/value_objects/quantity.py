from dataclasses import dataclass

from src.domain.exceptions import UnitConversionError

# Maps unit name → unit group
_UNIT_GROUPS: dict[str, str] = {
    "g": "weight",
    "kg": "weight",
    "ml": "volume",
    "l": "volume",
    "pcs": "count_pcs",
    "box": "count_box",
    "pack": "count_pack",
}

# Amount of each unit expressed in the group's base unit (g for weight, ml for volume)
_TO_BASE: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "ml": 1.0,
    "l": 1000.0,
    "pcs": 1.0,
    "box": 1.0,
    "pack": 1.0,
}


@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: str

    def __post_init__(self) -> None:
        if self.unit not in _UNIT_GROUPS:
            raise UnitConversionError(f"Unknown unit: '{self.unit}'")

    def convert_to(self, target_unit: str) -> "Quantity":
        if target_unit not in _UNIT_GROUPS:
            raise UnitConversionError(f"Unknown unit: '{target_unit}'")
        if _UNIT_GROUPS[self.unit] != _UNIT_GROUPS[target_unit]:
            raise UnitConversionError(
                f"Cannot convert '{self.unit}' to '{target_unit}': incompatible unit groups"
            )
        if self.unit == target_unit:
            return self
        base_amount = self.amount * _TO_BASE[self.unit]
        return Quantity(base_amount / _TO_BASE[target_unit], target_unit)

    def __add__(self, other: "Quantity") -> "Quantity":
        if _UNIT_GROUPS[self.unit] != _UNIT_GROUPS[other.unit]:
            raise UnitConversionError(
                f"Cannot add '{self.unit}' and '{other.unit}': incompatible unit groups"
            )
        converted = other.convert_to(self.unit)
        return Quantity(self.amount + converted.amount, self.unit)
