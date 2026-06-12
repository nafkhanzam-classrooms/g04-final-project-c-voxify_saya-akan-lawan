from datetime import timedelta
from repositories.user import UserRepository
from schema.user import UserCreate, UserLogin, Token, UserRead
from services.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.exceptions import AppException


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate) -> UserRead:
        # Check if user exists
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise AppException("A user with this email already exists.", 400)
        
        existing_username = await self.user_repo.get_by_username(user_in.username)
        if existing_username:
            raise AppException("This username is already taken.", 400)

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
            raise AppException("Incorrect username or password", 401)

        # Update online status
        await self.user_repo.update_online_status(user.id, True)
        await self.user_repo.session.commit()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, user=UserRead.model_validate(user))
