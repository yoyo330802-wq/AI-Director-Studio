"""
漫AI - 计费API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db import get_db
from app.models.database import User, PaymentTransaction, Order, Package, PaymentMethod, OrderStatus
from app.models.schemas import (
    BalanceResponse, RechargeRequest, RechargeResponse, TransactionResponse
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/bill", tags=["billing"])


@router.get(
    "/balance",
    response_model=BalanceResponse,
    summary="获取账户余额",
    description="获取当前用户的账户余额、视频配额使用情况",
    responses={
        200: {"description": "余额信息获取成功"},
        401: {"description": "未授权，需要登录"},
    }
)
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户的账户余额和视频配额信息。
    
    **返回内容**:
    - balance: 账户余额（元）
    - video_quota: 视频配额（秒）
    - video_used: 已使用配额（秒）
    - video_remaining: 剩余配额（秒）
    """
    return BalanceResponse(
        balance=current_user.balance or 0.0,
        video_quota=current_user.video_quota or 0,
        video_used=current_user.video_used or 0,
        video_remaining=(current_user.video_quota or 0) - (current_user.video_used or 0)
    )


@router.post(
    "/recharge",
    response_model=RechargeResponse,
    summary="账户充值",
    description="为账户余额充值，支持支付宝和微信支付",
    responses={
        200: {"description": "充值成功"},
        401: {"description": "未授权"},
    }
)
def recharge(
    request: RechargeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    为当前账户充值。
    
    **充值方式**:
    - alipay: 支付宝
    - wechat: 微信支付
    - balance: 余额支付（需有足够余额）
    
    **返回内容**:
    - order_id: 订单ID
    - order_no: 订单号
    - qr_code: 支付二维码（扫码支付）
    - expired_at: 支付过期时间
    """
    # 创建充值订单
    order_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{str(current_user.id)[-4:].upper()}"
    
    # 获取支付方式枚举
    payment_method = PaymentMethod.ALIPAY if request.payment_method == "alipay" else PaymentMethod.WECHAT
    
    # 创建订单
    order = Order(
        order_no=order_no,
        user_id=current_user.id,
        package_id=None,
        amount=request.amount,
        actual_amount=request.amount,
        discount=0.0,
        payment_method=payment_method,
        status=OrderStatus.PAID,  # 直接到账
        paid_at=datetime.utcnow()
    )
    db.add(order)
    db.flush()
    
    # 更新用户余额
    old_balance = current_user.balance or 0.0
    current_user.balance = old_balance + request.amount
    
    # 创建交易记录
    tx = PaymentTransaction(
        order_id=order.id,
        transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}{str(current_user.id)[-4:].upper()}",
        payment_method=payment_method,
        amount=request.amount,
        fee=0.0,
        net_amount=request.amount,
        status="success",
        paid_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()
    
    # 生成支付信息（模拟）
    qr_code = f"https://pay.example.com/qr/{order.id}"
    
    return RechargeResponse(
        order_id=str(order.id),
        order_no=order_no,
        amount=request.amount,
        payment_method=request.payment_method,
        qr_code=qr_code,
        expired_at=datetime.utcnow() + timedelta(hours=24)
    )


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取交易记录"""
    # 查询用户的支付交易
    transactions = db.query(PaymentTransaction).join(Order).filter(
        Order.user_id == current_user.id,
        PaymentTransaction.status == "success"
    ).order_by(PaymentTransaction.created_at.desc()).limit(limit).all()
    
    return [
        TransactionResponse(
            id=tx.id,
            transaction_no=tx.transaction_no,
            payment_method=tx.payment_method.value if hasattr(tx.payment_method, 'value') else str(tx.payment_method),
            amount=tx.amount,
            fee=tx.fee or 0.0,
            net_amount=tx.net_amount,
            status=tx.status,
            created_at=tx.created_at,
            paid_at=tx.paid_at
        )
        for tx in transactions
    ]


@router.get("/packages")
def get_packages():
    """获取套餐列表"""
    return [
        {
            "id": "experience",
            "name": "体验包",
            "price": 39.0,
            "minutes": 10,
            "features": ["基础功能", "社区模板"]
        },
        {
            "id": "creator",
            "name": "创作者月卡",
            "price": 399.0,
            "minutes": 100,
            "features": ["优先队列", "高级模板", "无水印"]
        },
        {
            "id": "studio",
            "name": "工作室季卡",
            "price": 1799.0,
            "minutes": 500,
            "features": ["API接入", "批量生成", "专属客服"]
        },
        {
            "id": "enterprise",
            "name": "企业年卡",
            "price": 9999.0,
            "minutes": 3000,
            "features": ["SLA 99.5%", "私有部署", "定制开发"]
        }
    ]


# ============ 按需计费 API (Sprint 6: S6-1) ============

@router.get("/on-demand/pricing", summary="按需计费价格表", tags=["billing"])
def get_on_demand_pricing():
    """获取按需计费价格表
    
    返回各质量模式的每秒价格和预估生成时间
    用于 Studio 界面实时显示费用预估
    """
    return {
        "billing_type": "on_demand",
        "currency": "CNY",
        "modes": [
            {
                "id": "fast",
                "name": "闪电模式",
                "model": "Wan2.1-1.3B",
                "price_per_second": 0.04,
                "price_per_minute": 2.40,
                "estimated_time_seconds": 15,
                "max_duration_seconds": 5,
                "features": ["text2video", "fast_generation"],
                "quality_score": 6,
            },
            {
                "id": "balanced",
                "name": "智能模式",
                "model": "智能路由",
                "price_per_second": 0.06,
                "price_per_minute": 3.60,
                "estimated_time_seconds": 30,
                "max_duration_seconds": 10,
                "features": ["text2video", "image2video", "smart_routing"],
                "quality_score": 7,
            },
            {
                "id": "premium",
                "name": "专业模式",
                "model": "Vidu/可灵",
                "price_per_second": 0.09,
                "price_per_minute": 5.40,
                "estimated_time_seconds": 60,
                "max_duration_seconds": 10,
                "features": ["text2video", "image2video", "anime_style", "motion_brush", "camera_control"],
                "quality_score": 9,
            },
        ],
        "image_to_video surcharge": {
            "description": "图生视频需要使用专业模式",
            "price_per_second": 0.09,
            "applicable_modes": ["premium"],
        },
        "video_minutes_included": 0,
        "note": "按需计费不计入套餐分钟数，单独按秒计费",
    }


@router.get("/on-demand/calculate", summary="计算预估费用", tags=["billing"])
def calculate_estimate(
    mode: str = Query("balanced", description="质量模式: fast/balanced/premium"),
    duration: int = Query(5, ge=5, le=10, description="视频时长(秒)"),
    image_url: str = Query(None, description="参考图片URL (可选，图生视频)"),
):
    """计算单次生成的预估费用
    
    用于用户提交任务前查看费用预览
    """
    pricing = {
        "fast": {"price_per_second": 0.04, "max_duration": 5},
        "balanced": {"price_per_second": 0.06, "max_duration": 10},
        "premium": {"price_per_second": 0.09, "max_duration": 10},
    }
    
    if mode not in pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的质量模式: {mode}，可选: fast/balanced/premium"
        )
    
    config = pricing[mode]
    if duration > config["max_duration"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{mode} 模式最长支持 {config['max_duration']} 秒"
        )
    
    # 图生视频必须用 premium 模式
    if image_url and mode != "premium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图生视频仅支持专业模式 (premium)"
        )
    
    cost = duration * config["price_per_second"]
    tokens = int(cost * 100)  # 1元 = 100 Token
    
    return {
        "mode": mode,
        "duration_seconds": duration,
        "image_url_provided": bool(image_url),
        "estimated_cost_yuan": round(cost, 2),
        "estimated_cost_tokens": tokens,
        "estimated_time_seconds": {
            "fast": 15,
            "balanced": 30,
            "premium": 60,
        }.get(mode, 30),
        "channel_recommended": {
            "fast": "Wan2.1-1.3B (自建)",
            "balanced": "智能路由",
            "premium": "Vidu/可灵 (硅基流动)",
        }.get(mode, "智能路由"),
    }


