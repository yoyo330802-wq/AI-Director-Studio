# 视频生成任务 (Celery)

import asyncio
from celery import Celery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.task import GenerationTask
from app.models.user import User
from app.clients.comfyui_client import comfyui_client
from app.clients.siliconflow_client import siliconflow_client
from app.services.router import is_comfyui_path, is_siliconflow_path, ExecutionPath

# Celery配置
celery_app = Celery(
    "video_generation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10分钟超时
)


def submit_generation_task(task_id: str):
    """提交生成任务到Celery"""
    process_generation_task.delay(task_id)


@celery_app.task(bind=True, max_retries=3)
def process_generation_task(self, task_id: str):
    """异步执行视频生成任务

    这是Celery任务，实际在worker进程中执行
    由于需要async/await，我们在event loop中运行
    """
    asyncio.run(_process_generation_async(task_id))


async def _process_generation_async(task_id: str):
    """异步执行视频生成"""

    # 1. 获取任务
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GenerationTask).where(GenerationTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            return

        # 更新状态为processing
        task.status = "processing"
        task.progress = 10
        await session.commit()

        # 2. 根据执行路径调用不同服务
        execution_path = task.execution_path
        video_url = None

        try:
            if is_comfyui_path(execution_path):
                video_url = await _generate_via_comfyui(task)
            elif is_siliconflow_path(execution_path):
                video_url = await _generate_via_siliconflow(task)
            else:
                video_url = None
                task.error = f"Unknown execution path: {execution_path}"
        except Exception as e:
            print(f"[VideoGen] Generation error: {e}")
            task.error = str(e)
            video_url = None

        # 3. 更新最终状态
        if video_url:
            task.status = "completed"
            task.progress = 100
            task.video_url = video_url

            # 扣除用户Token
            await _deduct_user_tokens(session, task.user_id, task.token_cost)
        else:
            task.status = "failed"
            if not task.error:
                task.error = "Generation failed"

        task.completed_at = asyncio.get_event_loop().time()
        await session.commit()


async def _generate_via_comfyui(task: GenerationTask) -> str | None:
    """通过ComfyUI Wan2.1生成视频"""

    from app.api.websocket import push_task_progress

    # 检查ComfyUI可用性
    if not await comfyui_client.is_available():
        print("[VideoGen] ComfyUI unavailable, falling back to SiliconFlow")
        # 降级到硅基流动
        task.execution_path = ExecutionPath.SILICONFLOW_VIDU.value
        return await _generate_via_siliconflow(task)

    # 构建并提交工作流
    result = await comfyui_client.generate_video(
        prompt=task.prompt,
        duration=task.duration,
        aspect_ratio=task.aspect_ratio,
        negative_prompt=getattr(task, 'negative_prompt', None) or "低质量, 模糊, 变形",
    )

    if "error" in result:
        print(f"[VideoGen] ComfyUI error: {result['error']}")
        # 降级到 SiliconFlow
        task.execution_path = ExecutionPath.SILICONFLOW_VIDU.value
        return await _generate_via_siliconflow(task)

    video_url = result.get("video_url")
    if video_url:
        await push_task_progress(task.id, "completed", 100, video_url)

    return video_url


async def _generate_via_siliconflow(task: GenerationTask) -> str | None:
    """通过硅基流动API生成视频"""

    from app.api.websocket import push_task_progress

    model = "vidu" if "vidu" in task.execution_path else "kling"

    # 1. 提交任务
    task_id = await siliconflow_client.generate_video(
        model=model,
        prompt=task.prompt,
        duration=task.duration,
        aspect_ratio=task.aspect_ratio,
    )

    if not task_id:
        print("[VideoGen] SiliconFlow: failed to submit task")
        return None

    # 2. 轮询状态
    for i in range(24):  # 最多等120秒
        await asyncio.sleep(5)

        status_result = await siliconflow_client.get_task_status(task_id)
        status = status_result.get("status", "unknown")
        progress = status_result.get("progress", 0)
        video_url = status_result.get("video_url")

        # 更新进度
        await _update_task_progress(task.id, progress)

        if status == "completed" and video_url:
            await push_task_progress(task.id, "completed", 100, video_url)
            return video_url
        elif status == "failed":
            print(f"[VideoGen] SiliconFlow failed: {status_result.get('error')}")
            return None

        print(f"[VideoGen] SiliconFlow polling... {i*5}s, status={status}")

    print("[VideoGen] SiliconFlow timeout")
    return None


async def _update_task_progress(task_id: str, progress: int):
    """更新任务进度"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GenerationTask).where(GenerationTask.id == task_id)
            )
            current_task = result.scalar_one_or_none()
            if current_task:
                current_task.progress = min(progress, 95)  # 不超过95，留给完成
                await session.commit()
    except Exception as e:
        print(f"[VideoGen] Failed to update progress: {e}")


async def _deduct_user_tokens(session: AsyncSession, user_id: int, tokens: int):
    """扣除用户Token"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.token_balance = max(0, user.token_balance - tokens)
        await session.commit()
