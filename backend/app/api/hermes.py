"""
漫AI - Hermes API

提供Hermes多Agent协作编排的REST API和WebSocket接口
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session, AsyncSessionLocal
from app.core.security import get_current_user, decode_token
from app.hermes.models import (
    HermesTask, HermesTaskStatus, HermesTaskCreate, HermesTaskResponse,
    HermesTaskListResponse, HermesEvent, HermesEventType
)
from app.hermes.state import hermes_state
from app.hermes.router import task_router
from app.hermes.gan_runner import GANRunner
from app.hermes.executor import get_executor
from app.hermes.evolution import evolution_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hermes", tags=["hermes"])


def _task_to_response(task: HermesTask) -> HermesTaskResponse:
    """转换任务模型到响应模型"""
    return HermesTaskResponse(
        id=task.id,
        command=task.command,
        agent_type=task.agent_type,
        status=task.status.value,
        current_phase=task.current_phase,
        overall_progress=task.overall_progress,
        scores=task.get_scores() if task.scores else None,
        result=task.get_result() if task.result else None,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


# ============ REST API ============

@router.post("/tasks", response_model=HermesTaskResponse, summary="提交Hermes任务")
async def create_hermes_task(
    request: HermesTaskCreate,
    current_user = Depends(get_current_user),
):
    """
    提交新的Hermes任务

    Hermes会自动:
    1. 分析指令，路由到合适的Agent类型
    2. Engineering任务走GAN Phase 0-8流程
    3. 其他任务直接执行
    """
    # 路由判定
    agent_type = task_router.route(request.command)
    sprint = task_router.get_sprint_from_command(request.command)

    # 创建任务
    task = await hermes_state.create_task(
        command=request.command,
        agent_type=agent_type,
        sprint=sprint,
        user_id=current_user.id,
    )

    logger.info(f"Hermes task created: {task.id}, agent_type={agent_type}, sprint={sprint}")

    # 异步执行任务
    asyncio.create_task(_execute_hermes_task(task.id))

    return _task_to_response(task)


async def _execute_hermes_task(task_id: str):
    """异步执行Hermes任务"""
    task = await hermes_state.get_task(task_id)
    if not task:
        return

    try:
        # 更新状态为进行中
        await hermes_state.update_task_status(
            task_id,
            HermesTaskStatus.IN_PROGRESS,
            progress=0
        )

        # 发布事件
        event = HermesEvent(
            event=HermesEventType.TASK_ASSIGNED,
            task_id=task_id,
            data={"agent_type": task.agent_type}
        )
        await hermes_state.publish_event(task_id, event)

        if task.agent_type == "engineer":
            # Engineering任务走GAN流程
            await _run_gan_workflow(task)
        else:
            # 其他任务直接执行
            await _run_simple_task(task)

        # 标记完成
        await hermes_state.update_task_status(
            task_id,
            HermesTaskStatus.COMPLETED,
            progress=100
        )

        # 发布完成事件
        event = HermesEvent(
            event=HermesEventType.TASK_COMPLETED,
            task_id=task_id,
            progress=100,
            data={"status": "completed"}
        )
        await hermes_state.publish_event(task_id, event)

    except Exception as e:
        logger.error(f"Task {task_id} execution failed: {e}")

        await hermes_state.update_task_status(
            task_id,
            HermesTaskStatus.FAILED,
            error_message=str(e)
        )

        event = HermesEvent(
            event=HermesEventType.TASK_FAILED,
            task_id=task_id,
            data={"error": str(e)}
        )
        await hermes_state.publish_event(task_id, event)


async def _run_gan_workflow(task: HermesTask):
    """运行GAN工作流"""
    workspace = str(Path(__file__).parent.parent.parent.parent)

    runner = GANRunner(workspace=workspace, sprint=task.gan_sprint)

    def on_progress(phase: int, progress: int, message: str):
        """进度回调"""
        asyncio.create_task(_update_progress(task.id, phase, progress, message))

    runner.set_progress_callback(on_progress)

    # 执行完整流程
    final_state = await runner.run_full(auto=True)

    # 更新结果
    await hermes_state.update_task_result(
        task.id,
        result={
            "completed_phases": final_state.completed_phases,
            "final_status": final_state.status,
        },
        scores=final_state.scores,
    )

    # 记录到进化引擎
    await evolution_engine.log_execution(
        task_id=task.id,
        phase=8,
        agent_type="engineer",
        input_text=task.command,
        output_text=json.dumps(final_state.to_dict(), ensure_ascii=False),
        score=final_state.scores.get(f"Sprint {task.gan_sprint}", 0) if final_state.scores else None,
        duration_ms=0,
    )


async def _run_simple_task(task: HermesTask):
    """运行简单任务（researcher/creator）"""
    executor = get_executor(workspace=str(Path(__file__).parent.parent.parent.parent))

    agent_type = task.agent_type

    # 发布开始事件
    event = HermesEvent(
        event=HermesEventType.PHASE_STARTED,
        task_id=task.id,
        phase=0,
        progress=10,
        data={"agent_type": agent_type}
    )
    await hermes_state.publish_event(task.id, event)

    # 执行agent
    result = await executor.execute_agent(
        agent_type=agent_type,
        command=task.command,
        on_output=lambda output: asyncio.create_task(_publish_output(task.id, output)),
    )

    # 更新进度
    await _update_progress(task.id, 0, 100, "Completed")

    # 记录结果
    await hermes_state.update_task_result(
        task.id,
        result={
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        },
    )

    # 记录到进化引擎
    await evolution_engine.log_execution(
        task_id=task.id,
        phase=0,
        agent_type=agent_type,
        input_text=task.command,
        output_text=result.get("output", ""),
        score=None,  # 非Engineering任务不评分
        duration_ms=0,
    )


async def _update_progress(task_id: str, phase: int, progress: int, message: str):
    """更新任务进度"""
    overall = min(100, max(0, (phase * 10) + (progress // 10)))

    await hermes_state.update_task_status(
        task_id,
        HermesTaskStatus.IN_PROGRESS,
        progress=overall,
        phase=phase
    )

    event = HermesEvent(
        event=HermesEventType.TASK_PROGRESS,
        task_id=task_id,
        phase=phase,
        progress=overall,
        data={"message": message}
    )
    await hermes_state.publish_event(task_id, event)


async def _publish_output(task_id: str, output: str):
    """发布Agent输出"""
    event = HermesEvent(
        event=HermesEventType.AGENT_MESSAGE,
        task_id=task_id,
        data={"output": output}
    )
    await hermes_state.publish_event(task_id, event)


@router.get("/tasks", response_model=HermesTaskListResponse, summary="列出Hermes任务")
async def list_hermes_tasks(
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
):
    """列出当前用户的所有任务"""
    status_enum = HermesTaskStatus(status) if status else None

    offset = (page - 1) * limit
    tasks, total = await hermes_state.list_tasks(
        user_id=current_user.id,
        status=status_enum,
        agent_type=agent_type,
        limit=limit,
        offset=offset,
    )

    return HermesTaskListResponse(
        items=[_task_to_response(t) for t in tasks],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=HermesTaskResponse, summary="获取任务详情")
async def get_hermes_task(
    task_id: str,
    current_user = Depends(get_current_user),
):
    """获取任务详情"""
    task = await hermes_state.get_task(task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@router.delete("/tasks/{task_id}", response_model=dict, summary="取消任务")
async def cancel_hermes_task(
    task_id: str,
    current_user = Depends(get_current_user),
):
    """取消正在执行的任务"""
    task = await hermes_state.get_task(task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this task")

    if task.status not in (HermesTaskStatus.NEW, HermesTaskStatus.QUEUED, HermesTaskStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in status '{task.status.value}'"
        )

    await hermes_state.update_task_status(
        task_id,
        HermesTaskStatus.CANCELLED
    )

    event = HermesEvent(
        event=HermesEventType.TASK_FAILED,
        task_id=task_id,
        data={"reason": "cancelled by user"}
    )
    await hermes_state.publish_event(task_id, event)

    return {"message": "Task cancelled", "task_id": task_id}


# ============ WebSocket ============

@router.websocket("/events/{task_id}")
async def hermes_websocket_events(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
):
    """WebSocket实时事件流

    连接: ws://localhost:8000/api/v1/hermes/events/{task_id}?token={jwt}
    """
    # 验证token
    user_id = decode_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # 订阅Redis事件
    pubsub = await hermes_state.subscribe_events(task_id)

    try:
        # 发送初始状态
        task = await hermes_state.get_task(task_id)
        if task:
            await websocket.send_json({
                "event": "connected",
                "task_id": task_id,
                "status": task.status.value,
                "progress": task.overall_progress,
                "current_phase": task.current_phase,
            })

        # 转发Redis事件
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=30.0
                )
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({
                    "event": "heartbeat",
                    "task_id": task_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"hermes:events:{task_id}")


# ============ 管理API ============

@router.get("/agents", summary="列出可用Agent")
async def list_agents(current_user = Depends(get_current_user)):
    """列出所有可用的Agent类型及其配置"""
    from app.hermes.executor import AGENT_CONFIGS

    return {
        "agents": [
            {
                "type": agent_type,
                "name": config.name,
                "model": config.model,
                "timeout": config.timeout,
                "gan_enabled": agent_type in ("planner", "coder", "reviewer", "writer"),
            }
            for agent_type, config in AGENT_CONFIGS.items()
        ]
    }


@router.get("/stats", summary="获取统计信息")
async def get_stats(current_user = Depends(get_current_user)):
    """获取Hermes全局统计"""
    stats = await hermes_state.get_stats()

    # 添加更多统计
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        from app.hermes.evolution import ExecutionLog, Decision

        # 执行日志统计
        result = await session.execute(
            select(func.count(), func.avg(ExecutionLog.score))
            .where(ExecutionLog.score.isnot(None))
        )
        log_count, avg_score = result.one_or_none()

        # 决策统计
        result = await session.execute(
            select(func.count()).select_from(Decision)
        )
        decision_count = result.scalar() or 0

    return {
        **stats,
        "execution_logs": {
            "total": log_count or 0,
            "avg_score": round(avg_score, 2) if avg_score else None,
        },
        "decisions": {
            "total": decision_count,
        }
    }


@router.get("/evolution/suggestions", summary="获取优化建议")
async def get_optimization_suggestions(
    agent_type: str = Query(..., description="Agent类型"),
):
    """获取指定Agent的优化建议"""
    from app.hermes.evolution import ExecutionLog

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # 获取最近的失败
        result = await session.execute(
            select(ExecutionLog)
            .where(
                ExecutionLog.agent_type == agent_type,
                ExecutionLog.score < 6.0
            )
            .order_by(ExecutionLog.created_at.desc())
            .limit(10)
        )
        failures = result.scalars().all()

    recent_failures = [
        {"message": f"Phase {f.phase} failed with score {f.score}"}
        for f in failures
    ]

    suggestion = await evolution_engine.generate_optimization_suggestion(
        agent_type, recent_failures
    )

    return {
        "agent_type": agent_type,
        "recent_failures": len(recent_failures),
        "suggestion": suggestion,
    }
