"""
漫AI - 视频生成API
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.database import User
from app.models.schemas import GenerationRequest, GenerationResponse, TaskStatus, TaskListResponse
from app.core.security import get_current_user
from app.services.generation import generation_service, GenerationService

router = APIRouter()


@router.post("", response_model=GenerationResponse)
async def create_generation(
    request: GenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建视频生成任务"""
    
    # 检查用户余额
    if current_user.balance <= 0 and not current_user.is_vip:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="余额不足，请先充值"
        )
    
    # 预估成本检查
    estimated_cost = {
        "fast": 0.04,
        "balanced": 0.06,
        "premium": 0.09,
    }.get(request.mode, 0.06) * request.duration
    
    if current_user.balance < estimated_cost and not current_user.is_vip:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"余额不足，当前预估消耗 ¥{estimated_cost}"
        )
    
    # 创建任务
    try:
        result = await generation_service.create_task(
            db=db,
            user_id=current_user.id,
            request=request
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    from app.models.database import Task, TaskStatus
    
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status:
        try:
            task_status = TaskStatus(status)
            query = query.filter(Task.status == task_status)
        except:
            pass
    
    total = query.count()
    tasks = query.order_by(Task.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return TaskListResponse(
        items=[
            TaskStatus(
                task_id=t.task_id,
                task_no=t.task_no,
                status=t.status.value,
                progress=t.progress or 0,
                video_url=t.video_url,
                cover_url=t.cover_url,
                error=t.error,
                cost=t.actual_cost,
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
            )
            for t in tasks
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    try:
        result = await generation_service.get_task_status(
            db=db,
            task_id=task_id,
            user_id=current_user.id
        )
        return TaskStatus(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消任务"""
    from app.models.database import Task, TaskStatus
    
    task = db.query(Task).filter(
        Task.task_id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消pending或queued状态的任务"
        )
    
    task.status = TaskStatus.CANCELLED
    db.commit()
    
    return {"message": "任务已取消"}


@router.post("/tasks/{task_id}/callback")
async def task_callback(
    task_id: str,
    db: Session = Depends(get_db)
):
    """第三方回调接口"""
    from app.models.database import Task, TaskStatus
    
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        return {"error": "task not found"}
    
    # 更新任务状态
    # 这里应该解析回调数据
    db.commit()
    
    return {"status": "ok"}
