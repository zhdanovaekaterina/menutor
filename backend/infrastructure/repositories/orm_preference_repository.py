from typing import Any

from sqlalchemy.orm import Session

from backend.domain.entities.preference import Preference
from backend.domain.exceptions import RepositoryError
from backend.domain.ports.preference_repository import PreferenceRepository
from backend.domain.value_objects.preference_enums import PreferenceMode, PreferenceType
from backend.domain.value_objects.types import (
    PreferenceId,
    ProductCategoryId,
    ProductId,
    RecipeCategoryId,
    UserId,
)
from backend.infrastructure.database.models import (
    PreferenceCategoryRow,
    PreferenceProductRow,
    PreferenceRecipeCategoryRow,
    PreferenceRow,
)


class OrmPreferenceRepository(PreferenceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id: PreferenceId) -> Preference | None:
        row = self._session.get(PreferenceRow, int(id))
        if row is None:
            return None
        self._session.refresh(row)
        return self._row_to_entity(row)

    def find_all(self, user_id: UserId) -> list[Preference]:
        rows = (
            self._session.query(PreferenceRow)
            .filter(PreferenceRow.user_id == int(user_id))
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

    def find_by_ids(
        self, ids: list[PreferenceId], user_id: UserId
    ) -> list[Preference]:
        if not ids:
            return []
        int_ids = [int(i) for i in ids]
        rows = (
            self._session.query(PreferenceRow)
            .filter(
                PreferenceRow.id.in_(int_ids),
                PreferenceRow.user_id == int(user_id),
            )
            .all()
        )
        return [self._row_to_entity(r) for r in rows]

    def find_by_name(self, name: str, user_id: UserId) -> Preference | None:
        row = (
            self._session.query(PreferenceRow)
            .filter(
                PreferenceRow.user_id == int(user_id),
                PreferenceRow.name == name,
            )
            .first()
        )
        if row is None:
            return None
        return self._row_to_entity(row)

    def save(self, preference: Preference) -> Preference:
        if int(preference.id) == 0:
            row = self._make_new_row(preference)
            self._session.add(row)
            self._session.flush()
            new_id = PreferenceId(row.id)
        else:
            row = self._session.get(PreferenceRow, int(preference.id))
            if row is None:
                raise RepositoryError(f"Preference {preference.id} not found")
            self._update_row(row, preference)
            new_id = preference.id
        self._session.commit()
        result = self.get_by_id(new_id)
        assert result is not None
        return result

    def delete(self, ids: list[PreferenceId]) -> None:
        if not ids:
            return
        int_ids = [int(i) for i in ids]
        self._session.query(PreferenceRow).filter(
            PreferenceRow.id.in_(int_ids)
        ).delete(synchronize_session=False)
        self._session.commit()

    def _make_new_row(self, pref: Preference) -> PreferenceRow:
        return PreferenceRow(
            user_id=int(pref.user_id),
            name=pref.name,
            type=pref.type.value,
            mode=pref.mode.value,
            categories=[
                PreferenceCategoryRow(category_id=int(cid))
                for cid in pref.category_ids
            ],
            products=[
                PreferenceProductRow(product_id=int(pid))
                for pid in pref.product_ids
            ],
            recipe_categories=[
                PreferenceRecipeCategoryRow(recipe_category_id=int(rcid))
                for rcid in pref.recipe_category_ids
            ],
        )

    def _update_row(self, row: Any, pref: Preference) -> None:
        row.name = pref.name
        row.type = pref.type.value
        row.mode = pref.mode.value
        row.categories.clear()
        for cid in pref.category_ids:
            row.categories.append(PreferenceCategoryRow(category_id=int(cid)))
        row.products.clear()
        for pid in pref.product_ids:
            row.products.append(PreferenceProductRow(product_id=int(pid)))
        row.recipe_categories.clear()
        for rcid in pref.recipe_category_ids:
            row.recipe_categories.append(
                PreferenceRecipeCategoryRow(recipe_category_id=int(rcid))
            )

    @staticmethod
    def _row_to_entity(row: Any) -> Preference:
        return Preference(
            id=PreferenceId(row.id),
            name=row.name,
            type=PreferenceType(row.type),
            mode=PreferenceMode(row.mode),
            category_ids=[ProductCategoryId(c.category_id) for c in row.categories],
            product_ids=[ProductId(p.product_id) for p in row.products],
            recipe_category_ids=[
                RecipeCategoryId(rc.recipe_category_id) for rc in row.recipe_categories
            ],
            user_id=UserId(row.user_id),
        )
