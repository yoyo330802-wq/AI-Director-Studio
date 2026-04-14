"""
漫AI - 数据库模型
SQLAlchemy ORM 模型定义
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class UserLevel(enum.Enum):
    """用户等级"""
    L1_TRIAL = "L1_TRIAL"      # 尝鲜用户
    L2_CREATOR = "L2_CREATOR"  # 内容创作者
    L3_STUDIO = "L3_STUDIO"     # 小型工作室
    L4_ENTERPRISE = "L4_ENTERPRISE"  # 企业客户


class TaskStatus(enum.Enum):
    """任务状态"""
    PENDING = "PENDING"        # 待处理
    QUEUED = "QUEUED"          # 排队中
    PROCESSING = "PROCESSING"   # 处理中
    COMPLETED = "COMPLETED"     # 完成
    FAILED = "FAILED"          # 失败
    CANCELLED = "CANCELLED"    # 已取消


class OrderStatus(enum.Enum):
    """订单状态"""
    PENDING = "PENDING"        # 待支付
    PAID = "PAID"              # 已支付
    REFUNDED = "REFUNDED"      # 已退款
    CANCELLED = "CANCELLED"    # 已取消


class PaymentMethod(enum.Enum):
    """支付方式"""
    ALIPAY = "ALIPAY"          # 支付宝
    WECHAT = "WECHAT"          # 微信
    BALANCE = "BALANCE"         # 余额


class ChannelType(enum.Enum):
    """上游渠道"""
    WAN21_1_3B = "WAN21_1_3B"
    WAN21_14B = "WAN21_14B"
    VIDU = "VIDU"
    KLING = "KLING"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基础信息
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    nickname = Column(String(100), nullable=True)
    avatar = Column(String(500), nullable=True)
    level = Column(Enum(UserLevel), default=UserLevel.L1_TRIAL)
    
    # 余额
    balance = Column(Float, default=0.0)           # 余额(元)
    total_balance = Column(Float, default=0.0)    # 累计充值
    total_consumption = Column(Float, default=0.0)  # 累计消费
    
    # 视频额度(秒)
    video_quota = Column(Integer, default=0)      # 赠送额度
    video_used = Column(Integer, default=0)       # 已使用
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)   # 是否验证
    is_vip = Column(Boolean, default=False)        # VIP
    
    # VIP过期时间
    vip_expires_at = Column(DateTime, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # 第三方登录
    oauth_provider = Column(String(50), nullable=True)  # google, github, wechat
    oauth_id = Column(String(255), nullable=True)
    
    # 关系
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, index=True, nullable=False)  # 订单号
    
    # 用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="orders")
    
    # 套餐信息
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)
    package = relationship("Package", back_populates="orders")
    
    # 订单金额
    amount = Column(Float, nullable=False)        # 应付金额
    actual_amount = Column(Float, nullable=False) # 实付金额
    discount = Column(Float, default=0.0)         # 优惠金额
    
    # 支付信息
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_no = Column(String(128), nullable=True)  # 第三方支付流水号
    paid_at = Column(DateTime, nullable=True)
    
    # 状态
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # 备注
    remark = Column(Text, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime, nullable=True)  # 过期时间(未支付订单)
    
    # 关系
    transactions = relationship("PaymentTransaction", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.order_no}>"


class Package(Base):
    """套餐表"""
    __tablename__ = "packages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 套餐信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Enum(UserLevel), nullable=False)
    
    # 价格
    price = Column(Float, nullable=False)          # 月费
    original_price = Column(Float, nullable=True)  # 原价
    
    # 权益
    video_minutes = Column(Integer, nullable=False)  # 视频时长(分钟)
    video_quota = Column(Integer, nullable=False)   # 实际配额(秒)
    
    # 有效期
    duration_days = Column(Integer, default=30)    # 有效期(天)
    
    # 特性
    features = Column(JSON, default=list)         # 功能列表
    priority_queue = Column(Boolean, default=False)  # 优先队列
    no_watermark = Column(Boolean, default=False)   # 无水印
    api_access = Column(Boolean, default=False)     # API接入
    batch_generation = Column(Boolean, default=False)  # 批量生成
    dedicated_support = Column(Boolean, default=False)  # 专属客服
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)  # 推荐
    sort_order = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    orders = relationship("Order", back_populates="package")
    
    def __repr__(self):
        return f"<Package {self.name}>"


class Task(Base):
    """生成任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_no = Column(String(64), unique=True, index=True, nullable=False)
    
    # 用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="tasks")
    
    # 任务参数
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    mode = Column(String(50), nullable=False)       # fast/balanced/premium
    duration = Column(Integer, default=5)         # 时长(秒)
    resolution = Column(String(20), default="720p")
    
    # 路由决策
    channel = Column(Enum(ChannelType), nullable=True)
    channel_name = Column(String(50), nullable=True)
    
    # 状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    progress = Column(Integer, default=0)          # 进度 0-100
    
    # 费用
    estimated_cost = Column(Float, default=0.0)    # 预估成本
    actual_cost = Column(Float, default=0.0)      # 实际成本
    billable_cost = Column(Float, default=0.0)    # 扣费金额
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # 第三方信息
    external_task_id = Column(String(128), nullable=True)  # 上游任务ID
    
    # 回调信息
    callback_url = Column(String(500), nullable=True)
    callback_retries = Column(Integer, default=0)
    callback_at = Column(DateTime, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # 关系
    video = relationship("Video", back_populates="task", uselist=False)
    
    def __repr__(self):
        return f"<Task {self.task_no}>"


class Video(Base):
    """视频作品表"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="videos")
    
    # 任务
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    task = relationship("Task", back_populates="video")
    
    # 视频信息
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    
    # 文件信息
    video_url = Column(String(500), nullable=True)     # 视频URL
    video_path = Column(String(500), nullable=True)    # 本地路径
    cover_url = Column(String(500), nullable=True)     # 封面URL
    thumbnail_url = Column(String(500), nullable=True)  # 缩略图
    
    # 文件大小
    file_size = Column(Integer, nullable=True)         # 字节
    duration = Column(Integer, nullable=True)           # 秒
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    
    # 标签/分类
    tags = Column(JSON, default=list)
    category = Column(String(50), nullable=True)
    
    # 公开设置
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)      # 精选
    is_ai_recommended = Column(Boolean, default=False) # AI推荐
    
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_videos_user_created', user_id, created_at.desc()),
        Index('idx_videos_public_created', is_public, created_at.desc()),
    )
    
    def __repr__(self):
        return f"<Video {self.id} - {self.title}>"


class PaymentTransaction(Base):
    """支付交易记录"""
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 订单
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    order = relationship("Order", back_populates="transactions")
    
    # 交易信息
    transaction_no = Column(String(128), unique=True, index=True)  # 交易流水号
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # 金额
    amount = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)              # 手续费
    net_amount = Column(Float, nullable=False)    # 实收
    
    # 第三方信息
    third_party_transaction_id = Column(String(128), nullable=True)
    third_party_order_id = Column(String(128), nullable=True)
    
    # 状态
    status = Column(String(20), default="pending")  # pending/success/failed
    error_message = Column(Text, nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Transaction {self.transaction_no}>"


class ChannelConfig(Base):
    """上游渠道配置"""
    __tablename__ = "channel_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 渠道信息
    channel_type = Column(Enum(ChannelType), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    
    # 配置
    api_base_url = Column(String(500), nullable=True)
    api_key = Column(String(255), nullable=True)
    is_enabled = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # 成本
    cost_per_second = Column(Float, default=0.0)
    
    # 权重
    weight = Column(Integer, default=100)          # 路由权重
    min_quality_score = Column(Integer, default=0)  # 最低质量分
    
    # 限制
    max_queue_size = Column(Integer, default=100)
    max_concurrent = Column(Integer, default=10)
    timeout_seconds = Column(Integer, default=120)
    
    # 统计
    total_requests = Column(Integer, default=0)
    success_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelConfig {self.name}>"


class SystemConfig(Base):
    """系统配置"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string/int/float/json/bool
    
    description = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False)      # 是否公开
    is_system = Column(Boolean, default=False)      # 是否系统级
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig {self.key}>"


class VideoTemplate(Base):
    """提示词模板"""
    __tablename__ = "video_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 模板信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    
    # 模板内容
    prompt_template = Column(Text, nullable=False)
    negative_prompt_template = Column(Text, nullable=True)
    
    # 推荐参数
    recommended_mode = Column(String(20), nullable=True)
    recommended_duration = Column(Integer, nullable=True)
    recommended_resolution = Column(String(20), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_official = Column(Boolean, default=False)     # 官方模板
    usage_count = Column(Integer, default=0)
    
    # 标签
    tags = Column(JSON, default=list)
    
    # 作者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<VideoTemplate {self.name}>"


# 创建所有表的函数
def create_all_tables(engine):
    """创建所有表"""
    Base.metadata.create_all(bind=engine)


# 导入后确保模型被注册
from app.models import schemas  # noqa
