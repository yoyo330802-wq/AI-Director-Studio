# 用户API - /api/v1/users

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User, UserResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息", tags=["users"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的详细信息
    
    需要 Authorization: Bearer <token> 认证
    
    返回用户ID、邮箱、名称、Token余额、视频配额等信息
    """
    return current_user
