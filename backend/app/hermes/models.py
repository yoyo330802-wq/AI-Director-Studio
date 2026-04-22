"""
Hermes - 数据模型
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Literal, Any
from sqlmodel import SQLModel, Field


class HermesTaskStatus(str, Enum):
    """Hermes任务状态"""
    NEW = "new"                    # 新创建
    IN_REVIEW = "in_review"        # 审核中（路由判定）
    ASSIGNED = "assigned"          # 已分配给Agent
    IN_PROGRESS = "in_progress"    # 执行中
    QUEUED = "queued"              # 队列等待（Agent全忙）
    DELIVERED = "delivered"       # 已交付待确认
    COMPLETED = "completed"        # 已完成
    FAILED = "failed"              # 执行失败
    CANCELLED = "cancelled"       # 已取消


class HermesEventType(str, Enum):
    """Hermes事件类型"""
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    SCORE_UPDATED = "score_updated"
    AGENT_MESSAGE = "agent_message"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR = "error"


class HermesTask(SQLModel, table=True):
    """Hermes任务模型"""
    __tablename__ = "hermes_tasks"

    id: str = Field(
        primary_key=True,
        default_factory=lambda: str(uuid.uuid4())
    )
    user_id: int = Field(foreign_key="users.id", index=True, description="所属用户ID")
    command: str = Field(description="用户原始指令")
    agent_type: str = Field(description="Agent类型")
    status: str = Field(
        default="new",
        description="当前状态"
    )
    current_phase: Optional[int] = Field(
        default=None,
        description="当前GAN phase (0-8)"
    )
    overall_progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="总体进度 0-100"
    )
    gan_sprint: str = Field(
        default="S1",
        description="当前Sprint编号"
    )
    result: Optional[str] = Field(
        default=None,
        description="执行结果(JSON字符串)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    scores: Optional[str] = Field(
        default=None,
        description="GAN评分(JSON字符串)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True

    def set_status(self, status_enum: HermesTaskStatus):
        """设置状态"""
        self.status = status_enum.value

    def set_result(self, data: dict):
        """设置结果数据"""
        import json
        self.result = json.dumps(data, ensure_ascii=False)

    def get_result(self) -> Optional[dict]:
        """获取结果数据"""
        import json
        if self.result:
            return json.loads(self.result)
        return None

    def set_scores(self, scores: dict):
        """设置评分数据"""
        import json
        self.scores = json.dumps(scores, ensure_ascii=False)

    def get_scores(self) -> Optional[dict]:
        """获取评分数据"""
        import json
        if self.scores:
            return json.loads(self.scores)
        return None


class HermesEvent(SQLModel):
    """Hermes事件模型（不持久化）"""
    event: HermesEventType
    task_id: str
    phase: Optional[int] = None
    progress: Optional[int] = None
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class HermesTaskCreate(SQLModel):
    """创建任务请求"""
    command: str = Field(description="用户指令")
    sprint: Optional[str] = Field(default="S1", description="Sprint编号")

    class Config:
        from_attributes = True


class HermesTaskResponse(SQLModel):
    """任务响应"""
    id: str
    command: str
    agent_type: str
    status: str
    current_phase: Optional[int] = None
    overall_progress: int
    scores: Optional[dict] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HermesTaskListResponse(SQLModel):
    """任务列表响应"""
    items: list[HermesTaskResponse]
    total: int
    page: int
    limit: int

    class Config:
        from_attributes = True
