# 认证API - /api/v1/auth

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User, UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.services.billing import DEFAULT_INITIAL_TOKENS

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """用户注册"""
    # 检查邮箱是否已存在
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # 创建用户
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hash_password(user_data.password),
        token_balance=DEFAULT_INITIAL_TOKENS,  # 初始100 Token
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """用户登录"""
    result = await session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    access_token = create_access_token(user.id)
    
    return TokenResponse(access_token=access_token)
