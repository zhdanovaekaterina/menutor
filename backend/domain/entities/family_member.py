from dataclasses import dataclass, field

from backend.domain.value_objects.types import FamilyMemberId, UserId


@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float = field(default=1.0)
    dietary_restrictions: str = field(default="")
    comment: str = field(default="")
    user_id: UserId = field(default=UserId(0))

    def effective_servings(self, base_servings: float) -> float:
        return base_servings * self.portion_multiplier
