# 视频生成API - /api/v1/generate

from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import uuid
from urllib.parse import urlparse

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
from app.services.content_moderation import content_moderation_service, ModerationLevel
from app.tasks.video_generation import submit_generation_task

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])


@router.post("", response_model=GenerationTaskSubmit, status_code=status.HTTP_202_ACCEPTED, summary="提交视频生成任务", tags=["generate"])
async def create_generation_task(
    task_data: GenerationTaskCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """提交新的视频生成任务
    
    **认证**: 需要 Bearer Token
    
    **请求体**:
    - **prompt**: 视频描述提示词（必填）
    - **negative_prompt**: 反向提示词（可选）
    - **duration**: 视频时长，5-30秒（必填）
    - **quality_mode**: 质量模式 - fast/balanced/premium（必填）
    - **aspect_ratio**: 宽高比 - 16:9/9:16/1:1（可选，默认16:9）
    
    **处理流程**:
    1. 内容审核（敏感词检测）
    2. 余额校验
    3. 智能路由（选择最优执行路径）
    4. 扣减Token
    5. 提交Celery异步任务
    
    **返回**: task_id 和预估完成时间
    """
    # 1. 内容审核 (Sprint 4: S4-F2)
    moderation_result = content_moderation_service.check_prompt(
        task_data.prompt,
        task_data.negative_prompt
    )
    if moderation_result.level == ModerationLevel.BLOCK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"内容审核未通过: {moderation_result.reason}"
        )

    # 验证image_url格式（如果提供）
    if task_data.image_url:
        try:
            parsed = urlparse(task_data.image_url)
            if parsed.scheme not in ('http', 'https'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="image_url必须使用http或https协议"
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_url格式无效"
            )
    
    # 2. 检查余额
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
    
    # 3. 确定执行路径
    execution_path, upstream_name = get_execution_path(
        task_data.quality_mode,
        task_data.duration
    )
    
    # 4. 计算Token消耗
    token_cost = calculate_cost_tokens(task_data.duration, task_data.quality_mode)

    # 5. 预留Token（立即扣除，但如果任务失败/取消会退款）
    current_user.token_balance -= token_cost
    await session.commit()

    # 6. 创建任务
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
        image_url=task_data.image_url,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # 7. 提交到Celery (异步执行)
    submit_generation_task(task.id)
    
    # 7. 返回预估时间
    estimated_time = get_estimated_time(task_data.quality_mode)
    
    return GenerationTaskSubmit(
        task_id=task.id,
        status="queued",
        estimated_time=estimated_time
    )


@router.get("/route/preview", summary="路由预览", tags=["generate"])
async def get_route_preview(
    mode: str = "balanced",
    duration: int = 5,
):
    """预览视频生成的路由信息（无需认证）
    
    **参数**:
    - **mode**: 质量模式 - fast/balanced/premium
    - **duration**: 视频时长（秒），5-60秒
    
    **返回**:
    - **execution_path**: 执行路径（comfyui_wan21/siliconflow_vidu/siliconflow_kling）
    - **channel_name**: 上游通道名称
    - **estimated_time**: 预估耗时（秒）
    - **quality_score**: 质量评分（1-10）
    - **token_cost**: Token消耗
    """
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


@router.get("/{task_id}", response_model=GenerationTaskResponse, summary="查询任务状态", tags=["generate"])
async def get_generation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """查询视频生成任务状态
    
    **认证**: 需要 Bearer Token
    
    **路径参数**:
    - **task_id**: 任务ID（UUID）
    
    **返回**:
    - **task_id**: 任务ID
    - **status**: 任务状态（queued/pending/processing/completed/failed/cancelled）
    - **progress**: 完成进度（0-100）
    - **video_url**: 视频URL（完成后可用）
    - **error**: 错误信息（失败时）
    - **estimated_time**: 预估剩余时间
    """
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


@router.delete("/{task_id}", summary="取消任务", tags=["generate"])
async def cancel_generation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """取消视频生成任务
    
    **认证**: 需要 Bearer Token
    
    **路径参数**:
    - **task_id**: 任务ID（UUID）
    
    **限制**: 仅当任务状态为 queued 或 pending 时可取消
    
    **处理流程**:
    1. 检查任务是否存在
    2. 检查任务状态是否可取消
    3. 退还Token到用户余额
    4. 更新任务状态为 cancelled
    
    **返回**: 确认消息和退款金额
    """
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

    if task.status not in ["queued", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status '{task.status}'. Only queued or pending tasks can be cancelled."
        )

    # ===== 退还Token到用户余额 =====
    refund_tokens = task.token_cost or 0
    if refund_tokens > 0:
        # 重新获取用户（避免缓存问题）
        user_result = await session.execute(
            select(User).where(User.id == current_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            user.token_balance += refund_tokens
            print(f"[Cancel Task] Refunded {refund_tokens} tokens to user {user.id}. New balance: {user.token_balance}")
    
    # 更新任务状态
    task.status = "cancelled"
    await session.commit()

    return {
        "message": "Task cancelled successfully",
        "task_id": task_id,
        "refund_tokens": refund_tokens,
        "current_balance": user.token_balance if refund_tokens > 0 else None
    }
