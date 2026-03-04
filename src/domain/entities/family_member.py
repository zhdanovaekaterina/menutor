from dataclasses import dataclass, field

from src.domain.value_objects.types import FamilyMemberId


@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float = field(default=1.0)
    dietary_restrictions: str = field(default="")
    comment: str = field(default="")

    def effective_servings(self, base_servings: float) -> float:
        return base_servings * self.portion_multiplier
