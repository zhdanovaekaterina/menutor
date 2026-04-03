from dataclasses import dataclass, field

from backend.domain.exceptions import InvalidEntityError
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import (
    PreferenceId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    UserId,
)


@dataclass
class Preference:
    id: PreferenceId
    name: str
    type: PreferenceType
    mode: PreferenceMode
    category_ids: list[ProductCategoryId] = field(default_factory=list)
    product_ids: list[ProductId] = field(default_factory=list)
    recipe_category_ids: list[RecipeCategoryId] = field(default_factory=list)
    user_id: UserId = field(default=UserId(0))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidEntityError("Название предпочтения не может быть пустым")
        if self.type == PreferenceType.ALLERGY and self.mode != PreferenceMode.BLOCKED:
            raise InvalidEntityError("Аллергия всегда имеет режим BLOCKED")
        if self.type == PreferenceType.CATEGORY_BASED and self.product_ids:
            raise InvalidEntityError(
                "Предпочтение по категориям не может содержать отдельные продукты"
            )
