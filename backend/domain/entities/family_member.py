from dataclasses import dataclass, field

from backend.domain.value_objects.types import FamilyMemberId, PreferenceId, UserId


@dataclass
class FamilyMember:
    id: FamilyMemberId
    name: str
    portion_multiplier: float = field(default=1.0)
    comment: str = field(default="")
    user_id: UserId = field(default=UserId(0))
    preference_ids: list[PreferenceId] = field(default_factory=list)

    def effective_servings(self, base_servings: float) -> float:
        return base_servings * self.portion_multiplier
