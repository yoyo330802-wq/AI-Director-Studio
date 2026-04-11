"""
漫AI - Celery视频生成任务
"""
from celery import Celery, Task
import httpx
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# 创建Celery应用
celery_app = Celery(
    "manai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10分钟超时
    task_soft_time_limit=540,  # 9分钟软超时
)


class CallbackTask(Task):
    """支持回调的任务基类"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        logger.info(f"任务成功: {task_id}")
        
        # 发送回调
        if callback_url := kwargs.get("callback_url"):
            try:
                httpx.post(callback_url, json={
                    "task_id": task_id,
                    "status": "completed",
                    "result": retval
                }, timeout=10)
            except Exception as e:
                logger.error(f"回调失败: {e}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        logger.error(f"任务失败: {task_id}, error: {exc}")
        
        # 更新任务状态
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, decode_responses=True)
            task_data = r.get(f"task:{task_id}")
            if task_data:
                task = json.loads(task_data)
                task["status"] = "failed"
                task["error"] = str(exc)
                task["failed_at"] = datetime.utcnow().isoformat()
                r.set(f"task:{task_id}", json.dumps(task))
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
        
        # 发送回调
        if callback_url := kwargs.get("callback_url"):
            try:
                httpx.post(callback_url, json={
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(exc)
                }, timeout=10)
            except Exception as e:
                logger.error(f"回调失败: {e}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60
)
def generate_video_task(
    self,
    task_id: str,
    channel: str,
    params: Dict,
    user_id: int,
    callback_url: str = None
) -> Dict:
    """
    异步视频生成任务
    
    Args:
        task_id: 任务ID
        channel: 渠道 (wan21_14b, wan21_1.3b, vidu, kling)
        params: 生成参数
        user_id: 用户ID
        callback_url: 回调URL
    
    Returns:
        Dict: 生成结果
    """
    try:
        # 根据渠道选择客户端
        if channel.startswith("wan21"):
            from app.clients.wan21_client import create_wan21_client
            client = create_wan21_client(channel, base_url=settings.WAN21_BASE_URL)
            
            # 调用生成
            if params.get("image_url"):
                result = asyncio.run(client.image_to_video(**params))
            else:
                result = asyncio.run(client.text_to_video(**params))
        
        elif channel == "vidu":
            from app.clients.vidu_client import ViduClient
            client = ViduClient(api_key=settings.VIDU_API_KEY)
            
            result = asyncio.run(client.text_to_video(**params))
        
        elif channel == "kling":
            from app.clients.siliconflow_client import SiliconFlowClient
            client = SiliconFlowClient(api_key=settings.SILICONFLOW_API_KEY)
            
            result = asyncio.run(client.text_to_video(model="kling", **params))
        
        else:
            raise ValueError(f"未知渠道: {channel}")
        
        # 更新任务状态
        _update_task_status(task_id, "completed", result)
        
        # 确认扣费（调整预扣与实际成本差异）
        from app.services.billing import BillingService
        BillingService.confirm_deduction(task_id, result.get("cost", 0))
        
        return result
    
    except Exception as exc:
        logger.error(f"生成任务异常: {task_id}, error: {exc}")
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"任务将在 {self.default_retry_delay} 秒后重试")
            raise self.retry(exc=exc)
        else:
            # 最终失败
            _update_task_status(task_id, "failed", {"error": str(exc)})
            
            # 退款
            from app.services.billing import BillingService
            task_data = _get_task_data(task_id)
            if task_data:
                BillingService.refund(
                    user_id=user_id,
                    amount=task_data.get("estimated_cost", 0),
                    task_id=task_id,
                    description="生成失败退款"
                )
            
            raise


def _update_task_status(task_id: str, status: str, result: Dict):
    """更新任务状态"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        task_data = r.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = status
            
            if status == "completed":
                task["video_url"] = result.get("video_url")
                task["cover_url"] = result.get("cover_url")
                task["cost"] = result.get("cost")
                task["completed_at"] = datetime.utcnow().isoformat()
                task["progress"] = 100
            elif status == "failed":
                task["error"] = result.get("error")
                task["failed_at"] = datetime.utcnow().isoformat()
            
            r.set(f"task:{task_id}", json.dumps(task))
            
    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")


def _get_task_data(task_id: str) -> Optional[Dict]:
    """获取任务数据"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        task_data = r.get(f"task:{task_id}")
        if task_data:
            return json.loads(task_data)
    except Exception:
        pass
    return None


# 导出celery_app
__all__ = ["celery_app", "generate_video_task"]
