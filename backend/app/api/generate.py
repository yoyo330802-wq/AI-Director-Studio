# 视频生成API - /api/v1/generate

from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import uuid

from app.database import get_session
from app.models.user import User
from app.models.task import GenerationTask, GenerationTaskCreate, GenerationTaskResponse, GenerationTaskSubmit
from app.core.security import get_current_user
from app.services.billing import (
    calculate_cost_tokens, 
    validate_balance, 
    get_estimated_time,
    PRICING
)
from app.services.router import get_execution_path
from app.tasks.video_generation import submit_generation_task

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])


@router.post("", response_model=GenerationTaskSubmit, status_code=status.HTTP_202_ACCEPTED)
async def create_generation_task(
    task_data: GenerationTaskCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """提交视频生成任务"""
    # 1. 检查余额
    is_valid, error_msg = validate_balance(
        current_user.token_balance,
        task_data.duration,
        task_data.quality_mode
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=error_msg
        )
    
    # 2. 确定执行路径
    execution_path, upstream_name = get_execution_path(
        task_data.quality_mode,
        task_data.duration
    )
    
    # 3. 计算Token消耗
    token_cost = calculate_cost_tokens(task_data.duration, task_data.quality_mode)
    
    # 4. 创建任务
    task = GenerationTask(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        prompt=task_data.prompt,
        duration=task_data.duration,
        quality_mode=task_data.quality_mode,
        aspect_ratio=task_data.aspect_ratio,
        status="queued",
        progress=0,
        token_cost=token_cost,
        execution_path=execution_path,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # 5. 提交到Celery (异步执行)
    submit_generation_task(task.id)
    
    # 6. 返回预估时间
    estimated_time = get_estimated_time(task_data.quality_mode)
    
    return GenerationTaskSubmit(
        task_id=task.id,
        status="queued",
        estimated_time=estimated_time
    )


@router.get("/route/preview")
async def get_route_preview(
    mode: str = "balanced",
    duration: int = 5,
):
    """路由预览 - 显示将使用的模型和预估信息"""
    execution_path, upstream_name = get_execution_path(mode, duration)
    
    # 预估时间(秒)
    time_map = {"comfyui_wan21": 30, "siliconflow_vidu": 60, "siliconflow_kling": 90}
    estimated_time = time_map.get(execution_path, 45)
    
    # 质量评分(1-10)
    quality_map = {"comfyui_wan21": 7, "siliconflow_vidu": 8, "siliconflow_kling": 9}
    quality_score = quality_map.get(execution_path, 7)
    
    # 成本
    token_cost = calculate_cost_tokens(duration, mode)
    
    return {
        "execution_path": execution_path,
        "channel_name": upstream_name,
        "estimated_time": estimated_time,
        "quality_score": quality_score,
        "token_cost": token_cost,
    }


@router.get("/{task_id}", response_model=GenerationTaskResponse)
async def get_generation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """查询任务状态"""
    result = await session.execute(
        select(GenerationTask).where(
            GenerationTask.id == task_id,
            GenerationTask.user_id == current_user.id
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return GenerationTaskResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        video_url=task.video_url,
        error=task.error,
        estimated_time=get_estimated_time(task.quality_mode)
    )
