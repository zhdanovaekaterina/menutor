from dataclasses import dataclass


@dataclass(frozen=True)
class CookingStep:
    order: int
    description: str
