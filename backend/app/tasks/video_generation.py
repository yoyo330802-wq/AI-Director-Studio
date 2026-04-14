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
        
        if is_comfyui_path(execution_path):
            video_url = await _generate_via_comfyui(task)
        elif is_siliconflow_path(execution_path):
            video_url = await _generate_via_siliconflow(task)
        else:
            video_url = None
            task.error = f"Unknown execution path: {execution_path}"
        
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
    """通过ComfyUI生成视频"""
    
    from app.api.websocket import push_task_progress
    
    # 模拟生成过程 (实际会调用ComfyUI API)
    
    # 检查ComfyUI可用性
    if not await comfyui_client.is_available():
        # 降级到硅基流动
        task.execution_path = ExecutionPath.SILICONFLOW_VIDU.value
        return await _generate_via_siliconflow(task)
    
    # 构建prompt
    prompt = comfyui_client.build_wan21_prompt(
        prompt=task.prompt,
        duration=task.duration,
        aspect_ratio=task.aspect_ratio
    )
    
    # 提交到ComfyUI队列
    prompt_id = await comfyui_client.queue_prompt(prompt)
    if not prompt_id:
        return None
    
    # 模拟轮询等待完成 (实际用WebSocket或轮询history)
    for i in range(20):  # 最多等待100秒
        await asyncio.sleep(5)
        
        # 更新进度
        progress = min(10 + (i * 4), 90)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GenerationTask).where(GenerationTask.id == task.id)
            )
            current_task = result.scalar_one_or_none()
            if current_task:
                current_task.progress = progress
                await session.commit()
        
        # 推送进度到WebSocket
        await push_task_progress(task.id, "processing", progress)
        
        # 模拟检查完成 (实际查询ComfyUI history)
        if i >= 3:  # 模拟15秒后完成
            video_url = f"https://minio.localhost:9000/videos/{task.id}.mp4"
            await push_task_progress(task.id, "completed", 100, video_url)
            return video_url
    
    return None


async def _generate_via_siliconflow(task: GenerationTask) -> str | None:
    """通过硅基流动API生成视频"""
    
    from app.api.websocket import push_task_progress
    
    # 模拟生成过程 (实际会调用硅基流动API)
    
    model = "vidu" if "vidu" in task.execution_path else "kling"
    
    # 模拟API调用
    for i in range(12):  # 最多等待60秒
        await asyncio.sleep(5)
        
        # 更新进度
        progress = min(10 + (i * 7), 90)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GenerationTask).where(GenerationTask.id == task.id)
            )
            current_task = result.scalar_one_or_none()
            if current_task:
                current_task.progress = progress
                await session.commit()
        
        # 推送进度到WebSocket
        await push_task_progress(task.id, "processing", progress)
        
        if i >= 5:  # 模拟30秒后完成
            video_url = f"https://minio.localhost:9000/videos/{task.id}.mp4"
            await push_task_progress(task.id, "completed", 100, video_url)
            return video_url
    
    return None


async def _deduct_user_tokens(session: AsyncSession, user_id: int, tokens: int):
    """扣除用户Token"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.token_balance = max(0, user.token_balance - tokens)
        await session.commit()
