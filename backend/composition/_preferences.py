"""Wire preference use cases."""

from typing import Any

from backend.application.use_cases.assign_preferences import AssignPreferencesToMember
from backend.application.use_cases.crud_base import GetEntity, ListEntities
from backend.application.use_cases.manage_preference import (
    CreatePreference,
    DeletePreference,
    UpdatePreference,
)
from backend.application.use_cases.match_recipe_preferences import MatchRecipePreferences
from backend.composition._infrastructure import _Infrastructure
from backend.domain.services.preference_matcher import PreferenceMatcher
from backend.infrastructure.repositories.orm_preference_repository import (
    OrmPreferenceRepository,
)


def _wire_preferences(infra: _Infrastructure) -> dict[str, Any]:
    pref_repo = OrmPreferenceRepository(infra.session)
    matcher = PreferenceMatcher(
        recipe_repo=infra.recipe_repo,
        product_repo=infra.product_repo,
    )
    return {
        "create_preference": CreatePreference(pref_repo),
        "update_preference": UpdatePreference(pref_repo),
        "delete_preference": DeletePreference(pref_repo, infra.family_repo),
        "get_preference": GetEntity(pref_repo),
        "list_preferences": ListEntities(pref_repo),
        "match_recipe_preferences": MatchRecipePreferences(
            recipe_repo=infra.recipe_repo,
            preference_repo=pref_repo,
            matcher=matcher,
        ),
        "assign_preferences_to_member": AssignPreferencesToMember(
            family_repo=infra.family_repo,
            preference_repo=pref_repo,
        ),
    }
