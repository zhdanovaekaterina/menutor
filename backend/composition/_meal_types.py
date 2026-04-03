"""Wire meal type use cases."""

from typing import Any

from backend.application.use_cases.manage_meal_type import (
    CheckMealTypeUsage,
    CreateMealType,
    DeleteMealType,
    ListMealTypes,
    UpdateMealType,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_meal_types(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "list_meal_types": ListMealTypes(infra.meal_type_repo),
        "create_meal_type": CreateMealType(infra.meal_type_repo),
        "update_meal_type": UpdateMealType(infra.meal_type_repo),
        "delete_meal_type": DeleteMealType(infra.meal_type_repo),
        "check_meal_type_usage": CheckMealTypeUsage(infra.meal_type_repo),
    }
