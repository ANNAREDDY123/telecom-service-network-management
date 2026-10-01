from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    AccountStatusResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.utils.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Authorization"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    access_token, refresh_token = service.login(data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    access_token = service.refresh_access_token(
        data.refresh_token
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=data.refresh_token,
    )


@router.post("/logout")
def logout(
    data: LogoutRequest,
):
    # Refresh-token rotation/revocation storage will be
    # extended with the session/token model in the security
    # hardening stage.
    return {
        "message": "Logout request accepted",
        "token_revocation_ready": True,
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post("/password-reset/request")
def password_reset_request(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    reset_token = service.request_password_reset(
        data.email
    )

    # In a production deployment, this token would be
    # delivered through email/SMS rather than returned.
    # Returning it during this development stage allows
    # Swagger/Postman testing.

    if reset_token is None:
        return {
            "message": "If the account exists, a reset request has been created."
        }

    return {
        "message": "Password reset request created",
        "reset_token": reset_token,
    }


@router.post("/password-reset/confirm")
def password_reset_confirm(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    service.reset_password(data)

    return {
        "message": "Password has been reset successfully"
    }


@router.patch(
    "/account/{user_id}/activate",
    response_model=AccountStatusResponse,
)
def activate_account(
    user_id: int,
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    user = service.set_account_status(
        user_id,
        True,
    )

    return AccountStatusResponse(
        message="User account activated successfully",
        user=user,
    )


@router.patch(
    "/account/{user_id}/deactivate",
    response_model=AccountStatusResponse,
)
def deactivate_account(
    user_id: int,
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    user = service.set_account_status(
        user_id,
        False,
    )

    return AccountStatusResponse(
        message="User account deactivated successfully",
        user=user,
    )