@router.get("/on-demand/compare", summary="套餐vs按需对比", tags=["billing"])
def compare_package_vs_ondemand(
    duration_minutes: int = Query(60, ge=1, le=1000, description="计划使用分钟数"),
):
    """对比套餐和按需计费的成本
    
    帮助用户选择最经济的方案
    """
    # 按需计费估算
    ondemand_cost_per_minute = 0.06  # balanced 模式
    ondemand_estimate = duration_minutes * ondemand_cost_per_minute
    
    # 套餐价格
    packages = [
        {"name": "体验版", "price": 0, "minutes": 5, "effective_per_minute": 0},
        {"name": "创作者月卡", "price": 39, "minutes": 60, "effective_per_minute": 0.65},
        {"name": "工作室季卡", "price": 199, "minutes": 300, "effective_per_minute": 0.66},
        {"name": "企业年卡", "price": 9999, "minutes": 99999, "effective_per_minute": 0.10},
    ]
    
    recommendations = []
    for pkg in packages:
        if duration_minutes <= pkg["minutes"]:
            if pkg["price"] == 0:
                recommendations.append({
                    "package": pkg["name"],
                    "cost": 0,
                    "savings": ondemand_estimate,
                    "recommended": True,
                })
            else:
                savings = ondemand_estimate - pkg["price"]
                recommendations.append({
                    "package": pkg["name"],
                    "cost": pkg["price"],
                    "savings": max(0, savings),
                    "recommended": savings > 0,
                })
    
    return {
        "usage_minutes": duration_minutes,
        "ondemand_estimate_yuan": round(ondemand_estimate, 2),
        "ondemand_estimate_tokens": int(ondemand_estimate * 100),
        "package_recommendation": recommendations,
        "best_option": recommendations[0]["package"] if recommendations else "按需计费",
    }