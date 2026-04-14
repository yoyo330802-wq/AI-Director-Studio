"""
漫AI - 视频生成服务
对接Wan2.1/Vidu/可灵等视频生成渠道
"""
import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Optional, AsyncGenerator, TYPE_CHECKING
from enum import Enum

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import Task, TaskStatus, ChannelConfig, ChannelType
from app.models.schemas import GenerationRequest, GenerationResponse
from app.services.router import get_router, GenerationMode


class VideoProvider(str, Enum):
    """视频生成提供商"""
    WAN_1_3B = "wan2.1-1.3b"
    WAN_14B = "wan2.1-14b"
    VIDU = "vidu"
    KLING = "kling"


def _get_provider_config():
    """获取提供商配置（延迟初始化）"""
    return {
        VideoProvider.WAN_1_3B: {
            "endpoint": settings.WAN2_1_1_3B_ENDPOINT,
            "api_key": settings.WAN2_1_1_3B_API_KEY,
            "timeout": 120,
            "max_retries": 2,
        },
        VideoProvider.WAN_14B: {
            "endpoint": settings.WAN2_1_14B_ENDPOINT,
            "api_key": settings.WAN2_1_14B_API_KEY,
            "timeout": 180,
            "max_retries": 2,
        },
        VideoProvider.VIDU: {
            "endpoint": settings.VIDU_ENDPOINT,
            "api_key": settings.VIDU_API_KEY,
            "timeout": 300,
            "max_retries": 1,
        },
        VideoProvider.KLING: {
            "endpoint": settings.KLING_ENDPOINT,
            "api_key": settings.KLING_API_KEY,
            "timeout": 300,
            "max_retries": 1,
        },
    }


