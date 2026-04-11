"""
漫AI - Pydantic数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ============ 用户相关 ============

class UserRegister(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9-.]+$")
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    balance: float = 0.0
    level: Literal["free", "basic", "pro", "enterprise"] = "free"
    created_at: datetime


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


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
    status: Literal["pending", "processing", "completed", "failed"]
    channel: str
    channel_name: str
    estimated_cost: float
    estimated_time: int  # 秒
    queue_position: int
    created_at: datetime


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = 0  # 0-100
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    completed_at: Optional[datetime] = None


# ============ 计费相关 ============

class BalanceResponse(BaseModel):
    """余额响应"""
    balance: float
    total_spent: float = 0.0
    total_generated: int = 0


class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0)
    payment_method: Literal["alipay", "wechat"] = "alipay"


class RechargeResponse(BaseModel):
    """充值响应"""
    order_id: str
    amount: float
    qr_code: Optional[str] = None  # 支付二维码


class Transaction(BaseModel):
    """交易记录"""
    id: int
    type: Literal["recharge", "deduct", "refund"]
    amount: float
    balance_after: float
    description: str
    created_at: datetime


# ============ 路由相关 ============

class RouteDecision(BaseModel):
    """路由决策"""
    channel: str
    channel_name: str
    estimated_cost: float
    estimated_time: int
    quality_score: int
    queue_position: int
    reasoning: str  # 路由理由
