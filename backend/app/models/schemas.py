"""
漫AI - Pydantic数据模型
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ============ 用户相关 ============

class UserLevelEnum(str, Enum):
    """用户等级"""
    L1_TRIAL = "L1_TRIAL"
    L2_CREATOR = "L2_CREATOR"
    L3_STUDIO = "L3_STUDIO"
    L4_ENTERPRISE = "L4_ENTERPRISE"


class UserRegister(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    nickname: Optional[str] = None
    invite_code: Optional[str] = None  # 邀请码


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """用户更新"""
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    level: UserLevelEnum = UserLevelEnum.L1_TRIAL
    balance: float = 0.0
    total_balance: float = 0.0
    total_consumption: float = 0.0
    video_quota: int = 0
    video_used: int = 0
    is_vip: bool = False
    vip_expires_at: Optional[datetime] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 86400  # 秒


class BalanceResponse(BaseModel):
    """余额响应"""
    balance: float
    video_quota: int
    video_used: int
    video_remaining: int


# ============ 生成任务相关 ============

class GenerationMode(str, Enum):
    """生成模式"""
    FAST = "fast"           # 闪电模式 - Wan2.1-1.3B
    BALANCED = "balanced"   # 智能模式 - 智能路由
    PREMIUM = "premium"     # 专业模式 - Vidu/可灵


class GenerationRequest(BaseModel):
    """生成请求"""
    mode: GenerationMode = GenerationMode.BALANCED
    prompt: str = Field(..., min_length=1, max_length=500)
    negative_prompt: Optional[str] = None
    duration: Literal[5, 10] = 5
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    resolution: Literal["480p", "720p", "1080p"] = "720p"
    image_url: Optional[str] = None  # 参考图片URL
    callback_url: Optional[str] = None  # 回调URL


class GenerationResponse(BaseModel):
    """生成响应"""
    task_id: str
    task_no: str
    status: Literal["pending", "queued", "processing", "completed", "failed"]
    channel: str
    channel_name: str
    estimated_cost: float
    estimated_time: int  # 秒
    queue_position: int
    created_at: datetime


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    task_no: str
    status: Literal["pending", "queued", "processing", "completed", "failed"]
    progress: int = 0  # 0-100
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    started_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    """任务列表"""
    items: list[TaskStatus]
    total: int
    page: int
    page_size: int


# ============ 视频/作品相关 ============

class VideoResponse(BaseModel):
    """视频响应"""
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_public: bool = False
    is_featured: bool = False
    view_count: int = 0
    like_count: int = 0
    share_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoCreate(BaseModel):
    """视频创建"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    is_public: bool = False


class VideoUpdate(BaseModel):
    """视频更新"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


# ============ 计费相关 ============

class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0)
    payment_method: Literal["alipay", "wechat", "balance"] = "alipay"
    package_id: Optional[int] = None


class RechargeResponse(BaseModel):
    """充值响应"""
    order_id: str
    order_no: str
    amount: float
    payment_method: str
    qr_code: Optional[str] = None  # 支付二维码
    pay_url: Optional[str] = None  # 支付链接
    expired_at: datetime


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    amount: float
    actual_amount: float
    discount: float
    payment_method: Optional[str] = None
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    """套餐响应"""
    id: int
    name: str
    description: Optional[str] = None
    level: UserLevelEnum
    price: float
    original_price: Optional[float] = None
    video_minutes: int
    duration_days: int
    features: list[str] = []
    priority_queue: bool = False
    no_watermark: bool = False
    api_access: bool = False
    batch_generation: bool = False
    dedicated_support: bool = False
    is_active: bool = True
    is_recommended: bool = False
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """交易记录"""
    id: int
    transaction_no: str
    payment_method: str
    amount: float
    fee: float = 0.0
    net_amount: float
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ 路由相关 ============

class RouteDecision(BaseModel):
    """路由决策"""
    channel_id: int = 1
    channel: str
    channel_name: str
    mode: Optional[str] = "balanced"
    estimated_cost: float
    estimated_time: int
    quality_score: int
    queue_position: int
    reasoning: str = ""  # 路由理由


# ============ 模板相关 ============

class TemplateResponse(BaseModel):
    """模板响应"""
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    prompt_template: str
    negative_prompt_template: Optional[str] = None
    recommended_mode: Optional[str] = None
    recommended_duration: Optional[int] = None
    tags: list[str] = []
    usage_count: int = 0
    is_official: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ 通用响应 ============

class PageResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """消息响应"""
    message: str
    code: int = 200


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: int = 400