class GenerationService:
    """视频生成服务"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient()
        self.PROVIDER_CONFIG = _get_provider_config()
    
    async def close(self):
        await self.http_client.aclose()
    
    async def create_task(
        self,
        db: Session,
        user_id: int,
        request: GenerationRequest
    ) -> GenerationResponse:
        """创建生成任务"""
        
        # 1. 获取路由决策
        router = await get_router()
        mode = GenerationMode(request.mode)
        
        try:
            route = await router.route(
                db=db,
                mode=mode,
                prompt=request.prompt,
                duration=request.duration,
                resolution=request.resolution
            )
        except Exception as e:
            # 降级到默认渠道
            route = await router.fallback_route(db, 0)
            if not route:
                raise Exception("暂无可用生成渠道")
        
        # 2. 创建任务记录
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task_no = f"MAN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        
        task = Task(
            task_id=task_id,
            task_no=task_no,
            user_id=user_id,
            channel_id=route.channel_id,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            mode=request.mode,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            reference_image=request.image_url,
            status=TaskStatus.PENDING,
            estimated_cost=route.estimated_cost,
            estimated_time=route.estimated_time,
            queue_position=route.queue_position,
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 3. 发送到生成队列
        await self._enqueue_task(task, request)
        
        # 4. 发送WebSocket通知
        await notify_task_progress(
            task_id=task_id,
            user_id=user_id,
            progress=0,
            status="pending"
        )
        
        return GenerationResponse(
            task_id=task_id,
            task_no=task_no,
            status="pending",
            channel=route.channel_name,
            channel_name=route.channel_name,
            estimated_cost=route.estimated_cost,
            estimated_time=route.estimated_time,
            queue_position=route.queue_position,
            created_at=task.created_at,
        )
    
    async def _enqueue_task(self, task: Task, request: GenerationRequest):
        """将任务加入生成队列"""
        # 这里应该加入Redis队列或消息队列
        # 简化实现：直接触发异步生成
        asyncio.create_task(self._process_task(task.id))
    
    async def _process_task(self, task_id: int):
        """处理任务（异步）"""
        # 获取数据库会话
        from app.models.db import SessionLocal
        db = SessionLocal()
        
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
            
            # 更新状态为处理中
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            db.commit()
            
            # 通知进度
            await notify_task_progress(
                task_id=task.task_id,
                user_id=task.user_id,
                progress=10,
                status="processing"
            )
            
            # 获取渠道配置
            channel = db.query(ChannelConfig).filter(
                ChannelConfig.id == task.channel_id
            ).first()
            
            if not channel:
                await self._fail_task(db, task, "渠道不可用")
                return
            
            # 调用对应提供商API
            provider = self._get_provider(channel.channel_code)
            
            try:
                result = await self._call_provider(provider, task, request)
                
                # 更新任务结果
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.video_url = result.get("video_url")
                task.cover_url = result.get("cover_url")
                task.thumbnail_url = result.get("thumbnail_url")
                task.actual_cost = result.get("cost", task.estimated_cost)
                task.progress = 100
                
                # 通知完成
                await notify_task_progress(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    progress=100,
                    status="completed",
                    video_url=result.get("video_url")
                )
                
            except Exception as e:
                await self._fail_task(db, task, str(e))
            
            db.commit()
            
        finally:
            db.close()
    
    def _get_provider(self, channel_code: str) -> VideoProvider:
        """获取提供商"""
        mapping = {
            "wan2.1-1.3b": VideoProvider.WAN_1_3B,
            "wan2.1-14b": VideoProvider.WAN_14B,
            "vidu": VideoProvider.VIDU,
            "kling": VideoProvider.KLING,
        }
        return mapping.get(channel_code, VideoProvider.WAN_1_3B)
    
    async def _call_provider(
        self,
        provider: VideoProvider,
        task: Task,
        request: GenerationRequest
    ) -> dict:
        """调用提供商API"""
        config = self.PROVIDER_CONFIG.get(provider)
        
        if not config or not config.get("endpoint"):
            # 模拟生成（开发环境）
            return await self._mock_generate(task)
        
        # 实际调用API
        async with httpx.AsyncClient(timeout=config["timeout"]) as client:
            response = await client.post(
                f"{config['endpoint']}/generate",
                json={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "duration": request.duration,
                    "aspect_ratio": request.aspect_ratio,
                    "resolution": request.resolution,
                    "image_url": request.image_url,
                    "callback_url": f"{settings.API_BASE_URL}/v1/tasks/{task.task_id}/callback",
                },
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.text}")
            
            result = response.json()
            
            # 轮询直到完成
            task_id = result.get("task_id")
            while True:
                await asyncio.sleep(5)
                status_response = await client.get(
                    f"{config['endpoint']}/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {config['api_key']}"}
                )
                status_data = status_response.json()
                
                if status_data["status"] == "completed":
                    return {
                        "video_url": status_data["video_url"],
                        "cover_url": status_data.get("cover_url"),
                        "thumbnail_url": status_data.get("thumbnail_url"),
                        "cost": status_data.get("cost"),
                    }
                elif status_data["status"] == "failed":
                    raise Exception(status_data.get("error", "生成失败"))
                
                # 更新进度
                task.progress = status_data.get("progress", 50)
                await notify_task_progress(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    progress=task.progress,
                    status="processing"
                )
    
    async def _mock_generate(self, task: Task) -> dict:
        """模拟生成（开发环境）"""
        # 模拟生成时间
        await asyncio.sleep(3)
        
        # 返回模拟结果
        return {
            "video_url": f"https://cdn.manai.example.com/videos/{task.task_id}.mp4",
            "cover_url": f"https://cdn.manai.example.com/covers/{task.task_id}.jpg",
            "thumbnail_url": f"https://cdn.manai.example.com/thumbs/{task.task_id}.jpg",
            "cost": task.estimated_cost,
        }
    
    async def _fail_task(self, db: Session, task: Task, error: str):
        """标记任务失败"""
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.utcnow()
        db.commit()
        
        await notify_task_progress(
            task_id=task.task_id,
            user_id=task.user_id,
            progress=0,
            status="failed",
            error=error
        )
    
    async def get_task_status(
        self,
        db: Session,
        task_id: str,
        user_id: int
    ) -> dict:
        """获取任务状态"""
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            raise ValueError("任务不存在")
        
        return {
            "task_id": task.task_id,
            "task_no": task.task_no,
            "status": task.status.value,
            "progress": task.progress or 0,
            "video_url": task.video_url,
            "cover_url": task.cover_url,
            "thumbnail_url": task.thumbnail_url,
            "error": task.error,
            "cost": task.actual_cost,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }


# 全局服务
generation_service = GenerationService()
