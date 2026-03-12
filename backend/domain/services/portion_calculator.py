from backend.domain.entities.family_member import FamilyMember


class PortionCalculator:
    def total_servings(self, base_servings: float, members: list[FamilyMember]) -> float:
        return sum(m.effective_servings(base_servings) for m in members)
