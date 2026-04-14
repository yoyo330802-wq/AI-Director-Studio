# 视频生成任务模型

import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class GenerationTaskBase(SQLModel):
    prompt: str
    duration: int  # 秒数
    quality_mode: str  # "cost" | "balanced" | "quality"
    aspect_ratio: str  # "16:9" | "9:16" | "1:1"


class GenerationTask(GenerationTaskBase, table=True):
    __tablename__ = "generation_tasks"

    id: str = Field(
        primary_key=True,
        default_factory=lambda: str(uuid.uuid4())
    )
    user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="queued")  # queued | processing | completed | failed
    progress: int = Field(default=0)  # 0-100
    video_url: Optional[str] = None
    error: Optional[str] = None
    token_cost: float  # 本次任务的Token消耗
    execution_path: str = Field(default="")  # comfyui_wan21 | siliconflow_vidu | siliconflow_kling
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationTaskCreate(SQLModel):
    prompt: str
    duration: int = Field(ge=5, le=30)  # 5-30秒
    quality_mode: str = Field(default="balanced")  # cost | balanced | quality
    aspect_ratio: str = Field(default="16:9")  # 16:9 | 9:16 | 1:1


class GenerationTaskResponse(SQLModel):
    task_id: str
    status: str
    progress: int
    video_url: Optional[str] = None
    error: Optional[str] = None
    estimated_time: int = 0  # 预估完成时间(秒)

    class Config:
        from_attributes = True


class GenerationTaskSubmit(SQLModel):
    task_id: str
    status: str = "queued"
    estimated_time: int
