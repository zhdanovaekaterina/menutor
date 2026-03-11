from pydantic import BaseModel


class FamilyMemberCreate(BaseModel):
    name: str
    portion_multiplier: float = 1.0
    dietary_restrictions: str = ""
    comment: str = ""


class FamilyMemberUpdate(BaseModel):
    name: str
    portion_multiplier: float = 1.0
    dietary_restrictions: str = ""
    comment: str = ""


class FamilyMemberResponse(BaseModel):
    id: int
    name: str
    portion_multiplier: float
    dietary_restrictions: str
    comment: str
