"""
漫AI - 内容审核 API
Sprint 4: S4-F2 内容审核
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

from app.core.security import get_current_user
from app.models.user import User
from app.services.content_moderation import (
    content_moderation_service,
    ModerationResult,
    ModerationLevel
)


router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])


class ModerationCheckRequest(BaseModel):
    """审核请求"""
    prompt: str
    negative_prompt: Optional[str] = None


class ModerationCheckResponse(BaseModel):
    """审核响应"""
    passed: bool
    level: str
    reason: Optional[str]
    flagged_terms: List[str]
    score: float


class ModerationBatchRequest(BaseModel):
    """批量审核请求"""
    prompts: List[str]


@router.post(
    "/check",
    response_model=ModerationCheckResponse,
    summary="内容审核",
    description="检查提示词是否包含违规内容，支持图文审核",
    responses={
        200: {"description": "审核完成"},
        401: {"description": "未授权"},
    }
)
async def check_content(
    request: ModerationCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """
    审核提示词内容
    
    **审核级别**:
    - SAFE: 内容安全，可直接使用
    - WARNING: 包含警告内容，建议修改
    - BLOCK: 包含违规内容，拒绝使用
    
    **返回内容**:
    - passed: 是否通过审核
    - level: 审核级别
    - reason: 审核原因
    - flagged_terms: 命中的敏感词列表
    - score: 风险评分 (0-1)
    """
    result = content_moderation_service.check_prompt(
        request.prompt,
        request.negative_prompt
    )
    
    return ModerationCheckResponse(
        passed=result.level != ModerationLevel.BLOCK,
        level=result.level.value,
        reason=result.reason,
        flagged_terms=result.flagged_terms,
        score=result.score
    )


@router.post(
    "/check-simple",
    summary="简单内容审核（无需认证）",
    description="用于前端实时预览时快速检查提示词，无需登录",
    responses={
        200: {"description": "审核结果"},
    }
)
async def check_content_simple(
    prompt: str,
    negative_prompt: Optional[str] = None,
):
    """
    简单审核接口（无需认证）
    
    用于前端实时预览时快速检查。
    此接口不需要 Authorization header，适合在用户输入时实时检测。
    """
    result = content_moderation_service.check_prompt(prompt, negative_prompt)
    
    return {
        "passed": result.level != ModerationLevel.BLOCK,
        "level": result.level.value,
        "warning": result.level == ModerationLevel.WARNING,
        "reason": result.reason,
        "flagged_terms": result.flagged_terms
    }


@router.post("/batch-check", response_model=List[ModerationCheckResponse])
async def batch_check_content(
    request: ModerationBatchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    批量审核提示词
    
    最多支持 20 条同时审核。
    """
    if len(request.prompts) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多支持20条同时审核"
        )
    
    results = []
    for prompt in request.prompts:
        result = content_moderation_service.check_text(prompt)
        results.append(ModerationCheckResponse(
            passed=result.level != ModerationLevel.BLOCK,
            level=result.level.value,
            reason=result.reason,
            flagged_terms=result.flagged_terms,
            score=result.score
        ))
    
    return results


@router.get("/terms")
async def get_moderation_terms():
    """
    获取审核服务状态信息

    返回审核服务是否启用等基本信息。
    注意：敏感词列表不对外暴露，以防止攻击者利用。
    """
    return {
        "enabled": content_moderation_service.enabled,
        "check_count": len(content_moderation_service.PROHIBITED_TERMS) + len(content_moderation_service.WARNING_TERMS),
    }
