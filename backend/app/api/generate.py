"""
漫AI - 视频生成API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime
import uuid
import json
import redis

from app.config import settings
from app.models.schemas import (
    GenerationRequest, GenerationResponse, TaskStatus,
    GenerationMode, RouteDecision
)
from app.router.smart_router import SmartRouter
from app.services.billing import BillingService

router = APIRouter()

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# OAuth2
oauth2_scheme = APIRouter.__init__.__code__

# 简单依赖获取用户
def get_current_username(token: str) -> str:
    """从token获取用户名"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")


@router.post("", response_model=GenerationResponse)
async def create_generation_task(
    request: GenerationRequest,
    token: str
):
    """创建视频生成任务"""
    # 验证token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    # 获取用户
    user_data = redis_client.get(f"user:{username}")
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    user = json.loads(user_data)
    
    # 初始化路由
    router_engine = SmartRouter(redis_client)
    
    # 构建路由请求
    route_request = type('RouteRequest', (), {
        'request_id': str(uuid.uuid4()),
        'mode': request.mode,
        'quality_priority': request.mode == GenerationMode.PREMIUM,
        'cost_priority': request.mode == GenerationMode.FAST,
        'duration': request.duration,
        'image_url': request.image_url,
        'style': 'anime',  # 默认动漫风格
        'camera_control': False,
        'motion_brush': False,
        'force_channel': None,
        'user_level': user.get('level', 'free')
    })()
    
    # 路由决策
    route_decision = router_engine.route(route_request)
    
    # 计算预估成本
    estimated_cost = route_decision["estimated_cost"] * request.duration
    
    # 检查余额
    if user["balance"] < estimated_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"余额不足，需要 ¥{estimated_cost:.2f}，当前余额 ¥{user['balance']:.2f}"
        )
    
    # 创建任务
    task_id = str(uuid.uuid4())
    task_data = {
        "task_id": task_id,
        "user_id": user_id,
        "username": username,
        "mode": request.mode,
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt,
        "duration": request.duration,
        "aspect_ratio": request.aspect_ratio,
        "resolution": request.resolution,
        "image_url": request.image_url,
        "channel": route_decision["channel"],
        "channel_name": route_decision["channel_name"],
        "estimated_cost": estimated_cost,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # 存储任务
    redis_client.set(f"task:{task_id}", json.dumps(task_data))
    redis_client.zadd(f"user:tasks:{username}", {task_id: datetime.utcnow().timestamp()})
    redis_client.zadd(f"channel:queue:{route_decision['channel']}", {task_id: datetime.utcnow().timestamp()})
    
    # 扣除余额（预扣）
    BillingService.deduct_balance(user_id, estimated_cost, task_id, is_precharge=True)
    
    return GenerationResponse(
        task_id=task_id,
        status="pending",
        channel=route_decision["channel"],
        channel_name=route_decision["channel_name"],
        estimated_cost=estimated_cost,
        estimated_time=route_decision["estimated_time"],
        queue_position=route_decision["queue_position"],
        created_at=datetime.utcnow()
    )


@router.get("/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_data = redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = json.loads(task_data)
    
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", 0),
        video_url=task.get("video_url"),
        cover_url=task.get("cover_url"),
        error=task.get("error"),
        cost=task.get("cost"),
        completed_at=datetime.fromisoformat(task["completed_at"]) if task.get("completed_at") else None
    )


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, token: str):
    """取消任务"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    task_data = redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = json.loads(task_data)
    
    if task["username"] != username:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    if task["status"] not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail="任务已结束，无法取消")
    
    # 更新任务状态
    task["status"] = "cancelled"
    task["cancelled_at"] = datetime.utcnow().isoformat()
    redis_client.set(f"task:{task_id}", json.dumps(task))
    
    # 退还预扣金额
    if task.get("estimated_cost"):
        BillingService.refund(task["user_id"], task["estimated_cost"], task_id)
    
    return {"message": "任务已取消", "task_id": task_id}


@router.get("/route/preview")
async def preview_route(
    mode: GenerationMode = GenerationMode.BALANCED,
    duration: int = 5
):
    """预览路由决策"""
    router_engine = SmartRouter(redis_client)
    
    route_request = type('RouteRequest', (), {
        'request_id': str(uuid.uuid4()),
        'mode': mode,
        'quality_priority': mode == GenerationMode.PREMIUM,
        'cost_priority': mode == GenerationMode.FAST,
        'duration': duration,
        'image_url': None,
        'style': 'anime',
        'camera_control': False,
        'motion_brush': False,
        'force_channel': None,
        'user_level': 'basic'
    })()
    
    decision = router_engine.route(route_request)
    
    return RouteDecision(
        channel=decision["channel"],
        channel_name=decision["channel_name"],
        estimated_cost=decision["estimated_cost"] * duration,
        estimated_time=decision["estimated_time"],
        quality_score=decision["quality_score"],
        queue_position=decision["queue_position"],
        reasoning=_get_routing_reason(mode, decision)
    )


def _get_routing_reason(mode: GenerationMode, decision: dict) -> str:
    """获取路由理由"""
    reasons = {
        GenerationMode.FAST: f"成本优先模式，选择最经济的{decision['channel_name']}",
        GenerationMode.BALANCED: f"智能平衡模式，综合评分最高{decision['channel_name']}",
        GenerationMode.PREMIUM: f"质量优先模式，选择最高质量的{decision['channel_name']}",
    }
    return reasons.get(mode, "智能路由选择")
