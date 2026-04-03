"""Wire auth use cases."""

from typing import Any

from backend.application.use_cases.auth import (
    ChangePassword,
    GetCurrentUser,
    LoginUser,
    LogoutUser,
    RefreshAccessToken,
    RegisterUser,
    UpdateProfile,
)
from backend.composition._infrastructure import _Infrastructure


def _wire_auth(infra: _Infrastructure) -> dict[str, Any]:
    return {
        "register_user": RegisterUser(
            infra.user_repo, infra.password_hasher, infra.family_repo,
            infra.meal_type_repo,
        ),
        "login_user": LoginUser(
            infra.user_repo,
            infra.password_hasher,
            infra.token_service,
            infra.refresh_token_repo,
        ),
        "refresh_access_token": RefreshAccessToken(
            infra.token_service, infra.refresh_token_repo, infra.user_repo
        ),
        "get_current_user": GetCurrentUser(infra.token_service, infra.user_repo),
        "logout_user": LogoutUser(infra.token_service, infra.refresh_token_repo),
        "change_password": ChangePassword(infra.user_repo, infra.password_hasher),
        "update_profile": UpdateProfile(infra.user_repo, infra.password_hasher),
    }
