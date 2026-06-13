from datetime import timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError

from repositories.user import UserRepository
from schema.user import UserCreate, UserLogin, UserRead, Token
from services.security import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    verify_password,
    create_access_token,
)
from utils.exceptions import AppException


async def get_user_from_token(token: str) -> Optional[UUID]:
    """Decode a JWT and return the user_id, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return UUID(str(user_id))
    except (JWTError, ValueError):
        return None
    return None


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate) -> UserRead:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise AppException("A user with this email already exists.", 400)

        existing_username = await self.user_repo.get_by_username(user_in.username)
        if existing_username:
            raise AppException("This username is already taken.", 400)

        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password

        new_user = await self.user_repo.create(**user_data)
        await self.user_repo.session.commit()
        return UserRead.model_validate(new_user)

    async def login(self, login_data: UserLogin) -> Token:
        user = await self.user_repo.get_by_username(login_data.username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise AppException("Incorrect username or password", 401)

        # Update online status
        await self.user_repo.update_online_status(user.id, True)
        await self.user_repo.session.commit()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, user=UserRead.model_validate(user))

    async def validate_token(self, token: str) -> Token:
        """Validate an existing JWT and restore the user session.
        Marks the user as online in the database."""
        if not token:
            raise AppException("No token provided", 401)

        user_id = await get_user_from_token(token)
        if not user_id:
            raise AppException("Invalid or expired token", 401)

        user = await self.user_repo.get(user_id)
        if not user:
            raise AppException("User not found", 404)

        # Mark user online (same as login)
        await self.user_repo.update_online_status(user.id, True)
        await self.user_repo.session.commit()

        # Re-fetch so is_online=True is reflected
        user = await self.user_repo.get(user_id)
        return Token(access_token=token, user=UserRead.model_validate(user))

    async def set_offline(self, user_id: UUID) -> None:
        """Mark a user as offline in the database."""
        await self.user_repo.update_online_status(user_id, False)
        await self.user_repo.session.commit()
