from pydantic import BaseModel


class FamilyMemberCreate(BaseModel):
    name: str
    portion_multiplier: float = 1.0
    comment: str = ""
    preference_ids: list[int] = []


FamilyMemberUpdate = FamilyMemberCreate


class FamilyMemberResponse(BaseModel):
    id: int
    name: str
    portion_multiplier: float
    comment: str
    preference_ids: list[int]
