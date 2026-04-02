from enum import Enum


class PreferenceType(Enum):
    CATEGORY_BASED = "CATEGORY_BASED"
    ALLERGY = "ALLERGY"


class PreferenceMode(Enum):
    BLOCKED = "BLOCKED"
    ALLOWED = "ALLOWED"
