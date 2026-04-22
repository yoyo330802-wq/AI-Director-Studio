"""
漫AI - 套餐API
Sprint 5: S5-F3 完整套餐体系
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.database import Package, User, UserLevel
from app.models.schemas import PackageResponse, UserLevelEnum
from app.services.package import package_service
from app.services.cache import cache_service
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/packages", tags=["packages"])


@router.get(
    "",
    response_model=List[PackageResponse],
    summary="获取套餐列表",
    description="获取所有可用的订阅套餐",
    responses={
        200: {"description": "套餐列表"},
        401: {"description": "未授权"},
    }
)
async def list_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有可用套餐列表。
    
    **套餐类型**:
    - L1_TRIAL: 体验版
    - L2_CREATOR: 创作者月卡
    - L3_STUDIO: 工作室季卡
    - L4_ENTERPRISE: 企业年卡
    """
    packages = await package_service.get_all_packages(db)
    return packages


@router.get(
    "/recommended",
    response_model=List[PackageResponse],
    summary="获取推荐套餐",
    description="获取标记为推荐的套餐列表",
    responses={
        200: {"description": "推荐套餐列表"},
        401: {"description": "未授权"},
    }
)
async def get_recommended_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取推荐套餐。
    
    推荐套餐是平台主推的套餐，通常具有较好的性价比。
    """
    packages = await package_service.get_all_packages(db)
    return [p for p in packages if p.get("is_recommended", False)]


@router.get(
    "/{package_id}",
    response_model=PackageResponse,
    summary="获取套餐详情",
    description="根据ID获取单个套餐的详细信息",
    responses={
        200: {"description": "套餐详情"},
        401: {"description": "未授权"},
        404: {"description": "套餐不存在"},
    }
)
async def get_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个套餐详情。
    
    **返回内容**:
    - id: 套餐ID
    - name: 套餐名称
    - price: 价格（元）
    - video_minutes: 包含视频分钟数
    - duration_days: 有效期（天）
    - features: 功能列表
    """
    package = await package_service.get_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    return package


@router.get(
    "/level/{level}",
    response_model=List[PackageResponse],
    summary="按等级获取套餐",
    description="根据用户等级获取对应的套餐列表",
    responses={
        200: {"description": "套餐列表"},
        401: {"description": "未授权"},
    }
)
async def get_packages_by_level(
    level: UserLevelEnum,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    根据用户等级获取对应套餐。
    
    不同等级用户可购买不同级别的套餐。
    """
    level_enum = UserLevel[level.name]
    packages = await package_service.get_package_by_level(db, level_enum)
    return packages


@router.post("/activate/{package_id}")
async def activate_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开通套餐
    
    用户购买套餐后调用此接口激活
    """
    success = await package_service.activate_package_for_user(
        db, current_user.id, package_id
    )
    if not success:
        raise HTTPException(status_code=400, detail="开通失败，请检查套餐是否可用")
    
    return {"message": "套餐开通成功", "package_id": package_id}


@router.get("/quota/calculate")
async def calculate_quota(
    duration_seconds: int = Query(..., ge=5, le=60),
    quality_mode: str = Query("balanced", pattern="^(fast|balanced|premium)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """计算视频消耗配额
    
    返回指定时长和质量模式下的Token消耗
    """
    tokens = package_service.calculate_video_cost(duration_seconds, quality_mode)
    return {
        "duration_seconds": duration_seconds,
        "quality_mode": quality_mode,
        "tokens": tokens,
        "balance_sufficient": True  # 实际应检查用户余额
    }


@router.get("/quota/check")
async def check_quota(
    required_tokens: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查用户配额是否足够"""
    is_valid, message = package_service.validate_user_quota(
        current_user, required_tokens
    )
    
    remaining = (current_user.video_quota or 0) - (current_user.video_used or 0)
    
    return {
        "sufficient": is_valid,
        "message": message,
        "remaining": remaining,
        "required": required_tokens
    }


# ============ 管理接口 (需要管理员权限) ============

@router.post("/admin/init")
async def init_default_packages(
    db: Session = Depends(get_db)
):
    """初始化默认套餐(管理员)"""
    packages = await package_service.init_default_packages(db)
    return {
        "message": f"已初始化 {len(packages)} 个默认套餐",
        "packages": [{"id": p.id, "name": p.name} for p in packages]
    }


@router.post("/admin/cache/clear")
async def clear_package_cache():
    """清除套餐缓存(管理员)"""
    success = await cache_service.invalidate_packages()
    return {"message": "缓存已清除" if success else "缓存清除失败"}
