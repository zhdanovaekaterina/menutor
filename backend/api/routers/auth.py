from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import get_current_user
from backend.api.deps import get_container
from backend.api.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from backend.application.use_cases.auth import LoginData, RegisterData
from backend.composition_root import ApplicationContainer
from backend.domain.entities.user import User
from backend.domain.exceptions import AuthenticationError, UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    body: RegisterRequest,
    container: ApplicationContainer = Depends(get_container),
) -> UserResponse:
    try:
        user = container.register_user.execute(
            RegisterData(
                email=body.email,
                password=body.password,
                nickname=body.nickname,
            )
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return UserResponse(
        id=int(user.id),
        email=user.email,
        nickname=user.nickname,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    try:
        pair = container.login_user.execute(
            LoginData(email=body.email, password=body.password)
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    container: ApplicationContainer = Depends(get_container),
) -> TokenResponse:
    try:
        pair = container.refresh_access_token.execute(body.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
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
    )


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    container: ApplicationContainer = Depends(get_container),
) -> UserResponse:
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.password is not None:
        user.hashed_password = container.password_hasher.hash(body.password)
    updated = container.user_repo.save(user)
    return UserResponse(
        id=int(updated.id),
        email=updated.email,
        nickname=updated.nickname,
        created_at=updated.created_at,
    )
