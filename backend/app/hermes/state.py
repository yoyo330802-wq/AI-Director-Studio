"""
Hermes - 状态管理
支持Redis实时状态 + PostgreSQL持久化
"""
import json
import logging
from typing import Optional, Any
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.database import AsyncSessionLocal
from app.hermes.models import HermesTask, HermesTaskStatus, HermesEvent, HermesEventType

logger = logging.getLogger(__name__)


class HermesStateManager:
    """
    Hermes状态管理器

    使用Redis存储实时状态（快速读写）
    使用PostgreSQL做持久化（数据安全）
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._prefix = "hermes:"

    async def _get_redis(self) -> redis.Redis:
        """获取Redis连接"""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    def _key(self, *parts) -> str:
        """生成Redis键"""
        return self._prefix + ":".join(str(p) for p in parts)

    # ============ PostgreSQL 操作 ============

    async def create_task(self, command: str, agent_type: str, sprint: str = "S1", user_id: int = 0) -> HermesTask:
        """创建新任务"""
        async with AsyncSessionLocal() as session:
            task = HermesTask(
                command=command,
                agent_type=agent_type,
                gan_sprint=sprint,
                status=HermesTaskStatus.NEW,
                overall_progress=0,
                user_id=user_id
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            # 同步到Redis
            await self._sync_to_redis(task)

            return task

    async def get_task(self, task_id: str, user_id: Optional[int] = None) -> Optional[HermesTask]:
        """获取任务"""
        async with AsyncSessionLocal() as session:
            query = select(HermesTask).where(HermesTask.id == task_id)
            if user_id is not None:
                query = query.where(HermesTask.user_id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def update_task_status(
        self,
        task_id: str,
        status: HermesTaskStatus,
        progress: Optional[int] = None,
        phase: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[HermesTask]:
        """更新任务状态"""
        async with AsyncSessionLocal() as session:
            task = await session.get(HermesTask, task_id)
            if not task:
                return None

            task.status = status
            task.updated_at = datetime.utcnow()

            if progress is not None:
                task.overall_progress = progress

            if phase is not None:
                task.current_phase = phase

            if error_message is not None:
                task.error_message = error_message

            if status in (HermesTaskStatus.COMPLETED, HermesTaskStatus.FAILED, HermesTaskStatus.CANCELLED):
                task.completed_at = datetime.utcnow()

            await session.commit()
            await session.refresh(task)

            # 同步到Redis
            await self._sync_to_redis(task)

            return task

    async def update_task_result(
        self,
        task_id: str,
        result: dict,
        scores: Optional[dict] = None
    ) -> Optional[HermesTask]:
        """更新任务结果"""
        async with AsyncSessionLocal() as session:
            task = await session.get(HermesTask, task_id)
            if not task:
                return None

            task.set_result(result)
            if scores:
                task.set_scores(scores)
            task.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(task)

            await self._sync_to_redis(task)

            return task

    async def list_tasks(
        self,
        user_id: Optional[int] = None,
        status: Optional[HermesTaskStatus] = None,
        agent_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[HermesTask], int]:
        """列出任务"""
        async with AsyncSessionLocal() as session:
            query = select(HermesTask)

            if user_id is not None:
                query = query.where(HermesTask.user_id == user_id)
            if status:
                query = query.where(HermesTask.status == status)
            if agent_type:
                query = query.where(HermesTask.agent_type == agent_type)

            # 获取总数
            from sqlalchemy import func
            count_query = select(func.count()).select_from(HermesTask)
            if user_id is not None:
                count_query = count_query.where(HermesTask.user_id == user_id)
            if status:
                count_query = count_query.where(HermesTask.status == status)
            if agent_type:
                count_query = count_query.where(HermesTask.agent_type == agent_type)
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # 分页
            query = query.order_by(HermesTask.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            tasks = list(result.scalars().all())

            return tasks, total

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        async with AsyncSessionLocal() as session:
            task = await session.get(HermesTask, task_id)
            if not task:
                return False

            await session.delete(task)
            await session.commit()

            # 从Redis删除
            r = await self._get_redis()
            await r.delete(self._key("task", task_id))

            return True

    # ============ Redis 操作（实时状态）============

    async def _sync_to_redis(self, task: HermesTask):
        """同步任务状态到Redis"""
        try:
            r = await self._get_redis()
            key = self._key("task", task.id)
            data = {
                "id": task.id,
                "command": task.command,
                "agent_type": task.agent_type,
                "status": task.status.value,
                "current_phase": task.current_phase,
                "overall_progress": task.overall_progress,
                "gan_sprint": task.gan_sprint,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            await r.set(key, json.dumps(data, ensure_ascii=False))
            # 设置过期时间 24小时
            await r.expire(key, 86400)
        except Exception as e:
            logger.warning(f"Failed to sync task to Redis: {e}")

    async def get_task_from_redis(self, task_id: str) -> Optional[dict]:
        """从Redis获取任务状态（快速）"""
        try:
            r = await self._get_redis()
            key = self._key("task", task_id)
            data = await r.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to get task from Redis: {e}")
        return None

    async def publish_event(self, task_id: str, event: HermesEvent):
        """发布任务事件到Redis频道"""
        try:
            r = await self._get_redis()
            channel = self._key("events", task_id)
            event_data = {
                "event": event.event.value,
                "task_id": event.task_id,
                "phase": event.phase,
                "progress": event.progress,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
            }
            await r.publish(channel, json.dumps(event_data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def subscribe_events(self, task_id: str):
        """订阅任务事件"""
        r = await self._get_redis()
        pubsub = r.pubsub()
        channel = self._key("events", task_id)
        await pubsub.subscribe(channel)
        return pubsub

    # ============ 统计 ============

    async def get_stats(self) -> dict:
        """获取全局统计"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func

            result = await session.execute(select(func.count(HermesTask.id)))
            total = result.scalar() or 0

            stats = {}
            for status in HermesTaskStatus:
                count_result = await session.execute(
                    select(func.count()).select_from(HermesTask).where(
                        HermesTask.status == status
                    )
                )
                stats[status.value] = count_result.scalar() or 0

            return {
                "total": total,
                "by_status": stats,
            }


# 全局单例
hermes_state = HermesStateManager()
