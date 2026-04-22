"""
漫AI - 套餐管理服务
Sprint 5: S5-F3 完整套餐体系
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.database import Package, User, Order, OrderStatus, UserLevel
from app.services.cache import cache_service


class PackageService:
    """套餐服务"""
    
    # 默认套餐配置
    DEFAULT_PACKAGES = [
        {
            "name": "体验包",
            "description": "适合尝鲜体验，包含基础功能",
            "level": UserLevel.L1_TRIAL,
            "price": 39.0,
            "original_price": 59.0,
            "video_minutes": 10,
            "video_quota": 600,  # 10分钟=600秒
            "duration_days": 30,
            "features": ["基础视频生成", "社区模板", "720p输出"],
            "priority_queue": False,
            "no_watermark": False,
            "api_access": False,
            "batch_generation": False,
            "dedicated_support": False,
            "is_active": True,
            "is_recommended": False,
            "sort_order": 1,
        },
        {
            "name": "创作者月卡",
            "description": "适合内容创作者，优先队列+无水印",
            "level": UserLevel.L2_CREATOR,
            "price": 399.0,
            "original_price": 599.0,
            "video_minutes": 100,
            "video_quota": 6000,  # 100分钟=6000秒
            "duration_days": 30,
            "features": ["优先队列", "高级模板", "无水印输出", "1080p输出", "每月10次高清导出"],
            "priority_queue": True,
            "no_watermark": True,
            "api_access": False,
            "batch_generation": False,
            "dedicated_support": False,
            "is_active": True,
            "is_recommended": True,
            "sort_order": 2,
        },
        {
            "name": "工作室季卡",
            "description": "适合小型工作室，支持API+批量生成",
            "level": UserLevel.L3_STUDIO,
            "price": 1799.0,
            "original_price": 2599.0,
            "video_minutes": 500,
            "video_quota": 30000,  # 500分钟=30000秒
            "duration_days": 90,
            "features": ["API接入", "批量生成(最多50条/批)", "优先队列", "无水印输出", "4K输出", "专属客服"],
            "priority_queue": True,
            "no_watermark": True,
            "api_access": True,
            "batch_generation": True,
            "dedicated_support": True,
            "is_active": True,
            "is_recommended": False,
            "sort_order": 3,
        },
        {
            "name": "企业年卡",
            "description": "适合企业客户，SLA保障+私有部署",
            "level": UserLevel.L4_ENTERPRISE,
            "price": 9999.0,
            "original_price": 15999.0,
            "video_minutes": 3000,
            "video_quota": 180000,  # 3000分钟=180000秒
            "duration_days": 365,
            "features": ["SLA 99.5%保障", "私有部署选项", "API无限调用", "无限批量生成", "专属技术经理", "7x24支持", "定制开发"],
            "priority_queue": True,
            "no_watermark": True,
            "api_access": True,
            "batch_generation": True,
            "dedicated_support": True,
            "is_active": True,
            "is_recommended": False,
            "sort_order": 4,
        },
    ]
    
    async def get_all_packages(self, db: Session, use_cache: bool = True) -> List[dict]:
        """获取所有可用套餐"""
        # 尝试从缓存获取
        if use_cache:
            cached = await cache_service.get_cached_packages()
            if cached:
                return cached
        
        # 从数据库查询
        result = db.execute(
            select(Package).where(
                Package.is_active == True
            ).order_by(Package.sort_order)
        )
        packages = result.scalars().all()
        
        if not packages:
            # 使用默认套餐
            packages_data = self.DEFAULT_PACKAGES
        else:
            packages_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "level": p.level.value if hasattr(p.level, 'value') else str(p.level),
                    "price": p.price,
                    "original_price": p.original_price,
                    "video_minutes": p.video_minutes,
                    "video_quota": p.video_quota,
                    "duration_days": p.duration_days,
                    "features": p.features or [],
                    "priority_queue": p.priority_queue,
                    "no_watermark": p.no_watermark,
                    "api_access": p.api_access,
                    "batch_generation": p.batch_generation,
                    "dedicated_support": p.dedicated_support,
                    "is_active": p.is_active,
                    "is_recommended": p.is_recommended,
                    "sort_order": p.sort_order,
                }
                for p in packages
            ]
        
        # 缓存结果
        await cache_service.cache_packages(packages_data)
        
        return packages_data
    
    async def get_package_by_id(self, db: Session, package_id: int, use_cache: bool = True) -> Optional[dict]:
        """获取单个套餐"""
        # 尝试从缓存获取
        if use_cache:
            cached = await cache_service.get_cached_package(package_id)
            if cached:
                return cached
        
        # 从数据库查询
        result = db.execute(
            select(Package).where(
                and_(Package.id == package_id, Package.is_active == True)
            )
        )
        package = result.scalar_one_or_none()
        
        if not package:
            return None
        
        package_data = {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "level": package.level.value if hasattr(package.level, 'value') else str(package.level),
            "price": package.price,
            "original_price": package.original_price,
            "video_minutes": package.video_minutes,
            "video_quota": package.video_quota,
            "duration_days": package.duration_days,
            "features": package.features or [],
            "priority_queue": package.priority_queue,
            "no_watermark": package.no_watermark,
            "api_access": package.api_access,
            "batch_generation": package.batch_generation,
            "dedicated_support": package.dedicated_support,
            "is_active": package.is_active,
            "is_recommended": package.is_recommended,
            "sort_order": package.sort_order,
        }
        
        # 缓存结果
        await cache_service.cache_package(package_id, package_data)
        
        return package_data
    
    async def get_package_by_level(self, db: Session, level: UserLevel) -> List[dict]:
        """根据用户等级获取套餐"""
        result = db.execute(
            select(Package).where(
                and_(
                    Package.level == level,
                    Package.is_active == True
                )
            ).order_by(Package.sort_order)
        )
        packages = result.scalars().all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "level": p.level.value if hasattr(p.level, 'value') else str(p.level),
                "price": p.price,
                "video_minutes": p.video_minutes,
                "video_quota": p.video_quota,
                "duration_days": p.duration_days,
                "features": p.features or [],
            }
            for p in packages
        ]
    
    async def create_package(self, db: Session, package_data: dict) -> Package:
        """创建套餐"""
        package = Package(**package_data)
        db.add(package)
        db.commit()
        db.refresh(package)
        
        # 清除套餐缓存
        await cache_service.invalidate_packages()
        
        return package
    
    async def update_package(self, db: Session, package_id: int, package_data: dict) -> Optional[Package]:
        """更新套餐"""
        result = db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalar_one_or_none()
        
        if not package:
            return None
        
        for key, value in package_data.items():
            if hasattr(package, key):
                setattr(package, key, value)
        
        db.commit()
        db.refresh(package)
        
        # 清除套餐缓存
        await cache_service.invalidate_packages()
        
        return package
    
    async def activate_package_for_user(self, db: Session, user_id: int, package_id: int) -> bool:
        """为用户开通套餐
        
        1. 检查用户是否存在
        2. 检查套餐是否存在
        3. 更新用户VIP状态和视频配额
        4. 创建订单记录
        """
        # 获取用户
        result = db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        # 获取套餐
        result = db.execute(
            select(Package).where(
                and_(Package.id == package_id, Package.is_active == True)
            )
        )
        package = result.scalar_one_or_none()
        if not package:
            return False
        
        # 更新用户状态
        user.level = package.level
        user.is_vip = True
        user.vip_expires_at = datetime.utcnow() + timedelta(days=package.duration_days)
        user.video_quota = (user.video_quota or 0) + package.video_quota
        
        # 创建激活记录订单
        order = Order(
            user_id=user_id,
            package_id=package_id,
            amount=package.price,
            actual_amount=package.price,
            discount=0.0,
            status=OrderStatus.PAID,
            paid_at=datetime.utcnow(),
        )
        db.add(order)
        
        db.commit()
        
        # 清除用户缓存
        await cache_service.invalidate_user(user_id)
        
        return True
    
    def calculate_video_cost(self, duration_seconds: int, quality_mode: str) -> int:
        """计算视频消耗的Token
        
        Args:
            duration_seconds: 视频时长(秒)
            quality_mode: fast/balanced/premium
        
        Returns:
            消耗的Token数量
        """
        # 基础比率: 1秒 = 1 Token
        base_tokens = duration_seconds
        
        # 质量模式乘数
        multipliers = {
            "fast": 1.0,      # 基础消耗
            "balanced": 1.5,  # 1.5倍
            "premium": 2.5,  # 2.5倍
        }
        
        multiplier = multipliers.get(quality_mode, 1.0)
        return int(base_tokens * multiplier)
    
    def validate_user_quota(self, user: User, required_tokens: int) -> tuple[bool, str]:
        """验证用户配额是否足够
        
        Returns:
            (is_valid, error_message)
        """
        remaining = (user.video_quota or 0) - (user.video_used or 0)
        
        if remaining < required_tokens:
            return False, f"视频配额不足。需要: {required_tokens}秒，可用: {remaining}秒"
        
        if user.is_vip and user.vip_expires_at:
            if user.vip_expires_at < datetime.utcnow():
                return False, "VIP已过期，请续费"
        
        return True, ""
    
    async def record_video_usage(self, db: Session, user_id: int, seconds: int) -> bool:
        """记录视频使用量
        
        Returns:
            是否成功
        """
        result = db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        user.video_used = (user.video_used or 0) + seconds
        db.commit()
        
        # 清除用户缓存
        await cache_service.invalidate_user(user_id)
        
        return True
    
    async def init_default_packages(self, db: Session) -> List[Package]:
        """初始化默认套餐（如果不存在）"""
        existing = db.execute(select(Package).limit(1)).scalar_one_or_none()
        if existing:
            return []
        
        packages = []
        for pkg_data in self.DEFAULT_PACKAGES:
            package = Package(**pkg_data)
            db.add(package)
            packages.append(package)
        
        db.commit()
        
        # 清除套餐缓存
        await cache_service.invalidate_packages()
        
        return packages


# 全局套餐服务实例
package_service = PackageService()
