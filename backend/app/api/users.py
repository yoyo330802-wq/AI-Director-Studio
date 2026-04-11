"""
漫AI - 用户API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import redis
import json

from app.config import settings
from app.models.schemas import UserRegister, UserLogin, UserResponse, Token, BalanceResponse

router = APIRouter()

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/login")

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user(username: str) -> Optional[dict]:
    """获取用户"""
    user_data = redis_client.get(f"user:{username}")
    if user_data:
        return json.loads(user_data)
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """通过ID获取用户"""
    user_data = redis_client.get(f"user:id:{user_id}")
    if user_data:
        return json.loads(user_data)
    return None


@router.post("/register", response_model=UserResponse)
def register(user: UserRegister):
    """用户注册"""
    # 检查用户名是否存在
    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    user_id = redis_client.incr("user_id_counter")
    user_data = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "balance": 0.0,
        "level": "free",
        "created_at": datetime.utcnow().isoformat(),
        "total_spent": 0.0,
        "total_generated": 0
    }
    
    # 存储
    redis_client.set(f"user:{user.username}", json.dumps(user_data))
    redis_client.set(f"user:id:{user_id}", json.dumps(user_data))
    
    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email,
        balance=0.0,
        level="free",
        created_at=datetime.utcnow()
    )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    user = get_user(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]}
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户信息"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的token")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        balance=user["balance"],
        level=user["level"],
        created_at=datetime.fromisoformat(user["created_at"])
    )


@router.get("/balance", response_model=BalanceResponse)
def get_balance(token: str = Depends(oauth2_scheme)):
    """获取用户余额"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return BalanceResponse(
        balance=user["balance"],
        total_spent=user.get("total_spent", 0.0),
        total_generated=user.get("total_generated", 0)
    )
