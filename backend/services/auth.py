from datetime import timedelta

from repositories.user import UserRepository
from schema.user import Token, UserCreate, UserLogin, UserRead
from services.exceptions import AppException
from services.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate) -> UserRead:
        # Check if user exists
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise AppException(
                status=400,
                message="A user with this email already exists.",
            )

        existing_username = await self.user_repo.get_by_username(user_in.username)
        if existing_username:
            raise AppException(
                status=400,
                message="This username is already taken.",
            )

        # Create user
        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_password

        new_user = await self.user_repo.create(**user_data)
        await self.user_repo.session.commit()
        return UserRead.model_validate(new_user)

    async def login(self, login_data: UserLogin) -> Token:
        user = await self.user_repo.get_by_username(login_data.username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise AppException(
                status=401,
                message="Incorrect username or password",
            )

        # Update online status
        await self.user_repo.update_online_status(user.id, True)
        await self.user_repo.session.commit()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, user=UserRead.model_validate(user))
