# WebSocket - /ws/tasks/{task_id}

import asyncio
import json
import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.task import GenerationTask
from app.core.security import decode_token

router = APIRouter()

# Redis 连接池
_redis_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_pool


class ConnectionManager:
    """WebSocket连接管理器（Redis pub/sub版本）"""
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        # 订阅该task的Redis频道
        r = await get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(f"task:{task_id}")
        return pubsub
    
    async def publish_progress(self, task_id: str, data: dict):
        """发布进度到Redis频道"""
        r = await get_redis()
        await r.publish(f"task:{task_id}", json.dumps(data))
    
    async def unsubscribe(self, task_id: str):
        """取消订阅"""
        r = await get_redis()
        await r.unsubscribe(f"task:{task_id}")


manager = ConnectionManager()


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
):
    """WebSocket推送任务进度
    
    连接: ws://localhost:8000/ws/tasks/{task_id}?token={jwt_token}
    内部使用Redis pub/sub，支持多worker
    """
    # 验证token
    user_id = decode_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # 验证任务归属
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GenerationTask).where(
                GenerationTask.id == task_id,
                GenerationTask.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            await websocket.close(code=4004, reason="Task not found")
            return
    
    pubsub = await manager.connect(websocket, task_id)
    
    try:
        # 发送当前状态
        await websocket.send_json({
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "video_url": task.video_url,
            "error": task.error,
        })
        
        # 监听Redis消息
        last_progress = task.progress
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=2.0
                )
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    await websocket.send_json(data)
                    last_progress = data.get('progress', last_progress)
                    if data.get('status') in ('completed', 'failed'):
                        break
            except asyncio.TimeoutError:
                # 超时检查：验证任务是否还在运行
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(GenerationTask).where(GenerationTask.id == task_id)
                    )
                    current_task = result.scalar_one_or_none()
                    if current_task and current_task.status in ('completed', 'failed'):
                        await websocket.send_json({
                            "task_id": task_id,
                            "status": current_task.status,
                            "progress": current_task.progress,
                            "video_url": current_task.video_url,
                            "error": current_task.error,
                        })
                        break
                        
    except WebSocketDisconnect:
        pass
    finally:
        await manager.unsubscribe(task_id)


async def push_task_progress(task_id: str, status: str, progress: int, video_url: str = None, error: str = None):
    """推送任务进度到WebSocket（供Celery任务调用）"""
    await manager.publish_progress(task_id, {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "video_url": video_url,
        "error": error,
    })
