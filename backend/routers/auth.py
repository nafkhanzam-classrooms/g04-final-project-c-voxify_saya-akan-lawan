from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from routers.deps import get_user_repository, get_current_user
from repositories.user import UserRepository
from services.auth import AuthService
from schema.user import UserCreate, UserRead, Token, UserLogin
from schema.base import BaseResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_auth_service(user_repo: Annotated[UserRepository, Depends(get_user_repository)]) -> AuthService:
    return AuthService(user_repo)

@router.post("/register", response_model=BaseResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    user = await auth_service.register(user_in)
    return BaseResponse(data=user, message="User registered successfully")

@router.post("/login", response_model=BaseResponse[Token])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    # OAuth2PasswordRequestForm uses 'username' and 'password'
    login_data = UserLogin(username=form_data.username, password=form_data.password)
    token = await auth_service.login(login_data)
    return BaseResponse(data=token, message="Login successful")

@router.get("/me", response_model=BaseResponse[UserRead])
async def get_me(current_user: Annotated[UserRead, Depends(get_current_user)]):
    return BaseResponse(data=current_user)
