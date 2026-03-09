from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.exceptions import CurrencyMismatchError


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = field(default="RUB")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot add {self.currency} and {other.currency}: currency mismatch"
            )
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)
