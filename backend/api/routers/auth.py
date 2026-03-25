from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.deps import get_container
from backend.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from backend.application.use_cases.auth import (
    ChangePasswordData,
    LoginData,
    RegisterData,
    UpdateProfileData,
)
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    body: RegisterRequest,
    container: ApplicationContainer = Depends(get_container),
) -> UserResponse:
    user = container.register_user.execute(
        RegisterData(
            email=body.email,
            password=body.password,
            nickname=body.nickname,
        )
    )
    return UserResponse(
        id=int(user.id),
        email=user.email,
        nickname=user.nickname,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    pair = container.login_user.execute(
        LoginData(email=body.email, password=body.password)
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    pair = container.refresh_access_token.execute(body.refresh_token)
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshRequest,
    container: ApplicationContainer = Depends(get_container),
) -> None:
    container.logout_user.execute(body.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=int(user.id),
        email=user.email,
        nickname=user.nickname,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> None:
    try:
        container.change_password.execute(
            user, ChangePasswordData(
                current_password=body.current_password,
                new_password=body.new_password,
            )
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> UserResponse:
    updated = container.update_profile.execute(
        user, UpdateProfileData(nickname=body.nickname, password=body.password)
    )
    return UserResponse(
        id=int(updated.id),
        email=updated.email,
        nickname=updated.nickname,
        created_at=updated.created_at,
        last_login_at=updated.last_login_at,
    )
