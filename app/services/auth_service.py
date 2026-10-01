from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    UserRegister,
)


class AuthService:

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register(self, data: UserRegister) -> User:
        existing_user = self.repository.get_by_email(
            data.email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = User(
            full_name=data.full_name.strip(),
            email=data.email.lower(),
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=True,
            is_verified=False,
        )

        return self.repository.create(user)

    def login(self, data: LoginRequest) -> tuple[str, str]:
        user = self.repository.get_by_email(
            data.email
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            data.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )

        refresh_token = create_refresh_token(
            subject=str(user.id)
        )

        return access_token, refresh_token

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> str:

        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = self.repository.get_by_id(int(user_id))

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or unavailable",
            )

        return create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )

    def request_password_reset(
        self,
        email: str,
    ) -> str | None:

        user = self.repository.get_by_email(email)

        if not user:
            return None

        return create_password_reset_token(
            subject=str(user.id)
        )

    def reset_password(
        self,
        data: PasswordResetConfirm,
    ) -> User:

        try:
            payload = decode_token(data.token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )

        user = self.repository.get_by_id(int(user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.hashed_password = hash_password(
            data.new_password
        )

        return self.repository.update(user)

    def set_account_status(
        self,
        user_id: int,
        is_active: bool,
    ) -> User:

        user = self.repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = is_active

        return self.repository.update(user)