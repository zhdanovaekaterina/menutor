from src.domain.value_objects.quantity import Quantity


class UnitConverter:
    def convert(self, quantity: Quantity, target_unit: str) -> Quantity:
        return quantity.convert_to(target_unit)
